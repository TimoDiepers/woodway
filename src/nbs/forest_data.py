"""Forest types per grid cell, from published global data (2026-10-05).

Replaces the earlier five hand-parameterised species, latitude bands and the
synthetic plantable split (nbs.landscape before this date).

* **Where reforestation is possible:** Walker et al. (2022, PNAS 119,
  e2111312119) NCS opportunity categories R/L + R/H, outside areas critical to
  food production and human habitation: 0.931 Gha.
* **How much carbon it adds:** Walker et al. *constrained unrealized*
  potential AGB+BGB [Mg C/ha] over exactly those pixels -- potential minus the
  current stock, i.e. the gain. Varies per cell.
* **Which forest grows there:** Hasler et al. (2024, Nat. Commun. 15, 2275)
  most likely forest class (IGBP ENF, EBF, DNF, DBF, MF). Woody savanna cells
  get their most frequent real forest class; reforestable cells without any
  forest class get the most frequent class in the 3x3, then 5x5 neighbourhood.
* **Which other types could grow there (for the comparison):** every class
  with at least 10 % of the classified pixels in the 3x3 neighbourhood.
* **How fast it grows:** Cook-Patton et al. (2020, Nature 585, 545) carbon
  accumulation in the first 30 years of natural regrowth (aboveground;
  belowground added with a root:shoot ratio of 0.25). The young forest grows
  towards Walker's *potential* stock P; with Chapman-Richards
  m(t) = P (1 - exp(-k t))^p, p = 2, the 30-year share
  f30 = 30 r (1 + 0.25) / P gives k = -ln(1 - sqrt(f30)) / 30, f30 capped at
  0.55 (Poorter et al. 2016: 90 % of old-growth biomass after 66 years). The carbon *gain* follows the same shape with amplitude M. k is the area-weighted median per forest type and climate zone, so
  the aggregation over cells stays exact (only M varies per cell).
* **Climate zone:** Walker et al. bioclimate zones (from FAO GEZ). The
  README swaps two codes; by latitude 1 is boreal and 5 polar. Polar cells
  (tundra margins) are treated as boreal.

Carbon is the same for all types at one location: the IPCC 2019 Tier-1
tables show no robust difference between forest types at the same place
(temperate plantations > 20 years: broadleaf ~ conifer ~ 200 t d.m./ha).
Types differ in albedo (Duveiller per IGBP class) and disturbance.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from nbs.grid import grid_lats

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "forest" / "forest_grid_0p5.npz"

TYPES = ("enf", "ebf", "dnf", "dbf", "mf")
IGBP_CODE = {"enf": 1, "ebf": 2, "dnf": 3, "dbf": 4, "mf": 5}
ZONES = {4: "tropisch", 2: "subtropisch", 3: "gemaessigt", 1: "boreal", 5: "boreal"}
ROOT_SHOOT = 0.25
P_SHAPE = 2.0
F30_CAP = 0.55
"""Upper bound on the 30-year share of the potential stock. Poorter et al.
(2016, Nature 530, 211-214): Neotropical secondary forests reach 90 % of
old-growth biomass after a median 66 years; with p = 2 that is 55 % after 30
years. Cook-Patton rates times 30 years exceed this share of Walker's
potential in about 40 % of the reforestable cells (mostly tropical evergreen
broadleaf and boreal evergreen needleleaf) -- the two datasets do not fit
there, and the field value is the more conservative, documented limit."""
ADMISSIBLE_SHARE = 0.10
TREES_PER_HA = 450.0  # trees left standing per ha after self-thinning (Albert et al. 2025): per-tree numbers = per-hectare / 450


@lru_cache(maxsize=1)
def raw() -> dict[str, NDArray]:
    with np.load(DATA) as f:
        return {k: f[k] for k in f.files}


def _neighbourhood_sum(a: NDArray, r: int) -> NDArray:
    out = np.zeros_like(a, dtype=float)
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            out += np.roll(np.roll(a, di, axis=-2), dj, axis=-1)
    return out


@lru_cache(maxsize=1)
def reforestable_area_m2() -> NDArray:
    return raw()["reforest_area_m2"].astype(float)


@lru_cache(maxsize=1)
def carbon_gain_mgc_ha() -> NDArray:
    """Constrained unrealized AGB+BGB carbon per reforestable hectare [Mg C/ha]."""
    return raw()["reforest_carbon_mgc_ha"].astype(float)


@lru_cache(maxsize=1)
def _forest_shares() -> NDArray:
    """(5, 360, 720) share of each real forest type among the classified pixels
    (woody savanna and none removed and renormalised)."""
    d = raw()
    classes = list(d["classes"])
    sh = np.stack([d["type_share"][classes.index(IGBP_CODE[t])] for t in TYPES]).astype(float)
    tot = sh.sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(tot > 0, sh / tot, 0.0)


@lru_cache(maxsize=None)
def typical_type(all_cells: bool = False) -> NDArray:
    """(360, 720) object: typical forest type key per cell, None where the
    cell is not reforestable (unless *all_cells*) or no forest type is found
    within 5x5 cells."""
    sh = _forest_shares()
    out = np.full(sh.shape[1:], None, dtype=object)
    refo = np.ones(sh.shape[1:], bool) if all_cells else reforestable_area_m2() > 0
    for r in (0, 1, 2):
        s = sh if r == 0 else _neighbourhood_sum(sh, r)
        has = s.sum(axis=0) > 0
        todo = refo & has & (out == None)  # noqa: E711
        idx = np.argmax(s, axis=0)
        for k, t in enumerate(TYPES):
            out[todo & (idx == k)] = t
    return out


@lru_cache(maxsize=1)
def admissible_types() -> dict[str, NDArray]:
    """Per type, (360, 720) bool: the type grows in the 3x3 neighbourhood
    with at least ADMISSIBLE_SHARE of the classified pixels, or is the
    cell's typical type. Only on reforestable cells."""
    s = _neighbourhood_sum(_forest_shares(), 1)
    tot = s.sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        share = np.where(tot > 0, s / tot, 0.0)
    typ = typical_type()
    refo = reforestable_area_m2() > 0
    return {t: refo & ((share[k] >= ADMISSIBLE_SHARE) | (typ == t)) for k, t in enumerate(TYPES)}


