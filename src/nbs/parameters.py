"""Central parameter definitions for the NBS Climate Framework."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INTERVENTIONS = [
    "tropical_reforestation",
    "boreal_afforestation",
    "avoided_deforestation",
    "beccs",
]

LATITUDES = [0, 15, 30, 45, 60]

LAND_USES = ["cropland", "grassland", "degraded_forest"]

SCENARIOS = ["ssp126", "ssp245", "ssp370"]

COMPLEXITY_LEVELS = [0, 1, 2, 3, 4, 5, 6]

T_START = 2025
T_END = 2150

S0 = 1361.0  # Solar constant [W/m²]

A_EARTH_M2 = 5.1006e14  # Earth surface area [m²]
HA_TO_M2 = 1.0e4  # 1 ha = 10^4 m²

DEFORESTATION_RATE = 0.005  # 0.5%/yr
C_FOREST_TROPICAL = 200.0  # tC/ha

BECCS_HARVEST_PERIOD = 15  # years
BECCS_CCS_EFFICIENCY = 0.87
BECCS_PROCESS_EMISSION_FRAC = 0.06

SOC_MU = 0.03  # yr⁻¹
SOIL_RESP_Q10 = 2.0
SOIL_RESP_T0 = 10.0  # °C
SOIL_RESP_BASE = {0: 15.0, 15: 12.0, 30: 8.0, 45: 5.0, 60: 3.0}  # tCO2/ha/yr at T0

# ---------------------------------------------------------------------------
# Growth parameters  (Chapman-Richards: B(t) = B_max * (1 - exp(-k*t))^p)
# ---------------------------------------------------------------------------

_GROWTH_PARAMS: dict[str, tuple[float, float, float]] = {
    "tropical_reforestation": (200.0, 0.08, 2.5),
    "boreal_afforestation": (100.0, 0.03, 2.0),
    "beccs": (50.0, 0.12, 1.75),
}


def get_growth_params(intervention: str) -> tuple[float, float, float]:
    """Return (B_max, k, p) for *intervention*.

    Raises ``KeyError`` for ``"avoided_deforestation"`` (no growth model).
    """
    return _GROWTH_PARAMS[intervention]


# ---------------------------------------------------------------------------
# SOC parameters  (tC/ha)
# ---------------------------------------------------------------------------

_SOC_PARAMS: dict[str, dict[int, tuple[float, float]]] = {
    "tropical_reforestation": {
        0: (120.0, 80.0),
        15: (110.0, 75.0),
    },
    "boreal_afforestation": {
        45: (90.0, 110.0),
        60: (85.0, 120.0),
    },
    "avoided_deforestation": {
        0: (120.0, 120.0),
        15: (110.0, 110.0),
    },
    "beccs": {
        30: (60.0, 70.0),
        45: (65.0, 75.0),
    },
}


def _nearest_key(keys: list[int], target: int) -> int:
    return min(keys, key=lambda k: abs(k - target))


def get_soc_params(intervention: str, lat: int) -> tuple[float, float]:
    """Return (SOC_forest, SOC_initial) for *intervention* at *lat*.

    Falls back to the nearest available latitude.
    """
    lat_map = _SOC_PARAMS[intervention]
    key = lat if lat in lat_map else _nearest_key(list(lat_map.keys()), lat)
    return lat_map[key]


# ---------------------------------------------------------------------------
# Disturbance probability
# ---------------------------------------------------------------------------

_DISTURBANCE_BASE: dict[str, float] = {
    "tropical_reforestation": 0.005,
    "boreal_afforestation": 0.01,
    "avoided_deforestation": 0.002,
    "beccs": 0.003,
}


def get_disturbance_probability(
    intervention: str, lat: int, years: NDArray
) -> NDArray:
    """Annual disturbance probability increasing linearly by 50% from T_START to T_END."""
    base = _DISTURBANCE_BASE[intervention]
    # Linear ramp: factor goes from 1.0 at T_START to 1.5 at T_END
    factor = 1.0 + 0.5 * (years - T_START) / (T_END - T_START)
    return base * factor


# ---------------------------------------------------------------------------
# Evapotranspiration forcing  ΔF_ET [W/m²]  (always negative = cooling)
# Values represent steady-state latent heat flux cooling relative to baseline
# land cover. Literature basis: Bonan (2008) Science, Duveiller et al. (2018).
# ---------------------------------------------------------------------------

_ET_VALUES: dict[str, dict[int, float]] = {
    "tropical_reforestation": {0: -1.5, 15: -1.2, 30: -0.8},
    "boreal_afforestation": {45: -0.3, 60: -0.1},
    "avoided_deforestation": {0: 0.0, 15: 0.0, 30: 0.0, 45: 0.0, 60: 0.0},
    "beccs": {0: -0.8, 15: -0.7, 30: -0.5, 45: -0.2, 60: -0.05},
}


def get_et_values(intervention: str, lat: int) -> float:
    """Return ΔF_ET [W/m²] for *intervention* at *lat*. Negative = cooling."""
    lat_map = _ET_VALUES[intervention]
    key = lat if lat in lat_map else _nearest_key(list(lat_map.keys()), lat)
    return lat_map[key]


# ---------------------------------------------------------------------------
# Albedo forcing  ΔF_α [W/m²]
# ---------------------------------------------------------------------------

_ALBEDO_VALUES: dict[str, dict[int, float]] = {
    "tropical_reforestation": {0: -0.3, 15: -0.25, 30: -0.15},
    "boreal_afforestation": {45: 0.8, 60: 1.15},
    "avoided_deforestation": {0: 0.0, 15: 0.0, 30: 0.0, 45: 0.0, 60: 0.0},
    "beccs": {0: -0.15, 15: -0.15, 30: -0.2, 45: 0.0, 60: 0.4},
}


def get_albedo_values(intervention: str, lat: int) -> float:
    """Return ΔF_α [W/m²] for *intervention* at *lat*.

    Falls back to the nearest available latitude.
    """
    lat_map = _ALBEDO_VALUES[intervention]
    key = lat if lat in lat_map else _nearest_key(list(lat_map.keys()), lat)
    return lat_map[key]
