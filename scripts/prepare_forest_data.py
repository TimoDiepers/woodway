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

It also writes data/vegan/frei_0p5.npz, the land a vegan world frees (freed_land; Walker's
``Societal_Constraints_500m.tif``, ``Base_Unr_AGB_BGB_MgCha_500m.tif``), alone with --only-freed.

    uv run python scripts/prepare_forest_data.py [--only-reforestation | --only-freed]
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


def _strip_sum(names: tuple[str, ...], weigh) -> tuple[np.ndarray, list[np.ndarray]]:
    """One pass over the (equal-area) Walker grid in latitude strips: per 0.5-degree cell, the weighted pixel
    area [m^2] and the area-weighted sums of some pixel values. *weigh(read)* gets read(k), which reads the k-th
    raster of *names* for the strip, and returns (weight per pixel, list of value arrays) or None for an empty
    strip; the first raster sets the strip grid."""
    area = np.zeros(DST_SHAPE)
    sums: list[np.ndarray] = []
    srcs = [rasterio.open(RAW / "walker" / n) for n in names]
    try:
        first = srcs[0]
        res = first.res[0]
        px_m2 = res * res
        left, top = first.transform.c, first.transform.f
        strip = 400
        for r0 in range(0, first.height, strip):
            win = rasterio.windows.Window(0, r0, first.width, min(strip, first.height - r0))
            got = weigh(lambda k: srcs[k].read(1, window=win))
            if got is None:
                continue
            w, values = got
            rows, cols = np.nonzero(w > 0)
            if not len(rows):
                continue
            wk = w[rows, cols]
            y = top - (r0 + rows + 0.5) * res
            x = left + (cols + 0.5) * res
            lat = np.degrees(y / R_SPHERE)
            lon = np.degrees(x / (R_SPHERE * np.cos(np.radians(lat))))
            ok = (lon >= -180) & (lon < 180)
            i = np.clip(((90.0 - lat[ok]) / 0.5).astype(int), 0, 359)
            j = np.clip(((lon[ok] + 180.0) / 0.5).astype(int), 0, 719)
            np.add.at(area, (i, j), wk[ok] * px_m2)
            while len(sums) < len(values):
                sums.append(np.zeros(DST_SHAPE))
            for k, v in enumerate(values):
                np.add.at(sums[k], (i, j), v[rows, cols][ok].astype(float) * wk[ok] * px_m2)
    finally:
        for src in srcs:
            src.close()
    return area, sums


def _mean(sum_: np.ndarray, area: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(area > 0, sum_ / area, 0.0)


def reforestation_and_carbon() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One pass over the (equal-area) Walker grid: reforestable area per
    0.5-degree cell [m^2] -- Walker NCS categories R/L + R/H, outside areas
    critical to food production and human habitation -- and the mean
    *constrained unrealized* AGB+BGB carbon over exactly those pixels
    [Mg C/ha]: potential minus current stock, i.e. what reforestation adds."""
    def weigh(read):
        sel = np.isin(read(0), REFOREST_CATEGORIES)
        if not sel.any():
            return None
        gain = read(1)
        # Constrained: areas critical to food production and human
        # habitation are 0 in this layer -> not plantable here.
        sel &= gain > 0
        if not sel.any():
            return None
        return sel.astype(float), [gain, np.maximum(read(2), 0)]

    area, (carbon_sum, pot_sum) = _strip_sum(
        ("NCS_Opportunity_Categories_500m.tif", "Base_Con_Unr_AGB_BGB_MgCha_500m.tif",
         "Base_Pot_AGB_BGB_MgCha_500m.tif"), weigh)
    return area, _mean(carbon_sum, area), _mean(pot_sum, area)


FREED_OUT = ROOT / "data" / "vegan" / "frei_0p5.npz"
ACKER_NETTO_FREI = 0.19  # Poore & Nemecek 2018, as nbs.vegan
WEIDE, ACKER = 3, 1      # Walker's Societal_Constraints_500m: 1 cropland, 2 shifting cultivation, 3 grazing, 4 urban


# Walker gives NCS categories only outside the societal constraints, so on grazing land and cropland its
# reforestation rule (R/L + R/H) is applied directly: woody potential (AGB+BGB >= 10 Mg C/ha) and current stock at
# most a quarter of it. Checked against the categories outside the constraints: 98.4 % of pixels agree
# (recall 96 %, precision 92 %).
R_POT_MIN = 10.0
R_CUR_MAX = 0.25


def freed_land() -> tuple[np.ndarray, np.ndarray]:
    """Area [m^2] per 0.5-degree cell that a vegan world frees and that could carry forest (Walker's R/L or R/H
    rule, see R_POT_MIN): grazing land (Walker's societal constraint 3) in full, cropland (1) at 19 %; only
    pixels that the reforestation area leaves out (constrained gain 0), so the two never overlap. And the
    unconstrained unrealised AGB+BGB carbon there [Mg C/ha], area-weighted."""
    def weigh(read):
        soc = read(0)
        w = np.where(soc == WEIDE, 1.0, np.where(soc == ACKER, ACKER_NETTO_FREI, 0.0))
        if not w.any():
            return None
        pot, unr = read(2).astype(float), read(3).astype(float)
        r_rule = (pot >= R_POT_MIN) & (unr > 0) & (pot - unr <= R_CUR_MAX * pot)
        w *= r_rule & (read(1) <= 0)   # Walker's reforestation rule, left out of the reforestation area
        return w, [unr]

    area, (carbon_sum,) = _strip_sum(
        ("Societal_Constraints_500m.tif", "Base_Con_Unr_AGB_BGB_MgCha_500m.tif",
         "Base_Pot_AGB_BGB_MgCha_500m.tif", "Base_Unr_AGB_BGB_MgCha_500m.tif"), weigh)
    return area, _mean(carbon_sum, area)


def main() -> None:
    import sys

    if "--only-freed" in sys.argv:
        return save_freed()
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
    save_freed()


def save_freed() -> None:
    fa, fc = freed_land()
    FREED_OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(FREED_OUT, freed_area_m2=fa.astype(np.float32), freed_carbon_mgc_ha=fc.astype(np.float32))
    print("frei:", round(float(fa.sum()) / 1e13, 3), "Gha")


if __name__ == "__main__":
    main()
