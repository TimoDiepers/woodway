# NBS Climate Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a transparent, reproducible framework that computes time-dependent temperature impact ΔT(t) for four forest-based climate interventions using FaIR v2.0, with break-even analysis and sensitivity analysis.

**Architecture:** Three modules (carbon dynamics, albedo forcing, FaIR coupling) feed into a scenario runner that loops over interventions × latitudes × land uses × SSPs. Each module is a standalone Python module with clear inputs/outputs. Results are analyzed via Sobol sensitivity and visualized in publication-quality figures.

**Tech Stack:** Python 3.11+, uv (package management), FaIR v2.1, NumPy, SciPy, xarray, matplotlib, SALib, pytest

---

## File Structure

```
nbs/
├── pyproject.toml                    # uv project config with all dependencies
├── src/
│   └── nbs/
│       ├── __init__.py
│       ├── carbon_module.py          # Biomass growth, SOC, soil respiration, disturbance, NEE
│       ├── albedo_module.py          # Albedo forcing computation
│       ├── fair_module.py            # FaIR baseline + perturbed runs, ΔT, break-even
│       ├── scenario_runner.py        # Full scenario loop over all combinations
│       ├── sensitivity.py            # OAT + Sobol sensitivity analysis
│       ├── figures.py                # All publication figures
│       └── parameters.py             # Central parameter definitions (growth params, albedo values, etc.)
├── tests/
│   ├── test_carbon_module.py
│   ├── test_albedo_module.py
│   ├── test_fair_module.py
│   ├── test_scenario_runner.py
│   └── test_sensitivity.py
├── notebooks/
│   └── 01_single_intervention_demo.ipynb
└── results/                          # Generated outputs (gitignored)
```

---

### Task 1: Project Setup and Dependencies

**Files:**
- Modify: `pyproject.toml`
- Create: `src/nbs/__init__.py`

- [ ] **Step 1: Add dependencies to pyproject.toml**

```toml
[project]
name = "nbs"
version = "0.1.0"
description = "Time-explicit framework for comparing forest-based climate interventions"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fair>=2.1.0,<3",
    "numpy>=1.24",
    "scipy>=1.10",
    "xarray>=2023.1",
    "matplotlib>=3.7",
    "SALib>=1.4",
    "pandas>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create package init**

Create `src/nbs/__init__.py`:
```python
"""NBS Climate Framework: Time-explicit comparison of forest-based climate interventions."""
```

- [ ] **Step 3: Install dependencies**

Run: `uv sync`
Expected: All packages install successfully, including `fair`.

- [ ] **Step 4: Verify FaIR import works**

Run: `uv run python -c "import fair; print(fair.__version__)"`
Expected: Prints `2.1.x` or similar.

- [ ] **Step 5: Create results directory with .gitkeep**

```bash
mkdir -p results tests notebooks
touch results/.gitkeep
```

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock src/ results/.gitkeep tests/ notebooks/
git commit -m "feat: initialize project with uv and FaIR dependencies"
```

---

### Task 2: Central Parameters Module

**Files:**
- Create: `src/nbs/parameters.py`
- Create: `tests/test_parameters.py`

This module holds all parameter lookups used across the framework: growth parameters, SOC values, albedo values, disturbance probabilities, and physical constants.

- [ ] **Step 1: Write tests for parameter lookups**

Create `tests/test_parameters.py`:
```python
import pytest
import numpy as np
from nbs.parameters import (
    get_growth_params,
    get_soc_params,
    get_disturbance_probability,
    get_albedo_values,
    INTERVENTIONS,
    LATITUDES,
    LAND_USES,
    SCENARIOS,
)


def test_growth_params_tropical_reforestation():
    b_max, k, p = get_growth_params("tropical_reforestation")
    assert 180 <= b_max <= 220
    assert 0.06 <= k <= 0.10
    assert 2.0 <= p <= 3.0


def test_growth_params_boreal_afforestation():
    b_max, k, p = get_growth_params("boreal_afforestation")
    assert 80 <= b_max <= 120
    assert 0.02 <= k <= 0.04
    assert 1.5 <= p <= 2.5


def test_growth_params_beccs():
    b_max, k, p = get_growth_params("beccs")
    assert 40 <= b_max <= 60
    assert 0.10 <= k <= 0.15
    assert 1.5 <= p <= 2.0


def test_growth_params_invalid():
    with pytest.raises(KeyError):
        get_growth_params("nonexistent")


def test_soc_params():
    soc_forest, soc_initial = get_soc_params("tropical_reforestation", lat=0)
    assert soc_forest > 0
    assert soc_initial > 0


def test_disturbance_probability():
    years = np.arange(2025, 2150)
    p_dist = get_disturbance_probability("tropical_reforestation", lat=0, years=years)
    assert p_dist.shape == years.shape
    assert np.all(p_dist >= 0)
    assert np.all(p_dist <= 1)


def test_albedo_values_tropical():
    delta_f = get_albedo_values("tropical_reforestation", lat=0)
    # Tropical reforestation: small negative forcing (slight cooling from albedo)
    assert -1.0 < delta_f < 0.5


def test_albedo_values_boreal():
    delta_f = get_albedo_values("boreal_afforestation", lat=60)
    # Boreal afforestation: positive forcing (warming from snow masking)
    assert 0.5 < delta_f < 2.0


def test_albedo_values_avoided_deforestation():
    delta_f = get_albedo_values("avoided_deforestation", lat=0)
    # No land use change => zero albedo forcing
    assert delta_f == 0.0


def test_constants_exist():
    assert len(INTERVENTIONS) == 4
    assert len(LATITUDES) == 5
    assert len(LAND_USES) == 3
    assert len(SCENARIOS) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_parameters.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.parameters'`

- [ ] **Step 3: Implement parameters module**

