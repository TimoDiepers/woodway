"""Tests for the scenario runner module."""

from __future__ import annotations

import numpy as np
import pytest

from nbs.legacy.scenario_runner import (
    is_valid_combination,
    run_single_scenario,
    run_all_scenarios,
)


# ---------------------------------------------------------------------------
# is_valid_combination
# ---------------------------------------------------------------------------


class TestIsValidCombination:
    """Validate latitude ranges per intervention."""

    def test_tropical_reforestation_at_0(self):
        assert is_valid_combination("tropical_reforestation", 0) is True

    def test_tropical_reforestation_at_60(self):
        assert is_valid_combination("tropical_reforestation", 60) is False

    def test_boreal_afforestation_at_0(self):
        assert is_valid_combination("boreal_afforestation", 0) is False

    def test_boreal_afforestation_at_60(self):
        assert is_valid_combination("boreal_afforestation", 60) is True

    def test_avoided_deforestation_at_0(self):
        assert is_valid_combination("avoided_deforestation", 0) is True

    def test_avoided_deforestation_at_60(self):
        assert is_valid_combination("avoided_deforestation", 60) is False

    def test_beccs_at_30(self):
        assert is_valid_combination("beccs", 30) is True


# ---------------------------------------------------------------------------
# run_single_scenario
# ---------------------------------------------------------------------------


class TestRunSingleScenario:
    """Integration test for a single scenario run."""

    @pytest.fixture(scope="class")
    def result(self):
        return run_single_scenario(
            "tropical_reforestation", 0, scenario="ssp245", area_mha=1.0
        )

    def test_returns_dict(self, result):
        assert isinstance(result, dict)

    def test_has_expected_keys(self, result):
        expected_keys = {"delta_t", "t_star", "delta_f_alpha", "nee"}
        assert set(result.keys()) == expected_keys

    def test_delta_t_is_array(self, result):
        assert isinstance(result["delta_t"], np.ndarray)

    def test_delta_t_shape(self, result):
        assert result["delta_t"].shape == (125,)

    def test_nee_is_array(self, result):
        assert isinstance(result["nee"], np.ndarray)

    def test_t_star_is_float(self, result):
        assert isinstance(result["t_star"], float)

    def test_delta_f_alpha_is_float(self, result):
        assert isinstance(result["delta_f_alpha"], float)


# ---------------------------------------------------------------------------
# run_all_scenarios
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestRunAllScenarios:
    """Integration test for the full scenario sweep."""

    @pytest.fixture(scope="class")
    def results(self):
        return run_all_scenarios(area_mha=1.0)

    def test_returns_dict(self, results):
        assert isinstance(results, dict)

    def test_no_invalid_combinations(self, results):
        for intervention, lat, scenario in results:
            assert is_valid_combination(intervention, lat), (
                f"Invalid combination found: {intervention} at {lat}°N"
            )

    def test_keys_are_tuples(self, results):
        for key in results:
            assert isinstance(key, tuple)
            assert len(key) == 3
