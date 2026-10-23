"""Figures for the storyline v2 deck (docs/slides/dissvortrag-storyline-v2.md).

Running example: the typical forest at Aachen, Fairbanks and Marabá, each
with its own locally measured albedo cell. Same colours, markers and surface
as nbs.animations, so every figure of the talk reads as one system.

German labels: these go straight onto slides.
"""

from __future__ import annotations

import dataclasses
import os
from functools import lru_cache

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
    Site,
    _clean_axes,
    _register_fonts,
    _style,
    site_cell,
    site_key,
    site_uptake_kg_co2,
)
from nbs.constants import M_CO2_PER_C, T_START, YEARS  # noqa: E402
from nbs.light import light_product  # noqa: E402
from nbs.metrics import t_star  # noqa: E402
from nbs.pipeline import SiteResult, run_single_tree  # noqa: E402
from nbs.response import convolve_response, green_carbon_preindustrial, green_temperature  # noqa: E402
from nbs.site_factor import site_factor  # noqa: E402
from nbs.species import get_species  # noqa: E402
from nbs.tree import simulate_deterministic  # noqa: E402

C_CARBON = "#1b7837"  # same as nbs.plots: phi_CO2 / Delta T_CO2
C_ALBEDO = "#d95f02"  # same as nbs.plots: phi_alpha / Delta T_alpha
C_NET = "#252525"
C_WARM_FILL = "#e7b7a8"
C_COOL_FILL = "#b9cfe3"

WIDE = (12.0, 5.1)
HALF = (7.3, 5.0)  # 1168 x 800 px: the chart column next to formulas (Klima chapter), ticks ~19 px  # 1920 x 816 px: fits under a slide title with a Kurz-gesagt box below


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
    key = site_key(site)
    return float(-light_product(key)[site_cell(site)] * get_species(key).stand_area_m2)


def _site_species(site: Site):
    """Registry entry of the site's typical forest, carbon level of its cell."""
    key = site_key(site)
    sp = get_species(key)
    return dataclasses.replace(sp, m_max_kgC=sp.m_max_kgC * site_factor(key, site.lat, site.lon))


def run_site(site: Site, plant_year: int = YEARS[0]) -> SiteResult:
    """Full model (all shells) at the site, with its own measured albedo cell."""
    key = site_key(site)
    product = float(light_product(key)[site_cell(site)])
    return run_single_tree(key, site.lat, delta_alpha=product, q_sw=1.0, plant_year=plant_year, lon_deg=site.lon)


def _shell_one_trajectory(site: Site):
    """Shell 1 at *site*: growth level from the site factor, disturbance at
    today's rate, no warming feedback."""
    sp = _site_species(site)
    sp = dataclasses.replace(sp, gamma_warming=0.0)
    return simulate_deterministic(sp, np.zeros(len(YEARS)))


# --------------------------------------------------------------------------
# B9: kg against W -- what the tree exchanges with its surroundings
# --------------------------------------------------------------------------


def tree_exchange_figure(out_path: str) -> str:
    _setup()
    closure = {s.name: _shell_one_trajectory(s).closure for s in SITES}

    fig, (ax_c, ax_w) = plt.subplots(1, 2, figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.07, right=0.84, bottom=0.13, top=0.86, wspace=0.55)
    for ax in (ax_c, ax_w):
        _clean_axes(ax)
        ax.set_xlim(YEARS[0], YEARS[-1])
        ax.set_xticks([T_START, 2050, 2075, 2100])

    top = 0.0
    for s in SITES:
        c = site_uptake_kg_co2(s)
        top = max(top, float(c.max()))
        ax_c.plot(YEARS, c, color=s.color, linewidth=2.6)
        ax_c.plot(YEARS[-1], c[-1], marker=s.marker, ms=10, mfc=s.color, mec="white", mew=1.8, clip_on=False)
        ax_c.annotate(f"{s.label}  {c[-1]:.0f} kg", (YEARS[-1], c[-1]), xytext=(10, 0), textcoords="offset points",
                      va="center", fontsize=12, color=C_INK, annotation_clip=False)
    ax_c.set_ylim(0, float(np.ceil(top / 50.0) * 50.0))
    ax_c.set_title("CO$_2$-Aufnahme [kg je Baum]", loc="left", fontsize=14, color=C_INK)

    for s in SITES:
        w = closure[s.name] * site_annual_watts(s)
        ax_w.plot(YEARS, w, color=s.color, linewidth=2.6)
        ax_w.plot(YEARS[-1], w[-1], marker=s.marker, ms=10, mfc=s.color, mec="white", mew=1.8, clip_on=False)
        ax_w.annotate(f"{s.label}  {w[-1]:.0f} W", (YEARS[-1], w[-1]), xytext=(10, 0), textcoords="offset points",
                      va="center", fontsize=12, color=C_INK, annotation_clip=False)
    ax_w.set_ylim(min(0.0, min(float((closure[s_.name] * site_annual_watts(s_)).min()) for s_ in SITES)) - 5, 80)
    ax_w.axhline(0, color=C_INK_MUTED, linewidth=0.8)
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
    g = green_carbon_preindustrial()
    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.76, bottom=0.13, top=0.92)
    _clean_axes(ax)
    top = 0.0
    for s in SITES:
        flux = -M_CO2_PER_C * _shell_one_trajectory(s).net_uptake_kgC_yr  # kg CO2/a into the air (negative)
        missing_tree = -np.cumsum(flux)
        missing_air = -convolve_response(g, flux)
        top = max(top, float(missing_tree.max()))
        ax.fill_between(YEARS, missing_air, missing_tree, color=s.color, alpha=0.08, linewidth=0)
        ax.plot(YEARS, missing_tree, color=s.color, linewidth=2.0, linestyle=(0, (5, 4)))
        ax.plot(YEARS, missing_air, color=s.color, linewidth=3.2)
        ax.annotate(f"{s.label}: {missing_air[-1]:.0f} von {missing_tree[-1]:.0f} kg", (YEARS[-1], missing_air[-1]),
                    xytext=(12, 0), textcoords="offset points", va="center", fontsize=12.5, color=C_INK,
                    fontweight="bold", annotation_clip=False)
    ax.set_xlim(YEARS[0], YEARS[-1])
    ax.set_ylim(0, float(np.ceil(top / 50.0) * 50.0))
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylabel("CO$_2$, das der Luft fehlt, je Baum [kg]")
    ax.text(2027, 0.93 * ax.get_ylim()[1], "gestrichelt: am Baum bilanziert\n"
            "durchgezogen: fehlt der Luft wirklich\nFläche dazwischen: von Ozean und Land zurückgegeben",
            fontsize=12, color=C_INK_MUTED, va="top")
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

    fig, axes = plt.subplots(1, len(SITES), figsize=(11.6, 3.4), dpi=FIG_DPI, sharey=True)  # flat: under formula and definitions, ticks ~19 px
    fig.subplots_adjust(left=0.08, right=0.985, bottom=0.17, top=0.84, wspace=0.08)
    for ax, s, (co2, alb, net) in zip(axes, SITES, series):
        _clean_axes(ax)
        y = YEARS
        ts = t_star(net, y)
        ax.fill_between(y, 0, net * scale, where=net > 0, color=C_WARM_FILL, linewidth=0, interpolate=True)
        ax.fill_between(y, 0, net * scale, where=net <= 0, color=C_COOL_FILL, linewidth=0, interpolate=True)
        ax.plot(y, co2 * scale, color=C_CARBON, linewidth=2.2)
        ax.plot(y, alb * scale, color=C_ALBEDO, linewidth=2.2)
        ax.plot(y, net * scale, color=C_NET, linewidth=2.8)
        ax.axhline(0, color=C_INK_MUTED, linewidth=0.8)
        if np.isfinite(ts) and ts > y[0]:
            ax.axvline(ts, color=C_INK_MUTED, linewidth=1.0, linestyle=(0, (3, 3)))
        if not np.isfinite(ts):
            label, ts_mark = "kühlt nicht bis 2100", None
        elif ts <= y[0]:
            label, ts_mark = "kühlt von Anfang an", None
        else:
            label = f"ab {ts:.0f} negativ" if quantity == "phi" else f"ab {ts:.0f} kühlend"
            ts_mark = ts
        if quantity != "phi":  # the forcing slide shows the curves only
            ax.annotate(label, (ts_mark if ts_mark is not None else y[0] + 2, lim * 0.82), xytext=(6, 0), textcoords="offset points",
                        fontsize=12, color=C_INK, fontweight="bold")
        ax.set_xlim(y[0], y[-1])
        ax.set_ylim(-lim, lim)
        ax.set_xticks([2030, 2060, 2090])
        ax.set_title(s.label, loc="left", fontsize=15, color=s.color, fontweight="bold")
    unit = "Antrieb [10$^{-15}$ W/m² je Baum]" if quantity == "phi" else "Temperatur [10$^{-15}$ K je Baum]"
    axes[0].set_ylabel(unit)
    lbl = "φ" if quantity == "phi" else "ΔT"
    # line labels in the first panel (Aachen: there the albedo warms, as the labels say)
    axes[0].text(2100, series[0][0][-1] * scale, f"{lbl} CO$_2$ (kühlt)", ha="right", va="top", fontsize=12,
                 color=C_CARBON)
    axes[0].text(2100, series[0][1][-1] * scale, f"{lbl} Albedo (wärmt)", ha="right", va="bottom",
                 fontsize=12, color=C_ALBEDO)
    axes[0].text(2100, series[0][2][-1] * scale - 0.08 * lim, "Summe", ha="right", va="top", fontsize=12,
                 color=C_NET, fontweight="bold")
    return _save(fig, out_path)


def forcing_two_sites_figure(out_path: str) -> str:
    return _two_site_panels(out_path, quantity="phi")


def temperature_two_sites_figure(out_path: str) -> str:
    return _two_site_panels(out_path, quantity="T")


# --------------------------------------------------------------------------
# K13: later planting -- the warming feeds back on the disturbance rate
# --------------------------------------------------------------------------


def planting_year_figure(out_path: str, plant_years: tuple[int, ...] = (T_START, T_START + 20, T_START + 40, T_START + 60)) -> str:
    """Effect per tree in 2100 by planting year at both sites (full model).

    The later a tree is planted, the warmer the world it grows into and the
    higher its disturbance rate (p = p0 e^{gamma T}) -- and the less time it
    has. Below zero: cooling; above zero: still warming in 2100.
    """
    _setup()
    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.09, right=0.80, bottom=0.14, top=0.92)
    _clean_axes(ax)
    width = 4.0
    allv = {}
    for k, s in enumerate(SITES):
        allv[s.name] = [run_site(s, plant_year=py).delta_t[-1] * 1e15 for py in plant_years]
    lo = min(min(v) for v in allv.values())
    hi = max(max(v) for v in allv.values())
    span = max(hi, 0.0) - min(lo, 0.0)
    pad = 0.04 * span
    for k, s in enumerate(SITES):
        offs = (k - (len(SITES) - 1) / 2) * (width + 0.6)
        vals = allv[s.name]
        ax.bar([py + offs for py in plant_years], vals, width=width, color=s.color, label=s.label)
        for py, v in zip(plant_years, vals):
            txt = "0" if abs(v) < 0.5 else f"{v:+.0f}".replace("-", "−")
            ax.text(py + offs, v + (pad if v >= 0 else -pad), txt, ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=11, color=C_INK)
    ax.set_ylim(min(lo, 0.0) - 3 * pad, max(hi, 0.0) + 3 * pad)
    ax.axhline(0, color=C_INK_MUTED, linewidth=0.9)
    ax.set_xticks(list(plant_years))
    ax.set_xticklabels([f"gepflanzt\n{py}" for py in plant_years])
    ax.tick_params(axis="x", pad=8)
    ax.set_ylabel("Wirkung je Baum im Jahr 2100 [10$^{-15}$ K]")
    ax.legend(frameon=False, fontsize=13, loc="center left", bbox_to_anchor=(1.0, 0.45))
    from matplotlib.transforms import blended_transform_factory

    tr = blended_transform_factory(ax.transAxes, ax.transData)
    ax.text(1.01, 2 * pad, "über null: wärmt 2100 noch", transform=tr, fontsize=12, color=C_INK_MUTED, va="bottom")
    ax.text(1.01, -2 * pad, "unter null: kühlt", transform=tr, fontsize=12, color=C_INK_MUTED, va="top")
    return _save(fig, out_path)