Create `src/nbs/parameters.py`:
```python
"""Central parameter definitions for the NBS climate framework.

All parameter values are sourced from the study design document.
Growth parameters: Cook-Patton et al. (2020), IPCC AR6 WGIII.
Albedo values: MODIS MCD43A3 processed values, from study design Table (Section 5.2).
SOC values: SoilGrids 2.0 (Poggio et al. 2021).
Disturbance: Anderegg et al. (2022), IPCC AR6 Chapter 5.
"""

import numpy as np
from numpy.typing import NDArray


INTERVENTIONS = [
    "tropical_reforestation",
    "boreal_afforestation",
    "avoided_deforestation",
    "beccs",
]

LATITUDES = [0, 15, 30, 45, 60]

LAND_USES = ["cropland", "grassland", "degraded_forest"]

SCENARIOS = ["ssp126", "ssp245", "ssp370"]

# Study time range
T_START = 2025
T_END = 2150

# Physical constants
S0 = 1361.0  # Solar constant [W/m^2]


# --- Growth parameters (Chapman-Richards) ---
# B_max [tC/ha], k [yr^-1], p [-]
# Using midpoint of ranges from study design Section 4.1
_GROWTH_PARAMS: dict[str, tuple[float, float, float]] = {
    "tropical_reforestation": (200.0, 0.08, 2.5),
    "boreal_afforestation": (100.0, 0.03, 2.0),
    "beccs": (50.0, 0.12, 1.75),
}


def get_growth_params(intervention: str) -> tuple[float, float, float]:
    """Return (B_max, k, p) for Chapman-Richards growth model.

    Raises KeyError if intervention has no growth model (e.g. avoided_deforestation).
    """
    return _GROWTH_PARAMS[intervention]


# --- SOC parameters ---
# (SOC_forest [tC/ha], SOC_initial [tC/ha]) by intervention and latitude
# Values representative of literature; SOC_initial depends on prior land use
_SOC_PARAMS: dict[str, dict[int, tuple[float, float]]] = {
    "tropical_reforestation": {
        0: (120.0, 80.0),
        15: (110.0, 75.0),
    },
    "boreal_afforestation": {
        45: (90.0, 110.0),  # Note: SOC_initial > SOC_forest (grassland has more SOC)
        60: (85.0, 120.0),
    },
    "avoided_deforestation": {
        0: (120.0, 120.0),  # No change — forest stays forest
        15: (110.0, 110.0),
    },
    "beccs": {
        30: (60.0, 70.0),
        45: (65.0, 75.0),
    },
}


def get_soc_params(intervention: str, lat: int) -> tuple[float, float]:
    """Return (SOC_forest, SOC_initial) in tC/ha.

    Falls back to nearest available latitude if exact match not found.
    """
    if intervention in _SOC_PARAMS:
        params = _SOC_PARAMS[intervention]
        if lat in params:
            return params[lat]
        # Fall back to nearest latitude
        available = list(params.keys())
        nearest = min(available, key=lambda x: abs(x - lat))
        return params[nearest]
    # Default fallback
    return (100.0, 90.0)


# --- Disturbance probability ---
# Base annual probability of stand-replacing disturbance
_DISTURBANCE_BASE: dict[str, float] = {
    "tropical_reforestation": 0.005,   # 0.5% per year
    "boreal_afforestation": 0.01,      # 1% per year (fire-prone)
    "avoided_deforestation": 0.002,    # Low (intact forest)
    "beccs": 0.003,                    # Managed plantation
}


def get_disturbance_probability(
    intervention: str, lat: int, years: NDArray[np.int_]
) -> NDArray[np.float64]:
    """Return annual disturbance probability array, increasing with climate change.

    Disturbance probability increases linearly by 50% from 2025 to 2150,
    reflecting increased fire/pest risk under warming.
    """
    base = _DISTURBANCE_BASE.get(intervention, 0.005)
    # Linear increase: 1.0x at 2025, 1.5x at 2150
    scale = 1.0 + 0.5 * (years - T_START) / (T_END - T_START)
    return base * scale


# --- Albedo forcing ---
# ΔF_α [W/m^2] from study design Section 5.2 Table
# Positive = warming, Negative = cooling
_ALBEDO_FORCING: dict[str, dict[int, float]] = {
    "tropical_reforestation": {
        0: -0.3,
        15: -0.25,
        30: -0.15,  # Extrapolated
    },
    "boreal_afforestation": {
        45: 0.8,
        60: 1.15,  # Midpoint of 0.8-1.5
    },
    "avoided_deforestation": {
        0: 0.0,
        15: 0.0,
        30: 0.0,
        45: 0.0,
        60: 0.0,
    },
    "beccs": {
        0: -0.15,
        15: -0.15,
        30: -0.2,
        45: 0.0,   # Interpolated
        60: 0.4,
    },
}


def get_albedo_values(intervention: str, lat: int) -> float:
    """Return ΔF_α [W/m^2] for the intervention at given latitude.

    Positive = warming (reduced reflection). Negative = cooling.
    """
    if intervention in _ALBEDO_FORCING:
        params = _ALBEDO_FORCING[intervention]
        if lat in params:
            return params[lat]
        available = list(params.keys())
        nearest = min(available, key=lambda x: abs(x - lat))
        return params[nearest]
    return 0.0


# --- Deforestation rate for Avoided Deforestation ---
DEFORESTATION_RATE = 0.005  # 0.5% per year baseline (Global Forest Watch)
C_FOREST_TROPICAL = 200.0  # tC/ha standing carbon in intact tropical forest

# --- BECCS parameters ---
BECCS_HARVEST_PERIOD = 15      # years (poplar short-rotation)
BECCS_CCS_EFFICIENCY = 0.87   # η_CCS
BECCS_PROCESS_EMISSION_FRAC = 0.06  # 6% of gross uptake

# --- SOC dynamics ---
SOC_MU = 0.03  # SOC equilibration rate [yr^-1], ~30-50 yr time constant

# --- Soil respiration ---
SOIL_RESP_Q10 = 2.0       # Temperature sensitivity
SOIL_RESP_T0 = 10.0       # Reference temperature [°C]
# Base soil respiration [tCO2/ha/yr] at T0, by latitude
SOIL_RESP_BASE: dict[int, float] = {
    0: 15.0,
    15: 12.0,
    30: 8.0,
    45: 5.0,
    60: 3.0,
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_parameters.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/nbs/parameters.py tests/test_parameters.py
git commit -m "feat: add central parameters module with growth, SOC, albedo, disturbance lookups"
```

---

### Task 3: Carbon Module

**Files:**
- Create: `src/nbs/carbon_module.py`
- Create: `tests/test_carbon_module.py`

Implements Chapman-Richards biomass growth, SOC dynamics, soil respiration, disturbance, and NEE computation for all four interventions.

- [ ] **Step 1: Write tests for carbon module**

Create `tests/test_carbon_module.py`:
```python
import pytest
import numpy as np
from nbs.carbon_module import (
    compute_biomass_growth,
    compute_soc_dynamics,
    compute_soil_respiration,
    compute_disturbance_loss,
    compute_nee_timeseries,
)


class TestBiomassGrowth:
    def test_starts_at_zero(self):
        B = compute_biomass_growth(B_max=200, k=0.08, p=2.5, t=np.array([0]))
        assert B[0] == pytest.approx(0.0, abs=1e-6)

    def test_approaches_bmax(self):
        t = np.arange(0, 300)
        B = compute_biomass_growth(B_max=200, k=0.08, p=2.5, t=t)
        assert B[-1] == pytest.approx(200.0, rel=0.01)

    def test_monotonically_increasing(self):
        t = np.arange(0, 150)
        B = compute_biomass_growth(B_max=200, k=0.08, p=2.5, t=t)
        assert np.all(np.diff(B) >= 0)

    def test_shape_matches_input(self):
        t = np.arange(0, 125)
        B = compute_biomass_growth(B_max=100, k=0.03, p=2.0, t=t)
        assert B.shape == t.shape


class TestSOCDynamics:
    def test_starts_at_initial(self):
        soc = compute_soc_dynamics(
            soc_forest=120.0, soc_initial=80.0, mu=0.03, t=np.array([0])
        )
        assert soc[0] == pytest.approx(80.0, abs=1e-6)

    def test_approaches_forest_equilibrium(self):
        t = np.arange(0, 500)
        soc = compute_soc_dynamics(soc_forest=120.0, soc_initial=80.0, mu=0.03, t=t)
        assert soc[-1] == pytest.approx(120.0, rel=0.01)

    def test_decreasing_soc_when_initial_higher(self):
        """Boreal case: grassland SOC > forest SOC, so SOC decreases initially."""
        t = np.arange(0, 100)
        soc = compute_soc_dynamics(soc_forest=85.0, soc_initial=120.0, mu=0.03, t=t)
        assert soc[0] > soc[10]  # Decreasing
        assert soc[-1] == pytest.approx(85.0, rel=0.05)


class TestSoilRespiration:
    def test_increases_with_temperature(self):
        r_low = compute_soil_respiration(
            r_base=5.0, q10=2.0, t0=10.0, temperature=10.0
        )
        r_high = compute_soil_respiration(
            r_base=5.0, q10=2.0, t0=10.0, temperature=20.0
        )
        assert r_high > r_low

    def test_at_reference_temp(self):
        r = compute_soil_respiration(r_base=5.0, q10=2.0, t0=10.0, temperature=10.0)
        assert r == pytest.approx(5.0)


class TestDisturbanceLoss:
    def test_proportional_to_biomass(self):
        B = np.array([100.0, 100.0])
        p_dist = np.array([0.01, 0.02])
        D = compute_disturbance_loss(B, p_dist)
        assert D[1] == pytest.approx(2 * D[0])

    def test_zero_when_no_disturbance(self):
        B = np.array([100.0])
        p_dist = np.array([0.0])
        D = compute_disturbance_loss(B, p_dist)
        assert D[0] == pytest.approx(0.0)


class TestNEETimeseries:
    def test_tropical_reforestation_is_net_removal(self):
        """TR should be net CO2 removal (negative NEE in atmospheric convention)."""
        nee = compute_nee_timeseries("tropical_reforestation", lat=0, area_mha=1.0)
        # Cumulative should be negative (removal from atmosphere)
        cumulative = np.cumsum(nee)
        assert cumulative[-1] < 0

    def test_output_shape(self):
        nee = compute_nee_timeseries("tropical_reforestation", lat=0, area_mha=1.0)
        expected_years = 2150 - 2025
        assert nee.shape == (expected_years,)

    def test_output_units_reasonable(self):
        """1 Mha of tropical forest should remove order of 0.01-0.5 GtCO2/yr at peak."""
        nee = compute_nee_timeseries("tropical_reforestation", lat=0, area_mha=1.0)
        peak_removal = np.min(nee)  # Most negative = peak removal
        assert -1.0 < peak_removal < 0.0

    def test_avoided_deforestation_immediate_benefit(self):
        """AD has immediate benefit — no growth lag."""
        nee = compute_nee_timeseries("avoided_deforestation", lat=0, area_mha=1.0)
        # First year should already show removal
        assert nee[0] < 0

    def test_beccs_has_harvest_cycles(self):
        """BECCS NEE should show periodic spikes from harvest events."""
        nee = compute_nee_timeseries("beccs", lat=30, area_mha=1.0)
        # There should be some years with larger negative values (harvest + CCS)
        assert np.min(nee) < np.mean(nee)

    def test_area_scaling(self):
        """Doubling area should double NEE."""
        nee_1 = compute_nee_timeseries("tropical_reforestation", lat=0, area_mha=1.0)
        nee_2 = compute_nee_timeseries("tropical_reforestation", lat=0, area_mha=2.0)
        np.testing.assert_allclose(nee_2, 2 * nee_1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_carbon_module.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.carbon_module'`

