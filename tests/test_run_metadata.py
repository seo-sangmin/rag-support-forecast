from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_forecast import pipeline
from rag_forecast.config import Config
from rag_forecast.data import ResolvedQuestion


def _q(qid: str, source: str = "manifold") -> ResolvedQuestion:
    return ResolvedQuestion(
        id=qid,
        source=source,
        question=f"Will {qid} happen?",
        background="",
        resolution_criteria="",
        freeze_datetime=datetime(2025, 10, 16, tzinfo=timezone.utc),
        freeze_value=None,
        resolution_date="2025-12-01",
        outcome=1.0,
    )


def _ids(*questions: ResolvedQuestion) -> list[dict[str, str]]:
    return [{"id": q.id, "source": q.source} for q in questions]


def _metadata(out: Path) -> dict:
    return json.loads(out.with_suffix(".meta.json").read_text())


def _resume_csv(path: Path, q: ResolvedQuestion) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "source", "p_h"])
        writer.writeheader()
        writer.writerow({"id": q.id, "source": q.source, "p_h": "0.123"})


def _mock_clients(
    monkeypatch: pytest.MonkeyPatch,
    *,
    inspect_metadata: Callable[[], None] = lambda: None,
    retrieval_errors: tuple[str, ...] = (),
    forecast_errors: tuple[str, ...] = (),
) -> list[tuple[str, str | None]]:
    calls: list[tuple[str, str | None]] = []

    def called(stage: str, q: ResolvedQuestion | None = None) -> None:
        inspect_metadata()
        calls.append((stage, q.id if q else None))

    class Forecaster:
        def __init__(self, cfg: Config) -> None:
            called("forecast_init")

        async def estimate_p_h(self, q: ResolvedQuestion) -> dict:
            called("prior", q)
            return {"probability": 0.4, "reasoning": "Prior explanation"}

        async def estimate_p_h_given_e(self, q: ResolvedQuestion, evidence: list) -> dict:
            called("posterior", q)
            if q.id in forecast_errors:
                raise RuntimeError("forecast failed")
            return {"probability": 0.6, "reasoning": "Posterior explanation"}

    class Retriever:
        def __init__(self, cfg: Config) -> None:
            called("retrieval_init")

        async def retrieve(self, q: ResolvedQuestion) -> list[dict]:
            called("retrieve", q)
            if q.id in retrieval_errors:
                raise RuntimeError("retrieval failed")
            return []

    monkeypatch.setattr(pipeline, "ForecastClient", Forecaster)
    monkeypatch.setattr(pipeline, "AskNewsRetriever", Retriever)
    return calls


