# Carbon Credit Reframing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add progressive-complexity analysis, pulse emission reference, equivalence ratio, and warming debt metrics to the existing NBS framework — reframing it around carbon credit debunking.

**Architecture:** Extend existing modules with new functions (no rewrites). New `credit_analysis.py` module owns the progressive-complexity logic and new metrics. New `credit_figures.py` owns the 6 new figures. Existing modules (fair_module, carbon_module, etc.) get small additions. All 103 existing tests must keep passing.

**Tech Stack:** Same as existing — Python 3.11+, FaIR v2.2, NumPy, matplotlib, SALib, pytest, uv

---

## File Structure

```
src/nbs/
  parameters.py          # MODIFY: add COMPLEXITY_LEVELS constant
  fair_module.py          # MODIFY: add compute_pulse_warming()
  carbon_module.py        # MODIFY: add compute_nee_at_level()
  credit_analysis.py      # CREATE: equivalence ratio, warming debt, level runner
  credit_figures.py       # CREATE: 6 new figures for progressive complexity
tests/
  test_fair_module.py     # MODIFY: add pulse warming tests
  test_carbon_module.py   # MODIFY: add level-based NEE tests
  test_credit_analysis.py # CREATE: equivalence ratio, warming debt, level runner tests
  test_credit_figures.py  # CREATE: figure output tests
```

---

### Task 1: Pulse Emission in FaIR

**Files:**
- Modify: `src/nbs/fair_module.py`
- Modify: `tests/test_fair_module.py`

Add a function to compute the warming trajectory from a single CO₂ emission pulse (representing a flight or other instantaneous emission).

- [ ] **Step 1: Write tests for pulse warming**

Append to `tests/test_fair_module.py`:
```python
from nbs.fair_module import compute_pulse_warming


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
        # Pulse causes warming
        assert pulse_dt[5] > 0

    def test_warming_decays(self, pulse_dt):
        # Warming should decrease over time (CO2 is gradually absorbed)
        assert pulse_dt[-1] < pulse_dt[10]

    def test_scales_with_pulse_size(self):
        dt_small = compute_pulse_warming(pulse_gtco2=0.5, scenario="ssp245")
        dt_large = compute_pulse_warming(pulse_gtco2=1.0, scenario="ssp245")
        # Larger pulse = more warming (approximately linear for small pulses)
        assert dt_large[50] > dt_small[50]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_fair_module.py::TestPulseWarming -v`
Expected: FAIL — `ImportError: cannot import name 'compute_pulse_warming'`

- [ ] **Step 3: Implement compute_pulse_warming**

Add to `src/nbs/fair_module.py` (after the `run_fair_perturbed` function):
```python
def compute_pulse_warming(
    pulse_gtco2: float = 1.0,
    scenario: str = "ssp245",
) -> NDArray:
    """Temperature impact of an instantaneous CO2 emission pulse at T_START.

    Runs FaIR with a single-year emission spike and returns the temperature
    difference relative to the unperturbed baseline.

    Parameters
    ----------
    pulse_gtco2 : float
        Size of the emission pulse [GtCO2] (default 1.0).
    scenario : str
        Background SSP scenario (default ``"ssp245"``).

    Returns
    -------
    NDArray, shape (T_END - T_START,)
        ΔT(t) from the pulse [K]. Positive = warming.
    """
    baseline = run_fair_baseline(scenario)

    f = _create_fair(scenario)

    # Add pulse at T_START only (single year)
    co2_vals = f.emissions.sel(specie="CO2 FFI").values.copy()
    co2_vals[_START_IDX, 0, 0] += pulse_gtco2
    f.emissions.loc[dict(specie="CO2 FFI")] = co2_vals

    f.run()

    temp = (
        f.temperature.sel(scenario=scenario, config="central", layer=0)
        .values[_START_IDX:_END_IDX]
    )
    perturbed = np.asarray(temp, dtype=np.float64)

    return perturbed - baseline
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_fair_module.py -v`
Expected: All tests PASS (existing + 5 new).

---

### Task 2: Complexity-Level NEE Computation

**Files:**
- Modify: `src/nbs/parameters.py`
- Modify: `src/nbs/carbon_module.py`
- Modify: `tests/test_carbon_module.py`

Add a function that computes NEE with processes toggled on/off by complexity level.

