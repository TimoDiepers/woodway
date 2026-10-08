"""Tests for nbs.dac_storage (Gidden et al. 2025 storage per country, basin proximity per cell)."""

import numpy as np
import pytest

from nbs.dac_storage import iso3_grid, region_by_country, storage_by_country, storage_mask
from nbs.grid import grid_lats, grid_lons


def _at(field, lat, lon):
    return field[np.argmin(abs(grid_lats() - lat)), np.argmin(abs(grid_lons() - lon))]


def test_world_total_matches_gidden():
    s = storage_by_country("prudent")
    assert sum(s.values()) == pytest.approx(1460, abs=2)


def test_known_countries():
    s = storage_by_country("prudent")
    assert s["DEU"] == pytest.approx(1.3, abs=0.1)
    assert s["RUS"] == pytest.approx(244, abs=1)
    assert s.get("CHE", 0.0) == 0.0


def test_no_phantom_rows():
    s = storage_by_country("prudent")
    assert all(len(k) == 3 and k.isupper() for k in s)
    assert "Total" not in s and "Final Total" not in s


def test_levels_are_ordered():
    p, t = storage_by_country("prudent"), storage_by_country("technisch")
    assert all(t[k] >= p[k] - 1e-9 for k in p)


def test_regions_cover_storage_countries():
    r = region_by_country()
    assert all(k in r for k, v in storage_by_country("prudent").items() if v > 0)


def test_mask_near_basins():
    m = storage_mask()
    assert m.shape == (360, 720) and m.dtype == bool
    assert _at(m, 53.5, 8.0)          # North German Basin / North Sea coast
    assert not _at(m, 72.0, -40.0)    # central Greenland ice sheet: no basin within 100 km
    assert 0.2 < m.mean() < 0.8


def test_iso3_grid_matches_known_places():
    g = iso3_grid()
    assert _at(g, 51.0, 10.0) == "DEU"
    assert _at(g, 60.0, 90.0) == "RUS"
    assert _at(g, 0.0, -30.0) == ""
