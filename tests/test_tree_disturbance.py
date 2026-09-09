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
    # SP.p_disturb * exp(SP.gamma_warming * T) only exceeds 1 above about
    # 22.1 K for picea_abies; 30 K is comfortably past that so the clip(...,
    # 0.0, 1.0) in disturbance_probability is actually exercised here.
    p = disturbance_probability(SP, np.full(len(YEARS), 30.0))
    assert SP.p_disturb * np.exp(SP.gamma_warming * 30.0) > 1.0, "clamp must be binding at this temperature"
    assert np.all(p <= 1.0)
    assert np.all(p == pytest.approx(1.0))


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


def test_uptake_array_is_internally_consistent_with_recorded_state():
    """Bookkeeping alignment check only -- NOT a proof of conservation.

    net_uptake_kgC_yr[i] is *defined* inside _integrate as
    (stock+debris)_after minus (stock+debris)_before for year i, and
    stock/debris[i] are read from that same running state. So
    cumsum(uptake)[:-1] == ecosystem[1:] - ecosystem[0] is an algebraic
    identity: it holds even if eps_immediate were 1.0, if to_debris were
    always zero, or if a disturbance silently discarded carbon outright, as
    long as the (m+d) before/after values used to fill both arrays agree.
    What it *does* catch is an off-by-one or misaligned write between the
    two arrays (e.g. uptake recorded against the wrong year's stock), which
    is a real and different bug class from broken conservation -- hence the
    rename and the separate test below for the split itself.
    """
    traj = simulate_deterministic(SP, STRONG_WARMING)
    ecosystem = traj.stock_kgC + traj.debris_kgC
    # uptake[i] spans year i to i+1, stock[i] is the state at year i
    assert np.allclose(
        np.cumsum(traj.net_uptake_kgC_yr)[:-1],
        ecosystem[1:] - ecosystem[0],
        atol=0.5,
    )


def test_disturbance_moves_carbon_to_debris_not_out_of_the_ecosystem():
    """The thing test_carbon_is_conserved was supposed to protect against:
    that a disturbance is an internal transfer, and only the eps_immediate
    fraction actually leaves the ecosystem (as combustion), the rest landing
    in debris rather than vanishing. This computes the ecosystem carbon
    change independently of net_uptake_kgC_yr, from stock/debris alone, and
    checks it against the disturbance parameters directly -- so it would
    fail if e.g. immediate carbon were also routed to debris, if
    eps_immediate were ignored, or if lost carbon were discarded outright
    instead of split.

    Growth is suppressed by using a fast-saturating species and reading the
    transition in the next-to-last year, where stock is essentially pinned
    at m_max (growth well below 1e-5 kgC/yr there); decay is suppressed
    because, with disturbance probability held at ~0 everywhere except one
    spiked year, no debris has had a chance to accumulate yet when the event
    fires. dt=1.0 makes that spiked year exactly one disturbance step, so the
    recorded transition *is* the single event.
    """
    sp = dataclasses.replace(get_species("eucalyptus_grandis"), p_disturb=1e-9)
    spike_idx = len(YEARS) - 2
    t_background = np.zeros(len(YEARS))
    t_background[spike_idx] = 200.0  # forces p_annual to clip to 1.0 there

    traj = simulate_deterministic(sp, t_background, dt=1.0)
    m_before = traj.stock_kgC[spike_idx]
    assert m_before == pytest.approx(sp.m_max_kgC, rel=1e-3)  # growth suppressed
    assert traj.debris_kgC[spike_idx] < 1e-4  # decay suppressed: nothing to decay yet

    severity = sp.severity_beta[0] / sum(sp.severity_beta)
    lost = severity * m_before  # p_step == 1.0 at the spike

    e_before = m_before + traj.debris_kgC[spike_idx]
    e_after = traj.stock_kgC[spike_idx + 1] + traj.debris_kgC[spike_idx + 1]
    assert (e_after - e_before) == pytest.approx(-sp.eps_immediate * lost, abs=1e-3)


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
    not the same as running the average. The gap is the risk premium
    (Jensen's inequality), and its sign is guaranteed asymptotically -- so
    once the ensemble is large enough to shrink sampling noise well below the
    gap, the comparison should be strict rather than padded with slack that
    would also pass a zero or reversed effect."""
    ens = simulate_ensemble(SP, STRONG_WARMING, n_members=1000, seed=3)
    mean_final = np.mean([t.stock_kgC[-1] for t in ens])
    assert mean_final < simulate_deterministic(SP, STRONG_WARMING).stock_kgC[-1]
