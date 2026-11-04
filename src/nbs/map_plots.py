"""Grid maps for the results section of the talk (Plan 2, Task 6).

Three figures, all built from ``nbs.aggregate.unit_curves`` and
``nbs.albedo_grid.alpha_q_product`` -- never by re-running the single-tree
pipeline per cell, which would mean ~5700 plantable cells times a FaIR call
each:

- ``plot_breakeven_map``: per-cell break-even year t* (the primary figure --
  it alone carries the whole "warming fraction by year" table the task-6
  brief measured: 62.5% of plantable cells still warming in 2030, dropping to
  2.9% by 2125).
- ``plot_sign_map``: the discrete warming/cooling split at one year, default
  2050 -- the year the measured table puts the split closest to 50/50
  (45.5% warming), which is when the talk's "opposite signs" claim is most
  visibly true on a single map. A single-year map at, say, 2125 would show
  almost no warming and understate the point: not because the albedo channel
  is missing, but because by then it is long over.
- ``plot_horizon_field``: the continuous version of the same fact for one
  species -- net Delta_T(time, latitude), with the zero contour tracing
  t*(latitude) directly, the same quantity a discrete breakeven table lists
  year by year.

Every figure carries ``footer_text()`` in its own footer, not just a
docstring: it names both data provenances (the Duveiller albedo-transition
raster via ``nbs.albedo_grid.product_provenance`` and the latitude-band
species assignment via ``nbs.landscape.provenance``) and states the
three-tier retrieval fractions -- local retrieval, zonal extrapolation,
latitude-table fallback -- for the species the talk foregrounds (Picea
abies, 60-70N). A map that is nine-tenths not-directly-measured is still a
legitimate product, provided it says so where the number is shown, not only
in a source comment.

German labels (these are slide material); code and docstrings in English.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

from nbs.aggregate import co2_factor_grid, delta_t_at_year, unit_curves  # noqa: E402
from nbs.albedo_grid import (  # noqa: E402
    product_provenance,
    provenance_fractions,
)
from nbs.config import ModelConfig  # noqa: E402
from nbs.constants import T_END, T_START, YEARS, SZENARIO  # noqa: E402
from nbs.grid import grid_lats, grid_lons  # noqa: E402
from nbs.landscape import assign_species  # noqa: E402
from nbs.landscape import provenance as landscape_provenance  # noqa: E402
from nbs.light import light_product  # noqa: E402
from nbs.borders import CITATION as borders_citation  # noqa: E402
from nbs.borders import add_borders, borders_available  # noqa: E402
from nbs.landscape import land_mask, plantable_area_m2  # noqa: E402
from nbs.recommend import (  # noqa: E402
    MK_PER_MHA_PER_K_PER_HA,
    M2_PER_GHA,
    improvement,
    recommend,
    summary,
)
from nbs.species import SPECIES, get_species  # noqa: E402

DPI = 300
_FOOTER_SPECIES = "mf_gemaessigt"
"""Forest type whose three-tier albedo fractions footer_text() quotes: the
typical forest at Aachen, the talk's running example."""

_COLOR_WARM = "#b2182b"
_COLOR_COOL = "#2166ac"
_COLOR_NEVER = "#7a0421"
_COLOR_UNPLANTABLE = "#e5e5e5"
_COLOR_LAND = "#c9c9c9"
"""Land that exists but is not available (forest, cropland, savanna, ice)."""

TYPE_COLORS: dict[str, str] = {
    "enf": "#2a78d6",  # slot 1 blue   -- immergrüner Nadelwald
    "dbf": "#eb6834",  # slot 2 orange -- sommergrüner Laubwald
    "ebf": "#1baf7a",  # slot 3 aqua   -- immergrüner Laubwald
    "dnf": "#eda100",  # slot 4 yellow -- Lärchenwald
    "mf": "#e87ba4",   # slot 5 magenta -- Mischwald
}
"""One hue per forest type, the dataviz reference palette in fixed order
(passes the adjacent-pair CVD and normal-vision checks; maps carry a legend
with direct labels because five classes cannot pass all-pairs)."""

