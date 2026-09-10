"""Which species belongs where: available area and the best planting choice.

``nbs.landscape`` answers "how much room is there" and hands every cell in a
latitude band the *one* species that band represents. That assignment is a
bookkeeping device for the aggregate, not advice: it never asks whether a
different admissible species would cool the same hectare faster. This module
asks exactly that.

**Admissibility.** A species may be planted in a cell if the cell's absolute
latitude falls inside the latitude hull of the species' registered FAO Global
Ecological Zones (``Species.valid_gez``). The GEZ-to-latitude table below is
the inverse of the band table in ``nbs.landscape``'s docstring -- the same
raster-free approximation, used the same way, with the same caveat: absent a
GEZ raster these are bands, not biomes. The difference is that a *hull* over
several zones is wider than one band, so several species compete for the same
cell:

======================  ==============  ====================================
species                 |lat| hull      competitors in the overlap
======================  ==============  ====================================
tropical_mixed          0 - 35 deg      eucalyptus_grandis above 10 deg
eucalyptus_grandis      10 - 35 deg     tropical_mixed
fagus_sylvatica         35 - 60 deg     pinus_sylvestris, picea_abies
pinus_sylvestris        35 - 70 deg     fagus_sylvatica, picea_abies
picea_abies             35 - 70 deg     fagus_sylvatica, pinus_sylvestris
======================  ==============  ====================================

**The score.** Per hectare, not per tree -- the question is what to do with a
piece of land, and the five species stand at different densities (4 to 6 m^2
per tree), so a per-tree comparison would silently reward whichever species
is planted closest together. For species *s* in cell *c* at the horizon year,

    score_s(c) = (10 000 / A_stand,s) * [ dT_CO2,s + U_s * P_s(c) ]   [K/ha]

the same two unit curves ``nbs.aggregate.unit_curves`` returns, times the
cell's own Delta_alpha * q_sw product for *that species'* land-cover
transition (``nbs.albedo_grid.alpha_q_product``, species-dependent -- this is
what makes the recommendation vary in space rather than reproduce the
latitude bands). More negative is better. The recommendation is the argmin
over the admissible species; ``margin`` is the gap to the runner-up, i.e. how
much the choice is actually worth.

**Horizon-dependence is real, not a defect.** The default year is 2100. At an
early horizon the albedo penalty dominates and the ranking favours whatever
darkens the ground least; late, the carbon channel dominates. A slide that
shows one map must name its year, which is why ``year`` is in every public
signature and in the figure title.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from numpy.typing import NDArray

from nbs.aggregate import _product_no_nan, _year_index, unit_curves
from nbs.config import ModelConfig
from nbs.grid import grid_lats
from nbs.landscape import assign_species, plantable_area_m2
from nbs.species import SPECIES, get_species

M2_PER_HA = 1.0e4
M2_PER_GHA = 1.0e13
MK_PER_MHA_PER_K_PER_HA = 1.0e9
"""Display conversion: K/ha -> mK per million hectares (1e6 ha, 1e3 mK).

