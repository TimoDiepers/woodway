"""Abbildungen für den erzählenden Teil und die Ergebnisse der Reise."""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
from nbs.legacy.carbon_module import area_for_credit
from nbs.legacy.credit_analysis import REISE, run_with
from nbs.legacy.parameters import T_END, T_START

OUT = os.path.join(os.path.dirname(__file__), "figures")

# Die Maßeinheit des Vortrags: ein Hin- und Rückflug pro Person.
FLUG_TCO2 = 2.0        # tCO2
STAEMME_HA = 2000      # Setzlinge je Hektar, übliche Pflanzdichte


def baeume_pro_flug(lat: int) -> float:
    """Wie viele Bäume die Zertifikatsrechnung für einen Flug bucht."""
    from nbs.legacy.carbon_module import nominal_credit_gtco2
    t_pro_ha = nominal_credit_gtco2(lat, 1.0) * 1e3
    return FLUG_TCO2 / t_pro_ha * STAEMME_HA


def m2_pro_flug(lat: int) -> float:
    from nbs.legacy.carbon_module import nominal_credit_gtco2
    t_pro_ha = nominal_credit_gtco2(lat, 1.0) * 1e3
    return FLUG_TCO2 / t_pro_ha * 1e4
YEARS = np.arange(T_START, T_END)

DARK = "#1E3A2F"
GRN = "#2D6A4F"
MID = "#52B788"
LITE = "#D8F3DC"
AMB = "#C97D1A"
AMBL = "#FDF0D5"
SUN = "#F2A93B"
WATER = "#3C8DBC"
IR = "#8E6BB0"
RED = "#C0392B"
SUB = "#5A6B62"
TXT = "#1A2320"

plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

STATION_FARBE = {"zertifikat": "#8C8C8C", "baum": MID, "boden": AMB, "luft": RED}
STATION_NAME = {
    "zertifikat": "wie das Zertifikat rechnet",
    "baum": "der Baum wächst",
    "boden": "Boden und Störungen",
    "luft": "Albedo und Verdunstung",
}


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {name}")


def arrow(ax, p0, p1, color, lw=2.4):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=16,
                                 color=color, lw=lw, shrinkA=0, shrinkB=0, zorder=6))


def box(ax, x, y, w, h, fc, ec, lw=1.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.12",
                                facecolor=fc, edgecolor=ec, lw=lw, zorder=3))


# ── 1. Was macht ein Baum den ganzen Tag ────────────────────────────────────
def sonne():
    fig, ax = plt.subplots(figsize=(12.5, 5.6))
    ax.set_xlim(0, 12.5); ax.set_ylim(0, 5.6); ax.axis("off")

    ax.add_patch(plt.Circle((1.1, 4.6), 0.5, color=SUN, zorder=4))
    ax.text(1.1, 3.75, "100", ha="center", fontsize=22, fontweight="bold", color="#B87407")
    ax.text(1.1, 3.35, "Sonne", ha="center", fontsize=12, color=SUB)
    arrow(ax, (1.75, 4.3), (3.3, 3.3), SUN, lw=3.4)

    ax.add_patch(plt.matplotlib.patches.Ellipse((4.3, 2.9), 2.1, 0.72, angle=-8,
                                                facecolor="#40916C", edgecolor=GRN, lw=1.8, zorder=4))
    ax.text(4.3, 2.9, "Blatt", ha="center", va="center", color="white",
            fontsize=12, fontweight="bold", zorder=5)

    posten = [
        ("zurückgeworfen", 20, SUN, 4.9),
        ("abgestrahlte Wärme", 21, IR, 3.85),
        ("warme Luft", 13, RED, 2.8),
        ("verdunstetes Wasser", 45, WATER, 1.75),
        ("Zucker", 1, GRN, 0.55),
    ]
    for name, wert, farbe, y in posten:
        arrow(ax, (5.5, 2.9), (6.6, y + 0.28), farbe, lw=1.4 + wert * 0.06)
        breite = 0.055 * wert + 0.35
        box(ax, 6.75, y, breite, 0.62, farbe, farbe, lw=0)
        ax.text(6.9, y + 0.31, str(wert), va="center", fontsize=16,
                fontweight="bold", color="white" if wert > 8 else farbe, zorder=5)
        ax.text(6.75 + breite + 0.25, y + 0.31, name, va="center", fontsize=13.5, color=TXT)

    ax.text(9.6, 0.86, "← davon lebt die Klimadebatte", fontsize=12.5,
            color=GRN, fontweight="bold")
    save(fig, "s1_sonne.png")


