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
from nbs.constants import A_EARTH_M2, T_END, TAU_ATM, YEARS
from nbs.landscape import assign_species, tree_count
from nbs.pipeline import run_single_tree
from nbs.response import convolve_response, green_temperature
from nbs.site_factor import site_factor_grid
from nbs.species import SPECIES, get_species, reference_site


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
    # At the species' reference site the site factor is 1: the CO2 curve is
    # the per-tree curve of slide 12, scaled per cell by co2_factor_grid.
    result = run_single_tree(
        species_key, lat_deg=reference_site(species_key), scenario=scenario, config=config
    )
    g_t = green_temperature(scenario)

    delta_t_co2 = convolve_response(g_t, result.phi_co2)

    if config.albedo:
        sp = get_species(species_key)
        closure = np.asarray(result.trajectory.closure, dtype=float)
        unit_phi_albedo = -TAU_ATM * closure * sp.stand_area_m2 / A_EARTH_M2
        delta_t_albedo_unit = convolve_response(g_t, unit_phi_albedo)
    else:
        # config.albedo=False switches the channel off, as in nbs.pipeline.
        # Before 2026-10-05 this branch was missing, so every aggregate
        # "carbon only" variant still carried the albedo.
        delta_t_albedo_unit = np.zeros(len(YEARS), dtype=float)

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


def co2_factor_grid(species_key: str, config: ModelConfig | None = None) -> NDArray:
    """(360, 720) factor on the CO2 unit curve per cell: the site factor
    (``nbs.site_factor``) when config.site_growth, else 1 everywhere.

    Exact, not an approximation: the site factor scales only m_max, so stock,
    net uptake and disturbance losses -- and with them phi_CO2 -- scale
    linearly with it, while canopy closure (and the albedo unit curve) does not
    change at all."""
    if config is None:
        config = ModelConfig()
    if not config.site_growth:
        return np.ones((360, 720))
    return site_factor_grid(species_key)


def _product_no_nan(species_key: str) -> NDArray:
    """(360, 720) afforestation Delta_alpha * q_sw product.

    ``nbs.albedo_grid.alpha_q_product`` now guarantees a fully finite grid by
    construction: every cell is filled from one of three tiers (a real local
    Duveiller retrieval, a zonal latitude-band median of the same species'
    other retrievals, or the Plan 1 latitude stand-in -- see
    ``nbs.albedo_grid``'s "Three-tier gap fill" comment and
    ``product_provenance_grid`` / ``provenance_fractions`` for which tier
    backs any given cell). This function is a defensive check on that
    guarantee, not a patch: if it ever finds a NaN here, the guarantee broke
    somewhere upstream, and that must fail loudly rather than silently
    zeroing the albedo channel -- which is exactly what an earlier version of
    this function did, before the three-tier fill existed, for the ~91% of
    plantable enf_boreal cells the raw raster alone has no data for. A zero
    product is a real physical statement ("this forest does not change the
    albedo at all"); it must never be how "we have no data here" gets
    represented.
    """
    p = alpha_q_product(species_key)
    if not np.all(np.isfinite(p)):
        n_nan = int(np.sum(~np.isfinite(p)))
        raise ValueError(
            f"alpha_q_product({species_key!r}) enthaelt {n_nan} nicht-endliche "
            "Werte trotz der Drei-Stufen-Fuellung in nbs.albedo_grid; das "
            "sollte nie vorkommen -- die Fuellung ist kaputt, nicht dieser "
            "Aufruf."
        )
    return p


