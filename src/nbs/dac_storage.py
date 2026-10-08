"""Geological CO2 storage for DAC: how much each country may store, and which cells lie near a basin.

Source: Gidden, M. J. et al. (2025), A prudent planetary limit for geologic carbon storage,
Nature 645, 124-132; data Zenodo 10.5281/zenodo.18343187 (CC-BY 4.0).

* Table S5: per country (ISO3) technical potential, prudent planetary limit and potential in
  basins with oil & gas infrastructure, onshore + offshore, Gt CO2. World prudent limit 1460 Gt.
* Figure 1a raster (0.01 deg): sedimentary basins, values 1-4 (onshore/offshore, assessed or
  not), 15 = outside. A 0.5 deg cell counts as near storage when a basin pixel lies within
  RADIUS_KM of its centre.

Not included: basalt mineralisation (Iceland = 0), injection-rate limits per basin.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from nbs.grid import N_LAT, N_LON, grid_lats, grid_lons

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "data" / "dac" / "speicher_gidden.json"
MASK = ROOT / "data" / "dac" / "speicher_maske.npz"
COUNTRIES = ROOT / "data" / "borders" / "ne_50m_admin_0_countries.geojson"
RADIUS_KM = 100.0
R_EARTH_KM = 6371.0
_LEVELS = {"technisch": 5, "prudent": 8, "oelgas": 11}  # S5 column index of each level's total


def derive_table(xlsx: Path) -> dict:
    """Read Gidden Table S5 into {iso3: {"region", "technisch", "prudent", "oelgas"}} (Gt CO2)."""
    import pandas as pd

    df = pd.read_excel(xlsx, sheet_name="S5", header=None, skiprows=3).iloc[:, :12]
    out = {}
    for _, row in df.iterrows():
        iso = row[0]
        if not (isinstance(iso, str) and len(iso) == 3 and iso.isupper()):
            continue  # skips the "Total" / "Final Total" rows and blank lines
        out[iso] = {"region": str(row[2])} | {k: float(pd.to_numeric(row[c], errors="coerce") or 0.0)
                                               for k, c in _LEVELS.items()}
    return out


def derive_mask(tif: Path, radius_km: float = RADIUS_KM) -> NDArray:
    """(360, 720) bool: a basin pixel (values 1-4) within *radius_km* of the cell centre."""
    import rasterio
    from rasterio.enums import Resampling
    from scipy.spatial import cKDTree

    with rasterio.open(tif) as d:
        h, w = d.height // 10, d.width // 10  # read at ~0.1 deg; basins are far larger than that
        v = d.read(1, out_shape=(h, w), resampling=Resampling.nearest)
        t = d.transform * d.transform.scale(d.width / w, d.height / h)
    rows, cols = np.nonzero((v >= 1) & (v <= 4))
    lon = t.c + (cols + 0.5) * t.a
    lat = t.f + (rows + 0.5) * t.e

    def xyz(la, lo):
        la, lo = np.radians(la), np.radians(lo)
        return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]

    tree = cKDTree(xyz(lat, lon))
    lo2, la2 = np.meshgrid(grid_lons(), grid_lats())
    chord = 2 * np.sin(radius_km / R_EARTH_KM / 2)
    d, _ = tree.query(xyz(la2.ravel(), lo2.ravel()), k=1, distance_upper_bound=chord)
    return np.isfinite(d).reshape(N_LAT, N_LON)


@lru_cache(maxsize=1)
def _table() -> dict:
    return json.loads(TABLE.read_text())


def storage_by_country(stufe: str = "prudent") -> dict[str, float]:
    """ISO3 -> storage [Gt CO2] at level *stufe* ("prudent", "technisch", "oelgas")."""
    return {k: v[stufe] for k, v in _table().items()}


def region_by_country() -> dict[str, str]:
    """ISO3 -> IPCC R5 region name as given by Gidden et al."""
    return {k: v["region"] for k, v in _table().items()}


@lru_cache(maxsize=1)
def storage_mask() -> NDArray:
    with np.load(MASK) as f:
        return f["mask"].astype(bool)


@lru_cache(maxsize=1)
def iso3_grid() -> NDArray:
    """country_for_land (ISO-A2, Natural Earth) translated to ISO-A3 via the same file."""
    from nbs.dac_climate import country_for_land

    feats = json.loads(COUNTRIES.read_text())["features"]
    a2a3 = {f["properties"]["ISO_A2_EH"]: f["properties"]["ISO_A3_EH"] for f in feats}
    a2 = country_for_land()
    out = np.full(a2.shape, "", dtype="<U3")
    for code in np.unique(a2[a2 != ""]):
        a3 = a2a3.get(str(code), "")
        if len(a3) == 3 and a3 != "-99":
            out[a2 == code] = a3
    return out