# ── 2. Wo landet der Zucker ─────────────────────────────────────────────────
def zucker():
    fig, ax = plt.subplots(figsize=(12.5, 5.4))
    ax.set_xlim(0, 12.5); ax.set_ylim(0, 5.4); ax.axis("off")

    box(ax, 0.3, 2.3, 2.3, 1.1, LITE, GRN)
    ax.text(1.45, 3.05, "100", ha="center", fontsize=20, fontweight="bold", color=GRN)
    ax.text(1.45, 2.62, "Zucker", ha="center", fontsize=12, color=SUB)

    arrow(ax, (2.7, 2.85), (4.0, 2.85), GRN)
    box(ax, 4.1, 2.3, 2.5, 1.1, "#F7F2E7", AMB)
    ax.text(5.35, 3.05, "50", ha="center", fontsize=20, fontweight="bold", color=AMB)
    ax.text(5.35, 2.62, "bleiben übrig", ha="center", fontsize=12, color=SUB)

    arrow(ax, (5.35, 3.5), (5.35, 4.7), RED)
    ax.text(5.55, 4.45, "50 veratmet der Baum selbst — wieder in die Luft",
            fontsize=13, color=RED, fontweight="bold")

    ziele = [
        ("Holz", 25, "Jahrzehnte", 3.35, MID),
        ("Blätter", 15, "wenige Jahre", 2.15, "#88C9A1"),
        ("Wurzeln", 10, "teils in den Boden", 0.95, "#B7C4AF"),
    ]
    for name, wert, dauer, y, farbe in ziele:
        arrow(ax, (6.7, 2.85), (7.9, y + 0.42), farbe)
        box(ax, 8.0, y, 1.5, 0.85, farbe, farbe, lw=0)
        ax.text(8.75, y + 0.42, str(wert), ha="center", va="center",
                fontsize=18, fontweight="bold", color="white")
        ax.text(9.7, y + 0.55, name, fontsize=13.5, color=TXT, fontweight="bold")
        ax.text(9.7, y + 0.2, f"bleibt {dauer}", fontsize=11, color=SUB)

    save(fig, "s2_zucker.png")


# ── Die Maßeinheit des Vortrags ─────────────────────────────────────────────
def einheit():
    fig, ax = plt.subplots(figsize=(12.5, 4.4))
    ax.set_xlim(0, 12.5); ax.set_ylim(0, 4.4); ax.axis("off")

    stationen = [
        ("ein Flug", "hin und zurück", "#9DB4C0"),
        ("2 Tonnen CO₂", "pro Person", RED),
        ("11 Bäume", "sagt das Zertifikat", MID),
        ("55 m²", "ein Stück Wald,\netwa ein kleines Zimmer", GRN),
    ]
    w = 2.75
    for i, (gross, klein, farbe) in enumerate(stationen):
        x = 0.42 + i * (w + 0.3)
        box(ax, x, 1.15, w, 1.85, "#FFFFFF", farbe, lw=2.2)
        ax.text(x + w / 2, 2.42, gross, ha="center", va="center",
                fontsize=18, fontweight="bold", color=farbe)
        ax.text(x + w / 2, 1.68, klein, ha="center", va="center",
                fontsize=10.5, color=SUB, linespacing=1.3)
        if i < len(stationen) - 1:
            arrow(ax, (x + w + 0.08, 2.05), (x + w + 0.47, 2.05), DARK, lw=2.0)
    ax.text(6.25, 0.55, "Das ist ab jetzt unsere Maßeinheit — alle Zahlen im Vortrag "
                        "gelten für diesen einen Flug",
            ha="center", fontsize=12.5, color=DARK, style="italic")
    save(fig, "s0_einheit.png")


