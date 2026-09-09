"""Tests for the credit analysis module."""

from __future__ import annotations

import numpy as np
import pytest

from nbs.legacy.credit_analysis import (
    compute_warming_debt,
    compute_equivalence_ratio,
    run_at_level,
    run_progressive_analysis,
)
from nbs.legacy.parameters import T_START, T_END

N_YEARS = T_END - T_START


class TestWarmingDebt:
    def test_all_positive_gives_positive_debt(self):
        delta_t = np.ones(N_YEARS) * 0.001
        debt = compute_warming_debt(delta_t)
        assert debt == pytest.approx(0.001 * N_YEARS, rel=0.01)

    def test_all_negative_gives_zero_debt(self):
        delta_t = np.full(N_YEARS, -0.001)
        debt = compute_warming_debt(delta_t)
        assert debt == 0.0

    def test_mixed_counts_only_positive(self):
        delta_t = np.zeros(N_YEARS)
        delta_t[:50] = 0.001
        delta_t[50:] = -0.001
        debt = compute_warming_debt(delta_t)
        assert debt == pytest.approx(0.001 * 50, rel=0.01)

    def test_returns_float(self):
        debt = compute_warming_debt(np.ones(N_YEARS))
        assert isinstance(debt, float)


class TestEquivalenceRatio:
    def test_perfect_offset_ratio_one(self):
        pulse = np.ones(N_YEARS) * 0.001
        offset = np.ones(N_YEARS) * -0.001
        ratio = compute_equivalence_ratio(pulse, offset, horizon_year=2100)
        assert ratio == pytest.approx(1.0, abs=0.1)

    def test_weak_offset_needs_more_credits(self):
        pulse = np.ones(N_YEARS) * 0.001
        offset = np.ones(N_YEARS) * -0.0005
        ratio = compute_equivalence_ratio(pulse, offset, horizon_year=2100)
        assert ratio == pytest.approx(2.0, abs=0.2)

    def test_zero_offset_returns_inf(self):
        pulse = np.ones(N_YEARS) * 0.001
        offset = np.zeros(N_YEARS)
        ratio = compute_equivalence_ratio(pulse, offset, horizon_year=2100)
        assert ratio == np.inf

    def test_warming_offset_returns_inf(self):
        pulse = np.ones(N_YEARS) * 0.001
        offset = np.ones(N_YEARS) * 0.001
        ratio = compute_equivalence_ratio(pulse, offset, horizon_year=2100)
        assert ratio == np.inf


class TestRunAtLevel:
    @pytest.mark.slow
    def test_returns_expected_keys(self):
        result = run_at_level(level=1, lat=0, scenario="ssp245")
        for key in [
            "delta_t",
            "t_star",
            "warming_debt",
            "nee",
            "equivalence_ratio_2100",
            "pulse_dt",
            "offset_dt",
        ]:
            assert key in result

    @pytest.mark.slow
    def test_level_0_offsets_in_proportion_to_credited_mass(self):
        """Naive accounting removes the credited mass at once. The credited mass
        (0.73 GtCO2 per Mha) is smaller than the 1 GtCO2 pulse, so warming is
        reduced in that proportion rather than cancelled outright."""
        result = run_at_level(level=0, lat=0, scenario="ssp245")
        credited = result["credited_gtco2"]
        expected = result["pulse_dt"][5] * (1.0 - credited)
        assert result["delta_t"][5] == pytest.approx(expected, rel=0.1)

    @pytest.mark.slow
    def test_level_0_equivalence_ratio_is_one(self):
        result = run_at_level(level=0, lat=0, scenario="ssp245")
        assert result["equivalence_ratio_2100"] == pytest.approx(1.0, abs=0.05)

    @pytest.mark.slow
    def test_growth_delay_creates_warming_debt(self):
        """Realistic growth cannot beat instantaneous accounting."""
        r0 = run_at_level(level=0, lat=0, scenario="ssp245")
        r1 = run_at_level(level=1, lat=0, scenario="ssp245")
        assert r1["warming_debt"] > r0["warming_debt"]

    @pytest.mark.slow
    def test_non_co2_forcing_is_area_weighted(self):
        """Local W/m2 values enter FaIR scaled by the project's share of the globe."""
        r = run_at_level(level=3, lat=60, scenario="ssp245", area_mha=1.0)
        assert abs(r["extra_forcing"]).max() < 1e-4


class TestProgressiveAnalysis:
    @pytest.mark.slow
    def test_returns_dict_keyed_by_level(self):
        results = run_progressive_analysis(lat=0, scenario="ssp245")
        for level in range(7):
            assert level in results

    @pytest.mark.slow
    def test_warming_debt_increases_with_disturbance(self):
        """L6 (disturbance) increases warming debt vs L1 at lat=60 (boreal).
        Boreal SOC releases carbon + disturbance -> less removal -> more warming debt."""
        results = run_progressive_analysis(lat=60, scenario="ssp245")
        assert results[6]["warming_debt"] >= results[1]["warming_debt"]
