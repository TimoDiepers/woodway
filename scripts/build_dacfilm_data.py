"""Data for the DAC result film and its still pictures (deck/chart_data/dacfilm.json).

One DAC path against the warming that remains after the trees (managed forest, timber bound; nbs.tree_paths):
DACCS as a cost optimisation that offsets the warming above 1.5 deg C from 2027 on, without a growth limit
(nbs.dac_optim.solve_cost_offset; the deck's dac.offset).
Each country's capacity is spread evenly over the cells the optimisation counts for it (cells near a sediment basin, at or above the
90 % quantile of the net share; here fixed by the year 2050), plus dark map backgrounds (land, basins).

    uv run python scripts/build_dacfilm_data.py
"""
import base64
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

from nbs.dac import dac_possible, efficiency_grid
from nbs.dac_climate import climate_grid
from nbs.dac_optim import growth_limit, solve_cost_offset
from nbs.tree_paths import delta_t
from nbs.vergleich_figures import overshoot_series, vl_series
from nbs.dac_storage import iso3_grid, storage_mask
from nbs.grid import grid_lats, grid_lons

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "deck/chart_data/dacfilm.json"
LAT_N, LAT_S = 84.0, -58.0
LAND, BASIN = (40, 47, 50), (120, 98, 58)


def _png(mask_rgba: np.ndarray) -> str:
    im = Image.fromarray(mask_rgba, "RGBA").resize((mask_rgba.shape[1] * 4, mask_rgba.shape[0] * 4), Image.NEAREST)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def main() -> None:
    need = np.array(overshoot_series()["noetig_k"]) * 1000
    tree = -delta_t("forst") * 1000
    paths, cool = {}, {}
    r = solve_cost_offset(np.array(vl_series()["median_c"]) - 1.5 - tree / 1000)   # cheapest offset, no growth limit
    r["x"] = r["u"]                                                   # the map shows what is removed
    paths["opt"] = (r["laender"], np.array(r["x"]), np.array(r["eta"]))
    cool["opt"] = np.array(r["kuehlung_k"])

    lat, lon = grid_lats(), grid_lons()
    rows = (lat <= LAT_N) & (lat >= LAT_S)
    iso = iso3_grid()
    ok = dac_possible() & storage_mask()
    eta50 = efficiency_grid(2050)
    used = sorted({c for L, x, _ in paths.values() for i, c in enumerate(L) if x[i].max() > 1e-4})
    cells, owner = [], []
    for k, c in enumerate(used):
        m = ok & (iso == c) & np.isfinite(eta50)
        v = eta50[m]
        sel = m & (eta50 >= np.quantile(v, 0.9))
        for i, j in zip(*np.nonzero(sel)):
            cells.append([round(float(lon[j]), 2), round(float(lat[i]), 2)])
            owner.append(k)
    owner = np.array(owner)
    n_per = np.bincount(owner, minlength=len(used))

    out_paths = {}
    for key, (L, x, eta) in paths.items():
        cap = np.zeros((len(used), x.shape[1]))
        for i, c in enumerate(L):
            if c in used:
                cap[used.index(c)] = x[i]
        net = (x * eta).sum(axis=0)
        out_paths[key] = {"cc": [[round(float(v), 4) for v in row] for row in cap],
                          "tot": [round(float(v), 4) for v in np.array(r["kap_land"]).sum(axis=0)],
                          "cum": [round(float(v), 2) for v in np.cumsum(net)],
                          "peak": round(float(np.array(r["kap_land"]).sum(axis=0).max()), 1),
                          "dac": [round(float(v if key == "max" else max(v, 0)), 1) for v in need - tree - 1000 * cool[key]]}
        over = np.array(out_paths[key]["dac"])
        out_paths[key]["below"] = next((int(2026 + i) for i in range(30, len(over)) if over[i:].max() <= 0.5), None)

    land = np.isfinite(climate_grid()["t_mean_c"])[rows]
    img = np.zeros(land.shape + (4,), np.uint8)
    img[land] = (*LAND, 255)
    land_png = _png(img)
    near = storage_mask()[rows]
    img = np.zeros(land.shape + (4,), np.uint8)
    img[near] = (*BASIN, 46)
    basin_png = _png(img)

    out = {"years": [int(y) for y in range(2026, 2101)], "lim": [round(float(v), 4) for v in growth_limit()],
           "vl": [round(float(v), 1) for v in need], "tree": [round(float(v), 1) for v in need - tree], "latN": LAT_N, "latS": LAT_S,
           "countries": used, "n": n_per.tolist(), "cells": cells, "owner": owner.tolist(),
           "paths": out_paths, "land": land_png, "basins": basin_png}
    OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print("wrote", OUT, f"{OUT.stat().st_size / 1e3:.0f} kB,", len(cells), "cells,", len(used), "countries,",
          {k: v["peak"] for k, v in out_paths.items()})


if __name__ == "__main__":
    main()
