"""Figures for the Bäume chapter (system boundary: one tree).

Main deck, static (decided 2026-10-01 after reviewing the clips):

- ``carbon_curve_figure`` (B6) -- CO2 one tree has taken out of the air: one
  curve, valid for both sites. No map, because it would be one colour.
- ``albedo_annual_map_figure`` (B8) -- annual extra shortwave per tree as a
  map, plus the monthly cycle at both sites as the reason why.

Optional material, looping clips. Both a map of where the Norway spruce can grow next to a curve
for the two example sites (Aachen, Archangelsk):

- ``carbon_map_animation`` -- CO2 one tree has taken out of the air, over the
  years. Growth depends on the species only, so the map fills uniformly and
  both sites share one curve. That uniformity is the message.
- ``albedo_map_animation`` -- extra shortwave one full-grown tree absorbs,
  over the months. Only locally measured cells carry a seasonal cycle; the
  rest of the range is drawn as "estimated, no seasonal cycle".

Shell 1 means no feedback from the climate yet: the disturbance rate stays at
its present-day value (gamma_warming = 0, no background warming).

German labels: these go straight onto slides.
"""

from __future__ import annotations

import dataclasses
import os
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.animation import FFMpegWriter, FuncAnimation  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

from nbs import albedo_grid  # noqa: E402
from nbs.borders import add_borders  # noqa: E402
from nbs.constants import M_CO2_PER_C, YEARS  # noqa: E402
from nbs.grid import grid_lats, grid_lons  # noqa: E402
from nbs.landscape import land_mask  # noqa: E402
from nbs.recommend import candidate_lat_range  # noqa: E402
from nbs.species import get_species  # noqa: E402
from nbs.tree import simulate_deterministic  # noqa: E402

SPECIES_KEY = "picea_abies"

# Deck surface and ink (docs/slides/dissvortrag.pptx).
C_SURFACE = "#f3eee6"
C_INK = "#1a2320"
C_INK_MUTED = "#5f6b66"
C_LAND_OUTSIDE = "#e6e0d4"
C_RANGE_UNMEASURED = "#cfc7b6"

# Sequential ramps, light -> dark, validated against C_SURFACE (dataviz
# validate_palette.js --ordinal: monotone L, step gaps, light end >= 2:1).
RAMP_CARBON = ("#8db57d", "#64955a", "#437541", "#2a582d", "#163b1b")
RAMP_ALBEDO = ("#e3934f", "#d07a30", "#b25f17", "#86420a", "#552704")

MONTHS_DE = ("Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez")
MONTHS_DE_LONG = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)

# Europe + western Russia: both sites in view, at a size that reads on a slide.
EXTENT = (-12.0, 65.0, 35.0, 72.0)  # lon_min, lon_max, lat_min, lat_max

FIG_SIZE_IN = (12.0, 5.625)  # 16:7.5 -> 1920 x 900 px at FIG_DPI
FIG_DPI = 160


@dataclass(frozen=True)
class Site:
    name: str
    lat: float
    lon: float
    color: str
    marker: str


# Validated as a categorical pair against C_SURFACE (CVD and normal-vision
# separation pass); markers differ in shape too, so identity is never colour alone.
SITES = (
    Site("Aachen", 50.78, 6.08, "#2f6fb7", "o"),
    Site("Archangelsk", 64.5, 40.6, "#b8357f", "s"),
)


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------


def site_cell(site: Site) -> tuple[int, int]:
    """(row, col) of the 0.5-degree cell containing the site."""
    return int(np.argmin(np.abs(grid_lats() - site.lat))), int(np.argmin(np.abs(grid_lons() - site.lon)))


def species_range_mask(species_key: str = SPECIES_KEY) -> NDArray:
    """(360, 720) bool: land within the species' latitude hull.

    Where it *can* grow, not where it is planted in the potential cascade --
    the latter also drops cropland and settlements, which would remove Aachen.
    """
    lo, hi = candidate_lat_range(species_key)
    abs_lat = np.abs(grid_lats())[:, None]
    return land_mask() & (abs_lat >= lo) & (abs_lat < hi)


