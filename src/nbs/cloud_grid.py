"""Low-cloud brightening over forest, from Duveiller et al. (2021).

Forests make more boundary-layer cumulus than the grass or cropland they
replace (Duveiller, G. et al. 2021, Nat. Commun. 12, 4337): monthly absolute
change of cloud fraction Delta_f for a full transition herbaceous -> forest.
Converted to a brightening after Cerasoli et al. (2021, PNAS 118,
e2026241118): a cloud raises reflectance by R_CLOUD, and the cumulus stands
for the afternoon share D_AFTERNOON of the daylight:

    Delta_alpha_W = Delta_f * R_CLOUD * D_AFTERNOON

multiplied with the surface insolation month by month like the albedo
product. Sign: positive = brighter = cooling, the opposite of
alpha_q_product's darker-is-negative convention, so the two simply add
(nbs.light.light_product).

Gaps (data only where forest and open land lie side by side) are filled per
month from the median of the same type's cells in the 10-degree latitude
band; a band with no cell at all gets 0 -- no cloud signal known there.
Only local, low, shortwave effects: advection blurs the signal (likely an
underestimate), longwave is neglected.
"""

from __future__ import annotations

import warnings
from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from nbs.albedo_grid import ZONAL_BIN_WIDTH_DEG, _interpolate_missing_months, _regrid, monthly_insolation_native
from nbs.constants import D_AFTERNOON, R_CLOUD
from nbs.species import get_species

DATA = Path(__file__).resolve().parents[2] / "data" / "clouds" / "duveiller2021_dcfc_1deg.npz"
_TYPES: dict[str, tuple[str, ...]] = {
    "evergreen_needleleaf": ("EFO",),
    "evergreen_broadleaf": ("EFO",),
    "deciduous_needleleaf": ("DFO",),
    "deciduous_broadleaf": ("DFO",),
    "mixed": ("EFO", "DFO"),
}
_TIER_LOCAL, _TIER_ZONAL, _TIER_NONE = 0, 1, 2
TIER_NAMES: dict[int, str] = {_TIER_LOCAL: "lokal", _TIER_ZONAL: "zonal", _TIER_NONE: "keine"}


@lru_cache(maxsize=1)
def _data() -> dict[str, NDArray]:
    d = np.load(DATA)
    return {k: d[k].astype(float) for k in ("lat", "lon", "EFO", "DFO")}


def delta_cloud_native(species_key: str) -> NDArray:
    """(12, 180, 360) Delta_f for the species' forest type, NaN without retrieval.
    Mixed forest: mean of evergreen and deciduous where both exist, else either."""
    d = _data()
    stack = np.stack([d[t] for t in _TYPES[get_species(species_key).igbp_class]])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmean(stack, axis=0)


@lru_cache(maxsize=None)
def _monthly_native_tiered(species_key: str) -> tuple[NDArray, NDArray]:
    """((12, 180, 360) product, fully finite; (180, 360) tier code)."""
    raw = delta_cloud_native(species_key) * R_CLOUD * D_AFTERNOON * monthly_insolation_native(species_key)
    raw = _interpolate_missing_months(raw)
    local = np.isfinite(raw).all(axis=0)
    out = raw.copy()
    tier = np.where(local, _TIER_LOCAL, _TIER_NONE).astype(np.int8)
    lat = _data()["lat"]
    edges = np.arange(-90.0, 90.0 + ZONAL_BIN_WIDTH_DEG, ZONAL_BIN_WIDTH_DEG)
    band = np.clip(np.digitize(lat, edges) - 1, 0, len(edges) - 2)
    for bi in np.unique(band):
        rows = np.where(band == bi)[0]
        loc = local[rows, :]
        if not loc.any():
            continue
        for m in range(12):
            block = out[m, rows, :]
            block[~loc] = float(np.median(raw[m, rows, :][loc]))
            out[m, rows, :] = block
        t = tier[rows, :]
        t[~loc] = _TIER_ZONAL
        tier[rows, :] = t
    return np.nan_to_num(out, nan=0.0), tier


@lru_cache(maxsize=None)
def _grid_cached(species_key: str) -> tuple[NDArray, NDArray]:
    native, tier = _monthly_native_tiered(species_key)
    return np.stack([_regrid(native[m]) for m in range(12)]), _regrid(tier).astype(np.int8)


def monthly_cloud_product(species_key: str) -> NDArray:
    """(12, 360, 720) W/m^2: Delta_alpha_W * q_in per month, positive = brighter."""
    return _grid_cached(species_key)[0].copy()


def cloud_q_product(species_key: str) -> NDArray:
    """(360, 720) W/m^2: annual mean of monthly_cloud_product."""
    return _grid_cached(species_key)[0].mean(axis=0)


def cloud_provenance_grid(species_key: str) -> NDArray:
    """(360, 720) int8: 0 lokal, 1 zonal (band median), 2 keine (set to 0)."""
    return _grid_cached(species_key)[1].copy()
