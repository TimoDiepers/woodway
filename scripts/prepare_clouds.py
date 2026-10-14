"""Bin Duveiller et al. (2021) cloud-change data onto the 1-degree Duveiller (2018) grid.

Input: data/raw/duveiller2021_data_for_figures.zip (Zenodo 10.5281/zenodo.4727774,
CC-BY-4.0), files df_dCFC_MOD05_{EFO,DFO}.Rdata: monthly absolute change of
low cloud fractional cover (MODIS Aqua 13:30, Cloud CCI 2004-2014) for a full
transition herbaceous -> forest, 0.35-degree cells, already filtered by the
authors (uncertainty <= 0.1, cover fraction >= 0.2, 0.5/99.5 % quantiles;
code/harvest/harvest___get-S4T-results-in-df.R).

Output: data/clouds/duveiller2021_dcfc_1deg.npz -- mean of the 0.35-degree
values inside each 1-degree cell, lat north to south like alb_det.nc.

    uv run --with pyreadr python scripts/prepare_clouds.py
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pyreadr

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "duveiller2021_data_for_figures.zip"
OUT = ROOT / "data" / "clouds" / "duveiller2021_dcfc_1deg.npz"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
LAT = np.arange(89.5, -90.0, -1.0)
LON = np.arange(-179.5, 180.0, 1.0)


def _bin(df) -> np.ndarray:
    tot = np.zeros((12, 180, 360))
    cnt = np.zeros((12, 180, 360))
    m = df["month"].astype(str).map(MONTHS.index).to_numpy()
    i = np.clip(np.floor(90.0 - df["lat"].to_numpy()).astype(int), 0, 179)
    j = np.clip(np.floor(df["lon"].to_numpy() + 180.0).astype(int), 0, 359)
    np.add.at(tot, (m, i, j), df["dCFC"].to_numpy())
    np.add.at(cnt, (m, i, j), 1.0)
    with np.errstate(invalid="ignore"):
        return np.where(cnt > 0, tot / cnt, np.nan).astype(np.float32)


def main() -> None:
    out = {"lat": LAT, "lon": LON}
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(SRC) as z:
        for t in ("EFO", "DFO"):
            path = z.extract(f"data_for_figures/df_dCFC_MOD05_{t}.Rdata", tmp)
            out[t] = _bin(next(iter(pyreadr.read_r(path).values())))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT, **out)
    print(f"geschrieben: {OUT}")


if __name__ == "__main__":
    main()
