import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

YEARS = np.arange(2025, 2150)

LEVEL_COLORS = {0: "#999999", 1: "#a6cee3", 2: "#1f78b4", 3: "#b2df8a", 4: "#33a02c", 5: "#fb9a99", 6: "#e31a1c"}
LEVEL_LABELS = {
    0: "L0: Static budget (naive)",
    1: "L1: CO₂ forcing + growth curve",
    2: "L2: + Location-dependent growth",
    3: "L3: + Albedo (ΔF_α)",
    4: "L4: + Evapotranspiration (ΔF_ET)",
    5: "L5: + Soil dynamics (SOC + Q10)",
    6: "L6: Full Earth system (FaIR)",
}

LATITUDES = [0, 15, 30, 45, 60]


def _ensure_dir(output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)


def plot_progressive_delta_t(progressive_results: dict[int, dict], output_dir: str, lat: int = 45) -> str:
    _ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    for level in sorted(progressive_results.keys()):
        data = progressive_results[level]
        delta_t_mk = data["delta_t"] * 1000
        lw = 2 if level in (0, 6) else 1.2
        alpha = 1.0 if level in (0, 6) else 0.7
        ax.plot(YEARS, delta_t_mk, color=LEVEL_COLORS[level], label=LEVEL_LABELS[level],
                linewidth=lw, alpha=alpha)

    ax.axhline(0, color="black", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Year")
    ax.set_ylabel("ΔT (mK)")
    ax.set_title(f"Progressive complexity – Temperature impact at {lat}°N")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "fig1_progressive_delta_t.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_equivalence_by_latitude(lat_results: dict[tuple, dict], output_dir: str) -> str:
    _ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    for level in [1, 3, 6]:
        lats = []
        ratios = []
        for lat in LATITUDES:
            key = (level, lat, "ssp245")
            if key in lat_results:
                val = lat_results[key]["equivalence_ratio_2100"]
                if not np.isinf(val):
                    lats.append(lat)
                    ratios.append(val)
        ax.plot(lats, ratios, marker="o", color=LEVEL_COLORS[level], label=LEVEL_LABELS[level])

    ax.axhline(1, color="black", linestyle="--", linewidth=0.8, label="Naive assumption")
    ax.set_xlabel("Latitude (°N)")
    ax.set_ylabel("Equivalence ratio (2100)")
    ax.set_title("Credit equivalence ratio by latitude")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "fig2_equivalence_by_latitude.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_breakeven_by_level(lat_results: dict[tuple, dict], output_dir: str) -> str:
    _ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    for level in [1, 3, 6]:
        lats = []
        t_stars = []
        for lat in LATITUDES:
            key = (level, lat, "ssp245")
            if key in lat_results:
                val = lat_results[key]["t_star"]
                if not np.isinf(val):
                    lats.append(lat)
                    t_stars.append(val)
        ax.plot(lats, t_stars, marker="o", color=LEVEL_COLORS[level], label=LEVEL_LABELS[level])

    ax.set_xlabel("Latitude (°N)")
    ax.set_ylabel("Break-even year (t*)")
    ax.set_title("Break-even time by latitude and complexity level")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "fig3_breakeven_by_level.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_warming_debt(lat_results: dict[tuple, dict], output_dir: str) -> str:
    _ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    levels = [1, 3, 6]
    n_levels = len(levels)
    bar_width = 0.25
    x = np.arange(len(LATITUDES))

    for i, level in enumerate(levels):
        debts = []
        for lat in LATITUDES:
            key = (level, lat, "ssp245")
            if key in lat_results:
                debts.append(lat_results[key]["warming_debt"])
            else:
                debts.append(0)
        offset = (i - (n_levels - 1) / 2) * bar_width
        ax.bar(x + offset, debts, bar_width, color=LEVEL_COLORS[level], label=LEVEL_LABELS[level])

    ax.set_xlabel("Latitude (°N)")
    ax.set_ylabel("Warming debt (K·yr)")
    ax.set_title("Warming debt by latitude and complexity level")
    ax.set_xticks(x)
    ax.set_xticklabels([str(lat) for lat in LATITUDES])
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    path = os.path.join(output_dir, "fig4_warming_debt.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_credit_depreciation(ssp_results: dict[tuple, dict], output_dir: str) -> str:
    _ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    ssp_colors = {"ssp126": "#4daf4a", "ssp245": "#377eb8", "ssp370": "#e41a1c"}

    for scenario, color in ssp_colors.items():
        lats = []
        ratios = []
        for lat in LATITUDES:
            key = (6, lat, scenario)
            if key in ssp_results:
                val = ssp_results[key]["equivalence_ratio_2100"]
                if not np.isinf(val):
                    lats.append(lat)
                    ratios.append(val)
        ax.plot(lats, ratios, marker="o", color=color, label=scenario.upper())

    ax.set_xlabel("Latitude (°N)")
    ax.set_ylabel("Equivalence ratio (2100)")
    ax.set_title("Credit depreciation under different SSP scenarios (Level 6)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "fig5_credit_depreciation.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_credit_sobol(sobol_results: dict, output_dir: str) -> str:
    _ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    param_names = sobol_results["param_names"]
    s1 = sobol_results["S1"]
    st = sobol_results["ST"]
    s1_conf = sobol_results["S1_conf"]
    st_conf = sobol_results["ST_conf"]

    x = np.arange(len(param_names))
    bar_width = 0.35

    ax.bar(x - bar_width / 2, s1, bar_width, yerr=s1_conf, color="#1f78b4",
           label="First-order (S1)", capsize=3)
    ax.bar(x + bar_width / 2, st, bar_width, yerr=st_conf, color="#e31a1c",
           label="Total-order (ST)", capsize=3)

    ax.set_xlabel("Parameter")
    ax.set_ylabel("Sensitivity index")
    ax.set_title("Sobol sensitivity analysis – Credit equivalence")
    ax.set_xticks(x)
    ax.set_xticklabels(param_names, rotation=45, ha="right")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    path = os.path.join(output_dir, "fig6_credit_sobol.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path
