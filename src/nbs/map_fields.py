"""The values behind the deck's maps, and the colour scales they are drawn with.

The matplotlib maps (b5, b8a, b8, v1, d1, d4) bake their colours into
images. The HTML deck draws the same maps itself, as hexagon tiles with
hover values, so it needs the numbers: per cell the value or the category,
plus the masks that give the grey background. Every function here uses the
same model functions and the same aggregation (0.5 deg cells, 2 deg blocks)
as the figure it stands for.

SCALES and CATEGORIES are the deck's map palettes: warm earth tones on the
cream slide, one hue family per quantity, diverging scales where a value has
a natural middle. They are validated for contrast against the slide
(#f2ede2) and kept apart from the two site colours (Aachen blue, Joensuu
magenta), so the sites never disappear into the field.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.constants import T_START

# --------------------------------------------------------------------------
# palettes
# --------------------------------------------------------------------------

SCALES = {
    # sunlight at the ground [W/m^2]: pale straw -> amber -> umber
    "sonne": {"stops": ["#f5ebc4", "#ebc766", "#d9952b", "#a95d18", "#5e3110"], "domain": [90, 260], "unit": "W/m²"},
    # how much darker forest is than open land [pp albedo]: mist -> glacier blue -> night
    "abdunkeln": {"stops": ["#e4ecf0", "#a6c3d8", "#5c8fbb", "#2c5b8e", "#122f55"], "domain": [0, 18], "unit": "%"},
    # extra reflection of the extra clouds over forest [pp albedo]: diverging at 0, fewer clouds = the albedo
    # orange family (darker, warming), more clouds = the deck's cloud blue (brighter, cooling)
    "wolken": {"stops": ["#86420a", "#d07a30", "#ebc39a", "#ece7d8", "#a9cbdc", "#4f8fb0", "#1d4e6a"],
               "domain": [-1.5, 3], "mid": 0, "unit": "%"},
    # extra absorbed light per tree [W]: straw -> orange -> brick -> wine (wide hue walk so 40 vs 60 W reads)
    "licht": {"stops": ["#f6e3b4", "#efb35d", "#dc7330", "#b33b2a", "#7a1c3a", "#3e1032"], "domain": [0, 100], "unit": "W"},
    # electricity per t CO2 [MWh]: diverging around the median, cheap = teal, costly = umber
    "strom": {"stops": ["#0f5c63", "#58a7a3", "#eae5d6", "#d9a55a", "#8e4d16"], "domain": [1.1, 1.9], "mid": 1.5,
              "unit": "MWh/t"},
    # reforestable share of the land [%]: sand -> sage -> forest
    # (square-root scale: in half the blocks under 3 % of the land is free, a linear scale would leave them white)
    "flaeche": {"stops": ["#ece6d3", "#c9d6a4", "#8db36c", "#4c8547", "#1f5532"], "domain": [0, 50], "gamma": 0.5,
                "unit": "%"},
    # temperature effect of one tree in 2100 [10^-15 K]: diverging at 0, cooling = the CO2 green family,
    # warming = the albedo orange family (the same pair as "kühlt/wärmt" in the Vergleich chapter)
    "baumwirkung": {"stops": ["#14532d", "#3f8a55", "#a9cf9a", "#ece7d8", "#efb98a", "#d0632a", "#7d2e10"],
                    "domain": [-90, 45], "mid": 0, "unit": "·10⁻¹⁵ K"},
    # what reforesting all free area of a block brings in 2100, per land area: same diverging palette
    "lohnt": {"stops": ["#14532d", "#3f8a55", "#a9cf9a", "#ece7d8", "#efb98a", "#d0632a", "#7d2e10"],
              "domain": [-12, 8], "mid": 0, "unit": "µK je Mha"},
    # year from which DAC beats the tree: diverging around 2037, early = deep teal, late = ochre
    "umstieg": {"stops": ["#0d4f57", "#3f9a96", "#e7e0cc", "#d8a24f", "#94591a"], "domain": [T_START, 2050],
                "mid": 2037.5, "unit": ""},
    # DAC: share of a removed tonne that is left net of the plant's own emissions [%]; diverging at 0,
    # net emitting = brick, net removing = the DAC teal family
    "dac_netto": {"stops": ["#7d2e10", "#c4612c", "#ebb88c", "#ece7d8", "#9ccfc6", "#3f9a96", "#0d4f57"],
                  "domain": [-50, 100], "mid": 0, "unit": "%"},
}
DAC_SCHWELLE = 0.8  # d5: DAC counts as "worth it" from this net share on; set before looking at the map

LAND = "#ddd6c7"         # land without the quantity (grey earth)
OUTSIDE = "#ece6d9"      # land outside the range on the Europe maps
UNMEASURED = "#d3ccbc"   # in range, no local measurement
COLD = "#45535f"         # hatching: too cold for sorbent DAC
TOO_COLD = "#bdb5a5"     # d1: too cold for sorbent DAC
NEITHER = "#7b6e62"      # d0/d4: neither the tree nor DAC cools (warm taupe, apart from the fjord blue)

CATEGORIES = {
    "waldtyp": [  # Hasler et al. 2024 types, ordered like the legend
        {"key": "dbf", "label": "Sommergrüner Laubwald", "color": "#9fae3f"},
        {"key": "enf", "label": "Immergrüner Nadelwald", "color": "#1e5b57"},
        {"key": "ebf", "label": "Immergrüner Laubwald", "color": "#3d8a42"},
        {"key": "dnf", "label": "Lärchenwald", "color": "#cf9536"},
        {"key": "mf", "label": "Mischwald", "color": "#8a5596"},
    ],
    "wirkung": [
        {"key": "kuehlt", "label": "Baum kühlt", "color": "#2f7d4f"},
        {"key": "waermt", "label": "Baum möglich, wärmt aber (Albedo)", "color": "#d0632a"},
    ],
    "machbar": [  # who can go where (d0)
        {"key": "beides", "label": "beides: Baum kühlt, DAC geht", "color": "#1e536d"},
        {"key": "baum", "label": "nur Baum: für DAC zu kalt", "color": "#5a8f2e"},
        {"key": "dac", "label": "nur DAC: Baum wärmt", "color": "#2f9c98"},
        {"key": "keins", "label": "keins: Baum wärmt, für DAC zu kalt", "color": NEITHER},
        {"key": "dac_frei", "label": "nur DAC: kein Platz für Bäume", "color": "#a9d2cd"},
    ],
    "umstieg": [
        {"key": "baum", "label": "Baum bleibt besser (Pflanzung bis 2070)", "color": "#5a8f2e"},
        {"key": "andere", "label": "nur eins von beiden oder keins (vorige Karte)", "color": "#cfc7b6"},
    ],
}

def scale_t(sc: dict, v):
    """Position 0..1 on a scale (diverging scales put `mid` at 0.5; `gamma` bends a sequential one)."""
    lo, hi = sc["domain"]
    v = np.asarray(v, dtype=float)
    if "mid" in sc:
        m = sc["mid"]
        t = np.where(v < m, 0.5 * (v - lo) / (m - lo), 0.5 + 0.5 * (v - m) / (hi - m))
    else:
        t = (v - lo) / (hi - lo)
    t = np.clip(t, 0.0, 1.0)
    return t ** sc["gamma"] if "gamma" in sc else t


def scale_cmap(sc: dict):
    """The scale as a matplotlib colormap on 0..1 (use with scale_t / scale_norm)."""
    import matplotlib.colors as mcolors

    return mcolors.LinearSegmentedColormap.from_list("deck", sc["stops"])


def scale_norm(sc: dict):
    """A matplotlib norm that maps values to scale_t (for colour bars)."""
    import matplotlib.colors as mcolors

    lo, hi = sc["domain"]
    return mcolors.FuncNorm((lambda v: scale_t(sc, v), lambda t: _inverse_t(sc, t)), vmin=lo, vmax=hi)


def _inverse_t(sc: dict, t):
    lo, hi = sc["domain"]
    t = np.asarray(t, dtype=float)
    if "gamma" in sc:
        t = np.clip(t, 0, 1) ** (1 / sc["gamma"])
    if "mid" in sc:
        m = sc["mid"]
        return np.where(t < 0.5, lo + t / 0.5 * (m - lo), m + (t - 0.5) / 0.5 * (hi - m))
    return lo + t * (hi - lo)


# --------------------------------------------------------------------------
# encoding
# --------------------------------------------------------------------------


def _grid(d: float) -> dict:
    return {"lon0": -180.0, "lat0": 90.0, "d": d, "nx": int(round(360 / d)), "ny": int(round(180 / d))}


def _mask(m: NDArray) -> list[list[int]]:
    r, c = np.nonzero(m)
    return [[int(a), int(b)] for a, b in zip(r, c)]


def _num(field: NDArray, keep: NDArray, nd: int = 2) -> list[list]:
    r, c = np.nonzero(keep & np.isfinite(field))
    return [[int(a), int(b), round(float(field[a, b]), nd)] for a, b in zip(r, c)]


def _cat(code: NDArray, share: NDArray | None = None) -> list[list]:
    r, c = np.nonzero(code >= 0)
    if share is None:
        return [[int(a), int(b), int(code[a, b])] for a, b in zip(r, c)]
    return [[int(a), int(b), int(code[a, b]), round(float(share[a, b]), 2)] for a, b in zip(r, c)]


# --------------------------------------------------------------------------
# the maps
# --------------------------------------------------------------------------

MIN_LAND_CELLS = 3
"""A 2 deg block is drawn only if at least this many of its 16 half-degree cells
are land. Single land cells are either spurious (the CRU land mask has a few
isolated cells in open sea, e.g. 1.75 E / 65.75 N) or atolls, and would show up
as a full 2 deg tile. Display only: every area total is summed from the cells."""


def _keep_blocks(land_cells: NDArray) -> NDArray:
    from nbs.dac_figures import BLOCK

    n, m = land_cells.shape[0] // BLOCK, land_cells.shape[1] // BLOCK
    return land_cells.astype(int).reshape(n, BLOCK, m, BLOCK).sum(axis=(1, 3)) >= MIN_LAND_CELLS


def _only(cells: list, keep: NDArray) -> list:
    return [c for c in cells if keep[c[0], c[1]]]


def forest_types() -> dict:
    """b5: typical forest type per 2 deg block, intensity = reforestable share (full from 30 %)."""
    from nbs.dac_climate import climate_grid
    from nbs.dac_figures import BLOCK
    from nbs.forest_data import TYPES, reforestable_area_m2, typical_type
    from nbs.grid import cell_area_m2

    keys = [c["key"] for c in CATEGORIES["waldtyp"]]
    order = [k for k in keys if k in TYPES]
    assert len(order) == len(TYPES), (order, TYPES)
    typ = typical_type()
    w = np.where(typ != None, reforestable_area_m2(), 0.0)  # noqa: E711
    n, m = w.shape[0] // BLOCK, w.shape[1] // BLOCK

    def blk(a):
        return a.reshape(n, BLOCK, m, BLOCK).sum(axis=(1, 3))

    per_type = np.stack([blk(np.where(typ == t, w, 0.0)) for t in order])
    total = per_type.sum(axis=0)
    land = np.isfinite(climate_grid()["t_mean_c"]) | (w > 0)
    land_area = blk(np.where(land, cell_area_m2(), 0.0))
    share = np.clip(np.where(land_area > 0, total / np.maximum(land_area, 1.0), 0.0) / 0.30, 0.0, 1.0)
    code = np.where(total > 0, np.argmax(per_type, axis=0), -1)
    areas = [float(w[typ == t].sum() / 1e13) for t in order]
    keep = _keep_blocks(land)
    return {"panels": [{"grid": _grid(2.0), "layers": [
        {"kind": "mask", "color": LAND, "cells": _mask(keep & (code < 0)), "label": "nicht wiederbewaldbar"},
        {"kind": "cat", "cats": "waldtyp", "cells": _only(_cat(code, share), keep), "areas": areas},
    ]}]}


def _europe_masks():
    from nbs.animations import species_range_mask, typical_measured_mask
    from nbs.landscape import land_mask

    in_range = species_range_mask()
    measured = in_range & typical_measured_mask()
    return measured, in_range & ~measured, land_mask() & ~in_range


def _europe_panel(field: NDArray, scale: str) -> dict:
    measured, unmeasured, outside = _europe_masks()
    box = _europe_box()
    return {"grid": _grid(0.5), "layers": [
        {"kind": "mask", "color": OUTSIDE, "cells": _mask(outside & box)},
        {"kind": "mask", "color": UNMEASURED, "cells": _mask(unmeasured & box), "label": "wiederbewaldbar, nicht gemessen"},
        {"kind": "num", "scale": scale, "cells": _num(field, measured & box, 2)},
    ]}


def _world_panel(field: NDArray, scale: str, measured: NDArray | None = None) -> dict:
    """Light maps since a tropical site joined: the world in 1 deg blocks (the slide shows the part with the
    three sites) -- mean of the locally
    measured cells (area-weighted); grey where the block has reforestable land but no measurement."""
    from nbs.grid import cell_area_m2
    from nbs.landscape import land_mask

    from nbs.animations import species_range_mask

    if measured is None:
        measured, unmeasured, _outside = _europe_masks()
    else:
        unmeasured = species_range_mask() & ~measured
    area = cell_area_m2()
    BLOCK = 2  # 1 deg blocks: the map shows only the part with the three sites, so finer tiles fit
    n, m = field.shape[0] // BLOCK, field.shape[1] // BLOCK

    def blk(a):
        return a.reshape(n, BLOCK, m, BLOCK).sum(axis=(1, 3))

    ok = measured & np.isfinite(field)
    den = blk(np.where(ok, area, 0.0))
    mean = np.where(den > 0, blk(np.where(ok, field * area, 0.0)) / np.maximum(den, 1e-9), np.nan)
    has = den > 0
    grey = (blk(unmeasured.astype(float)) > 0) & ~has
    lm = land_mask()
    keep = lm.astype(int).reshape(n, BLOCK, m, BLOCK).sum(axis=(1, 3)) >= 2
    return {"grid": _grid(1.0), "layers": [
        {"kind": "mask", "color": LAND, "cells": _mask(keep & ~has & ~grey)},
        {"kind": "mask", "color": UNMEASURED, "cells": _mask(keep & grey), "label": "wiederbewaldbar, nicht gemessen"},
        {"kind": "num", "scale": scale, "cells": _num(mean, keep & has, 2)},
    ]}


def _europe_box() -> NDArray:
    from nbs.animations import EXTENT
    from nbs.grid import grid_lats, grid_lons

    lon0, lon1, lat0, lat1 = EXTENT
    lo, la = np.meshgrid(grid_lons(), grid_lats())
    return (lo >= lon0 - 1) & (lo <= lon1 + 1) & (la >= lat0 - 1) & (la <= lat1 + 1)


def albedo_ingredients() -> dict:
    """b8a: sunlight at the ground and how much darker the forest is, measured cells."""
    from nbs import albedo_grid
    from nbs.animations import _by_type

    q = _by_type(albedo_grid.insolation_grid)
    darker = -100.0 * _by_type(albedo_grid.delta_alpha_grid)
    return {"panels": [_world_panel(q, "sonne"), _world_panel(darker, "abdunkeln")]}


def cloud_brightening() -> dict:
    """b8c: extra reflection of the extra clouds over forest (Delta_alpha_W) [pp], cells with a local retrieval."""
    from nbs.animations import cloud_brightening_grid

    field, measured = cloud_brightening_grid()
    return {"panels": [_world_panel(field, "wolken", measured)]}


def light_ingredients() -> dict:
    """b8i: sunlight at the ground, how much darker the forest is and the cloud brightening, side by side."""
    from nbs.animations import cloud_brightening_grid

    cloud, measured = cloud_brightening_grid()
    alb = albedo_ingredients()["panels"]
    return {"panels": [*alb, _world_panel(cloud, "wolken", measured)]}


def absorbed_light() -> dict:
    """b8: extra absorbed light per full-grown tree [W], annual mean."""
    from nbs.animations import _STAND_AREA_M2, typical_light_product

    return {"panels": [_world_panel(-typical_light_product() * _STAND_AREA_M2, "licht")]}


def availability() -> dict:
    """v1: where trees cool / warm, intensity = plantable share; hatching = too cold for DAC."""
    from nbs import vergleich_figures as V

    w = V.plantable_area_m2()
    eff = V.tree_efficiency_grid(T_START)
    land = np.isfinite(V.climate_grid()["t_mean_c"]) | (w > 0)
    n, m = w.shape[0] // V.BLOCK, w.shape[1] // V.BLOCK

    def blk(a):
        return a.reshape(n, V.BLOCK, m, V.BLOCK).sum(axis=(1, 3))

    cool = blk(np.where((w > 0) & (eff > 0), w, 0.0))
    warm = blk(np.where((w > 0) & ~(eff > 0), w, 0.0))
    plant = cool + warm
    land_b = blk(land.astype(float)) > 0
    share = plant / plant.max()
    code = np.where(plant > 0, np.where(cool >= warm, 0, 1), -1)
    cold = blk(np.where(land & ~V.dac_possible(), V.cell_area_m2(), 0.0))
    land_area = blk(np.where(land, V.cell_area_m2(), 0.0))
    cold_b = land_b & (cold > 0.5 * land_area)
    areas = [float(w[(w > 0) & (eff > 0)].sum() / 1e13), float(w[(w > 0) & ~(eff > 0)].sum() / 1e13)]
    keep = _keep_blocks(land)
    return {"panels": [{"grid": _grid(2.0), "layers": [
        {"kind": "mask", "color": LAND, "cells": _mask(keep & land_b & (code < 0)), "label": "kein Platz für Bäume"},
        {"kind": "cat", "cats": "wirkung", "cells": _only(_cat(code, 0.3 + 0.7 * share), keep), "areas": areas},
    ]}]}


def dac_energy() -> dict:
    """d1: electricity per t CO2 with heat pump [MWh], 2 deg block means; grey = too cold."""
    from nbs import dac_figures as D

    e = D.energy_grid("waermepumpe")["strom"]
    blocks = D._block_mean(e, D.cell_area_m2())
    keep = _keep_blocks(np.isfinite(D.climate_grid()["t_mean_c"]))
    cold = keep & D._land_blocks() & ~np.isfinite(blocks)
    return {"panels": [{"grid": _grid(2.0), "layers": [
        {"kind": "mask", "color": TOO_COLD, "cells": _mask(cold), "label": "zu kalt für Sorbens-DAC"},
        {"kind": "num", "scale": "strom", "cells": _num(blocks, keep & np.isfinite(blocks), 3)},
    ]}]}


def feasibility() -> dict:
    """d0: who can go where, per 2 deg block. On reforestable land the tree counts if it cools
    (recommended species, planted in the start year) and DAC if it is warm enough for sorbent DAC; on the
    rest of the land only DAC can go (pale), or nothing (grey)."""
    from nbs import vergleich_figures as V
    from nbs.dac import dac_possible
    from nbs.dac_figures import _block_mode

    w = V.plantable_area_m2()
    p = w > 0
    cools = p & (V.tree_efficiency_grid(T_START) > 0)
    ok = dac_possible()
    land = np.isfinite(V.climate_grid()["t_mean_c"]) | p
    code = np.full(w.shape, -1)
    code[land] = np.where(ok[land], 4, 5)          # no room for trees: DAC only / nothing
    code[p & ~cools] = np.where(ok[p & ~cools], 2, 3)
    code[cools] = np.where(ok[cools], 0, 1)
    # weight = reforestable area where there is some, otherwise a tiny share of the land area
    blocks = _block_mode(code, np.where(p, w, 1e-3 * V.cell_area_m2()), 6)
    keep = _keep_blocks(land)
    return {"panels": [{"grid": _grid(2.0), "layers": [
        {"kind": "mask", "color": LAND, "cells": _mask(keep & (blocks == 5)), "label": "kein Platz für Bäume, für DAC zu kalt"},
        {"kind": "cat", "cats": "machbar", "cells": _only(_cat(np.where(blocks == 5, -1, blocks)), keep)},
    ]}]}


def switch_year() -> dict:
    """d4: first year DAC beats the tree, per 2 deg block (area-weighted mean), where both can go
    (slide d0); there the tree may also stay better until 2100. The rest is one shade."""
    from nbs import dac_figures as D

    sw = D.switch_year_grid()
    w = D.plantable_area_m2()
    cat = D.switch_categories(sw, w)
    yr = D._block_mean(np.where((w > 0) & np.isfinite(sw), sw, np.nan), w)
    cat_b = D._block_mode(cat, w, 3)
    land_b = D._land_blocks()
    keep = _keep_blocks(np.isfinite(D.climate_grid()["t_mean_c"]) | (w > 0))
    return {"panels": [{"grid": _grid(2.0), "layers": [
        {"kind": "mask", "color": LAND, "cells": _mask(keep & land_b & (cat_b < 0))},
        {"kind": "cat", "cats": "umstieg", "cells": _only(_cat(np.where(cat_b >= 1, cat_b - 1, -1)), keep)},
        {"kind": "num", "scale": "umstieg", "cells": _num(np.where(cat_b == 0, yr, np.nan), keep & (cat_b == 0), 1)},
    ]}]}


DAC_JAHRE = tuple(range(T_START, 2101))


def dac_year_reached(threshold: float = DAC_SCHWELLE) -> NDArray:
    """(360, 720) first year from which sorbent DAC keeps at least *threshold* of a removed tonne net
    (heat pump, electricity mix of that year, REMIND-EU SSP2-NDC); inf = not by 2100, NaN = too cold."""
    from nbs.dac import efficiency_grid

    out = np.full(efficiency_grid(T_START).shape, np.inf)
    out[~np.isfinite(efficiency_grid(T_START))] = np.nan
    for y in reversed(DAC_JAHRE):  # backwards: the last year from which on it stays above
        ok = efficiency_grid(y) >= threshold
        out[ok & ~np.isnan(out) & ((out == np.inf) | (out == y + 1))] = y
    return out


def dac_net_over_time() -> dict:
    """d5: net share of a removed tonne [%] per 2 deg block (area-weighted mean), one frame per year
    2025-2100 (electricity mix of that year); the deck plays the frames. Grey = too cold."""
    from nbs import dac_figures as D
    from nbs.dac import efficiency_grid

    area = D.cell_area_m2()
    keep = _keep_blocks(np.isfinite(D.climate_grid()["t_mean_c"]))
    frames = {y: D._block_mean(100.0 * efficiency_grid(y), area) for y in DAC_JAHRE}
    first = frames[DAC_JAHRE[0]]
    cold = keep & D._land_blocks() & ~np.isfinite(first)
    cells = _num(first, keep & np.isfinite(first), 0)
    rows = [(r, c) for r, c, _v in cells]
    return {"panels": [{"grid": _grid(2.0), "layers": [
        {"kind": "mask", "color": TOO_COLD, "cells": _mask(cold), "label": "zu kalt für Sorbens-DAC"},
        {"kind": "num", "scale": "dac_netto", "cells": cells, "years": list(DAC_JAHRE),
         "frames": [[int(round(float(frames[y][r, c]))) for r, c in rows] for y in DAC_JAHRE]},
    ]}]}


def dac_facts() -> dict:
    """Numbers for slide d5, area-weighted over the land (cells, not blocks)."""
    from nbs.dac import efficiency_grid
    from nbs.dac_climate import climate_grid
    from nbs.grid import cell_area_m2
    from nbs.vergleich_figures import PLACES, place_cell

    area = np.broadcast_to(cell_area_m2(), efficiency_grid(T_START).shape) if np.ndim(cell_area_m2()) == 2 else \
        np.broadcast_to(np.asarray(cell_area_m2())[:, None], efficiency_grid(T_START).shape)
    land = np.isfinite(climate_grid()["t_mean_c"])
    total = area[land].sum()
    e = efficiency_grid(T_START)
    ok = land & np.isfinite(e)
    order = np.argsort(e[ok])
    cum = np.cumsum(area[ok][order])
    median = float(e[ok][order][np.searchsorted(cum, cum[-1] / 2)])
    yr = dac_year_reached()
    share = lambda m: float(area[m].sum() / total)  # noqa: E731
    return {
        "schwelle": DAC_SCHWELLE,
        "zu_kalt": share(land & ~np.isfinite(e)),
        "median_start": median,
        "netto_emittierend_start": share(ok & (e < 0)),
        "unter_50_start": share(ok & (e < 0.5)),
        "erreicht": {y: share(land & (yr <= y)) for y in (T_START, 2030, 2035, 2040, 2050)},
        "nie": share(land & np.isinf(yr)),
        "orte": {p.label: {"eta_start": float(e[place_cell(p)]), "ab80": float(yr[place_cell(p)])} for p in PLACES},
    }


def _tree_dt_grid() -> NDArray:
    """(360, 720) temperature effect in 2100 of one tree of the cell's typical forest,
    planted in the start year, full model [K]; NaN without a typical forest. Same terms as
    nbs.dac_compare.tree_efficiency_grid (CO2 part + albedo part at 2100)."""
    from nbs.aggregate import _product_no_nan, co2_factor_grid
    from nbs.dac_compare import _unit_curves_planted
    from nbs.forest_data import key_grid
    from nbs.species import SPECIES

    keys = key_grid()
    out = np.full(keys.shape, np.nan)
    for key in SPECIES:
        m = keys == key
        if not m.any():
            continue
        co2, alb = _unit_curves_planted(key, T_START)
        out[m] = co2_factor_grid(key)[m] * co2 + _product_no_nan(key)[m] * alb
    return out


def _blocks_and_land():
    from nbs.dac_climate import climate_grid
    from nbs.dac_figures import BLOCK
    from nbs.forest_data import reforestable_area_m2, typical_type
    from nbs.grid import cell_area_m2

    typ = typical_type()
    w = np.where(typ != None, reforestable_area_m2(), 0.0)  # noqa: E711
    land = np.isfinite(climate_grid()["t_mean_c"]) | (w > 0)
    n, m = w.shape[0] // BLOCK, w.shape[1] // BLOCK

    def blk(a):
        return a.reshape(n, BLOCK, m, BLOCK).sum(axis=(1, 3))

    return w, land, blk, blk(np.where(land, cell_area_m2(), 0.0))


def reforestable_share() -> dict:
    """v0: reforestable share of each 2 deg block's land [%] (Walker et al. 2022, cells with a typical forest)."""
    w, land, blk, land_area = _blocks_and_land()
    share = np.where(land_area > 0, 100.0 * blk(w) / np.maximum(land_area, 1.0), np.nan)
    keep = _keep_blocks(land)
    has = keep & (blk(w) > 0)
    return {"panels": [{"grid": _grid(2.0), "layers": [
        {"kind": "mask", "color": LAND, "cells": _mask(keep & (land_area > 0) & ~has), "label": "kein Platz für Bäume"},
        {"kind": "num", "scale": "flaeche", "cells": _num(share, has, 1)},
    ]}]}


