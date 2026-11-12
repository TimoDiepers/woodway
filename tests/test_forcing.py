import numpy as np
import pytest

from nbs.constants import A_CO2_W_M2_PER_KG, M_CO2_PER_C, YEARS
from nbs.forcing import (
    co2_flux_kg_per_yr,
    fallback_delta_alpha,
    fallback_q_sw,
    light_bulb_watts,
    phi_albedo,
    phi_co2,
    phi_co2_background,
)
from nbs.species import get_species

BOREAL = get_species("enf_boreal")
TROPICAL = get_species("ebf_tropisch")


def test_uptake_becomes_negative_co2_flux():
    flux = co2_flux_kg_per_yr(np.array([1.0, 2.0]))
    assert flux == pytest.approx([-M_CO2_PER_C, -2.0 * M_CO2_PER_C])


def test_release_becomes_positive_co2_flux():
    assert co2_flux_kg_per_yr(np.array([-1.0]))[0] > 0.0


def test_phi_co2_of_steady_removal_is_negative_and_grows():
    flux = np.full(len(YEARS), -100.0)
    g_c = np.ones(len(YEARS))  # nothing is reabsorbed: worst case for the sign
    phi = phi_co2(flux, g_c)
    assert phi[10] < 0.0
    assert phi[-1] < phi[10], "the gap keeps widening while removal continues"


def test_phi_co2_scales_with_radiative_efficiency():
    flux = np.zeros(len(YEARS))
    flux[0] = -1000.0
    g_c = np.ones(len(YEARS))
    phi = phi_co2(flux, g_c)
    # Expected magnitude is 1.76e-12: pytest.approx's default abs=1e-12 is the
    # same order as the value under test, so a wrong result could pass. Drop
    # the absolute floor and rely on a tight relative tolerance instead.
    assert phi[0] == pytest.approx(-1000.0 * A_CO2_W_M2_PER_KG, rel=1e-9, abs=0)


def test_darker_forest_warms():
    """delta_alpha < 0 means the forest is darker than what it replaces."""
    f = np.ones(len(YEARS))
    assert phi_albedo(f, -0.13, 110.0, BOREAL)[0] > 0.0


def test_brighter_surface_cools():
    f = np.ones(len(YEARS))
    assert phi_albedo(f, +0.05, 200.0, TROPICAL)[0] < 0.0


def test_albedo_forcing_follows_canopy_closure():
    f = np.linspace(0.0, 1.0, len(YEARS))
    phi = phi_albedo(f, -0.13, 110.0, BOREAL)
    # Real phi values elsewhere in this run are ~1e-13; pytest.approx's
    # default abs=1e-12 would let a wrongly nonzero phi[0] of that order pass
    # as "zero". f[0] is exactly 0.0 so phi[0] must be exactly 0.0 (a product
    # against 0.0 carries no floating-point rounding), hence the near-zero abs.
    assert phi[0] == pytest.approx(0.0, abs=1e-20)
    assert np.all(np.diff(phi) >= 0.0)


def test_boreal_tree_is_a_seventy_watt_light_bulb():
    """Slide 14 quotes about 70 W for a boreal tree. Code and slide must agree.

    This is a regression guard, not a physical validation: _DELTA_ALPHA_TABLE
    and _Q_SW_TABLE in nbs.forcing were fitted specifically to reproduce this
    figure, so a pass here only confirms the calibration was applied
    correctly, not that the slide's number is right.
    """
    w = light_bulb_watts(fallback_delta_alpha(60.0), fallback_q_sw(60.0), BOREAL)
    assert 245.0 < w < 400.0   # the 55-90 W of 2000 trees/ha, at 450 trees/ha (crown area x 4.44)


def test_tropical_tree_is_about_half_a_boreal_one():
    """Slide 14: 'in den Tropen etwa halb so viel'.

    This is a regression guard, not a physical validation: _DELTA_ALPHA_TABLE
    and _Q_SW_TABLE in nbs.forcing were fitted specifically to reproduce this
    figure, so a pass here only confirms the calibration was applied
    correctly, not that the slide's number is right.
    """
    boreal = light_bulb_watts(fallback_delta_alpha(60.0), fallback_q_sw(60.0), BOREAL)
    tropical = light_bulb_watts(fallback_delta_alpha(0.0), fallback_q_sw(0.0), TROPICAL)
    assert 0.3 < tropical / boreal < 0.7


