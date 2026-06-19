from __future__ import annotations

import os
import re
from datetime import timedelta
from typing import Any

from asknews_sdk import AsyncAskNewsSDK

from .cache import JsonCache
from .config import Config
from .data import ResolvedQuestion

_EG_SPLIT = re.compile(r"\n\s*\n\s*e\.g\.", re.IGNORECASE)


def _shorten_query(text: str, limit: int = 400) -> str:
    if len(text) <= limit:
        return text
    return _EG_SPLIT.split(text, maxsplit=1)[0].rstrip()


class AskNewsRetriever:
    def __init__(self, cfg: Config) -> None:
        api_key = os.environ.get("ASKNEWS_API_KEY")
        if not api_key:
            raise RuntimeError("ASKNEWS_API_KEY is not set")
        self.cfg = cfg
        self.client = AsyncAskNewsSDK(api_key=api_key)
        self.cache = JsonCache(cfg.cache_dir / "asknews")

    def _truncate(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        n = self.cfg.asknews_snippet_chars
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
        end = q.freeze_datetime
        start = end - timedelta(days=self.cfg.lookback_days)
        payload = {
            "query": _shorten_query(q.question),
            "start_timestamp": int(start.timestamp()),
            "end_timestamp": int(end.timestamp()),
            "n_articles": self.cfg.asknews_n_articles,
            "method": self.cfg.asknews_method,
        }
        cached = self.cache.get(payload)
        if cached is not None:
            return cached

        # historical=True searches the full archive rather than only the recent
        # hot window, and time_filter="pub_date" bounds results by publication
        # date, so evidence never postdates the question's freeze_datetime.
        response = await self.client.news.search_news(
            query=payload["query"],
            n_articles=payload["n_articles"],
            start_timestamp=payload["start_timestamp"],
            end_timestamp=payload["end_timestamp"],
            method=payload["method"],
            time_filter="pub_date",
            historical=True,
            return_type="dicts",
        )
        results = self._truncate(
            [
                {
                    "title": a.title,
                    "url": str(a.article_url),
                    "content": a.summary,
                    "published_date": a.pub_date.isoformat() if a.pub_date else "",
                    "source_id": a.source_id,
                }
                for a in (response.as_dicts or [])
            ]
        )
        self.cache.put(payload, results)
        return results
