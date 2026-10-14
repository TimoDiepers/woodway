"""DAC without a growth limit, as much as it takes to hold the warming at 1.5 deg C (nbs.dac_optim.solve_offset):
the least yearly capacity that keeps every year from 2027 on at or below 1.5 deg C, then the least total."""
import numpy as np
import pytest

from nbs.constants import YEARS


@pytest.fixture(scope="module")
def runs():
    from nbs import vegan
    from nbs.dac_optim import solve_offset
    from nbs.tree_paths import delta_t
    from nbs.vergleich_figures import vl_series

    gap = np.array(vl_series()["median_c"]) - 1.5 + delta_t("forst")
    gv = gap + vegan.dt_gase() + vegan.dt_flaeche()
    return gap, solve_offset(gap), gv, solve_offset(gv)


def test_holds_1p5_from_2027(runs):
    gap, r, gv, rv = runs
    for g, x in ((gap, r), (gv, rv)):
        over = g - np.array(x["kuehlung_k"])
        assert over[1:].max() <= 1e-6


def test_storage_and_eta(runs):
    from nbs.dac_storage import storage_by_country
    _, r, _, _ = runs
    x, eta = np.array(r["x"]), np.array(r["eta"])
    st = storage_by_country("prudent")
    assert np.all(x.sum(axis=1) <= np.array([st[c] for c in r["laender"]]) + 1e-6)
    assert np.all(x[eta <= 0] == 0)


def test_vegan_needs_less(runs):
    _, r, _, rv = runs
    assert rv["kapazitaet_gt"] < r["kapazitaet_gt"] and rv["brutto_gt"] < r["brutto_gt"]


def test_the_capacity_runs_now_not_late(runs):
    _, r, _, _ = runs
    w = np.array(r["x"]).sum(axis=0)
    assert w[0] > 0.9 * r["kapazitaet_gt"]          # the work is now: the peak is close
    assert w[list(YEARS).index(2060):].max() < 1e-6


def test_capacity_stands_while_plants_idle_and_goes_at_shutdown():
    from nbs.dac_optim import capacity_from_run
    u = np.zeros(len(YEARS)); u[:16] = 60.0; u[10:13] = 30.0
    c = capacity_from_run(u)
    assert np.all(c[:16] == 60.0) and np.all(c[16:] == 0.0)


def test_cost_of_a_run_pays_each_plant_once():
    from nbs.dac_optim import COST, path_cost_run
    u = np.zeros(len(YEARS)); u[:16] = 60.0; u[10:13] = 30.0
    r = path_cost_run(u)
    opex = COST["fom"] + COST["sorbent"] + COST["energy"]
    want = (COST["capex"] * 60.0 + COST["fom"] * 60.0 * 16 + (COST["sorbent"] + COST["energy"]) * u.sum()) * 1e9 / 1e12
    assert r["summe_bio"] == pytest.approx(want, rel=1e-9)
    assert min(r["je_jahr_bio"]) >= 0 and all(v == 0 for v in r["je_jahr_bio"][16:])
