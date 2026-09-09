"""The common 0.5-degree grid every raster is resampled onto.

Cell areas use the exact spherical-cap difference rather than a cosine
approximation: the potential calculation is an area-weighted sum over the
whole planet, so a systematic area error would bias every number downstream.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.constants import A_EARTH_M2

GRID_RESOLUTION_DEG = 0.5
N_LAT = 360
N_LON = 720

_R_EARTH_M = np.sqrt(A_EARTH_M2 / (4.0 * np.pi))
"""Earth radius consistent with the A_EARTH_M2 used everywhere else."""


def grid_lats() -> NDArray:
    """Cell-centre latitudes, north to south [degrees]."""
    edges = np.linspace(90.0, -90.0, N_LAT + 1)
    return 0.5 * (edges[:-1] + edges[1:])


def grid_lons() -> NDArray:
    """Cell-centre longitudes, west to east [degrees]."""
    edges = np.linspace(-180.0, 180.0, N_LON + 1)
    return 0.5 * (edges[:-1] + edges[1:])


def cell_area_m2() -> NDArray:
    """Area of every grid cell [m^2], shape (N_LAT, N_LON).

    A latitude band between phi1 and phi2 has area
    2 pi R^2 |sin(phi2) - sin(phi1)|, split evenly across the longitudes.
    """
    edges = np.deg2rad(np.linspace(90.0, -90.0, N_LAT + 1))
    band = 2.0 * np.pi * _R_EARTH_M**2 * np.abs(np.sin(edges[:-1]) - np.sin(edges[1:]))
    return np.repeat((band / N_LON)[:, None], N_LON, axis=1)