- [ ] **Step 3: Implement carbon module**

Create `src/nbs/carbon_module.py`:
```python
"""Module 1: Carbon dynamics for forest-based climate interventions.

Implements:
- Chapman-Richards biomass growth model
- Soil organic carbon (SOC) equilibration dynamics
- Temperature-sensitive soil respiration
- Stochastic disturbance loss
- Net Ecosystem Exchange (NEE) timeseries computation
"""

import numpy as np
from numpy.typing import NDArray

from nbs.parameters import (
    T_START,
    T_END,
    SOC_MU,
    SOIL_RESP_Q10,
    SOIL_RESP_T0,
    SOIL_RESP_BASE,
    DEFORESTATION_RATE,
    C_FOREST_TROPICAL,
    BECCS_HARVEST_PERIOD,
    BECCS_CCS_EFFICIENCY,
    BECCS_PROCESS_EMISSION_FRAC,
    get_growth_params,
    get_soc_params,
    get_disturbance_probability,
)


def compute_biomass_growth(
    B_max: float, k: float, p: float, t: NDArray[np.int_]
) -> NDArray[np.float64]:
    """Chapman-Richards growth model: B(t) = B_max * (1 - exp(-k*t))^p [tC/ha]."""
    return B_max * (1 - np.exp(-k * t)) ** p


def compute_soc_dynamics(
    soc_forest: float, soc_initial: float, mu: float, t: NDArray[np.int_]
) -> NDArray[np.float64]:
    """Exponential SOC equilibration: SOC(t) = SOC_forest + (SOC_initial - SOC_forest) * exp(-mu*t) [tC/ha]."""
    return soc_forest + (soc_initial - soc_forest) * np.exp(-mu * t)


def compute_soil_respiration(
    r_base: float, q10: float, t0: float, temperature: float | NDArray[np.float64]
) -> float | NDArray[np.float64]:
    """Temperature-sensitive soil respiration: R = R_base * Q10^((T-T0)/10) [tCO2/ha/yr]."""
    return r_base * q10 ** ((temperature - t0) / 10.0)


def compute_disturbance_loss(
    biomass: NDArray[np.float64], p_disturb: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Disturbance-driven biomass loss: D(t) = p_disturb(t) * B(t) [tC/ha/yr]."""
    return p_disturb * biomass


def _get_temperature_trajectory(lat: int, years: NDArray[np.int_]) -> NDArray[np.float64]:
    """Simple temperature trajectory: base temp + linear warming.

    Uses a simplified warming assumption (~2°C by 2100 for SSP2-4.5 equivalent).
    Latitude-dependent base temperature.
    """
    base_temps = {0: 25.0, 15: 22.0, 30: 17.0, 45: 10.0, 60: 2.0}
    base = base_temps.get(lat, 15.0)
    # Linear warming: +2°C over 2025-2150
    warming = 2.0 * (years - T_START) / (T_END - T_START)
    return base + warming


def compute_nee_timeseries(
    intervention: str, lat: int, area_mha: float = 1.0
) -> NDArray[np.float64]:
    """Compute annual NEE timeseries for an intervention.

    Parameters
    ----------
    intervention : str
        One of: "tropical_reforestation", "boreal_afforestation",
                "avoided_deforestation", "beccs"
    lat : int
        Latitude in degrees North
    area_mha : float
        Area in million hectares (default 1.0)

    Returns
    -------
    nee_gt : NDArray[np.float64]
        Annual NEE [GtCO2/yr], shape (125,) for 2025-2150.
        Negative = removal from atmosphere.
    """
    years = np.arange(T_START, T_END)
    t = years - T_START  # Time since intervention start
    n = len(years)

    if intervention == "avoided_deforestation":
        return _compute_nee_avoided_deforestation(lat, years, t, n, area_mha)

    # --- Biomass growth ---
    B_max, k, p = get_growth_params(intervention)
    B = compute_biomass_growth(B_max, k, p, t)
    dBdt = np.gradient(B)

    # --- SOC dynamics ---
    soc_forest, soc_initial = get_soc_params(intervention, lat)
    soc = compute_soc_dynamics(soc_forest, soc_initial, SOC_MU, t)
    dSOCdt = np.gradient(soc)

    # --- Soil respiration ---
    temps = _get_temperature_trajectory(lat, years)
    r_base = SOIL_RESP_BASE.get(lat, 5.0)
    r_soil = compute_soil_respiration(r_base, SOIL_RESP_Q10, SOIL_RESP_T0, temps)

    # --- Disturbance ---
    p_dist = get_disturbance_probability(intervention, lat, years)
    D = compute_disturbance_loss(B, p_dist)

    # --- NEE [tCO2/ha/yr], negative = removal ---
    # Carbon uptake (biomass + SOC growth) converted to CO2, minus losses
    nee = -((dBdt + dSOCdt) * (44.0 / 12.0) - r_soil - D * (44.0 / 12.0))
    # Sign: positive dBdt = carbon uptake = negative NEE (removal)
    # Actually: NEE convention here: negative = removal from atmosphere
    # nee = -(net_uptake) where net_uptake = (dB/dt + dSOC/dt)*(44/12) - R_soil - D*(44/12)
    # Let's be explicit:
    net_uptake = (dBdt + dSOCdt) * (44.0 / 12.0) - r_soil - D * (44.0 / 12.0)
    nee = -net_uptake  # Negative means removal from atmosphere

    # --- BECCS: add CCS removal at harvest ---
    if intervention == "beccs":
        harvest_flux = np.zeros(n)
        for hy in range(BECCS_HARVEST_PERIOD, n, BECCS_HARVEST_PERIOD):
            # At harvest: remove biomass, capture CO2
            captured = B[hy] * BECCS_CCS_EFFICIENCY * (44.0 / 12.0)
            process_emissions = captured * BECCS_PROCESS_EMISSION_FRAC
            harvest_flux[hy] = -(captured - process_emissions)
        nee = nee + harvest_flux

    # Scale to area [GtCO2/yr]: tCO2/ha * 1e6 ha/Mha * 1e-9 Gt/t = 1e-3
    nee_gt = nee * area_mha * 1e-3

    return nee_gt


def _compute_nee_avoided_deforestation(
    lat: int,
    years: NDArray[np.int_],
    t: NDArray[np.int_],
    n: int,
    area_mha: float,
) -> NDArray[np.float64]:
    """NEE for avoided deforestation: prevented emissions from baseline deforestation."""
    # Each year, lambda(t) fraction of forest would have been lost
    # Prevented emission = lambda * C_forest * (44/12) [tCO2/ha/yr]
    prevented = DEFORESTATION_RATE * C_FOREST_TROPICAL * (44.0 / 12.0)
    nee = np.full(n, -prevented)  # Negative = removal (prevented emission)

    # Scale to area
    nee_gt = nee * area_mha * 1e-3

    return nee_gt
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_carbon_module.py -v`
Expected: All tests PASS. If any fail, debug and adjust parameter values or sign conventions.

- [ ] **Step 5: Commit**

```bash
git add src/nbs/carbon_module.py tests/test_carbon_module.py
git commit -m "feat: add carbon dynamics module with biomass growth, SOC, NEE"
```

---

### Task 4: Albedo Module

**Files:**
- Create: `src/nbs/albedo_module.py`
- Create: `tests/test_albedo_module.py`

Simple module that computes time-varying albedo forcing with a transition phase.

- [ ] **Step 1: Write tests for albedo module**

