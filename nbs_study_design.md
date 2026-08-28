# The Biophysics of Afforestation as CDR
## How Progressive Physical Realism Reveals the Net Climate Effectiveness of Forest-Based Carbon Dioxide Removal

**Document purpose:** Full study design for implementation with Claude Code.
**Status:** v3 — reframed around CDR gap and biophysical energy balance.

---

## 1. Research Question & Framing

### Overarching question
Climate scenarios consistent with 1.5–2°C warming require not just reaching net zero emissions, but achieving net negative CO₂ — a **CDR gap** that must be bridged by actively removing CO₂ from the atmosphere. Afforestation is among the most widely proposed natural approaches. But how effective is it, really, when we account for the full biophysical response of the Earth system?

### The core problem
Simple carbon accounting treats afforestation as a direct subtraction from atmospheric CO₂. The physics is more complex:

1. **Trees take time.** CO₂ remains in the atmosphere for decades before being fully absorbed. This temporal mismatch creates a warming debt — cumulative warming that occurs while waiting for the forest to grow.
2. **Growth rates vary by latitude.** Temperature, rainfall, and sunlight drive 3–4× differences in carbon uptake rates between tropical and boreal forests.
3. **Albedo acts against cooling at high latitudes.** Dark forest canopy absorbs more solar radiation than the snow-covered or open land it replaces. In boreal regions, this warming effect can exceed the cooling from carbon uptake — making afforestation net warming over the relevant timescale.
4. **The sink shrinks under warming.** Rising temperatures accelerate soil respiration and increase disturbance probability (fire, pests), reducing the CDR effectiveness of forests over time. The world where CDR is most needed is also the world where it works least well.
5. **Soil carbon transitions take time.** Converting some land types to forest initially releases soil carbon before a new equilibrium is reached, adding an early warming spike.

Each of these effects modifies the net climate outcome of afforestation. The question is: by how much, where, and under what scenarios?

### Scientific gap
No existing study:
1. Progressively adds physical processes to quantify **how each biophysical term in the energy balance modifies the CDR effectiveness of afforestation**
2. Uses a **transparent, reproducible** climate model (FaIR) rather than opaque ESMs
3. Computes an **equivalence ratio** (effective CDR relative to naive carbon accounting) as a function of location and physical completeness
4. Derives **location-dependent assessments** of where afforestation provides genuine CDR, where it underperforms, and where it causes net warming

### Paper title (draft)
*"Beyond carbon counting: biophysical energy balance controls the climate effectiveness of afforestation as CDR"*

**Target journals:** Nature Climate Change, Environmental Science & Technology, One Earth

---

## 2. The Progressive Complexity Framework

The study's central structure: start with the simplest possible model, then add one physical process at a time. Each level reveals how much the net climate outcome departs from naive carbon-only accounting.

### Level 0 — Carbon-Only (Static)
**Assumption:** Afforestation sequesters CO₂ instantly and permanently. Temperature impact of the reference emission is cancelled immediately.
**Result:** Perfect CDR. ΔT = 0. Equivalence ratio = 1.0.
*This is what simple carbon accounting implicitly assumes.*

### Level 1 — Trees Take Time
**Added process:** Chapman-Richards biomass growth curve.
**Key insight:** The CO₂ stays in the atmosphere for decades before being fully absorbed. The integrated excess warming ("warming debt") is nonzero even if the forest eventually absorbs everything.
**New metric:** Warming debt = ∫ΔT(t) dt [K·yr] — cumulative excess warming while waiting for the forest to grow.

### Level 2 — Location-Dependent Growth
**Added process:** Latitude-dependent growth parameters (B_max, k, p vary by biome).
**Key insight:** A tropical forest (k≈0.08) closes the warming debt much faster than a boreal forest (k≈0.03). CDR effectiveness is strongly latitude-dependent.
**New metric:** Growth-adjusted equivalence ratio by latitude.

### Level 3 — The Albedo Effect
**Added process:** Surface albedo change from land-use conversion.
**Key insight:** In boreal regions with snow cover, forest darkening can cause more warming than carbon uptake prevents. Some afforestation scenarios are net warming — they slow CDR rather than providing it.
**New metric:** Break-even year t* — when (if ever) the carbon benefit overcomes the albedo penalty. Equivalence ratio may become infinite (intervention is climate-neutral or net harmful).

