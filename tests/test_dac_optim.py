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


def test_gap_uses_the_current_tree_cooling():
    """The trees' share comes from the model's area series, not a frozen copy, so a model
    change (e.g. clouds) moves the gap."""
    import json

    from nbs.dac_optim import GAP_FILE
    from nbs.vergleich_figures import area_series

    need = np.array(json.loads(GAP_FILE.read_text())["need"]) / 1000.0
    trees = -np.array(area_series()["kuehlt"])
    np.testing.assert_allclose(gap_series(), np.maximum(0.0, need - trees))


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
    assert h["ziel"] == "co2" and h["co2_ziel_gt"] > 0
    assert len(d["wachstumsgrenze_gt"]) == 75 and d["wachstumsgrenze_gt"][4] == pytest.approx(0.0088)


def test_mini_keep_running_never_shuts_down():
    k, eta = _mini()
    gap = np.zeros(10)
    gap[-1] = 9e-3
    ok, x = build_and_solve(eta[:1], k, gap, storage=np.array([50.0]), x_from=9, growth=10.0, start_2030=None,
                            objective="min_peak", keep_running=True, life=None)
    assert ok
    assert np.all(np.diff(x[0]) >= -1e-9)


def test_builds_matrix_rebuilds_after_the_lifetime():
    from nbs.dac_optim import builds_matrix

    x = np.array([1.0, 2, 2, 2, 2, 0])
    assert builds_matrix(6, 3) @ x == pytest.approx([1, 1, 0, 1, 1, -2])   # shutting down at 5 would need b < 0
    assert builds_matrix(6, None) @ x == pytest.approx(np.r_[x[0], np.diff(x)])


def test_mini_plants_run_their_lifetime_then_may_retire():
    # removal needed only in years 0-2 (cooling counted per year): with a 3-year life plants may stop after year 2,
    # with a 2-year life a plant built in year 0 must not run into year 2 alone
    k = -1e-3 * np.eye(10)
    eta = np.array([[1.0] * 10])
    gap = np.r_[np.ones(3), np.zeros(7)] * 1e-3
    ok, x = build_and_solve(eta, k, gap, storage=np.array([50.0]), x_from=0, growth=10.0, start_2030=None,
                            objective="min_total", keep_running=True, life=3)
    assert ok
    assert x[0] == pytest.approx([1, 1, 1, 0, 0, 0, 0, 0, 0, 0], abs=1e-7)
    ok, x = build_and_solve(eta, k, gap, storage=np.array([50.0]), x_from=0, growth=10.0, start_2030=None,
                            objective="min_total", keep_running=True, life=None)
    assert x[0] == pytest.approx(np.ones(10), abs=1e-7)                 # never retiring: runs to the end


def test_main_case_plants_run_their_lifetime(main_case):
    from nbs.dac_optim import builds_matrix

    x = np.array(main_case["x"])
    assert np.all(builds_matrix(x.shape[1]) @ x.T >= -1e-7)


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


def test_mini_co2_target_counts_net_removal():
    # 9 Gt net needed by the end, eta 0.9 -> 10 Gt gross, spread evenly at least capacity
    k, eta = _mini()
    ok, x = build_and_solve(eta[:1], k, np.zeros(10), storage=np.array([50.0]), x_from=9, growth=10.0, start_2030=None,
                            objective="min_peak", co2_target=9.0)
    assert ok
    assert (x * eta[:1]).sum() == pytest.approx(9.0, rel=1e-5)
    assert x.sum(axis=0).max() == pytest.approx(1.0, rel=1e-4)


def test_co2_target_matches_the_temperature_gap():
    from nbs.dac_optim import co2_target_gt

    r = co2_target_gt()
    assert 200 < r < 320


@pytest.fixture(scope="module")
def co2_case():
    return solve(ziel="co2")


def test_co2_case_reaches_target(co2_case):
    from nbs.dac_optim import co2_target_gt

    r = co2_case
    net = (np.array(r["x"]) * np.array(r["eta"])).sum()
    assert net == pytest.approx(co2_target_gt(), rel=1e-4)
    assert r["co2_ziel_gt"] == pytest.approx(co2_target_gt())


def test_slow_growth_co2_target_approaches():
    r = solve(growth=1.11, ziel="co2")
    assert r["status"] == "annaeherung"
    assert r["netto_gt"] < r["co2_ziel_gt"]