- [ ] **Step 1: Add COMPLEXITY_LEVELS to parameters.py**

Add to `src/nbs/parameters.py` after the `SCENARIOS` line:
```python
COMPLEXITY_LEVELS = [0, 1, 2, 3, 4, 5, 6]
```

- [ ] **Step 2: Write tests for level-based NEE**

Append to `tests/test_carbon_module.py`:
```python
from nbs.carbon_module import compute_nee_at_level


class TestNEEAtLevel:
    """NEE computation with progressive complexity levels."""

    def test_level_0_returns_zeros(self):
        """Level 0: no offset — NEE is zero (fantasy of instant offset)."""
        nee = compute_nee_at_level(level=0, lat=0, area_mha=1.0)
        np.testing.assert_allclose(nee, 0.0)

    def test_level_1_has_carbon_uptake(self):
        """Level 1: biomass growth only (no albedo, no feedbacks)."""
        nee = compute_nee_at_level(level=1, lat=0, area_mha=1.0)
        assert np.sum(nee) < 0  # Net removal

    def test_level_1_same_regardless_of_latitude(self):
        """Level 1 uses tropical growth params for all latitudes (no location dependence)."""
        nee_0 = compute_nee_at_level(level=1, lat=0, area_mha=1.0)
        nee_60 = compute_nee_at_level(level=1, lat=60, area_mha=1.0)
        np.testing.assert_allclose(nee_0, nee_60)

    def test_level_2_differs_by_latitude(self):
        """Level 2: location-dependent growth — different latitudes give different NEE."""
        nee_0 = compute_nee_at_level(level=2, lat=0, area_mha=1.0)
        nee_60 = compute_nee_at_level(level=2, lat=60, area_mha=1.0)
        assert not np.allclose(nee_0, nee_60)

    def test_level_2_tropical_faster(self):
        """Tropical growth is faster than boreal."""
        nee_0 = compute_nee_at_level(level=2, lat=0, area_mha=1.0)
        nee_60 = compute_nee_at_level(level=2, lat=60, area_mha=1.0)
        # Tropical has more cumulative removal in first 50 years
        assert np.sum(nee_0[:50]) < np.sum(nee_60[:50])

    def test_level_3_same_nee_as_level_2(self):
        """Level 3 adds albedo (handled separately), NEE unchanged from Level 2."""
        nee_2 = compute_nee_at_level(level=2, lat=0, area_mha=1.0)
        nee_3 = compute_nee_at_level(level=3, lat=0, area_mha=1.0)
        np.testing.assert_allclose(nee_2, nee_3)

    def test_level_4_less_removal_than_level_2(self):
        """Level 4 adds soil respiration feedback + disturbance — less net removal."""
        nee_2 = compute_nee_at_level(level=2, lat=0, area_mha=1.0)
        nee_4 = compute_nee_at_level(level=4, lat=0, area_mha=1.0)
        # Level 4 should have less removal (more positive = less negative)
        assert np.sum(nee_4) > np.sum(nee_2)

    def test_level_5_includes_soc(self):
        """Level 5 adds SOC dynamics — may differ from Level 4 at some latitudes."""
        nee_4 = compute_nee_at_level(level=4, lat=60, area_mha=1.0)
        nee_5 = compute_nee_at_level(level=5, lat=60, area_mha=1.0)
        # At 60N, SOC_initial > SOC_forest (grassland has more SOC), so Level 5 has less removal
        assert np.sum(nee_5) > np.sum(nee_4)

    def test_level_6_equals_level_5(self):
        """Level 6 is the full model — same as Level 5."""
        nee_5 = compute_nee_at_level(level=5, lat=0, area_mha=1.0)
        nee_6 = compute_nee_at_level(level=6, lat=0, area_mha=1.0)
        np.testing.assert_allclose(nee_5, nee_6)

    def test_output_shape(self):
        nee = compute_nee_at_level(level=3, lat=30, area_mha=1.0)
        assert nee.shape == (125,)

    def test_area_scaling(self):
        nee_1 = compute_nee_at_level(level=2, lat=0, area_mha=1.0)
        nee_2 = compute_nee_at_level(level=2, lat=0, area_mha=2.0)
        np.testing.assert_allclose(nee_2, 2 * nee_1)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_carbon_module.py::TestNEEAtLevel -v`
Expected: FAIL — `ImportError`

