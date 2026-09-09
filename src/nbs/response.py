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
    """
    if len(x) == len(YEARS):
        return x
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
    return _to_study_length(np.asarray(g, dtype=float))


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
    return _to_study_length(g)


def convolve_response(g: NDArray, x: NDArray, dt: float = 1.0) -> NDArray:
    """Causal discrete convolution y[n] = dt * sum_{m<=n} g[n-m] x[m]."""
    g = np.asarray(g, dtype=float)
    x = np.asarray(x, dtype=float)
    return dt * np.convolve(x, g)[: len(x)]