TYPE_NAMES: dict[str, str] = {
    "enf": "Immergrüner Nadelwald",
    "dbf": "Sommergrüner Laubwald",
    "ebf": "Immergrüner Laubwald",
    "dnf": "Lärchenwald",
    "mf": "Mischwald",
}


def forest_type(key: str) -> str:
    """'mf_gemaessigt' -> 'mf'."""
    return key.split("_")[0]


class _ByType(dict):
    """Colour lookup by registry key ('mf_boreal') or by type ('mf')."""

    def __missing__(self, key: str) -> str:
        return TYPE_COLORS[forest_type(key)]


_SPECIES_COLORS: dict[str, str] = _ByType()
"""Same colour for a forest type in every climate zone."""


def _save(fig, out_path: str) -> str:
    directory = os.path.dirname(out_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _de1(value: float) -> str:
    """One-decimal German number formatting, e.g. 48.2 -> '48,2'."""
    return f"{value:.1f}".replace(".", ",")


def _de2(value: float) -> str:
    """Two-decimal German number formatting, e.g. 0.9488 -> '0,95'.

    Gha totals need the second decimal: the whole plantable area rounds to
    "0,9 Gha" at one decimal, which loses the difference between 0.85 and
    0.95 -- a hundred million hectares.
    """
    return f"{value:.2f}".replace(".", ",")


def _de_pct(fraction: float) -> str:
    """Format a 0-1 fraction as a German-style percentage, e.g. 0.089 -> '8,9 %'."""
    return _de1(fraction * 100.0) + " %"


def _warming_cooling_pct(year: int, scenario: str) -> tuple[float, float]:
    """(warm_pct, cool_pct) over plantable cells only, 0-100, summing to 100.

    Plantability is read from nbs.landscape.assign_species(), not from
    "field != 0" -- an exact zero Delta_T is possible in principle and would
    otherwise be indistinguishable from an unplantable cell.
    """
    field = delta_t_at_year(year, scenario)
    plantable = assign_species() != None  # noqa: E711
    n_total = int(plantable.sum())
    if n_total == 0:
        return float("nan"), float("nan")
    warm_pct = 100.0 * int((plantable & (field > 0.0)).sum()) / n_total
    return warm_pct, 100.0 - warm_pct


def footer_text(species_key: str = _FOOTER_SPECIES) -> str:
    """Both data provenances, plus the named species' three-tier fractions.

    Composed as plain text so it can be asserted on directly (the plotting
    functions close their figure on save, leaving no live artist to
    interrogate afterwards) and so every figure in this module places the
    identical string, keeping the wording consistent across P1 and E6.
    """
    prod = product_provenance()
    land = landscape_provenance()
    frac = provenance_fractions(species_key)
    sp = get_species(species_key)
    return (
        f"Albedo-Rasterquelle (Duveiller et al. 2018, JRC v2.0): {prod}  |  "
        f"Flächen und Waldtypen: Walker et al. 2022, Hasler et al. 2024 ({land})  |  "
        f"{sp.name_de}: {_de_pct(frac['lokal'])} lokal erhoben, "
        f"{_de_pct(frac['zonal'])} zonal extrapoliert, "
        f"{_de_pct(frac['tabelle'])} Breitentabelle"
        + (f"  |  {borders_citation}" if borders_available() else "")
    )


def _add_footer(fig, species_key: str = _FOOTER_SPECIES) -> None:
    """Place footer_text() as an unmissable, boxed strip under the axes.

    A hairline caption is easy to skip; a coloured box spanning the figure
    width is not. fig.text (not ax.text) so it survives independent of
    whichever axes the caller built, and bbox_inches="tight" in _save()
    still picks it up because it is a figure-level artist.
    """
    fig.text(
        0.5,
        -0.02,
        footer_text(species_key),
        ha="center",
        va="top",
        fontsize=9.5,
        wrap=True,
        transform=fig.transFigure,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#fff3cd", edgecolor="#8a6d3b", linewidth=1.0),
    )


def _lat_formatter(deg: float, _pos=None) -> str:
    if deg == 0:
        return "0°"
    hemi = "N" if deg > 0 else "S"
    return f"{abs(deg):.0f}°{hemi}"


def _lon_formatter(deg: float, _pos=None) -> str:
    if deg == 0:
        return "0°"
    hemi = "O" if deg > 0 else "W"
    return f"{abs(deg):.0f}°{hemi}"


def _add_lat_lon_grid(ax) -> None:
    """Plain-equirectangular graticule, coastlines and national borders.

    No cartopy: the fields are drawn in raw lon/lat, so Natural Earth's
    1:110m line strings plot directly in the same coordinates (see
    ``nbs.borders``). Borders go on before the limits are fixed, so the
    LineCollection can never autoscale the axes out of the -180..180 /
    -90..90 frame.

    An earlier version deliberately left coastlines off ("the message is the
    pattern by latitude"). That was wrong for a talk: without a coastline a
    viewer cannot tell Siberia from the North Pacific, and the boreal
    argument lives on exactly that distinction.
    """
    add_borders(ax)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(-90, 91, 30))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_lon_formatter))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_lat_formatter))
    ax.set_aspect("equal")
    ax.grid(True, color="0.5", alpha=0.35, linewidth=0.6)
    ax.set_xlabel("Länge")
    ax.set_ylabel("Breite")


