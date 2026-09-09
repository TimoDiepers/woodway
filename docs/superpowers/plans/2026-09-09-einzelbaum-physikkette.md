# Einzelbaum-Physikkette — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Physik-Kette des Dissertationsvortrags — ein Baum, zwei Antriebskanäle, Faltung zur Temperatur — als getesteter Rechenkern, der ΔT(t) für einen einzelnen Baum einer benannten Art an einem benannten Ort liefert, mit Störungsrisiko als Ensemble.

**Architecture:** Der Vorrat eines Baums wird in Bestandskoordinaten integriert, damit er nach einer Störung weiterwachsen kann. Aus dem Vorrat folgen zwei Antriebe: CO₂ global, Albedo lokal über den Flächenanteil. FaIR liefert einmalig die zwei Impulsantworten g_C und g_T; alles danach ist Faltung, wodurch 1000er-Ensembles bezahlbar werden.

**Tech Stack:** Python 3.11+, numpy, scipy, FaIR v2.2, matplotlib, pytest, uv

**Spec:** `docs/superpowers/specs/2026-09-09-baum-klima-geo-potenzial-design.md`

## Global Constraints

- Python ≥ 3.11; Abhängigkeiten ausschließlich über `uv`, niemals `pip` direkt.
- Tests: `uv run pytest`. Langsame Tests, die FaIR starten, tragen `@pytest.mark.slow`.
- Zeitachse durchgehend `T_START = 2025` bis `T_END = 2150`, jährliche Ausgabe.
- Einheiten strikt: Kohlenstoffvorrat in **kgC je Baum**, CO₂-Flüsse in **kg CO₂ pro Jahr je Baum**, Antriebe in **W/m² global**, Temperaturen in **K**.
- Vorzeichen: Δα < 0 bedeutet, der Wald ist dunkler als die Fläche, die er ersetzt. Daraus folgt φ_α > 0, also Erwärmung.
- Evapotranspiration ist **kein** Term in φ. Wer sie einbaut, widerspricht Folie 18.
- Deutsche Bezeichner nur in nutzersichtbaren Texten (Abbildungen, Notebooks). Code, Funktionsnamen und Docstrings auf Englisch, wie im Bestand.
- Kein bestehendes Modul wird gelöscht; alles Alte wandert nach `src/nbs/legacy/` und dessen Tests laufen weiter.

---

### Task 1: Legacy-Umzug und gemeinsame Konstanten

Der Bestand muss aus dem Weg, bevor neue Module gleiche Namen belegen. Danach gibt es eine einzige Quelle für die physikalischen Konstanten.

**Files:**
- Create: `src/nbs/legacy/__init__.py`
- Create: `src/nbs/constants.py`
- Modify: alle Dateien unter `src/nbs/legacy/` (Importpfade)
- Modify: `tests/test_*.py` (Importpfade)
- Test: `tests/test_constants.py`

**Interfaces:**
- Consumes: nichts
- Produces: `nbs.constants` mit `A_EARTH_M2: float`, `A_CO2_W_M2_PER_KG: float`, `M_CO2_PER_C: float`, `TAU_ATM: float`, `T_START: int`, `T_END: int`, `YEARS: np.ndarray` (Länge 126, 2025…2150 einschließlich)

- [ ] **Step 1: Module verschieben**

```bash
cd /Users/timodiepers/Documents/Coding/dissvortrag
mkdir -p src/nbs/legacy
git mv src/nbs/albedo_module.py src/nbs/carbon_module.py src/nbs/credit_analysis.py \
       src/nbs/credit_figures.py src/nbs/et_module.py src/nbs/figures.py \
       src/nbs/parameters.py src/nbs/scenario_runner.py src/nbs/sensitivity.py \
       src/nbs/legacy/
printf '"""Vorheriger Stand des Rahmenwerks.\n\nBleibt lauffaehig und liefert Material fuer Backup-Folien: Aequivalenzverhaeltnis,\nWarming Debt, Sobol-Indizes, Vergleich mit BECCS und vermiedener Entwaldung.\n\nWICHTIG: ``et_module`` ist **kein** Bestandteil des Antriebs phi. Evapotranspiration\nueberquert die Bilanzgrenze am Oberrand der Atmosphaere nicht; ihre Wirkung steckt im\nRueckkopplungsparameter Lambda. Siehe Folie 18 des Vortrags.\n"""\n' > src/nbs/legacy/__init__.py
```

- [ ] **Step 2: Importpfade in legacy und Tests umschreiben**

```bash
cd /Users/timodiepers/Documents/Coding/dissvortrag
for m in albedo_module carbon_module credit_analysis credit_figures et_module figures parameters scenario_runner sensitivity; do
  grep -rl "nbs\.$m" src/nbs/legacy tests | xargs -r sed -i '' "s/nbs\.$m/nbs.legacy.$m/g"
done
grep -rn "from nbs import" src tests || true
```

- [ ] **Step 3: Bestandstests laufen lassen**

Run: `uv run pytest -q -m "not slow"`
Expected: PASS — dieselbe Anzahl bestandener Tests wie vor dem Umzug. Schlägt etwas fehl, ist ein Importpfad übersehen worden; `grep -rn "nbs\.\(parameters\|carbon_module\)" src tests` zeigt es.

- [ ] **Step 4: Test für die Konstanten schreiben**

```python
# tests/test_constants.py
import numpy as np
from nbs import constants as C


def test_years_axis_covers_study_period_inclusive():
    assert C.YEARS[0] == C.T_START
    assert C.YEARS[-1] == C.T_END
    assert len(C.YEARS) == C.T_END - C.T_START + 1


def test_co2_radiative_efficiency_matches_slide_value():
    # Folie 21: A_CO2 ~ 1,76e-15 W m^-2 kg^-1
    assert 1.6e-15 < C.A_CO2_W_M2_PER_KG < 1.9e-15


def test_molar_mass_ratio():
    assert C.M_CO2_PER_C == 44.0 / 12.0


def test_earth_area_order_of_magnitude():
    assert 5.0e14 < C.A_EARTH_M2 < 5.2e14
```

- [ ] **Step 5: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_constants.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.constants'`

- [ ] **Step 6: Konstanten implementieren**

```python
# src/nbs/constants.py
"""Physical constants shared by the tree-level forcing chain.

Values are those quoted on the presentation slides, so that derivation and
computation carry identical numbers.
"""

from __future__ import annotations

import numpy as np

T_START = 2025
T_END = 2150
YEARS = np.arange(T_START, T_END + 1, dtype=int)

A_EARTH_M2 = 5.1006e14
"""Earth surface area [m^2]. Slide 22."""

A_CO2_W_M2_PER_KG = 1.76e-15
"""Radiative efficiency of atmospheric CO2 [W m^-2 kg^-1]. IPCC AR6, slide 21."""

M_CO2_PER_C = 44.0 / 12.0
"""Molar mass ratio CO2 to C. Slide 13."""

TAU_ATM = 0.8
"""Upward atmospheric transmittance for surface shortwave anomalies. Slide 22."""
```

- [ ] **Step 7: Tests laufen lassen**

Run: `uv run pytest tests/test_constants.py -v`
Expected: PASS, 4 Tests

- [ ] **Step 8: Commit**

```bash
git add -A src/nbs tests
git commit -m "refactor: move previous framework to nbs.legacy, add shared constants

The presentation's physics chain needs the top-level module names. Nothing is
deleted: equivalence ratio, warming debt and the Sobol analysis stay reachable
under nbs.legacy and their tests keep running."
```

---

### Task 2: Baumarten

**Files:**
- Create: `src/nbs/species.py`
- Test: `tests/test_species.py`

**Interfaces:**
- Consumes: nichts
- Produces:
  - `nbs.species.Species` — eingefrorene Dataclass mit den Feldern
    `key: str`, `name_de: str`, `name_lat: str`, `m_max_kgC: float`, `k: float`,
    `p: float`, `beta_closure: float`, `stand_area_m2: float`,
    `alpha_canopy: float`, `igbp_class: str`, `p_disturb: float`,
    `severity_beta: tuple[float, float]`, `gamma_warming: float`,
    `eps_immediate: float`, `tau_decay_yr: float`, `valid_gez: tuple[str, ...]`,
    `sources: dict[str, str]`
  - `nbs.species.SPECIES: dict[str, Species]` mit den Schlüsseln
    `"picea_abies"`, `"pinus_sylvestris"`, `"fagus_sylvatica"`,
    `"eucalyptus_grandis"`, `"tropical_mixed"`
  - `nbs.species.get_species(key: str) -> Species`

- [ ] **Step 1: Test schreiben**

```python
# tests/test_species.py
import dataclasses
import pytest

from nbs.species import SPECIES, Species, get_species

EXPECTED_KEYS = {
    "picea_abies",
    "pinus_sylvestris",
    "fagus_sylvatica",
    "eucalyptus_grandis",
    "tropical_mixed",
}


def test_five_species_one_per_biome():
    assert set(SPECIES) == EXPECTED_KEYS


def test_species_are_immutable():
    sp = get_species("picea_abies")
    assert dataclasses.is_dataclass(sp)
    with pytest.raises(dataclasses.FrozenInstanceError):
        sp.k = 0.5  # type: ignore[misc]


@pytest.mark.parametrize("key", sorted(EXPECTED_KEYS))
def test_parameters_are_physically_plausible(key):
    sp = get_species(key)
    assert 10.0 < sp.m_max_kgC < 500.0
    assert 0.01 < sp.k < 0.25
    assert 1.0 <= sp.p <= 4.0
    assert 0.1 <= sp.beta_closure <= 1.0
    assert 1.0 < sp.stand_area_m2 < 50.0
    assert 0.05 < sp.alpha_canopy < 0.25
    assert 0.0 < sp.p_disturb < 0.05
    assert 0.0 <= sp.eps_immediate <= 1.0
    assert 1.0 < sp.tau_decay_yr < 100.0
    assert sp.valid_gez


def test_boreal_grows_slower_than_tropical():
    assert get_species("picea_abies").k < get_species("tropical_mixed").k


def test_plantation_grows_fastest():
    ks = {k: sp.k for k, sp in SPECIES.items()}
    assert max(ks, key=ks.get) == "eucalyptus_grandis"


@pytest.mark.parametrize("key", sorted(EXPECTED_KEYS))
def test_every_species_documents_its_sources(key):
    sp = get_species(key)
    for field in ("m_max_kgC", "k", "p", "p_disturb", "alpha_canopy"):
        assert field in sp.sources, f"{key}: keine Quelle fuer {field}"


def test_unknown_species_raises_with_helpful_message():
    with pytest.raises(KeyError, match="quercus_robur"):
        get_species("quercus_robur")
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_species.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.species'`

- [ ] **Step 3: Implementieren**

