from __future__ import annotations

from typing import Any

from .cache import JsonCache, cache_namespace
from .config import Config
from .data import ResolvedQuestion, _parse_dt
from .retrieval import ASKNEWS_BACKEND, build_search_payload


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
    evidence are counted in ``n_uncached`` and skipped. The audit fails closed on
    provenance it cannot verify: an article whose ``published_date`` is missing or
    unparseable cannot be proven to predate the freeze, so it is reported in
    ``evidence_unverifiable`` (with a ``reason``) and counts against ``ok`` rather
    than being silently skipped.
    """
    cache = JsonCache(cfg.cache_dir)
    violations: list[dict[str, Any]] = []
    unverifiable: list[dict[str, Any]] = []
    n_cached = 0
    n_uncached = 0
    n_articles_checked = 0
    for q in questions:
        namespace = cache_namespace(
            q.question_set_date, "retrieval", ASKNEWS_BACKEND
        )
        evidence = cache.get(build_search_payload(q, cfg), namespace=namespace)
        if evidence is None:
            n_uncached += 1
            continue
        n_cached += 1
        for article in evidence:
            published = article.get("published_date")
            entry = {
                "id": q.id,
                "source": q.source,
                "published_date": published,
                "freeze_datetime": q.freeze_datetime.isoformat(),
                "title": article.get("title", ""),
                "url": article.get("url", ""),
            }
            if not isinstance(published, str) or not published:
                unverifiable.append({**entry, "reason": "missing"})
                continue
            try:
                published_dt = _parse_dt(published)
            except ValueError:
                unverifiable.append({**entry, "reason": "unparseable"})
                continue
            n_articles_checked += 1
            if published_dt > q.freeze_datetime:
                violations.append(entry)
    return {
        "n_questions": len(questions),
        "n_cached": n_cached,
        "n_uncached": n_uncached,
        "n_articles_checked": n_articles_checked,
        "n_violations": len(violations),
        "n_unverifiable": len(unverifiable),
        "ok": not violations and not unverifiable,
        "evidence_after_freeze": violations,
        "evidence_unverifiable": unverifiable,
    }