- [ ] **Step 4: Implement compute_nee_at_level**

Add to `src/nbs/carbon_module.py` (after `compute_nee_timeseries`):
```python
# Default tropical growth params for Level 1 (location-independent)
_LEVEL1_GROWTH = (200.0, 0.08, 2.5)  # Tropical: B_max, k, p

# Location-dependent growth params for Level 2+
_LEVEL2_GROWTH: dict[int, tuple[float, float, float]] = {
    0: (200.0, 0.08, 2.5),     # Tropical
    15: (200.0, 0.08, 2.5),    # Tropical
    30: (120.0, 0.05, 2.0),    # Temperate
    45: (100.0, 0.03, 2.0),    # Boreal
    60: (100.0, 0.03, 2.0),    # Boreal
}


def compute_nee_at_level(
    level: int, lat: int, area_mha: float = 1.0
) -> NDArray:
    """Compute NEE with processes toggled by complexity level.

    Levels
    ------
    0 : No offset (returns zeros — the "fantasy")
    1 : Biomass growth only, location-independent (tropical params for all)
    2 : Biomass growth, location-dependent (latitude-specific params)
    3 : Same as 2 (albedo is handled in credit_analysis, not here)
    4 : Level 2 + soil respiration feedback + disturbance
    5 : Level 4 + SOC dynamics
    6 : Same as 5 (full model)

    Parameters
    ----------
    level : int
        Complexity level (0-6).
    lat : int
        Latitude in degrees N.
    area_mha : float
        Area in million hectares.

    Returns
    -------
    NDArray, shape (125,)
        NEE [GtCO2/yr]. Negative = removal.
    """
    n_years = T_END - T_START
    years = np.arange(T_START, T_END)
    t = np.arange(n_years, dtype=float)

    if level == 0:
        return np.zeros(n_years)

    # --- Biomass growth ---
    if level == 1:
        B_max, k, p = _LEVEL1_GROWTH
    else:
        lat_key = _nearest_lat(lat, _LEVEL2_GROWTH)
        B_max, k, p = _LEVEL2_GROWTH[lat_key]

    biomass = compute_biomass_growth(B_max, k, p, t)
    dB_dt = np.diff(biomass, prepend=0.0)

    # --- SOC dynamics (Level 5+) ---
    if level >= 5:
        soc_forest, soc_initial = get_soc_params("tropical_reforestation", lat)
        soc = compute_soc_dynamics(soc_forest, soc_initial, SOC_MU, t)
        dSOC_dt = np.diff(soc, prepend=soc_initial)
    else:
        dSOC_dt = np.zeros(n_years)

    # --- Soil respiration feedback (Level 4+) ---
    if level >= 4:
        lat_key_temp = _nearest_lat(lat, BASE_TEMP)
        base_temp = BASE_TEMP[lat_key_temp]
        temperature = base_temp + 2.0 * t / (n_years - 1)
        lat_key_resp = _nearest_lat(lat, SOIL_RESP_BASE)
        r_base = SOIL_RESP_BASE[lat_key_resp]
        R_soil_full = compute_soil_respiration(r_base, SOIL_RESP_Q10, SOIL_RESP_T0, temperature)
        R_soil_baseline = compute_soil_respiration(r_base, SOIL_RESP_Q10, SOIL_RESP_T0, base_temp)
        R_soil = R_soil_full - R_soil_baseline
    else:
        R_soil = np.zeros(n_years)

    # --- Disturbance (Level 4+) ---
    if level >= 4:
        p_disturb = get_disturbance_probability("tropical_reforestation", lat, years)
        D = compute_disturbance_loss(biomass, p_disturb)
    else:
        D = np.zeros(n_years)

    # --- Net uptake -> NEE ---
    net_uptake = (dB_dt + dSOC_dt) * C_TO_CO2 - R_soil - D * C_TO_CO2
    nee = -net_uptake

    return nee * area_mha * 1e-3
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_carbon_module.py -v`
Expected: All tests PASS (existing 18 + new 11 = 29).

---

### Task 3: Credit Analysis Module

**Files:**
- Create: `src/nbs/credit_analysis.py`
- Create: `tests/test_credit_analysis.py`

The core new module: computes equivalence ratio, warming debt, and orchestrates level-by-level analysis.

- [ ] **Step 1: Write tests**

