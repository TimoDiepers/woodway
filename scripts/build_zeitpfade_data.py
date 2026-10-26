"""Data for chapters 3 and 4 told along time (deck/chart_data/zeitpfade.json).

Chapter 3: three planting paths, each planted at once in 2026 (every reforestable cell, the cooling cells, the
cooling cells as managed forest with the timber bound; the timber released as the dashed comparison), each one
full FaIR run, and the warming of Very Low above 1.5 deg C.
Chapter 5: with the trees on the cooling cells (left to grow) as the trees' contribution, DACCS as a cost optimisation (optimistic costs of
Okosun et al. 2026) that offsets the remaining warming above 1.5 deg C from the earliest year a build-out of at most
20, 50 or 100 %/a allows (nbs.dac_optim.solve_cost_offset); the 20 %/a plan also priced with the median and
pessimistic costs, set against the EU-27
GDP and the explicit fossil-fuel subsidies. The vegan world from 2026: methane and nitrous oxide of livestock gone
and forest on the freed land (nbs.vegan) lower the warming; the same cost optimisation for the rest.

    uv run python scripts/build_zeitpfade_data.py
"""
import json
from pathlib import Path

import numpy as np

from nbs.constants import YEARS
from nbs import vegan
from nbs.dac_optim import (COST_CASES, EU27_BIP_BIO_EUR, FOSSIL_SUBV_BIO_EUR, GROWTH, START_2030_GT, VERGLEICH_QUELLEN,
                           max_buildout, price_plan, solve_cost_offset)
from nbs.tree_paths import delta_t, delta_t_parts, forcing
from nbs.vergleich_figures import overshoot_series, vl_series

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "deck/chart_data/zeitpfade.json"
# land of the Earth without Antarctica [Gha]: FAOSTAT 13.0, forest FAO FRA 2020 4.06; farmland 4.1 after Poore &
# Nemecek 2018, 83 % of it for animals (pasture and feed), vegan about 1.0 in all; reforestable after Walker et al. 2022
# (as slide 25); freed and forest-capable in a vegan world from nbs.vegan.flaeche_info (Walker's rule)
LAND_GHA = {"gesamt": 13.0, "wald": 4.06, "tiere": 3.4, "acker": 0.7, "acker_vegan": 1.0, "wiederbewaldbar": 0.83}


def _mk(a) -> list[float]:
    return [round(1000 * float(v), 2) for v in a]


def _rest(gap, r) -> list[float]:
    return [round(float(v), 1) for v in 1000 * np.maximum(0.0, gap - np.array(r["kuehlung_k"]))]


