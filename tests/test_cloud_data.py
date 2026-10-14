"""The prepared Duveiller (2021) cloud file: grid, orientation, site values."""

from pathlib import Path

import numpy as np
import pytest

F = Path(__file__).resolve().parents[1] / "data" / "clouds" / "duveiller2021_dcfc_1deg.npz"


@pytest.fixture(scope="module")
def d():
    return np.load(F)


def test_grid_is_the_duveiller_2018_one_degree_grid(d):
    assert d["lat"][0] == 89.5 and d["lat"][-1] == -89.5
    assert d["lon"][0] == -179.5 and d["lon"][-1] == 179.5
    assert d["EFO"].shape == d["DFO"].shape == (12, 180, 360)


def test_values_are_absolute_fractions(d):
    for t in ("EFO", "DFO"):
        v = d[t][np.isfinite(d[t])]
        assert 0.02 < np.isfinite(d[t]).mean() < 0.3      # sparse: only co-occurrence cells
        assert -0.3 < v.min() and v.max() < 0.3


def test_aachen_summer_more_clouds_over_forest(d):
    i, j = int(np.argmin(abs(d["lat"] - 50.78))), int(np.argmin(abs(d["lon"] - 6.08)))
    block = np.nanmean(np.stack([d["EFO"], d["DFO"]])[:, 5:8, i - 1:i + 2, j - 1:j + 2])
    assert 0.005 < block < 0.06
