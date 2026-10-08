"""The full chain for one tree at one place: stock, forcing, temperature."""

from __future__ import annotations

from functools import lru_cache

import dataclasses
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from nbs.config import ModelConfig
from nbs.constants import T_START, YEARS
from nbs.forcing import (
    co2_flux_kg_per_yr,
    fallback_delta_alpha,
    fallback_q_sw,
    phi_albedo,
    phi_co2,
    phi_co2_background,
)
from nbs.response import (
    background_co2_ppm,
    convolve_response,
    green_carbon,
    green_carbon_preindustrial,
    green_temperature,
)
from nbs.site_factor import site_factor
from nbs.species import get_species
from nbs.tree import (
    TreeTrajectory,
    simulate_deterministic,
    simulate_ensemble,
    simulate_stochastic,
)


@dataclass(frozen=True)
class SiteResult:
    """Everything the results slides need for one tree at one site."""

    species_key: str
    lat_deg: float
    scenario: str
    years: NDArray
    phi_co2: NDArray
    phi_albedo: NDArray
    phi_total: NDArray
    delta_t: NDArray
    trajectory: TreeTrajectory
    plant_year: int
    """Calendar year the tree was planted. The time axis is the common YEARS
    grid regardless, so cohorts planted in different years can be compared on
    one figure without realigning anything."""
    config: ModelConfig
    """The model-complexity switches (nbs.config.ModelConfig) that produced
    this result. Carried on the result itself so several variants can sit in
    one figure without losing track of what generated each one."""


def _background_temperature(scenario: str) -> NDArray:
    """Pad FaIR's 125-year baseline temperature series to the 126-year study axis.

    Raises ValueError if the input is not exactly one element shorter than
    YEARS: silently appending one value regardless of the actual gap would
    otherwise produce a truncated background series with no error if
    fair_module's window ever changed.
    """
    from nbs.fair_module import run_fair_baseline

    base = run_fair_baseline(scenario)
    if len(base) != len(YEARS) - 1:
        raise ValueError(
            f"expected a series of length {len(YEARS) - 1}, got {len(base)}"
        )
    return np.append(base, base[-1])


def _green_carbon_for(config: ModelConfig, scenario: str) -> NDArray:
    """g_C selected by config.carbon_sink (slide 13)."""
    if config.carbon_sink == "preindustrial":
        return green_carbon_preindustrial()
    return green_carbon(scenario)


def _species_for(species_key: str, config: ModelConfig, lat_deg: float, lon_deg: float | None = None):
    """The species used for growth/disturbance integration at *lat_deg*:
    growth level scaled by the site factor (``nbs.site_factor``) when
    config.site_growth, p_disturb zeroed when config.disturbance == "off".
    Never mutates the frozen registry entry -- dataclasses.replace returns a
    new instance."""
    sp = get_species(species_key)
    if config.site_growth:
        sp = dataclasses.replace(sp, m_max_kgC=sp.m_max_kgC * site_factor(species_key, lat_deg, lon_deg))
    if config.disturbance == "off":
        sp = dataclasses.replace(sp, p_disturb=0.0)
    return sp


@lru_cache(maxsize=None)
def typical_product(species_key: str) -> float:
    """Area-weighted mean measured albedo product Delta-alpha*q [W/m^2] over
    the cells where *species_key* is the typical forest."""
    from nbs.albedo_grid import alpha_q_product
    from nbs.landscape import assign_species, plantable_area_m2

    cells = assign_species() == species_key
    if not cells.any():
        from nbs.forest_data import admissible_types

        cells = admissible_types()[species_key.split("_")[0]]
    a = plantable_area_m2()[cells]
    prod = alpha_q_product(species_key)[cells]
    ok = np.isfinite(prod) & (a > 0)
    return float(np.average(prod[ok], weights=a[ok]))


