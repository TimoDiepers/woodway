# DAC-Kapitel: Spitze, Tempo, Kosten, vegane Welt – Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kapitel 5 des Vortrags neu rechnen und bauen: DAC mit Ziel „niedrigste Spitze, dann früh zurück auf 1,5 °C“, Tempo-Vergleich, Kosten im Nachgang mit Vergleichsgrößen, und eine vegane Welt (Methan/N₂O weg, Wald auf frei werdenden Flächen), die die Lücke und den DAC-Bedarf verkleinert.

**Architecture:** Alles hängt an einer Lücke `gap = noetig(Very Low) − ΔT_Bäume`. Bäume werden neu 2026 auf einmal gepflanzt (Bonn-Tempo entfällt). Neues Modul `nbs.vegan` liefert zwei ΔT-Pfade (Gase über FaIR auf CMIP7 Very Low, Flächen über die vorhandene Baumkette). `scripts/build_zeitpfade_data.py` setzt alles zusammen und schreibt `deck/chart_data/zeitpfade.json`; die Folien lesen nur diese Datei.

**Tech Stack:** Python 3.13 mit uv, numpy, scipy (`linprog`/HiGHS), FaIR 2 (`nbs.fair_module`), rasterio für die Rasteraufbereitung, pytest; Deck: HTML + echarts (`deck/src`, `deck/build.py`).

**Spec:** `docs/superpowers/specs/2026-10-13-dac-kapitel-vegan-design.md`

**Arbeitsort:** Worktree `/Users/timodiepers/Documents/Coding/dissvortrag-main` (Branch `main`). Alle Pfade unten relativ dazu. Rohdaten (gitignored) liegen in `/Users/timodiepers/Documents/Coding/dissvortrag/data/raw`; im main-Worktree gibt es kein `data/raw` – Task 5 legt einen Symlink an.

## Global Constraints

- Startjahr `nbs.constants.T_START = 2026`, Horizont `T_END = 2100`, Jahre `YEARS = 2026..2100`; nie 2025/2026 fest verdrahten.
- Bezug ist CMIP7 Very Low (`overshoot_series()["noetig_k"]`).
- Bäume und frei werdende Flächen: alles 2026 gepflanzt, kein Bonn-Tempo mehr.
- Vegan: vollständig ab 2026, keine Übergangszeit.
- DAC: Wachstum 20 %/a (`GROWTH = 1.20`), Start 8,8 Mt/a 2030 (`START_2030_GT`), Lebensdauer 20 a (`LIFETIME`), Speicher je Land, η je Land.
- Kosten: Okosun et al. 2026 (`COST_CASES`), reale EUR 2024, unverzinst (`rate=0.0`).
- Vergleich: BIP EU-27 2024 (Eurostat) und explizite fossile Subventionen (IEA) auf der Folie; IMF inkl. impliziter Kosten nur in Notizen.
- Folientexte Deutsch, sachliche Titel (keine Slogans); Takeaway darf auf Überleitungsfolien eine Frage sein.
- Lesbarkeit: Achsen/Legenden ≥ 18 px auf 1600×900.
- Nur Neues animieren; Elemente der Vorfolie an exakt gleicher Position.
- Commits ohne `Co-Authored-By` und ohne „Generated with Claude Code“ (Timos Regel).
- Gestaltung erst als Screenshot zeigen, nach Timos Zustimmung committen (gilt für die Deck-Tasks 10–12).
- Tests: `uv run pytest <pfad> -q`.

## Review Focus

1. **Doppelzählung Agrar-Methan:** Very Low senkt CH₄ selbst (363 → 161 Mt/a 2025→2050). Das Delta darf nie größer sein als der Tierhaltungsanteil am Very-Low-Pfad – Test in Task 5 (`test_delta_never_exceeds_share_of_scenario`).
2. **Überlappung der Flächen:** Frei werdende Flächen dürfen nicht mit Walkers Aufforstungsflächen (R/L+R/H außerhalb der Nutzungsklassen) überlappen – Test in Task 6 (`test_freed_land_disjoint_from_reforestable`).
3. **Lücke schließt sich ganz:** Wenn `gap_vegan` überall ≤ 0 ist, muss die Optimierung einen Null-Pfad mit Status melden statt zu scheitern – Test in Task 8 (`test_min_peak_with_closed_gap_builds_nothing`).
4. **Kosten eines leeren Pfads und Einheiten:** `path_cost` mit Null-Pfad → 0; Einheit Bio. EUR – Test in Task 3.
5. **Wärmende Zellen auf Weiden:** Steppen-/boreale Weiden wärmen über Albedo; nur kühlende Zellen zählen – Test in Task 7 (`test_only_cooling_cells_count`).

---

### Task 1: WIP auf main sichern

Der nicht committete Stand (20 a Lebensdauer, `solve_min_peak`, Kostenfunktionen) ist die Grundlage dieses Plans.

**Files:**
- Modify (nur committen): `src/nbs/dac_optim.py`, `tests/test_dac_optim.py`, `scripts/build_zeitpfade_data.py`, `docs/methods/dac-modell.md`, `deck/src/js/dacfilm.js`, `deck/src/js/deck.js`, `deck/src/slides/05_dac.html`, `deck/src/slides/07_backup.html`, `data/dac/optim.json`, `deck/chart_data/dacfilm.json`, `deck/chart_data/zeitpfade.json`

- [ ] **Step 1: Tests des WIP laufen lassen**

Run: `uv run pytest tests/test_dac_optim.py -q`
Expected: alle PASS. Bei FAIL: stoppen und Timo die Ausgabe zeigen.

- [ ] **Step 2: Commit**

```bash
git add src/nbs/dac_optim.py tests/test_dac_optim.py scripts/build_zeitpfade_data.py docs/methods/dac-modell.md \
  deck/src/js/dacfilm.js deck/src/js/deck.js deck/src/slides/05_dac.html deck/src/slides/07_backup.html \
  data/dac/optim.json deck/chart_data/dacfilm.json deck/chart_data/zeitpfade.json
git commit -m "feat(dac): plants run 20 years, lowest peak first"
```

---

### Task 2: Bäume ab 2026 auf einmal (Bonn-Tempo raus)

**Files:**
- Modify: `src/nbs/tree_paths.py` (Docstring, `BONN_RATE_GHA`, Defaults von `forcing`/`delta_t`)
- Modify: `tests/test_tree_paths.py`

**Interfaces:**
- Produces: `forcing(path, start=T_START, rate_gha=None, release=False)`, `delta_t(path, start=T_START, rate_gha=None, release=False)` – Default ist jetzt „alles im Startjahr“. `schedule(area, start, rate_gha)` bleibt (für Tests mit expliziter Rate). `BONN_RATE_GHA` entfällt.

- [ ] **Step 1: Tests anpassen (failing)**

In `tests/test_tree_paths.py` den Import und die zwei Bonn-Tests ersetzen:

```python
from nbs.tree_paths import delta_t, forcing, schedule


def test_schedule_with_a_rate_spreads_the_area():
    f = schedule(0.39, rate_gha=0.0175)
    assert abs(f.sum() - 1.0) < 1e-12
    assert f[0] == np.float64(0.0175 / 0.39)


def test_default_plants_everything_in_the_start_year():
    assert schedule(0.39, rate_gha=None)[0] == 1.0
    assert np.array_equal(delta_t("kuehlt"), delta_t("kuehlt", rate_gha=None))


def test_planting_everything_in_the_start_year_reproduces_the_area_slide():
    cached = json.loads((ROOT / "deck/chart_data/flaechen_zeitreihe.json").read_text())
    ref = np.array(cached["kuehlt"])[: len(delta_t("kuehlt"))]
    assert np.allclose(delta_t("kuehlt"), ref, rtol=1e-6, atol=1e-9)
```

(`test_planting_at_the_bonn_rate_cools_less_early_than_planting_at_once` löschen.)

- [ ] **Step 2: Run, expect FAIL**

Run: `uv run pytest tests/test_tree_paths.py -q`
Expected: FAIL (`ImportError`/Default noch Bonn).

- [ ] **Step 3: Implementieren**

In `src/nbs/tree_paths.py`:
- Zeile `BONN_RATE_GHA = 0.35 / 20.0 ...` löschen.
- `def schedule(area_gha: float, start: int = T_START, rate_gha: float | None = None) -> NDArray:`
- `def forcing(path: str, start: int = T_START, rate_gha: float | None = None, release: bool = False)`
- `def delta_t(path: str, start: int = T_START, rate_gha: float | None = None, release: bool = False)`
- Modul-Docstring: Absatz „Planting rate: the Bonn Challenge pace …“ ersetzen durch
  `Planting: every path is planted at once in the start year (T_START), a stated simplification; schedule() can still spread a path at a given rate.`
