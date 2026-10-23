"""Data for the temperature slide's native chart (deck/chart_data/tempsum.json).

The tree's temperature effect built up from single years: the answer to one year of forcing (Aachen, 2041),
the same for every fifth year, their sum over all years, then the three sites. All with the temperature
response g_T of the FaIR member, so the sum is exactly FaIR's result (checked here).

Per site also the net Delta T split by cause (slide 22, the overlay per site): CO2 uptake, and the albedo
forcing split into leaves (alpha_q_product) and clouds (cloud_q_product). Both splits are exact: the albedo
forcing is linear in the light product, Delta T is linear in the forcing (checked here).

    uv run python scripts/build_tempsum_data.py
"""
import json
from pathlib import Path

import numpy as np

from nbs.albedo_grid import alpha_q_product
from nbs.animations import SITES, site_cell, site_key
from nbs.cloud_grid import cloud_q_product
from nbs.response import green_temperature
from nbs.storyline_figures import run_site

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "deck/chart_data/tempsum.json"
ONE_YEAR, EVERY, SCALE = 2041, 5, 1e15


def main() -> None:
    g = np.asarray(green_temperature("ssp245"), dtype=float)
    sites = []
    for s in SITES:
        r = run_site(s)
        phi, dt = np.asarray(r.phi_total, dtype=float), np.asarray(r.delta_t, dtype=float)
        n = len(phi)
        conv = lambda f: np.array([np.dot(g[: t + 1][::-1], f[: t + 1]) for t in range(n)])
        assert np.max(np.abs(conv(phi) - dt)) * SCALE < 0.05, s.name
        # the albedo forcing by its two light products at the site's cell
        key, cell = site_key(s), site_cell(s)
        p_leaf, p_cloud = float(alpha_q_product(key)[cell]), float(cloud_q_product(key)[cell])
        f_alb = np.asarray(r.phi_albedo, dtype=float)
        f_leaf, f_cloud = f_alb * p_leaf / (p_leaf + p_cloud), f_alb * p_cloud / (p_leaf + p_cloud)
        parts = {"co2": conv(np.asarray(r.phi_co2, dtype=float)), "laub": conv(f_leaf), "wolke": conv(f_cloud)}
        assert np.max(np.abs(sum(parts.values()) - dt)) * SCALE < 0.05, s.name
        sites.append({"name": s.name, "label": s.label, "color": s.color, "phi": phi.tolist(),
                      "dt": [round(v * SCALE, 3) for v in dt],
                      **{k: [round(v * SCALE, 3) for v in a] for k, a in parts.items()}})
    years = [int(y) for y in np.asarray(run_site(SITES[0]).years)]
    phi0 = np.asarray(sites[0]["phi"])

    def pulse(i):
        return [round(float(v) * SCALE, 4) for v in g[: len(years) - i] * phi0[i]]

    pulses = [{"year": years[i], "v": pulse(i)} for i in range(0, len(years), EVERY)]
    out = {"years": years, "one": {"year": ONE_YEAR, "v": pulse(years.index(ONE_YEAR))}, "every": EVERY,
           "pulses": [p for p in pulses if p["year"] != ONE_YEAR],
           "sites": [{k: v for k, v in s.items() if k != "phi"} for s in sites]}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
