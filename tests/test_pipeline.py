from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_forecast.config import Config
from rag_forecast.data import ResolvedQuestion
from rag_forecast.pipeline import (
    Row,
    _filter_questions,
    _forecast_all,
    _load_processed,
    _retrieve_all,
    _sample_questions,
    _write_combined_csv,
)


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


def _row(qid: str, source: str = "manifold") -> Row:
    return Row(
        id=qid,
        source=source,
        question=f"Will {qid} happen?",
        freeze_datetime="2025-10-16T00:00:00+00:00",
        resolution_date="2025-12-01",
        outcome=1.0,
        p_h=0.5,
        p_he=0.7,
        n_evidence=3,
        brier_h=0.25,
        brier_he=0.09,
        brier_delta=0.16,
        z=0.4,
        abs_z=0.4,
    )


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def test_load_processed_dedupes_across_files(tmp_path: Path) -> None:
    fields = ["id", "source", "p_h"]
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    _write_csv(
        a,
        [
            {"id": "q1", "source": "manifold", "p_h": "0.1"},
            {"id": "q2", "source": "fred", "p_h": "0.2"},
        ],
        fields,
    )
    _write_csv(
        b,
        [
            {"id": "q2", "source": "fred", "p_h": "0.99"},  # duplicate; ignored
            {"id": "q3", "source": "manifold", "p_h": "0.3"},
        ],
        fields,
    )

    keys, rows = _load_processed([a, b])
    assert keys == {("q1", "manifold"), ("q2", "fred"), ("q3", "manifold")}
    assert [(r["id"], r["source"], r["p_h"]) for r in rows] == [
        ("q1", "manifold", "0.1"),
        ("q2", "fred", "0.2"),
        ("q3", "manifold", "0.3"),
    ]


def test_load_processed_missing_columns_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    _write_csv(bad, [{"id": "q1", "p_h": "0.1"}], ["id", "p_h"])
    with pytest.raises(ValueError, match="missing required columns"):
        _load_processed([bad])


def test_load_processed_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        _load_processed([tmp_path / "does_not_exist.csv"])


def test_load_processed_empty_or_none_returns_empty() -> None:
    assert _load_processed(None) == (set(), [])
    assert _load_processed([]) == (set(), [])


def test_filter_questions_excludes_processed() -> None:
    qs = [_q(f"q{i}") for i in range(1, 6)]
    processed = {("q2", "manifold"), ("q4", "manifold")}
    remaining = _filter_questions(qs, processed)
    assert [q.id for q in remaining] == ["q1", "q3", "q5"]


def test_filter_questions_keys_on_id_and_source() -> None:
    qs = [_q("q1", "manifold"), _q("q1", "fred")]
    processed = {("q1", "manifold")}
    remaining = _filter_questions(qs, processed)
    assert [(q.id, q.source) for q in remaining] == [("q1", "fred")]


def test_sample_questions_is_seed_reproducible() -> None:
    qs = [_q(f"q{i}") for i in range(20)]
    a = _sample_questions(qs, 5, seed=42)
    b = _sample_questions(qs, 5, seed=42)
    c = _sample_questions(qs, 5, seed=43)
    assert [q.id for q in a] == [q.id for q in b]
    # different seeds shouldn't match on a pool of 20 (probability ~1/15504)
    assert [q.id for q in a] != [q.id for q in c]
    # all 5 are distinct and from the input pool
    assert len({q.id for q in a}) == 5
    assert {q.id for q in a}.issubset({q.id for q in qs})


def test_sample_questions_clamps_to_pool() -> None:
    qs = [_q(f"q{i}") for i in range(3)]
    out = _sample_questions(qs, 10, seed=0)
    assert len(out) == 3
    assert {q.id for q in out} == {"q0", "q1", "q2"}


