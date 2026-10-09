"""Tests for nbs.tree_paths: planting paths over time."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from nbs.tree_paths import BONN_RATE_GHA, delta_t, forcing, schedule

ROOT = Path(__file__).resolve().parents[1]


def test_schedule_plants_the_whole_area_at_the_stated_rate():
    f = schedule(0.39)
    assert abs(f.sum() - 1.0) < 1e-12
    full_years = np.flatnonzero(np.isclose(f, BONN_RATE_GHA / 0.39))
    assert full_years[0] == 0 and len(full_years) == int(0.39 // BONN_RATE_GHA)
    assert schedule(0.39, rate_gha=None)[0] == 1.0


def test_planting_everything_in_the_start_year_reproduces_the_area_slide():
    cached = json.loads((ROOT / "deck/chart_data/flaechen_zeitreihe.json").read_text())
    ref = np.array(cached["kuehlt"])[: len(delta_t("kuehlt", rate_gha=None))]
    assert np.allclose(delta_t("kuehlt", rate_gha=None), ref, rtol=1e-6, atol=1e-9)


def test_planting_at_the_bonn_rate_cools_less_early_than_planting_at_once():
    assert -delta_t("kuehlt")[24] < 0.6 * -delta_t("kuehlt", rate_gha=None)[24]


def test_managed_forest_keeps_more_cooling_with_the_timber_bound_than_released():
    bound, freed = -delta_t("forst")[-1], -delta_t("forst", release=True)[-1]
    assert bound > -delta_t("kuehlt")[-1] > freed > 0


def test_released_timber_is_emitted_at_felling_only():
    nee_b, rf_b, area_b = forcing("forst")
    nee_r, rf_r, area_r = forcing("forst", release=True)
    assert area_b == area_r and np.allclose(rf_b, rf_r)
    assert np.all(nee_r >= nee_b - 1e-12)          # releasing never removes more
