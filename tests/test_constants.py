import numpy as np
from nbs import constants as C


def test_years_axis_covers_study_period_inclusive():
    assert C.YEARS[0] == C.T_START
    assert C.YEARS[-1] == C.T_END
    assert len(C.YEARS) == C.T_END - C.T_START + 1


def test_co2_radiative_efficiency_matches_slide_value():
    # Folie 21: A_CO2 ~ 1,76e-15 W m^-2 kg^-1
    assert 1.6e-15 < C.A_CO2_W_M2_PER_KG < 1.9e-15


def test_molar_mass_ratio():
    assert C.M_CO2_PER_C == 44.0 / 12.0


def test_earth_area_order_of_magnitude():
    assert 5.0e14 < C.A_EARTH_M2 < 5.2e14
