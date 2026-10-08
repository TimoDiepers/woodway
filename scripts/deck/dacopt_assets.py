"""Images and geometry for the DAC optimisation slides (cached PNG data URIs + country centroids).

Equirectangular crop: lon -180..180, lat LAT_N..LAT_S. A point maps to
x = (lon + 180) / 360 * W, y = (LAT_N - lat) / (LAT_N - LAT_S) * H.
"""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
CACHE = HERE / "dacopt_cache.json"
LAT_N, LAT_S = 84.0, -58.0


def _rows():
    from nbs.grid import grid_lats
    lat = grid_lats()
    return (lat <= LAT_N) & (lat >= LAT_S)


def _png(rgba: np.ndarray, scale: int = 2) -> str:
    from PIL import Image
    im = Image.fromarray((rgba * 255).astype(np.uint8), "RGBA")
    im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _hex(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def build() -> dict:
    from nbs.dac import dac_possible, efficiency_grid
    from nbs.dac_climate import climate_grid
    from nbs.dac_storage import iso3_grid, storage_mask
    from nbs.grid import grid_lats, grid_lons

    r = _rows()
    land = np.isfinite(climate_grid()["t_mean_c"])[r]
    ok = dac_possible()[r]
    eta = efficiency_grid(2030)[r]
    near = storage_mask()[r]

    def canvas():
        img = np.zeros(land.shape + (4,))
        img[land] = np.r_[_hex("#d8d2c4"), 1.0]
        return img

    # eta 2030: orange (<= 0) -> sand (0.5) -> teal (1)
    img = canvas()
    stops = [(-0.2, "#c8602a"), (0.5, "#e9dcae"), (1.0, "#1f7a74")]
    xs = np.array([s[0] for s in stops])
    cols = np.array([_hex(s[1]) for s in stops])
    e = np.clip(np.nan_to_num(eta, nan=0.5), xs[0], xs[-1])
    rgb = np.stack([np.interp(e, xs, cols[:, k]) for k in range(3)], -1)
    img[ok] = np.c_[rgb[ok], np.ones(ok.sum())]
    eta_png = _png(img)

    # storage: basins near land in tan
    img = canvas()
    img[near & land] = np.r_[_hex("#b7925a"), 1.0]
    img[near & ~land] = np.r_[_hex("#b7925a"), 0.45]
    store_png = _png(img)

    # land only (result map background)
    land_png = _png(canvas())

    # centroids (area-weighted, on the cell grid)
    iso = iso3_grid()
    lo2, la2 = np.meshgrid(grid_lons(), grid_lats())
    w = np.cos(np.radians(la2))
    cent = {}
    for c in np.unique(iso[iso != ""]):
        m = iso == c
        lon = lo2[m]
        if lon.max() - lon.min() > 180:  # dateline (Russia, Fiji, USA with Aleutians): mean on the circle
            ang = np.radians(lon)
            mlon = float(np.degrees(np.arctan2((np.sin(ang) * w[m]).sum(), (np.cos(ang) * w[m]).sum())))
        else:
            mlon = float((lon * w[m]).sum() / w[m].sum())
        cent[str(c)] = [round(mlon, 2), round(float((la2[m] * w[m]).sum() / w[m].sum()), 2)]
    cent.update({"USA": [-99.0, 39.5], "RUS": [95.0, 61.0], "CAN": [-105.0, 57.0], "FRA": [2.5, 46.5],
                 "NOR": [9.0, 61.5], "AUS": [134.0, -25.0]})  # mainland centres for overseas/arctic spread
    return {"eta_png": eta_png, "store_png": store_png, "land_png": land_png, "cent": cent,
            "w": int(land.shape[1]), "h": int(land.shape[0])}


def assets() -> dict:
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    a = build()
    CACHE.write_text(json.dumps(a))
    return a


if __name__ == "__main__":
    a = assets()
    print({k: (len(v) if isinstance(v, str) else v if not isinstance(v, dict) else len(v)) for k, v in a.items()})
