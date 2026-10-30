"""Figures for the Bäume chapter (system boundary: one tree).

Main deck, static (decided 2026-10-01 after reviewing the clips):

- ``carbon_curve_figure`` (B6) -- CO2 one tree has taken out of the air at
  the two sites (growth level from nbs.site_factor).
- ``albedo_annual_map_figure`` (B8) -- annual extra shortwave per tree as a
  map, plus the monthly cycle at both sites as the reason why.

Optional material, looping clips. Both a map of where the Norway spruce can grow next to a curve
for the example sites (Aachen, Fairbanks, Marabá):

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
from functools import lru_cache
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
from nbs.constants import M_CO2_PER_C, T_START, YEARS  # noqa: E402
from nbs.grid import grid_lats, grid_lons  # noqa: E402
from nbs.landscape import land_mask  # noqa: E402
from nbs.site_factor import site_factor, site_factor_grid  # noqa: E402
from nbs.forest_data import TYPES, key_grid, typical_type  # noqa: E402
from nbs.species import SPECIES, get_species  # noqa: E402
from nbs.tree import simulate_deterministic  # noqa: E402

SPECIES_KEY: str | None = None
_STAND_AREA_M2 = 5.0  # 2000 trees/ha (nbs.forest_data.TREES_PER_HA)
"""None = each cell / site with its own typical forest (2026-10-05). The
running example used to be one species, Norway spruce, everywhere."""

# Deck surface and ink (the HTML deck's paper and ink colours).
C_SURFACE = "#f3eee6"
C_INK = "#1a2320"
C_INK_MUTED = "#5f6b66"
C_LAND_OUTSIDE = "#f3eee6"  # outside the range: no fill, borders only
C_RANGE_UNMEASURED = "#e2ddd3"  # validated apart from the ramps' light ends

# Sequential ramps, light -> dark, validated against C_SURFACE (dataviz
# validate_palette.js --ordinal: monotone L, step gaps, light end >= 2:1).
RAMP_CARBON = ("#8db57d", "#64955a", "#437541", "#2a582d", "#163b1b")
RAMP_ALBEDO = ("#e3934f", "#d07a30", "#b25f17", "#86420a", "#552704")
# Map ramps, validated the same way. Multi-hue sand -> brick -> wine for the
# extra absorbed light (more steps that read apart than a single hue), and one
# ramp per ingredient so the three maps are never confused for each other.
RAMP_ABSORBED = ("#cf9534", "#c9762c", "#b85328", "#97332d", "#6a1f40", "#3a1338")
RAMP_SUN = ("#cf9e33", "#bb8428", "#9c6921", "#7a4f1b", "#513413")
RAMP_SNOW = ("#88aad2", "#5e8cc1", "#3b6ba5", "#25507e", "#143154")

MONTHS_DE = ("Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez")
MONTHS_DE_LONG = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)

# Europe + western Russia: both sites in view, at a size that reads on a slide.
EXTENT = (-12.0, 65.0, 35.0, 72.0)  # lon_min, lon_max, lat_min, lat_max
WORLD = (-180.0, 180.0, -58.0, 84.0)
# the light maps since a tropical site joined (2026-10-06): the part of the world with all three sites
SITES_VIEW = (-160.0, 55.0, -30.0, 72.0)

FIG_SIZE_IN = (12.0, 5.625)  # 16:7.5 -> 1920 x 900 px at FIG_DPI
FIG_DPI = 160


@dataclass(frozen=True)
class Site:
    name: str
    lat: float
    lon: float
    color: str
    marker: str
    cc: str = ""  # ISO country code, shown with the name

    @property
    def label(self) -> str:
        return f"{self.name} ({self.cc})" if self.cc else self.name


# Each site in the colour of its forest type on the forest-type map (nbs.map_fields CATEGORIES["waldtyp"]);
# markers differ in shape too, so identity is never colour alone.
SITES = (
    Site("Aachen", 50.78, 6.08, "#8a5596", "o", "DE"),
    # interior Alaska: boreal conifer forest, snow half the year, much reforestable land -- a site where the tree
    # warms by 2100 (replaced Joensuu, boreal mixed forest, 2026-10-22)
    Site("Fairbanks", 64.84, -147.72, "#243f8f", "s", "US"),
    # south-eastern Amazon (Pará), "arc of deforestation": much reforestable land, much sun, a typical
    # tropical carbon potential (Walker et al. 2022: 139 Mg C/ha; Belém, tried first, has only 80) -- 2026-10-06
    Site("Marabá", -5.37, -49.12, "#3d8a42", "D", "BR"),
)


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------


def site_cell(site: Site) -> tuple[int, int]:
    """(row, col) of the 0.5-degree cell containing the site."""
    return int(np.argmin(np.abs(grid_lats() - site.lat))), int(np.argmin(np.abs(grid_lons() - site.lon)))


def site_key(site: Site) -> str:
    """Typical forest x climate zone at the site (nbs.forest_data.key_grid)."""
    return str(key_grid()[site_cell(site)])


def species_range_mask(species_key: str | None = SPECIES_KEY) -> NDArray:
    """(360, 720) bool: reforestable cells (Walker et al. 2022) with a known
    typical forest -- all of them for None, else where *species_key* is the
    typical forest."""
    keys = key_grid()
    return keys != None if species_key is None else keys == species_key  # noqa: E711


def cumulative_uptake_kg_co2(
    species_key: str | None = SPECIES_KEY, lat_deg: float | None = None, lon_deg: float | None = None
) -> NDArray:
    """CO2 one tree has taken out of the air since planting [kg CO2], on YEARS.

    Shell 1: disturbance at its present-day rate, no warming feedback.
    Net uptake already nets out what disturbance returns to the air. Carbon
    level at the site's cell via the site factor (nbs.site_factor); no
    latitude = the key's median cell.
    """
    sp = get_species(species_key)
    f = 1.0 if lat_deg is None else site_factor(species_key, lat_deg, lon_deg)
    sp = dataclasses.replace(sp, gamma_warming=0.0, m_max_kgC=sp.m_max_kgC * f)
    traj = simulate_deterministic(sp, np.zeros(len(YEARS)))
    return M_CO2_PER_C * np.cumsum(traj.net_uptake_kgC_yr)


def site_uptake_kg_co2(site: Site) -> NDArray:
    """cumulative_uptake_kg_co2 for the typical forest at *site*'s cell."""
    return cumulative_uptake_kg_co2(site_key(site), site.lat, site.lon)


