import numpy as np
import pytest

from nbs.config import ModelConfig
from nbs.constants import YEARS
from nbs.metrics import t_star
from nbs.pipeline import SiteResult, _background_temperature, run_single_tree, run_single_tree_ensemble


def test_background_temperature_rejects_a_series_of_the_wrong_length(monkeypatch):
    """Silent-drift guard: appending exactly one element regardless of the
    actual gap would otherwise mask a change in FaIR's window size. A
    baseline series that is not exactly len(YEARS)-1 long must raise,
    naming both lengths involved."""
    import nbs.fair_module as fair_module

    bad = np.zeros(len(YEARS) - 2)
    monkeypatch.setattr(fair_module, "run_fair_baseline", lambda scenario: bad)
    with pytest.raises(ValueError) as exc_info:
        _background_temperature("ssp245")
    message = str(exc_info.value)
    assert str(len(YEARS) - 1) in message
    assert str(len(bad)) in message


@pytest.mark.slow
def test_single_tree_result_is_well_formed():
    r = run_single_tree("ebf_tropisch", lat_deg=0.0)
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
    out -- or, at 60 N since the calibrated FaIR (2026-10-05), not before
    2150 at all: there carbon and albedo nearly cancel at the horizon, and
    whether the sign flips before 2150 depends on the climate-model
    parameter set (docs/methods/klimamodell-fair.md). The shape (warms
    early, later break-even than the tropical case, nonzero albedo forcing
    at the end) is asserted rather than the exact years.
    """
    tropical = run_single_tree("ebf_tropisch", lat_deg=0.0)
    boreal = run_single_tree("enf_boreal", lat_deg=60.0)
    assert tropical.delta_t[-1] < 0.0
    assert t_star(tropical.delta_t, YEARS) < np.inf
    assert boreal.delta_t[-1] > tropical.delta_t[-1]

    # The albedo channel must be doing real work: the boreal tree actually
    # warms for a stretch early in its life before turning net cooling.
    assert np.any(boreal.delta_t[:30] > 0.0)
    assert boreal.phi_albedo[-1] > 0.0
    boreal_t_star = t_star(boreal.delta_t, YEARS)
    assert boreal_t_star > t_star(tropical.delta_t, YEARS)


@pytest.mark.slow
def test_albedo_channel_warms_at_high_latitude():
    boreal = run_single_tree("enf_boreal", lat_deg=60.0)
    assert np.all(boreal.phi_albedo >= 0.0)
    assert boreal.phi_albedo[-1] > 0.0


@pytest.mark.slow
def test_carbon_channel_cools_once_the_tree_has_grown():
    r = run_single_tree("ebf_tropisch", lat_deg=0.0)
    assert r.phi_co2[-1] < 0.0


@pytest.mark.slow
def test_ensemble_returns_matching_shapes_and_spread():
    det, ens = run_single_tree_ensemble("enf_boreal", lat_deg=60.0, n_members=20, seed=0)
    assert ens.shape == (20, len(YEARS))
    assert ens[:, -1].std() > 0.0


@pytest.mark.slow
def test_explicit_albedo_override_beats_the_fallback():
    a = run_single_tree("enf_boreal", lat_deg=60.0, delta_alpha=-0.30, q_sw=110.0)
    b = run_single_tree("enf_boreal", lat_deg=60.0, delta_alpha=-0.05, q_sw=110.0)
    assert a.phi_albedo[-1] > b.phi_albedo[-1]


# --- ModelConfig threading ---------------------------------------------


@pytest.mark.slow
def test_default_config_is_attached_to_the_result():
    r = run_single_tree("enf_boreal", lat_deg=60.0)
    assert r.config == ModelConfig()


@pytest.mark.slow
def test_explicit_config_is_carried_through():
    cfg = ModelConfig(co2_forcing="linear", albedo=False)
    r = run_single_tree("enf_boreal", lat_deg=60.0, config=cfg)
    assert r.config == cfg


@pytest.mark.slow
def test_albedo_switch_off_zeroes_the_albedo_channel():
    r = run_single_tree("enf_boreal", lat_deg=60.0, config=ModelConfig(albedo=False))
    assert np.all(r.phi_albedo == 0.0)
    # phi_total/phi_co2 are of order 1e-13 W/m^2; np.allclose's default
    # atol=1e-8 would call any two such arrays "close" regardless of a real
    # (if small) leftover albedo contribution. Scale the tolerance to the
    # signal instead (see also test_single_tree_result_is_well_formed).
    scale = np.abs(r.phi_co2).max()
    assert np.allclose(r.phi_total, r.phi_co2, rtol=0.0, atol=1e-9 * scale)


@pytest.mark.slow
def test_disturbance_off_gives_a_species_with_zero_disturbance_probability():
    r = run_single_tree("enf_boreal", lat_deg=60.0, config=ModelConfig(disturbance="off"))
    assert r.trajectory.n_disturbances == 0
    # matches a deterministic run with p_disturb forced to zero directly
    from dataclasses import replace

    from nbs.species import get_species
    from nbs.tree import simulate_deterministic
    from nbs.pipeline import _background_temperature

    quiet_sp = replace(get_species("enf_boreal"), p_disturb=0.0)
    expected = simulate_deterministic(quiet_sp, _background_temperature("ssp245"))
    assert np.allclose(r.trajectory.stock_kgC, expected.stock_kgC)


@pytest.mark.slow
def test_disturbance_stochastic_is_reproducible_from_its_seed():
    a = run_single_tree(
        "enf_boreal", lat_deg=60.0, config=ModelConfig(disturbance="stochastic"), seed=7
    )
    b = run_single_tree(
        "enf_boreal", lat_deg=60.0, config=ModelConfig(disturbance="stochastic"), seed=7
    )
    assert np.array_equal(a.trajectory.stock_kgC, b.trajectory.stock_kgC)
    assert np.array_equal(a.delta_t, b.delta_t)


@pytest.mark.slow
def test_disturbance_stochastic_differs_across_seeds():
    a = run_single_tree(
        "enf_boreal", lat_deg=60.0, config=ModelConfig(disturbance="stochastic"), seed=1
    )
    b = run_single_tree(
        "enf_boreal", lat_deg=60.0, config=ModelConfig(disturbance="stochastic"), seed=2
    )
    assert not np.array_equal(a.trajectory.stock_kgC, b.trajectory.stock_kgC)


@pytest.mark.slow
def test_carbon_sink_switch_changes_the_co2_channel():
    # phi_co2 is of order 1e-13 W/m^2; np.allclose's default atol=1e-8 would
    # call any two such arrays "close" regardless of their actual
    # difference. Scale the tolerance to the signal instead.
    scenario_cfg = ModelConfig(carbon_sink="scenario")
    preindustrial_cfg = ModelConfig(carbon_sink="preindustrial")
    r_scenario = run_single_tree("ebf_tropisch", lat_deg=0.0, config=scenario_cfg)
    r_preindustrial = run_single_tree("ebf_tropisch", lat_deg=0.0, config=preindustrial_cfg)
    scale = np.abs(r_scenario.phi_co2).max()
    assert not np.allclose(
        r_scenario.phi_co2, r_preindustrial.phi_co2, rtol=0.0, atol=1e-6 * scale
    )


@pytest.mark.slow
def test_co2_forcing_switch_changes_the_co2_channel():
    linear = run_single_tree("ebf_tropisch", lat_deg=0.0, config=ModelConfig(co2_forcing="linear"))
    log = run_single_tree("ebf_tropisch", lat_deg=0.0, config=ModelConfig(co2_forcing="logarithmic"))
    scale = np.abs(linear.phi_co2).max()
    assert not np.allclose(linear.phi_co2, log.phi_co2, rtol=0.0, atol=1e-6 * scale)


@pytest.mark.slow
def test_ensemble_disturbance_off_removes_all_spread():
    """With p_disturb forced to zero, every ensemble member follows the same
    deterministic growth curve, so the spread collapses to zero."""
    det, ens = run_single_tree_ensemble(
        "enf_boreal",
        lat_deg=60.0,
        n_members=10,
        seed=0,
        config=ModelConfig(disturbance="off"),
    )
    assert ens[:, -1].std() == pytest.approx(0.0, abs=1e-18)


@pytest.mark.slow
def test_ensemble_respects_the_albedo_switch():
    det, ens = run_single_tree_ensemble(
        "enf_boreal",
        lat_deg=60.0,
        n_members=5,
        seed=0,
        config=ModelConfig(albedo=False),
    )
    assert np.all(det.phi_albedo == 0.0)
