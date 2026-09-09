from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_forecast.config import Config
from rag_forecast.data import load_resolved_questions


def _write_fixtures(raw_dir: Path, date: str) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    questions = {
        "forecast_due_date": date,
        "question_set": f"{date}-llm.json",
        "questions": [
            {
                "id": "q1",
                "source": "manifold",
                "question": "Will X happen?",
                "resolution_criteria": "Resolves YES if X happens.",
                "background": "Some context.",
                "freeze_datetime": "2025-10-16T00:00:00+00:00",
                "freeze_datetime_value": 0.42,
            },
            {
                "id": "q2",
                "source": "fred",
                "question": "Will Y exceed threshold?",
                "resolution_criteria": "Resolves YES if Y > threshold.",
                "background": "",
                "freeze_datetime": "2025-10-16T00:00:00+00:00",
                "freeze_datetime_value": None,
            },
            {
                "id": "q3",
                "source": "manifold",
                "question": "Will Z drop?",
                "resolution_criteria": "",
                "background": "",
                "freeze_datetime": "2025-10-16T00:00:00+00:00",
                "freeze_datetime_value": 0.1,
            },
        ],
    }
    resolutions = {
        "forecast_due_date": date,
        "question_set": f"{date}-llm.json",
        "resolutions": [
            {
                "id": "q1",
                "source": "manifold",
                "direction": None,
                "resolution_date": "2025-12-01",
                "resolved_to": 1.0,
                "resolved": True,
            },
            {
                "id": "q2",
                "source": "fred",
                "direction": None,
                "resolution_date": "2025-12-15",
                "resolved_to": 0.0,
                "resolved": True,
            },
            # q3 is unresolved -> must be filtered out
            {
                "id": "q3",
                "source": "manifold",
                "direction": None,
                "resolution_date": None,
                "resolved_to": None,
                "resolved": False,
            },
        ],
    }
    (raw_dir / f"{date}-llm.json").write_text(json.dumps(questions))
    (raw_dir / f"{date}_resolution_set.json").write_text(json.dumps(resolutions))


def test_load_resolved_questions_filters_and_joins(tmp_path: Path) -> None:
    cfg = Config(raw_dir=tmp_path / "raw", cache_dir=tmp_path / "cache",
                 results_dir=tmp_path / "results")
    _write_fixtures(cfg.raw_dir, "2025-10-26")

    out = load_resolved_questions("2025-10-26", cfg)
    assert len(out) == 2
    by_id = {q.id: q for q in out}
    assert by_id["q1"].outcome == 1.0
    assert by_id["q1"].source == "manifold"
    assert by_id["q1"].freeze_value == 0.42
    assert by_id["q1"].question_set_date == "2025-10-26"
    assert by_id["q2"].outcome == 0.0
    assert "q3" not in by_id


@pytest.mark.parametrize(
    ("market_info", "expected"),
    [
        ({}, ""),
        ({"market_info_resolution_criteria": None}, ""),
        ({"market_info_resolution_criteria": ""}, ""),
        (
            {
                "market_info_resolution_criteria": (
                    "Only accounts held before January 1, 2025 count."
                )
            },
            "Only accounts held before January 1, 2025 count.",
        ),
    ],
)
def test_load_resolved_questions_includes_market_criteria(
    tmp_path: Path, market_info: dict, expected: str
) -> None:
    date = "2025-10-26"
    cfg = Config(raw_dir=tmp_path / "raw", cache_dir=tmp_path / "cache",
                 results_dir=tmp_path / "results")
    _write_fixtures(cfg.raw_dir, date)
    question_path = cfg.raw_dir / f"{date}-llm.json"
    questions = json.loads(question_path.read_text())
    questions["questions"][0].update(market_info)
    question_path.write_text(json.dumps(questions))

    question = next(q for q in load_resolved_questions(date, cfg) if q.id == "q1")

    assert question.market_info_resolution_criteria == expected
    assert question.resolution_criteria == "Resolves YES if X happens."
    assert question.background == "Some context."


def test_load_resolved_questions_keeps_earliest_resolution_date(tmp_path: Path) -> None:
    date = "2025-10-26"
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    questions = {
        "forecast_due_date": date,
        "question_set": f"{date}-llm.json",
        "questions": [
            {
                "id": "q1",
                "source": "manifold",
                "question": "Will X happen by {resolution_date}?",
                "resolution_criteria": "Resolves YES if X happens.",
                "market_info_resolution_criteria": (
                    "Forecast due {forecast_due_date}; resolves {resolution_date}."
                ),
                "background": "",
                "freeze_datetime": "2025-10-16T00:00:00+00:00",
                "freeze_datetime_value": 0.42,
            },
        ],
    }
    # Same (id, source) resolved at two horizons, out of order on purpose.
    resolutions = {
        "forecast_due_date": date,
        "question_set": f"{date}-llm.json",
        "resolutions": [
            {
                "id": "q1",
                "source": "manifold",
                "direction": None,
                "resolution_date": "2026-01-15",
                "resolved_to": 0.0,
                "resolved": True,
            },
            {
                "id": "q1",
                "source": "manifold",
                "direction": None,
                "resolution_date": "2025-12-01",
                "resolved_to": 1.0,
                "resolved": True,
            },
        ],
    }
    (raw_dir / f"{date}-llm.json").write_text(json.dumps(questions))
    (raw_dir / f"{date}_resolution_set.json").write_text(json.dumps(resolutions))

    cfg = Config(raw_dir=raw_dir, cache_dir=tmp_path / "cache",
                 results_dir=tmp_path / "results")
    out = load_resolved_questions(date, cfg)

    assert len(out) == 1
    rq = out[0]
    assert rq.resolution_date == "2025-12-01"
    assert rq.outcome == 1.0
    assert "2025-12-01" in rq.question
    assert rq.market_info_resolution_criteria == (
        "Forecast due 2025-10-26; resolves 2025-12-01."
    )
