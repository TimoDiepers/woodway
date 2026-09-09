"""Physical constants shared by the tree-level forcing chain.

Values are those quoted on the presentation slides, so that derivation and
computation carry identical numbers.
"""

from __future__ import annotations

import numpy as np

T_START = 2025
T_END = 2150
YEARS = np.arange(T_START, T_END + 1, dtype=int)

A_EARTH_M2 = 5.1006e14
"""Earth surface area [m^2]. Slide 22."""

A_CO2_W_M2_PER_KG = 1.76e-15
"""Radiative efficiency of atmospheric CO2 [W m^-2 kg^-1]. IPCC AR6, slide 21."""

M_CO2_PER_C = 44.0 / 12.0
"""Molar mass ratio CO2 to C. Slide 13."""

TAU_ATM = 0.8
"""Upward atmospheric transmittance for surface shortwave anomalies. Slide 22."""
