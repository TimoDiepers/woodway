"""Coastlines and national borders for the grid maps.

Every map in this package draws a 0.5-degree field in plain
longitude/latitude (an equirectangular projection with no further
transformation), so an overlay only has to be plotted in the same
coordinates -- no projection library, no runtime download. Natural Earth's
1:110m coastline and land boundary lines are committed under ``data/borders/``
as GeoJSON for exactly that reason: they are ~0.5 MB together, public domain,
and a figure that silently loses its coastlines on a fresh checkout is worse
than a slightly larger repository.

``add_borders(ax)`` is the only function callers need. It is a no-op with a
clear return value when the files are missing, so a map still renders (and
``borders_available()`` lets the figure say so) rather than raising in the
middle of a plotting run.

Antimeridian: Natural Earth's line strings are already split at +/-180, so no
segment wraps the globe. Segments are still clipped defensively -- a single
unsplit feature would otherwise draw a horizontal line straight across the
map, which is the classic failure mode of hand-rolled coastline plotting.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from matplotlib.collections import LineCollection

BORDER_DIR = Path(__file__).resolve().parents[2] / "data" / "borders"

_FILES = {
    "coastline": "ne_110m_coastline.geojson",
    "countries": "ne_110m_admin_0_boundary_lines_land.geojson",
}

CITATION = "Grenzen: Natural Earth 1:110m (public domain)"

_COLOR_COAST = "#333333"
_COLOR_COUNTRY = "#666666"


def _segments(path: Path) -> list[np.ndarray]:
    """Every LineString in a GeoJSON file as an (N, 2) lon/lat array."""
    data = json.loads(path.read_text())
    out: list[np.ndarray] = []
    for feature in data["features"]:
        geom = feature.get("geometry") or {}
        kind = geom.get("type")
        if kind == "LineString":
            parts = [geom["coordinates"]]
        elif kind == "MultiLineString":
            parts = geom["coordinates"]
        else:
            continue
        for part in parts:
            arr = np.asarray(part, dtype=float)
            if arr.ndim != 2 or arr.shape[0] < 2:
                continue
            # Split anywhere two consecutive vertices jump more than half the
            # globe in longitude: that is a wrap, not a real line.
            breaks = np.flatnonzero(np.abs(np.diff(arr[:, 0])) > 180.0) + 1
            for chunk in np.split(arr, breaks):
                if chunk.shape[0] >= 2:
                    out.append(chunk)
    return out


@lru_cache(maxsize=1)
def _load() -> dict[str, list[np.ndarray]]:
    out: dict[str, list[np.ndarray]] = {}
    for key, name in _FILES.items():
        path = BORDER_DIR / name
        out[key] = _segments(path) if path.exists() else []
    return out


def borders_available() -> bool:
    """True when both overlay files are on disk and non-empty."""
    loaded = _load()
    return all(loaded[key] for key in _FILES)


def add_borders(
    ax,
    *,
    coastline: bool = True,
    countries: bool = True,
    linewidth: float = 0.45,
    alpha: float = 0.85,
) -> bool:
    """Draw coastlines and national borders on a lon/lat axes.

    Returns True if anything was drawn. Country borders are thinner and
    lighter than coastlines so the land/sea edge stays the dominant line --
    on a global map at slide size, equally weighted borders turn Europe into
    a grey smudge.

    The overlay is drawn above the field (high zorder) but never changes the
    axes limits, so a caller that has already set its own extent keeps it.
    """
    loaded = _load()
    drawn = False
    if coastline and loaded["coastline"]:
        ax.add_collection(
            LineCollection(
                loaded["coastline"],
                colors=_COLOR_COAST,
                linewidths=linewidth * 1.6,
                alpha=alpha,
                zorder=5,
            )
        )
        drawn = True
    if countries and loaded["countries"]:
        ax.add_collection(
            LineCollection(
                loaded["countries"],
                colors=_COLOR_COUNTRY,
                linewidths=linewidth,
                alpha=alpha * 0.8,
                zorder=4,
            )
        )
        drawn = True
    return drawn


__all__ = ["BORDER_DIR", "CITATION", "add_borders", "borders_available"]
