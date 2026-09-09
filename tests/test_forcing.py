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
)
from nbs.species import get_species

BOREAL = get_species("picea_abies")
TROPICAL = get_species("tropical_mixed")


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
    """Slide 14 quotes about 70 W for a boreal tree. Code and slide must agree."""
    w = light_bulb_watts(fallback_delta_alpha(60.0), fallback_q_sw(60.0), BOREAL)
    assert 55.0 < w < 90.0


def test_tropical_tree_is_about_half_a_boreal_one():
    """Slide 14: 'in den Tropen etwa halb so viel'."""
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
