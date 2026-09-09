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
    anomaly Delta_C [ppm] and then run through a fixed-coefficient
    logarithmic CO2 forcing law, evaluated against the scenario's background
    concentration C_bg(t) rather than assumed constant:

        phi(t) = a * ln( (C_bg(t) + Delta_C(t)) / C_bg(t) )

    with a = A_CO2_LOG_W_M2_PER_PPM (Myhre et al. 1998, GRL 25(14)) and
    KG_CO2_PER_PPM converting kg CO2 to ppm.

    This a=5.35 form is a close *standard approximation* of FaIR's forcing
    law, not identical to it: ``fair_module._create_fair`` never sets
    ``ghg_method``, so FaIR actually uses its default ``meinshausen2020``, a
    more elaborate, state- and N2O-dependent formula. Measured directly
    against FaIR along the ssp245 background, the effective coefficient
    ``meinshausen2020`` implies is 5.354 at 424 ppm (0.08% above the fixed
    5.35 used here) and 5.482 at 624 ppm (2.46% above). The fixed Myhre
    coefficient is kept deliberately -- a model whose equations are meant to
    fit on a slide should not carry a state-dependent forcing expression for
    a ~2.5% effect, especially one dwarfed by the ~15% pulse-superposition
    error already documented in the mirror test
    (``tests/test_response.py::test_co2_chain_reproduces_a_full_fair_run_for_both_variants``).
    The *shape* of the approximation -- logarithmic, evaluated against the
    real rising background -- is what actually fixes the 26-40% CO2-channel
    deviation from using a constant linear efficiency; the ~2.5% residual
    from the fixed coefficient is a separate, much smaller effect.

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


def phi_albedo_from_product(
    closure: NDArray, alpha_q_product_w_m2: float, sp: Species
) -> NDArray:
    """Albedo forcing [W/m^2] from a pre-formed delta_alpha * q_sw product.

    Identical physics to phi_albedo; the difference is that the product arrives
    already formed. The grid needs this because delta_alpha and the insolation
    must be multiplied month by month before being averaged -- spring snow
    masking depends on the two peaking together, and multiplying annual means
    loses that covariance. See nbs.albedo_grid and the Plan 1 findings
    document (docs/superpowers/specs/2026-09-09-befunde-fuer-plan-2-und-3.md),
    section 4.
    """
    f = np.asarray(closure, dtype=float)
    return -alpha_q_product_w_m2 * TAU_ATM * f * sp.stand_area_m2 / A_EARTH_M2


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
