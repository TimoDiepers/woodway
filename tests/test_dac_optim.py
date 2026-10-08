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


from nbs.dac_optim import build_and_solve, solve


def _mini():
    # two countries, flat kernel (1 Gt removed -> 1 mK cooling forever), 10 years
    n = 10
    k = np.triu(np.full((n, n), -1e-3))
    eta = np.array([[0.9] * n, [0.5] * n])
    return k, eta


def test_mini_uses_better_country_first():
    k, eta = _mini()
    gap = np.full(10, 2e-3)      # 2 mK from year 0 on: 2.22 Gt in country 0 at eta 0.9
    ok, x = build_and_solve(eta, k, gap, storage=np.array([5.0, 5.0]), x_from=0, growth=10.0, start_2030=None)
    assert ok
    assert x[1].sum() == pytest.approx(0.0, abs=1e-9)
    assert x[0].sum() == pytest.approx(2e-3 / 1e-3 / 0.9, rel=1e-6)


def test_mini_storage_forces_second_country():
    k, eta = _mini()
    gap = np.full(10, 2e-3)
    ok, x = build_and_solve(eta, k, gap, storage=np.array([1.0, 5.0]), x_from=0, growth=10.0, start_2030=None)
    assert ok
    assert x[0].sum() == pytest.approx(1.0, rel=1e-6)
    assert x[1].sum() > 0


def test_mini_infeasible_reports_false():
    k, eta = _mini()
    ok, _ = build_and_solve(eta, k, np.full(10, 1.0), storage=np.array([1.0, 1.0]), x_from=0, growth=10.0, start_2030=None)
    assert not ok


def test_negative_eta_never_used():
    k, eta = _mini()
    eta[0, :5] = -0.2
    ok, x = build_and_solve(eta, k, np.full(10, 1e-3), storage=np.array([5.0, 5.0]), x_from=5, growth=10.0, start_2030=None)
    assert ok
    assert np.allclose(x[0, :5], 0.0)


@pytest.fixture(scope="module")
def main_case():
    return solve()


def test_main_case_respects_constraints(main_case):
    from nbs.dac_storage import storage_by_country

    r = main_case
    x = np.array(r["x"])
    tot = x.sum(axis=0)
    y = np.array(r["jahre"])
    assert np.all(x >= -1e-9)
    assert tot[y == 2030][0] <= 0.0088 + 1e-9
    for i in range(1, len(y)):
        if y[i] > 2030:
            assert tot[i] <= 1.2 * tot[i - 1] + 1e-9
    s = storage_by_country("prudent")
    assert all(x[i].sum() <= s[c] + 1e-6 for i, c in enumerate(r["laender"]))


def test_main_case_closes_or_approaches(main_case):
    r = main_case
    assert r["status"] in ("geschlossen", "annaeherung")
    if r["status"] == "geschlossen":
        i = r["jahre"].index(r["jahr_x"])
        assert np.all(np.array(r["kuehlung_k"])[i:] >= np.array(r["luecke_k"])[i:] - 1e-9)


def test_slow_growth_still_returns():
    r = solve(growth=1.11)
    assert r["status"] in ("geschlossen", "annaeherung")
    assert np.all(np.isfinite(r["kuehlung_k"]))


def test_export_file_is_complete():
    import json
    from pathlib import Path

    d = json.loads((Path(__file__).resolve().parents[1] / "data" / "dac" / "optim.json").read_text())
    h = d["haupt"]
    assert len(h["region"]) == len(h["laender"])
    assert len(h["fair_kuehlung_k"]) == 74
    assert np.isfinite(d["fair_abweichung_2100_rel"])
    assert set(d["sens"]) == {"wachstum_11", "technisch", "median"}
