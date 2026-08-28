import numpy as np
import pytest

from nbs.albedo_module import compute_albedo_forcing_timeseries


class TestAlbedoForcingTimeseries:
    """Tests for compute_albedo_forcing_timeseries."""

    def test_ad_returns_all_zeros(self):
        """Avoided deforestation has zero albedo forcing at all latitudes."""
        result = compute_albedo_forcing_timeseries("avoided_deforestation", 0)
        np.testing.assert_array_equal(result, np.zeros(125))

    def test_tr_at_equator_is_negative(self):
        """Tropical reforestation at 0 deg has negative (cooling) forcing."""
        result = compute_albedo_forcing_timeseries("tropical_reforestation", 0)
        # After transition, all values should be negative
        assert np.all(result[3:] < 0)

    def test_ba_at_60_is_positive(self):
        """Boreal afforestation at 60 deg has positive (warming) forcing."""
        result = compute_albedo_forcing_timeseries("boreal_afforestation", 60)
        # After transition, all values should be positive
        assert np.all(result[3:] > 0)

    def test_transition_starts_at_zero(self):
        """Forcing starts at 0.0 in the first year."""
        result = compute_albedo_forcing_timeseries("tropical_reforestation", 0)
        assert result[0] == 0.0

    def test_transition_ramped_by_year_5(self):
        """Forcing should have reached full value by year 5 (index 5)."""
        result = compute_albedo_forcing_timeseries(
            "tropical_reforestation", 0, transition_years=3
        )
        # Year index 3 onward should be at full value
        assert result[5] == result[3]
        assert result[5] != 0.0

    def test_constant_after_transition(self):
        """Value at year 10 equals value at year 50."""
        result = compute_albedo_forcing_timeseries("boreal_afforestation", 60)
        assert result[10] == result[50]

    def test_output_shape(self):
        """Output shape must be (125,)."""
        result = compute_albedo_forcing_timeseries("tropical_reforestation", 0)
        assert result.shape == (125,)
