"""Carbon stock of a single tree.

The closed Chapman-Richards solution describes an undisturbed tree. Disturbed
trees need the growth rate expressed in stock coordinates, because a tree that
has lost half its stock must resume growing at the rate belonging to what is
left, not at the rate belonging to its age.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from nbs.constants import YEARS
from nbs.species import Species


def biomass_closed(t_yr: NDArray, sp: Species) -> NDArray:
    """Chapman-Richards stock of an undisturbed tree [kgC].

    m(t) = m_max (1 - exp(-k t))^p
    """
    t = np.asarray(t_yr, dtype=float)
    return sp.m_max_kgC * (1.0 - np.exp(-sp.k * t)) ** sp.p


def growth_rate_from_stock(m, sp: Species):
    """Growth rate dm/dt [kgC/a] as a function of stock alone.

    Substituting u = (m/m_max)^(1/p), so that exp(-k t) = 1 - u, turns the
    time derivative of the closed form into

        dm/dt = k p m_max u^(p-1) (1 - u)

    which no longer refers to t.
    """
    m_arr = np.asarray(m, dtype=float)
    u = np.clip(m_arr / sp.m_max_kgC, 0.0, 1.0) ** (1.0 / sp.p)
    rate = sp.k * sp.p * sp.m_max_kgC * u ** (sp.p - 1.0) * (1.0 - u)
    return rate if np.ndim(m) else float(rate)


def advance_stock(m: float, dt: float, sp: Species) -> float:
    """Exact time-dt flow of dm/dt = growth_rate_from_stock(m, sp).

    growth_rate_from_stock exists so a disturbed tree can resume growing at
    the rate belonging to what stock is left, without tracking age. The same
    stock<->age correspondence lets a step advance exactly rather than
    approximately: invert the current stock to its equivalent age under the
    closed form, step that age forward by dt, and read the resulting stock
    back off the closed form.

        u = (m / m_max)^(1/p) = 1 - exp(-k t)  =>  t = -ln(1 - u) / k
        m(t + dt) = biomass_closed(t + dt, sp)

    This has zero truncation error for growth alone: growth, debris decay
    and disturbance are combined by first-order operator splitting in the
    caller, so the coupled integrator is still O(dt) once disturbance is
    active.

    u is clipped to 1 - 1e-12 before inversion so that t stays finite as m
    approaches m_max. That makes m_max a very slightly repelling fixed point
    rather than an attracting one -- about -1.6e-10 kgC lost per step, on
    the order of 2.5e-7 kgC over a full run -- which is expected, not a bug.
    """
    u = min(np.clip(m / sp.m_max_kgC, 0.0, 1.0) ** (1.0 / sp.p), 1.0 - 1e-12)
    t_eff = -np.log(1.0 - u) / sp.k
    return float(biomass_closed(t_eff + dt, sp))


def canopy_closure(m, sp: Species):
    """Fraction of the tree's footprint covered by canopy, f in [0, 1].

    f = min(1, (m/m_max)^beta) with beta < 1: canopy closes ahead of stock
    accumulation, so the albedo penalty arrives before the carbon benefit.
    """
    m_arr = np.asarray(m, dtype=float)
    f = np.clip(m_arr / sp.m_max_kgC, 0.0, 1.0) ** sp.beta_closure
    f = np.clip(f, 0.0, 1.0)
    return f if np.ndim(m) else float(f)


@dataclass(frozen=True)
class TreeTrajectory:
    """One realisation of a tree's carbon over the study period."""

    years: NDArray
    stock_kgC: NDArray
    debris_kgC: NDArray
    closure: NDArray
    net_uptake_kgC_yr: NDArray
    """dE/dt of the ecosystem (tree + debris); positive means uptake."""
    n_disturbances: int


def disturbance_probability(sp: Species, t_background_k: NDArray) -> NDArray:
    """Annual disturbance probability, rising with background warming.

    p(t) = p0 exp(gamma T_background(t)), capped at 1.
    """
    t = np.asarray(t_background_k, dtype=float)
    return np.clip(sp.p_disturb * np.exp(sp.gamma_warming * t), 0.0, 1.0)


def _integrate(
    sp: Species,
    t_background_k: NDArray,
    dt: float,
    rng: np.random.Generator | None,
) -> TreeTrajectory:
    """Shared integrator. ``rng is None`` gives the expected-value run."""
    n_years = len(YEARS)
    p_annual = disturbance_probability(sp, t_background_k)
    steps_per_year = int(round(1.0 / dt))
    if abs(steps_per_year * dt - 1.0) > 1e-9:
        raise ValueError(f"dt={dt} does not divide one year evenly")

    stock = np.zeros(n_years)
    debris = np.zeros(n_years)
    uptake = np.zeros(n_years)

    m = 0.0  # advance_stock's exact step advances a zero seed off the origin cleanly
    d = 0.0
    n_dist = 0

    for iy in range(n_years):
        # record the state *at* YEARS[iy], before integrating that year, so
        # stock[0] is 0 and lines up with biomass_closed(0)
        stock[iy] = m
        debris[iy] = d
        e_before = m + d

        p_step = 1.0 - (1.0 - p_annual[iy]) ** dt

        for _ in range(steps_per_year):
            # growth: exact closed-form step, see advance_stock
            grown = advance_stock(m, dt, sp) - m

            # debris decay
            decayed = d * (1.0 - np.exp(-dt / sp.tau_decay_yr))

            # disturbance
            if rng is None:
                severity = sp.severity_beta[0] / sum(sp.severity_beta)
                lost = p_step * severity * m
            else:
                if rng.random() < p_step:
                    severity = rng.beta(*sp.severity_beta)
                    lost = severity * m
                    n_dist += 1
                else:
                    lost = 0.0

            immediate = sp.eps_immediate * lost  # straight to the atmosphere
            to_debris = lost - immediate

            m = m + grown - lost
            d = d + to_debris - decayed

        uptake[iy] = (m + d) - e_before

    return TreeTrajectory(
        years=YEARS.copy(),
        stock_kgC=stock,
        debris_kgC=debris,
        closure=canopy_closure(stock, sp),
        net_uptake_kgC_yr=uptake,
        n_disturbances=n_dist,
    )


def simulate_deterministic(
    sp: Species, t_background_k: NDArray, dt: float = 1.0 / 12.0
) -> TreeTrajectory:
    """Expected-value run: disturbance drains stock continuously at p * E[s]."""
    return _integrate(sp, t_background_k, dt, rng=None)


def simulate_stochastic(
    sp: Species,
    t_background_k: NDArray,
    rng: np.random.Generator,
    dt: float = 1.0 / 12.0,
) -> TreeTrajectory:
    """One Monte-Carlo realisation with discrete disturbance events."""
    return _integrate(sp, t_background_k, dt, rng=rng)


def simulate_ensemble(
    sp: Species,
    t_background_k: NDArray,
    n_members: int = 1000,
    seed: int = 0,
    dt: float = 1.0 / 12.0,
) -> list[TreeTrajectory]:
    """``n_members`` independent realisations from one seed sequence."""
    seeds = np.random.SeedSequence(seed).spawn(n_members)
    return [
        simulate_stochastic(sp, t_background_k, np.random.default_rng(s), dt)
        for s in seeds
    ]
