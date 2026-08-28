"""Tests for the sensitivity analysis module."""

from __future__ import annotations

import numpy as np
import pytest

from nbs.sensitivity import PARAM_BOUNDS, run_oat_sensitivity, run_sobol_sensitivity


# ---------------------------------------------------------------------------
# Unit tests (no FaIR)
# ---------------------------------------------------------------------------


class TestParamBounds:
    def test_has_all_six_parameters(self):
        expected = {"B_max_scale", "Q10", "eta_CCS", "p_disturb_scale", "mu", "albedo_scale"}
        assert set(PARAM_BOUNDS.keys()) == expected

    def test_bounds_are_tuples_of_two(self):
        for name, bounds in PARAM_BOUNDS.items():
            assert isinstance(bounds, tuple), f"{name} bounds should be a tuple"
            assert len(bounds) == 2, f"{name} bounds should have 2 elements"
            assert bounds[0] < bounds[1], f"{name} low should be less than high"


# ---------------------------------------------------------------------------
# Integration tests (slow — run FaIR)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestOATSensitivity:
    @pytest.fixture(scope="class")
    def oat_result(self):
        return run_oat_sensitivity("tropical_reforestation", 0)

    def test_returns_dict_with_all_params(self, oat_result):
        assert isinstance(oat_result, dict)
        assert set(oat_result.keys()) == set(PARAM_BOUNDS.keys())

    def test_each_entry_has_required_keys(self, oat_result):
        for name, entry in oat_result.items():
            assert "low" in entry, f"{name} missing 'low'"
            assert "high" in entry, f"{name} missing 'high'"
            assert "t_star_low" in entry, f"{name} missing 't_star_low'"
            assert "t_star_high" in entry, f"{name} missing 't_star_high'"

    def test_t_star_values_are_numeric(self, oat_result):
        for name, entry in oat_result.items():
            assert isinstance(entry["t_star_low"], float), f"{name} t_star_low not float"
            assert isinstance(entry["t_star_high"], float), f"{name} t_star_high not float"


@pytest.mark.slow
class TestSobolSensitivity:
    @pytest.fixture(scope="class")
    def sobol_result(self):
        return run_sobol_sensitivity("tropical_reforestation", 0, n_samples=64)

    def test_returns_dict_with_required_keys(self, sobol_result):
        assert "S1" in sobol_result
        assert "ST" in sobol_result
        assert "S1_conf" in sobol_result
        assert "ST_conf" in sobol_result
        assert "param_names" in sobol_result

    def test_arrays_correct_length(self, sobol_result):
        n_params = len(PARAM_BOUNDS)
        assert len(sobol_result["S1"]) == n_params
        assert len(sobol_result["ST"]) == n_params
        assert len(sobol_result["S1_conf"]) == n_params
        assert len(sobol_result["ST_conf"]) == n_params
        assert len(sobol_result["param_names"]) == n_params
