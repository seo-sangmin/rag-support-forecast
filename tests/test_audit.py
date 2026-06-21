from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_forecast.audit import audit_evidence_leakage
from rag_forecast.cache import JsonCache
from rag_forecast.config import Config
from rag_forecast.data import ResolvedQuestion
from rag_forecast.retrieval import build_search_payload

FREEZE = datetime(2025, 10, 16, tzinfo=timezone.utc)


def _question(qid: str = "q1", question: str = "Will it rain?") -> ResolvedQuestion:
    return ResolvedQuestion(
        id=qid,
        source="manifold",
        question=question,
        background="",
        resolution_criteria="",
        freeze_datetime=FREEZE,
        freeze_value=None,
        resolution_date="2025-12-01",
        outcome=1.0,
    )


def _article(published_date: str, title: str = "t") -> dict:
    return {
        "title": title,
        "url": "https://example.com",
        "content": "c",
        "published_date": published_date,
        "source_id": "src",
    }


def _seed(cfg: Config, q: ResolvedQuestion, articles: list[dict]) -> None:
    # Round-trips through the real cache + payload code, so the audit finds it
    # exactly as it would find evidence written by a real run.
    JsonCache(cfg.cache_dir / "asknews").put(build_search_payload(q, cfg), articles)


def test_clean_evidence_passes(tmp_path: Path) -> None:
    cfg = Config(cache_dir=tmp_path)
    q = _question()
    _seed(
        cfg,
        q,
        [_article("2025-10-01T12:00:00+00:00"), _article("2025-09-15T00:00:00+00:00")],
    )
    summary = audit_evidence_leakage([q], cfg)
    assert summary["ok"] is True
    assert summary["n_violations"] == 0
    assert summary["n_cached"] == 1
    assert summary["n_articles_checked"] == 2
    assert summary["evidence_after_freeze"] == []


def test_article_after_freeze_flagged(tmp_path: Path) -> None:
    cfg = Config(cache_dir=tmp_path)
    q = _question()
    _seed(
        cfg,
        q,
        [_article("2025-10-01T00:00:00+00:00"), _article("2025-10-20T00:00:00+00:00")],
    )
    summary = audit_evidence_leakage([q], cfg)
    assert summary["ok"] is False
    assert summary["n_violations"] == 1
    v = summary["evidence_after_freeze"][0]
    assert v["id"] == "q1"
    assert v["published_date"] == "2025-10-20T00:00:00+00:00"


def test_uncached_question_skipped(tmp_path: Path) -> None:
    cfg = Config(cache_dir=tmp_path)
    q = _question()  # nothing seeded for it
    summary = audit_evidence_leakage([q], cfg)
    assert summary["ok"] is True
    assert summary["n_cached"] == 0
    assert summary["n_uncached"] == 1
    assert summary["n_articles_checked"] == 0


def test_missing_published_date_skipped(tmp_path: Path) -> None:
    cfg = Config(cache_dir=tmp_path)
    q = _question()
    _seed(cfg, q, [_article(""), _article("2025-10-05T00:00:00+00:00")])
    summary = audit_evidence_leakage([q], cfg)
    assert summary["ok"] is True
    assert summary["n_articles_checked"] == 1  # blank-date article is skipped


def test_no_questions(tmp_path: Path) -> None:
    cfg = Config(cache_dir=tmp_path)
    summary = audit_evidence_leakage([], cfg)
    assert summary["ok"] is True
    assert summary["n_questions"] == 0
    assert summary["n_cached"] == 0