def test_max_case_builds_at_the_growth_limit_until_the_storage_binds():
    from nbs.dac_optim import growth_limit, solve_max

    r = solve_max()
    x, eta = np.array(r["x"]), np.array(r["eta"])
    tot, lim = x.sum(axis=0), growth_limit()
    assert np.all(tot <= lim * (1 + 1e-6) + 1e-9)                 # never faster than the growth limit
    assert x.sum() <= r["speicher_gt"] * (1 + 1e-6)                # never more than the storage
    i60 = 2060 - 2026
    assert np.allclose(tot[: i60 + 1], lim[: i60 + 1], rtol=1e-4, atol=1e-6)  # as early as possible: at the limit
    assert r["netto_gt"] > 0.9 * r["speicher_gt"]                  # the storage is nearly full by 2100


def test_min_peak_never_raises_the_peak_and_more_growth_lowers_it():
    from nbs.dac_optim import solve_min_peak
    from nbs.vergleich_figures import overshoot_series

    gap = np.array(overshoot_series()["noetig_k"])
    slow, free = solve_min_peak(gap), solve_min_peak(gap, growth=1e6, limit_start=False)
    rest = np.maximum(0.0, gap - np.array(slow["kuehlung_k"]))
    assert abs(rest.max() - slow["spitze_k"]) < 1e-6                 # the reported peak is the path's peak
    assert slow["spitze_k"] <= gap.max() + 1e-9
    assert free["spitze_k"] < slow["spitze_k"] - 0.05                 # without a growth limit far lower


def test_min_peak_then_earliest_stays_below_from_its_year():
    from nbs.dac_optim import solve_min_peak
    from nbs.tree_paths import delta_t
    from nbs.vergleich_figures import overshoot_series

    gap = np.array(overshoot_series()["noetig_k"]) + delta_t("forst")   # the deck's gap: after the trees
    r = solve_min_peak(gap, danach="frueh")
    assert r["status"] == "spitze_dann_frueh"
    over = gap - np.array(r["kuehlung_k"])
    i = r["jahre"].index(r["ab_jahr"])
    assert np.all(over[i:] <= 1e-7)
    assert over[i - 1] > 0                                              # not below a year earlier
    late = solve_min_peak(gap)                                          # 1.5 deg C only by 2100: less capacity
    assert late["status"] == "spitze_und_ziel" and late["ab_jahr"] == 2100
    assert late["kapazitaet_gt"] < r["kapazitaet_gt"]


def test_path_cost_of_nothing_is_zero():
    from nbs.dac_optim import path_cost
    r = path_cost(np.zeros(len(YEARS)))
    assert r["summe_bio"] == 0.0 and r["spitze_bio_a"] == 0.0


def test_path_cost_constant_path_matches_cost_per_gt():
    from nbs.dac_optim import COST, cost_per_gt, path_cost
    w = np.ones(len(YEARS))  # 1 Gt/a every year
    r = path_cost(w)
    assert r["summe_bio"] == pytest.approx(float(cost_per_gt(0.0, COST).sum()), rel=1e-9)
    # one Gt/a at the median: a few hundred EUR per tonne
    assert 150 < r["eur_t"] < 600


def test_path_cost_cases_are_ordered():
    from nbs.dac_optim import COST_CASES, path_cost
    w = np.linspace(0, 5, len(YEARS))
    s = {k: path_cost(w, c)["summe_bio"] for k, c in COST_CASES.items()}
    assert s["optimistisch"] < s["median"] < s["pessimistisch"]


def test_comparison_values_have_sources():
    from nbs.dac_optim import EU27_BIP_BIO_EUR, FOSSIL_SUBV_BIO_EUR, VERGLEICH_QUELLEN
    assert 15 < EU27_BIP_BIO_EUR < 21
    assert 0.3 < FOSSIL_SUBV_BIO_EUR < 1.5
    assert set(VERGLEICH_QUELLEN) == {"eu27_bip", "fossil_subv"}


def test_min_peak_with_closed_gap_builds_nothing():
    from nbs.dac_optim import solve_min_peak
    r = solve_min_peak(np.zeros(len(YEARS)), danach="frueh")
    assert r["spitze_k"] == pytest.approx(0.0, abs=1e-9)
    assert r["kapazitaet_gt"] == pytest.approx(0.0, abs=1e-6)
    assert r["ab_jahr"] == int(YEARS[0])
