import numpy as np
import pytest

from nbs.parameters import (
    BECCS_CCS_EFFICIENCY,
    BECCS_HARVEST_PERIOD,
    BECCS_PROCESS_EMISSION_FRAC,
    C_FOREST_TROPICAL,
    DEFORESTATION_RATE,
    INTERVENTIONS,
    LAND_USES,
    LATITUDES,
    S0,
    SCENARIOS,
    SOC_MU,
    SOIL_RESP_BASE,
    SOIL_RESP_Q10,
    SOIL_RESP_T0,
    T_END,
    T_START,
    get_albedo_values,
    get_disturbance_probability,
    get_growth_params,
    get_soc_params,
)


# --- Constants lists ---


class TestConstants:
    def test_interventions_length(self):
        assert len(INTERVENTIONS) == 4

    def test_latitudes_length(self):
        assert len(LATITUDES) == 5

    def test_land_uses_length(self):
        assert len(LAND_USES) == 3

    def test_scenarios_length(self):
        assert len(SCENARIOS) == 3

    def test_soil_resp_base_length(self):
        assert len(SOIL_RESP_BASE) == 5

    def test_time_range(self):
        assert T_START == 2025
        assert T_END == 2150

    def test_solar_constant(self):
        assert S0 == 1361.0


# --- Growth parameters ---


class TestGrowthParams:
    @pytest.mark.parametrize(
        "intervention",
        ["tropical_reforestation", "boreal_afforestation", "beccs"],
    )
    def test_returns_three_positive_floats(self, intervention):
        b_max, k, p = get_growth_params(intervention)
        assert b_max > 0
        assert k > 0
        assert p > 0

    def test_tropical_reforestation_values(self):
        b_max, k, p = get_growth_params("tropical_reforestation")
        assert b_max == 200
        assert k == 0.08
        assert p == 2.5

    def test_boreal_afforestation_values(self):
        b_max, k, p = get_growth_params("boreal_afforestation")
        assert b_max == 100
        assert k == 0.03
        assert p == 2.0

    def test_beccs_values(self):
        b_max, k, p = get_growth_params("beccs")
        assert b_max == 50
        assert k == 0.12
        assert p == 1.75

    def test_avoided_deforestation_raises(self):
        with pytest.raises(KeyError):
            get_growth_params("avoided_deforestation")


# --- SOC parameters ---


class TestSOCParams:
    @pytest.mark.parametrize(
        "intervention,lat",
        [
            ("tropical_reforestation", 0),
            ("tropical_reforestation", 15),
            ("boreal_afforestation", 45),
            ("boreal_afforestation", 60),
            ("avoided_deforestation", 0),
            ("beccs", 30),
        ],
    )
    def test_returns_positive_values(self, intervention, lat):
        soc_forest, soc_initial = get_soc_params(intervention, lat)
        assert soc_forest > 0
        assert soc_initial > 0

    def test_fallback_to_nearest_latitude(self):
        # TR only has lat 0 and 15; requesting lat 10 should fallback
        soc_forest, soc_initial = get_soc_params("tropical_reforestation", 10)
        assert soc_forest > 0
        assert soc_initial > 0


# --- Disturbance probability ---


class TestDisturbanceProbability:
    def test_shape_matches_years(self):
        years = np.arange(2025, 2150)
        result = get_disturbance_probability("tropical_reforestation", 0, years)
        assert result.shape == years.shape

    def test_values_in_zero_one(self):
        years = np.arange(2025, 2151)
        for intervention in INTERVENTIONS:
            result = get_disturbance_probability(intervention, 0, years)
            assert np.all(result >= 0)
            assert np.all(result <= 1)

    def test_increases_over_time(self):
        years = np.array([2025, 2150])
        result = get_disturbance_probability("tropical_reforestation", 0, years)
        assert result[-1] > result[0]

    def test_increases_by_50_percent(self):
        years = np.array([2025, 2150])
        result = get_disturbance_probability("tropical_reforestation", 0, years)
        assert np.isclose(result[-1] / result[0], 1.5)


# --- Albedo values ---


class TestAlbedoValues:
    def test_tr_at_0_is_negative(self):
        assert get_albedo_values("tropical_reforestation", 0) < 0

    def test_ba_at_60_is_positive(self):
        assert get_albedo_values("boreal_afforestation", 60) > 0

    def test_ad_is_always_zero(self):
        for lat in LATITUDES:
            assert get_albedo_values("avoided_deforestation", lat) == 0.0

    def test_fallback_to_nearest_latitude(self):
        # TR has data at 0, 15, 30; requesting 10 should return nearest
        val = get_albedo_values("tropical_reforestation", 10)
        assert isinstance(val, float)