Create `tests/test_albedo_module.py`:
```python
import numpy as np
import pytest
from nbs.albedo_module import compute_albedo_forcing_timeseries


class TestAlbedoForcingTimeseries:
    def test_avoided_deforestation_zero(self):
        """AD has no land use change, so zero albedo forcing."""
        rf = compute_albedo_forcing_timeseries("avoided_deforestation", lat=0)
        np.testing.assert_allclose(rf, 0.0)

    def test_tropical_reforestation_negative(self):
        """TR at equator has small negative forcing (slightly darker, but minor)."""
        rf = compute_albedo_forcing_timeseries("tropical_reforestation", lat=0)
        assert rf[-1] < 0  # Cooling (slightly)

    def test_boreal_afforestation_positive(self):
        """BA at 60N has strong positive forcing (snow masking)."""
        rf = compute_albedo_forcing_timeseries("boreal_afforestation", lat=60)
        assert rf[-1] > 0  # Warming

    def test_transition_phase(self):
        """Forcing should ramp up from 0 over first few years."""
        rf = compute_albedo_forcing_timeseries("boreal_afforestation", lat=60)
        assert rf[0] == pytest.approx(0.0)  # Starts at zero
        assert abs(rf[5]) > 0  # Has ramped up by year 5

    def test_constant_after_transition(self):
        """Forcing should be constant after transition period."""
        rf = compute_albedo_forcing_timeseries("tropical_reforestation", lat=0)
        # After year 3, should be constant
        assert rf[10] == pytest.approx(rf[50])

    def test_output_shape(self):
        rf = compute_albedo_forcing_timeseries("tropical_reforestation", lat=0)
        assert rf.shape == (125,)  # 2025-2150
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_albedo_module.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement albedo module**

Create `src/nbs/albedo_module.py`:
```python
"""Module 2: Albedo forcing computation.

Computes radiative forcing timeseries from surface albedo change
when land use transitions occur. Uses hardcoded values from MODIS MCD43A3
analysis (study design Section 5.2).
"""

import numpy as np
from numpy.typing import NDArray

from nbs.parameters import T_START, T_END, get_albedo_values


TRANSITION_YEARS = 3  # Linear ramp-up period for albedo change


def compute_albedo_forcing_timeseries(
    intervention: str, lat: int, transition_years: int = TRANSITION_YEARS
) -> NDArray[np.float64]:
    """Compute albedo radiative forcing timeseries [W/m^2].

    Parameters
    ----------
    intervention : str
        Intervention type
    lat : int
        Latitude in degrees North
    transition_years : int
        Number of years for linear ramp-up from 0 to full forcing

    Returns
    -------
    rf_timeseries : NDArray[np.float64]
        Albedo forcing [W/m^2], shape (125,). Positive = warming.
    """
    n_years = T_END - T_START
    delta_f_final = get_albedo_values(intervention, lat)

    if delta_f_final == 0.0:
        return np.zeros(n_years)

    rf = np.full(n_years, delta_f_final)

    # Linear ramp-up during transition
    for i in range(min(transition_years, n_years)):
        rf[i] = delta_f_final * (i / transition_years)

    return rf
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_albedo_module.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/nbs/albedo_module.py tests/test_albedo_module.py
git commit -m "feat: add albedo module with transition phase forcing"
```

---

### Task 5: FaIR Coupling Module

**Files:**
- Create: `src/nbs/fair_module.py`
- Create: `tests/test_fair_module.py`

This is the core integration module. It runs FaIR baseline and perturbed scenarios, computes ΔT(t), and finds break-even years.

- [ ] **Step 1: Write tests for FaIR module**

Create `tests/test_fair_module.py`:
```python
import numpy as np
import pytest
from nbs.fair_module import (
    run_fair_baseline,
    run_fair_perturbed,
    compute_delta_t,
    find_breakeven_year,
)


@pytest.fixture(scope="module")
def baseline_temperature():
    """Run baseline once for all tests (slow)."""
    return run_fair_baseline(scenario="ssp245")


class TestFairBaseline:
    def test_baseline_returns_array(self, baseline_temperature):
        assert isinstance(baseline_temperature, np.ndarray)

    def test_baseline_shape(self, baseline_temperature):
        # Should have 125 years (2025-2150) or similar
        assert len(baseline_temperature) > 100

    def test_baseline_warming(self, baseline_temperature):
        """SSP2-4.5 should show warming over the period."""
        assert baseline_temperature[-1] > baseline_temperature[0]


class TestFairPerturbed:
    def test_removal_causes_cooling(self, baseline_temperature):
        """Negative emissions should reduce temperature vs baseline."""
        n = len(baseline_temperature)
        # Constant removal of 0.1 GtCO2/yr
        nee = np.full(n, -0.1)
        albedo_rf = np.zeros(n)
        t_pert = run_fair_perturbed(nee, albedo_rf, scenario="ssp245")
        delta_t = t_pert - baseline_temperature
        # By end, should be cooler than baseline
        assert delta_t[-1] < 0

    def test_warming_albedo_increases_temp(self, baseline_temperature):
        """Positive albedo forcing should warm relative to baseline."""
        n = len(baseline_temperature)
        nee = np.zeros(n)
        albedo_rf = np.full(n, 1.0)  # 1 W/m^2 constant warming
        t_pert = run_fair_perturbed(nee, albedo_rf, scenario="ssp245")
        delta_t = t_pert - baseline_temperature
        assert delta_t[-1] > 0


class TestDeltaT:
    def test_delta_t_shape(self, baseline_temperature):
        n = len(baseline_temperature)
        nee = np.full(n, -0.05)
        albedo_rf = np.zeros(n)
        t_pert = run_fair_perturbed(nee, albedo_rf, scenario="ssp245")
        delta_t = compute_delta_t(t_pert, baseline_temperature)
        assert delta_t.shape == baseline_temperature.shape


class TestBreakeven:
    def test_pure_removal_immediate_breakeven(self, baseline_temperature):
        """Pure removal (no albedo penalty) should break even quickly."""
        n = len(baseline_temperature)
        nee = np.full(n, -0.1)
        albedo_rf = np.zeros(n)
        t_pert = run_fair_perturbed(nee, albedo_rf, scenario="ssp245")
        delta_t = compute_delta_t(t_pert, baseline_temperature)
        t_star = find_breakeven_year(delta_t)
        assert t_star < 2050

    def test_strong_albedo_may_never_breakeven(self, baseline_temperature):
        """Strong warming albedo with weak removal may never break even."""
        n = len(baseline_temperature)
        nee = np.full(n, -0.001)  # Very weak removal
        albedo_rf = np.full(n, 2.0)  # Very strong warming
        t_pert = run_fair_perturbed(nee, albedo_rf, scenario="ssp245")
        delta_t = compute_delta_t(t_pert, baseline_temperature)
        t_star = find_breakeven_year(delta_t)
        assert t_star == np.inf
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_fair_module.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement FaIR module**