@lru_cache(maxsize=1)
def _uptake_parts() -> tuple[NDArray, NDArray, NDArray]:
    """(curves (n_keys, n_years), key index grid (-1 = none), factor grid):
    the uptake field is curves[idx][:, n] * factor, without holding all years
    of the full grid in memory."""
    keys = key_grid()
    names = sorted({k for k in keys.ravel() if k is not None})
    curves = np.stack([cumulative_uptake_kg_co2(k) for k in names])
    idx = np.full(keys.shape, -1)
    factor = np.zeros(keys.shape)
    for n, k in enumerate(names):
        sel = keys == k
        idx[sel] = n
        factor[sel] = site_factor_grid(k)[sel]
    return curves, idx, factor


def uptake_field(year_index: int) -> NDArray:
    """(360, 720) cumulative uptake per tree [kg CO2] of the typical forest
    in each cell at YEARS[year_index]; NaN where no typical forest."""
    curves, idx, factor = _uptake_parts()
    return np.where(idx >= 0, curves[np.maximum(idx, 0), year_index] * factor, np.nan)


def _type_representative(ftype: str) -> str:
    """Any registry key of the forest type: albedo depends on the IGBP class only."""
    return next(k for k in SPECIES if k.startswith(ftype + "_"))


def _by_type(fn) -> NDArray:
    """Compose a per-key albedo grid: each cell takes its typical forest type."""
    typ = typical_type()
    out = None
    for t in TYPES:
        sel = typ == t
        if not sel.any():
            continue
        g = np.asarray(fn(_type_representative(t)))
        if out is None:
            out = np.full(g.shape, np.nan)
        out[..., sel] = g[..., sel]
    return out


@lru_cache(maxsize=1)
def typical_alpha_q_product() -> NDArray:
    """(360, 720) annual alpha*Q product of the typical forest per cell."""
    return _by_type(albedo_grid.alpha_q_product)