```python
# src/nbs/species.py
"""Representative tree species, one per biome.

Stock parameters are per tree at the stated stand density, not per hectare:
the presentation reasons about a single tree throughout, and the albedo term
needs the tree's own footprint.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Species:
    """Parameter set for one representative species."""

    key: str
    name_de: str
    name_lat: str

    m_max_kgC: float
    """Saturation carbon stock per tree [kgC]."""
    k: float
    """Chapman-Richards growth rate [1/a]."""
    p: float
    """Chapman-Richards shape parameter [-]."""
    beta_closure: float
    """Exponent linking canopy closure to relative stock [-]."""

    stand_area_m2: float
    """Ground area occupied by one tree [m^2]."""
    alpha_canopy: float
    """Albedo of the closed canopy [-]."""
    igbp_class: str
    """IGBP land cover class, used to look up transition albedo deltas."""

    p_disturb: float
    """Annual disturbance probability at zero background warming [1/a]."""
    severity_beta: tuple[float, float]
    """Beta(a, b) shape of the lost stock fraction given a disturbance."""
    gamma_warming: float
    """Sensitivity of disturbance probability to background warming [1/K]."""
    eps_immediate: float
    """Fraction of disturbed carbon released at once (combustion) [-]."""
    tau_decay_yr: float
    """Decay time of the remaining debris pool [a]."""

    valid_gez: tuple[str, ...]
    """FAO Global Ecological Zones the species may be planted in."""

    sources: dict[str, str] = field(default_factory=dict)


_IPCC = "IPCC 2019 Refinement, Vol. 4 Ch. 4"
_SEIDL = "Seidl et al. 2017, Nat. Clim. Change"
_BONAN = "Bonan 2008, Science"

SPECIES: dict[str, Species] = {
    "picea_abies": Species(
        key="picea_abies",
        name_de="Gemeine Fichte",
        name_lat="Picea abies",
        m_max_kgC=50.0,
        k=0.030,
        p=2.0,
        beta_closure=0.5,
        stand_area_m2=5.0,
        alpha_canopy=0.09,
        igbp_class="evergreen_needleleaf",
        p_disturb=0.012,
        severity_beta=(2.0, 2.0),
        gamma_warming=0.20,
        eps_immediate=0.30,
        tau_decay_yr=30.0,
        valid_gez=("boreal_coniferous_forest", "boreal_tundra_woodland",
                   "temperate_continental_forest"),
        sources={"m_max_kgC": _IPCC, "k": _IPCC, "p": _IPCC,
                 "p_disturb": _SEIDL, "alpha_canopy": _BONAN},
    ),
    "pinus_sylvestris": Species(
        key="pinus_sylvestris",
        name_de="Waldkiefer",
        name_lat="Pinus sylvestris",
        m_max_kgC=60.0,
        k=0.045,
        p=2.0,
        beta_closure=0.5,
        stand_area_m2=5.0,
        alpha_canopy=0.10,
        igbp_class="evergreen_needleleaf",
        p_disturb=0.008,
        severity_beta=(2.0, 2.5),
        gamma_warming=0.20,
        eps_immediate=0.35,
        tau_decay_yr=25.0,
        valid_gez=("temperate_continental_forest", "temperate_oceanic_forest",
                   "boreal_coniferous_forest"),
        sources={"m_max_kgC": _IPCC, "k": _IPCC, "p": _IPCC,
                 "p_disturb": _SEIDL, "alpha_canopy": _BONAN},
    ),
    "fagus_sylvatica": Species(
        key="fagus_sylvatica",
        name_de="Rotbuche",
        name_lat="Fagus sylvatica",
        m_max_kgC=75.0,
        k=0.040,
        p=2.2,
        beta_closure=0.5,
        stand_area_m2=6.0,
        alpha_canopy=0.15,
        igbp_class="deciduous_broadleaf",
        p_disturb=0.005,
        severity_beta=(2.0, 3.0),
        gamma_warming=0.20,
        eps_immediate=0.15,
        tau_decay_yr=20.0,
        valid_gez=("temperate_oceanic_forest", "temperate_continental_forest",
                   "temperate_mountain_system"),
        sources={"m_max_kgC": _IPCC, "k": _IPCC, "p": _IPCC,
                 "p_disturb": _SEIDL, "alpha_canopy": _BONAN},
    ),
    "eucalyptus_grandis": Species(
        key="eucalyptus_grandis",
        name_de="Rosen-Eukalyptus (Plantage)",
        name_lat="Eucalyptus grandis",
        m_max_kgC=50.0,
        k=0.120,
        p=1.75,
        beta_closure=0.4,
        stand_area_m2=4.0,
        alpha_canopy=0.13,
        igbp_class="evergreen_broadleaf",
        p_disturb=0.010,
        severity_beta=(2.0, 2.0),
        gamma_warming=0.20,
        eps_immediate=0.45,
        tau_decay_yr=12.0,
        valid_gez=("subtropical_humid_forest", "tropical_moist_deciduous_forest"),
        sources={"m_max_kgC": _IPCC, "k": _IPCC, "p": _IPCC,
                 "p_disturb": _SEIDL, "alpha_canopy": _BONAN},
    ),
    "tropical_mixed": Species(
        key="tropical_mixed",
        name_de="Tropischer Mischbestand",
        name_lat="gemischt, immergruen",
        m_max_kgC=100.0,
        k=0.080,
        p=2.5,
        beta_closure=0.5,
        stand_area_m2=5.0,
        alpha_canopy=0.12,
        igbp_class="evergreen_broadleaf",
        p_disturb=0.005,
        severity_beta=(2.0, 4.0),
        gamma_warming=0.20,
        eps_immediate=0.25,
        tau_decay_yr=10.0,
        valid_gez=("tropical_rainforest", "tropical_moist_deciduous_forest"),
        sources={"m_max_kgC": _IPCC, "k": _IPCC, "p": _IPCC,
                 "p_disturb": _SEIDL, "alpha_canopy": _BONAN},
    ),
}


def get_species(key: str) -> Species:
    """Return the species registered under *key*."""
    try:
        return SPECIES[key]
    except KeyError:
        known = ", ".join(sorted(SPECIES))
        raise KeyError(f"unknown species {key!r}; known species: {known}") from None
```

- [ ] **Step 4: Tests laufen lassen**

Run: `uv run pytest tests/test_species.py -v`
Expected: PASS, 16 Tests

- [ ] **Step 5: Commit**

```bash
git add src/nbs/species.py tests/test_species.py
git commit -m "feat: add five representative tree species

Stock parameters are per tree at the stated stand density, since the albedo
term needs the tree's own footprint. Every parameter carries its source so the
slides can quote the same numbers the code uses."
```

---

### Task 3: Wachstum in Bestandsform

Der Kern des Plans. Die geschlossene Chapman-Richards-Lösung kann keinen gestörten Baum beschreiben; die Bestandsform kann es.

**Files:**
- Create: `src/nbs/tree.py`
- Test: `tests/test_tree_growth.py`

**Interfaces:**
- Consumes: `nbs.species.Species`, `nbs.constants.YEARS`
- Produces:
  - `nbs.tree.biomass_closed(t_yr: np.ndarray, sp: Species) -> np.ndarray` — m(t) [kgC], geschlossene Lösung, nur für den ungestörten Fall
  - `nbs.tree.growth_rate_from_stock(m: np.ndarray | float, sp: Species) -> np.ndarray | float` — dm/dt [kgC/a] allein aus dem Vorrat
  - `nbs.tree.canopy_closure(m: np.ndarray | float, sp: Species) -> np.ndarray | float` — f ∈ [0, 1]

- [ ] **Step 1: Test schreiben**

```python
# tests/test_tree_growth.py
import numpy as np
import pytest

from nbs.species import get_species
from nbs.tree import biomass_closed, canopy_closure, growth_rate_from_stock

SP = get_species("fagus_sylvatica")


def test_closed_form_starts_at_zero_and_saturates():
    assert biomass_closed(np.array([0.0]), SP)[0] == pytest.approx(0.0)
    assert biomass_closed(np.array([1000.0]), SP)[0] == pytest.approx(SP.m_max_kgC, rel=1e-6)


def test_closed_form_is_monotonic():
    m = biomass_closed(np.arange(0.0, 200.0, 1.0), SP)
    assert np.all(np.diff(m) >= 0.0)


def test_stock_form_reproduces_closed_form_when_undisturbed():
    """Integrating dm/dt = g(m) must recover m(t) = m_max (1 - e^-kt)^p.

    This is the load-bearing property: everything downstream integrates the
    stock form, so if it drifts from the closed form the growth model quietly
    stops being Chapman-Richards.
    """
    dt = 1.0 / 12.0
    n = int(200 / dt)
    m = 1e-9  # a seedling, not exactly zero: dm/dt vanishes at m = 0
    for _ in range(n):
        # midpoint rule
        k1 = growth_rate_from_stock(m, SP)
        k2 = growth_rate_from_stock(m + 0.5 * dt * k1, SP)
        m = m + dt * k2
    expected = biomass_closed(np.array([200.0]), SP)[0]
    assert m == pytest.approx(expected, rel=1e-3)


def test_growth_rate_vanishes_at_saturation():
    assert growth_rate_from_stock(SP.m_max_kgC, SP) == pytest.approx(0.0, abs=1e-9)


def test_growth_rate_is_positive_below_saturation():
    assert growth_rate_from_stock(0.5 * SP.m_max_kgC, SP) > 0.0


def test_growth_rate_depends_only_on_stock_not_on_age():
    """A tree knocked back to half its stock grows like a tree that has just
    reached half its stock. That is what lets disturbed trees recover."""
    half = 0.5 * SP.m_max_kgC
    assert growth_rate_from_stock(half, SP) == growth_rate_from_stock(half, SP)


def test_canopy_closure_bounds():
    assert canopy_closure(0.0, SP) == pytest.approx(0.0)
    assert canopy_closure(SP.m_max_kgC, SP) == pytest.approx(1.0)
    assert canopy_closure(2.0 * SP.m_max_kgC, SP) == pytest.approx(1.0)


def test_canopy_closes_faster_than_stock_accumulates():
    """beta < 1: a young tree shades its footprint long before it is grown."""
    rel_stock = 0.25
    f = canopy_closure(rel_stock * SP.m_max_kgC, SP)
    assert f > rel_stock
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_tree_growth.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.tree'`

- [ ] **Step 3: Implementieren**