Create `tests/test_credit_analysis.py`:
```python
"""Tests for credit analysis module."""

from __future__ import annotations

import numpy as np
import pytest

from nbs.credit_analysis import (
    compute_warming_debt,
    compute_equivalence_ratio,
    run_at_level,
    run_progressive_analysis,
)
from nbs.parameters import T_START, T_END

N_YEARS = T_END - T_START


class TestWarmingDebt:
    """Warming debt = cumulative excess warming [K·yr]."""

    def test_all_positive_gives_positive_debt(self):
        delta_t = np.ones(N_YEARS) * 0.001  # 1 mK constant warming
        debt = compute_warming_debt(delta_t)
        assert debt == pytest.approx(0.001 * N_YEARS, rel=0.01)

    def test_all_negative_gives_zero_debt(self):
        delta_t = np.full(N_YEARS, -0.001)
        debt = compute_warming_debt(delta_t)
        assert debt == 0.0

    def test_mixed_counts_only_positive(self):
        delta_t = np.zeros(N_YEARS)
        delta_t[:50] = 0.001   # 50 years of warming
        delta_t[50:] = -0.001  # 75 years of cooling
        debt = compute_warming_debt(delta_t)
        assert debt == pytest.approx(0.001 * 50, rel=0.01)

    def test_returns_float(self):
        delta_t = np.ones(N_YEARS)
        assert isinstance(compute_warming_debt(delta_t), float)


class TestEquivalenceRatio:
    """Equivalence ratio = credits needed per tCO2 for net zero by horizon."""

    def test_perfect_offset_ratio_one(self):
        # Pulse warming exactly cancelled by offset cooling
        pulse = np.ones(N_YEARS) * 0.001
        offset = np.ones(N_YEARS) * -0.001
        ratio = compute_equivalence_ratio(pulse, offset, horizon_year=2100)
        assert ratio == pytest.approx(1.0, abs=0.1)

    def test_weak_offset_needs_more_credits(self):
        pulse = np.ones(N_YEARS) * 0.001
        offset = np.ones(N_YEARS) * -0.0005  # Half as effective
        ratio = compute_equivalence_ratio(pulse, offset, horizon_year=2100)
        assert ratio == pytest.approx(2.0, abs=0.2)

    def test_zero_offset_returns_inf(self):
        pulse = np.ones(N_YEARS) * 0.001
        offset = np.zeros(N_YEARS)
        ratio = compute_equivalence_ratio(pulse, offset, horizon_year=2100)
        assert ratio == np.inf

    def test_warming_offset_returns_inf(self):
        pulse = np.ones(N_YEARS) * 0.001
        offset = np.ones(N_YEARS) * 0.001  # Also warming — net harmful
        ratio = compute_equivalence_ratio(pulse, offset, horizon_year=2100)
        assert ratio == np.inf


class TestRunAtLevel:
    """Run a single complexity level and return results."""

    @pytest.mark.slow
    def test_returns_expected_keys(self):
        result = run_at_level(level=1, lat=0, scenario="ssp245")
        assert "delta_t" in result
        assert "t_star" in result
        assert "warming_debt" in result
        assert "nee" in result

    @pytest.mark.slow
    def test_level_0_returns_pulse_only(self):
        result = run_at_level(level=0, lat=0, scenario="ssp245")
        # Level 0 = no offset, so delta_t should be the pulse warming
        assert result["delta_t"][5] > 0  # Warming from uncompensated pulse

    @pytest.mark.slow
    def test_level_1_reduces_warming(self):
        r0 = run_at_level(level=0, lat=0, scenario="ssp245")
        r1 = run_at_level(level=1, lat=0, scenario="ssp245")
        # Level 1 (carbon uptake) should reduce warming vs Level 0 (no offset)
        assert r1["warming_debt"] < r0["warming_debt"]


class TestProgressiveAnalysis:
    """Run all levels for one latitude."""

    @pytest.mark.slow
    def test_returns_dict_keyed_by_level(self):
        results = run_progressive_analysis(lat=0, scenario="ssp245")
        for level in range(7):
            assert level in results

    @pytest.mark.slow
    def test_warming_debt_generally_increases_with_complexity(self):
        results = run_progressive_analysis(lat=0, scenario="ssp245")
        # Level 4 (feedbacks) should have more warming debt than Level 1 (carbon only)
        assert results[4]["warming_debt"] >= results[1]["warming_debt"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_credit_analysis.py -v -m "not slow"`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement credit_analysis.py**

