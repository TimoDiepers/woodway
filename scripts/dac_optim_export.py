"""Run the DAC optimisation (main case + sensitivities), cross-check with full FaIR, write data/dac/optim.json.

Run: .venv/bin/python scripts/dac_optim_export.py
"""

import json

import numpy as np

from nbs.dac_optim import ROOT, capacity_by_target, solve
from nbs.dac_storage import region_by_country
from nbs.fair_module import run_fair_baseline, run_fair_perturbed

OUT = ROOT / "data" / "dac" / "optim.json"


def short(r):
    return {"ziel_jahr": r["ziel_jahr"], "status": r["status"], "kuehlung_k": r["kuehlung_k"],
            "kapazitaet_gt": r["kapazitaet_gt"], "summe_gt": float(np.sum(r["x"]))}


main = solve()
reg = region_by_country()
main["region"] = [reg[c] for c in main["laender"]]
net = (np.array(main["x"]) * np.array(main["eta"])).sum(axis=0)        # Gt/a net removal, 2026..2100
n = len(run_fair_baseline())                                           # 74: FaIR study axis 2026..2099
fair = run_fair_perturbed(-net[:n], np.zeros(n)) - run_fair_baseline()
main["fair_kuehlung_k"] = (-fair).tolist()
lp_last = main["kuehlung_k"][n - 1]
dev = float((-fair[-1] - lp_last) / lp_last) if lp_last else float("nan")
out = {"haupt": main, "fair_abweichung_2100_rel": dev,
       "sens": {"wachstum_11": short(solve(growth=1.11)), "technisch": short(solve(stufe="technisch")),
                "median": short(solve(quantil=0.5))},
       "ziel_kurve": capacity_by_target()}
OUT.write_text(json.dumps(out, ensure_ascii=False))
print("ok", main["status"], main["ziel_jahr"], f"{main['kapazitaet_gt']:.1f} Gt/a", f"{np.sum(main['x']):.0f} Gt brutto",
      f"FaIR-Abweichung {dev:+.1%}", {k: (v["status"], round(v["kapazitaet_gt"], 1)) for k, v in out["sens"].items()},
      [(c["ziel_jahr"], round(c["kapazitaet_gt"], 1)) for c in out["ziel_kurve"]])
