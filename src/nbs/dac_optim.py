"""Where, when and how much DAC: a linear programme that closes the 1.5 deg C gap of Very Low.

Decision variables x[c, y]: gross DAC removal in country c and year y [Gt/a]. The climate effect
is linear in x through the FaIR kernel K[y, t] (temperature in year t per Gt net removal in year y,
the same chain as the trees) and the country's net efficiency eta[c, y] (nbs.dac):

    cooling(t) = - sum_c sum_y K[y, t] * eta[c, y] * x[c, y]   >= gap(t)  for t >= X
    sum_y x[c, y] <= storage[c]                                (Gidden et al. 2025)
    sum_c x[c, t] <= GROWTH * sum_c x[c, t-1], t > 2030;  sum_c x[c, 2030] <= 0.0088
                                                               (Zurbriggen et al. 2026)

Stage 1 finds the earliest X; stage 2 minimises total gross removal at that X. If no X <= 2100 is
feasible, the closest approach minimises the summed shortfall instead.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from nbs.constants import YEARS

ROOT = Path(__file__).resolve().parents[2]
GAP_FILE = ROOT / "docs" / "slides" / "chart_data" / "luecke.json"
START_2030_GT = 0.0088   # mean planned DAC capacity 2030 (Zurbriggen et al. 2026)
GROWTH = 1.20            # wind-energy analogue, 20 %/a (Zurbriggen et al. 2026)
N_Y = len(YEARS)


def eta_by_country(quantil: float = 0.9, stufe: str = "prudent") -> tuple[list[str], NDArray]:
    """Countries with storage and at least one DAC-capable cell near a basin, and their net
    efficiency per year: the median of the cells at or above the *quantil* of eta in that year."""
    from nbs.dac import dac_possible, efficiency_grid
    from nbs.dac_storage import iso3_grid, storage_by_country, storage_mask

    store = storage_by_country(stufe)
    iso = iso3_grid()
    ok = dac_possible() & storage_mask()
    grids = [efficiency_grid(int(y)) for y in YEARS]
    countries, rows = [], []
    for c in sorted(k for k, v in store.items() if v > 0):
        cells = ok & (iso == c)
        if not cells.any():
            continue
        row = []
        for g in grids:
            v = g[cells]
            v = v[np.isfinite(v)]
            row.append(float(np.median(v[v >= np.quantile(v, quantil)])) if v.size else np.nan)
        if np.all(np.isfinite(row)):
            countries.append(c)
            rows.append(row)
    return countries, np.array(rows)


@lru_cache(maxsize=1)
def removal_kernel_matrix(scenario: str = "ssp245") -> NDArray:
    """K[y, t]: temperature change [K] in year t per Gt CO2 taken out of the air in year y."""
    from nbs.forcing import phi_co2_background
    from nbs.response import background_co2_ppm, convolve_response, green_carbon, green_temperature

    g_c, g_t, bg = green_carbon(scenario), green_temperature(scenario), background_co2_ppm(scenario)
    k = np.zeros((N_Y, N_Y))
    for i in range(N_Y):
        flux = np.zeros(N_Y)
        flux[i] = -1000.0  # one tonne removed [kg], the marginal response ...
        k[i] = convolve_response(g_t, phi_co2_background(flux, g_c, bg)) * 1e9  # ... scaled to 1 Gt
    return k


def gap_series() -> NDArray:
    """Cooling needed on top of Very Low and the trees on cooling areas [K], year by year (slide 25)."""
    d = json.loads(GAP_FILE.read_text())
    assert d["y"] == YEARS.tolist()
    return np.maximum(0.0, (np.array(d["need"]) - np.array(d["k"])) / 1000.0)
