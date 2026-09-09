"""The two forcing channels of a single tree.

Carbon acts globally and carries no area term, because CO2 mixes. Albedo acts
only where the tree stands and is therefore weighted by the tree's share of the
Earth's surface. Slides 21 and 22.

Evapotranspiration is deliberately absent: it does not cross the top-of-
atmosphere boundary and its effect sits in the feedback parameter Lambda.
Slide 18 argues this in full.

The latitude fallback tables below (_DELTA_ALPHA_TABLE, _Q_SW_TABLE) are a
joint calibration against slide 14's ~70 W and ~half figures, not independent
measurements: see their docstrings before citing either one as an observation.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.constants import (
    A_CO2_LOG_W_M2_PER_PPM,
    A_CO2_W_M2_PER_KG,
    A_EARTH_M2,
    KG_CO2_PER_PPM,
    M_CO2_PER_C,
    TAU_ATM,
)
from nbs.response import convolve_response
from nbs.species import Species


def co2_flux_kg_per_yr(net_uptake_kgC_yr: NDArray) -> NDArray:
    """Atmospheric CO2 flux [kg CO2/a] from ecosystem carbon uptake.

    What the tree stores is missing from the air, hence the sign flip.
    """
    return -M_CO2_PER_C * np.asarray(net_uptake_kgC_yr, dtype=float)


def phi_co2(co2_flux_kg_per_yr: NDArray, g_c: NDArray) -> NDArray:
    """Radiative forcing [W/m^2] from the CO2 the tree keeps out of the air.

    The flux is convolved with the airborne fraction, so only the part of each
    past year's removal that is still missing counts today.
    """
    delta_m = convolve_response(g_c, np.asarray(co2_flux_kg_per_yr, dtype=float))
    return A_CO2_W_M2_PER_KG * delta_m


def phi_co2_background(
    co2_flux_kg_per_yr: NDArray, g_c: NDArray, c_background_ppm: NDArray
) -> NDArray:
    """Marginal CO2 radiative forcing [W/m^2] against a rising background.

    This is the logarithmic variant of ``phi_co2``: the flux is convolved
    with the airborne fraction exactly as in ``phi_co2`` to get the airborne
    mass anomaly Delta_m_CO2 [kg], which is converted to a concentration
    anomaly Delta_C [ppm] and then run through the actual (logarithmic) CO2
    forcing law FaIR uses, evaluated against the scenario's background
    concentration C_bg(t) rather than assumed constant:

        phi(t) = a * ln( (C_bg(t) + Delta_C(t)) / C_bg(t) )

    with a = A_CO2_LOG_W_M2_PER_PPM (Myhre et al. 1998) and
    KG_CO2_PER_PPM converting kg CO2 to ppm.

    Leave ``phi_co2`` (the linear, constant-efficiency variant) untouched --
    existing tests pin it, and it is what slide 21 derives. This function is
    the scenario-consistent alternative selected by
    ``ModelConfig(co2_forcing="logarithmic")``.

    For a small Delta_C this linearises to phi ~= a * Delta_C / C_bg, i.e. an
    effective radiative efficiency of a / (C_bg * KG_CO2_PER_PPM) per kg --
    1.61e-15 W/m^2/kg at 424 ppm, 1.10e-15 at 624 ppm, both below the linear
    constant A_CO2_W_M2_PER_KG = 1.76e-15. That gap is exactly the 26-40%
    integrated CO2-channel deviation the review measured against FaIR.
    """
    delta_m = convolve_response(g_c, np.asarray(co2_flux_kg_per_yr, dtype=float))
    delta_c_ppm = delta_m / KG_CO2_PER_PPM
    c_bg = np.asarray(c_background_ppm, dtype=float)
    return A_CO2_LOG_W_M2_PER_PPM * np.log((c_bg + delta_c_ppm) / c_bg)


def phi_albedo(
    closure: NDArray, delta_alpha: float, q_sw_w_m2: float, sp: Species
) -> NDArray:
    """Radiative forcing [W/m^2] from the tree darkening its footprint.

    delta_alpha is the albedo of the forest minus the albedo of the land it
    replaces, so a darker forest gives delta_alpha < 0 and a positive forcing.

    Carries TAU_ATM, unlike light_bulb_watts: the light-bulb figure is what
    the tree absorbs at the surface, while this is the part of that surface
    anomaly which actually reaches the top of the atmosphere.
    """
    f = np.asarray(closure, dtype=float)
    return -delta_alpha * q_sw_w_m2 * TAU_ATM * f * sp.stand_area_m2 / A_EARTH_M2


def light_bulb_watts(delta_alpha: float, q_sw_w_m2: float, sp: Species) -> float:
    """Extra power absorbed by one closed-canopy tree [W].

    No transmittance factor: this is measured at the surface, where the tree
    is, not at the top of the atmosphere. Slide 14's 'light bulb that never
    goes out'.
    """
    return float(-delta_alpha * q_sw_w_m2 * sp.stand_area_m2)


_LAT_TABLE = np.array([0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0])
_DELTA_ALPHA_TABLE = np.array([-0.033, -0.033, -0.040, -0.070, -0.130, -0.160, -0.160])
_Q_SW_TABLE = np.array([210.0, 230.0, 225.0, 160.0, 110.0, 75.0, 60.0])


def fallback_delta_alpha(lat_deg: float) -> float:
    """Annual-mean forest-minus-open albedo change, by latitude.

    Stand-in until the Duveiller transition rasters land in plan 2. Values are
    tuned, jointly with _Q_SW_TABLE in fallback_q_sw, so that a boreal tree
    comes out near the 70 W quoted on slide 14. Neither table should be cited
    as an observation until the raster data replaces them.

    lat_deg is mirrored by absolute value, so southern latitudes reuse the
    northern-hemisphere row; inputs beyond +/-90 degrees clamp to the 90 degree
    table edge (np.interp does not extrapolate).
    """
    return float(np.interp(abs(lat_deg), _LAT_TABLE, _DELTA_ALPHA_TABLE))


def fallback_q_sw(lat_deg: float) -> float:
    """Annual-mean downward shortwave at the surface [W/m^2], by latitude.

    Stand-in until CERES or ERA5 fields land in plan 2. Values are tuned,
    jointly with _DELTA_ALPHA_TABLE in fallback_delta_alpha, so that the
    boreal-vs-tropical light-bulb figures on slide 14 (~70 W, ~half in the
    tropics) come out right — both slide numbers depend on the product of
    the two tables. Neither table should be cited as an observation until
    the raster data replaces them.

    lat_deg is mirrored by absolute value, so southern latitudes reuse the
    northern-hemisphere row; inputs beyond +/-90 degrees clamp to the 90 degree
    table edge (np.interp does not extrapolate).
    """
    return float(np.interp(abs(lat_deg), _LAT_TABLE, _Q_SW_TABLE))
