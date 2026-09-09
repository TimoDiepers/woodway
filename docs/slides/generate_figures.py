"""Generate all slide figures."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from nbs.legacy.parameters import T_START, T_END
from nbs.legacy.carbon_module import compute_nee_at_level, compute_biomass_growth
from nbs.legacy.albedo_module import compute_albedo_forcing_timeseries
from nbs.legacy.et_module import compute_et_forcing_timeseries
from nbs.fair_module import run_fair_baseline, compute_pulse_warming
from nbs.legacy.credit_analysis import run_at_level, run_progressive_analysis

YEARS = np.arange(T_START, T_END)
OUT = os.path.join(os.path.dirname(__file__), "figures")
PALETTE = {
    "tropical": "#2ca02c",
    "temperate": "#ff7f0e",
    "boreal": "#1f77b4",
    "pulse": "#d62728",
    "neutral": "#666666",
}
LEVEL_COLORS = {
    0: "#999999", 1: "#a6cee3", 2: "#1f78b4",
    3: "#b2df8a", 4: "#33a02c", 5: "#fb9a99", 6: "#e31a1c",
}
LEVEL_LABELS = {
    0: "Kohlenstoffkonto",
    1: "+ Wachstum über die Zeit",
    2: "+ Standort",
    3: "+ Albedo",
    4: "+ Verdunstung",
    5: "+ Bodendynamik",
    6: "+ Störungen, volles Erdsystem",
}
LEVEL_SHORT = {
    0: "Konto", 1: "+Zeit", 2: "+Ort", 3: "+Albedo",
    4: "+Verdunst.", 5: "+Boden", 6: "+Erdsystem",
}

LATITUDES = [0, 15, 30, 45, 60]
SCENARIO = "ssp245"

plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.labelsize": 13,
    "axes.titlesize": 14,
    "legend.fontsize": 11,
})


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {name}")


print("=== Generating slide figures ===")

# ── Figure 1: Energy balance schematic ──────────────────────────────────────
print("Fig 1: Energy balance schematic")
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")

# Earth
earth = plt.Circle((5, 1.5), 1.2, color="#4a90d9", zorder=3)
ax.add_patch(earth)
ax.text(5, 1.5, "Erde", ha="center", va="center", fontsize=12, color="white", fontweight="bold")

# Sun arrow in
ax.annotate("", xy=(3.8, 2.1), xytext=(1.5, 4.0),
            arrowprops=dict(arrowstyle="-|>", color="#f5a623", lw=2.5))
ax.text(1.8, 4.4, "kurzwellig\nherein\n$(1-α)S_0/4$", ha="center", color="#f5a623", fontsize=11)

# IR out arrow
ax.annotate("", xy=(6.2, 2.1), xytext=(8.5, 4.0),
            arrowprops=dict(arrowstyle="-|>", color="#7b4ea0", lw=2.5))
ax.text(8.2, 4.4, "langwellig\nhinaus\nOLR", ha="center", color="#7b4ea0", fontsize=11)

# GHG layer
gg = mpatches.FancyBboxPatch((2.5, 3.0), 5, 0.7, boxstyle="round,pad=0.1",
                               linewidth=1.5, edgecolor="#e74c3c", facecolor="#fdecea")
ax.add_patch(gg)
ax.text(5, 3.35, "Treibhausgase halten Abstrahlung zurück  →  OLR sinkt  →  Erwärmung",
        ha="center", va="center", fontsize=10, color="#c0392b")

# Imbalance arrow
ax.annotate("", xy=(5, 2.8), xytext=(5, 3.0),
            arrowprops=dict(arrowstyle="-|>", color="#e74c3c", lw=2))

# Integral text
ax.text(5, 0.3, r"Erwärmung $\propto \int_0^T \left(\Delta F_{\mathrm{CO_2}} + \Delta F_\alpha + \Delta F_{\mathrm{ET}} + \ldots\right) dt$",
        ha="center", fontsize=12, color="#333333",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff9e6", edgecolor="#f5a623", lw=1.5))

ax.set_title("Erwärmung = angesammeltes Energieungleichgewicht", pad=12)
save(fig, "01_energiebilanz_erde.png")


# ── Figure 2: Static CO2 budget ───────────────────────────────────────────────
print("Fig 2: Static CO2 budget")
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

budget = 300  # GtCO2 remaining

# Left: budget bar
ax = axes[0]
ax.bar(["verbleibendes\nCO₂-Budget"], [budget], color="#e74c3c", width=0.4, label="Budget (GtCO₂)")
ax.set_ylabel("GtCO₂")
ax.set_title("Wie viel CO₂ muss weg?")
ax.text(0, budget + 5, f"{budget} GtCO₂", ha="center", fontsize=13, fontweight="bold", color="#e74c3c")
ax.set_ylim(0, 380)
ax.axhline(budget, color="#e74c3c", linestyle="--", alpha=0.4)

# Right: trees-to-area calculation
B_max = 200.0
co2_per_ha = B_max * (44/12)
trees_per_ha = 1000
co2_per_tree = co2_per_ha / trees_per_ha  # tCO2/tree
trees_needed = (budget * 1e9) / co2_per_tree  # trees
area_needed_mkm2 = trees_needed / trees_per_ha / 1e10

ax = axes[1]
labels = ["Afrika\n(30 Mio. km²)", "benötigte Fläche\n(naive Rechnung)", "alle Wälder heute\n(40 Mio. km²)"]
values = [30, area_needed_mkm2, 40]
colors = ["#bdc3c7", "#e74c3c", "#2ecc71"]
bars = ax.bar(labels, values, color=colors, width=0.5)
ax.set_ylabel("Mio. km²")
ax.set_title("Wie viele Bäume? — die naive Rechnung")
for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.3, f"{val:.0f} Mio. km²",
            ha="center", fontsize=11, fontweight="bold")
ax.set_ylim(0, 55)

plt.tight_layout()
save(fig, "02_static_co2_budget.png")


# ── Figure 3: Growth curves by latitude ─────────────────────────────────────
print("Fig 3: Growth curves")
t = np.arange(0, 125)
growth_configs = [
    (0,  200.0, 0.08, 2.5, PALETTE["tropical"], "0°N — tropisch"),
    (30, 120.0, 0.05, 2.0, PALETTE["temperate"], "30°N — gemäßigt"),
    (60, 100.0, 0.03, 2.0, PALETTE["boreal"], "60°N — boreal"),
]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for lat_val, Bmax, k, p, color, label in growth_configs:
    biomass = compute_biomass_growth(Bmax, k, p, t)
    dB = np.diff(biomass, prepend=0.0) * (44/12)
    axes[0].plot(YEARS, biomass, color=color, linewidth=2.5, label=label)
    axes[1].plot(YEARS, dB, color=color, linewidth=2.5, label=label)

axes[0].set_xlabel("Jahr"); axes[0].set_ylabel("Biomasse (tC/ha)")
axes[0].set_title("Biomasseaufbau nach Breitengrad")
axes[0].legend(); axes[0].grid(True, alpha=0.25)

axes[1].set_xlabel("Jahr"); axes[1].set_ylabel("jährliche CO₂-Aufnahme (tCO₂/ha/a)")
axes[1].set_title("jährliche Aufnahmerate")
axes[1].axhline(0, color="black", linewidth=0.5)
axes[1].legend(); axes[1].grid(True, alpha=0.25)

plt.tight_layout()
save(fig, "03_growth_curves.png")


# ── Figure 4: Pulse warming + warming debt concept ──────────────────────────
print("Fig 4: Pulse warming")
pulse_dt = compute_pulse_warming(pulse_gtco2=1.0, scenario=SCENARIO)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(YEARS, pulse_dt * 1000, color=PALETTE["pulse"], linewidth=2.5, label="Erwärmung durch 1 GtCO₂-Puls")
ax.fill_between(YEARS, pulse_dt * 1000, 0, where=pulse_dt > 0, alpha=0.18, color=PALETTE["pulse"])
ax.axhline(0, color="black", linewidth=0.8, linestyle="--")

# Annotate warming debt
mid_idx = 40
ax.annotate("Erwärmungsschuld:\nintegrierte Übertemperatur\n(K·a)",
            xy=(YEARS[mid_idx], pulse_dt[mid_idx] * 1000 * 0.5),
            xytext=(2065, pulse_dt[mid_idx] * 1000 * 0.4 + 0.8),
            fontsize=11, color=PALETTE["pulse"],
            arrowprops=dict(arrowstyle="->", color=PALETTE["pulse"]))

ax.set_xlabel("Jahr"); ax.set_ylabel("ΔT (mK)")
ax.set_title("Temperaturantwort auf einen Emissionspuls von 1 GtCO₂ (2025)")
ax.legend(); ax.grid(True, alpha=0.25)
save(fig, "04_pulse_warming.png")


# ── Figure 5: L0 vs L1 — flat vs growth curve ───────────────────────────────
print("Fig 5: L0 vs L1")
r0 = run_at_level(0, lat=45, scenario=SCENARIO)
r1 = run_at_level(1, lat=45, scenario=SCENARIO)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# NEE comparison
ax = axes[0]
ax.plot(YEARS, r0["nee"], color=LEVEL_COLORS[0], linewidth=2.5, label="L0: konstant (naiv)")
ax.plot(YEARS, r1["nee"], color=LEVEL_COLORS[1], linewidth=2.5, label="L1: Wachstumskurve")
ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
ax.set_xlabel("Jahr"); ax.set_ylabel("NEE (GtCO₂/yr)")
ax.set_title("CO₂-Aufnahme: konstant vs. Wachstumskurve")
ax.legend(); ax.grid(True, alpha=0.25)

# ΔT comparison
ax = axes[1]
ax.fill_between(YEARS, r1["delta_t"] * 1000, 0, where=r1["delta_t"] > 0,
                alpha=0.2, color=LEVEL_COLORS[1], label="Erwärmungsschuld (L1)")
ax.plot(YEARS, r0["delta_t"] * 1000, color=LEVEL_COLORS[0], linewidth=2.5,
        linestyle="--", label="L0: konstant (naiv)", alpha=0.8)
ax.plot(YEARS, r1["delta_t"] * 1000, color=LEVEL_COLORS[1], linewidth=2.5,
        label="L1: Wachstumskurve")
ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
t_star = r1["t_star"]
if t_star != np.inf:
    ax.axvline(t_star, color=LEVEL_COLORS[1], linewidth=1.5, linestyle=":",
               label=f"Umschlagpunkt t* = {t_star:.0f}")
ax.set_xlabel("Jahr"); ax.set_ylabel("ΔT (mK)")
ax.set_title("Nettotemperatur: naive Annahme vs. Realität")
ax.legend(fontsize=10); ax.grid(True, alpha=0.25)

plt.tight_layout()
save(fig, "05_level0_vs_level1.png")


# ── Figure 6: L2 — location matters ─────────────────────────────────────────
print("Fig 6: Location matters")
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

colors_lat = [PALETTE["tropical"], PALETTE["temperate"], "#9467bd", PALETTE["boreal"]]
lats_show = [0, 30, 45, 60]

for lat_val, color in zip(lats_show, colors_lat):
    r = run_at_level(2, lat=lat_val, scenario=SCENARIO)
    eq_str = f"{r['equivalence_ratio_2100']:.1f}x" if not np.isinf(r["equivalence_ratio_2100"]) else "∞"
    label = f"{lat_val}°N (EQ={eq_str})"
    axes[0].plot(YEARS, r["nee"], color=color, linewidth=2, label=label)
    axes[1].plot(YEARS, r["delta_t"] * 1000, color=color, linewidth=2, label=label)

axes[0].axhline(0, color="black", linewidth=0.5, linestyle="--")
axes[0].set_xlabel("Jahr"); axes[0].set_ylabel("NEE (GtCO₂/yr)")
axes[0].set_title("L2: CO₂-Aufnahme nach Breitengrad")
axes[0].legend(fontsize=10); axes[0].grid(True, alpha=0.25)

axes[1].axhline(0, color="black", linewidth=0.8, linestyle="--")
axes[1].set_xlabel("Jahr"); axes[1].set_ylabel("ΔT (mK)")
axes[1].set_title("L2: Temperaturwirkung nach Breitengrad")
axes[1].legend(fontsize=10); axes[1].grid(True, alpha=0.25)

plt.tight_layout()
save(fig, "06_location_matters.png")


# ── Figure 7: Albedo forcing ──────────────────────────────────────────────────
print("Fig 7: Albedo")
interventions_lat = [
    ("tropical_reforestation", 0, PALETTE["tropical"], "0°N — tropisch"),
    ("tropical_reforestation", 15, "#5aae61", "15°N — subtropisch"),
    ("boreal_afforestation", 45, PALETTE["temperate"], "45°N — gemäßigt"),
    ("boreal_afforestation", 60, PALETTE["boreal"], "60°N — boreal"),
]

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

steady_vals = []
lat_vals = []
for intv, lat_val, color, label in interventions_lat:
    alpha_ts = compute_albedo_forcing_timeseries(intv, lat_val)
    axes[0].plot(YEARS, alpha_ts, color=color, linewidth=2.5, label=label)
    steady_vals.append(alpha_ts[-1])
    lat_vals.append(lat_val)

axes[0].axhline(0, color="black", linewidth=0.8, linestyle="--")
axes[0].fill_between([T_START, T_END], 0, 2, alpha=0.06, color="red", label="Erwärmung")
axes[0].fill_between([T_START, T_END], -0.5, 0, alpha=0.06, color="blue", label="Kühlung")
axes[0].set_xlabel("Jahr"); axes[0].set_ylabel("ΔF_α (W/m²)")
axes[0].set_title("Albedo-Antrieb über die Zeit, nach Breitengrad")
axes[0].legend(fontsize=10); axes[0].grid(True, alpha=0.25)

bar_colors = [PALETTE["tropical"], "#5aae61", PALETTE["temperate"], PALETTE["boreal"]]
bars = axes[1].bar([f"{l}°N" for l in lat_vals], steady_vals, color=bar_colors, width=0.5)
axes[1].axhline(0, color="black", linewidth=0.8, linestyle="--")
axes[1].set_xlabel("Breitengrad"); axes[1].set_ylabel("stationärer ΔF_α (W/m²)")
axes[1].set_title("Albedo-Antrieb: Vorzeichenwechsel in hohen Breiten")
for bar, val in zip(bars, steady_vals):
    y = val + 0.03 if val >= 0 else val - 0.08
    axes[1].text(bar.get_x() + bar.get_width()/2, y, f"{val:+.2f}", ha="center", fontsize=11)
axes[1].grid(True, alpha=0.25, axis="y")

plt.tight_layout()
save(fig, "07_albedo_forcing.png")


# ── Figure 8: Albedo trap — boreal credits can warm ─────────────────────────
print("Fig 8: Albedo trap")
fig, ax = plt.subplots(figsize=(11, 5.5))

lats_albedo = [0, 30, 45, 60]
colors_a = [PALETTE["tropical"], PALETTE["temperate"], "#9467bd", PALETTE["boreal"]]

for lat_val, color in zip(lats_albedo, colors_a):
    r = run_at_level(3, lat=lat_val, scenario=SCENARIO)
    eq_str = f"{r['equivalence_ratio_2100']:.1f}x" if not np.isinf(r["equivalence_ratio_2100"]) else "∞ (netto Erwärmung)"
    ax.plot(YEARS, r["delta_t"] * 1000, color=color, linewidth=2.5,
            label=f"{lat_val}°N — ÄV: {eq_str}")

ax.axhline(0, color="black", linewidth=1.0, linestyle="--")
ax.fill_between([T_START, T_END], 0, 3, alpha=0.06, color="red")
ax.fill_between([T_START, T_END], -3, 0, alpha=0.06, color="blue")
ax.text(2148, 1.5, "netto\nErwärmung", ha="right", color="#c0392b", fontsize=11)
ax.text(2148, -1.5, "netto\nKühlung", ha="right", color="#2471a3", fontsize=11)
ax.set_xlabel("Jahr"); ax.set_ylabel("ΔT (mK)")
ax.set_title("L3 (CO₂ + Albedo): Aufforstung in hohen Breiten kann netto erwärmen")
ax.legend(fontsize=10); ax.grid(True, alpha=0.25)
save(fig, "08_albedo_trap.png")


# ── Figure 9: ET forcing ─────────────────────────────────────────────────────
print("Fig 9: ET + combined forcing")
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

for intv, lat_val, color, label in interventions_lat:
    et_ts = compute_et_forcing_timeseries(intv, lat_val)
    al_ts = compute_albedo_forcing_timeseries(intv, lat_val)
    axes[0].plot(YEARS, et_ts, color=color, linewidth=2.5, label=label)
    axes[1].plot(YEARS, al_ts + et_ts, color=color, linewidth=2.5, label=label)

axes[0].axhline(0, color="black", linewidth=0.8, linestyle="--")
axes[0].set_xlabel("Jahr"); axes[0].set_ylabel("ΔF_ET (W/m²)")
axes[0].set_title("Kühlung durch Verdunstung nach Breitengrad")
axes[0].legend(fontsize=10); axes[0].grid(True, alpha=0.25)

axes[1].axhline(0, color="black", linewidth=0.8, linestyle="--")
axes[1].fill_between([T_START, T_END], 0, 1.5, alpha=0.06, color="red")
axes[1].fill_between([T_START, T_END], -2, 0, alpha=0.06, color="blue")
axes[1].set_xlabel("Jahr"); axes[1].set_ylabel("ΔF_α + ΔF_ET (W/m²)")
axes[1].set_title("Summe der Nicht-CO₂-Terme (Albedo + Verdunstung)")
axes[1].legend(fontsize=10); axes[1].grid(True, alpha=0.25)

plt.tight_layout()
save(fig, "09_et_and_combined_forcing.png")


# ── Figure 10: Progressive complexity — all levels at 45°N ─────────────────
print("Fig 10: Progressive complexity at 45°N")
print("  Running all levels (this may take a minute)...")
prog_45 = run_progressive_analysis(lat=45, scenario=SCENARIO)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

ax = axes[0]
for level in range(7):
    d = prog_45[level]
    lw = 2.5 if level in (0, 6) else 1.8
    alpha = 1.0 if level in (0, 6) else 0.75
    eq = d["equivalence_ratio_2100"]
    eq_str = f"{eq:.1f}x" if not np.isinf(eq) else "∞"
    ts = d["t_star"]
    ts_str = f"{ts:.0f}" if ts != np.inf else "∞"
    ax.plot(YEARS, d["delta_t"] * 1000, color=LEVEL_COLORS[level],
            linewidth=lw, alpha=alpha,
            label=f"{LEVEL_LABELS[level]}  |  ÄV={eq_str}  t*={ts_str}")

ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
ax.set_xlabel("Jahr"); ax.set_ylabel("ΔT (mK)")
ax.set_title("45°N: Nettowirkung, Systemgrenze für Systemgrenze")
ax.legend(fontsize=8, loc="lower left")
ax.grid(True, alpha=0.25)

# Equivalence ratio bar chart
ax = axes[1]
levels = list(range(7))
eq_vals = []
for level in levels:
    eq = prog_45[level]["equivalence_ratio_2100"]
    eq_vals.append(min(eq, 12) if not np.isinf(eq) else 12)

bar_colors = [LEVEL_COLORS[l] for l in levels]
bars = ax.bar([LEVEL_SHORT[l] for l in levels], eq_vals, color=bar_colors, width=0.6)
ax.axhline(1, color="black", linewidth=1.5, linestyle="--", label="naive 1:1-Annahme")
ax.set_ylabel("Äquivalenzverhältnis (Gutschriften je tCO₂)")
ax.set_title("Benötigte Gutschriften je tCO₂ bei 45°N (bis 2100)")
ax.legend(fontsize=11)
ax.grid(True, alpha=0.25, axis="y")

for bar, val, level in zip(bars, eq_vals, levels):
    orig = prog_45[level]["equivalence_ratio_2100"]
    label = f"{orig:.1f}x" if not np.isinf(orig) else "∞"
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.1, label, ha="center", fontsize=10)

plt.tight_layout()
save(fig, "10_progressive_complexity_45N.png")


# ── Figure 11: Equivalence ratio by latitude (multi-level) ──────────────────
print("Fig 11: Equivalence by latitude")
levels_show = [1, 3, 4, 6]

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

ax = axes[0]
for level in levels_show:
    lats_valid, eq_vals = [], []
    for lat_val in LATITUDES:
        r = run_at_level(level, lat_val, scenario=SCENARIO)
        if not np.isinf(r["equivalence_ratio_2100"]):
            lats_valid.append(lat_val)
            eq_vals.append(r["equivalence_ratio_2100"])
    ax.plot(lats_valid, eq_vals, marker="o", linewidth=2.5, markersize=8,
            color=LEVEL_COLORS[level], label=LEVEL_LABELS[level])

ax.axhline(1, color="black", linewidth=1.5, linestyle="--", label="naive 1:1-Annahme")
ax.set_xlabel("Breitengrad (°N)"); ax.set_ylabel("Äquivalenzverhältnis (Gutschriften je tCO₂)")
ax.set_title("Benötigte Gutschriften je tCO₂ nach Breitengrad")
ax.legend(fontsize=9); ax.grid(True, alpha=0.25)

ax = axes[1]
for level in levels_show:
    lats_valid, t_stars = [], []
    for lat_val in LATITUDES:
        r = run_at_level(level, lat_val, scenario=SCENARIO)
        if r["t_star"] != np.inf:
            lats_valid.append(lat_val)
            t_stars.append(r["t_star"])
    ax.plot(lats_valid, t_stars, marker="o", linewidth=2.5, markersize=8,
            color=LEVEL_COLORS[level], label=LEVEL_LABELS[level])

ax.set_xlabel("Breitengrad (°N)"); ax.set_ylabel("Umschlagjahr t*")
ax.set_title("Ab wann kühlt die Aufforstung?")
ax.legend(fontsize=9); ax.grid(True, alpha=0.25)

plt.tight_layout()
save(fig, "11_equivalence_by_latitude.png")


# ── Figure 12: SSP scenario sensitivity ─────────────────────────────────────
print("Fig 12: SSP sensitivity")
ssp_colors = {"ssp126": "#27ae60", "ssp245": "#2980b9", "ssp370": "#c0392b"}
ssp_labels = {"ssp126": "SSP1-2.6 (starker Klimaschutz)", "ssp245": "SSP2-4.5 (mittleres Szenario)", "ssp370": "SSP3-7.0 (hohe Emissionen)"}

fig, ax = plt.subplots(figsize=(10, 5.5))

for scenario, color in ssp_colors.items():
    lats_valid, eq_vals = [], []
    for lat_val in LATITUDES:
        r = run_at_level(6, lat_val, scenario=scenario)
        if not np.isinf(r["equivalence_ratio_2100"]):
            lats_valid.append(lat_val)
            eq_vals.append(r["equivalence_ratio_2100"])
    ax.plot(lats_valid, eq_vals, marker="o", linewidth=2.5, markersize=9,
            color=color, label=ssp_labels[scenario])

ax.axhline(1, color="black", linewidth=1.5, linestyle="--", label="naive 1:1-Annahme")
ax.set_xlabel("Breitengrad (°N)"); ax.set_ylabel("Äquivalenzverhältnis (Stufe L6, bis 2100)")
ax.set_title("Äquivalenzverhältnis im vollen Modell für verschiedene Emissionsszenarien")
ax.legend(fontsize=10); ax.grid(True, alpha=0.25)
save(fig, "12_ssp_sensitivity.png")


print("\n=== All figures saved to", OUT, "===")
