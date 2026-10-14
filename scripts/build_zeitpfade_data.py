"""Data for chapters 3 and 4 told along time (deck/chart_data/zeitpfade.json).

Chapter 3: three planting paths, each planted at once in 2026 (every reforestable cell, the cooling cells, the
cooling cells as managed forest with the timber bound; the timber released as the dashed comparison), each one
full FaIR run, and the warming of Very Low above 1.5 deg C.
Chapter 4: with the managed forest as the trees' contribution, DAC that keeps the highest warming above 1.5 deg C
as low as possible, then returns to 1.5 deg C as early as possible (plants run 20 years), at growth limits of 20,
30 and 50 %/a and without any limit; the simple case (capacity spread by storage) against the optimised one.
Costs after the fact: the main path priced with Okosun et al. 2026 (three cases), set against the EU-27 GDP and
the explicit fossil-fuel subsidies. The vegan world from 2026: methane and nitrous oxide of livestock gone and
forest on the freed land (nbs.vegan) lower the gap; DAC optimised again, with what it saves.

    uv run python scripts/build_zeitpfade_data.py
"""
import json
from pathlib import Path

import numpy as np

from nbs.constants import YEARS
from nbs import vegan
from nbs.dac_optim import (COST_CASES, EU27_BIP_BIO_EUR, FOSSIL_SUBV_BIO_EUR, VERGLEICH_QUELLEN, path_cost, solve,
                           solve_cost, solve_min_peak, solve_naive)
