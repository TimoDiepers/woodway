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
    # 1 Gt removed in 2026: about -0.34 mK by 2100 (TCRE-like, against a rising background)
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
        i = r["jahre"].index(r["ziel_jahr"])
        assert np.all(np.array(r["kuehlung_k"])[i:] >= np.array(r["luecke_k"])[i:] - 1e-9)


def test_slow_growth_still_returns():
    r = solve(growth=1.11)
    assert r["status"] in ("geschlossen", "annaeherung")
    assert np.all(np.isfinite(r["kuehlung_k"]))


def test_mini_min_peak_spreads_removal_evenly():
    # flat kernel, gap only in the last year: 9 mK at eta 0.9 needs 10 Gt in total, at best 1 Gt/a over 10 years
    k, eta = _mini()
    gap = np.zeros(10)
    gap[-1] = 9e-3
    ok, x = build_and_solve(eta[:1], k, gap, storage=np.array([50.0]), x_from=9, growth=10.0, start_2030=None,
                            objective="min_peak")
    assert ok
    assert x.sum(axis=0).max() == pytest.approx(1.0, rel=1e-4)
    assert x.sum() == pytest.approx(10.0, rel=1e-4)


def test_main_case_reaches_target_with_least_capacity(main_case):
    r = main_case
    assert r["ziel_jahr"] == 2100 and r["status"] == "geschlossen"
    tot = np.array(r["x"]).sum(axis=0)
    assert r["kapazitaet_gt"] == pytest.approx(tot.max(), rel=1e-6)
    assert 3.0 < r["kapazitaet_gt"] < 15.0


def test_capacity_falls_with_later_target():
    from nbs.dac_optim import capacity_by_target

    c = capacity_by_target((2090, 2100))
    assert c[0]["kapazitaet_gt"] > c[1]["kapazitaet_gt"]


def test_export_file_is_complete():
    import json
    from pathlib import Path

    d = json.loads((Path(__file__).resolve().parents[1] / "data" / "dac" / "optim.json").read_text())
    h = d["haupt"]
    assert len(h["region"]) == len(h["laender"])
    assert np.isfinite(d["fair_abweichung_2100_rel"])
    assert set(d["sens"]) == {"wachstum_11", "technisch", "median"}
    assert [c["ziel_jahr"] for c in d["ziel_kurve"]] == [2085, 2090, 2095, 2100]
    assert [p["strompfad"] for p in d["strompfade"]] == ["SSP2-NPi", "SSP2-NDC", "SSP2-PkBudg650"]
    assert all(len(p["eta_median"]) == 75 for p in d["strompfade"])
    assert 0.0 < d["fair_abweichung_2100_rel"] < 0.15
    assert len(h["fair_kuehlung_k"]) == 75


def test_mini_keep_running_never_shuts_down():
    k, eta = _mini()
    gap = np.zeros(10)
    gap[-1] = 9e-3
    ok, x = build_and_solve(eta[:1], k, gap, storage=np.array([50.0]), x_from=9, growth=10.0, start_2030=None,
                            objective="min_peak", keep_running=True)
    assert ok
    assert np.all(np.diff(x[0]) >= -1e-9)


def test_main_case_plants_keep_running(main_case):
    x = np.array(main_case["x"])
    assert np.all(np.diff(x, axis=1) >= -1e-7)


def test_pathway_changes_eta():
    from nbs.dac_optim import eta_by_country

    c1, e1 = eta_by_country(pathway="SSP2-NDC")
    c2, e2 = eta_by_country(pathway="SSP2-NPi")
    assert c1 == c2
    assert np.median(e2[:, 14]) < np.median(e1[:, 14])   # 2040: slower decarbonisation, lower net share


def test_fair_cooling_is_aligned_with_kernel():
    # a 1 Gt pulse in 2036 must give the same cooling on the LP year axis in both models
    from nbs.dac_optim import fair_cooling

    net = np.zeros(75)
    net[10] = 1.0
    f = fair_cooling(net)
    k = -removal_kernel_matrix()[10]
    assert f.shape == (75,)
    assert f[30] == pytest.approx(k[30], rel=0.05)
    assert abs(f[9]) < 1e-6 * abs(k[30])
    assert np.all(np.isnan(f[-2:]))  # FaIR's study axis (timebounds 2026..2099) ends before LP years 2099/2100


def test_target_year_out_of_range():
    with pytest.raises(ValueError):
        solve(ziel_jahr=2101)
