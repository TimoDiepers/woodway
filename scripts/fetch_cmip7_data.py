"""CMIP7 marker scenarios for the opening slides: warming and CO2 removal.

Builds the small tables behind the two slides that replaced the Carbon Brief
screenshot (docs/slides/dissvortrag_v2.pptx, slides 2 and 3), straight from
the published sources:

* Warming: the FaIR v2.2 ensemble of the ScenarioMIP-CMIP7 description paper
  (van Vuuren et al. 2026, GMD 19, 2627; archive zenodo.org/records/20713982,
  fair-calibrate 1.5.0, 841 members). Median and 5-95 % per marker scenario,
  relative to 1850-1900. Carbon Brief ran the same emissions through
  fair-calibrate 1.4.5; the medians differ by a few hundredths of a degree.
* Observations: Indicators of Global Climate Change 2025 (Forster et al.),
  observed warming (the multi-dataset reference series), 1-year average (IIASA ixmp4 platform
  "igcc-2025").
* CO2 removal: the scenario extensions to 2500 shipped with the same archive.
  "Neuartig" = BECCS + direct air capture + enhanced weathering + ocean
  (cdr_components_future.csv); "Land" = the net AFOLU sink, i.e. negative net
  AFOLU CO2 (continuous_emissions_timeseries_1750_2500.csv). Carbon Brief's
  bars also count soil carbon and other land removals from the full IAM
  database; those are not split out in the extensions, so the totals here are
  5-20 % lower than theirs (Very Low: 590 instead of 655 Gt CO2).

Needs network access and ixmp4 (not a project dependency), so run it as

    uvx --python 3.11 --with pyam-iamc --with xarray --with netcdf4 python scripts/fetch_cmip7_data.py

Writes data/cmip7/{temperatur,beobachtung,entnahme}.csv.
"""

from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "cmip7"
OUT = REPO / "data" / "cmip7"
ARCHIVE = "https://zenodo.org/api/records/20713982/files/chrisroadmap/cmip7-scenariomip-1.1.1.zip/content"
ROOT = "chrisroadmap-cmip7-scenariomip-ab9b226"

# extension scenario names -> marker labels used on the slides
MARKERS = {
    "SSP1 - Very Low Emissions": "VL",
    "SSP2 - Low Overshoot_a": "LN",
    "SSP2 - Low Emissions": "L",
    "SSP2 - Medium-Low Emissions": "ML",
    "SSP2 - Medium Emissions": "M",
    "SSP3 - High Emissions": "H",
    "SSP5 - Medium-Low Emissions_a": "HL",
}
CDR_VARS = [
    "Emissions|CO2|BECCS",
    "Emissions|CO2|Direct Air Capture",
    "Emissions|CO2|Enhanced Weathering",
    "Emissions|CO2|Ocean",
]


def archive_dir() -> Path:
    d = RAW / "paper_plots" / ROOT
    if not d.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        print("downloading", ARCHIVE)
        with urllib.request.urlopen(ARCHIVE) as r:
            zipfile.ZipFile(io.BytesIO(r.read())).extractall(RAW / "paper_plots")
    return d


def temperature(d: Path) -> pd.DataFrame:
    import xarray as xr

    fair = xr.open_dataset(d / "data" / "fair-outputs" / "fair_run.nc")
    t = fair["temperature"]
    t = t - t.sel(timebounds=slice(1850, 1901)).mean("timebounds")   # 1850-1900, as in the paper's plotting.py
    t = t.sel(timebounds=slice(1950, 2150))
    rows = []
    for sc in t.scenario.values:
        ts = t.sel(scenario=sc)
        q = ts.quantile([0.05, 0.5, 0.95], dim="config").values
        for k, yr in enumerate(ts.timebounds.values):
            rows.append({"szenario": str(sc), "jahr": int(yr), "p05": q[0, k], "median": q[1, k], "p95": q[2, k]})
    return pd.DataFrame(rows).round(4)


def observations() -> pd.DataFrame:
    import ixmp4

    mp = ixmp4.Platform("igcc-2025")
    df = mp.iamc.tabulate(variable={"name": "Induced Warming|Observed|1-Year Average"}, scenario={"name": "Reference"},
                          run={"default_only": True})
    df = df[["year", "value"]].rename(columns={"year": "jahr", "value": "erwaermung_k"}).sort_values("jahr")
    return df[df.jahr >= 1950].round(4)


def removal(d: Path) -> pd.DataFrame:
    cdr = pd.read_csv(d / "data" / "cdr_components_future.csv")
    ce = pd.read_csv(d / "data" / "continuous_emissions_timeseries_1750_2500.csv")
    years = [f"{y}.0" for y in range(2023, 2151)]
    rows = []
    for sc, key in MARKERS.items():
        c = cdr[(cdr.scenario == sc) & cdr.variable.isin(CDR_VARS)]
        novel = -c[years].sum(axis=0).to_numpy() / 1000                       # Gt CO2/a, removal positive
        afolu = ce[(ce.scenario == sc) & (ce.variable == "Emissions|CO2|AFOLU")][years].astype(float).to_numpy()[0] / 1000
        land = np.clip(-afolu, 0, None)
        for yr, n, l in zip(range(2023, 2151), novel, land):
            rows.append({"szenario": key, "jahr": yr, "neuartig_gt": n, "land_gt": l})
    return pd.DataFrame(rows).round(4)


def main() -> None:
    d = archive_dir()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, df in (("temperatur", temperature(d)), ("beobachtung", observations()), ("entnahme", removal(d))):
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"{name}.csv: {len(df)} rows")
    e = pd.read_csv(OUT / "entnahme.csv")
    e = e[e.jahr >= 2024].groupby("szenario")[["neuartig_gt", "land_gt"]].sum().round(0)
    print("cumulative 2024-2150 [Gt CO2]:\n", e.assign(gesamt=e.sum(axis=1)))


if __name__ == "__main__":
    main()
