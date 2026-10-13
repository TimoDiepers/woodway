"""World livestock emissions from FAOSTAT (Emissions Totals, domain GT) for the vegan world.

Download (not in git): https://bulks-faostat.fao.org/production/Emissions_Totals_E_All_Data_(Normalized).zip
into data/raw/faostat/. Output: data/vegan/faostat_tierhaltung.json, world, year JAHR, kt per gas.

With --vl-agrar it also fetches Very Low's farm emissions (CH4, N2O of AFOLU|Agriculture, world) from the IIASA
ScenarioMIP-CMIP7 database into data/vegan/vl_agrar.json (needs ixmp4, hence the extra package):

    uv run python scripts/prepare_vegan_data.py
    uv run --with pyam-iamc python scripts/prepare_vegan_data.py --vl-agrar
"""
import json
import sys
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "data/raw/faostat/Emissions_Totals_E_All_Data_(Normalized).zip"
OUT = ROOT / "data/vegan/faostat_tierhaltung.json"
VL_OUT = ROOT / "data/vegan/vl_agrar.json"
VL_PLATFORM = "scenariomip-cmip7"   # ScenarioMIP-CMIP7 (Release 2026), IIASA
VL_MODELL = "REMIND-MAgPIE 3.5-4.11"
VL_SZENARIO = "Very Low - SSP1 (Marker)"
JAHR = 2022
CH4_ITEMS = ("Enteric Fermentation", "Manure Management")
N2O_ITEMS = ("Manure Management", "Manure left on Pasture", "Manure applied to Soils")
N2O_ACKER = ("Synthetic Fertilizers", "Crop Residues")  # scaled by the net cropland that a vegan world frees


def main() -> None:
    with zipfile.ZipFile(ZIP) as z:
        name = next(n for n in z.namelist() if n.endswith(".csv") and "Normalized" in n)
        df = pd.read_csv(z.open(name), encoding="latin-1")
    w = df[(df["Area"] == "World") & (df["Year"] == JAHR) & (df["Source"] == "FAO TIER 1")]

    def kt(items, element):
        sel = w[w["Item"].isin(items) & (w["Element"] == element)]
        missing = set(items) - set(sel["Item"])
        if missing:
            raise KeyError(f"FAOSTAT items missing: {missing}")
        return float(sel["Value"].sum())

    out = {"jahr": JAHR, "quelle": "FAOSTAT Emissions Totals (GT), World, FAO TIER 1",
           "ch4_kt": kt(CH4_ITEMS, "Emissions (CH4)"), "n2o_tier_kt": kt(N2O_ITEMS, "Emissions (N2O)"),
           "n2o_acker_kt": kt(N2O_ACKER, "Emissions (N2O)"),
           # farm totals, the denominator when Very Low's farm path is known
           "ch4_agrar_kt": kt(CH4_ITEMS + ("Rice Cultivation",), "Emissions (CH4)"),
           "n2o_agrar_kt": kt(N2O_ITEMS + N2O_ACKER, "Emissions (N2O)")}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(out)


def vl_agrar() -> None:
    """Very Low's farm emissions by year (world): CH4 [Mt/a] and N2O [kt/a] of Emissions|*|AFOLU|Agriculture."""
    import ixmp4

    df = ixmp4.Platform(VL_PLATFORM).iamc.tabulate(
        model={"name": VL_MODELL}, scenario={"name": VL_SZENARIO}, region={"name": "World"},
        variable={"name__in": ["Emissions|CH4|AFOLU|Agriculture", "Emissions|N2O|AFOLU|Agriculture"]})
    ch4 = df[df.variable == "Emissions|CH4|AFOLU|Agriculture"].sort_values("year")
    n2o = df[df.variable == "Emissions|N2O|AFOLU|Agriculture"].sort_values("year")
    if set(ch4.unit) != {"Mt CH4/yr"} or set(n2o.unit) != {"kt N2O/yr"} or list(ch4.year) != list(n2o.year):
        raise ValueError(f"unexpected units or years: {set(ch4.unit)}, {set(n2o.unit)}")
    out = {"quelle": f"IIASA {VL_PLATFORM} (ScenarioMIP-CMIP7 Release 2026), abgerufen {date.today().isoformat()}",
           "modell": VL_MODELL, "szenario": VL_SZENARIO, "jahre": [int(y) for y in ch4.year],
           "ch4_mt": [round(float(v), 4) for v in ch4.value], "n2o_kt": [round(float(v), 3) for v in n2o.value]}
    VL_OUT.write_text(json.dumps(out, indent=1))
    print(out)


if __name__ == "__main__":
    vl_agrar() if "--vl-agrar" in sys.argv else main()
