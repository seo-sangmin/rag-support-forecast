from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pytest

from rag_forecast.metrics import (
    bootstrap_ci,
    brier,
    log_loss,
    pearson,
    shift_measures,
    spearman,
    z_crupi_tentori,
)


def test_brier_extremes() -> None:
    assert brier(1.0, 1.0) == 0.0
    assert brier(0.0, 0.0) == 0.0
    assert brier(0.0, 1.0) == 1.0
    assert brier(1.0, 0.0) == 1.0
    assert math.isclose(brier(0.7, 1.0), 0.09)


def test_z_positive_branch() -> None:
    # P(H|E) > P(H): denominator is (1 - P(H))
    z = z_crupi_tentori(0.4, 0.7)
    assert math.isclose(z, (0.7 - 0.4) / (1 - 0.4), rel_tol=1e-6)


def test_z_negative_branch() -> None:
    # P(H|E) < P(H): denominator is P(H)
    z = z_crupi_tentori(0.6, 0.3)
    assert math.isclose(z, (0.3 - 0.6) / 0.6, rel_tol=1e-6)


def test_z_equal_is_zero() -> None:
    assert z_crupi_tentori(0.5, 0.5) == 0.0


def test_z_bounds() -> None:
    # Maximal positive confirmation: P(H|E) = 1, P(H) just above 0 -> Z -> +1
    assert math.isclose(z_crupi_tentori(0.0, 1.0), 1.0, rel_tol=1e-3)
    # Maximal negative: P(H|E) = 0, P(H) just below 1 -> Z -> -1
    assert math.isclose(z_crupi_tentori(1.0, 0.0), -1.0, rel_tol=1e-3)


def test_spearman_perfect() -> None:
    rho, p = spearman([1, 2, 3, 4, 5], [10, 20, 30, 40, 50])
    assert math.isclose(rho, 1.0)
    assert p < 0.05


def test_spearman_anticorrelated() -> None:
    rho, _ = spearman([1, 2, 3, 4], [4, 3, 2, 1])
    assert math.isclose(rho, -1.0)


def test_spearman_too_few() -> None:
    rho, p = spearman([1.0], [2.0])
    assert math.isnan(rho) and math.isnan(p)


def test_pearson_perfect() -> None:
    r, p = pearson([1, 2, 3, 4, 5], [10, 20, 30, 40, 50])
    assert math.isclose(r, 1.0)
    assert p < 0.05


def test_pearson_anticorrelated() -> None:
    r, _ = pearson([1, 2, 3, 4], [4, 3, 2, 1])
    assert math.isclose(r, -1.0)


def test_pearson_too_few() -> None:
    r, p = pearson([1.0], [2.0])
    assert math.isnan(r) and math.isnan(p)


def test_log_loss_values() -> None:
    assert math.isclose(log_loss(0.5, 1), math.log(2))
    assert math.isclose(log_loss(0.8, 0), -math.log(0.2))
    # A forecast of exactly 0 that resolves YES is clipped to 1e-6, not infinite.
    assert math.isclose(log_loss(0.0, 1), -math.log(1e-6))


def _expected(score, truth: float, r: float) -> float:
    """E[score(r, Y)] when Y ~ Bernoulli(truth)."""
    return truth * score(r, 1) + (1 - truth) * score(r, 0)


PQ_PAIRS = [(0.4, 0.7), (0.7, 0.4), (0.1, 0.3), (0.9, 0.95), (0.02, 0.5)]


@pytest.mark.parametrize("p, q", PQ_PAIRS)
def test_shift_measures_match_definitions(p: float, q: float) -> None:
    m = shift_measures(p, q)
    # Brier gain if the truth is t = p + lam*(q - p) equals (2*lam - 1) * delta_sq.
    lam = 0.8
    t = p + lam * (q - p)
    assert math.isclose(
        _expected(brier, t, p) - _expected(brier, t, q), (2 * lam - 1) * m["delta_sq"]
    )
    # Log-loss gain if the truth is q equals KL(q || p).
    assert math.isclose(_expected(log_loss, q, p) - _expected(log_loss, q, q), m["kl"])
    # Uncertainty reductions: E_p[S(p)] - E_q[S(q)].
    assert math.isclose(_expected(brier, p, p) - _expected(brier, q, q), m["ur_brier"])
    assert math.isclose(_expected(log_loss, p, p) - _expected(log_loss, q, q), m["ur_log"])
    assert math.isclose(m["abs_z"], abs(z_crupi_tentori(p, q)))
    # |KO| = tanh(|change in log-odds| / 2).
    logit = lambda r: math.log(r / (1 - r))  # noqa: E731
    assert math.isclose(m["abs_ko"], math.tanh(abs(logit(q) - logit(p)) / 2))


def test_shift_measures_ko_hand_value() -> None:
    assert math.isclose(shift_measures(0.4, 0.7)["abs_ko"], 0.3 / 0.54)


def test_shift_measures_unchanged_forecast_is_zero() -> None:
    for name, value in shift_measures(0.3, 0.3).items():
        assert value == pytest.approx(0.0, abs=1e-12), name


@pytest.mark.parametrize("p, q", [(0.0, 1.0), (1.0, 0.0), (0.0, 0.0), (1.0, 1.0), (0.0, 0.5)])
def test_shift_measures_finite_at_extremes(p: float, q: float) -> None:
    for name, value in shift_measures(p, q).items():
        assert np.isfinite(value), name


def test_shift_measures_on_arrays() -> None:
    p = [0.4, 0.7, 0.1]
    q = [0.7, 0.4, 0.3]
    m = shift_measures(p, q)
    for name, values in m.items():
        assert values.shape == (3,), name
        for i in range(3):
            assert math.isclose(values[i], shift_measures(p[i], q[i])[name]), name


def test_bootstrap_ci_mean_contains_sample_mean() -> None:
    values = [0.1, -0.2, 0.05, 0.3, -0.1, 0.0, 0.2, -0.05, 0.15, 0.1]
    low, high = bootstrap_ci([values], np.mean, n_resamples=2_000)
    assert low < float(np.mean(values)) < high


def test_bootstrap_ci_constant_data_is_a_point() -> None:
    low, high = bootstrap_ci([[0.4] * 10], np.mean, n_resamples=500)
    assert math.isclose(low, 0.4) and math.isclose(high, 0.4)


def test_bootstrap_ci_keeps_pairs_together() -> None:
    # If rows were resampled independently per column, rho would scatter around 0.
    xs = list(range(20))
    ys = [2 * x for x in xs]
    low, high = bootstrap_ci([xs, ys], lambda x, y: spearman(x, y)[0], n_resamples=500)
    assert math.isclose(low, 1.0) and math.isclose(high, 1.0)


def test_bootstrap_ci_same_seed_is_reproducible() -> None:
    values = [0.3, 0.1, 0.4, 0.1, 0.5, 0.9, 0.2, 0.6]
    first = bootstrap_ci([values], np.mean, n_resamples=500, seed=7)
    second = bootstrap_ci([values], np.mean, n_resamples=500, seed=7)
    assert first == second


def test_bootstrap_ci_too_few() -> None:
    low, high = bootstrap_ci([[1.0]], np.mean)
    assert math.isnan(low) and math.isnan(high)


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_bootstrap_ci_rejects_nonfinite_input(bad: float) -> None:
    xs = [0.1, 0.2, 0.3, 0.4, 0.5]
    ys = [0.5, bad, 0.3, 0.2, 0.1]
    with pytest.raises(ValueError, match="column 1"):
        bootstrap_ci([xs, ys], lambda x, y: spearman(x, y)[0], n_resamples=100)
