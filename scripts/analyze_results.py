from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from rag_forecast.metrics import bootstrap_ci, log_loss, pearson, shift_measures, spearman  # noqa: E402

CI_CONFIDENCE = 0.95
CI_RESAMPLES = 10_000
CI_SEED = 0
LOG_LOSS_EPS = 1e-6


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a per-question results CSV.")
    parser.add_argument("csv", type=Path, help="Path to per-question results CSV.")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Where to write summary.json (default: alongside the input CSV).",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    n = len(df)
    ci_kwargs = {"confidence": CI_CONFIDENCE, "n_resamples": CI_RESAMPLES, "seed": CI_SEED}
    brier_delta_ci = bootstrap_ci([df["brier_delta"]], np.mean, **ci_kwargs)
    log_loss_h = log_loss(df["p_h"].to_numpy(), df["outcome"].to_numpy(), LOG_LOSS_EPS)
    log_loss_he = log_loss(df["p_he"].to_numpy(), df["outcome"].to_numpy(), LOG_LOSS_EPS)
    log_loss_delta = log_loss_h - log_loss_he
    log_loss_delta_ci = bootstrap_ci([log_loss_delta], np.mean, **ci_kwargs)

    outcomes = {"brier_delta": df["brier_delta"].to_numpy(), "log_loss_delta": log_loss_delta}
    measures = shift_measures(df["p_h"], df["p_he"], LOG_LOSS_EPS)
    correlations = {}
    for out_name, y in outcomes.items():
        correlations[out_name] = {}
        for m_name, x in measures.items():
            cell = {}
            for method_name, method in [("pearson", pearson), ("spearman", spearman)]:
                estimate, p_value = method(x, y)
                ci = bootstrap_ci([x, y], lambda a, b: method(a, b)[0], **ci_kwargs)
                cell[method_name] = {"estimate": estimate, "p_value": p_value, "ci": list(ci)}
            correlations[out_name][m_name] = cell

    summary = {
        "n": n,
        "mean_brier_h": float(df["brier_h"].mean()) if n else None,
        "mean_brier_he": float(df["brier_he"].mean()) if n else None,
        "mean_brier_delta": float(df["brier_delta"].mean()) if n else None,
        "mean_brier_delta_ci": list(brier_delta_ci) if n else None,
        "frac_brier_improved": float((df["brier_delta"] > 0).mean()) if n else None,
        "mean_log_loss_h": float(log_loss_h.mean()) if n else None,
        "mean_log_loss_he": float(log_loss_he.mean()) if n else None,
        "mean_log_loss_delta": float(log_loss_delta.mean()) if n else None,
        "mean_log_loss_delta_ci": list(log_loss_delta_ci) if n else None,
        "log_loss_clip_eps": LOG_LOSS_EPS,
        "mean_abs_z": float(df["abs_z"].mean()) if n else None,
        "frac_z_positive": float((df["z"] > 0).mean()) if n else None,
        "correlations": correlations,
        "ci_method": {
            "method": "percentile bootstrap, resampling questions with replacement",
            "confidence": CI_CONFIDENCE,
            "n_resamples": CI_RESAMPLES,
            "seed": CI_SEED,
        },
    }

    out = args.out or args.csv.with_name(args.csv.stem + "_summary.json")
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
