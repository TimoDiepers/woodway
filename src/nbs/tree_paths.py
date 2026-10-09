"""Planting paths over time: the trees are planted at a stated rate, not all in the start year.

Three ways to use the reforestable land, each as one full FaIR run (removals as negative CO2 emissions,
albedo as a forcing; the same chain as ``nbs.potential.fair_global_delta_t``):

- ``"alle"``: every reforestable cell with a typical forest (0.83 Gha), left to grow.
- ``"kuehlt"``: only the cells whose tree still cools at the horizon (the area slide's main case), left to grow.
- ``"forst"``: the cooling cells as managed forest: clear-cut at a rotation age by climate zone (boreal 80,
  temperate 60, subtropical 30, tropical 20 years) and replanted. The stem (70 % of the stand's carbon)
  leaves the forest as timber and stays bound -- the optimistic case; the residues go back to the air at
  felling. ``release=True`` sends the timber back to the air too (the comparison case).

Planting rate: the Bonn Challenge pace, 350 Mha restored 2011-2030, i.e. 17.5 Mha a year. Every cell of a
path gets the same share each year, so a path is the start-year planting spread over its years.

Approximations, stated: each cohort grows with the trajectory of its own planting year (calendar-dependent
disturbance hazard); later rotations reuse that trajectory shifted by the rotation age.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.typing import NDArray

from nbs.aggregate import co2_factor_grid
from nbs.albedo_grid import alpha_q_product
from nbs.config import ModelConfig
from nbs.constants import A_EARTH_M2, M_CO2_PER_C, T_START, TAU_ATM, YEARS
from nbs.fair_module import run_fair_baseline, run_fair_perturbed
from nbs.landscape import assign_species, plantable_area_m2, tree_count
from nbs.species import SPECIES, get_species, reference_site

BONN_RATE_GHA = 0.35 / 20.0     # Bonn Challenge: 350 Mha restored 2011-2030 [Gha/a]
# managed forest: clear-cut at a rotation age by climate zone (the zone is the suffix of the forest-type key)
ROTATION_BY_ZONE = {"boreal": 80, "gemaessigt": 60, "subtropisch": 30, "tropisch": 20}  # [a]
STEM_SHARE = 0.7                # share of the stand's carbon that leaves as timber; the residues decay
PATHS = ("alle", "kuehlt", "forst")
N_Y = len(YEARS)


def masks() -> dict[str, NDArray]:
    """Cells of each path: every reforestable cell, and the cells that cool by the horizon."""
    from nbs.map_plots import _breakeven_year_field

    plant = assign_species() != None  # noqa: E711
    cool = plant & ~np.isinf(_breakeven_year_field("ssp245"))
    return {"alle": plant, "kuehlt": cool}


def schedule(area_gha: float, start: int = T_START, rate_gha: float | None = BONN_RATE_GHA) -> NDArray:
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
    tr = simulate_deterministic(sp, _background_temperature("ssp245"), plant_year=plant_year)
    out = tuple(np.asarray(a, dtype=float) for a in (tr.net_uptake_kgC_yr, tr.closure, tr.stock_kgC))
    for a in out:
        a.setflags(write=False)
    return out


def _cells(key: str, mask: NDArray) -> tuple[float, float, float]:
    """Sums over the cells of *key* in *mask*: (trees x co2 site factor, trees x albedo product, area [Gha])."""
    m = (assign_species() == key) & mask
    n = tree_count()[m]
    return (float((n * co2_factor_grid(key)[m]).sum()), float((n * np.nan_to_num(alpha_q_product(key)[m])).sum()),
            float(plantable_area_m2()[m].sum()) / 1e13)


def forcing(path: str, start: int = T_START, rate_gha: float | None = BONN_RATE_GHA,
            release: bool = False) -> tuple[NDArray, NDArray, float]:
    """(net CO2 exchange [Gt CO2/a, < 0 = removal], albedo forcing [W/m^2], planted area [Gha]) of a path."""
    if path not in PATHS:
        raise ValueError(f"unknown path {path!r}")
    mask = masks()["alle" if path == "alle" else "kuehlt"]
    sums = {key: _cells(key, mask) for key in SPECIES}
    sums = {k: v for k, v in sums.items() if v[2] > 0}
    area = sum(v[2] for v in sums.values())
    f = schedule(area, start, rate_gha)
    nee, rf = np.zeros(N_Y), np.zeros(N_Y)
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
                    nee[span.stop] += share * M_CO2_PER_C * st[src.stop - 1] * n_sum * w / 1e12
    return nee, rf, area


@lru_cache(maxsize=None)
def delta_t(path: str, start: int = T_START, rate_gha: float | None = BONN_RATE_GHA, release: bool = False) -> NDArray:
    """Global temperature change [K] of a path, one full FaIR run (SSP2-4.5 background)."""
    nee, rf, _ = forcing(path, start, rate_gha, release)
    base = run_fair_baseline("ssp245")
    pert = run_fair_perturbed(nee[: len(base)], rf[: len(base)], "ssp245")
    out = np.append(pert - base, (pert - base)[-1])[:N_Y]
    out.setflags(write=False)
    return out
