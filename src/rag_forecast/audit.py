from __future__ import annotations

from typing import Any

from .cache import JsonCache
from .config import Config
from .data import ResolvedQuestion, _parse_dt
from .retrieval import build_search_payload


def audit_evidence_leakage(
    questions: list[ResolvedQuestion], cfg: Config
) -> dict[str, Any]:
    """Flag cached AskNews evidence published after a question's freeze.

    Retrieval bounds the AskNews search to ``end_timestamp = freeze_datetime``
    (see ``retrieval.build_search_payload``), so no retrieved article should be
    published after the forecast was frozen. This audit verifies that held: for
    each question it looks up the evidence cached for its retrieval payload and
    flags any article whose ``published_date`` is later than the question's
    ``freeze_datetime``.

    Reads the cache only -- it never calls AskNews. Questions with no cached
    evidence are counted in ``n_uncached`` and skipped; articles with a missing
    or unparseable ``published_date`` are skipped as well.
    """
    cache = JsonCache(cfg.cache_dir / "asknews")
    violations: list[dict[str, Any]] = []
    n_cached = 0
    n_uncached = 0
    n_articles_checked = 0
    for q in questions:
        evidence = cache.get(build_search_payload(q, cfg))
        if evidence is None:
            n_uncached += 1
            continue
        n_cached += 1
        for article in evidence:
            published = article.get("published_date")
            if not isinstance(published, str) or not published:
                continue
            try:
                published_dt = _parse_dt(published)
            except ValueError:
                continue
            n_articles_checked += 1
            if published_dt > q.freeze_datetime:
                violations.append(
                    {
                        "id": q.id,
                        "source": q.source,
                        "published_date": published,
                        "freeze_datetime": q.freeze_datetime.isoformat(),
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                    }
                )
    return {
        "n_questions": len(questions),
        "n_cached": n_cached,
        "n_uncached": n_uncached,
        "n_articles_checked": n_articles_checked,
        "n_violations": len(violations),
        "ok": not violations,
        "evidence_after_freeze": violations,
    }