Create `src/nbs/fair_module.py`:
```python
"""Module 3: FaIR v2.0 coupling for temperature response.

Runs FaIR baseline (unperturbed SSP) and perturbed scenarios
with NEE emissions modifications and external albedo forcing.
Computes ΔT(t) and break-even year t*.
"""

import numpy as np
from numpy.typing import NDArray
import fair
from fair import FAIR
from fair.interface import fill, initialise
from fair.io import read_properties
import pandas as pd

from nbs.parameters import T_START, T_END


def _create_fair_instance(scenario: str) -> FAIR:
    """Create and configure a FaIR instance for the given scenario."""
    f = FAIR(ch4_method="Thornhill2021")
    f.define_time(1750, T_END, 1)
    f.define_scenarios([scenario])
    f.define_configs(["central"])

    # Use RCMIP species
    species, properties = read_properties()
    f.define_species(species, properties)
    f.allocate()

    # Fill with RCMIP data
    fill(f.climate_configs, filename="AR6_WG1", config="central")
    fill(f.emissions, filename="ssp_emissions_1750", scenario=scenario)
    fill(f.forcing, filename="volcanic_ERF")
    fill(f.forcing, filename="solar_amplitude")

    initialise(f.concentration, f.species, f.properties)
    initialise(f.forcing, f.species, f.properties)
    initialise(f.temperature, f.species, f.properties)
    initialise(f.airborne_emissions, f.species, f.properties)
    initialise(f.cumulative_emissions, f.species, f.properties)

    return f


def run_fair_baseline(scenario: str = "ssp245") -> NDArray[np.float64]:
    """Run unperturbed FaIR for the given SSP scenario.

    Returns
    -------
    temperature : NDArray[np.float64]
        Global mean surface temperature anomaly [K],
        trimmed to study period (T_START to T_END).
    """
    f = _create_fair_instance(scenario)
    f.run()

    # Extract temperature: sum over layers, select scenario and config
    temp = f.temperature.sel(
        scenario=scenario, config="central", layer=0
    ).values

    # Trim to study period
    # FaIR time axis starts at 1750
    start_idx = T_START - 1750
    end_idx = T_END - 1750
    return temp[start_idx:end_idx]


def run_fair_perturbed(
    nee_gtco2_yr: NDArray[np.float64],
    albedo_rf_wm2: NDArray[np.float64],
    scenario: str = "ssp245",
) -> NDArray[np.float64]:
    """Run FaIR with NEE perturbation and albedo forcing.

    Parameters
    ----------
    nee_gtco2_yr : NDArray[np.float64]
        NEE timeseries [GtCO2/yr], negative = removal. Shape (n_study_years,).
    albedo_rf_wm2 : NDArray[np.float64]
        Albedo radiative forcing [W/m^2], positive = warming. Shape (n_study_years,).
    scenario : str
        Background SSP scenario.

    Returns
    -------
    temperature : NDArray[np.float64]
        Global mean surface temperature anomaly [K], study period only.
    """
    f = _create_fair_instance(scenario)

    # Add NEE as perturbation to CO2 FFI emissions (study period only)
    start_idx = T_START - 1750
    end_idx = T_END - 1750
    n = end_idx - start_idx

    # Ensure correct length
    nee = nee_gtco2_yr[:n] if len(nee_gtco2_yr) >= n else np.pad(
        nee_gtco2_yr, (0, n - len(nee_gtco2_yr))
    )
    albedo = albedo_rf_wm2[:n] if len(albedo_rf_wm2) >= n else np.pad(
        albedo_rf_wm2, (0, n - len(albedo_rf_wm2))
    )

    # Perturb CO2 emissions
    f.emissions.loc[dict(
        timepoints=np.arange(T_START, T_END),
        scenario=scenario,
        config="central",
        specie="CO2 FFI",
    )] += nee

    # Add albedo as external forcing perturbation
    # Use "Aerosol-cloud interactions" or another forcing category
    # Actually, we add to the total forcing after run... but FaIR doesn't easily support
    # arbitrary external forcing pre-run. Instead, we can use the solar forcing channel
    # or add to an existing minor forcing.
    # Best approach: add to forcing after allocation but before run
    f.forcing.loc[dict(
        timepoints=np.arange(T_START, T_END),
        scenario=scenario,
        config="central",
        specie="Solar",
    )] += albedo

    f.run()

    temp = f.temperature.sel(
        scenario=scenario, config="central", layer=0
    ).values

    return temp[start_idx:end_idx]


def compute_delta_t(
    t_perturbed: NDArray[np.float64],
    t_baseline: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute temperature difference: ΔT(t) = T_perturbed - T_baseline."""
    return t_perturbed - t_baseline


def find_breakeven_year(
    delta_t: NDArray[np.float64],
) -> float:
    """Find break-even year t* where intervention becomes net cooling.

    Returns
    -------
    t_star : float
        Year when ΔT first becomes <= 0 (net cooling).
        Returns np.inf if never net cooling within study period.
    """
    cooling_indices = np.where(delta_t <= 0)[0]
    if len(cooling_indices) > 0:
        return float(T_START + cooling_indices[0])
    return np.inf
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_fair_module.py -v`
Expected: All tests PASS. Note: These tests are slower (~10-30s) since FaIR runs actual climate simulations.

If FaIR's API doesn't match exactly (method names, data loading), debug by checking:
```bash
uv run python -c "import fair; help(fair.FAIR)" | head -50
```
and adjust the implementation accordingly. The FaIR v2 API may differ from the study design pseudocode.

- [ ] **Step 5: Commit**

```bash
git add src/nbs/fair_module.py tests/test_fair_module.py
git commit -m "feat: add FaIR coupling module with baseline, perturbed runs, break-even"
```

---

### Task 6: Scenario Runner

**Files:**
- Create: `src/nbs/scenario_runner.py`
- Create: `tests/test_scenario_runner.py`

Loops over all intervention × latitude × land use × SSP combinations, skipping impossible combos.

- [ ] **Step 1: Write tests for scenario runner**

Create `tests/test_scenario_runner.py`:
```python
import numpy as np
import pytest
from nbs.scenario_runner import (
    is_valid_combination,
    run_single_scenario,
    run_all_scenarios,
)


class TestValidCombinations:
    def test_tropical_reforestation_at_equator(self):
        assert is_valid_combination("tropical_reforestation", 0) is True

    def test_tropical_reforestation_at_60(self):
        assert is_valid_combination("tropical_reforestation", 60) is False

    def test_boreal_afforestation_at_equator(self):
        assert is_valid_combination("boreal_afforestation", 0) is False

    def test_boreal_afforestation_at_60(self):
        assert is_valid_combination("boreal_afforestation", 60) is True

    def test_avoided_deforestation_tropical(self):
        assert is_valid_combination("avoided_deforestation", 0) is True

    def test_avoided_deforestation_high_lat(self):
        assert is_valid_combination("avoided_deforestation", 60) is False

    def test_beccs_temperate(self):
        assert is_valid_combination("beccs", 30) is True


class TestRunSingleScenario:
    def test_returns_expected_keys(self):
        result = run_single_scenario(
            intervention="tropical_reforestation",
            lat=0,
            scenario="ssp245",
        )
        assert "delta_t" in result
        assert "t_star" in result
        assert "delta_f_alpha" in result
        assert "nee" in result

    def test_delta_t_is_array(self):
        result = run_single_scenario(
            intervention="tropical_reforestation",
            lat=0,
            scenario="ssp245",
        )
        assert isinstance(result["delta_t"], np.ndarray)


class TestRunAllScenarios:
    def test_returns_dict(self):
        results = run_all_scenarios()
        assert isinstance(results, dict)
        assert len(results) > 0

    def test_no_invalid_combinations(self):
        results = run_all_scenarios()
        for key in results:
            intervention, lat, scenario = key
            assert is_valid_combination(intervention, lat)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_scenario_runner.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement scenario runner**

Create `src/nbs/scenario_runner.py`:
```python
"""Scenario runner: loops over all intervention × latitude × SSP combinations.

Produces a results dictionary keyed by (intervention, lat, scenario) tuples.
"""

import numpy as np
from numpy.typing import NDArray

from nbs.parameters import INTERVENTIONS, LATITUDES, SCENARIOS
from nbs.carbon_module import compute_nee_timeseries
from nbs.albedo_module import compute_albedo_forcing_timeseries
from nbs.fair_module import (
    run_fair_baseline,
    run_fair_perturbed,
    compute_delta_t,
    find_breakeven_year,
)


# Valid latitude ranges per intervention
_VALID_LATITUDES: dict[str, tuple[int, int]] = {
    "tropical_reforestation": (0, 25),
    "boreal_afforestation": (45, 90),
    "avoided_deforestation": (0, 25),
    "beccs": (0, 60),
}


def is_valid_combination(intervention: str, lat: int) -> bool:
    """Check if an intervention-latitude combination is physically valid."""
    lat_range = _VALID_LATITUDES.get(intervention)
    if lat_range is None:
        return False
    return lat_range[0] <= lat <= lat_range[1]


def run_single_scenario(
    intervention: str,
    lat: int,
    scenario: str = "ssp245",
    area_mha: float = 1.0,
    baseline_temperature: NDArray[np.float64] | None = None,
) -> dict:
    """Run a single intervention scenario and return results.

    Parameters
    ----------
    intervention : str
        Intervention type
    lat : int
        Latitude in degrees North
    scenario : str
        SSP scenario
    area_mha : float
        Area in Mha
    baseline_temperature : NDArray or None
        Pre-computed baseline. If None, computed fresh.

    Returns
    -------
    dict with keys: delta_t, t_star, delta_f_alpha, nee
    """
    if baseline_temperature is None:
        baseline_temperature = run_fair_baseline(scenario)

    nee = compute_nee_timeseries(intervention, lat, area_mha)
    albedo_rf = compute_albedo_forcing_timeseries(intervention, lat)

    t_pert = run_fair_perturbed(nee, albedo_rf, scenario)
    delta_t = compute_delta_t(t_pert, baseline_temperature)
    t_star = find_breakeven_year(delta_t)

    return {
        "delta_t": delta_t,
        "t_star": t_star,
        "delta_f_alpha": albedo_rf[-1] if len(albedo_rf) > 0 else 0.0,
        "nee": nee,
    }


