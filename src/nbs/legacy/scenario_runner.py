"""Scenario runner for NBS climate interventions.

Orchestrates carbon, albedo, and FaIR modules to compute delta-T
timeseries for all valid intervention/latitude/scenario combinations.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.legacy.albedo_module import compute_albedo_forcing_timeseries
from nbs.legacy.carbon_module import compute_nee_timeseries
from nbs.fair_module import (
    compute_delta_t,
    find_breakeven_year,
    run_fair_baseline,
    run_fair_perturbed,
)
from nbs.legacy.parameters import INTERVENTIONS, LATITUDES, SCENARIOS

# Valid latitude ranges per intervention (inclusive bounds)
_VALID_LAT_RANGES: dict[str, tuple[int, int]] = {
    "tropical_reforestation": (0, 25),
    "boreal_afforestation": (45, 90),
    "avoided_deforestation": (0, 25),
    "beccs": (0, 60),
}


def is_valid_combination(intervention: str, lat: int) -> bool:
    """Check whether *intervention* is valid at latitude *lat* degrees N."""
    lo, hi = _VALID_LAT_RANGES[intervention]
    return lo <= lat <= hi


def run_single_scenario(
    intervention: str,
    lat: int,
    scenario: str = "ssp245",
    area_mha: float = 1.0,
    baseline_temperature: NDArray | None = None,
) -> dict:
    """Run a single intervention scenario and return results.

    Parameters
    ----------
    intervention : str
        Intervention name.
    lat : int
        Latitude in degrees N.
    scenario : str
        SSP scenario (default ``"ssp245"``).
    area_mha : float
        Area in million hectares (default 1.0).
    baseline_temperature : NDArray or None
        Pre-computed baseline temperature. If None, computed via
        ``run_fair_baseline``.

    Returns
    -------
    dict
        Keys: ``"delta_t"`` (NDArray), ``"t_star"`` (float),
        ``"delta_f_alpha"`` (float), ``"nee"`` (NDArray).
    """
    if baseline_temperature is None:
        baseline_temperature = run_fair_baseline(scenario)

    nee = compute_nee_timeseries(intervention, lat, area_mha=area_mha)
    albedo = compute_albedo_forcing_timeseries(intervention, lat)

    t_pert = run_fair_perturbed(nee, albedo, scenario)
    delta_t = compute_delta_t(t_pert, baseline_temperature)
    t_star = find_breakeven_year(delta_t)

    return {
        "delta_t": delta_t,
        "t_star": t_star,
        "delta_f_alpha": float(albedo[-1]),
        "nee": nee,
    }


def run_all_scenarios(area_mha: float = 1.0) -> dict[tuple[str, int, str], dict]:
    """Run all valid intervention/latitude/scenario combinations.

    Baselines are cached per scenario (3 total). Invalid combinations
    are skipped.

    Returns
    -------
    dict
        Keyed by ``(intervention, lat, scenario)`` tuples.
    """
    # Pre-compute baselines
    baselines: dict[str, NDArray] = {}
    for scenario in SCENARIOS:
        print(f"Computing baseline for {scenario}...")
        baselines[scenario] = run_fair_baseline(scenario)

    results: dict[tuple[str, int, str], dict] = {}
    total = len(INTERVENTIONS) * len(LATITUDES) * len(SCENARIOS)
    done = 0

    for intervention in INTERVENTIONS:
        for lat in LATITUDES:
            for scenario in SCENARIOS:
                done += 1
                if not is_valid_combination(intervention, lat):
                    continue
                print(
                    f"[{done}/{total}] {intervention} | {lat}°N | {scenario}"
                )
                result = run_single_scenario(
                    intervention,
                    lat,
                    scenario=scenario,
                    area_mha=area_mha,
                    baseline_temperature=baselines[scenario],
                )
                results[(intervention, lat, scenario)] = result

    print(f"Completed {len(results)} valid scenarios.")
    return results