- Erste Zeile des Docstrings: `"""Planting paths over time: three ways to use the reforestable land, all planted in the start year.`

- [ ] **Step 4: Run, expect PASS**

Run: `uv run pytest tests/test_tree_paths.py -q`
Expected: PASS.

- [ ] **Step 5: Weitere Nutzer von BONN_RATE_GHA finden**

Run: `grep -rn "BONN_RATE_GHA\|rate_gha=" src scripts tests`
Expected: keine Treffer außer `schedule`-Tests. Treffer entsprechend anpassen (Argument weglassen).

- [ ] **Step 6: Commit**

```bash
git add src/nbs/tree_paths.py tests/test_tree_paths.py
git commit -m "feat(trees): plant every path at once in 2026, drop the Bonn pace"
```

---

### Task 3: Kosten im Nachgang (`path_cost`) und Vergleichsgrößen

**Files:**
- Modify: `src/nbs/dac_optim.py` (nach `cost_per_gt`)
- Test: `tests/test_dac_optim.py`

**Interfaces:**
- Consumes: `cost_per_gt(rate, c, life) -> NDArray` [Bio. EUR je Gt/a im Jahr y], `COST_CASES`, `YEARS`.
- Produces:
  - `path_cost(w: NDArray, c: dict = COST, rate: float = 0.0) -> dict` mit Schlüsseln `je_jahr_bio` (list[float], Bio. EUR je Jahr, Investition im Baujahr), `spitze_bio_a` (float), `summe_bio` (float), `eur_t` (float, EUR je Tonne brutto).
  - Konstanten `EU27_BIP_BIO_EUR: float`, `FOSSIL_SUBV_BIO_EUR: float`, `VERGLEICH_QUELLEN: dict[str, str]`.

- [ ] **Step 1: Vergleichswerte prüfen**

Per WebSearch die zwei Zahlen mit Quelle bestätigen:
- Eurostat, BIP EU-27 2024 zu jeweiligen Preisen (Datensatz `nama_10_gdp`), in Bio. EUR.
- IEA, Fossil Fuel Subsidies Database, Konsumsubventionen 2023, in Mrd. USD; Umrechnung mit dem EZB-Jahresmittel 2024 USD/EUR (Referenzkurs, z. B. 1,0824).
Die geprüften Werte in Step 3 eintragen (die Zahlen unten sind Startwerte und müssen durch die geprüften ersetzt werden, falls sie abweichen).

- [ ] **Step 2: Failing tests schreiben**

```python
def test_path_cost_of_nothing_is_zero():
    from nbs.dac_optim import path_cost
    r = path_cost(np.zeros(len(YEARS)))
    assert r["summe_bio"] == 0.0 and r["spitze_bio_a"] == 0.0


def test_path_cost_constant_path_matches_cost_per_gt():
    from nbs.dac_optim import COST, cost_per_gt, path_cost
    w = np.ones(len(YEARS))  # 1 Gt/a every year
    r = path_cost(w)
    assert r["summe_bio"] == pytest.approx(float(cost_per_gt(0.0, COST).sum()), rel=1e-9)
    # one Gt/a at the median: a few hundred EUR per tonne
    assert 150 < r["eur_t"] < 600


def test_path_cost_cases_are_ordered():
    from nbs.dac_optim import COST_CASES, path_cost
    w = np.linspace(0, 5, len(YEARS))
    s = {k: path_cost(w, c)["summe_bio"] for k, c in COST_CASES.items()}
    assert s["optimistisch"] < s["median"] < s["pessimistisch"]


def test_comparison_values_have_sources():
    from nbs.dac_optim import EU27_BIP_BIO_EUR, FOSSIL_SUBV_BIO_EUR, VERGLEICH_QUELLEN
    assert 15 < EU27_BIP_BIO_EUR < 21
    assert 0.3 < FOSSIL_SUBV_BIO_EUR < 1.5
    assert set(VERGLEICH_QUELLEN) == {"eu27_bip", "fossil_subv"}
```

Run: `uv run pytest tests/test_dac_optim.py -q -k "path_cost or comparison"`
Expected: FAIL (`ImportError`).

- [ ] **Step 3: Implementieren**

Nach `cost_per_gt` in `src/nbs/dac_optim.py`:

```python
# what the costs are set against on the slide (real EUR 2024): the EU-27 economy and what the world pays today
# in explicit fossil-fuel subsidies (consumption subsidies; the IMF's 7 trillion USD incl. unpaid damages is
# only in the notes)
EU27_BIP_BIO_EUR = 17.9        # Eurostat nama_10_gdp, EU-27 GDP 2024, current prices
FOSSIL_SUBV_BIO_EUR = 0.620 / 1.0824  # IEA fossil-fuel subsidies database, 2023, USD -> EUR at the ECB mean 2024
VERGLEICH_QUELLEN = {"eu27_bip": "Eurostat nama_10_gdp (2024)",
                     "fossil_subv": "IEA Fossil Fuel Subsidies Database (2023), EZB-Jahresmittel 2024"}


def path_cost(w: NDArray, c: dict = COST, rate: float = 0.0) -> dict:
    """Cost of a world DAC path w [Gt/a per year of YEARS] after the fact (not optimised for): investment in the
    years capacity is built (new or rebuilt after LIFETIME), operation, sorbent and energy each year it runs.
    Per year [trillion EUR], highest year, sum 2026-2100 and EUR per tonne removed (gross)."""
    w = np.asarray(w, dtype=float)
    d = (1.0 + rate) ** -(YEARS - YEARS[0]).astype(float)
    build = builds_matrix(N_Y, LIFETIME) @ w
    per_year = (c["capex"] * build + (c["fom"] + c["sorbent"] + c["energy"]) * w) * d * 1e9 / 1e12
    total = float(per_year.sum())
    return {"je_jahr_bio": [float(v) for v in per_year], "spitze_bio_a": float(per_year.max(initial=0.0)),
            "summe_bio": total, "eur_t": total * 1e3 / float(w.sum()) if w.sum() > 0 else 0.0}
```

Hinweis: `builds_matrix(n, life) @ w` liefert die Bauten je Jahr (neu und Ersatz); Summe über Jahre ist identisch zu `(cost_per_gt * w).sum()` (dort über `R^T d` geschrieben). Wenn `test_path_cost_constant_path_matches_cost_per_gt` scheitert, `builds_matrix`-Orientierung prüfen (`R` vs `R.T`) und an `cost_per_gt` angleichen.

- [ ] **Step 4: Run, expect PASS**

Run: `uv run pytest tests/test_dac_optim.py -q -k "path_cost or comparison"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/nbs/dac_optim.py tests/test_dac_optim.py
git commit -m "feat(dac): cost of a path after the fact, EU GDP and fossil subsidies"
```

---

### Task 4: FaIR mit geänderten CH₄/N₂O-Emissionen

**Files:**
- Modify: `src/nbs/fair_module.py` (nach `run_fair_perturbed`)
- Test: `tests/test_fair_module.py`

**Interfaces:**
- Produces: `run_fair_emission_delta(delta: dict[str, NDArray], scenario: str = "cmip7-VL") -> NDArray` – addiert `delta[specie]` (Länge wie `nee` in `run_fair_perturbed`, Studienzeitraum ab `_START_IDX`) auf die Emissionen der Spezies (`"CH4"` in Mt CH₄/a, `"N2O"` in kt N₂O/a), gibt Oberflächentemperatur wie `run_fair_baseline` zurück.

- [ ] **Step 1: Failing test**

```python
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
```

Run: `uv run pytest tests/test_fair_module.py -q -k emission_delta`
Expected: FAIL (`ImportError`).

- [ ] **Step 2: Implementieren**

```python
def run_fair_emission_delta(delta: dict[str, NDArray], scenario: str = "cmip7-VL") -> NDArray:
    """FaIR with changed emissions of some species over the study period (e.g. {"CH4": -x [Mt CH4/a],
    "N2O": -y [kt N2O/a]}), in the units of the scenario's emission file. Surface temperature as run_fair_baseline."""
    f = _create_fair(scenario)
    for specie, d in delta.items():
        vals = f.emissions.sel(specie=specie).values.copy()
        vals[_START_IDX:_END_IDX, 0, 0] += np.asarray(d, dtype=float)
        f.emissions.loc[dict(specie=specie)] = vals
    f.run()
    return _surface_temperature(f, scenario)
```

- [ ] **Step 3: Run, expect PASS**

