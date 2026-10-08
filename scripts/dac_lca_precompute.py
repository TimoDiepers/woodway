"""Pre-compute the life-cycle GWP inputs of the DAC model from premise databases.

Runs in a Brightway environment (bw2data >= 4.7, bw2calc, bw_temporalis -- the
project's pickled exchanges need it), not in this repository's own venv:

    ~/Documents/Coding/h2-transport-lco/.venv/bin/python scripts/dac_lca_precompute.py
    ... scripts/dac_lca_precompute.py --pathway SSP2-PkBudg650   # sensitivity, see build_premise_scenarios.py

The main case (SSP2-NDC) writes ``lca_vintages.json``; another pathway writes
``lca_vintages_<pathway>.json`` and takes the 2020 vintage from SSP2-NDC (the
REMIND pathways do not differ yet).

Project ``ei312_REMIND_EU``: ecoinvent 3.12 cut-off, transformed by premise
with REMIND-EU, SSP2-NDC, vintages 2020/2030/2040/2050/2075/2100.

Per vintage it writes (``data/dac/lca_vintages.json``):

* ``strom_kg_pro_kwh[ISO2]``: GWP100 of 1 kWh from the country's
  "market for electricity, medium voltage" (premise links it to the REMIND
  region's market group, so countries of one REMIND region share a mix);
  countries without such a market -> the market group of their REMIND-EU
  region (``data/dac/remind-eu-topology.json``, copied from premise,
  commit 82b7475), and only if a country is in no region -> "World".
* ``rest_kg_pro_kg``: GWP100 of everything in the premise dataset "carbon
  dioxide, captured and stored, with a sorbent-based direct air capture
  system, 100ktCO2" *except* its energy inputs and the CO2 taken from the air:
  sorbent, plant construction and end of life, compression, transport and
  storage. Construction-type inputs come from the global/regional markets the
  dataset already uses.
* ``waerme_dampf_kg_pro_mj``: GWP100 of 1 MJ "market for heat, district or
  industrial" as in the industrial-steam variant (sensitivity only).
* the dataset's own energy amounts, for documentation.

Method: IPCC 2021, climate change: total (excl. biogenic CO2), GWP100.
"""

from __future__ import annotations

import json
from pathlib import Path

import bw2calc as bc
import bw2data as bd

PROJECT = "ei312_REMIND_EU"
VINTAGES = (2020, 2030, 2040, 2050, 2075, 2100)
DB = "ei312_REMIND-EU_SSP2_NDC_{year}"
METHOD = ("ecoinvent-3.12", "IPCC 2021", "climate change: total (excl. biogenic CO2)", "global warming potential (GWP100)")
DAC_STORED = ("carbon dioxide, captured and stored, with a sorbent-based direct air capture system, 100ktCO2, "
              "with heat pump heat, and grid electricity")
DAC_STEAM = ("carbon dioxide, captured, with a sorbent-based direct air capture system, 100ktCO2, "
             "with industrial steam heat, and grid electricity")
OUT = Path(__file__).resolve().parent.parent / "data" / "dac"


TOPOLOGY = json.loads((Path(__file__).resolve().parent.parent / "data" / "dac" / "remind-eu-topology.json").read_text())
REGION_OF = {c: r for r, cs in TOPOLOGY.items() if r != "World" for c in cs}


def _electricity_node(db: str, iso2: str):
    for name in ("market for electricity, medium voltage", "market group for electricity, medium voltage"):
        try:
            return bd.get_node(database=db, name=name, location=iso2), False
        except Exception:  # noqa: BLE001 -- not found or ambiguous: try the next
            continue
    region = REGION_OF.get(iso2, "World")
    return bd.get_node(database=db, name="market group for electricity, medium voltage", location=region), True


def _resolve(node):
    """premise 2.4.9 regionalises DAC: the RER dataset only links to one regional dataset (DEU, whose
    electricity the RER dataset of older versions used as well). Follow that single link."""
    ins = list(node.technosphere())
    if len(ins) == 1 and ins[0].input["name"].startswith("carbon dioxide, captured"):
        return ins[0].input
    return node


def _region(node) -> str:
    """REMIND region a country market is linked to (premise: one input)."""
    ins = list(node.technosphere())
    if len(ins) == 1 and ins[0].input["name"].startswith("market group for electricity"):
        return ins[0].input["location"]
    return node["location"]


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--pathway", default="SSP2-NDC")
    pathway = ap.parse_args().pathway
    tag = pathway.replace("-", "_")
    bd.projects.set_current(PROJECT)
    countries = json.loads((OUT / "countries.json").read_text())
    result = {"methode": list(METHOD), "projekt": PROJECT, "pfad": pathway, "jahre": {}}
    for year in VINTAGES:
        db = DB.format(year=year) if (year == 2020 or tag == "SSP2_NDC") else f"ei312_REMIND-EU_{tag}_{year}"
        dac = _resolve(bd.get_node(database=db, name=DAC_STORED, location="RER"))
        steam = _resolve(bd.get_node(database=db, name=DAC_STEAM, location="RER"))
        heat = next(e.input for e in steam.technosphere() if e.input["name"].startswith("market for heat"))

        energy = {}
        rest_demand = {}
        for exc in dac.technosphere():
            name = exc.input["name"]
            if "electricity" in name:
                energy["strom_kwh_pro_kg"] = exc["amount"]
                continue
            rest_demand[exc.input.id] = rest_demand.get(exc.input.id, 0.0) + exc["amount"]
        energy["waerme_dampf_mj_pro_kg"] = next(e["amount"] for e in steam.technosphere() if e.input.id == heat.id)
        energy["strom_dampfvariante_kwh_pro_kg"] = next(
            e["amount"] for e in steam.technosphere() if "electricity" in e.input["name"])

        # Iterative solver with a Jacobi preconditioner (bw2calc): on ARM without
        # UMFPACK/PARDISO every direct solve refactorizes; GMRES with a warm
        # start from the previous solution is much faster for ~190 demands.
        lca = bc.JacobiGMRESLCA({heat.id: 1.0}, METHOD, rtol=1e-10)
        lca.lci()
        lca.lcia()
        heat_score = float(lca.score)

        def score(demand: dict) -> float:
            lca.lci(demand=demand)
            lca.lcia()
            return float(lca.score)

        rest = score(rest_demand)
        el, regions, fallback = {}, {}, []
        for iso2 in countries + ["World"]:
            node, fb = _electricity_node(db, iso2)
            el[iso2] = score({node.id: 1.0})
            regions[iso2] = _region(node)
            if fb:
                fallback.append(iso2)
        result["jahre"][str(year)] = {
            "datenbank": db,
            "strom_kg_pro_kwh": el,
            "remind_region": regions,
            "ohne_eigenen_markt": fallback,
            "rest_kg_pro_kg": rest,
            "waerme_dampf_kg_pro_mj": heat_score,
            "energie_premise": energy,
        }
        print(year, f"rest {rest:.3f} kg/kg, DE {el.get('DE', float('nan')):.3f}, NO {el.get('NO', float('nan')):.3f} "
              f"kg/kWh, fallback {len(fallback)}", flush=True)
    out = "lca_vintages.json" if tag == "SSP2_NDC" else f"lca_vintages_{pathway}.json"
    (OUT / out).write_text(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
