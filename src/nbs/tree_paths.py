"""Planting paths over time: three ways to use the reforestable land, all planted in the start year.

Three ways to use the reforestable land, each as one full FaIR run (removals as negative CO2 emissions,
albedo as a forcing; the same chain as ``nbs.potential.fair_global_delta_t``):

- ``"alle"``: every reforestable cell with a typical forest (0.83 Gha), left to grow.
- ``"kuehlt"``: only the cells whose tree still cools at the horizon (the area slide's main case), left to grow.
- ``"kuehlt_rodung"``: ``"kuehlt"`` plus today's forest where forest warms, cut in the start year with its
  biomass buried (felling_forcing_split), both in one FaIR run; the forgone sink counts as release.
- ``"forst"``: the cooling cells as managed forest: clear-cut at a rotation age by climate zone (boreal 80,
  temperate 60, subtropical 30, tropical 20 years) and replanted. The stem (70 % of the stand's carbon)
  leaves the forest as timber and stays bound -- the optimistic case; the residues go back to the air at
  felling. ``release=True`` sends the timber back to the air too (the comparison case).

Planting: every path is planted at once in the start year (T_START), a stated simplification; schedule() can
still spread a path at a given rate.

Approximations, stated: each cohort grows with the trajectory of its own planting year (calendar-dependent
disturbance hazard); later rotations reuse that trajectory shifted by the rotation age.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.typing import NDArray

from nbs.aggregate import co2_factor_grid
from nbs.light import light_product
from nbs.config import ModelConfig
from nbs.constants import A_EARTH_M2, M_CO2_PER_C, T_START, TAU_ATM, YEARS, SZENARIO
from nbs.fair_module import run_fair_baseline, run_fair_perturbed
from nbs.landscape import assign_species, plantable_area_m2, tree_count
from nbs.species import SPECIES, get_species, reference_site

# managed forest: clear-cut at a rotation age by climate zone (the zone is the suffix of the forest-type key)
ROTATION_BY_ZONE = {"boreal": 80, "gemaessigt": 60, "subtropisch": 30, "tropisch": 20}  # [a]
STEM_SHARE = 0.7                # share of the stand's carbon that leaves as timber; the residues decay
PATHS = ("alle", "kuehlt", "forst", "kuehlt_rodung")
N_Y = len(YEARS)


def masks() -> dict[str, NDArray]:
    """Cells of each path: every reforestable cell, and the cells that cool by the horizon."""
    from nbs.map_plots import _breakeven_year_field

    plant = assign_species() != None  # noqa: E711
    cool = plant & ~np.isinf(_breakeven_year_field(SZENARIO))
    return {"alle": plant, "kuehlt": cool}


def schedule(area_gha: float, start: int = T_START, rate_gha: float | None = None) -> NDArray:
    """Share of the area planted in each year of YEARS (sums to 1): *rate_gha* a year from *start*;
    rate None plants everything in the start year."""
    f = np.zeros(N_Y)
    i0 = start - int(YEARS[0])
    if rate_gha is None or area_gha <= 0:
        f[i0] = 1.0
        return f
    left, i = 1.0, i0
    while left > 1e-12 and i < N_Y:
        f[i] = min(left, rate_gha / area_gha)
        left -= f[i]
        i += 1
    return f / f.sum()


@lru_cache(maxsize=None)
def _trajectory(key: str, plant_year: int) -> tuple[NDArray, NDArray, NDArray]:
    """(net uptake [kgC/a], canopy closure [-], stock [kgC]) of one tree at the species' reference site, on
    YEARS, planted in *plant_year* (zero before)."""
    from nbs.pipeline import _background_temperature, _species_for
    from nbs.tree import simulate_deterministic

    sp = _species_for(key, ModelConfig(), reference_site(key))
    tr = simulate_deterministic(sp, _background_temperature(SZENARIO), plant_year=plant_year)
    out = tuple(np.asarray(a, dtype=float) for a in (tr.net_uptake_kgC_yr, tr.closure, tr.stock_kgC))
    for a in out:
        a.setflags(write=False)
    return out


def _cells(key: str, mask: NDArray) -> tuple[float, float, float]:
    """Sums over the cells of *key* in *mask*: (trees x co2 site factor, trees x albedo product, area [Gha])."""
    m = (assign_species() == key) & mask
    n = tree_count()[m]
    return (float((n * co2_factor_grid(key)[m]).sum()), float((n * np.nan_to_num(light_product(key)[m])).sum()),
            float(plantable_area_m2()[m].sum()) / 1e13)


def forcing(path: str, start: int = T_START, rate_gha: float | None = None,
            release: bool = False) -> tuple[NDArray, NDArray, float]:
    """(net CO2 exchange [Gt CO2/a, < 0 = removal], albedo forcing [W/m^2], planted area [Gha]) of a path."""
    up, loss, rf, area = forcing_split(path, start, rate_gha, release)
    return up + loss, rf, area


def forcing_split(path: str, start: int = T_START, rate_gha: float | None = None,
                  release: bool = False) -> tuple[NDArray, NDArray, NDArray, float]:
    """forcing with the CO2 exchange split: (uptake of the standing trees [Gt CO2/a, < 0], release at felling
    [Gt CO2/a, >= 0], albedo forcing [W/m^2], planted area [Gha])."""
    if path not in PATHS:
        raise ValueError(f"unknown path {path!r}")
    if path == "kuehlt_rodung":   # the cooling cells planted, plus today's warming forest cut and buried (stacked)
        up, loss, rf, area = forcing_split("kuehlt", start, rate_gha, release)
        lost, _, rf_cut, a_cut, _ = felling_forcing_split(start)
        return up, loss + lost, rf + rf_cut, area + a_cut
    mask = masks()["alle" if path == "alle" else "kuehlt"]
    sums = {key: _cells(key, mask) for key in SPECIES}
    sums = {k: v for k, v in sums.items() if v[2] > 0}
    area = sum(v[2] for v in sums.values())
    f = schedule(area, start, rate_gha)
    nee, loss, rf = np.zeros(N_Y), np.zeros(N_Y), np.zeros(N_Y)
    for key, (n_sum, np_sum, _) in sums.items():
        sp = get_species(key)
        rotation = ROTATION_BY_ZONE[key.split("_", 1)[1]] if path == "forst" else N_Y
        for i_py in np.flatnonzero(f):
            up, cl, st = _trajectory(key, int(YEARS[i_py]))
            w = f[i_py]
            # rotations: the same cohort trajectory shifted by multiples of the rotation age
            for r0 in range(i_py, N_Y, rotation):
                span = slice(r0, min(N_Y, r0 + rotation))
                src = slice(i_py, i_py + (span.stop - span.start))
                nee[span] -= M_CO2_PER_C * up[src] * n_sum * w / 1e12
                rf[span] += -TAU_ATM * cl[src] * sp.stand_area_m2 / A_EARTH_M2 * np_sum * w
                if span.stop < N_Y:
                    # felled: the residues go back to the air, the timber too only if release
                    share = 1.0 if release else 1.0 - STEM_SHARE
                    loss[span.stop] += share * M_CO2_PER_C * st[src.stop - 1] * n_sum * w / 1e12
    return nee, loss, rf, area


def _site_factor(keys: NDArray, carbon_mgc_ha: NDArray) -> NDArray:
    """Carbon of each cell relative to its forest key's median cell (as nbs.site_factor, for any carbon grid)."""
    from nbs.forest_data import growth_by_key

    g = growth_by_key()
    ref = np.array([[g[k]["m_ref_mgc_ha"] if k in g else np.nan for k in row] for row in keys])
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where((carbon_mgc_ha > 0) & (ref > 0), carbon_mgc_ha / ref, 0.0)