from nbs.tree_paths import delta_t, delta_t_parts, forcing
from nbs.vergleich_figures import overshoot_series, vl_series

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "deck/chart_data/zeitpfade.json"


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
    gap = need + delta_t("forst")
    # how fast DAC may grow: the least highest warming above 1.5 deg C, then at that peak the least capacity for
    # 1.5 deg C by 2100; growth limits of 10, 20, 30 %/a and none at all
    cases = {"ohne": {"spitze": round(1000 * float(gap.max()), 1)}}
    for key, kw in (("g20", {}), ("g30", {"growth": 1.3}), ("g10", {"growth": 1.1}),
                    ("frei", {"growth": 1e6, "limit_start": False}), ("vollgas", {"danach": "schnell"})):
        r = solve_min_peak(gap, **kw)
        x = np.array(r["x"])
        over = 1000 * (gap - np.array(r["kuehlung_k"]))
        cases[key] = {"status": r["status"], "kap": round(float(x.sum(axis=0).max()), 2), "netto": round(float(r["netto_gt"])),
                      "spitze": round(1000 * r["spitze_k"], 1), "rest": _rest(gap, r), "temp": [round(float(v), 1) for v in over],
                      "ab": next((int(YEARS[i]) for i in range(20, len(YEARS)) if over[i:].max() <= 0.5), None)}
        print(key, cases[key]["status"], cases[key]["kap"], max(cases[key]["rest"]), flush=True)
    naive = solve_naive(gap)
    ort = {"optimiert": cases["g20"]["kap"], "nach_speicher": round(naive["kapazitaet_gt"], 2),
           "spitze_nach_speicher": round(1000 * float((gap - np.array(naive["kuehlung_k"])).max()), 1)}
    print("ort", ort)
    # chapter 4: the optimisation (the lowest peak, then back to 1.5 deg C as early as possible, per country and
    # year, nbs.dac_optim.solve_min_peak) at the 20 %/a growth limit, then the growth rate as the lever
    # (30, 50 %/a, no limit) and a later start (solve: with the growth limit the peak stage changes nothing)
    def _case(r, g=None):
        g = gap if g is None else g
        x = np.array(r["x"]); over = 1000 * (g - np.array(r["kuehlung_k"]))
        return {"kap": round(float(r["kapazitaet_gt"]), 2), "ab": r.get("ab_jahr"), "w": [round(float(v), 3) for v in x.sum(axis=0)],
                "temp": [round(float(v), 1) for v in np.maximum(over, 0)], "spitze": round(float(over.max()), 1),
                "laender": r["laender"], "x_2100": [round(float(v), 4) for v in x[:, -1]]}
    frueh = dict(danach="frueh")
    runs = {"opt_20": solve_min_peak(gap, **frueh), "opt_30": solve_min_peak(gap, growth=1.3, **frueh),
            "opt_50": solve_min_peak(gap, growth=1.5, **frueh), "opt_100": solve_min_peak(gap, growth=2.0, **frueh),
            "opt_frei": solve_min_peak(gap, growth=1e6, limit_start=False, **frueh)}
    dac = {k: _case(r) for k, r in runs.items()}
    dac.update(opt_2035=_case(solve(gap_k=gap, start_jahr=2035)), opt_2040=_case(solve(gap_k=gap, start_jahr=2040)))
    # what speed costs: the same lowest peak, back to 1.5 deg C from an earlier year on (and staying there), each
    # with the least capacity; and the earliest year at all
    dac["ab_jahr"] = {str(z): _case(solve_min_peak(gap, ziel_jahr=z)) for z in (2085, 2090, 2095)}
    dac["ab_jahr"]["2100"] = _case(solve_min_peak(gap))   # 1.5 deg C only by 2100; opt_20 now returns early
    dac["fruehestens"] = _case(solve_min_peak(gap, danach="frueh"))
    print({k: (v["kap"], v["spitze"], v["ab"]) for k, v in dac.items() if "kap" in v},
          {k: v["kap"] for k, v in dac["ab_jahr"].items()})
    # backup: the cost-optimal path (Okosun et al. 2026 costs): cost cases, growth limits, an earlier target year
    def _cost(r):
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}
    kosten = {"faelle": {k: _cost(solve_cost(gap, c=c)) for k, c in COST_CASES.items()},
              "tempo": {g: _cost(solve_cost(gap, growth=f, limit_start=f < 1e5)) for g, f in (("20", 1.2), ("30", 1.3), ("50", 1.5), ("frei", 1e6))},
              "zieljahr": {f"{g}_{z}": _cost(solve_cost(gap, growth=f, ziel_jahr=z)) for g, f in (("20", 1.2), ("30", 1.3), ("50", 1.5)) for z in (2090, 2080)}}
    print({k: {kk: vv.get("kosten_bio") for kk, vv in v.items()} for k, v in kosten.items()})
    # costs of the main path after the fact (not optimised for), against the EU-27 economy and fossil subsidies
    w20 = np.array(dac["opt_20"]["w"])

    def _rk(d):
        return {k: (round(v, 4) if isinstance(v, float) else [round(x, 4) for x in v]) for k, v in d.items()}
    kosten_pfad = {k: _rk(path_cost(w20, c)) for k, c in COST_CASES.items()}
    kosten_pfad.update(eu27_bip_bio=EU27_BIP_BIO_EUR, fossil_subv_bio=round(FOSSIL_SUBV_BIO_EUR, 3), quellen=VERGLEICH_QUELLEN)
    print("kosten", {k: kosten_pfad[k]["summe_bio"] for k in COST_CASES})
    # the vegan world from 2026: gases and forest on the freed land lower the gap, then DAC again
    dg, df = vegan.dt_gase(), vegan.dt_flaeche()
    gap_v = gap + dg + df
    vcase = _case(solve_min_peak(gap_v, **frueh), gap_v)
    wv = np.array(vcase["w"])
    vk = {k: _rk(path_cost(wv, c)) for k, c in COST_CASES.items()}
    over = np.where(gap_v > 1e-9)[0]   # without any DAC: the vegan world's own peak and return below 1.5 deg C
    ohne_dac = {"spitze": round(float(gap_v.max()) * 1e3, 1),
                "ab": int(YEARS[over[-1] + 1]) if len(over) and over[-1] + 1 < len(YEARS) else (None if len(over) else int(YEARS[0]))}
    veg = {"dt_gase": _mk(dg), "dt_flaeche": _mk(df), **{k: round(v, 3) for k, v in vegan.flaeche_info().items()},
           "gap": _mk(np.maximum(gap_v, 0.0)), "opt_20": vcase, "kosten": vk, "ohne_dac": ohne_dac,
           "beitraege": {k: _mk(v) for k, v in vegan.contributions().items()},
           "ersparnis": {"kap_gt": round(dac["opt_20"]["kap"] - vcase["kap"], 2),
                         "brutto_gt": round(float(w20.sum() - wv.sum()), 1),
                         "kosten_bio": {k: round(kosten_pfad[k]["summe_bio"] - vk[k]["summe_bio"], 2) for k in COST_CASES}}}
    # chapter 5 anchor: Very Low in deg C and what each measure does to it, unclipped (mK, < 0 = cooler)
    wirkung = {"baeume": _mk(delta_t("forst")), "vegan": _mk(dg + df),
               **{f"dac_{k}": _mk(-np.array(runs[f"opt_{k}"]["kuehlung_k"])) for k in ("20", "50", "100", "frei")}}
    vl_c = [round(v, 3) for v in vl_series()["median_c"]]
    print("vegan", veg["ersparnis"], ohne_dac, vegan.flaeche_info())
    out = {"jahre": [int(y) for y in YEARS], "noetig": _mk(need), "baeume_rest": _mk(gap), "pfade": paths, "pfade_teile": teile, "vl_c": vl_c, "wirkung": wirkung,
           "flaechen_gha": areas, "tempo": cases, "ort": ort, "dac": dac, "kosten": kosten,
           "kosten_pfad": kosten_pfad, "vegan": veg}
    OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