@lru_cache(maxsize=None)
def zone_name(all_cells: bool = False) -> NDArray:
    """(360, 720) object: climate zone name per cell (None where unknown)."""
    z = raw()["zone"]
    out = np.full(z.shape, None, dtype=object)
    for code, name in ZONES.items():
        out[z == code] = name
    # reforestable cells without a zone value: nearest zone in the row band
    lat = np.abs(grid_lats())[:, None] * np.ones((1, z.shape[1]))
    miss = (all_cells | (reforestable_area_m2() > 0)) & (out == None)  # noqa: E711
    out[miss & (lat < 23.5)] = "tropisch"
    out[miss & (lat >= 23.5) & (lat < 35)] = "subtropisch"
    out[miss & (lat >= 35) & (lat < 50)] = "gemaessigt"
    out[miss & (lat >= 50)] = "boreal"
    return out


@lru_cache(maxsize=1)
def k_per_cell() -> NDArray:
    """Chapman-Richards k per cell from Cook-Patton (NaN where no rate)."""
    r = raw()["cookpatton_agb_rate_mgc_ha_yr"].astype(float)
    # Pace relative to the forest's *potential* stock (what the young forest
    # grows towards); the gain (potential minus current stock) is only the
    # amplitude. Relative to the gain, boreal cells would saturate in 30 years.
    m = raw()["reforest_potential_mgc_ha"].astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        f30 = np.where((m > 0) & (r > 0), 30.0 * r * (1.0 + ROOT_SHOOT) / m, np.nan)
    f30 = np.minimum(f30, F30_CAP)
    return -np.log(1.0 - f30 ** (1.0 / P_SHAPE)) / 30.0


def _weighted_median(v: NDArray, w: NDArray) -> float:
    o = np.argsort(v)
    cw = np.cumsum(w[o])
    return float(v[o][np.searchsorted(cw, 0.5 * cw[-1])])


@lru_cache(maxsize=1)
def growth_by_key() -> dict[str, dict]:
    """Per key 'type_zone' present as a typical type: area-weighted median k,
    median carbon gain M_ref [Mg C/ha], area-weighted mean |latitude|, area."""
    typ, zone, a = typical_type(), zone_name(), reforestable_area_m2()
    m, k = carbon_gain_mgc_ha(), k_per_cell()
    lat = np.abs(grid_lats())[:, None] * np.ones((1, a.shape[1]))
    out = {}
    zones_k = {}
    for z in set(ZONES.values()):
        sel = (zone == z) & (a > 0) & np.isfinite(k)
        if sel.any():
            zones_k[z] = _weighted_median(k[sel], a[sel])
    for t in TYPES:
        for z in sorted(set(ZONES.values())):
            cells = (typ == t) & (zone == z) & (a > 0)
            admissible = admissible_types()[t] & (zone == z)
            if not admissible.any():
                continue
            ref_cells = cells if cells.any() else admissible
            fin = ref_cells & np.isfinite(k)
            out[f"{t}_{z}"] = {
                "type": t,
                "zone": z,
                "k": _weighted_median(k[fin], a[fin]) if fin.any() else zones_k[z],
                "m_ref_mgc_ha": _weighted_median(m[ref_cells], a[ref_cells]),
                "lat_ref": float(np.average(lat[ref_cells], weights=a[ref_cells])),
                "area_typical_m2": float(a[cells].sum()),
            }
    return out


@lru_cache(maxsize=None)
def key_grid(all_cells: bool = False) -> NDArray:
    """(360, 720) object: 'type_zone' key of the typical forest per
    reforestable cell (or per cell with a forest type nearby, *all_cells*)."""
    typ, zone = typical_type(all_cells), zone_name(all_cells)
    out = np.full(typ.shape, None, dtype=object)
    ok = (typ != None) & (zone != None)  # noqa: E711
    out[ok] = [f"{t}_{z}" for t, z in zip(typ[ok], zone[ok])]
    return out