Create `src/nbs/credit_analysis.py`:
```python
"""Credit analysis: progressive complexity and carbon credit metrics.

Computes equivalence ratio (credits needed per tCO2 emitted),
warming debt (cumulative excess warming), and orchestrates
level-by-level analysis.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.albedo_module import compute_albedo_forcing_timeseries
from nbs.carbon_module import compute_nee_at_level
from nbs.fair_module import (
    compute_delta_t,
    compute_pulse_warming,
    find_breakeven_year,
    run_fair_baseline,
    run_fair_perturbed,
)
from nbs.parameters import COMPLEXITY_LEVELS, T_END, T_START

N_YEARS = T_END - T_START


def compute_warming_debt(delta_t: NDArray) -> float:
    """Cumulative excess warming while offset is not yet effective.

    Only counts years where ΔT > 0 (net warming despite offset).

    Parameters
    ----------
    delta_t : NDArray
        Temperature difference [K], shape (125,).

    Returns
    -------
    float
        Warming debt [K·yr]. Higher = worse offset.
    """
    positive = np.maximum(delta_t, 0.0)
    return float(np.sum(positive))


def compute_equivalence_ratio(
    pulse_dt: NDArray,
    offset_dt: NDArray,
    horizon_year: int = 2100,
) -> float:
    """How many credits needed per tCO2 emitted for net zero by horizon.

    Compares cumulative warming from pulse to cumulative cooling from
    1 credit of offset, up to the horizon year.

    Parameters
    ----------
    pulse_dt : NDArray
        ΔT from 1 tCO2 pulse [K], shape (125,).
    offset_dt : NDArray
        ΔT from 1 credit of offset [K], shape (125,).
        Should be negative (cooling) for an effective offset.
    horizon_year : int
        Year by which to achieve net zero warming (default 2100).

    Returns
    -------
    float
        Number of credits needed. Returns ``np.inf`` if offset is
        ineffective (zero or net warming).
    """
    idx = min(horizon_year - T_START, len(pulse_dt) - 1)

    # Integrated warming from pulse up to horizon
    pulse_integral = float(np.sum(pulse_dt[:idx + 1]))

    # Integrated cooling from 1 credit up to horizon
    offset_integral = float(np.sum(offset_dt[:idx + 1]))

    if offset_integral >= 0:
        # Offset is not cooling — worthless or harmful
        return np.inf

    # Ratio: how many offsets needed to cancel the pulse warming
    ratio = -pulse_integral / offset_integral

    if ratio <= 0:
        return np.inf

    return ratio


def run_at_level(
    level: int,
    lat: int,
    scenario: str = "ssp245",
    pulse_gtco2: float = 1.0,
    area_mha: float = 1.0,
) -> dict:
    """Run a single complexity level and return credit analysis results.

    Parameters
    ----------
    level : int
        Complexity level (0-6).
    lat : int
        Latitude in degrees N.
    scenario : str
        SSP background scenario.
    pulse_gtco2 : float
        Size of emission pulse to offset [GtCO2].
    area_mha : float
        Afforestation area [Mha].

    Returns
    -------
    dict
        Keys: delta_t, t_star, warming_debt, nee, equivalence_ratio_2100
    """
    pulse_dt = compute_pulse_warming(pulse_gtco2, scenario)
    baseline = run_fair_baseline(scenario)

    # Compute NEE at this complexity level
    nee = compute_nee_at_level(level, lat, area_mha)

    # Albedo: only included at Level 3+
    if level >= 3:
        # Use tropical_reforestation albedo values (afforestation context)
        albedo = compute_albedo_forcing_timeseries("tropical_reforestation", lat)
    else:
        albedo = np.zeros(N_YEARS)

    # Run FaIR with offset
    if level == 0:
        # No offset — just the pulse
        offset_dt = np.zeros(N_YEARS)
    else:
        perturbed = run_fair_perturbed(nee, albedo, scenario)
        offset_dt = compute_delta_t(perturbed, baseline)

    # Net effect: pulse warming + offset effect
    net_dt = pulse_dt + offset_dt

    t_star = find_breakeven_year(net_dt)
    warming_debt = compute_warming_debt(net_dt)
    eq_ratio = compute_equivalence_ratio(pulse_dt, offset_dt, horizon_year=2100)

    return {
        "delta_t": net_dt,
        "t_star": t_star,
        "warming_debt": warming_debt,
        "nee": nee,
        "equivalence_ratio_2100": eq_ratio,
        "pulse_dt": pulse_dt,
        "offset_dt": offset_dt,
    }


def run_progressive_analysis(
    lat: int,
    scenario: str = "ssp245",
    pulse_gtco2: float = 1.0,
    area_mha: float = 1.0,
) -> dict[int, dict]:
    """Run all complexity levels for one latitude.

    Parameters
    ----------
    lat : int
        Latitude in degrees N.
    scenario : str
        SSP background scenario.
    pulse_gtco2 : float
        Size of emission pulse [GtCO2].
    area_mha : float
        Afforestation area [Mha].

    Returns
    -------
    dict[int, dict]
        Results keyed by complexity level (0-6).
    """
    results = {}
    for level in COMPLEXITY_LEVELS:
        results[level] = run_at_level(level, lat, scenario, pulse_gtco2, area_mha)
    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_credit_analysis.py -v -m "not slow"`
