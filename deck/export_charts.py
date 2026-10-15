"""Chart data for the HTML deck: deck/assets/data/{ec_charts,maps,cmip7}.js.

Every chart is drawn by the model's own matplotlib code (nbs.*_figures). This
script catches each figure at ``savefig`` and hands it to mpl_to_echarts,
which writes it out in data coordinates; the deck redraws it with ECharts
(hover read-outs, per-element animation). Map values go to maps.js
(nbs.map_fields), the CMIP7 tables to cmip7.js. deck/build.py copies only
the charts the slides use.

    uv run python deck/export_charts.py              # everything
    uv run python deck/export_charts.py --only b6,k10
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

DECK = Path(__file__).resolve().parent
REPO = DECK.parent
OUT = DECK / "assets" / "data"


# --------------------------------------------------------------------------
# capture
# --------------------------------------------------------------------------

EC_SCENES: dict[str, dict] = {}   # the same figures in data coordinates, for ECharts (mpl_to_echarts)
_CURRENT: list[str] = []
_orig_savefig = Figure.savefig


def _capture(self: Figure, fname, *args, **kwargs):
    dpi = kwargs.get("dpi")
    if dpi and dpi != "figure":
        self.set_dpi(dpi)
    key = _CURRENT[-1]
    from mpl_to_echarts import data_scene

    EC_SCENES[key] = data_scene(self)


def run(key: str, fn, *args) -> None:
    _CURRENT.append(key)
    try:
        with tempfile.TemporaryDirectory() as d:
            fn(str(Path(d) / f"{key}.png"), *args)
    finally:
        _CURRENT.pop()
        plt.close("all")
    print(f"  {key}", flush=True)


def timescales_figure(out_path: str) -> str:
    """Slide 10: net carbon flux of one tree on three time scales (illustrative), from the tree's point of
    view as in the formula above (positive = uptake). Each panel marks which terms act, in the colours of
    the formula: day = photosynthesis against respiration, year = respiration and decomposition in winter,
    decades = saturation and a disturbance event (stock with the Aachen model tree of the next slide)."""
    from nbs.animations import C_INK_MUTED, FIG_DPI, _clean_axes
    from nbs.storyline_figures import _setup

    _setup()
    c_ps, c_re, c_zs, c_st, c_ink = "#2f7a45", "#7e4a74", "#3d6698", "#c0392b", "#1a2320"
    fig = plt.figure(figsize=(12.0, 5.6), dpi=FIG_DPI)
    # three panels of equal size; the fourth place (bottom right) stays free for the takeaway on the slide
    gs = fig.add_gridspec(2, 2, left=0.07, right=0.97, bottom=0.1, top=0.92, hspace=0.62, wspace=0.22)
    a1, a2, a3 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 0])
    for ax in (a1, a2, a3):
        _clean_axes(ax)

    # all panels in kg C per tree and on one scale: a summer day sums to about 26 g C (July in the year panel),
    # the year to about 1 kg C net, the growth of the stand curve below (Aachen model tree, at most ~1 kg C/a)

    # day: photosynthesis only with light, respiration around the clock [g C per tree and hour]
    t = np.linspace(0, 24, 241)
    ps = np.where((t > 6) & (t < 20), 3.8 * np.sin(np.pi * (t - 6) / 14), 0.0)
    net = ps - 0.35
    a1.axhline(0, color=C_INK_MUTED, lw=0.8)
    a1.fill_between(t, 0, net, where=net > 0, color=c_ps, alpha=0.22, lw=0)
    a1.fill_between(t, 0, net, where=net < 0, color=c_re, alpha=0.25, lw=0)
    a1.plot(t, net, color=c_ink, lw=2.2)
    a1.text(13, 4.35, "Tag: Photosynthese (PS) > Respiration (RE)", ha="center", fontsize=12, color=c_ps, fontweight="bold")
    a1.text(0.4, -0.75, "Nacht: nur Respiration (RE) → Abgabe", ha="left", va="top", fontsize=12, color=c_re, fontweight="bold")
    a1.set_xlim(0, 24)
    a1.set_ylim(-2.0, 4.9)
    a1.set_xticks(range(0, 25, 4))
    a1.set_xlabel("Uhrzeit [h]")
    a1.set_ylabel("10$^{-3}$ kg C je Baum und h")
    a1.set_title("Über den Tag", loc="left", fontsize=19, fontweight="bold", color=c_ink)

    # year (deciduous forest): gross fluxes per month -- photosynthesis up, respiration down in every month
    # (strongest in the warm summer), decomposition of litter and dead wood (ZS) hatched below; the line is the
    # tree's net balance PS - RE: clearly positive in summer, only slightly negative in winter (no leaves,
    # respiration throttled by the cold). Illustrative, the model has no seasonal cycle.
    months = np.arange(1, 13)
    ps = 0.1 * np.array([0.0, 0.0, 0.3, 2.4, 7.0, 10.2, 11.4, 10.6, 7.6, 3.4, 0.2, 0.0])
    re_ = 0.1 * np.array([0.8, 0.8, 0.9, 1.4, 2.5, 3.4, 3.6, 3.4, 2.6, 1.6, 0.9, 0.8])
    zs = 0.17 * np.array([0.6, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.1, 1.1, 1.4, 1.3, 0.8])
    a2.axhline(0, color=C_INK_MUTED, lw=0.8)
    a2.bar(months, ps, color=c_ps, alpha=0.75, width=0.7)
    a2.bar(months, -re_, color=c_re, alpha=0.75, width=0.7)
    a2.bar(months, -zs, bottom=-re_, color="none", edgecolor=c_zs, hatch="///", lw=1.2, width=0.7)
    a2.plot(months, ps - re_, color=c_ink, lw=2.0, marker="o", ms=5, zorder=5)
    a2.text(0.6, 1.14, "Photosynthese (PS)", ha="left", fontsize=11.5, color=c_ps, fontweight="bold")
    a2.text(0.6, 0.92, "— Netto PS − RE", ha="left", fontsize=11.5, color=c_ink, fontweight="bold")
    a2.text(0.6, -0.56, "Respiration (RE)", ha="left", fontsize=11.5, color=c_re, fontweight="bold")
    a2.text(0.6, -0.79, "schraffiert: Zersetzung (ZS)", ha="left", fontsize=11.5, color=c_zs, fontweight="bold")
    a2.set_xticks(months)
    a2.set_xlim(0.4, 12.6)
    a2.set_ylim(-0.9, 1.3)
    a2.set_yticks([-0.5, 0, 0.5, 1.0])
    a2.set_xlabel("Monat")
    a2.set_ylabel("kg C je Baum und Monat")
    a2.set_title("Über das Jahr", loc="left", fontsize=19, fontweight="bold", color=c_ink)

    # decades: Chapman-Richards stock of the Aachen model tree (m_max 49 kg C, k 0.043/a, p 2), a
    # disturbance at age 55 removes 60 % of the stock, then the stand regrows along the same curve
    m_max, k, p = 49.0, 0.043, 2.0
    S = lambda a: m_max * (1 - np.exp(-k * np.clip(a, 0, None))) ** p  # noqa: E731
    age = np.linspace(0, 100, 501)
    stock = S(age)
    ev, keep = 55.0, 0.4
    rest = keep * S(ev)
    a_eq = -np.log(1 - (rest / m_max) ** (1 / p)) / k  # age on the curve with the residual stock
    dist = np.where(age < ev, stock, S(a_eq + (age - ev)))
    a3.plot(age, stock, color=c_ps, lw=2.6)
    a3.plot(age[age >= ev], dist[age >= ev], color=c_st, lw=2.6)
    a3.plot([ev, ev], [S(ev), rest], color=c_st, lw=2.6, ls=(0, (3, 2)))
    a3.text(ev - 2, 12, "Störung (ST)", ha="right", va="center", fontsize=12.5, color=c_st, fontweight="bold")
    a3.text(99, 4, "Sättigung: Zuwachs ≈ Zersetzung (ZS)", ha="right", va="center", fontsize=12.5,
            color=c_zs, fontweight="bold")
    a3.text(2, 44, "Aufbau: PS − RE", ha="left", va="center", fontsize=12, color=c_ps,
            fontweight="bold")
    a3.set_xlim(0, 100)
    a3.set_ylim(0, m_max * 1.08)
    a3.set_xlabel("Bestandesalter [a]")
    a3.set_ylabel("kg C je Baum (Vorrat)")
    a3.set_title("Über Jahrzehnte", loc="left", fontsize=19, fontweight="bold", color=c_ink)
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path


def growth_model_figure(out_path: str) -> str:
    """Slide 12: carbon stock of one tree, Aachen mixed forest, three variants."""
    from nbs.constants import T_START

    from nbs.animations import FIG_DPI, _clean_axes
    from nbs.storyline_figures import _setup

    _setup()
    fig, ax = plt.subplots(figsize=(7.8, 3.9), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.1, right=0.67, bottom=0.15, top=0.93)
    _clean_axes(ax)
    styles = {
        "nur Wachstum": ("#2f7a45", "-", 2.6, "nur Wachstum"),
        "mit Störung, ΔT_w = 0": ("#d6604d", "-", 2.2, "mit Störung, $\\Delta T_w$ = 0"),
        "mit Störung, ΔT_w = 1 K (linear)": ("#a50f15", (0, (6, 4)), 2.2, "mit Störung, $\\Delta T_w$ = 1 K"),
    }
    # the curves of the former native chart (deck/chart_data/s12_vorrat.json), shown to the horizon
    series = json.loads((REPO / "deck" / "chart_data" / "s12_vorrat.json").read_text(encoding="utf-8"))
    for ser in series:
        name = ser["name"]
        # the series start at planting in 2025; shifted so that planting is the start year
        xs = [v + (T_START - 2025) for v in ser["x"]]
        x, y = [v for v in xs if v <= 2100], ser["y"][:len([v for v in xs if v <= 2100])]
        c, ls, lw, lab = styles[name]
        ax.plot(x, y, color=c, ls=ls, lw=lw)
        ax.annotate(lab, (x[-1], y[-1]), xytext=(8, {"nur Wachstum": 10, "mit Störung, ΔT_w = 0": -5}.get(name, -21)),
                    textcoords="offset points", fontsize=13.5, color=c, va="center", annotation_clip=False)
    ax.set_xlim(T_START, 2100)
    ax.set_ylim(0, 52)
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylabel("Vorrat $m_{Baum}$ [kg C]")
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path


# --------------------------------------------------------------------------
# chart list: key -> figure function (keys as in data-chart on the slides)
# --------------------------------------------------------------------------


def chart_jobs() -> list[tuple[str, object]]:
    from nbs import animations as an
    from nbs import dac_figures as df
    from nbs import storyline_figures as sf
    from nbs import vergleich_figures as vf

    return [
        ("s11", timescales_figure),
        ("s12", growth_model_figure),
        ("b5", sf.forest_type_map_figure),
        ("b6s", sf.uptake_panel_figure),
        ("b8i", an.light_ingredients_figure),
        ("b8", an.albedo_annual_map_figure),
        ("b10", sf.common_currency_bars_figure),
        ("k3s", sf.irf_side_figure),
        ("k5", sf.missing_air_bars_figure),
        ("k6", sf.co2_forcing_figure),
        ("k6e", sf.co2_efficiency_figure),
        ("k10", sf.forcing_two_sites_figure),
        ("k13", sf.planting_year_figure),
        ("k14", sf.ladder_figure),
        ("k15", vf.tree_effect_figure),
        ("v0", vf.reforestable_share_figure),
        ("v1b", sf.literature_comparison_figure),
        ("w3", vf.planting_delay_figure),
        ("d1", df.energy_map_figure),
        ("d5", df.dac_net_figure),
    ]


def export_charts(only: set[str] | None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    Figure.savefig = _capture
    try:
        for key, fn in chart_jobs():
            if only and key not in only:
                continue
            run(key, fn)
    finally:
        Figure.savefig = _orig_savefig
    ec = OUT / "ec_charts.js"
    if only and ec.exists():
        old = ec.read_text(encoding="utf-8")
        EC_SCENES.update({k: v for k, v in json.loads(old[old.index("=") + 1 :].rstrip().rstrip(";")).items() if k not in EC_SCENES})
    ec.write_text("window.ECDATA = " + json.dumps(EC_SCENES, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + ";\n",
                  encoding="utf-8")
    print(f"wrote {ec} ({ec.stat().st_size / 1e6:.1f} MB)")


def export_maps() -> None:
    """Per-cell values of the deck's maps and their palettes (nbs.map_fields), for the hexagon maps."""
    from nbs import map_fields

    data = map_fields.export()
    js = OUT / "maps.js"
    js.write_text("window.MAPDATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + ";\n",
                  encoding="utf-8")
    print(f"wrote {js} ({js.stat().st_size / 1e6:.1f} MB)")