def run_all_scenarios(area_mha: float = 1.0) -> dict[tuple[str, int, str], dict]:
    """Run all valid intervention × latitude × SSP combinations.

    Returns
    -------
    results : dict
        Keyed by (intervention, lat, scenario) tuples.
    """
    results = {}

    # Cache baselines per scenario
    baselines: dict[str, NDArray[np.float64]] = {}

    for scenario in SCENARIOS:
        print(f"Computing baseline for {scenario}...")
        baselines[scenario] = run_fair_baseline(scenario)

    total = 0
    for intervention in INTERVENTIONS:
        for lat in LATITUDES:
            if not is_valid_combination(intervention, lat):
                continue
            for scenario in SCENARIOS:
                key = (intervention, lat, scenario)
                print(f"Running {key}...")
                results[key] = run_single_scenario(
                    intervention=intervention,
                    lat=lat,
                    scenario=scenario,
                    area_mha=area_mha,
                    baseline_temperature=baselines[scenario],
                )
                total += 1

    print(f"Completed {total} scenario runs.")
    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_scenario_runner.py -v`
Expected: All tests PASS (slow — multiple FaIR runs).

- [ ] **Step 5: Commit**

```bash
git add src/nbs/scenario_runner.py tests/test_scenario_runner.py
git commit -m "feat: add scenario runner with validation and full loop"
```

---

### Task 7: Sensitivity Analysis

**Files:**
- Create: `src/nbs/sensitivity.py`
- Create: `tests/test_sensitivity.py`

Implements one-at-a-time (OAT) and Sobol global sensitivity analysis using SALib.

- [ ] **Step 1: Write tests for sensitivity module**

Create `tests/test_sensitivity.py`:
```python
import numpy as np
import pytest
from nbs.sensitivity import (
    PARAM_BOUNDS,
    run_oat_sensitivity,
    run_sobol_sensitivity,
)


class TestOAT:
    def test_returns_dict(self):
        results = run_oat_sensitivity(
            intervention="tropical_reforestation",
            lat=0,
            scenario="ssp245",
        )
        assert isinstance(results, dict)

    def test_has_all_parameters(self):
        results = run_oat_sensitivity(
            intervention="tropical_reforestation",
            lat=0,
            scenario="ssp245",
        )
        for param in PARAM_BOUNDS:
            assert param in results

    def test_each_result_has_breakeven(self):
        results = run_oat_sensitivity(
            intervention="tropical_reforestation",
            lat=0,
            scenario="ssp245",
        )
        for param, values in results.items():
            assert "low" in values
            assert "high" in values
            assert "t_star_low" in values
            assert "t_star_high" in values


class TestSobol:
    def test_returns_sobol_indices(self):
        si = run_sobol_sensitivity(
            intervention="tropical_reforestation",
            lat=0,
            scenario="ssp245",
            n_samples=64,  # Small for testing
        )
        assert "S1" in si
        assert "ST" in si

    def test_sobol_indices_shape(self):
        si = run_sobol_sensitivity(
            intervention="tropical_reforestation",
            lat=0,
            scenario="ssp245",
            n_samples=64,
        )
        n_params = len(PARAM_BOUNDS)
        assert len(si["S1"]) == n_params
        assert len(si["ST"]) == n_params
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_sensitivity.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement sensitivity module**

Create `src/nbs/sensitivity.py`:
```python
"""Sensitivity analysis: OAT and Sobol global sensitivity.

Analyzes how model parameters affect break-even year t*.
"""

import numpy as np
from numpy.typing import NDArray
from SALib.sample import saltelli
from SALib.analyze import sobol

from nbs.parameters import T_START, T_END, get_growth_params
from nbs.carbon_module import compute_biomass_growth, compute_soc_dynamics, compute_nee_timeseries
from nbs.albedo_module import compute_albedo_forcing_timeseries
from nbs.fair_module import run_fair_baseline, run_fair_perturbed, compute_delta_t, find_breakeven_year


# Parameter bounds for sensitivity analysis
# (name, low, high) — base values from parameters.py
PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "B_max_scale": (0.7, 1.3),        # ±30% of base B_max
    "Q10": (1.5, 2.5),                # Soil respiration temperature sensitivity
    "eta_CCS": (0.75, 0.95),          # CCS capture efficiency
    "p_disturb_scale": (0.5, 2.0),    # Disturbance probability multiplier
    "mu": (0.01, 0.06),               # SOC equilibration rate
    "albedo_scale": (0.7, 1.3),       # ±1 std dev of albedo forcing
}


def _run_with_params(
    intervention: str,
    lat: int,
    scenario: str,
    baseline_temp: NDArray[np.float64],
    params: dict[str, float],
) -> float:
    """Run a single scenario with overridden parameters, return t*."""
    years = np.arange(T_START, T_END)
    t = years - T_START
    n = len(years)

    # Get base growth params
    if intervention != "avoided_deforestation":
        base_bmax, base_k, base_p = get_growth_params(intervention)
        B_max = base_bmax * params.get("B_max_scale", 1.0)
        B = compute_biomass_growth(B_max, base_k, base_p, t)
        dBdt = np.gradient(B)
    else:
        dBdt = np.zeros(n)
        B = np.zeros(n)

    # SOC
    from nbs.parameters import get_soc_params, SOIL_RESP_BASE
    soc_forest, soc_initial = get_soc_params(intervention, lat)
    mu = params.get("mu", 0.03)
    soc = compute_soc_dynamics(soc_forest, soc_initial, mu, t)
    dSOCdt = np.gradient(soc)

    # Soil respiration
    q10 = params.get("Q10", 2.0)
    from nbs.carbon_module import _get_temperature_trajectory, compute_soil_respiration
    from nbs.parameters import SOIL_RESP_T0
    temps = _get_temperature_trajectory(lat, years)
    r_base = SOIL_RESP_BASE.get(lat, 5.0)
    r_soil = compute_soil_respiration(r_base, q10, SOIL_RESP_T0, temps)

    # Disturbance
    from nbs.parameters import get_disturbance_probability
    p_dist = get_disturbance_probability(intervention, lat, years)
    p_dist = p_dist * params.get("p_disturb_scale", 1.0)
    D = p_dist * B

    if intervention == "avoided_deforestation":
        from nbs.parameters import DEFORESTATION_RATE, C_FOREST_TROPICAL
        prevented = DEFORESTATION_RATE * C_FOREST_TROPICAL * (44.0 / 12.0)
        nee = np.full(n, -prevented)
    else:
        net_uptake = (dBdt + dSOCdt) * (44.0 / 12.0) - r_soil - D * (44.0 / 12.0)
        nee = -net_uptake

    if intervention == "beccs":
        from nbs.parameters import BECCS_HARVEST_PERIOD, BECCS_PROCESS_EMISSION_FRAC
        eta = params.get("eta_CCS", 0.87)
        harvest_flux = np.zeros(n)
        for hy in range(BECCS_HARVEST_PERIOD, n, BECCS_HARVEST_PERIOD):
            captured = B[hy] * eta * (44.0 / 12.0)
            process_em = captured * BECCS_PROCESS_EMISSION_FRAC
            harvest_flux[hy] = -(captured - process_em)
        nee = nee + harvest_flux

    nee_gt = nee * 1e-3  # 1 Mha

    # Albedo
    from nbs.parameters import get_albedo_values
    albedo_scale = params.get("albedo_scale", 1.0)
    albedo_rf = compute_albedo_forcing_timeseries(intervention, lat)
    albedo_rf = albedo_rf * albedo_scale

    t_pert = run_fair_perturbed(nee_gt, albedo_rf, scenario)
    delta_t = compute_delta_t(t_pert, baseline_temp)
    return find_breakeven_year(delta_t)


def run_oat_sensitivity(
    intervention: str,
    lat: int,
    scenario: str = "ssp245",
) -> dict[str, dict]:
    """One-at-a-time sensitivity analysis.

    Varies each parameter to its low and high bound while keeping others at default.

    Returns
    -------
    results : dict
        {param_name: {"low": value, "high": value, "t_star_low": float, "t_star_high": float}}
    """
    baseline_temp = run_fair_baseline(scenario)
    results = {}

    for param, (low, high) in PARAM_BOUNDS.items():
        # Low
        params_low = {param: low}
        t_star_low = _run_with_params(intervention, lat, scenario, baseline_temp, params_low)

        # High
        params_high = {param: high}
        t_star_high = _run_with_params(intervention, lat, scenario, baseline_temp, params_high)

        results[param] = {
            "low": low,
            "high": high,
            "t_star_low": t_star_low,
            "t_star_high": t_star_high,
        }

    return results


def run_sobol_sensitivity(
    intervention: str,
    lat: int,
    scenario: str = "ssp245",
    n_samples: int = 256,
) -> dict:
    """Sobol global sensitivity analysis using SALib.

    Returns
    -------
    si : dict
        Sobol indices with keys "S1", "ST", "S1_conf", "ST_conf", "param_names".
    """
    param_names = list(PARAM_BOUNDS.keys())
    bounds = [PARAM_BOUNDS[p] for p in param_names]

    problem = {
        "num_vars": len(param_names),
        "names": param_names,
        "bounds": bounds,
    }

    param_values = saltelli.sample(problem, n_samples)
    baseline_temp = run_fair_baseline(scenario)

    Y = np.zeros(param_values.shape[0])
    for i, pv in enumerate(param_values):
        params = dict(zip(param_names, pv))
        t_star = _run_with_params(intervention, lat, scenario, baseline_temp, params)
        # Replace inf with a large number for Sobol analysis
        Y[i] = t_star if t_star != np.inf else T_END + 100

    si = sobol.analyze(problem, Y)

    return {
        "S1": si["S1"],
        "ST": si["ST"],
        "S1_conf": si["S1_conf"],
        "ST_conf": si["ST_conf"],
        "param_names": param_names,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_sensitivity.py -v`
