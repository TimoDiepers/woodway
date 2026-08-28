"""Carbon dynamics module for forest-based climate interventions."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.parameters import (
    BECCS_CCS_EFFICIENCY,
    BECCS_HARVEST_PERIOD,
    BECCS_PROCESS_EMISSION_FRAC,
    C_FOREST_TROPICAL,
    DEFORESTATION_RATE,
    SOC_MU,
    SOIL_RESP_BASE,
    SOIL_RESP_Q10,
    SOIL_RESP_T0,
    T_END,
    T_START,
    get_disturbance_probability,
    get_growth_params,
    get_soc_params,
)

# Conversion factor from tC to tCO2
C_TO_CO2 = 44.0 / 12.0

# Default tropical growth params for Level 1 (location-independent)
_LEVEL1_GROWTH = (200.0, 0.08, 2.5)  # Tropical: B_max, k, p

# Location-dependent growth params for Level 2+
_LEVEL2_GROWTH: dict[int, tuple[float, float, float]] = {
    0: (200.0, 0.08, 2.5),     # Tropical
    15: (200.0, 0.08, 2.5),    # Tropical
    30: (120.0, 0.05, 2.0),    # Temperate
    45: (100.0, 0.03, 2.0),    # Boreal
    60: (100.0, 0.03, 2.0),    # Boreal
}

# Base temperatures by latitude [deg C]
BASE_TEMP: dict[int, float] = {0: 25.0, 15: 22.0, 30: 17.0, 45: 10.0, 60: 2.0}


def _nearest_lat(lat: int, mapping: dict[int, float]) -> int:
    return min(mapping.keys(), key=lambda k: abs(k - lat))


# ---------------------------------------------------------------------------
# Component functions
# ---------------------------------------------------------------------------


def compute_biomass_growth(
    B_max: float, k: float, p: float, t: NDArray
) -> NDArray:
    """Chapman-Richards growth curve.

    Parameters
    ----------
    B_max : float  – asymptotic biomass [tC/ha]
    k     : float  – growth-rate constant [yr⁻¹]
    p     : float  – shape exponent
    t     : NDArray – time since planting [yr]

    Returns
    -------
    NDArray – biomass at each time step [tC/ha]
    """
    return B_max * (1.0 - np.exp(-k * t)) ** p


def compute_soc_dynamics(
    soc_forest: float, soc_initial: float, mu: float, t: NDArray
) -> NDArray:
    """Exponential SOC convergence toward forest equilibrium.

    Parameters
    ----------
    soc_forest  : float  – equilibrium SOC under forest [tC/ha]
    soc_initial : float  – initial SOC [tC/ha]
    mu          : float  – convergence rate [yr⁻¹]
    t           : NDArray – time [yr]

    Returns
    -------
    NDArray – SOC at each time step [tC/ha]
    """
    return soc_forest + (soc_initial - soc_forest) * np.exp(-mu * t)


def compute_soil_respiration(
    r_base: float, q10: float, t0: float, temperature: float | NDArray
) -> float | NDArray:
    """Q10-based soil respiration.

    Parameters
    ----------
    r_base      : float        – base respiration rate at t0 [tCO2/ha/yr]
    q10         : float        – Q10 factor
    t0          : float        – reference temperature [deg C]
    temperature : float|NDArray – actual temperature(s) [deg C]

    Returns
    -------
    float|NDArray – respiration rate(s) [tCO2/ha/yr]
    """
    return r_base * q10 ** ((temperature - t0) / 10.0)


def compute_disturbance_loss(biomass: NDArray, p_disturb: NDArray) -> NDArray:
    """Annual disturbance loss.

    Parameters
    ----------
    biomass   : NDArray – standing biomass [tC/ha]
    p_disturb : NDArray – annual disturbance probability

    Returns
    -------
    NDArray – carbon lost to disturbance [tC/ha/yr]
    """
    return p_disturb * biomass


# ---------------------------------------------------------------------------
# Level-based NEE computation
# ---------------------------------------------------------------------------


def compute_nee(
    lat: int,
    area_mha: float = 1.0,
    *,
    growth: bool = True,
    location: bool = True,
    soil: bool = False,
    disturbance: bool = False,
) -> NDArray:
    """Net ecosystem exchange [GtCO2/yr] with each process switched on explicitly.

    ``growth=False`` reproduces carbon-only accounting: the credited mass leaves
    the atmosphere in the first year and never returns. Every other flag adds one
    physical process, in the order the talk introduces them.

    Negative values = net removal from the atmosphere.
    """
    n_years = T_END - T_START  # 125
    years = np.arange(T_START, T_END)
    t = np.arange(n_years, dtype=float)

    if not growth:
        nee = np.zeros(n_years)
        nee[0] = -nominal_credit_gtco2(lat, area_mha, location=location)
        return nee

    if location:
        lat_key = _nearest_lat(lat, _LEVEL2_GROWTH)
        B_max, k, p = _LEVEL2_GROWTH[lat_key]
    else:
        B_max, k, p = _LEVEL1_GROWTH

    biomass = compute_biomass_growth(B_max, k, p, t)
    dB_dt = np.diff(biomass, prepend=0.0)

    _intervention = (
        "tropical_reforestation" if lat <= 15
        else "boreal_afforestation"
    )

    if soil:
        soc_forest, soc_initial = get_soc_params(_intervention, lat)
        soc = compute_soc_dynamics(soc_forest, soc_initial, SOC_MU, t)
        dSOC_dt = np.diff(soc, prepend=soc_initial)

        lat_key_temp = _nearest_lat(lat, BASE_TEMP)
        base_temp = BASE_TEMP[lat_key_temp]
        temperature = base_temp + 2.0 * t / (n_years - 1)

        lat_key_resp = _nearest_lat(lat, SOIL_RESP_BASE)
        r_base = SOIL_RESP_BASE[lat_key_resp]
        R_soil = compute_soil_respiration(
            r_base, SOIL_RESP_Q10, SOIL_RESP_T0, temperature
        ) - compute_soil_respiration(
            r_base, SOIL_RESP_Q10, SOIL_RESP_T0, base_temp
        )
    else:
        dSOC_dt = np.zeros(n_years)
        R_soil = np.zeros(n_years)

    if disturbance:
        p_disturb = get_disturbance_probability(_intervention, lat, years)
        D = compute_disturbance_loss(biomass, p_disturb)
    else:
        D = np.zeros(n_years)

    net_uptake = (dB_dt + dSOC_dt) * C_TO_CO2 - R_soil - D * C_TO_CO2
    return -net_uptake * area_mha * 1e-3


def area_for_credit(gtco2: float, lat: int, *, location: bool = True) -> float:
    """Area [Mha] a certificate needs to claim *gtco2* of removal at *lat*.

    The inverse of :func:`nominal_credit_gtco2`: how much land has to be planted
    so that carbon-only accounting books exactly this much CO2.
    """
    return gtco2 / nominal_credit_gtco2(lat, 1.0, location=location)


# Complexity levels of the original study design, expressed as process flags.
_LEVEL_FLAGS: dict[int, dict[str, bool]] = {
    0: dict(growth=False, location=False, soil=False, disturbance=False),
    1: dict(growth=True, location=False, soil=False, disturbance=False),
    2: dict(growth=True, location=True, soil=False, disturbance=False),
    3: dict(growth=True, location=True, soil=False, disturbance=False),
    4: dict(growth=True, location=True, soil=False, disturbance=False),
    5: dict(growth=True, location=True, soil=True, disturbance=False),
    6: dict(growth=True, location=True, soil=True, disturbance=True),
}


def compute_nee_at_level(level: int, lat: int, area_mha: float = 1.0) -> NDArray:
    """NEE for one of the study's complexity levels 0-6.

    Thin wrapper around :func:`compute_nee`; albedo and ET forcings are handled
    in ``credit_analysis`` and do not change NEE.
    """
    return compute_nee(lat, area_mha, **_LEVEL_FLAGS[level])


def nominal_credit_gtco2(
    lat: int, area_mha: float = 1.0, *, location: bool = True
) -> float:
    """Carbon mass a certificate would credit for this project [GtCO2].

    Carbon-only accounting credits the standing biomass the stand reaches at
    maturity, ``B_max``, regardless of how long that takes or of what else the
    stand does to the energy balance. With ``location=False`` the accounting is
    location-blind and uses tropical parameters everywhere.
    """
    if location:
        B_max = _LEVEL2_GROWTH[_nearest_lat(lat, _LEVEL2_GROWTH)][0]
    else:
        B_max = _LEVEL1_GROWTH[0]
    return B_max * C_TO_CO2 * area_mha * 1e-3


# ---------------------------------------------------------------------------
# Main integration function
# ---------------------------------------------------------------------------


def compute_nee_timeseries(
    intervention: str, lat: int, area_mha: float = 1.0
) -> NDArray:
    """Compute annual NEE time series for *intervention* at *lat*.

    Returns shape (125,) array of NEE [GtCO2/yr] for 2025-2150.
    Negative values = net removal from atmosphere.

    Parameters
    ----------
    intervention : str   – one of the four intervention keys
    lat          : int   – latitude band [deg N]
    area_mha     : float – project area [million ha]
    """
    n_years = T_END - T_START  # 125
    years = np.arange(T_START, T_END)  # [2025 .. 2149]
    t = np.arange(n_years, dtype=float)  # [0 .. 124]

    # ----- Avoided deforestation: constant prevented emission -----
    if intervention == "avoided_deforestation":
        prevented = DEFORESTATION_RATE * C_FOREST_TROPICAL * C_TO_CO2  # tCO2/ha/yr
        nee = np.full(n_years, -prevented)  # negative = removal
        return nee * area_mha * 1e-3

    # ----- Growth-based interventions (TR, BA, BECCS) -----
    B_max, k, p = get_growth_params(intervention)

    # Biomass
    biomass = compute_biomass_growth(B_max, k, p, t)
    dB_dt = np.diff(biomass, prepend=0.0)  # annual increment [tC/ha/yr]

    # SOC
    soc_forest, soc_initial = get_soc_params(intervention, lat)
    soc = compute_soc_dynamics(soc_forest, soc_initial, SOC_MU, t)
    dSOC_dt = np.diff(soc, prepend=soc_initial)  # annual change [tC/ha/yr]

    # Temperature trajectory: linear warming of +2 deg C over the period
    lat_key = _nearest_lat(lat, BASE_TEMP)
    base_temp = BASE_TEMP[lat_key]
    temperature = base_temp + 2.0 * t / (n_years - 1)

    # Soil respiration – only the *additional* respiration due to warming matters;
    # baseline respiration is already implicit in the SOC dynamics model.
    lat_key_resp = _nearest_lat(lat, SOIL_RESP_BASE)
    r_base = SOIL_RESP_BASE[lat_key_resp]
    R_soil_full = compute_soil_respiration(r_base, SOIL_RESP_Q10, SOIL_RESP_T0, temperature)
    R_soil_baseline = compute_soil_respiration(r_base, SOIL_RESP_Q10, SOIL_RESP_T0, base_temp)
    R_soil = R_soil_full - R_soil_baseline  # warming-induced excess

    # Disturbance
    p_disturb = get_disturbance_probability(intervention, lat, years)
    D = compute_disturbance_loss(biomass, p_disturb)  # tC/ha/yr

    # Net uptake [tCO2/ha/yr]
    net_uptake = (dB_dt + dSOC_dt) * C_TO_CO2 - R_soil - D * C_TO_CO2
    nee = -net_uptake  # negative = removal

    # ----- BECCS: harvest spikes -----
    if intervention == "beccs":
        harvest_flux = np.zeros(n_years)
        for hy in range(BECCS_HARVEST_PERIOD, n_years, BECCS_HARVEST_PERIOD):
            captured = biomass[hy] * BECCS_CCS_EFFICIENCY * C_TO_CO2
            process_em = captured * BECCS_PROCESS_EMISSION_FRAC
            harvest_flux[hy] = -(captured - process_em)
        nee = nee + harvest_flux

    # Scale: tCO2/ha/yr  ->  GtCO2/yr  for area_mha Mha
    return nee * area_mha * 1e-3
