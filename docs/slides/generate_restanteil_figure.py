"""Slide 13: Restanteil eines CO2-Pulses -- vorindustrielle Idealkurve gegen
die eigene SSP2-4.5-Rechnung.

Erzeugt fuer Task 2 von Plan 3 (2026-09-10-praesentation-ergebnisse-und-potenzial),
weil Folie 13 bislang nur die vorindustrielle Joos-Kurve zeigte und den
Unterschied zur eigenen, szenariengebundenen Rechnung nicht sichtbar machte.
Siehe docs/superpowers/specs/2026-09-09-befunde-fuer-plan-2-und-3.md, Abschnitt 2.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from nbs.constants import YEARS
from nbs.response import green_carbon, green_carbon_preindustrial

OUT = os.path.join(os.path.dirname(__file__), "figures")

DARK = "#1E3A2F"
SUB = "#5A6B62"
RED = "#C0392B"
GRN = "#2D6A4F"

plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def main() -> None:
    g_ssp = green_carbon("ssp245")
    g_pre = green_carbon_preindustrial()
    t = YEARS - YEARS[0]  # Jahre seit dem Puls, 0..125

    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    ax.plot(t, g_pre * 100, color=RED, lw=2.6, ls="--",
            label="vorindustrielle Idealkurve (Joos et al. 2013)")
    ax.plot(t, g_ssp * 100, color=GRN, lw=3.0,
            label="eigene Rechnung, SSP2-4.5")
    ax.fill_between(t, g_ssp * 100, g_pre * 100, color=GRN, alpha=0.08)

    idx75 = 75
    for g, color, label in [(g_pre, RED, f"{g_pre[idx75] * 100:.1f} %"),
                             (g_ssp, GRN, f"{g_ssp[idx75] * 100:.1f} %")]:
        ax.plot([idx75], [g[idx75] * 100], "o", color=color, ms=9, zorder=5)
    ax.axvline(idx75, color="0.75", lw=1.0, ls=":")
    ax.annotate(f"75 a: {g_pre[idx75] * 100:.1f} %", xy=(idx75, g_pre[idx75] * 100),
                xytext=(idx75 + 6, g_pre[idx75] * 100 - 10), fontsize=11, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED))
    ax.annotate(f"75 a: {g_ssp[idx75] * 100:.1f} %", xy=(idx75, g_ssp[idx75] * 100),
                xytext=(idx75 + 6, g_ssp[idx75] * 100 + 6), fontsize=11, color=GRN,
                fontweight="bold", arrowprops=dict(arrowstyle="->", color=GRN))

    # Minimum der SSP245-Kurve um 2046 -- real, nicht wegglaetten.
    i_min = int(np.argmin(g_ssp))
    ax.plot([t[i_min]], [g_ssp[i_min] * 100], "v", color=GRN, ms=8, zorder=5)
    ax.annotate(f"Minimum {YEARS[i_min]}: {g_ssp[i_min] * 100:.1f} %,\ndanach wieder steigend",
                xy=(t[i_min], g_ssp[i_min] * 100),
                xytext=(t[i_min] + 2, g_ssp[i_min] * 100 - 32), fontsize=10, color=GRN,
                arrowprops=dict(arrowstyle="->", color=GRN))

    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, 105)
    ax.set_xlabel("Jahre nach der Emission")
    ax.set_ylabel("noch in der Luft [%]")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right", fontsize=11, frameon=False)
    ax.set_title(
        "Je heißer die Welt, desto länger wirkt jede Tonne nach",
        fontsize=14, color=DARK, pad=10,
    )
    ax.text(0.01, 0.03,
            "vorindustriell: g_C nach Joos et al. (2013), fester Hintergrund  —  "
            "SSP2-4.5: nbs.response.green_carbon, Puls auf gesättigteren Senken",
            transform=ax.transAxes, ha="left", fontsize=9.5, color=SUB, style="italic")

    path = os.path.join(OUT, "restanteil_ssp245_vs_vorindustriell.png")
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"saved {path}")
    print(f"g_pre[75] = {g_pre[idx75]:.4f}, g_ssp[75] = {g_ssp[idx75]:.4f}")
    print(f"g_ssp min = {g_ssp[i_min]:.4f} at year {YEARS[i_min]}")


if __name__ == "__main__":
    main()