@lru_cache(maxsize=1)
def typical_light_product() -> NDArray:
    """(360, 720) net light product (albedo + clouds, nbs.light) of the typical forest per cell."""
    from nbs.light import light_product

    return _by_type(light_product)


@lru_cache(maxsize=1)
def typical_cloud_product() -> NDArray:
    """(360, 720) cloud brightening product (nbs.cloud_grid) of the typical forest per cell."""
    from nbs.cloud_grid import cloud_q_product

    return _by_type(cloud_q_product)


@lru_cache(maxsize=1)
def typical_measured_mask() -> NDArray:
    """(360, 720) bool: albedo of the cell's typical forest locally measured."""
    return _by_type(lambda k: (albedo_grid.product_provenance_grid(k) == 0).astype(float)) == 1.0


def interpolate_frames(monthly: NDArray, steps_per_month: int) -> NDArray:
    """Linear in-between frames, wrapping December -> January.

    Returns 12 * steps_per_month frames; frame k * steps_per_month is month k.
    """
    nxt = np.roll(monthly, -1, axis=0)
    w = np.arange(steps_per_month) / steps_per_month
    frames = [(1.0 - wi) * monthly[m] + wi * nxt[m] for m in range(12) for wi in w]
    return np.stack(frames, axis=0)


def albedo_watts_monthly(species_key: str | None = SPECIES_KEY) -> tuple[NDArray, NDArray]:
    """((12, 360, 720) W per full-grown tree, (360, 720) bool measured).

    None: each cell with its typical forest type. Positive = the tree
    absorbs more than the open land it replaces. Measured monthly values,
    unsmoothed: the in-between frames already make the loop continuous, and
    smoothing would flatten the spring peak that is the point.
    """
    from nbs.forest_data import TREES_PER_HA

    area = 1e4 / TREES_PER_HA
    from nbs.light import monthly_light_product

    if species_key is None:
        watts = -_by_type(monthly_light_product) * area
        return watts, typical_measured_mask()
    watts = -monthly_light_product(species_key) * area
    measured = albedo_grid.product_provenance_grid(species_key) == 0
    return watts, measured


# --------------------------------------------------------------------------
# Drawing helpers
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


def _map_base(ax, field_mask_outside: NDArray, unmeasured: NDArray | None, extent=EXTENT) -> None:
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
    lon0, lon1, lat0, lat1 = extent
    ax.set_xlim(lon0, lon1)
    ax.set_ylim(lat0, lat1)
    # Europe: equal distances at its middle latitude; world: the deck's world projection (nbs.borders.MAP_ASPECT)
    from nbs.borders import MAP_ASPECT
    ax.set_aspect(1.0 / np.cos(np.deg2rad(0.5 * (lat0 + lat1))) if extent == EXTENT else MAP_ASPECT)
    ax.set_axis_off()


def _title_with_symbol(ax, title: str, symbol: str, color: str) -> None:
    """A map's title and, right after it, its symbol in the slides' equation (the deck sets the symbol with
    KaTeX, boxed in its colour); some room between title and map."""
    t = ax.set_title(title, loc="left", fontsize=15, color=C_INK, fontweight="bold", pad=16)
    ax.annotate(symbol, xy=(1, 0.5), xycoords=t, xytext=(14, 0), textcoords="offset points", ha="left", va="center",
                fontsize=15, color=color, fontweight="bold")


