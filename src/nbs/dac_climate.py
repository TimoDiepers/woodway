"""Ambient conditions and countries on the common 0.5-degree grid, for DAC.

Climate: CRU TS 4.09 (Harris et al. 2020, Sci. Data 7, 109), monthly mean
near-surface temperature (``tmp``) and vapour pressure (``vap``), 2011-2020,
already on 0.5 degrees. Relative humidity per month from vapour pressure and
the saturation vapour pressure over water (Magnus form, WMO 2018 guide):

    e_s(T) = 6.112 hPa * exp(17.62 T / (243.12 + T)),    RH = vap / e_s(T)

averaged to a yearly value, as the DAC model works on yearly means (Sendi et
al. 2022 aggregate their climate classes the same way).

Countries: Natural Earth 1:50m admin-0 (public domain), ``ISO_A2_EH``, one
code per cell centre.

The raw CRU files (~0.5 GB each) live in ``data/raw/cru`` (not in git);
``climate_grid`` caches the three derived fields in
``data/dac/klima_cru_2011_2020.npz`` so they are needed only once.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from nbs.grid import N_LAT, N_LON, grid_lats, grid_lons

ROOT = Path(__file__).resolve().parents[2]
CRU_DIR = ROOT / "data" / "raw" / "cru"
CACHE = ROOT / "data" / "dac" / "klima_cru_2011_2020.npz"
COUNTRIES = ROOT / "data" / "borders" / "ne_50m_admin_0_countries.geojson"


def saturation_vapour_pressure_hpa(t_c: NDArray) -> NDArray:
    """Saturation vapour pressure over water [hPa] (Magnus, WMO 2018)."""
    return 6.112 * np.exp(17.62 * t_c / (243.12 + t_c))


def _read_cru(var: str) -> NDArray:
    """(120, 360, 720) monthly field, north to south like nbs.grid; NaN at sea."""
    import netCDF4

    path = CRU_DIR / f"cru_ts4.09.2011.2020.{var}.dat.nc"
    with netCDF4.Dataset(path) as ds:
        lat = np.asarray(ds["lat"][:])
        data = np.ma.filled(ds[var][:].astype(np.float64), np.nan)
    if lat[0] < lat[-1]:  # CRU runs south to north
        data = data[:, ::-1, :]
    return data


def _derive() -> dict[str, NDArray]:
    tmp = _read_cru("tmp")
    vap = _read_cru("vap")
    rh = np.clip(100.0 * vap / saturation_vapour_pressure_hpa(tmp), 0.0, 100.0)
    monthly_clim = tmp.reshape(10, 12, N_LAT, N_LON).mean(axis=0)  # mean of each calendar month
    with np.errstate(invalid="ignore"):
        return {
            "t_mean_c": np.nanmean(tmp, axis=0),
            "rh_mean_pct": np.nanmean(rh, axis=0),
            "t_coldest_month_c": np.nanmin(monthly_clim, axis=0),
        }


@lru_cache(maxsize=1)
def climate_grid() -> dict[str, NDArray]:
    """Yearly mean temperature [deg C], yearly mean relative humidity [%] and
    the coldest calendar-month mean [deg C], 2011-2020, each (360, 720)."""
    if CACHE.exists():
        with np.load(CACHE) as f:
            return {k: f[k].astype(np.float64) for k in f.files}
    fields = _derive()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **{k: v.astype(np.float32) for k, v in fields.items()})
    return fields


@lru_cache(maxsize=1)
def country_grid() -> NDArray:
    """(360, 720) array of ISO 3166-1 alpha-2 codes per cell centre ('' at sea
    or outside every polygon)."""
    import shapely
    from shapely.geometry import shape

    lon2d, lat2d = np.meshgrid(grid_lons(), grid_lats())
    points = shapely.points(lon2d.ravel(), lat2d.ravel())
    out = np.full(points.shape, "", dtype="<U2")
    features = json.loads(COUNTRIES.read_text())["features"]
    for feat in features:
        code = feat["properties"].get("ISO_A2_EH") or feat["properties"].get("ISO_A2")
        if not code or code == "-99":
            continue
        geom = shape(feat["geometry"])
        shapely.prepare(geom)
        out[shapely.contains_xy(geom, lon2d.ravel(), lat2d.ravel())] = code
    return out.reshape(N_LAT, N_LON)


@lru_cache(maxsize=1)
def country_for_land() -> NDArray:
    """``country_grid`` with every cell that has CRU climate but no country
    (coastal cells whose centre lies just offshore of the 1:50m polygon) given
    the code of the nearest coded cell within 3 cells; '' where there is none."""
    codes = country_grid().copy()
    land = np.isfinite(climate_grid()["t_mean_c"])
    missing = np.argwhere(land & (codes == ""))
    for i, j in missing:
        for r in (1, 2, 3):
            win = country_grid()[max(i - r, 0): i + r + 1, np.arange(j - r, j + r + 1) % N_LON]
            found = win[win != ""]
            if found.size:
                vals, counts = np.unique(found, return_counts=True)
                codes[i, j] = vals[np.argmax(counts)]
                break
    return codes
