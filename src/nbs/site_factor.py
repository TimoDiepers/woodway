"""Location-dependent carbon gain: one factor per cell and forest type.

Since 2026-10-05 the carbon a forest adds at a location comes from Walker et
al. (2022): the constrained unrealized potential (AGB+BGB) over the
reforestable pixels of each 0.5-degree cell (nbs.forest_data). Each registry
entry (forest type x climate zone, nbs.species) carries the median of its
cells as m_max; this module returns, per cell, the cell's own value relative
to that median:

    m_max(cell) = m_max(key) * f(cell),    f(cell) = M(cell) / M_ref(key)

Only m_max scales -- k, p and the canopy-closure curve stay as they are --
so the CO2 channel scales exactly linearly with f, which keeps the
aggregation over cells (nbs.aggregate) exact.

This replaces the earlier latitude-only factor from forest-inventory
increments (all-species anchors DE/FI); see docs/methods/waldtypen.md.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.typing import NDArray

from nbs.grid import grid_lats, grid_lons


@lru_cache(maxsize=None)
def site_factor_grid(species_key: str) -> NDArray:
    """(360, 720) factor per cell (1 where the cell has no carbon value)."""
    from nbs.forest_data import carbon_gain_mgc_ha, growth_by_key

    g = growth_by_key().get(species_key)
    m = carbon_gain_mgc_ha()
    if not g or g["m_ref_mgc_ha"] <= 0:
        return np.ones(m.shape)
    return np.where(m > 0, m / g["m_ref_mgc_ha"], 1.0)


def site_factor(species_key: str, lat_deg: float, lon_deg: float | None = None) -> float:
    """Factor at a site: the cell's value relative to the key's median cell.
    Without a longitude there is no cell -- the key's median cell (f = 1),
    which is what the unit curves of nbs.aggregate are computed for."""
    if lon_deg is None:
        return 1.0
    grid = site_factor_grid(species_key)
    i = int(np.argmin(np.abs(grid_lats() - lat_deg)))
    return float(grid[i, int(np.argmin(np.abs(grid_lons() - lon_deg)))])
