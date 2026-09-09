import numpy as np
import pytest

from nbs.constants import YEARS
from nbs.response import (
    _to_study_length,
    background_co2_ppm,
    convolve_response,
    green_carbon,
    green_carbon_preindustrial,
    green_temperature,
)


def test_to_study_length_rejects_a_series_of_the_wrong_length():
    """Silent-drift guard: padding by exactly one element regardless of the
    actual gap would otherwise mask a change in FaIR's window size. Any
    length other than len(YEARS)-1 (needs padding) or len(YEARS) (already
    the study length) must raise, naming both lengths involved."""
    bad = np.zeros(len(YEARS) - 2)
    with pytest.raises(ValueError) as exc_info:
        _to_study_length(bad)
    message = str(exc_info.value)
    assert str(len(YEARS) - 1) in message
    assert str(len(bad)) in message


def test_convolution_is_causal():
    g = np.array([0.0, 1.0, 0.5, 0.25])
    x = np.array([0.0, 0.0, 1.0, 0.0])
    y = convolve_response(g, x)
    assert y[0] == 0.0
    assert y[1] == 0.0  # nothing before the input can respond to it


def test_convolution_matches_hand_computed_values():
    g = np.array([0.0, 1.0, 0.5])
    x = np.array([2.0, 0.0, 0.0])
    y = convolve_response(g, x)
    assert y == pytest.approx([0.0, 2.0, 1.0])


def test_convolution_preserves_length():
    g = np.ones(len(YEARS))
    x = np.ones(len(YEARS))
    assert convolve_response(g, x).shape == (len(YEARS),)


def test_convolution_is_linear():
    rng = np.random.default_rng(0)
    g = rng.random(20)
    a, b = rng.random(20), rng.random(20)
    lhs = convolve_response(g, 3.0 * a + 2.0 * b)
    rhs = 3.0 * convolve_response(g, a) + 2.0 * convolve_response(g, b)
    assert np.allclose(lhs, rhs)


@pytest.mark.slow
def test_carbon_green_function_is_a_decaying_airborne_fraction():
    """Bounds reflect the *marginal* pulse response on top of the ssp245
    background, not the idealised pre-industrial-background pulse experiment
    that gives the textbook ~40%-after-75-years figure from Joos et al.
    (2013). Under ssp245, atmospheric CO2 rises by ~200 ppm over the study
    period, which weakens the ocean and land sinks (state-dependent carbon
    cycle), so the marginal airborne fraction of an added pulse is measurably
    higher than that literature value, and can drift back up slightly late in
    the run as continued warming keeps weakening the sinks even after
    emissions decline (verified against this project's FaIR configuration:
    g_C bottoms out around ~0.66 near 2046 and drifts back to ~0.71 by 2150 —
    a real feature of the state-dependent carbon cycle, not noise).
    """
    g = green_carbon("ssp245")
    assert g.shape == (len(YEARS),)
    assert g[0] == pytest.approx(1.0, abs=0.06)
    assert 0.55 < g[75] < 0.85, "ssp245's rising CO2 background keeps more of the pulse airborne than the pre-industrial Joos (2013) figure"
    assert g[30] < 0.75 * g[0], "fast initial decay within a few decades"
    assert np.argmax(g) == 0, "no later point exceeds the immediate post-pulse airborne fraction"


@pytest.mark.slow
def test_temperature_green_function_peaks_then_decays():
    """g_T(0) is not required to be zero.

    FaIR computes the state at timebound n directly from the forcing
    recorded at timebound n (see ``step_temperature`` in
    ``fair/energy_balance_model.py``: ``cummins_state[n+1]`` is a function of
    ``forcing[n+1]`` and the state at ``n``). A one-year forcing pulse
    recorded at bound 0 therefore already acts on the temperature read at
    bound 0 itself — verified against ``test_convolution_reproduces_a_full_fair_run``,
    which fails by one timestep of lag if g_T[0] is forced to zero. What
    should hold instead is that the immediate response is positive but does
    not exceed the (near-immediate) peak of the fast surface layer.
    """
    g = green_temperature("ssp245")
    assert g.shape == (len(YEARS),)
    assert 0.0 < g[0] <= g.max()
    peak = int(np.argmax(g))
    assert 0 < peak < 25, "surface response peaks within a couple of decades"
    assert g[-1] < g[peak], "deep ocean draws the response back down"


def test_green_carbon_preindustrial_starts_at_one():
    """No FaIR call: pure Joos et al. (2013) four-box impulse response, so
    this is fast enough to run outside -m slow."""
    g = green_carbon_preindustrial()
    assert g.shape == (len(YEARS),)
    assert g[0] == pytest.approx(1.0, abs=1e-9)


def test_green_carbon_preindustrial_matches_textbook_75_year_figure():
    """Task spec: the Joos curve at 75 years should come out substantially
    lower than the scenario-conditioned g_C[75] (~0.700, committed value),
    near the ~0.4 the talk's slide 13 quotes."""
    g = green_carbon_preindustrial()
    assert 0.35 < g[75] < 0.45


def test_green_carbon_preindustrial_is_lower_than_scenario_conditioned_at_75_years():
    """This is the whole point of the carbon_sink switch: a pulse on top of
    a rising ssp245 background meets more saturated sinks than a pulse
    against a flat pre-industrial background."""
    g_pre = green_carbon_preindustrial()
    assert g_pre[75] < 0.700, "must come out below the committed scenario g_C[75]"


