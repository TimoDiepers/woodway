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
