# The Biophysics of Afforestation as CDR

A transparent, reproducible framework for quantifying the net climate effectiveness of afforestation as a carbon dioxide removal strategy, using progressive physical realism and the FaIR v2 simple climate model.

## The Problem

Despite rapid decarbonisation, IPCC scenarios for limiting warming to 1.5–2°C require substantial net negative CO₂ emissions — a **CDR gap** that natural climate solutions, particularly afforestation, are frequently proposed to fill. But forests modify the Earth's energy balance through multiple pathways simultaneously:

1. **Trees take time.** CO₂ stays in the atmosphere for decades before being absorbed. The integrated warming during this gap is a real climate cost.
2. **Growth rates vary by latitude.** A tropical forest sequesters 3–4× faster than a boreal one.
3. **Albedo works against you at high latitudes.** Dark forest canopy absorbs more solar radiation than the open land or snow-covered ground it replaces — in boreal regions, this warming can exceed the cooling from carbon uptake.
4. **The sink shrinks.** Warming increases soil respiration and fire risk, reducing CDR effectiveness over time.
5. **Soil carbon transitions take time.** Converting some land types to forest can initially release soil carbon, adding an early warming spike.

This framework quantifies each effect through a **progressive complexity framework** (Levels 0–6), revealing how the net climate effectiveness of afforestation departs from naive carbon-only accounting.

## Progressive Complexity Levels

| Level | Name | What's added | Key insight |
|-------|------|-------------|-------------|
| 0 | Carbon-only (static) | No dynamics | Assumes instant, permanent sequestration |
| 1 | Trees Take Time | Carbon uptake with growth curve (tropical) | Temporal delay creates warming debt |
| 2 | Location Matters | Latitude-dependent growth parameters | Tropical forests offset 3× faster than boreal |
| 3 | The Albedo Effect | Surface albedo change | Boreal afforestation can cause net warming |
| 4 | The Shrinking Sink | Q10 respiration + disturbance probability | CDR effectiveness degrades under warming |
| 5 | Soil Carbon Dynamics | SOC dynamics during land-use transition | Early soil carbon release adds warming spike |
| 6 | The Full Picture | All processes combined | Net climate effectiveness at full physical realism |

## Key Metrics

| Metric | Definition | Unit |
|--------|-----------|------|
| **Equivalence ratio** | Forest area needed to achieve genuine climate neutrality relative to naive carbon accounting | dimensionless |
| **Warming debt** | Cumulative excess warming while waiting for CDR to take effect | K·yr |
| **Break-even year (t\*)** | Year when the intervention becomes net cooling | year |
| **ΔT(t)** | Time-dependent net temperature impact of the intervention | K |

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Quick Start

### Progressive complexity analysis

```python
from nbs.credit_analysis import run_progressive_analysis, run_at_level

# Run all 7 complexity levels for a single latitude
results = run_progressive_analysis(lat=45, scenario="ssp245", pulse_gtco2=1.0, area_mha=1.0)

for level, data in results.items():
    print(f"Level {level}: equiv_ratio={data['equivalence_ratio_2100']:.2f}, "
          f"warming_debt={data['warming_debt']:.4f} K·yr, t*={data['t_star']}")
```

### Run a single complexity level

```python
result = run_at_level(level=3, lat=60, scenario="ssp245", pulse_gtco2=1.0, area_mha=1.0)
print(f"Equivalence ratio: {result['equivalence_ratio_2100']:.2f}")
print(f"Warming debt: {result['warming_debt']:.4f} K·yr")
print(f"Break-even year: {result['t_star']}")
```

### Generate figures