# ── 3. Die Speicher und ihr Leck (je Hektar, gleiche Skala wie der Rest) ────
def speicher():
    fig, (ax, axr) = plt.subplots(1, 2, figsize=(13, 5.2),
                                  gridspec_kw={"width_ratios": [1.1, 1]})
    namen = ["Blätter und\nFeinwurzeln", "Holz", "Boden"]
    werte = [8, 92, 100]
    farben = ["#A3B18A", MID, "#8B6F47"]
    bars = ax.bar(namen, werte, color=farben, width=0.58)
    for b, v in zip(bars, werte):
        ax.text(b.get_x() + b.get_width() / 2, v + 3, f"{v} t",
                ha="center", fontsize=13, fontweight="bold", color=TXT)
    ax.set_ylabel("Kohlenstoff je Hektar [tC]")
    ax.set_ylim(0, 125)
    ax.grid(True, axis="y", alpha=0.25)
    ax.set_title("Ein Hektar Wald bei 45 °N — wo der Kohlenstoff steckt",
                 fontsize=13, color=DARK, pad=10)
    for x, txt in [(0, "Jahre"), (1, "Jahrzehnte"), (2, "Jahrhunderte")]:
        ax.text(x, 6, txt, ha="center", fontsize=11, color="white", fontweight="bold")

    axr.set_xlim(0, 10); axr.set_ylim(0, 8); axr.axis("off")
    box(axr, 1.2, 2.6, 7.4, 3.4, "#EFE3D2", "#B9A489")
    axr.text(4.9, 5.3, "gespeicherter Kohlenstoff", ha="center", fontsize=13.5,
             color="#6B5535", fontweight="bold")
    for x, txt in [(2.4, "Feuer"), (4.9, "Käfer"), (7.4, "Dürre")]:
        arrow(axr, (x, 2.6), (x, 0.9), RED, lw=2.6)
        axr.text(x, 0.45, txt, ha="center", fontsize=12.5, color=RED, fontweight="bold")
    axr.text(4.9, 6.8, "Ein Speicher mit Leckrate", ha="center", fontsize=15,
             fontweight="bold", color=DARK)
    axr.text(4.9, 6.25, "was drin ist, muss nicht drin bleiben", ha="center",
             fontsize=12, color=SUB, style="italic")
    plt.tight_layout()
    save(fig, "s3_speicher.png")


# ── 4. Wohin die Tonne verschwindet ─────────────────────────────────────────
def tonne():
    """Impulsantwort des Kohlenstoffkreislaufs, Joos et al. (2013)."""
    t = np.arange(0, 1001, 1.0)
    frac = (0.2173 + 0.2240 * np.exp(-t / 394.4)
            + 0.2824 * np.exp(-t / 36.54) + 0.2763 * np.exp(-t / 4.304))

    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    ax.plot(t, frac * 100, color=RED, lw=3)
    ax.fill_between(t, frac * 100, 0, color=RED, alpha=0.12)
    ax.set_xscale("symlog", linthresh=10)
    ax.set_xlim(0, 1000); ax.set_ylim(0, 105)
    ax.set_xlabel("Jahre nach der Emission")
    ax.set_ylabel("noch in der Luft [%]")
    ax.set_xticks([0, 10, 100, 1000])
    ax.set_xticklabels(["heute", "10", "100", "1000"])
    ax.grid(True, alpha=0.25)
    for jahr, txt in [(10, "nach 10 Jahren\nnoch 68 %"),
                      (100, "nach 100 Jahren\nnoch 41 %"),
                      (1000, "nach 1000 Jahren\nnoch 24 %")]:
        i = int(jahr)
        ax.plot([jahr], [frac[i] * 100], "o", color=RED, ms=9)
        ax.annotate(txt, xy=(jahr, frac[i] * 100), xytext=(jahr * 0.55, frac[i] * 100 + 18),
                    fontsize=11.5, color=RED,
                    arrowprops=dict(arrowstyle="->", color=RED))
    ax.set_title("Eine Tonne CO₂ verschwindet nicht — sie verdünnt sich",
                 fontsize=14, color=DARK, pad=10)
    ax.text(0.98, 0.06, "Impulsantwort nach Joos et al. (2013)", transform=ax.transAxes,
            ha="right", fontsize=10.5, color=SUB, style="italic")
    save(fig, "s4_tonne.png")


