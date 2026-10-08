"""Tests for nbs.dac_optim."""

import numpy as np
import pytest

from nbs.constants import YEARS
from nbs.dac_optim import eta_by_country, gap_series, removal_kernel_matrix


def test_kernel_is_causal_and_cooling():
    k = removal_kernel_matrix()
    assert k.shape == (75, 75)
    assert np.allclose(np.tril(k, -1), 0)  # K[y, t] = 0 for t < y
    assert np.all(k[0, 1:] < 0)


def test_kernel_matches_existing_horizon_kernel():
    from nbs.dac_compare import _removal_kernel  # K per t CO2 at T_END

    k = removal_kernel_matrix()
    assert k[:, -1] == pytest.approx(_removal_kernel() * 1e9, rel=1e-6)


def test_kernel_size_is_tcre_like():
    # 1 Gt removed in 2026: roughly -0.45 mK by 2100 (TCRE ~0.45 K / 1000 Gt)
    assert -1e-3 < removal_kernel_matrix()[0, -1] < -2e-4


def test_eta_countries_have_storage_and_cells():
    from nbs.dac_storage import storage_by_country

    countries, eta = eta_by_country()
    s = storage_by_country("prudent")
    assert eta.shape == (len(countries), 75)
    assert all(s[c] > 0 for c in countries)
    assert "CHE" not in countries  # prudent limit 0 (Iceland has 7 Mt, so it may stay)
    assert np.all(np.isfinite(eta))
    assert np.all(eta <= 1.0)


def test_eta_rises_with_cleaner_power():
    countries, eta = eta_by_country()
    assert np.median(eta[:, YEARS.tolist().index(2050)]) > np.median(eta[:, 0])


def test_best_decile_beats_median():
    _, best = eta_by_country(0.9)
    _, med = eta_by_country(0.5)
    assert np.all(best >= med - 1e-12)


def test_gap_matches_slide_25():
    g = gap_series()
    assert g.shape == (75,) and np.all(g >= 0)
    i = YEARS.tolist().index(2050)
    assert g[i] * 1000 == pytest.approx(323 - 14, abs=3)   # need minus trees, mK