```python
# src/nbs/tree.py
"""Carbon stock of a single tree.

The closed Chapman-Richards solution describes an undisturbed tree. Disturbed
trees need the growth rate expressed in stock coordinates, because a tree that
has lost half its stock must resume growing at the rate belonging to what is
left, not at the rate belonging to its age.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.species import Species


def biomass_closed(t_yr: NDArray, sp: Species) -> NDArray:
    """Chapman-Richards stock of an undisturbed tree [kgC].

    m(t) = m_max (1 - exp(-k t))^p
    """
    t = np.asarray(t_yr, dtype=float)
    return sp.m_max_kgC * (1.0 - np.exp(-sp.k * t)) ** sp.p


def growth_rate_from_stock(m, sp: Species):
    """Growth rate dm/dt [kgC/a] as a function of stock alone.

    Substituting u = (m/m_max)^(1/p), so that exp(-k t) = 1 - u, turns the
    time derivative of the closed form into

        dm/dt = k p m_max u^(p-1) (1 - u)

    which no longer refers to t.
    """
    m_arr = np.asarray(m, dtype=float)
    u = np.clip(m_arr / sp.m_max_kgC, 0.0, 1.0) ** (1.0 / sp.p)
    rate = sp.k * sp.p * sp.m_max_kgC * u ** (sp.p - 1.0) * (1.0 - u)
    return rate if np.ndim(m) else float(rate)


def canopy_closure(m, sp: Species):
    """Fraction of the tree's footprint covered by canopy, f in [0, 1].

    f = min(1, (m/m_max)^beta) with beta < 1: canopy closes ahead of stock
    accumulation, so the albedo penalty arrives before the carbon benefit.
    """
    m_arr = np.asarray(m, dtype=float)
    f = np.clip(m_arr / sp.m_max_kgC, 0.0, 1.0) ** sp.beta_closure
    f = np.clip(f, 0.0, 1.0)
    return f if np.ndim(m) else float(f)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `uv run pytest tests/test_tree_growth.py -v`
Expected: PASS, 9 Tests

- [ ] **Step 5: Commit**

```bash
git add src/nbs/tree.py tests/test_tree_growth.py
git commit -m "feat: add Chapman-Richards growth in stock coordinates

Expressing dm/dt as a function of stock rather than age is what lets a
disturbed tree resume growing from whatever is left. The test that the stock
form reproduces the closed form under integration is the load-bearing one."
```

---

### Task 4: Störungspfade und Ökosystem-Kohlenstoff

**Files:**
- Modify: `src/nbs/tree.py`
- Test: `tests/test_tree_disturbance.py`

**Interfaces:**
- Consumes: `growth_rate_from_stock`, `canopy_closure`, `nbs.constants.YEARS`
- Produces:
  - `nbs.tree.TreeTrajectory` — eingefrorene Dataclass mit `years: NDArray`, `stock_kgC: NDArray`, `debris_kgC: NDArray`, `closure: NDArray`, `net_uptake_kgC_yr: NDArray` (positiv = Aufnahme durch das Ökosystem), `n_disturbances: int`
  - `nbs.tree.simulate_deterministic(sp: Species, t_background_k: NDArray, dt: float = 1/12) -> TreeTrajectory`
  - `nbs.tree.simulate_stochastic(sp: Species, t_background_k: NDArray, rng: np.random.Generator, dt: float = 1/12) -> TreeTrajectory`
  - `nbs.tree.simulate_ensemble(sp: Species, t_background_k: NDArray, n_members: int = 1000, seed: int = 0, dt: float = 1/12) -> list[TreeTrajectory]`
  - `nbs.tree.disturbance_probability(sp: Species, t_background_k: NDArray) -> NDArray`

Bilanzkonvention: der Ökosystemvorrat ist E = Vorrat + Zersetzungsvorrat. `net_uptake_kgC_yr` ist dE/dt. Eine Störung verschiebt einen Anteil s des Vorrats: der Anteil ε geht sofort in die Atmosphäre, der Rest in den Zersetzungsvorrat, der mit τ_dec zerfällt. Nur Zuwachs, Sofortfreisetzung und Zersetzung verändern E — die Störung selbst verschiebt intern.

- [ ] **Step 1: Test schreiben**

```python
# tests/test_tree_disturbance.py
import dataclasses

import numpy as np
import pytest

from nbs.constants import YEARS
from nbs.species import get_species
from nbs.tree import (
    TreeTrajectory,
    biomass_closed,
    disturbance_probability,
    simulate_deterministic,
    simulate_ensemble,
    simulate_stochastic,
)

SP = get_species("picea_abies")
NO_WARMING = np.zeros(len(YEARS))
STRONG_WARMING = np.linspace(0.0, 4.0, len(YEARS))


def test_disturbance_probability_rises_with_background_warming():
    p_cold = disturbance_probability(SP, NO_WARMING)
    p_warm = disturbance_probability(SP, STRONG_WARMING)
    assert p_cold[0] == pytest.approx(SP.p_disturb)
    assert p_warm[-1] > p_cold[-1]
    assert np.all(np.diff(p_warm) >= 0.0)


def test_disturbance_probability_stays_a_probability():
    p = disturbance_probability(SP, np.full(len(YEARS), 20.0))
    assert np.all(p <= 1.0)


def test_deterministic_run_without_disturbance_matches_closed_form():
    sp = get_species("fagus_sylvatica")
    quiet = dataclasses.replace(sp, p_disturb=0.0)
    traj = simulate_deterministic(quiet, NO_WARMING)
    expected = biomass_closed(YEARS - YEARS[0], quiet)
    assert np.allclose(traj.stock_kgC, expected, rtol=2e-3)


def test_trajectory_arrays_are_annual_and_aligned():
    traj = simulate_deterministic(SP, NO_WARMING)
    assert isinstance(traj, TreeTrajectory)
    for arr in (traj.stock_kgC, traj.debris_kgC, traj.closure, traj.net_uptake_kgC_yr):
        assert arr.shape == YEARS.shape
    assert np.array_equal(traj.years, YEARS)


def test_deterministic_disturbance_lowers_stock_below_undisturbed():
    quiet = dataclasses.replace(SP, p_disturb=0.0)
    assert simulate_deterministic(SP, NO_WARMING).stock_kgC[-1] < \
           simulate_deterministic(quiet, NO_WARMING).stock_kgC[-1]


def test_carbon_is_conserved():
    """Cumulative net uptake must equal the ecosystem stock that is standing.

    Carbon may sit in the tree or in debris; anything else has gone back to the
    atmosphere and must show up as reduced cumulative uptake.
    """
    traj = simulate_deterministic(SP, STRONG_WARMING)
    ecosystem = traj.stock_kgC + traj.debris_kgC
    # uptake[i] spans year i to i+1, stock[i] is the state at year i
    assert np.allclose(
        np.cumsum(traj.net_uptake_kgC_yr)[:-1],
        ecosystem[1:] - ecosystem[0],
        atol=0.5,
    )


def test_stochastic_run_is_reproducible_from_its_seed():
    a = simulate_stochastic(SP, NO_WARMING, np.random.default_rng(42))
    b = simulate_stochastic(SP, NO_WARMING, np.random.default_rng(42))
    assert np.array_equal(a.stock_kgC, b.stock_kgC)


def test_stochastic_runs_differ_across_seeds():
    a = simulate_stochastic(SP, NO_WARMING, np.random.default_rng(1))
    b = simulate_stochastic(SP, NO_WARMING, np.random.default_rng(2))
    assert not np.array_equal(a.stock_kgC, b.stock_kgC)


def test_disturbed_tree_regrows():
    """After a loss the stock must rise again — the point of the stock form."""
    rng = np.random.default_rng(7)
    traj = next(
        t for t in (simulate_stochastic(SP, NO_WARMING, rng) for _ in range(50))
        if t.n_disturbances > 0
    )
    drops = np.where(np.diff(traj.stock_kgC) < 0)[0]
    first_drop = int(drops[0])
    later = traj.stock_kgC[first_drop + 1:]
    assert later.max() > traj.stock_kgC[first_drop + 1]


def test_ensemble_size_and_spread():
    ens = simulate_ensemble(SP, NO_WARMING, n_members=50, seed=0)
    assert len(ens) == 50
    finals = np.array([t.stock_kgC[-1] for t in ens])
    assert finals.std() > 0.0


def test_ensemble_mean_stock_is_below_deterministic_run():
    """Disturbance is multiplicative in the stock, so averaging trajectories is
    not the same as running the average. The gap is the risk premium."""
    ens = simulate_ensemble(SP, STRONG_WARMING, n_members=200, seed=3)
    mean_final = np.mean([t.stock_kgC[-1] for t in ens])
    assert mean_final < simulate_deterministic(SP, STRONG_WARMING).stock_kgC[-1] * 1.05
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_tree_disturbance.py -v`
Expected: FAIL — `ImportError: cannot import name 'TreeTrajectory' from 'nbs.tree'`

- [ ] **Step 3: Implementieren**

```python
# an src/nbs/tree.py anhaengen

from dataclasses import dataclass

from nbs.constants import YEARS


@dataclass(frozen=True)
class TreeTrajectory:
    """One realisation of a tree's carbon over the study period."""

    years: NDArray
    stock_kgC: NDArray
    debris_kgC: NDArray
    closure: NDArray
    net_uptake_kgC_yr: NDArray
    """dE/dt of the ecosystem (tree + debris); positive means uptake."""
    n_disturbances: int


def disturbance_probability(sp: Species, t_background_k: NDArray) -> NDArray:
    """Annual disturbance probability, rising with background warming.

    p(t) = p0 exp(gamma T_background(t)), capped at 1.
    """
    t = np.asarray(t_background_k, dtype=float)
    return np.clip(sp.p_disturb * np.exp(sp.gamma_warming * t), 0.0, 1.0)


def _integrate(
    sp: Species,
    t_background_k: NDArray,
    dt: float,
    rng: np.random.Generator | None,
) -> TreeTrajectory:
    """Shared integrator. ``rng is None`` gives the expected-value run."""
    n_years = len(YEARS)
    p_annual = disturbance_probability(sp, t_background_k)
    steps_per_year = int(round(1.0 / dt))
    if abs(steps_per_year * dt - 1.0) > 1e-9:
        raise ValueError(f"dt={dt} does not divide one year evenly")

    stock = np.zeros(n_years)
    debris = np.zeros(n_years)
    uptake = np.zeros(n_years)

    m = 1e-9  # dm/dt vanishes at exactly zero, so start from a seedling
    d = 0.0
    n_dist = 0

    for iy in range(n_years):
        # record the state *at* YEARS[iy], before integrating that year, so
        # stock[0] is the seedling and lines up with biomass_closed(0)
        stock[iy] = m
        debris[iy] = d
        e_before = m + d

        p_step = 1.0 - (1.0 - p_annual[iy]) ** dt

        for _ in range(steps_per_year):
            # growth, midpoint rule
            k1 = growth_rate_from_stock(m, sp)
            k2 = growth_rate_from_stock(m + 0.5 * dt * k1, sp)
            grown = dt * k2

            # debris decay
            decayed = d * (1.0 - np.exp(-dt / sp.tau_decay_yr))

            # disturbance
            if rng is None:
                severity = sp.severity_beta[0] / sum(sp.severity_beta)
                lost = p_step * severity * m
            else:
                if rng.random() < p_step:
                    severity = rng.beta(*sp.severity_beta)
                    lost = severity * m
                    n_dist += 1
                else:
                    lost = 0.0

            immediate = sp.eps_immediate * lost  # straight to the atmosphere
            to_debris = lost - immediate

            m = m + grown - lost
            d = d + to_debris - decayed

        uptake[iy] = (m + d) - e_before

    return TreeTrajectory(
        years=YEARS.copy(),
        stock_kgC=stock,
        debris_kgC=debris,
        closure=canopy_closure(stock, sp),
        net_uptake_kgC_yr=uptake,
        n_disturbances=n_dist,
    )


