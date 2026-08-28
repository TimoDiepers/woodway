"""Tests for the figures module."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from nbs.parameters import INTERVENTIONS, LATITUDES, SCENARIOS, T_START, T_END


@pytest.fixture
def mock_results():
    """Create mock results dict with random data for all combinations."""
    rng = np.random.default_rng(42)
    n_years = T_END - T_START + 1  # 126, but spec says 125 shape
    n = 125
    results = {}
    for intervention in INTERVENTIONS:
        for lat in LATITUDES:
            for scenario in SCENARIOS:
                results[(intervention, lat, scenario)] = {
                    "delta_t": rng.standard_normal(n) * 1e-3,
                    "t_star": float(rng.uniform(T_START, T_END)),
                    "delta_f_alpha": float(rng.uniform(-1, 1)),
                    "nee": rng.standard_normal(n) * 10,
                }
    # Make one entry have t_star=inf for breakeven map test
    results[(INTERVENTIONS[0], LATITUDES[0], "ssp245")]["t_star"] = float("inf")
    return results


@pytest.fixture
def mock_sobol_results():
    """Create mock Sobol results dict."""
    n_params = 5
    rng = np.random.default_rng(99)
    return {
        "S1": rng.uniform(0, 1, n_params),
        "ST": rng.uniform(0, 1, n_params),
        "S1_conf": rng.uniform(0, 0.1, n_params),
        "ST_conf": rng.uniform(0, 0.1, n_params),
        "param_names": [f"param_{i}" for i in range(n_params)],
    }


class TestPlotDeltaTCurves:
    def test_returns_existing_path(self, mock_results, tmp_path):
        from nbs.figures import plot_delta_t_curves

        path = plot_delta_t_curves(mock_results, str(tmp_path))
        assert Path(path).exists()

    def test_default_filename(self, mock_results, tmp_path):
        from nbs.figures import plot_delta_t_curves

        path = plot_delta_t_curves(mock_results, str(tmp_path))
        assert Path(path).name == "fig1_delta_t_curves.png"


class TestPlotBreakevenMap:
    def test_returns_existing_path(self, mock_results, tmp_path):
        from nbs.figures import plot_breakeven_map

        path = plot_breakeven_map(mock_results, str(tmp_path))
        assert Path(path).exists()

    def test_default_filename(self, mock_results, tmp_path):
        from nbs.figures import plot_breakeven_map

        path = plot_breakeven_map(mock_results, str(tmp_path))
        assert Path(path).name == "fig2_breakeven_map.png"


class TestPlotRankingHeatmap:
    def test_returns_existing_path(self, mock_results, tmp_path):
        from nbs.figures import plot_ranking_heatmap

        path = plot_ranking_heatmap(mock_results, str(tmp_path))
        assert Path(path).exists()

    def test_default_filename(self, mock_results, tmp_path):
        from nbs.figures import plot_ranking_heatmap

        path = plot_ranking_heatmap(mock_results, str(tmp_path))
        assert Path(path).name == "fig3_ranking_heatmap.png"


class TestPlotSspSensitivity:
    def test_returns_existing_path(self, mock_results, tmp_path):
        from nbs.figures import plot_ssp_sensitivity

        path = plot_ssp_sensitivity(mock_results, str(tmp_path))
        assert Path(path).exists()

    def test_default_filename(self, mock_results, tmp_path):
        from nbs.figures import plot_ssp_sensitivity

        path = plot_ssp_sensitivity(mock_results, str(tmp_path))
        assert Path(path).name == "fig4_ssp_sensitivity.png"


class TestPlotSobolIndices:
    def test_returns_existing_path(self, mock_sobol_results, tmp_path):
        from nbs.figures import plot_sobol_indices

        path = plot_sobol_indices(mock_sobol_results, str(tmp_path))
        assert Path(path).exists()

    def test_default_filename(self, mock_sobol_results, tmp_path):
        from nbs.figures import plot_sobol_indices

        path = plot_sobol_indices(mock_sobol_results, str(tmp_path))
        assert Path(path).name == "fig5_sobol_indices.png"