A single hectare moves the global mean temperature by ~1e-10 K, which reads
as -0.0 in any table a human looks at. Per Mha and in milli-kelvin the same
number is ~0.3, and a million hectares is the unit afforestation programmes
are actually announced in."""

# Inverse of the band table in nbs.landscape's docstring: the absolute
# latitude range [deg] each FAO Global Ecological Zone is approximated by.
# Same raster-free stand-in, same caveat -- see this module's docstring.
_GEZ_LAT_BANDS: dict[str, tuple[float, float]] = {
    "tropical_rainforest": (0.0, 10.0),
    "tropical_moist_deciduous_forest": (10.0, 35.0),
    "subtropical_humid_forest": (10.0, 35.0),
    "temperate_oceanic_forest": (35.0, 50.0),
    "temperate_continental_forest": (35.0, 60.0),
    "temperate_mountain_system": (35.0, 50.0),
    "boreal_coniferous_forest": (50.0, 70.0),
    "boreal_tundra_woodland": (60.0, 70.0),
}


def candidate_lat_range(species_key: str) -> tuple[float, float]:
    """(lo, hi) absolute latitude [deg] a species may be planted in.

    The hull of its ``valid_gez`` zones' bands. Every registered zone must be
    in ``_GEZ_LAT_BANDS``: an unknown zone means a species was added without
    deciding where it grows, which must fail loudly rather than quietly
    shrinking that species' range to its known zones.
    """
    zones = get_species(species_key).valid_gez
    unknown = [z for z in zones if z not in _GEZ_LAT_BANDS]
    if unknown:
        raise KeyError(
            f"{species_key}: keine Breitenbaender fuer die Zonen {unknown} "
            "hinterlegt (nbs.recommend._GEZ_LAT_BANDS)"
        )
    los = [_GEZ_LAT_BANDS[z][0] for z in zones]
    his = [_GEZ_LAT_BANDS[z][1] for z in zones]
    return min(los), max(his)


def admissible_mask(species_key: str) -> NDArray:
    """(360, 720) bool: cells that are plantable *and* in the species' hull."""
    lo, hi = candidate_lat_range(species_key)
    abs_lat = np.abs(grid_lats())[:, None]
    in_band = (abs_lat >= lo) & (abs_lat < hi)
    return np.broadcast_to(in_band, (360, 720)) & (plantable_area_m2() > 0.0)


def score_field(
    species_key: str,
    year: int = 2100,
    scenario: str = "ssp245",
    config: ModelConfig | None = None,
) -> NDArray:
    """(360, 720) Delta_T per hectare [K/ha] at *year*, NaN where inadmissible.

    Negative is cooling. See the module docstring for why the normalisation is
    per hectare and not per tree.
    """
    idx = _year_index(year)
    co2, albedo_unit = unit_curves(species_key, scenario, config)
    trees_per_ha = M2_PER_HA / get_species(species_key).stand_area_m2
    product = _product_no_nan(species_key)

    field = trees_per_ha * (float(co2[idx]) + float(albedo_unit[idx]) * product)
    return np.where(admissible_mask(species_key), field, np.nan)


@dataclass(frozen=True)
class Recommendation:
    """Per-cell planting advice at one horizon year."""

    year: int
    scenario: str
    species: NDArray
    """(360, 720) object: recommended species key, None where not plantable."""
    score: NDArray
    """(360, 720) [K/ha]: the recommended species' score, NaN off-grid."""
    margin: NDArray
    """(360, 720) [K/ha]: runner-up score minus recommended score, >= 0.
    NaN where no second admissible species exists (or no first)."""
    assigned: NDArray
    """(360, 720) object: what ``nbs.landscape.assign_species`` would plant."""


@lru_cache(maxsize=8)
def _recommend_cached(year: int, scenario: str, config: ModelConfig) -> Recommendation:
    keys = list(SPECIES)
    stacked = np.stack([score_field(k, year, scenario, config) for k in keys])  # (S, 360, 720)

    any_admissible = np.any(np.isfinite(stacked), axis=0)
    filled = np.where(np.isfinite(stacked), stacked, np.inf)
    best_idx = np.argmin(filled, axis=0)

    best_score = np.take_along_axis(filled, best_idx[None], axis=0)[0]
    # Runner-up: the smallest score that is not the winner's own entry.
    without_best = filled.copy()
    np.put_along_axis(without_best, best_idx[None], np.inf, axis=0)
    second_score = np.min(without_best, axis=0)

    species = np.full(best_idx.shape, None, dtype=object)
    key_arr = np.array(keys, dtype=object)
    species[any_admissible] = key_arr[best_idx[any_admissible]]

    score = np.where(any_admissible, best_score, np.nan)
    has_second = any_admissible & np.isfinite(second_score)
    # Subtract only where both entries are finite: inf - inf is a NaN *and* a
    # RuntimeWarning, and the cells it would fire on are exactly the ones
    # already destined for NaN.
    margin = np.full(best_score.shape, np.nan)
    margin[has_second] = second_score[has_second] - best_score[has_second]

    return Recommendation(
        year=year,
        scenario=scenario,
        species=species,
        score=score,
        margin=margin,
        assigned=assign_species(),
    )


