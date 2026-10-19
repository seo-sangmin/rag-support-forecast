from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from rag_forecast.metrics import (  # noqa: E402
    best_log_scale,
    bootstrap_ci,
    lambda_hat,
    leave_one_source_out,
    log_loss,
    pearson,
    shift_measures,
    spearman,
    within_source_groups,
)

CI_CONFIDENCE = 0.95
CI_RESAMPLES = 10_000
CI_SEED = 0
LOG_LOSS_EPS = 1e-6
GROUPS = 4  # within-source groups per measure (SQ2, SQ3)
# Dataset questions sharing a source and resolution day are decided by one event (e.g.
# one week's market), so they form one family for the bootstrap; market questions don't.
DATASET_SOURCES = ("acled", "dbnomics", "fred", "wikipedia", "yfinance")


def brier_gain(p, q, y):
    return float(np.mean((p - y) ** 2 - (q - y) ** 2))


def log_gain(p, q, y):
    return float(np.mean(log_loss(p, y, LOG_LOSS_EPS) - log_loss(q, y, LOG_LOSS_EPS)))


def c_star(p, q, y):
    return best_log_scale(p, q, y, LOG_LOSS_EPS)[0]


def in_group(fn, g):
    """Bootstrap statistic: regroup within sources, then apply fn(p, q, y) to group g."""

    def stat(m, s, p, q, y):
        rows = within_source_groups(m, s, GROUPS) == g
        return fn(p[rows], q[rows], y[rows]) if rows.any() else float("nan")

    return stat


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a per-question results CSV.")
    parser.add_argument("csv", type=Path, help="Path to per-question results CSV.")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Where to write summary.json (default: alongside the input CSV).",
    )
    parser.add_argument(
        "--train-only",
        type=Path,
        nargs="+",
        default=[],
        help="Result CSVs whose (id, source) rows help choose the SQ3 cuts but are never tested.",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    n = len(df)
    family = np.where(
        df["source"].isin(DATASET_SOURCES),
        df["source"] + "|" + df["resolution_date"].astype(str),
        df["source"] + "|" + df["id"].astype(str),
    )
    families = pd.factorize(family)[0]
    ci_kwargs = {"confidence": CI_CONFIDENCE, "n_resamples": CI_RESAMPLES, "seed": CI_SEED, "clusters": families}
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

    # SQ2 (warrant) and SQ3 (decision) use only the questions whose forecast moved.
    train_only = {(str(r.id), r.source) for f in args.train_only for r in pd.read_csv(f).itertuples()}
    moved = (df["p_he"] != df["p_h"]).to_numpy()
    mv = df[moved]
    p, q, y, src = (mv[c].to_numpy() for c in ("p_h", "p_he", "outcome", "source"))
    testable = np.array([(str(i), s) not in train_only for i, s in zip(mv["id"], src)])
    codes = pd.factorize(src)[0]  # bootstrap_ci takes numbers, so sources go in as codes
    moved_ci = {**ci_kwargs, "clusters": families[moved]}

    # No CI per source: a dataset source on one date is a single family.
    warrant = {"by_source": {}}
    for s in np.unique(src):
        r = src == s
        warrant["by_source"][s] = {"n": int(r.sum()), "lambda_hat": lambda_hat(p[r], q[r], y[r])}
    moved_measures = shift_measures(p, q, LOG_LOSS_EPS)
    for m_name, m in moved_measures.items():
        groups = within_source_groups(m, src, GROUPS)
        cols = [m, codes, p, q, y]
        warrant[m_name] = {}
        for g in range(1, GROUPS + 1):
            r = groups == g
            lam, b_gain = lambda_hat(p[r], q[r], y[r]), brier_gain(p[r], q[r], y[r])
            c, l_avail = best_log_scale(p[r], q[r], y[r], LOG_LOSS_EPS)
            l_gain = log_gain(p[r], q[r], y[r])
            warrant[m_name][g] = {
                "n": int(r.sum()),
                "mean_delta_sq": float(np.mean((q[r] - p[r]) ** 2)),
                "brier": {
                    "achieved": b_gain,
                    "achieved_ci": list(bootstrap_ci(cols, in_group(brier_gain, g), **moved_ci)),
                    "lambda_hat": lam,
                    "lambda_hat_ci": list(bootstrap_ci(cols, in_group(lambda_hat, g), **moved_ci)),
                    "share": (2 * lam - 1) / lam**2 if b_gain > 0 else None,
                },
                "log_loss": {
                    "achieved": l_gain,
                    "achieved_ci": list(bootstrap_ci(cols, in_group(log_gain, g), **moved_ci)),
                    "c_star": c,
                    "c_star_ci": list(bootstrap_ci(cols, in_group(c_star, g), **moved_ci)),
                    "share": l_gain / l_avail if l_gain > 0 else None,
                },
            }

    decision = {}
    for out_name, gain in ((k, v[moved]) for k, v in outcomes.items()):
        decision[out_name] = {}
        for m_name, m in moved_measures.items():
            d, per_source, marks = leave_one_source_out(m, src, gain, testable, GROUPS)
            ci = bootstrap_ci(
                [m, codes, gain, testable],
                lambda m_, s_, g_, t_: leave_one_source_out(m_, s_, g_, t_ > 0.5, GROUPS)[0],
                **moved_ci,
            )
            groups = within_source_groups(m, src, GROUPS)
            decision[out_name][m_name] = {
                "D": d,
                "D_ci": list(ci),
                "n_tested": int(testable.sum()),
                "per_source": per_source,
                "keep_p_groups_by_round": marks,
                "keep_p_groups_all_data": [g for g in range(1, GROUPS + 1) if gain[groups == g].mean() < 0],
            }

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
        "correlations": correlations,
        "n_moved": int(moved.sum()),
        "warrant": warrant,
        "decision": decision,
        "ci_method": {
            "method": "percentile bootstrap resampling families with replacement; groups and "
            "leave-one-source-out recomputed per resample",
            "family": "dataset questions sharing a source and resolution date; each other question alone",
            "dataset_sources": list(DATASET_SOURCES),
            "groups_per_source": GROUPS,
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