# ── 5. Alle Uhren nebeneinander ─────────────────────────────────────────────
def uhren():
    eintraege = [
        ("die Buchung im Zertifikat", None, "sofort und für immer", "#8C8C8C"),
        ("Wärme im Blatt", 10 / (365 * 24 * 3600), "Sekunden", "#88C9A1"),
        ("Wasserdampf in der Luft", 9 / 365, "9 Tage", WATER),
        ("Blattstreu am Boden", 2, "2 Jahre", "#A3B18A"),
        ("Holz im Stamm", 50, "Jahrzehnte", MID),
        ("Kohlenstoff im Boden", 300, "Jahrhunderte", "#8B6F47"),
        ("CO₂ in der Luft", 400, "Jahrhunderte", RED),
        ("Wärme im Ozean", 1000, "Jahrtausende", "#2C6D93"),
    ]
    fig, ax = plt.subplots(figsize=(12.5, 6.2))
    links = 3e-8
    y = np.arange(len(eintraege))[::-1]
    for (name, jahre, label, farbe), yy in zip(eintraege, y):
        if jahre is None:
            ax.plot([links], [yy], marker="X", ms=17, color=farbe, zorder=5)
            ax.text(links * 2.2, yy, label, va="center", fontsize=12.5,
                    color=farbe, fontweight="bold")
            continue
        ax.plot([links, jahre], [yy, yy], color=farbe, lw=3.0, alpha=0.55, zorder=3)
        ax.plot([jahre], [yy], marker="o", ms=14, color=farbe, zorder=5)
        ax.text(jahre * 1.9, yy, label, va="center", fontsize=12.5,
                color=farbe, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([e[0] for e in eintraege], fontsize=13.5)
    ax.set_xscale("log")
    ax.set_xlim(links * 0.6, 3e4)
    ax.set_xticks([1e-7, 1e-5, 1e-3, 1e-1, 1e1, 1e3])
    ax.set_xticklabels(["Sekunde", "Minute", "Stunde", "Monat", "Jahrzehnt", "Jahrtausend"])
    ax.set_xlabel("wie lange es liegen bleibt")
    ax.grid(True, axis="x", alpha=0.25)
    ax.axhline(y[0] - 0.5, color=DARK, lw=1.2, ls="--")
    ax.text(3e2, y[0], "hier rechnet die Kompensation", fontsize=12.5,
            color=DARK, fontweight="bold", ha="right", va="center")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    save(fig, "s5_uhren.png")


# ── 6. Zwei Uhren: lokal und sofort gegen global und langsam ────────────────
def zwei_uhren():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.0))
    for ax in axes:
        ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis("off")

    ax = axes[0]
    box(ax, 0.6, 1.2, 8.8, 5.2, AMBL, AMB)
    ax.text(5.0, 5.75, "wirkt sofort — aber nur vor Ort", ha="center",
            fontsize=15, fontweight="bold", color="#8A5311")
    for i, (t, d) in enumerate([("dunklere Kronen", "mehr Sonne wird geschluckt"),
                                ("mehr Verdunstung", "kühlt die Oberfläche"),
                                ("raue Oberfläche", "mischt Wärme nach oben")]):
        ax.text(1.2, 4.65 - i * 1.05, t, fontsize=13.5, fontweight="bold", color=TXT)
        ax.text(1.2, 4.28 - i * 1.05, d, fontsize=11.5, color=SUB)
    ax.text(5.0, 0.55, "Wirkung: ab dem ersten Jahr, im Umkreis des Waldes",
            ha="center", fontsize=12, color="#8A5311", style="italic")

    ax = axes[1]
    box(ax, 0.6, 1.2, 8.8, 5.2, LITE, GRN)
    ax.text(5.0, 5.75, "wirkt langsam — dafür überall", ha="center",
            fontsize=15, fontweight="bold", color=GRN)
    for i, (t, d) in enumerate([("Kohlenstoff im Holz", "baut sich über Jahrzehnte auf"),
                                ("weniger CO₂ in der Luft", "wirkt auf dem ganzen Planeten"),
                                ("bleibt Jahrhunderte", "solange der Speicher hält")]):
        ax.text(1.2, 4.65 - i * 1.05, t, fontsize=13.5, fontweight="bold", color=TXT)
        ax.text(1.2, 4.28 - i * 1.05, d, fontsize=11.5, color=SUB)
    ax.text(5.0, 0.55, "Wirkung: erst nach Jahrzehnten, dann global",
            ha="center", fontsize=12, color=GRN, style="italic")
    plt.tight_layout()
    save(fig, "s6_zwei_uhren.png")


