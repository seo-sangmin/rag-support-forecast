from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rag_forecast.audit import audit_evidence_leakage  # noqa: E402
from rag_forecast.config import Config  # noqa: E402
from rag_forecast.data import load_resolved_questions  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit cached AskNews evidence for articles published after "
        "each question's freeze_datetime, or with a missing/unparseable publish "
        "date (retrieval leakage). Reads the cache only; no AskNews calls."
    )
    parser.add_argument(
        "--question-sets",
        default="2025-10-26",
        help="Comma-separated ForecastBench question-set dates (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=60,
        help="AskNews window start offset; must match the run being audited so "
        "the cache keys line up.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Where to write the report JSON "
        "(default: data/results/leakage_<timestamp>.json).",
    )
    args = parser.parse_args()

    dates = tuple(d.strip() for d in args.question_sets.split(",") if d.strip())
    cfg = Config(question_set_dates=dates, lookback_days=args.lookback_days)

    questions = []
    for date in cfg.question_set_dates:
        questions.extend(load_resolved_questions(date, cfg))

    summary = audit_evidence_leakage(questions, cfg)

    out = args.out or cfg.results_dir / (
        f"leakage_{datetime.now(tz=timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {out}")
    sys.exit(0 if summary["ok"] else 1)


if __name__ == "__main__":
    main()
