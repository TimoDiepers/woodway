"""Kontrollvolumen- und Gleichungsserie für den Vortrag.

Zwei Serien in identischer Bildsprache:
  kv_1..kv_6      Systemgrenze als Kontrollvolumen, Pfeile = Terme der Bilanz
  gl_1..gl_6      dieselbe Bilanzgleichung, bei jeder Stufe um Terme erweitert

Neu hinzukommende Terme sind bernsteinfarben, bereits eingeführte dunkelgrün.
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Ellipse, Polygon, Circle

OUT = os.path.join(os.path.dirname(__file__), "figures")

DARK = "#1E3A2F"
GRN  = "#2D6A4F"
MID  = "#52B788"
AMB  = "#C97D1A"
AMBL = "#FDF0D5"
LITE = "#D8F3DC"
SUB  = "#5A6B62"
TXT  = "#1A2320"
BG   = "#FFFFFF"

plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 12,
    "mathtext.fontset": "dejavusans",
})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  {name}")


# ───────────────────────────────────────────────────────────── Kontrollvolumen
def arrow(ax, p0, p1, color, lw=2.2):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=15,
                                 color=color, lw=lw, shrinkA=0, shrinkB=0, zorder=6))


def _beschriftung(ax, x, y, label, value, col, oben):
    """Label plus Zahlenwert am äußeren Ende eines Pfeils."""
    dy = 0.20 if oben else -0.20
    va = "bottom" if oben else "top"
    ax.text(x, y + dy, label, ha="center", va=va, fontsize=13,
            color=col, fontweight="bold", zorder=7)
    if value:
        ax.text(x, y + dy + (0.34 if oben else -0.34), value, ha="center", va=va,
                fontsize=9.8, color=SUB, zorder=7)


def ein(ax, xy_aussen, xy_grenze, label, value=None, neu=True):
    """Zufluss: Pfeil von außen auf die Systemgrenze."""
    col = AMB if neu else GRN
    arrow(ax, xy_aussen, xy_grenze, col)
    _beschriftung(ax, xy_aussen[0], xy_aussen[1], label, value, col,
                  oben=xy_aussen[1] > xy_grenze[1])


def aus(ax, xy_grenze, xy_aussen, label, value=None, neu=True):
    """Abfluss: Pfeil von der Systemgrenze nach außen."""
    col = AMB if neu else GRN
    arrow(ax, xy_grenze, xy_aussen, col)
    _beschriftung(ax, xy_aussen[0], xy_aussen[1], label, value, col,
                  oben=xy_aussen[1] > xy_grenze[1])


def frame(ax, x, y, w, h, titel):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.15",
                                facecolor="#F7FAF8", edgecolor=DARK, lw=2.0,
                                linestyle=(0, (6, 4)), zorder=2))
    ax.text(x + 0.16, y + 0.22, titel, fontsize=11, color=SUB,
            style="italic", zorder=7)


def fuss(ax, text, col=None):
    ax.text(6.25, 0.30, text, ha="center", fontsize=12, color=col or AMB,
            fontweight="bold")


def leaf(ax, cx, cy, s=1.0):
    ax.add_patch(Ellipse((cx, cy), 2.6 * s, 0.85 * s, angle=-8, facecolor="#40916C",
                         edgecolor=GRN, lw=1.6, zorder=4))
    ax.plot([cx - 1.15 * s, cx + 1.15 * s], [cy + 0.16 * s, cy - 0.16 * s],
            color="#1B4332", lw=1.2, zorder=5)


def tree(ax, cx, cy, s=1.0, col="#1B4332"):
    ax.add_patch(plt.Rectangle((cx - 0.07 * s, cy), 0.14 * s, 0.55 * s,
                               color="#5A3A22", zorder=4))
    for k, wd in enumerate([1.0, 0.8, 0.55]):
        ax.add_patch(Polygon([[cx - wd * s * 0.5, cy + 0.42 * s + k * 0.42 * s],
                              [cx + wd * s * 0.5, cy + 0.42 * s + k * 0.42 * s],
                              [cx, cy + 1.10 * s + k * 0.42 * s]],
                             closed=True, color=col, zorder=4))


def soil(ax, x, y, w, h):
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor="#E4D7C5",
                               edgecolor="#B9A489", lw=1.0, zorder=3))


def kontrollvolumen(stufe: int):
    """Systemgrenze der Stufe 1..6 mit den Termen der jeweiligen Bilanz."""
    fig, ax = plt.subplots(figsize=(12.5, 6.9))
    ax.set_xlim(0, 12.5); ax.set_ylim(0, 6.9); ax.axis("off")

    titel = {
        1: "Systemgrenze: ein Blatt",
        2: "Systemgrenze: ein Baum",
        3: "Systemgrenze: ein Bestand",
        4: "Systemgrenze: Luftsäule bis zur Atmosphärenobergrenze",
        5: "Systemgrenze: das Erdsystem",
        6: "Systemgrenze: das Erdsystem über die Zeit",
    }[stufe]

    if stufe == 1:
        frame(ax, 3.2, 2.4, 6.1, 2.2, "Kontrollvolumen")
        leaf(ax, 6.25, 3.3, 1.15)
        ein(ax, (2.1, 5.9), (4.3, 4.5), r"$(1-\alpha)\,S\!\downarrow$", "≈ 640 W/m²")
        aus(ax, (5.4, 4.5), (5.0, 5.9), r"$\varepsilon\sigma T^4$", "≈ 90 W/m²")
        aus(ax, (7.2, 4.5), (7.6, 5.9), r"$H$", "≈ 150 W/m²")
        aus(ax, (8.6, 4.5), (10.3, 5.9), r"$LE$", "≈ 390 W/m²")
        aus(ax, (6.25, 2.5), (6.25, 1.5), r"$\dot{W}_{\mathrm{chem}}$", "≈ 8 W/m²  (1 – 2 %)")
        fuss(ax, "stationär: das Blatt speichert praktisch keine Energie", SUB)

    elif stufe == 2:
        frame(ax, 2.6, 1.9, 7.3, 3.2, "Kontrollvolumen")
        soil(ax, 2.65, 1.95, 7.2, 0.7)
        tree(ax, 6.25, 2.6, 1.15)
        ein(ax, (1.8, 6.2), (3.6, 5.0), r"$(1-\alpha)\,S\!\downarrow$", None, neu=False)
        aus(ax, (4.4, 5.0), (4.1, 6.2), r"$\varepsilon\sigma T^4,\ H,\ LE$", None, neu=False)
        ein(ax, (7.6, 6.2), (7.4, 5.0), r"$\mathrm{GPP}$", "Bruttoaufnahme")
        aus(ax, (8.6, 5.0), (10.4, 6.2), r"$R_a + R_h$", "≈ 50 % der GPP")
        aus(ax, (6.25, 2.0), (6.25, 1.1), r"$\Lambda$", "Streu in den Boden")
        fuss(ax, r"neu: Speicherterme  d$C_B$/d$t$  und  d$C_S$/d$t$  —  die Bilanz ist nicht mehr nur Energie")

    elif stufe == 3:
        frame(ax, 1.5, 1.9, 9.5, 3.3, "Kontrollvolumen")
        soil(ax, 1.55, 1.95, 9.4, 0.7)
        for x, sc in [(2.6, 0.95), (4.0, 1.15), (5.4, 1.0), (6.8, 1.2), (8.2, 1.0), (9.6, 0.9)]:
            tree(ax, x, 2.6, sc)
        ein(ax, (1.5, 6.3), (2.9, 5.1), r"$R_n$", "Nettostrahlung", neu=False)
        aus(ax, (4.4, 5.1), (4.2, 6.3), r"$H$", r"Bowen $\beta = H/LE$", neu=False)
        aus(ax, (6.3, 5.1), (6.4, 6.3), r"$LE$", "Wald: β ≈ 0,3 – 0,6", neu=False)
        aus(ax, (8.6, 5.1), (9.6, 6.3), r"$g_a$", "Rauigkeit 5 – 10× Gras")
        aus(ax, (6.25, 2.0), (6.25, 1.1), r"$G$", "Bodenwärmestrom")
        fuss(ax, "neu: turbulenter Austausch und Speicher des ganzen Bestands")

    elif stufe == 4:
        frame(ax, 1.2, 1.6, 10.1, 3.7, "Kontrollvolumen bis zur Atmosphärenobergrenze (TOA)")
        ax.plot([1.3, 11.2], [5.05, 5.05], color="#7FA8C9", lw=1.6, ls="--", zorder=4)
        ax.text(1.45, 5.16, "TOA", fontsize=10.5, color="#39668C")
        ax.add_patch(plt.Rectangle((1.3, 3.45), 9.9, 1.0, facecolor="#EAF2F8",
                                   edgecolor="#B9CBD8", lw=1.0, zorder=3))
        ax.text(6.25, 3.95, r"Atmosphäre:  CO$_2$, H$_2$O, Wolken", ha="center",
                fontsize=12, color="#39668C", zorder=5)
        soil(ax, 1.35, 1.65, 9.9, 0.6)
        for x, sc in [(3.0, 0.8), (4.2, 0.9), (5.4, 0.8), (6.6, 0.95), (7.8, 0.8)]:
            tree(ax, x, 2.2, sc)
        ein(ax, (2.2, 6.25), (2.5, 5.15), r"$S\!\downarrow$", None, neu=False)
        aus(ax, (4.9, 5.15), (4.6, 6.25), r"$\Delta F_{\mathrm{CO_2}}$", r"$5{,}35\,\ln(C/C_0)$")
        aus(ax, (7.3, 5.15), (7.5, 6.25), r"$f_A\,\Delta F_\alpha$", r"$f_A = A_i/A_E$")
        aus(ax, (9.4, 5.15), (10.4, 6.25), r"$f_A\,\Delta F_{LE}$", "nichtstrahlend")
        fuss(ax, r"neu: lokale Flüsse werden über den Flächenanteil $f_A$ zu globalen Antrieben")

    elif stufe == 5:
        frame(ax, 1.2, 1.5, 10.1, 4.2, "Kontrollvolumen: Planet")
        ax.add_patch(Circle((6.25, 3.4), 1.45, facecolor="#3E7CB1", edgecolor="#2C5F8A",
                            lw=1.5, zorder=4))
        ax.text(6.25, 3.4, "Erde", ha="center", va="center", color="white",
                fontsize=13, fontweight="bold", zorder=5)
        ax.add_patch(Circle((6.25, 3.4), 1.9, facecolor="none", edgecolor="#9CC3DE",
                            lw=1.2, ls="--", zorder=3))
        ein(ax, (2.3, 6.4), (4.6, 4.6), r"$\Delta F$", "Antrieb", neu=False)
        aus(ax, (7.9, 4.6), (10.2, 6.4), r"$\lambda\,\Delta T$", "λ ≈ 1,3 W/m²K")
        ax.text(2.6, 2.35, r"$C\,\mathrm{d}\Delta T/\mathrm{d}t$", fontsize=15, color=AMB)
        ax.text(2.6, 1.95, "Deckschicht speichert", fontsize=10, color=SUB)
        ax.text(8.3, 2.35, r"$\gamma\,(\Delta T - \Delta T_d)$", fontsize=15, color=AMB)
        ax.text(8.3, 1.95, "Tiefenozean, Jahrhunderte", fontsize=10, color=SUB)
        fuss(ax, "neu: Wärmespeicher und Rückkopplungen des Planeten — Ozean nimmt 91 % auf")

    else:
        frame(ax, 1.2, 1.8, 10.1, 3.9, "Kontrollvolumen: Planet, instationär")
        ax.add_patch(Circle((3.0, 3.6), 1.0, facecolor="#3E7CB1", edgecolor="#2C5F8A",
                            lw=1.4, zorder=4))
        ax.text(3.0, 3.6, "Erde", ha="center", va="center", color="white",
                fontsize=11.5, fontweight="bold", zorder=5)
        ax.annotate("", xy=(10.8, 2.5), xytext=(4.6, 2.5),
                    arrowprops=dict(arrowstyle="-|>", color=DARK, lw=2.2), zorder=6)
        ax.text(7.7, 2.15, "Zeit", ha="center", fontsize=12, color=DARK, fontweight="bold")
        for x, sc, lab in [(5.3, 0.45, "Pflanzung"), (6.9, 0.75, "+20 a"),
                           (8.5, 1.0, "+50 a"), (10.1, 1.2, "+100 a")]:
            tree(ax, x, 2.75, sc)
            ax.text(x, 5.05, lab, ha="center", fontsize=9.8, color=SUB)
        ax.text(6.25, 6.3, r"$\Delta T(t) = \int_0^{\,t} R(t-t^{\prime})\,"
                           r"\Delta F(t^{\prime})\,\mathrm{d}t^{\prime}$",
                ha="center", fontsize=17, color=AMB)
        fuss(ax, "neu: Antrieb und Antwort haben verschiedene Zeitkonstanten")

    save(fig, f"kv_{stufe}.png")


# ─────────────────────────────────────────────────────────────── Gleichungen
def gleichung(stufe: int, fragmente, symbole, quelle):
    """Bilanzgleichung aus Fragmenten (tex, neu?) plus Symboltabelle."""
    fig = plt.figure(figsize=(12.5, 5.4))
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    renderer = fig.canvas.get_renderer()
    x_px = 60
    y_px = fig.get_figheight() * fig.dpi - 130
    for tex, neu in fragmente:
        t = ax.text(x_px, y_px, tex, transform=None, fontsize=25,
                    color=AMB if neu else DARK,
                    fontweight="bold" if neu else "normal", va="center")
        x_px += t.get_window_extent(renderer=renderer).width + 8

    y = 0.60
    for sym, bedeutung, wert in symbole:
        ax.text(0.05, y, sym, fontsize=15, color=DARK, va="center")
        ax.text(0.20, y, bedeutung, fontsize=13, color=TXT, va="center")
        ax.text(0.68, y, wert, fontsize=13, color=SUB, va="center")
        y -= 0.105

    ax.add_patch(plt.Rectangle((0.045, 0.035), 0.91, 0.075, transform=ax.transAxes,
                               facecolor=LITE, edgecolor=GRN, lw=0, zorder=1))
    ax.text(0.062, 0.072, quelle, fontsize=11, color=GRN, va="center", zorder=2)
    save(fig, f"gl_{stufe}.png")


def alle_gleichungen():
    gleichung(
        1,
        [(r"$0$", False), (r"$=$", False), (r"$(1-\alpha)\,S\!\downarrow$", True),
         (r"$-\ \varepsilon\sigma T^4$", True), (r"$-\ H$", True), (r"$-\ LE$", True),
         (r"$-\ \dot{W}_{\mathrm{chem}}$", True)],
        [(r"$\alpha$", "Albedo des Blattes", "0,15 – 0,25"),
         (r"$H$", "fühlbarer Wärmestrom", "≈ 150 W/m²"),
         (r"$LE$", "latenter Wärmestrom (Transpiration)", "≈ 390 W/m²"),
         (r"$\dot{W}_{\mathrm{chem}}$", "chemisch gebundene Leistung", "≈ 8 W/m²  (1 – 2 %)")],
        "Gates (1980) · Nobel (2009) · Monteith & Unsworth (2013) · Wirkungsgrad: Zhu, Long & Ort (2010)",
    )

    gleichung(
        2,
        [(r"$0 = (1-\alpha)S\!\downarrow - \varepsilon\sigma T^4 - H - LE - \dot{W}_{\mathrm{chem}}$", False),
         (r"$\qquad$", False),
         (r"$\dfrac{\mathrm{d}C_B}{\mathrm{d}t} = \mathrm{GPP} - R_a - \Lambda$", True)],
        [(r"$\mathrm{GPP}$", "Bruttoprimärproduktion", "Bruttoaufnahme"),
         (r"$R_a$", "Eigenatmung der Pflanze", "≈ 50 % der GPP"),
         (r"$\Lambda$", "Streufall in den Boden", "Blätter, Feinwurzeln"),
         (r"$\mathrm{d}C_S/\mathrm{d}t$", r"Bodenkohlenstoff: $\Lambda - R_h$", "Umsatz Jahre – Jahrhunderte")],
        "Kohlenstoffnutzungseffizienz NPP/GPP ≈ 0,45 – 0,55: Waring et al. (1998) · DeLucia et al. (2007)",
    )

    gleichung(
        3,
        [(r"$R_n$", False), (r"$=$", False), (r"$H$", False), (r"$+\ LE$", False),
         (r"$+\ G$", True), (r"$+\ \Delta S$", True),
         (r"$\qquad \beta = H/LE$", True)],
        [(r"$R_n$", "Nettostrahlung des Bestands", r"$(1-\alpha_s)S\!\downarrow + L\!\downarrow - L\!\uparrow$"),
         (r"$\beta$", "Bowen-Verhältnis", "Wald 0,3 – 0,6 · Gras 0,6 – 1,5"),
         (r"$g_a$", "aerodynamische Leitfähigkeit", "Wald 5 – 10× höher als Gras"),
         (r"$\alpha_s$", "Bestandsalbedo", "Nadelwald 0,08 – 0,12 · Gras 0,20")],
        "Jarvis & McNaughton (1986) · Bonan (2008) · Lee et al. (2011) · Alkama & Cescatti (2016) · Duveiller et al. (2018)",
    )

    gleichung(
        4,
        [(r"$\Delta N$", True), (r"$=$", False), (r"$\Delta F$", True),
         (r"$-\ \lambda\,\Delta T$", True), (r"$,\qquad$", False),
         (r"$\Delta F = \Delta F_{\mathrm{CO_2}} + f_A\,(\Delta F_\alpha + \Delta F_{LE})$", True)],
        [(r"$\Delta N$", "Energieungleichgewicht an der TOA", "W/m²"),
         (r"$\Delta F_{\mathrm{CO_2}}$", r"$5{,}35\,\ln(C/C_0)$", "Myhre et al. (1998)"),
         (r"$f_A$", r"Flächenanteil $A_i/A_E$", r"1 Mha $\to$ 2,0·10⁻⁵"),
         (r"$\lambda$", "Rückkopplungsparameter", "≈ 1,3 W/m²K")],
        "Betts (2000) · Bala et al. (2007) · Bright et al. (2015) · Winckler et al. (2019): lokal ≠ global",
    )

    gleichung(
        5,
        [(r"$C\,\dfrac{\mathrm{d}\Delta T}{\mathrm{d}t}$", True), (r"$=$", False),
         (r"$\Delta F$", False), (r"$-\ \lambda\,\Delta T$", False),
         (r"$-\ \gamma\,(\Delta T - \Delta T_d)$", True)],
        [(r"$C$", "Wärmekapazität der Deckschicht", "Ozean nimmt 91 % auf"),
         (r"$\gamma$", "Austausch mit dem Tiefenozean", "Jahrhunderte"),
         (r"$\lambda$", "Klimarückkopplung", "1,2 – 1,4 W/m²K"),
         ("TCRE", "Erwärmung je 1000 GtCO₂", "0,27 – 0,63 K")],
        "Gregory et al. (2004) · Held et al. (2010) · Geoffroy et al. (2013) · Sherwood et al. (2020) · IPCC AR6",
    )

    gleichung(
        6,
        [(r"$\Delta T(t)$", True), (r"$=$", False),
         (r"$\int_0^{\,t} R(t-t^{\prime})\,\Delta F(t^{\prime})\,\mathrm{d}t^{\prime}$", True)],
        [(r"$R$", "Impulsantwort des Klimasystems", "zwei Zeitkonstanten: ~4 a, ~250 a"),
         (r"$\Delta F(t)$", "zeitabhängiger Antrieb", "Emission sofort, Wald über Jahrzehnte"),
         (r"$t^*$", "Umschlagpunkt der Nettowirkung", "aus dem Modell"),
         (r"$\int \Delta T\,\mathrm{d}t$", "zeitintegrierte Erwärmung", "K·a")],
        "Joos et al. (2013) · Millar et al. (2017) · Leach et al. (2021) · Metrik: Kirschbaum (2006), Sierra et al. (2021)",
    )


if __name__ == "__main__":
    print("=== Kontrollvolumen ===")
    for st in range(1, 7):
        kontrollvolumen(st)
    print("=== Gleichungen ===")
    alle_gleichungen()
    print("=== fertig ===")
