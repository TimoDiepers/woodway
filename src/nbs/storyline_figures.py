"""Figures for the storyline v2 deck (docs/slides/dissvortrag-storyline-v2.md).

Running example: Norway spruce at two sites, Aachen and Archangelsk, each
with its own locally measured albedo cell. Same colours, markers and surface
as nbs.animations, so every figure of the talk reads as one system.

German labels: these go straight onto slides.
"""

from __future__ import annotations

import dataclasses
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

from nbs import albedo_grid  # noqa: E402
from nbs.animations import (  # noqa: E402
    C_INK,
    C_INK_MUTED,
    FIG_DPI,
    RAMP_ALBEDO,
    RAMP_CARBON,
    SITES,
    SPECIES_KEY,
    Site,
    _clean_axes,
    _register_fonts,
    _style,
    cumulative_uptake_kg_co2,
    site_cell,
)
from nbs.constants import M_CO2_PER_C, YEARS  # noqa: E402
from nbs.metrics import t_star  # noqa: E402
from nbs.pipeline import SiteResult, run_single_tree  # noqa: E402
from nbs.response import convolve_response, green_carbon_preindustrial, green_temperature  # noqa: E402
from nbs.species import get_species  # noqa: E402
from nbs.tree import simulate_deterministic  # noqa: E402

C_CARBON = "#1b7837"  # same as nbs.plots: phi_CO2 / Delta T_CO2
C_ALBEDO = "#d95f02"  # same as nbs.plots: phi_alpha / Delta T_alpha
C_NET = "#252525"
C_WARM_FILL = "#e7b7a8"
C_COOL_FILL = "#b9cfe3"

WIDE = (12.0, 5.1)  # 1920 x 816 px: fits under a slide title with a Kurz-gesagt box below


def _setup() -> None:
    _heading, body = _register_fonts()
    _style(body)