def test_write_combined_csv_unions_and_dedupes(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    prior = [
        {
            "id": "q1",
            "source": "manifold",
            "question": "Will q1 happen?",
            "freeze_datetime": "2025-10-16T00:00:00+00:00",
            "resolution_date": "2025-12-01",
            "outcome": "1.0",
            "p_h": "0.1",
            "p_he": "0.2",
            "n_evidence": "1",
            "brier_h": "0.81",
            "brier_he": "0.64",
            "brier_delta": "0.17",
            "z": "0.111",
            "abs_z": "0.111",
        }
    ]
    new = [_row("q1"), _row("q2")]  # q1 overlaps with prior; q2 is new

    _write_combined_csv(prior, new, out)

    with out.open(newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == list(Row.__annotations__.keys())
        result = list(reader)

    assert [(r["id"], r["source"]) for r in result] == [
        ("q1", "manifold"),
        ("q2", "manifold"),
    ]
    # prior wins on collision
    assert result[0]["p_h"] == "0.1"
    assert result[1]["p_h"] == "0.5"


def test_write_combined_csv_handles_schema_drift(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    # Prior CSV has an extra legacy column and is missing 'abs_z'.
    prior = [
        {
            "id": "q1",
            "source": "manifold",
            "question": "Will q1 happen?",
            "freeze_datetime": "2025-10-16T00:00:00+00:00",
            "resolution_date": "2025-12-01",
            "outcome": "1.0",
            "p_h": "0.1",
            "p_he": "0.2",
            "n_evidence": "1",
            "brier_h": "0.81",
            "brier_he": "0.64",
            "brier_delta": "0.17",
            "z": "0.111",
            "legacy_extra": "drop-me",
        }
    ]

    _write_combined_csv(prior, [_row("q2")], out)

    with out.open(newline="") as f:
        reader = csv.DictReader(f)
        result = list(reader)
        assert reader.fieldnames == list(Row.__annotations__.keys())
        assert "legacy_extra" not in (reader.fieldnames or [])
    assert result[0]["abs_z"] == ""  # missing prior column -> empty cell
    assert result[1]["abs_z"] == "0.4"


class _FakeRetriever:
    """Stand-in for AskNewsRetriever: canned results, optional per-id errors."""

    def __init__(
        self,
        results: dict[str, list[dict]] | None = None,
        errors: set[str] | None = None,
    ) -> None:
        self.results = results or {}
        self.errors = errors or set()

    async def retrieve(self, q: ResolvedQuestion) -> list[dict]:
        if q.id in self.errors:
            raise RuntimeError(f"retrieval boom: {q.id}")
        return self.results.get(q.id, [])


class _FakeForecaster:
    """Stand-in for ForecastClient: fixed probabilities, optional per-id errors."""

    def __init__(
        self,
        p_h: float = 0.5,
        p_he: float = 0.7,
        errors: set[str] | None = None,
    ) -> None:
        self.p_h = p_h
        self.p_he = p_he
        self.errors = errors or set()

    async def estimate_p_h(self, q: ResolvedQuestion) -> dict:
        if q.id in self.errors:
            raise RuntimeError(f"prior boom: {q.id}")
        return {"probability": self.p_h, "reasoning": ""}

    async def estimate_p_h_given_e(
        self, q: ResolvedQuestion, evidence: list[dict]
    ) -> dict:
        if q.id in self.errors:
            raise RuntimeError(f"posterior boom: {q.id}")
        return {"probability": self.p_he, "reasoning": ""}


async def test_retrieve_all_drops_errors_and_keeps_empty() -> None:
    qs = [_q("q1"), _q("q2"), _q("q3")]
    retriever = _FakeRetriever(
        results={"q1": [{"title": "a"}], "q3": []},
        errors={"q2"},
    )
    evidence = await _retrieve_all(qs, retriever, Config())

    # q2 errored -> dropped from the map; q3's empty list is kept.
    assert set(evidence) == {("q1", "manifold"), ("q3", "manifold")}
    assert evidence[("q1", "manifold")] == [{"title": "a"}]
    assert evidence[("q3", "manifold")] == []


async def test_forecast_all_skips_questions_without_evidence() -> None:
    qs = [_q("q1"), _q("q2")]  # q2 never retrieved
    evidence = {("q1", "manifold"): [{"title": "a"}]}
    rows = await _forecast_all(qs, evidence, _FakeForecaster(), Config())
    assert [r.id for r in rows] == ["q1"]


async def test_forecast_all_empty_evidence_still_produces_row() -> None:
    qs = [_q("q1")]
    evidence = {("q1", "manifold"): []}  # retrieved, just no articles
    rows = await _forecast_all(qs, evidence, _FakeForecaster(), Config())
    assert len(rows) == 1
    assert rows[0].n_evidence == 0


async def test_forecast_all_skips_row_on_prompt_error() -> None:
    qs = [_q("q1"), _q("q2")]
    evidence = {("q1", "manifold"): [{"t": 1}], ("q2", "manifold"): [{"t": 1}]}
    forecaster = _FakeForecaster(errors={"q2"})
    rows = await _forecast_all(qs, evidence, forecaster, Config())
    assert [r.id for r in rows] == ["q1"]


async def test_retrieve_then_forecast_end_to_end() -> None:
    qs = [_q("q1")]
    retriever = _FakeRetriever(results={"q1": [{"t": 1}, {"t": 2}]})
    evidence = await _retrieve_all(qs, retriever, Config())
    rows = await _forecast_all(
        qs, evidence, _FakeForecaster(p_h=0.5, p_he=0.7), Config()
    )

    assert len(rows) == 1
    r = rows[0]
    assert r.p_h == 0.5
    assert r.p_he == 0.7
    assert r.n_evidence == 2
    assert r.brier_h == pytest.approx(0.25)  # (0.5 - 1)^2
    assert r.brier_he == pytest.approx(0.09)  # (0.7 - 1)^2
    assert r.brier_delta == pytest.approx(0.16)
