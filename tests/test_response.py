import numpy as np
import pytest

from nbs.constants import YEARS
from nbs.response import convolve_response, green_carbon, green_temperature


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
    assert 0 <= peak < 25, "surface response peaks within a couple of decades"
    assert g[-1] < g[peak], "deep ocean draws the response back down"


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
