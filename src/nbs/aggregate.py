"""Exact grid-wide aggregation of the single-tree chain, and its proof.

Everything past the tree trajectory is linear in tree count, and phi_CO2
carries no location (CO2 mixes globally, see ``nbs.forcing``). For a cell *c*
with ``N_c`` trees of species *s* planted at t=T_START,

    Delta_T_c(t) = N_c * [ Delta_T_CO2,s(t) + P_c * U_s(t) ]

with ``P_c`` the cell's own afforestation Delta_alpha * q_sw product
(``nbs.albedo_grid.alpha_q_product``) and two curves computed **once per
species**, not once per cell:

    Delta_T_CO2,s = g_T * phi_CO2,s                     (a single tree's own
                                                           CO2 channel)
    U_s           = g_T * ( -tau * A_s / A_Earth * closure_s )
                                                          (temperature response
                                                           per unit of the
                                                           Delta_alpha * q_sw
                                                           product -- the
                                                           albedo channel with
                                                           the product factored
                                                           out)

``unit_curves`` returns exactly this pair. Five species times two curves is
ten convolutions total; after that every cell is one multiply-add, and the
global sum reduces to two scalars per species:

    Delta_T_global(t) = sum_s [ (sum_c N_c) * Delta_T_CO2,s(t)
                                 + (sum_c N_c * P_c) * U_s(t) ]

``aggregate_by_species`` returns those two scalars per species. This is
**exact**, not an approximation -- the whole point of the module is that
259 200 cells never need to run through the tree-growth/FaIR chain
individually. ``test_aggregation_equals_cellwise_computation_on_a_sample`` in
tests/test_aggregate.py is the proof: it recomputes a random sample of cells
explicitly, one at a time, through the same unit curves, and checks the sum
against the aggregate route.

One trap this module deliberately avoids: ``SiteResult.phi_albedo`` (from
``nbs.pipeline.run_single_tree``) already comes multiplied by whatever
delta_alpha/q_sw product that call used (the fallback latitude tables, by
default). Dividing it back out to recover the per-unit response would be
fragile and, worse, silently wrong wherever the fallback product is zero or
near it. ``unit_curves`` never touches ``result.phi_albedo``; it rebuilds the
albedo unit curve from ``result.trajectory.closure`` directly, exactly the
quantity ``phi_albedo_from_product`` would multiply the product against.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.typing import NDArray

from nbs.albedo_grid import alpha_q_product
from nbs.config import ModelConfig
from nbs.constants import A_EARTH_M2, TAU_ATM, YEARS
from nbs.landscape import assign_species, tree_count
from nbs.pipeline import run_single_tree
from nbs.response import convolve_response, green_temperature
from nbs.species import SPECIES, get_species


def _year_index(year: int) -> int:
    """Index of *year* into the 126-element YEARS axis, or raise."""
    idx = int(year) - int(YEARS[0])
    if not (0 <= idx < len(YEARS)):
        raise ValueError(
            f"Jahr {year} liegt ausserhalb des Studienzeitraums "
            f"{int(YEARS[0])}-{int(YEARS[-1])}"
        )
    return idx


@lru_cache(maxsize=None)
def _unit_curves_cached(
    species_key: str, scenario: str, config: ModelConfig
) -> tuple[NDArray, NDArray]:
    """The cached, immutable computation behind ``unit_curves``.

    ``run_single_tree`` is used for the CO2 channel and for the tree's own
    growth trajectory (closure), exactly as the module docstring's "builds on
    run_single_tree" describes; its ``phi_albedo`` field is never read here --
    it was formed against the fallback latitude product for this call's
    (arbitrary) lat_deg=0.0, which is not the per-unit quantity this function
    needs.
    """
    result = run_single_tree(species_key, lat_deg=0.0, scenario=scenario, config=config)
    g_t = green_temperature(scenario)

    delta_t_co2 = convolve_response(g_t, result.phi_co2)

    sp = get_species(species_key)
    closure = np.asarray(result.trajectory.closure, dtype=float)
    unit_phi_albedo = -TAU_ATM * closure * sp.stand_area_m2 / A_EARTH_M2
    delta_t_albedo_unit = convolve_response(g_t, unit_phi_albedo)

    delta_t_co2.setflags(write=False)
    delta_t_albedo_unit.setflags(write=False)
    return delta_t_co2, delta_t_albedo_unit


def unit_curves(
    species_key: str, scenario: str = "ssp245", config: ModelConfig | None = None
) -> tuple[NDArray, NDArray]:
    """Two length-126 curves for one species: ``(delta_t_co2_per_tree,
    delta_t_albedo_per_unit_product)``.

    ``delta_t_co2_per_tree`` [K]: one tree's own CO2-channel temperature
    response, independent of where it stands.

    ``delta_t_albedo_per_unit_product`` [K per (W/m^2)]: the temperature
    response to one tree's albedo channel **per unit of the cell's own
    Delta_alpha * q_sw product** -- multiply by a cell's actual product
    (``nbs.albedo_grid.alpha_q_product``) to get that cell's albedo-channel
    Delta_T for one tree of this species there.

    Cached per (species_key, scenario, config): this is the module's one
    genuinely expensive step (a FaIR-backed tree simulation), so repeated
    calls across ``delta_t_at_year``, ``delta_t_field`` and
    ``global_delta_t`` do not re-run it.
    """
    if config is None:
        config = ModelConfig()
    co2, albedo_unit = _unit_curves_cached(species_key, scenario, config)
    return co2.copy(), albedo_unit.copy()


def _product_no_nan(species_key: str) -> NDArray:
    """(360, 720) afforestation Delta_alpha * q_sw product, NaN replaced by 0.

    NaN in ``alpha_q_product`` means "no evidence of this specific land-cover
    transition here" -- a real, expected geographic gap (see
    ``nbs.albedo_grid``'s own docstrings on this point), not a bug. Because
    ``nbs.landscape`` assigns species by latitude band alone, uncorrelated
    with where the Duveiller raster actually carries data for that
    transition, most plantable cells fall in that gap for every species (in
    this repository's raster, roughly 96-97% of the grid). Rather than
    discarding those cells (which would shrink the plantable-area estimate
    to a sliver unrelated to nbs.landscape's own accounting) or propagating
    NaN into every downstream sum, the albedo term is treated as zero there:
    the CO2 channel, which never depends on P_c, is unaffected, and the
    albedo channel is simply not claimed where it is unmeasured.
    """
    return np.nan_to_num(alpha_q_product(species_key), nan=0.0)


def aggregate_by_species() -> dict[str, tuple[float, float]]:
    """Per species, ``(sum_c N_c, sum_c N_c * P_c)`` over every grid cell.

    ``N_c`` is the tree count assigned to a cell (``nbs.landscape.tree_count``)
    and ``P_c`` its afforestation Delta_alpha * q_sw product
    (``nbs.albedo_grid.alpha_q_product``, with NaN cells treated as zero --
    see ``_product_no_nan``). These two scalars per species are everything
    ``global_delta_t`` needs -- purely geometric, independent of scenario or
    model config.
    """
    species_grid = assign_species()
    n_grid = tree_count()

    out: dict[str, tuple[float, float]] = {}
    for key in SPECIES:
        mask = species_grid == key
        n_sum = float(n_grid[mask].sum())
        if mask.any():
            p = _product_no_nan(key)
            np_sum = float(np.sum(n_grid[mask] * p[mask]))
        else:
            np_sum = 0.0
        out[key] = (n_sum, np_sum)
    return out


def global_delta_t(scenario: str = "ssp245", config: ModelConfig | None = None) -> NDArray:
    """Length-126 global Delta_T(t) [K], summed over every grid cell.

    Formed from ``aggregate_by_species``'s two scalars per species and
    ``unit_curves``'s two curves per species -- five species, ten
    convolutions total, never per-cell. Exact, not an approximation; see the
    module docstring and ``tests/test_aggregate.py::
    test_aggregation_equals_cellwise_computation_on_a_sample``.
    """
    total = np.zeros(len(YEARS), dtype=float)
    for key, (n_sum, np_sum) in aggregate_by_species().items():
        if n_sum == 0.0 and np_sum == 0.0:
            continue
        co2, albedo_unit = unit_curves(key, scenario, config)
        total += n_sum * co2 + np_sum * albedo_unit
    return total


def delta_t_at_year(
    year: int, scenario: str = "ssp245", config: ModelConfig | None = None
) -> NDArray:
    """(360, 720) Delta_T [K] at *year*, one cell-wise field.

    Never builds the full (360, 720, 126) array (1.5 GB) -- only this one
    year's slice of each species' unit curves is read out, then every cell is
    one multiply-add against its own N_c and P_c.
    """
    idx = _year_index(year)
    species_grid = assign_species()
    n_grid = tree_count()

    field = np.zeros(species_grid.shape, dtype=float)
    for key in SPECIES:
        mask = species_grid == key
        if not mask.any():
            continue
        co2, albedo_unit = unit_curves(key, scenario, config)
        c = float(co2[idx])
        a = float(albedo_unit[idx])
        p = _product_no_nan(key)
        field[mask] = n_grid[mask] * (c + a * p[mask])
    return field


def delta_t_field(
    years_subset: list[int] | NDArray,
    scenario: str = "ssp245",
    config: ModelConfig | None = None,
) -> NDArray:
    """(len(years_subset), 360, 720) Delta_T [K] at a handful of support years.

    Same shortcut as ``delta_t_at_year``, evaluated at several years without
    recomputing the unit curves per year: each species' curves are read out
    once for every requested year, not resimulated.
    """
    idxs = [_year_index(y) for y in years_subset]
    species_grid = assign_species()
    n_grid = tree_count()

    out = np.zeros((len(idxs),) + species_grid.shape, dtype=float)
    for key in SPECIES:
        mask = species_grid == key
        if not mask.any():
            continue
        co2, albedo_unit = unit_curves(key, scenario, config)
        p = _product_no_nan(key)
        n_masked = n_grid[mask]
        p_masked = p[mask]
        for k, idx in enumerate(idxs):
            c = float(co2[idx])
            a = float(albedo_unit[idx])
            out[k][mask] = n_masked * (c + a * p_masked)
    return out


__all__ = [
    "aggregate_by_species",
    "delta_t_at_year",
    "delta_t_field",
    "global_delta_t",
    "unit_curves",
]
