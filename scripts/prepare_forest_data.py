"""Aggregate the forest-type input rasters to the model's 0.5-degree grid.

Inputs (data/raw, not in git):

* Hasler et al. (2024), Harvard Dataverse doi:10.7910/DVN/G17RXL,
  ``MostLikelyForests.tif``: most likely forest class per 0.005-degree pixel
  (IGBP: 1 ENF, 2 EBF, 3 DNF, 4 DBF, 5 MF, 8 woody savanna; 255 no data),
  90 N to 60 S.
* Walker et al. (2022), doi:10.7910/DVN/DSDDQK: ``Base_Pot_AGB_BGB_MgCha_500m.tif``
  (potential above- plus belowground biomass carbon, Mg C/ha) and
  ``Bioclimate_Zones_500m.tif`` (from FAO GEZ; the README says 1 polar ...
  5 boreal, but by latitude 1 is boreal and 5 polar: 2 subtropics,
  3 temperate, 4 tropics) and ``NCS_Opportunity_Categories_500m.tif``
  (2 R/L and 5 R/H = reforestation opportunity, 931 Mha), all MODIS
  sinusoidal 463 m.

Output: data/forest/forest_grid_0p5.npz with, per 0.5-degree cell,
``type_share`` (6, 360, 720) share of each forest class among the classified
pixels, ``typical`` (360, 720) the most frequent class (0 = none),
``walker_max_mgc_ha`` (360, 720) mean potential AGB+BGB carbon, and
``zone`` (360, 720) most frequent bioclimate zone (0 = none).

    .venv/bin/python scripts/prepare_forest_data.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "forest" / "forest_grid_0p5.npz"
CLASSES = (1, 2, 3, 4, 5, 8)  # ENF, EBF, DNF, DBF, MF, woody savanna
DST_TRANSFORM = from_origin(-180.0, 90.0, 0.5, 0.5)
DST_SHAPE = (360, 720)


def forest_types() -> tuple[np.ndarray, np.ndarray]:
    """Class shares per 0.5-degree cell from the 0.005-degree Hasler map
    (100 x 100 pixels per cell, read in latitude strips)."""
    shares = np.zeros((len(CLASSES),) + DST_SHAPE)
    with rasterio.open(RAW / "hasler" / "MostLikelyForests.tif") as src:
        rows_per_cell = int(round(0.5 / src.res[1]))
        n_cells = src.height // rows_per_cell  # 300 rows of cells: 90 N .. 60 S
        for i in range(n_cells):
            win = rasterio.windows.Window(0, i * rows_per_cell, src.width, rows_per_cell)
            a = src.read(1, window=win).reshape(rows_per_cell, 720, rows_per_cell)
            for k, c in enumerate(CLASSES):
                shares[k, i] = (a == c).sum(axis=(0, 2))
    tot = shares.sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        shares = np.where(tot > 0, shares / tot, 0.0)
    typical = np.where(tot > 0, np.array(CLASSES)[np.argmax(shares, axis=0)], 0)
    return shares, typical


def walker(name: str, resampling: Resampling, dtype) -> np.ndarray:
    dst = np.zeros(DST_SHAPE, dtype=dtype)
    with rasterio.open(RAW / "walker" / name) as src:
        reproject(source=rasterio.band(src, 1), destination=dst, src_transform=src.transform, src_crs=src.crs,
                  src_nodata=src.nodata, dst_transform=DST_TRANSFORM, dst_crs="EPSG:4326", dst_nodata=0,
                  resampling=resampling, warp_mem_limit=2048, num_threads=4)
    return dst


REFOREST_CATEGORIES = (2, 5)  # Walker NCS opportunity: R/L and R/H (reforestation), 931 Mha in total
R_SPHERE = 6371007.181  # MODIS sinusoidal sphere


def reforestation_and_carbon() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One pass over the (equal-area) Walker grid: reforestable area per
    0.5-degree cell [m^2] -- Walker NCS categories R/L + R/H, outside areas
    critical to food production and human habitation -- and the mean
    *constrained unrealized* AGB+BGB carbon over exactly those pixels
    [Mg C/ha]: potential minus current stock, i.e. what reforestation adds."""
    area = np.zeros(DST_SHAPE)
    carbon_sum = np.zeros(DST_SHAPE)
    pot_sum = np.zeros(DST_SHAPE)
    with rasterio.open(RAW / "walker" / "NCS_Opportunity_Categories_500m.tif") as cat_src, \
            rasterio.open(RAW / "walker" / "Base_Con_Unr_AGB_BGB_MgCha_500m.tif") as c_src, \
            rasterio.open(RAW / "walker" / "Base_Pot_AGB_BGB_MgCha_500m.tif") as p_src:
        res = cat_src.res[0]
        px_m2 = res * res
        left, top = cat_src.transform.c, cat_src.transform.f
        strip = 400
        for r0 in range(0, cat_src.height, strip):
            win = rasterio.windows.Window(0, r0, cat_src.width, min(strip, cat_src.height - r0))
            cat = cat_src.read(1, window=win)
            sel = np.isin(cat, REFOREST_CATEGORIES)
            if not sel.any():
                continue
            gain = c_src.read(1, window=win)
            # Constrained: areas critical to food production and human
            # habitation are 0 in this layer -> not plantable here.
            sel &= gain > 0
            if not sel.any():
                continue
            rows, cols = np.nonzero(sel)
            carbon = gain[rows, cols].astype(float)
            pot = np.maximum(p_src.read(1, window=win)[rows, cols].astype(float), 0.0)
            y = top - (r0 + rows + 0.5) * res
            x = left + (cols + 0.5) * res
            lat = np.degrees(y / R_SPHERE)
            lon = np.degrees(x / (R_SPHERE * np.cos(np.radians(lat))))
            ok = (lon >= -180) & (lon < 180)
            i = np.clip(((90.0 - lat[ok]) / 0.5).astype(int), 0, 359)
            j = np.clip(((lon[ok] + 180.0) / 0.5).astype(int), 0, 719)
            np.add.at(area, (i, j), px_m2)
            np.add.at(carbon_sum, (i, j), carbon[ok] * px_m2)
            np.add.at(pot_sum, (i, j), pot[ok] * px_m2)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_c = np.where(area > 0, carbon_sum / area, 0.0)
        mean_p = np.where(area > 0, pot_sum / area, 0.0)
    return area, mean_c, mean_p


