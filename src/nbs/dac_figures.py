"""Figures and clips for the DAC slides (Vergleich chapter).

Maps use the same 2-degree blocks as the planting map (nbs.map_plots.plot_planting_map):
a block shows the area-weighted mean of a field, or the option that wins on
most of its plantable area.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FuncAnimation  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

from nbs.animations import FIG_DPI, _writer  # noqa: E402
from nbs.borders import add_borders  # noqa: E402
from nbs.constants import T_START  # noqa: E402
from nbs.dac import dac_possible, efficiency_grid, energy_grid  # noqa: E402
from nbs.dac_climate import climate_grid  # noqa: E402
from nbs.dac_compare import OPTIONS, best_option_grid, tree_efficiency_grid  # noqa: E402
from nbs.grid import cell_area_m2  # noqa: E402
from nbs.landscape import plantable_area_m2  # noqa: E402
from nbs.map_plots import _COLOR_LAND, _COLOR_NEVER, _SPECIES_COLORS  # noqa: E402
from nbs.species import SPECIES, get_species  # noqa: E402

C_DAC = "#01a8a8"  # checked against all species colours and _COLOR_NEVER (CVD Delta E >= 8.4)
C_BG = "#f3eee6"
C_INK = "#2b2b2b"
C_MUTED = "#6b6b6b"
BLOCK = 4  # 0.5 deg cells per 2 deg block
EXTENT = (-180, 180, -60, 84)
# decision years for the time comparison: the tree planted then still grows at least 30 years
# before the horizon (T_END = 2100); later cohorts would look good only because they are young
LAST_PLANT_YEAR = 2070
YEARS_CLIP = tuple(range(T_START, LAST_PLANT_YEAR + 1))


def _setup() -> None:
    from nbs.animations import _register_fonts

    _heading, body = _register_fonts()   # Arial like every other figure of the deck, so layouts match the HTML
    plt.rcParams.update({"font.family": body, "font.size": 13, "axes.edgecolor": C_MUTED,
                         "figure.facecolor": C_BG, "axes.facecolor": C_BG, "savefig.facecolor": C_BG})


def _save(fig, path: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)
    return path


def _map_axes(ax) -> None:
    ax.set_xlim(EXTENT[0], EXTENT[1])
    ax.set_ylim(EXTENT[2], EXTENT[3])
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    add_borders(ax, linewidth=0.3)


def _block_mean(field: NDArray, weight: NDArray) -> NDArray:
    n, m = field.shape[0] // BLOCK, field.shape[1] // BLOCK
    f = np.where(np.isfinite(field), field, 0.0).reshape(n, BLOCK, m, BLOCK)
    w = np.where(np.isfinite(field), weight, 0.0).reshape(n, BLOCK, m, BLOCK)
    tot = w.sum(axis=(1, 3))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(tot > 0, (f * w).sum(axis=(1, 3)) / tot, np.nan)


def _block_mode(cat: NDArray, weight: NDArray, n_cat: int) -> NDArray:
    """Category with the most weight per block; -1 where the block has none."""
    n, m = cat.shape[0] // BLOCK, cat.shape[1] // BLOCK
    c = cat.reshape(n, BLOCK, m, BLOCK)
    w = weight.reshape(n, BLOCK, m, BLOCK)
    sums = np.stack([np.where(c == k, w, 0.0).sum(axis=(1, 3)) for k in range(n_cat)])
    out = np.argmax(sums, axis=0)
    out[sums.sum(axis=0) <= 0] = -1
    return out


def _land_blocks() -> NDArray:
    land = np.isfinite(climate_grid()["t_mean_c"]).astype(float)
    return _block_mean(np.where(land > 0, 1.0, np.nan), cell_area_m2()) > 0


# --------------------------------------------------------------------------
# 1  DAC alone: energy demand from the climate
# --------------------------------------------------------------------------


def energy_map_figure(out_path: str) -> str:
    _setup()
    e = energy_grid("waermepumpe")["strom"]
    blocks = _block_mean(e, cell_area_m2())
    cold = _land_blocks() & ~np.isfinite(blocks)
    # world map at full width, colour bar and legend underneath
    fig, ax = plt.subplots(figsize=(12.0, 4.7), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.005, right=0.995, bottom=0.2, top=0.995)
    rgba = np.zeros(blocks.shape + (4,))
    rgba[cold] = mcolors.to_rgba("#d9d4cb")
    ax.imshow(rgba, extent=(-180, 180, -90, 90), origin="upper", interpolation="nearest")
    cmap = mcolors.LinearSegmentedColormap.from_list("e", ["#e3f2f1", "#7cc9c6", "#01a8a8", "#016b6b", "#013d3d"])
    im = ax.imshow(np.ma.masked_invalid(blocks), extent=(-180, 180, -90, 90), origin="upper", cmap=cmap,
                   vmin=1.1, vmax=1.9, interpolation="nearest")
    _map_axes(ax)
    from nbs import map_fields as M
    from nbs.vergleich_figures import de_num, map_site_value, world_site_labels

    data = M.MAPS["d1"]()
    world_site_labels(ax, lambda s: None if (v := map_site_value(data, s)) is None else f"{de_num(v, 2)} MWh/t")
    cax = fig.add_axes([0.33, 0.045, 0.34, 0.025])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal")
    cb.set_label("Strom je t CO$_2$ [MWh], Wärmepumpe eingerechnet", fontsize=11)
    cb.ax.xaxis.set_label_position("top")
    fig.legend(handles=[Patch(facecolor="#d9d4cb", label="zu kalt für Sorbens-DAC")], loc="lower left",
               bbox_to_anchor=(0.72, 0.01), frameon=False, fontsize=11)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# 2  DAC over time: net efficiency as the grid decarbonises
# --------------------------------------------------------------------------

_EFF_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "eff", ["#b2182b", "#f4a582", "#f7f7f7", "#7cc9c6", "#01a8a8", "#014f4f"])
_EFF_NORM = mcolors.TwoSlopeNorm(vmin=-0.5, vcenter=0.0, vmax=1.0)


def _draw_eff(ax, year: int, variant: str = "waermepumpe"):
    blocks = _block_mean(efficiency_grid(year, variant), cell_area_m2())
    cold = _land_blocks() & ~np.isfinite(blocks)
    rgba = np.zeros(blocks.shape + (4,))
    rgba[cold] = mcolors.to_rgba("#d9d4cb")
    ax.imshow(rgba, extent=(-180, 180, -90, 90), origin="upper", interpolation="nearest")
    im = ax.imshow(np.ma.masked_invalid(blocks), extent=(-180, 180, -90, 90), origin="upper", cmap=_EFF_CMAP,
                   norm=_EFF_NORM, interpolation="nearest")
    _map_axes(ax)
    return im


def dac_efficiency_multiples_figure(out_path: str, years=(T_START, 2030, 2040, 2050)) -> str:
    _setup()
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 5.6), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.01, right=0.88, bottom=0.02, top=0.95, wspace=0.03, hspace=0.12)
    for ax, y in zip(axes.ravel(), years):
        im = _draw_eff(ax, y)
        ax.set_title(str(y), loc="left", fontsize=15, color=C_INK, fontweight="bold")
    cax = fig.add_axes([0.9, 0.15, 0.015, 0.7])
    cb = fig.colorbar(im, cax=cax, ticks=[-0.5, 0, 0.5, 0.9, 1.0])
    cb.ax.set_yticklabels(["−50 %", "0 %", "50 %", "90 %", "100 %"])
    cb.set_label("Netto-Wirkungsgrad DAC")
    return _save(fig, out_path)


def dac_efficiency_clip(out_path: str, fps: int = 8) -> str:
    _setup()
    fig, ax = plt.subplots(figsize=(12.0, 5.12), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.01, right=0.88, bottom=0.03, top=0.93)
    cax = fig.add_axes([0.9, 0.2, 0.015, 0.6])
    title = fig.text(0.02, 0.95, "", fontsize=18, fontweight="bold", color=C_INK, va="top")
    frames = list(YEARS_CLIP) + [YEARS_CLIP[-1]] * fps * 2

    def draw(k):
        ax.clear()
        im = _draw_eff(ax, frames[k])
        if k == 0:
            cb = fig.colorbar(im, cax=cax, ticks=[-0.5, 0, 0.5, 0.9, 1.0])
            cb.ax.set_yticklabels(["−50 %", "0 %", "50 %", "90 %", "100 %"])
            cb.set_label("Netto-Wirkungsgrad DAC")
        title.set_text(str(frames[k]))

    FuncAnimation(fig, draw, frames=len(frames), blit=False).save(out_path, writer=_writer(fps), dpi=100)  # 1200x510: even sizes for H.264
    plt.close(fig)
    return out_path


# --------------------------------------------------------------------------
# 3  Trees or DAC: the better option per block and year
# --------------------------------------------------------------------------

_CATS = ["nichts kühlt"] + list(OPTIONS)  # index = best_option_grid code


def _cat_color(k: int) -> str:
    if k == 0:
        return _COLOR_NEVER
    key = OPTIONS[k - 1]
    return C_DAC if key == "dac" else _SPECIES_COLORS[key]


def _draw_best(ax, year: int, variant: str = "waermepumpe"):
    code = best_option_grid(year, variant)
    w = plantable_area_m2()
    blocks = _block_mode(np.where(w > 0, code, -1), w, len(_CATS))
    rgba = np.zeros(blocks.shape + (4,))
    rgba[_land_blocks()] = mcolors.to_rgba(_COLOR_LAND)
    for k in range(len(_CATS)):
        rgba[blocks == k] = mcolors.to_rgba(_cat_color(k))
    ax.imshow(rgba, extent=(-180, 180, -90, 90), origin="upper", interpolation="nearest")
    _map_axes(ax)


def _legend_handles():
    keys = [k for k in SPECIES if k != "ebf_subtropisch"]  # never recommended (slide "Wo ist Platz")
    hs = [Patch(facecolor=C_DAC, label="DAC")]
    hs += [Patch(facecolor=_SPECIES_COLORS[k], label=get_species(k).name_de) for k in keys]
    hs += [Patch(facecolor=_COLOR_NEVER, label="keins kühlt"),
           Patch(facecolor=_COLOR_LAND, label="keine Fläche für Bäume")]
    return hs


def best_option_multiples_figure(out_path: str, years=(T_START, 2030, 2040, 2050)) -> str:
    _setup()
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 5.6), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.01, right=0.76, bottom=0.02, top=0.95, wspace=0.03, hspace=0.12)
    for ax, y in zip(axes.ravel(), years):
        _draw_best(ax, y)
        ax.set_title(str(y), loc="left", fontsize=15, color=C_INK, fontweight="bold")
    fig.legend(handles=_legend_handles(), loc="center left", bbox_to_anchor=(0.765, 0.5), frameon=False,
               fontsize=12)
    return _save(fig, out_path)


def best_option_clip(out_path: str, fps: int = 8) -> str:
    """Map only; the legend is a separate image (``legend_figure``) on the slide."""
    _setup()
    fig, ax = plt.subplots(figsize=(12.0, 5.12), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
    title = fig.text(0.015, 0.97, "", fontsize=20, fontweight="bold", color=C_INK, va="top")
    frames = list(YEARS_CLIP) + [YEARS_CLIP[-1]] * fps * 2

    def draw(k):
        ax.clear()
        _draw_best(ax, frames[k])
        title.set_text(str(frames[k]))

    FuncAnimation(fig, draw, frames=len(frames), blit=False).save(out_path, writer=_writer(fps), dpi=100)  # even sizes for H.264
    plt.close(fig)
    return out_path


def legend_figure(out_path: str) -> str:
    """The best-option legend on its own, to sit next to the clip on the slide."""
    _setup()
    fig = plt.figure(figsize=(3.4, 3.0), dpi=FIG_DPI)
    fig.legend(handles=_legend_handles(), loc="center left", frameon=False, fontsize=12)
    return _save(fig, out_path)


def switch_year_grid(variant: str = "waermepumpe") -> NDArray:
    """First decision year (2025-2070) from which DAC beats the tree planted that year on a
    plantable cell; inf where it never does in that window."""
    w = plantable_area_m2()
    out = np.full(w.shape, np.inf)
    for y in YEARS_CLIP:
        tree = tree_efficiency_grid(y - (y - YEARS_CLIP[0]) % 5)
        dac = efficiency_grid(y, variant)
        win = (w > 0) & np.isfinite(dac) & (dac > np.where(np.isfinite(tree), tree, -np.inf)) & np.isinf(out)
        out[win] = y
    return out


def area_shares(variant: str = "waermepumpe") -> dict[str, NDArray]:
    """Share of the plantable area per best option, per year in YEARS_CLIP."""
    w = plantable_area_m2()
    tot = w.sum()
    res = {c: [] for c in _CATS}
    for y in YEARS_CLIP:
        code = best_option_grid(y, variant)
        for k, c in enumerate(_CATS):
            res[c].append(float(w[code == k].sum() / tot))
    return {c: np.array(v) for c, v in res.items()}


def switch_categories(sw: NDArray, w: NDArray) -> NDArray:
    """Per plantable cell: 0 = both can go there (the tree planted 2025 cools, warm enough for
    sorbent DAC) and DAC overtakes the tree by 2100 (year in *sw*), 1 = both can go there and the
    tree stays better, 2 = only one of them or neither (slide "Wer wo entnehmen kann"); -1 = no area."""
    both = (w > 0) & (tree_efficiency_grid(T_START) > 0) & dac_possible()
    cat = np.full(w.shape, -1)
    cat[w > 0] = 2
    cat[both & np.isfinite(sw)] = 0
    cat[both & np.isinf(sw)] = 1
    return cat


def switch_year_figure(out_path: str) -> str:
    from nbs.map_fields import CATEGORIES, NEITHER

    _setup()
    sw = switch_year_grid()
    w = plantable_area_m2()
    c_tree, c_none = (c["color"] for c in CATEGORIES["umstieg"])
    # the map takes most of the width; colour bar and legend underneath it
    fig, (ax, ax_s) = plt.subplots(1, 2, figsize=(12.0, 4.7), dpi=FIG_DPI, gridspec_kw={"width_ratios": [3.6, 1.0]})
    fig.subplots_adjust(left=0.005, right=0.975, bottom=0.2, top=0.93, wspace=0.08)

    yr_blocks = _block_mean(np.where((w > 0) & np.isfinite(sw), sw, np.nan), w)
    cat_b = _block_mode(switch_categories(sw, w), w, 3)
    rgba = np.zeros(cat_b.shape + (4,))
    rgba[_land_blocks()] = mcolors.to_rgba(_COLOR_LAND)
    rgba[cat_b == 1] = mcolors.to_rgba(c_tree)
    rgba[cat_b == 2] = mcolors.to_rgba(c_none)
    ax.imshow(rgba, extent=(-180, 180, -90, 90), origin="upper", interpolation="nearest")
    cmap = mcolors.LinearSegmentedColormap.from_list("sw", ["#014f4f", "#01a8a8", "#7cc9c6", "#e3f2f1"])
    shown = np.where(cat_b == 0, yr_blocks, np.nan)
    im = ax.imshow(np.ma.masked_invalid(shown), extent=(-180, 180, -90, 90), origin="upper", cmap=cmap,
                   vmin=T_START, vmax=2050, interpolation="nearest")
    _map_axes(ax)
    cax = fig.add_axes([0.1, 0.045, 0.3, 0.025])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal", ticks=[T_START, 2030, 2035, 2040, 2045, 2050])
    cb.set_label("ab diesem Jahr ist der Netto-Anteil von DAC höher als der des Baums", fontsize=11)
    cb.ax.xaxis.set_label_position("top")
    fig.legend(handles=[Patch(facecolor=c["color"], label=c["label"]) for c in CATEGORIES["umstieg"]],
               loc="lower left", bbox_to_anchor=(0.45, 0.0), frameon=False, fontsize=11)

    shares = area_shares()
    yrs = np.array(YEARS_CLIP)
    tree_total = sum(shares[k] for k in SPECIES)
    ax_s.stackplot(yrs, shares["dac"], tree_total, shares["nichts kühlt"],
                   colors=[C_DAC, c_tree, NEITHER], alpha=0.95)
    ax_s.set_xlim(T_START, LAST_PLANT_YEAR)
    ax_s.set_ylim(0, 1)
    ax_s.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax_s.set_yticklabels(["0", "25", "50", "75", "100 %"])
    ax_s.set_xticks([T_START, 2045, 2070])
    ax_s.set_xlabel("Jahr: Baum gepflanzt, DAC in Betrieb", fontsize=11)
    ax_s.set_title("Anteil der bepflanzbaren Fläche", loc="left", fontsize=13, color=C_INK)
    for s in ("top", "right"):
        ax_s.spines[s].set_visible(False)
    i50 = list(yrs).index(2050)
    ax_s.text(2027, shares["dac"][i50] / 2, "DAC", color="white", fontsize=13, fontweight="bold", va="center")
    ax_s.text(2027, shares["dac"][i50] + tree_total[i50] / 2, "Baum", color="white", fontsize=13, fontweight="bold",
              va="center")
    ax_s.text(2027, 1 - shares["nichts kühlt"][i50] / 2, "keins kühlt", color="white", fontsize=12, va="center")
    return _save(fig, out_path)


def dac_net_figure(out_path: str) -> str:
    """D5 layout: one world map of the net share of a removed tonne (nbs.map_fields.dac_net_over_time,
    drawn and played year by year by the deck), colour bar underneath; the first frame (2025) as reference."""
    from nbs.vergleich_figures import _world_map_skeleton, de_num

    return _world_map_skeleton(out_path, "d5", "Anteil einer entnommenen Tonne, der netto bleibt [%]",
                               [-50, 0, 25, 50, 75, 100], "zu kalt für Sorbens-DAC", lambda v: f"{de_num(v)} %")


DAC_PATHWAYS = (("SSP2-PkBudg650", "sehr optimistisch", "#0d4f57"), ("SSP2-NDC", "Mitte", "#2f9c98"),
                ("SSP2-NPi", "sehr pessimistisch", "#9ccfc6"))


def dac_pathway_medians(years=(T_START,) + tuple(range(2030, 2101, 5))) -> dict:
    """Median (area-weighted over the land where sorbent DAC is possible) of the net share per year and
    pathway, plus the share of that land where DAC is net emitting."""
    area = np.broadcast_to(np.asarray(cell_area_m2())[:, None], climate_grid()["t_mean_c"].shape) \
        if np.ndim(cell_area_m2()) == 1 else cell_area_m2()
    out = {}
    for p, _l, _c in DAC_PATHWAYS:
        med, neg = [], []
        for y in years:
            e = efficiency_grid(y, "waermepumpe", p)
            ok = np.isfinite(e)
            o = np.argsort(e[ok])
            cum = np.cumsum(area[ok][o])
            med.append(float(e[ok][o][np.searchsorted(cum, cum[-1] / 2)]))
            neg.append(float(area[ok & (e < 0)].sum() / area[ok].sum()))
        out[p] = {"jahre": list(years), "median": med, "netto_emittierend": neg}
    return out


def dac_scenarios_figure(out_path: str) -> str:
    """D6: DAC net share (median over the land where it works) 2025-2100 under three REMIND-EU pathways
    (premise), against the trees' net share on the cooling cells under the matching FaIR backgrounds."""
    from nbs.vergleich_figures import CMIP7_SHOWN, tree_scenarios

    _setup()
    d = dac_pathway_medians()
    t = tree_scenarios()
    shares = [100 * t[k]["kuehlt"]["anteil"] for k in CMIP7_SHOWN]
    fig, ax = plt.subplots(figsize=(12.0, 4.7), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.97, bottom=0.13, top=0.92)
    ax.axhspan(min(shares), max(shares), color="#cfe5c8", linewidth=0, zorder=0)
    ax.text(2052, min(shares) - 6, f"Bäume auf den kühlenden Flächen: {min(shares):.0f}–{max(shares):.0f} % netto (vier Szenarien)",
            fontsize=12, color="#1b7837", fontweight="bold")
    ax.axhline(0, color=C_MUTED, linewidth=0.9)
    for p, label, col in DAC_PATHWAYS:
        y, m = np.array(d[p]["jahre"]), 100 * np.array(d[p]["median"])
        ax.plot(y, m, color=col, linewidth=3.2, label=f"DAC {label} ({p})")
    ax.legend(loc="lower right", frameon=False, fontsize=12)
    ax.set_xlim(T_START, 2100)
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylim(min(0, min(min(d[p]["median"]) for p, _l, _c in DAC_PATHWAYS) * 100 - 5), 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25 %", "50 %", "75 %", "100 %"])
    ax.set_ylabel("Anteil der Tonne, der netto bleibt (Median)")
    ax.set_title("Strommix nach drei REMIND-EU-Pfaden (premise)", loc="left", fontsize=13, color=C_INK)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    return _save(fig, out_path)


def build_all(out_dir: str, clips: bool = True) -> list[str]:
    out = [
        energy_map_figure(os.path.join(out_dir, "d1_dac_energie.png")),
        dac_efficiency_multiples_figure(os.path.join(out_dir, "d2_dac_wirkungsgrad.png")),
        best_option_multiples_figure(os.path.join(out_dir, "d3_baum_oder_dac.png")),
        switch_year_figure(os.path.join(out_dir, "d4_ab_wann_dac.png")),
    ]
    if clips:
        out += [
            dac_efficiency_clip(os.path.join(out_dir, "d2_dac_wirkungsgrad.mp4")),
            best_option_clip(os.path.join(out_dir, "d3_baum_oder_dac.mp4")),
            legend_figure(os.path.join(out_dir, "d3_legende.png")),
        ]
    return out
