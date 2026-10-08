"""Opening slides: where the CMIP7 marker scenarios take the climate, and how
much CO2 removal they assume to get there.

Data: data/cmip7/*.csv, built from the published sources by
scripts/fetch_cmip7_data.py (FaIR ensemble of van Vuuren et al. 2026, IGCC
2025 observations, ScenarioMIP extensions). Same picture as Carbon Brief's
explainer, redrawn from the original data so the deck can animate it.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from nbs.animations import C_INK, C_INK_MUTED, FIG_DPI, _clean_axes  # noqa: E402
from nbs.storyline_figures import WIDE, _save, _setup  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "data" / "cmip7"

# marker -> (German label, colour); Carbon Brief's colours, so the slide reads like the source
MARKERS = {
    "VL": ("Very Low (VL)", "#4c5bd4"),
    "LN": ("Low-to-Negative (LN)", "#1da8e2"),
    "L": ("Low (L)", "#1e8e4e"),
    "ML": ("Medium-Low (ML)", "#d4a21e"),
    "M": ("Medium (M)", "#d9611e"),
    "H": ("High (H)", "#8e2433"),
    "HL": ("High-to-Low (HL)", "#c86cc4"),
}
EXTENSION_FROM = 2100  # IAM scenarios end here; beyond: the published extensions (drawn the same way)


def temperature() -> pd.DataFrame:
    return pd.read_csv(DATA / "temperatur.csv")


def observations() -> pd.DataFrame:
    return pd.read_csv(DATA / "beobachtung.csv")


def removal() -> pd.DataFrame:
    return pd.read_csv(DATA / "entnahme.csv")


def cumulative_removal(y0: int = 2024, y1: int = 2100) -> pd.DataFrame:
    """Gt CO2 removed y0..y1 per marker: novel CDR, land sink, total (sorted, largest first)."""
    e = removal()
    e = e[(e.jahr >= y0) & (e.jahr <= y1)].groupby("szenario")[["neuartig_gt", "land_gt"]].sum()
    e["gesamt_gt"] = e.sum(axis=1)
    return e.sort_values("gesamt_gt", ascending=False)


def facts() -> dict:
    """Numbers the two slides state."""
    t = temperature()
    out = {}
    for k in MARKERS:
        s = t[t.szenario == k].set_index("jahr")["median"]
        out[k] = {"peak_k": float(s.max()), "peak_jahr": int(s.idxmax()), "k_2100": float(s[2100]),
                  "k_2150": float(s[2150]),
                  "unter_15_ab": int(next((y for y in s.index if y > s.idxmax() and s[y] < 1.5), 0)) or None}
    cum = cumulative_removal()
    for k in MARKERS:
        out[k].update({c: float(cum.loc[k, c]) for c in cum.columns})
    return out


def _split(years, values, at=EXTENSION_FROM):
    """Solid part up to `at`, dashed part from `at` on (they share the point at `at`)."""
    years = np.asarray(years)
    a = years <= at
    b = years >= at
    return (years[a], np.asarray(values)[a]), (years[b], np.asarray(values)[b])


def temperature_figure(out_path: str) -> str:
    """Median warming of the seven markers (5-95 % for M and L), observations since 1950."""
    _setup()
    t = temperature()
    obs = observations()
    fig, ax = plt.subplots(figsize=(12.0, 5.6), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.07, right=0.83, bottom=0.1, top=0.96)
    _clean_axes(ax)
    for k in ("M", "L"):
        s = t[t.szenario == k]
        s = s[s.jahr >= 2023]
        ax.fill_between(s.jahr, s.p05, s.p95, color=MARKERS[k][1], alpha=0.13, linewidth=0)
    for lvl in (1.5, 2.0):
        ax.axhline(lvl, color=C_INK_MUTED, linewidth=1.0, linestyle=(0, (5, 4)))
        ax.text(1952, lvl + 0.05, f"{lvl:.1f} °C".replace(".0 ", " ").replace(".", ","), fontsize=12,
                color=C_INK_MUTED, va="bottom")
    ax.plot(obs.jahr, obs.erwaermung_k, color=C_INK, linewidth=2.2)
    ax.text(1990, 1.25, "Beobachtung", fontsize=12.5, color=C_INK, ha="right")
    ends = []
    for k, (label, color) in MARKERS.items():
        s = t[(t.szenario == k) & (t.jahr >= 2023)]
        (x1, y1), (x2, y2) = _split(s.jahr, s["median"])
        ax.plot(x1, y1, color=color, linewidth=2.4)
        ax.plot(x2, y2, color=color, linewidth=2.4)
        ends.append([float(y2[-1]), label, color])
    # direct labels at 2100, pushed apart where they would overlap
    ends.sort()
    gap = 0.24
    for i in range(1, len(ends)):
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + gap)
    for y, label, color in ends:
        ax.text(2153, y, label, fontsize=12.5, color=color, va="center", fontweight="bold")
    ax.set_xlim(1950, 2150)
    ax.set_ylim(0, 5)
    ax.set_xticks([1950, 1975, 2000, 2025, 2050, 2075, 2100, 2125, 2150])
    ax.set_yticks([0, 1, 2, 3, 4, 5])
    ax.set_yticklabels([f"{v} °C" for v in range(6)])
    ax.set_ylabel("Erwärmung gegenüber 1850–1900")
    return _save(fig, out_path)


def removal_figure(out_path: str) -> str:
    """Left: CO2 removed per year (novel CDR + land sink). Right: cumulative 2024-2100."""
    _setup()
    e = removal()
    cum = cumulative_removal()
    fig = plt.figure(figsize=WIDE, dpi=FIG_DPI)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], left=0.065, right=0.95, bottom=0.12, top=0.9, wspace=0.42)
    ax, bx = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    _clean_axes(ax)
    for k, (label, color) in MARKERS.items():
        s = e[(e.szenario == k) & (e.jahr >= 2023)]
        (x1, y1), (x2, y2) = _split(s.jahr, s.neuartig_gt + s.land_gt)
        ax.plot(x1, y1, color=color, linewidth=2.4)
        ax.plot(x2, y2, color=color, linewidth=2.4)
    ax.set_xlim(2023, 2150)
    ax.set_ylim(0, None)
    ax.set_xticks([2025, 2050, 2075, 2100, 2125, 2150])
    ax.set_ylabel("Gt CO$_2$ je Jahr")
    ax.set_title("Entnahme je Jahr: neuartig + Landsenke", loc="left", fontsize=14, color=C_INK)

    _clean_axes(bx)
    bx.grid(axis="y", visible=False)
    bx.grid(axis="x", color="#d9d2c4", linewidth=0.8)
    names = list(cum.index)
    ys = np.arange(len(names))[::-1]
    for y, k in zip(ys, names):
        color = MARKERS[k][1]
        n, land, tot = cum.loc[k, ["neuartig_gt", "land_gt", "gesamt_gt"]]
        bx.barh(y, n, color=color, height=0.62)
        bx.barh(y, land, left=n, color=color, alpha=0.38, height=0.62)
        bx.text(tot + 30, y, f"{tot:,.0f}".replace(",", "."), va="center", fontsize=12, color=C_INK)
    bx.set_yticks(ys)
    bx.set_yticklabels([k for k in names])
    for lab, k in zip(bx.get_yticklabels(), names):
        lab.set_color(MARKERS[k][1])
        lab.set_fontweight("bold")
    bx.set_xlim(0, float(cum.gesamt_gt.max()) * 1.18)
    bx.set_xlabel("Gt CO$_2$, 2024–2100")
    bx.set_title("Summe bis 2100: kräftig = neuartig, blass = Land", loc="left", fontsize=14, color=C_INK)
    return _save(fig, out_path)


def build_all(out_dir: str) -> list[str]:
    return [
        temperature_figure(os.path.join(out_dir, "c7_temperatur.png")),
        removal_figure(os.path.join(out_dir, "c7_entnahme.png")),
    ]