def _site_markers(ax, values=None) -> None:
    """The three sites; *values* maps a site to a second label line (the value of its cell)."""
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    for s in SITES:
        if not (min(x0, x1) <= s.lon <= max(x0, x1) and min(y0, y1) <= s.lat <= max(y0, y1)):
            continue  # e.g. Marabá on a map of Europe
        ax.plot(
            s.lon, s.lat, marker=s.marker, ms=11, mfc=s.color, mec="white", mew=2.0,
            zorder=10, linestyle="none",
        )
        # with values (two lines), the northern sites: labels left of their marker
        left = values is not None and s.lon > 0
        # Fairbanks (north) on one line beside its marker, Aachen below-left of its own
        north = left and s.lat > 55
        off, ha, va = ((-12, 0), "right", "center") if north else ((-11, -4), "right", "top") if left else ((9, 7), "left", "baseline")
        text = s.label if values is None else f"{s.label}: {values(s)}" if north else f"{s.label}\n{values(s)}"
        ax.annotate(
            text, (s.lon, s.lat), xytext=off, textcoords="offset points",
            ha=ha, va=va,
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

    site_curves = [site_uptake_kg_co2(s) for s in SITES]
    in_range = species_range_mask()
    outside = land_mask() & ~in_range
    lon0, lon1, lat0, lat1 = EXTENT
    view = in_range & (grid_lons()[None, :] >= lon0) & (grid_lons()[None, :] <= lon1) \
        & (grid_lats()[:, None] >= lat0) & (grid_lats()[:, None] <= lat1)
    vmax = float(np.ceil(max(float(np.nanpercentile(uptake_field(len(YEARS) - 1)[view], 98)), 1.0) / 50.0) * 50.0)
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
                      orientation="horizontal", extend="max")
    cb.outline.set_visible(False)
    cb.set_label("CO$_2$, das ein Baum des typischen Waldes der Luft entnommen hat [kg]", fontsize=12, color=C_INK)

    _clean_axes(ax_curve)
    ax_curve.set_xlim(YEARS[0], YEARS[-1])
    ax_curve.set_ylim(0.0, float(np.ceil(max(float(c.max()) for c in site_curves) / 50.0) * 50.0))
    ax_curve.set_xticks([T_START, 2050, 2075, 2100])
    ax_curve.set_ylabel("kg CO$_2$ je Baum")
    lines, dots = [], []
    for st, curve in zip(SITES, site_curves):
        ax_curve.plot(YEARS, curve, color=st.color, linewidth=2.0, alpha=0.25)
        lines.append(ax_curve.plot([], [], color=st.color, linewidth=2.5)[0])
        dots.append(ax_curve.plot([], [], marker=st.marker, ms=10, mfc=st.color, mec="white", mew=1.8,
                                  linestyle="none", zorder=5, clip_on=False)[0])
    ax_curve.set_title("Aachen und Fairbanks", fontsize=13, loc="left", color=C_INK)
    fig.text(0.69, 0.06, "Farbig: wiederbewaldbare Flächen (Walker et al. 2022),\n"
             "typischer Wald je Ort, Störung mit heutiger Rate.", fontsize=10, color=C_INK_MUTED, va="bottom")

    n_hold = int(round(hold_s * fps))
    frame_idx = list(range(len(YEARS))) + [len(YEARS) - 1] * n_hold

    def draw(k: int):
        n = frame_idx[k]
        mesh.set_array(np.ma.masked_invalid(np.where(in_range, uptake_field(n), np.nan)))
        year_txt.set_text(str(int(YEARS[n])))
        for ln, d, curve in zip(lines, dots, site_curves):
            ln.set_data(YEARS[: n + 1], curve[: n + 1])
            d.set_data([YEARS[n]], [curve[n]])
        return [mesh, year_txt, *lines, *dots]

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
    annual = -typical_light_product() * _STAND_AREA_M2

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
    cb.set_label("zusätzlich absorbiertes Sonnenlicht je ausgewachsenem Baum [W]", fontsize=12,
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
    ax_curve.set_ylim(min(0.0, min(float(s.min()) for s in site_series)) - 6,
                      max(float(s.max()) for s in site_series) * 1.12)
    ax_curve.axhline(0, color=C_INK_MUTED, linewidth=0.8)
    ax_curve.set_ylabel("W je Baum")
    ax_curve.set_title("Jahresgang an den drei Orten", fontsize=13, loc="left", color=C_INK)
    dots = [
        ax_curve.plot([], [], marker=s.marker, ms=10, mfc=s.color, mec="white", mew=1.8, linestyle="none",
                      zorder=5, clip_on=False)[0]
        for s in SITES
    ]
    cursor = ax_curve.axvline(0, color=C_INK_MUTED, linewidth=1.0, alpha=0.6)
    fig.text(0.69, 0.06, "Farbig: lokal gemessen (Duveiller et al. 2018).\n"
             "Ausgewachsener typischer Wald statt Wiese.", fontsize=10, color=C_INK_MUTED, va="bottom")
    fig.patches.append(plt.Rectangle((0.555, 0.115), 0.018, 0.03, transform=fig.transFigure,
                                     fc=C_RANGE_UNMEASURED, ec="none"))
    fig.text(0.578, 0.13, "wiederbewaldbar,\nnicht gemessen", fontsize=10, color=C_INK, va="center")

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
    curves = {s.name: site_uptake_kg_co2(s) for s in SITES}
    top = max(float(c.max()) for c in curves.values())

    fig = plt.figure(figsize=FIG_SIZE_IN, dpi=FIG_DPI)
    ax = fig.add_axes((0.08, 0.14, 0.74, 0.76))
    _clean_axes(ax)
    ax.set_xlim(YEARS[0], YEARS[-1])
    ax.set_ylim(0.0, float(np.ceil(top / 50.0) * 50.0))
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylabel("CO$_2$-Aufnahme je Baum [kg]")
    for s in SITES:
        c = curves[s.name]
        ax.plot(YEARS, c, color=s.color, linewidth=3.0)
        ax.plot(YEARS[-1], c[-1], marker=s.marker, ms=11, mfc=s.color, mec="white", mew=2.0,
                linestyle="none", zorder=5, clip_on=False)
        ax.annotate(f"{s.label}  {c[-1]:.0f} kg", (YEARS[-1], c[-1]), xytext=(14, 0), textcoords="offset points",
                    fontsize=14, fontweight="bold", color=C_INK, va="center", annotation_clip=False)
    fig.text(0.08, 0.025, "Typischer Wald je Ort (Hasler et al. 2024): Mischwald. Zusätzlicher Kohlenstoff je Ort "
             "(Walker et al. 2022), Tempo aus Cook-Patton et al. (2020), 2000 Bäume/ha, Störung mit heutiger Rate.",
             fontsize=10.5, color=C_INK_MUTED)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path


def albedo_annual_map_figure(out_path: str) -> str:
    """B8: yearly extra shortwave per full-grown tree as a map.

    The same layout as the deck's other world maps (nbs.vergleich_figures._world_map_skeleton): the world at full
    width, colour bar with its title and the grey layers' legend in a strip underneath. The deck draws the cells
    (nbs.map_fields.absorbed_light, 1 deg blocks); the sites keep the value of their own cell, as in the talk."""
    from nbs.vergleich_figures import _world_map_skeleton

    annual = -typical_light_product() * _STAND_AREA_M2
    return _world_map_skeleton(out_path, "b8", "zusätzlich absorbiertes Sonnenlicht je Baum, Jahresmittel [W]",
                               [0, 20, 40, 60, 80, 100], "kein Platz für Bäume", None,
                               site_label=lambda s: f"{annual[site_cell(s)]:.0f} W je Baum", width=6.9, lats=(-56, 80), fit=True)


C_CLOUD = "#4f8fb0"  # cloud brightening, as in the deck's "Wodurch ein Baum aufs Klima wirkt" drawing


def cloud_season_series(site: Site) -> tuple[NDArray, NDArray, NDArray]:
    """(albedo, clouds, net) per month in W per full-grown tree at *site*; positive = the
    Earth absorbs more light (warming), so the clouds come out mostly negative."""
    from nbs.albedo_grid import monthly_product
    from nbs.cloud_grid import monthly_cloud_product

    key, cell = site_key(site), (slice(None), *site_cell(site))
    alb = -monthly_product(key)[cell] * _STAND_AREA_M2
    cld = -monthly_cloud_product(key)[cell] * _STAND_AREA_M2
    return alb, cld, alb + cld


def cloud_season_figure(out_path: str) -> str:
    """B8w: month by month at the three sites, albedo up, clouds down, the sum as a line."""
    _heading_font, body_font = _register_fonts()
    _style(body_font)
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 3.6), dpi=FIG_DPI, sharey=True)
    fig.subplots_adjust(left=0.07, right=0.99, top=0.85, bottom=0.12, wspace=0.08)
    x = np.arange(12)
    series = [cloud_season_series(s) for s in SITES]
    lo = min(float(c.min()) for _, c, _ in series)
    hi = max(float(a.max()) for a, _, _ in series)
    for ax, s, (alb, cld, net) in zip(axes, SITES, series):
        _clean_axes(ax)
        ax.bar(x, alb, width=0.72, color=RAMP_ALBEDO[1], label="Albedo")
        # where the clouds warm too (fewer clouds over the forest), their bar sits on top of the albedo
        ax.bar(x, cld, bottom=np.where(cld > 0, alb, 0.0), width=0.72, color=C_CLOUD, label="Wolken")
        ax.plot(x, net, color=C_INK, linewidth=2.4, marker=s.marker, ms=6, mfc=s.color, mec="white", label="Summe")
        ax.axhline(0, color=C_INK_MUTED, linewidth=0.9)
        ax.set_xticks(x)
        ax.set_xticklabels([m[0] for m in MONTHS_DE])
        ax.set_xlim(-0.6, 11.6)
        ax.set_ylim(min(0.0, lo) * 1.25 - 4, hi * 1.15)
        ax.set_title(s.label, loc="left", fontsize=14, fontweight="bold", color=s.color)
    axes[0].set_ylabel("W je Baum")
    axes[-1].legend(loc="lower right", frameon=False, fontsize=12, ncol=3, bbox_to_anchor=(1.0, 1.08))
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path