def main() -> None:
    need = np.array(overshoot_series()["noetig_k"])
    paths = {p: _mk(-delta_t(p)) for p in ("alle", "kuehlt", "forst")}
    paths["forst_frei"] = _mk(-delta_t("forst", release=True))
    # the same paths by cause (cooling > 0): CO2 uptake of the standing trees, CO2 released at felling, albedo
    teile = {p: {k: _mk(-v) for k, v in delta_t_parts(p).items()} for p in ("alle", "kuehlt", "forst")}
    teile["forst_frei"] = {k: _mk(-v) for k, v in delta_t_parts("forst", release=True).items()}
    areas = {p: round(forcing(p)[2], 3) for p in ("alle", "kuehlt", "forst")}
    gap = need + delta_t("kuehlt")
    gap_c = np.array(vl_series()["median_c"]) - 1.5 + delta_t("kuehlt")   # unclipped: below 1.5 deg C counts too

    def _case(r, g):
        x = np.array(r["u"]); over = 1000 * (g - np.array(r["kuehlung_k"]))
        return {"kap": round(float(r["kapazitaet_gt"]), 2), "ab": r["ab_jahr"], "bis": r["bis_jahr"],
                "brutto": round(float(r["brutto_gt"]), 1), "u": [round(float(v), 3) for v in x.sum(axis=0)],
                "w": [round(float(v), 3) for v in np.array(r["kap_land"]).sum(axis=0)],
                "bau": [round(float(v), 3) for v in np.array(r["bau"]).sum(axis=0)],
                "temp": [round(float(v), 1) for v in np.maximum(over, 0)], "spitze": round(float(over.max()), 1),
                "laender": r["laender"], "anteil": [round(float(v), 4) for v in x.sum(axis=1) / max(x.sum(), 1e-12)]}
    # chapter 5: DACCS as a cost optimisation (optimistic costs of Okosun et al. 2026): the cheapest builds and runs
    # per country and year that offset the warming the trees leave (nbs.dac_optim.solve_cost_offset). The plan of the
    # 20 %/a case priced with the median and pessimistic costs, against the EU-27 economy and fossil subsidies.
    def _rk(d):
        return {k: (round(v, 4) if isinstance(v, float) else [round(x, 4) for x in v]) for k, v in d.items()}
    # the build-out ramps to the 8.8 Mt/a planned for 2030 and then grows at most 20 %/a (like wind power once), or
    # 50 or 100 %/a; the offset holds from the earliest year each pace allows (still very optimistic)
    runs = {g: solve_cost_offset(gap_c, growth=1 + g / 100) for g in (20, 50, 100)}
    dac = {f"g{g}": _case(r, gap_c) for g, r in runs.items()}
    for g in (20, 50, 100):
        dac[f"g{g}"]["kosten"] = {k: _rk(price_plan(np.array(dac[f"g{g}"]["bau"]), np.array(dac[f"g{g}"]["u"]), c)) for k, c in COST_CASES.items()}
    w, u, bau = np.array(dac["g20"]["w"]), np.array(dac["g20"]["u"]), np.array(dac["g20"]["bau"])
    # the main slide: DACCS at the fastest build-out (linear to 8.8 Mt/a in 2030, then +20 %/a), no optimisation, shown
    # up to the peak; its cost up to 2050 with the optimistic, median and pessimistic costs
    r_max = max_buildout()
    dac["max"] = {"w": [round(float(v), 4) for v in r_max["w"]], "netto": [round(float(v), 4) for v in r_max["netto"]],
                  "entnahme": [round(float(v), 4) for v in r_max["entnahme"]], "speicher_voll": r_max["speicher_voll"],
                  "brutto_bis_2050": round(r_max["brutto_bis_gt"], 2),
                  "kosten_bis_2050": {k: round(max_buildout(c=c)["kosten_bis_2050"]["summe_bio"], 3) for k, c in COST_CASES.items()}}
    kosten_pfad = {k: _rk(price_plan(bau, u, c)) for k, c in COST_CASES.items()}
    kosten_pfad.update(eu27_bip_bio=EU27_BIP_BIO_EUR, fossil_subv_bio=round(FOSSIL_SUBV_BIO_EUR, 3), quellen=VERGLEICH_QUELLEN)
    print("dac", {g: {k: v for k, v in c.items() if not isinstance(v, (list, dict))} for g, c in dac.items()}, "kosten", {k: kosten_pfad[k]["summe_bio"] for k in COST_CASES})
    # the vegan world from 2026: gases and forest on the freed land lower the warming, then the same DAC rule
    dg, df = vegan.dt_gase(), vegan.dt_flaeche()
    gap_v = gap + dg + df
    r_v = solve_cost_offset(gap_c + dg + df, growth=GROWTH)   # the same 20 %/a as the main DACCS case
    vcase = _case(r_v, gap_c + dg + df)
    uv = np.array(vcase["u"])
    vk = {k: _rk(price_plan(np.array(vcase["bau"]), uv, c)) for k, c in COST_CASES.items()}
    over = np.where(gap_v > 1e-9)[0]   # without any DAC: the vegan world's own peak and return below 1.5 deg C
    ohne_dac = {"spitze": round(float(gap_v.max()) * 1e3, 1),
                "ab": int(YEARS[over[-1] + 1]) if len(over) and over[-1] + 1 < len(YEARS) else (None if len(over) else int(YEARS[0]))}
    veg = {"dt_gase": _mk(dg), "dt_flaeche": _mk(df), **{k: round(v, 3) for k, v in vegan.flaeche_info().items()},
           "gap": _mk(np.maximum(gap_v, 0.0)), "g20": vcase, "kosten": vk, "ohne_dac": ohne_dac,
           "beitraege": {k: _mk(v) for k, v in vegan.contributions().items()},
           # the chapter-5 opener: 1 Gt CH4 not emitted against 1 Gt CO2 removed in 2026 [mK], and the land of the
           # Earth today and in a vegan world [Gha]
           "puls": {g.lower(): [round(1000 * float(v), 3) for v in vegan.dt_puls(g)] for g in ("CH4", "CO2")},
           "masse": {g.lower(): [round(float(v), 4) for v in vegan.puls_masse(g)] for g in ("CH4", "CO2")},
           "epsilon": {g.lower(): vegan.epsilon(g) for g in ("CH4", "CO2")},
           # forcing of that gas after 1 kg taken out [10^-15 W/m^2 per kg]: the mass times its strength, over time
           "antrieb": {g.lower(): [round(float(v), 4) for v in vegan.puls_antrieb(g)] for g in ("CH4", "CO2")},
           "land": LAND_GHA,
           "ersparnis": {"kap_gt": round(dac["g20"]["kap"] - vcase["kap"], 2),
                         "brutto_gt": round(float(u.sum() - uv.sum()), 1),
                         "kosten_bio": {k: round(kosten_pfad[k]["summe_bio"] - vk[k]["summe_bio"], 2) for k in COST_CASES}}}
    # chapter 5 anchor: Very Low in deg C and what each measure does to it, unclipped (mK, < 0 = cooler)
    wirkung = {"baeume": _mk(delta_t("kuehlt")), "vegan": _mk(dg + df),
               **{f"dac_{g}": _mk(-np.array(r["kuehlung_k"])) for g, r in runs.items()}, "dac_max": _mk(-np.array(r_max["kuehlung_k"])),
               "dac_vegan": _mk(-np.array(r_v["kuehlung_k"]))}
    vl_c = [round(v, 3) for v in vl_series()["median_c"]]
    print("vegan", veg["ersparnis"], ohne_dac, vegan.flaeche_info())
    out = {"jahre": [int(y) for y in YEARS], "noetig": _mk(need), "baeume_rest": _mk(gap), "pfade": paths, "pfade_teile": teile, "vl_c": vl_c, "wirkung": wirkung,
           "flaechen_gha": areas, "dac": dac, "kosten_pfad": kosten_pfad, "vegan": veg}
    OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print("wrote", OUT)



if __name__ == "__main__":
    main()