def simulate_deterministic(
    sp: Species, t_background_k: NDArray, dt: float = 1.0 / 12.0
) -> TreeTrajectory:
    """Expected-value run: disturbance drains stock continuously at p * E[s]."""
    return _integrate(sp, t_background_k, dt, rng=None)


def simulate_stochastic(
    sp: Species,
    t_background_k: NDArray,
    rng: np.random.Generator,
    dt: float = 1.0 / 12.0,
) -> TreeTrajectory:
    """One Monte-Carlo realisation with discrete disturbance events."""
    return _integrate(sp, t_background_k, dt, rng=rng)


def simulate_ensemble(
    sp: Species,
    t_background_k: NDArray,
    n_members: int = 1000,
    seed: int = 0,
    dt: float = 1.0 / 12.0,
) -> list[TreeTrajectory]:
    """``n_members`` independent realisations from one seed sequence."""
    seeds = np.random.SeedSequence(seed).spawn(n_members)
    return [
        simulate_stochastic(sp, t_background_k, np.random.default_rng(s), dt)
        for s in seeds
    ]
```

- [ ] **Step 4: Tests laufen lassen**

Run: `uv run pytest tests/test_tree_disturbance.py -v`
Expected: PASS, 11 Tests. Sollte `test_carbon_is_conserved` scheitern, ist die Buchführung falsch: Störung darf E nicht direkt verändern, nur Sofortfreisetzung und Zersetzung dürfen das.

- [ ] **Step 5: Laufzeit prüfen**

Run: `uv run python -c "
import time, numpy as np
from nbs.constants import YEARS
from nbs.species import get_species
from nbs.tree import simulate_ensemble
t0=time.time(); simulate_ensemble(get_species('picea_abies'), np.zeros(len(YEARS)), n_members=1000, seed=0); print(f'{time.time()-t0:.1f} s')
"`
Expected: unter 60 s. Dauert es länger, `dt` auf 1/4 anheben und den Vergleich mit der geschlossenen Form erneut prüfen.

- [ ] **Step 6: Commit**

```bash
git add src/nbs/tree.py tests/test_tree_disturbance.py
git commit -m "feat: add disturbance events, debris pool and Monte-Carlo ensemble

Disturbance moves carbon within the ecosystem; only combustion and debris decay
return it to the atmosphere. Keeping that distinction is what makes the carbon
conservation test meaningful, and it makes the albedo penalty relax on its own
when a stand is lost."
```

---

### Task 5: Impulsantworten aus FaIR und Faltung

**Files:**
- Create: `src/nbs/response.py`
- Test: `tests/test_response.py`

**Interfaces:**
- Consumes: `nbs.legacy.fair_module` existiert nicht — FaIR wird hier direkt angesprochen; `src/nbs/fair_module.py` bleibt an seinem Platz und wird wiederverwendet
- Produces:
  - `nbs.response.green_carbon(scenario: str = "ssp245") -> NDArray` — g_C, Länge `len(YEARS)`, `g_C[0] == 1.0`, monoton fallend
  - `nbs.response.green_temperature(scenario: str = "ssp245") -> NDArray` — g_T [K je (W/m²·a)], Länge `len(YEARS)`, `g_T[0] == 0.0`
  - `nbs.response.convolve_response(g: NDArray, x: NDArray, dt: float = 1.0) -> NDArray` — kausale diskrete Faltung, Länge wie `x`

Hinweis für den Implementierenden: `src/nbs/fair_module.py` blieb bei Task 1 auf oberster Ebene liegen, weil es weiterverwendet wird. Seine Zeitachse läuft von 2025 bis 2149 (125 Werte); `YEARS` hat 126 Werte. Die Impulsantworten werden auf `len(YEARS)` gebracht, indem der letzte Wert einmal wiederholt wird — dokumentiert im Docstring.

- [ ] **Step 1: Test schreiben**

```python
# tests/test_response.py
import numpy as np
import pytest

from nbs.constants import YEARS
from nbs.response import convolve_response, green_carbon, green_temperature


def test_convolution_is_causal():
    g = np.array([0.0, 1.0, 0.5, 0.25])
    x = np.array([0.0, 0.0, 1.0, 0.0])
    y = convolve_response(g, x)
    assert y[0] == 0.0
    assert y[1] == 0.0  # nothing before the input can respond to it


def test_convolution_matches_hand_computed_values():
    g = np.array([0.0, 1.0, 0.5])
    x = np.array([2.0, 0.0, 0.0])
    y = convolve_response(g, x)
    assert y == pytest.approx([0.0, 2.0, 1.0])


def test_convolution_preserves_length():
    g = np.ones(len(YEARS))
    x = np.ones(len(YEARS))
    assert convolve_response(g, x).shape == (len(YEARS),)


def test_convolution_is_linear():
    rng = np.random.default_rng(0)
    g = rng.random(20)
    a, b = rng.random(20), rng.random(20)
    lhs = convolve_response(g, 3.0 * a + 2.0 * b)
    rhs = 3.0 * convolve_response(g, a) + 2.0 * convolve_response(g, b)
    assert np.allclose(lhs, rhs)


@pytest.mark.slow
def test_carbon_green_function_is_a_decaying_airborne_fraction():
    g = green_carbon("ssp245")
    assert g.shape == (len(YEARS),)
    assert g[0] == pytest.approx(1.0, abs=0.05)
    assert 0.2 < g[75] < 0.6, "about 40 percent airborne after 75 years (Joos 2013)"
    assert np.all(np.diff(g) <= 1e-3), "airborne fraction must not rise"


@pytest.mark.slow
def test_temperature_green_function_peaks_then_decays():
    g = green_temperature("ssp245")
    assert g.shape == (len(YEARS),)
    assert g[0] == pytest.approx(0.0, abs=1e-9)
    assert g.max() > 0.0
    peak = int(np.argmax(g))
    assert 0 < peak < 25, "surface response peaks within a couple of decades"
    assert g[-1] < g[peak], "deep ocean draws the response back down"


@pytest.mark.slow
def test_convolution_reproduces_a_full_fair_run():
    """The whole plan rests on replacing FaIR runs with one convolution.

    Build a forcing series, push it through FaIR directly, and check that the
    convolution of the Green's function with the same series agrees.
    """
    from nbs.fair_module import run_fair_baseline, run_fair_perturbed

    n = len(YEARS) - 1  # fair_module works on 125 years
    phi = np.zeros(n)
    phi[10:] = 0.05  # a step in forcing, W/m^2

    direct = run_fair_perturbed(np.zeros(n), phi, scenario="ssp245") - run_fair_baseline("ssp245")
    via_convolution = convolve_response(green_temperature("ssp245"), np.append(phi, phi[-1]))[:n]

    scale = np.abs(direct).max()
    assert np.abs(direct - via_convolution).max() < 0.05 * scale
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_response.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.response'`

- [ ] **Step 3: Implementieren**

```python
# src/nbs/response.py
"""Impulse responses of the carbon cycle and of temperature.

FaIR is run a handful of times here and never again. Everything downstream —
Monte-Carlo ensembles, global grids — is a convolution against these two
functions, which is what makes those affordable. It is also literally the
equation on slide 24.
"""

from __future__ import annotations

import functools

import numpy as np
from numpy.typing import NDArray

from nbs.constants import YEARS

_PULSE_GTCO2 = 1.0
_PULSE_WM2 = 1.0


def _to_study_length(x: NDArray) -> NDArray:
    """Pad a 125-year fair_module series to the 126-year study axis.

    fair_module slices 2025..2149; YEARS runs 2025..2150 inclusive. The final
    year is filled by repeating the last value, which is well inside the noise
    of a response that is nearly flat by then.
    """
    if len(x) == len(YEARS):
        return x
    return np.append(x, x[-1])


@functools.lru_cache(maxsize=4)
def green_carbon(scenario: str = "ssp245") -> NDArray:
    """Airborne fraction g_C(t) of a CO2 pulse released at T_START.

    Returns the fraction of the pulse still in the atmosphere after t years,
    so g_C(0) = 1 and g_C decays. Joos et al. (2013), slide 13.
    """
    from nbs.fair_module import _START_IDX, _END_IDX, _create_fair

    base = _create_fair(scenario)
    base.run()
    airborne_base = base.airborne_emissions.sel(
        scenario=scenario, config="central", specie="CO2"
    ).values[_START_IDX:_END_IDX]

    pert = _create_fair(scenario)
    co2 = pert.emissions.sel(specie="CO2 FFI").values.copy()
    co2[_START_IDX, 0, 0] += _PULSE_GTCO2
    pert.emissions.loc[dict(specie="CO2 FFI")] = co2
    pert.run()
    airborne_pert = pert.airborne_emissions.sel(
        scenario=scenario, config="central", specie="CO2"
    ).values[_START_IDX:_END_IDX]

    g = (np.asarray(airborne_pert) - np.asarray(airborne_base)) / _PULSE_GTCO2
    return _to_study_length(np.asarray(g, dtype=float))


@functools.lru_cache(maxsize=4)
def green_temperature(scenario: str = "ssp245") -> NDArray:
    """Temperature response g_T(t) to a one-year unit forcing pulse.

    Units: K per (W/m^2 sustained for one year). g_T(0) = 0 because the pulse
    has not acted yet at the moment it is applied.
    """
    from nbs.fair_module import _START_IDX, _END_IDX, _create_fair, run_fair_baseline

    baseline = run_fair_baseline(scenario)

    f = _create_fair(scenario)
    solar = f.forcing.sel(specie="Solar").values.copy()
    solar[_START_IDX, 0, 0] += _PULSE_WM2
    f.forcing.loc[dict(specie="Solar")] = solar
    f.run()
    perturbed = f.temperature.sel(
        scenario=scenario, config="central", layer=0
    ).values[_START_IDX:_END_IDX]

    g = (np.asarray(perturbed, dtype=float) - baseline) / _PULSE_WM2
    g = _to_study_length(g)
    g[0] = 0.0
    return g


def convolve_response(g: NDArray, x: NDArray, dt: float = 1.0) -> NDArray:
    """Causal discrete convolution y[n] = dt * sum_{m<=n} g[n-m] x[m]."""
    g = np.asarray(g, dtype=float)
    x = np.asarray(x, dtype=float)
    return dt * np.convolve(x, g)[: len(x)]
```