def recommend(
    year: int = 2100, scenario: str = "ssp245", config: ModelConfig | None = None
) -> Recommendation:
    """Best admissible species per plantable cell at *year*.

    Cached per (year, scenario, config); the returned arrays are the cached
    ones, so treat them as read-only.
    """
    return _recommend_cached(year, scenario, config or ModelConfig())


def total_delta_t(
    species_grid: NDArray,
    year: int = 2100,
    scenario: str = "ssp245",
    config: ModelConfig | None = None,
) -> float:
    """Global Delta_T [K] at *year* if every plantable cell carries
    ``species_grid``'s species, at that species' stand density.

    Cell contribution is ``area_ha * score_s(cell)``, the same score the
    recommendation ranks by -- so this and ``recommend`` can never disagree
    about which of two grids is better.
    """
    area_ha = plantable_area_m2() / M2_PER_HA
    total = 0.0
    for key in SPECIES:
        mask = species_grid == key
        if not mask.any():
            continue
        idx = _year_index(year)
        co2, albedo_unit = unit_curves(key, scenario, config)
        trees_per_ha = M2_PER_HA / get_species(key).stand_area_m2
        product = _product_no_nan(key)
        per_ha = trees_per_ha * (float(co2[idx]) + float(albedo_unit[idx]) * product[mask])
        total += float(np.sum(area_ha[mask] * per_ha))
    return total


def summary(
    year: int = 2100, scenario: str = "ssp245", config: ModelConfig | None = None
) -> dict[str, dict[str, float]]:
    """Per species: recommended and band-assigned area [Gha], mean score and
    mean margin (both in mK per Mha, see MK_PER_MHA_PER_K_PER_HA) over the
    cells where it is recommended.

    ``flaeche_gha`` sums to the total plantable area; ``flaeche_zugewiesen_gha``
    does too, so the two columns are directly comparable.
    """
    rec = recommend(year, scenario, config)
    area = plantable_area_m2()

    out: dict[str, dict[str, float]] = {}
    for key in SPECIES:
        mask = rec.species == key
        assigned_mask = rec.assigned == key
        out[key] = {
            "flaeche_gha": float(area[mask].sum() / M2_PER_GHA),
            "flaeche_zugewiesen_gha": float(area[assigned_mask].sum() / M2_PER_GHA),
            "score_mk_pro_mha": (
                float(np.mean(rec.score[mask])) * MK_PER_MHA_PER_K_PER_HA
                if mask.any()
                else float("nan")
            ),
            "vorsprung_mk_pro_mha": (
                float(np.nanmean(rec.margin[mask])) * MK_PER_MHA_PER_K_PER_HA
                if mask.any()
                else float("nan")
            ),
        }
    return out


def improvement(
    year: int = 2100, scenario: str = "ssp245", config: ModelConfig | None = None
) -> dict[str, float]:
    """How much the species choice is worth against the latitude-band default.

    Returns the two global Delta_T values [K] and the relative gain. The gain
    is never negative: the band assignment is one admissible grid among the
    ones the argmin ranks, so the recommendation is at least as good by
    construction.
    """
    rec = recommend(year, scenario, config)
    dt_rec = total_delta_t(rec.species, year, scenario, config)
    dt_band = total_delta_t(rec.assigned, year, scenario, config)
    gain = dt_band - dt_rec  # both negative; recommended is the more negative
    rel = gain / abs(dt_band) if dt_band != 0.0 else float("nan")
    return {
        "delta_t_empfohlen_k": dt_rec,
        "delta_t_breitenband_k": dt_band,
        "gewinn_k": gain,
        "gewinn_anteil": rel,
    }


__all__ = [
    "MK_PER_MHA_PER_K_PER_HA",
    "M2_PER_GHA",
    "M2_PER_HA",
    "Recommendation",
    "admissible_mask",
    "candidate_lat_range",
    "improvement",
    "recommend",
    "score_field",
    "summary",
    "total_delta_t",
]