def build_all(out_dir: str) -> list[str]:
    return [
        tree_exchange_figure(os.path.join(out_dir, "b9_kg_gegen_watt.png")),
        co2_profile_figure(os.path.join(out_dir, "k4_co2_profil.png")),
        forcing_two_sites_figure(os.path.join(out_dir, "k10_antrieb_zwei_orte.png")),
        temperature_two_sites_figure(os.path.join(out_dir, "k12_temperatur_zwei_orte.png")),
        planting_year_figure(os.path.join(out_dir, "k13_pflanzjahr_zwei_orte.png")),
        co2_spectrum_figure(os.path.join(out_dir, "k7_co2_spektrum.png")),
        co2_saturation_figure(os.path.join(out_dir, "k8_co2_saettigung.png")),
        ladder_figure(os.path.join(out_dir, "k14_leiter_schalen.png")),
        temperature_path_figure(os.path.join(out_dir, "v6_temperaturpfad.png")),
        tree_energy_figure(os.path.join(out_dir, "b10_energie_am_baum.png")),
        carbon_response_figure(os.path.join(out_dir, "k3_restanteil_joos.png")),
        carbon_pulse_figure(os.path.join(out_dir, "k3_ein_jahr_puls.png")),
        emission_height_figure(os.path.join(out_dir, "k7_abstrahlhoehe.png")),
        missing_air_figure(os.path.join(out_dir, "k5_was_der_luft_fehlt.png")),
        uptake_bars_figure(os.path.join(out_dir, "b6_aufnahme_balken.png")),
        exchange_bars_figure(os.path.join(out_dir, "b9_austausch_balken.png")),
        common_currency_bars_figure(os.path.join(out_dir, "b10_waehrung_balken.png")),
        missing_air_bars_figure(os.path.join(out_dir, "k5_luft_balken_linie.png")),
        inertia_result_figure(os.path.join(out_dir, "k12b_traege_erde_ergebnis.png")),
        forcing_to_temperature_figure(os.path.join(out_dir, "k11_antrieb_zu_temperatur.png")),
        temperature_response_figure(os.path.join(out_dir, "k11b_g_T.png")),
        forest_type_map_figure(os.path.join(out_dir, "b5_waldtypen_karte.png")),
        literature_comparison_figure(os.path.join(out_dir, "v1b_literatur.png")),
    ]


# --------------------------------------------------------------------------
# K7: what CO2 does to the outgoing heat -- schematic spectrum
# --------------------------------------------------------------------------


def _planck_um(lam_um: NDArray, temp_k: float) -> NDArray:
    """Spectral radiance per micrometre [W m^-2 sr^-1 um^-1]."""
    h, c, k = 6.62607015e-34, 2.99792458e8, 1.380649e-23
    lam = lam_um * 1e-6
    return 2 * h * c**2 / lam**5 / np.expm1(h * c / (lam * k * temp_k)) * 1e-6


def co2_spectrum_figure(out_path: str) -> str:
    """Schematic: the Earth emits like a 288 K body except in the CO2 band
    around 15 um, where the emission comes from cold air high up (~220 K).
    More CO2 widens the band. Shape only -- not a radiative-transfer result."""
    _setup()
    lam = np.linspace(4.0, 30.0, 800)
    warm, cold = _planck_um(lam, 288.0), _planck_um(lam, 220.0)

    def band(width_um):
        return np.exp(-0.5 * ((lam - 15.0) / width_um) ** 4)

    today = warm - (warm - cold) * band(1.9)
    more = warm - (warm - cold) * band(2.4)

    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.07, right=0.78, bottom=0.14, top=0.92)
    _clean_axes(ax)
    ax.plot(lam, warm, color="#c9762c", linewidth=1.6, linestyle=(0, (5, 4)))
    ax.plot(lam, cold, color="#3b6ba5", linewidth=1.6, linestyle=(0, (5, 4)))
    ax.fill_between(lam, more, today, where=today > more, color=C_CARBON, alpha=0.30, linewidth=0)
    ax.plot(lam, today, color=C_INK, linewidth=3.0)
    ax.plot(lam, more, color=C_CARBON, linewidth=2.0)
    ax.set_xlim(4, 30)
    ax.set_ylim(0, warm.max() * 1.12)
    ax.set_yticks([])
    ax.set_xlabel("Wellenlänge [µm]")
    ax.set_ylabel("abgestrahlte Leistung (schematisch)")
    x = 30.3
    ax.annotate("so strahlt ein 15 °C warmer Boden", (24, _planck_um(np.array([24.0]), 288.0)[0]), xytext=(x, 0.86 * ax.get_ylim()[1]),
                fontsize=12, color="#9a5a1f", annotation_clip=False, va="center")
    ax.annotate("so strahlt −53 °C kalte Höhenluft", (24, _planck_um(np.array([24.0]), 220.0)[0]), xytext=(x, 0.32 * ax.get_ylim()[1]),
                fontsize=12, color="#25507e", annotation_clip=False, va="center")
    ax.text(x, 0.66 * ax.get_ylim()[1], "Abstrahlung der Erde heute", fontsize=12.5, color=C_INK, fontweight="bold",
            va="center")
    ax.text(x, 0.55 * ax.get_ylim()[1], "mit mehr CO$_2$: die Kerbe wird\nbreiter, grün = weniger raus", fontsize=12,
            color=C_CARBON, va="center")
    ax.text(15, 0.04 * ax.get_ylim()[1], "CO$_2$-Band", ha="center", fontsize=12, color=C_INK_MUTED)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# K8: why every kilogram does less in a fuller atmosphere
# --------------------------------------------------------------------------


def co2_saturation_figure(out_path: str) -> str:
    from nbs.constants import A_CO2_LOG_W_M2_PER_PPM, A_CO2_W_M2_PER_KG, KG_CO2_PER_PPM
    from nbs.response import background_co2_ppm

    _setup()
    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.07, right=0.97, bottom=0.14, top=0.86, wspace=0.28)
    for ax in (ax_l, ax_r):
        _clean_axes(ax)

    cbg = background_co2_ppm("ssp245")
    c = np.linspace(280.0, 720.0, 300)
    phi = A_CO2_LOG_W_M2_PER_PPM * np.log(c / 280.0)
    ax_l.plot(c, phi, color=C_CARBON, linewidth=3.0)
    for c0, year, col in ((float(cbg[0]), str(T_START), "#2f6fb7"), (float(cbg[-1]), "2100", "#b8357f")):
        slope = A_CO2_LOG_W_M2_PER_PPM / c0
        p0 = A_CO2_LOG_W_M2_PER_PPM * np.log(c0 / 280.0)
        xs = np.array([c0 - 90, c0 + 90])
        ax_l.plot(xs, p0 + slope * (xs - c0), color=col, linewidth=2.0, linestyle=(0, (5, 3)))
        ax_l.plot(c0, p0, "o", ms=9, color=col, mec="white", mew=1.6, zorder=5)
        ax_l.annotate(f"{year}: {c0:.0f} ppm", (c0, p0), xytext=(-12, 14), textcoords="offset points", ha="right",
                      fontsize=12, color=C_INK)
    ax_l.set_xlabel("CO$_2$-Konzentration [ppm]")
    ax_l.set_ylabel("Antrieb gegenüber 280 ppm [W/m²]")
    ax_l.set_title("Antrieb wächst logarithmisch", loc="left", fontsize=14, color=C_INK)
    ax_l.set_xlim(280, 720)
    ax_l.set_ylim(0, None)

    a_t = A_CO2_LOG_W_M2_PER_PPM / (cbg * KG_CO2_PER_PPM) * 1e15
    ax_r.plot(YEARS, a_t, color=C_CARBON, linewidth=3.0)
    ax_r.axhline(A_CO2_W_M2_PER_KG * 1e15, color=C_INK_MUTED, linewidth=1.5, linestyle=(0, (5, 4)))
    ax_r.text(YEARS[-1], A_CO2_W_M2_PER_KG * 1e15 + 0.02, "Lehrbuchkonstante 1,76", ha="right", va="bottom",
              fontsize=11.5, color=C_INK_MUTED)
    for i in (0, -1):
        ax_r.annotate(f"{a_t[i]:.2f}".replace(".", ","), (YEARS[i], a_t[i]), xytext=(10, 4) if i == 0 else (0, 12),
                      textcoords="offset points", ha="left" if i == 0 else "right", fontsize=12, color=C_INK,
                      fontweight="bold")
    ax_r.set_xlim(YEARS[0], YEARS[-1])
    ax_r.set_ylim(0.9, 1.9)
    ax_r.set_xticks([T_START, 2050, 2075, 2100])
    ax_r.set_ylabel("Wirkung je kg CO$_2$ [10$^{-15}$ W/m²]")
    ax_r.set_title("…also wirkt jedes kg später weniger (SSP2-4,5)", loc="left", fontsize=14, color=C_INK)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# K14: what each shell does to t* -- the ladder, in shell order
# --------------------------------------------------------------------------

LADDER_STEPS = (
    "nur Kohlenstoff\nim Baum",
    "+ Albedo",
    "+ Ozean und Land\ngeben zurück",
    "+ vollere\nAtmosphäre",
    "+ Erwärmung\nerhöht Störung",
)


def ladder_t_star(site: Site) -> list[float]:
    """t* after each shell, cumulative, at *site* (full model as the last step)."""
    from nbs.constants import A_CO2_W_M2_PER_KG
    from nbs.forcing import co2_flux_kg_per_yr, phi_albedo, phi_co2_background
    from nbs.pipeline import _background_temperature
    from nbs.response import background_co2_ppm, green_carbon

    g_t = green_temperature("ssp245")
    sp = _site_species(site)
    calm = simulate_deterministic(dataclasses.replace(sp, gamma_warming=0.0), np.zeros(len(YEARS)))
    warm = simulate_deterministic(sp, _background_temperature("ssp245"))
    product = float(light_product(site_key(site))[site_cell(site)])

    def t_of(phi):
        return t_star(convolve_response(g_t, phi), YEARS)

    def alb(traj):
        return phi_albedo(traj.closure, product, 1.0, sp)

    flux = co2_flux_kg_per_yr(calm.net_uptake_kgC_yr)
    naive = A_CO2_W_M2_PER_KG * np.cumsum(flux)
    rebound = A_CO2_W_M2_PER_KG * convolve_response(green_carbon_preindustrial(), flux)
    fuller = phi_co2_background(flux, green_carbon("ssp245"), background_co2_ppm("ssp245"))
    full = phi_co2_background(co2_flux_kg_per_yr(warm.net_uptake_kgC_yr), green_carbon("ssp245"),
                              background_co2_ppm("ssp245"))
    return [t_of(naive), t_of(naive + alb(calm)), t_of(rebound + alb(calm)), t_of(fuller + alb(calm)),
            t_of(full + alb(warm))]


def ladder_delta_t(site: Site) -> list[float]:
    """Temperature effect per tree in 2100 [K] after each shell, cumulative
    (same chain as ladder_t_star). Unlike t*, this does not jump when a site
    sits near the balance of carbon and albedo."""
    from nbs.constants import A_CO2_W_M2_PER_KG
    from nbs.forcing import co2_flux_kg_per_yr, phi_albedo, phi_co2_background
    from nbs.pipeline import _background_temperature
    from nbs.response import background_co2_ppm, green_carbon

    g_t = green_temperature("ssp245")
    sp = _site_species(site)
    calm = simulate_deterministic(dataclasses.replace(sp, gamma_warming=0.0), np.zeros(len(YEARS)))
    warm = simulate_deterministic(sp, _background_temperature("ssp245"))
    product = float(light_product(site_key(site))[site_cell(site)])

    def end(phi):
        return float(convolve_response(g_t, phi)[-1])

    def alb(traj):
        return phi_albedo(traj.closure, product, 1.0, sp)

    flux = co2_flux_kg_per_yr(calm.net_uptake_kgC_yr)
    naive = A_CO2_W_M2_PER_KG * np.cumsum(flux)
    rebound = A_CO2_W_M2_PER_KG * convolve_response(green_carbon_preindustrial(), flux)
    fuller = phi_co2_background(flux, green_carbon("ssp245"), background_co2_ppm("ssp245"))
    full = phi_co2_background(co2_flux_kg_per_yr(warm.net_uptake_kgC_yr), green_carbon("ssp245"),
                              background_co2_ppm("ssp245"))
    return [end(naive), end(naive + alb(calm)), end(rebound + alb(calm)), end(fuller + alb(calm)),
            end(full + alb(warm))]


