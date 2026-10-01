"""Tests for nbs.animations: the data behind the looping Bäume-chapter maps.

The video encoding itself is not tested here; the poster smoke tests check
that every frame-drawing path runs and writes a file.
"""

from __future__ import annotations

import numpy as np
import pytest

from nbs import albedo_grid
from nbs.animations import (
    SITES,
    albedo_annual_map_figure,
    albedo_map_animation,
    carbon_curve_figure,
    albedo_watts_monthly,
    carbon_map_animation,
    cumulative_uptake_kg_co2,
    interpolate_frames,
    site_cell,
    species_range_mask,
)
from nbs.constants import YEARS
from nbs.species import get_species


def test_both_sites_lie_inside_the_spruce_range():
    mask = species_range_mask()
    for s in SITES:
        assert mask[site_cell(s)], f"{s.name} liegt nicht im Fichtengebiet"


def test_cumulative_uptake_is_on_the_study_axis_and_ends_positive():
    u = cumulative_uptake_kg_co2()
    assert u.shape == YEARS.shape
    assert u[-1] > 0.0


def test_shell_one_uptake_ignores_warming_feedback():
    """Shell 1 has no climate yet: the curve must not depend on background T,
    so it differs from the full model's (which raises the disturbance rate)."""
    from nbs.pipeline import run_single_tree
    from nbs.constants import M_CO2_PER_C

    full = M_CO2_PER_C * np.cumsum(run_single_tree("picea_abies", 60.0).trajectory.net_uptake_kgC_yr)
    assert cumulative_uptake_kg_co2()[-1] > full[-1]


def test_interpolated_frames_hit_each_month_and_wrap_to_january():
    monthly = np.arange(12.0)[:, None, None] * np.ones((12, 2, 2))
    frames = interpolate_frames(monthly, steps_per_month=4)
    assert frames.shape == (48, 2, 2)
    assert np.allclose(frames[::4], monthly)
    # last in-between frame runs from December (11) back towards January (0)
    assert frames[-1, 0, 0] == pytest.approx(11.0 * 0.25)


def test_albedo_watts_are_the_unsmoothed_monthly_product_per_tree():
    watts, measured = albedo_watts_monthly()
    area = get_species("picea_abies").stand_area_m2
    assert np.allclose(watts, -albedo_grid.monthly_product("picea_abies") * area)
    assert measured.dtype == bool and measured.any()


def test_annual_mean_at_the_sites_matches_the_storyline_numbers():
    """Aachen 43.6 W, Archangelsk 65.3 W -- the values quoted in the storyline."""
    watts, _ = albedo_watts_monthly()
    expected = {"Aachen": 43.6, "Archangelsk": 65.3}
    for s in SITES:
        assert watts[(slice(None), *site_cell(s))].mean() == pytest.approx(expected[s.name], abs=0.05)


@pytest.mark.slow
def test_posters_render(tmp_path):
    c = tmp_path / "c.png"
    a = tmp_path / "a.png"
    carbon_map_animation(str(tmp_path / "c.mp4"), poster_path=str(c), poster_only=True)
    albedo_map_animation(str(tmp_path / "a.mp4"), poster_path=str(a), poster_only=True)
    assert c.stat().st_size > 10_000 and a.stat().st_size > 10_000


def test_static_figures_render(tmp_path):
    b6 = carbon_curve_figure(str(tmp_path / "b6.png"))
    b8 = albedo_annual_map_figure(str(tmp_path / "b8.png"))
    for path in (b6, b8):
        assert (tmp_path / path.split("/")[-1]).stat().st_size > 10_000