def _save(fig, out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path


def site_annual_watts(site: Site) -> float:
    """Annual extra shortwave per full-grown tree at the site's cell [W]."""
    area = get_species(SPECIES_KEY).stand_area_m2
    return float(-albedo_grid.alpha_q_product(SPECIES_KEY)[site_cell(site)] * area)


def run_site(site: Site, plant_year: int = YEARS[0]) -> SiteResult:
    """Full model (all shells) at the site, with its own measured albedo cell."""
    product = float(albedo_grid.alpha_q_product(SPECIES_KEY)[site_cell(site)])
    return run_single_tree(SPECIES_KEY, site.lat, delta_alpha=product, q_sw=1.0, plant_year=plant_year)


def _shell_one_trajectory():
    sp = dataclasses.replace(get_species(SPECIES_KEY), gamma_warming=0.0)
    return simulate_deterministic(sp, np.zeros(len(YEARS)))


# --------------------------------------------------------------------------
# B9: kg against W -- what the tree exchanges with its surroundings
# --------------------------------------------------------------------------


def tree_exchange_figure(out_path: str) -> str:
    _setup()
    uptake = cumulative_uptake_kg_co2()
    closure = _shell_one_trajectory().closure

    fig, (ax_c, ax_w) = plt.subplots(1, 2, figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.07, right=0.84, bottom=0.13, top=0.86, wspace=0.42)
    for ax in (ax_c, ax_w):
        _clean_axes(ax)
        ax.set_xlim(YEARS[0], YEARS[-1])
        ax.set_xticks([2025, 2050, 2075, 2100, 2125, 2150])

    ax_c.plot(YEARS, uptake, color=C_CARBON, linewidth=3.0)
    ax_c.set_ylim(0, 180)
    ax_c.set_title("CO$_2$ aus der Luft geholt [kg je Baum]", loc="left", fontsize=14, color=C_INK)
    ax_c.text(2140, 40, "Aachen = Archangelsk", ha="right", fontsize=13, color=C_INK)

    for s in SITES:
        w = closure * site_annual_watts(s)
        ax_w.plot(YEARS, w, color=s.color, linewidth=2.6)
        ax_w.plot(YEARS[-1], w[-1], marker=s.marker, ms=10, mfc=s.color, mec="white", mew=1.8, clip_on=False)
        ax_w.annotate(f"{s.name}  {w[-1]:.0f} W", (YEARS[-1], w[-1]), xytext=(10, 0), textcoords="offset points",
                      va="center", fontsize=12, color=C_INK, annotation_clip=False)
    ax_w.set_ylim(0, 80)
    ax_w.set_title("zusätzlich absorbiertes Sonnenlicht [W je Baum]", loc="left", fontsize=14, color=C_INK)

    fig.text(0.493, 0.50, "?", fontsize=40, ha="center", va="center", color=C_INK_MUTED)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# K4: the CO2 profile in the air -- shell 2, carbon cycle without background
# --------------------------------------------------------------------------


def co2_profile_figure(out_path: str) -> str:
    """Each year's uptake decays with g_C; their sum is what the air lacks.

    Shell 2 has no rising background yet, so g_C is the pre-industrial
    Joos et al. (2013) response here. Dashed: the shell-1 balance at the tree.
    """
    _setup()
    flux = -M_CO2_PER_C * _shell_one_trajectory().net_uptake_kgC_yr  # kg CO2/a into the air (negative)
    g = green_carbon_preindustrial()
    profile = convolve_response(g, flux)
    at_tree = np.cumsum(flux)

    missing_tree = -at_tree  # positive: kg CO2 the air lacks
    missing_air = -profile
    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.78, bottom=0.13, top=0.92)
    _clean_axes(ax)
    ax.fill_between(YEARS, missing_air, missing_tree, color=C_CARBON, alpha=0.10, linewidth=0)
    ax.plot(YEARS, missing_tree, color=C_INK_MUTED, linewidth=2.2, linestyle=(0, (5, 4)))
    ax.plot(YEARS, missing_air, color=C_CARBON, linewidth=3.4)
    ax.set_xlim(YEARS[0], YEARS[-1])
    ax.set_ylim(0, float(np.ceil(missing_tree.max() / 20.0) * 20.0))
    ax.set_xticks([2025, 2050, 2075, 2100, 2125, 2150])
    ax.set_ylabel("CO$_2$, das der Luft fehlt, je Baum [kg]")
    x = YEARS[-1]
    ax.annotate(f"am Baum bilanziert\n{missing_tree[-1]:.0f} kg", (x, missing_tree[-1]), xytext=(12, 0),
                textcoords="offset points", va="center", fontsize=13, color=C_INK, annotation_clip=False)
    ax.annotate(f"fehlt der Luft\nwirklich: {missing_air[-1]:.0f} kg", (x, missing_air[-1]),
                xytext=(12, 0), textcoords="offset points", va="center", fontsize=13, color=C_INK,
                fontweight="bold", annotation_clip=False)
    i = int(np.searchsorted(YEARS, 2105))
    ax.text(2105, 0.5 * (missing_air[i] + missing_tree[i]), "von Ozean und Land\nzurückgegeben", ha="center",
            va="center", fontsize=13, color=C_INK_MUTED)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# K10 / K12: forcing and temperature at both sites, full model
# --------------------------------------------------------------------------