def light_parts_sites_figure(out_path: str) -> str:
    """B8s: the extra absorbed light per tree at the three sites over time, 2026-2100 [W, annual mean]: it grows with
    the canopy, A_Baum(t) = closure(t) x stand area, as in the model. Laid out like the growth chart beside the
    forest-type map: sites in their colours, names centred just above their curve. Per place the net (leaves plus
    clouds); with the last click the other two places step back and Aachen's two parts come in, each as a line with
    its area to the axis (as on the slide "Ein Baum an drei Orten"): the leaves' Delta alpha_Baum up, the clouds' down."""
    from nbs.storyline_figures import run_site

    _heading_font, body_font = _register_fonts()
    _style(body_font)
    c_baum, c_wolke = "#5c7200", "#056fab"   # deck.css --s-dal, --s-daw
    fig, ax = plt.subplots(figsize=(4.4, 5.4), dpi=FIG_DPI)   # beside the 905 px map
    fig.subplots_adjust(left=0.141, right=0.977, bottom=0.07, top=0.98)
    _clean_axes(ax)
    y = YEARS
    xl = 2080   # the names stand here, just above (the steep curves: higher) their own curve
    for s in SITES:
        alb, cld, net = (float(v.mean()) for v in cloud_season_series(s))
        f = np.asarray(run_site(s).trajectory.closure, dtype=float)
        shown = s.name == "Aachen"
        fade = "" if shown else " fade:2"   # at the last click the other places step back
        ax.plot(y, net * f, color=s.color, linewidth=2.8, label=None, gid="step:0" + fade)
        # the canopy is not closed yet everywhere in 2100: the value is that of the curve
        below = s.name == "Marabá"   # lowest curve: its name below it
        off = -22 if below else {"Fairbanks": 28}.get(s.name, 18)
        ax.annotate(f"{s.label}: {net * f[-1]:.0f} W", (xl, float(np.interp(xl, y, net * f))), xytext=(0, off), textcoords="offset points",
                    ha="center", va="top" if below else "bottom", fontsize=13.5, fontweight="bold", color=s.color, gid="step:0 fade:2")   # at the last click the parts have the room
        if shown:
            for part, col, name, xn, yn, up in ((alb * f, c_baum, "Albedo (Baum)", 2042, 10.5, True), (cld * f, c_wolke, "Albedo (Wolken)", 2054, -5.0, False)):
                ax.fill_between(y, 0, part, color=col, alpha=0.22, linewidth=0, gid="step:2")
                ax.plot(y, part, color=col, linewidth=2.2, label=None, gid="step:2")
                ax.text(xn, yn, name, ha="center", va="center", fontsize=12, fontweight="bold",
                        color=col, bbox=dict(boxstyle="round,pad=0.25", facecolor=col, alpha=0.16, edgecolor="none"), gid="step:2")
                ax.annotate(f"{part[-1]:+.0f} W".replace("-", "\u2212"), (y[-1], float(part[-1])), xytext=(-2, 7 if up else -7), textcoords="offset points",
                            ha="right", va="center", fontsize=11.5, fontweight="bold", color=col, gid="step:2")
    ax.axhline(0, color=C_INK_MUTED, linewidth=0.9)
    ax.set_xlim(y[0], y[-1])
    ax.set_ylim(-8, 68)
    ax.set_yticks([0, 20, 40, 60])
    ax.set_xticks([T_START, 2060, 2100])
    ax.set_ylabel("W je Baum, Jahresmittel")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path


