from __future__ import annotations

from typing import Callable, Sequence

import numpy as np
from scipy import optimize, stats


def brier(p: float, outcome: float) -> float:
    """Brier score for a binary outcome in {0, 1}."""
    return (p - outcome) ** 2


def log_loss(p, outcome, eps: float = 1e-6):
    """Log loss -[y log p + (1 - y) log(1 - p)] for a binary outcome in {0, 1}.

    p is clipped to [eps, 1 - eps] so a forecast of exactly 0 or 1 scores a
    large finite loss instead of infinity. Works on scalars and numpy arrays.
    """
    p = np.clip(p, eps, 1.0 - eps)
    return -(outcome * np.log(p) + (1 - outcome) * np.log(1 - p))


def shift_measures(p_h, p_he, eps: float = 1e-6) -> dict[str, np.ndarray]:
    """Per-question belief-shift measures from P(H) = p and P(H|E) = q.

    delta_sq  (q - p)^2                   expected Brier gain / (2*lam - 1) if truth is p + lam*(q - p)
    kl        KL(q || p)                  expected log-loss gain if truth is q
    ur_brier  (q - p)(p + q - 1)          E_p[Brier(p)] - E_q[Brier(q)]
    ur_log    H(p) - H(q)                 E_p[LogLoss(p)] - E_q[LogLoss(q)]
    abs_z     |Crupi-Tentori Z|
    abs_ko    |(q - p) / (p + q - 2pq)|   |Kemeny-Oppenheim|

    kl, ur_log and abs_ko use p and q clipped to [eps, 1 - eps].
    """
    p = np.asarray(p_h, dtype=float)
    q = np.asarray(p_he, dtype=float)
    pc, qc = np.clip(p, eps, 1.0 - eps), np.clip(q, eps, 1.0 - eps)

    def neg_entropy(r):
        return r * np.log(r) + (1 - r) * np.log(1 - r)

    return {
        "delta_sq": (q - p) ** 2,
        "kl": qc * np.log(qc / pc) + (1 - qc) * np.log((1 - qc) / (1 - pc)),
        "ur_brier": (q - p) * (p + q - 1),
        "ur_log": neg_entropy(qc) - neg_entropy(pc),
        "abs_z": np.abs(np.vectorize(z_crupi_tentori)(p, q, eps)),
        "abs_ko": np.abs((qc - pc) / (pc + qc - 2 * pc * qc)),
    }


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


def lambda_hat(p, q, y) -> float:
    """Best single scale c for the moves under Brier: argmin_c sum (p + c(q - p) - y)^2.

    1 = the moves were the right size, < 1 too large, > 1 too small. The mean
    Brier gain of q over p is below 0 exactly when lambda_hat < 1/2.
    """
    p, q, y = (np.asarray(a, dtype=float) for a in (p, q, y))
    d = q - p
    return float(np.sum(d * (y - p)) / np.sum(d * d))


def best_log_scale(p, q, y, eps: float = 1e-6) -> tuple[float, float]:
    """Scale c* minimizing the mean log loss of p + c(q - p); returns (c*, mean log-loss gain over p).

    The mean log loss is convex in c, so c* < 1 means the moves were too large and
    c* > 1 too small. c is bounded so every scaled forecast stays in [eps, 1 - eps].
    """
    p, q, y = (np.asarray(a, dtype=float) for a in (p, q, y))
    d = q - p
    up, down = d > 0, d < 0
    lo = np.max(np.concatenate([(eps - p[up]) / d[up], (1 - eps - p[down]) / d[down]]))
    hi = np.min(np.concatenate([(1 - eps - p[up]) / d[up], (eps - p[down]) / d[down]]))

    def loss(c: float) -> float:
        return float(np.mean(log_loss(p + c * d, y, eps)))

    c = float(optimize.minimize_scalar(loss, bounds=(lo, hi), method="bounded").x)
    return c, loss(0.0) - loss(c)


def within_source_groups(measure, source, k: int = 4) -> np.ndarray:
    """Group 1..k per row: rank by measure within the row's own source, cut each source into k parts.

    Pooling group g across sources gives every group the same source mix. Tied
    measure values share a group.
    """
    measure, source = np.asarray(measure, dtype=float), np.asarray(source)
    groups = np.empty(len(measure), dtype=int)
    for s in np.unique(source):
        rows = source == s
        groups[rows] = np.ceil(k * stats.rankdata(measure[rows]) / rows.sum())
    return groups


def leave_one_source_out(measure, source, gain, testable, k: int = 4):
    """Test the keep-p rule on each source with marks chosen only from the other sources.

    Rows are grouped with within_source_groups (measure only, no outcomes). For each
    source s with testable rows, group g is marked "keep p" if the mean gain of the
    rows outside s in group g is below 0; the marks are then applied to the testable
    rows of s. Rows of s that are not testable are neither used to choose nor tested.

    gain is score(p) - score(q). Returns (D, per_source_D, marks), where D is the mean
    over tested rows of -gain where the rule keeps p and 0 where it uses q, so D > 0
    means the rule beats always using q.
    """
    measure, source, gain = (np.asarray(a) for a in (measure, source, gain))
    testable = np.asarray(testable, dtype=bool)
    groups = within_source_groups(measure, source, k)
    tested, per_source, marks = [], {}, {}
    for s in np.unique(source[testable]):
        train = source != s
        keep_p = [g for g in range(1, k + 1) if (gt := gain[train & (groups == g)]).size and gt.mean() < 0]
        test = testable & (source == s)
        contribution = np.where(np.isin(groups[test], keep_p), -gain[test], 0.0)
        tested.append(contribution)
        per_source[s], marks[s] = float(contribution.mean()), keep_p
    return float(np.concatenate(tested).mean()), per_source, marks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float]:
    """Spearman rank correlation; returns (rho, p_value)."""
    if len(xs) < 2:
        return float("nan"), float("nan")
    res = stats.spearmanr(xs, ys)
    return float(res.statistic), float(res.pvalue)


def pearson(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float]:
    """Pearson correlation; returns (r, p_value). The p-value assumes normal data."""
    if len(xs) < 2:
        return float("nan"), float("nan")
    res = stats.pearsonr(xs, ys)
    return float(res.statistic), float(res.pvalue)


def bootstrap_ci(
    columns: Sequence[Sequence[float]],
    statistic: Callable[..., float],
    confidence: float = 0.95,
    n_resamples: int = 10_000,
    seed: int = 0,
    strata: Sequence | None = None,
) -> tuple[float, float]:
    """Percentile bootstrap confidence interval for ``statistic``; returns (low, high).

    Each resample draws n rows with replacement and recomputes ``statistic``.
    The same row indices are used for every column, so paired values (a
    question's |Z| and its Brier delta) stay together. With ``strata`` (e.g.
    each row's source), rows are drawn within each stratum, so every resample
    keeps the same number of rows per stratum.

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
    pools = None if strata is None else [np.flatnonzero(np.asarray(strata) == s) for s in np.unique(strata)]
    estimates = np.empty(n_resamples)
    for i in range(n_resamples):
        if pools is None:
            idx = rng.integers(0, n, size=n)
        else:
            idx = np.concatenate([pool[rng.integers(0, pool.size, size=pool.size)] for pool in pools])
        estimates[i] = statistic(*(a[idx] for a in arrays))
    estimates = estimates[np.isfinite(estimates)]
    if estimates.size == 0:
        return float("nan"), float("nan")
    tail = 100 * (1 - confidence) / 2
    low, high = np.percentile(estimates, [tail, 100 - tail])
    return float(low), float(high)
