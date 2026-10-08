"""Tests for the carbon dynamics module."""

from __future__ import annotations

import numpy as np
import pytest

from nbs.legacy.parameters import T_END, T_START
from nbs.legacy.carbon_module import (
    compute_biomass_growth,
    compute_disturbance_loss,
    compute_nee_at_level,
    compute_nee_timeseries,
    compute_soc_dynamics,
    compute_soil_respiration,
    nominal_credit_gtco2,
)


# ---------------------------------------------------------------------------
# compute_biomass_growth
# ---------------------------------------------------------------------------


class TestBiomassGrowth:
    """Chapman-Richards growth curve."""

    def test_starts_at_zero(self):
        t = np.arange(0, 100)
        B = compute_biomass_growth(200.0, 0.08, 2.5, t)
        assert B[0] == pytest.approx(0.0, abs=1e-10)

    def test_approaches_bmax(self):
        t = np.arange(0, 500)
        B = compute_biomass_growth(200.0, 0.08, 2.5, t)
        assert B[-1] == pytest.approx(200.0, rel=0.01)

    def test_monotonically_increasing(self):
        t = np.arange(0, 200)
        B = compute_biomass_growth(200.0, 0.08, 2.5, t)
        assert np.all(np.diff(B) >= 0)

    def test_correct_shape(self):
        t = np.arange(0, 125)
        B = compute_biomass_growth(100.0, 0.03, 2.0, t)
        assert B.shape == (125,)


# ---------------------------------------------------------------------------
# compute_soc_dynamics
# ---------------------------------------------------------------------------


class TestSOCDynamics:
    """Exponential SOC convergence."""

    def test_starts_at_initial(self):
        t = np.arange(0, 100)
        soc = compute_soc_dynamics(120.0, 80.0, 0.03, t)
        assert soc[0] == pytest.approx(80.0)

    def test_approaches_forest_equilibrium(self):
        t = np.arange(0, 500)
        soc = compute_soc_dynamics(120.0, 80.0, 0.03, t)
        assert soc[-1] == pytest.approx(120.0, rel=0.01)

    def test_can_decrease_boreal(self):
        """Boreal case: initial SOC > forest equilibrium."""
        t = np.arange(0, 200)
        soc = compute_soc_dynamics(90.0, 110.0, 0.03, t)
        # SOC should decrease from 110 toward 90
        assert soc[0] > soc[-1]
        assert soc[-1] == pytest.approx(90.0, rel=0.01)


# ---------------------------------------------------------------------------
# compute_soil_respiration
# ---------------------------------------------------------------------------


class TestSoilRespiration:
    """Q10-based soil respiration."""

    def test_equals_rbase_at_t0(self):
        R = compute_soil_respiration(15.0, 2.0, 10.0, 10.0)
        assert R == pytest.approx(15.0)

    def test_increases_with_temperature(self):
        R_low = compute_soil_respiration(15.0, 2.0, 10.0, 10.0)
        R_high = compute_soil_respiration(15.0, 2.0, 10.0, 20.0)
        assert R_high > R_low

    def test_array_input(self):
        temps = np.array([10.0, 20.0, 30.0])
        R = compute_soil_respiration(15.0, 2.0, 10.0, temps)
        assert R.shape == (3,)
        assert np.all(np.diff(R) > 0)


# ---------------------------------------------------------------------------
# compute_disturbance_loss
# ---------------------------------------------------------------------------


class TestDisturbanceLoss:
    """Disturbance proportional to biomass."""

    def test_proportional_to_biomass(self):
        biomass = np.array([10.0, 50.0, 100.0])
        p = np.array([0.01, 0.01, 0.01])
        D = compute_disturbance_loss(biomass, p)
        np.testing.assert_allclose(D, [0.1, 0.5, 1.0])

    def test_zero_when_no_disturbance(self):
        biomass = np.array([10.0, 50.0, 100.0])
        p = np.zeros(3)
        D = compute_disturbance_loss(biomass, p)
        np.testing.assert_allclose(D, 0.0)


# ---------------------------------------------------------------------------
# compute_nee_timeseries
# ---------------------------------------------------------------------------