def cloud_brightening_grid() -> tuple[NDArray, NDArray]:
    """((360, 720) extra reflection of the extra clouds over the typical forest [%-points], annual mean;
    (360, 720) bool: in range with a local cloud retrieval)."""
    from nbs.cloud_grid import delta_alpha_w_grid

    field = 100.0 * _by_type(delta_alpha_w_grid)
    return field, species_range_mask() & np.isfinite(field)


def _pp(v: float) -> str:
    return f"{round(float(v), 2) + 0.0:.2f}".replace(".", ",").replace("-", "−")


def cloud_brightening_map_figure(out_path: str) -> str:
    """B8c: the extra reflection of the extra clouds over forest (Delta_alpha_W), annual mean, as a map.

    Same canvas and place as the maps of B8a (the slide before), the right half left free for the
    equation the slide sets there. Coloured where Duveiller et al. (2021) retrieve the cloud change
    locally; diverging at 0 -- in places the forest has fewer clouds than the open land.
    """
    from nbs.map_fields import SCALES, scale_cmap, scale_norm

    _heading_font, body_font = _register_fonts()
    _style(body_font)

    field, measured = cloud_brightening_grid()
    in_range = species_range_mask()
    outside = land_mask() & ~in_range
    sc = SCALES["wolken"]

    fig = plt.figure(figsize=(12.0, 5.6), dpi=FIG_DPI)
    ax_map = fig.add_axes((0.01, 0.16, 0.48, 0.73))
    ax_cbar = fig.add_axes((0.08, 0.085, 0.34, 0.028))
    _map_base(ax_map, outside, in_range & ~measured, SITES_VIEW)
    cmap, norm = scale_cmap(sc), scale_norm(sc)
    ax_map.pcolormesh(grid_lons(), grid_lats(), np.ma.masked_where(~measured, field), cmap=cmap, norm=norm,
                      shading="auto", zorder=3)
    _site_markers(ax_map, lambda s: f"{_pp(field[site_cell(s)])} %")
    _title_with_symbol(ax_map, "Zusätzliche Reflexion durch Wolken", r"$\Delta\alpha_{\mathrm{W}}$", "#056fab")

    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=ax_cbar, orientation="horizontal",
                      extend="both")
    cb.outline.set_visible(False)
    ax_cbar.text(1.03, 0.5, "[%]", transform=ax_cbar.transAxes, ha="left", va="center",
                 fontsize=11, color=C_INK)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path


