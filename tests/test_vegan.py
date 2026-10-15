"""Tests for nbs.vegan: the vegan world from 2026."""

import numpy as np
import pytest

from nbs.constants import YEARS


def test_livestock_shares_are_plausible():
    from nbs.vegan import livestock_shares, quelle_bezug
    s = livestock_shares()
    if quelle_bezug() == "agrar":
        assert 0.6 < s["CH4"] < 0.9   # livestock: most of farm methane (rest: rice, burning)
    else:
        assert 0.25 < s["CH4"] < 0.40  # livestock: about a third of all anthropogenic methane
    assert 0.05 < s["N2O"] < 0.8


def test_delta_never_exceeds_share_of_scenario():
    import pandas as pd
    from nbs.vegan import emission_delta, livestock_shares, quelle_bezug
    em = pd.read_csv("data/cmip7/fair-inputs/emissions_1750-2500.csv")
    vl = em[(em.scenario == "VL") & (em.variable == "CH4")]
    ch4 = np.array([float(vl[f"{y}.5"].iloc[0]) for y in YEARS])
    d = emission_delta()["CH4"]
    assert d.shape == (len(YEARS),)
    assert np.all(d <= 0)
    assert np.all(-d <= ch4 + 1e-9)              # never more than all of Very Low's methane
    assert np.all(-d <= livestock_shares()["CH4"] * ch4 + 1e-9) or quelle_bezug() == "agrar"  # fallback: share of total


def test_vegan_gases_cool_fast():
    from nbs.vegan import dt_gase
    dt = dt_gase()
    assert dt.shape == (len(YEARS),)
    assert dt[24] < -0.05           # 2050: clearly cooler
    assert dt[24] < 0.5 * dt[-1] or dt[24] < -0.1  # most of the effect early (short-lived)


def test_vegan_gases_cool_within_the_known_magnitude():
    # Ivanovich et al. 2023: all of food adds ~1 K by 2100; livestock gases on Very Low: a few tenths of a K at most
    from nbs.vegan import dt_gase
    dt = dt_gase()
    assert np.all(dt > -0.5) and np.all(np.isfinite(dt))


def test_freed_land_is_plausible():
    from nbs.vegan import freed_area_m2
    gha = freed_area_m2().sum() / 1e13
    assert 0.3 < gha < 2.5     # forest-capable grazing land plus 19 % of forest-capable cropland


def test_freed_land_disjoint_from_reforestable():
    from nbs.forest_data import reforestable_area_m2
    from nbs.grid import cell_area_m2
    from nbs.vegan import freed_area_m2
    tot = freed_area_m2() + reforestable_area_m2()
    assert np.all(tot <= cell_area_m2() * 1.0001)


def test_freed_carbon_where_freed():
    from nbs.vegan import freed_area_m2, freed_carbon_mgc_ha
    a, c = freed_area_m2(), freed_carbon_mgc_ha()
    assert np.all(c[a > 0] >= 0) and np.median(c[a > 0]) > 10


def test_forest_on_freed_land_cools():
    from nbs.vegan import dt_flaeche, flaeche_info
    from nbs.tree_paths import delta_t, forcing
    dt = dt_flaeche()
    assert dt.shape == (len(YEARS),)
    info = flaeche_info()
    assert 0 < info["kuehlt_gha"] <= info["frei_gha"]
    # same tree chain: cooling per cooling Gha in 2100 like the reforestation's, within a factor of two
    per_gha = dt[-1] / info["kuehlt_gha"]
    ref = delta_t("kuehlt")[-1] / forcing("kuehlt")[2]
    assert 0.5 * ref > per_gha > 2.0 * ref


def test_emission_parts_add_up_to_the_delta():
    # avoided livestock emissions (CH4, N2O, CO2), plus what the replacement crops add, give the net delta
    from nbs.vegan import emission_delta, emission_parts
    p, d = emission_parts(), emission_delta()
    assert set(p) == {"ch4_tier", "n2o_vermieden", "co2_hof", "co2_entwaldung", "ersatz"}
    assert set(d) == {"CH4", "N2O", "CO2 FFI", "CO2 AFOLU"}
    for sp in d:
        assert np.allclose(sum(p[k].get(sp, 0) for k in p), d[sp])
    for k in ("ch4_tier", "n2o_vermieden", "co2_hof", "co2_entwaldung"):
        assert all(np.all(v <= 0) for v in p[k].values())
    assert all(np.all(v >= 0) for v in p["ersatz"].values())


def test_avoided_co2_is_small_next_to_very_low():
    # fossil farm-gate CO2 of feed and deforestation for beef: a few hundred Mt/a now, gone with Very Low's decline
    from nbs.vegan import emission_parts
    p = emission_parts()
    hof, wald = p["co2_hof"]["CO2 FFI"], p["co2_entwaldung"]["CO2 AFOLU"]
    assert 200 < -hof[0] < 1000 and 500 < -wald[0] < 2000      # Mt CO2/a in 2026
    assert hof[-1] == 0 and wald[-1] == 0                      # Very Low: no fossil or deforestation CO2 by 2100


def test_contributions_sum_to_the_vegan_world():
    from nbs.vegan import contributions, dt_flaeche, dt_gase
    c = contributions()
    assert set(c) == {"ch4_tier", "n2o_vermieden", "n2o_tier", "n2o_acker", "co2_hof", "co2_entwaldung", "ersatz", "wald_co2", "wald_albedo", "netto"}
    assert np.allclose(c["netto"], dt_gase() + dt_flaeche())
    assert c["ch4_tier"][-1] < 0 and c["n2o_vermieden"][-1] < 0 and c["co2_hof"][-1] < 0 and c["co2_entwaldung"][-1] < 0 and c["ersatz"][-1] > 0
    assert c["wald_co2"][-1] < 0 and c["wald_albedo"][-1] > 0
    parts = sum(c[k] for k in c if k != "netto")
    assert np.max(np.abs(parts - c["netto"])) < 0.05 * np.max(np.abs(c["netto"]))   # FaIR nearly linear here
