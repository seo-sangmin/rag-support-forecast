from __future__ import annotations

import asyncio
import os
import re
from datetime import timedelta
from typing import Any

_EG_SPLIT = re.compile(r"\n\s*\n\s*e\.g\.", re.IGNORECASE)


def _shorten_query(text: str, limit: int = 400) -> str:
    if len(text) <= limit:
        return text
    return _EG_SPLIT.split(text, maxsplit=1)[0].rstrip()

from tavily import TavilyClient

from .cache import JsonCache
from .config import Config
from .data import ResolvedQuestion


class TavilyRetriever:
    def __init__(self, cfg: Config) -> None:
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY is not set")
        self.cfg = cfg
        self.client = TavilyClient(api_key=api_key)
        self.cache = JsonCache(cfg.cache_dir / "tavily")

    def _truncate(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        n = self.cfg.tavily_snippet_chars
        out = []
        for r in results:
            r = dict(r)
            for k in ("content", "raw_content"):
                v = r.get(k)
                if isinstance(v, str) and len(v) > n:
                    r[k] = v[:n] + "…"
            out.append(r)
        return out

    async def retrieve(self, q: ResolvedQuestion) -> list[dict[str, Any]]:
        end = q.freeze_datetime.date()
        start = end - timedelta(days=self.cfg.lookback_days)
        payload = {
            "query": _shorten_query(q.question),
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "max_results": self.cfg.tavily_max_results,
            "search_depth": self.cfg.tavily_search_depth,
        }
        cached = self.cache.get(payload)
        if cached is not None:
            return cached

        def _call() -> dict[str, Any]:
            return self.client.search(
                query=payload["query"],
                start_date=payload["start_date"],
                end_date=payload["end_date"],
                max_results=payload["max_results"],
                search_depth=payload["search_depth"],
                include_raw_content="markdown",
            )

        response = await asyncio.to_thread(_call)
        results = self._truncate(response.get("results", []))
        self.cache.put(payload, results)
        return results