SITES_CROP = (-62.0, 42.0, -22.0, 70.0)  # the three sites, tight enough for three maps side by side


def light_ingredients_figure(out_path: str) -> str:
    """B8i: the three ingredients of the extra absorbed light side by side, cropped to the three sites.

    Sunlight at the ground [W/m^2], how much darker the forest is (-Delta_alpha) and the extra
    reflection of the extra clouds (Delta_alpha_W), both in percent, annual means; as B8a and B8c,
    each coloured only where measured locally.
    """
    from nbs.map_fields import SCALES, scale_cmap, scale_norm

    _heading_font, body_font = _register_fonts()
    _style(body_font)

    in_range = species_range_mask()
    outside = land_mask() & ~in_range
    measured = in_range & typical_measured_mask()
    q = _by_type(albedo_grid.insolation_grid)
    darker = -100.0 * _by_type(albedo_grid.delta_alpha_grid)
    cloud, cloud_measured = cloud_brightening_grid()

    fig = plt.figure(figsize=(12.0, 5.6), dpi=FIG_DPI)
    panels = [
        (q, measured, "sonne", (100, 150, 200, 250), "[W/m²]", lambda v: f"{v:.0f} W/m²", "Einstrahlung", r"$\dot{q}_{\mathrm{ein}}$",
         "#a55500"),
        (darker, measured, "abdunkeln", (0, 5, 10, 15), "[%]", lambda v: f"{v:.0f} %", "Albedo-Kontrast", r"$\Delta\alpha_{\mathrm{B}}$",
         "#5c7200"),
        (cloud, cloud_measured, "wolken", (-1, 0, 1, 2, 3), "[%]", lambda v: f"{_pp(v)} %", "Reflexion durch Wolken",
         r"$\Delta\alpha_{\mathrm{W}}$", "#056fab"),
    ]
    for k, (field, ok, scale, ticks, unit, fmt, title, symbol, symbol_color) in enumerate(panels):
        ax = fig.add_axes((0.005 + k * 0.333, 0.16, 0.323, 0.73))
        cax = fig.add_axes((0.045 + k * 0.333, 0.085, 0.21, 0.028))
        _map_base(ax, outside, in_range & ~ok, SITES_CROP)
        sc = SCALES[scale]
        cmap, norm = scale_cmap(sc), scale_norm(sc)
        ax.pcolormesh(grid_lons(), grid_lats(), np.ma.masked_where(~ok, field), cmap=cmap, norm=norm,
                      shading="auto", zorder=3)
        _site_markers(ax, lambda s, f=field, fmt=fmt: fmt(f[site_cell(s)]))
        _title_with_symbol(ax, title, symbol, symbol_color)
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal",
                          extend="both")
        cb.outline.set_visible(False)
        cb.set_ticks(ticks)
        cax.text(1.04, 0.5, unit, transform=cax.transAxes, ha="left", va="center", fontsize=11, color=C_INK)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path


