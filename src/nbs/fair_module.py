"""FaIR v2.2.4 coupling module for NBS climate interventions.

Runs baseline and perturbed FaIR scenarios, computes temperature
differences (delta-T), and finds break-even years.
"""

from __future__ import annotations

import functools
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from fair import FAIR
from fair.interface import fill, initialise
from fair.io import read_properties

from nbs.legacy.parameters import T_START, T_END

# Index offsets: FaIR time axis starts at 1750
_START_IDX = T_START - 1750
_END_IDX = T_END - 1750      # 350


# fair-calibrate v1.4.1 (Smith et al. 2024, GMD 17, 8569): the constrained
# 841-member ensemble FaIR's own documentation uses, run without internal
# variability. "central" is one member of it, chosen by
# scripts/select_fair_member.py as the one closest to the ensemble median at
# once in historical warming (2011-2020: 1.08 K, observed 1.09; 2015-2024)
# and in 2081-2100 warming under SSP1-2.6/2-4.5/3-7.0/5-8.5 (1.83 / 2.62 /
# 3.21 / 4.10 K; IPCC AR6: 1.8 / 2.7 / 3.6 / 4.4). ECS 2.9 K.
# Emissions are RCMIP, as in FaIR's SSP example; with them the whole
# ensemble reaches about 403 ppm CO2 in 2020 (observed 412).
# This replaces hand-set EBM parameters whose feedback (0.65 W/m^2/K) meant
# an ECS of about 5.6 K and SSP2-4.5 warming of 3.5 K by 2100.
_CALIBRATION = Path(__file__).resolve().parents[2] / "data" / "fair_calibrate_1.4.1"
_PARAMS_CSV = _CALIBRATION / "calibrated_constrained_parameters_calibration1.4.1.csv"
_SPECIES_CSV = _CALIBRATION / "species_configs_properties_calibration1.4.1.csv"
CENTRAL_MEMBER = 787474

# Temperatures are reported relative to 1850-1900, the reference of the
# Paris 1.5 degC target and of the IPCC assessment (timebounds 1850..1900).
_PRE_SLICE = slice(1850 - 1750, 1900 - 1750 + 1)


@functools.lru_cache(maxsize=1)
def _central_params_csv() -> str:
    """The chosen member's parameter row as a one-row CSV indexed 'central'
    (FAIR.override_defaults reads its configs from a file)."""
    df = pd.read_csv(_PARAMS_CSV, index_col=0)
    row = df.loc[[CENTRAL_MEMBER]].copy()
    row.index = ["central"]
    path = Path(tempfile.mkdtemp(prefix="fair_central_")) / "central.csv"
    row.to_csv(path)
    return str(path)


_CMIP7_INPUTS = Path(__file__).resolve().parents[2] / "data" / "cmip7" / "fair-inputs"


@functools.lru_cache(maxsize=None)
def _cmip7_inputs(scenario: str) -> tuple[str, str]:
    """(emissions file, forcing file) of one CMIP7 marker, with the scenario column renamed to *scenario*
    ("cmip7-VL", ...), so that FaIR's arrays carry the same name as every other scenario in this module."""
    code = scenario.removeprefix("cmip7-")
    d = Path(tempfile.mkdtemp(prefix=f"fair_{code}_"))
    em = pd.read_csv(_CMIP7_INPUTS / "emissions_1750-2500.csv")
    em = em[em["scenario"] == code].drop(columns=["long_scenario"]).copy()
    em["scenario"] = scenario
    fo = pd.read_csv(_CMIP7_INPUTS / "volcanic_solar.csv")
    fo = fo[fo["Scenario"] == code].copy()
    fo["Scenario"] = scenario
    em.to_csv(d / "emissions.csv", index=False)
    fo.to_csv(d / "forcing.csv", index=False)
    return str(d / "emissions.csv"), str(d / "forcing.csv")


def _create_fair(scenario: str = "ssp245") -> FAIR:
    """FaIR with the constrained fair-calibrate 1.4.1 parameters (one member)."""
    f = FAIR(ch4_method="Thornhill2021")
    f.define_time(1750, T_END, 1)
    f.define_scenarios([scenario])
    f.define_configs(["central"])

    species, properties = read_properties(filename=str(_SPECIES_CSV))
    f.define_species(species, properties)
    f.allocate()
    if scenario.startswith("cmip7-"):
        # CMIP7 marker scenarios (VL, LN, L, ML, M, H, HL): emissions and volcanic/solar forcing as the
        # ScenarioMIP description paper runs them (van Vuuren et al. 2026; scripts/run_fair_simulations.py
        # of its archive: fill_from_csv, then solar forcing set to zero)
        emis, forc = _cmip7_inputs(scenario)
        # fair registers unknown unit spellings of the CSV (e.g. "kt HFC4310/yr") in its module-wide unit
        # tables; that breaks every later fill_from_rcmip in the same process (KeyError 'HFC4310'), so the
        # tables are restored afterwards
        import copy

        from fair.structure import units as fair_units

        saved = {k: copy.deepcopy(getattr(fair_units, k))
                 for k in ("compound_convert", "desired_emissions_units", "desired_concentration_units")}
        try:
            f.fill_from_csv(forcing_file=forc, emissions_file=emis)
        finally:
            for k, v in saved.items():
                getattr(fair_units, k).clear()
                getattr(fair_units, k).update(v)
        f.forcing.loc[dict(scenario=scenario, specie="Solar")] = 0
    else:
        f.fill_from_rcmip()
    f.fill_species_configs(str(_SPECIES_CSV))
    f.override_defaults(_central_params_csv())
    # The calibration samples internal variability (stochastic_run=True,
    # sigma_eta/sigma_xi). The model needs the forced response: a smooth
    # baseline, and pulse responses that are not differences of noise.
    fill(f.climate_configs["stochastic_run"], False, config="central")

    initialise(f.concentration, f.species_configs["baseline_concentration"])
    initialise(f.forcing, 0)
    initialise(f.temperature, 0)
    initialise(f.cumulative_emissions, 0)
    initialise(f.airborne_emissions, 0)
    initialise(f.ocean_heat_content_change, 0)
    return f


def _surface_temperature(f: FAIR, scenario: str) -> NDArray:
    """Study-window surface temperature [K] relative to 1850-1900."""
    temp = np.asarray(
        f.temperature.sel(scenario=scenario, config="central", layer=0).values, dtype=np.float64
    )
    return temp[_START_IDX:_END_IDX] - temp[_PRE_SLICE].mean()


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
    return _surface_temperature(f, scenario)


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

    return _surface_temperature(f, scenario)


def run_fair_emission_delta(delta: dict[str, NDArray], scenario: str = "cmip7-VL") -> NDArray:
    """FaIR with changed emissions of some species over the study period (e.g. {"CH4": -x [Mt CH4/a],
    "N2O": -y [kt N2O/a]}), in the units of the scenario's emission file. Surface temperature as run_fair_baseline."""
    f = _create_fair(scenario)
    for specie, d in delta.items():
        vals = f.emissions.sel(specie=specie).values.copy()
        vals[_START_IDX:_END_IDX, 0, 0] += np.asarray(d, dtype=float)
        f.emissions.loc[dict(specie=specie)] = vals
    f.run()
    return _surface_temperature(f, scenario)


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

    return _surface_temperature(f, scenario) - baseline


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
