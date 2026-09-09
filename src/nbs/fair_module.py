"""FaIR v2.2.4 coupling module for NBS climate interventions.

Runs baseline and perturbed FaIR scenarios, computes temperature
differences (delta-T), and finds break-even years.
"""

from __future__ import annotations

import functools

import numpy as np
from numpy.typing import NDArray

from fair import FAIR
from fair.interface import fill, initialise
from fair.io import read_properties

from nbs.legacy.parameters import T_START, T_END

# Index offsets: FaIR time axis starts at 1750
_START_IDX = T_START - 1750  # 275
_END_IDX = T_END - 1750      # 400


def _create_fair(scenario: str = "ssp245") -> FAIR:
    """Create and configure a FaIR instance with AR6-calibrated parameters."""
    f = FAIR(ch4_method="Thornhill2021")
    f.define_time(1750, 2150, 1)
    f.define_scenarios([scenario])
    f.define_configs(["central"])

    species, properties = read_properties()
    f.define_species(species, properties)
    f.allocate()
    f.fill_from_rcmip()
    f.fill_species_configs()

    # EBM parameters (AR6 calibrated)
    for i, val in enumerate([3.18, 8.95, 142.73]):
        fill(f.climate_configs["ocean_heat_capacity"], val, config="central", layer=i)
    for i, val in enumerate([0.65, 2.15, 0.67]):
        fill(f.climate_configs["ocean_heat_transfer"], val, config="central", layer=i)
    fill(f.climate_configs["deep_ocean_efficacy"], 1.28, config="central")
    fill(f.climate_configs["stochastic_run"], False, config="central")
    fill(f.climate_configs["forcing_4co2"], 7.33, config="central")
    fill(f.climate_configs["sigma_eta"], 0.5, config="central")
    fill(f.climate_configs["sigma_xi"], 0.5, config="central")
    fill(f.climate_configs["gamma_autocorrelation"], 2.0, config="central")
    fill(f.climate_configs["seed"], 0, config="central")
    fill(f.climate_configs["use_seed"], False, config="central")

    # Initialise state variables at t=0
    initialise(f.concentration, 0, specie="CO2", config="central", scenario=scenario)
    initialise(f.forcing, 0, config="central", scenario=scenario)
    initialise(f.temperature, 0, config="central", scenario=scenario)
    initialise(f.airborne_emissions, 0, config="central", scenario=scenario)
    initialise(f.cumulative_emissions, 0, config="central", scenario=scenario)

    return f


@functools.lru_cache(maxsize=4)
def run_fair_baseline(scenario: str = "ssp245") -> NDArray:
    """Run an unperturbed FaIR scenario and return surface temperature.

    Returns
    -------
    NDArray, shape (T_END - T_START,)
        Surface temperature anomaly [K] for the study period.
    """
    f = _create_fair(scenario)
    f.run()
    temp = (
        f.temperature.sel(scenario=scenario, config="central", layer=0)
        .values[_START_IDX:_END_IDX]
    )
    return np.asarray(temp, dtype=np.float64)


def run_fair_perturbed(
    nee_gtco2_yr: NDArray,
    albedo_rf_wm2: NDArray,
    scenario: str = "ssp245",
) -> NDArray:
    """Run a perturbed FaIR scenario and return surface temperature.

    Parameters
    ----------
    nee_gtco2_yr : NDArray, shape (125,)
        Net ecosystem exchange [GtCO2/yr]. Negative = removal.
    albedo_rf_wm2 : NDArray, shape (125,)
        Albedo radiative forcing [W/m^2]. Positive = warming.
    scenario : str
        SSP scenario name (default ``"ssp245"``).

    Returns
    -------
    NDArray, shape (125,)
        Surface temperature anomaly [K] for the study period.
    """
    f = _create_fair(scenario)

    # Add NEE to CO2 FFI emissions (timepoints, shape 400,1,1)
    co2_vals = f.emissions.sel(specie="CO2 FFI").values.copy()
    co2_vals[_START_IDX:_END_IDX, 0, 0] += nee_gtco2_yr
    f.emissions.loc[dict(specie="CO2 FFI")] = co2_vals

    # Add albedo perturbation to Solar forcing (timebounds, shape 401,1,1).
    # FaIR initialises forcing to 0; Solar forcing is externally prescribed
    # (not computed from emissions), so pre-run values are carried through.
    solar_vals = f.forcing.sel(specie="Solar").values.copy()
    solar_vals[_START_IDX:_END_IDX, 0, 0] += albedo_rf_wm2
    f.forcing.loc[dict(specie="Solar")] = solar_vals

    f.run()

    temp = (
        f.temperature.sel(scenario=scenario, config="central", layer=0)
        .values[_START_IDX:_END_IDX]
    )
    return np.asarray(temp, dtype=np.float64)


def compute_pulse_warming(
    pulse_gtco2: float = 1.0,
    scenario: str = "ssp245",
) -> NDArray:
    """Temperature impact of an instantaneous CO2 emission pulse at T_START.

    Runs FaIR with a single-year emission spike and returns the temperature
    difference relative to the unperturbed baseline.

    Parameters
    ----------
    pulse_gtco2 : float
        Size of the emission pulse [GtCO2] (default 1.0).
    scenario : str
        Background SSP scenario (default "ssp245").

    Returns
    -------
    NDArray, shape (T_END - T_START,)
        ΔT(t) from the pulse [K]. Positive = warming.
    """
    baseline = run_fair_baseline(scenario)

    f = _create_fair(scenario)

    # Add pulse at T_START only (single year)
    co2_vals = f.emissions.sel(specie="CO2 FFI").values.copy()
    co2_vals[_START_IDX, 0, 0] += pulse_gtco2
    f.emissions.loc[dict(specie="CO2 FFI")] = co2_vals

    f.run()

    temp = (
        f.temperature.sel(scenario=scenario, config="central", layer=0)
        .values[_START_IDX:_END_IDX]
    )
    perturbed = np.asarray(temp, dtype=np.float64)

    return perturbed - baseline


def compute_delta_t(t_perturbed: NDArray, t_baseline: NDArray) -> NDArray:
    """Compute temperature difference between perturbed and baseline runs.

    Returns
    -------
    NDArray
        ``t_perturbed - t_baseline``. Negative values indicate cooling.
    """
    return t_perturbed - t_baseline


def find_breakeven_year(delta_t: NDArray) -> float:
    """Find the year from which the intervention stays net cooling.

    Not the *first* year with ``delta_t <= 0`` — at the start of the run neither
    the emission nor the forest has had any effect yet, so that year would always
    be the first one. The break-even year is the year after the last sign change:
    from here on the net effect never turns positive again.

    Parameters
    ----------
    delta_t : NDArray, shape (125,)
        Temperature difference time series.

    Returns
    -------
    float
        Calendar year of lasting net cooling, or ``np.inf`` if it never happens.
    """
    warming_indices = np.where(delta_t > 0)[0]
    if len(warming_indices) == 0:
        return float(T_START)
    last_warming = int(warming_indices[-1])
    if last_warming >= len(delta_t) - 1:
        return np.inf
    return float(T_START + last_warming + 1)