def cumulative_uptake_kg_co2(species_key: str = SPECIES_KEY) -> NDArray:
    """CO2 one tree has taken out of the air since planting [kg CO2], on YEARS.

    Shell 1: disturbance at its present-day rate, no warming feedback.
    Net uptake already nets out what disturbance returns to the air.
    """
    sp = dataclasses.replace(get_species(species_key), gamma_warming=0.0)
    traj = simulate_deterministic(sp, np.zeros(len(YEARS)))
    return M_CO2_PER_C * np.cumsum(traj.net_uptake_kgC_yr)


def interpolate_frames(monthly: NDArray, steps_per_month: int) -> NDArray:
    """Linear in-between frames, wrapping December -> January.

    Returns 12 * steps_per_month frames; frame k * steps_per_month is month k.
    """
    nxt = np.roll(monthly, -1, axis=0)
    w = np.arange(steps_per_month) / steps_per_month
    frames = [(1.0 - wi) * monthly[m] + wi * nxt[m] for m in range(12) for wi in w]
    return np.stack(frames, axis=0)


def albedo_watts_monthly(species_key: str = SPECIES_KEY) -> tuple[NDArray, NDArray]:
    """((12, 360, 720) W per full-grown tree, (360, 720) bool measured).

    Positive = the tree absorbs more than the open land it replaces. Measured
    monthly values, unsmoothed: the in-between frames already make the loop
    continuous, and smoothing would flatten the spring peak that is the point.
    """
    area = get_species(species_key).stand_area_m2
    watts = -albedo_grid.monthly_product(species_key) * area
    measured = albedo_grid.product_provenance_grid(species_key) == 0
    return watts, measured


# --------------------------------------------------------------------------
# Drawing
# --------------------------------------------------------------------------