def albedo_ingredients_figure(out_path: str) -> str:
    """B8a: the two ingredients of the extra absorbed light, as two maps.

    Left: sunlight reaching the ground [W/m^2], annual mean. Right: how much
    darker the full-grown spruce is than the open land it replaces
    (-Delta_alpha, percentage points), annual mean -- large where snow lies
    under the open land. Same cells as the result map: locally measured only.
    The result map multiplies them month by month, not as these annual means.
    """
    _heading_font, body_font = _register_fonts()
    _style(body_font)

    in_range = species_range_mask()
    measured = in_range & typical_measured_mask()
    unmeasured = in_range & ~measured
    outside = land_mask() & ~in_range
    q = _by_type(albedo_grid.insolation_grid)
    darker = -100.0 * _by_type(albedo_grid.delta_alpha_grid)

    # the whole slide body (no takeaway under it): taller figure, the maps as large as their half allows
    fig = plt.figure(figsize=(12.0, 5.6), dpi=FIG_DPI)
    # each map names its symbol in the equation of the next slide, in that equation's colour
    panels = [
        (fig.add_axes((0.01, 0.16, 0.48, 0.73)), fig.add_axes((0.08, 0.085, 0.34, 0.028)), q, RAMP_SUN,
         (90.0, 260.0), "[W/m²]", "Einstrahlung an der Oberfläche",
         r"$\dot{q}_{\mathrm{ein}}$", "#a55500"),
        (fig.add_axes((0.51, 0.16, 0.48, 0.73)), fig.add_axes((0.58, 0.085, 0.34, 0.028)), darker, RAMP_SNOW,
         (0.0, 18.0), "[%]",
         "Albedo-Kontrast Wald gegen Offenland", r"$\Delta\alpha_{\mathrm{B}}$", "#5c7200"),
    ]
    units = {id(q): "W/m²", id(darker): "%"}
    for ax, cax, field, ramp, (lo, hi), label, title, symbol, symbol_color in panels:
        _map_base(ax, outside, unmeasured, SITES_VIEW)
        cmap = _ramp_cmap(ramp)
        norm = mcolors.Normalize(lo, hi)
        ax.pcolormesh(grid_lons(), grid_lats(), np.ma.masked_where(~measured, field), cmap=cmap, norm=norm,
                      shading="auto", zorder=3)
        _site_markers(ax, lambda s, f=field: f"{f[site_cell(s)]:.0f} {units[id(f)]}")
        _title_with_symbol(ax, title, symbol, symbol_color)
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal",
                          extend="both")
        cb.outline.set_visible(False)
        # the title names the quantity: the bar carries only its unit, to its right
        cax.text(1.03, 0.5, label, transform=cax.transAxes, ha="left", va="center", fontsize=11, color=C_INK)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path
