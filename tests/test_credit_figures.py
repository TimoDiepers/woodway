import numpy as np
import pytest
from pathlib import Path
from nbs.legacy.credit_figures import (
    plot_progressive_delta_t, plot_equivalence_by_latitude,
    plot_breakeven_by_level, plot_warming_debt,
    plot_credit_depreciation, plot_credit_sobol,
)

N = 125

@pytest.fixture
def mock_progressive():
    results = {}
    for level in range(7):
        results[level] = {"delta_t": np.linspace(0.001, -0.001, N) * (1 + level * 0.1)}
    return results

@pytest.fixture
def mock_lat_results():
    results = {}
    for level in [1, 3, 6]:
        for lat in [0, 15, 30, 45, 60]:
            results[(level, lat, "ssp245")] = {
                "equivalence_ratio_2100": 1.0 + lat * 0.05 + level * 0.2,
                "t_star": 2050 + lat + level * 5,
                "warming_debt": 0.01 * (1 + lat / 10 + level / 3),
            }
    return results

@pytest.fixture
def mock_ssp_results():
    results = {}
    for scenario in ["ssp126", "ssp245", "ssp370"]:
        mult = {"ssp126": 0.8, "ssp245": 1.0, "ssp370": 1.3}[scenario]
        for lat in [0, 15, 30, 45, 60]:
            results[(6, lat, scenario)] = {"equivalence_ratio_2100": 2.0 * mult + lat * 0.02}
    return results

@pytest.fixture
def output_dir(tmp_path):
    return str(tmp_path / "figures")

class TestCreditFigures:
    def test_progressive_delta_t(self, mock_progressive, output_dir):
        path = plot_progressive_delta_t(mock_progressive, output_dir, lat=45)
        assert Path(path).exists()

    def test_equivalence_by_latitude(self, mock_lat_results, output_dir):
        path = plot_equivalence_by_latitude(mock_lat_results, output_dir)
        assert Path(path).exists()

    def test_breakeven_by_level(self, mock_lat_results, output_dir):
        path = plot_breakeven_by_level(mock_lat_results, output_dir)
        assert Path(path).exists()

    def test_warming_debt(self, mock_lat_results, output_dir):
        path = plot_warming_debt(mock_lat_results, output_dir)
        assert Path(path).exists()

    def test_credit_depreciation(self, mock_ssp_results, output_dir):
        path = plot_credit_depreciation(mock_ssp_results, output_dir)
        assert Path(path).exists()

    def test_credit_sobol(self, output_dir):
        si = {
            "S1": np.array([0.3, 0.2, 0.1, 0.05, 0.15, 0.1]),
            "ST": np.array([0.4, 0.25, 0.15, 0.1, 0.2, 0.15]),
            "S1_conf": np.array([0.05] * 6),
            "ST_conf": np.array([0.05] * 6),
            "param_names": ["B_max", "Q10", "eta_CCS", "p_dist", "mu", "albedo"],
        }
        path = plot_credit_sobol(si, output_dir)
        assert Path(path).exists()