def export_cmip7() -> None:
    """The CMIP7 tables (data/cmip7, scripts/fetch_cmip7_data.py) for the D3 charts on slides 2 and 3."""
    from nbs import cmip7_figures as C

    t, obs, rem, cum = C.temperature(), C.observations(), C.removal(), C.cumulative_removal()
    r2 = lambda v: [round(float(x), 3) for x in v]  # noqa: E731
    out = {
        "ext": C.EXTENSION_FROM,
        "markers": [{"k": k, "label": lab, "color": col} for k, (lab, col) in C.MARKERS.items()],
        "obs": {"y": [int(v) for v in obs.jahr], "v": r2(obs.erwaermung_k)},
        "temp": {k: {"y": [int(v) for v in g.jahr], "med": r2(g["median"]), "p05": r2(g.p05), "p95": r2(g.p95)}
                 for k, g in t.groupby("szenario")},
        "rem": {k: {"y": [int(v) for v in g.jahr], "novel": r2(g.neuartig_gt), "land": r2(g.land_gt)}
                for k, g in rem.groupby("szenario")},
        "cum": [{"k": k, "novel": round(float(r.neuartig_gt), 1), "land": round(float(r.land_gt), 1),
                 "total": round(float(r.gesamt_gt), 1)} for k, r in cum.iterrows()],
        "facts": C.facts(),
    }
    js = OUT / "cmip7.js"
    js.write_text("window.CMIP7 = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"wrote {js} ({js.stat().st_size / 1e3:.0f} kB)")


def main() -> None:
    sys.path.insert(0, str(REPO / "src"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated chart keys")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    export_cmip7()
    export_maps()
    export_charts(set(a.only.split(",")) if a.only else None)


if __name__ == "__main__":
    main()