class TestNEETimeseries:
    """Integration tests for compute_nee_timeseries."""

    def test_tr_shape(self):
        nee = compute_nee_timeseries("tropical_reforestation", 0)
        assert nee.shape == (T_END - T_START,)

    def test_tr_cumulative_negative(self):
        """Net removal: cumulative NEE should be negative."""
        nee = compute_nee_timeseries("tropical_reforestation", 0)
        assert nee.sum() < 0

    def test_tr_peak_removal_range(self):
        """Peak removal should be in reasonable range for 1 Mha."""
        nee = compute_nee_timeseries("tropical_reforestation", 0, area_mha=1.0)
        assert -1.0 < nee.min() < 0.0

    def test_ad_immediate_benefit(self):
        """Avoided deforestation gives immediate negative NEE."""
        nee = compute_nee_timeseries("avoided_deforestation", 0)
        assert nee[0] < 0

    def test_beccs_harvest_spikes(self):
        """BECCS should have harvest spikes making min < mean."""
        nee = compute_nee_timeseries("beccs", 30)
        assert nee.min() < nee.mean()

    def test_area_scaling(self):
        """Doubling area doubles NEE."""
        nee1 = compute_nee_timeseries("tropical_reforestation", 0, area_mha=1.0)
        nee2 = compute_nee_timeseries("tropical_reforestation", 0, area_mha=2.0)
        np.testing.assert_allclose(nee2, 2.0 * nee1)


# ---------------------------------------------------------------------------
# compute_nee_at_level
# ---------------------------------------------------------------------------


class TestNEEAtLevel:
    def test_level_0_removes_credited_mass_at_once(self):
        """L0 encodes carbon-only accounting: the credited mass leaves the
        atmosphere in year one and never comes back."""
        nee = compute_nee_at_level(level=0, lat=0, area_mha=1.0)
        assert nee[0] == pytest.approx(-nominal_credit_gtco2(0, 1.0, location=False))
        assert np.all(nee[1:] == 0.0)

    def test_level_1_has_carbon_uptake(self):
        nee = compute_nee_at_level(level=1, lat=0, area_mha=1.0)
        assert np.sum(nee) < 0

    def test_level_1_same_regardless_of_latitude(self):
        nee_0 = compute_nee_at_level(level=1, lat=0, area_mha=1.0)
        nee_60 = compute_nee_at_level(level=1, lat=60, area_mha=1.0)
        np.testing.assert_allclose(nee_0, nee_60)

    def test_level_2_differs_by_latitude(self):
        nee_0 = compute_nee_at_level(level=2, lat=0, area_mha=1.0)
        nee_60 = compute_nee_at_level(level=2, lat=60, area_mha=1.0)
        assert not np.allclose(nee_0, nee_60)

    def test_level_2_tropical_faster(self):
        nee_0 = compute_nee_at_level(level=2, lat=0, area_mha=1.0)
        nee_60 = compute_nee_at_level(level=2, lat=60, area_mha=1.0)
        assert np.sum(nee_0[:50]) < np.sum(nee_60[:50])

    def test_level_3_same_nee_as_level_2(self):
        nee_2 = compute_nee_at_level(level=2, lat=0, area_mha=1.0)
        nee_3 = compute_nee_at_level(level=3, lat=0, area_mha=1.0)
        np.testing.assert_allclose(nee_2, nee_3)

    def test_level_4_same_nee_as_level_2(self):
        """L4 adds ET forcing (handled in credit_analysis), not a NEE change."""
        nee_2 = compute_nee_at_level(level=2, lat=0, area_mha=1.0)
        nee_4 = compute_nee_at_level(level=4, lat=0, area_mha=1.0)
        np.testing.assert_allclose(nee_2, nee_4)

    def test_level_5_includes_soc(self):
        nee_4 = compute_nee_at_level(level=4, lat=60, area_mha=1.0)
        nee_5 = compute_nee_at_level(level=5, lat=60, area_mha=1.0)
        assert np.sum(nee_5) > np.sum(nee_4)

    def test_level_6_less_removal_than_level_5(self):
        """L6 adds disturbance loss on top of L5 -> less net removal."""
        nee_5 = compute_nee_at_level(level=5, lat=0, area_mha=1.0)
        nee_6 = compute_nee_at_level(level=6, lat=0, area_mha=1.0)
        assert np.sum(nee_6) > np.sum(nee_5)

    def test_output_shape(self):
        nee = compute_nee_at_level(level=3, lat=30, area_mha=1.0)
        assert nee.shape == (T_END - T_START,)

    def test_area_scaling(self):
        nee_1 = compute_nee_at_level(level=2, lat=0, area_mha=1.0)
        nee_2 = compute_nee_at_level(level=2, lat=0, area_mha=2.0)
        np.testing.assert_allclose(nee_2, 2 * nee_1)