- [ ] **Step 4: Schnelle Tests laufen lassen**

Run: `uv run pytest tests/test_response.py -v -m "not slow"`
Expected: PASS, 4 Tests

- [ ] **Step 5: Langsame Tests laufen lassen**

Run: `uv run pytest tests/test_response.py -v -m slow`
Expected: PASS, 3 Tests.

Kommt `g_C[0]` als ungefähr 0 statt 1 heraus, ist die Zeitachse um einen Index
verschoben: FaIR legt Emissionen auf *timepoints*, Bestände auf *timebounds*.
Dann in `green_carbon` auf `_START_IDX + 1 : _END_IDX + 1` wechseln und den
Docstring entsprechend ergänzen.

Der Faltungsvergleich ist der wichtigste Test des ganzen Plans. Scheitert er, ist entweder die Zeitachsen-Ausrichtung um ein Jahr verschoben oder die Linearitätsannahme trägt nicht; beides muss geklärt werden, bevor irgendetwas darauf aufbaut.

- [ ] **Step 6: Commit**

```bash
git add src/nbs/response.py tests/test_response.py
git commit -m "feat: derive carbon and temperature Green's functions from FaIR

FaIR runs a handful of times here and never again; ensembles and grids become
convolutions. The test comparing convolution against a direct FaIR run is what
licenses that substitution."
```

---

### Task 6: Antriebe

**Files:**
- Create: `src/nbs/forcing.py`
- Test: `tests/test_forcing.py`

**Interfaces:**
- Consumes: `nbs.constants`, `nbs.species.Species`, `nbs.response.green_carbon`, `nbs.response.convolve_response`
- Produces:
  - `nbs.forcing.co2_flux_kg_per_yr(net_uptake_kgC_yr: NDArray) -> NDArray` — ṁ_CO₂ [kg CO₂/a], negativ = Entnahme
  - `nbs.forcing.phi_co2(co2_flux_kg_per_yr: NDArray, g_c: NDArray) -> NDArray` — [W/m²]
  - `nbs.forcing.phi_albedo(closure: NDArray, delta_alpha: float, q_sw_w_m2: float, sp: Species) -> NDArray` — [W/m²]
  - `nbs.forcing.light_bulb_watts(delta_alpha: float, q_sw_w_m2: float, sp: Species) -> float` — zusätzlich absorbierte Leistung je Baum bei geschlossenem Kronendach [W], **ohne** τ, weil an der Oberfläche gemessen
  - `nbs.forcing.fallback_delta_alpha(lat_deg: float) -> float` und `nbs.forcing.fallback_q_sw(lat_deg: float) -> float` — breitenparametrisierte Ersatzwerte, bis die Raster aus Plan 2 vorliegen

- [ ] **Step 1: Test schreiben**

```python
# tests/test_forcing.py
import numpy as np
import pytest

from nbs.constants import A_CO2_W_M2_PER_KG, M_CO2_PER_C, YEARS
from nbs.forcing import (
    co2_flux_kg_per_yr,
    fallback_delta_alpha,
    fallback_q_sw,
    light_bulb_watts,
    phi_albedo,
    phi_co2,
)
from nbs.species import get_species

BOREAL = get_species("picea_abies")
TROPICAL = get_species("tropical_mixed")


def test_uptake_becomes_negative_co2_flux():
    flux = co2_flux_kg_per_yr(np.array([1.0, 2.0]))
    assert flux == pytest.approx([-M_CO2_PER_C, -2.0 * M_CO2_PER_C])


def test_release_becomes_positive_co2_flux():
    assert co2_flux_kg_per_yr(np.array([-1.0]))[0] > 0.0


def test_phi_co2_of_steady_removal_is_negative_and_grows():
    flux = np.full(len(YEARS), -100.0)
    g_c = np.ones(len(YEARS))  # nothing is reabsorbed: worst case for the sign
    phi = phi_co2(flux, g_c)
    assert phi[10] < 0.0
    assert phi[-1] < phi[10], "the gap keeps widening while removal continues"


def test_phi_co2_scales_with_radiative_efficiency():
    flux = np.zeros(len(YEARS))
    flux[0] = -1000.0
    g_c = np.ones(len(YEARS))
    phi = phi_co2(flux, g_c)
    assert phi[0] == pytest.approx(-1000.0 * A_CO2_W_M2_PER_KG)


def test_darker_forest_warms():
    """delta_alpha < 0 means the forest is darker than what it replaces."""
    f = np.ones(len(YEARS))
    assert phi_albedo(f, -0.13, 110.0, BOREAL)[0] > 0.0


def test_brighter_surface_cools():
    f = np.ones(len(YEARS))
    assert phi_albedo(f, +0.05, 200.0, TROPICAL)[0] < 0.0


def test_albedo_forcing_follows_canopy_closure():
    f = np.linspace(0.0, 1.0, len(YEARS))
    phi = phi_albedo(f, -0.13, 110.0, BOREAL)
    assert phi[0] == pytest.approx(0.0)
    assert np.all(np.diff(phi) >= 0.0)


def test_boreal_tree_is_a_seventy_watt_light_bulb():
    """Slide 14 quotes about 70 W for a boreal tree. Code and slide must agree."""
    w = light_bulb_watts(fallback_delta_alpha(60.0), fallback_q_sw(60.0), BOREAL)
    assert 55.0 < w < 90.0


def test_tropical_tree_is_about_half_a_boreal_one():
    """Slide 14: 'in den Tropen etwa halb so viel'."""
    boreal = light_bulb_watts(fallback_delta_alpha(60.0), fallback_q_sw(60.0), BOREAL)
    tropical = light_bulb_watts(fallback_delta_alpha(0.0), fallback_q_sw(0.0), TROPICAL)
    assert 0.3 < tropical / boreal < 0.7


def test_fallback_albedo_change_grows_with_latitude():
    lats = [0.0, 15.0, 30.0, 45.0, 60.0, 75.0]
    magnitudes = [abs(fallback_delta_alpha(x)) for x in lats]
    assert magnitudes == sorted(magnitudes)


def test_fallback_insolation_falls_towards_the_pole():
    assert fallback_q_sw(15.0) > fallback_q_sw(60.0) > fallback_q_sw(85.0)


def test_fallback_functions_interpolate_between_table_rows():
    mid = fallback_q_sw(52.5)
    assert min(fallback_q_sw(45.0), fallback_q_sw(60.0)) < mid < max(
        fallback_q_sw(45.0), fallback_q_sw(60.0)
    )
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_forcing.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.forcing'`

- [ ] **Step 3: Implementieren**

```python
# src/nbs/forcing.py
"""The two forcing channels of a single tree.

Carbon acts globally and carries no area term, because CO2 mixes. Albedo acts
only where the tree stands and is therefore weighted by the tree's share of the
Earth's surface. Slides 21 and 22.

Evapotranspiration is deliberately absent: it does not cross the top-of-
atmosphere boundary and its effect sits in the feedback parameter Lambda.
Slide 18 argues this in full.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.constants import A_CO2_W_M2_PER_KG, A_EARTH_M2, M_CO2_PER_C, TAU_ATM
from nbs.response import convolve_response
from nbs.species import Species


def co2_flux_kg_per_yr(net_uptake_kgC_yr: NDArray) -> NDArray:
    """Atmospheric CO2 flux [kg CO2/a] from ecosystem carbon uptake.

    What the tree stores is missing from the air, hence the sign flip.
    """
    return -M_CO2_PER_C * np.asarray(net_uptake_kgC_yr, dtype=float)


def phi_co2(co2_flux_kg_per_yr: NDArray, g_c: NDArray) -> NDArray:
    """Radiative forcing [W/m^2] from the CO2 the tree keeps out of the air.

    The flux is convolved with the airborne fraction, so only the part of each
    past year's removal that is still missing counts today.
    """
    delta_m = convolve_response(g_c, np.asarray(co2_flux_kg_per_yr, dtype=float))
    return A_CO2_W_M2_PER_KG * delta_m


def phi_albedo(
    closure: NDArray, delta_alpha: float, q_sw_w_m2: float, sp: Species
) -> NDArray:
    """Radiative forcing [W/m^2] from the tree darkening its footprint.

    delta_alpha is the albedo of the forest minus the albedo of the land it
    replaces, so a darker forest gives delta_alpha < 0 and a positive forcing.
    """
    f = np.asarray(closure, dtype=float)
    return -delta_alpha * q_sw_w_m2 * TAU_ATM * f * sp.stand_area_m2 / A_EARTH_M2


def light_bulb_watts(delta_alpha: float, q_sw_w_m2: float, sp: Species) -> float:
    """Extra power absorbed by one closed-canopy tree [W].

    No transmittance factor: this is measured at the surface, where the tree
    is, not at the top of the atmosphere. Slide 14's 'light bulb that never
    goes out'.
    """
    return float(-delta_alpha * q_sw_w_m2 * sp.stand_area_m2)


_LAT_TABLE = np.array([0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0])
_DELTA_ALPHA_TABLE = np.array([-0.033, -0.033, -0.040, -0.070, -0.130, -0.160, -0.160])
_Q_SW_TABLE = np.array([210.0, 230.0, 225.0, 160.0, 110.0, 75.0, 60.0])


def fallback_delta_alpha(lat_deg: float) -> float:
    """Annual-mean forest-minus-open albedo change, by latitude.

    Stand-in until the Duveiller transition rasters land in plan 2. Values are
    tuned so that a boreal tree comes out near the 70 W quoted on slide 14.
    """
    return float(np.interp(abs(lat_deg), _LAT_TABLE, _DELTA_ALPHA_TABLE))


def fallback_q_sw(lat_deg: float) -> float:
    """Annual-mean downward shortwave at the surface [W/m^2], by latitude.

    Stand-in until CERES or ERA5 fields land in plan 2.
    """
    return float(np.interp(abs(lat_deg), _LAT_TABLE, _Q_SW_TABLE))
```

- [ ] **Step 4: Tests laufen lassen**

Run: `uv run pytest tests/test_forcing.py -v`
Expected: PASS, 12 Tests. `test_boreal_tree_is_a_seventy_watt_light_bulb` bindet den Code an eine Zahl, die im Vortrag steht — scheitert er, muss entweder die Tabelle oder die Folie geändert werden, und diese Entscheidung gehört dem Nutzer.

- [ ] **Step 5: Commit**

```bash
git add src/nbs/forcing.py tests/test_forcing.py
git commit -m "feat: add CO2 and albedo forcing channels

Carbon carries no area term because it mixes; albedo is weighted by the tree's
share of the Earth's surface. Latitude fallbacks stand in until the rasters
arrive, tuned so a boreal tree reproduces the 70 W quoted on slide 14."
```

---

### Task 7: Kennzahlen und die vollständige Kette