def aggregate_by_species(config: ModelConfig | None = None) -> dict[str, tuple[float, float]]:
    """Per species, ``(sum_c N_c, sum_c N_c * P_c)`` over every grid cell.

    ``N_c`` is the tree count assigned to a cell (``nbs.landscape.tree_count``),
    in the first scalar weighted by the cell's site factor ``f_c``
    (``co2_factor_grid``) because only the CO2 channel scales with it, so the
    pair is really ``(sum_c N_c f_c, sum_c N_c P_c)``;
    and ``P_c`` its afforestation Delta_alpha * q_sw product
    (``nbs.albedo_grid.alpha_q_product``, always fully finite through its own
    three-tier gap fill -- ``_product_no_nan`` here is a defensive check on
    that guarantee, not a patch for missing data). These two scalars per
    species are everything ``global_delta_t`` needs -- purely geometric,
    independent of scenario or model config.
    """
    species_grid = assign_species()
    n_grid = tree_count()

    out: dict[str, tuple[float, float]] = {}
    for key in SPECIES:
        mask = species_grid == key
        n_sum = float((n_grid[mask] * co2_factor_grid(key, config)[mask]).sum())
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
    for key, (n_sum, np_sum) in aggregate_by_species(config).items():
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
        f = co2_factor_grid(key, config)
        field[mask] = n_grid[mask] * (f[mask] * c + a * p[mask])
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
        f_masked = co2_factor_grid(key, config)[mask]
        for k, idx in enumerate(idxs):
            c = float(co2[idx])
            a = float(albedo_unit[idx])
            out[k][mask] = n_masked * (f_masked * c + a * p_masked)
    return out


def albedo_offset_field(
    year: int = T_END, scenario: str = "ssp245", config: ModelConfig | None = None
) -> NDArray:
    """(360, 720) albedo offset [%] per plantable cell, NaN elsewhere.

    The share of a cell's carbon cooling that its albedo warming cancels:

        offset = albedo warming / carbon cooling * 100

    0% means albedo costs nothing, 50% means it halves the benefit, and
    above 100% the cell is net warming even at *year*. This is the quantity
    Hasler et al. (2024) map globally, and the only one that lets this model
    be compared against an external result cell by cell -- see
    ``docs/superpowers/specs/2026-09-10-abgleich-hasler-2024.md``.

    Note what it is *not*: the cascade's albedo step
    (``nbs.potential.cascade``) removes cells that never break even at all,
    which is a filter on 1.8% of the area. This is a discount on every cell,
    and its median is around 39%. The two answer different questions -- "does
    it ever cool" versus "how much of the cooling survives" -- and neither
    substitutes for the other.

    Tree count cancels out of the ratio, so this is a per-hectare quantity
    that does not depend on the assumed stand density.
    """
    idx = _year_index(year)
    species_grid = assign_species()
    out = np.full(species_grid.shape, np.nan)
    for key in SPECIES:
        mask = species_grid == key
        if not mask.any():
            continue
        co2, albedo_unit = unit_curves(key, scenario, config)
        product = _product_no_nan(key)
        carbon = co2_factor_grid(key, config)[mask] * float(co2[idx])
        albedo = product[mask] * float(albedo_unit[idx])
        out[mask] = albedo / (-carbon) * 100.0
    return out


def albedo_offset_summary(
    year: int = T_END, scenario: str = "ssp245", config: ModelConfig | None = None
) -> dict[str, float]:
    """Area-weighted summary of ``albedo_offset_field``.

    ``median``       area-weighted median offset [%]
    ``ueber_50``     share of plantable area with more than 50% offset [-]
    ``ueber_100``    share that is net warming at *year* [-]
    ``p5``, ``p95``  unweighted 5th and 95th percentile [%]

    Area-weighted, not cell-weighted: half-degree cells differ in size by a
    factor of three across the plantable latitudes, and the comparison
    figures in Hasler et al. are area shares.
    """
    from nbs.landscape import plantable_area_m2

    field = albedo_offset_field(year, scenario, config)
    area = plantable_area_m2()
    finite = np.isfinite(field)
    values, weights = field[finite], area[finite]

    order = np.argsort(values)
    v_sorted, w_sorted = values[order], weights[order]
    total = w_sorted.sum()
    median = float(v_sorted[np.searchsorted(np.cumsum(w_sorted), 0.5 * total)])
    return {
        "median": median,
        "ueber_50": float(weights[values > 50.0].sum() / total),
        "ueber_100": float(weights[values > 100.0].sum() / total),
        "p5": float(np.percentile(values, 5)),
        "p95": float(np.percentile(values, 95)),
    }


__all__ = [
    "albedo_offset_field",
    "albedo_offset_summary",
    "aggregate_by_species",
    "delta_t_at_year",
    "delta_t_field",
    "global_delta_t",
    "unit_curves",
]
