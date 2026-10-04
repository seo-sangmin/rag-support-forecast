from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from rag_forecast.metrics import bootstrap_ci, spearman  # noqa: E402

CI_CONFIDENCE = 0.95
CI_RESAMPLES = 10_000
CI_SEED = 0


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
    rho, p = spearman(df["abs_z"].tolist(), df["brier_delta"].tolist())
    ci_kwargs = {"confidence": CI_CONFIDENCE, "n_resamples": CI_RESAMPLES, "seed": CI_SEED}
    brier_delta_ci = bootstrap_ci([df["brier_delta"]], np.mean, **ci_kwargs)
    rho_ci = bootstrap_ci(
        [df["abs_z"], df["brier_delta"]], lambda x, y: spearman(x, y)[0], **ci_kwargs
    )

    summary = {
        "n": n,
        "mean_brier_h": float(df["brier_h"].mean()) if n else None,
        "mean_brier_he": float(df["brier_he"].mean()) if n else None,
        "mean_brier_delta": float(df["brier_delta"].mean()) if n else None,
        "mean_brier_delta_ci": list(brier_delta_ci) if n else None,
        "frac_brier_improved": float((df["brier_delta"] > 0).mean()) if n else None,
        "mean_abs_z": float(df["abs_z"].mean()) if n else None,
        "frac_z_positive": float((df["z"] > 0).mean()) if n else None,
        "spearman_abs_z_vs_brier_delta": {"rho": rho, "p_value": p, "ci": list(rho_ci)},
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
