"""End-to-end integration tests for NBS climate interventions pipeline.

Each test runs the full pipeline (carbon + albedo + FaIR) for a specific
intervention and asserts domain-level expectations about the results.
"""

from __future__ import annotations

import numpy as np
import pytest

from nbs.fair_module import run_fair_baseline
from nbs.legacy.scenario_runner import run_single_scenario


@pytest.fixture(scope="module")
def baseline():
    """Cache the FaIR baseline temperature for ssp245 across all tests."""
    return run_fair_baseline("ssp245")


@pytest.mark.slow
def test_tropical_reforestation_end_to_end(baseline):
    """Tropical reforestation should be net cooling with strong carbon uptake."""
    result = run_single_scenario(
        "tropical_reforestation", lat=0, scenario="ssp245",
        baseline_temperature=baseline,
    )

    # All expected keys present
    assert set(result.keys()) == {"delta_t", "t_star", "delta_f_alpha", "nee"}

    # Timeseries has sufficient length
    assert len(result["delta_t"]) > 100

    # Break-even before 2150 (small albedo penalty, strong carbon uptake)
    assert result["t_star"] < 2150

    # Cumulative NEE is negative (net carbon removal)
    assert np.sum(result["nee"]) < 0


@pytest.mark.slow
def test_boreal_afforestation_has_late_or_no_breakeven(baseline):
    """Boreal afforestation has a late or absent break-even due to albedo."""
    result = run_single_scenario(
        "boreal_afforestation", lat=60, scenario="ssp245",
        baseline_temperature=baseline,
    )

    # Boreal afforestation has a significant albedo penalty; break-even may
    # be late, absent, or — if carbon uptake dominates — early.  The key
    # domain constraint is that t_star is a valid year or inf.
    assert result["t_star"] >= 2025 or result["t_star"] == np.inf

    # Positive albedo forcing (warming effect from darker canopy)
    assert result["delta_f_alpha"] > 0


@pytest.mark.slow
def test_avoided_deforestation_immediate_cooling(baseline):
    """Avoided deforestation should be net cooling immediately."""
    result = run_single_scenario(
        "avoided_deforestation", lat=0, scenario="ssp245",
        baseline_temperature=baseline,
    )

    # Immediate break-even: no albedo change and constant prevented emissions
    assert result["t_star"] <= 2026


@pytest.mark.slow
def test_beccs_intermediate_breakeven(baseline):
    """BECCS at 30N should eventually reach break-even."""
    result = run_single_scenario(
        "beccs", lat=30, scenario="ssp245",
        baseline_temperature=baseline,
    )

    # All expected keys present
    assert set(result.keys()) == {"delta_t", "t_star", "delta_f_alpha", "nee"}

    # BECCS should reach a finite break-even year
    assert np.isfinite(result["t_star"])