Expected: All tests PASS (slow — many FaIR runs for Sobol).

- [ ] **Step 5: Commit**

```bash
git add src/nbs/sensitivity.py tests/test_sensitivity.py
git commit -m "feat: add OAT and Sobol sensitivity analysis"
```

---

### Task 8: Figure Generation

**Files:**
- Create: `src/nbs/figures.py`
- Create: `tests/test_figures.py`

Generates all five publication figures from the study design (Section 11).

- [ ] **Step 1: Write tests for figures module**

Create `tests/test_figures.py`:
```python
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch
from nbs.figures import (
    plot_delta_t_curves,
    plot_breakeven_map,
    plot_ranking_heatmap,
    plot_ssp_sensitivity,
    plot_sobol_indices,
)


@pytest.fixture
def mock_results():
    """Create mock results dict for figure tests."""
    n = 125
    results = {}
    for intervention in ["tropical_reforestation", "boreal_afforestation",
                          "avoided_deforestation", "beccs"]:
        for lat in [0, 15, 30, 45, 60]:
            for scenario in ["ssp126", "ssp245", "ssp370"]:
                key = (intervention, lat, scenario)
                results[key] = {
                    "delta_t": np.random.randn(n) * 0.01,
                    "t_star": np.random.choice([2040, 2060, 2080, np.inf]),
                    "delta_f_alpha": np.random.uniform(-0.5, 1.5),
                    "nee": np.random.randn(n) * 0.01,
                }
    return results


@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "figures"


class TestFigures:
    def test_plot_delta_t_curves(self, mock_results, output_dir):
        path = plot_delta_t_curves(mock_results, output_dir)
        assert Path(path).exists()

    def test_plot_breakeven_map(self, mock_results, output_dir):
        path = plot_breakeven_map(mock_results, output_dir)
        assert Path(path).exists()

    def test_plot_ranking_heatmap(self, mock_results, output_dir):
        path = plot_ranking_heatmap(mock_results, output_dir)
        assert Path(path).exists()

    def test_plot_ssp_sensitivity(self, mock_results, output_dir):
        path = plot_ssp_sensitivity(mock_results, output_dir)
        assert Path(path).exists()

    def test_plot_sobol_indices(self, output_dir):
        si = {
            "S1": np.array([0.3, 0.2, 0.1, 0.05, 0.15, 0.1]),
            "ST": np.array([0.4, 0.25, 0.15, 0.1, 0.2, 0.15]),
            "S1_conf": np.array([0.05] * 6),
            "ST_conf": np.array([0.05] * 6),
            "param_names": ["B_max_scale", "Q10", "eta_CCS",
                           "p_disturb_scale", "mu", "albedo_scale"],
        }
        path = plot_sobol_indices(si, output_dir)
        assert Path(path).exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_figures.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement figures module**

Create `src/nbs/figures.py`:
```python
"""Publication figure generation for the NBS climate framework.

Generates Figures 1-5 from the study design (Section 11).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

from nbs.parameters import T_START, T_END, INTERVENTIONS, LATITUDES, SCENARIOS


# Consistent colors per intervention
COLORS = {
    "tropical_reforestation": "#2ca02c",
    "boreal_afforestation": "#1f77b4",
    "avoided_deforestation": "#ff7f0e",
    "beccs": "#d62728",
}

LABELS = {
    "tropical_reforestation": "Tropical Reforestation",
    "boreal_afforestation": "Boreal Afforestation",
    "avoided_deforestation": "Avoided Deforestation",
    "beccs": "BECCS",
}

YEARS = np.arange(T_START, T_END)


def _ensure_dir(output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def plot_delta_t_curves(
    results: dict,
    output_dir: Path | str,
    scenario: str = "ssp245",
) -> str:
    """Fig. 1: ΔT(t) curves for all four interventions at representative latitudes."""
    output_dir = _ensure_dir(output_dir)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Pick representative lat per intervention
    rep_lats = {
        "tropical_reforestation": 0,
        "boreal_afforestation": 60,
        "avoided_deforestation": 0,
        "beccs": 30,
    }

    for intervention, lat in rep_lats.items():
        key = (intervention, lat, scenario)
        if key in results:
            delta_t = results[key]["delta_t"]
            years_plot = YEARS[:len(delta_t)]
            ax.plot(
                years_plot, delta_t * 1000,  # Convert to mK for readability
                color=COLORS[intervention],
                linewidth=2,
                label=f"{LABELS[intervention]} ({lat}°N)",
            )

    ax.axhline(y=0, color="black", linewidth=0.5, linestyle="--")
    ax.set_xlabel("Year")
    ax.set_ylabel("ΔT [mK]")
    ax.set_title(f"Temperature impact of forest-based interventions ({scenario.upper()})")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    path = output_dir / "fig1_delta_t_curves.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def plot_breakeven_map(
    results: dict,
    output_dir: Path | str,
    scenario: str = "ssp245",
) -> str:
    """Fig. 2: Break-even year t* by latitude and intervention."""
    output_dir = _ensure_dir(output_dir)

    fig, ax = plt.subplots(figsize=(10, 6))

    for intervention in INTERVENTIONS:
        lats = []
        t_stars = []
        for lat in LATITUDES:
            key = (intervention, lat, scenario)
            if key in results:
                t_star = results[key]["t_star"]
                if t_star != np.inf:
                    lats.append(lat)
                    t_stars.append(t_star)
        if lats:
            ax.scatter(lats, t_stars, color=COLORS[intervention],
                      s=100, label=LABELS[intervention], zorder=5)
            ax.plot(lats, t_stars, color=COLORS[intervention],
                   linewidth=1, alpha=0.5)

    ax.set_xlabel("Latitude [°N]")
    ax.set_ylabel("Break-even year t*")
    ax.set_title(f"Break-even horizons by latitude ({scenario.upper()})")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    path = output_dir / "fig2_breakeven_map.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def plot_ranking_heatmap(
    results: dict,
    output_dir: Path | str,
) -> str:
    """Fig. 3: Ranking heatmap — which intervention wins at 2050/2100/2150."""
    output_dir = _ensure_dir(output_dir)

    horizons = [2050, 2100, 2150]
    horizon_indices = [h - T_START for h in horizons]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    for ax, horizon, idx in zip(axes, horizons, horizon_indices):
        data = []
        for lat in LATITUDES:
            row = []
            for intervention in INTERVENTIONS:
                key = (intervention, lat, "ssp245")
                if key in results:
                    dt = results[key]["delta_t"]
                    val = dt[min(idx, len(dt) - 1)] * 1000  # mK
                else:
                    val = np.nan
                row.append(val)
            data.append(row)

        data = np.array(data)
        im = ax.imshow(data, cmap="RdBu_r", aspect="auto",
                      vmin=-np.nanmax(np.abs(data)), vmax=np.nanmax(np.abs(data)))
        ax.set_xticks(range(len(INTERVENTIONS)))
        ax.set_xticklabels(["TR", "BA", "AD", "BECCS"], rotation=45)
        ax.set_yticks(range(len(LATITUDES)))
        ax.set_yticklabels([f"{l}°N" for l in LATITUDES])
        ax.set_title(f"ΔT at {horizon}")
        plt.colorbar(im, ax=ax, label="ΔT [mK]")

    fig.suptitle("Ranking of interventions by time horizon", fontsize=14)
    fig.tight_layout()

    path = output_dir / "fig3_ranking_heatmap.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def plot_ssp_sensitivity(
    results: dict,
    output_dir: Path | str,
) -> str:
    """Fig. 4: SSP sensitivity — how t* changes by background scenario."""
    output_dir = _ensure_dir(output_dir)

    fig, ax = plt.subplots(figsize=(10, 6))

    bar_width = 0.25
    x = np.arange(len(INTERVENTIONS))

    for i, scenario in enumerate(SCENARIOS):
        t_stars = []
        for intervention in INTERVENTIONS:
            # Find best available latitude
            best_t_star = np.inf
            for lat in LATITUDES:
                key = (intervention, lat, scenario)
                if key in results:
                    t_star = results[key]["t_star"]
                    if t_star < best_t_star:
                        best_t_star = t_star
            t_stars.append(best_t_star if best_t_star != np.inf else T_END)

        ax.bar(x + i * bar_width, t_stars, bar_width,
              label=scenario.upper(), alpha=0.8)

    ax.set_xticks(x + bar_width)
    ax.set_xticklabels([LABELS[i] for i in INTERVENTIONS], rotation=15)
    ax.set_ylabel("Break-even year t*")
    ax.set_title("Break-even sensitivity to background SSP scenario")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    path = output_dir / "fig4_ssp_sensitivity.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def plot_sobol_indices(
    sobol_results: dict,
    output_dir: Path | str,
) -> str:
    """Fig. 5: Sobol sensitivity indices — which parameters dominate uncertainty."""
    output_dir = _ensure_dir(output_dir)

    fig, ax = plt.subplots(figsize=(10, 6))

    param_names = sobol_results["param_names"]
    s1 = sobol_results["S1"]
    st = sobol_results["ST"]
    s1_conf = sobol_results["S1_conf"]
    st_conf = sobol_results["ST_conf"]

    x = np.arange(len(param_names))
    width = 0.35

    ax.bar(x - width / 2, s1, width, yerr=s1_conf, label="First-order (S1)",
          capsize=3, color="#2ca02c", alpha=0.8)
    ax.bar(x + width / 2, st, width, yerr=st_conf, label="Total-order (ST)",
          capsize=3, color="#1f77b4", alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(param_names, rotation=30, ha="right")
    ax.set_ylabel("Sobol index")
    ax.set_title("Parameter sensitivity for break-even year t*")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    path = output_dir / "fig5_sobol_indices.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_figures.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/nbs/figures.py tests/test_figures.py
git commit -m "feat: add publication figure generation (Figs 1-5)"
```

---

### Task 9: Demo Notebook

**Files:**
- Create: `notebooks/01_single_intervention_demo.ipynb`

Creates a Jupyter notebook demonstrating a single intervention run (tropical reforestation at 0°N, SSP2-4.5).

- [ ] **Step 1: Add notebook dependency**

```bash
uv add --dev jupyter
```

- [ ] **Step 2: Create the demo notebook**

Create `notebooks/01_single_intervention_demo.ipynb` with these cells:

**Cell 1 (Markdown):**
```markdown
# Single Intervention Demo
## Tropical Reforestation at 0°N, SSP2-4.5

This notebook demonstrates the full pipeline:
1. Compute NEE timeseries from the carbon module
2. Compute albedo forcing
3. Run FaIR baseline and perturbed
4. Plot ΔT(t) and identify break-even year t*
```

**Cell 2 (Code):**
```python
import numpy as np
import matplotlib.pyplot as plt
from nbs.carbon_module import compute_nee_timeseries
from nbs.albedo_module import compute_albedo_forcing_timeseries
from nbs.fair_module import run_fair_baseline, run_fair_perturbed, compute_delta_t, find_breakeven_year
from nbs.parameters import T_START, T_END
```

**Cell 3 (Code):**
```python
# 1. Carbon module: compute NEE
nee = compute_nee_timeseries("tropical_reforestation", lat=0, area_mha=1.0)

years = np.arange(T_START, T_END)
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(years, nee, color="green")
ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
ax.set_xlabel("Year")
ax.set_ylabel("NEE [GtCO2/yr]")
ax.set_title("Net Ecosystem Exchange — Tropical Reforestation (1 Mha)")
ax.grid(True, alpha=0.3)
plt.show()

print(f"Cumulative removal by 2150: {np.sum(nee):.2f} GtCO2")
```

**Cell 4 (Code):**
```python
# 2. Albedo forcing
albedo_rf = compute_albedo_forcing_timeseries("tropical_reforestation", lat=0)
print(f"Steady-state albedo forcing: {albedo_rf[-1]:.3f} W/m²")
```

**Cell 5 (Code):**
```python
# 3. Run FaIR
print("Running FaIR baseline...")
T_base = run_fair_baseline("ssp245")
print("Running FaIR perturbed...")
T_pert = run_fair_perturbed(nee, albedo_rf, "ssp245")

delta_t = compute_delta_t(T_pert, T_base)
t_star = find_breakeven_year(delta_t)
print(f"Break-even year: {t_star}")
```

**Cell 6 (Code):**
```python
# 4. Plot ΔT(t)
fig, ax = plt.subplots(figsize=(10, 5))
years_plot = years[:len(delta_t)]
ax.plot(years_plot, delta_t * 1000, color="green", linewidth=2)
ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
if t_star != np.inf:
    ax.axvline(t_star, color="red", linewidth=1, linestyle=":", label=f"t* = {t_star:.0f}")
    ax.legend()
ax.set_xlabel("Year")
ax.set_ylabel("ΔT [mK]")
ax.set_title("Temperature impact: Tropical Reforestation (1 Mha, SSP2-4.5)")
ax.grid(True, alpha=0.3)
plt.show()
```

- [ ] **Step 3: Run the notebook**

Run: `uv run jupyter nbconvert --to notebook --execute notebooks/01_single_intervention_demo.ipynb`
Expected: Notebook executes without errors, produces plots.

- [ ] **Step 4: Commit**

```bash
git add notebooks/01_single_intervention_demo.ipynb
git commit -m "feat: add single intervention demo notebook"
```

---

### Task 10: Integration Test — Full Pipeline

**Files:**
- Create: `tests/test_integration.py`

End-to-end test that runs a small subset of the full pipeline to verify all modules work together.

- [ ] **Step 1: Write integration test**

Create `tests/test_integration.py`:
```python
"""Integration test: full pipeline from NEE to ΔT for one scenario."""

import numpy as np
import pytest
from nbs.scenario_runner import run_single_scenario, is_valid_combination


@pytest.mark.slow
class TestFullPipeline:
    def test_tropical_reforestation_end_to_end(self):
        """Full pipeline for tropical reforestation at equator."""
        result = run_single_scenario(
            intervention="tropical_reforestation",
            lat=0,
            scenario="ssp245",
        )

        # Should have all expected outputs
        assert "delta_t" in result
        assert "t_star" in result
        assert "nee" in result
        assert "delta_f_alpha" in result

        # ΔT should be an array of reasonable length
        assert len(result["delta_t"]) > 100

        # Tropical reforestation should eventually be net cooling
        # (small albedo penalty, strong carbon uptake)
        assert result["t_star"] < 2150

        # NEE should show net removal
        assert np.sum(result["nee"]) < 0

    def test_boreal_afforestation_has_late_or_no_breakeven(self):
        """Boreal afforestation at 60N: late break-even due to albedo penalty."""
        result = run_single_scenario(
            intervention="boreal_afforestation",
            lat=60,
            scenario="ssp245",
        )

        # Should have later break-even than tropical (or possibly never)
        assert result["t_star"] > 2050 or result["t_star"] == np.inf

        # Should have positive albedo forcing
        assert result["delta_f_alpha"] > 0
```

- [ ] **Step 2: Run integration tests**

Run: `uv run pytest tests/test_integration.py -v -m slow`
Expected: PASS (takes ~1 minute due to FaIR runs).

To run all tests excluding slow: `uv run pytest -v -m "not slow"`

Add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py pyproject.toml
git commit -m "feat: add integration tests for full pipeline"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Carbon module: Chapman-Richards, SOC, soil respiration, disturbance, NEE (Task 3)
- [x] Albedo module: ΔF_α with transition phase (Task 4)
- [x] FaIR coupling: baseline, perturbed, ΔT, break-even (Task 5)
- [x] Scenario runner: all valid combinations (Task 6)
- [x] Sensitivity: OAT + Sobol (Task 7)
- [x] Figures 1-5 (Task 8)
- [x] Demo notebook (Task 9)
- [x] Integration test (Task 10)
- [x] Four interventions: TR, BA, AD, BECCS
- [x] Five latitudes, three SSPs, three land uses in parameters
- [x] Break-even t* as central metric
- [ ] Land use dimension in scenario loop — note: simplified to intervention × lat × SSP (land use affects SOC params but not a separate loop dimension in this implementation; can be added as enhancement)

**Placeholder scan:** No TBDs or TODOs found.

**Type consistency:** Checked — function signatures match across modules. `compute_nee_timeseries` returns `NDArray[np.float64]`, consumed by `run_fair_perturbed` which expects `NDArray[np.float64]`.