def _register_fonts() -> tuple[str, str]:
    """(heading, body) font families: Literata + Arial like the deck, if installed."""
    heading = "DejaVu Serif"
    for path in Path.home().joinpath("Library", "Fonts").glob("Literata_18pt-SemiBold.ttf"):
        font_manager.fontManager.addfont(str(path))
        heading = font_manager.FontProperties(fname=str(path)).get_name()
    body = "Arial" if any(f.name == "Arial" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
    return heading, body


def _style(body: str) -> None:
    plt.rcParams.update(
        {
            "font.family": body,
            "font.size": 13,
            "mathtext.fontset": "custom",
            "mathtext.rm": body,
            "mathtext.it": f"{body}:italic",
            "text.color": C_INK,
            "axes.labelcolor": C_INK_MUTED,
            "axes.edgecolor": C_INK_MUTED,
            "xtick.color": C_INK_MUTED,
            "ytick.color": C_INK_MUTED,
            "figure.facecolor": C_SURFACE,
            "axes.facecolor": C_SURFACE,
            "savefig.facecolor": C_SURFACE,
        }
    )


def _ramp_cmap(ramp: tuple[str, ...]) -> mcolors.Colormap:
    return mcolors.LinearSegmentedColormap.from_list("ramp", list(ramp))


def _layout():
    fig = plt.figure(figsize=FIG_SIZE_IN, dpi=FIG_DPI)
    ax_map = fig.add_axes((0.015, 0.20, 0.60, 0.78))
    ax_cbar = fig.add_axes((0.10, 0.115, 0.43, 0.03))
    ax_curve = fig.add_axes((0.69, 0.20, 0.25, 0.63))
    return fig, ax_map, ax_cbar, ax_curve


def _map_base(ax, field_mask_outside: NDArray, unmeasured: NDArray | None) -> None:
    """Background layers: land outside the range, range without data."""
    lons, lats = grid_lons(), grid_lats()
    ax.pcolormesh(
        lons, lats, np.ma.masked_where(~field_mask_outside, np.ones(field_mask_outside.shape)),
        cmap=mcolors.ListedColormap([C_LAND_OUTSIDE]), shading="auto", zorder=1,
    )
    if unmeasured is not None:
        ax.pcolormesh(
            lons, lats, np.ma.masked_where(~unmeasured, np.ones(unmeasured.shape)),
            cmap=mcolors.ListedColormap([C_RANGE_UNMEASURED]), shading="auto", zorder=2,
        )
    add_borders(ax, linewidth=0.5, alpha=0.7)
    lon0, lon1, lat0, lat1 = EXTENT
    ax.set_xlim(lon0, lon1)
    ax.set_ylim(lat0, lat1)
    ax.set_aspect(1.0 / np.cos(np.deg2rad(0.5 * (lat0 + lat1))))
    ax.set_axis_off()


def _site_markers(ax) -> None:
    for s in SITES:
        ax.plot(
            s.lon, s.lat, marker=s.marker, ms=11, mfc=s.color, mec="white", mew=2.0,
            zorder=10, linestyle="none",
        )
        ax.annotate(
            s.name, (s.lon, s.lat), xytext=(9, 7), textcoords="offset points",
            fontsize=13, fontweight="bold", color=C_INK, zorder=11,
            bbox=dict(boxstyle="round,pad=0.2", fc=C_SURFACE, ec="none", alpha=0.85),
        )


def _clean_axes(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", color="#d9d2c4", linewidth=0.8)
    ax.set_axisbelow(True)


def _writer(fps: int) -> FFMpegWriter:
    try:
        import imageio_ffmpeg

        plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:  # system ffmpeg on PATH
        pass
    return FFMpegWriter(
        fps=fps, codec="libx264", bitrate=-1,
        extra_args=["-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-movflags", "+faststart"],
    )


# --------------------------------------------------------------------------
# Clip 1: carbon over the years
# --------------------------------------------------------------------------


def carbon_map_animation(
    out_path: str,
    *,
    poster_path: str | None = None,
    fps: int = 12,
    hold_s: float = 2.0,
    poster_only: bool = False,
) -> str:
    heading_font, body_font = _register_fonts()
    _style(body_font)

    uptake = cumulative_uptake_kg_co2()
    in_range = species_range_mask()
    outside = land_mask() & ~in_range
    vmax = float(np.ceil(uptake.max() / 10.0) * 10.0)
    norm = mcolors.Normalize(0.0, vmax)
    cmap = _ramp_cmap(RAMP_CARBON)
    cmap.set_under(C_RANGE_UNMEASURED)

    fig, ax_map, ax_cbar, ax_curve = _layout()
    _map_base(ax_map, outside, None)
    field = np.where(in_range, 0.0, np.nan)
    mesh = ax_map.pcolormesh(
        grid_lons(), grid_lats(), np.ma.masked_invalid(field), cmap=cmap,
        norm=mcolors.Normalize(1e-9, vmax), shading="auto", zorder=3,
    )
    _site_markers(ax_map)
    year_txt = ax_map.text(
        0.015, 0.97, "", va="top", transform=ax_map.transAxes, fontsize=34, family=heading_font,
        color=C_INK, zorder=12,
    )

    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=_ramp_cmap(RAMP_CARBON)), cax=ax_cbar,
                      orientation="horizontal")
    cb.outline.set_visible(False)
    cb.set_label("CO$_2$, das eine Fichte der Luft entnommen hat [kg]", fontsize=12, color=C_INK)

    _clean_axes(ax_curve)
    ax_curve.set_xlim(YEARS[0], YEARS[-1])
    ax_curve.set_ylim(0.0, vmax)
    ax_curve.set_xticks([2025, 2050, 2075, 2100, 2125, 2150])
    ax_curve.set_ylabel("kg CO$_2$ je Baum")
    ax_curve.plot(YEARS, uptake, color=RAMP_CARBON[0], linewidth=2.0, alpha=0.35)
    (line,) = ax_curve.plot([], [], color=RAMP_CARBON[3], linewidth=2.5)
    dots = [
        ax_curve.plot([], [], marker=s.marker, ms=10, mfc=s.color, mec="white", mew=1.8,
                      linestyle="none", zorder=5, clip_on=False)[0]
        for s in SITES
    ]
    ax_curve.set_title("Aachen und Archangelsk: dieselbe Kurve", fontsize=13, loc="left", color=C_INK)
    fig.text(0.69, 0.06, "Im Modell wächst eine Art überall gleich schnell.\n"
             "Gemeine Fichte, Störung mit heutiger Rate.", fontsize=10, color=C_INK_MUTED, va="bottom")

    n_hold = int(round(hold_s * fps))
    frame_idx = list(range(len(YEARS))) + [len(YEARS) - 1] * n_hold

    def draw(k: int):
        n = frame_idx[k]
        mesh.set_array(np.ma.masked_invalid(np.where(in_range, uptake[n], np.nan)))
        year_txt.set_text(str(int(YEARS[n])))
        line.set_data(YEARS[: n + 1], uptake[: n + 1])
        for i, d in enumerate(dots):
            # the two sites lie on the same curve; offset the markers slightly
            d.set_data([YEARS[n] - (3.2 if i == 0 else 0.0)], [uptake[n]])
        return [mesh, year_txt, line, *dots]

    if poster_path:
        draw(len(frame_idx) - 1)
        fig.savefig(poster_path, dpi=FIG_DPI)
    if not poster_only:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        FuncAnimation(fig, draw, frames=len(frame_idx), blit=False).save(out_path, writer=_writer(fps), dpi=FIG_DPI)
    plt.close(fig)
    return out_path


