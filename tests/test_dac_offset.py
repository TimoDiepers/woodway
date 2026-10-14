"""DACCS as a cost optimisation (nbs.dac_optim.solve_cost_offset): the cheapest builds and runs per country and year,
optimistic costs of Okosun et al. 2026, such that the cooling offsets the warming above 1.5 deg C that the trees
leave, in every year from 2027 on. No growth limit; plants run at most LIFETIME years and may idle."""
import numpy as np
import pytest

from nbs.constants import YEARS


@pytest.fixture(scope="module")
def runs():
    from nbs import vegan
    from nbs.dac_optim import solve_cost_offset
    from nbs.tree_paths import delta_t
    from nbs.vergleich_figures import vl_series

    gap = np.array(vl_series()["median_c"]) - 1.5 + delta_t("forst")
    gv = gap + vegan.dt_gase() + vegan.dt_flaeche()
    return gap, solve_cost_offset(gap), gv, solve_cost_offset(gv)


def test_offsets_the_warming_from_2027(runs):
    gap, r, gv, rv = runs
    for g, x in ((gap, r), (gv, rv)):
        assert (g - np.array(x["kuehlung_k"]))[1:].max() <= 1e-6


def test_runs_only_on_standing_plants(runs):
    from nbs.dac_optim import LIFETIME
    _, r, _, _ = runs
    b, u, cap = np.array(r["bau"]), np.array(r["u"]), np.array(r["kap_land"])
    assert b.min() >= -1e-9
    for t in range(len(YEARS)):
        assert np.allclose(cap[:, t], b[:, max(0, t - LIFETIME + 1):t + 1].sum(axis=1), atol=1e-6)
    assert np.all(u <= cap + 1e-6)


def test_storage_and_eta(runs):
    from nbs.dac_storage import storage_by_country
    _, r, _, _ = runs
    u, eta = np.array(r["u"]), np.array(r["eta"])
    st = storage_by_country("prudent")
    assert np.all(u.sum(axis=1) <= np.array([st[c] for c in r["laender"]]) + 1e-6)
    assert np.all(u[eta <= 0] <= 1e-9)


def test_reported_cost_is_the_objective(runs):
    from nbs.dac_optim import COST_CASES, price_plan
    _, r, _, _ = runs
    p = price_plan(np.array(r["bau"]).sum(axis=0), np.array(r["u"]).sum(axis=0), COST_CASES["optimistisch"])
    assert p["summe_bio"] == pytest.approx(r["kosten_bio"], rel=1e-6)


def test_vegan_is_cheaper(runs):
    _, r, _, rv = runs
    assert rv["kosten_bio"] < r["kosten_bio"] and rv["kapazitaet_gt"] < r["kapazitaet_gt"]


def test_price_plan_pays_build_and_fixed_cost_per_plant_and_energy_per_tonne():
    from nbs.dac_optim import COST, LIFETIME, price_plan
    b = np.zeros(len(YEARS)); b[0] = 60.0
    u = np.zeros(len(YEARS)); u[:16] = 60.0; u[10:13] = 30.0
    p = price_plan(b, u, COST)
    want = (COST["capex"] * 60.0 + COST["fom"] * 60.0 * LIFETIME + (COST["sorbent"] + COST["energy"]) * u.sum()) * 1e9 / 1e12
    assert p["summe_bio"] == pytest.approx(want, rel=1e-9)
