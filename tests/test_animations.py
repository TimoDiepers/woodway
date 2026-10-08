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
    site_key,
    site_uptake_kg_co2,
    interpolate_frames,
    site_cell,
    species_range_mask,
)
from nbs.constants import YEARS
from nbs.species import get_species


def test_both_sites_lie_on_reforestable_cells_with_a_typical_forest():
    mask = species_range_mask()
    for s in SITES:
        assert mask[site_cell(s)], f"{s.name}: keine wiederbewaldbare Zelle mit Waldtyp"
        assert site_key(s).startswith("mf_"), f"{s.name}: typischer Wald ist {site_key(s)}"


def test_cumulative_uptake_is_on_the_study_axis_and_ends_positive():
    for s in SITES:
        u = site_uptake_kg_co2(s)
        assert u.shape == YEARS.shape
        assert u[-1] > 0.0


def test_shell_one_uptake_ignores_warming_feedback():
    """Shell 1 has no climate yet: the curve must not depend on background T,
    so it differs from the full model's (which raises the disturbance rate)."""
    from nbs.constants import M_CO2_PER_C
    from nbs.pipeline import run_single_tree

    s = SITES[0]
    full = run_single_tree(site_key(s), s.lat, lon_deg=s.lon).trajectory.net_uptake_kgC_yr
    assert not np.allclose(site_uptake_kg_co2(s), M_CO2_PER_C * np.cumsum(full))


def test_interpolated_frames_hit_each_month_and_wrap_to_january():
    monthly = np.arange(12.0)[:, None, None] * np.ones((12, 2, 2))
    frames = interpolate_frames(monthly, steps_per_month=4)
    assert frames.shape == (48, 2, 2)
    assert np.allclose(frames[::4], monthly)
    # last in-between frame runs from December (11) back towards January (0)
    assert frames[-1, 0, 0] == pytest.approx(11.0 * 0.25)


def test_albedo_watts_are_the_unsmoothed_monthly_product_per_tree():
    """Each cell with its typical forest type: at the sites, the monthly product
    of that type times the stand area, unsmoothed."""
    watts, measured = albedo_watts_monthly()
    for s in SITES:
        key = site_key(s)
        cell = (slice(None), *site_cell(s))
        expected = -albedo_grid.monthly_product(key)[cell] * get_species(key).stand_area_m2
        assert np.allclose(watts[cell], expected)
    assert measured.dtype == bool and measured.any()


def test_annual_mean_at_the_sites_matches_the_storyline_numbers():
    """Annual means quoted on the albedo slide (fakten.json, baeume.orte.*.licht_w)."""
    import json
    from pathlib import Path

    facts = json.loads((Path(__file__).resolve().parents[1] / "docs/slides/chart_data/fakten.json").read_text())
    watts, _ = albedo_watts_monthly()
    for s in SITES:
        expected = facts["baeume"]["orte"][s.name]["licht_w"]
        assert watts[(slice(None), *site_cell(s))].mean() == pytest.approx(expected, rel=1e-6)


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
