"""Figures for the Vergleich chapter: one targeted graphic per slide.

V1 where trees can go and where DAC works (one map),
V2 how much removal is needed (CMIP7, slide 2) against the trees,
V3 trees against DAC at six places with today's electricity,
V4 the same places over time as the grid decarbonises.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from nbs.animations import FIG_DPI  # noqa: E402
from nbs.config import ModelConfig  # noqa: E402
from nbs.constants import T_START  # noqa: E402
from nbs.dac import dac_possible, electricity_gwp_grid, energy_grid, rest_gwp  # noqa: E402
from nbs.dac_climate import climate_grid  # noqa: E402
from nbs.dac_compare import tree_efficiency_grid  # noqa: E402
from nbs.dac_figures import BLOCK, C_BG, C_DAC, C_INK, C_MUTED, _map_axes, _setup  # noqa: E402
from nbs.grid import cell_area_m2, grid_lats, grid_lons  # noqa: E402
from nbs.landscape import assign_species, plantable_area_m2  # noqa: E402
from nbs.map_plots import _COLOR_LAND, _SPECIES_COLORS  # noqa: E402
from nbs.species import get_species  # noqa: E402

C_TREE = "#1b7837"
C_TREE_LIGHT = "#a6d4a0"
C_WARM = "#c2672f"
C_COLD = "#9fb3c8"


def _save(fig, path: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# V1  Where trees can go, where they cool, where DAC works
# --------------------------------------------------------------------------


def availability_map_figure(out_path: str) -> str:
    """Per 2-degree block: green = trees cool (planted in the start year, typical forest),
    orange = trees possible but net warming at 2100 (albedo), grey = no room
    for trees. Saturation = plantable share of the block, as on the planting
    map. Hatched = too cold for sorbent DAC (coldest month < -15 deg C)."""
    _setup()
    w = plantable_area_m2()
    eff = tree_efficiency_grid(T_START)
    land = np.isfinite(climate_grid()["t_mean_c"]) | (w > 0)
    n, m = w.shape[0] // BLOCK, w.shape[1] // BLOCK

    def blk(a):
        return a.reshape(n, BLOCK, m, BLOCK).sum(axis=(1, 3))

    cool = blk(np.where((w > 0) & (eff > 0), w, 0.0))
    warm = blk(np.where((w > 0) & ~(eff > 0), w, 0.0))
    plant = cool + warm
    land_b = blk(land.astype(float)) > 0
    share = plant / plant.max()
    base = np.array(mcolors.to_rgb(_COLOR_LAND))
    rgba = np.zeros((n, m, 4))
    rgba[land_b] = mcolors.to_rgba(_COLOR_LAND)
    for mask, col in ((plant > 0) & (cool >= warm), C_TREE), ((plant > 0) & (warm > cool), C_WARM):
        rgb = np.array(mcolors.to_rgb(col))
        rgba[mask, :3] = base + (rgb - base) * (0.3 + 0.7 * share[mask, None])
        rgba[mask, 3] = 1.0

    cold = blk(np.where(land & ~dac_possible(), cell_area_m2(), 0.0))
    land_area = blk(np.where(land, cell_area_m2(), 0.0))
    cold_b = land_b & (cold > 0.5 * land_area)

    # world map at full width, legend in one row underneath
    fig, ax = plt.subplots(figsize=(12.0, 4.7), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.005, right=0.995, bottom=0.13, top=0.995)
    ax.imshow(rgba, extent=(-180, 180, -90, 90), origin="upper", interpolation="nearest")
    lon_e = np.linspace(-180, 180, m + 1)
    lat_e = np.linspace(90, -90, n + 1)
    # (no "too cold for DAC" hatching here: DAC is introduced later in the talk; the energy map shows it)
    _ = (lon_e, lat_e, cold_b)
    _map_axes(ax)
    a_cool = float(w[(w > 0) & (eff > 0)].sum() / 1e13)
    a_warm = float(w[(w > 0) & ~(eff > 0)].sum() / 1e13)
    handles = [
        Patch(facecolor=C_TREE, label=f"Baum kühlt ({a_cool:.2f} Gha)".replace(".", ",")),
        Patch(facecolor=C_WARM, label=f"Baum möglich, wärmt aber (Albedo, {a_warm:.2f} Gha)".replace(".", ",")),
        Patch(facecolor=_COLOR_LAND, label="kein Platz für Bäume (Wald, Acker, Stadt, …)"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=len(handles), frameon=False,
               fontsize=11.5, columnspacing=1.8, handlelength=1.3, handletextpad=0.5)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# V2  How much is needed (CMIP7, slide 2) -- and what the trees contribute
# --------------------------------------------------------------------------

# Carbon Brief (Hausfather 2026), "Explainer: The CMIP7 emissions scenarios",
# cumulative CO2 removal 2024-2100 (van Vuuren et al. 2026; FLEX extensions).
# Totals are quoted in the text; the engineered/land split is read off the
# article's bar chart (slide 2), +-10 GtCO2.
def _cmip7_removal() -> dict[str, tuple[float, float]]:
    """scenario name -> (novel CDR, land sink) [Gt CO2] 2024-2100, from the CMIP7 data of slides 2-3
    (nbs.cmip7_figures; the same 591 Gt for Very Low as there)."""
    from nbs.cmip7_figures import MARKERS, cumulative_removal

    cum = cumulative_removal()
    return {MARKERS[k][0].split(" (")[0]: (float(cum.loc[k, "neuartig_gt"]), float(cum.loc[k, "land_gt"]))
            for k in ("VL", "L", "ML")}


CMIP7_REMOVAL = _cmip7_removal()  # scenario -> (novel CDR, land sink) [GtCO2], CMIP7 data


@lru_cache(maxsize=1)
def planting_choice() -> dict[str, dict[str, float]]:
    """Where to plant: only where the tree cools by 2100 against every reforestable cell.

    Per variant: area [Gha], CO2 stored by 2100 (gross, from the cascade's carbon) and net of
    albedo [Gt CO2], and the global temperature change in 2100 [K] from one FaIR run with the
    whole planting (typical forest, planted in the start year, SSP2-4.5). Net = gross x (Delta_T full /
    Delta_T without albedo). Gross carbon: cascade steps "Nicht-Wald-Biome ausgeschlossen"
    (all reforestable cells with a typical forest) and the last step (cells that cool)."""
    import json
    from pathlib import Path

    from nbs.map_plots import _breakeven_year_field
    from nbs.potential import _masked_global_delta_t, cascade

    # four global FaIR runs take a while: cached next to the slide facts (delete to recompute)
    cache = Path(__file__).resolve().parents[2] / "docs" / "slides" / "chart_data" / "pflanzwahl.json"
    if cache.exists():
        return json.loads(cache.read_text())
    plant = assign_species() != None  # noqa: E711
    cool = plant & ~np.isinf(_breakeven_year_field("ssp245"))
    steps = cascade()
    land = next(s for s in steps if s["area_gha"] is not None)
    w = plantable_area_m2()
    out = {}
    for key, mask, carbon in (("kuehlt", cool, steps[-1]["carbon_gtc"]), ("alle", plant, land["carbon_gtc"])):
        full = float(_masked_global_delta_t(mask, "ssp245")[-1])
        co2 = float(_masked_global_delta_t(mask, "ssp245", ModelConfig(albedo=False))[-1])
        gross = carbon * 44.0 / 12.0
        out[key] = {"flaeche_gha": float(w[mask].sum() / 1e13), "brutto_gt": gross, "netto_gt": gross * full / co2,
                    "dt_2100_k": full, "dt_nur_co2_k": co2}
        print(f"planting_choice {key}: {out[key]}", flush=True)
    cache.write_text(json.dumps(out, indent=1))
    return out


def _cached_json(name: str, compute):
    import json
    from pathlib import Path

    cache = Path(__file__).resolve().parents[2] / "docs" / "slides" / "chart_data" / name
    if cache.exists():
        return json.loads(cache.read_text())
    out = compute()
    cache.write_text(json.dumps(out, indent=1))
    return out


@lru_cache(maxsize=1)
def area_series() -> dict:
    """Global temperature change [K] year by year from planting (typical forest, 2025) on the cooling
    cells and on every reforestable cell, each with and without albedo -- the same four FaIR runs as
    planting_choice, kept as time series (cached in docs/slides/chart_data/flaechen_zeitreihe.json)."""

    def compute():
        from nbs.constants import YEARS
        from nbs.map_plots import _breakeven_year_field
        from nbs.potential import _masked_global_delta_t

        plant = assign_species() != None  # noqa: E711
        cool = plant & ~np.isinf(_breakeven_year_field("ssp245"))
        out = {"jahre": [int(y) for y in YEARS]}
        for key, mask in (("kuehlt", cool), ("alle", plant)):
            out[key] = [float(v) for v in _masked_global_delta_t(mask, "ssp245")]
            out[key + "_nur_co2"] = [float(v) for v in _masked_global_delta_t(mask, "ssp245", ModelConfig(albedo=False))]
        return out

    return _cached_json("flaechen_zeitreihe.json", compute)


@lru_cache(maxsize=1)
def planting_delay() -> dict:
    """Cooling of the cooling cells in 2050 and 2100 by planting year, relative to planting in 2025.
    Per-tree runs (typical forest per cell, full model incl. warming-dependent disturbance) summed over
    the trees of each cell; cached in docs/slides/chart_data/pflanzjahr_global.json."""

    def compute():
        from nbs.constants import A_EARTH_M2, TAU_ATM, YEARS
        from nbs.forest_data import key_grid
        from nbs.map_plots import _breakeven_year_field
        from nbs.pipeline import run_single_tree
        from nbs.response import convolve_response, green_temperature
        from nbs.species import SPECIES, reference_site
        from nbs.aggregate import _product_no_nan, co2_factor_grid

        g_t = green_temperature("ssp245")
        keys = key_grid()
        w = plantable_area_m2()
        cool = (keys != None) & ~np.isinf(_breakeven_year_field("ssp245")) & (w > 0)  # noqa: E711

        def total(py):
            t = np.zeros(len(YEARS))
            for k in SPECIES:
                m = (keys == k) & cool
                if not m.any():
                    continue
                sp = get_species(k)
                n = w[m] / sp.stand_area_m2
                res = run_single_tree(k, lat_deg=reference_site(k), plant_year=py)
                co2 = convolve_response(g_t, res.phi_co2)
                alb = convolve_response(g_t, -TAU_ATM * np.asarray(res.trajectory.closure, float) * sp.stand_area_m2 / A_EARTH_M2)
                t += (co2_factor_grid(k)[m] * n).sum() * co2 + (_product_no_nan(k)[m] * n).sum() * alb
            return t

        years = [T_START + 5 * i for i in range(5)]
        series = {py: total(py) for py in years}
        i50, i100 = 2050 - int(YEARS[0]), 2100 - int(YEARS[0])
        ref = series[T_START]
        return {"pflanzjahre": years,
                "anteil_2050": [float(series[py][i50] / ref[i50]) for py in years],
                "anteil_2100": [float(series[py][i100] / ref[i100]) for py in years]}

    return _cached_json("pflanzjahr_global.json", compute)


def area_time_figure(out_path: str) -> str:
    """W2: all trees together, year by year -- cooling cells with albedo (solid) and CO2 only (dashed),
    every reforestable cell (orange); the year from which planting everywhere cools less marked."""
    _setup()
    s = area_series()
    yrs = np.array(s["jahre"])
    m = yrs <= 2100
    k = -1000 * np.array(s["kuehlt"])[m]
    kc = -1000 * np.array(s["kuehlt_nur_co2"])[m]
    al = -1000 * np.array(s["alle"])[m]
    y = yrs[m]
    fig, ax = plt.subplots(figsize=(12.0, 4.7), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.8, bottom=0.13, top=0.92)
    ax.plot(y, k, color=C_TREE, linewidth=3.2)
    ax.plot(y, al, color=C_WARM, linewidth=3.2)
    cross = int(y[np.argmax((k > al) & (y > 2030))])
    ax.axvline(cross, color=C_MUTED, linewidth=1.0, linestyle=(0, (4, 3)))
    ax.text(cross + 1, 2, f"ab {cross} kühlt\n„überall“ weniger", fontsize=12, color=C_INK)

    def de(v, nd=0):
        return f"{v:.{nd}f}".replace(".", ",")

    i50, i100 = list(y).index(2050), len(y) - 1
    for i in (i50, i100):
        ax.plot(y[i], k[i], "o", ms=8, color=C_TREE, mec="white", mew=1.5, zorder=5)
        ax.annotate(f"{de(100 * k[i] / kc[i])} % netto", (y[i], k[i]), xytext=(8, -18) if i == i50 else (-6, 10),
                    textcoords="offset points", ha="left" if i == i50 else "right", fontsize=12.5, color=C_TREE,
                    fontweight="bold")
    ax.annotate(f"kühlende Flächen: {de(k[-1])} mK", (y[-1], k[-1]), xytext=(8, 0),
                textcoords="offset points", va="center", fontsize=12.5, color=C_TREE, fontweight="bold",
                annotation_clip=False)
    ax.annotate(f"alle Flächen: {de(al[-1])} mK", (y[-1], al[-1]), xytext=(8, 0), textcoords="offset points",
                va="center", fontsize=12.5, color=C_WARM, fontweight="bold", annotation_clip=False)
    ax.set_xlim(T_START, 2100)
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylim(0, max(k.max(), al.max()) * 1.15)
    ax.set_ylabel("Kühlung der Erde [mK]")
    ax.set_title(f"Alle Bäume, gepflanzt {T_START}: Kühlung Jahr für Jahr (1 mK = 0,001 K)", loc="left", fontsize=13, color=C_INK)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    return _save(fig, out_path)


def need_temperature_series() -> dict:
    """Cooling [K, positive] that the removal CMIP7 Very Low needs (novel + land) would bring, year by
    year from the start year: the removal as a negative CO2 flux through the same chain as the trees
    (impulse response g_C, logarithmic forcing against the SSP2-4.5 background, temperature response g_T).
    Cached in docs/slides/chart_data/bedarf_temperatur.json."""

    def compute():
        from nbs.cmip7_figures import removal
        from nbs.constants import YEARS
        from nbs.forcing import phi_co2_background
        from nbs.response import background_co2_ppm, convolve_response, green_carbon, green_temperature

        e = removal()
        r = e[e.szenario == "VL"].sort_values("jahr")
        gt = np.interp(YEARS, r.jahr.to_numpy(), (r.neuartig_gt + r.land_gt).to_numpy())
        phi = phi_co2_background(-gt * 1e12, green_carbon("ssp245"), background_co2_ppm("ssp245"))
        dt = convolve_response(green_temperature("ssp245"), phi)
        return {"jahre": [int(y) for y in YEARS], "kuehlung_k": [float(-v) for v in dt],
                "entnahme_gt": [float(v) for v in np.cumsum(gt)]}

    return _cached_json("bedarf_temperatur.json", compute)


def overshoot_series() -> dict:
    """The limit, read off the scenario data: how far CMIP7 Very Low (median) lies above 1.5 deg C, year by
    year -- the cooling that would be needed on top of Very Low to stay at 1.5 deg C."""
    from nbs.cmip7_figures import temperature

    t = temperature()
    v = t[(t.szenario == "VL") & (t.jahr >= T_START) & (t.jahr <= 2100)].sort_values("jahr")
    med = v["median"].rolling(7, center=True, min_periods=1).mean()  # the median still carries the ensemble's year-to-year noise
    return {"jahre": [int(y) for y in v.jahr], "noetig_k": [float(max(0.0, x - 1.5)) for x in med]}


def area_need_figure(out_path: str) -> str:
    """W2b, overlay on the availability map: cooling of all trees year by year (cooling cells, every cell)
    against the limit: the cooling needed to keep Very Low at 1.5 deg C."""
    _setup()
    s = area_series()
    o = overshoot_series()
    y = np.array(s["jahre"])
    k = -1000 * np.array(s["kuehlt"])
    al = -1000 * np.array(s["alle"])
    need = 1000 * np.interp(y, o["jahre"], o["noetig_k"])
    fig, ax = plt.subplots(figsize=(7.0, 4.3), dpi=FIG_DPI)  # sized to the overlay card: ticks ~20 px
    fig.subplots_adjust(left=0.12, right=0.66, bottom=0.12, top=0.9)
    ax.fill_between(y, k, need, where=need > k, color="#c4121f", alpha=0.85, lw=0)   # the gap, dramatically red
    ax.plot(y, need, color="#8e0d16", linewidth=3.0, linestyle=(0, (6, 3)))
    ax.plot(y, k, color=C_TREE, linewidth=3.2)
    ax.plot(y, al, color=C_WARM, linewidth=3.2)
    ip = int(np.argmax(need))
    ax.plot(y[ip], need[ip], "o", ms=8, color="#8e0d16", mec="white", mew=1.5, zorder=5)
    ax.annotate(f"{y[ip]}: {need[ip]:.0f} mK über 1,5 °C", (y[ip], need[ip]), xytext=(8, 8), textcoords="offset points",
                fontsize=12.5, color="#8e0d16", fontweight="bold")
    end = dict(xytext=(8, 0), textcoords="offset points", va="center", annotation_clip=False)
    ax.annotate("nötig für 1,5 °C\n(Very Low)", (y[-1], need[-1]), fontsize=12.5, color="#8e0d16", fontweight="bold", **end)
    ax.annotate(f"Bäume, kühlende\nFlächen: {k[-1]:.0f} mK", (y[-1], k[-1] + 26), fontsize=12.5, color=C_TREE, fontweight="bold", **end)
    ax.annotate(f"alle Flächen: {al[-1]:.0f} mK", (y[-1], al[-1] - 12), fontsize=12.5, color=C_WARM, fontweight="bold", **end)
    ax.set_xlim(T_START, 2100)
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylim(0, need.max() * 1.15)
    ax.set_ylabel("Kühlung der Erde [mK]")
    ax.set_title("Kühlung Jahr für Jahr, gepflanzt 2026", loc="left", fontsize=13, color=C_INK)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    return _save(fig, out_path)


def planting_delay_figure(out_path: str) -> str:
    """W3: what waiting costs -- cooling in 2050 (peak of warming in the lowest scenario) and in 2100,
    relative to planting in 2025, on the cooling cells."""
    _setup()
    d = planting_delay()
    yrs = d["pflanzjahre"]
    x = np.arange(len(yrs))
    fig, ax = plt.subplots(figsize=(12.0, 4.6), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.97, bottom=0.14, top=0.86)
    wdt = 0.36
    for off, key, col, lab in ((-wdt / 2, "anteil_2050", C_TREE, "Kühlung 2050, Höhepunkt der Erwärmung"),
                               (wdt / 2, "anteil_2100", C_TREE_LIGHT, "Kühlung 2100")):
        v = 100 * np.array(d[key])
        ax.bar(x + off, v, width=wdt, color=col, label=lab)
        for xi, vi in zip(x + off, v):
            ax.text(xi, vi + 2, f"{vi:.0f} %", ha="center", fontsize=12.5, color=C_INK, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"gepflanzt {y}" for y in yrs], fontsize=12.5)
    ax.set_ylim(0, 120)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25 %", "50 %", "75 %", "100 %"])
    ax.set_ylabel(f"Kühlung, gemessen an Pflanzung {T_START}")
    ax.legend(loc="upper right", frameon=False, fontsize=12.5, ncol=2, bbox_to_anchor=(1.0, 1.13))
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    return _save(fig, out_path)


CMIP7_WORLDS = ("VL", "LN", "L", "ML", "M", "HL", "H")  # the seven CMIP7 markers, background and removal from one scenario
CMIP7_SHOWN = ("VL", "ML", "M", "H")  # the scenarios the deck draws (2026-10-07: four instead of seven)


@lru_cache(maxsize=1)
def tree_scenarios() -> dict:
    """Trees on the same cells (cooling 0.42 Gha, all 0.83 Gha) in each CMIP7 marker world: the marker's own
    emissions drive FaIR (background warming, CO2, sinks) and its own removal 2024-2100 is the need. Net share
    in 2100 from two FaIR runs (with and without albedo) on top of the scenario; net CO2 = the cascade's carbon
    x net share. Cached in docs/slides/chart_data/szenarien_cmip7_baeume.json."""

    def compute():
        from nbs.cmip7_figures import MARKERS, cumulative_removal
        from nbs.fair_module import run_fair_baseline
        from nbs.map_plots import _breakeven_year_field
        from nbs.potential import _masked_global_delta_t

        c = planting_choice()
        plant = assign_species() != None  # noqa: E711
        cool = plant & ~np.isinf(_breakeven_year_field("ssp245"))
        cum = cumulative_removal()
        out = {}
        for code in CMIP7_WORLDS:
            sc = f"cmip7-{code}"
            base = run_fair_baseline(sc)
            r = {"name": MARKERS[code][0].split(" (")[0], "farbe": MARKERS[code][1],
                 "land_gt": float(cum.loc[code, "land_gt"]), "neuartig_gt": float(cum.loc[code, "neuartig_gt"]),
                 "erwaermung_2100_k": float(base[-1]), "erwaermung_max_k": float(base.max())}
            for key, mask in (("kuehlt", cool), ("alle", plant)):
                full = _masked_global_delta_t(mask, sc)
                co2 = _masked_global_delta_t(mask, sc, ModelConfig(albedo=False))
                share = float(full[-1] / co2[-1])
                r[key] = {"anteil": share, "netto_gt": c[key]["brutto_gt"] * share, "brutto_gt": c[key]["brutto_gt"],
                          "dt_2100_mk": float(-1000 * full[-1])}
            out[code] = r
            print(code, round(r["erwaermung_2100_k"], 2), round(r["kuehlt"]["netto_gt"], 1), round(r["alle"]["netto_gt"], 1),
                  flush=True)
        return out

    return _cached_json("szenarien_cmip7_baeume.json", compute)


def removal_series() -> dict:
    """Cumulative CO2 removal by the trees on the cooling cells, year by year, for planting in the start
    year and ten years later: gross (stock change x 44/12) and net of albedo (gross x Delta_T full /
    Delta_T CO2 only, the net share of the talk, here time-resolved). Per-tree runs (typical forest per
    cell, full model) summed over the trees of each cell, as planting_delay. Cached in
    docs/slides/chart_data/baeume_entnahme_zeitreihe.json."""

    def compute():
        from nbs.aggregate import _product_no_nan, co2_factor_grid
        from nbs.constants import A_EARTH_M2, M_CO2_PER_C, TAU_ATM, YEARS
        from nbs.forest_data import key_grid
        from nbs.map_plots import _breakeven_year_field
        from nbs.pipeline import run_single_tree
        from nbs.response import convolve_response, green_temperature
        from nbs.species import SPECIES, reference_site

        g_t = green_temperature("ssp245")
        keys = key_grid()
        w = plantable_area_m2()
        cool = (keys != None) & ~np.isinf(_breakeven_year_field("ssp245")) & (w > 0)  # noqa: E711

        def series(py):
            gross, t_co2, t_alb = np.zeros(len(YEARS)), np.zeros(len(YEARS)), np.zeros(len(YEARS))
            for k in SPECIES:
                m = (keys == k) & cool
                if not m.any():
                    continue
                sp = get_species(k)
                n = w[m] / sp.stand_area_m2
                res = run_single_tree(k, lat_deg=reference_site(k), plant_year=py)
                f_c = (co2_factor_grid(k)[m] * n).sum()
                gross += f_c * np.cumsum(M_CO2_PER_C * np.asarray(res.trajectory.net_uptake_kgC_yr, float)) / 1e12
                t_co2 += f_c * convolve_response(g_t, res.phi_co2)
                t_alb += (_product_no_nan(k)[m] * n).sum() * convolve_response(
                    g_t, -TAU_ATM * np.asarray(res.trajectory.closure, float) * sp.stand_area_m2 / A_EARTH_M2)
            share = np.where(np.abs(t_co2) > 0, (t_co2 + t_alb) / np.where(t_co2 == 0, 1, t_co2), 1.0)
            return {"brutto_gt": gross.tolist(), "netto_gt": (gross * share).tolist(), "anteil": share.tolist()}

        return {"jahre": [int(y) for y in YEARS], "pflanzjahre": {str(py): series(py) for py in (T_START, T_START + 10)}}

    return _cached_json("baeume_entnahme_zeitreihe.json", compute)


def removal_gap_figure(out_path: str) -> str:
    """W4: cumulative removal the scenario needs (CMIP7 Very Low, novel + land, from 2024) against the
    trees' net removal on the cooling cells, planted in the start year and ten years later; the gap is
    what technical removal has to deliver. Time profile from the per-tree runs, level normalised to the
    cascade (slide "Wiederbewaldbare Flaeche") so that the deck quotes one number; net share of the
    start-year planting from the FaIR area runs, of the later planting from the per-tree runs."""
    from nbs.cmip7_figures import removal

    _setup()
    d = removal_series()
    years = np.array(d["jahre"])
    e = removal()
    r = e[(e.szenario == "VL") & (e.jahr >= 2024) & (e.jahr <= 2100)].sort_values("jahr")
    need = np.interp(years, r.jahr.to_numpy(), np.cumsum((r.neuartig_gt + r.land_gt).to_numpy()))
    pw = planting_choice()["kuehlt"]
    f = pw["brutto_gt"] / d["pflanzjahre"][str(T_START)]["brutto_gt"][-1]
    a = area_series()
    kc = np.array(a["kuehlt_nur_co2"])
    share = np.interp(years, a["jahre"], np.array(a["kuehlt"]) / np.where(kc == 0, 1, kc))
    gross = f * np.array(d["pflanzjahre"][str(T_START)]["brutto_gt"])
    net = gross * share
    later = f * np.array(d["pflanzjahre"][str(T_START + 10)]["netto_gt"])

    fig, ax = plt.subplots(figsize=(11.5, 5.0), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.76, bottom=0.12, top=0.9)
    ax.fill_between(years, net, need, where=need > net, color=C_COLD, alpha=0.35, lw=0)
    ax.plot(years, need, color=C_INK, lw=2.8)
    ax.plot(years, gross, color=C_TREE, lw=1.6, ls=(0, (2, 3)))
    ax.plot(years, later, color=C_TREE_LIGHT, lw=3.0)
    ax.plot(years, net, color=C_TREE, lw=3.2)
    i50 = 2050 - int(years[0])
    ax.plot([2050, 2050], [net[i50], need[i50]], "o-", color=C_INK, ms=6, lw=1.0)
    ax.annotate(f"2050: Bäume {net[i50]:.0f} von {need[i50]:.0f} Gt", (2050, need[i50]), xytext=(-10, 14),
                textcoords="offset points", ha="right", fontsize=12.5, color=C_INK, fontweight="bold")
    ax.annotate(f"gepflanzt {T_START + 10}: {later[i50]:.0f} Gt", (2050, later[i50]), xytext=(10, -14),
                textcoords="offset points", ha="left", fontsize=12, color="#5d9b57")
    end = dict(xytext=(8, 0), textcoords="offset points", va="center", annotation_clip=False)
    ax.annotate(f"Bedarf Very Low: {need[-1]:.0f} Gt", (years[-1], need[-1]), fontsize=13, color=C_INK,
                fontweight="bold", **end)
    ax.annotate(f"Bäume brutto: {gross[-1]:.0f} Gt", (years[-1], gross[-1]), fontsize=12, color=C_TREE,
                **{**end, "xytext": (8, 7)})
    ax.annotate(f"Bäume netto: {net[-1]:.0f} Gt\n(gepflanzt {T_START} oder {T_START + 10})", (years[-1], net[-1]),
                fontsize=12.5, color=C_TREE, fontweight="bold", **{**end, "xytext": (8, -14)})
    xm = 2084
    ym = 0.5 * (np.interp(xm, years, net) + np.interp(xm, years, need))
    ax.text(xm, ym, f"Lücke bis 2100: {need[-1] - net[-1]:.0f} Gt\n→ technische Entnahme", fontsize=13.5,
            color="#2f4a63", ha="center", va="center", fontweight="bold")
    ax.set_xlim(T_START, 2100)
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylim(0, need[-1] * 1.08)
    ax.set_ylabel("kumulierte CO$_2$-Entnahme [Gt]")
    ax.set_title("Bäume auf den kühlenden Flächen gegen den Entnahmebedarf im Szenario Very Low", loc="left",
                 fontsize=13, color=C_INK)
    return _save(fig, out_path)


def need_scenarios_figure(out_path: str) -> str:
    """V2: the seven CMIP7 worlds, ordered by warming in 2100. Per world the removal it counts on 2024-2100
    (land sink and novel) and, next to it, the trees on the cooling cells in that world (gross hatched,
    net solid; tick = trees on every cell), with the share of the need they cover."""
    _setup()
    d = tree_scenarios()
    fig, ax = plt.subplots(figsize=(12.0, 4.9), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.07, right=0.99, bottom=0.2, top=0.86)
    x = np.arange(len(CMIP7_WORLDS))
    wn, wt = 0.34, 0.26

    def de(v, nd=0):
        return f"{v:.{nd}f}".replace(".", ",")

    for xi, code in zip(x, CMIP7_WORLDS):
        r = d[code]
        land, novel = r["land_gt"], r["neuartig_gt"]
        need = land + novel
        xn, xt = xi - 0.18, xi + 0.16
        ax.bar(xn, land, width=wn, color=C_TREE_LIGHT)
        ax.bar(xn, novel, bottom=land, width=wn, color=C_DAC)
        ax.text(xn, need + 14, de(need), ha="center", fontsize=11.5, color=C_INK)
        k, a = r["kuehlt"], r["alle"]
        ax.bar(xt, k["brutto_gt"], width=wt, color="white", edgecolor=C_TREE, linewidth=1.2, hatch="//")
        ax.bar(xt, k["netto_gt"], width=wt, color=C_TREE)
        ax.plot([xt - wt / 2, xt + wt / 2], [a["netto_gt"]] * 2, color=C_WARM, linewidth=2.6)
        lab = f"{100 * k['netto_gt'] / need:.0f} %" if need > 5 else "–"
        ax.text(xt, k["brutto_gt"] + 14, lab, ha="center", fontsize=13.5, color=C_TREE, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d[c]['name']}\n{de(d[c]['erwaermung_2100_k'], 1)} °C 2100" for c in CMIP7_WORLDS], fontsize=12)
    ax.set_xlim(-0.6, len(CMIP7_WORLDS) - 0.4)
    ax.set_ylim(0, 900)
    ax.set_ylabel("CO$_2$-Entnahme 2024–2100 [Gt]")
    ax.text(-0.55, -150, "← optimistisch", fontsize=12, color=C_MUTED)
    ax.text(len(CMIP7_WORLDS) - 0.45, -150, "pessimistisch →", fontsize=12, color=C_MUTED, ha="right")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(handles=[Patch(facecolor=C_TREE_LIGHT, label="Szenario: Entnahme an Land"),
                       Patch(facecolor=C_DAC, label="Szenario: neuartige Entnahme (BECCS, DAC, …)"),
                       Patch(facecolor=C_TREE, label="unsere Bäume, wo sie kühlen: netto"),
                       Patch(facecolor="white", edgecolor=C_TREE, hatch="//", label="… brutto, im Holz"),
                       plt.Line2D([], [], color=C_WARM, lw=2.6, label="Bäume überall: netto")],
              loc="upper left", frameon=False, fontsize=11.5, ncol=3, bbox_to_anchor=(0.0, 1.17))
    return _save(fig, out_path)


def tree_potential_gtco2() -> tuple[float, float]:
    """(gross, net of albedo) CO2 stored by 2100 where the tree cools (the cascade's usable area)."""
    c = planting_choice()["kuehlt"]
    return c["brutto_gt"], c["netto_gt"]


@lru_cache(maxsize=1)
def planting_rank() -> dict:
    """Reforestable cells ranked by their cooling in 2100 per hectare, best first (typical forest,
    planted in the start year, full model, per-tree runs summed over the trees of each cell).

    Returns cumulative area [Gha] and cumulative cooling in 2100 [mK, positive = cooler], plus the
    position of the three sites on that ranking. Summing per-tree effects is linear; the global FaIR
    runs of planting_choice (whole area at once) give 20 and 9 mK where this sum gives 19 and 8."""
    from nbs.animations import SITES, site_cell
    from nbs.forest_data import key_grid
    from nbs.map_fields import _tree_dt_grid
    from nbs.species import SPECIES

    dt = _tree_dt_grid()
    keys = key_grid()
    w = plantable_area_m2()
    trees = np.zeros_like(dt)
    for k in SPECIES:
        m = keys == k
        trees[m] = w[m] / get_species(k).stand_area_m2
    tot = dt * trees
    ok = np.isfinite(tot) & (w > 0)
    per_ha = np.full(w.shape, np.nan)
    per_ha[ok] = tot[ok] / w[ok]
    order = np.argsort(per_ha[ok])
    area = np.concatenate([[0.0], np.cumsum(w[ok][order]) / 1e13])
    cool = np.concatenate([[0.0], -np.cumsum(tot[ok][order]) * 1000])
    srt = per_ha[ok][order]
    sites = {}
    for st in SITES:
        v = per_ha[site_cell(st)]
        j = int(np.searchsorted(srt, v))
        sites[st.label] = (float(area[j]), float(cool[j]), st.color, st.marker)
    return {"area": area, "cool": cool, "sites": sites}


def planting_rank_figure(out_path: str) -> str:
    """W1: cooling in 2100 against the reforested area, the cells planted in the order of their
    cooling per hectare -- rises to the cooling area (0.42 Gha), then falls (albedo wins)."""
    _setup()
    r = planting_rank()
    a0, c0 = r["area"], r["cool"]
    # one point per cell is ~10^5 points; 500 along the area plus the maximum draw the same curve
    i0 = int(np.argmax(c0))
    a = np.unique(np.concatenate([np.linspace(0, a0[-1], 500), [a0[i0]]]))
    c = np.interp(a, a0, c0)
    i = int(np.argmax(c))
    fig, ax = plt.subplots(figsize=(12.0, 4.6), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.97, bottom=0.15, top=0.93)
    ax.fill_between(a[: i + 1], 0, c[: i + 1], color=C_TREE, alpha=0.12, linewidth=0)
    ax.plot(a[: i + 1], c[: i + 1], color=C_TREE, linewidth=3.0)
    ax.plot(a[i:], c[i:], color=C_WARM, linewidth=3.0)

    def de(v, nd):
        return f"{v:.{nd}f}".replace(".", ",")

    peak = c[i]
    for q in (0.1, 0.2):
        v = float(np.interp(q, a0, c0))
        ax.plot([q, q], [0, v], color=C_MUTED, linewidth=1.0, linestyle=(0, (4, 3)))
        ax.plot(q, v, "o", ms=7, color=C_INK, mec="white", mew=1.5, zorder=5)
        ax.text(q + 0.006, 1.2, f"{100 * v / c0[i0]:.0f} %", fontsize=13, color=C_INK, fontweight="bold")
    ax.plot(a[i], peak, "o", ms=9, color=C_TREE, mec="white", mew=1.8, zorder=6)
    ax.annotate(f"{de(a[i], 2)} Gha: {peak:.0f} mK, größte Kühlung", (a[i], peak), xytext=(0, 12),
                textcoords="offset points", ha="center", fontsize=13, color=C_TREE, fontweight="bold")
    ax.plot(a[-1], c[-1], "o", ms=9, color=C_WARM, mec="white", mew=1.8, zorder=6)
    ax.annotate(f"alle {de(a[-1], 2)} Gha: {c[-1]:.0f} mK", (a[-1], c[-1]), xytext=(-8, 12),
                textcoords="offset points", ha="right", fontsize=13, color=C_WARM, fontweight="bold")
    ax.text(0.64, 2.5, "ab hier wärmt jeder weitere Hektar:\nNorden, Trockengebiete", fontsize=12.5,
            color=C_WARM, ha="center")
    for label, (x, y, col, mk) in r["sites"].items():
        ax.plot(x, y, marker=mk, ms=9, mfc=col, mec="white", mew=1.8, zorder=7, linestyle="none")
        right = label.startswith("Marabá")
        ax.annotate(label, (x, y), xytext=(8, -6) if right else (-8, 4), textcoords="offset points", fontsize=11.5,
                    ha="left" if right else "right", color=col, fontweight="bold")
    ax.set_xlim(0, 0.88)
    ax.set_ylim(0, peak * 1.22)
    ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    ax.set_xticklabels(["0", "0,1", "0,2", "0,3", "0,4", "0,5", "0,6", "0,7", "0,8"])
    ax.set_xlabel("bepflanzte Fläche [Gha], die am stärksten kühlenden Flächen zuerst")
    ax.set_ylabel("Kühlung 2100 [mK]")
    ax.text(0.006, peak * 1.16, "Prozent: Anteil an der größten Kühlung", fontsize=11.5, color=C_MUTED)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    return _save(fig, out_path)



# --------------------------------------------------------------------------
# V2  How much is needed (CMIP7) against the trees
# --------------------------------------------------------------------------


def need_figure(out_path: str) -> str:
    _setup()
    c = planting_choice()
    names = list(CMIP7_REMOVAL)
    fig, ax = plt.subplots(figsize=(12.0, 4.6), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.2, right=0.97, bottom=0.16, top=0.95)
    y = np.arange(len(names) + 2)[::-1]
    for yi, name in zip(y[:-2], names):
        eng, land = CMIP7_REMOVAL[name]
        ax.barh(yi, land, color=C_TREE_LIGHT, height=0.6)
        ax.barh(yi, eng, left=land, color=C_DAC, height=0.6)
        ax.text(land + eng + 15, yi, f"{land + eng:,.0f}".replace(",", "."), va="center", fontsize=13, color=C_INK)
    for yi, k in zip(y[-2:], ("kuehlt", "alle")):
        gross, net = c[k]["brutto_gt"], c[k]["netto_gt"]
        col = C_TREE if k == "kuehlt" else C_WARM
        ax.barh(yi, gross, color="white", edgecolor=col, linewidth=1.6, height=0.6, hatch="//")
        ax.barh(yi, net, color=col, height=0.6)
        ax.text(gross + 15, yi, f"{net:.0f} netto · {gross:.0f} brutto", va="center", fontsize=13, color=C_INK)
    ax.set_yticks(y)
    ax.set_yticklabels(names + [f"Bäume, nur wo sie kühlen\n({c['kuehlt']['flaeche_gha']:.2f} Gha)".replace(".", ","),
                                f"Bäume überall\n({c['alle']['flaeche_gha']:.2f} Gha)".replace(".", ",")], fontsize=13)
    ax.set_xlim(0, 1600)
    ax.set_xlabel("CO$_2$-Entnahme 2024–2100 [Gt CO$_2$]")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(handles=[Patch(facecolor=C_TREE_LIGHT, label="Land (Nettosenke der Landnutzung)"),
                       Patch(facecolor=C_DAC, label="neuartig (BECCS, DAC, …)"),
                       Patch(facecolor=C_TREE, label="Bäume netto, nach Albedo")],
              loc="lower right", frameon=False, fontsize=12)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# V3 / V4  Six places: trees against DAC, today and over time
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Place:
    name: str
    lat: float
    lon: float
    cc: str = ""  # ISO country code, shown with the name

    @property
    def label(self) -> str:
        return f"{self.name} ({self.cc})" if self.cc else self.name


PLACES = (
    Place("Joensuu", 62.60, 29.76, "FI"),
    Place("Aachen", 50.78, 6.08, "DE"),
    Place("Krakau", 50.06, 19.94, "PL"),
    Place("Peking", 39.90, 116.40, "CN"),
    Place("Manaus", -3.10, -60.00, "BR"),
    Place("Marabá", -5.37, -49.12, "BR"),  # south-eastern Amazon: much reforestable land, much sun
    Place("Kinshasa", -4.30, 15.30, "CD"),
)


@lru_cache(maxsize=None)
def place_cell(place: Place) -> tuple[int, int]:
    """Nearest cell with plantable area and DAC, within 3 cells."""
    w = plantable_area_m2()
    ok = np.isfinite(energy_grid()["strom"])
    i0 = int(np.argmin(np.abs(grid_lats() - place.lat)))
    j0 = int(np.argmin(np.abs(grid_lons() - place.lon)))
    best, dist = None, np.inf
    for di in range(-3, 4):
        for dj in range(-3, 4):
            i, j = i0 + di, (j0 + dj) % w.shape[1]
            if 0 <= i < w.shape[0] and w[i, j] > 0 and ok[i, j] and di * di + dj * dj < dist:
                best, dist = (i, j), di * di + dj * dj
    if best is None:
        raise ValueError(f"no cell with trees and DAC near {place.name}")
    return best


def place_species(place: Place) -> str:
    """Typical forest x climate zone of the place's cell (nbs.landscape.assign_species)."""
    return str(assign_species()[place_cell(place)])


def _type_short(place: Place) -> str:
    from nbs.map_fields import CATEGORIES

    key = place_species(place).split("_")[0]
    return next(c["label"] for c in CATEGORIES["waldtyp"] if c["key"] == key)


def tree_eta_at(place: Place, plant_year: int) -> float:
    """Net efficiency of the place's typical forest, planted in *plant_year*, at the horizon."""
    return float(tree_efficiency_grid(plant_year)[place_cell(place)])


def dac_eta_at(place: Place, year: int, mix_year: int | None = None) -> float:
    """Net efficiency of sorbent DAC (heat pump) at the place, run in *year*; the electricity mix of
    *mix_year* (default: the same year)."""
    my = year if mix_year is None else mix_year
    i, j = place_cell(place)
    e = energy_grid()["strom"][i, j]
    return float(1.0 - (e * electricity_gwp_grid(my)[i, j] + rest_gwp(my)))


def crossover_year(place: Place) -> int | None:
    """First year (2020 .. LAST_PLANT_YEAR) in which DAC with that year's electricity removes at least
    as cleanly as a tree of the latest planting cohort (nbs.dac_compare.DECISION_YEARS, every 5 years
    from 2025); None if the tree stays ahead."""
    from nbs.dac_figures import LAST_PLANT_YEAR

    for y in range(2020, LAST_PLANT_YEAR + 1):
        if dac_eta_at(place, y) >= tree_eta_at(place, max(T_START, y - (y - T_START) % 5)):
            return y
    return None


def today_figure(out_path: str) -> str:
    """V3: net efficiency at the places today -- tree planted in the start year against DAC with the 2020 mix."""
    _setup()
    fig, ax = plt.subplots(figsize=(12.0, 4.8), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.2, right=0.97, bottom=0.16, top=0.93)
    lo = -0.72
    ys = np.arange(len(PLACES))[::-1]
    for y, p in zip(ys, PLACES):
        t, d = tree_eta_at(p, T_START), dac_eta_at(p, T_START, 2020)
        ax.plot([max(t, lo), d], [y, y], color="#c9c0ae", linewidth=3.0, zorder=1)
    ax.axvline(0, color=C_MUTED, linewidth=1.0, zorder=2)
    for y, p in zip(ys, PLACES):
        t, d = tree_eta_at(p, T_START), dac_eta_at(p, T_START, 2020)
        if t < lo:
            ax.plot(lo, y, marker="<", ms=14, color=C_TREE, mec="white", mew=2.0, zorder=3, linestyle="none")
            ax.text(lo + 0.04, y + 0.28, f"{100 * t:.0f} %".replace("-", "−"), fontsize=11, color=C_INK)
        else:
            ax.plot(t, y, marker="o", ms=14, color=C_TREE, mec="white", mew=2.0, zorder=3, linestyle="none")
        ax.plot(d, y, marker="s", ms=13, color=C_DAC, mec="white", mew=2.0, zorder=3, linestyle="none")
    ax.text(lo, ys[0] + 0.63, "◀ netto emittierend", fontsize=12, color=C_MUTED)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{p.label}\n{_type_short(p)}" for p in PLACES], fontsize=12)
    ax.set_xlim(-0.75, 1.1)
    ax.set_ylim(-0.3, len(PLACES) - 0.7)
    ax.set_xticks([-0.5, 0, 0.5, 1.0])
    ax.set_xticklabels(["−50 %", "0", "50 %", "100 %"])
    ax.set_title("Netto-Wirkungsgrad: Anteil der entnommenen Tonne, der übrig bleibt", fontsize=13, color="#5f6b66")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(handles=[plt.Line2D([], [], marker="o", ms=10, color=C_TREE, lw=0, label=f"Baum, gepflanzt {T_START}"),
                       plt.Line2D([], [], marker="s", ms=9, color=C_DAC, lw=0, label="DAC, Strommix 2020")],
              loc="lower left", frameon=False, fontsize=12)
    return _save(fig, out_path)


def over_time_figure(out_path: str) -> str:
    """V4: net efficiency over time at the places -- DAC with the electricity of each year against
    the tree planted that year; the crossover marked."""
    _setup()
    from nbs.dac_figures import LAST_PLANT_YEAR

    years = np.arange(2020, LAST_PLANT_YEAR + 1)
    fig, axes = plt.subplots(2, 4, figsize=(12.0, 5.0), dpi=FIG_DPI, sharex=True, sharey=True)
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.08, top=0.9, wspace=0.08, hspace=0.5)
    for ax, p in zip(axes.ravel(), PLACES):
        d = [dac_eta_at(p, int(y)) for y in years]
        t = [tree_eta_at(p, int(max(y, T_START))) for y in years]
        ax.axhline(0, color=C_MUTED, linewidth=0.8)
        ax.plot(years, t, color=C_TREE, linewidth=2.6)
        ax.plot(years, d, color=C_DAC, linewidth=2.6)
        cy = crossover_year(p)
        if cy is not None and cy > 2020:
            ax.axvline(cy, color=C_INK, linewidth=1.0, linestyle=(0, (4, 3)))
            ax.text(cy + 2, -0.55, f"ab {cy}", fontsize=12, color=C_INK, fontweight="bold")
        elif cy == 2020:
            ax.text(2024, -0.55, "DAC schon heute", fontsize=12, color=C_INK, fontweight="bold")
        elif cy is None:
            ax.text(2024, -0.55, "Baum bleibt vorn (bis 2070)", fontsize=12, color=C_INK, fontweight="bold")
        ax.set_title(f"{p.label}\n{_type_short(p)}", loc="left", fontsize=11.5, color=C_INK, linespacing=1.1)
        ax.set_ylim(-0.7, 1.1)
        if min(t) < -0.7:
            ax.text(2026, -0.3, f"Baum: {100 * min(t):.0f} % (unter der Skala)".replace("-", "−"), ha="left",
                    fontsize=11, color=C_TREE)
        ax.set_yticks([-0.5, 0, 0.5, 1.0])
        ax.set_yticklabels(["−50 %", "0", "50 %", "100 %"])
        ax.set_xticks([T_START, 2045, 2070])
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    # the eighth panel holds the legend
    spare = axes.ravel()[len(PLACES)]
    spare.axis("off")
    spare.legend(handles=[plt.Line2D([], [], color=C_TREE, lw=2.6, label="Baum, in diesem\nJahr gepflanzt"),
                          plt.Line2D([], [], color=C_DAC, lw=2.6, label="DAC mit dem Strom\ndieses Jahres")],
                 loc="center", frameon=False, fontsize=12, labelspacing=1.2)
    return _save(fig, out_path)


def build_all(out_dir: str) -> list[str]:
    return [
        availability_map_figure(os.path.join(out_dir, "v1_wo_baum_wo_dac.png")),
        need_figure(os.path.join(out_dir, "v2_bedarf_cmip7.png")),
        today_figure(os.path.join(out_dir, "v3_heute_sechs_orte.png")),
        over_time_figure(os.path.join(out_dir, "v4_zeit_sechs_orte.png")),
    ]


def _world_map_skeleton(out_path: str, key: str, cbar_label: str, ticks, legend_label: str, sites: bool) -> str:
    """Layout of a world hex map: map at full width, colour bar and legend underneath.

    The deck draws the map itself (nbs.map_fields + the HTML renderer, exported to the
    pptx as SVG); this figure supplies the layout, the borders and a reference picture."""
    from nbs import map_fields as M
    from nbs.animations import SITES

    _setup()
    data = M.MAPS[key]()
    layer = next(L for L in data["panels"][0]["layers"] if L["kind"] == "num")
    sc = M.SCALES[layer["scale"]]
    grid = np.full((90, 180), np.nan)
    for r, c, v in layer["cells"]:
        grid[r, c] = v
    fig, ax = plt.subplots(figsize=(12.0, 4.7), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.005, right=0.995, bottom=0.2, top=0.995)
    im = ax.imshow(np.ma.masked_invalid(grid), extent=(-180, 180, -90, 90), origin="upper", cmap=M.scale_cmap(sc),
                   norm=M.scale_norm(sc), interpolation="nearest")
    _map_axes(ax)
    if sites:
        for s in SITES:
            ax.plot(s.lon, s.lat, marker=s.marker, ms=9, mfc=s.color, mec="white", mew=2.0, zorder=6, linestyle="none")
            ax.annotate(s.label, (s.lon, s.lat), xytext=(7, 5 if s.name == "Joensuu" else -12), textcoords="offset points",
                        fontsize=11, fontweight="bold", color=C_INK, zorder=7)
    cax = fig.add_axes([0.3, 0.045, 0.36, 0.025])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal", ticks=ticks)
    cb.set_label(cbar_label, fontsize=11)
    cb.ax.xaxis.set_label_position("top")
    cb.outline.set_visible(False)
    fig.legend(handles=[Patch(facecolor=M.LAND, label=legend_label)], loc="lower left", bbox_to_anchor=(0.69, 0.01),
               frameon=False, fontsize=11)
    return _save(fig, out_path)


def reforestable_share_figure(out_path: str) -> str:
    """V0: where trees could go at all -- reforestable share of each 2 deg block's land."""
    return _world_map_skeleton(out_path, "v0", "wiederbewaldbarer Anteil der Landfläche [%]", [0, 5, 10, 20, 30, 50],
                               "kein Platz für Bäume (Wald, Acker, Stadt, …)", sites=False)


def feasibility_figure(out_path: str) -> str:
    """D0 layout: who can go where (nbs.map_fields.feasibility); legend underneath."""
    from nbs import map_fields as M

    _setup()
    data = M.MAPS["d0"]()
    cats = M.CATEGORIES["machbar"]
    mask, layer = data["panels"][0]["layers"]
    rgba = np.zeros((90, 180, 4))
    for r, c in mask["cells"]:
        rgba[r, c] = mcolors.to_rgba(mask["color"])
    for r, c, k in layer["cells"]:
        rgba[r, c] = mcolors.to_rgba(cats[k]["color"])
    fig, ax = plt.subplots(figsize=(12.0, 4.7), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.005, right=0.995, bottom=0.13, top=0.995)
    ax.imshow(rgba, extent=(-180, 180, -90, 90), origin="upper", interpolation="nearest")
    _map_axes(ax)
    handles = [Patch(facecolor=c["color"], label=c["label"]) for c in cats]
    handles.append(Patch(facecolor=mask["color"], label=mask["label"]))
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=3, frameon=False, fontsize=11)
    return _save(fig, out_path)


def tree_effect_figure(out_path: str) -> str:
    """K15: temperature effect in 2100 of one tree of the local typical forest, planted in the start year."""
    return _world_map_skeleton(out_path, "k15", "Wirkung je Baum im Jahr 2100 [10$^{-15}$ K]: grün kühlt, orange wärmt",
                               [-90, -60, -30, 0, 15, 30, 45], "kein Platz für Bäume", sites=True)