# ── Modellarchitektur: aus Stationen werden Module ──────────────────────────
def architektur():
    fig, ax = plt.subplots(figsize=(12.5, 5.2))
    ax.set_xlim(0, 12.5); ax.set_ylim(0, 5.2); ax.axis("off")
    stationen = [
        ("Blatt & Baum", "carbon_module", "wie viel CO₂, wann"),
        ("Wald & Boden", "carbon_module", "Speicher, Q₁₀, Störungen"),
        ("Oberfläche", "albedo_module\net_module", "Albedo, Verdunstung"),
        ("Luft", "Flächenwichtung", "lokal → global, W/m²"),
        ("Planet", "fair_module", "Antrieb → Temperatur"),
    ]
    w = 2.15
    for i, (station, modul, was) in enumerate(stationen):
        x = 0.35 + i * (w + 0.32)
        box(ax, x, 3.15, w, 1.35, LITE, GRN)
        ax.text(x + w / 2, 3.82, station, ha="center", va="center",
                fontsize=13.5, fontweight="bold", color=DARK)
        arrow(ax, (x + w / 2, 3.05), (x + w / 2, 2.35), GRN, lw=2.0)
        box(ax, x, 0.95, w, 1.35, "#EEF3F0", DARK)
        ax.text(x + w / 2, 1.9, modul, ha="center", va="center",
                fontsize=11, fontweight="bold", color=GRN, family="monospace")
        ax.text(x + w / 2, 1.35, was, ha="center", va="center", fontsize=10, color=SUB)
        if i < len(stationen) - 1:
            arrow(ax, (x + w + 0.04, 1.62), (x + w + 0.28, 1.62), DARK, lw=1.8)
    ax.text(6.25, 4.85, "Die Stationen der Reise sind die Bausteine des Modells",
            ha="center", fontsize=14, fontweight="bold", color=DARK)
    ax.text(6.25, 0.35, "jede Station bringt genau einen Term mit", ha="center",
            fontsize=11.5, color=SUB, style="italic")
    save(fig, "architektur.png")


# ── Ergebnisse ──────────────────────────────────────────────────────────────
def _laufe(lat, area_faktor=1.0):
    area = area_for_credit(1.0, lat) * area_faktor
    return {name: run_with(lat, area_mha=area, **flags) for name, flags in REISE.items()}


