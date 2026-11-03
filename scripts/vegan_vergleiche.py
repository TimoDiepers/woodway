"""Ecoinvent-based factors for the "one vegan year" comparison (backup slide).

Runs in the Brightway environment of the DAC precompute (see scripts/dac_lca_precompute.py):

    ~/Documents/Coding/h2-transport-lco/.venv/bin/python scripts/vegan_vergleiche.py

Project ``ei312_REMIND_EU``, premise REMIND-EU SSP2-NDC vintages 2020 and 2050.
Writes ``data/vegan/vergleiche_lca.json`` (kg CO2e per unit; not the final counts, see the slide).
"""

from __future__ import annotations

import json
from pathlib import Path

import bw2calc as bc
import bw2data as bd

PROJECT = "ei312_REMIND_EU"
METHOD = ("ecoinvent-3.12", "IPCC 2021", "climate change: total (excl. biogenic CO2)", "global warming potential (GWP100)")
OUT = Path(__file__).resolve().parents[1] / "data" / "vegan" / "vergleiche_lca.json"


def find(db, name, loc):
    hits = [a for a in db if a["name"] == name and a["location"] == loc]
    if not hits:
        raise SystemExit(f"{db.name}: not found: {name} [{loc}]")
    return hits[0]


HORIZON = 25   # 2026 -> peak 2050: the slide compares equal cooling at the peak, so the metric has to look 25 years ahead
M20 = METHOD[:3] + ("global warming potential (GWP20)",)
CH4_FLOWS = {"Methane, fossil": True, "Methane, non-fossil": False, "Methane, from soil or biomass stock": False}
N2O_FLOW = "Dinitrogen monoxide"
CH4_TO_CO2 = 2.75   # fossil CH4 oxidises to CO2 (AR6: fossil 29.8 vs non-fossil 27.0 at 100 years)


def _agwp(characterize, horizon):
    """Absorbed radiative forcing per kg over `horizon` years (AR6 impulse responses of dynamic_characterization)."""
    import numpy as np
    import pandas as pd
    row = pd.Series({"date": pd.Timestamp("2026-01-01"), "amount": 1.0, "flow": 0, "activity": 0})
    return float(np.sum(characterize(row, period=horizon).amount))


def gwp_factors(horizon: int) -> dict:
    """GWP_H of CH4 (non-fossil, fossil) and N2O against CO2 for the same horizon."""
    from dynamic_characterization.ipcc_ar6 import characterize_ch4, characterize_co2, characterize_n2o
    co2 = _agwp(characterize_co2, horizon)
    ch4 = _agwp(characterize_ch4, horizon) / co2
    return {"ch4_nf": ch4, "ch4_f": ch4 + CH4_TO_CO2, "n2o": _agwp(characterize_n2o, horizon) / co2}


def gwp(act, amount=1.0, horizon: int | None = None, method=METHOD):
    """kg CO2e per unit. With `horizon`, CH4 and N2O are re-characterised for that horizon, everything else keeps its
    IPCC 2021 GWP100 factor (CO2 is 1 at any horizon, other gases are a few per mille of these activities)."""
    lca = bc.LCA({act: amount}, method)
    lca.lci()
    lca.lcia()
    if horizon is None:
        return lca.score
    f = gwp_factors(horizon)
    amounts = lca.inventory.sum(axis=1).A1
    score = lca.characterized_inventory.sum(axis=1).A1.copy()
    for flow_id, row in lca.dicts.biosphere.items():
        name = bd.get_node(id=flow_id)["name"]
        if name in CH4_FLOWS:
            score[row] = amounts[row] * (f["ch4_f"] if CH4_FLOWS[name] else f["ch4_nf"])
        elif name == N2O_FLOW:
            score[row] = amounts[row] * f["n2o"]
    return float(score.sum())


BUDGET_KG = 4000.0   # one vegan year per person, peak 2050 (docs/methods/vegan-modell.md)


def zahlen(v20: dict, v50: dict) -> dict:
    """What 4.0 t CO2e buys. ecoinvent factors from the 2020 vintage (today's world), assumptions in the keys."""
    strom = v20["strom_kg_kwh"]
    n = {}
    n["zug_erdumfang"] = BUDGET_KG / v20["zug_kg_pkm"] / 40075.0           # Erdumfang 40 075 km
    dusche_kg = 60 * 4.186 * 28 / 1000 * v20["gas_kg_mj"] + 60 * v20["leitungswasser_kg_kg"]   # 60 L, 10 -> 38 degC, gas boiler (wastewater credit left out)
    n["duschen"] = BUDGET_KG / dusche_kg
    n["duschen_jahre"] = n["duschen"] / 365
    n["netflix_jahre_2050"] = BUDGET_KG / (0.077 * v50["strom_kg_kwh"]) / 8760
    n["netflix_stunden"] = BUDGET_KG / (0.077 * strom)                      # 0.077 kWh/h with devices and network (IEA 2020)
    n["netflix_jahre"] = n["netflix_stunden"] / 8760
    n["waesche"] = BUDGET_KG / (1.0 * strom + 50 * v20["leitungswasser_kg_kg"])   # 60 degC, 1 kWh, 50 L (detergent left out)
    n["klima_sommer"] = BUDGET_KG / (1.0 * 8 * 120 * strom)                 # 1 kW, 8 h a day, 120 days
    n["chatgpt_anfragen"] = BUDGET_KG / (0.0003 * strom)                    # 0.3 Wh per answer (Epoch AI 2025), without training
    n["haushaltsstrom_jahre"] = BUDGET_KG / (3500 * strom)                  # household 3 500 kWh
    n["waermepumpe_jahre"] = BUDGET_KG / (18000 / 3.2 * strom)              # house 18 000 kWh heat, seasonal COP 3.2
    n["bitcoin"] = BUDGET_KG / (1.04e6 * 0.4)                               # ~1.04 GWh per coin mined (Cambridge CBECI, 164 000 coins a year), 0.4 kg/kWh
    return n


def main() -> None:
    bd.projects.set_current(PROJECT)
    out = {}
    for year in (2020, 2050):
        db = bd.Database(f"ei312_REMIND-EU_SSP2_NDC_{year}")
        strom = find(db, "market for electricity, medium voltage", "DE")
        res = {"strom_kg_kwh": gwp(strom, horizon=HORIZON), "strom_kg_kwh_gwp100": gwp(strom)}
        # train: fleet average, Germany if the vintage has it, else the world market
        try:
            zug = find(db, "transport, passenger, train, fleet average", "DE")
        except SystemExit:
            zug = find(db, "market for transport, passenger, train, fleet average", "GLO")
        res["zug_kg_pkm"] = gwp(zug, horizon=HORIZON)
        res["zug_dataset"] = f"{zug['name']} [{zug['location']}]"
        flug = find(db, "market for transport, passenger, aircraft, long haul", "GLO")
        res["flug_kg_pkm"] = gwp(flug, horizon=HORIZON)
        gas = find(db, "market group for heat, central or small-scale, natural gas", "RER")
        res["gas_kg_mj"] = gwp(gas, horizon=HORIZON)
        wasser = find(db, "market group for tap water", "RER")
        res["leitungswasser_kg_kg"] = gwp(wasser, horizon=HORIZON)
        abwasser = find(db, "market for wastewater, average", "Europe without Switzerland")
        res["abwasser_kg_m3"] = gwp(abwasser, horizon=HORIZON)
        out[str(year)] = res
        print(year, json.dumps(res, indent=1))
    out["zahlen"] = zahlen(out["2020"], out["2050"])
    print(json.dumps(out["zahlen"], indent=1, ensure_ascii=False))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