def _t_star_batch(traj: NDArray, years: NDArray) -> NDArray:
    """Vectorised nbs.metrics.t_star over the leading axis of *traj*.

    traj: (n_cells, n_years). Returns (n_cells,) break-even years, with the
    identical semantics as the scalar t_star: years[0] if never warming,
    np.inf if the last warming year is the final one in the horizon, else the
    year right after the last sign change.
    """
    warming = traj > 0.0
    n_years = traj.shape[1]
    any_warm = warming.any(axis=1)
    idx_from_end = np.argmax(warming[:, ::-1], axis=1)
    last_idx = n_years - 1 - idx_from_end

    out = np.full(traj.shape[0], float(years[0]))
    still_warming_at_end = any_warm & (last_idx == n_years - 1)
    recovers = any_warm & (last_idx < n_years - 1)
    out[still_warming_at_end] = np.inf
    out[recovers] = years[last_idx[recovers] + 1]
    return out


def _breakeven_year_field(scenario: str = SZENARIO, config: ModelConfig | None = None) -> NDArray:
    """(360, 720) break-even year t* per cell, NaN where unplantable.

    Built from unit_curves (two curves per species, five species total) and
    each cell's own alpha_q_product -- ten convolutions' worth of trajectory
    shape, reused across every plantable cell of that species, exactly the
    same shortcut nbs.aggregate uses for Delta_T itself. A cell's tree count
    N_c is strictly positive wherever a species is assigned, so it never
    changes the sign of (co2(t) + P_c * albedo_unit(t)) and is left out of
    this per-cell trajectory on purpose -- t* only depends on sign.
    """
    species_grid = assign_species()
    field = np.full(species_grid.shape, np.nan, dtype=float)
    for key in SPECIES:
        mask = species_grid == key
        if not mask.any():
            continue
        co2, albedo_unit = unit_curves(key, scenario, config)
        p = light_product(key)[mask]
        f = co2_factor_grid(key, config)[mask]
        traj = f[:, None] * co2[None, :] + p[:, None] * albedo_unit[None, :]
        field[mask] = _t_star_batch(traj, YEARS)
    return field