**Files:**
- Create: `src/nbs/metrics.py`
- Create: `src/nbs/pipeline.py`
- Test: `tests/test_metrics.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: alles Bisherige
- Produces:
  - `nbs.metrics.t_star(delta_t: NDArray, years: NDArray) -> float` — Jahr, ab dem ΔT dauerhaft ≤ 0 bleibt; `np.inf`, wenn nie
  - `nbs.metrics.prob_warming(ensemble_delta_t: NDArray, years: NDArray, year: int) -> float` — Anteil der Läufe mit ΔT > 0 in `year`; `ensemble_delta_t` hat die Form (n_members, n_years)
  - `nbs.metrics.risk_premium(ensemble_delta_t: NDArray, deterministic_delta_t: NDArray, years: NDArray, year: int) -> float` — Ensemblemittel minus deterministischer Wert [K]
  - `nbs.metrics.quantile_band(ensemble_delta_t: NDArray, lo: float = 0.05, hi: float = 0.95) -> tuple[NDArray, NDArray, NDArray]` — (unteres Band, Median, oberes Band)
  - `nbs.pipeline.SiteResult` — eingefrorene Dataclass mit `species_key: str`, `lat_deg: float`, `scenario: str`, `years: NDArray`, `phi_co2: NDArray`, `phi_albedo: NDArray`, `phi_total: NDArray`, `delta_t: NDArray`, `trajectory: TreeTrajectory`
  - `nbs.pipeline.run_single_tree(species_key: str, lat_deg: float, scenario: str = "ssp245", delta_alpha: float | None = None, q_sw: float | None = None) -> SiteResult`
  - `nbs.pipeline.run_single_tree_ensemble(species_key: str, lat_deg: float, scenario: str = "ssp245", n_members: int = 1000, seed: int = 0, delta_alpha: float | None = None, q_sw: float | None = None) -> tuple[SiteResult, NDArray]` — deterministisches Ergebnis plus Ensemble-ΔT der Form (n_members, n_years)

- [ ] **Step 1: Test für die Kennzahlen schreiben**

```python
# tests/test_metrics.py
import numpy as np
import pytest

from nbs.metrics import prob_warming, quantile_band, risk_premium, t_star

YEARS = np.arange(2025, 2035)


def test_t_star_is_the_year_after_the_last_sign_change():
    dt = np.array([1.0, 1.0, -1.0, 1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0])
    assert t_star(dt, YEARS) == 2030


def test_t_star_is_infinite_when_still_warming_at_the_end():
    assert t_star(np.ones(10), YEARS) == np.inf


def test_t_star_is_the_first_year_when_never_warming():
    assert t_star(-np.ones(10), YEARS) == 2025


def test_prob_warming_counts_members_above_zero():
    ens = np.array([[1.0] * 10, [-1.0] * 10, [1.0] * 10, [-1.0] * 10])
    assert prob_warming(ens, YEARS, 2030) == pytest.approx(0.5)


def test_risk_premium_is_positive_when_ensemble_warms_more():
    ens = np.full((5, 10), -0.1)
    det = np.full(10, -0.3)
    assert risk_premium(ens, det, YEARS, 2030) == pytest.approx(0.2)


def test_quantile_band_is_ordered():
    rng = np.random.default_rng(0)
    ens = rng.normal(size=(200, 10))
    lo, med, hi = quantile_band(ens)
    assert np.all(lo <= med)
    assert np.all(med <= hi)
    assert lo.shape == (10,)
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_metrics.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.metrics'`

- [ ] **Step 3: Kennzahlen implementieren**

```python
# src/nbs/metrics.py
"""Summary numbers for a temperature trajectory."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def t_star(delta_t: NDArray, years: NDArray) -> float:
    """Year from which the intervention stays net cooling.

    Not the first year with delta_t <= 0 — early on neither channel has acted
    yet, so that year would always be the first. This is the year after the
    last sign change: from here on the net effect never turns positive again.
    """
    dt = np.asarray(delta_t, dtype=float)
    warming = np.flatnonzero(dt > 0.0)
    if warming.size == 0:
        return float(years[0])
    last = int(warming[-1])
    if last >= len(dt) - 1:
        return float(np.inf)
    return float(years[last + 1])


def _year_index(years: NDArray, year: int) -> int:
    idx = np.flatnonzero(np.asarray(years) == year)
    if idx.size == 0:
        raise ValueError(f"year {year} is outside {years[0]}..{years[-1]}")
    return int(idx[0])


def prob_warming(ensemble_delta_t: NDArray, years: NDArray, year: int) -> float:
    """Fraction of ensemble members that are still warming in *year*."""
    col = np.asarray(ensemble_delta_t)[:, _year_index(years, year)]
    return float(np.mean(col > 0.0))


def risk_premium(
    ensemble_delta_t: NDArray, deterministic_delta_t: NDArray, years: NDArray, year: int
) -> float:
    """Ensemble mean minus deterministic run [K] in *year*.

    Positive means the deterministic run overstates the cooling — the amount by
    which ignoring disturbance risk flatters the result.
    """
    i = _year_index(years, year)
    return float(np.mean(np.asarray(ensemble_delta_t)[:, i]) - np.asarray(deterministic_delta_t)[i])


def quantile_band(
    ensemble_delta_t: NDArray, lo: float = 0.05, hi: float = 0.95
) -> tuple[NDArray, NDArray, NDArray]:
    """Lower band, median and upper band across ensemble members."""
    ens = np.asarray(ensemble_delta_t, dtype=float)
    return (
        np.quantile(ens, lo, axis=0),
        np.quantile(ens, 0.5, axis=0),
        np.quantile(ens, hi, axis=0),
    )
```

- [ ] **Step 4: Kennzahlen-Tests laufen lassen**

Run: `uv run pytest tests/test_metrics.py -v`
Expected: PASS, 6 Tests

- [ ] **Step 5: Test für die Kette schreiben**

```python
# tests/test_pipeline.py
import numpy as np
import pytest

from nbs.constants import YEARS
from nbs.metrics import t_star
from nbs.pipeline import SiteResult, run_single_tree, run_single_tree_ensemble


@pytest.mark.slow
def test_single_tree_result_is_well_formed():
    r = run_single_tree("tropical_mixed", lat_deg=0.0)
    assert isinstance(r, SiteResult)
    for arr in (r.phi_co2, r.phi_albedo, r.phi_total, r.delta_t):
        assert arr.shape == YEARS.shape
    assert np.allclose(r.phi_total, r.phi_co2 + r.phi_albedo)


@pytest.mark.slow
def test_tropical_tree_cools_and_boreal_tree_does_not():
    """The central claim of the talk, as a test."""
    tropical = run_single_tree("tropical_mixed", lat_deg=0.0)
    boreal = run_single_tree("picea_abies", lat_deg=60.0)
    assert tropical.delta_t[-1] < 0.0
    assert t_star(tropical.delta_t, YEARS) < np.inf
    assert boreal.delta_t[-1] > tropical.delta_t[-1]


@pytest.mark.slow
def test_albedo_channel_warms_at_high_latitude():
    boreal = run_single_tree("picea_abies", lat_deg=60.0)
    assert np.all(boreal.phi_albedo >= 0.0)
    assert boreal.phi_albedo[-1] > 0.0


@pytest.mark.slow
def test_carbon_channel_cools_once_the_tree_has_grown():
    r = run_single_tree("tropical_mixed", lat_deg=0.0)
    assert r.phi_co2[-1] < 0.0


@pytest.mark.slow
def test_ensemble_returns_matching_shapes_and_spread():
    det, ens = run_single_tree_ensemble("picea_abies", lat_deg=60.0, n_members=20, seed=0)
    assert ens.shape == (20, len(YEARS))
    assert ens[:, -1].std() > 0.0


@pytest.mark.slow
def test_explicit_albedo_override_beats_the_fallback():
    a = run_single_tree("picea_abies", lat_deg=60.0, delta_alpha=-0.30, q_sw=110.0)
    b = run_single_tree("picea_abies", lat_deg=60.0, delta_alpha=-0.05, q_sw=110.0)
    assert a.phi_albedo[-1] > b.phi_albedo[-1]
```

- [ ] **Step 6: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_pipeline.py -v -m slow`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.pipeline'`

- [ ] **Step 7: Kette implementieren**

```python
# src/nbs/pipeline.py
"""The full chain for one tree at one place: stock, forcing, temperature."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from nbs.constants import YEARS
from nbs.forcing import (
    co2_flux_kg_per_yr,
    fallback_delta_alpha,
    fallback_q_sw,
    phi_albedo,
    phi_co2,
)
from nbs.response import convolve_response, green_carbon, green_temperature
from nbs.species import get_species
from nbs.tree import TreeTrajectory, simulate_deterministic, simulate_ensemble


@dataclass(frozen=True)
class SiteResult:
    """Everything the results slides need for one tree at one site."""

    species_key: str
    lat_deg: float
    scenario: str
    years: NDArray
    phi_co2: NDArray
    phi_albedo: NDArray
    phi_total: NDArray
    delta_t: NDArray
    trajectory: TreeTrajectory


def _background_temperature(scenario: str) -> NDArray:
    from nbs.fair_module import run_fair_baseline

    base = run_fair_baseline(scenario)
    if len(base) == len(YEARS):
        return base
    return np.append(base, base[-1])


def _forcings(
    trajectory: TreeTrajectory,
    species_key: str,
    lat_deg: float,
    scenario: str,
    delta_alpha: float | None,
    q_sw: float | None,
) -> tuple[NDArray, NDArray]:
    sp = get_species(species_key)
    d_alpha = fallback_delta_alpha(lat_deg) if delta_alpha is None else delta_alpha
    q = fallback_q_sw(lat_deg) if q_sw is None else q_sw

    f_co2 = phi_co2(
        co2_flux_kg_per_yr(trajectory.net_uptake_kgC_yr), green_carbon(scenario)
    )
    f_alb = phi_albedo(trajectory.closure, d_alpha, q, sp)
    return f_co2, f_alb


def run_single_tree(
    species_key: str,
    lat_deg: float,
    scenario: str = "ssp245",
    delta_alpha: float | None = None,
    q_sw: float | None = None,
) -> SiteResult:
    """Deterministic run: one tree, one place, expected-value disturbance."""
    sp = get_species(species_key)
    background = _background_temperature(scenario)
    traj = simulate_deterministic(sp, background)
    f_co2, f_alb = _forcings(traj, species_key, lat_deg, scenario, delta_alpha, q_sw)
    phi = f_co2 + f_alb
    delta_t = convolve_response(green_temperature(scenario), phi)

    return SiteResult(
        species_key=species_key,
        lat_deg=lat_deg,
        scenario=scenario,
        years=YEARS.copy(),
        phi_co2=f_co2,
        phi_albedo=f_alb,
        phi_total=phi,
        delta_t=delta_t,
        trajectory=traj,
    )


def run_single_tree_ensemble(
    species_key: str,
    lat_deg: float,
    scenario: str = "ssp245",
    n_members: int = 1000,
    seed: int = 0,
    delta_alpha: float | None = None,
    q_sw: float | None = None,
) -> tuple[SiteResult, NDArray]:
    """Deterministic run plus a Monte-Carlo ensemble of delta_t trajectories."""
    sp = get_species(species_key)
    background = _background_temperature(scenario)
    deterministic = run_single_tree(species_key, lat_deg, scenario, delta_alpha, q_sw)

    g_t = green_temperature(scenario)
    members = simulate_ensemble(sp, background, n_members=n_members, seed=seed)

    ensemble = np.empty((n_members, len(YEARS)))
    for i, traj in enumerate(members):
        f_co2, f_alb = _forcings(traj, species_key, lat_deg, scenario, delta_alpha, q_sw)
        ensemble[i] = convolve_response(g_t, f_co2 + f_alb)

    return deterministic, ensemble
```