def test_fallback_albedo_change_grows_with_latitude():
    lats = [0.0, 15.0, 30.0, 45.0, 60.0, 75.0]
    magnitudes = [abs(fallback_delta_alpha(x)) for x in lats]
    assert magnitudes == sorted(magnitudes)


def test_fallback_insolation_falls_towards_the_pole():
    assert fallback_q_sw(15.0) > fallback_q_sw(60.0) > fallback_q_sw(85.0)


def test_fallback_functions_interpolate_between_table_rows():
    mid = fallback_q_sw(52.5)
    assert min(fallback_q_sw(45.0), fallback_q_sw(60.0)) < mid < max(
        fallback_q_sw(45.0), fallback_q_sw(60.0)
    )


# --- phi_co2_background: logarithmic CO2 forcing against a background ------
#
# Sanity anchor from the task spec: linearising phi = a*ln((C0+dC)/C0) around
# a small dC gives an effective radiative efficiency of a/(C0*KG_CO2_PER_PPM)
# per kg. At 424 ppm that works out to 1.61e-15 W/m^2/kg; at 624 ppm to
# 1.10e-15. Both are below the linear constant A_CO2_W_M2_PER_KG = 1.76e-15,
# which is exactly the source of the 26-40% CO2-channel deviation the review
# measured (9% high at 424 ppm, 38% high at 624 ppm).


def _effective_efficiency(c_background_ppm: float) -> float:
    """phi_co2_background's forcing per kg for a tiny pulse, at t=0."""
    flux = np.zeros(len(YEARS))
    flux[0] = -1.0e10  # 10 Mt CO2: tiny relative to a ppm of the atmosphere,
    # far from double-precision cancellation (dC/C ~ 3e-6, x^2/2 ~ 4.5e-12)
    g_c = np.zeros(len(YEARS))
    g_c[0] = 1.0  # all still airborne at t=0
    c_bg = np.full(len(YEARS), c_background_ppm)
    phi = phi_co2_background(flux, g_c, c_bg)
    return phi[0] / flux[0]


def test_logarithmic_effective_efficiency_at_424ppm():
    # pytest.approx's default abs=1e-12 dominates a value of order 1e-15 by
    # three orders of magnitude and would accept almost anything (including
    # 0.0) as "close enough". abs=0 forces the comparison to run on rel
    # alone.
    assert _effective_efficiency(424.0) == pytest.approx(1.61e-15, rel=0.01, abs=0)


def test_logarithmic_effective_efficiency_at_624ppm():
    assert _effective_efficiency(624.0) == pytest.approx(1.10e-15, rel=0.01, abs=0)


def test_logarithmic_effective_efficiency_below_linear_constant():
    """This ordering is the whole point of the sensitivity switch: the
    constant A_CO2_W_M2_PER_KG overstates the true (logarithmic) efficiency
    at both ends of the ssp245 study period, more so as CO2 rises."""
    eff_424 = _effective_efficiency(424.0)
    eff_624 = _effective_efficiency(624.0)
    assert eff_424 < A_CO2_W_M2_PER_KG
    assert eff_624 < eff_424, "efficiency keeps falling as the background rises"


def test_phi_co2_background_removal_cools():
    """A steady removal flux (negative, as co2_flux_kg_per_yr convention has
    it) must give a negative (cooling) forcing, same sign as phi_co2."""
    flux = np.full(len(YEARS), -1.0e11)
    g_c = np.ones(len(YEARS))
    c_bg = np.full(len(YEARS), 424.0)
    phi = phi_co2_background(flux, g_c, c_bg)
    assert phi[10] < 0.0
    assert phi[-1] < phi[10], "the gap keeps widening while removal continues"


def test_phi_co2_background_zero_flux_gives_zero_forcing():
    flux = np.zeros(len(YEARS))
    g_c = np.ones(len(YEARS))
    c_bg = np.full(len(YEARS), 424.0)
    phi = phi_co2_background(flux, g_c, c_bg)
    assert np.allclose(phi, 0.0, atol=1e-25)


def test_phi_co2_background_tracks_rising_background_at_fixed_mass():
    """The same airborne mass anomaly forces less against a higher
    background -- that is the entire mechanism behind the deviation."""
    flux = np.zeros(len(YEARS))
    flux[0] = -1.0e11
    g_c = np.ones(len(YEARS))
    phi_low = phi_co2_background(flux, g_c, np.full(len(YEARS), 424.0))
    phi_high = phi_co2_background(flux, g_c, np.full(len(YEARS), 624.0))
    assert abs(phi_high[-1]) < abs(phi_low[-1])
