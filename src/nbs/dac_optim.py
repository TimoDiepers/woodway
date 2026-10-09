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


def eta_by_country(quantil: float = 0.9, stufe: str = "prudent", pathway: str = "SSP2-NDC") -> tuple[list[str], NDArray]:
    """Countries with storage and at least one DAC-capable cell near a basin, and their net
    efficiency per year: the median of the cells at or above the *quantil* of eta in that year."""
    from nbs.dac import dac_possible, efficiency_grid
    from nbs.dac_storage import iso3_grid, storage_by_country, storage_mask

    store = storage_by_country(stufe)
    iso = iso3_grid()
    ok = dac_possible() & storage_mask()
    grids = [efficiency_grid(int(y), pathway=pathway) for y in YEARS]
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
def _infeasible(res) -> bool:
    """HiGHS infeasible -- also when presolve leaves the model status unknown but the primal status infeasible."""
    return res.status == 2 or (res.status == 4 and "primal_status is Infeasible" in res.message)


def build_and_solve(eta: NDArray, kernel: NDArray, gap: NDArray, storage: NDArray, x_from: int | None,
                    growth: float, start_2030: float | None = START_2030_GT, objective: str = "min_total",
                    years: NDArray | None = None, keep_running: bool = False,
                    co2_target: float | None = None, then_total: bool = False,
                    cap: float | None = None) -> tuple[bool, NDArray | None]:
    """The LP on plain arrays. x is flattened country-major: x[c * n + y].

    objective "min_total": cooling >= gap for t >= x_from, minimise sum x.
    objective "min_peak": cooling >= gap for t >= x_from, minimise the largest yearly world removal, then at
    that peak (+1e-6 relative) minimise sum x.
    objective "max_net": no target; maximise the net removal, each tonne weighted by the years it is out of the air
    until the last year -- as much DAC as early as the growth limit and the storage allow.
    objective "min_shortfall": extra slack s[t] >= gap - cooling, s >= 0, minimise sum of s[t] for t >= x_from
    (all years if x_from is None).
    co2_target: the target on the CO2 level instead: cumulative net removal sum_{c, y<=t} eta * x >= co2_target
    [Gt] for t >= x_from (kernel and gap are not used then).
    keep_running: plants once built run on, x[c, t] >= x[c, t-1] (makes where/when unique enough to show).
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
    if co2_target is not None:  # cumulative net removal up to year t
        for c in range(n_c):
            cool[:, c * n:(c + 1) * n] = np.tril(np.ones((n, n))) * eta[c][None, :]
        gap = np.full(n, float(co2_target))
    else:
        for c in range(n_c):
            cool[:, c * n:(c + 1) * n] = (-kernel * eta[c][:, None]).T
    a, b = [], []
    if slack:
        rows = np.hstack([-cool, -np.eye(n)])          # -cooling - s <= -gap
        a.append(rows); b.append(-gap)
    elif objective != "max_net":
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
                hi = max(0.0, start_2030 * (years[y] - 2025) / 5)  # per-country cap; the sum cap follows below
            if eta[c, y] <= 0:
                hi = 0.0                                          # a plant that warms is never built
            bounds[c * n + y] = (0.0, hi)
    if start_2030 is not None:                                    # world caps 2026-2030
        for y in np.where(years <= 2030)[0]:
            row = np.zeros(nv); row[y:nx:n] = 1.0
            a.append(row[None, :]); b.append(np.array([max(0.0, start_2030 * (years[y] - 2025) / 5)]))
    if keep_running:
        kr = np.zeros((n_c * (n - 1), nv))
        for c in range(n_c):
            for t in range(1, n):
                kr[c * (n - 1) + t - 1, c * n + t - 1] = 1.0
                kr[c * (n - 1) + t - 1, c * n + t] = -1.0
        a.append(kr); b.append(np.zeros(len(kr)))
    if cap is not None:                                           # world capacity at most *cap* [Gt/a]
        wc = np.zeros((n, nv))
        for t in range(n):
            wc[t, t:nx:n] = 1.0
        a.append(wc); b.append(np.full(n, float(cap)))
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
        if _infeasible(res):
            return False, None
        if res.status != 0:
            raise RuntimeError(f"LP stage 1: {res.message}")
        peak = res.x[-1] * (1 + 1e-6) + 1e-12
        A, B = np.vstack([A, world[:, :-1]]), np.r_[B, np.full(n, peak)]
    if slack and then_total:
        # stage 1: least summed shortfall; stage 2: at that shortfall, the least total DAC
        c1 = np.r_[np.zeros(nx), np.ones(n)]
        res = linprog(c1, A_ub=A, b_ub=B, bounds=bounds, method="highs")
        if res.status != 0:
            raise RuntimeError(f"LP stage 1: {res.message}")
        A = np.vstack([A, c1[None, :]]); B = np.r_[B, res.fun * (1 + 1e-6) + 1e-9]
        c_obj = np.r_[np.ones(nx), np.zeros(n)]
    elif objective == "max_net":
        c_obj = np.r_[-(eta * (n - np.arange(n))[None, :]).reshape(-1), np.zeros(nv - nx)]
    elif slack:
        c_obj = np.r_[np.zeros(nx), (np.arange(n) >= (x_from or 0)).astype(float)]
    else:
        c_obj = np.r_[np.ones(nx), np.zeros(nv - nx)]
    res = linprog(c_obj, A_ub=A, b_ub=B, bounds=bounds, method="highs")
    if _infeasible(res):
        return False, None
    if res.status != 0:
        raise RuntimeError(f"LP: {res.message}")
    return True, np.maximum(res.x[:nx].reshape(n_c, n), 0.0)  # solver noise around the bound (~1e-8)


TARGET_YEAR = 2100


PATHWAYS = ("SSP2-NPi", "SSP2-NDC", "SSP2-PkBudg650")  # electricity: current policies, pledges, 650 Gt budget


def _setup(stufe: str, quantil: float, pathway: str):
    from nbs.dac_storage import storage_by_country

    countries, eta = eta_by_country(quantil, stufe, pathway)
    store = storage_by_country(stufe)
    return countries, eta, np.array([store[c] for c in countries])


def solve(growth: float = GROWTH, stufe: str = "prudent", quantil: float = 0.9, ziel_jahr: int = TARGET_YEAR,
          pathway: str = "SSP2-NDC", keep_running: bool = True, ziel: str = "temperatur",
          gap_k: NDArray | None = None, limit_start: bool = True) -> dict:
    """Least DAC capacity (then least total) that closes the gap from *ziel_jahr* on, plants running on once
    built; if impossible, the closest approach (least summed shortfall from *ziel_jahr* on).
    ziel="co2": the target is the net CO2 removal co2_target_gt() by *ziel_jahr* instead of the cooling.
    gap_k: the warming above 1.5 deg C to close [K, per year] instead of the area slide's gap; limit_start=False
    drops the 2030 start (8.8 Mt/a) so only *growth* limits the build-out (growth=inf: no limit at all)."""
    if not YEARS[0] <= ziel_jahr <= YEARS[-1]:
        raise ValueError(f"ziel_jahr {ziel_jahr} outside {YEARS[0]}..{YEARS[-1]}")
    countries, eta, storage = _setup(stufe, quantil, pathway)
    k = removal_kernel_matrix()
    gap = gap_series() if gap_k is None else np.maximum(0.0, np.asarray(gap_k, dtype=float))
    i = int(ziel_jahr - YEARS[0])
    start = START_2030_GT if limit_start else None
    co2 = co2_target_gt() if ziel == "co2" else None
    ok, x = build_and_solve(eta, k, gap, storage, i, growth, start_2030=start, objective="min_peak", years=YEARS,
                            keep_running=keep_running, co2_target=co2)
    status = "geschlossen"
    if not ok:
        ok, x = build_and_solve(eta, k, gap, storage, i, growth, start_2030=start, objective="min_shortfall", years=YEARS,
                                keep_running=keep_running, co2_target=co2)
        assert ok, "closest-approach LP must always be feasible (x = 0 is a solution)"
        status = "annaeherung"
    cooling = -np.einsum("yt,cy,cy->t", k, eta, x)
    return {"jahre": YEARS.tolist(), "laender": countries, "x": x.tolist(), "eta": eta.tolist(),
            "kuehlung_k": cooling.tolist(), "luecke_k": gap.tolist(), "ziel_jahr": int(ziel_jahr), "status": status,
            "kapazitaet_gt": float(x.sum(axis=0).max()), "wachstum": growth, "stufe": stufe, "quantil": quantil,
            "strompfad": pathway, "ziel": ziel, "co2_ziel_gt": co2,
            "netto_gt": float((x * eta).sum())}


@lru_cache(maxsize=1)
def co2_target_gt() -> float:
    """The 1.5 deg C gap of 2100 on the CO2 level [Gt net]: the net removal of the least-capacity path that cools
    the gap in 2100 (temperature target, main case). Fixed by this rule, not tuned: the CO2 target then asks for
    the same amount of CO2, and the result shows what that amount does to the temperature over time."""
    r = solve(ziel="temperatur")
    assert r["status"] == "geschlossen"
    return r["netto_gt"]


def growth_limit(growth: float = GROWTH) -> NDArray:
    """Largest world removal the growth limit allows each year [Gt/a] (linear to 8.8 Mt/a in 2030, then x growth)."""
    out = np.zeros(N_Y)
    for i, y in enumerate(YEARS):
        out[i] = START_2030_GT * (y - 2025) / 5 if y <= 2030 else out[i - 1] * growth
    return out


def solve_max(growth: float = GROWTH, stufe: str = "prudent", quantil: float = 0.9, pathway: str = "SSP2-NDC",
              keep_running: bool = True) -> dict:
    """As much DAC as possible: the growth limit from 8.8 Mt/a in 2030 and the storage of each country are the
    only limits; maximises the net removal up to 2100. The cooling follows with the removal kernel."""
    countries, eta, storage = _setup(stufe, quantil, pathway)
    k = removal_kernel_matrix()
    ok, x = build_and_solve(eta, k, np.zeros(N_Y), storage, None, growth, objective="max_net", years=YEARS,
                            keep_running=keep_running)
    assert ok
    cooling = -np.einsum("yt,cy,cy->t", k, eta, x)
    return {"jahre": YEARS.tolist(), "laender": countries, "x": x.tolist(), "eta": eta.tolist(),
            "kuehlung_k": cooling.tolist(), "kapazitaet_gt": float(x.sum(axis=0).max()), "netto_gt": float((x * eta).sum()),
            "speicher_gt": float(storage.sum()), "wachstum": growth, "strompfad": pathway}


def solve_naive(gap_k: NDArray, ziel_jahr: int = TARGET_YEAR, growth: float = GROWTH, stufe: str = "prudent",
                quantil: float = 0.9, pathway: str = "SSP2-NDC") -> dict:
    """The simple case for comparison: the world capacity spread over the countries in proportion to their safe
    storage, the same every year (no choice of place by electricity or climate); least capacity that closes
    *gap_k* from *ziel_jahr* on, with the same growth limit and plants running on."""
    from scipy.optimize import linprog

    countries, eta, storage = _setup(stufe, quantil, pathway)
    share = storage / storage.sum()
    eta_mix = (share[:, None] * np.maximum(eta, 0.0)).sum(axis=0)     # net share of the spread capacity per year
    k = removal_kernel_matrix()
    gap = np.maximum(0.0, np.asarray(gap_k, dtype=float))
    n, i = N_Y, int(ziel_jahr - YEARS[0])
    cool = (-k * eta_mix[:, None]).T                                 # cooling[t] per Gt/a of world capacity in y
    a, b = [-cool[i:]], [-gap[i:]]
    for t_ in range(1, n):                                           # running on, growth limit
        r = np.zeros(n); r[t_ - 1], r[t_] = 1.0, -1.0; a.append(r[None]); b.append([0.0])
        if YEARS[t_] > 2030:
            r = np.zeros(n); r[t_], r[t_ - 1] = 1.0, -growth; a.append(r[None]); b.append([0.0])
    bounds = [(0.0, START_2030_GT * (y - 2025) / 5 if y <= 2030 else None) for y in YEARS]
    A, B = np.vstack(a), np.concatenate([np.atleast_1d(v) for v in b])
    res = linprog(np.r_[np.zeros(n - 1), 1.0], A_ub=A, b_ub=B, bounds=bounds, method="highs")  # least final capacity
    if res.status != 0:
        return {"status": "unmoeglich"}
    A2, B2 = np.vstack([A, np.r_[np.zeros(n - 1), 1.0][None]]), np.r_[B, res.x[-1] * (1 + 1e-6)]
    res = linprog(np.ones(n), A_ub=A2, b_ub=B2, bounds=bounds, method="highs")
    w = res.x
    x = share[:, None] * w[None, :]
    assert np.all(x.sum(axis=1) <= storage * (1 + 1e-6)), "storage would bind; the simple case is not defined"
    cooling = cool @ w
    return {"status": "geschlossen", "laender": countries, "x": x.tolist(), "eta": eta.tolist(), "kuehlung_k": cooling.tolist(),
            "kapazitaet_gt": float(w.max()), "brutto_gt": float(w.sum()), "netto_gt": float((w * eta_mix).sum())}


def solve_min_peak(gap_k: NDArray, growth: float = GROWTH, limit_start: bool = True, ziel_jahr: int | None = TARGET_YEAR,
                   stufe: str = "prudent", quantil: float = 0.9, pathway: str = "SSP2-NDC", danach: str = "ziel") -> dict:
    """The least highest warming above 1.5 deg C after trees and DAC (*gap_k* [K] per year without DAC). Then, at
    that peak: danach="schnell" back down to 1.5 deg C as fast as possible (least summed warming above 1.5 deg C),
    then the least total DAC at that; danach="ziel": the least DAC that brings the world to 1.5 deg C from
    *ziel_jahr* on (if it can; otherwise the least total DAC at the peak). Plants run on, storage per country,
    growth limit as everywhere."""
    from scipy.optimize import linprog

    countries, eta, storage = _setup(stufe, quantil, pathway)
    k = removal_kernel_matrix()
    gap = np.maximum(0.0, np.asarray(gap_k, dtype=float))
    n_c, n = eta.shape
    nx = n_c * n
    cool = np.zeros((n, nx))
    for c in range(n_c):
        cool[:, c * n:(c + 1) * n] = (-k * eta[c][:, None]).T
    # the usual constraints: storage per country, growth limit (with the 2030 start), plants running on
    years = YEARS
    start = START_2030_GT if limit_start else None
    a, b = [], []
    st = np.zeros((n_c, nx))
    for c in range(n_c):
        st[c, c * n:(c + 1) * n] = 1.0
    a.append(st); b.append(storage)
    first = 1 if start is None else int(np.where(years == 2030)[0][0]) + 1
    gr = np.zeros((n - first, nx))
    for j, t_ in enumerate(range(first, n)):
        gr[j, t_::n] = 1.0
        gr[j, t_ - 1::n] = -growth
    a.append(gr); b.append(np.zeros(n - first))
    bounds = [(0.0, None)] * nx
    for c in range(n_c):
        for y in range(n):
            hi = None
            if start is not None and years[y] <= 2030:
                hi = start * (years[y] - 2025) / 5
            if eta[c, y] <= 0:
                hi = 0.0
            bounds[c * n + y] = (0.0, hi)
    if start is not None:
        for y in np.where(years <= 2030)[0]:
            row = np.zeros(nx); row[y::n] = 1.0
            a.append(row[None]); b.append(np.array([start * (years[y] - 2025) / 5]))
    kr = np.zeros((n_c * (n - 1), nx))
    for c in range(n_c):
        for t_ in range(1, n):
            kr[c * (n - 1) + t_ - 1, c * n + t_ - 1] = 1.0
            kr[c * (n - 1) + t_ - 1, c * n + t_] = -1.0
    a.append(kr); b.append(np.zeros(len(kr)))
    A = np.hstack([np.vstack(a), np.zeros((sum(m.shape[0] for m in a), 1))])
    B = np.concatenate(b)
    # stage 1: M >= gap - cooling in every year, minimise M
    A1 = np.vstack([A, np.hstack([-cool, -np.ones((n, 1))])])
    B1 = np.r_[B, -gap]
    res = linprog(np.r_[np.zeros(nx), 1.0], A_ub=A1, b_ub=B1, bounds=bounds + [(0.0, None)], method="highs")
    if res.status != 0:
        raise RuntimeError(f"LP stage 1: {res.message}")
    peak = float(res.x[-1])
    A2 = np.vstack([A1, np.r_[np.zeros(nx), 1.0][None]]); B2 = np.r_[B1, peak * (1 + 1e-6) + 1e-9]
    status = "spitze"
    if danach == "schnell":
        # stage 2: slack s[t] >= gap - cooling, least sum of s; stage 3: at that sum, the least total DAC
        A4 = np.vstack([np.hstack([A2, np.zeros((A2.shape[0], n))]), np.hstack([-cool, np.zeros((n, 1)), -np.eye(n)])])
        B4 = np.r_[B2, -gap]
        b4 = bounds + [(0.0, None)] + [(0.0, None)] * n
        res = linprog(np.r_[np.zeros(nx + 1), np.ones(n)], A_ub=A4, b_ub=B4, bounds=b4, method="highs")
        if res.status != 0:
            raise RuntimeError(f"LP stage 2: {res.message}")
        A5 = np.vstack([A4, np.r_[np.zeros(nx + 1), np.ones(n)][None]]); B5 = np.r_[B4, res.fun * (1 + 1e-6) + 1e-9]
        res = linprog(np.r_[np.ones(nx), 0.0, np.zeros(n)], A_ub=A5, b_ub=B5, bounds=b4, method="highs")
        if res.status != 0:
            raise RuntimeError(f"LP stage 3: {res.message}")
        status = "spitze_dann_schnell"
    elif ziel_jahr is not None:
        i = int(ziel_jahr - years[0])
        A3 = np.vstack([A2, np.hstack([-cool[i:], np.zeros((n - i, 1))])]); B3 = np.r_[B2, -gap[i:]]
        res = linprog(np.r_[np.ones(nx), 0.0], A_ub=A3, b_ub=B3, bounds=bounds + [(0.0, None)], method="highs")
        if res.status == 0:
            status = "spitze_und_ziel"
    if status == "spitze":
        res = linprog(np.r_[np.ones(nx), 0.0], A_ub=A2, b_ub=B2, bounds=bounds + [(0.0, None)], method="highs")
    x = np.maximum(res.x[:nx].reshape(n_c, n), 0.0)
    cooling = cool @ x.reshape(-1)
    return {"jahre": years.tolist(), "laender": countries, "x": x.tolist(), "eta": eta.tolist(), "kuehlung_k": cooling.tolist(),
            "spitze_k": peak, "status": status, "kapazitaet_gt": float(x.sum(axis=0).max()), "netto_gt": float((x * eta).sum())}


def capacity_by_target(ziel_jahre=(2085, 2090, 2095, 2100), growth: float = GROWTH, ziel: str = "co2") -> list[dict]:
    """Least capacity [Gt/a] and total [Gt] needed to reach the target by each target year."""
    out = []
    for z in ziel_jahre:
        r = solve(growth=growth, ziel_jahr=z, ziel=ziel)
        out.append({"ziel_jahr": int(z), "status": r["status"], "kapazitaet_gt": r["kapazitaet_gt"],
                    "summe_gt": float(np.sum(r["x"]))})
    return out


def fair_cooling(net_gt: NDArray) -> NDArray:
    """Cooling [K] by a net removal path [Gt/a on YEARS] in the full FaIR model, on the LP's year axis.

    FaIR reports temperature at timebounds 2026.0..2099.0; the kernel books a removal into the stock in the
    year it happens, so LP year index j matches FaIR timebound j + 1. LP years 2099 and 2100 have no FaIR
    value (NaN)."""
    from nbs.fair_module import run_fair_baseline, run_fair_perturbed

    base = run_fair_baseline()
    n = len(base)
    dt = run_fair_perturbed(-np.asarray(net_gt, dtype=float)[:n], np.zeros(n)) - base
    out = np.full(N_Y, np.nan)
    out[: n - 1] = -dt[1:]
    return out
