import numpy as np
import pytest

from nbs.grid import GRID_RESOLUTION_DEG, cell_area_m2, grid_lats, grid_lons
from nbs.constants import A_EARTH_M2


def test_grid_shape_is_half_degree_global():
    assert GRID_RESOLUTION_DEG == 0.5
    assert grid_lats().shape == (360,)
    assert grid_lons().shape == (720,)


def test_grid_cells_are_centres_not_edges():
    assert grid_lats()[0] == pytest.approx(89.75)
    assert grid_lats()[-1] == pytest.approx(-89.75)
    assert grid_lons()[0] == pytest.approx(-179.75)
    assert grid_lons()[-1] == pytest.approx(179.75)


def test_cell_areas_sum_to_the_earth_surface():
    """The whole potential calculation is an area-weighted sum, so a grid whose
    cells do not add up to the planet would bias every number downstream."""
    total = cell_area_m2().sum()
    assert total == pytest.approx(A_EARTH_M2, rel=1e-3)


def test_cell_area_shrinks_towards_the_poles():
    a = cell_area_m2()
    equator_row = int(np.argmin(np.abs(grid_lats())))
    assert a[equator_row, 0] > a[0, 0]
    assert a[equator_row, 0] > a[-1, 0]


def test_cell_area_is_constant_along_a_latitude_row():
    a = cell_area_m2()
    assert np.allclose(a[100, :], a[100, 0], rtol=1e-12)
