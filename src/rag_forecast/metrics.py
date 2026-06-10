from __future__ import annotations

from typing import Sequence

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