async def test_metadata_records_seeded_selection_and_settings_before_clients(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = Config(
        question_set_dates=("2025-10-26", "2025-11-02"),
        model="custom-model",
        temperature=0.25,
        max_tokens=2048,
        lookback_days=30,
        asknews_n_articles=4,
        asknews_method="kw",
        asknews_snippet_chars=500,
    )
    questions = [_q("same"), _q("same", "fred")] + [_q(f"q{i}") for i in range(1, 6)]
    pools = dict(zip(cfg.question_set_dates, [questions[:3], questions[3:]]))
    monkeypatch.setattr(pipeline, "load_resolved_questions", lambda date, cfg: pools[date])
    parents = [tmp_path / "first.csv", tmp_path / "second.csv"]
    _resume_csv(parents[0], questions[0])
    _resume_csv(parents[1], questions[2])
    out = tmp_path / "new_directory" / "rerun.csv"
    # Seed 1 samples q2, same/fred, q5 after excluding both resumed pairs.
    selected = _ids(questions[3], questions[1], questions[6])
    expected = {
        "seed": 1,
        "random": True,
        "max_questions": 3,
        "question_sets": list(cfg.question_set_dates),
        "resume_from": [str(p) for p in parents],
        "model": "custom-model",
        "temperature": 0.25,
        "max_tokens": 2048,
        "lookback_days": 30,
        "asknews_n_articles": 4,
        "asknews_method": "kw",
        "asknews_snippet_chars": 500,
        "selected_question_ids": selected,
        "complete": False,
        "missing_question_ids": selected,
    }

    def inspect_metadata() -> None:
        assert _metadata(out) == expected
        assert not out.exists()

    calls = _mock_clients(monkeypatch, inspect_metadata=inspect_metadata)
    count = await pipeline.run(
        cfg, 3, out, random_sample=True, seed=1, resume_from=parents
    )

    assert count == 3
    assert len(calls) == 2 + 3 * 3  # Both constructors, retrieval, prior, posterior.
    assert _metadata(out) == {**expected, "complete": True, "missing_question_ids": []}
    with out.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert [(r["id"], r["source"], r["p_h"]) for r in rows[:2]] == [
        ("same", "manifold", "0.123"),
        ("q1", "manifold", "0.123"),
    ]
    assert {(r["id"], r["source"]) for r in rows[2:]} == {
        (q["id"], q["source"]) for q in selected
    }
    assert all(r["reasoning_h"] == "Prior explanation" for r in rows[2:])


async def test_metadata_lists_only_questions_skipped_by_retrieval_or_forecasting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    questions = [_q("success"), _q("retrieval_error"), _q("forecast_error")]
    monkeypatch.setattr(pipeline, "load_resolved_questions", lambda date, cfg: questions)
    calls = _mock_clients(
        monkeypatch,
        retrieval_errors=("retrieval_error",),
        forecast_errors=("forecast_error",),
    )
    out = tmp_path / "incomplete.csv"

    assert await pipeline.run(Config(), None, out) == 1

    meta = _metadata(out)
    assert meta["selected_question_ids"] == _ids(*questions)
    assert meta["missing_question_ids"] == _ids(*questions[1:])
    assert meta["complete"] is False
    assert meta["seed"] == 0
    assert meta["random"] is False
    assert meta["max_questions"] is None
    assert meta["resume_from"] == []
    assert ("prior", "retrieval_error") not in calls
    with out.open(newline="") as f:
        assert [row["id"] for row in csv.DictReader(f)] == ["success"]


@pytest.mark.parametrize("failure_stage", ["constructor", "csv_write"])
async def test_metadata_remains_incomplete_when_run_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_stage: str
) -> None:
    question = _q("q1")
    monkeypatch.setattr(pipeline, "load_resolved_questions", lambda date, cfg: [question])
    _mock_clients(monkeypatch)
    out = tmp_path / "failed.csv"

    def fail(*args: object) -> None:
        assert _metadata(out)["complete"] is False
        raise RuntimeError("run interrupted")

    monkeypatch.setattr(
        pipeline,
        "ForecastClient" if failure_stage == "constructor" else "_write_combined_csv",
        fail,
    )
    with pytest.raises(RuntimeError, match="run interrupted"):
        await pipeline.run(Config(), 1, out)

    meta = _metadata(out)
    assert meta["complete"] is False
    assert meta["selected_question_ids"] == _ids(question)
    assert meta["missing_question_ids"] == _ids(question)
    assert not out.exists()


async def test_metadata_marks_no_remaining_questions_complete_without_clients(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    question = _q("q1")
    monkeypatch.setattr(pipeline, "load_resolved_questions", lambda date, cfg: [question])
    prior = tmp_path / "prior.csv"
    _resume_csv(prior, question)
    out = tmp_path / "copy.csv"

    def unexpected_client(cfg: Config) -> None:
        pytest.fail("No service client is needed when there are no new questions")

    monkeypatch.setattr(pipeline, "ForecastClient", unexpected_client)
    monkeypatch.setattr(pipeline, "AskNewsRetriever", unexpected_client)
    assert await pipeline.run(Config(), 3, out, resume_from=[prior]) == 0

    meta = _metadata(out)
    assert meta["selected_question_ids"] == []
    assert meta["missing_question_ids"] == []
    assert meta["complete"] is True
    assert meta["resume_from"] == [str(prior)]
    with out.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert (rows[0]["id"], rows[0]["p_h"]) == ("q1", "0.123")