def treffen(lat=45):
    """Treffen sich die beiden Reisenden? Mit der Fläche, die es wirklich braucht."""
    basis = area_for_credit(1.0, lat)
    voll = run_with(lat, area_mha=basis, **REISE["luft"])
    eq = voll["equivalence_ratio_2100"]
    gross = run_with(lat, area_mha=basis * eq, **REISE["luft"])

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), sharey=True)

    n_zert = baeume_pro_flug(lat)
    for ax, r, titel in [
        (axes[0], voll, f"so viel Wald, wie das Zertifikat verkauft — {n_zert:.0f} Bäume je Flug"),
        (axes[1], gross, f"so viel, wie es bräuchte — {n_zert*eq:.0f} Bäume je Flug"),
    ]:
        ax.plot(YEARS, r["pulse_dt"] * 1000, color=RED, lw=2.2, label="was die Emission bewirkt")
        ax.plot(YEARS, r["offset_dt"] * 1000, color=MID, lw=2.2, label="was der Wald bewirkt")
        ax.plot(YEARS, r["delta_t"] * 1000, color=DARK, lw=3.0, label="unter dem Strich")
        ax.axhline(0, color="black", lw=0.9, ls="--")
        ax.fill_between(YEARS, r["delta_t"] * 1000, 0, where=r["delta_t"] > 0,
                        color=RED, alpha=0.13)
        ax.fill_between(YEARS, r["delta_t"] * 1000, 0, where=r["delta_t"] <= 0,
                        color=MID, alpha=0.18)
        ax.set_title(titel, fontsize=13, color=DARK, pad=8)
        ax.set_xlabel("Jahr")
        ax.grid(True, alpha=0.22)

    axes[0].set_ylabel("Temperaturwirkung [mK]")
    axes[0].text(0.02, 0.03, "Verhältnisse wie im Text; Kurven für einen Puls von 1 GtCO₂",
                 transform=axes[0].transAxes, fontsize=9.5, color=SUB, style="italic")
    axes[0].legend(fontsize=10.5, loc="upper right")

    dt = gross["delta_t"] * 1000
    vz = YEARS[1:][np.sign(dt[1:]) != np.sign(dt[:-1])]
    if len(vz) >= 2:
        axes[1].annotate(f"treffen sich {vz[-2]:.0f}", xy=(vz[-2], 0),
                         xytext=(vz[-2] - 40, dt.min() * 1.5), fontsize=12, color=DARK,
                         arrowprops=dict(arrowstyle="->", color=DARK))
        axes[1].annotate(f"laufen ab {vz[-1]:.0f}\nwieder auseinander", xy=(vz[-1], 0),
                         xytext=(vz[-1] - 10, dt.max() * 0.55), fontsize=12, color=RED,
                         arrowprops=dict(arrowstyle="->", color=RED))
    plt.tight_layout()
    save(fig, "r1_treffen.png")


def reise_45(res45):
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4))
    ax = axes[0]
    for name, r in res45.items():
        ax.plot(YEARS, r["delta_t"] * 1000, lw=2.6, color=STATION_FARBE[name],
                label=STATION_NAME[name])
    ax.axhline(0, color="black", lw=0.9, ls="--")
    ax.set_xlabel("Jahr"); ax.set_ylabel("was unter dem Strich bleibt [mK]")
    ax.set_title("45 °N: Station für Station", fontsize=13, color=DARK, pad=8)
    ax.legend(fontsize=10.5); ax.grid(True, alpha=0.22)

    ax = axes[1]
    namen = list(res45.keys())
    basis = baeume_pro_flug(45)
    werte = [res45[n]["equivalence_ratio_2100"] * basis for n in namen]
    bars = ax.bar([STATION_NAME[n].replace(" ", "\n", 1) for n in namen], werte,
                  color=[STATION_FARBE[n] for n in namen], width=0.6)
    ax.axhline(basis, color="black", lw=1.4, ls="--")
    ax.text(3.45, basis + 2, "was das Zertifikat verkauft", ha="right",
            fontsize=11, color=SUB)
    ax.set_ylabel("Bäume für einen Flug")
    ax.set_title("Wie viele Bäume der Flug wirklich bräuchte", fontsize=13, color=DARK, pad=8)
    ax.grid(True, axis="y", alpha=0.25)
    for b, v in zip(bars, werte):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.0f}",
                ha="center", fontsize=13, fontweight="bold", color=TXT)
    ax.set_ylim(0, max(werte) * 1.22)
    plt.tight_layout()
    save(fig, "r2_reise_45N.png")


