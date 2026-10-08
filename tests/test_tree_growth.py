import numpy as np
import pytest

from nbs.species import get_species
from nbs.tree import advance_stock, biomass_closed, canopy_closure, growth_rate_from_stock

SP = get_species("dbf_gemaessigt")


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


def test_advance_stock_matches_growth_rate_from_stock_in_the_small_dt_limit():
    """advance_stock must solve the ODE growth_rate_from_stock states, not a
    different one: this is the only thing pinning the exact-step integrator
    to the model it claims to be exact for. If growth_rate_from_stock ever
    changes (a mortality term, a temperature dependence, a different p
    convention) without a matching change to advance_stock, this is the test
    that must catch it."""
    sp = get_species("enf_boreal")
    dt = 1e-5
    for m in (0.01 * sp.m_max_kgC, 0.25 * sp.m_max_kgC, 0.5 * sp.m_max_kgC, 0.8 * sp.m_max_kgC):
        finite_diff_rate = (advance_stock(m, dt, sp) - m) / dt
        assert finite_diff_rate == pytest.approx(growth_rate_from_stock(m, sp), rel=1e-4)


def test_growth_rate_vanishes_at_saturation():
    assert growth_rate_from_stock(SP.m_max_kgC, SP) == pytest.approx(0.0, abs=1e-9)


def test_growth_rate_is_positive_below_saturation():
    assert growth_rate_from_stock(0.5 * SP.m_max_kgC, SP) > 0.0


def test_canopy_closure_bounds():
    assert canopy_closure(0.0, SP) == pytest.approx(0.0)
    assert canopy_closure(SP.m_max_kgC, SP) == pytest.approx(1.0)
    assert canopy_closure(2.0 * SP.m_max_kgC, SP) == pytest.approx(1.0)


def test_albedo_effect_reaches_half_after_forty_years():
    """Williams et al. (2026): about half of the albedo decline after
    reforestation within 40 years, 80 % only after 50-120 years. The canopy
    closure drives the albedo channel, so it must follow that timing --
    slower than a young tree's stock (beta > 1), not faster as assumed
    before 2026-10-05 (beta = 0.5)."""
    from nbs.species import SPECIES

    for key, sp in SPECIES.items():
        f = lambda t: canopy_closure(float(biomass_closed(np.array([t]), sp)[0]), sp)  # noqa: E731
        assert f(40.0) == pytest.approx(0.5, abs=1e-6), key
        assert 0.8 <= f(120.0), key
        assert sp.beta_closure > 1.0, key