def cooling_cells(area_m2: NDArray, carbon_mgc_ha: NDArray) -> NDArray:
    """Cells with area whose typical forest still cools by T_END (finite break-even year), Very Low without its removal."""
    from nbs.aggregate import unit_curves
    from nbs.forest_data import key_grid
    from nbs.map_plots import _t_star_batch

    keys = key_grid(all_cells=True)
    f = _site_factor(keys, carbon_mgc_ha)
    out = np.zeros(area_m2.shape, bool)
    for key in SPECIES:
        m = (keys == key) & (area_m2 > 0) & (f > 0)
        if not m.any():
            continue
        co2, alb = unit_curves(key, SZENARIO)
        traj = f[m][:, None] * co2[None, :] + np.nan_to_num(light_product(key)[m])[:, None] * alb[None, :]
        out[m] = ~np.isinf(_t_star_batch(traj, YEARS))
    return out


def forcing_cells(area_m2: NDArray, carbon_mgc_ha: NDArray, start: int = T_START) -> tuple[NDArray, NDArray, float]:
    """(net CO2 exchange [Gt CO2/a], albedo forcing [W/m^2], counted area [Gha]) of forest on any land, planted
    at once in *start*, left to grow, only on the cells that cool (cooling_cells). Same chain as forcing()."""
    from nbs.forest_data import key_grid

    keys = key_grid(all_cells=True)
    f = _site_factor(keys, carbon_mgc_ha)
    cool = cooling_cells(area_m2, carbon_mgc_ha)
    i0 = start - int(YEARS[0])
    nee, rf, area = np.zeros(N_Y), np.zeros(N_Y), 0.0
    for key in SPECIES:
        m = (keys == key) & cool
        if not m.any():
            continue
        sp = get_species(key)
        n_trees = area_m2[m] / sp.stand_area_m2       # as nbs.landscape.tree_count
        up, cl, _ = _trajectory(key, start)
        n_sum = float((n_trees * f[m]).sum())
        np_sum = float((n_trees * np.nan_to_num(light_product(key)[m])).sum())
        nee[i0:] -= M_CO2_PER_C * up[i0:] * n_sum / 1e12
        rf[i0:] += -TAU_ATM * cl[i0:] * sp.stand_area_m2 / A_EARTH_M2 * np_sum
        area += float(area_m2[m].sum()) / 1e13
    return nee, rf, area


