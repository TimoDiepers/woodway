"""Evapotranspiration (latent heat) radiative forcing timeseries.

Forests pump more water from soil to atmosphere than the baseline land cover
they replace. Evaporation cools the surface (latent heat absorbed); condensation
in the troposphere releases that heat higher up, redistributing energy vertically.
The net effect on global energy balance operates through:
  1. Surface cooling (lower OLR from cooler surface)
  2. Water vapour feedback (additional H₂O is a greenhouse gas — slight warming)
  3. Cloud changes (complex, sign varies)

Net result from observations (Bonan 2008; Duveiller et al. 2018):
  tropical > subtropical > temperate > boreal (cooling), all negative.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.legacy.parameters import T_END, T_START, get_et_values


def compute_et_forcing_timeseries(
    intervention: str,
    lat: int,
    transition_years: int = 10,
) -> NDArray:
    """Return ET radiative forcing [W/m²] timeseries from T_START to T_END.

    Parameters
    ----------
    intervention : str
        One of the defined intervention types.
    lat : int
        Latitude in degrees.
    transition_years : int
        Years to linearly ramp from 0 to full ET forcing (default 10 — canopy
        needs time to reach full leaf area for maximum transpiration).

    Returns
    -------
    NDArray, shape (125,)
        Negative values = cooling (ET removes heat from surface).
    """
    n_years = T_END - T_START
    delta_f = get_et_values(intervention, lat)

    if delta_f == 0.0:
        return np.zeros(n_years)

    timeseries = np.ones(n_years) * delta_f
    ramp_indices = min(transition_years, n_years)
    timeseries[:ramp_indices] = np.linspace(0, delta_f, ramp_indices + 1)[:-1]

    return timeseries