Run: `uv run pytest tests/test_fair_module.py -q -k emission_delta`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add src/nbs/fair_module.py tests/test_fair_module.py
git commit -m "feat(fair): run with changed emissions of any species"
```

---

### Task 5: Vegane Welt – Emissionsdelta und ΔT der Gase

**Files:**
- Create: `scripts/prepare_vegan_data.py` (FAOSTAT → `data/vegan/faostat_tierhaltung.json`)
- Create: `data/vegan/faostat_tierhaltung.json` (vom Skript erzeugt, eingecheckt), `data/vegan/QUELLE.md`
- Create: `src/nbs/vegan.py`
- Test: `tests/test_vegan.py`

**Interfaces:**
- Consumes: `run_fair_baseline`, `run_fair_emission_delta`, `_START_IDX`, `_END_IDX` (Task 4); CMIP7-Emissionsdatei `data/cmip7/fair-inputs/emissions_1750-2500.csv` (Spalten `"2022.5"` …).
- Produces:
  - `ACKER_NETTO_FREI = 0.19` (Poore & Nemecek 2018: Ackerfläche −19 % bei veganer Ernährung, netto nach Ersatz).
  - `livestock_shares() -> dict[str, float]` – Anteil der Tierhaltung an CH₄ und N₂O des Szenarios im Bezugsjahr (`{"CH4": s, "N2O": s}`).
  - `emission_delta() -> dict[str, NDArray]` – negative Deltas je Jahr in `YEARS` (Mt CH₄/a, kt N₂O/a).
  - `dt_gase() -> NDArray` [K] auf `YEARS`, < 0 = kühler.

- [ ] **Step 1: FAOSTAT-Daten holen und verdichten**

`scripts/prepare_vegan_data.py`:

```python
"""World livestock emissions from FAOSTAT (Emissions Totals, domain GT) for the vegan world.

Download (not in git): https://bulks-faostat.fao.org/production/Emissions_Totals_E_All_Data_(Normalized).zip
into data/raw/faostat/. Output: data/vegan/faostat_tierhaltung.json, world, year JAHR, kt per gas.

    uv run python scripts/prepare_vegan_data.py
"""
import json
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "data/raw/faostat/Emissions_Totals_E_All_Data_(Normalized).zip"
OUT = ROOT / "data/vegan/faostat_tierhaltung.json"
JAHR = 2022
CH4_ITEMS = ("Enteric Fermentation", "Manure Management")
N2O_ITEMS = ("Manure Management", "Manure left on Pastures", "Manure applied to Soils")
N2O_ACKER = ("Synthetic Fertilizers", "Crop Residues")  # scaled by the net cropland that a vegan world frees


def main() -> None:
    with zipfile.ZipFile(ZIP) as z:
        name = next(n for n in z.namelist() if n.endswith(".csv") and "Normalized" in n)
        df = pd.read_csv(z.open(name), encoding="latin-1")
    w = df[(df["Area"] == "World") & (df["Year"] == JAHR) & (df["Source"] == "FAO TIER 1")]
    def kt(items, element):
        sel = w[w["Item"].isin(items) & (w["Element"] == element)]
        missing = set(items) - set(sel["Item"])
        if missing:
            raise KeyError(f"FAOSTAT items missing: {missing}")
        return float(sel["Value"].sum())
    out = {"jahr": JAHR, "quelle": "FAOSTAT Emissions Totals (GT), World, FAO TIER 1",
           "ch4_kt": kt(CH4_ITEMS, "Emissions (CH4)"), "n2o_tier_kt": kt(N2O_ITEMS, "Emissions (N2O)"),
           "n2o_acker_kt": kt(N2O_ACKER, "Emissions (N2O)")}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(out)


if __name__ == "__main__":
    main()
```

Run:
```bash
ln -s /Users/timodiepers/Documents/Coding/dissvortrag/data/raw /Users/timodiepers/Documents/Coding/dissvortrag-main/data/raw
git check-ignore data/raw   # muss den Pfad ausgeben
mkdir -p /Users/timodiepers/Documents/Coding/dissvortrag/data/raw/faostat
curl -L -o "/Users/timodiepers/Documents/Coding/dissvortrag/data/raw/faostat/Emissions_Totals_E_All_Data_(Normalized).zip" \
  "https://bulks-faostat.fao.org/production/Emissions_Totals_E_All_Data_(Normalized).zip"
uv run python scripts/prepare_vegan_data.py
```
Expected: CH₄ der Tierhaltung ≈ 110–130 Mt (also 110 000–130 000 kt), N₂O Tierhaltung ≈ 1–2 Mt. Liegt `ch4_kt` außerhalb 90 000–150 000: Spaltennamen/Quelle (`Source`) prüfen, nicht still weiterrechnen. Fehlt das `Source`-Feld, den Filter entfernen und im Docstring vermerken.

`data/vegan/QUELLE.md`: Quelle, Download-URL, Datum, Filter (World, 2022, FAO TIER 1, Items wie oben), Poore & Nemecek 2018 (doi:10.1126/science.aaq0216) für 19 %.

- [ ] **Step 2: Failing tests**

`tests/test_vegan.py`:

```python
"""Tests for nbs.vegan: the vegan world from 2026."""

import numpy as np
import pytest

from nbs.constants import YEARS


def test_livestock_shares_are_plausible():
    from nbs.vegan import livestock_shares
    s = livestock_shares()
    assert 0.25 < s["CH4"] < 0.40     # livestock: about a third of anthropogenic methane
    assert 0.05 < s["N2O"] < 0.35


def test_delta_never_exceeds_share_of_scenario():
    import pandas as pd
    from nbs.vegan import emission_delta, livestock_shares
    em = pd.read_csv("data/cmip7/fair-inputs/emissions_1750-2500.csv")
    vl = em[(em.scenario == "VL") & (em.variable == "CH4")]
    ch4 = np.array([float(vl[f"{y}.5"].iloc[0]) for y in YEARS])
    d = emission_delta()["CH4"]
    assert d.shape == (len(YEARS),)
    assert np.all(d <= 0)
    assert np.all(-d <= livestock_shares()["CH4"] * ch4 + 1e-9)


def test_vegan_gases_cool_fast():
    from nbs.vegan import dt_gase
    dt = dt_gase()
    assert dt.shape == (len(YEARS),)
    assert dt[24] < -0.05           # 2050: clearly cooler
    assert dt[24] < 0.5 * dt[-1] or dt[24] < -0.1  # most of the effect early (short-lived)
