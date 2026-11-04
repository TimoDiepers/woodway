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

from nbs.config import ModelConfig  # noqa: E402
from nbs.constants import M_CO2_PER_C, YEARS, SZENARIO  # noqa: E402
from nbs.forcing import co2_flux_kg_per_yr  # noqa: E402
from nbs.metrics import quantile_band, t_star  # noqa: E402
from nbs.pipeline import SiteResult  # noqa: E402
from nbs.response import convolve_response, green_temperature  # noqa: E402
from nbs.species import get_species  # noqa: E402

C_COHORT = ("#08519c", "#3182bd", "#e6550d", "#a63603")
"""One colour per planting cohort, cool (early) to warm (late)."""

C_CARBON = "#067a3c"  # deck.css --s-phic (phi_CO2)
C_ALBEDO = "#706a19"  # deck.css --s-phia (Delta phi_alpha)
C_TEMP = "#902b3c"  # deck.css --s-dt (Delta T)
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

    Two panels rather than one, kept deliberately even though the two curve
    shapes are in fact nearly identical — the temperature Green's function's
    memory is short relative to the timescale on which the forcing varies,
    so ΔT ≈ φ · equilibrium sensitivity. Collapsing to one panel would save
    space but would throw away the one thing this figure can show that a
    single panel cannot: forcing and temperature are two independently
    computed chains (φ integrates the two physical channels directly; ΔT is
    their convolution with the temperature Green's function) that land on
    the same story — itself a consistency check worth showing on the core
    result slide.

    The real difference between the panels is timing, and at this line
    width it is otherwise invisible: the net forcing settles into permanent
    cooling a few years before the net temperature does (thermal inertia).
    Both zero-crossings (``t*`` for φ and for ΔT, using the same "last sign
    change" definition as ``nbs.metrics.t_star``) are marked explicitly and
    the lag between them is annotated, so the delay is visible instead of
    lost in the line.
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

    ts_phi = t_star(result.phi_total, y)
    ts_dt = t_star(result.delta_t, y)

    if np.isfinite(ts_phi):
        axes[0].axvline(ts_phi, color=C_NET, ls=":", lw=1)
        axes[0].annotate(f"t*$_\\varphi$ = {ts_phi:.0f}", (ts_phi, 0.0),
                         textcoords="offset points", xytext=(6, 10), fontsize=9)
    if np.isfinite(ts_dt):
        axes[1].axvline(ts_dt, color=C_NET, ls=":", lw=1)
        axes[1].annotate(f"t*$_{{\\Delta T}}$ = {ts_dt:.0f}", (ts_dt, 0.0),
                         textcoords="offset points", xytext=(6, 10), fontsize=9)
    if not (np.isfinite(ts_phi) and np.isfinite(ts_dt)):
        axes[1].annotate("kein t* im Horizont", (y[len(y) // 2], 0.0),
                         textcoords="offset points", xytext=(0, 10), fontsize=9)
    else:
        lag = ts_dt - ts_phi
        fig.text(0.5, 0.965, f"thermische Trägheit: φ wird {lag:.0f} Jahre vor ΔT dauerhaft negativ",
                  ha="center", fontsize=10, style="italic")

    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
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


def plot_planting_time(
    out_path: str,
    *,
    species_key: str = "enf_boreal",
    lat_deg: float = 60.0,
    scenario: str = SZENARIO,
    age_yr: int | None = None,
    config: ModelConfig | None = None,
) -> str:
    """Folie: the same tree planted in four different years.

    Three panels, because "planting later is worse" hides two different
    mechanisms that a single panel would blur together:

    left
        The disturbance hazard p(t) = p0 exp(gamma T_background(t)) and each
        cohort's own window on it. This is the *cause*: nothing about the
        species changes, only the climate it has to survive.
    middle
        Stock over calendar time, solid with the hazard on and dotted with it
        off. The gap between the two lines of one colour is the risk cost;
        the shift between colours is the calendar cost.
    right
        The two costs as numbers: the probability of at least one disturbance
        within ``age_yr`` years of planting, and the break-even year t* the
        cohort reaches. Bars for the first, dots on the twin axis for the
        second.
    """
    from nbs.planting_time import (  # local import: keeps plots importable without FaIR
        DEFAULT_AGE_YR,
        PLANT_YEARS,
        cohort,
        cohort_table,
        hazard_curve,
    )

    age = DEFAULT_AGE_YR if age_yr is None else age_yr
    base = config or ModelConfig()
    undisturbed = ModelConfig(**{**base.__dict__, "disturbance": "off"})
    sp = get_species(species_key)
    table = cohort_table(species_key, lat_deg, scenario, PLANT_YEARS, age, base)
    hazard = hazard_curve(species_key, scenario)

    fig, (ax_p, ax_m, ax_b) = plt.subplots(1, 3, figsize=(16.5, 5.0))

    # -- left: the hazard, and who lives through which stretch of it ---------
    ax_p.plot(YEARS, hazard * 100.0, color=C_NET, linewidth=1.8)
    for i, py in enumerate(PLANT_YEARS):
        colour = C_COHORT[i % len(C_COHORT)]
        sel = (YEARS >= py) & (YEARS <= py + age)
        ax_p.fill_between(YEARS[sel], 0.0, hazard[sel] * 100.0, color=colour, alpha=0.28)
        ax_p.annotate(
            f"×{table[py]['risikofaktor']:.2f}".replace(".", ","),
            xy=(py + age / 2.0, hazard[(YEARS >= py) & (YEARS <= py + age)].max() * 100.0),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            color=colour,
        )
    ax_p.set_xlabel("Jahr")
    ax_p.set_ylabel("jährliche Störungswahrscheinlichkeit [%]")
    _gamma = f"{sp.gamma_warming:.2f}".replace(".", ",")
    ax_p.set_title(f"Das Risiko steigt mit der Erwärmung\n(γ = {_gamma} 1/K)")
    ax_p.grid(alpha=0.3)
    ax_p.set_ylim(bottom=0.0)

    # -- middle: stock, hazard on vs off ------------------------------------
    for i, py in enumerate(PLANT_YEARS):
        colour = C_COHORT[i % len(C_COHORT)]
        res = cohort(species_key, py, lat_deg, scenario, base)
        ref = cohort(species_key, py, lat_deg, scenario, undisturbed)
        ax_m.plot(YEARS, res.trajectory.stock_kgC, color=colour, linewidth=1.9,
                  label=f"gepflanzt {py}")
        ax_m.plot(YEARS, ref.trajectory.stock_kgC, color=colour, linewidth=1.0,
                  linestyle=":", alpha=0.8)
    ax_m.set_xlabel("Jahr")
    ax_m.set_ylabel("Kohlenstoffvorrat [kgC]")
    ax_m.set_title("Vorrat: durchgezogen mit Störung,\ngepunktet ohne")
    ax_m.grid(alpha=0.3)
    ax_m.legend(fontsize=8.5, loc="upper left")

    # -- right: the two costs as numbers ------------------------------------
    x = np.arange(len(PLANT_YEARS))
    colours = [C_COHORT[i % len(C_COHORT)] for i in range(len(PLANT_YEARS))]
    ax_b.bar(
        x,
        [table[py]["p_stoerung"] * 100.0 for py in PLANT_YEARS],
        color=colours,
        width=0.6,
    )
    for i, py in enumerate(PLANT_YEARS):
        ax_b.text(
            i,
            table[py]["p_stoerung"] * 100.0 + 1.0,
            f"−{table[py]['verlust_anteil'] * 100:.1f} %".replace(".", ","),
            ha="center",
            fontsize=9,
            color=C_NET,
        )
    ax_b.set_xticks(x)
    ax_b.set_xticklabels([str(py) for py in PLANT_YEARS])
    ax_b.set_xlabel("Pflanzjahr")
    ax_b.set_ylabel(f"P(mind. 1 Störung in {age} a) [%]")
    ax_b.set_ylim(0, 100)
    ax_b.grid(axis="y", alpha=0.3)

    ax_t = ax_b.twinx()
    stars = [table[py]["t_star"] for py in PLANT_YEARS]
    finite = [(i, v) for i, v in enumerate(stars) if np.isfinite(v)]
    if finite:
        ax_t.plot(
            [i for i, _ in finite],
            [v for _, v in finite],
            marker="D",
            markersize=7,
            color=C_NET,
            linewidth=1.4,
            label="Ausgleichsjahr t*",
        )
    for i, v in enumerate(stars):
        if not np.isfinite(v):
            ax_t.annotate("kein t*", xy=(i, 0.5), xycoords=("data", "axes fraction"),
                          ha="center", fontsize=9, color=C_NET)
    ax_t.set_ylabel("Ausgleichsjahr t*")
    # No legend: it would sit on top of a bar or an annotation whichever
    # corner it took. The right-hand axis label and the panel title
    # ("t*, Rauten") already say what the diamonds are.
    ax_b.set_title(
        f"Später pflanzen kostet zweimal:\nRisiko (Balken) und Zeit (t*, Rauten)"
    )

    fig.suptitle(
        f"{sp.name_de} ({sp.name_lat}), {abs(lat_deg):.0f}°"
        f"{'S' if lat_deg < 0 else 'N'}, {scenario.upper()}: "
        f"derselbe Baum, vier Pflanzjahre",
        fontsize=13,
    )
    fig.tight_layout()
    return _save(fig, out_path)


def plot_growth_curves(
    out_path: str,
    *,
    scenario: str = SZENARIO,
    config: ModelConfig | None = None,
) -> str:
    """Folie: the five species' growth curves, the parameterisation made visible.

    One panel, five curves, m(t) per tree. This is the first figure of the
    analysis part and the simplest one in the deck on purpose: everything
    that follows is this curve pushed through the forcing chain, so the
    audience should see the input before the output.

    Each curve is annotated with its own m_max and k, and the saturation
    level is drawn as a faint dashed line, so the two parameters that shape
    it can be read off the figure rather than looked up in a table. The
    disturbed run (solid) is shown against the undisturbed one (dotted) for
    the same species, which is what makes the gap between "what the equation
    says" and "what the model carries" visible at a glance.
    """
    from nbs.pipeline import run_single_tree
    from nbs.species import REFERENCE_SITES

    base = config or ModelConfig()
    undisturbed = ModelConfig(**{**base.__dict__, "disturbance": "off"})
    colours = ("#2166ac", "#8073ac", "#fdb863", "#7fbc41", "#1b7837")

    fig, ax = plt.subplots(figsize=(12.5, 5.6))
    for i, (key, lat) in enumerate(REFERENCE_SITES.items()):
        sp = get_species(key)
        colour = colours[i % len(colours)]
        with_dist = run_single_tree(key, lat, scenario, config=base)
        without = run_single_tree(key, lat, scenario, config=undisturbed)
        ax.plot(YEARS, without.trajectory.stock_kgC, color=colour, linewidth=1.1,
                linestyle=":", alpha=0.9)
        k_de = f"{sp.k:.3f}".replace(".", ",")
        hemi = "S" if lat < 0 else "N"
        ax.plot(
            YEARS, with_dist.trajectory.stock_kgC, color=colour, linewidth=2.2,
            label=(
                f"{sp.name_de} ({abs(lat):.0f}°{hemi})   "
                f"m$_{{max}}$ {sp.m_max_kgC:.0f} kgC · k {k_de} 1/a"
            ),
        )
        # The parameters live in the legend, not as annotations on the
        # saturation lines: two species share m_max = 50 kgC, so annotations
        # placed at that level sit on top of each other.
        ax.axhline(sp.m_max_kgC, color=colour, linewidth=0.7, linestyle="--", alpha=0.35)

    ax.set_xlabel("Jahr")
    ax.set_ylabel("Kohlenstoffvorrat je Baum [kgC]")
    ax.set_title(
        "Eine Wachstumsform, fünf Parametersätze\n"
        "durchgezogen mit Störung, gepunktet ohne — gestrichelt die Sättigung m$_{max}$"
    )
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9.5, loc="upper left", frameon=True)
    ax.set_xlim(YEARS[0], YEARS[-1])
    ax.set_ylim(bottom=0.0)
    fig.tight_layout()
    return _save(fig, out_path)


C_GROWTH = C_CARBON
C_LOSS_TODAY = "#d6604d"
C_LOSS_WARM = "#a50f15"


def plot_stock_loss_terms(
    out_path: str,
    *,
    species_key: str = "enf_boreal",
    warming_per_century_k: float = 1.0,
    dt: float = 1.0 / 12.0,
) -> str:
    """Folie 11: what each term of m(t) does to the stock of one tree.

    Three runs of the same tree, so the two factors of the slide's equation
    can be read off one figure:

    ``nur Wachstum``    the closed Chapman-Richards form, ``m_max (1 -
                        exp(-k t))^p`` -- the growth factor alone.
    ``mit Verlustterm`` the same tree with today's disturbance rate
                        ``s_0`` acting on the *stock* every year.
    ``mit steigendem``  the same tree again, with ``s(t) = s_0 exp(gamma
                        Delta T_w)`` under a linear background warming of
                        ``warming_per_century_k`` per century.

    The loss runs come from ``nbs.tree.simulate_deterministic``, i.e. from
    the integrator the notebooks use, not from the slide's algebraic factor
    ``(1 - s_0 exp(gamma Delta T_w))``. The two are not the same thing and
    the difference is the point of the figure: as a one-off factor the loss
    term is about one per cent, while the same rate applied to the standing
    stock year after year costs about a sixth of the saturation stock. What
    is drawn is the model, not the shorthand.

    The lower panel carries the disturbance rate itself. Without it the
    warming line is hard to read: ``gamma = 0,20 1/K`` over a single degree
    raises the rate by a bit more than a fifth, which is clearly visible as
    a rate and only a couple of kgC as a stock.
    """
    from nbs.tree import biomass_closed, disturbance_probability, simulate_deterministic

    sp = get_species(species_key)
    t_age = YEARS - YEARS[0]
    t_warm = warming_per_century_k * t_age / 100.0
    t_flat = np.zeros_like(t_warm, dtype=float)

    m_growth = biomass_closed(t_age, sp)
    m_today = simulate_deterministic(sp, t_flat, dt=dt).stock_kgC
    m_warm = simulate_deterministic(sp, t_warm, dt=dt).stock_kgC

    s_today = disturbance_probability(sp, t_flat) * 100.0
    s_warm = disturbance_probability(sp, t_warm) * 100.0

    fig, (ax, ax_s) = plt.subplots(
        2, 1, figsize=(9.5, 6.2), sharex=True,
        gridspec_kw={"height_ratios": [3.0, 1.0], "hspace": 0.12},
    )

    ax.fill_between(YEARS, m_warm, m_growth, color=C_LOSS_TODAY, alpha=0.13, lw=0)
    ax.fill_between(YEARS, m_warm, m_today, color=C_LOSS_WARM, alpha=0.30, lw=0)

    ax.axhline(sp.m_max_kgC, color=C_GROWTH, lw=0.8, ls="--", alpha=0.45)
    ax.annotate(
        f"$m^c_{{max}}$ = {sp.m_max_kgC:.0f} kgC",
        xy=(YEARS[0] + 2, sp.m_max_kgC), xytext=(0, 4),
        textcoords="offset points", fontsize=9, color=C_GROWTH, alpha=0.9,
    )

    ax.plot(
        YEARS, m_growth, color=C_GROWTH, lw=2.4,
        label="nur Wachstum: $m^c_{max}(1-e^{-k\\,t})^{\\,p}$",
    )
    ax.plot(
        YEARS, m_today, color=C_LOSS_TODAY, lw=2.2,
        label=(
            "mit Verlustterm, heutige Störungsrate  "
            f"($s_0$ = {sp.p_disturb * 100:.1f} %/a,  $\\Delta T_w$ = 0)"
        ).replace(".", ","),
    )
    ax.plot(
        YEARS, m_warm, color=C_LOSS_WARM, lw=2.2,
        label=(
            "mit Verlustterm, steigende Störungsrate  "
            f"($\\Delta T_w$ = +{warming_per_century_k:.0f} K je Jahrhundert,  "
            f"$\\gamma$ = {sp.gamma_warming:.2f} 1/K)"
        ).replace(".", ","),
    )

    # end-of-horizon values inside the axes, staggered so the two loss labels
    # (about 1,5 kgC apart) do not sit on top of each other
    y_end = int(YEARS[-1])
    for value, colour, dy in (
        (m_growth[-1], C_GROWTH, -14),
        (m_today[-1], C_LOSS_TODAY, 10),
        (m_warm[-1], C_LOSS_WARM, -11),
    ):
        label = (
            f"{value:.1f} kgC  ({value * M_CO2_PER_C:.0f} kg CO$_2$)".replace(".", ",")
        )
        ax.annotate(
            label, xy=(y_end - 1, value), xytext=(0, dy),
            textcoords="offset points", fontsize=9.5, color=colour,
            ha="right", va="center",
        )
    ax.annotate(
        f"Verlust bis {y_end}:  −{(1 - m_today[-1] / m_growth[-1]) * 100:.0f} %"
        f"\nmit Erwärmung:  −{(1 - m_warm[-1] / m_growth[-1]) * 100:.0f} %",
        xy=(YEARS[0] + 3, sp.m_max_kgC * 0.89), ha="left", va="top",
        fontsize=10.5, color=C_LOSS_WARM,
    )

    ax.set_ylabel("Kohlenstoffvorrat $m^c_{Baum}$ [kgC je Baum]")
    ax.set_ylim(0.0, sp.m_max_kgC * 1.12)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9.5, loc="lower right", frameon=True, borderpad=0.7)
    ax.set_title(
        f"{sp.name_de} ({sp.name_lat}): was der Verlustterm vom Vorrat nimmt",
        fontsize=12,
    )

    ax_s.plot(YEARS, s_today, color=C_LOSS_TODAY, lw=2.0)
    ax_s.plot(YEARS, s_warm, color=C_LOSS_WARM, lw=2.0)
    ax_s.fill_between(YEARS, s_today, s_warm, color=C_LOSS_WARM, alpha=0.20, lw=0)
    ax_s.annotate(
        f"$s(t) = s_0\\,e^{{\\gamma \\Delta T_w}}$:  "
        f"+{(s_warm[-1] / s_today[-1] - 1) * 100:.0f} % bis {y_end}",
        xy=(YEARS[0] + 4, s_warm[-1]), fontsize=10, color=C_LOSS_WARM, va="top",
    )
    ax_s.annotate(
        "$s_0$ konstant", xy=(y_end - 2, s_today[-1]), xytext=(0, 5),
        textcoords="offset points", fontsize=9, color=C_LOSS_TODAY,
        ha="right", va="bottom",
    )
    ax_s.set_ylim(s_today[0] - 0.06, s_warm[-1] + 0.06)
    ax_s.set_ylabel("Störungsrate $s$\n[%/a]", fontsize=9.5)
    ax_s.set_xlabel("Jahr")
    ax_s.grid(alpha=0.3)
    ax_s.set_xlim(YEARS[0], YEARS[-1])

    fig.subplots_adjust(left=0.085, right=0.985, top=0.925, bottom=0.095)
    return _save(fig, out_path)
