"""Species assignment and plantable area per grid cell.

**This module has no land-cover raster to work from.** No land-cover /
Global Ecological Zone (GEZ) source is registered in ``nbs.datasources`` (only
the two Duveiller albedo-transition rasters are), so every number this module
returns is a stand-in, not a measurement, and ``provenance()`` always reports
``"fallback"``. The moment a real GEZ/IGBP raster is registered and wired up,
this module should read that grid instead of the latitude bands below --
until then, the assignment is driven purely by ``nbs.species.Species.valid_gez``
and by literature-order-of-magnitude biome-area fractions, both hard-coded and
clearly not per-cell geography (a Siberian cell and a Canadian cell at the
same latitude get the same treatment; deserts, mountains and coastlines are
not resolved).

**Species assignment.** Every species' ``valid_gez`` tuple is a set of named
FAO Global Ecological Zones; absent an actual GEZ raster, the zones are
approximated by five non-overlapping absolute-latitude bands, chosen so each
band's dominant zone matches one species' registered GEZ list:

============  ========================  ================================
|lat| (deg)   species                   representative GEZ
============  ========================  ================================
 0 - 10       tropical_mixed            tropical_rainforest
10 - 35       eucalyptus_grandis        tropical_moist_deciduous_forest /
                                         subtropical_humid_forest
35 - 50       fagus_sylvatica           temperate_oceanic_forest /
                                         temperate_continental_forest
50 - 60       pinus_sylvestris          temperate_continental_forest /
                                         boreal_coniferous_forest
60 - 70       picea_abies               boreal_coniferous_forest /
                                         boreal_tundra_woodland
============  ========================  ================================

Cells beyond 70 degrees absolute latitude get no species (see
``exclusion_mask()["kryosphaere"]``). No cell in the 0-70 degree range is
left unassigned: exactly one species covers every band, chosen for that
band rather than letting several tied candidates compete cell by cell,
because a raster-free grid has no per-cell signal to break the tie with.

**Exclusion masks.** ``exclusion_mask()`` returns the five reasons the
talk's potential cascade (Akt 6) enumerates, each its own boolean grid so
a later waterfall chart can put a number on every correction separately:
``"kein_land"`` (ocean), ``"bestehender_wald"`` (already forested),
``"savanne_grasland"`` (natural savanna, grassland, steppe and desert --
land whose native cover is not a closed canopy, so afforesting it is a
land-cover conversion, not restoration, per the Bastin-critique reading the
talk follows), ``"kryosphaere"`` (beyond the tree line), and
``"landwirtschaft"`` (cropland, excluded on food-security grounds).

Absent per-cell geography, each latitude row is partitioned into these five
categories plus a "plantable" remainder by hard-coded biome-area fractions
per band (land fraction, and within the land fraction: existing-forest,
savanna/grassland/desert, and cropland shares -- order-of-magnitude figures
compatible with FAO / Bastin-era global forest and land-use statistics, not
observations of the specific band). The row's columns are then split
between the categories by a fixed per-row random permutation (seeded on the
row index, so the split is reproducible and deterministic but not a single
contiguous geographic block); this has no locational meaning and must not
be read as "this longitude is savanna" -- only the per-row *count* in each
category, and hence the row's total area, is meant to carry information.

A cell in the "plantable" remainder gets the row's full cell area; nothing
here models partial canopy density within a plantable cell, matching how
``tree_count()`` (area / stand_area_m2) already treats the whole area as
available for planting at the assigned species' stand density.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.typing import NDArray

from nbs.grid import N_LAT, N_LON, cell_area_m2, grid_lats
from nbs.species import get_species

# (lower bound, upper bound) absolute latitude [deg], exclusive of the upper
# bound except for the last band, and the species assigned to that band.
_BAND_SPECIES: tuple[tuple[float, float, str], ...] = (
    (0.0, 10.0, "tropical_mixed"),
    (10.0, 35.0, "eucalyptus_grandis"),
    (35.0, 50.0, "fagus_sylvatica"),
    (50.0, 60.0, "pinus_sylvestris"),
    (60.0, 70.0, "picea_abies"),
)
KRYOSPHERE_LAT_DEG = 70.0
"""Cells beyond this absolute latitude are entirely kryosphaere (no species)."""

# Per band, in the same order as _BAND_SPECIES:
#   land_frac    -- fraction of the row's area that is land, not ocean
#   forest_frac  -- fraction of LAND already existing closed forest
#   savanna_frac -- fraction of LAND that is savanna, grassland, steppe or
#                   desert (natural non-forest cover, per the Bastin-critique
#                   reading: afforesting it is conversion, not restoration)
#   agri_frac    -- fraction of LAND under cropland
# Order-of-magnitude figures only, chosen to be compatible with widely cited
# global totals (~31% of land under forest, ~12% cropland, ~25% grass/
# savanna/desert -- FAO FRA-era statistics), not measurements of any one
# band. See the module docstring.
_LAND_FRAC = (0.20, 0.30, 0.42, 0.30, 0.35)
_FOREST_FRAC = (0.60, 0.20, 0.35, 0.55, 0.45)
_SAVANNA_FRAC = (0.20, 0.62, 0.32, 0.18, 0.22)
_AGRI_FRAC = (0.10, 0.15, 0.28, 0.18, 0.05)

_MASK_NAMES = (
    "kein_land",
    "bestehender_wald",
    "savanne_grasland",
    "kryosphaere",
    "landwirtschaft",
)


def _band_index(abs_lat_deg: float) -> int | None:
    for idx, (lo, hi, _key) in enumerate(_BAND_SPECIES):
        if lo <= abs_lat_deg < hi:
            return idx
    return None


@lru_cache(maxsize=1)
def _compute() -> tuple[NDArray, NDArray, NDArray, dict[str, NDArray]]:
    """Build the species grid, plantable area, tree count and exclusion masks.

    Computed once and cached; the public functions below return copies so a
    caller can never mutate the cached arrays out from under later calls.
    """
    species_grid = np.full((N_LAT, N_LON), None, dtype=object)
    area_grid = np.zeros((N_LAT, N_LON), dtype=float)
    count_grid = np.zeros((N_LAT, N_LON), dtype=float)
    masks = {name: np.zeros((N_LAT, N_LON), dtype=bool) for name in _MASK_NAMES}

    cell_area = cell_area_m2()
    lats = grid_lats()

    for i in range(N_LAT):
        abs_lat = abs(float(lats[i]))
        row_area = float(cell_area[i, 0])  # constant along a latitude row

        if abs_lat >= KRYOSPHERE_LAT_DEG:
            masks["kryosphaere"][i, :] = True
            continue

        band_idx = _band_index(abs_lat)
        assert band_idx is not None, f"lat {lats[i]} not covered by any band"
        species_key = _BAND_SPECIES[band_idx][2]
        land_frac = _LAND_FRAC[band_idx]
        forest_frac = _FOREST_FRAC[band_idx]
        savanna_frac = _SAVANNA_FRAC[band_idx]
        agri_frac = _AGRI_FRAC[band_idx]

        n_ocean = round((1.0 - land_frac) * N_LON)
        n_forest = round(land_frac * forest_frac * N_LON)
        n_savanna = round(land_frac * savanna_frac * N_LON)
        n_agri = round(land_frac * agri_frac * N_LON)
        n_used = n_ocean + n_forest + n_savanna + n_agri
        if n_used > N_LON:
            # Rounding overshoot on a near-full row; trim agriculture last --
            # it is the smallest share everywhere it matters.
            n_agri = max(0, n_agri - (n_used - N_LON))
            n_used = n_ocean + n_forest + n_savanna + n_agri

        order = np.random.default_rng(i).permutation(N_LON)
        pos = 0
        ocean_cols = order[pos : pos + n_ocean]
        pos += n_ocean
        forest_cols = order[pos : pos + n_forest]
        pos += n_forest
        savanna_cols = order[pos : pos + n_savanna]
        pos += n_savanna
        agri_cols = order[pos : pos + n_agri]
        pos += n_agri
        plantable_cols = order[pos:]

        masks["kein_land"][i, ocean_cols] = True
        masks["bestehender_wald"][i, forest_cols] = True
        masks["savanne_grasland"][i, savanna_cols] = True
        masks["landwirtschaft"][i, agri_cols] = True

        species_grid[i, plantable_cols] = species_key
        area_grid[i, plantable_cols] = row_area
        count_grid[i, plantable_cols] = row_area / get_species(species_key).stand_area_m2

    return species_grid, area_grid, count_grid, masks


def assign_species() -> NDArray:
    """(360, 720) object array: species key per cell, or None where unplantable.

    Fallback assignment by absolute-latitude band, consistent with each
    registered species' ``valid_gez`` -- see the module docstring for the
    exact bands. Not derived from any land-cover raster.
    """
    species_grid, _area, _count, _masks = _compute()
    return species_grid.copy()


def plantable_area_m2() -> NDArray:
    """(360, 720) afforestable area per cell [m^2], 0 where excluded."""
    _species, area_grid, _count, _masks = _compute()
    return area_grid.copy()


def tree_count() -> NDArray:
    """(360, 720) trees per cell: plantable_area_m2() / stand_area_m2 of the
    assigned species, 0 where no species is assigned."""
    _species, _area, count_grid, _masks = _compute()
    return count_grid.copy()


def exclusion_mask() -> dict[str, NDArray]:
    """Per exclusion reason, a (360, 720) boolean grid.

    Reasons: "kein_land", "bestehender_wald", "savanne_grasland",
    "kryosphaere", "landwirtschaft" -- the terms the talk's potential
    cascade (Akt 6) enumerates, one mask each so a waterfall chart can show
    every correction's own area rather than a single lumped total. The five
    masks are mutually exclusive by construction (each cell falls into at
    most one, via the per-row partition in ``_compute``).
    """
    _species, _area, _count, masks = _compute()
    return {name: grid.copy() for name, grid in masks.items()}


def provenance() -> str:
    """Always "fallback": no land-cover/GEZ raster is registered in
    nbs.datasources, so this module has never had a raster path to report.
    """
    return "fallback"


__all__ = [
    "KRYOSPHERE_LAT_DEG",
    "assign_species",
    "exclusion_mask",
    "plantable_area_m2",
    "provenance",
    "tree_count",
]