def ladder_figure(out_path: str) -> str:
    """Temperature effect per tree in 2100 after each widening of the system
    boundary, both sites. Points, not bars (bars mean yearly exchange)."""
    _setup()
    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.09, right=0.86, bottom=0.25, top=0.92)
    _clean_axes(ax)
    x = np.arange(len(LADDER_STEPS))
    ax.axhline(0, color=C_INK_MUTED, linewidth=1.0)
    scale = 1e15
    for k, s in enumerate(SITES):
        v = np.array(ladder_delta_t(s)) * scale
        offs = (k - (len(SITES) - 1) / 2) * 0.12
        ax.plot(x + offs, v, color=s.color, linewidth=1.2, alpha=0.6)
        ax.plot(x + offs, v, marker=s.marker, ms=11, mfc=s.color, mec="white", mew=1.6, linestyle="none")
        for xi, vi in zip(x, v):
            # labels: first site below, second above, third to the right of its point
            xy_off, ha = ((0, -20), "center") if k == 0 else (((0, 12), "center") if k == 1 else ((10, -4), "left"))
            ax.annotate(f"{vi:+.0f}".replace("-", "−"), (xi + offs, vi), xytext=xy_off,
                        textcoords="offset points", ha=ha, fontsize=11.5, color=C_INK)
        ax.annotate(s.label, (x[-1] + offs, v[-1]), xytext=(30, 0), textcoords="offset points", va="center",
                    fontsize=13, fontweight="bold", color=s.color, annotation_clip=False)
    lo = min(min(ladder_delta_t(s_)) for s_ in SITES) * scale
    ax.set_ylim(lo * 1.15, max(30.0, -lo * 0.12))
    ax.set_xticks(x)
    ax.set_xticklabels(LADDER_STEPS, fontsize=11.5)
    ax.set_ylabel("Temperatur je Baum 2100 [10$^{-15}$ K]")
    return _save(fig, out_path)


def ladder_t_star_figure(out_path: str) -> str:
    _setup()
    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.84, bottom=0.25, top=0.92)
    _clean_axes(ax)
    x = np.arange(len(LADDER_STEPS))
    cap = 2160
    for k, s in enumerate(SITES):
        ts = ladder_t_star(s)
        ys = [cap if not np.isfinite(t) else t for t in ts]
        offs = (k - (len(SITES) - 1) / 2) * 0.08
        ax.plot(x + offs, ys, color=s.color, linewidth=2.4, drawstyle="steps-mid")
        ax.plot(x + offs, ys, marker=s.marker, ms=10, mfc=s.color, mec="white", mew=1.6, linestyle="none")
        for xi, t, y in zip(x, ts, ys):
            label = "nie" if not np.isfinite(t) else ("sofort" if t <= YEARS[0] else f"{t:.0f}")
            ax.annotate(label, (xi + offs, y), xytext=(0, 10 if k else -18), textcoords="offset points",
                        ha="center", fontsize=11.5, color=C_INK)
        ax.annotate(s.label, (x[-1] + offs, ys[-1]), xytext=(18, 0), textcoords="offset points", va="center",
                    fontsize=13, fontweight="bold", color=s.color, annotation_clip=False)
    ax.set_xticks(x)
    ax.set_xticklabels(LADDER_STEPS, fontsize=11.5)
    ax.set_ylim(2015, 2165)
    ax.set_ylabel("t*: ab hier dauerhaft kühlend")
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# V6: the temperature path -- does it reach 1.5 degC?
# --------------------------------------------------------------------------


def temperature_path_figure(out_path: str) -> str:
    from nbs.fair_module import run_fair_baseline
    from nbs.landscape import assign_species
    from nbs.map_plots import _breakeven_year_field
    from nbs.potential import _masked_global_delta_t, cascade, reverse_1p5

    _setup()
    base = run_fair_baseline("ssp245")
    years = YEARS[: len(base)]
    retain = (assign_species() != None) & ~np.isinf(_breakeven_year_field("ssp245"))  # noqa: E711
    dt4 = _masked_global_delta_t(retain, "ssp245")[: len(base)]
    final = cascade("ssp245")[-1]["delta_t_2150"]
    trees = base + dt4 * (final / float(_masked_global_delta_t(retain, "ssp245")[-1]))
    factor = reverse_1p5("ssp245")["mit_albedo_und_stoerung"]["vielfaches_der_modellierten_flaeche"]

    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.78, bottom=0.13, top=0.92)
    _clean_axes(ax)
    ax.axhline(1.5, color="#b2182b", linewidth=1.6, linestyle=(0, (5, 4)))
    ax.text(years[0] + 1, 1.55, "1,5 °C", color="#b2182b", fontsize=13, va="bottom")
    ax.fill_between(years, trees, base, color=C_CARBON, alpha=0.25, linewidth=0)
    ax.plot(years, base, color=C_INK_MUTED, linewidth=2.6)
    ax.plot(years, trees, color=C_CARBON, linewidth=2.6)
    ax.annotate("SSP2-4,5 ohne Aufforstung", (years[-1], base[-1]), xytext=(10, 6), textcoords="offset points",
                fontsize=12.5, color=C_INK, annotation_clip=False)
    ax.annotate(f"mit allen nutzbaren Flächen\n(−{abs(final):.2f} K bis 2100)".replace(".", ","),
                (years[-1], trees[-1]), xytext=(10, -22), textcoords="offset points", fontsize=12.5,
                color=C_CARBON, annotation_clip=False)
    ax.set_xlim(years[0], 2100)
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylim(0.8, max(base) * 1.08)
    ax.set_ylabel("globale Erwärmung [°C]")
    ax.text(0.02, 0.97, f"Für dauerhaft 1,5 °C ab 2050 bräuchte es das {factor:.1f}-Fache der Fläche".replace(".", ","),
            transform=ax.transAxes, fontsize=13, color=C_INK, fontweight="bold", va="top")
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# B10: a common currency at the tree -- both channels in watts
# --------------------------------------------------------------------------


def naive_co2_watts(site: Site) -> NDArray:
    """Heat the removed CO2 would hold back [W per tree], naively: every kg
    stays in the air and acts with the textbook 1.76e-15 W m^-2 kg^-1."""
    from nbs.constants import A_CO2_W_M2_PER_KG, A_EARTH_M2

    return A_CO2_W_M2_PER_KG * A_EARTH_M2 * site_uptake_kg_co2(site)


def tree_energy_figure(out_path: str) -> str:
    _setup()
    fig, axes = plt.subplots(1, 2, figsize=WIDE, dpi=FIG_DPI, sharey=True)
    fig.subplots_adjust(left=0.07, right=0.83, bottom=0.13, top=0.88, wspace=0.12)
    top = 0.0
    for ax, s in zip(axes, SITES):
        _clean_axes(ax)
        co2 = naive_co2_watts(s)
        alb = _shell_one_trajectory(s).closure * site_annual_watts(s)
        top = max(top, float(co2.max()), float(alb.max()))
        ax.plot(YEARS, co2, color=C_CARBON, linewidth=3.0)
        ax.plot(YEARS, alb, color=C_ALBEDO, linewidth=3.0)
        ax.set_title(s.label, loc="left", fontsize=15, color=s.color, fontweight="bold")
        ax.set_xlim(YEARS[0], YEARS[-1])
        ax.set_xticks([T_START, 2060, 2100])
        light_ahead = np.nonzero(alb[1:] >= co2[1:])[0]  # year 0: both zero
        if light_ahead.size:
            yr = int(YEARS[light_ahead[-1] + 2])
            ax.axvline(yr, color=C_INK_MUTED, linewidth=1.0, linestyle=(0, (4, 3)))
            ax.text(yr + 2, 0.93 * top, f"bis {yr - 1} überwiegt\ndie Albedo", fontsize=12, color=C_INK, va="top")
        else:
            ax.text(2030, 0.93 * top, "CO$_2$ überwiegt\nvom ersten Jahr an", fontsize=12, color=C_INK, va="top")
    axes[0].set_ylim(0, top * 1.05)
    axes[0].set_ylabel("Leistung je Baum [W]")
    axes[1].annotate("CO$_2$: zurückgehaltene\nWärmestrahlung (naiv)", (YEARS[-1], co2[-1]), xytext=(10, 0),
                     textcoords="offset points", va="center", fontsize=12, color=C_CARBON, annotation_clip=False)
    axes[1].annotate("Albedo: zusätzlich\nabsorbierte Strahlung", (YEARS[-1], alb[-1]), xytext=(10, 0),
                     textcoords="offset points", va="center", fontsize=12, color=C_ALBEDO, annotation_clip=False)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# K3: what is left of one removed kilogram -- Joos et al. (2013)
# --------------------------------------------------------------------------


def carbon_response_figure(out_path: str) -> str:
    _setup()
    g = green_carbon_preindustrial()
    t = YEARS - YEARS[0]
    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.95, bottom=0.14, top=0.92)
    _clean_axes(ax)
    ax.fill_between(t, g, 1.0, color=C_CARBON, alpha=0.10, linewidth=0)
    ax.plot(t, g, color=C_CARBON, linewidth=3.0)
    for yr in (20, 75, 125):
        ax.plot(yr, g[yr], "o", ms=9, color=C_CARBON, mec="white", mew=1.6, zorder=5, clip_on=False)
        ax.annotate(f"nach {yr} Jahren: {100 * g[yr]:.0f} %", (yr, g[yr]), xytext=(-6 if yr == 125 else 6, 12),
                    textcoords="offset points", fontsize=12.5, color=C_INK, ha="right" if yr == 125 else "left")
    ax.text(62, 0.88, "von Ozean und Land zurückgegeben", fontsize=13, color=C_INK_MUTED, ha="center")
    ax.set_xlim(0, 125)
    ax.set_ylim(0, 1.02)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0 %", "25 %", "50 %", "75 %", "100 %"])
    ax.set_xlabel("Jahre nach der Entnahme")
    ax.set_ylabel("g$_C$: was davon der Luft noch fehlt")
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# K11: from forcing to temperature -- the Earth as a pot on a hotplate
# --------------------------------------------------------------------------