Expected: Unit tests PASS. Then run slow tests:
Run: `uv run pytest tests/test_credit_analysis.py -v`
Expected: All tests PASS.

---

### Task 4: Credit Figures

**Files:**
- Create: `src/nbs/credit_figures.py`
- Create: `tests/test_credit_figures.py`

Six new figures for the progressive complexity narrative.

- [ ] **Step 1: Write tests**

Create `tests/test_credit_figures.py`:
```python
"""Tests for credit analysis figure generation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from nbs.credit_figures import (
    plot_progressive_delta_t,
    plot_equivalence_by_latitude,
    plot_breakeven_by_level,
    plot_warming_debt,
    plot_credit_depreciation,
    plot_credit_sobol,
)
from nbs.parameters import T_END, T_START

N_YEARS = T_END - T_START


@pytest.fixture
def mock_progressive_results():
    """Mock results from run_progressive_analysis for one latitude."""
    results = {}
    for level in range(7):
        scale = 1.0 + level * 0.1
        results[level] = {
            "delta_t": np.linspace(0.001, -0.001, N_YEARS) * scale,
            "t_star": 2060 + level * 5 if level < 5 else np.inf,
            "warming_debt": 0.05 * scale,
            "nee": np.full(N_YEARS, -0.01) / scale,
            "equivalence_ratio_2100": 1.0 + level * 0.5,
            "pulse_dt": np.ones(N_YEARS) * 0.001,
            "offset_dt": np.ones(N_YEARS) * -0.001 / scale,
        }
    return results


@pytest.fixture
def mock_lat_results():
    """Mock results keyed by (level, lat, scenario)."""
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
    """Mock results keyed by (level, lat, scenario) for SSP comparison."""
    results = {}
    for scenario in ["ssp126", "ssp245", "ssp370"]:
        ssp_mult = {"ssp126": 0.8, "ssp245": 1.0, "ssp370": 1.3}[scenario]
        for level in [6]:
            for lat in [0, 30, 60]:
                results[(level, lat, scenario)] = {
                    "equivalence_ratio_2100": 2.0 * ssp_mult + lat * 0.02,
                }
    return results


@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "figures"


class TestCreditFigures:
    def test_progressive_delta_t(self, mock_progressive_results, output_dir):
        path = plot_progressive_delta_t(mock_progressive_results, output_dir, lat=45)
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
            "param_names": ["B_max_scale", "Q10", "eta_CCS",
                           "p_disturb_scale", "mu", "albedo_scale"],
        }
        path = plot_credit_sobol(si, output_dir)
        assert Path(path).exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_credit_figures.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement credit_figures.py**

Create `src/nbs/credit_figures.py`:
```python
"""Figure generation for the carbon credit progressive complexity analysis."""

from __future__ import annotations

import os
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from nbs.parameters import LATITUDES, T_END, T_START

N_YEARS = T_END - T_START
YEARS = np.arange(T_START, T_END)

LEVEL_COLORS = {
    0: "#999999",
    1: "#a6cee3",
    2: "#1f78b4",
    3: "#b2df8a",
    4: "#33a02c",
    5: "#fb9a99",
    6: "#e31a1c",
}

