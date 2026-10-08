"""Run the DAC optimisation (main case + sensitivities), cross-check with full FaIR, write data/dac/optim.json.

Run: .venv/bin/python scripts/dac_optim_export.py
"""

import json

import numpy as np

from nbs.dac_optim import PATHWAYS, ROOT, capacity_by_target, fair_cooling, growth_limit, solve
from nbs.dac_storage import region_by_country

OUT = ROOT / "data" / "dac" / "optim.json"


def short(r):
    return {"ziel_jahr": r["ziel_jahr"], "status": r["status"], "kuehlung_k": r["kuehlung_k"], "netto_gt": r["netto_gt"],
            "kapazitaet_gt": r["kapazitaet_gt"], "summe_gt": float(np.sum(r["x"]))}


main = solve(ziel="co2")
reg = region_by_country()
main["region"] = [reg[c] for c in main["laender"]]
net = (np.array(main["x"]) * np.array(main["eta"])).sum(axis=0)        # Gt/a net removal, 2026..2100
fair = fair_cooling(net)                                               # same year axis, NaN for 2099/2100
main["fair_kuehlung_k"] = [None if np.isnan(v) else float(v) for v in fair]
j = int(np.flatnonzero(np.isfinite(fair))[-1])                         # last common year: 2098
dev = float((fair[j] - main["kuehlung_k"][j]) / main["kuehlung_k"][j])
pathways = []
for pw in PATHWAYS:
    r = main if pw == "SSP2-NDC" else solve(pathway=pw, ziel="co2")
    pathways.append({"strompfad": pw, "kapazitaet_gt": r["kapazitaet_gt"], "summe_gt": float(np.sum(r["x"])),
                     "eta_median": np.median(np.array(r["eta"]), axis=0).tolist()})
out = {"haupt": main, "fair_abweichung_2100_rel": dev,
       "sens": {"wachstum_11": short(solve(growth=1.11, ziel="co2")), "technisch": short(solve(stufe="technisch", ziel="co2")),
                "median": short(solve(quantil=0.5, ziel="co2"))},
       "wachstumsgrenze_gt": growth_limit().tolist(),
       "ziel_kurve": capacity_by_target(), "strompfade": pathways}
OUT.write_text(json.dumps(out, ensure_ascii=False))
print("ok", main["status"], main["ziel_jahr"], f"{main['kapazitaet_gt']:.1f} Gt/a", f"{np.sum(main['x']):.0f} Gt brutto",
      f"FaIR-Abweichung {dev:+.1%}", {k: (v["status"], round(v["kapazitaet_gt"], 1)) for k, v in out["sens"].items()},
      [(c["ziel_jahr"], round(c["kapazitaet_gt"], 1)) for c in out["ziel_kurve"]],
      [(p["strompfad"], round(p["kapazitaet_gt"], 2)) for p in pathways])