def tree_effect() -> dict:
    """k15: temperature effect in 2100 of one tree (typical forest, planted in the start year), 2 deg block mean
    weighted by reforestable area [10^-15 K]."""
    w, land, blk, land_area = _blocks_and_land()
    dt = _tree_dt_grid() * 1e15
    ok = np.isfinite(dt) & (w > 0)
    wsum = blk(np.where(ok, w, 0.0))
    mean = np.where(wsum > 0, blk(np.where(ok, dt * w, 0.0)) / np.maximum(wsum, 1e-9), np.nan)
    keep = _keep_blocks(land)
    has = keep & (wsum > 0)
    return {"panels": [{"grid": _grid(2.0), "layers": [
        {"kind": "mask", "color": LAND, "cells": _mask(keep & (land_area > 0) & ~has), "label": "kein Platz für Bäume"},
        {"kind": "num", "scale": "baumwirkung", "cells": _num(mean, has, 1)},
    ]}]}


def total_effect() -> dict:
    """k16: temperature effect in 2100 of reforesting all free area of a 2 deg block (typical forest, planted in the
    start year): per-tree effect x trees on the reforestable area, summed over the block, per block land area
    [µK per Mha of land]. Where reforestation pays most: the tree cools and there is space."""
    from nbs.forest_data import key_grid
    from nbs.species import SPECIES, get_species
    w, land, blk, land_area = _blocks_and_land()
    dt = _tree_dt_grid()
    keys = key_grid()
    trees = np.zeros_like(dt)
    for key in SPECIES:
        m = keys == key
        trees[m] = w[m] / get_species(key).stand_area_m2
    ok = np.isfinite(dt) & (w > 0)
    tot = blk(np.where(ok, dt * trees, 0.0))
    per = np.where(land_area > 0, tot * 1e6 / np.maximum(land_area, 1.0) * 1e10, np.nan)
    keep = _keep_blocks(land)
    has = keep & (blk(np.where(ok, w, 0.0)) > 0)
    return {"panels": [{"grid": _grid(2.0), "layers": [
        {"kind": "mask", "color": LAND, "cells": _mask(keep & (land_area > 0) & ~has), "label": "kein Platz für Bäume"},
        {"kind": "num", "scale": "lohnt", "cells": _num(per, has, 2)},
    ]}]}