def orte(alle):
    """Bäume für einen Flug: was das Zertifikat verkauft, was es bräuchte."""
    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    lats = sorted(alle.keys())
    gebucht = [baeume_pro_flug(l) for l in lats]
    noetig = [alle[l]["luft"]["equivalence_ratio_2100"] * baeume_pro_flug(l) for l in lats]

    ax.plot(lats, gebucht, marker="o", ms=10, lw=2.8, color="#8C8C8C",
            label="was das Zertifikat verkauft")
    ax.plot(lats, noetig, marker="o", ms=10, lw=2.8, color=RED,
            label="was der Flug wirklich bräuchte")
    ax.fill_between(lats, gebucht, noetig, color=RED, alpha=0.10)
    for l, g, n in zip(lats, gebucht, noetig):
        ax.annotate(f"{n:.0f}", xy=(l, n), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=12, color=RED, fontweight="bold")
        ax.annotate(f"{g:.0f}", xy=(l, g), xytext=(0, -18), textcoords="offset points",
                    ha="center", fontsize=11.5, color="#6E6E6E")
    ax.set_yscale("log")
    ax.set_xlabel("Breitengrad [°N]")
    ax.set_ylabel("Bäume für einen Flug")
    ax.set_xticks(lats)
    ax.set_ylim(3, 900)
    ax.set_yticks([5, 10, 50, 100, 500])
    ax.set_yticklabels(["5", "10", "50", "100", "500"])
    ax.set_title("Derselbe Flug, anderer Pflanzort", fontsize=14, color=DARK, pad=10)
    ax.legend(fontsize=11, loc="upper left"); ax.grid(True, alpha=0.25, which="both")
    save(fig, "r3_orte.png")


def vergleich():
    """Wie sich die nötige Fläche zu realen Aufforstungsprogrammen verhält."""
    eintraege = [
        ("Bonn Challenge — Ziel 2030", 350, "welt"),
        ("Bonn Challenge — bisher zugesagt", 210, "welt"),
        ("60 °N: nötig für 1 GtCO₂", 111, "modell"),
        ("Great Green Wall — Ziel 2030", 100, "welt"),
        ("Fläche Deutschlands", 36, "massstab"),
        ("45 °N: nötig für 1 GtCO₂", 20, "modell"),
        ("Great Green Wall — bisher erreicht", 18, "welt"),
        ("weltweite Aufforstung, pro Jahr", 5, "welt"),
        ("45 °N: was das Zertifikat bucht", 2.7, "zertifikat"),
    ]
    farben = {"modell": RED, "zertifikat": "#8C8C8C", "welt": MID, "massstab": "#9DB4C0"}

    fig, ax = plt.subplots(figsize=(12.5, 6.0))
    y = np.arange(len(eintraege))[::-1]
    for (name, wert, art), yy in zip(eintraege, y):
        ax.barh(yy, wert, color=farben[art], height=0.62)
        ax.text(wert + 6, yy, f"{wert:g} Mha".replace(".", ","), va="center",
                fontsize=12, color=farben[art], fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([e[0] for e in eintraege], fontsize=12.5)
    ax.set_xlim(0, 420)
    ax.set_xlabel("Fläche [Millionen Hektar]")
    ax.grid(True, axis="x", alpha=0.25)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    for lbl, farbe in [("was das Modell verlangt", RED),
                       ("was Zertifikate buchen", "#8C8C8C"),
                       ("reale Programme", MID)]:
        ax.plot([], [], "s", color=farbe, ms=11, label=lbl)
    ax.legend(fontsize=11, loc="lower right", frameon=False)
    save(fig, "r4_vergleich.png")


if __name__ == "__main__":
    print("=== Story ===")
    einheit(); sonne(); zucker(); speicher(); tonne(); uhren(); zwei_uhren(); architektur()
    print("=== Ergebnisse (FaIR-Läufe) ===")
    alle = {lat: _laufe(lat) for lat in [0, 15, 30, 45, 60]}
    reise_45(alle[45])
    orte(alle)
    treffen(45)
    vergleich()
    print("=== fertig ===")
