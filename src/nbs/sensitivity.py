"""Sensitivity analysis for NBS climate interventions.

One-at-a-time (OAT) and global Sobol sensitivity analysis of key
parameters affecting the break-even year t*.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.albedo_module import compute_albedo_forcing_timeseries
from nbs.carbon_module import (
    BASE_TEMP,
    C_TO_CO2,
    compute_biomass_growth,
    compute_disturbance_loss,
    compute_soc_dynamics,
    compute_soil_respiration,
)
from nbs.fair_module import (
    compute_delta_t,
    find_breakeven_year,
    run_fair_baseline,
    run_fair_perturbed,
)
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

# ---------------------------------------------------------------------------
# Parameter bounds for sensitivity analysis
# ---------------------------------------------------------------------------

PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "B_max_scale": (0.7, 1.3),
    "Q10": (1.5, 2.5),
    "eta_CCS": (0.75, 0.95),
    "p_disturb_scale": (0.5, 2.0),
    "mu": (0.01, 0.06),
    "albedo_scale": (0.7, 1.3),
}


def _nearest_lat(lat: int, mapping: dict[int, float]) -> int:
    return min(mapping.keys(), key=lambda k: abs(k - lat))


def _run_with_params(
    intervention: str,
    lat: int,
    scenario: str,
    baseline_temp: NDArray,
    params: dict,
) -> float:
    """Rebuild NEE with overridden parameters and return break-even year t*.

    Parameters
    ----------
    intervention : str
        Intervention name.
    lat : int
        Latitude in degrees N.
    scenario : str
        SSP scenario name.
    baseline_temp : NDArray
        Pre-computed baseline temperature from FaIR.
    params : dict
        Parameter overrides. Supported keys: B_max_scale, Q10, eta_CCS,
        p_disturb_scale, mu, albedo_scale.

    Returns
    -------
    float
        Break-even year, or np.inf if never reached.
    """
    n_years = T_END - T_START  # 125
    years = np.arange(T_START, T_END)
    t = np.arange(n_years, dtype=float)

    area_mha = 1.0

    # ----- Avoided deforestation: no growth params to vary -----
    if intervention == "avoided_deforestation":
        prevented = DEFORESTATION_RATE * C_FOREST_TROPICAL * C_TO_CO2
        nee = np.full(n_years, -prevented) * area_mha * 1e-3
    else:
        # ----- Growth-based interventions -----
        B_max_base, k, p = get_growth_params(intervention)
        B_max = B_max_base * params.get("B_max_scale", 1.0)

        # Biomass
        biomass = compute_biomass_growth(B_max, k, p, t)
        dB_dt = np.diff(biomass, prepend=0.0)

        # SOC
        soc_forest, soc_initial = get_soc_params(intervention, lat)
        mu = params.get("mu", SOC_MU)
        soc = compute_soc_dynamics(soc_forest, soc_initial, mu, t)
        dSOC_dt = np.diff(soc, prepend=soc_initial)

        # Temperature trajectory
        lat_key = _nearest_lat(lat, BASE_TEMP)
        base_temp = BASE_TEMP[lat_key]
        temperature = base_temp + 2.0 * t / (n_years - 1)

        # Soil respiration (warming-induced excess only)
        lat_key_resp = _nearest_lat(lat, SOIL_RESP_BASE)
        r_base = SOIL_RESP_BASE[lat_key_resp]
        Q10 = params.get("Q10", SOIL_RESP_Q10)
        R_soil_full = compute_soil_respiration(r_base, Q10, SOIL_RESP_T0, temperature)
        R_soil_baseline = compute_soil_respiration(r_base, Q10, SOIL_RESP_T0, base_temp)
        R_soil = R_soil_full - R_soil_baseline

        # Disturbance
        p_disturb = get_disturbance_probability(intervention, lat, years)
        p_disturb = p_disturb * params.get("p_disturb_scale", 1.0)
        D = compute_disturbance_loss(biomass, p_disturb)

        # Net uptake -> NEE
        net_uptake = (dB_dt + dSOC_dt) * C_TO_CO2 - R_soil - D * C_TO_CO2
        nee = -net_uptake

        # BECCS harvest
        if intervention == "beccs":
            eta_CCS = params.get("eta_CCS", BECCS_CCS_EFFICIENCY)
            harvest_flux = np.zeros(n_years)
            for hy in range(BECCS_HARVEST_PERIOD, n_years, BECCS_HARVEST_PERIOD):
                captured = biomass[hy] * eta_CCS * C_TO_CO2
                process_em = captured * BECCS_PROCESS_EMISSION_FRAC
                harvest_flux[hy] = -(captured - process_em)
            nee = nee + harvest_flux

        nee = nee * area_mha * 1e-3

    # Albedo forcing with optional scaling
    albedo = compute_albedo_forcing_timeseries(intervention, lat)
    albedo = albedo * params.get("albedo_scale", 1.0)

    # Run FaIR
    t_pert = run_fair_perturbed(nee, albedo, scenario)
    delta_t = compute_delta_t(t_pert, baseline_temp)
    return find_breakeven_year(delta_t)


def run_oat_sensitivity(
    intervention: str,
    lat: int,
    scenario: str = "ssp245",
) -> dict:
    """One-at-a-time sensitivity analysis.

    Varies each parameter individually to its low and high bound while
    keeping all others at their default values.

    Parameters
    ----------
    intervention : str
        Intervention name.
    lat : int
        Latitude in degrees N.
    scenario : str
        SSP scenario (default ``"ssp245"``).

    Returns
    -------
    dict
        ``{param_name: {"low": val, "high": val, "t_star_low": float, "t_star_high": float}}``
    """
    baseline_temp = run_fair_baseline(scenario)
    results: dict = {}

    for name, (lo, hi) in PARAM_BOUNDS.items():
        # Low bound
        t_star_low = _run_with_params(
            intervention, lat, scenario, baseline_temp, {name: lo}
        )
        # High bound
        t_star_high = _run_with_params(
            intervention, lat, scenario, baseline_temp, {name: hi}
        )
        results[name] = {
            "low": lo,
            "high": hi,
            "t_star_low": t_star_low,
            "t_star_high": t_star_high,
        }

    return results


def run_sobol_sensitivity(
    intervention: str,
    lat: int,
    scenario: str = "ssp245",
    n_samples: int = 256,
) -> dict:
    """Global Sobol sensitivity analysis using SALib.

    Parameters
    ----------
    intervention : str
        Intervention name.
    lat : int
        Latitude in degrees N.
    scenario : str
        SSP scenario (default ``"ssp245"``).
    n_samples : int
        Number of Saltelli samples (default 256).

    Returns
    -------
    dict
        ``{"S1": array, "ST": array, "S1_conf": array, "ST_conf": array, "param_names": list}``
    """
    from SALib.analyze import sobol

    # Use newer sobol sampler if available, fall back to saltelli
    try:
        from SALib.sample import sobol as sobol_sample
        _sample = sobol_sample.sample
    except (ImportError, AttributeError):
        from SALib.sample import saltelli
        _sample = saltelli.sample

    param_names = list(PARAM_BOUNDS.keys())
    problem = {
        "num_vars": len(param_names),
        "names": param_names,
        "bounds": [list(PARAM_BOUNDS[n]) for n in param_names],
    }

    param_values = _sample(problem, n_samples)
    baseline_temp = run_fair_baseline(scenario)

    Y = np.empty(len(param_values))
    for i, row in enumerate(param_values):
        p = dict(zip(param_names, row))
        t_star = _run_with_params(intervention, lat, scenario, baseline_temp, p)
        # Replace inf with T_END + 100 for numerical analysis
        Y[i] = t_star if np.isfinite(t_star) else T_END + 100

    Si = sobol.analyze(problem, Y)

    return {
        "S1": np.asarray(Si["S1"]),
        "ST": np.asarray(Si["ST"]),
        "S1_conf": np.asarray(Si["S1_conf"]),
        "ST_conf": np.asarray(Si["ST_conf"]),
        "param_names": param_names,
    }
