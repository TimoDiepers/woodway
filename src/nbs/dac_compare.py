"""Trees or DAC, per grid cell and decision year -- by net efficiency.

Both options are judged by the same question: of the CO2 they take out of
the air, how much of the climate benefit is left after their own side effects?

* Trees: 1 - albedo offset (the Hasler quantity, nbs.aggregate.albedo_offset_field)
  for a stand planted in the decision year, evaluated at the model horizon
  (T_END, 2100): (Delta_T_CO2 + Delta_T_albedo) / Delta_T_CO2. Disturbance at the
  deterministic rate is inside both terms. The forest is the cell's typical
  forest (nbs.landscape.assign_species), as everywhere else in the talk.
* DAC: 1 - life-cycle emissions per t removed (nbs.dac), operated in the
  decision year.

Not part of the metric: cost, area, speed, permanence, scale. A cell where
DAC "wins" is one where a removed tonne is cleaner with DAC than with trees,
nothing more.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.typing import NDArray

from nbs.aggregate import _product_no_nan, co2_factor_grid
from nbs.constants import T_START, TAU_ATM, A_EARTH_M2
from nbs.dac import efficiency_grid
from nbs.pipeline import run_single_tree
from nbs.landscape import assign_species
from nbs.response import convolve_response, green_temperature
from nbs.species import SPECIES, get_species, reference_site

DECISION_YEARS = tuple(range(T_START, 2071, 5))  # planting years with at least 30 years to the 2100 horizon
OPTIONS = ("dac",) + tuple(SPECIES)  # categorical codes 1.. ; 0 = nothing cools / not possible


@lru_cache(maxsize=None)
def _unit_curves_planted(species_key: str, plant_year: int) -> tuple[float, float]:
    """(Delta_T_CO2 per tree, Delta_T_albedo per unit product) at T_END (2100) for a
    tree planted in *plant_year* -- nbs.aggregate.unit_curves with a planting year."""
    res = run_single_tree(species_key, lat_deg=reference_site(species_key), plant_year=plant_year)
    g_t = green_temperature("ssp245")
    co2 = convolve_response(g_t, res.phi_co2)
    sp = get_species(species_key)
    unit_alb = -TAU_ATM * np.asarray(res.trajectory.closure, dtype=float) * sp.stand_area_m2 / A_EARTH_M2
    return float(co2[-1]), float(convolve_response(g_t, unit_alb)[-1])


@lru_cache(maxsize=None)
def tree_efficiency_grid(plant_year: int) -> NDArray:
    """(360, 720) net efficiency of the cell's typical forest (Hasler et al. 2024), planted in
    *plant_year* -- the same tree as everywhere else in the talk (nbs.landscape.assign_species)."""
    species = assign_species()
    out = np.full(species.shape, np.nan)
    for key in SPECIES:
        mask = species == key
        if not mask.any():
            continue
        co2, alb = _unit_curves_planted(key, plant_year)
        carbon = co2_factor_grid(key)[mask] * co2
        albedo = _product_no_nan(key)[mask] * alb
        out[mask] = (carbon + albedo) / carbon
    return out


@lru_cache(maxsize=None)
def best_option_grid(year: int, variant: str = "waermepumpe") -> NDArray:
    """(360, 720) int: 0 = neither cools (or neither possible), 1 = DAC,
    2.. = the cell's typical forest (index in OPTIONS); -1 = no data."""
    tree = tree_efficiency_grid(year)
    dac = efficiency_grid(year, variant)
    species = assign_species()
    out = np.full(tree.shape, -1, dtype=int)
    has_any = np.isfinite(tree) | np.isfinite(dac)
    t = np.where(np.isfinite(tree), tree, -np.inf)
    d = np.where(np.isfinite(dac), dac, -np.inf)
    best = np.maximum(t, d)
    out[has_any] = 0
    dac_wins = has_any & (d >= t) & (best > 0)
    out[dac_wins] = OPTIONS.index("dac") + 1
    for k, key in enumerate(SPECIES):
        out[has_any & ~dac_wins & (best > 0) & (species == key)] = OPTIONS.index(key) + 1
    return out


@lru_cache(maxsize=1)
def _removal_kernel(scenario: str = "ssp245") -> NDArray:
    """K[y]: temperature change at the horizon (T_END) [K] per t CO2 taken out of the air in study
    year y -- the same climate chain as the tree (FaIR g_C, logarithmic CO2 forcing against the
    scenario background, FaIR g_T)."""
    from nbs.constants import YEARS
    from nbs.forcing import phi_co2_background
    from nbs.response import background_co2_ppm, green_carbon

    g_c, g_t, bg = green_carbon(scenario), green_temperature(scenario), background_co2_ppm(scenario)
    out = np.zeros(len(YEARS))
    for i in range(len(YEARS)):
        flux = np.zeros(len(YEARS))
        flux[i] = -1000.0  # kg CO2 into the air: one tonne removed
        out[i] = convolve_response(g_t, phi_co2_background(flux, g_c, bg))[-1]
    return out


@lru_cache(maxsize=4)
def dac_delta_t_grid(start_year: int = T_START, variant: str = "waermepumpe") -> NDArray:
    """(360, 720) temperature change at the horizon [K] from a DAC plant that removes 1 t CO2 a year
    from *start_year* on, net of its own life-cycle emissions in each year (eta_DAC, electricity mix
    of that year); NaN where sorbent DAC is not possible (too cold)."""
    from nbs.constants import YEARS

    k = _removal_kernel()
    total = None
    for i, y in enumerate(YEARS):
        if y < start_year:
            continue
        term = efficiency_grid(int(y), variant) * k[i]
        total = term if total is None else total + term
    return total
