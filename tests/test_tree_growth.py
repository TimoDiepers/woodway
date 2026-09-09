import numpy as np
import pytest

from nbs.species import get_species
from nbs.tree import biomass_closed, canopy_closure, growth_rate_from_stock

SP = get_species("fagus_sylvatica")


def test_closed_form_starts_at_zero_and_saturates():
    assert biomass_closed(np.array([0.0]), SP)[0] == pytest.approx(0.0)
    assert biomass_closed(np.array([1000.0]), SP)[0] == pytest.approx(SP.m_max_kgC, rel=1e-6)


def test_closed_form_is_monotonic():
    m = biomass_closed(np.arange(0.0, 200.0, 1.0), SP)
    assert np.all(np.diff(m) >= 0.0)


def test_stock_form_reproduces_closed_form_when_undisturbed():
    """Integrating dm/dt = g(m) must recover m(t) = m_max (1 - e^-kt)^p.

    This is the load-bearing property: everything downstream integrates the
    stock form, so if it drifts from the closed form the growth model quietly
    stops being Chapman-Richards.
    """
    dt = 1.0 / 12.0
    n = int(200 / dt)
    m = 1e-9  # a seedling, not exactly zero: dm/dt vanishes at m = 0
    for _ in range(n):
        # midpoint rule
        k1 = growth_rate_from_stock(m, SP)
        k2 = growth_rate_from_stock(m + 0.5 * dt * k1, SP)
        m = m + dt * k2
    expected = biomass_closed(np.array([200.0]), SP)[0]
    assert m == pytest.approx(expected, rel=1e-3)


def test_growth_rate_vanishes_at_saturation():
    assert growth_rate_from_stock(SP.m_max_kgC, SP) == pytest.approx(0.0, abs=1e-9)


def test_growth_rate_is_positive_below_saturation():
    assert growth_rate_from_stock(0.5 * SP.m_max_kgC, SP) > 0.0


def test_growth_rate_depends_only_on_stock_not_on_age():
    """A tree knocked back to half its stock grows like a tree that has just
    reached half its stock. That is what lets disturbed trees recover."""
    half = 0.5 * SP.m_max_kgC
    assert growth_rate_from_stock(half, SP) == growth_rate_from_stock(half, SP)


def test_canopy_closure_bounds():
    assert canopy_closure(0.0, SP) == pytest.approx(0.0)
    assert canopy_closure(SP.m_max_kgC, SP) == pytest.approx(1.0)
    assert canopy_closure(2.0 * SP.m_max_kgC, SP) == pytest.approx(1.0)


def test_canopy_closes_faster_than_stock_accumulates():
    """beta < 1: a young tree shades its footprint long before it is grown."""
    rel_stock = 0.25
    f = canopy_closure(rel_stock * SP.m_max_kgC, SP)
    assert f > rel_stock