def plot_breakeven_map(out_path: str, *, scenario: str = SZENARIO) -> str:
    """Folie P1 (primary): per-cell break-even year t*, one still that
    carries the whole warming-fraction-by-year table (task-6 brief): 62.5%
    of plantable cells still warming in 2030, 49.2% in 2040, 45.5% in 2050,
    24.7% in 2060, 1.7% in 2080, 2.9% in 2125. Early break-even years read
    bright, late ones dark, and cells that never break even within the
    2025-2100 horizon get their own distinct colour rather than being folded
    into the "late" end of the scale, which would silently equate "took 120
    years" with "never".
    """
    field = _breakeven_year_field(scenario)
    lats, lons = grid_lats(), grid_lons()

    # Anchor years for the title's summary line: the same two years the
    # task-6 brief's warming-fraction table uses to bracket the transient
    # decades (62.5% -> 2.9% under the default ssp245), recomputed here (not
    # hardcoded) so the number stays correct if a caller passes a different
    # scenario.
    _start_year, _end_year = 2030, T_END
    _warm_start, _ = _warming_cooling_pct(_start_year, scenario)
    _warm_end, _ = _warming_cooling_pct(_end_year, scenario)

    cmap = plt.get_cmap("viridis_r").copy()
    cmap.set_bad(_COLOR_UNPLANTABLE)
    cmap.set_over(_COLOR_NEVER)
    norm = mcolors.Normalize(vmin=T_START, vmax=T_END)

    fig, ax = plt.subplots(figsize=(12, 6.8))
    im = ax.pcolormesh(
        lons, lats, np.ma.masked_invalid(field), cmap=cmap, norm=norm, shading="auto"
    )
    cbar = fig.colorbar(im, ax=ax, extend="max", pad=0.02, shrink=0.85)
    cbar.set_label("Ausgleichsjahr t* [Jahr]")

    legend_handles = [
        Patch(facecolor=_COLOR_NEVER, label=f"kein Ausgleich bis {T_END}"),
        Patch(facecolor=_COLOR_UNPLANTABLE, label="nicht bepflanzbar"),
    ]
    ax.legend(handles=legend_handles, loc="lower left", frameon=True, fontsize=9)

    _add_lat_lon_grid(ax)
    ax.set_title(
        f"Ausgleichsjahr t* je Rasterzelle, {scenario.upper()}\n"
        f"wärmend {_start_year} : {_de1(_warm_start)} %  →  "
        f"wärmend {_end_year} : {_de1(_warm_end)} %"
    )
    _add_footer(fig)
    return _save(fig, out_path)


def plot_sign_map(
    year: int = 2050, out_path: str = "sign_map.png", *, scenario: str = SZENARIO
) -> str:
    """Folie P1b: discrete warming/cooling split at one year.

    Defaults to 2050 (not the horizon end): the measured warming-cell
    fraction is 62.5% in 2030, 49.2% in 2040, 45.5% in 2050, 24.7% in 2060,
    1.7% in 2080 and 2.9% in 2125 (task-6 brief) -- by 2125 the map would be
    almost entirely one colour, which is correct but makes a single still
    understate the "opposite signs" claim the talk makes about the transient
    decades. 2050 is closest to an even split (48/52) and keeps the argument
    legible in a single frame; plot_breakeven_map carries the full
    across-year picture this figure necessarily reduces to one year.

    Plantability is read from nbs.landscape.assign_species(), not from
    "field != 0" -- an exact zero Delta_T is possible in principle and would
    otherwise be indistinguishable from an unplantable cell.
    """
    field = delta_t_at_year(year, scenario)
    plantable = assign_species() != None  # noqa: E711
    warm = plantable & (field > 0.0)
    cool = plantable & ~(field > 0.0)

    warm_pct, cool_pct = _warming_cooling_pct(year, scenario)

    sign = np.full(field.shape, np.nan)
    sign[cool] = -1.0
    sign[warm] = 1.0

    lats, lons = grid_lats(), grid_lons()
    cmap = mcolors.ListedColormap([_COLOR_COOL, _COLOR_WARM])
    cmap.set_bad(_COLOR_UNPLANTABLE)
    norm = mcolors.BoundaryNorm([-1.5, 0.0, 1.5], cmap.N)

    fig, ax = plt.subplots(figsize=(12, 6.8))
    ax.pcolormesh(lons, lats, np.ma.masked_invalid(sign), cmap=cmap, norm=norm, shading="auto")

    legend_handles = [
        Patch(facecolor=_COLOR_COOL, label="kühlend (ΔT ≤ 0)"),
        Patch(facecolor=_COLOR_WARM, label="wärmend (ΔT > 0)"),
        Patch(facecolor=_COLOR_UNPLANTABLE, label="nicht bepflanzbar"),
    ]
    ax.legend(handles=legend_handles, loc="lower left", frameon=True, fontsize=9)

    _add_lat_lon_grid(ax)
    ax.set_title(
        f"Vorzeichen von ΔT({year}) je Rasterzelle, {scenario.upper()}\n"
        f"wärmend: {_de1(warm_pct)} %  ·  kühlend: {_de1(cool_pct)} %"
    )
    _add_footer(fig)
    return _save(fig, out_path)


