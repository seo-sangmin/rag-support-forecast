from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_forecast.metrics import brier, spearman, z_crupi_tentori


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
