"""Slide 12: Wachstumskurve -- die tatsaechlichen Picea-abies-Parameter statt
drei Legacy-Parametersaetzen.

Die bisherige Abbildung (fig_wachstum.png) zeigte drei hektarbezogene
Legacy-Parametersaetze ("tropische/boreale Aufforstung", "Kurzumtrieb
(BECCS)", tC/ha) aus einem aelteren Modell -- eine andere Groesse als die
jetzt im Formelzeichen-Text der Folie genannten m_max_kgC (pro Baum, kgC)
von Picea abies. Gefunden bei der Sichtpruefung in Task 2 (siehe
task-1-2-report.md), dort als Inkonsistenz vermerkt, hier behoben.

Diese Abbildung zeigt stattdessen m(t) = nbs.tree.biomass_closed(t, sp) fuer
Picea abies (nbs.species.SPECIES["picea_abies"]) und die davon abgeleitete
Stoerungsverlustrate m_Stoer(t) = p_Stoer * m(t) -- exakt die zwei Formeln,
die die Folie als LaTeX-Text traegt.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from nbs.species import SPECIES
from nbs.tree import biomass_closed

OUT = os.path.join(os.path.dirname(__file__), "figures")

DARK = "#1E3A2F"
SUB = "#5A6B62"
GRN = "#2D6A4F"
RED = "#C0392B"

plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def main() -> None:
    sp = SPECIES["picea_abies"]
    t = np.linspace(0, 150, 601)
    m = biomass_closed(t, sp)
    loss_rate = sp.p_disturb * m  # dot m_Stoer(t) = p_Stoer * m(t)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 7.2), sharex=True)

    ax1.plot(t, m, color=GRN, lw=3.0)
    ax1.axhline(sp.m_max_kgC, color="0.75", lw=1.0, ls=":")
    ax1.annotate(f"m_max = {sp.m_max_kgC:.0f} kgC", xy=(150, sp.m_max_kgC),
                 xytext=(-6, 6), textcoords="offset points",
                 ha="right", fontsize=10, color=SUB)

    # 90%-Marke: wann ist der Vorrat "fast voll"?
    frac = 0.90
    t90 = -np.log(1 - frac ** (1.0 / sp.p)) / sp.k
    ax1.plot([t90], [frac * sp.m_max_kgC], "o", color=GRN, ms=8, zorder=5)
    ax1.annotate(f"90 % nach {t90:.0f} a", xy=(t90, frac * sp.m_max_kgC),
                 xytext=(t90 + 6, frac * sp.m_max_kgC - 8), fontsize=10, color=GRN,
                 arrowprops=dict(arrowstyle="->", color=GRN))

    ax1.set_ylabel("Vorrat m(t)\n[kgC je Baum]")
    ax1.set_ylim(0, sp.m_max_kgC * 1.08)
    ax1.grid(True, alpha=0.25)
    ax1.set_title(
        f"{sp.name_de} ({sp.name_lat}): Chapman-Richards-Wachstum und Störungsverlust",
        fontsize=13, color=DARK, pad=10,
    )

    ax2.plot(t, loss_rate, color=RED, lw=2.6)
    ax2.fill_between(t, 0, loss_rate, color=RED, alpha=0.10)
    ax2.set_ylabel("Störungsrate $\\dot m_{Stör}(t)$\n[kgC/a je Baum]")
    ax2.set_xlabel("Baumalter [a]")
    ax2.set_xlim(0, 150)
    ax2.grid(True, alpha=0.25)
    ax2.text(0.01, 0.90,
              "Verlust hängt am Vorrat, nicht am Zuwachs — mit dem Bestand wächst auch,\n"
              "was ein Störungsereignis kosten kann.",
              transform=ax2.transAxes, ha="left", va="top", fontsize=9.5, color=SUB,
              style="italic")

    fig.text(0.01, 0.005,
              "m_max = 50 kgC, k = 0,030 1/a, p = 2,0, p_Stör = 0,012 1/a — "
              "nbs.species.SPECIES['picea_abies'], nbs.tree.biomass_closed",
              ha="left", fontsize=8.5, color=SUB)

    fig.tight_layout(rect=(0, 0.02, 1, 1))
    path = os.path.join(OUT, "wachstumskurve_picea_abies.png")
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"saved {path}")
    print(f"m_max={sp.m_max_kgC}, k={sp.k}, p={sp.p}, p_disturb={sp.p_disturb}")
    print(f"t90%={t90:.2f}")


if __name__ == "__main__":
    main()