```python
from nbs.credit_analysis import run_progressive_analysis, run_at_level
from nbs.credit_figures import (
    plot_progressive_delta_t,
    plot_equivalence_by_latitude,
    plot_breakeven_by_level,
    plot_warming_debt,
    plot_credit_depreciation,
    plot_credit_sobol,
)

# Fig 1: Progressive complexity at one latitude
results_45 = run_progressive_analysis(lat=45)
plot_progressive_delta_t(results_45, "results/figures", lat=45)

# Figs 2–5: Cross-latitude and SSP analysis
lat_results = {}
for lat in [0, 15, 30, 45, 60]:
    for scenario in ["ssp126", "ssp245", "ssp370"]:
        for level in [1, 3, 6]:
            r = run_at_level(level, lat, scenario=scenario)
            lat_results[(level, lat, scenario)] = r

plot_equivalence_by_latitude(lat_results, "results/figures")
plot_breakeven_by_level(lat_results, "results/figures")
plot_warming_debt(lat_results, "results/figures")
plot_credit_depreciation(lat_results, "results/figures")
```

### Intervention comparison

```python
from nbs.scenario_runner import run_single_scenario, run_all_scenarios

result = run_single_scenario(
    intervention="tropical_reforestation",
    lat=0, scenario="ssp245", area_mha=1.0,
)
print(f"Break-even year: {result['t_star']}")
print(f"Peak cooling: {result['delta_t'].min() * 1000:.1f} mK")

results = run_all_scenarios(area_mha=1.0)
```

## Configuration

### Spatial scope

| Dimension | Options |
|-----------|---------|
| Latitude bands | 0°, 15°, 30°, 45°, 60°N |
| SSP scenarios | SSP1-2.6, SSP2-4.5, SSP3-7.0 |
| Complexity levels | 0, 1, 2, 3, 4, 5, 6 |

### Interventions

| Intervention | Key | Valid latitudes |
|---|---|---|
| Tropical Reforestation | `tropical_reforestation` | 0–25°N |
| Boreal Afforestation | `boreal_afforestation` | 45–90°N |
| Avoided Deforestation | `avoided_deforestation` | 0–25°N |
| BECCS | `beccs` | 0–60°N |

### Sensitivity parameters

| Parameter | Base | Range | Controls |
|---|---|---|---|
| `B_max_scale` | 1.0 | 0.7–1.3 | Maximum biomass (±30%) |
| `Q10` | 2.0 | 1.5–2.5 | Soil respiration temperature sensitivity |
| `eta_CCS` | 0.87 | 0.75–0.95 | CCS capture efficiency |
| `p_disturb_scale` | 1.0 | 0.5–2.0 | Disturbance probability multiplier |
| `mu` | 0.03 yr⁻¹ | 0.01–0.06 | SOC equilibration rate |
| `albedo_scale` | 1.0 | 0.7–1.3 | Albedo forcing multiplier |

## Project Structure

```
src/nbs/
  parameters.py       # Physical constants, growth/SOC/albedo parameters
  carbon_module.py    # Biomass growth, SOC, soil respiration, disturbance, NEE
  albedo_module.py    # Albedo radiative forcing with transition phase
  fair_module.py      # FaIR v2 baseline/perturbed runs, pulse warming, ΔT
  scenario_runner.py  # Orchestration for 4-intervention comparison
  sensitivity.py      # OAT and Sobol global sensitivity analysis
  figures.py          # Publication figures
  credit_analysis.py  # Progressive complexity analysis, equivalence ratio, warming debt
  credit_figures.py   # Analysis figures (6 figure types)
tests/                # ~130 tests (fast + slow/integration)
notebooks/
  01_single_intervention_demo.ipynb
```

## Running Tests

```bash
uv run pytest                    # fast tests only
uv run pytest -m slow            # integration tests (slow, runs FaIR)
uv run pytest -v --tb=short      # all tests, verbose
```

## Model Details

- **Carbon dynamics**: Chapman-Richards growth model, exponential SOC equilibration, Q10 soil respiration, stochastic disturbance
- **Albedo**: MODIS-derived values per intervention/latitude, 3-year linear transition
- **Climate model**: FaIR v2.2 (Leach et al. 2021), AR6-calibrated EBM parameters
- **Reference emission**: Single-year CO₂ pulse at 2025
- **Time horizon**: 2025–2150