```

Run: `uv run pytest tests/test_vegan.py -q`
Expected: FAIL (`ModuleNotFoundError: nbs.vegan`).

- [ ] **Step 3: Implementieren**

`src/nbs/vegan.py`:

```python
"""The vegan world: everyone eats vegan from T_START on (an upper bound, stated as such).

Two parts, as on the slides:

- gases: methane and nitrous oxide of livestock disappear. Taken as the livestock share of the CMIP7 Very Low
  emissions, so that what Very Low already cuts in agriculture is not counted twice; the share is that of
  FAOSTAT 2022 (world, livestock) in Very Low's 2022 value, held constant (Very Low cuts energy methane faster
  than farm methane, so the true share rises -- constant is the cautious choice). N2O of cropland
  (synthetic fertiliser, crop residues) falls by the net cropland a vegan diet frees (Poore & Nemecek 2018: -19 %).
- land: grazing land and the freed cropland grow forest (see dt_flaeche), the larger and more uncertain part.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from nbs.constants import YEARS

ROOT = Path(__file__).resolve().parents[2]
FAO = ROOT / "data/vegan/faostat_tierhaltung.json"
CMIP7_EM = ROOT / "data/cmip7/fair-inputs/emissions_1750-2500.csv"
SCENARIO = "cmip7-VL"
ACKER_NETTO_FREI = 0.19   # Poore & Nemecek 2018: arable land -19 % in a vegan world, net of the replacement crops


@lru_cache(maxsize=None)
def _vl(specie: str) -> pd.Series:
    em = pd.read_csv(CMIP7_EM)
    row = em[(em.scenario == "VL") & (em.variable == specie)].iloc[0]
    return row


@lru_cache(maxsize=1)
def livestock_shares() -> dict[str, float]:
    """Livestock share of Very Low's CH4 and N2O in FAOSTAT's year."""
    fao = json.loads(FAO.read_text())
    y = f"{fao['jahr']}.5"
    ch4 = fao["ch4_kt"] / 1e3 / float(_vl("CH4")[y])                    # kt -> Mt CH4
    n2o = (fao["n2o_tier_kt"] + ACKER_NETTO_FREI * fao["n2o_acker_kt"]) / float(_vl("N2O")[y])  # kt N2O
    return {"CH4": ch4, "N2O": n2o}


def emission_delta() -> dict[str, NDArray]:
    """Change of emissions per year of YEARS (negative): CH4 [Mt/a], N2O [kt/a]."""
    s = livestock_shares()
    return {sp: -s[sp] * np.array([float(_vl(sp)[f"{y}.5"]) for y in YEARS]) for sp in ("CH4", "N2O")}


@lru_cache(maxsize=1)
def dt_gase() -> NDArray:
    """Temperature change [K] on YEARS from the gases alone, FaIR on Very Low."""
    from nbs.fair_module import _END_IDX, _START_IDX, run_fair_baseline, run_fair_emission_delta

    n = _END_IDX - _START_IDX
    d = {sp: np.pad(v, (0, max(0, n - len(v))))[:n] for sp, v in emission_delta().items()}
    base = run_fair_baseline(SCENARIO)
    out = (run_fair_emission_delta(d, SCENARIO) - base)
    out = np.append(out, out[-1])[: len(YEARS)]
    out.setflags(write=False)
    return out
```

Hinweis zur Zeitachse: `run_fair_perturbed` beginnt bei `_START_IDX` mit dem Jahr `T_START`; `tree_paths.delta_t` hängt den letzten Wert an, weil FaIR ein Jahr kürzer ist. Gleiches Muster hier.

- [ ] **Step 4: Run, expect PASS**

Run: `uv run pytest tests/test_vegan.py -q`
Expected: PASS. Den Wert `dt_gase()[24]` und `dt_gase()[-1]` notieren (für den Bericht in Task 9).

- [ ] **Step 5: Gegenprobe Ivanovich**

Ivanovich et al. 2023 (Nat. Clim. Change 13, 297): Ernährung trägt bis 2100 fast 1 °C, davon ~75 % aus methanreichen Lebensmitteln. Unser `dt_gase` ist kein gleicher Vergleich (wir starten auf Very Low, nicht auf heutigen Emissionen), sollte aber die Größenordnung 0,1–0,3 K treffen. Abweichung in `docs/methods/vegan-modell.md` (Task 12) festhalten.

- [ ] **Step 6: Commit**

```bash
git add scripts/prepare_vegan_data.py data/vegan/faostat_tierhaltung.json data/vegan/QUELLE.md src/nbs/vegan.py tests/test_vegan.py
git commit -m "feat(vegan): methane and nitrous oxide of a vegan world on Very Low"
```

---

### Task 6: Frei werdende Flächen als Raster

Walker et al. 2022 hat genau die Flächen ausgeschlossen, die eine vegane Welt frei macht: `Societal_Constraints_500m.tif` (1 Acker, 2 Wanderfeldbau, 3 Weide, 4 Siedlung). Frei werden: Weide (3) ganz, Acker (1) zu 19 %, jeweils nur auf Pixeln mit Aufforstungschance (NCS 2 = R/L, 5 = R/H). Kohlenstoff: nicht realisiertes Potenzial ohne Nutzungsbeschränkung (`Base_Unr_AGB_BGB_MgCha_500m.tif`).

**Files:**
- Modify: `scripts/prepare_forest_data.py` (neue Funktion `freed_land()`, Ausgabe in eigene Datei)
- Create: `data/vegan/frei_0p5.npz` (vom Skript erzeugt, eingecheckt; klein)
- Create: `src/nbs/vegan.py` – Funktionen `freed_area_m2()`, `freed_carbon_mgc_ha()`
- Test: `tests/test_vegan.py`

**Interfaces:**
- Produces: `freed_area_m2() -> NDArray (360, 720)`, `freed_carbon_mgc_ha() -> NDArray (360, 720)` (Gewinn je ha auf den frei werdenden Pixeln, flächengewichtet).

- [ ] **Step 1: Rohdaten verlinken und laden**

Der Symlink `data/raw` existiert seit Task 5. Ziel: `/Users/timodiepers/Documents/Coding/dissvortrag/data/raw/walker`.
Aus Harvard Dataverse doi:10.7910/DVN/DSDDQK die Dateien `Societal_Constraints_500m.tif` und `Base_Unr_AGB_BGB_MgCha_500m.tif` herunterladen (Dataverse-API: `https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/DSDDQK` liefert die Datei-IDs; Download über `https://dataverse.harvard.edu/api/access/datafile/<id>`). Prüfen: `gdalinfo` bzw. `rasterio` öffnet sie, gleiche Form wie `NCS_Opportunity_Categories_500m.tif`.

- [ ] **Step 2: Failing tests**

An `tests/test_vegan.py` anhängen:

```python
def test_freed_land_is_plausible():
    from nbs.vegan import freed_area_m2
    gha = freed_area_m2().sum() / 1e13
    assert 0.3 < gha < 2.5     # forest-capable grazing land plus 19 % of forest-capable cropland


def test_freed_land_disjoint_from_reforestable():
    from nbs.forest_data import reforestable_area_m2
    from nbs.grid import cell_area_m2
    from nbs.vegan import freed_area_m2
    tot = freed_area_m2() + reforestable_area_m2()
    assert np.all(tot <= cell_area_m2()[:, None] * 1.0001)


def test_freed_carbon_where_freed():
    from nbs.vegan import freed_area_m2, freed_carbon_mgc_ha
    a, c = freed_area_m2(), freed_carbon_mgc_ha()
    assert np.all(c[a > 0] >= 0) and np.median(c[a > 0]) > 10
```

(`cell_area_m2` aus `nbs.grid`: Signatur vor dem Test prüfen; falls es ein (360,)-Vektor ist, wie oben broadcasten, falls (360, 720), `[:, None]` weglassen.)

Run: `uv run pytest tests/test_vegan.py -q -k freed`
Expected: FAIL.

- [ ] **Step 3: Aufbereitung im Skript**

In `scripts/prepare_forest_data.py` neben der vorhandenen Aggregation (Zeilen ~85–130 lesen die NCS-Kategorien in Streifen) eine Funktion nach demselben Muster:

```python
FREED_OUT = ROOT / "data" / "vegan" / "frei_0p5.npz"
ACKER_NETTO_FREI = 0.19  # Poore & Nemecek 2018, as nbs.vegan


def freed_land() -> tuple[np.ndarray, np.ndarray]:
    """Area [m^2] per 0.5-degree cell that a vegan world frees and that could carry forest (NCS R/L or R/H):
    grazing land (Walker's societal constraint 3) in full, cropland (1) at 19 %; and the unconstrained
    unrealised AGB+BGB carbon there [Mg C/ha], area-weighted."""
    area = np.zeros(DST_SHAPE)
    carbon = np.zeros(DST_SHAPE)
    with rasterio.open(RAW / "walker" / "NCS_Opportunity_Categories_500m.tif") as cat_src, \
            rasterio.open(RAW / "walker" / "Societal_Constraints_500m.tif") as soc_src, \
            rasterio.open(RAW / "walker" / "Base_Unr_AGB_BGB_MgCha_500m.tif") as c_src:
        # same strip-wise reprojection as the reforestation block above: per strip, pixel area x weight,
        # summed into the 0.5-degree cells (reuse its helper for pixel -> cell indices)
        ...
    with np.errstate(invalid="ignore", divide="ignore"):
        carbon = np.where(area > 0, carbon / area, 0.0)
    return area, carbon
```

Die Strip-Schleife **wörtlich** aus dem vorhandenen Reforestation-Block übernehmen (dort wird `cat in (2, 5)` mit Pixelfläche in Zellen summiert und `c_src` flächengewichtet). Änderung: Gewicht je Pixel `w = (soc == 3) * 1.0 + (soc == 1) * ACKER_NETTO_FREI`, Bedingung `cat in (2, 5)`; Fläche `+= w * pixel_area`, Kohlenstoff `+= w * pixel_area * c`. Den bestehenden Block dabei in eine Hilfsfunktion `_strip_sum(weight_fn, carbon_src)` ziehen, die beide nutzen (DRY), ohne die Ausgabe von `forest_grid_0p5.npz` zu ändern.

Am Ende von `main()`:

```python
    fa, fc = freed_land()
    FREED_OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(FREED_OUT, freed_area_m2=fa.astype(np.float32), freed_carbon_mgc_ha=fc.astype(np.float32))
    print("frei:", fa.sum() / 1e13, "Gha")
```

Run: `uv run python scripts/prepare_forest_data.py`
Expected: `forest_grid_0p5.npz` unverändert (`git diff --stat data/forest` leer), `frei: … Gha` zwischen 0,3 und 2,5.

- [ ] **Step 4: Lesefunktionen**

In `src/nbs/vegan.py`:

```python
FREI = ROOT / "data/vegan/frei_0p5.npz"


@lru_cache(maxsize=1)
def _frei() -> dict[str, NDArray]:
    with np.load(FREI) as f:
        return {k: f[k].astype(float) for k in f.files}


def freed_area_m2() -> NDArray:
    """(360, 720) area a vegan world frees and that could carry forest [m^2] (Walker's grazing land in full,
    cropland at ACKER_NETTO_FREI, only on reforestation-opportunity pixels)."""
    return _frei()["freed_area_m2"].copy()


def freed_carbon_mgc_ha() -> NDArray:
    """(360, 720) unrealised AGB+BGB carbon on that area [Mg C/ha] (Walker, unconstrained)."""
    return _frei()["freed_carbon_mgc_ha"].copy()
```

- [ ] **Step 5: Run, expect PASS**

Run: `uv run pytest tests/test_vegan.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/prepare_forest_data.py data/vegan/frei_0p5.npz src/nbs/vegan.py tests/test_vegan.py
git commit -m "feat(vegan): land a vegan world frees, from Walker's societal constraints"
```

---

### Task 7: Wald auf frei werdenden Flächen – ΔT

**Files:**
- Modify: `src/nbs/tree_paths.py` (neue Funktion `forcing_cells`)
- Modify: `src/nbs/vegan.py` (`dt_flaeche`, `flaeche_info`)
- Test: `tests/test_tree_paths.py`, `tests/test_vegan.py`

**Interfaces:**
- Consumes: `forest_data.key_grid(all_cells=True)`, `forest_data.growth_by_key()`, `forest_data.TREES_PER_HA`, `aggregate.unit_curves(key, "ssp245")`, `albedo_grid.alpha_q_product(key)`, `map_plots._t_star_batch(traj, YEARS)`, `_trajectory(key, plant_year)`.
- Produces:
  - `tree_paths.forcing_cells(area_m2: NDArray, carbon_mgc_ha: NDArray, start: int = T_START) -> tuple[NDArray, NDArray, float]` – (nee [Gt CO₂/a], Albedo-Forcing [W/m²], gezählte Fläche [Gha]) für beliebige Flächen, alles in `start` gepflanzt, nur kühlende Zellen.
  - `tree_paths.cooling_cells(area_m2: NDArray, carbon_mgc_ha: NDArray) -> NDArray[bool]`
  - `vegan.dt_flaeche() -> NDArray` [K] auf `YEARS`; `vegan.flaeche_info() -> dict` mit `frei_gha`, `kuehlt_gha`.

- [ ] **Step 1: Failing tests**

`tests/test_tree_paths.py`:

```python
def test_forcing_cells_reproduces_the_cooling_path():
    from nbs.forest_data import carbon_gain_mgc_ha, reforestable_area_m2
    from nbs.tree_paths import forcing_cells
    nee, rf, area = forcing_cells(reforestable_area_m2(), carbon_gain_mgc_ha())
    nee_k, rf_k, area_k = forcing("kuehlt")
    assert area == pytest.approx(area_k, rel=0.02)
    assert nee.sum() == pytest.approx(nee_k.sum(), rel=0.02)


def test_only_cooling_cells_count():
    from nbs.forest_data import carbon_gain_mgc_ha, reforestable_area_m2
    from nbs.tree_paths import cooling_cells
    a = reforestable_area_m2()
    cool = cooling_cells(a, carbon_gain_mgc_ha())
    assert cool.sum() < (a > 0).sum()          # some reforestable cells warm
    assert not np.any(cool & (a <= 0))
```

(`import pytest` am Dateikopf ergänzen.)

`tests/test_vegan.py`:

```python
def test_forest_on_freed_land_cools():
    from nbs.vegan import dt_flaeche, flaeche_info
    dt = dt_flaeche()
    assert dt.shape == (len(YEARS),)
    assert dt[-1] < -0.02
    info = flaeche_info()
    assert 0 < info["kuehlt_gha"] <= info["frei_gha"]
```

Run: `uv run pytest tests/test_tree_paths.py tests/test_vegan.py -q -k "cells or freed_land_cools"`
Expected: FAIL.

- [ ] **Step 2: `cooling_cells` und `forcing_cells` implementieren**

In `src/nbs/tree_paths.py`:

```python
def _site_factor(keys: NDArray, carbon_mgc_ha: NDArray) -> NDArray:
    """Carbon of each cell relative to its forest key's median cell (as nbs.site_factor, for any carbon grid)."""
    from nbs.forest_data import growth_by_key

    g = growth_by_key()
    ref = np.array([[g[k]["m_ref_mgc_ha"] if k in g else np.nan for k in row] for row in keys])
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where((carbon_mgc_ha > 0) & (ref > 0), carbon_mgc_ha / ref, 0.0)


def cooling_cells(area_m2: NDArray, carbon_mgc_ha: NDArray) -> NDArray:
    """Cells with area whose typical forest still cools by T_END (finite break-even year), SSP2-4.5."""
    from nbs.aggregate import unit_curves
    from nbs.forest_data import key_grid
    from nbs.map_plots import _t_star_batch

    keys = key_grid(all_cells=True)
    f = _site_factor(keys, carbon_mgc_ha)
    out = np.zeros(area_m2.shape, bool)
    for key in SPECIES:
        m = (keys == key) & (area_m2 > 0) & (f > 0)
        if not m.any():
            continue
        co2, alb = unit_curves(key, "ssp245")
        traj = f[m][:, None] * co2[None, :] + np.nan_to_num(alpha_q_product(key)[m])[:, None] * alb[None, :]
        out[m] = ~np.isinf(_t_star_batch(traj, YEARS))
    return out


def forcing_cells(area_m2: NDArray, carbon_mgc_ha: NDArray, start: int = T_START) -> tuple[NDArray, NDArray, float]:
    """(net CO2 exchange [Gt CO2/a], albedo forcing [W/m^2], counted area [Gha]) of forest on any land, planted
    at once in *start*, left to grow, only on the cells that cool (cooling_cells). Same chain as forcing()."""
    from nbs.forest_data import TREES_PER_HA, key_grid

    keys = key_grid(all_cells=True)
    f = _site_factor(keys, carbon_mgc_ha)
    cool = cooling_cells(area_m2, carbon_mgc_ha)
    n_trees = area_m2 / (1e4 / TREES_PER_HA)
    i0 = start - int(YEARS[0])
    nee, rf, area = np.zeros(N_Y), np.zeros(N_Y), 0.0
    for key in SPECIES:
        m = (keys == key) & cool
        if not m.any():
            continue
        sp = get_species(key)
        up, cl, _ = _trajectory(key, start)
        n_sum = float((n_trees[m] * f[m]).sum())
        np_sum = float((n_trees[m] * np.nan_to_num(alpha_q_product(key)[m])).sum())
        nee[i0:] -= M_CO2_PER_C * up[i0:] * n_sum / 1e12
        rf[i0:] += -TAU_ATM * cl[i0:] * sp.stand_area_m2 / A_EARTH_M2 * np_sum
        area += float(area_m2[m].sum()) / 1e13
    return nee, rf, area
```

Hinweis: `forcing("kuehlt")` nutzt `co2_factor_grid` (= `site_factor_grid`, Bezug `carbon_gain_mgc_ha`) und `masks()["kuehlt"]` (über `_breakeven_year_field` mit `assign_species()`). Der Test in Step 1 prüft, dass die neue Funktion auf denselben Eingaben dasselbe Ergebnis liefert (±2 %). Weicht es mehr ab: Unterschied zwischen `key_grid(all_cells=True)` und `assign_species()` auf den Walker-Zellen prüfen (sollte gleich sein) und `_site_factor` gegen `site_factor_grid(key)` vergleichen.

- [ ] **Step 3: `dt_flaeche` implementieren**

In `src/nbs/vegan.py`:

```python
@lru_cache(maxsize=1)
def _flaeche_forcing():
    from nbs.tree_paths import forcing_cells
    return forcing_cells(freed_area_m2(), freed_carbon_mgc_ha())


@lru_cache(maxsize=1)
def dt_flaeche() -> NDArray:
    """Temperature change [K] on YEARS of forest on the freed land, one FaIR run (SSP2-4.5 background, as the
    trees of chapter 2-3)."""
    from nbs.fair_module import run_fair_baseline, run_fair_perturbed

    nee, rf, _ = _flaeche_forcing()
    base = run_fair_baseline("ssp245")
    d = run_fair_perturbed(nee[: len(base)], rf[: len(base)], "ssp245") - base
    out = np.append(d, d[-1])[: len(YEARS)]
    out.setflags(write=False)
    return out


def flaeche_info() -> dict:
    return {"frei_gha": float(freed_area_m2().sum() / 1e13), "kuehlt_gha": float(_flaeche_forcing()[2])}
```

- [ ] **Step 4: Run, expect PASS**

Run: `uv run pytest tests/test_tree_paths.py tests/test_vegan.py -q`
Expected: PASS. `flaeche_info()` und `dt_flaeche()[-1]` notieren.

- [ ] **Step 5: Commit**

```bash
git add src/nbs/tree_paths.py src/nbs/vegan.py tests/test_tree_paths.py tests/test_vegan.py
git commit -m "feat(vegan): forest on the freed land, same tree chain, cooling cells only"
```

---

### Task 8: Zusammenführen im Build-Skript

**Files:**
- Modify: `scripts/build_zeitpfade_data.py`
- Modify: `src/nbs/dac_optim.py` (`solve_min_peak` bei geschlossener Lücke)
- Test: `tests/test_dac_optim.py`

**Interfaces:**
- Consumes: `solve_min_peak(gap, growth, limit_start, ziel_jahr, danach="frueh")` → dict mit `x`, `kuehlung_k`, `spitze_k`, `ab_jahr`, `kapazitaet_gt`, `netto_gt`, `status`; `path_cost`; `vegan.dt_gase`, `vegan.dt_flaeche`, `vegan.flaeche_info`.
- Produces in `deck/chart_data/zeitpfade.json`:
  - `dac.opt_20|opt_30|opt_50|opt_frei` wie bisher (`kap`, `ab`, `w`, `temp`, `spitze`, `laender`, `x_2100`), jetzt mit `danach="frueh"`.
  - `kosten_pfad`: `{"median": path_cost-dict, "optimistisch": …, "pessimistisch": …, "eu27_bip_bio": float, "fossil_subv_bio": float, "quellen": dict}` für `opt_20`.
  - `vegan`: `{"dt_gase": [mK], "dt_flaeche": [mK], "frei_gha", "kuehlt_gha", "gap": [mK], "opt_20": _case(...), "kosten": {"median": …, "optimistisch": …, "pessimistisch": …}, "ersparnis": {"kap_gt": float, "brutto_gt": float, "kosten_bio": {"median", "optimistisch", "pessimistisch"}}}`.

- [ ] **Step 1: Failing test für geschlossene Lücke**

```python
def test_min_peak_with_closed_gap_builds_nothing():
    from nbs.dac_optim import solve_min_peak
    r = solve_min_peak(np.zeros(len(YEARS)), danach="frueh")
    assert r["spitze_k"] == pytest.approx(0.0, abs=1e-9)
    assert r["kapazitaet_gt"] == pytest.approx(0.0, abs=1e-6)
    assert r["ab_jahr"] == int(YEARS[0])
```

Run: `uv run pytest tests/test_dac_optim.py -q -k closed_gap`
Expected: PASS oder FAIL. Bei FAIL (z. B. `RuntimeError` aus einer Stufe): in `solve_min_peak` direkt nach `gap = np.maximum(...)` einfügen:

```python
    if not gap.any():
        x0 = np.zeros((n_c, len(YEARS)))
        return {"jahre": YEARS.tolist(), "laender": countries, "x": x0.tolist(), "eta": eta.tolist(),
                "kuehlung_k": [0.0] * len(YEARS), "spitze_k": 0.0, "status": "keine_luecke",
                "ab_jahr": int(YEARS[0]), "kapazitaet_gt": 0.0, "netto_gt": 0.0}
```
(`n_c` aus `eta.shape` vorher bestimmen.) Erneut laufen lassen → PASS.

- [ ] **Step 2: Build-Skript umstellen**

In `scripts/build_zeitpfade_data.py`:

1. Modul-Docstring: Bonn-Satz entfernen („planted at once in 2026“), Kapitel-4-Absatz auf „lowest peak, then back to 1.5 °C as early as possible“, plus Absatz „costs after the fact; the vegan world“.
2. Import ergänzen: `from nbs.dac_optim import COST_CASES, EU27_BIP_BIO_EUR, FOSSIL_SUBV_BIO_EUR, VERGLEICH_QUELLEN, path_cost, solve, solve_cost, solve_min_peak, solve_naive` und `from nbs import vegan`.
3. Im `dac`-Block jeden `solve_min_peak(gap, ...)` mit `danach="frueh"` aufrufen:

```python
    frueh = dict(danach="frueh")
    dac = {"opt_20": _case(solve_min_peak(gap, **frueh)),
           "opt_30": _case(solve_min_peak(gap, growth=1.3, **frueh)), "opt_50": _case(solve_min_peak(gap, growth=1.5, **frueh)),
           "opt_frei": _case(solve_min_peak(gap, growth=1e6, limit_start=False, **frueh)),
```
   (übrige Schlüssel des Blocks unverändert lassen.)
4. Nach dem `dac`-Block:

```python
    # costs of the main path after the fact (not optimised for), against the EU-27 economy and fossil subsidies
    w20 = np.array(dac["opt_20"]["w"])
    def _rk(d):
        return {k: (round(v, 4) if isinstance(v, float) else [round(x, 4) for x in v]) for k, v in d.items()}
    kosten_pfad = {k: _rk(path_cost(w20, c)) for k, c in COST_CASES.items()}
    kosten_pfad.update(eu27_bip_bio=EU27_BIP_BIO_EUR, fossil_subv_bio=round(FOSSIL_SUBV_BIO_EUR, 3), quellen=VERGLEICH_QUELLEN)
    print("kosten", {k: kosten_pfad[k]["summe_bio"] for k in COST_CASES})
    # the vegan world from 2026: gases and forest on the freed land lower the gap, then DAC again
    dg, df = vegan.dt_gase(), vegan.dt_flaeche()
    gap_v = gap + dg + df
    v20 = solve_min_peak(gap_v, **frueh)
    vcase = _case(v20)
    wv = np.array(vcase["w"])
    vk = {k: _rk(path_cost(wv, c)) for k, c in COST_CASES.items()}
    veg = {"dt_gase": _mk(dg), "dt_flaeche": _mk(df), **{k: round(v, 3) for k, v in vegan.flaeche_info().items()},
           "gap": _mk(np.maximum(gap_v, 0.0)), "opt_20": vcase, "kosten": vk,
           "ersparnis": {"kap_gt": round(dac["opt_20"]["kap"] - vcase["kap"], 2),
                         "brutto_gt": round(float(w20.sum() - wv.sum()), 1),
                         "kosten_bio": {k: round(kosten_pfad[k]["summe_bio"] - vk[k]["summe_bio"], 2) for k in COST_CASES}}}
    print("vegan", veg["ersparnis"], vegan.flaeche_info())
```
5. In das ausgegebene JSON-Dict `"kosten_pfad": kosten_pfad, "vegan": veg` aufnehmen.
6. Die alten `cases`-Fälle (`g20`, `g30`, … mit Default `danach="ziel"`) bleiben für die Backup-Folie unverändert.

- [ ] **Step 3: Schnelltest des Skripts ohne Volllauf**

Run: `uv run python -c "import scripts.build_zeitpfade_data"` (oder `python -c "import ast; ast.parse(open('scripts/build_zeitpfade_data.py').read())"`)
Expected: kein Syntaxfehler.

- [ ] **Step 4: Tests**

Run: `uv run pytest tests/test_dac_optim.py tests/test_vegan.py tests/test_tree_paths.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_zeitpfade_data.py src/nbs/dac_optim.py tests/test_dac_optim.py
git commit -m "feat(zeitpfade): lowest peak then early return, costs, vegan world"
```

---

### Task 9: Volllauf und Zahlen an Timo

**Files:**
- Modify (erzeugt): `deck/chart_data/zeitpfade.json`, `deck/chart_data/dacfilm.json`, `data/dac/optim.json`

- [ ] **Step 1: Volllauf (~1 h)**

Run (im Hintergrund):
```bash
uv run python scripts/build_zeitpfade_data.py 2>&1 | tee /tmp/zeitpfade.log
uv run python scripts/build_dacfilm_data.py 2>&1 | tee /tmp/dacfilm.log
```
Expected: beide ohne Fehler; Log zeigt `kosten …`, `vegan …`.

- [ ] **Step 2: Zahlen auslesen**

```bash
uv run python - <<'EOF'
import json
z = json.load(open("deck/chart_data/zeitpfade.json"))
d, k, v = z["dac"], z["kosten_pfad"], z["vegan"]
for c in ("opt_20", "opt_30", "opt_50", "opt_frei"):
    print(c, "Spitze", d[c]["spitze"], "mK; zurück", d[c]["ab"], "; Kap", d[c]["kap"], "Gt/a")
for c in ("optimistisch", "median", "pessimistisch"):
    print(c, "Spitze", k[c]["spitze_bio_a"], "Bio/a; Summe", k[c]["summe_bio"], "Bio; EUR/t", k[c]["eur_t"])
print("EU27", k["eu27_bip_bio"], "Subv", k["fossil_subv_bio"])
print("vegan Gase 2050/2100", v["dt_gase"][24], v["dt_gase"][-1], "mK; Fläche", v["dt_flaeche"][24], v["dt_flaeche"][-1],
      "mK; frei/kühlt", v["frei_gha"], v["kuehlt_gha"], "Gha")
print("mit vegan: Spitze", v["opt_20"]["spitze"], "Kap", v["opt_20"]["kap"], "; Ersparnis", v["ersparnis"])
EOF
```

- [ ] **Step 3: Plausibilität**

- Spitze sinkt mit schnellerem Wachstum (`opt_frei` < `opt_20`).
- `ab` bei `opt_20` ≤ 2100.
- `dt_gase` 2050 < 0, Betrag 50–300 mK.
- Ersparnis ≥ 0 in allen drei Kostenfällen.
Abweichungen nicht glätten, sondern Timo nennen ([[wissenschaftlich-ehrlich-bleiben]]).

- [ ] **Step 4: Bericht an Timo – STOPP**

Tabelle der Zahlen aus Step 2 an Timo, mit dem Hinweis auf Annahmen (Anteil konstant, 19 % Acker, alles 2026). Erst nach seinem OK weiter mit Task 10. Daten erst danach committen:

```bash
git add deck/chart_data/zeitpfade.json deck/chart_data/dacfilm.json data/dac/optim.json
git commit -m "data: chapter 5 numbers with trees at once, lowest peak, costs, vegan world"
```

---

### Task 10: Folien – Optimierung, Tempo, Kosten, Zwischenfazit

**Files:**
- Modify: `deck/src/slides/05_dac.html` (Folien „Optimierung von DAC“, „Optimierung: Ergebnis“, „Ausbautempo“; neu „Kosten“, „Zwischenfazit“)
- Modify: `deck/src/js/deck.js` (neuer Chart `EC_KOSTEN`, in `EC_CHARTS` als `kosten` registrieren)

- [ ] **Step 1: Texte der bestehenden Folien**

- „Optimierung von DAC“: Ziel-Zeile ersetzen durch „Ziel: erst die niedrigste Spitze über 1,5 °C, dann so früh wie möglich zurück auf 1,5 °C“. Notizen: Stufen des LP (Spitze minimieren → frühestes Jahr per Bisektion → kleinste Kapazität → kleinste Gesamtmenge).
- „Optimierung: Ergebnis“: `dnum` = `dac.opt_20.kap` („Gt CO₂/a“), Rückkehrjahr `dac.opt_20.ab`, Länderanteile aus `dacfilm.json` (wie bisher, neue Zahlen).
- „Ausbautempo“: Takeaway „Nur schnellerer Ausbau senkt die Spitze: von X K (20 %/a) auf Y K (ohne Grenze)“ mit Zahlen aus Task 9; ein Satz in Notizen und auf der Folie, warum die Spitze zählt (Kipppunkte und Extremereignisse wachsen mit der Spitzenerwärmung; Quelle: Armstrong McKay et al. 2022, Science 377, eabn7950).

- [ ] **Step 2: Kostenfolie (neu, nach „Ausbautempo“)**

```html
<section class="slide dark" data-ch="dac" data-title="Kosten">
  <header class="sh"><h2>Was der DAC-Pfad kostet</h2></header>
  <div class="body">
    <div class="chart" data-ec="kosten" data-label="Jährliche Kosten des DAC-Pfads 2026 bis 2100 mit Spanne, verglichen mit dem BIP der EU-27 und den fossilen Subventionen"></div>
    <div class="foot"><div></div><p class="takeaway" data-step="1" style="--d:900">TEXT_AUS_TASK_9</p></div>
  </div>
  <p class="src">Kosten: Okosun et al. 2026 (Median, Spanne Quartile), reale EUR 2024, unverzinst, im Nachgang auf den optimierten Pfad gerechnet. BIP: Eurostat nama_10_gdp 2024. Subventionen: IEA Fossil Fuel Subsidies Database 2023.</p>
  <aside class="notes" data-n="0">
    <p>Die Kosten sind nicht optimiert, sondern im Nachgang auf den Pfad gerechnet, der die Spitze minimiert.</p>
    <p class="q">Falls Fragen kommen — IMF zählt inklusive nicht bezahlter Umwelt- und Gesundheitsschäden rund 7 Bio. USD (2022); das ist kein Geld, das ausgegeben wird, darum nicht auf der Folie.</p>
  </aside>
</section>
```

`TEXT_AUS_TASK_9` durch einen sachlichen Satz mit den Zahlen ersetzen, z. B. „In der Spitze X Bio. EUR im Jahr – Y-mal die fossilen Subventionen, Z % des EU-BIP“. Die Faktoren aus `kosten_pfad` berechnen, nicht schätzen.

`deck/src/js/deck.js`, vor `const EC_CHARTS`:

```js
/* costs of the DAC path after the fact: median per year with the optimistic-pessimistic band, and two reference
   lines (EU-27 GDP, explicit fossil subsidies), in trillion EUR per year */
const EC_KOSTEN = {
  steps: 1,
  option(k) {
    const D = window.ZEIT, K = D.kosten_pfad, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const lo = K.optimistisch.je_jahr_bio, hi = K.pessimistisch.je_jahr_bio;
    const ref = (v, name, color) => ({ silent: true, symbol: 'none', lineStyle: { color, width: 2.4, type: [8, 6] },
      label: { show: true, position: 'insideEndTop', color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, formatter: name },
      data: [{ yAxis: v }] });
    const series = [
      { id: 'lo', type: 'line', stack: 'band', data: P(lo), showSymbol: false, lineStyle: { opacity: 0 }, silent: true },
      { id: 'band', type: 'line', stack: 'band', data: P(hi.map((v, i) => v - lo[i])), showSymbol: false,
        lineStyle: { opacity: 0 }, areaStyle: { color: '#ff5a4f', opacity: .22 }, silent: true },
      { id: 'med', name: 'DAC (Median)', type: 'line', data: P(K.median.je_jahr_bio), showSymbol: false, z: 5,
        lineStyle: { color: '#ff5a4f', width: 3.4 }, itemStyle: { color: '#ff5a4f' }, animationDuration: 1600,
        markLine: k >= 1 ? ref(K.fossil_subv_bio, `fossile Subventionen ${ecNum(K.fossil_subv_bio, 1)} Bio. €/a`, '#f0b04a') : undefined }];
    return {
      title: { text: 'Kosten [Bio. € pro Jahr]', left: 70, top: 0, textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
      grid: { left: 70, right: 24, top: 64, bottom: 40 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, formatter: v => ecNum(v, 1) }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  }
};
```

In `EC_CHARTS` `kosten: EC_KOSTEN` ergänzen. Das EU-BIP (~18 Bio. €) liegt wahrscheinlich weit über der Kurve: dann nicht als Linie, sondern als Zahl im Takeaway („… entspricht Z % des EU-BIP“) – nach den Zahlen aus Task 9 entscheiden und Timo im Screenshot beide Varianten zeigen, falls unklar.

- [ ] **Step 3: Zwischenfazit (neu, nach „Kosten“)**

```html
<section class="slide dark" data-ch="dac" data-title="Zwischenfazit Tempo">
  <header class="sh"><h2>Die Spitze hängt am Tempo</h2></header>
  <div class="body">
    <div class="chart" data-ec="dactempot" data-label="Erwärmung über 1,5 °C bei verschiedenen Ausbautempi"></div>
    <div class="foot"><div></div><p class="takeaway" style="--d:600">Weder Ort noch Menge senken die Spitze nennenswert – nur wie schnell entnommen wird.</p></div>
  </div>
</section>
```
(Takeaway-Text an die Zahlen aus Task 9 anpassen; wenn die Folie dieselbe Grafik wie „Ausbautempo“ zeigt, an exakt gleicher Position, ohne neue Animation – [[animation-nur-neues]].)

- [ ] **Step 4: Bauen, Screenshot, Timo zeigen – STOPP**

```bash
uv run python deck/build.py
```
Screenshots der Folien „Optimierung von DAC“, „Ausbautempo“, „Kosten“, „Zwischenfazit Tempo“ (headless Chrome auf `deck/dist/index.html#N`; bei leeren Charts erneut versuchen – Ladereihenfolge von echarts ist flaky). Timo zeigen, erst nach OK committen:

```bash
git add deck/src/slides/05_dac.html deck/src/js/deck.js
git commit -m "feat(deck): DAC optimisation, pace, costs and the pace takeaway"
```

---

### Task 11: Folien – vegane Welt

**Files:**
- Modify: `deck/src/slides/05_dac.html` (fünf neue Folien vor der Finale-Folie „Auf dem Holzweg? Nein.“, Finale-Text)
- Modify: `deck/src/js/deck.js` (`EC_VEGAN`, `EC_VEGAN_BAEUME`, `EC_VEGAN_DAC`, registriert als `vegan`, `veganbaeume`, `vegandac`)

- [ ] **Step 1: Überleitung**

```html
<section class="slide dark" data-ch="dac" data-title="Was geht sofort?">
  <header class="sh"><h2>Was ließe sich sofort tun?</h2></header>
  <div class="body">
    <p class="lead rise">Eine Maßnahme ohne technische Hürde und ohne direkte Kosten, die schnell kühlt: Die ganze Welt ernährt sich ab 2026 vegan.</p>
    <p class="lead rise" style="--d:300">Methan aus der Tierhaltung wirkt stark, aber kurz – fällt es weg, kühlt es innerhalb von Jahrzehnten.</p>
    <div class="foot"><div></div><p class="takeaway" style="--d:700">Wie viel bringt das – und wie viel DAC spart es?</p></div>
  </div>
</section>
```

- [ ] **Step 2: Kühlung der veganen Welt**

Chart `vegan`: zwei gestapelte Flächen über die Zeit, `-dt_gase` („Methan und Lachgas“) und `-dt_flaeche` („Wald auf frei werdenden Flächen“, schraffiert/heller, Legendenzusatz „unsicherer“), Einheit K, y aus mK wie `kOf`.

```js
/* the vegan world: cooling from the gases and from forest on the freed land, stacked (data in mK, read in K) */
const EC_VEGAN = {
  steps: 1,
  option(k) {
    const D = window.ZEIT, V = D.vegan, P = ys => D.jahre.map((y, i) => [y, -ys[i]]);
    const A = (id, ys, color, name, op) => ({ id, name, type: 'line', stack: 'v', data: P(ys), showSymbol: false,
      lineStyle: { color, width: 2.4 }, areaStyle: { color, opacity: op }, itemStyle: { color }, animationDuration: 1600 });
    const series = [A('g', V.dt_gase, '#7fd0e0', 'Methan und Lachgas', .55)];
    if (k >= 1) series.push(A('f', V.dt_flaeche, '#7fbf8c', 'Wald auf frei werdenden Flächen (unsicherer)', .3));
    return {
      title: { text: 'Kühlung der Erde [K]', left: 70, top: 0, textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
      grid: { left: 70, right: 24, top: 64, bottom: 40 },
      legend: { right: 24, top: 60, orient: 'vertical', textStyle: { color: '#d6dbd6', fontFamily: EC.font, fontSize: 19 } },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, formatter: kOf }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  }
};
```

Folie „Kühlung der veganen Welt“ mit `data-ec="vegan"`, Takeaway mit Werten 2050/2100 aus Task 9; Quelle: FAOSTAT 2022, Walker et al. 2022 (Societal Constraints), Poore & Nemecek 2018, FaIR auf CMIP7 Very Low. Fußnote ausdrücklich: „Wald auf frei werdenden Flächen: größerer, aber unsicherer Teil (Radrapu 2025; Leip et al. 2019); alles ab 2026, Grenzfall.“

- [ ] **Step 3: Vegan plus Bäume**

Chart `veganbaeume`: wie `EC_DACTEMP` (`ecDacSmall`) mit Linien „nur Bäume“ (`D.baeume_rest`, gestrichelt) und „Bäume + vegan“ (`D.vegan.gap`, Fläche). Folie „Vegan plus Bäume“: Takeaway nennt die neue Spitze (max von `vegan.gap`) gegen die alte.

```js
const EC_VEGAN_BAEUME = ecDacSmall('Erwärmung über 1,5 °C [K]', 400, kOf, D => [
  ['b', D.baeume_rest, '#7fbf8c', 'nur Bäume', [8, 6]], ['v', D.vegan.gap, '#7fd0e0', '+ vegan', null, true]]);
```

- [ ] **Step 4: Weniger DAC und gesparte Kosten**

Chart `vegandac`: Weltkapazität `D.dac.opt_20.w` („ohne vegan“) gegen `D.vegan.opt_20.w` („mit vegan“):

```js
const EC_VEGAN_DAC = ecDacSmall('DAC-Kapazität weltweit [Gt CO₂/a]', 20, v => String(v), D => [
  ['o', D.dac.opt_20.w, '#ff5a4f', 'ohne vegan'], ['m', D.vegan.opt_20.w, '#7fd0e0', 'mit vegan', null, true]]);
```

Folie „Weniger DAC“ (`data-ec="vegandac"`): Takeaway „X Gt/a weniger Kapazität, Y Gt weniger Entnahme bis 2100“ aus `vegan.ersparnis`.
Folie „Gesparte Kosten“: drei Zahlen groß (`.col h4 .big-n` wie in vorhandenen Spaltenfolien) – Ersparnis Median, Spanne optimistisch–pessimistisch in Bio. EUR bis 2100, dazu „entspricht N Jahren fossiler Subventionen“ (berechnet: Ersparnis / `fossil_subv_bio`).

In `EC_CHARTS`: `vegan: EC_VEGAN, veganbaeume: EC_VEGAN_BAEUME, vegandac: EC_VEGAN_DAC`.

- [ ] **Step 5: Finale-Folie**

Text der Finale „Auf dem Holzweg? Nein.“ um einen Satz ergänzen: „Tempo ist der Hebel: Was sofort wirkt – wie weniger Methan –, senkt die Spitze und spart DAC.“ Genauen Wortlaut mit Timo im Screenshot abstimmen.

- [ ] **Step 6: Bauen, Screenshot, Timo zeigen – STOPP**

`uv run python deck/build.py`, Screenshots der fünf neuen Folien und der Finale, Timo zeigen. Nach OK:

```bash
git add deck/src/slides/05_dac.html deck/src/js/deck.js
git commit -m "feat(deck): the vegan world, its cooling, less DAC and the money saved"
```

---

### Task 12: Bonn-Reste entfernen, Methodendoku, Abschluss

**Files:**
- Modify: `deck/src/slides/04_potenzial.html`, `deck/src/slides/05_dac.html`, `deck/src/slides/07_backup.html`, `deck/src/js/deck.js` (Bonn-Erwähnungen)
- Create: `docs/methods/vegan-modell.md`
- Modify: `docs/methods/dac-modell.md`

- [ ] **Step 1: Bonn-Stellen finden und ersetzen**

Run: `grep -n -i "bonn" deck/src/slides/*.html deck/src/js/deck.js src scripts`
Jede Stelle: „mit dem Tempo der Bonn Challenge gepflanzt“ → „alles 2026 gepflanzt (vereinfachende Annahme)“. Zahlen auf den Folien von Kapitel 4 kommen aus `zeitpfade.json` (`D.baeume_rest`, Pfade `alle/kuehlt/forst`) und ändern sich mit Task 9 automatisch; feste Zahlen im Fließtext gegen das JSON prüfen und anpassen.
Expected danach: `grep -i bonn` ohne Treffer in `deck/src` und `src`.

- [ ] **Step 2: Methodendoku**

`docs/methods/vegan-modell.md` (Deutsch, wie `docs/methods/dac-modell.md` gegliedert):
- Frage und Grenzfall (alles 2026).
- Gase: FAOSTAT-Items, Anteil an Very Low 2022, konstant gehalten (warum vorsichtig), 19 % Ackerfläche (Poore & Nemecek 2018), FaIR auf `cmip7-VL`; Zahlen aus Task 9; Gegenprobe Ivanovich 2023.
- Flächen: Walker Societal Constraints (Weide 3 ganz, Acker 1 zu 19 %), nur NCS R/L+R/H, unbeschränktes nicht realisiertes AGB+BGB, gleiche Baumkette, nur kühlende Zellen; frei/kühlt in Gha.
- Was fehlt: Bodenkohlenstoff, Ersatz von Gülle durch Mineraldünger (Leip 2019), Handel, Ernährungsübergang; Spannbreite der Literatur (Eisen & Brown 2022 vs. Radrapu 2025).

`docs/methods/dac-modell.md`: Abschnitt „Ziel“ auf „niedrigste Spitze, dann frühestes Rückkehrjahr“ ändern; Abschnitt „Kosten im Nachgang“ mit `path_cost`, Vergleichswerten und Quellen.

- [ ] **Step 3: Gesamte Tests**

Run: `uv run pytest -q`
Expected: PASS. Fehlschläge in fremden Tests (z. B. `test_slide_numbers.py`, die Folienzahlen prüfen): Ausgabe lesen; wenn sie veraltete Zahlen erwarten, an die neuen JSON-Werte anpassen, nie den Test abschwächen.

- [ ] **Step 4: Deck bauen**

Run: `uv run python deck/build.py`
Expected: `deck/dist/index.html … slides` ohne Warnung über fehlende Marker.

- [ ] **Step 5: Commit**

```bash
git add deck/src docs/methods/vegan-modell.md docs/methods/dac-modell.md tests
git commit -m "docs: vegan world method, DAC target and costs; no Bonn pace left"
```

- [ ] **Step 6: Memory aktualisieren**

`dac-optimierung.md` (neues Ziel, Zahlen aus Task 9, Kostenfolie), `storyline-zeit-kapitel34.md` (Bonn raus erledigt), neue Memory `vegane-welt-modell.md` (Annahmen, Datenquellen, Zahlen) und Zeile in `MEMORY.md`.