def plot_horizon_field(out_path: str, *, species_key: str, scenario: str = SZENARIO) -> str:
    """Folie E6: continuous horizon x latitude field of net Delta_T per tree.

    **This is a counterfactual sweep**, and the figure says so: it puts the
    *same* species at every latitude, including latitudes it would never be
    planted at. ``nbs.landscape`` assigns enf_boreal to 60-70 degrees only;
    the shaded band marks that range so the rest is read as "what if", not as
    a recommendation. Outside it the Delta_alpha values are the three-tier
    fill's zonal extrapolation of a transition that was never retrieved
    there, and at 20S in particular that produces the largest albedo penalty
    on the whole figure -- a real consequence of high subtropical insolation
    times an extrapolated albedo contrast, not a measurement.

    x: study year (2025-2100, the model's own annual resolution -- the
    "continuous" axis the brief asks for, as opposed to the handful of
    support years plot_breakeven_map and plot_sign_map single out).
    y: latitude, zonal-mean alpha_q_product per row for *species_key*,
    **averaged over that row's land cells only**. Averaging over the whole
    row instead mixes in ~80% ocean, where the fill still supplies a value
    and nothing is ever planted; that version put a spurious zero contour
    through the southern ocean. Rows with no land at all are left blank
    rather than filled.
    colour: net Delta_T per tree [K] (co2 + albedo channel), diverging
    around zero.

    The white zero contour is not a decoration: it *is* t*(latitude) for
    this species, drawn as a continuous curve instead of read off a table of
    discrete years -- the same sign change nbs.metrics.t_star locates on a
    single trajectory, here traced across every latitude row at once. A
    thin black stroke is added beneath the white line (matplotlib
    path_effects) so it stays legible in both the pale centre of the RdBu_r
    colourmap and its saturated ends.
    """
    co2, albedo_unit = unit_curves(species_key, scenario)
    lats = grid_lats()
    land = land_mask()
    n_land = land.sum(axis=1)
    product = light_product(species_key)
    zonal_product = np.where(
        n_land > 0, (product * land).sum(axis=1) / np.maximum(n_land, 1), np.nan
    )  # (360,)

    f_rows = co2_factor_grid(species_key)[:, 0]  # depends on latitude only
    field_k = f_rows[:, None] * co2[None, :] + zonal_product[:, None] * albedo_unit[None, :]  # (360, 126) K
    field = np.ma.masked_invalid(field_k * 1e15)  # 1e-15 K per tree, as nbs.plots

    vmax = float(np.max(np.abs(field)))
    norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)

    fig, ax = plt.subplots(figsize=(11, 6.8))
    im = ax.pcolormesh(YEARS, lats, field, cmap="RdBu_r", norm=norm, shading="auto")
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Netto ΔT je Baum [10$^{-15}$ K]")

    band = _assignment_band(species_key)
    if band is not None:
        lo_lat, hi_lat = band
        ax.axhspan(lo_lat, hi_lat, color="0.15", alpha=0.10, zorder=1, linewidth=0)
        ax.axhline(lo_lat, color="0.15", linewidth=0.8, linestyle="--", zorder=6)
        ax.axhline(hi_lat, color="0.15", linewidth=0.8, linestyle="--", zorder=6)

    cs = ax.contour(YEARS, lats, field, levels=[0.0], colors="white", linewidths=2.4, zorder=5)
    cs.set_path_effects([pe.Stroke(linewidth=4.0, foreground="black"), pe.Normal()])

    band_proxy = (
        Patch(facecolor="0.15", alpha=0.10, label="tatsächlich zugewiesenes Gebiet")
        if band is not None
        else None
    )
    zero_line_proxy = Line2D(
        [0], [0], color="white", lw=2.4,
        path_effects=[pe.Stroke(linewidth=4.0, foreground="black"), pe.Normal()],
        label="t*(Breite) — Nullkontur",
    )
    handles = [zero_line_proxy] + ([band_proxy] if band_proxy is not None else [])
    ax.legend(handles=handles, loc="upper right", frameon=True, fontsize=9)

    sp = get_species(species_key)
    ax.set_title(
        f"Horizontfeld: Netto ΔT je Baum, {sp.name_de} ({sp.name_lat}), "
        f"{scenario.upper()}\nGedankenexperiment: dieselbe Art auf jeder Breite, "
        f"Zonalmittel nur über Landzellen"
    )
    ax.set_xlabel("Jahr")
    ax.set_ylabel("Breite")
    ax.set_ylim(-90, 90)
    ax.set_yticks(np.arange(-90, 91, 30))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_lat_formatter))
    ax.grid(alpha=0.2, color="0.4", linewidth=0.6)
    _add_footer(fig, species_key)
    return _save(fig, out_path)