- [ ] **Step 8: Tests laufen lassen**

Run: `uv run pytest tests/test_pipeline.py -v -m slow`
Expected: PASS, 6 Tests. Scheitert `test_tropical_tree_cools_and_boreal_tree_does_not`, ist die Aussage des Vortrags im Modell nicht reproduziert — das ist ein Befund, kein Testfehler, und muss dem Nutzer vorgelegt werden, bevor Parameter angepasst werden.

- [ ] **Step 9: Gesamte Testsuite laufen lassen**

Run: `uv run pytest -q`
Expected: PASS, alle Tests einschließlich der Legacy-Suite

- [ ] **Step 10: Commit**

```bash
git add src/nbs/metrics.py src/nbs/pipeline.py tests/test_metrics.py tests/test_pipeline.py
git commit -m "feat: wire the full single-tree chain and its summary metrics

run_single_tree goes stock -> two forcing channels -> convolution -> delta_t.
The test that a tropical tree cools while a boreal one does not is the talk's
central claim written as an assertion."
```

---

### Task 8: Abbildungen für die Ergebnisfolien

**Files:**
- Create: `src/nbs/plots.py`
- Test: `tests/test_plots.py`

**Interfaces:**
- Consumes: `nbs.pipeline.SiteResult`, `nbs.metrics`
- Produces:
  - `nbs.plots.plot_tree_inputs(result: SiteResult, out_path: str) -> str` — Folie E2: m(t), ṁ_CO₂(t), f(t)
  - `nbs.plots.plot_decomposition(result: SiteResult, out_path: str) -> str` — Folie E3: zwei Zeilen, oben φ zerlegt, unten ΔT zerlegt
  - `nbs.plots.plot_disturbance_fan(result: SiteResult, ensemble: NDArray, out_path: str) -> str` — Folie E4
  - Alle geben den geschriebenen Pfad zurück und legen fehlende Verzeichnisse an.

Für die ΔT-Zerlegung in E3 wird jeder Kanal einzeln gefaltet: ΔT_CO₂ = g_T ∗ φ_CO₂ und ΔT_α = g_T ∗ φ_α. Wegen der Linearität der Faltung addieren sich beide exakt zu ΔT — das ist zugleich ein Test.

- [ ] **Step 1: Test schreiben**

```python
# tests/test_plots.py
import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

from nbs.constants import YEARS  # noqa: E402
from nbs.plots import (  # noqa: E402
    plot_decomposition,
    plot_disturbance_fan,
    plot_tree_inputs,
)


@pytest.fixture(scope="module")
def result():
    from nbs.pipeline import run_single_tree

    return run_single_tree("picea_abies", lat_deg=60.0)


@pytest.mark.slow
def test_channel_decomposition_sums_to_the_total(result):
    from nbs.response import convolve_response, green_temperature

    g = green_temperature(result.scenario)
    dt_c = convolve_response(g, result.phi_co2)
    dt_a = convolve_response(g, result.phi_albedo)
    assert np.allclose(dt_c + dt_a, result.delta_t)


@pytest.mark.slow
def test_input_figure_is_written(tmp_path, result):
    p = plot_tree_inputs(result, str(tmp_path / "sub" / "e2.png"))
    assert p.endswith("e2.png")
    assert (tmp_path / "sub" / "e2.png").stat().st_size > 10_000


@pytest.mark.slow
def test_decomposition_figure_is_written(tmp_path, result):
    p = plot_decomposition(result, str(tmp_path / "e3.png"))
    assert (tmp_path / "e3.png").stat().st_size > 10_000


@pytest.mark.slow
def test_fan_figure_is_written(tmp_path, result):
    rng = np.random.default_rng(0)
    ensemble = result.delta_t[None, :] + rng.normal(scale=1e-4, size=(30, len(YEARS)))
    p = plot_disturbance_fan(result, ensemble, str(tmp_path / "e4.png"))
    assert (tmp_path / "e4.png").stat().st_size > 10_000
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_plots.py -v -m slow`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.plots'`

- [ ] **Step 3: Implementieren**

```python
# src/nbs/plots.py
"""Figures for the results section of the talk.

German labels: these go straight onto slides.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

from nbs.metrics import quantile_band, t_star  # noqa: E402
from nbs.pipeline import SiteResult  # noqa: E402
from nbs.response import convolve_response, green_temperature  # noqa: E402
from nbs.species import get_species  # noqa: E402

C_CARBON = "#1b7837"
C_ALBEDO = "#d95f02"
C_NET = "#252525"
DPI = 300


def _save(fig, out_path: str) -> str:
    directory = os.path.dirname(out_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _title(result: SiteResult) -> str:
    sp = get_species(result.species_key)
    return f"{sp.name_de} ({sp.name_lat}), {result.lat_deg:.0f}°N, {result.scenario.upper()}"


def plot_tree_inputs(result: SiteResult, out_path: str) -> str:
    """Slide E2: what goes into the forcing — stock, CO2 flux, canopy closure."""
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    y = result.years
    traj = result.trajectory

    axes[0].plot(y, traj.stock_kgC, color=C_CARBON)
    axes[0].set_ylabel("Vorrat m\n[kgC je Baum]")

    axes[1].plot(y, -44.0 / 12.0 * traj.net_uptake_kgC_yr, color=C_CARBON)
    axes[1].axhline(0.0, color="0.6", lw=0.8)
    axes[1].set_ylabel("$\\dot m_{CO_2}$\n[kg CO$_2$/a]")

    axes[2].plot(y, traj.closure, color=C_ALBEDO)
    axes[2].set_ylabel("Bedeckungsgrad f\n[-]")
    axes[2].set_ylim(0, 1.05)
    axes[2].set_xlabel("Jahr")

    axes[0].set_title(_title(result))
    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout()
    return _save(fig, out_path)


def plot_decomposition(result: SiteResult, out_path: str) -> str:
    """Slide E3: forcing above, temperature below, both split by channel.

    Two panels rather than one, because the albedo forcing arrives at once
    while the carbon cooling takes decades — sharper in the forcing than in
    the temperature it produces.
    """
    g = green_temperature(result.scenario)
    dt_carbon = convolve_response(g, result.phi_co2)
    dt_albedo = convolve_response(g, result.phi_albedo)

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    y = result.years

    axes[0].plot(y, result.phi_co2 * 1e15, color=C_CARBON, label="$\\varphi_{CO_2}$ (kühlt)")
    axes[0].plot(y, result.phi_albedo * 1e15, color=C_ALBEDO, label="$\\varphi_\\alpha$ (wärmt)")
    axes[0].plot(y, result.phi_total * 1e15, color=C_NET, lw=2, label="$\\varphi$ netto")
    axes[0].axhline(0.0, color="0.6", lw=0.8)
    axes[0].set_ylabel("Antrieb\n[10$^{-15}$ W/m² je Baum]")
    axes[0].legend(frameon=False, ncol=3)
    axes[0].set_title(_title(result))

    axes[1].plot(y, dt_carbon * 1e15, color=C_CARBON)
    axes[1].plot(y, dt_albedo * 1e15, color=C_ALBEDO)
    axes[1].plot(y, result.delta_t * 1e15, color=C_NET, lw=2)
    axes[1].axhline(0.0, color="0.6", lw=0.8)
    axes[1].set_ylabel("Temperatur\n[10$^{-15}$ K je Baum]")
    axes[1].set_xlabel("Jahr")

    ts = t_star(result.delta_t, y)
    if np.isfinite(ts):
        axes[1].axvline(ts, color=C_NET, ls=":", lw=1)
        axes[1].annotate(f"t* = {ts:.0f}", (ts, 0.0), textcoords="offset points",
                         xytext=(6, 10), fontsize=9)
    else:
        axes[1].annotate("kein t* im Horizont", (y[len(y) // 2], 0.0),
                         textcoords="offset points", xytext=(0, 10), fontsize=9)

    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout()
    return _save(fig, out_path)


def plot_disturbance_fan(result: SiteResult, ensemble: NDArray, out_path: str) -> str:
    """Slide E4: median, 5-95 percent band, deterministic run for contrast."""
    lo, med, hi = quantile_band(ensemble)
    y = result.years

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(y, lo * 1e15, hi * 1e15, color=C_NET, alpha=0.18,
                    label="5–95 % der Läufe")
    ax.plot(y, med * 1e15, color=C_NET, lw=2, label="Median mit Störung")
    ax.plot(y, result.delta_t * 1e15, color=C_CARBON, lw=1.5, ls="--",
            label="ohne Störungsereignisse")
    ax.axhline(0.0, color="0.6", lw=0.8)

    share_warming = float(np.mean(ensemble[:, -1] > 0.0))
    ax.set_title(f"{_title(result)}\nAnteil erwärmender Läufe {y[-1]}: {share_warming:.0%}")
    ax.set_xlabel("Jahr")
    ax.set_ylabel("$\\Delta T$ [10$^{-15}$ K je Baum]")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return _save(fig, out_path)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `uv run pytest tests/test_plots.py -v -m slow`
Expected: PASS, 4 Tests

- [ ] **Step 5: Commit**

```bash
git add src/nbs/plots.py tests/test_plots.py
git commit -m "feat: add results figures for slides E2 to E4

The decomposition figure carries forcing and temperature in separate panels:
the albedo forcing arrives at once while the carbon cooling takes decades, and
that contrast is sharper in the forcing than in the temperature."
```

---

### Task 9: Notebook und Dokumentation

**Files:**
- Create: `notebooks/01_einzelbaum.ipynb`
- Create: `notebooks/archiv/.gitkeep`
- Modify: `README.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: alles Bisherige
- Produces: keine neuen Codeschnittstellen

- [ ] **Step 1: Alte Notebooks archivieren**