# --------------------------------------------------------------------------
# Clip 2: albedo over the months
# --------------------------------------------------------------------------


def albedo_map_animation(
    out_path: str,
    *,
    poster_path: str | None = None,
    poster_month: int = 4,
    fps: int = 16,
    steps_per_month: int = 8,
    poster_only: bool = False,
    vmax: float = 250.0,
) -> str:
    heading_font, body_font = _register_fonts()
    _style(body_font)

    watts, measured_all = albedo_watts_monthly()
    in_range = species_range_mask()
    measured = in_range & measured_all
    outside = land_mask() & ~in_range
    frames = interpolate_frames(watts, steps_per_month)
    annual = albedo_grid.alpha_q_product(SPECIES_KEY) * -get_species(SPECIES_KEY).stand_area_m2

    norm = mcolors.Normalize(0.0, vmax)
    cmap = _ramp_cmap(RAMP_ALBEDO)

    fig, ax_map, ax_cbar, ax_curve = _layout()
    _map_base(ax_map, outside, in_range & ~measured)
    mesh = ax_map.pcolormesh(
        grid_lons(), grid_lats(), np.ma.masked_where(~measured, frames[0]), cmap=cmap, norm=norm,
        shading="auto", zorder=3,
    )
    _site_markers(ax_map)
    month_txt = ax_map.text(
        0.015, 0.97, "", va="top", transform=ax_map.transAxes, fontsize=34, family=heading_font,
        color=C_INK, zorder=12,
    )

    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=ax_cbar, orientation="horizontal",
                      extend="max")
    cb.outline.set_visible(False)
    cb.set_label("zusätzlich absorbiertes Sonnenlicht je ausgewachsener Fichte [W]", fontsize=12,
                 color=C_INK)

    _clean_axes(ax_curve)
    x_month = np.arange(12)
    x_frames = np.arange(len(frames)) / steps_per_month
    site_series = []
    for s in SITES:
        i, j = site_cell(s)
        series = frames[:, i, j]
        site_series.append(series)
        ax_curve.plot(np.append(x_frames, 12.0), np.append(series, series[0]), color=s.color, linewidth=2.2)
        mean_w = float(annual[i, j])
        ax_curve.axhline(mean_w, color=s.color, linewidth=1.2, linestyle=(0, (4, 3)), alpha=0.8)
        ax_curve.text(12.25, mean_w, f"Ø {mean_w:.0f} W", color=C_INK, fontsize=11, ha="left",
                      va="center", clip_on=False)
    ax_curve.set_xlim(0, 12)
    ax_curve.set_xticks(x_month + 0.0)
    ax_curve.set_xticklabels([m[0] for m in MONTHS_DE])
    ax_curve.set_ylim(0, max(float(s.max()) for s in site_series) * 1.12)
    ax_curve.set_ylabel("W je Baum")
    ax_curve.set_title("Jahresgang an beiden Orten", fontsize=13, loc="left", color=C_INK)
    dots = [
        ax_curve.plot([], [], marker=s.marker, ms=10, mfc=s.color, mec="white", mew=1.8, linestyle="none",
                      zorder=5, clip_on=False)[0]
        for s in SITES
    ]
    cursor = ax_curve.axvline(0, color=C_INK_MUTED, linewidth=1.0, alpha=0.6)
    fig.text(0.69, 0.06, "Farbig: lokal gemessen (Duveiller et al. 2018).\n"
             "Ausgewachsene Gemeine Fichte statt Wiese.", fontsize=10, color=C_INK_MUTED, va="bottom")
    fig.patches.append(plt.Rectangle((0.555, 0.115), 0.018, 0.03, transform=fig.transFigure,
                                     fc=C_RANGE_UNMEASURED, ec="none"))
    fig.text(0.578, 0.13, "Fichtengebiet,\nnicht gemessen", fontsize=10, color=C_INK, va="center")

    def draw(k: int):
        mesh.set_array(np.ma.masked_where(~measured, frames[k]))
        month_txt.set_text(MONTHS_DE_LONG[k // steps_per_month])
        for d, series in zip(dots, site_series):
            d.set_data([x_frames[k]], [series[k]])
        cursor.set_xdata([x_frames[k], x_frames[k]])
        return [mesh, month_txt, cursor, *dots]

    if poster_path:
        draw((poster_month - 1) * steps_per_month)
        fig.savefig(poster_path, dpi=FIG_DPI)
    if not poster_only:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        FuncAnimation(fig, draw, frames=len(frames), blit=False).save(out_path, writer=_writer(fps), dpi=FIG_DPI)
    plt.close(fig)
    return out_path


# --------------------------------------------------------------------------
# Static figures for the main deck (the clips above stay as optional material)
# --------------------------------------------------------------------------


def carbon_curve_figure(out_path: str) -> str:
    """B6: CO2 one tree has taken out of the air, one curve for both sites.

    Deliberately no map: growth depends on the species only, so a map would
    be one colour everywhere -- a curve dressed up as a map.
    """
    _heading_font, body_font = _register_fonts()
    _style(body_font)
    uptake = cumulative_uptake_kg_co2()

    fig = plt.figure(figsize=FIG_SIZE_IN, dpi=FIG_DPI)
    ax = fig.add_axes((0.08, 0.14, 0.74, 0.76))
    _clean_axes(ax)
    ax.plot(YEARS, uptake, color=RAMP_CARBON[3], linewidth=3.0)
    ax.set_xlim(YEARS[0], YEARS[-1])
    ax.set_ylim(0.0, float(np.ceil(uptake.max() / 20.0) * 20.0))
    ax.set_xticks([2025, 2050, 2075, 2100, 2125, 2150])
    ax.set_ylabel("CO$_2$ aus der Luft geholt, je Baum [kg]")

    x_end, y_end = float(YEARS[-1]), float(uptake[-1])
    ax.plot(x_end, y_end, marker="o", ms=9, mfc=RAMP_CARBON[3], mec="white", mew=2.0, linestyle="none",
            zorder=5, clip_on=False)
    ax.annotate(f"{y_end:.0f} kg", (x_end, y_end), xytext=(14, 0), textcoords="offset points", fontsize=14,
                fontweight="bold", color=C_INK, va="center", annotation_clip=False)
    from matplotlib.lines import Line2D

    handles = [Line2D([], [], marker=s.marker, ms=11, mfc=s.color, mec="white", mew=1.8, linestyle="none")
               for s in SITES]
    ax.legend(handles, [s.name for s in SITES], title="gilt für", loc="upper left",
              bbox_to_anchor=(1.01, y_end / ax.get_ylim()[1] - 0.06), frameon=False, fontsize=13,
              title_fontsize=12, handletextpad=0.4, borderaxespad=0.0)
    fig.text(0.08, 0.025, "Gemeine Fichte, Störung mit heutiger Rate. Im Modell wächst eine Art überall gleich "
             "schnell — an beiden Orten dieselbe Kurve.", fontsize=10.5, color=C_INK_MUTED)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path


def albedo_annual_map_figure(out_path: str, *, vmin: float = 20.0, vmax: float = 100.0) -> str:
    """B8: yearly extra shortwave per full-grown tree as a map, plus the
    monthly cycle at both sites as the reason why.

    Only locally measured cells are coloured; the rest of the range is grey.
    (A variant that coloured the latitude-band estimates too and hatched them
    was tried and dropped: the hatching smeared the whole map.) The colour
    scale is stretched to vmin..vmax because the annual values cluster at
    30-100 W -- on a 0-based scale the north-south difference vanishes,
    although 44 vs 65 W is worth 20 years of t*.
    """
    _heading_font, body_font = _register_fonts()
    _style(body_font)

    area = get_species(SPECIES_KEY).stand_area_m2
    annual = -albedo_grid.alpha_q_product(SPECIES_KEY) * area
    watts, measured_all = albedo_watts_monthly()
    in_range = species_range_mask()
    measured = in_range & measured_all
    estimated = in_range & ~measured_all
    outside = land_mask() & ~in_range

    cmap = _ramp_cmap(RAMP_ALBEDO)
    norm = mcolors.Normalize(vmin, vmax)
    fig, ax_map, ax_cbar, ax_curve = _layout()
    _map_base(ax_map, outside, estimated)
    ax_map.pcolormesh(grid_lons(), grid_lats(), np.ma.masked_where(~measured, annual), cmap=cmap, norm=norm,
                      shading="auto", zorder=3)
    _site_markers(ax_map)

    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=ax_cbar, orientation="horizontal",
                      extend="both")
    cb.outline.set_visible(False)
    cb.set_label("zusätzlich absorbiertes Sonnenlicht je ausgewachsener Fichte, Jahresmittel [W]",
                 fontsize=12, color=C_INK)
    fig.patches.append(plt.Rectangle((0.555, 0.115), 0.018, 0.03, transform=fig.transFigure,
                                     fc=C_RANGE_UNMEASURED, ec="none"))
    legend_txt = "Fichtengebiet,\nnicht gemessen"
    fig.text(0.578, 0.13, legend_txt, fontsize=10, color=C_INK, va="center")

    _clean_axes(ax_curve)
    x = np.arange(12)
    top = 0.0
    for s in SITES:
        i, j = site_cell(s)
        series = watts[:, i, j]
        top = max(top, float(series.max()))
        ax_curve.plot(x, series, color=s.color, linewidth=2.4, marker=s.marker, ms=6, mfc=s.color,
                      mec="white", mew=1.0)
        mean_w = float(annual[i, j])
        ax_curve.axhline(mean_w, color=s.color, linewidth=1.2, linestyle=(0, (4, 3)), alpha=0.8)
        ax_curve.text(11.4, mean_w, f"Ø {mean_w:.0f} W", color=C_INK, fontsize=11, ha="left", va="center",
                      clip_on=False)
    ax_curve.set_xlim(-0.3, 11.3)
    ax_curve.set_xticks(x)
    ax_curve.set_xticklabels([m[0] for m in MONTHS_DE])
    ax_curve.set_ylim(0, top * 1.12)
    ax_curve.set_ylabel("W je Baum")
    ax_curve.set_title("Warum: Jahresgang an beiden Orten", fontsize=13, loc="left", color=C_INK)
    fig.text(0.69, 0.06, "Lokal gemessen nach Duveiller et al. (2018).\nAusgewachsene Gemeine Fichte statt Wiese.",
             fontsize=10, color=C_INK_MUTED, va="bottom")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path
