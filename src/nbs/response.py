"""Impulse responses of the carbon cycle and of temperature.

FaIR is run a handful of times here and never again. Everything downstream —
Monte-Carlo ensembles, global grids — is a convolution against these two
functions, which is what makes those affordable. It is also literally the
equation on slide 24.
"""

from __future__ import annotations

import functools

import numpy as np
from numpy.typing import NDArray

from nbs.constants import YEARS

_PULSE_GTCO2 = 1.0
_PULSE_WM2 = 1.0


def _to_study_length(x: NDArray) -> NDArray:
    """Pad a 125-year fair_module series to the 126-year study axis.

    fair_module slices 2025..2149; YEARS runs 2025..2150 inclusive. The final
    year is filled by repeating the last value, which is well inside the noise
    of a response that is nearly flat by then.

    Raises ValueError if ``x`` is not exactly one element shorter than YEARS:
    silently appending one value regardless of the actual gap would otherwise
    produce a truncated Green's function with no error if fair_module's
    window ever changed.
    """
    if len(x) == len(YEARS):
        return x
    if len(x) != len(YEARS) - 1:
        raise ValueError(
            f"expected a series of length {len(YEARS) - 1} (or {len(YEARS)}), "
            f"got {len(x)}"
        )
    return np.append(x, x[-1])


@functools.lru_cache(maxsize=4)
def green_carbon(scenario: str = "ssp245") -> NDArray:
    """Airborne fraction g_C(t) of a CO2 pulse released at T_START.

    Returns the fraction of the pulse still in the atmosphere after t years,
    so g_C(0) is close to (but, as explained below, not exactly) 1, and g_C
    decays from there. Joos et al. (2013), slide 13.

    Index note: emissions live on FaIR's *timepoint* axis (a flow during the
    year that starts at a given timebound) while airborne_emissions is a
    *stock* on the *timebound* axis. A CO2 pulse added at timepoint
    ``_START_IDX`` has not yet been booked into the atmosphere at the
    timebound of the same index (the year has not happened yet) — it first
    shows up in the stock at timebound ``_START_IDX + 1``. Reading the slice
    with a +1 offset (``_START_IDX + 1 : _END_IDX + 1``) is therefore what
    makes ``g_C[0] == 1.0`` (confirmed empirically: without the offset,
    ``g_C[0]`` comes out as ~0.0). Because of the shift, ``g_C[0]`` is
    actually the marginal airborne fraction *one year* after the pulse
    (~0.95, not exactly 1.0) — the fastest of FaIR's carbon-cycle response
    modes has already partly decayed by then, consistent with the ~4-year
    e-folding component of the Joos-style multi-box impulse response.

    Scenario dependence: this is the *marginal* response of a 1 GtCO2 pulse
    superimposed on the full ssp245 background, not the idealised pulse
    experiment run against a flat/pre-industrial background that produces
    the textbook ~40% airborne fraction after 75 years (Joos et al. 2013).
    Under ssp245, atmospheric CO2 keeps rising through the study period
    (~424 ppm in 2025 to ~624 ppm in 2149 in this run), which weakens the
    ocean's buffering capacity (a higher Revelle factor) and the land sink,
    so the marginal airborne fraction of an added pulse is measurably higher
    than the pre-industrial-background literature value, and can even creep
    back up slightly late in the run as background warming continues to
    weaken the sinks even after emissions start declining. This was verified
    against this project's FaIR configuration: g_C bottoms out around
    ~0.66 near 2046 and drifts back up to ~0.71 by 2150 (see
    ``tests/test_response.py``). This is a real, scenario-conditioned
    feature of the state-dependent carbon cycle, not a bug.
    """
    from nbs.fair_module import _START_IDX, _END_IDX, _create_fair

    base = _create_fair(scenario)
    base.run()
    airborne_base = base.airborne_emissions.sel(
        scenario=scenario, config="central", specie="CO2"
    ).values[_START_IDX + 1 : _END_IDX + 1]

    pert = _create_fair(scenario)
    co2 = pert.emissions.sel(specie="CO2 FFI").values.copy()
    co2[_START_IDX, 0, 0] += _PULSE_GTCO2
    pert.emissions.loc[dict(specie="CO2 FFI")] = co2
    pert.run()
    airborne_pert = pert.airborne_emissions.sel(
        scenario=scenario, config="central", specie="CO2"
    ).values[_START_IDX + 1 : _END_IDX + 1]

    g = (np.asarray(airborne_pert) - np.asarray(airborne_base)) / _PULSE_GTCO2
    result = _to_study_length(np.asarray(g, dtype=float))
    result.setflags(write=False)
    return result