def forcing_to_temperature_figure(out_path: str) -> str:
    """Step and pulse response of the model's own g_T (FaIR, calibrated)."""
    import pandas as pd

    from nbs.fair_module import _PARAMS_CSV, CENTRAL_MEMBER

    _setup()
    lam = float(pd.read_csv(_PARAMS_CSV, index_col=0).loc[CENTRAL_MEMBER, "ocean_heat_transfer[0]"])
    g = green_temperature("ssp245")
    t = YEARS - YEARS[0]
    step = np.cumsum(g)

    fig, (ax_s, ax_p) = plt.subplots(1, 2, figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.07, right=0.97, bottom=0.14, top=0.86, wspace=0.25)
    for ax in (ax_s, ax_p):
        _clean_axes(ax)
        ax.set_xlim(0, 125)
        ax.set_xlabel("Jahre")

    eq = 1.0 / lam
    ax_s.axhline(eq, color=C_INK_MUTED, linewidth=1.4, linestyle=(0, (5, 4)))
    ax_s.text(124, eq + 0.015, f"Gleichgewicht φ/Λ = {eq:.2f} K".replace(".", ","), ha="right", va="bottom",
              fontsize=12, color=C_INK_MUTED)
    ax_s.plot(t, step, color="#b2182b", linewidth=3.0)
    i5 = 5
    ax_s.annotate(f"nach {i5} Jahren {step[i5]:.2f} K:\nOberfläche und Mischschicht".replace(".", ","),
                  (i5, step[i5]), xytext=(18, -46), textcoords="offset points", fontsize=12, color=C_INK,
                  arrowprops=dict(arrowstyle="-", color=C_INK_MUTED, lw=0.8))
    ax_s.annotate(f"nach 125 Jahren {step[-1]:.2f} K:\nder tiefe Ozean heizt sich langsam mit".replace(".", ","),
                  (124, step[-1]), xytext=(-250, -60), textcoords="offset points", fontsize=12, color=C_INK,
                  arrowprops=dict(arrowstyle="-", color=C_INK_MUTED, lw=0.8))
    ax_s.set_ylim(0, eq * 1.12)
    ax_s.set_ylabel("Erwärmung [K]")
    ax_s.set_title("Herdplatte an: 1 W/m² dauerhaft", loc="left", fontsize=14, color=C_INK)

    ax_p.fill_between(t, 0, g, color="#b2182b", alpha=0.15, linewidth=0)
    ax_p.plot(t, g, color="#b2182b", linewidth=3.0)
    ax_p.annotate(f"{g[0]:.2f} K im selben Jahr".replace(".", ","), (0, g[0]), xytext=(14, -4),
                  textcoords="offset points", fontsize=12, color=C_INK)
    ax_p.annotate(f"nach 20 Jahren noch {100 * g[20] / g[0]:.0f} % davon —\nklein, aber lang: das summiert sich",
                  (20, g[20]), xytext=(30, 0.05), textcoords="data", fontsize=12, color=C_INK, ha="left",
                  arrowprops=dict(arrowstyle="-", color=C_INK_MUTED, lw=0.8))
    ax_p.set_ylim(0, g[0] * 1.15)
    ax_p.set_ylabel("Erwärmung [K]")
    ax_p.set_title("Herdplatte ein Jahr an: 1 W/m² für ein Jahr = g$_T$", loc="left", fontsize=14, color=C_INK)
    return _save(fig, out_path)


def temperature_response_figure(out_path: str) -> str:
    """g_T alone, for the convolution slide: the model's own response (FaIR)."""
    _setup()
    g = green_temperature("ssp245")
    t = YEARS - YEARS[0]
    fig, ax = plt.subplots(figsize=(9.0, 3.86), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.11, right=0.97, bottom=0.2, top=0.93)
    _clean_axes(ax)
    ax.fill_between(t, 0, g, color="#b2182b", alpha=0.15, linewidth=0)
    ax.plot(t, g, color="#b2182b", linewidth=3.0)
    ax.set_xlim(0, 125)
    ax.set_ylim(0, g[0] * 1.15)
    ax.set_xlabel("Jahre nach einem Jahr mit 1 W/m² Antrieb")
    ax.set_ylabel("g$_T$ [K]")
    ax.text(12, 0.8 * g[0], "schnell: Oberfläche und Mischschicht", fontsize=13, color=C_INK)
    ax.text(60, 0.12 * g[0], "lang und klein: tiefer Ozean", fontsize=13, color=C_INK)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# K3 (new): one year's uptake of the known tree, and what of it stays missing
# --------------------------------------------------------------------------


def carbon_pulse_figure(out_path: str, site_name: str = "Aachen", pulse_year: int = 2050) -> str:
    """Left: yearly CO2 removal of both known trees (Aachen, Fairbanks; from the
    growth curves of the Bäume chapter). Right: one year's removal at
    *site_name* and what of it is still missing from the air later -- the
    Joos g_C applied to that pulse. Site colours as on the profile slide."""
    _setup()
    site = next(s_ for s_ in SITES if s_.name == site_name)
    removal = {s_.name: M_CO2_PER_C * _shell_one_trajectory(s_).net_uptake_kgC_yr for s_ in SITES}
    g = green_carbon_preindustrial()
    k = int(pulse_year - YEARS[0])
    pulse = float(removal[site_name][k])

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=WIDE, dpi=FIG_DPI, gridspec_kw={"width_ratios": [1.0, 1.15]})
    fig.subplots_adjust(left=0.07, right=0.97, bottom=0.14, top=0.88, wspace=0.28)
    for ax in (ax_l, ax_r):
        _clean_axes(ax)

    top = max(float(r.max()) for r in removal.values())
    for s_ in SITES:
        r = removal[s_.name]
        if s_.name == site_name:
            ax_l.fill_between(YEARS, 0, r, color=s_.color, alpha=0.22, linewidth=0, step="mid")
            ax_l.plot(YEARS, r, color=s_.color, linewidth=2.2, drawstyle="steps-mid")
            ax_l.bar([pulse_year], [pulse], width=1.6, color=s_.color, zorder=4)
            ax_l.annotate(f"{pulse_year}: {pulse:.1f} kg".replace(".", ","), (pulse_year, pulse), xytext=(12, 4),
                          textcoords="offset points", fontsize=12.5, color=C_INK, fontweight="bold")
        else:
            ax_l.plot(YEARS, r, color=s_.color, linewidth=2.4, linestyle=(0, (5, 3)))
        i_lab = int(np.argmax(r)) + 25
        ax_l.text(YEARS[i_lab], r[i_lab] + 0.12 * top, s_.label, color=s_.color, fontsize=13, fontweight="bold")
    ax_l.set_xlim(YEARS[0], YEARS[-1])
    ax_l.set_ylim(0, top * 1.18)
    ax_l.set_xticks([T_START, 2050, 2075, 2100])
    ax_l.set_ylabel("CO$_2$-Aufnahme [kg je Jahr]")
    ax_l.set_title("Jahr für Jahr, aus den Wachstumskurven", loc="left", fontsize=14, color=C_INK)

    t = YEARS[k:]
    missing = pulse * g[: len(t)]
    col = site.color
    ax_r.plot(t, np.full(len(t), pulse), color=col, linewidth=2.0, linestyle=(0, (5, 4)))
    ax_r.fill_between(t, missing, pulse, color=col, alpha=0.10, linewidth=0)
    ax_r.plot(t, missing, color=col, linewidth=3.2)
    for yrs, off, ha in ((20, (-6, -32), "right"), (75, (0, 14), "center")):
        ax_r.plot(pulse_year + yrs, pulse * g[yrs], "o", ms=9, color=col, mec="white", mew=1.6, zorder=5)
        ax_r.annotate(f"nach {yrs} Jahren: {100 * g[yrs]:.0f} %", (pulse_year + yrs, pulse * g[yrs]), xytext=off,
                      textcoords="offset points", fontsize=12.5, color=C_INK, ha=ha)
    for s_ in SITES:
        if s_.name == site_name:
            continue
        p2 = float(removal[s_.name][k])
        ax_r.plot(t, np.full(len(t), p2), color=s_.color, linewidth=1.4, linestyle=(0, (1, 2)))
        ax_r.plot(t, p2 * g[: len(t)], color=s_.color, linewidth=2.4, linestyle=(0, (5, 3)))
        ax_r.text(pulse_year - 2, p2, f"{s_.label}\n{p2:.1f} kg".replace(".", ","), color=s_.color,
                  fontsize=12.5, fontweight="bold", ha="right", va="center")
    ax_r.text(pulse_year - 2, pulse, f"{site_name}\n{pulse:.1f} kg".replace(".", ","), color=col,
              fontsize=12.5, fontweight="bold", ha="right", va="center")
    ax_r.text(pulse_year + 2, pulse * 1.04, "am Baum bilanziert: fehlt für immer", fontsize=12, color=C_INK_MUTED)
    ax_r.text(pulse_year + 45, pulse * 0.78, "von Ozean und Land\nzurückgegeben", fontsize=12, color=C_INK_MUTED,
              ha="center")
    ax_r.set_xlim(YEARS[0], YEARS[-1])
    ax_r.set_xticks([T_START, 2050, 2075, 2100])
    ax_r.set_ylim(0, pulse * 1.18)
    ax_r.set_ylabel("davon fehlt der Luft noch [kg]")
    ax_r.set_title(f"Das Jahr {pulse_year}: was davon der Luft fehlt", loc="left", fontsize=14, color=C_INK)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# K7 (new): why CO2 warms -- the emission height picture
# --------------------------------------------------------------------------

SIGMA = 5.670374419e-8
LAPSE_K_PER_KM = 6.5
T_SURFACE_K = 288.0
T_EMISSION_K = 255.0


def emission_height_figure(out_path: str) -> str:
    """Textbook picture (e.g. Pierrehumbert 2011, Physics Today 64(1), 33):
    the Earth radiates to space from the height where the air becomes
    transparent to heat radiation; more CO2 lifts that height into colder air.
    Doubling CO2 = 3.7 W/m^2 less out (5.35 ln 2), i.e. ~1 K colder at the
    emission height, ~150 m higher at 6.5 K/km."""
    _setup()
    z_e = (T_SURFACE_K - T_EMISSION_K) / LAPSE_K_PER_KM
    out_now = SIGMA * T_EMISSION_K**4
    d_f = 5.35 * np.log(2.0)
    d_t = d_f / (4 * SIGMA * T_EMISSION_K**3)
    d_z = d_t / LAPSE_K_PER_KM

    def de_(x, nd=0):
        return f"{x:.{nd}f}".replace(".", ",").replace("-", "−")

    fig, (ax, ax_t) = plt.subplots(1, 2, figsize=WIDE, dpi=FIG_DPI, gridspec_kw={"width_ratios": [1.45, 1.0]})
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.14, top=0.9, wspace=0.12)
    _clean_axes(ax)
    z = np.linspace(0, 11, 100)
    ax.plot(T_SURFACE_K - LAPSE_K_PER_KM * z - 273.15, z, color=C_INK, linewidth=2.6)
    t_now = T_SURFACE_K - LAPSE_K_PER_KM * z_e - 273.15
    t_up = T_SURFACE_K - LAPSE_K_PER_KM * (z_e + 1.0) - 273.15
    for zz, tt, col in ((z_e, t_now, "#2f6fb7"), (z_e + 1.0, t_up, "#b2182b")):
        ax.plot([-60, tt], [zz, zz], color=col, linewidth=1.6, linestyle=(0, (5, 3)))
        ax.plot(tt, zz, "o", ms=11, color=col, mec="white", mew=1.8, zorder=5)
    ax.text(t_now + 4, z_e - 0.1, f"heute: ab hier geht die Wärme ins All\n{de_(z_e, 1)} km Höhe, {de_(t_now)} °C",
            fontsize=12, color="#2f6fb7", va="bottom")
    ax.text(t_up + 4, z_e + 1.15, "mehr CO$_2$: diese Höhe steigt\n(hier überzeichnet)", fontsize=12, color="#b2182b",
            va="bottom")
    ax.annotate("", xy=(-35, z_e + 1.0), xytext=(-35, z_e), arrowprops=dict(arrowstyle="->", color="#b2182b", lw=2))
    ax.text(-58, 0.35, "Boden: 15 °C", fontsize=12, color=C_INK_MUTED)
    ax.set_xlim(-60, 20)
    ax.set_ylim(0, 11)
    ax.set_xticks([-60, -40, -20, 0, 20])
    ax.set_xticklabels(["−60", "−40", "−20", "0", "20"])
    ax.set_xlabel("Lufttemperatur [°C]")
    ax.set_ylabel("Höhe [km]")
    ax.set_title("Nach oben wird es kälter", loc="left", fontsize=14, color=C_INK)

    ax_t.axis("off")
    rows = [
        ("rein, von der Sonne", f"{de_(out_now)} W/m²", C_INK),
        ("raus, heute", f"{de_(out_now)} W/m²", "#2f6fb7"),
        ("raus, doppelt so viel CO$_2$", f"{de_(out_now - d_f)} W/m²", "#b2182b"),
    ]
    for k, (lab, val, col) in enumerate(rows):
        y = 0.86 - 0.17 * k
        ax_t.text(0.0, y, lab, fontsize=14, color=C_INK, transform=ax_t.transAxes, va="center")
        ax_t.text(1.0, y, val, fontsize=16, color=col, fontweight="bold", transform=ax_t.transAxes, va="center",
                  ha="right")
    ax_t.plot([0, 1], [0.44, 0.44], color=C_INK_MUTED, linewidth=1.0, transform=ax_t.transAxes)
    ax_t.text(0.0, 0.33, f"{de_(d_f, 1)} W/m² bleiben drin", fontsize=17, color="#b2182b", fontweight="bold",
              transform=ax_t.transAxes, va="center")
    ax_t.text(0.0, 0.14, f"Die Abstrahlhöhe liegt {de_(1000 * d_z)} m höher und {de_(d_t, 1)} K kälter.\n"
              "Die Erde erwärmt sich, bis sie wieder\nso viel abstrahlt, wie hereinkommt.",
              fontsize=12.5, color=C_INK, transform=ax_t.transAxes, va="center")
    ax_t.set_title("Kälteres strahlt weniger", loc="left", fontsize=14, color=C_INK)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# Klima, compact: (1) what the air really lacks, (2) the Earth warms slowly