### Level 4 — The Shrinking Sink
**Added process:** Climate feedback on soil respiration (Q10) and disturbance probability (fire, pests).
**Key insight:** Forests planted today will be less effective CDR providers in 2050 than current models assume. As climate warms, soil respiration accelerates and disturbance risk rises.
**New metric:** CDR depreciation rate — how fast the equivalence ratio worsens under different warming scenarios.

### Level 5 — Soil Carbon Dynamics
**Added process:** SOC dynamics during land-use transition.
**Key insight:** Converting carbon-rich grassland to forest initially releases soil carbon (SOC_initial > SOC_forest). This adds an early warming spike, further delaying break-even.
**New metric:** SOC penalty — additional warming debt from soil carbon release during transition.

### Level 6 — The Full Picture
**All processes combined.** The net climate effectiveness of afforestation at full physical realism — quantified as an equivalence ratio relative to naive carbon accounting.

---

## 3. Functional Unit & System Boundary

**Functional unit:** ΔT(t) per reference CO₂ emission pulse, offset by afforestation of sufficient area. All results normalised to show net temperature impact of the intervention relative to the unmitigated pulse.

**Reference emission:** Pulse emission of 1 tCO₂ at t=0 (2025), representing an instantaneous emission. This allows clean attribution of the warming debt and break-even dynamics.

**Offset area:** Area of afforestation required to sequester 1 tCO₂ over the project lifetime (varies by location and growth rate).

**Time horizon:** 2025–2150

**Spatial scope:** Global, disaggregated by latitude band (0°, 15°, 30°, 45°, 60°N)

**Processes included (added progressively):**
- Aboveground biomass carbon (Level 1)
- Latitude-dependent growth rates (Level 2)
- Surface albedo change including snow-albedo feedback (Level 3)
- Temperature-dependent soil respiration + disturbance probability (Level 4)
- Soil organic carbon dynamics during land-use transition (Level 5)

**Processes excluded (with justification):**
- Evapotranspiration: too uncertain, highly site-dependent
- BVOCs: small relative effect
- Indirect land-use change: requires IAM coupling, out of scope
- N₂O/CH₄ fluxes: second-order, flagged as limitation

---

## 4. Module 1 — Carbon Dynamics

### 4.1 Biomass Growth Model

Chapman-Richards growth model:
```
B(t) = B_max * (1 - exp(-k * t))^p    [tC/ha]
```

**Parameters by biome/latitude:**

| Parameter | Tropical (0–15°N) | Temperate (30°N) | Boreal (45–60°N) |
|---|---|---|---|
| B_max [tC/ha] | 200 | 120 | 100 |
| k [yr⁻¹] | 0.08 | 0.05 | 0.03 |
| p [-] | 2.5 | 2.0 | 2.0 |

### 4.2 Soil Organic Carbon
Exponential equilibration with rate μ = 0.03 yr⁻¹.

### 4.3 Soil Respiration
Q10 model with warming-induced excess respiration.

### 4.4 Disturbance
Stochastic disturbance with increasing probability under climate change.

### 4.5 Net CO₂ Flux
NEE computed for the area required to sequester the reference emission.

---

## 5. Module 2 — Albedo

MODIS-derived albedo values per intervention and latitude. Key values:

| Latitude | ΔF_α [W/m²] | Physical reason |
|---|---|---|
| 0°N | −0.30 | Slight: clouds dominate, no snow |
| 15°N | −0.25 | Similar to equatorial |
| 30°N | −0.20 | Moderate, some seasonal effect |
| 45°N | +0.80 | Snow masking begins to dominate |
| 60°N | +1.15 | Strong snow masking, major warming |

Positive values indicate warming forcing (forest absorbs more solar radiation than the land it replaces).

---

## 6. Module 3 — FaIR Coupling

### 6.1 Reference Pulse Emission
Run FaIR with a single CO₂ pulse at 2025:
```python
def compute_pulse_warming(pulse_gtco2, scenario="ssp245"):
    """Temperature impact of an instantaneous CO2 emission pulse."""
    # Add pulse to CO2 FFI emissions at 2025 only
    # Run FaIR, return ΔT(t) relative to no-pulse baseline
```

This gives the warming trajectory that the afforestation intervention is evaluated against.

### 6.2 Complexity-Level Runs
```python
def run_at_complexity_level(level, intervention, lat, scenario, area_mha):
    """
    Level 0: Static sequestration (no dynamics)
    Level 1: Carbon uptake with growth curve (tropical params)
    Level 2: Level 1 + location-dependent growth params
    Level 3: Level 2 + albedo forcing
    Level 4: Level 3 + climate feedbacks (Q10, disturbance)
    Level 5: Level 4 + SOC dynamics
    Level 6: All processes (full model)
    """
```

