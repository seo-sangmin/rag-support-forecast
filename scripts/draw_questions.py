"""Draw question lists from ForecastBench files.

    python scripts/draw_questions.py exploration

redraws data/exploration/questions.csv (see data/exploration/README.md). It
needs internet: every ForecastBench file it reads is downloaded through the
repo's loader from one named version into a temporary folder, which is deleted
at the end. A part for the test list is added after the exploration.
"""

from __future__ import annotations

import argparse
import csv
import filecmp
import random
import sys
import tempfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag_forecast.config import Config  # noqa: E402
from rag_forecast.data import load_resolved_questions  # noqa: E402

# ForecastBench version (a commit of forecastbench-datasets, the nightly of
# 2026-11-15) that the exploration list is drawn from. It is named here instead
# of taken from Config so that the list is redrawn the same way after Config
# moves to the test's version.
EXPLORATION_VERSION = "fe2a07344bf835fc44356c8f497a7542e8a58f94"
# Sources whose questions come from datasets, not markets. serpapi is counted
# here although the analysis does not treat it as a dataset source yet.
DATASET_SOURCES = {"acled", "dbnomics", "fred", "wikipedia", "yfinance", "serpapi"}
# Test question sets: every 14 days from 2025-12-07 to 2026-09-27, except the
# exploration's 2026-03-15.
TEST_DATES = [str(date(2025, 12, 7) + timedelta(days=14 * k)) for k in range(22)]
TEST_DATES.remove("2026-03-15")
PILOT_RESULTS = REPO_ROOT / "data" / "results" / "run_20260914T104832Z.csv"

Row = tuple[str, str, str, str, str]  # question_set, id, source, kind, batch


def ids_by_source(question_set: str, cfg: Config) -> dict[str, list[str]]:
    """Ids of the set's resolved yes/no questions for each source, sorted as text."""
    out: dict[str, list[str]] = {}
    for q in load_resolved_questions(question_set, cfg):
        out.setdefault(q.source, []).append(q.id)
    return {s: sorted(ids) for s, ids in out.items()}


def draw_exploration() -> list[Row]:
    print(f"Downloading ForecastBench files from version {EXPLORATION_VERSION[:7]}…")
    with tempfile.TemporaryDirectory() as tmp:
        cfg = Config(raw_dir=Path(tmp), forecastbench_commit=EXPLORATION_VERSION)
        a = ids_by_source("2026-03-15", cfg)
        b = ids_by_source("2026-10-11", cfg)
        on_test = {
            (q.id, q.source)
            for d in TEST_DATES
            for q in load_resolved_questions(d, cfg)
            if q.source not in DATASET_SOURCES
        }
        # The run reads data/raw, so its copies must be these same files.
        for name in (
            "2026-03-15-llm.json",
            "2026-03-15_resolution_set.json",
            "2026-10-11-llm.json",
            "2026-10-11_resolution_set.json",
        ):
            if not filecmp.cmp(cfg.raw_dir / name, Config().raw_dir / name, shallow=False):
                sys.exit(f"data/raw/{name} differs from version {EXPLORATION_VERSION}")

    pilot = {(r["id"], r["source"]) for r in csv.DictReader(open(PILOT_RESULTS))}
    rng = random.Random(0)
    rows: list[Row] = []
    # 1. 2026-03-15: 15 dataset questions per source.
    for s in ("acled", "dbnomics", "fred", "wikipedia", "yfinance"):
        rows += [("2026-03-15", i, s, "dataset", "1") for i in rng.sample(a[s], 15)]
    # 2. 2026-03-15: all market questions, shuffled. The first 20 go to batch 1.
    markets = sorted((s, i) for s, ids in a.items() if s not in DATASET_SOURCES for i in ids)
    assert not {(i, s) for s, i in markets} & pilot, "a 2026-03-15 market was in the pilot"
    rng.shuffle(markets)
    rows += [
        ("2026-03-15", i, s, "market", "1" if n < 20 else "2")
        for n, (s, i) in enumerate(markets)
    ]
    # 3. 2026-10-11: 15 dataset questions per source (serpapi skipped).
    for s in ("acled", "dbnomics", "fred", "yfinance"):
        rows += [("2026-10-11", i, s, "dataset", "3") for i in rng.sample(b[s], 15)]
    # 4. 2026-10-11: 5 Kalshi questions that are usable on no test date.
    kalshi = sorted(i for i in b["kalshi"] if (i, "kalshi") not in on_test)
    rows += [("2026-10-11", i, "kalshi", "market", "3") for i in rng.sample(kalshi, 5)]
    return sorted(rows, key=lambda r: (r[4], r[0], r[3], r[2], r[1]))


def write_list(rows: list[Row], path: Path) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["question_set", "id", "source", "kind", "batch"])
        writer.writerows(rows)
    per_batch = ", ".join(f"batch {k}: {n}" for k, n in sorted(Counter(r[4] for r in rows).items()))
    print(f"Wrote {len(rows)} questions ({per_batch}) to {path.relative_to(REPO_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw a question list from ForecastBench files.")
    parser.add_argument("part", choices=["exploration"], help="which list to draw")
    parser.parse_args()
    write_list(draw_exploration(), REPO_ROOT / "data" / "exploration" / "questions.csv")


if __name__ == "__main__":
    main()