def facts() -> dict:
    """Numbers the map slides state (from the cell data, not from the drawn blocks)."""
    from nbs.animations import SITES, site_cell
    from nbs.potential import ICE_FREE_LAND_GHA

    w, land, _blk, _la = _blocks_and_land()
    dt = _tree_dt_grid() * 1e15
    ok = np.isfinite(dt) & (w > 0)
    area = float(w.sum() / 1e13)
    return {"flaeche_gha": area, "anteil_eisfrei": area / ICE_FREE_LAND_GHA,
            "kuehlt_anteil": float(w[ok & (dt < 0)].sum() / w[ok].sum()),
            "kuehlt_gha": float(w[ok & (dt < 0)].sum() / 1e13),
            "p05": float(np.percentile(dt[ok], 5)), "p95": float(np.percentile(dt[ok], 95)),
            "orte": {s.name: float(dt[site_cell(s)]) for s in SITES}}


MAPS = {"v0": reforestable_share, "k15": tree_effect, "k16": total_effect, "b5": forest_types, "b8i": light_ingredients, "b8": absorbed_light, "v1": availability,
        "d1": dac_energy, "d0": feasibility, "d4": switch_year, "d5": dac_net_over_time}


def export() -> dict:
    """All map fields plus the palettes, JSON-ready."""
    from nbs.animations import SITES

    return {"scales": SCALES, "categories": CATEGORIES,
            "sites": [{"name": s.label, "lon": s.lon, "lat": s.lat, "color": s.color,
                       "sym": {"o": "circle", "s": "rect", "D": "diamond"}.get(s.marker, "circle")} for s in SITES],
            "maps": {k: fn() for k, fn in MAPS.items()}}
