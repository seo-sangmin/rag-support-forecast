"""How many test dates H needs, from the family bootstrap of one results CSV.

For each measure, H's two gaps (λ̂ and c*) are redrawn with the same family resamples
as analyze_results.py. Their spread is scaled from this run's questions to PER_DATE
questions per test date. H passes only when both gaps pass, so its power is the chance
that both clear their bar. DETAILS.md ("Power and test dates") gives the steps.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import integrate, stats

import analyze_results as ar  # also puts src/ on sys.path
from rag_forecast.metrics import lambda_hat, shift_measures  # noqa: E402

GAPS = (0.25, 0.5, 0.75, 1.0, 1.5)  # true gap, the same for λ̂ and c*. 1.0 is the gap that matters
POWER = 0.80
PER_DATE = 380  # usable questions per ForecastBench date
MAX_DATES = 500


def both_below(a, b, r):
    """P(X < a and Y < b) for standard normal X and Y with correlation r."""
    return integrate.quad(lambda x: stats.norm.pdf(x) * stats.norm.cdf((b - r * x) / np.sqrt(1 - r * r)), -np.inf, a)[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Test dates H needs, from a per-question results CSV.")
    parser.add_argument("csv", type=Path, help="Path to per-question results CSV.")
    df = pd.read_csv(parser.parse_args().csv)
    family = np.where(
        df["source"].isin(ar.DATASET_SOURCES),
        df["source"] + "|" + df["resolution_date"].astype(str),
        df["source"] + "|" + df["id"].astype(str),
    )
    moved = (df["p_he"] != df["p_h"]).to_numpy()
    p, q, y, src = (df.loc[moved, c].to_numpy() for c in ("p_h", "p_he", "outcome", "source"))
    codes, fam = pd.factorize(src)[0], pd.factorize(family)[0][moved]
    # The same resamples as bootstrap_ci(..., seed=CI_SEED, clusters=fam) in analyze_results.py.
    rng = np.random.default_rng(ar.CI_SEED)
    pools = [np.flatnonzero(fam == c) for c in np.unique(fam)]
    draws = [np.concatenate([pools[j] for j in rng.integers(0, len(pools), size=len(pools))]) for _ in range(ar.CI_RESAMPLES)]
    z = stats.norm.ppf(1 - ar.H_ALPHA)  # a gap passes when it is more than z standard errors above 0

    print(f"Test dates H needs for {POWER:.0%} power, {PER_DATE} questions per date")
    print(f"{'measure':10}{'SE lam':>8}{'SE c*':>7}{'corr':>6} | gap" + "".join(f"{g:>6}" for g in GAPS))
    for name, m in shift_measures(p, q, ar.LOG_LOSS_EPS).items():
        lam, cst = (np.array([ar.half_gap(fn)(m[i], codes[i], p[i], q[i], y[i]) for i in draws]) for fn in (lambda_hat, ar.c_star))
        ok = np.isfinite(lam) & np.isfinite(cst)
        lam, cst = lam[ok], cst[ok]
        se_lam = np.std(lam, ddof=1)
        q1, q3 = np.percentile(cst, [25, 75])
        se_cst = (q3 - q1) / 1.349  # middle half: the few resamples at the c* cap would inflate the SD
        r = 2 * np.sin(np.pi * stats.spearmanr(lam, cst).statistic / 6)  # rank correlation to normal correlation
        needed = []
        for g in GAPS:
            for k in range(1, MAX_DATES + 1):
                shrink = np.sqrt(len(df) / (PER_DATE * k))  # standard errors shrink as 1/√(questions)
                if both_below(g / (se_lam * shrink) - z, g / (se_cst * shrink) - z, r) >= POWER:
                    break
            else:
                k = f">{MAX_DATES}"
            needed.append(k)
        print(f"{name:10}{se_lam:8.2f}{se_cst:7.2f}{r:6.2f} |    " + "".join(f"{k:>6}" for k in needed))


if __name__ == "__main__":
    main()
