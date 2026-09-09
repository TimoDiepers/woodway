"""Figure generation for the NBS Climate Framework."""

from __future__ import annotations

import os
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from nbs.legacy.parameters import INTERVENTIONS, LATITUDES, SCENARIOS, T_END, T_START

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------

COLORS: dict[str, str] = {
    "tropical_reforestation": "#2ca02c",
    "boreal_afforestation": "#1f77b4",
    "avoided_deforestation": "#ff7f0e",
    "beccs": "#d62728",
}

LABELS: dict[str, str] = {
    "tropical_reforestation": "Tropical Reforestation",
    "boreal_afforestation": "Boreal Afforestation",
    "avoided_deforestation": "Avoided Deforestation",
    "beccs": "BECCS",
}

# Representative latitudes for Fig 1
_FIG1_LATS: dict[str, int] = {
    "tropical_reforestation": 0,
    "boreal_afforestation": 60,
    "avoided_deforestation": 0,
    "beccs": 30,
}


def _years_array() -> np.ndarray:
    """Return the time axis matching the 125-element result arrays."""
    return np.linspace(T_START, T_END, 125)


# ---------------------------------------------------------------------------
# Figure 1 – ΔT(t) curves
# ---------------------------------------------------------------------------


def plot_delta_t_curves(
    results: dict[tuple, dict],
    output_dir: str,
    scenario: str = "ssp245",
) -> str:
    """Fig 1: ΔT(t) curves for all 4 interventions at representative latitudes."""
    years = _years_array()
    fig, ax = plt.subplots(figsize=(10, 6))

    for intervention in INTERVENTIONS:
        lat = _FIG1_LATS[intervention]
        key = (intervention, lat, scenario)
        delta_t_mK = results[key]["delta_t"] * 1000
        ax.plot(
            years,
            delta_t_mK,
            color=COLORS[intervention],
            label=f"{LABELS[intervention]} ({lat}°N)",
        )

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Year")
    ax.set_ylabel("ΔT (mK)")
    ax.set_title("Temperature response of forest-based climate interventions")
    ax.legend()
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "fig1_delta_t_curves.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Figure 2 – Break-even map
# ---------------------------------------------------------------------------


def plot_breakeven_map(
    results: dict[tuple, dict],
    output_dir: str,
    scenario: str = "ssp245",
) -> str:
    """Fig 2: Scatter plot of t* by latitude per intervention."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for intervention in INTERVENTIONS:
        lats, t_stars = [], []
        for lat in LATITUDES:
            key = (intervention, lat, scenario)
            t_star = results[key]["t_star"]
            if not np.isinf(t_star):
                lats.append(lat)
                t_stars.append(t_star)
        ax.scatter(
            lats,
            t_stars,
            color=COLORS[intervention],
            label=LABELS[intervention],
            s=80,
            zorder=3,
        )

    ax.set_xlabel("Latitude (°N)")
    ax.set_ylabel("Break-even year (t*)")
    ax.set_title("Break-even time by latitude")
    ax.legend()
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "fig2_breakeven_map.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Figure 3 – Ranking heatmap
# ---------------------------------------------------------------------------


def plot_ranking_heatmap(
    results: dict[tuple, dict],
    output_dir: str,
) -> str:
    """Fig 3: Heatmaps at 2050, 2100, 2150 showing ΔT by intervention × latitude."""
    years = _years_array()
    target_years = [2050, 2100, 2150]
    scenario = "ssp245"

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    for ax, target_year in zip(axes, target_years):
        idx = int(np.argmin(np.abs(years - target_year)))
        data = np.zeros((len(INTERVENTIONS), len(LATITUDES)))
        for i, intervention in enumerate(INTERVENTIONS):
            for j, lat in enumerate(LATITUDES):
                key = (intervention, lat, scenario)
                data[i, j] = results[key]["delta_t"][idx] * 1000  # mK

        vmax = max(abs(data.min()), abs(data.max())) or 1.0
        im = ax.imshow(
            data,
            cmap="RdBu_r",
            vmin=-vmax,
            vmax=vmax,
            aspect="auto",
        )
        ax.set_xticks(range(len(LATITUDES)))
        ax.set_xticklabels([f"{l}°N" for l in LATITUDES])
        ax.set_yticks(range(len(INTERVENTIONS)))
        ax.set_yticklabels([LABELS[iv] for iv in INTERVENTIONS])
        ax.set_title(f"ΔT in {target_year} (mK)")
        fig.colorbar(im, ax=ax, shrink=0.8)

    fig.suptitle("Ranking of interventions (SSP2-4.5)", fontsize=14)
    fig.tight_layout()

    path = os.path.join(output_dir, "fig3_ranking_heatmap.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Figure 4 – SSP sensitivity
# ---------------------------------------------------------------------------


def plot_ssp_sensitivity(
    results: dict[tuple, dict],
    output_dir: str,
) -> str:
    """Fig 4: Grouped bar chart of best t* by intervention, one bar per SSP."""
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(INTERVENTIONS))
    width = 0.25
    ssp_colors = {"ssp126": "#4daf4a", "ssp245": "#377eb8", "ssp370": "#e41a1c"}

    for k, scenario in enumerate(SCENARIOS):
        best_t_stars = []
        for intervention in INTERVENTIONS:
            t_star_values = []
            for lat in LATITUDES:
                key = (intervention, lat, scenario)
                t_star_values.append(results[key]["t_star"])
            best = min(t_star_values)
            best_t_stars.append(T_END if np.isinf(best) else best)
        ax.bar(
            x + k * width,
            best_t_stars,
            width,
            label=scenario.upper().replace("SSP", "SSP"),
            color=ssp_colors[scenario],
        )

    ax.set_xticks(x + width)
    ax.set_xticklabels([LABELS[iv] for iv in INTERVENTIONS], rotation=15, ha="right")
    ax.set_ylabel("Best break-even year (t*)")
    ax.set_title("SSP sensitivity of break-even time")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    path = os.path.join(output_dir, "fig4_ssp_sensitivity.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Figure 5 – Sobol indices
# ---------------------------------------------------------------------------


def plot_sobol_indices(
    sobol_results: dict[str, Any],
    output_dir: str,
) -> str:
    """Fig 5: Bar chart with first-order and total-order Sobol indices."""
    s1 = sobol_results["S1"]
    st = sobol_results["ST"]
    s1_conf = sobol_results["S1_conf"]
    st_conf = sobol_results["ST_conf"]
    param_names = sobol_results["param_names"]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(param_names))
    width = 0.35

    ax.bar(
        x - width / 2,
        s1,
        width,
        yerr=s1_conf,
        label="First-order (S1)",
        color="#1f77b4",
        capsize=3,
    )
    ax.bar(
        x + width / 2,
        st,
        width,
        yerr=st_conf,
        label="Total-order (ST)",
        color="#ff7f0e",
        capsize=3,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(param_names, rotation=30, ha="right")
    ax.set_ylabel("Sobol index")
    ax.set_title("Sobol sensitivity indices")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    path = os.path.join(output_dir, "fig5_sobol_indices.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path
