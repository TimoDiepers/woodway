"""Credit analysis module for progressive complexity framework.

Orchestrates carbon, albedo, and FaIR modules to evaluate climate
credits across complexity levels 0-6.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.albedo_module import compute_albedo_forcing_timeseries
from nbs.carbon_module import compute_nee, compute_nee_at_level, nominal_credit_gtco2
from nbs.et_module import compute_et_forcing_timeseries
from nbs.fair_module import (
    compute_delta_t,
    compute_pulse_warming,
    find_breakeven_year,
    run_fair_baseline,
    run_fair_perturbed,
)
from nbs.parameters import (
    A_EARTH_M2,
    COMPLEXITY_LEVELS,
    HA_TO_M2,
    T_END,
    T_START,
)

N_YEARS = T_END - T_START


def compute_warming_debt(delta_t: NDArray) -> float:
    """Cumulative excess warming [K-yr]. Only counts years where delta_T > 0."""
    positive = np.maximum(delta_t, 0.0)
    return float(np.sum(positive))


def compute_equivalence_ratio(
    pulse_dt: NDArray,
    offset_dt: NDArray,
    horizon_year: int = 2100,
    pulse_gtco2: float = 1.0,
    credited_gtco2: float = 1.0,
) -> float:
    """Credits needed per tCO2 for net-zero warming by *horizon_year*.

    Both sides are normalised per tonne so the ratio is a physical statement and
    not an artefact of project size: the numerator is the time-integrated warming
    caused per tCO2 emitted, the denominator the time-integrated warming avoided
    per tCO2 a certificate would credit. Carbon-only accounting asserts a ratio
    of 1; every physical process we add moves it away from 1.

    Returns np.inf when the intervention provides no net cooling.
    """
    idx = min(horizon_year - T_START, len(pulse_dt) - 1)
    pulse_integral = float(np.sum(pulse_dt[: idx + 1])) / pulse_gtco2
    offset_integral = float(np.sum(offset_dt[: idx + 1])) / credited_gtco2

    if offset_integral >= 0:
        return np.inf

    ratio = -pulse_integral / offset_integral
    if ratio <= 0:
        return np.inf
    return ratio


def run_with(
    lat: int,
    scenario: str = "ssp245",
    pulse_gtco2: float = 1.0,
    area_mha: float = 1.0,
    *,
    growth: bool = True,
    location: bool = True,
    soil: bool = False,
    disturbance: bool = False,
    albedo: bool = False,
    et: bool = False,
) -> dict:
    """Run one configuration with every physical process switched on explicitly.

    The flags follow the order the talk introduces them: the certificate's
    instantaneous booking (all flags off), then the growing stand, then soil and
    disturbance, then the biophysical forcings. Non-CO2 forcings are local values
    over the treated area and are weighted by that area's share of the globe.
    """
    pulse_dt = compute_pulse_warming(pulse_gtco2=pulse_gtco2, scenario=scenario)
    baseline = run_fair_baseline(scenario=scenario)
    nee = compute_nee(
        lat,
        area_mha,
        growth=growth,
        location=location,
        soil=soil,
        disturbance=disturbance,
    )

    _intervention = "tropical_reforestation" if lat <= 15 else "boreal_afforestation"

    albedo_rf = (
        compute_albedo_forcing_timeseries(_intervention, lat)
        if albedo else np.zeros(N_YEARS)
    )
    et_rf = (
        compute_et_forcing_timeseries(_intervention, lat)
        if et else np.zeros(N_YEARS)
    )

    area_fraction = area_mha * 1e6 * HA_TO_M2 / A_EARTH_M2
    extra_forcing = (albedo_rf + et_rf) * area_fraction

    t_pert = run_fair_perturbed(nee, extra_forcing, scenario=scenario)
    offset_dt = compute_delta_t(t_pert, baseline)
    net_dt = pulse_dt + offset_dt
    credited = nominal_credit_gtco2(lat, area_mha, location=location)

    return {
        "delta_t": net_dt,
        "t_star": find_breakeven_year(net_dt),
        "warming_debt": compute_warming_debt(net_dt),
        "nee": nee,
        "equivalence_ratio_2100": compute_equivalence_ratio(
            pulse_dt,
            offset_dt,
            pulse_gtco2=pulse_gtco2,
            credited_gtco2=credited,
        ),
        "credited_gtco2": credited,
        "extra_forcing": extra_forcing,
        "pulse_dt": pulse_dt,
        "offset_dt": offset_dt,
    }


# The stations of the talk's journey, in narrative order.
REISE = {
    "zertifikat": dict(growth=False, location=False),
    "baum": dict(growth=True, location=True),
    "boden": dict(growth=True, location=True, soil=True, disturbance=True),
    "luft": dict(
        growth=True, location=True, soil=True, disturbance=True,
        albedo=True, et=True,
    ),
}


def run_journey(lat: int, scenario: str = "ssp245", area_mha: float = 1.0) -> dict[str, dict]:
    """Run all stations of the journey for one latitude."""
    return {
        name: run_with(lat, scenario=scenario, area_mha=area_mha, **flags)
        for name, flags in REISE.items()
    }


def run_at_level(
    level: int,
    lat: int,
    scenario: str = "ssp245",
    pulse_gtco2: float = 1.0,
    area_mha: float = 1.0,
) -> dict:
    """Run one of the study's complexity levels 0-6."""
    from nbs.carbon_module import _LEVEL_FLAGS

    flags = dict(_LEVEL_FLAGS[level])
    flags["albedo"] = level >= 3
    flags["et"] = level >= 4
    return run_with(
        lat,
        scenario=scenario,
        pulse_gtco2=pulse_gtco2,
        area_mha=area_mha,
        **flags,
    )


def run_progressive_analysis(
    lat: int,
    scenario: str = "ssp245",
    pulse_gtco2: float = 1.0,
    area_mha: float = 1.0,
) -> dict[int, dict]:
    """Run all complexity levels (0-6) for one latitude."""
    return {
        level: run_at_level(
            level, lat, scenario=scenario, pulse_gtco2=pulse_gtco2, area_mha=area_mha
        )
        for level in COMPLEXITY_LEVELS
    }
