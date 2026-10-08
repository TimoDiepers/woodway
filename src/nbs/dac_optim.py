"""Where, when and how much DAC: a linear programme that closes the 1.5 deg C gap of Very Low.

Decision variables x[c, y]: gross DAC removal in country c and year y [Gt/a]. The climate effect
is linear in x through the FaIR kernel K[y, t] (temperature in year t per Gt net removal in year y,
the same chain as the trees) and the country's net efficiency eta[c, y] (nbs.dac):

    cooling(t) = - sum_c sum_y K[y, t] * eta[c, y] * x[c, y]   >= gap(t)  for t >= X
    sum_y x[c, y] <= storage[c]                                (Gidden et al. 2025)
    sum_c x[c, t] <= GROWTH * sum_c x[c, t-1], t > 2030;  sum_c x[c, 2030] <= 0.0088
                                                               (Zurbriggen et al. 2026)

X is the target year (2100: the gap of slide 25 is closed at the end of the century, the overshoot before
stays). Objective: the least DAC capacity -- the largest yearly removal, max_t sum_c x[c, t] -- and at that
capacity the least total removal. Minimising only the total would bunch the removal into a few years of
enormous capacity, because a tonne removed late cools slightly more by the target year. If the target
cannot be met, the closest approach minimises the summed shortfall instead.
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
def build_and_solve(eta: NDArray, kernel: NDArray, gap: NDArray, storage: NDArray, x_from: int | None,
                    growth: float, start_2030: float | None = START_2030_GT, objective: str = "min_total",
                    years: NDArray | None = None) -> tuple[bool, NDArray | None]:
    """The LP on plain arrays. x is flattened country-major: x[c * n + y].

    objective "min_total": cooling >= gap for t >= x_from, minimise sum x.
    objective "min_peak": cooling >= gap for t >= x_from, minimise the largest yearly world removal, then at
    that peak (+1e-6 relative) minimise sum x.
    objective "min_shortfall": extra slack s[t] >= gap - cooling, s >= 0, minimise sum s (x_from ignored).
    start_2030=None drops the 2026-2030 caps (unit tests); growth applies to every year after the
    first then.
    """
    from scipy.optimize import linprog
    from scipy.sparse import lil_matrix

    n_c, n = eta.shape
    years = np.arange(2026, 2026 + n) if years is None else years
    nx = n_c * n
    slack = objective == "min_shortfall"
    nv = nx + (n if slack else 0)
    # cooling(t) = sum_{c,y} -K[y, t] * eta[c, y] * x[c, y]
    cool = np.zeros((n, nx))
    for c in range(n_c):
        cool[:, c * n:(c + 1) * n] = (-kernel * eta[c][:, None]).T
    a, b = [], []
    if slack:
        rows = np.hstack([-cool, -np.eye(n)])          # -cooling - s <= -gap
        a.append(rows); b.append(-gap)
    else:
        a.append(np.hstack([-cool[x_from:], np.zeros((n - x_from, nv - nx))])); b.append(-gap[x_from:])
    st = lil_matrix((n_c, nv))                          # storage per country
    for c in range(n_c):
        st[c, c * n:(c + 1) * n] = 1.0
    a.append(st.toarray()); b.append(storage)
    first = 1 if start_2030 is None else int(np.where(years == 2030)[0][0]) + 1
    gr = np.zeros((n - first, nv))                       # sum_c x[c, t] - growth * sum_c x[c, t-1] <= 0
    for j, t in enumerate(range(first, n)):
        gr[j, t::n][:n_c] = 1.0
        gr[j, t - 1::n][:n_c] = -growth
    a.append(gr); b.append(np.zeros(n - first))
    bounds = [(0.0, None)] * nv
    for c in range(n_c):
        for y in range(n):
            hi = None
            if start_2030 is not None and years[y] <= 2030:
                hi = start_2030 * (years[y] - 2025) / 5          # per-country cap; the sum cap follows below
            if eta[c, y] <= 0:
                hi = 0.0                                          # a plant that warms is never built
            bounds[c * n + y] = (0.0, hi)
    if start_2030 is not None:                                    # world caps 2026-2030
        for y in np.where(years <= 2030)[0]:
            row = np.zeros(nv); row[y:nx:n] = 1.0
            a.append(row[None, :]); b.append(np.array([START_2030_GT * (years[y] - 2025) / 5]))
    A, B = np.vstack(a), np.concatenate(b)
    if objective == "min_peak":
        # one more variable P >= sum_c x[c, t] for every t; minimise P first
        world = np.zeros((n, nv + 1))
        for t in range(n):
            world[t, t:nx:n] = 1.0
            world[t, -1] = -1.0
        A1 = np.vstack([np.hstack([A, np.zeros((A.shape[0], 1))]), world])
        B1 = np.r_[B, np.zeros(n)]
        res = linprog(np.r_[np.zeros(nv), 1.0], A_ub=A1, b_ub=B1, bounds=bounds + [(0.0, None)], method="highs")
        if res.status != 0:
            return False, None
        peak = res.x[-1] * (1 + 1e-6) + 1e-12
        A, B = np.vstack([A, world[:, :-1]]), np.r_[B, np.full(n, peak)]
    c_obj = np.r_[np.zeros(nx), np.ones(n)] if slack else np.r_[np.ones(nx), np.zeros(nv - nx)]
    res = linprog(c_obj, A_ub=A, b_ub=B, bounds=bounds, method="highs")
    if res.status != 0:
        return False, None
    return True, res.x[:nx].reshape(n_c, n)


TARGET_YEAR = 2100


def _setup(stufe: str, quantil: float):
    from nbs.dac_storage import storage_by_country

    countries, eta = eta_by_country(quantil, stufe)
    store = storage_by_country(stufe)
    return countries, eta, np.array([store[c] for c in countries])


def solve(growth: float = GROWTH, stufe: str = "prudent", quantil: float = 0.9, ziel_jahr: int = TARGET_YEAR) -> dict:
    """Least DAC capacity (then least total) that closes the gap from *ziel_jahr* on; if impossible,
    the closest approach (least summed shortfall)."""
    countries, eta, storage = _setup(stufe, quantil)
    k, gap = removal_kernel_matrix(), gap_series()
    ok, x = build_and_solve(eta, k, gap, storage, int(ziel_jahr - YEARS[0]), growth, objective="min_peak", years=YEARS)
    status = "geschlossen"
    if not ok:
        ok, x = build_and_solve(eta, k, gap, storage, None, growth, objective="min_shortfall", years=YEARS)
        assert ok, "closest-approach LP must always be feasible (x = 0 is a solution)"
        status = "annaeherung"
    cooling = -np.einsum("yt,cy,cy->t", k, eta, x)
    return {"jahre": YEARS.tolist(), "laender": countries, "x": x.tolist(), "eta": eta.tolist(),
            "kuehlung_k": cooling.tolist(), "luecke_k": gap.tolist(), "ziel_jahr": int(ziel_jahr), "status": status,
            "kapazitaet_gt": float(x.sum(axis=0).max()), "wachstum": growth, "stufe": stufe, "quantil": quantil}


def capacity_by_target(ziel_jahre=(2085, 2090, 2095, 2100), growth: float = GROWTH) -> list[dict]:
    """Least capacity [Gt/a] and total [Gt] needed to hold 1.5 deg C from each target year on."""
    out = []
    for z in ziel_jahre:
        r = solve(growth=growth, ziel_jahr=z)
        out.append({"ziel_jahr": int(z), "status": r["status"], "kapazitaet_gt": r["kapazitaet_gt"],
                    "summe_gt": float(np.sum(r["x"]))})
    return out
