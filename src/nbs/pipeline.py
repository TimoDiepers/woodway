"""The full chain for one tree at one place: stock, forcing, temperature."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from nbs.constants import YEARS
from nbs.forcing import (
    co2_flux_kg_per_yr,
    fallback_delta_alpha,
    fallback_q_sw,
    phi_albedo,
    phi_co2,
)
from nbs.response import convolve_response, green_carbon, green_temperature
from nbs.species import get_species
from nbs.tree import TreeTrajectory, simulate_deterministic, simulate_ensemble


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


def _background_temperature(scenario: str) -> NDArray:
    from nbs.fair_module import run_fair_baseline

    base = run_fair_baseline(scenario)
    if len(base) == len(YEARS):
        return base
    return np.append(base, base[-1])


def _forcings(
    trajectory: TreeTrajectory,
    species_key: str,
    lat_deg: float,
    scenario: str,
    delta_alpha: float | None,
    q_sw: float | None,
) -> tuple[NDArray, NDArray]:
    sp = get_species(species_key)
    d_alpha = fallback_delta_alpha(lat_deg) if delta_alpha is None else delta_alpha
    q = fallback_q_sw(lat_deg) if q_sw is None else q_sw

    f_co2 = phi_co2(
        co2_flux_kg_per_yr(trajectory.net_uptake_kgC_yr), green_carbon(scenario)
    )
    f_alb = phi_albedo(trajectory.closure, d_alpha, q, sp)
    return f_co2, f_alb


def run_single_tree(
    species_key: str,
    lat_deg: float,
    scenario: str = "ssp245",
    delta_alpha: float | None = None,
    q_sw: float | None = None,
) -> SiteResult:
    """Deterministic run: one tree, one place, expected-value disturbance."""
    sp = get_species(species_key)
    background = _background_temperature(scenario)
    traj = simulate_deterministic(sp, background)
    f_co2, f_alb = _forcings(traj, species_key, lat_deg, scenario, delta_alpha, q_sw)
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
    )


def run_single_tree_ensemble(
    species_key: str,
    lat_deg: float,
    scenario: str = "ssp245",
    n_members: int = 1000,
    seed: int = 0,
    delta_alpha: float | None = None,
    q_sw: float | None = None,
) -> tuple[SiteResult, NDArray]:
    """Deterministic run plus a Monte-Carlo ensemble of delta_t trajectories."""
    sp = get_species(species_key)
    background = _background_temperature(scenario)
    deterministic = run_single_tree(species_key, lat_deg, scenario, delta_alpha, q_sw)

    g_t = green_temperature(scenario)
    members = simulate_ensemble(sp, background, n_members=n_members, seed=seed)

    ensemble = np.empty((n_members, len(YEARS)))
    for i, traj in enumerate(members):
        f_co2, f_alb = _forcings(traj, species_key, lat_deg, scenario, delta_alpha, q_sw)
        ensemble[i] = convolve_response(g_t, f_co2 + f_alb)

    return deterministic, ensemble
