"""Net extra light per forest: darker canopy (albedo) plus more low clouds.

light_product = alpha_q_product + cloud_q_product [W/m^2]; negative means the
forest makes the Earth absorb more light (warming). Every forcing, map and
aggregate reads this, so the cloud effect enters the whole model in one place.
NBS_CLOUDS=0 in the environment switches the clouds off (the model before
2026-10-14, backup "ohne Wolken").
"""

from __future__ import annotations

import os

from numpy.typing import NDArray

from nbs.albedo_grid import alpha_q_product, monthly_product
from nbs.cloud_grid import cloud_q_product, monthly_cloud_product


def clouds_enabled() -> bool:
    return os.environ.get("NBS_CLOUDS", "1") != "0"


def light_product(species_key: str, *, clouds: bool | None = None) -> NDArray:
    """(360, 720) W/m^2 net light product of the forest type."""
    p = alpha_q_product(species_key)
    return p + cloud_q_product(species_key) if (clouds_enabled() if clouds is None else clouds) else p


def monthly_light_product(species_key: str, *, clouds: bool | None = None) -> NDArray:
    """(12, 360, 720) W/m^2, monthly net light product."""
    p = monthly_product(species_key)
    return p + monthly_cloud_product(species_key) if (clouds_enabled() if clouds is None else clouds) else p
