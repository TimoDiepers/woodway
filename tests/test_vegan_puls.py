"""Pulse responses for the chapter-5 opener: 1 Gt CH4 avoided against 1 Gt CO2 removed in 2026 (FaIR on Very Low)."""
import numpy as np

from nbs.constants import YEARS


def test_methane_cools_far_more_per_tonne_but_fades():
    from nbs.vegan import dt_puls
    ch4, co2 = dt_puls("CH4"), dt_puls("CO2")
    assert ch4[0] == 0 and co2[0] == 0
    assert ch4.min() < 100 * co2.min() < 0             # per tonne methane cools over a hundred times more
    i50, i100 = list(YEARS).index(2050), len(YEARS) - 1
    assert ch4[i100] > 0.2 * ch4.min()                 # methane fades: by 2100 less than a fifth of its peak is left
    assert co2[i100] < 0.6 * co2.min()                 # CO2 removed stays removed: most of its cooling remains
    assert np.argmin(ch4) <= list(YEARS).index(2040) and ch4[i50] < 0


def test_mass_change_methane_is_gone_co2_stays():
    from nbs.vegan import puls_masse
    ch4, co2 = puls_masse("CH4"), puls_masse("CO2")
    i75 = list(YEARS).index(2075)
    assert -1 < ch4.min() < -0.9 and -1 < co2.min() < -0.85   # 1 Gt out, the first year already part refilled
    assert ch4[i75] > 0.1 * ch4.min()                          # methane is largely gone within five decades
    assert co2[-1] < 0.25 * co2.min()                          # removed CO2 stays partly removed


def test_forcing_strength_per_kg():
    from nbs.vegan import epsilon
    e_co2, e_ch4 = epsilon("CO2"), epsilon("CH4")
    assert 1.4e-15 < e_co2 < 1.8e-15                           # as 5.35 W/m^2 / (k c) with c ~ 427 ppm
    assert 60 < e_ch4 / e_co2 < 120