# --------------------------------------------------------------------------


def missing_air_figure(out_path: str, pulse_year: int = 2050) -> str:
    """Left: one year's removal (2050) at both sites and what of it the air still
    lacks later (Joos g_C). Right: all years summed -- the CO2 profile -- with
    the uptake curve of the Bäume chapter dashed."""
    _setup()
    g = green_carbon_preindustrial()
    k = int(pulse_year - YEARS[0])
    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=WIDE, dpi=FIG_DPI, gridspec_kw={"width_ratios": [1.0, 1.15]})
    fig.subplots_adjust(left=0.07, right=0.86, bottom=0.14, top=0.88, wspace=0.3)
    for ax in (ax_l, ax_r):
        _clean_axes(ax)
        ax.set_xlim(YEARS[0], YEARS[-1])
        ax.set_xticks([T_START, 2050, 2075, 2100])

    t = YEARS[k:]
    for s in SITES:
        flux = -M_CO2_PER_C * _shell_one_trajectory(s).net_uptake_kgC_yr  # into the air, negative
        pulse = float(-flux[k])
        ax_l.plot(t, np.full(len(t), pulse), color=s.color, linewidth=1.4, linestyle=(0, (5, 3)))
        ax_l.plot(t, pulse * g[: len(t)], color=s.color, linewidth=3.0)
        ax_l.text(pulse_year - 2, pulse, f"{s.label}\n{pulse:.1f} kg".replace(".", ","), color=s.color, fontsize=12,
                  fontweight="bold", ha="right", va="center")
        tree = -np.cumsum(flux)
        air = -convolve_response(g, flux)
        ax_r.fill_between(YEARS, air, tree, color=s.color, alpha=0.08, linewidth=0)
        ax_r.plot(YEARS, tree, color=s.color, linewidth=1.8, linestyle=(0, (5, 4)))
        ax_r.plot(YEARS, air, color=s.color, linewidth=3.0)
        ax_r.annotate(f"{air[-1]:.0f} von {tree[-1]:.0f} kg", (YEARS[-1], air[-1]), xytext=(8, 0),
                      textcoords="offset points", va="center", fontsize=12, color=s.color, fontweight="bold",
                      annotation_clip=False)
    a_pulse = float(M_CO2_PER_C * _shell_one_trajectory(SITES[0]).net_uptake_kgC_yr[k])
    ax_l.annotate(f"nach 20 Jahren\nnoch {100 * g[20]:.0f} %", (pulse_year + 20, a_pulse * g[20]), xytext=(30, 48),
                  textcoords="offset points", fontsize=12, color=C_INK,
                  arrowprops=dict(arrowstyle="-", color=C_INK_MUTED, lw=0.8))
    ax_l.annotate(f"nach 50 Jahren\nnoch {100 * g[50]:.0f} %", (pulse_year + 50, a_pulse * g[50]), xytext=(4, 34),
                  textcoords="offset points", fontsize=12, color=C_INK, ha="center",
                  arrowprops=dict(arrowstyle="-", color=C_INK_MUTED, lw=0.8))
    ax_l.set_ylim(0, a_pulse * 1.2)
    ax_l.set_ylabel("fehlt der Luft [kg CO$_2$]")
    ax_l.set_title(f"Ein Jahr ({pulse_year}): gestrichelt am Baum, durchgezogen in der Luft", loc="left",
                   fontsize=12.5, color=C_INK)
    ax_r.set_ylim(0, None)
    ax_r.set_title("Alle Jahre zusammen", loc="left", fontsize=12.5, color=C_INK)
    return _save(fig, out_path)


def inertia_result_figure(out_path: str) -> str:
    """Left: how the Earth answers 1 W/m^2 that stays on (model's own g_T, summed).
    Right: the net temperature effect per tree at both sites."""
    import pandas as pd

    from nbs.fair_module import _PARAMS_CSV, CENTRAL_MEMBER

    _setup()
    lam = float(pd.read_csv(_PARAMS_CSV, index_col=0).loc[CENTRAL_MEMBER, "ocean_heat_transfer[0]"])
    g = green_temperature("ssp245")
    t = YEARS - YEARS[0]
    step = np.cumsum(g)
    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=HALF, dpi=FIG_DPI, gridspec_kw={"width_ratios": [1.0, 1.25]})
    fig.subplots_adjust(left=0.1, right=0.78, bottom=0.12, top=0.9, wspace=0.45)
    for ax in (ax_l, ax_r):
        _clean_axes(ax)

    eq = 1.0 / lam
    ax_l.axhline(eq, color=C_INK_MUTED, linewidth=1.2, linestyle=(0, (5, 4)))
    ax_l.text(t[-1] - 1, eq + 0.02, f"Gleichgewicht {eq:.1f} K".replace(".", ","), ha="right", va="bottom", fontsize=12,
              color=C_INK_MUTED)
    ax_l.plot(t, step, color="#b2182b", linewidth=3.0)
    for yr, off in ((5, (14, -18)), (int(t[-1]) - 5, (-4, -40))):
        ax_l.plot(yr, step[yr], "o", ms=8, color="#b2182b", mec="white", mew=1.5)
        ax_l.annotate(f"nach {yr} Jahren: {step[yr]:.1f} K".replace(".", ","), (yr, step[yr]), xytext=off,
                      textcoords="offset points", fontsize=12, color=C_INK, ha="left" if yr < 50 else "right")
    ax_l.set_xlim(0, t[-1])
    ax_l.set_ylim(0, eq * 1.15)
    ax_l.set_xlabel("Jahre")
    ax_l.set_ylabel("Erwärmung [K]")
    ax_l.set_title("Sprungantwort auf 1 W/m²", loc="left", fontsize=12.5, color=C_INK)

    scale = 1e15
    ax_r.axhline(0, color=C_INK_MUTED, linewidth=0.9)
    from nbs.config import ModelConfig

    for s in SITES:
        r = run_site(s)
        key = site_key(s)
        product = float(light_product(key)[site_cell(s)])
        co2 = run_single_tree(key, s.lat, delta_alpha=product, q_sw=1.0, lon_deg=s.lon,
                              config=ModelConfig(albedo=False)).delta_t
        ax_r.plot(YEARS, r.delta_t * scale, color=s.color, linewidth=3.0)
        share = r.delta_t[-1] / co2[-1]
        ax_r.annotate(s.label, (YEARS[-1], r.delta_t[-1] * scale), xytext=(8, 0),
                      textcoords="offset points", va="center", fontsize=12, color=s.color, fontweight="bold",
                      annotation_clip=False)
    ax_r.set_xlim(YEARS[0], YEARS[-1])
    ax_r.set_xticks([T_START, 2050, 2075, 2100])
    ax_r.set_ylabel("Temperatur je Baum [10$^{-15}$ K]")
    ax_r.set_title("Je Baum", loc="left", fontsize=12.5, color=C_INK)
    ax_r.text(2027, ax_r.get_ylim()[0] * 0.9, "unter null: kühlt", fontsize=11.5, color=C_INK_MUTED)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# Visual language (2026-10-05): bars = what one tree exchanges per year
# (tree accounting); continuous lines = with the climate system's response.
# --------------------------------------------------------------------------

DECADES = np.arange(2030, YEARS[-1] + 1, 10)
_IDX = (DECADES - YEARS[0]).astype(int)
_BAR_W = 2.9


def _annual_uptake(site: Site) -> NDArray:
    """kg CO2 taken out of the air in each year (tree accounting)."""
    return M_CO2_PER_C * _shell_one_trajectory(site).net_uptake_kgC_yr


def _annual_watts(site: Site) -> NDArray:
    """W of extra absorbed sunlight in each year (tree accounting)."""
    return _shell_one_trajectory(site).closure * site_annual_watts(site)


def _decade_axes(ax) -> None:
    _clean_axes(ax)
    ax.set_xlim(DECADES[0] - 7, DECADES[-1] + 7)
    ax.set_xticks([2030, 2050, 2070, 2090])


def uptake_bars_figure(out_path: str) -> str:
    """B6: CO2 one tree takes up per year, as a continuous line from planting (start year) to 2100;
    the peak marked, the sum to 2100 at the right."""
    _setup()
    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.8, bottom=0.13, top=0.92)
    _clean_axes(ax)
    ax.set_xlim(YEARS[0], YEARS[-1])
    ax.set_xticks([T_START, 2050, 2075, 2100])
    for k, s in enumerate(SITES):
        u = _annual_uptake(s)
        ax.plot(YEARS, u, color=s.color, linewidth=3.0)
        i = int(np.argmax(u))
        ax.plot(YEARS[i], u[i], "o", ms=8, color=s.color, mec="white", mew=1.5, zorder=5)
        ax.annotate(f"{u[i]:.1f} kg/a um {YEARS[i]}".replace(".", ","), (YEARS[i], u[i]), xytext=(8, 6),
                    textcoords="offset points", fontsize=12, color=s.color)
        ax.text(1.01, 0.75 - 0.18 * k, f"{s.label}\n{float(u.sum()):.0f} kg bis 2100", transform=ax.transAxes,
                fontsize=13, color=s.color, fontweight="bold", va="center")
    ax.set_ylim(0, None)
    ax.set_ylabel("CO$_2$-Aufnahme [kg je Jahr]")
    ax.set_title(f"Je Baum, gepflanzt {T_START}", loc="left", fontsize=13, color=C_INK)
    return _save(fig, out_path)


def uptake_panel_figure(out_path: str) -> str:
    """B6 for the side panel next to the forest-type map: the same three lines, sized to the narrow
    panel (ticks ~19 px on the slide); each line named at its peak, the sums stand in the takeaway."""
    _setup()
    # figure as large as its slot in the side panel of slide 12, so ticks and labels reach the hall minimum (2026-10-11)
    fig, ax = plt.subplots(figsize=(3.4, 2.75), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.15, right=0.96, bottom=0.12, top=0.97)
    _clean_axes(ax)
    ax.set_xlim(YEARS[0], YEARS[-1])
    ax.set_xticks([T_START, 2060, 2100])
    peaks = []
    for s in SITES:
        u = _annual_uptake(s)
        ax.plot(YEARS, u, color=s.color, linewidth=3.0)
        i = int(np.argmax(u))
        ax.plot(YEARS[i], u[i], "o", ms=8, color=s.color, mec="white", mew=1.5, zorder=5)
        peaks.append((float(u[i]), s))
    # names in the empty upper right, in the order of the curves (highest first)
    for k, (_, s) in enumerate(sorted(peaks, key=lambda p: -p[0])):
        ax.text(0.98, 0.96 - 0.11 * k, s.label, transform=ax.transAxes, ha="right", va="top",
                fontsize=12.5, color=s.color, fontweight="bold")
    ax.set_ylim(0, None)
    ax.set_ylabel("kg CO$_2$ je Jahr")
    return _save(fig, out_path)