def main() -> None:
    import sys

    if "--only-reforestation" in sys.argv:
        data = dict(np.load(OUT))
        data["reforest_area_m2"], data["reforest_carbon_mgc_ha"], data["reforest_potential_mgc_ha"] = (
            x.astype(np.float32) for x in reforestation_and_carbon())
        np.savez_compressed(OUT, **data)
        print("reforestation done", round(float(data["reforest_area_m2"].sum()) / 1e13, 3), "Gha")
        return
    shares, typical = forest_types()
    print("forest types done", {c: int((typical == c).sum()) for c in CLASSES})
    wmax = walker("Base_Pot_AGB_BGB_MgCha_500m.tif", Resampling.average, np.float32)
    print("walker done", float(np.nanmax(wmax)))
    zone = walker("Bioclimate_Zones_500m.tif", Resampling.mode, np.uint8)
    zone[zone == 15] = 0
    print("zones done", np.unique(zone, return_counts=True))
    refo_area, refo_carbon, refo_pot = reforestation_and_carbon()
    print("reforestation done", round(refo_area.sum() / 1e13, 3), "Gha")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT, type_share=shares.astype(np.float32), typical=typical.astype(np.uint8),
                        walker_max_mgc_ha=wmax, zone=zone, classes=np.array(CLASSES),
                        reforest_area_m2=refo_area.astype(np.float32),
                        reforest_carbon_mgc_ha=refo_carbon.astype(np.float32),
                        reforest_potential_mgc_ha=refo_pot.astype(np.float32))


if __name__ == "__main__":
    main()