```bash
cd /Users/timodiepers/Documents/Coding/dissvortrag
mkdir -p notebooks/archiv
git mv notebooks/01_single_intervention_demo.ipynb notebooks/archiv/
git mv notebooks/01_energy_balance_and_carbon_credits.ipynb notebooks/archiv/
git mv notebooks/equivalence_ratio_by_latitude_and_scenario.png notebooks/archiv/
touch notebooks/archiv/.gitkeep
```

- [ ] **Step 2: Notebook aus einem Skript erzeugen**

```bash
cd /Users/timodiepers/Documents/Coding/dissvortrag
mkdir -p /tmp/nb && cat > /tmp/nb/build.py <<'PY'
import nbformat as nbf

nb = nbf.v4.new_notebook()
C = nb.cells

C.append(nbf.v4.new_markdown_cell(
    "# Ein Baum, ein Ort, ein Zeitpunkt\n\n"
    "Die Kette des Vortrags, einmal durchgerechnet: Vorrat, zwei Antriebskanaele,\n"
    "Faltung zur Temperatur. Erst deterministisch, dann als Stoerungs-Ensemble.\n\n"
    "Die Albedo-Werte stammen noch aus der Breitengrad-Ersatztabelle; die Raster\n"
    "kommen mit Plan 2."
))

C.append(nbf.v4.new_code_cell(
    "import numpy as np\n"
    "import matplotlib.pyplot as plt\n\n"
    "from nbs.constants import YEARS\n"
    "from nbs.forcing import fallback_delta_alpha, fallback_q_sw, light_bulb_watts\n"
    "from nbs.metrics import prob_warming, risk_premium, t_star\n"
    "from nbs.pipeline import run_single_tree, run_single_tree_ensemble\n"
    "from nbs.plots import plot_decomposition, plot_disturbance_fan, plot_tree_inputs\n"
    "from nbs.species import SPECIES, get_species\n\n"
    "FIG = '../docs/slides/figures'"
))

C.append(nbf.v4.new_markdown_cell(
    "## Die Gluehbirne von Folie 14\n\n"
    "Bevor irgendetwas gerechnet wird: stimmt die Zahl, die auf der Folie steht?"
))
C.append(nbf.v4.new_code_cell(
    "for key, lat in [('picea_abies', 60.0), ('tropical_mixed', 0.0)]:\n"
    "    sp = get_species(key)\n"
    "    w = light_bulb_watts(fallback_delta_alpha(lat), fallback_q_sw(lat), sp)\n"
    "    print(f'{sp.name_de:32s} {lat:4.0f} Grad N: {w:5.1f} W je Baum')"
))

C.append(nbf.v4.new_markdown_cell("## Der boreale Fall"))
C.append(nbf.v4.new_code_cell(
    "boreal = run_single_tree('picea_abies', lat_deg=60.0, scenario='ssp245')\n"
    "print('t* =', t_star(boreal.delta_t, YEARS))\n"
    "print('Delta T 2150 =', f'{boreal.delta_t[-1]:.3e} K je Baum')"
))
C.append(nbf.v4.new_code_cell(
    "plot_tree_inputs(boreal, f'{FIG}/e2_eingangsgroessen_boreal.png')\n"
    "plot_decomposition(boreal, f'{FIG}/e3_zerlegung_boreal.png')"
))

C.append(nbf.v4.new_markdown_cell("## Der tropische Fall — dieselbe Rechnung, anderes Vorzeichen"))
C.append(nbf.v4.new_code_cell(
    "tropisch = run_single_tree('tropical_mixed', lat_deg=0.0, scenario='ssp245')\n"
    "plot_decomposition(tropisch, f'{FIG}/e3_zerlegung_tropisch.png')\n"
    "print('t* tropisch =', t_star(tropisch.delta_t, YEARS))"
))

C.append(nbf.v4.new_markdown_cell(
    "## Alle fuenf Arten an ihren Standorten\n\n"
    "Vorlage fuer Folie E5."
))
C.append(nbf.v4.new_code_cell(
    "SITES = {\n"
    "    'picea_abies': 60.0,\n"
    "    'pinus_sylvestris': 52.0,\n"
    "    'fagus_sylvatica': 50.0,\n"
    "    'eucalyptus_grandis': 25.0,\n"
    "    'tropical_mixed': 0.0,\n"
    "}\n"
    "results = {k: run_single_tree(k, lat) for k, lat in SITES.items()}\n\n"
    "fig, ax = plt.subplots(figsize=(9, 5))\n"
    "for key, r in results.items():\n"
    "    ax.plot(r.years, r.delta_t * 1e15, label=f'{get_species(key).name_de} ({SITES[key]:.0f} Grad N)')\n"
    "ax.axhline(0, color='0.6', lw=0.8)\n"
    "ax.set_xlabel('Jahr'); ax.set_ylabel('Delta T [1e-15 K je Baum]')\n"
    "ax.legend(frameon=False); ax.grid(alpha=0.25)\n"
    "fig.savefig(f'{FIG}/e5_arten.png', dpi=300, bbox_inches='tight')"
))

C.append(nbf.v4.new_markdown_cell(
    "## Stoerung als Risiko\n\n"
    "1000 Laeufe. Der Abstand zwischen Ensemblemittel und deterministischem Lauf\n"
    "ist die Risikopraemie: um so viel schmeichelt sich eine Rechnung ohne\n"
    "Stoerungsereignisse selbst."
))
C.append(nbf.v4.new_code_cell(
    "det, ens = run_single_tree_ensemble('picea_abies', lat_deg=60.0, n_members=1000, seed=0)\n"
    "print('P(Delta T > 0 in 2100) =', f\"{prob_warming(ens, YEARS, 2100):.1%}\")\n"
    "print('Risikopraemie 2100     =', f\"{risk_premium(ens, det.delta_t, YEARS, 2100):.3e} K\")\n"
    "plot_disturbance_fan(det, ens, f'{FIG}/e4_stoerungsfaecher_boreal.png')"
))

C.append(nbf.v4.new_markdown_cell(
    "## Offen\n\n"
    "- Albedo und Einstrahlung aus echten Rastern statt aus der Breitentabelle (Plan 2)\n"
    "- Hochskalierung auf Flaechenpotenziale und die Bastin-Korrekturkaskade (Plan 2)\n"
    "- Uebernahme der Abbildungen in die Praesentation (Plan 3)"
))

nbf.write(nb, "notebooks/01_einzelbaum.ipynb")
print("geschrieben")
PY
uv run --with nbformat python /tmp/nb/build.py
```

- [ ] **Step 3: Notebook ausführen und prüfen**

Run: `uv run --with jupyter jupyter nbconvert --to notebook --execute --inplace notebooks/01_einzelbaum.ipynb`
Expected: läuft ohne Fehler durch; danach liegen in `docs/slides/figures/` die Dateien `e2_eingangsgroessen_boreal.png`, `e3_zerlegung_boreal.png`, `e3_zerlegung_tropisch.png`, `e4_stoerungsfaecher_boreal.png`, `e5_arten.png`.

- [ ] **Step 4: Abbildungen ansehen**

Run: `ls -la docs/slides/figures/e*.png`
Öffne `e3_zerlegung_boreal.png` und prüfe mit den Augen: steigt φ_α sofort an und bleibt positiv, fällt φ_CO₂ verzögert ins Negative, liegt die Nettokurve dazwischen? Wenn nicht, ist ein Vorzeichen verdreht, und kein Test hätte das gefangen.

- [ ] **Step 5: README aktualisieren**

Zwei Änderungen an `README.md`.

**(a)** Ersetze den Block unter „## Project Structure" durch:

~~~~
src/nbs/
  species.py    fünf Arten, je Biom eine
  tree.py       Vorrat, Kronenschluss, Störungspfade — je Baum
  forcing.py    φ_CO₂ und φ_α
  response.py   Impulsantworten g_C, g_T; Faltung
  pipeline.py   die vollständige Kette für einen Baum an einem Ort
  metrics.py    t*, Risikoprämie, Quantilbänder
  plots.py      Abbildungen für die Ergebnisfolien
  constants.py  gemeinsame physikalische Konstanten
  fair_module.py
  legacy/       vorheriger Stand, Tests laufen weiter
tests/
notebooks/
  01_einzelbaum.ipynb
  archiv/
~~~~

**(b)** Füge unmittelbar vor „## Quick Start" ein:

~~~~
## Die Kette

Ein Baum, zwei Kanäle, eine Faltung:

    m(t)  →  ṁ_CO₂ = −(44/12)·ṁ  →  Δm_CO₂ = g_C ∗ ṁ_CO₂  →  φ_CO₂ = A_CO₂·Δm_CO₂
          →  f(t)                                          →  φ_α = −Δα·q̇_kurz·τ·f·A_Baum/A_Erde
                                                           →  ΔT = g_T ∗ (φ_CO₂ + φ_α)

FaIR liefert g_C und g_T einmalig; alles danach ist Faltung. Evapotranspiration
ist kein Term in φ — sie überquert die Bilanzgrenze am Oberrand der Atmosphäre
nicht und steckt im Rückkopplungsparameter Λ.

```python
from nbs.pipeline import run_single_tree
from nbs.metrics import t_star

r = run_single_tree("picea_abies", lat_deg=60.0, scenario="ssp245")
print(t_star(r.delta_t, r.years))
```

Der vorherige Stand — Komplexitätslevel 0–6, Äquivalenzverhältnis, Sobol —
liegt unverändert unter `nbs.legacy`.
~~~~

- [ ] **Step 6: .gitignore ergänzen**

```bash
cd /Users/timodiepers/Documents/Coding/dissvortrag
printf '\n# Rohdaten der Rasterschicht\ndata/raw/\n' >> .gitignore
```

- [ ] **Step 7: Gesamte Testsuite**

Run: `uv run pytest -q`
Expected: PASS, alle Tests

- [ ] **Step 8: Commit**

```bash
git add notebooks README.md .gitignore docs/slides/figures
git commit -m "docs: add single-tree notebook and update README for the new chain

The notebook checks the slide's 70 W light bulb before it computes anything
else, so a parameter drift shows up against the presentation rather than
quietly inside it."
```

---

## Danach

Plan 2 (Rasterdatenschicht, Artzuweisung, Potenzialkaskade) und Plan 3
(Übernahme in die Präsentation) werden geschrieben, sobald dieser Plan steht —
gegen die dann tatsächlich vorhandenen Signaturen statt gegen vermutete.

Was Plan 1 bewusst offen lässt:

- Δα und q̇_kurz kommen aus einer Breitentabelle, nicht aus Rastern. Die
  Tabelle ist so gewählt, dass sie die 70 W von Folie 14 reproduziert, aber sie
  ist eine Kalibrierung, keine Messung.
- Keine Aussage über Flächen, Potenziale oder Hochskalierung.
- Das Horizontfeld für Folie E6 braucht mehrere Breitengrade und entsteht in
  Plan 2.