@functools.lru_cache(maxsize=4)
def green_temperature(scenario: str = "ssp245") -> NDArray:
    """Temperature response g_T(t) to a one-year unit forcing pulse.

    Units: K per (W/m^2 sustained for one year).

    Index note: unlike CO2 airborne emissions, ``forcing`` and ``temperature``
    are both on the *timebound* axis, and FaIR's own stepping rule
    (``fair.fair`` computes ``cummins_state[timebound n+1]`` directly from
    ``forcing[timebound n+1]`` and the state at ``n``, see
    ``step_temperature`` in ``fair/energy_balance_model.py``) means a forcing
    value recorded at bound n is exactly what produces the temperature at
    that same bound n. So g_T(0) is *not* zero: the naive assumption that "the
    pulse has not acted yet at the moment it is applied" does not hold for
    FaIR's own indexing, because the forcing at bound 0 is what determines
    the state at bound 0 (given the state at bound -1). This was verified two
    ways: (1) reading the FaIR source for ``step_temperature``, and (2)
    empirically — forcing ``g_T[0]`` to 0 makes
    ``test_convolution_reproduces_a_full_fair_run`` fail by exactly one
    timestep of lag, while leaving the raw value in place reproduces a full
    FaIR run to within numerical noise. Do not zero this value.
    """
    from nbs.fair_module import _START_IDX, _END_IDX, _create_fair, run_fair_baseline

    baseline = run_fair_baseline(scenario)

    f = _create_fair(scenario)
    solar = f.forcing.sel(specie="Solar").values.copy()
    solar[_START_IDX, 0, 0] += _PULSE_WM2
    f.forcing.loc[dict(specie="Solar")] = solar
    f.run()
    perturbed = f.temperature.sel(
        scenario=scenario, config="central", layer=0
    ).values[_START_IDX:_END_IDX]

    g = (np.asarray(perturbed, dtype=float) - baseline) / _PULSE_WM2
    result = _to_study_length(g)
    result.setflags(write=False)
    return result


@functools.lru_cache(maxsize=4)
def background_co2_ppm(scenario: str = "ssp245") -> NDArray:
    """Baseline CO2 concentration C_bg(t) [ppm] under *scenario*, on YEARS.

    Unlike ``green_carbon``, this is not a pulse-minus-baseline difference:
    it is the concentration trajectory of the unperturbed baseline run
    itself, so none of ``green_carbon``'s +1 timepoint-vs-timebound offset
    applies here. That offset exists only because a pulse is added on the
    *timepoint* axis (a flow during the year) and airborne_emissions is a
    *stock* on the *timebound* axis, so a pulse added at timepoint
    ``_START_IDX`` first shows up in the stock at timebound
    ``_START_IDX + 1``.

    Concentration, like temperature, is a state variable that already lives
    on the timebound axis and is read directly here with no pulse involved
    -- exactly the pattern ``green_temperature`` and ``run_fair_baseline``
    use for temperature (also a timebound quantity): slice
    ``[_START_IDX:_END_IDX]`` with no offset, then pad to the study length.
    Timebound index ``_START_IDX`` (275) is by construction the calendar
    year T_START (2025), so this reads off exactly the calendar years in
    YEARS.

    Used by ``nbs.forcing.phi_co2_background`` as C_bg(t) for the marginal
    logarithmic CO2 forcing law. Under ssp245 this rises from about 424 ppm
    in 2025 to about 624 ppm by the end of the study period.
    """
    from nbs.fair_module import _START_IDX, _END_IDX, _create_fair

    f = _create_fair(scenario)
    f.run()
    conc = f.concentration.sel(
        scenario=scenario, config="central", specie="CO2"
    ).values[_START_IDX:_END_IDX]
    result = _to_study_length(np.asarray(conc, dtype=float))
    result.setflags(write=False)
    return result


_JOOS_A0 = 0.2173
"""Permanent airborne fraction as t -> infinity. Joos et al. (2013), Table 5."""
_JOOS_A = (0.2240, 0.2824, 0.2763)
"""Amplitudes of the three decaying exponential modes. Joos et al. (2013)."""
_JOOS_TAU = (394.4, 36.54, 4.304)
"""Time constants [a] of the three decaying modes. Joos et al. (2013)."""


@functools.lru_cache(maxsize=1)
def green_carbon_preindustrial() -> NDArray:
    """Airborne fraction of a CO2 pulse against a flat, pre-industrial-style
    background: the standard Joos et al. (2013) four-box impulse response,

        IRF(t) = a0 + sum_i a_i * exp(-t / tau_i)

    with the published coefficients (a0 permanent, a1/tau1, a2/tau2, a3/tau3
    the three decaying modes). This is the textbook curve slide 13 quotes
    (~40% still airborne after 75 years) -- unlike ``green_carbon``, it does
    not depend on FaIR or on any scenario, because it is not a marginal
    response superimposed on a rising background: it describes a pulse
    against an unchanging atmosphere.

    ``green_carbon`` differs from this because a pulse added on top of the
    actual, rising ssp245 trajectory meets sinks that are already more
    saturated (weaker ocean buffering via a higher Revelle factor, a
    weakened land sink) than the flat background this curve assumes. That
    is why ``green_carbon``'s marginal airborne fraction is measurably
    higher at the same time horizon (g_C[75] ~= 0.700, scenario-conditioned,
    versus this function's g[75] ~= 0.44, the pre-industrial-style figure)
    -- both are real, neither is a bug. See ``ModelConfig.carbon_sink``.
    """
    t = np.arange(len(YEARS), dtype=float)
    g = np.full_like(t, _JOOS_A0)
    for a, tau in zip(_JOOS_A, _JOOS_TAU):
        g = g + a * np.exp(-t / tau)
    g.setflags(write=False)
    return g


def convolve_response(g: NDArray, x: NDArray, dt: float = 1.0) -> NDArray:
    """Causal discrete convolution y[n] = dt * sum_{m<=n} g[n-m] x[m]."""
    g = np.asarray(g, dtype=float)
    x = np.asarray(x, dtype=float)
    return dt * np.convolve(x, g)[: len(x)]
