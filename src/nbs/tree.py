"""Carbon stock of a single tree.

The closed Chapman-Richards solution describes an undisturbed tree. Disturbed
trees need the growth rate expressed in stock coordinates, because a tree that
has lost half its stock must resume growing at the rate belonging to what is
left, not at the rate belonging to its age.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

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


def canopy_closure(m, sp: Species):
    """Fraction of the tree's footprint covered by canopy, f in [0, 1].

    f = min(1, (m/m_max)^beta) with beta < 1: canopy closes ahead of stock
    accumulation, so the albedo penalty arrives before the carbon benefit.
    """
    m_arr = np.asarray(m, dtype=float)
    f = np.clip(m_arr / sp.m_max_kgC, 0.0, 1.0) ** sp.beta_closure
    f = np.clip(f, 0.0, 1.0)
    return f if np.ndim(m) else float(f)