@lru_cache(maxsize=None)
def delta_t(path: str, start: int = T_START, rate_gha: float | None = None, release: bool = False) -> NDArray:
    """Global temperature change [K] of a path, one full FaIR run (Very Low background, without its own removal)."""
    nee, rf, _ = forcing(path, start, rate_gha, release)
    base = run_fair_baseline(SZENARIO)
    pert = run_fair_perturbed(nee[: len(base)], rf[: len(base)], SZENARIO)
    out = np.append(pert - base, (pert - base)[-1])[:N_Y]
    out.setflags(write=False)
    return out


@lru_cache(maxsize=None)
def delta_t_parts(path: str, start: int = T_START, release: bool = False) -> dict[str, NDArray]:
    """delta_t of a path by cause, each its own FaIR run: CO2 uptake of the standing trees, CO2 released at
    felling (residues, the timber too if *release*), albedo. They add up to delta_t only nearly (FaIR)."""
    up, loss, rf, _ = forcing_split(path, start, None, release)
    base = run_fair_baseline(SZENARIO)
    z = np.zeros(len(base))

    def run(nee, f):
        d = run_fair_perturbed(nee[: len(base)], f[: len(base)], SZENARIO) - base
        out = np.append(d, d[-1])[:N_Y]
        out.setflags(write=False)
        return out
    return {"co2_aufnahme": run(up, z), "co2_verlust": run(loss, z) if loss.any() else np.zeros(N_Y), "albedo": run(z, rf)}


# ---- felling: the existing forest that warms, cut in the start year, its biomass buried ----------------------

BESTAND = __import__("pathlib").Path(__file__).resolve().parents[2] / "data" / "forest" / "bestand_0p5.npz"


@lru_cache(maxsize=None)
def _bestand() -> tuple[NDArray, NDArray, NDArray]:
    """(area [m^2], current AGB+BGB carbon [Mg C/ha], potential [Mg C/ha]) of the woody land today per cell
    (Walker et al. 2022, NCS categories MM and M; scripts/prepare_bestand.py)."""
    d = np.load(BESTAND)
    return (d["area_m2"].astype(float), d["current_mgc_ha"].astype(float), d["potential_mgc_ha"].astype(float))


