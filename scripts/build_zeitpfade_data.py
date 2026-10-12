"""Data for chapters 3 and 4 told along time (deck/chart_data/zeitpfade.json).

Chapter 3: three planting paths at the Bonn Challenge rate (every reforestable cell, the cooling cells, the
cooling cells as managed forest with the timber bound; the timber released as the dashed comparison), each one
full FaIR run, and the warming of Very Low above 1.5 deg C.
Chapter 4: with the managed forest as the trees' contribution, DAC that keeps the highest warming above 1.5 deg C
as low as possible (then 1.5 deg C by 2100 with the least DAC), at growth limits of 10, 20 and 30 %/a and without
any limit; and the simple case (capacity spread by storage) against the optimised one.

    uv run python scripts/build_zeitpfade_data.py
"""
import json
from pathlib import Path

import numpy as np

from nbs.constants import YEARS
from nbs.dac_optim import solve, solve_min_peak, solve_naive
from nbs.tree_paths import delta_t, forcing
from nbs.vergleich_figures import overshoot_series

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
    areas = {p: round(forcing(p)[2], 3) for p in ("alle", "kuehlt", "forst")}
    gap = need + delta_t("forst")
    # how fast DAC may grow: the least highest warming above 1.5 deg C, then at that peak the least DAC for
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
    # chapter 4: the optimisation (1.5 deg C by 2100 with the least capacity, per country and year,
    # nbs.dac_optim.solve) at the 20 %/a growth limit, then the growth rate as the lever (30, 50 %/a, no limit)
    # and a later start
    def _case(r):
        x = np.array(r["x"]); over = 1000 * (gap - np.array(r["kuehlung_k"]))
        return {"kap": round(float(r["kapazitaet_gt"]), 2), "w": [round(float(v), 3) for v in x.sum(axis=0)],
                "temp": [round(float(v), 1) for v in np.maximum(over, 0)], "spitze": round(float(over.max()), 1),
                "laender": r["laender"], "x_2100": [round(float(v), 4) for v in x[:, -1]]}
    dac = {"opt_20": _case(solve(gap_k=gap)),
           "opt_30": _case(solve(gap_k=gap, growth=1.3)), "opt_50": _case(solve(gap_k=gap, growth=1.5)),
           "opt_frei": _case(solve(gap_k=gap, growth=1e6, limit_start=False)),
           "opt_2035": _case(solve(gap_k=gap, start_jahr=2035)), "opt_2040": _case(solve(gap_k=gap, start_jahr=2040))}
    print({k: (v["kap"], v["spitze"]) for k, v in dac.items()})
    out = {"jahre": [int(y) for y in YEARS], "noetig": _mk(need), "baeume_rest": _mk(gap), "pfade": paths,
           "flaechen_gha": areas, "tempo": cases, "ort": ort, "dac": dac}
    OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
