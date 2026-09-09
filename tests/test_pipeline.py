import numpy as np
import pytest

from nbs.constants import YEARS
from nbs.metrics import t_star
from nbs.pipeline import SiteResult, run_single_tree, run_single_tree_ensemble


@pytest.mark.slow
def test_single_tree_result_is_well_formed():
    r = run_single_tree("tropical_mixed", lat_deg=0.0)
    assert isinstance(r, SiteResult)
    for arr in (r.phi_co2, r.phi_albedo, r.phi_total, r.delta_t):
        assert arr.shape == YEARS.shape
    # phi_total is of order 1e-13 W/m^2; np.allclose's default atol=1e-8
    # would swamp that entirely and let a wrong sum pass. Scale the
    # tolerance to the signal instead (see also tests/test_plots.py).
    scale = np.abs(r.phi_total).max()
    assert np.allclose(r.phi_total, r.phi_co2 + r.phi_albedo, rtol=0.0, atol=1e-9 * scale)


@pytest.mark.slow
def test_tropical_tree_cools_and_boreal_tree_does_not():
    """The central claim of the talk, as a test.

    Guards against a weaker version of this test that would still pass with
    the albedo channel effectively switched off (e.g. delta_alpha ~ 0):
    a tropical tree cools from the start, while a boreal tree at high
    latitude is a net *warming* influence for an early stretch of decades —
    the albedo penalty of a darkening canopy outweighing its still-small
    carbon uptake — before the accumulating carbon benefit eventually wins
    out. The shape (warms early, cools later, later break-even than the
    tropical case, nonzero albedo forcing at the end) is asserted rather
    than the exact years, so this stays meaningful once the latitude
    fallback tables are replaced by real raster data.
    """
    tropical = run_single_tree("tropical_mixed", lat_deg=0.0)
    boreal = run_single_tree("picea_abies", lat_deg=60.0)
    assert tropical.delta_t[-1] < 0.0
    assert t_star(tropical.delta_t, YEARS) < np.inf
    assert boreal.delta_t[-1] > tropical.delta_t[-1]

    # The albedo channel must be doing real work: the boreal tree actually
    # warms for a stretch early in its life before turning net cooling.
    assert np.any(boreal.delta_t[:30] > 0.0)
    assert boreal.phi_albedo[-1] > 0.0
    boreal_t_star = t_star(boreal.delta_t, YEARS)
    assert boreal_t_star < np.inf
    assert boreal_t_star > t_star(tropical.delta_t, YEARS)


@pytest.mark.slow
def test_albedo_channel_warms_at_high_latitude():
    boreal = run_single_tree("picea_abies", lat_deg=60.0)
    assert np.all(boreal.phi_albedo >= 0.0)
    assert boreal.phi_albedo[-1] > 0.0


@pytest.mark.slow
def test_carbon_channel_cools_once_the_tree_has_grown():
    r = run_single_tree("tropical_mixed", lat_deg=0.0)
    assert r.phi_co2[-1] < 0.0


@pytest.mark.slow
def test_ensemble_returns_matching_shapes_and_spread():
    det, ens = run_single_tree_ensemble("picea_abies", lat_deg=60.0, n_members=20, seed=0)
    assert ens.shape == (20, len(YEARS))
    assert ens[:, -1].std() > 0.0


@pytest.mark.slow
def test_explicit_albedo_override_beats_the_fallback():
    a = run_single_tree("picea_abies", lat_deg=60.0, delta_alpha=-0.30, q_sw=110.0)
    b = run_single_tree("picea_abies", lat_deg=60.0, delta_alpha=-0.05, q_sw=110.0)
    assert a.phi_albedo[-1] > b.phi_albedo[-1]
