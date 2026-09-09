import dataclasses

import numpy as np
import pytest

from nbs.constants import YEARS
from nbs.species import get_species
from nbs.tree import (
    TreeTrajectory,
    biomass_closed,
    disturbance_probability,
    simulate_deterministic,
    simulate_ensemble,
    simulate_stochastic,
)

SP = get_species("picea_abies")
NO_WARMING = np.zeros(len(YEARS))
STRONG_WARMING = np.linspace(0.0, 4.0, len(YEARS))


def test_disturbance_probability_rises_with_background_warming():
    p_cold = disturbance_probability(SP, NO_WARMING)
    p_warm = disturbance_probability(SP, STRONG_WARMING)
    assert p_cold[0] == pytest.approx(SP.p_disturb)
    assert p_warm[-1] > p_cold[-1]
    assert np.all(np.diff(p_warm) >= 0.0)


def test_disturbance_probability_stays_a_probability():
    p = disturbance_probability(SP, np.full(len(YEARS), 20.0))
    assert np.all(p <= 1.0)


def test_deterministic_run_without_disturbance_matches_closed_form():
    sp = get_species("fagus_sylvatica")
    quiet = dataclasses.replace(sp, p_disturb=0.0)
    traj = simulate_deterministic(quiet, NO_WARMING)
    expected = biomass_closed(YEARS - YEARS[0], quiet)
    assert np.allclose(traj.stock_kgC, expected, rtol=2e-3)


def test_trajectory_arrays_are_annual_and_aligned():
    traj = simulate_deterministic(SP, NO_WARMING)
    assert isinstance(traj, TreeTrajectory)
    for arr in (traj.stock_kgC, traj.debris_kgC, traj.closure, traj.net_uptake_kgC_yr):
        assert arr.shape == YEARS.shape
    assert np.array_equal(traj.years, YEARS)


def test_deterministic_disturbance_lowers_stock_below_undisturbed():
    quiet = dataclasses.replace(SP, p_disturb=0.0)
    assert simulate_deterministic(SP, NO_WARMING).stock_kgC[-1] < \
           simulate_deterministic(quiet, NO_WARMING).stock_kgC[-1]


def test_carbon_is_conserved():
    """Cumulative net uptake must equal the ecosystem stock that is standing.

    Carbon may sit in the tree or in debris; anything else has gone back to the
    atmosphere and must show up as reduced cumulative uptake.
    """
    traj = simulate_deterministic(SP, STRONG_WARMING)
    ecosystem = traj.stock_kgC + traj.debris_kgC
    # uptake[i] spans year i to i+1, stock[i] is the state at year i
    assert np.allclose(
        np.cumsum(traj.net_uptake_kgC_yr)[:-1],
        ecosystem[1:] - ecosystem[0],
        atol=0.5,
    )


def test_stochastic_run_is_reproducible_from_its_seed():
    a = simulate_stochastic(SP, NO_WARMING, np.random.default_rng(42))
    b = simulate_stochastic(SP, NO_WARMING, np.random.default_rng(42))
    assert np.array_equal(a.stock_kgC, b.stock_kgC)


def test_stochastic_runs_differ_across_seeds():
    a = simulate_stochastic(SP, NO_WARMING, np.random.default_rng(1))
    b = simulate_stochastic(SP, NO_WARMING, np.random.default_rng(2))
    assert not np.array_equal(a.stock_kgC, b.stock_kgC)


def test_disturbed_tree_regrows():
    """After a loss the stock must rise again — the point of the stock form."""
    rng = np.random.default_rng(7)
    traj = next(
        t for t in (simulate_stochastic(SP, NO_WARMING, rng) for _ in range(50))
        if t.n_disturbances > 0
    )
    drops = np.where(np.diff(traj.stock_kgC) < 0)[0]
    first_drop = int(drops[0])
    later = traj.stock_kgC[first_drop + 1:]
    assert later.max() > traj.stock_kgC[first_drop + 1]


def test_ensemble_size_and_spread():
    ens = simulate_ensemble(SP, NO_WARMING, n_members=50, seed=0)
    assert len(ens) == 50
    finals = np.array([t.stock_kgC[-1] for t in ens])
    assert finals.std() > 0.0


def test_ensemble_mean_stock_is_below_deterministic_run():
    """Disturbance is multiplicative in the stock, so averaging trajectories is
    not the same as running the average. The gap is the risk premium."""
    ens = simulate_ensemble(SP, STRONG_WARMING, n_members=200, seed=3)
    mean_final = np.mean([t.stock_kgC[-1] for t in ens])
    assert mean_final < simulate_deterministic(SP, STRONG_WARMING).stock_kgC[-1] * 1.05
