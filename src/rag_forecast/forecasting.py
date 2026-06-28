from __future__ import annotations

import asyncio
import json
import os
import random
import re
from typing import Any

from anthropic import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncAnthropic,
    InternalServerError,
    RateLimitError,
)

from .cache import JsonCache, cache_namespace
from .config import Config
from .data import ResolvedQuestion
from .prompts import (
    SYSTEM_POSTERIOR,
    SYSTEM_PRIOR,
    render_evidence,
    render_question,
)
from .rate_limiter import (
    AsyncRateLimiter,
    Reservations,
    estimate_input_tokens,
    parse_retry_after,
)


class ForecastClient:
    def __init__(
        self, cfg: Config, limiter: AsyncRateLimiter | None = None
    ) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.cfg = cfg
        self.client = AsyncAnthropic(
            api_key=api_key, max_retries=cfg.llm_sdk_max_retries
        )
        self.cache = JsonCache(cfg.cache_dir)
        self.limiter = limiter or AsyncRateLimiter(
            requests_per_minute=cfg.requests_per_minute,
            input_tokens_per_minute=cfg.input_tokens_per_minute,
            output_tokens_per_minute=cfg.output_tokens_per_minute,
        )

    async def _call(self, system: str, user: str, date: str) -> dict[str, Any]:
        payload = {
            "model": self.cfg.model,
            "temperature": self.cfg.temperature,
            "max_tokens": self.cfg.max_tokens,
            "system": system,
            "user": user,
        }
        namespace = cache_namespace(date, "prompt", self.cfg.model)
        cached = self.cache.get(payload, namespace=namespace)
        if cached is not None:
            return cached

        in_est = estimate_input_tokens(system, user)
        out_est = self.cfg.max_tokens

        msg = await self._send_with_retry(system, user, in_est, out_est)

        text = "".join(
            b.text for b in msg.content if getattr(b, "type", "") == "text"
        )
        parsed = _parse_json(text)
        value = {"raw": text, **parsed}
        self.cache.put(payload, value, namespace=namespace)
        return value

    async def _send_with_retry(
        self, system: str, user: str, in_est: int, out_est: int
    ):
        attempts = self.cfg.llm_max_retries + 1
        last_err: Exception | None = None
        for attempt in range(attempts):
            reservations = await self.limiter.acquire(in_est, out_est)
            try:
                msg = await self.client.messages.create(
                    model=self.cfg.model,
                    temperature=self.cfg.temperature,
                    max_tokens=self.cfg.max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
            except RateLimitError as e:
                # SDK already retried internally; the server is still saying
                # "slow down". Cool the limiter for the full retry-after window
                # so no other in-flight task fires another request meanwhile.
                last_err = e
                cooldown = parse_retry_after(
                    _headers(e), default=_backoff_seconds(attempt, base=5.0)
                )
                await self.limiter.penalize(cooldown)
                if attempt == attempts - 1:
                    break
                await asyncio.sleep(cooldown)
                continue
            except (APIConnectionError, APITimeoutError, InternalServerError) as e:
                last_err = e
                if attempt == attempts - 1:
                    break
                await asyncio.sleep(_backoff_seconds(attempt, base=1.0))
                continue
            except APIStatusError as e:
                last_err = e
                # Retry other transient server errors; bail on 4xx.
                if e.status_code < 500 or attempt == attempts - 1:
                    break
                await asyncio.sleep(_backoff_seconds(attempt, base=1.0))
                continue

            in_actual = int(getattr(msg.usage, "input_tokens", 0) or 0)
            out_actual = int(getattr(msg.usage, "output_tokens", 0) or 0)
            await self.limiter.commit(
                reservations,
                input_actual=in_actual,
                output_actual=out_actual,
            )
            return msg

        raise RuntimeError(
            f"LLM call failed after {attempts} attempt(s): {last_err}"
        ) from last_err

    async def estimate_p_h(self, q: ResolvedQuestion) -> dict[str, Any]:
        return await self._call(SYSTEM_PRIOR, render_question(q), q.question_set_date)

    async def estimate_p_h_given_e(
        self, q: ResolvedQuestion, evidence: list[dict[str, Any]]
    ) -> dict[str, Any]:
        user = render_question(q) + "\n\nEvidence:\n" + render_evidence(evidence)
        return await self._call(SYSTEM_POSTERIOR, user, q.question_set_date)


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_json(text: str) -> dict[str, Any]:
    match = _JSON_RE.search(text)
    if not match:
        raise ValueError(f"no JSON object in model output: {text!r}")
    obj = json.loads(match.group(0))
    p = obj.get("probability")
    if not isinstance(p, (int, float)):
        raise ValueError(f"probability missing or non-numeric: {obj!r}")
    p = float(p)
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"probability out of range: {p}")
    return {"probability": p, "reasoning": obj.get("reasoning", "")}


def _backoff_seconds(attempt: int, *, base: float, cap: float = 60.0) -> float:
    """Exponential backoff with jitter."""
    raw = base * (2 ** attempt)
    return min(cap, raw) * (0.5 + random.random() * 0.5)


def _headers(exc: BaseException) -> object | None:
    response = getattr(exc, "response", None)
    return getattr(response, "headers", None) if response is not None else None
