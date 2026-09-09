import numpy as np
import pytest

from nbs.metrics import prob_warming, quantile_band, risk_premium, t_star

YEARS = np.arange(2025, 2035)


def test_t_star_is_the_year_after_the_last_sign_change():
    dt = np.array([1.0, 1.0, -1.0, 1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0])
    assert t_star(dt, YEARS) == 2029


def test_t_star_is_infinite_when_still_warming_at_the_end():
    assert t_star(np.ones(10), YEARS) == np.inf


def test_t_star_is_the_first_year_when_never_warming():
    assert t_star(-np.ones(10), YEARS) == 2025


def test_prob_warming_counts_members_above_zero():
    ens = np.array([[1.0] * 10, [-1.0] * 10, [1.0] * 10, [-1.0] * 10])
    assert prob_warming(ens, YEARS, 2030) == pytest.approx(0.5)


def test_risk_premium_is_positive_when_ensemble_warms_more():
    ens = np.full((5, 10), -0.1)
    det = np.full(10, -0.3)
    assert risk_premium(ens, det, YEARS, 2030) == pytest.approx(0.2)


def test_quantile_band_is_ordered():
    rng = np.random.default_rng(0)
    ens = rng.normal(size=(200, 10))
    lo, med, hi = quantile_band(ens)
    assert np.all(lo <= med)
    assert np.all(med <= hi)
    assert lo.shape == (10,)
