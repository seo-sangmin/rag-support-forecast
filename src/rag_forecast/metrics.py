from __future__ import annotations

from typing import Callable, Sequence

import numpy as np
from scipy import stats


def brier(p: float, outcome: float) -> float:
    """Brier score for a binary outcome in {0, 1}."""
    return (p - outcome) ** 2


def z_crupi_tentori(p_h: float, p_he: float, eps: float = 1e-6) -> float:
    """Crupi-Tentori Z confirmation measure.

    Z = (P(H|E) - P(H)) / (1 - P(H))   if P(H|E) >= P(H)
    Z = (P(H|E) - P(H)) / P(H)          otherwise

    P(H) is clipped to (eps, 1 - eps) to avoid division by zero.
    """
    p_h_c = min(max(p_h, eps), 1.0 - eps)
    if p_he >= p_h_c:
        return (p_he - p_h_c) / (1.0 - p_h_c)
    return (p_he - p_h_c) / p_h_c


def spearman(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float]:
    """Spearman rank correlation; returns (rho, p_value)."""
    if len(xs) < 2:
        return float("nan"), float("nan")
    res = stats.spearmanr(xs, ys)
    return float(res.statistic), float(res.pvalue)


def bootstrap_ci(
    columns: Sequence[Sequence[float]],
    statistic: Callable[..., float],
    confidence: float = 0.95,
    n_resamples: int = 10_000,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile bootstrap confidence interval for ``statistic``; returns (low, high).

    Each resample draws n rows with replacement and recomputes ``statistic``.
    The same row indices are used for every column, so paired values (a
    question's |Z| and its Brier delta) stay together.

    Raises ValueError if any input value is NaN or infinite; otherwise resamples
    that happen to skip the bad row would yield a CI for an undefined statistic.
    Resamples where the statistic is undefined (NaN, e.g. Spearman on constant
    input) are still dropped.
    """
    arrays = [np.asarray(c, dtype=float) for c in columns]
    for i, a in enumerate(arrays):
        if not np.isfinite(a).all():
            raise ValueError(f"bootstrap_ci column {i} contains NaN or infinite values")
    n = len(arrays[0])
    if n < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    estimates = np.empty(n_resamples)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        estimates[i] = statistic(*(a[idx] for a in arrays))
    estimates = estimates[np.isfinite(estimates)]
    if estimates.size == 0:
        return float("nan"), float("nan")
    tail = 100 * (1 - confidence) / 2
    low, high = np.percentile(estimates, [tail, 100 - tail])
    return float(low), float(high)