### 6.3 Equivalence Ratio
```python
def compute_equivalence_ratio(pulse_warming, offset_warming, horizon_year):
    """Ratio of warming integrals: how much larger the offset needs to be
    to cancel the pulse warming by horizon_year.
    
    If offset never achieves neutrality, returns inf.
    """
```

### 6.4 Warming Debt
```python
def compute_warming_debt(delta_t, years):
    """Cumulative excess warming: integral of max(ΔT, 0) dt  [K·yr].
    
    Measures the climate cost incurred while waiting for CDR to take effect.
    """
```

---

## 7. Scenario Space

### Primary analysis: Progressive complexity
For each latitude band (0°, 15°, 30°, 45°, 60°N), run Levels 0–6 and track:
- ΔT(t) at each level
- Equivalence ratio at each level
- Warming debt at each level
- Break-even year at each level

### Secondary: SSP sensitivity
How does the background emissions scenario affect CDR effectiveness?
- SSP1-2.6 (optimistic): forests more effective, lower feedback amplification
- SSP2-4.5 (middle road): moderate degradation
- SSP3-7.0 (pessimistic): strong feedbacks, CDR effectiveness degrades fastest

### Tertiary: Tree/biome types
Optional extension: vary species parameters within latitude bands to show within-biome variability.

---

## 8. Sensitivity Analysis

OAT + Sobol analysis over 6 parameters. Output metric: equivalence ratio at 2100.

---

## 9. Key Outputs and Figure Plan

| Figure | Content | Key message |
|---|---|---|
| Fig. 1 | ΔT(t) at each complexity level for one location (e.g., 45°N) | **Each physical layer modifies the net CDR outcome** |
| Fig. 2 | Equivalence ratio vs. latitude at Levels 1, 3, 6 | **CDR effectiveness is strongly latitude-dependent** |
| Fig. 3 | Break-even year by latitude and complexity level | **Albedo eliminates break-even above ~50°N** |
| Fig. 4 | Warming debt by latitude and level | **The climate cost of temporal delay** |
| Fig. 5 | Equivalence ratio under SSP1-2.6 vs SSP3-7.0 | **High-emissions worlds degrade CDR most** |
| Fig. 6 | Sobol indices: parameter uncertainty in equivalence ratio | **What we need to constrain better** |

### The central scientific message
**"Afforestation provides genuine CDR in the tropics, but its effectiveness degrades rapidly with latitude as albedo effects dominate. At boreal latitudes, afforestation can be net warming over century timescales. Full biophysical accounting — temporal dynamics, albedo, soil feedbacks — is essential for evaluating natural CDR strategies."**

---

## 10. Differentiation from Existing Literature

| Aspect | Existing work | This study |
|---|---|---|
| Framing | "Is afforestation good?" | "How effective is afforestation at CDR, physically?" |
| Complexity | All-or-nothing | Progressive reveal (Levels 0–6) |
| Metric | ΔT or RF at one point | Equivalence ratio, warming debt, break-even |
| Policy relevance | General | Directly applicable to CDR accounting standards |
| Reproducibility | ESM (opaque) | FaIR (transparent, open source) |
| Albedo + carbon jointly? | Sometimes | Yes, as Level 3 in progressive framework |

---

## 11. Implementation Notes

### What stays the same
- Carbon module (biomass, SOC, respiration, disturbance, NEE)
- Albedo module (forcing timeseries)
- FaIR coupling (baseline, perturbed runs)
- Sensitivity analysis (SALib Sobol)
- Parameters module

### Key components
1. **Pulse emission function** — FaIR run with single-year CO₂ pulse as reference
2. **Complexity-level runner** — toggle physical processes on/off per level
3. **Equivalence ratio** — net CDR effectiveness relative to naive accounting
4. **Warming debt** — cumulative ΔT integral during CDR delay
5. **Progressive complexity figures** — waterfall of physical effects
6. **Scenario runner** — loops over levels × latitudes × SSPs
7. **Sensitivity analysis** — Sobol indices over equivalence ratio

### Implementation priority
1. Add pulse emission to fair_module.py
2. Add complexity levels to carbon_module.py
3. Add equivalence ratio + warming debt to fair_module.py
4. Update scenario runner for level-based analysis
5. New figures
6. Update sensitivity analysis to use equivalence ratio