def stock_panel_figure(out_path: str) -> str:
    """B6 as carbon stock, for the side panel next to the forest-type map: the stock of one tree at the
    three sites (disturbance at today's rate), as the Aachen curve on the slide before; names upper left."""
    _setup()
    # sized to its box on the slide (520 x 581 px) at the scale of the other model charts (~0.675 px per figure px),
    # so lines and type match them
    fig, ax = plt.subplots(figsize=(4.8, 5.4), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.13, right=0.97, bottom=0.07, top=0.98)
    _clean_axes(ax)
    ax.set_xlim(YEARS[0], YEARS[-1])
    ax.set_xticks([T_START, 2060, 2100])
    ends = []
    for s in SITES:
        m = _shell_one_trajectory(s).stock_kgC
        ax.plot(YEARS, m, color=s.color, linewidth=2.6)
        ends.append((float(m[-1]), s))
    # each name just above its own curve, towards the end (a little higher on the steeper curves)
    xl = 2080
    for _, s in ends:
        m = _shell_one_trajectory(s).stock_kgC
        ax.annotate(s.label, (xl, float(np.interp(xl, YEARS, m))), xytext=(0, {"Fairbanks": 12, "Aachen": 20}.get(s.name, 30)), textcoords="offset points",
                    ha="center", va="bottom", fontsize=13.5, color=s.color, fontweight="bold")
    ax.set_ylim(0, None)
    ax.set_ylabel("Kohlenstoffvorrat mᶜ$_{Baum}$ [kg C]")
    return _save(fig, out_path)


def exchange_bars_figure(out_path: str) -> str:
    """B9: what one tree exchanges per year: kg CO2 (left) and W of light (right)."""
    _setup()
    fig, (ax_c, ax_w) = plt.subplots(1, 2, figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.07, right=0.97, bottom=0.13, top=0.86, wspace=0.3)
    for k, s in enumerate(SITES):
        x = DECADES + (k - (len(SITES) - 1) / 2) * _BAR_W
        ax_c.bar(x, _annual_uptake(s)[_IDX], width=_BAR_W * 0.92, color=s.color, label=s.label)
        ax_w.bar(x, _annual_watts(s)[_IDX], width=_BAR_W * 0.92, color=s.color)
    for ax in (ax_c, ax_w):
        _decade_axes(ax)
        ax.set_xticks([2030, 2060, 2090])
    ax_c.set_title("CO$_2$-Aufnahme [kg je Jahr]", loc="left", fontsize=14, color=C_INK)
    ax_w.set_title("zusätzlich absorbierte Strahlung [W]", loc="left", fontsize=14, color=C_INK)
    ax_c.legend(frameon=False, fontsize=12, loc="upper right")
    fig.text(0.5, 0.5, "?", fontsize=40, ha="center", va="center", color=C_INK_MUTED)
    return _save(fig, out_path)


def common_currency_bars_figure(out_path: str) -> str:
    """B10: both channels in W, both sites, one plot. Light warms (up), the CO2
    the tree has taken so far holds back heat (cools, down; naive: all of it
    stays missing, textbook effect per kg). Dot = sum."""
    import matplotlib.colors as mcolors
    from matplotlib.patches import Patch

    _setup()
    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.79, bottom=0.13, top=0.92)
    _decade_axes(ax)
    ax.axhline(0, color=C_INK_MUTED, linewidth=0.9)
    for k, s in enumerate(SITES):
        x = DECADES + (k - (len(SITES) - 1) / 2) * _BAR_W
        light = _annual_watts(s)[_IDX]
        co2 = -naive_co2_watts(s)[_IDX]
        hatch = (None, "///", "\\\\\\")[k]
        ax.bar(x, light, width=_BAR_W * 0.92, color=C_ALBEDO, hatch=hatch, edgecolor="white", linewidth=0)
        ax.bar(x, co2, width=_BAR_W * 0.92, color=C_CARBON, hatch=hatch, edgecolor="white", linewidth=0)
        ax.plot(x, light + co2, "o", ms=7, color=C_NET, mec="white", mew=1.2, zorder=5)
    ax.set_ylabel("Leistung je Baum [W]")
    ax.text(DECADES[0] - 6, ax.get_ylim()[1] * 0.85, "wärmt", fontsize=12, color=C_INK_MUTED)
    ax.text(DECADES[0] - 6, ax.get_ylim()[0] * 0.92, "kühlt", fontsize=12, color=C_INK_MUTED)
    handles = [Patch(facecolor=C_ALBEDO, label="Albedo"),
               Patch(facecolor=C_CARBON, label="CO$_2$ (naiv: bleibt\nweg, Lehrbuchwert)"),
               plt.Line2D([], [], marker="o", ls="", color=C_NET, ms=7, label="Summe"),
               *[Patch(facecolor="#9a9a9a", hatch=h, edgecolor="white", label=f"{s_.label}{t}")
                 for s_, h, t in zip(SITES, (None, "///", "\\\\\\"), ("", "", ""))]]
    fig.legend(handles=handles, loc="center left", bbox_to_anchor=(0.8, 0.5), frameon=False, fontsize=12,
               labelspacing=1.0)
    return _save(fig, out_path)


def irf_figure(out_path: str, horizon: int = 150, figsize: tuple[float, float] = (7.2, 3.5), left: float = 0.17,
               ylabel: str = "CO$_2$-Änderung der Atmosphäre") -> str:
    """K3: the carbon cycle answers a pulse -- the same impulse response (Joos et al. 2013) for one
    tonne emitted (what stays in the air, up) and one tonne removed (what the air still lacks, down)."""
    _setup()
    g = green_carbon_preindustrial(horizon + 1)
    t = np.arange(horizon + 1)
    c_em, c_rm = "#8c6d5a", "#2e7d4f"  # emission: earth brown; removal: the deck's CO2 green
    fig, ax = plt.subplots(figsize=figsize, dpi=FIG_DPI)  # sized to its place on the slide: ticks ~19 px
    fig.subplots_adjust(left=left, right=0.97, bottom=0.17, top=0.95)
    _clean_axes(ax)
    # the removal on its own (invisible) axes, a hair lower at the top: the deck shows it one click later
    l, b, w, h = ax.get_position().bounds
    ax_rm = fig.add_axes((l, b, w, h - 0.0045))
    ax_rm.axis("off")
    ax.axhline(0, color=C_INK_MUTED, linewidth=1.0)
    ax.fill_between(t, 0, g, color=c_em, alpha=0.12, linewidth=0)
    ax_rm.fill_between(t, 0, -g, color=c_rm, alpha=0.12, linewidth=0)
    ax.plot(t, g, color=c_em, linewidth=3.0)
    ax_rm.plot(t, -g, color=c_rm, linewidth=3.0)
    for yr in (20, 50, 100):
        ax.plot(yr, g[yr], "o", ms=7, color=c_em, mec="white", mew=1.5, zorder=5)
        ax_rm.plot(yr, -g[yr], "o", ms=7, color=c_rm, mec="white", mew=1.5, zorder=5)
        ax.annotate(f"{100 * g[yr]:.0f} %", (yr, g[yr]), xytext=(0, 10), textcoords="offset points", ha="center",
                    fontsize=12, color=C_INK)
    # the limit the curve tends to: the share that stays for good (Joos et al. 2013, a0)
    from nbs.response import _JOOS_A0 as a0
    ax.axhline(a0, color=c_em, linewidth=1.1, linestyle=(0, (4, 4)), alpha=0.8)
    ax_rm.axhline(-a0, color=c_rm, linewidth=1.1, linestyle=(0, (4, 4)), alpha=0.8)
    ax.text(horizon, a0 - 0.05, f"→ {100 * a0:.0f} % dauerhaft", ha="right", va="top", fontsize=12, color=c_em)
    ax_rm.text(horizon, -a0 + 0.05, f"→ {100 * a0:.0f} % dauerhaft", ha="right", va="bottom", fontsize=12, color=c_rm)
    ax.text(2, 1.08, "Zusatzemission von 1 t CO$_2$", fontsize=12.5, color=c_em, fontweight="bold")
    ax_rm.text(2, -1.14, "Entnahme von 1 t CO$_2$", fontsize=12.5, color=c_rm, fontweight="bold")
    # same data limits; the shorter box scales y by 0.6 %, under 2 px on the slide
    lo, hi = -1.25, 1.25
    ax_rm.set_xlim(0, horizon)
    ax_rm.set_ylim(lo, hi - (hi - lo) * 0.0045 / h)
    ax.set_xlim(0, horizon)
    ax.set_ylim(-1.25, 1.25)
    ax.set_yticks([-1, -0.5, 0, 0.5, 1])
    ax.set_yticklabels(["−1 t", "−0,5 t", "0", "+0,5 t", "+1 t"])
    ax.set_xlabel("Jahre nach Emission oder Entnahme")
    ax.set_ylabel(ylabel)
    return _save(fig, out_path)


def co2_forcing_figure(out_path: str) -> str:
    """K6: how strongly CO2 warms. Left: forcing of the whole CO2 in the air, 5.35 ln(C/C0), with its tangent
    in 2025 and 2100 (SSP2-4.5 background) -- the fuller the air, the flatter. Right: the forcing per kg that
    follows, A_CO2(t) = 5.35 / (C_bg(t) k)."""
    from nbs.constants import A_CO2_LOG_W_M2_PER_PPM as A, KG_CO2_PER_PPM as K
    from nbs.response import background_co2_ppm

    _setup()
    c0 = 278.0
    cbg = np.asarray(background_co2_ppm("ssp245"), dtype=float)
    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=HALF, dpi=FIG_DPI, gridspec_kw={"width_ratios": [1.1, 1.0]})
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.13, top=0.9, wspace=0.42)
    for ax in (ax_l, ax_r):
        _clean_axes(ax)
    cc = np.linspace(c0, 650, 200)
    ax_l.plot(cc, A * np.log(cc / c0), color="#8c6d5a", linewidth=3.0)
    for yr, col in ((T_START, "#2f6fb7"), (2100, "#b2182b")):
        c = float(cbg[yr - YEARS[0]])
        f = A * np.log(c / c0)
        xs = np.array([c - 90, c + 90])
        ax_l.plot(xs, f + A / c * (xs - c), color=col, linewidth=1.6, linestyle=(0, (5, 3)))
        ax_l.plot(c, f, "o", ms=8, color=col, mec="white", mew=1.5, zorder=5)
        ax_l.annotate(f"{yr}: {c:.0f} ppm", (c, f), xytext=(14, -16) if yr == T_START else (-10, 12), textcoords="offset points",
                      ha="left" if yr == T_START else "right",
                      fontsize=12, color=col, fontweight="bold")
    ax_l.set_xlim(c0, 650)
    ax_l.set_ylim(0, 5.2)
    ax_l.set_xlabel("CO$_2$-Konzentration [ppm]")
    ax_l.set_ylabel("Antrieb [W/m$^2$]")
    ax_l.set_title("Gesamtes CO$_2$ (log.)", loc="left", fontsize=12.5, color=C_INK)
    a_kg = A / (cbg * K) * 1e15
    ax_r.plot(YEARS, a_kg, color="#8c6d5a", linewidth=3.0)
    for yr in (T_START, 2100):
        v = a_kg[yr - YEARS[0]]
        ax_r.plot(yr, v, "o", ms=8, color=C_INK, mec="white", mew=1.5, zorder=5)
        ax_r.annotate(f"{v:.2f}".replace(".", ","), (yr, v), xytext=(8, 8) if yr == T_START else (0, 10),
                      textcoords="offset points", ha="left" if yr == T_START else "right", fontsize=12.5, color=C_INK, fontweight="bold")
    ax_r.set_xlim(YEARS[0], YEARS[-1])
    ax_r.set_xticks([T_START, 2050, 2075, 2100])
    ax_r.set_ylim(0, 2.0)
    ax_r.set_ylabel("Antrieb je kg [10$^{-15}$ W/m$^2$]")
    ax_r.set_title("Je kg CO$_2$, SSP2-4.5", loc="left", fontsize=12.5, color=C_INK)
    return _save(fig, out_path)


