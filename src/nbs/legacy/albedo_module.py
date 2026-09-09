"""Albedo radiative forcing timeseries for forest-based climate interventions."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.legacy.parameters import T_END, T_START, get_albedo_values


def compute_albedo_forcing_timeseries(
    intervention: str,
    lat: int,
    transition_years: int = 3,
) -> NDArray:
    """Return albedo radiative forcing [W/m²] timeseries from T_START to T_END.

    Parameters
    ----------
    intervention : str
        One of the defined intervention types.
    lat : int
        Latitude in degrees.
    transition_years : int
        Number of years to linearly ramp from 0 to full forcing (default 3).

    Returns
    -------
    NDArray, shape (125,)
        Positive values indicate warming, negative indicate cooling.
    """
    n_years = T_END - T_START  # 125
    delta_f = get_albedo_values(intervention, lat)

    if delta_f == 0.0:
        return np.zeros(n_years)

    timeseries = np.ones(n_years) * delta_f

    # Linear ramp over transition_years: year 0 starts at 0, reaches full at transition_years
    ramp_indices = min(transition_years, n_years)
    timeseries[:ramp_indices] = np.linspace(0, delta_f, ramp_indices + 1)[:-1]

    return timeseries