def _blocks(field: NDArray, factor: int) -> NDArray:
    """Reshape a (360, 720) grid into (360/f, 720/f, f*f) blocks.

    Display-only aggregation. The plantable/excluded split inside a latitude
    row is a synthetic per-row permutation (see nbs.landscape) and therefore
    scatters single plantable cells across the row; at 0.5 degrees that reads
    as noise. Binning to whole blocks turns it into the quantity the split
    actually carries -- the per-row *count* -- while keeping continents
    recognisable. It changes no number: every total in the legend is summed
    from the unbinned grid.
    """
    n_lat, n_lon = field.shape
    return (
        field.reshape(n_lat // factor, factor, n_lon // factor, factor)
        .transpose(0, 2, 1, 3)
        .reshape(n_lat // factor, n_lon // factor, factor * factor)
    )


def _assignment_band(species_key: str) -> tuple[float, float] | None:
    """Signed latitude range where this species actually has plantable cells.

    Not the ``nbs.landscape._BAND_SPECIES`` band itself: that band is stated
    in *absolute* latitude and so nominally covers both hemispheres, but the
    land mask leaves a species with no cells at all in one of them (there is
    no land at 60-70S). Deriving the range from ``assign_species()`` instead
    of from the band table means the shaded strip marks where trees of this
    species really stand, and never a southern band the model never fills.
    """
    from nbs.landscape import assign_species

    rows = np.flatnonzero((assign_species() == species_key).any(axis=1))
    if rows.size == 0:
        return None
    lats = grid_lats()
    return float(lats[rows].min()), float(lats[rows].max())


def plot_planting_map(
    out_path: str,
    *,
    year: int = 2100,
    scenario: str = SZENARIO,
    block_deg: float = 2.0,
) -> str:
    """Folie P: available afforestation area, and what belongs on it.

    Hue is the recommended species (``nbs.recommend.recommend`` -- the
    admissible species with the most cooling per hectare at *year*, not the
    latitude band's default). Saturation is how much of the block is actually
    available: a fully saturated block is entirely plantable, a pale one has
    a few free hectares in an otherwise forested, farmed or frozen
    neighbourhood. Grey is land with nothing available.

    The right-hand bars carry the numbers the map cannot: available area per
    recommended species [Gha], with the latitude-band assignment behind it as
    a hollow bar, so the difference between "what a band model plants" and
    "what cools most" is visible as area, not just as hue.
    """
    ratio = block_deg / 0.5
    factor = int(round(ratio))
    if abs(ratio - factor) > 1e-9 or factor < 1 or 360 % factor or 720 % factor:
        raise ValueError(f"block_deg={block_deg} teilt das 0,5°-Raster nicht auf")

    rec = recommend(year, scenario)
    stats = summary(year, scenario)
    gain = improvement(year, scenario)

    area = plantable_area_m2()
    cell_total = np.where(land_mask(), 1.0, 0.0)

    area_blocks = _blocks(area, factor)
    land_blocks = _blocks(cell_total, factor)
    keys = list(SPECIES)
    key_idx = np.full(area.shape, -1, dtype=int)
    for i, k in enumerate(keys):
        key_idx[rec.species == k] = i
    idx_blocks = _blocks(key_idx, factor)

    n_lat_b, n_lon_b, _ = area_blocks.shape
    rgba = np.zeros((n_lat_b, n_lon_b, 4))
    block_area = area_blocks.sum(axis=2)
    max_area = block_area.max()

    for i in range(n_lat_b):
        for j in range(n_lon_b):
            has_land = land_blocks[i, j].sum() > 0
            if not has_land:
                continue
            if block_area[i, j] <= 0.0:
                rgba[i, j] = mcolors.to_rgba(_COLOR_LAND, alpha=1.0)
                continue
            # Dominant recommendation by available area, not by cell count:
            # a block's colour should answer "most of the free hectares here
            # want which species", which is the planting decision.
            weights = np.zeros(len(keys))
            for s_i in range(len(keys)):
                sel = idx_blocks[i, j] == s_i
                weights[s_i] = area_blocks[i, j][sel].sum()
            dominant = keys[int(np.argmax(weights))]
            share = float(block_area[i, j] / max_area)
            rgb = np.array(mcolors.to_rgb(_SPECIES_COLORS[dominant]))
            # Blend towards the land grey by availability rather than using
            # alpha: alpha over a white canvas would wash out to white and
            # read as "no land", which is a different statement.
            base = np.array(mcolors.to_rgb(_COLOR_LAND))
            rgba[i, j, :3] = base + (rgb - base) * (0.25 + 0.75 * share)
            rgba[i, j, 3] = 1.0

    fig, (ax, ax_bar) = plt.subplots(
        1, 2, figsize=(16.0, 5.0), gridspec_kw={"width_ratios": [3.3, 1.0]}
    )
    ax.imshow(rgba, extent=(-180, 180, -90, 90), origin="upper", interpolation="nearest")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    _add_lat_lon_grid(ax)

    total_gha = float(area.sum() / M2_PER_GHA)
    legend_handles = [
        Patch(facecolor=_SPECIES_COLORS[k], label=get_species(k).name_de)
        for k in keys
        if stats[k]["flaeche_gha"] > 0.0
    ]
    legend_handles.append(Patch(facecolor=_COLOR_LAND, label="Land, nichts verfügbar"))
    ax.legend(handles=legend_handles, loc="lower left", frameon=True, fontsize=8.5)
    ax.set_title(
        f"Verfügbare Fläche: {_de2(total_gha)} Gha  ·  "
        f"empfohlene Art (stärkste Kühlung je Hektar bis {year})\n"
        f"Farbsättigung = verfügbarer Anteil der {_de1(block_deg)}°-Zelle"
    )

    order = sorted(keys, key=lambda k: -stats[k]["flaeche_gha"])
    y = np.arange(len(order))
    ax_bar.barh(
        y,
        [stats[k]["flaeche_gha"] for k in order],
        color=[_SPECIES_COLORS[k] for k in order],
        height=0.62,
        label="empfohlen",
    )
    ax_bar.barh(
        y,
        [stats[k]["flaeche_zugewiesen_gha"] for k in order],
        height=0.62,
        facecolor="none",
        edgecolor="0.25",
        linestyle="--",
        linewidth=1.2,
        label="Breitenband-Zuordnung",
    )
    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels([])
    # Names inside the panel rather than on the axis: the German species names
    # are long enough that left-hand tick labels reach into the map.
    for pos, key in zip(y, order):
        ax_bar.text(
            0.012,
            pos - 0.42,
            get_species(key).name_de,
            fontsize=8.5,
            va="bottom",
            ha="left",
        )
    ax_bar.invert_yaxis()
    # The two bar styles are named in the axis label, not in a legend box:
    # wherever the box went it covered one of the five rows.
    ax_bar.set_xlabel(
        "verfügbare Fläche [Gha]\nvoll: empfohlen  ·  gestrichelt: Breitenband"
    )
    ax_bar.grid(axis="x", alpha=0.3)
    ax_bar.set_title(
        "Artenwahl statt Breitenband:\n"
        f"{_de1(gain['gewinn_anteil'] * 100)} % mehr "
        f"Kühlung in {year}",
        fontsize=10,
    )

    _add_footer(fig)
    return _save(fig, out_path)


__all__ = [
    "footer_text",
    "plot_breakeven_map",
    "plot_horizon_field",
    "plot_planting_map",
    "plot_sign_map",
]