def irf_side_figure(out_path: str, horizon: int = 150) -> str:
    """K3 as a side panel next to the carbon-cycle drawing: only the removal of 1 kg CO2 by the tree. The
    air lacks the green part; the brown part between -1 kg and the curve is what land and ocean give back."""
    _setup()
    g = green_carbon_preindustrial(horizon + 1)
    t = np.arange(horizon + 1)
    c_rm, c_back = "#2e7d4f", "#8c6d5a"
    # sized to its slot on the slide (530 x 360 px) at the scale of the other model charts (~0.675 px per figure px),
    # so lines and type match them
    fig, ax = plt.subplots(figsize=(4.9, 3.33), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.205, right=0.97, bottom=0.17, top=0.97)
    _clean_axes(ax)
    ax.axhline(0, color=C_INK_MUTED, linewidth=1.0)
    ax.axhline(-1, color=c_rm, linewidth=1.1, linestyle=(0, (2, 3)), alpha=0.8)
    ax.fill_between(t, 0, -g, color=c_rm, alpha=0.14, linewidth=0)
    ax.fill_between(t, -g, -1, color=c_back, alpha=0.16, linewidth=0)
    ax.plot(t, -g, color=c_rm, linewidth=2.6)
    # one marked point is enough to read the curve: half a century on, about half is still missing in the air
    for yr in (50,):
        ax.plot(yr, -g[yr], "o", ms=7, color=c_rm, mec="white", mew=1.5, zorder=5)
        ax.annotate(f"{100 * g[yr]:.0f} % nach {yr} Jahren", (yr, -g[yr]), xytext=(4, -10), textcoords="offset points", ha="left",
                    va="top", fontsize=12, color=C_INK)
    from nbs.response import _JOOS_A0 as a0
    ax.axhline(-a0, color=c_rm, linewidth=1.1, linestyle=(0, (4, 4)), alpha=0.8)
    ax.text(horizon, -a0 + 0.04, f"{100 * a0:.0f} % dauerhaft entfernt", ha="right", va="bottom", fontsize=13.5, color=c_rm,
            fontweight="bold")
    ax.text(horizon - 2, -0.96, "Land + Ozean gasen aus", ha="right", va="bottom", fontsize=13.5, color=c_back,
            fontweight="bold")   # as large as the share that stays removed: the two parts of the same kilogram
    ax.set_xlim(0, horizon)
    ax.set_ylim(-1.12, 0.1)
    ax.set_yticks([-1, -0.5, 0])
    ax.set_yticklabels(["−1 kg", "−0,5 kg", "0"])
    ax.set_xlabel("Jahre nach der Entnahme")
    # y label on the slide as a formula overlay (Delta m_CO2), in the colour of the formula
    return _save(fig, out_path)


def step_response_figure(out_path: str) -> str:
    """Slide 21, alone in the drawing's place: how the Earth's temperature answers 1 W/m^2 that stays on
    (FaIR's own temperature response, summed): fast at first (surface), then slowly (deep ocean), towards
    the equilibrium phi / Lambda."""
    import pandas as pd

    from nbs.fair_module import _PARAMS_CSV, CENTRAL_MEMBER

    _setup()
    lam = float(pd.read_csv(_PARAMS_CSV, index_col=0).loc[CENTRAL_MEMBER, "ocean_heat_transfer[0]"])
    step = np.cumsum(green_temperature("ssp245"))
    t = np.arange(len(step))
    fig, ax = plt.subplots(figsize=(7.3, 4.6), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.13, right=0.96, bottom=0.14, top=0.9)
    _clean_axes(ax)
    eq = 1.0 / lam
    ax.axhline(eq, color=C_INK_MUTED, linewidth=1.2, linestyle=(0, (5, 4)))
    ax.text(t[-1] - 1, eq + 0.02, f"Gleichgewicht φ/Λ ≈ {eq:.1f} K".replace(".", ","), ha="right", va="bottom", fontsize=12.5,
            color=C_INK_MUTED)
    ax.plot(t, step, color="#b2182b", linewidth=3.2)
    for yr, off, ha in ((5, (14, -6), "left"), (int(t[-1]) - 5, (0, -30), "right")):
        ax.plot(yr, step[yr], "o", ms=9, color="#b2182b", mec="white", mew=1.6, zorder=5)
        ax.annotate(f"nach {yr} Jahren: {step[yr]:.1f} K".replace(".", ","), (yr, step[yr]), xytext=off,
                    textcoords="offset points", fontsize=12.5, color=C_INK, ha=ha)
    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, eq * 1.15)
    ax.set_xlabel("Jahre, nachdem 1 W/m² dazukommt")
    ax.set_ylabel("Erwärmung T [K]")
    ax.set_title("Beispiel: φ = 1 W/m² dauerhaft", loc="left", fontsize=13, color=C_INK)
    return _save(fig, out_path)


def _tree_temperature_frame():
    """Axes shared by the one-year example and the tree result on the temperature slide: same size, same
    limits, so the deck can swap the curves in the same frame."""
    _setup()
    fig, ax = plt.subplots(figsize=(7.3, 4.6), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.13, right=0.8, bottom=0.12, top=0.9)
    _clean_axes(ax)
    ax.axhline(0, color=C_INK_MUTED, linewidth=0.9)
    lo = min(float(np.min(run_site(s).delta_t)) for s in SITES) * 1e15
    ax.set_xlim(YEARS[0], YEARS[-1])
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylim(lo * 1.06, -lo * 0.05)
    ax.set_ylabel("ΔT je Baum [10$^{-15}$ K]")
    return fig, ax


def tree_temperature_figure(out_path: str) -> str:
    """Slide 21, after the example: the temperature effect of one tree at the three sites (its forcing of
    slide 20 put into FaIR)."""
    fig, ax = _tree_temperature_frame()
    scale = 1e15
    for s in SITES:
        r = run_site(s)
        ax.plot(YEARS, r.delta_t * scale, color=s.color, linewidth=3.2)
        ax.annotate(s.label, (YEARS[-1], r.delta_t[-1] * scale), xytext=(8, 0), textcoords="offset points", va="center",
                    fontsize=12.5, color=s.color, fontweight="bold", annotation_clip=False)
    ax.set_title("Je Baum: sein Antrieb φ(t) → ΔT(t)", loc="left", fontsize=13, color=C_INK)
    ax.text(2028, ax.get_ylim()[0] * 0.92, "unter null: kühlt", fontsize=12, color=C_INK_MUTED)
    return _save(fig, out_path)


def co2_efficiency_figure(out_path: str) -> str:
    """K6e: on top of the greenhouse explanation: the forcing per kg falls as the background concentration
    rises (SSP2-4.5); one line, the two ends labelled with value and concentration."""
    from nbs.constants import A_CO2_LOG_W_M2_PER_PPM as A, KG_CO2_PER_PPM as K
    from nbs.response import background_co2_ppm

    _setup()
    cbg = np.asarray(background_co2_ppm("ssp245"), dtype=float)
    a_kg = A / (cbg * K) * 1e15
    fig, ax = plt.subplots(figsize=(7.3, 4.6), dpi=FIG_DPI)  # replaces the 860 px drawing: ticks ~19 px
    fig.subplots_adjust(left=0.13, right=0.95, bottom=0.12, top=0.9)
    _clean_axes(ax)
    ax.plot(YEARS, a_kg, color="#1b7837", linewidth=3.2)
    for yr, off, ha in ((T_START, (10, 8), "left"), (2100, (0, 14), "right")):
        i = yr - YEARS[0]
        ax.plot(yr, a_kg[i], "o", ms=9, color="#1b7837", mec="white", mew=1.6, zorder=5)
        ax.annotate(f"{a_kg[i]:.2f}".replace(".", ",") + f"\n{yr}: {cbg[i]:.0f} ppm CO$_2$", (yr, a_kg[i]), xytext=off,
                    textcoords="offset points", ha=ha, va="bottom", fontsize=12.5, color=C_INK, fontweight="bold")
    ax.set_xlim(YEARS[0], YEARS[-1])
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylim(0, 2.0)
    # y label on the slide as a formula overlay (epsilon_CO2), in the colour of the formula
    ax.set_title("Mehr CO$_2$ im Hintergrund, weniger Wirkung je kg (SSP2-4.5)", loc="left", fontsize=13, color=C_INK)
    return _save(fig, out_path)


LONG_END = 2200  # k5 only: long enough to see the atmospheric change fall after the tree stops growing


def _annual_uptake_long(site: Site, end: int = LONG_END) -> NDArray:
    """kg CO2 taken up per year, 2025..*end*: the tree model on a longer time grid (the integrator
    reads the module grid ``nbs.tree.YEARS``). After 2100 nothing changes in the model, the forest
    simply stands: growth and disturbance balance, the uptake goes to zero."""
    from unittest import mock

    import nbs.tree as tree_mod

    years = np.arange(YEARS[0], end + 1)
    sp = dataclasses.replace(_site_species(site), gamma_warming=0.0)
    with mock.patch.object(tree_mod, "YEARS", years):
        return M_CO2_PER_C * simulate_deterministic(sp, np.zeros(len(years))).net_uptake_kgC_yr


def missing_air_bars_figure(out_path: str) -> str:
    """Klima: bars = what the tree has taken up so far (tree accounting), lines = the CO2 change of the
    atmosphere once ocean and land answer every yearly uptake (Joos g_C, slide before). Runs to 2200 so
    the decline after the tree stops growing is visible; 2100 (the horizon of all results) marked."""
    _setup()
    years = np.arange(YEARS[0], LONG_END + 1)
    g = green_carbon_preindustrial(len(years))
    bars = np.arange(2030, LONG_END + 1, 20)
    idx = bars - years[0]
    fig, ax = plt.subplots(figsize=(7.3, 4.4), dpi=FIG_DPI)  # its slot next to the formulas: ticks ~19 px
    fig.subplots_adjust(left=0.13, right=0.75, bottom=0.12, top=0.83)
    _clean_axes(ax)
    ax.set_xlim(years[0], years[-1] + 3)
    ax.set_xticks([2050, 2100, 2150, 2200])
    ax.axvline(2100, color=C_INK_MUTED, linewidth=1.2, linestyle=(0, (4, 3)))
    ends = {}
    for j, s in enumerate(SITES):
        u = _annual_uptake_long(s)
        tree = np.cumsum(u)
        air = convolve_response(g, u)
        ends[s.label] = (air[-1], tree[-1], s.color)
        ax.bar(bars + (j - (len(SITES) - 1) / 2) * 4.4, tree[idx], width=4.4 * 0.92, color=s.color, alpha=0.35)
        ax.plot(years, air, color=s.color, linewidth=3.0)
        i100 = 2100 - years[0]
        ax.plot(2100, air[i100], "o", ms=7, color=s.color, mec="white", mew=1.4, zorder=5)
    ax.set_ylim(0, None)
    # end labels (two lines each) kept apart: at least 17 % of the axis height, pushed upwards from the lowest
    gap, prev = 0.17 * ax.get_ylim()[1], None
    for label, (a_end, t_end, col) in sorted(ends.items(), key=lambda kv: kv[1][0]):
        y = max(a_end, 0.09 * ax.get_ylim()[1]) if prev is None else max(a_end, prev + gap)
        ax.annotate(f"{label}\n{a_end:.0f} von {t_end:.0f} kg", (years[-1], a_end), xytext=(years[-1] + 6, y), textcoords="data",
                    va="center", fontsize=12.5, color=col, fontweight="bold", annotation_clip=False)
        prev = y
    ax.text(2101.5, ax.get_ylim()[1] * 0.97, "Horizont: 2100", fontsize=11.5, color=C_INK_MUTED, va="top")
    ax.set_ylabel("CO$_2$ je Baum [kg]")
    ax.set_title("Balken: vom Baum bisher aufgenommen\nLinie: Abnahme des CO$_2$ in der Atmosphäre ($-\\Delta m_{CO_2}$)", loc="left", fontsize=12.5,
                 color=C_INK)
    return _save(fig, out_path)


# --------------------------------------------------------------------------
# B5: which forest grows where (replaces the five-species chart)
# --------------------------------------------------------------------------


