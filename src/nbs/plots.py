"""Figures for the results section of the talk.

German labels: these go straight onto slides.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

from nbs.forcing import co2_flux_kg_per_yr  # noqa: E402
from nbs.metrics import quantile_band, t_star  # noqa: E402
from nbs.pipeline import SiteResult  # noqa: E402
from nbs.response import convolve_response, green_temperature  # noqa: E402
from nbs.species import get_species  # noqa: E402

C_CARBON = "#1b7837"
C_ALBEDO = "#d95f02"
C_NET = "#252525"
DPI = 300


def _save(fig, out_path: str) -> str:
    directory = os.path.dirname(out_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _title(result: SiteResult) -> str:
    sp = get_species(result.species_key)
    hemisphere = "S" if result.lat_deg < 0 else "N"
    return (
        f"{sp.name_de} ({sp.name_lat}), {abs(result.lat_deg):.0f}°{hemisphere}, "
        f"{result.scenario.upper()}"
    )


def plot_tree_inputs(result: SiteResult, out_path: str) -> str:
    """Slide E2: what goes into the forcing — stock, CO2 flux, canopy closure."""
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    y = result.years
    traj = result.trajectory

    axes[0].plot(y, traj.stock_kgC, color=C_CARBON)
    axes[0].set_ylabel("Vorrat m\n[kgC je Baum]")

    axes[1].plot(y, co2_flux_kg_per_yr(traj.net_uptake_kgC_yr), color=C_CARBON)
    axes[1].axhline(0.0, color="0.6", lw=0.8)
    axes[1].set_ylabel("$\\dot m_{CO_2}$\n[kg CO$_2$/a]")

    axes[2].plot(y, traj.closure, color=C_ALBEDO)
    axes[2].set_ylabel("Bedeckungsgrad f\n[-]")
    axes[2].set_ylim(0, 1.05)
    axes[2].set_xlabel("Jahr")

    axes[0].set_title(_title(result))
    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout()
    return _save(fig, out_path)


def plot_decomposition(result: SiteResult, out_path: str) -> str:
    """Slide E3: forcing above, temperature below, both split by channel.

    Two panels rather than one, not because the contrast between channels is
    sharper in the forcing than in the temperature — the two panels are in
    fact nearly identical, because the temperature Green's function's memory
    is short relative to the timescale on which the forcing varies. The real
    difference the second panel shows is timing: the net forcing crosses
    zero about four years before the net temperature does.
    """
    g = green_temperature(result.scenario)
    dt_carbon = convolve_response(g, result.phi_co2)
    dt_albedo = convolve_response(g, result.phi_albedo)

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    y = result.years

    axes[0].plot(y, result.phi_co2 * 1e15, color=C_CARBON, label="$\\varphi_{CO_2}$ (kühlt)")
    axes[0].plot(y, result.phi_albedo * 1e15, color=C_ALBEDO, label="$\\varphi_\\alpha$ (wärmt)")
    axes[0].plot(y, result.phi_total * 1e15, color=C_NET, lw=2, label="$\\varphi$ netto")
    axes[0].axhline(0.0, color="0.6", lw=0.8)
    axes[0].set_ylabel("Antrieb\n[10$^{-15}$ W/m² je Baum]")
    axes[0].legend(frameon=False, ncol=3)
    axes[0].set_title(_title(result))

    axes[1].plot(y, dt_carbon * 1e15, color=C_CARBON)
    axes[1].plot(y, dt_albedo * 1e15, color=C_ALBEDO)
    axes[1].plot(y, result.delta_t * 1e15, color=C_NET, lw=2)
    axes[1].axhline(0.0, color="0.6", lw=0.8)
    axes[1].set_ylabel("Temperatur\n[10$^{-15}$ K je Baum]")
    axes[1].set_xlabel("Jahr")

    ts = t_star(result.delta_t, y)
    if np.isfinite(ts):
        axes[1].axvline(ts, color=C_NET, ls=":", lw=1)
        axes[1].annotate(f"t* = {ts:.0f}", (ts, 0.0), textcoords="offset points",
                         xytext=(6, 10), fontsize=9)
    else:
        axes[1].annotate("kein t* im Horizont", (y[len(y) // 2], 0.0),
                         textcoords="offset points", xytext=(0, 10), fontsize=9)

    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout()
    return _save(fig, out_path)


def plot_disturbance_fan(result: SiteResult, ensemble: NDArray, out_path: str) -> str:
    """Slide E4: median, 5-95 percent band, deterministic run for contrast."""
    lo, med, hi = quantile_band(ensemble)
    y = result.years

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(y, lo * 1e15, hi * 1e15, color=C_NET, alpha=0.18,
                    label="5–95 % der Läufe")
    ax.plot(y, med * 1e15, color=C_NET, lw=2, label="Median mit Störung")
    ax.plot(y, result.delta_t * 1e15, color=C_CARBON, lw=1.5, ls="--",
            label="ohne Störungsereignisse")
    ax.axhline(0.0, color="0.6", lw=0.8)

    share_warming = float(np.mean(ensemble[:, -1] > 0.0))
    ax.set_title(f"{_title(result)}\nAnteil erwärmender Läufe {y[-1]}: {share_warming:.0%}")
    ax.set_xlabel("Jahr")
    ax.set_ylabel("$\\Delta T$ [10$^{-15}$ K je Baum]")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return _save(fig, out_path)
