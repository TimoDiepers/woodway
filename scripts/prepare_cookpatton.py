"""Aggregate the Cook-Patton et al. (2020) regrowth rate to the 0.5-degree grid.

Input: Cook-Patton, S. C. et al. (2020): Mapping carbon accumulation potential
from global natural forest regrowth. Nature 585, 545-550,
doi:10.1038/s41586-020-2686-x -- aboveground carbon accumulation rate of the
first 30 years of natural regrowth [Mg C/ha/yr], 1 km, downloaded from Global
Forest Watch ("full extent", forest and savanna biomes):
data/raw/cookpatton/sequestration_rate__mean__aboveground__full_extent__Mg_C_ha_yr.tif

Adds ``cookpatton_agb_rate_mgc_ha_yr`` (360, 720) to data/forest/forest_grid_0p5.npz:
the mean over the pixels with a value in each cell (0 = no regrowth there).

    .venv/bin/python scripts/prepare_cookpatton.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "cookpatton" / "sequestration_rate__mean__aboveground__full_extent__Mg_C_ha_yr.tif"
OUT = ROOT / "data" / "forest" / "forest_grid_0p5.npz"


def main() -> None:
    rate = np.zeros((360, 720), dtype=np.float32)
    with rasterio.open(SRC) as src:
        n = int(round(0.5 / src.res[0]))  # 60 pixels per 0.5-degree cell
        for i in range(360):
            a = src.read(1, window=rasterio.windows.Window(0, i * n, src.width, n)).reshape(n, 720, n)
            valid = np.isfinite(a) & (a > 0)
            cnt = valid.sum(axis=(0, 2))
            tot = np.where(valid, a, 0.0).sum(axis=(0, 2))
            rate[i] = np.where(cnt > 0, tot / np.maximum(cnt, 1), 0.0)
    data = dict(np.load(OUT))
    data["cookpatton_agb_rate_mgc_ha_yr"] = rate
    np.savez_compressed(OUT, **data)
    v = rate[rate > 0]
    print("cells with rate", v.size, "median", float(np.median(v)), "p95", float(np.percentile(v, 95)))


if __name__ == "__main__":
    main()