def forest_type_map_figure(out_path: str) -> str:
    """Typical forest type (Hasler et al. 2024) on the reforestable area
    (Walker et al. 2022), per 2-degree block: hue = the type with the most
    reforestable area in the block, saturation = reforestable share of the
    block's land (full colour from 30 %), so the map does not suggest more
    area than there is. Both sites marked in ink, not in their site colours,
    which would clash with the type colours."""
    import matplotlib.colors as mcolors
    from matplotlib.patches import Patch

    from nbs.dac_figures import BLOCK, _map_axes
    from nbs.forest_data import TYPES, reforestable_area_m2, typical_type
    from nbs.map_plots import _COLOR_LAND, TYPE_COLORS, TYPE_NAMES

    _setup()
    typ = typical_type()
    w = np.where(typ != None, reforestable_area_m2(), 0.0)  # noqa: E711
    n, m = w.shape[0] // BLOCK, w.shape[1] // BLOCK

    def blk(a):
        return a.reshape(n, BLOCK, m, BLOCK).sum(axis=(1, 3))

    per_type = np.stack([blk(np.where(typ == t, w, 0.0)) for t in TYPES])
    total = per_type.sum(axis=0)
    dom = np.argmax(per_type, axis=0)
    from nbs.dac_climate import climate_grid
    from nbs.grid import cell_area_m2

    land = np.isfinite(climate_grid()["t_mean_c"]) | (w > 0)
    land_area = blk(np.where(land, cell_area_m2(), 0.0))
    share = np.clip(np.where(land_area > 0, total / np.maximum(land_area, 1.0), 0.0) / 0.30, 0.0, 1.0)
    land_b = land_area > 0
    base = np.array(mcolors.to_rgb(_COLOR_LAND))
    rgba = np.zeros((n, m, 4))
    rgba[land_b] = mcolors.to_rgba(_COLOR_LAND)
    for k, t in enumerate(TYPES):
        sel = (total > 0) & (dom == k)
        rgb = np.array(mcolors.to_rgb(TYPE_COLORS[t]))
        rgba[sel, :3] = base + (rgb - base) * (0.12 + 0.88 * share[sel, None])
        rgba[sel, 3] = 1.0

    # the left 860 px of the slide, the three sites' curves beside it (2026-10-12); legend in two rows underneath.
    # 7.4 in for 860 px keeps the fonts at the size they had on the full-width map
    fig, ax = plt.subplots(figsize=(7.4, 4.1), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.005, right=0.995, bottom=0.25, top=0.995)
    ax.imshow(rgba, extent=(-180, 180, -90, 90), origin="upper", interpolation="nearest")
    _map_axes(ax)
    from nbs import map_fields as M
    from nbs.vergleich_figures import map_site_value, world_site_labels

    data = M.MAPS["b5"]()
    world_site_labels(ax, lambda s_: map_site_value(data, s_), dict(mfc="white", mec=C_INK))
    areas = {t: float(w[typ == t].sum() / 1e13) for t in TYPES}
    order = sorted(TYPES, key=lambda t: -areas[t])
    handles = [Patch(facecolor=TYPE_COLORS[t], label=f"{TYPE_NAMES[t]}\n{de_gha(areas[t])}") for t in order]
    handles.append(Patch(facecolor=_COLOR_LAND, label="nicht wiederbewaldbar\n(Wald, Acker, Stadt, Savanne, …)"))
    ax.text(0.995, 0.03, "Kräftige Farbe: ≥ 30 % der Fläche wiederbewaldbar", transform=ax.transAxes, ha="right",
            fontsize=10, color=C_INK_MUTED)
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=3, frameon=False,
               fontsize=11, columnspacing=1.6, handlelength=1.3, handletextpad=0.5)
    return _save(fig, out_path)


def de_gha(x: float) -> str:
    return f"{x:.2f} Gha".replace(".", ",")


# --------------------------------------------------------------------------
# Literature comparison: how much of the pure carbon benefit survives albedo
# --------------------------------------------------------------------------

LITERATURE_REMAINING = (
    # (label, detail, remaining share of the carbon-only benefit, lower-bound?)
    ("Riley et al. 2025", "172 bestehende Projekte, statisch (Median)", 1.0 - 0.18, False),
    ("Weber et al. 2024", "Erdsystemmodell, Albedo + Luftchemie, 4-°C-Welt", 2.0 / 3.0, True),
    ("Fahrenbach et al. 2026", "CESM2, Bastin-Fläche, SSP2-4.5, bis 2100", 0.13 / 0.22, False),
    ("Hasler et al. 2024", "Bastin-Fläche, statisch (max. CO$_2$e)", 101.0 / 214.0, False),
    ("Liang et al. 2025", "0,88 Gha, bis 2100, SSP1-2.6, Feuer + Albedo", 37.5 / 125.0, False),
    ("Rohatyn et al. 2022", "Trockengebiete, bis 2100", (32.3 - 22.6) / 32.3, False),
)
"""Riley: Nat. Commun. 16, 8810 (median albedo deduction 18 % over 172 ARR
projects); Fahrenbach: Commun. Earth Environ. 7, 204 (Bastin area: -0.22 K
from carbon, -0.13 K net by 2086-2100; includes evapotranspiration and
non-local effects); Weber: Science 383, 860 ("offset up to a third"); Hasler: Nat. Commun. 15,
2275 (214 -> 101 Pg CO2e on the Bastin area); Liang: Sci. Adv. 2025,
adn7915 (125 Pg C NEP -> 37.5 Pg Ceq after fire and albedo); Rohatyn:
Science 377, 1436 (22.6 of 32.3 Gt C needed to balance albedo)."""


@lru_cache(maxsize=1)
def own_remaining() -> dict[str, float]:
    """This model in the same unit: remaining share of the carbon-only benefit.

    static: Hasler's own formula (400 ppm, mean 100-year airborne fraction
    0.52) on this model's cells, Delta-alpha*q and Walker carbon.
    alle / kuehlend: Delta-T in 2100 under SSP2-4.5 with albedo and
    disturbance over Delta-T carbon-only without disturbance -- over all
    reforestable area, and over the cells that cool by 2100."""
    from nbs.config import ModelConfig
    from nbs.constants import A_EARTH_M2, TAU_ATM
    from nbs.forest_data import carbon_gain_mgc_ha
    from nbs.landscape import assign_species, plantable_area_m2
    from nbs.map_plots import _breakeven_year_field
    from nbs.potential import _masked_global_delta_t

    from nbs.animations import _by_type

    plant = assign_species() != None  # noqa: E711
    a = plantable_area_m2()
    cool = plant & np.isfinite(_breakeven_year_field("ssp245"))
    out = {}
    for name, m in (("alle", plant), ("kuehlend", cool)):
        full = _masked_global_delta_t(m, "ssp245")[-1]
        co2 = _masked_global_delta_t(m, "ssp245", ModelConfig(albedo=False, disturbance="off"))[-1]
        out[name] = float(full / co2)
        out[f"flaeche_{name}_gha"] = float(a[m].sum() / 1e13)
    prod = _by_type(light_product)
    m = plant & np.isfinite(prod)
    per_tco2 = 5.35 / 400.0 / (2.13e9 * 44.0 / 12.0)
    alb = (-prod * TAU_ATM * 1e4 / A_EARTH_M2 / per_tco2 / 0.52 * a / 1e4)[m].sum()
    carbon = (carbon_gain_mgc_ha() * 44.0 / 12.0 * a / 1e4)[m].sum()
    out["statisch"] = float(1.0 - alb / carbon)
    return out


def literature_comparison_figure(out_path: str) -> str:
    """Dot plot: remaining share of the carbon-only benefit after albedo,
    literature (ink) against this model (green), one row per estimate."""
    _setup()
    own = own_remaining()
    rows = [(lab, det, v, lb, False) for lab, det, v, lb in LITERATURE_REMAINING]
    rows += [
        ("Dieses Modell", "Haslers Formel auf unseren Zellen", own["statisch"], False, True),
        ("Dieses Modell", f"ΔT 2100, SSP2-4.5, alle {de(own['flaeche_alle_gha'], 2)} Gha", own["alle"], False, True),
        ("Dieses Modell", f"ΔT 2100, nur kühlende {de(own['flaeche_kuehlend_gha'], 2)} Gha", own["kuehlend"], False,
         True),
    ]
    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.42, right=0.96, bottom=0.12, top=0.97)
    _clean_axes(ax)
    n = len(rows)
    y = np.arange(n)[::-1]
    ax.axvspan(-40, 0, color=C_WARM_FILL, alpha=0.45, lw=0)
    ax.axvline(0, color=C_INK_MUTED, lw=1.0)
    ax.text(-38, n - 0.45, "netto\nwärmend", fontsize=10, color=C_INK_MUTED, va="top")
    for yi, (lab, det, v, lb, mine) in zip(y, rows):
        col = C_CARBON if mine else C_INK
        ax.plot([0, 100 * v], [yi, yi], color=col, lw=1.2, alpha=0.35)
        ax.plot(100 * v, yi, marker="o", ms=11, mfc=col, mec="white", mew=1.6, zorder=5)
        if lb:
            ax.annotate("", xy=(100 * v + 9, yi), xytext=(100 * v + 2, yi),
                        arrowprops=dict(arrowstyle="->", color=col, lw=1.6))
        ax.text(100 * v + (12 if lb else 3.5), yi + 0.28, ("≥ " if lb else "") + f"{100 * v:.0f} %".replace("-", "−"),
                fontsize=12, color=C_INK, fontweight="bold", va="center")
        fig.text(0.015, 0, "")  # keeps the layout stable when labels are long
        ax.text(-42, yi + 0.12, lab, transform=ax.transData, ha="right", va="center", fontsize=12.5,
                fontweight="bold", color=col, clip_on=False)
        ax.text(-42, yi - 0.25, det, ha="right", va="center", fontsize=10.5, color=C_INK_MUTED, clip_on=False)
    ax.set_xlim(-40, 100)
    ax.set_ylim(-0.7, n - 0.3)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("vom reinen Kohlenstoffnutzen bleibt nach Albedo [%]")
    return _save(fig, out_path)


def de(x: float, nd: int = 1) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


# --------------------------------------------------------------------------
# Z1: time matters -- DAC removes at once, the tree only as it grows
# --------------------------------------------------------------------------

TROPICAL_SITE = SITES[2]  # Marabá (BR)


def uptake_share_by_2100(site: Site) -> NDArray:
    """Share [0..1] of the CO2 one tree (planted 2025) takes out of the air by T_END, reached in each year."""
    c = np.cumsum(_annual_uptake(site))
    return c / c[-1]


def time_share_figure(out_path: str) -> str:
    """Z1: how much of what a tree planted 2025 removes by 2100 it has removed by each year;
    DAC removes a tonne in the year it runs."""
    from nbs.dac_figures import C_DAC

    _setup()
    fig, ax = plt.subplots(figsize=WIDE, dpi=FIG_DPI)
    fig.subplots_adjust(left=0.08, right=0.8, bottom=0.13, top=0.92)
    _clean_axes(ax)
    ax.axhline(1.0, color=C_DAC, linewidth=3.0)
    ax.text(YEARS[0] + 1, 1.03, "DAC: die Tonne zählt ab dem Jahr, in dem die Anlage läuft", fontsize=12.5,
            color=C_DAC, fontweight="bold", va="bottom")
    sites = list(SITES)
    for s in sites:
        f = uptake_share_by_2100(s)
        ax.plot(YEARS, f, color=s.color, linewidth=2.6)
        ax.annotate(s.label, (YEARS[-1], f[-1] - 0.04 * sites.index(s)), xytext=(8, 0), textcoords="offset points",
                    va="center", fontsize=12, color=s.color, fontweight="bold", annotation_clip=False)
    ref = uptake_share_by_2100(SITES[0])
    for y in (2035, 2050):
        v = float(ref[y - YEARS[0]])
        ax.plot([y, y], [0, v], color=C_INK_MUTED, linewidth=1.0, linestyle=(0, (4, 3)))
        ax.plot(y, v, "o", ms=8, color=C_INK, mec="white", mew=1.5, zorder=5)
        ax.annotate(f"{y}: {100 * v:.0f} %", (y, v), xytext=(8, -4), textcoords="offset points", fontsize=12.5,
                    color=C_INK, fontweight="bold", va="top")
    ax.set_xlim(YEARS[0], YEARS[-1])
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0", "25 %", "50 %", "75 %", "100 %"])
    ax.set_ylabel("schon entnommen, Anteil der Menge bis 2100")
    ax.set_title(f"Baum gepflanzt {T_START}: wie viel seiner Entnahme bis 2100 schon geschehen ist", loc="left",
                 fontsize=13, color=C_INK)
    return _save(fig, out_path)