def felling_cells() -> NDArray:
    """Cells of today's forest where forest warms: the deck's own rule (the cell's typical forest does not cool by
    T_END, cooling_cells with Walker's potential carbon), applied to the woody land of Walker's MM and M categories."""
    from nbs.forest_data import key_grid

    area, _, pot = _bestand()
    has_key = key_grid(all_cells=True) != None  # noqa: E711
    m = (area > 0) & (pot > 0) & has_key
    return m & ~cooling_cells(np.where(m, area, 0.0), pot)


def felling_forcing_split(start: int = T_START, forgone: bool = True) -> tuple[NDArray, NDArray, NDArray, float, float]:
    """The warming existing forest (felling_cells) cut at once in *start*, the land kept open, all biomass buried
    (no CO2 back to the air). Returns (forgone uptake [Gt CO2/a, >= 0: the sink the stand would still have had],
    zeros for the release, albedo forcing [W/m^2, < 0: the open land is brighter], area [Gha], buried carbon [Gt C]).

    Forgone uptake: each stand is placed on its forest key's growth curve (stock scaled to the cell's potential, as
    the site factor does) at the age where it holds today's carbon; the uptake it would have had from that age on is
    lost. The albedo: the full-canopy forcing of that forest type there, with the opposite sign."""
    from nbs.forest_data import key_grid

    area, cur, pot = _bestand()
    keys = key_grid(all_cells=True)
    cut = felling_cells()
    f = _site_factor(keys, pot)
    i0 = start - int(YEARS[0])
    n_left = N_Y - i0
    up_lost, rf, a_sum, c_sum = np.zeros(N_Y), np.zeros(N_Y), 0.0, 0.0
    for key in SPECIES:
        m = (keys == key) & cut & (f > 0)
        if not m.any():
            continue
        sp = get_species(key)
        n_trees = area[m] / sp.stand_area_m2
        rf[i0:] += TAU_ATM * sp.stand_area_m2 / A_EARTH_M2 * float((n_trees * np.nan_to_num(light_product(key)[m])).sum())
        a_sum += float(area[m].sum()) / 1e13
        c_sum += float((area[m] * cur[m]).sum()) / 1e4 / 1e9
        if forgone:
            up, _, st = _trajectory(key, int(YEARS[0]))
            s_ref = np.maximum.accumulate(st)
            c_tree = cur[m] * 1000.0 * sp.stand_area_m2 / 1e4       # kg C per tree today
            a0 = np.searchsorted(s_ref, c_tree / f[m])               # age that holds today's stock
            idx = np.minimum(a0[:, None] + np.arange(n_left)[None, :], N_Y - 1)
            up_cells = np.maximum(up[idx], 0.0) * (f[m] * n_trees)[:, None]
            up_lost[i0:] += M_CO2_PER_C * up_cells.sum(axis=0) / 1e12
    return up_lost, np.zeros(N_Y), rf, a_sum, c_sum


def _fair(nee: NDArray, rf: NDArray) -> NDArray:
    base = run_fair_baseline(SZENARIO)
    d = run_fair_perturbed(nee[: len(base)], rf[: len(base)], SZENARIO) - base
    out = np.append(d, d[-1])[:N_Y]
    out.setflags(write=False)
    return out


@lru_cache(maxsize=None)
def delta_t_felling(start: int = T_START, forgone: bool = True) -> NDArray:
    """Global temperature change [K] of felling the warming existing forest (felling_forcing_split), one FaIR run."""
    up, _, rf, _, _ = felling_forcing_split(start, forgone)
    return _fair(up, rf)


@lru_cache(maxsize=None)
def delta_t_felling_parts(start: int = T_START) -> dict[str, NDArray]:
    """delta_t_felling by cause, each its own FaIR run: the forgone sink and the albedo."""
    up, _, rf, _, _ = felling_forcing_split(start)
    z = np.zeros(N_Y)
    return {"co2_entgangen": _fair(up, z), "albedo": _fair(z, rf)}
