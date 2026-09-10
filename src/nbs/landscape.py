"""Species assignment and plantable area per grid cell.

**Land mask.** ``land_mask()`` is derived from the Duveiller albedo-transition
raster (``data/raw/alb_det.nc``, the same file ``nbs.albedo_grid`` reads):
the union, across all 45 land-cover transitions and all 12 months, of cells
where ``Delta_albedo_ext`` is finite. The dataset only carries a value where
the transition's vegetated land cover is actually present, so this union is
a usable vegetated-land mask even though the raster was never built to be
one. Measured: 52 688 of 259 200 half-degree cells, 20.3% of the globe --
below the textbook ~29% land fraction because it excludes desert, ice and
bare rock (nothing in a forest <-> grassland/cropland transition dataset has
signal there), which is the expected direction and size for a
vegetation-only mask. Falls back to an all-land grid, clearly labelled via
``land_mask_provenance() == "fallback_alles_land"``, if the raster is not on
disk -- this is deliberately not a coastline approximation; a caller without
the raster must see loudly that nothing is being excluded, not silently get
a plausible-looking but invented shape.

**Species assignment**, and the plantable/exclusion split within land, still
have no land-cover / Global Ecological Zone (GEZ) source to work from (only
the Duveiller albedo-transition rasters are registered in
``nbs.datasources``), so ``provenance()`` -- unrelated to
``land_mask_provenance()`` above -- always reports ``"fallback"``. Every
species' ``valid_gez`` tuple is a set of named FAO Global Ecological Zones;
absent an actual GEZ raster, the zones are approximated by five
non-overlapping absolute-latitude bands, chosen so each band's dominant zone
matches one species' registered GEZ list:

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
``exclusion_mask()["kryosphaere"]``), regardless of the land mask -- a
latitude-only rule, same as before this fix. No land cell in the 0-70 degree
range is left unassigned: exactly one species covers every band, chosen for
that band rather than letting several tied candidates compete cell by cell,
because a raster-free grid has no per-cell signal to break the tie with.

**Exclusion masks.** ``exclusion_mask()`` returns the five reasons the
talk's potential cascade (Akt 6) enumerates, each its own boolean grid so a
later waterfall chart can put a number on every correction separately:
``"kein_land"`` (the land mask's complement, restricted to the
non-kryosphaere rows -- see below), ``"bestehender_wald"`` (already
forested), ``"savanne_grasland"`` (natural savanna, grassland, steppe and
desert -- land whose native cover is not a closed canopy, so afforesting it
is a land-cover conversion, not restoration, per the Bastin-critique reading
the talk follows), ``"kryosphaere"`` (beyond the tree line), and
``"landwirtschaft"`` (cropland, excluded on food-security grounds).

Row by row: rows at or beyond ``KRYOSPHERE_LAT_DEG`` absolute latitude are
entirely ``"kryosphaere"``, regardless of ``land_mask()`` -- this predates
the land-mask fix and is left as is, since it is a real biophysical rule
(beyond the tree line, nothing is planted whether it is land or sea ice).
For every other row, ``"kein_land"`` is set to exactly ``~land_mask()`` for
that row: this is what makes the two masks each other's complement outside
the kryosphaere, per the fix's instruction, while keeping the five masks
mutually exclusive (a kryosphaere-row ocean cell is "kryosphaere", not
double-counted as "kein_land").

Within the land cells of a non-kryosphaere row, a fixed per-row random
permutation of *only those land columns* (seeded on the row index, so the
split is reproducible and deterministic but not a single contiguous
geographic block) partitions them into existing-forest, savanna/grassland/
desert, cropland and plantable, using hard-coded biome-area *fractions of
land* per band (order-of-magnitude figures compatible with FAO /
Bastin-era global forest and land-use statistics, not observations of the
specific band). This has no locational meaning within a row and must not be
read as "this longitude is savanna" -- only the per-row *count* in each
category, and hence the row's total area, is meant to carry information.
Confetti at this level (a plantable pixel with non-plantable land on every
side) is the known, accepted residue of this synthetic split; what the land
mask fixes is confetti *over ocean*, which had no such excuse.

A cell in the "plantable" remainder gets the row's full cell area; nothing
here models partial canopy density within a plantable cell, matching how
``tree_count()`` (area / stand_area_m2) already treats the whole area as
available for planting at the assigned species' stand density.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import xarray as xr
from numpy.typing import NDArray

from nbs.datasources import resolve
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

# Per band, in the same order as _BAND_SPECIES -- fractions *of land*, not of
# the row's total area (the row's land extent now comes from land_mask()):
#   forest_frac  -- fraction of LAND already existing closed forest
#   savanna_frac -- fraction of LAND that is savanna, grassland, steppe or
#                   desert (natural non-forest cover, per the Bastin-critique
#                   reading: afforesting it is conversion, not restoration)
#   agri_frac    -- fraction of LAND under cropland
# Order-of-magnitude figures only, chosen to be compatible with widely cited
# global totals (~31% of land under forest, ~12% cropland, ~25% grass/
# savanna/desert -- FAO FRA-era statistics), not measurements of any one
# band. See the module docstring.
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
def _land_mask_and_provenance() -> tuple[NDArray, str]:
    """Build the (360, 720) vegetated-land mask once, with its provenance.

    "raster": built from the union, over all 45 iTr transitions and all 12
    months, of finite ``Delta_albedo_ext`` cells in ``data/raw/alb_det.nc``
    (native 1-degree grid, regridded onto the 0.5-degree target grid by
    exact 2x replication, the same scheme ``nbs.albedo_grid._regrid`` uses).
    A cell is finite there only where Duveiller et al. (2018) actually
    observed the underlying vegetated land-cover transition, so the union is
    a real, if imperfect (vegetation-only, not full-land) footprint.

    "fallback_alles_land": the raster is not on disk. Rather than inventing
    a coastline, every cell is marked land -- a caller without the raster
    must see, loudly, that nothing is being excluded, not quietly get a
    plausible-looking shape that happens to be wrong at the coast.
    """
    path = resolve("duveiller_albedo")
    if path is None:
        return np.ones((N_LAT, N_LON), dtype=bool), "fallback_alles_land"

    with xr.open_dataset(path) as ds:
        finite = np.isfinite(np.asarray(ds["Delta_albedo_ext"].values))  # (45, 12, 180, 360)
    union_native = finite.any(axis=(0, 1))  # (180, 360)
    mask = np.repeat(np.repeat(union_native, 2, axis=0), 2, axis=1)
    assert mask.shape == (N_LAT, N_LON)
    return mask, "raster"


def land_mask() -> NDArray:
    """(360, 720) bool: True where the raster union sees vegetated land.

    See ``land_mask_provenance()`` for whether this came from the Duveiller
    raster or from the all-land fallback.
    """
    mask, _prov = _land_mask_and_provenance()
    return mask.copy()


def land_mask_provenance() -> str:
    """"raster" or "fallback_alles_land" -- see ``land_mask()``."""
    _mask, prov = _land_mask_and_provenance()
    return prov


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
    land = land_mask()

    for i in range(N_LAT):
        abs_lat = abs(float(lats[i]))
        row_area = float(cell_area[i, 0])  # constant along a latitude row

        if abs_lat >= KRYOSPHERE_LAT_DEG:
            masks["kryosphaere"][i, :] = True
            continue

        land_row = land[i, :]
        land_cols = np.flatnonzero(land_row)
        n_land = land_cols.size
        masks["kein_land"][i, :] = ~land_row

        if n_land == 0:
            continue

        band_idx = _band_index(abs_lat)
        assert band_idx is not None, f"lat {lats[i]} not covered by any band"
        species_key = _BAND_SPECIES[band_idx][2]
        forest_frac = _FOREST_FRAC[band_idx]
        savanna_frac = _SAVANNA_FRAC[band_idx]
        agri_frac = _AGRI_FRAC[band_idx]

        n_forest = round(n_land * forest_frac)
        n_savanna = round(n_land * savanna_frac)
        n_agri = round(n_land * agri_frac)
        n_used = n_forest + n_savanna + n_agri
        if n_used > n_land:
            # Rounding overshoot on a near-full land row; trim agriculture
            # last -- it is the smallest share everywhere it matters.
            n_agri = max(0, n_agri - (n_used - n_land))
            n_used = n_forest + n_savanna + n_agri

        order = np.random.default_rng(i).permutation(n_land)
        pos = 0
        forest_cols = land_cols[order[pos : pos + n_forest]]
        pos += n_forest
        savanna_cols = land_cols[order[pos : pos + n_savanna]]
        pos += n_savanna
        agri_cols = land_cols[order[pos : pos + n_agri]]
        pos += n_agri
        plantable_cols = land_cols[order[pos:]]

        masks["bestehender_wald"][i, forest_cols] = True
        masks["savanne_grasland"][i, savanna_cols] = True
        masks["landwirtschaft"][i, agri_cols] = True

        species_grid[i, plantable_cols] = species_key
        area_grid[i, plantable_cols] = row_area
        count_grid[i, plantable_cols] = row_area / get_species(species_key).stand_area_m2

    return species_grid, area_grid, count_grid, masks


def assign_species() -> NDArray:
    """(360, 720) object array: species key per cell, or None where unplantable.

    None everywhere ``land_mask()`` is False, plus the latitude-band
    exclusions (kryosphaere) and the synthetic forest/savanna/agriculture
    split within land -- see the module docstring for the exact bands and
    fractions. Not derived from any land-cover/GEZ raster.
    """
    species_grid, _area, _count, _masks = _compute()
    return species_grid.copy()


def plantable_area_m2() -> NDArray:
    """(360, 720) afforestable area per cell [m^2], 0 where excluded
    (including everywhere outside ``land_mask()``)."""
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
    most one, via the per-row partition in ``_compute``). "kein_land" is
    exactly ``~land_mask()`` on every row that is not entirely
    "kryosphaere" -- see the module docstring.
    """
    _species, _area, _count, masks = _compute()
    return {name: grid.copy() for name, grid in masks.items()}


def provenance() -> str:
    """Always "fallback": no land-cover/GEZ raster is registered in
    nbs.datasources for species assignment or the forest/savanna/agriculture
    split, so this module has never had a raster path to report *that* part
    of the pipeline from. This is unrelated to ``land_mask_provenance()``,
    which the land mask itself (built from the Duveiller raster union when
    available) now does report honestly.
    """
    return "fallback"


__all__ = [
    "KRYOSPHERE_LAT_DEG",
    "assign_species",
    "exclusion_mask",
    "land_mask",
    "land_mask_provenance",
    "plantable_area_m2",
    "provenance",
    "tree_count",
]
