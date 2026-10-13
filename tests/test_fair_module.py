"""Tests for the FaIR coupling module."""

from __future__ import annotations

import numpy as np
import pytest

from nbs.fair_module import (
    compute_delta_t,
    compute_pulse_warming,
    find_breakeven_year,
    run_fair_baseline,
    run_fair_perturbed,
)
from nbs.legacy.parameters import T_START, T_END

N_YEARS = T_END - T_START  # 125


# ---------------------------------------------------------------------------
# Shared fixture — baseline is expensive, compute once per module
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def baseline_temperature():
    return run_fair_baseline(scenario="ssp245")


# ---------------------------------------------------------------------------
# run_fair_baseline
# ---------------------------------------------------------------------------


class TestBaseline:
    """Baseline SSP2-4.5 temperature trajectory."""

    def test_returns_array(self, baseline_temperature):
        assert isinstance(baseline_temperature, np.ndarray)

    def test_shape(self, baseline_temperature):
        assert baseline_temperature.shape == (N_YEARS,)

    def test_shows_warming(self, baseline_temperature):
        # Temperature at end should exceed temperature at start (warming trend)
        assert baseline_temperature[-1] > baseline_temperature[0]


# ---------------------------------------------------------------------------
# run_fair_perturbed — pure removal
# ---------------------------------------------------------------------------


class TestPerturbedRemoval:
    """A constant CO2 removal should cool relative to baseline."""

    @pytest.fixture(scope="class")
    def removal_temperature(self):
        nee = np.full(N_YEARS, -1.0)  # -1 GtCO2/yr removal
        albedo = np.zeros(N_YEARS)
        return run_fair_perturbed(nee, albedo, scenario="ssp245")

    def test_shape(self, removal_temperature):
        assert removal_temperature.shape == (N_YEARS,)

    def test_cooling(self, removal_temperature, baseline_temperature):
        dt = compute_delta_t(removal_temperature, baseline_temperature)
        # End of century should show cooling
        assert dt[-1] < 0


# ---------------------------------------------------------------------------
# run_fair_perturbed — warming albedo
# ---------------------------------------------------------------------------


class TestPerturbedAlbedo:
    """Positive albedo forcing (warming) should increase temperature."""

    @pytest.fixture(scope="class")
    def albedo_temperature(self):
        nee = np.zeros(N_YEARS)
        albedo = np.full(N_YEARS, 0.5)  # +0.5 W/m² warming
        return run_fair_perturbed(nee, albedo, scenario="ssp245")

    def test_warming(self, albedo_temperature, baseline_temperature):
        dt = compute_delta_t(albedo_temperature, baseline_temperature)
        assert dt[-1] > 0


# ---------------------------------------------------------------------------
# compute_delta_t
# ---------------------------------------------------------------------------


class TestDeltaT:
    """Simple subtraction of baseline from perturbed."""

    def test_shape(self):
        a = np.ones(N_YEARS)
        b = np.zeros(N_YEARS)
        dt = compute_delta_t(a, b)
        assert dt.shape == (N_YEARS,)

    def test_values(self):
        a = np.full(N_YEARS, 3.0)
        b = np.full(N_YEARS, 2.0)
        dt = compute_delta_t(a, b)
        np.testing.assert_allclose(dt, 1.0)


# ---------------------------------------------------------------------------
# find_breakeven_year
# ---------------------------------------------------------------------------


class TestBreakevenYear:
    """Find the first year where delta_t transitions to cooling."""

    def test_pure_removal_breaks_even_quickly(self, baseline_temperature):
        nee = np.full(N_YEARS, -1.0)
        albedo = np.zeros(N_YEARS)
        t_pert = run_fair_perturbed(nee, albedo, scenario="ssp245")
        dt = compute_delta_t(t_pert, baseline_temperature)
        t_star = find_breakeven_year(dt)
        assert t_star < 2050

    def test_strong_warming_never_breaks_even(self):
        # delta_t always positive => never breaks even
        dt = np.ones(N_YEARS) * 0.5
        t_star = find_breakeven_year(dt)
        assert t_star == np.inf

    def test_immediate_cooling(self):
        dt = np.full(N_YEARS, -0.1)
        t_star = find_breakeven_year(dt)
        assert t_star == T_START


# ---------------------------------------------------------------------------
# compute_pulse_warming
# ---------------------------------------------------------------------------


class TestPulseWarming:
    """A CO2 pulse should cause transient warming that decays slowly."""

    @pytest.fixture(scope="class")
    def pulse_dt(self):
        return compute_pulse_warming(pulse_gtco2=1.0, scenario="ssp245")

    def test_returns_array(self, pulse_dt):
        assert isinstance(pulse_dt, np.ndarray)

    def test_shape(self, pulse_dt):
        assert pulse_dt.shape == (N_YEARS,)

    def test_initially_positive(self, pulse_dt):
        assert pulse_dt[5] > 0

    def test_warming_rate_slows(self, pulse_dt):
        # The rapid early warming should give way to a much slower increase,
        # i.e. the rate of change in the first decade exceeds the last decade.
        early_rate = pulse_dt[10] - pulse_dt[1]
        late_rate = pulse_dt[-1] - pulse_dt[-10]
        assert early_rate > late_rate

    def test_scales_with_pulse_size(self):
        dt_small = compute_pulse_warming(pulse_gtco2=0.5, scenario="ssp245")
        dt_large = compute_pulse_warming(pulse_gtco2=1.0, scenario="ssp245")
        assert dt_large[50] > dt_small[50]


def test_emission_delta_less_methane_cools_quickly():
    import numpy as np
    from nbs.fair_module import _END_IDX, _START_IDX, run_fair_baseline, run_fair_emission_delta
    n = _END_IDX - _START_IDX
    base = run_fair_baseline("cmip7-VL")
    cut = run_fair_emission_delta({"CH4": np.full(n, -100.0)}, "cmip7-VL")
    d = cut - base
    assert d[20] < -0.1          # 100 Mt CH4/a less: clearly cooler after 20 years
    assert abs(d[0]) < 0.02      # no jump in the first year


def test_emission_delta_zero_is_baseline():
    import numpy as np
    from nbs.fair_module import _END_IDX, _START_IDX, run_fair_baseline, run_fair_emission_delta
    n = _END_IDX - _START_IDX
    assert np.allclose(run_fair_emission_delta({"N2O": np.zeros(n)}, "cmip7-VL"), run_fair_baseline("cmip7-VL"))