def _two_site_panels(out_path: str, *, quantity: str) -> str:
    _setup()
    results = [run_site(s) for s in SITES]
    g_t = green_temperature("ssp245")
    series = []
    for r in results:
        if quantity == "phi":
            series.append((r.phi_co2, r.phi_albedo, r.phi_total))
        else:
            series.append((convolve_response(g_t, r.phi_co2), convolve_response(g_t, r.phi_albedo), r.delta_t))
    scale = 1e15
    lim = max(float(np.abs(np.concatenate(s)).max()) for s in series) * scale * 1.1

    fig, axes = plt.subplots(1, 2, figsize=WIDE, dpi=FIG_DPI, sharey=True)
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.13, top=0.86, wspace=0.08)
    for ax, s, (co2, alb, net) in zip(axes, SITES, series):
        _clean_axes(ax)
        y = YEARS
        ts = t_star(net, y)
        ax.fill_between(y, 0, net * scale, where=y < ts, color=C_WARM_FILL, linewidth=0, interpolate=True)
        ax.fill_between(y, 0, net * scale, where=y >= ts, color=C_COOL_FILL, linewidth=0, interpolate=True)
        ax.plot(y, co2 * scale, color=C_CARBON, linewidth=2.2)
        ax.plot(y, alb * scale, color=C_ALBEDO, linewidth=2.2)
        ax.plot(y, net * scale, color=C_NET, linewidth=2.8)
        ax.axhline(0, color=C_INK_MUTED, linewidth=0.8)
        ax.axvline(ts, color=C_INK_MUTED, linewidth=1.0, linestyle=(0, (3, 3)))
        label = f"ab {ts:.0f} negativ" if quantity == "phi" else f"ab {ts:.0f} kühlend"
        ax.annotate(label, (ts, lim * 0.82), xytext=(6, 0), textcoords="offset points",
                    fontsize=12, color=C_INK, fontweight="bold")
        ax.set_xlim(y[0], y[-1])
        ax.set_ylim(-lim, lim)
        ax.set_xticks([2025, 2050, 2075, 2100, 2125, 2150])
        ax.set_title(s.name, loc="left", fontsize=15, color=s.color, fontweight="bold")
    unit = "Antrieb [10$^{-15}$ W/m² je Baum]" if quantity == "phi" else "Temperatur [10$^{-15}$ K je Baum]"
    axes[0].set_ylabel(unit)
    lbl = "φ" if quantity == "phi" else "ΔT"
    axes[1].text(2150, series[1][0][-1] * scale, f"{lbl} CO$_2$ (kühlt)", ha="right", va="top", fontsize=12,
                 color=C_CARBON)
    axes[1].text(2150, series[1][1][-1] * scale, f"{lbl} Albedo (wärmt)", ha="right", va="bottom",
                 fontsize=12, color=C_ALBEDO)
    axes[1].text(2150, series[1][2][-1] * scale + 0.08 * lim, "Summe", ha="right", va="bottom", fontsize=12,
                 color=C_NET, fontweight="bold")
    return _save(fig, out_path)


def forcing_two_sites_figure(out_path: str) -> str:
    return _two_site_panels(out_path, quantity="phi")


def temperature_two_sites_figure(out_path: str) -> str:
    return _two_site_panels(out_path, quantity="T")


# --------------------------------------------------------------------------
# K13: later planting -- the warming feeds back on the disturbance rate
# --------------------------------------------------------------------------


def planting_year_figure(out_path: str, plant_years: tuple[int, ...] = (2025, 2045, 2065, 2085)) -> str:
    _setup()
    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.80, bottom=0.14, top=0.92)
    _clean_axes(ax)
    width = 4.0
    for k, s in enumerate(SITES):
        offs = (k - 0.5) * (width + 0.6)
        ts = [t_star(run_site(s, plant_year=py).delta_t, YEARS) for py in plant_years]
        wait = [t - py for t, py in zip(ts, plant_years)]
        bars = ax.bar([py + offs for py in plant_years], wait, width=width, color=s.color, label=s.name)
        for b, w, t in zip(bars, wait, ts):
            ax.text(b.get_x() + b.get_width() / 2, w + 1.0, f"{t:.0f}", ha="center", va="bottom", fontsize=11,
                    color=C_INK)
    ax.set_xticks(list(plant_years))
    ax.set_xticklabels([f"gepflanzt\n{py}" for py in plant_years])
    ax.set_ylabel("Jahre bis zur dauerhaften Kühlung")
    ax.legend(frameon=False, fontsize=13, loc="upper left")
    ax.text(1.01, 0.5, "Zahl über dem Balken:\nJahr t*, ab dem der\nBaum dauerhaft kühlt", transform=ax.transAxes,
            fontsize=12, color=C_INK_MUTED, va="center")
    return _save(fig, out_path)


def build_all(out_dir: str) -> list[str]:
    return [
        tree_exchange_figure(os.path.join(out_dir, "b9_kg_gegen_watt.png")),
        co2_profile_figure(os.path.join(out_dir, "k4_co2_profil.png")),
        forcing_two_sites_figure(os.path.join(out_dir, "k10_antrieb_zwei_orte.png")),
        temperature_two_sites_figure(os.path.join(out_dir, "k12_temperatur_zwei_orte.png")),
        planting_year_figure(os.path.join(out_dir, "k13_pflanzjahr_zwei_orte.png")),
    ]