def test_green_carbon_preindustrial_decays_monotonically():
    g = green_carbon_preindustrial()
    assert np.all(np.diff(g) <= 1e-9)


@pytest.mark.slow
def test_background_co2_ppm_spans_the_ssp245_study_period():
    c = background_co2_ppm("ssp245")
    assert c.shape == (len(YEARS),)
    assert 400.0 < c[0] < 440.0, "~424 ppm in 2025"
    assert 590.0 < c[-1] < 660.0, "~624 ppm by 2149/2150"
    # the final entry is a repeat of the previous one (_to_study_length pads
    # the 125-year fair_module series to the 126-year study axis), so the
    # last diff is exactly 0 rather than positive
    assert np.all(np.diff(c)[:-1] > 0.0), "ssp245 CO2 background keeps rising"


@pytest.mark.slow
def test_convolution_reproduces_a_full_fair_run():
    """The whole plan rests on replacing FaIR runs with one convolution.

    Build a forcing series, push it through FaIR directly, and check that the
    convolution of the Green's function with the same series agrees.
    """
    from nbs.fair_module import run_fair_baseline, run_fair_perturbed

    n = len(YEARS) - 1  # fair_module works on 125 years
    phi = np.zeros(n)
    phi[10:] = 0.05  # a step in forcing, W/m^2

    direct = run_fair_perturbed(np.zeros(n), phi, scenario="ssp245") - run_fair_baseline("ssp245")
    via_convolution = convolve_response(green_temperature("ssp245"), np.append(phi, phi[-1]))[:n]

    scale = np.abs(direct).max()
    assert np.abs(direct - via_convolution).max() < 0.05 * scale


@pytest.mark.slow
def test_co2_chain_reproduces_a_full_fair_run_for_both_variants():
    """Mirror of test_convolution_reproduces_a_full_fair_run for the OTHER
    half of the chain: flux -> forcing, never checked against FaIR before
    this task. That gap is how the review's 26-40% CO2-channel deviation
    survived undetected.

    Build a CO2 removal flux (a ramp reaching a few tenths of a GtCO2/yr),
    push it through nbs.fair_module.run_fair_perturbed directly as NEE
    emissions with zero albedo forcing, and compare the resulting
    temperature against the study chain (flux -> phi_co2[_background] ->
    convolve with g_T) for both CO2 forcing variants.

    Units: run_fair_perturbed takes GtCO2/yr on the 125-entry fair_module
    axis (2025..2149); the chain works in kg CO2/yr on the 126-entry study
    axis (YEARS). g_c is the scenario-conditioned green_carbon, which is
    itself derived from FaIR's own marginal pulse response -- so this test
    isolates the forcing *law* (linear vs logarithmic), not the airborne
    fraction.

    Measured deviations (max |direct - chain| over the run, as a fraction of
    the direct FaIR run's peak |ΔT|, recorded here as required by the task
    spec): linear ~34.7%, logarithmic ~15.3% -- more than a factor of two
    smaller. Both numbers are larger than the review's 26-40% CO2-*channel*
    figure alone because this test also carries the chain's other known
    approximations (the pulse-superposition assumption behind convolving a
    continuous flux with green_carbon's single-pulse kernel, and the ~5%
    forcing-to-temperature convolution error already pinned by
    test_convolution_reproduces_a_full_fair_run above). The ordering --
    logarithmic tracking FaIR clearly better than linear -- is what this
    test exists to confirm. If the logarithmic variant did not come out
    substantially closer, that would mean phi_co2_background is wrong.
    """
    from nbs.fair_module import run_fair_baseline, run_fair_perturbed
    from nbs.forcing import phi_co2, phi_co2_background
    from nbs.response import background_co2_ppm

    n = len(YEARS) - 1  # fair_module works on 125 years
    flux_gtco2_yr = np.linspace(0.0, -0.3, n)  # a growing removal, GtCO2/yr

    direct = (
        run_fair_perturbed(flux_gtco2_yr, np.zeros(n), scenario="ssp245")
        - run_fair_baseline("ssp245")
    )

    flux_kg_yr = np.append(flux_gtco2_yr, flux_gtco2_yr[-1]) * 1.0e12  # -> kg, 126 entries
    g_c = green_carbon("ssp245")
    g_t = green_temperature("ssp245")
    c_bg = background_co2_ppm("ssp245")

    phi_lin = phi_co2(flux_kg_yr, g_c)
    phi_log = phi_co2_background(flux_kg_yr, g_c, c_bg)

    dt_lin = convolve_response(g_t, phi_lin)[:n]
    dt_log = convolve_response(g_t, phi_log)[:n]

    scale = np.abs(direct).max()
    dev_lin = np.abs(direct - dt_lin).max() / scale
    dev_log = np.abs(direct - dt_log).max() / scale

    assert dev_log < dev_lin, "the logarithmic variant must track FaIR better than the linear one"
    # Explicit, measured tolerances (see docstring: measured dev_lin ~0.347,
    # dev_log ~0.153 when this test was written). A margin is left around
    # each measured value so ordinary numerical noise cannot flip the
    # comparison, but a genuinely broken implementation still fails loudly.
    assert dev_log < 0.20, f"logarithmic deviation {dev_log:.3f} should be well below the linear one"
    assert dev_lin > 0.25, f"linear deviation {dev_lin:.3f} should be the known large one"
    assert dev_log < 0.5 * dev_lin, "logarithmic must be substantially -- not just marginally -- better"