def _forcings(
    trajectory: TreeTrajectory,
    species_key: str,
    lat_deg: float,
    scenario: str,
    delta_alpha: float | None,
    q_sw: float | None,
    config: ModelConfig,
) -> tuple[NDArray, NDArray]:
    sp = get_species(species_key)
    if delta_alpha is None and q_sw is None:
        # No site cell given: the forest type's measured mean (Duveiller),
        # not the old latitude table (nbs.forcing.fallback_*), which knew
        # nothing about forest types (2026-10-05).
        d_alpha, q = typical_product(species_key), 1.0
    else:
        d_alpha = fallback_delta_alpha(lat_deg) if delta_alpha is None else delta_alpha
        q = fallback_q_sw(lat_deg) if q_sw is None else q_sw

    flux = co2_flux_kg_per_yr(trajectory.net_uptake_kgC_yr)
    g_c = _green_carbon_for(config, scenario)
    if config.co2_forcing == "linear":
        f_co2 = phi_co2(flux, g_c)
    else:
        f_co2 = phi_co2_background(flux, g_c, background_co2_ppm(scenario))

    if config.albedo:
        f_alb = phi_albedo(trajectory.closure, d_alpha, q, sp)
    else:
        f_alb = np.zeros_like(trajectory.closure, dtype=float)

    return f_co2, f_alb


def run_single_tree(
    species_key: str,
    lat_deg: float,
    scenario: str = "ssp245",
    delta_alpha: float | None = None,
    q_sw: float | None = None,
    config: ModelConfig | None = None,
    seed: int = 0,
    plant_year: int = T_START,
    lon_deg: float | None = None,
) -> SiteResult:
    """One tree, one place, under the model-complexity choices in *config*.

    ``config.disturbance`` selects the integrator: "off" and "deterministic"
    both use the expected-value integrator (the former on a species with
    p_disturb forced to zero, so it degenerates to the undisturbed case);
    "stochastic" draws a single seeded Monte-Carlo realisation via *seed*
    rather than the full ensemble (see ``run_single_tree_ensemble`` for
    that).
    """
    if config is None:
        config = ModelConfig()
    sp = _species_for(species_key, config, lat_deg, lon_deg)
    background = _background_temperature(scenario)
    if config.disturbance == "stochastic":
        rng = np.random.default_rng(seed)
        traj = simulate_stochastic(sp, background, rng, plant_year=plant_year)
    else:
        traj = simulate_deterministic(sp, background, plant_year=plant_year)
    f_co2, f_alb = _forcings(
        traj, species_key, lat_deg, scenario, delta_alpha, q_sw, config
    )
    phi = f_co2 + f_alb
    delta_t = convolve_response(green_temperature(scenario), phi)

    return SiteResult(
        species_key=species_key,
        lat_deg=lat_deg,
        scenario=scenario,
        years=YEARS.copy(),
        phi_co2=f_co2,
        phi_albedo=f_alb,
        phi_total=phi,
        delta_t=delta_t,
        trajectory=traj,
        plant_year=plant_year,
        config=config,
    )


def run_single_tree_ensemble(
    species_key: str,
    lat_deg: float,
    scenario: str = "ssp245",
    n_members: int = 1000,
    seed: int = 0,
    delta_alpha: float | None = None,
    q_sw: float | None = None,
    config: ModelConfig | None = None,
    plant_year: int = T_START,
    lon_deg: float | None = None,
) -> tuple[SiteResult, NDArray]:
    """Deterministic (or config-selected) run plus a Monte-Carlo ensemble.

    The ensemble members themselves are always drawn from the discrete
    stochastic integrator (that is the point of an ensemble); the config's
    disturbance switch only matters here through "off", which zeroes
    p_disturb on the species used for every member, collapsing the ensemble
    to a single deterministic trajectory with zero spread. Every other
    switch (co2_forcing, albedo, carbon_sink) is respected for both the
    single companion run and every ensemble member.
    """
    if config is None:
        config = ModelConfig()
    sp = _species_for(species_key, config, lat_deg, lon_deg)
    background = _background_temperature(scenario)
    deterministic = run_single_tree(
        species_key,
        lat_deg,
        scenario,
        delta_alpha,
        q_sw,
        config=config,
        seed=seed,
        plant_year=plant_year,
        lon_deg=lon_deg,
    )

    g_t = green_temperature(scenario)
    members = simulate_ensemble(
        sp, background, n_members=n_members, seed=seed, plant_year=plant_year
    )

    ensemble = np.empty((n_members, len(YEARS)))
    for i, traj in enumerate(members):
        f_co2, f_alb = _forcings(
            traj, species_key, lat_deg, scenario, delta_alpha, q_sw, config
        )
        ensemble[i] = convolve_response(g_t, f_co2 + f_alb)

    return deterministic, ensemble