LEVEL_LABELS = {
    0: "L0: No offset (fantasy)",
    1: "L1: Carbon uptake only",
    2: "L2: + Location-dependent growth",
    3: "L3: + Albedo",
    4: "L4: + Climate feedbacks",
    5: "L5: + SOC dynamics",
    6: "L6: Full model",
}


def _ensure_dir(output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def plot_progressive_delta_t(
    progressive_results: dict[int, dict],
    output_dir: str,
    lat: int = 45,
) -> str:
    """Fig 1: ΔT(t) at each complexity level — the progressive peeling-back."""
    output_dir = _ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(12, 6))

    for level in sorted(progressive_results.keys()):
        dt = progressive_results[level]["delta_t"]
        ax.plot(
            YEARS[:len(dt)],
            dt * 1000,
            color=LEVEL_COLORS.get(level, "black"),
            linewidth=2 if level in (0, 6) else 1.2,
            alpha=1.0 if level in (0, 6) else 0.7,
            label=LEVEL_LABELS.get(level, f"Level {level}"),
        )

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Year")
    ax.set_ylabel("Net ΔT [mK]  (pulse + offset)")
    ax.set_title(f"Progressive complexity: net warming from 1 tCO₂ + afforestation offset ({lat}°N)")
    ax.legend(fontsize=9, loc="best")
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "fig1_progressive_delta_t.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_equivalence_by_latitude(
    lat_results: dict[tuple, dict],
    output_dir: str,
) -> str:
    """Fig 2: Equivalence ratio vs latitude at Levels 1, 3, 6."""
    output_dir = _ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    for level in [1, 3, 6]:
        lats, ratios = [], []
        for lat in LATITUDES:
            key = (level, lat, "ssp245")
            if key in lat_results:
                ratio = lat_results[key]["equivalence_ratio_2100"]
                if np.isfinite(ratio):
                    lats.append(lat)
                    ratios.append(ratio)
        if lats:
            ax.plot(
                lats, ratios,
                color=LEVEL_COLORS[level],
                marker="o", markersize=8, linewidth=2,
                label=LEVEL_LABELS[level],
            )

    ax.axhline(1, color="black", linewidth=0.8, linestyle="--", label="Naive assumption (ratio = 1)")
    ax.set_xlabel("Latitude (°N)")
    ax.set_ylabel("Equivalence ratio (credits per tCO₂)")
    ax.set_title("How many credits do you actually need?")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "fig2_equivalence_by_latitude.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_breakeven_by_level(
    lat_results: dict[tuple, dict],
    output_dir: str,
) -> str:
    """Fig 3: Break-even year by latitude and complexity level."""
    output_dir = _ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    for level in [1, 3, 6]:
        lats, t_stars = [], []
        for lat in LATITUDES:
            key = (level, lat, "ssp245")
            if key in lat_results:
                t_star = lat_results[key]["t_star"]
                if np.isfinite(t_star):
                    lats.append(lat)
                    t_stars.append(t_star)
        if lats:
            ax.plot(
                lats, t_stars,
                color=LEVEL_COLORS[level],
                marker="s", markersize=8, linewidth=2,
                label=LEVEL_LABELS[level],
            )

    ax.set_xlabel("Latitude (°N)")
    ax.set_ylabel("Break-even year")
    ax.set_title("When does your carbon credit actually work?")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "fig3_breakeven_by_level.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_warming_debt(
    lat_results: dict[tuple, dict],
    output_dir: str,
) -> str:
    """Fig 4: Warming debt by latitude and level."""
    output_dir = _ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    bar_width = 0.25
    x = np.arange(len(LATITUDES))

    for i, level in enumerate([1, 3, 6]):
        debts = []
        for lat in LATITUDES:
            key = (level, lat, "ssp245")
            if key in lat_results:
                debts.append(lat_results[key]["warming_debt"])
            else:
                debts.append(0.0)
        ax.bar(
            x + i * bar_width, debts, bar_width,
            color=LEVEL_COLORS[level],
            label=LEVEL_LABELS[level],
        )

    ax.set_xticks(x + bar_width)
    ax.set_xticklabels([f"{l}°N" for l in LATITUDES])
    ax.set_ylabel("Warming debt [K·yr]")
    ax.set_title("Cumulative excess warming while waiting for offset")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")

    path = os.path.join(output_dir, "fig4_warming_debt.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_credit_depreciation(
    ssp_results: dict[tuple, dict],
    output_dir: str,
) -> str:
    """Fig 5: Credit depreciation — equivalence ratio under different SSPs."""
    output_dir = _ensure_dir(output_dir)
    fig, ax = plt.subplots(figsize=(10, 6))

    scenarios = ["ssp126", "ssp245", "ssp370"]
    ssp_colors = {"ssp126": "#4daf4a", "ssp245": "#377eb8", "ssp370": "#e41a1c"}
    ssp_labels = {"ssp126": "SSP1-2.6 (optimistic)", "ssp245": "SSP2-4.5", "ssp370": "SSP3-7.0 (pessimistic)"}

    for scenario in scenarios:
        lats, ratios = [], []
        for lat in LATITUDES:
            key = (6, lat, scenario)
            if key in ssp_results:
                ratio = ssp_results[key]["equivalence_ratio_2100"]
                if np.isfinite(ratio):
                    lats.append(lat)
                    ratios.append(ratio)
        if lats:
            ax.plot(
                lats, ratios,
                color=ssp_colors[scenario],
                marker="o", markersize=8, linewidth=2,
                label=ssp_labels[scenario],
            )

    ax.axhline(1, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Latitude (°N)")
    ax.set_ylabel("Equivalence ratio (credits per tCO₂)")
    ax.set_title("Credit depreciation: warming makes offsets less effective")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    path = os.path.join(output_dir, "fig5_credit_depreciation.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_credit_sobol(
    sobol_results: dict[str, Any],
    output_dir: str,
) -> str:
    """Fig 6: Sobol indices for equivalence ratio uncertainty."""
    output_dir = _ensure_dir(output_dir)

    s1 = sobol_results["S1"]
    st = sobol_results["ST"]
    s1_conf = sobol_results["S1_conf"]
    st_conf = sobol_results["ST_conf"]
    names = sobol_results["param_names"]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(names))
    w = 0.35

    ax.bar(x - w / 2, s1, w, yerr=s1_conf, label="First-order (S1)",
           color="#1f78b4", capsize=3)
    ax.bar(x + w / 2, st, w, yerr=st_conf, label="Total-order (ST)",
           color="#fb9a99", capsize=3)

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=30, ha="right")
    ax.set_ylabel("Sobol index")
    ax.set_title("What drives uncertainty in carbon credit value?")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    path = os.path.join(output_dir, "fig6_credit_sobol.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_credit_figures.py -v`
Expected: All 7 tests PASS.

---

### Task 5: Update README

**Files:**
- Modify: `README.md`

Update to reflect the carbon credit debunking framing and new functionality.

- [ ] **Step 1: Update README**

Add a new section after "Quick start" called "Carbon Credit Analysis" documenting the progressive complexity workflow:

```python
from nbs.credit_analysis import run_progressive_analysis, run_at_level

# Run all 7 complexity levels for afforestation at 45°N
results = run_progressive_analysis(lat=45, scenario="ssp245")

for level, r in results.items():
    print(f"Level {level}: t*={r['t_star']:.0f}, debt={r['warming_debt']:.4f} K·yr, "
          f"equiv_ratio={r['equivalence_ratio_2100']:.1f}")
```

Also document the new metrics (equivalence ratio, warming debt) and the complexity levels table.

- [ ] **Step 2: Run all tests to confirm nothing is broken**

Run: `uv run pytest -v -m "not slow"`
Expected: All tests PASS (existing 91 + new ~30 = ~120+).

---

## Self-Review

**Spec coverage:**
- [x] Pulse emission function (Task 1)
- [x] Complexity levels 0-6 in carbon module (Task 2)
- [x] Equivalence ratio metric (Task 3)
- [x] Warming debt metric (Task 3)
- [x] Level runner + progressive analysis (Task 3)
- [x] 6 new figures (Task 4)
- [x] Updated README (Task 5)

**Placeholder scan:** No TBDs found.

**Type consistency:** `compute_nee_at_level` returns NDArray(125,), consumed by `run_at_level` which passes it to `run_fair_perturbed`. `compute_pulse_warming` returns NDArray(125,), consumed by `run_at_level`. All consistent.

**Existing tests preserved:** No existing functions are modified, only new functions added. All 103 existing tests will keep passing.
