"""Physical constants shared by the tree-level forcing chain.

Values are those quoted on the presentation slides, so that derivation and
computation carry identical numbers.
"""

from __future__ import annotations

import numpy as np

T_START = 2026  # the current year: planting, DAC start and every time axis begin here (was 2025 until 2026-10-07)
T_END = 2100  # evaluation horizon: keep warming low until 2100 (was 2150 until 2026-10-06)
YEARS = np.arange(T_START, T_END + 1, dtype=int)

A_EARTH_M2 = 5.1006e14
"""Earth surface area [m^2]. Slide 22."""

A_CO2_W_M2_PER_KG = 1.76e-15
"""Radiative efficiency of atmospheric CO2 [W m^-2 kg^-1]. IPCC AR6, slide 21.

This is the *linear* variant: a constant efficiency, independent of the
background concentration. It is what slide 21 derives. FaIR's own CO2 forcing
is logarithmic (see A_CO2_LOG_W_M2_PER_PPM below); the two agree only in the
limit of a small perturbation to a fixed background, which is why this
constant runs increasingly high as the ssp245 background rises over the
study period (see ``nbs.forcing.phi_co2_background``).
"""

A_CO2_LOG_W_M2_PER_PPM = 5.35
"""Logarithmic CO2 forcing coefficient a in phi = a * ln(C/C0) [W/m^2].

Myhre, Highwood, Shine & Stordal (1998), GRL 25(14), 2715-2718 -- the
standard, fixed-coefficient simplified expression for CO2 radiative forcing.
This is a close approximation of, but not identical to, what FaIR itself
computes: ``fair_module._create_fair`` never sets ``ghg_method``, so FaIR
uses its default ``meinshausen2020``, a state- and N2O-dependent formula.
See ``nbs.forcing.phi_co2_background`` for the size of that approximation
along the ssp245 background. Paired with KG_CO2_PER_PPM in
``nbs.forcing.phi_co2_background`` to convert an airborne mass anomaly into
the marginal forcing against a rising background concentration.
"""

KG_CO2_PER_PPM = 7.82e12
"""Mass of atmospheric CO2 per ppm of concentration [kg CO2 / ppm].

Standard conversion (1 ppm CO2 ~= 7.82 Gt CO2 for the current atmospheric
mass), used to turn the airborne mass anomaly Delta_m_CO2 [kg] into a
concentration anomaly Delta_C [ppm] in ``nbs.forcing.phi_co2_background``.
"""

M_CO2_PER_C = 44.0 / 12.0
"""Molar mass ratio CO2 to C. Slide 13."""

TAU_ATM = 0.854
"""Upward atmospheric transmittance for surface shortwave anomalies: the share of a change in
surface reflection that reaches the top of the atmosphere. Global annual clear-sky mean,
T_a = sqrt(f_a) with the two-way transmittance f_a = 0.730 (Lacis and Hansen 1974), as used by
Lenton and Vaughan (2009, ACP 9, 5539) and Cherubini et al. (2012)."""

R_CLOUD = 0.5
"""Extra reflectance of a low cloud over the surface (Cerasoli et al. 2021, PNAS 118,
e2026241118: f_C = 0.5, 'an average value of cloud albedo')."""

D_AFTERNOON = 0.5
"""Share of the day's sunlight after the boundary-layer cumulus forms. Duveiller et al.
(2021) see the clouds at their 13:30 peak; Cerasoli et al. (2021) let them persist from
onset until sunset."""
