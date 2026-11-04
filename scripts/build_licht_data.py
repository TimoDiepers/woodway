"""Data for the native chart beside the absorbed-light map (deck/chart_data/licht.json).

Per site the extra absorbed light of one tree planted in 2026 [W, annual mean]: it grows with the crown,
A_Baum(t) = closure(t) x 5 m2, so the value in 2100 is the one the map shows. Net, and the two causes: the
leaves' albedo (alpha_q_product) and the clouds (cloud_q_product); net = leaves + clouds.

    uv run python scripts/build_licht_data.py
"""
import json
from pathlib import Path

import numpy as np

from nbs.animations import SITES, cloud_season_series
from nbs.storyline_figures import run_site

OUT = Path(__file__).resolve().parents[1] / "deck/chart_data/licht.json"


def main() -> None:
    sites = []
    for s in SITES:
        alb, cld, net = (float(v.mean()) for v in cloud_season_series(s))
        f = np.asarray(run_site(s).trajectory.closure, dtype=float)
        r = lambda a: [round(float(v), 3) for v in a]
        sites.append({"name": s.name, "label": s.label, "color": s.color, "laub": r(alb * f), "wolke": r(cld * f), "dt": r(net * f)})
    years = [int(y) for y in np.asarray(run_site(SITES[0]).years)]
    OUT.write_text(json.dumps({"years": years, "sites": sites}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("wrote", OUT, {s["name"]: round(s["dt"][-1], 1) for s in sites})


if __name__ == "__main__":
    main()
