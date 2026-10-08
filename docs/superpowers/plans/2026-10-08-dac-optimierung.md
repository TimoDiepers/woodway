# DAC-Optimierung Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein lineares Programm berechnet, wo (Land), wann (Jahr) und wie viel DAC nötig ist, damit die Temperatur ab dem frühestmöglichen Jahr X dauerhaft bei 1,5 °C bleibt. Zwei neue Folien zeigen Problem und Ergebnis.

**Architecture:**
- Drei kleine Module:
  - `nbs.dac_storage`: Gidden-Speicher je Land und Speichernähe je 0,5°-Zelle.
  - `nbs.dac_optim`: η je Land, FaIR-Kernel als Matrix, Lücke, LP mit HiGHS.
  - `scripts/dac_optim_export.py`: Fälle rechnen, FaIR-Gegenprobe, JSON schreiben.
- Das Deck liest das JSON über einen neuen Patch `patch_dac_optim.py` am Ende der Build-Kette in `scratchpad/new_vergleich.py`. Zwei neue Folien (30, 31) mit ECharts.

**Tech Stack:** Python 3.12 (`.venv`), numpy, scipy (`linprog`, `cKDTree`), rasterio, openpyxl/pandas, FaIR 2.2.4 (vorhanden), ECharts im HTML-Deck.

**Spec:** `docs/superpowers/specs/2026-10-08-dac-optimierung-design.md`

## Global Constraints

- **Zeitachse:** `nbs.constants.YEARS` = 2026…2100, 75 Jahre; `T_START = 2026`, `T_END = 2100`.
- **Speicher:** Gidden et al. 2025, Tabelle S5, „Planetary Limit (Gt CO2)“, Spalte Total je Land; Weltsumme 1 460 Gt.
- **Speichernah:** Sedimentbecken (Rasterwerte 1–4) innerhalb von 100 km um den Zellmittelpunkt.
- **η je Land:** Median der besten 10 % (Quantil 0,9 aufwärts) der Zellen mit `dac_possible() & speicher_maske()`, aus `efficiency_grid(year)` (Variante `"waermepumpe"`, Pfad `"SSP2-NDC"`).
- **Wachstum:**
  - 2030 ≤ 0,0088 Gt/a; 2026–2029 ≤ 0,0088 · (y − 2025)/5 Gt/a.
  - Ab 2031: Summe Jahr t ≤ 1,2 · Summe Jahr t−1.
  - Sensitivität 1,11.
- **Lücke(t):** `need − k` aus `scratchpad/luecke.json` (mK, Very Low minus Bäume auf kühlenden Flächen), in K umgerechnet, untere Grenze 0.
- **Klimawirkung:** FaIR-Kette des Repos (`green_carbon`, `phi_co2_background`, `green_temperature`, `background_co2_ppm`, Szenario `"ssp245"`), kein `dynamic_characterization`.
- **Solver:** `scipy.optimize.linprog(method="highs")`.
- **Sprache:** Folientexte auf Deutsch. Code-Kommentare und Docstrings auf Englisch, wie im Repo.
- **Commits:** ohne Co-Authored-By und ohne „Generated with Claude Code“.
- **Deck-Regeln:**
  - Lesbarkeit im großen Saal: Ticks und Legenden ≥ 19 px auf 1600×900.
  - Elemente der Vorfolie werden nicht neu animiert.
  - Highlight-Klasse `.hl`, Bernstein-Akzent über `data-ch="dac"`.
  - Titel beschreibend, keine Slogans.
- **Verboten:** `export_html_v2.py --backup`. Die pptx bleibt unberührt.

## Review Focus

1. **Länder ohne passende Zelle oder mit Speicher 0** (Schweiz, Island) müssen still herausfallen, nicht mit NaN ins LP gehen. Test in Task 2: `eta_by_country` liefert für sie keinen Eintrag, und `solve` läuft.
2. **Kein machbares X bis 2100** (z. B. bei 11 %/a): `solve` darf nicht abbrechen, sondern muss die beste Annäherung mit `status="annaeherung"` liefern. Test in Task 3.
3. **Ländercodes:** Das Raster nutzt ISO-A2, Gidden ISO-A3. Fehlende Zuordnungen (z. B. Kosovo, Nordzypern, „Total“-Zeilen) dürfen keine Phantom-Länder erzeugen. Test in Task 1.
4. **Nichtlinearität des CO₂-Antriebs:** Der Kernel ist marginal (1 t), das LP skaliert ihn linear auf Hunderte Gt. Die FaIR-Gegenprobe muss die Abweichung messen und ins JSON schreiben. Test in Task 4: Feld vorhanden und endlich.
5. **η ≤ 0 in frühen Jahren** (dreckiger Strom): DAC würde netto wärmen. Das LP darf dort nichts bauen, weil die Kühlung negativ zählt. Ein Land mit η ≤ 0 in Jahr y bekommt die Obergrenze x = 0. Test in Task 3.

---

## File Structure

| Datei | Verantwortung |
|---|---|
| `scripts/fetch_storage_gidden.py` (neu) | Download Zenodo 18343187 nach `data/raw/gidden/`; Ableitung von `data/dac/speicher_gidden.json` und `data/dac/speicher_maske.npz` |
| `src/nbs/dac_storage.py` (neu) | Laden der abgeleiteten Dateien; ISO-A2→A3; Ableitungsfunktionen (vom Script aufgerufen) |
| `src/nbs/dac_optim.py` (neu) | `eta_by_country`, `removal_kernel_matrix`, `gap_series`, `solve` |
| `scripts/dac_optim_export.py` (neu) | Hauptfall, Sensitivitäten, FaIR-Gegenprobe → `data/dac/optim.json` |
| `tests/test_dac_storage.py`, `tests/test_dac_optim.py` (neu) | Tests |
| `docs/methods/dac-modell.md` (ändern) | Abschnitt „8 Optimierung“ |
| `<scratchpad>/patch_dac_optim.py` (neu) | Folien 30/31, Backup-Verschiebungen, Texte 32/33 |
| `<scratchpad>/new_vergleich.py` (ändern) | Patch an die Kette anhängen |

`<scratchpad>` = `/private/tmp/claude-501/-Users-timodiepers-Documents-Coding-dissvortrag/bacac32b-441b-44d3-8d88-405cf362504a/scratchpad`

---

### Task 1: Gidden-Speicherdaten und Speichermaske

**Files:**
- Create: `scripts/fetch_storage_gidden.py`, `src/nbs/dac_storage.py`, `tests/test_dac_storage.py`
- Output: `data/dac/speicher_gidden.json`, `data/dac/speicher_maske.npz` (beide eingecheckt; `data/raw/` ist gitignored)

**Interfaces:**
- Consumes: `nbs.grid.grid_lats/grid_lons/N_LAT/N_LON`, `data/borders/ne_50m_admin_0_countries.geojson` (Properties `ISO_A2_EH`, `ISO_A3_EH`)
- Produces:
  - `storage_by_country(stufe: str = "prudent") -> dict[str, float]`: ISO-A3 → Gt; `stufe ∈ {"prudent", "technisch", "oelgas"}`.
  - `region_by_country() -> dict[str, str]`: ISO-A3 → R5-Name, z. B. `"R5OECD90+EU"`.
  - `storage_mask() -> NDArray[bool]` (360, 720).
  - `iso3_grid() -> NDArray[str]` (360, 720): ISO-A3 je Zelle, `""` ohne Land.
  - Ableitungen `derive_table(xlsx: Path) -> dict` und `derive_mask(tif: Path, radius_km: float = 100.0) -> NDArray[bool]`.

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for nbs.dac_storage (Gidden et al. 2025 storage per country, basin proximity per cell)."""

import numpy as np
import pytest

from nbs.dac_storage import iso3_grid, region_by_country, storage_by_country, storage_mask
from nbs.grid import grid_lats, grid_lons


def _at(field, lat, lon):
    return field[np.argmin(abs(grid_lats() - lat)), np.argmin(abs(grid_lons() - lon))]


def test_world_total_matches_gidden():
    s = storage_by_country("prudent")
    assert sum(s.values()) == pytest.approx(1460, abs=2)


def test_known_countries():
    s = storage_by_country("prudent")
    assert s["DEU"] == pytest.approx(1.3, abs=0.1)
    assert s["RUS"] == pytest.approx(244, abs=1)
    assert s.get("CHE", 0.0) == 0.0


def test_no_phantom_rows():
    s = storage_by_country("prudent")
    assert all(len(k) == 3 and k.isupper() for k in s)
    assert "Total" not in s and "Final Total" not in s


def test_levels_are_ordered():
    p, t = storage_by_country("prudent"), storage_by_country("technisch")
    assert all(t[k] >= p[k] - 1e-9 for k in p)


def test_regions_cover_storage_countries():
    r = region_by_country()
    assert all(k in r for k, v in storage_by_country("prudent").items() if v > 0)


def test_mask_near_basins():
    m = storage_mask()
    assert m.shape == (360, 720) and m.dtype == bool
    assert _at(m, 53.5, 8.0)          # North German Basin / North Sea coast
    assert not _at(m, 46.8, 8.2)      # central Switzerland: no basin within 100 km
    assert 0.2 < m.mean() < 0.8


def test_iso3_grid_matches_known_places():
    g = iso3_grid()
    assert _at(g, 51.0, 10.0) == "DEU"
    assert _at(g, 60.0, 90.0) == "RUS"
    assert _at(g, 0.0, -30.0) == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_dac_storage.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'nbs.dac_storage'`

- [ ] **Step 3: Write `src/nbs/dac_storage.py`**

```python
"""Geological CO2 storage for DAC: how much each country may store, and which cells lie near a basin.

Source: Gidden, M. J. et al. (2025), A prudent planetary limit for geologic carbon storage,
Nature 645, 124-132; data Zenodo 10.5281/zenodo.18343187 (CC-BY 4.0).

* Table S5: per country (ISO3) technical potential, prudent planetary limit and potential in
  basins with oil & gas infrastructure, onshore + offshore, Gt CO2. World prudent limit 1460 Gt.
* Figure 1a raster (0.01 deg): sedimentary basins, values 1-4 (onshore/offshore, assessed or
  not), 15 = outside. A 0.5 deg cell counts as near storage when a basin pixel lies within
  RADIUS_KM of its centre.

Not included: basalt mineralisation (Iceland = 0), injection-rate limits per basin.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from nbs.grid import N_LAT, N_LON, grid_lats, grid_lons

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "data" / "dac" / "speicher_gidden.json"
MASK = ROOT / "data" / "dac" / "speicher_maske.npz"
COUNTRIES = ROOT / "data" / "borders" / "ne_50m_admin_0_countries.geojson"
RADIUS_KM = 100.0
R_EARTH_KM = 6371.0
_LEVELS = {"technisch": 5, "prudent": 8, "oelgas": 11}  # S5 column index of each level's total


def derive_table(xlsx: Path) -> dict:
    """Read Gidden Table S5 into {iso3: {"region", "technisch", "prudent", "oelgas"}} (Gt CO2)."""
    import pandas as pd

    df = pd.read_excel(xlsx, sheet_name="S5", header=None, skiprows=3).iloc[:, :12]
    out = {}
    for _, row in df.iterrows():
        iso = row[0]
        if not (isinstance(iso, str) and len(iso) == 3 and iso.isupper()):
            continue  # skips the "Total" / "Final Total" rows and blank lines
        out[iso] = {"region": str(row[2])} | {k: float(pd.to_numeric(row[c], errors="coerce") or 0.0)
                                               for k, c in _LEVELS.items()}
    return out


def derive_mask(tif: Path, radius_km: float = RADIUS_KM) -> NDArray:
    """(360, 720) bool: a basin pixel (values 1-4) within *radius_km* of the cell centre."""
    import rasterio
    from rasterio.enums import Resampling
    from scipy.spatial import cKDTree

    with rasterio.open(tif) as d:
        h, w = d.height // 10, d.width // 10  # read at ~0.1 deg; basins are far larger than that
        v = d.read(1, out_shape=(h, w), resampling=Resampling.nearest)
        t = d.transform * d.transform.scale(d.width / w, d.height / h)
    rows, cols = np.nonzero((v >= 1) & (v <= 4))
    lon = t.c + (cols + 0.5) * t.a
    lat = t.f + (rows + 0.5) * t.e

    def xyz(la, lo):
        la, lo = np.radians(la), np.radians(lo)
        return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]

    tree = cKDTree(xyz(lat, lon))
    lo2, la2 = np.meshgrid(grid_lons(), grid_lats())
    chord = 2 * np.sin(radius_km / R_EARTH_KM / 2)
    d, _ = tree.query(xyz(la2.ravel(), lo2.ravel()), k=1, distance_upper_bound=chord)
    return np.isfinite(d).reshape(N_LAT, N_LON)


@lru_cache(maxsize=1)
def _table() -> dict:
    return json.loads(TABLE.read_text())


def storage_by_country(stufe: str = "prudent") -> dict[str, float]:
    """ISO3 -> storage [Gt CO2] at level *stufe* ("prudent", "technisch", "oelgas")."""
    return {k: v[stufe] for k, v in _table().items()}


def region_by_country() -> dict[str, str]:
    """ISO3 -> IPCC R5 region name as given by Gidden et al."""
    return {k: v["region"] for k, v in _table().items()}


@lru_cache(maxsize=1)
def storage_mask() -> NDArray:
    with np.load(MASK) as f:
        return f["mask"].astype(bool)


@lru_cache(maxsize=1)
def iso3_grid() -> NDArray:
    """country_for_land (ISO-A2, Natural Earth) translated to ISO-A3 via the same file."""
    from nbs.dac_climate import country_for_land

    feats = json.loads(COUNTRIES.read_text())["features"]
    a2a3 = {f["properties"]["ISO_A2_EH"]: f["properties"]["ISO_A3_EH"] for f in feats}
    a2 = country_for_land()
    out = np.full(a2.shape, "", dtype="<U3")
    for code in np.unique(a2[a2 != ""]):
        a3 = a2a3.get(str(code), "")
        if len(a3) == 3 and a3 != "-99":
            out[a2 == code] = a3
    return out
```

- [ ] **Step 4: Write `scripts/fetch_storage_gidden.py`**

```python
"""Download Gidden et al. (2025) storage data and derive the per-country table and basin mask.

Run: .venv/bin/python scripts/fetch_storage_gidden.py
"""

import json
import urllib.request

import numpy as np

from nbs.dac_storage import MASK, ROOT, TABLE, derive_mask, derive_table

RECORD = "https://zenodo.org/api/records/18343187/files/{}/content"
FILES = ("gidden_et_al_2025_supplemental_data.xlsx", "Figure_1a_EPSG4326_generalised_to_0_01degree.tif",
         "Read_Me_Figure1a.rtf")
RAW = ROOT / "data" / "raw" / "gidden"

RAW.mkdir(parents=True, exist_ok=True)
for name in FILES:
    if not (RAW / name).exists():
        urllib.request.urlretrieve(RECORD.format(name), RAW / name)
TABLE.write_text(json.dumps(derive_table(RAW / FILES[0]), indent=1, ensure_ascii=False))
np.savez_compressed(MASK, mask=derive_mask(RAW / FILES[1]))
print("ok", TABLE, MASK)
```

- [ ] **Step 5: Run the script**

Run: `.venv/bin/python scripts/fetch_storage_gidden.py`
Expected: `ok …speicher_gidden.json …speicher_maske.npz`

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_dac_storage.py -v`
Expected: 7 passed.

Wenn `test_mask_near_basins` an der Schweiz scheitert (Molassebecken liegt im Raster): Ort auf einen sicher beckenfreien Punkt ändern, z. B. Zentralgrönland (72.0, −40.0), dann `assert not`. Die Änderung im Commit-Text nennen.

- [ ] **Step 7: Commit**

```bash
git add scripts/fetch_storage_gidden.py src/nbs/dac_storage.py tests/test_dac_storage.py data/dac/speicher_gidden.json data/dac/speicher_maske.npz
git commit -m "feat(dac): geological storage per country and basin proximity (Gidden et al. 2025)"
```

---

### Task 2: η je Land, Kernel-Matrix, Lücke

**Files:**
- Create: `src/nbs/dac_optim.py`, `tests/test_dac_optim.py`

**Interfaces:**
- Consumes: Task 1 (`storage_by_country`, `storage_mask`, `iso3_grid`); `nbs.dac.efficiency_grid(year, variant, pathway)`, `nbs.dac.dac_possible()`; `nbs.response.green_carbon/green_temperature/background_co2_ppm/convolve_response`; `nbs.forcing.phi_co2_background(flux_kg_per_yr, g_c, bg_ppm)`; `nbs.constants.YEARS`.
- Produces:
  - `eta_by_country(quantil: float = 0.9) -> tuple[list[str], NDArray]`: Länder (ISO3, sortiert) und η (n_c, 75). Nur Länder mit Speicher > 0 und mindestens einer passenden Zelle.
  - `removal_kernel_matrix() -> NDArray` (75, 75): K[y, t] = ΔT [K] im Jahr t je **Gt** Netto-Entnahme im Jahr y (negativ = Kühlung), 0 für t < y.
  - `gap_series() -> NDArray` (75,): benötigte Kühlung [K] ≥ 0.

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for nbs.dac_optim."""

import numpy as np
import pytest

from nbs.constants import YEARS
from nbs.dac_optim import eta_by_country, gap_series, removal_kernel_matrix


def test_kernel_is_causal_and_cooling():
    k = removal_kernel_matrix()
    assert k.shape == (75, 75)
    assert np.allclose(np.tril(k, -1), 0)  # K[y, t] = 0 for t < y
    assert np.all(k[0, 1:] < 0)


def test_kernel_matches_existing_horizon_kernel():
    from nbs.dac_compare import _removal_kernel  # K per t CO2 at T_END

    k = removal_kernel_matrix()
    assert k[:, -1] == pytest.approx(_removal_kernel() * 1e9, rel=1e-6)


def test_kernel_size_is_tcre_like():
    # 1 Gt removed in 2026: roughly -0.45 mK by 2100 (TCRE ~0.45 K / 1000 Gt)
    assert -1e-3 < removal_kernel_matrix()[0, -1] < -2e-4


def test_eta_countries_have_storage_and_cells():
    from nbs.dac_storage import storage_by_country

    countries, eta = eta_by_country()
    s = storage_by_country("prudent")
    assert eta.shape == (len(countries), 75)
    assert all(s[c] > 0 for c in countries)
    assert "CHE" not in countries and "ISL" not in countries
    assert np.all(np.isfinite(eta))
    assert np.all(eta <= 1.0)


def test_eta_rises_with_cleaner_power():
    countries, eta = eta_by_country()
    assert np.median(eta[:, YEARS.tolist().index(2050)]) > np.median(eta[:, 0])


def test_best_decile_beats_median():
    _, best = eta_by_country(0.9)
    _, med = eta_by_country(0.5)
    assert np.all(best >= med - 1e-12)


def test_gap_matches_slide_25():
    g = gap_series()
    assert g.shape == (75,) and np.all(g >= 0)
    i = YEARS.tolist().index(2050)
    assert g[i] * 1000 == pytest.approx(323 - 14, abs=3)   # need minus trees, mK
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_dac_optim.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'nbs.dac_optim'`

- [ ] **Step 3: Write `src/nbs/dac_optim.py` (first part)**

```python
"""Where, when and how much DAC: a linear programme that closes the 1.5 deg C gap of Very Low.

Decision variables x[c, y]: gross DAC removal in country c and year y [Gt/a]. The climate effect
is linear in x through the FaIR kernel K[y, t] (temperature in year t per Gt net removal in year y,
the same chain as the trees) and the country's net efficiency eta[c, y] (nbs.dac):

    cooling(t) = - sum_c sum_y K[y, t] * eta[c, y] * x[c, y]   >= gap(t)  for t >= X
    sum_y x[c, y] <= storage[c]                                (Gidden et al. 2025)
    sum_c x[c, t] <= GROWTH * sum_c x[c, t-1], t > 2030;  sum_c x[c, 2030] <= 0.0088
                                                               (Zurbriggen et al. 2026)

Stage 1 finds the earliest X; stage 2 minimises total gross removal at that X. If no X <= 2100 is
feasible, the closest approach minimises the summed shortfall instead.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from nbs.constants import YEARS

ROOT = Path(__file__).resolve().parents[2]
GAP_FILE = ROOT / "docs" / "slides" / "chart_data" / "luecke.json"
START_2030_GT = 0.0088   # mean planned DAC capacity 2030 (Zurbriggen et al. 2026)
GROWTH = 1.20            # wind-energy analogue, 20 %/a (Zurbriggen et al. 2026)
N_Y = len(YEARS)


def eta_by_country(quantil: float = 0.9, stufe: str = "prudent") -> tuple[list[str], NDArray]:
    """Countries with storage and at least one DAC-capable cell near a basin, and their net
    efficiency per year: the median of the cells at or above the *quantil* of eta in that year."""
    from nbs.dac import dac_possible, efficiency_grid
    from nbs.dac_storage import iso3_grid, storage_by_country, storage_mask

    store = storage_by_country(stufe)
    iso = iso3_grid()
    ok = dac_possible() & storage_mask()
    grids = [efficiency_grid(int(y)) for y in YEARS]
    countries, rows = [], []
    for c in sorted(k for k, v in store.items() if v > 0):
        cells = ok & (iso == c)
        if not cells.any():
            continue
        row = []
        for g in grids:
            v = g[cells]
            v = v[np.isfinite(v)]
            row.append(float(np.median(v[v >= np.quantile(v, quantil)])) if v.size else np.nan)
        if np.all(np.isfinite(row)):
            countries.append(c)
            rows.append(row)
    return countries, np.array(rows)


@lru_cache(maxsize=1)
def removal_kernel_matrix(scenario: str = "ssp245") -> NDArray:
    """K[y, t]: temperature change [K] in year t per Gt CO2 taken out of the air in year y."""
    from nbs.forcing import phi_co2_background
    from nbs.response import background_co2_ppm, convolve_response, green_carbon, green_temperature

    g_c, g_t, bg = green_carbon(scenario), green_temperature(scenario), background_co2_ppm(scenario)
    k = np.zeros((N_Y, N_Y))
    for i in range(N_Y):
        flux = np.zeros(N_Y)
        flux[i] = -1000.0  # one tonne removed [kg], the marginal response ...
        k[i] = convolve_response(g_t, phi_co2_background(flux, g_c, bg)) * 1e9  # ... scaled to 1 Gt
    return k


def gap_series() -> NDArray:
    """Cooling needed on top of Very Low and the trees on cooling areas [K], year by year (slide 25)."""
    d = json.loads(GAP_FILE.read_text())
    assert d["y"] == YEARS.tolist()
    return np.maximum(0.0, (np.array(d["need"]) - np.array(d["k"])) / 1000.0)
```

- [ ] **Step 4: Copy the gap data into the repo**

`luecke.json` liegt bisher nur im Scratchpad. Ins Repo kopieren, damit Code und Tests nicht vom Scratchpad abhängen:

Run: `cp <scratchpad>/luecke.json docs/slides/chart_data/luecke.json`

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_dac_optim.py -v`
Expected: 7 passed. Laufzeit beim ersten Mal einige Minuten (75 η-Gitter, 75 Kernel-Läufe).

Wenn `test_gap_matches_slide_25` abweicht:
- `luecke.json` öffnen und den Wert 2050 von `need` und `k` prüfen. Die Folie nennt 323 mK und 14 mK.
- Die Testtoleranz nur anpassen, wenn die Folienwerte gerundet sind, nicht wenn die Daten anders sind.

- [ ] **Step 6: Commit**

```bash
git add src/nbs/dac_optim.py tests/test_dac_optim.py docs/slides/chart_data/luecke.json
git commit -m "feat(dac): net efficiency per country near storage, FaIR removal kernel, 1.5 deg C gap"
```

---

### Task 3: LP lösen (frühestes X, minimale Entnahme, Annäherung)

**Files:**
- Modify: `src/nbs/dac_optim.py` (anhängen)
- Modify: `tests/test_dac_optim.py` (anhängen)

**Interfaces:**
- Consumes: Task 2 (`eta_by_country`, `removal_kernel_matrix`, `gap_series`, `GROWTH`, `START_2030_GT`); `nbs.dac_storage.storage_by_country`.
- Produces:
  - `build_and_solve(eta, kernel, gap, storage, x_from, growth, start_2030=START_2030_GT, objective="min_total") -> tuple[bool, NDArray | None]`: reiner LP-Kern ohne Datenzugriff (für den Minifall testbar).
  - `solve(growth: float = GROWTH, stufe: str = "prudent", quantil: float = 0.9) -> dict` mit Schlüsseln:
    - `"jahre"`, `"laender"`, `"x"` (n_c × 75, Gt/a), `"eta"`.
    - `"kuehlung_k"` (75), `"luecke_k"` (75), `"jahr_x"` (int oder None).
    - `"status"` (`"geschlossen"` | `"annaeherung"`), `"wachstum"`, `"stufe"`, `"quantil"`.

- [ ] **Step 1: Write the failing tests**

```python
from nbs.dac_optim import build_and_solve, solve


def _mini():
    # two countries, flat kernel (1 Gt removed -> 1 mK cooling forever), 10 years
    n = 10
    k = np.triu(np.full((n, n), -1e-3))
    eta = np.array([[0.9] * n, [0.5] * n])
    return k, eta


def test_mini_uses_better_country_first():
    k, eta = _mini()
    gap = np.full(10, 2e-3)      # 2 mK from year 0 on: 2.22 Gt in country 0 at eta 0.9
    ok, x = build_and_solve(eta, k, gap, storage=np.array([5.0, 5.0]), x_from=0, growth=10.0, start_2030=None)
    assert ok
    assert x[1].sum() == pytest.approx(0.0, abs=1e-9)
    assert x[0].sum() == pytest.approx(2e-3 / 1e-3 / 0.9, rel=1e-6)


def test_mini_storage_forces_second_country():
    k, eta = _mini()
    gap = np.full(10, 2e-3)
    ok, x = build_and_solve(eta, k, gap, storage=np.array([1.0, 5.0]), x_from=0, growth=10.0, start_2030=None)
    assert ok
    assert x[0].sum() == pytest.approx(1.0, rel=1e-6)
    assert x[1].sum() > 0


def test_mini_infeasible_reports_false():
    k, eta = _mini()
    ok, _ = build_and_solve(eta, k, np.full(10, 1.0), storage=np.array([1.0, 1.0]), x_from=0, growth=10.0, start_2030=None)
    assert not ok


def test_negative_eta_never_used():
    k, eta = _mini()
    eta[0, :5] = -0.2
    ok, x = build_and_solve(eta, k, np.full(10, 1e-3), storage=np.array([5.0, 5.0]), x_from=5, growth=10.0, start_2030=None)
    assert ok
    assert np.allclose(x[0, :5], 0.0)


@pytest.fixture(scope="module")
def main_case():
    return solve()


def test_main_case_respects_constraints(main_case):
    from nbs.dac_storage import storage_by_country

    r = main_case
    x = np.array(r["x"])
    tot = x.sum(axis=0)
    y = np.array(r["jahre"])
    assert np.all(x >= -1e-9)
    assert tot[y == 2030][0] <= 0.0088 + 1e-9
    for i in range(1, len(y)):
        if y[i] > 2030:
            assert tot[i] <= 1.2 * tot[i - 1] + 1e-9
    s = storage_by_country("prudent")
    assert all(x[i].sum() <= s[c] + 1e-6 for i, c in enumerate(r["laender"]))


def test_main_case_closes_or_approaches(main_case):
    r = main_case
    assert r["status"] in ("geschlossen", "annaeherung")
    if r["status"] == "geschlossen":
        i = r["jahre"].index(r["jahr_x"])
        assert np.all(np.array(r["kuehlung_k"])[i:] >= np.array(r["luecke_k"])[i:] - 1e-9)


def test_slow_growth_still_returns():
    r = solve(growth=1.11)
    assert r["status"] in ("geschlossen", "annaeherung")
    assert np.all(np.isfinite(r["kuehlung_k"]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_dac_optim.py -v -k "mini or negative or main_case or slow"`
Expected: FAIL with `ImportError: cannot import name 'build_and_solve'`

- [ ] **Step 3: Implement (append to `src/nbs/dac_optim.py`)**

```python
def build_and_solve(eta: NDArray, kernel: NDArray, gap: NDArray, storage: NDArray, x_from: int | None,
                    growth: float, start_2030: float | None = START_2030_GT, objective: str = "min_total",
                    years: NDArray | None = None) -> tuple[bool, NDArray | None]:
    """The LP on plain arrays. x is flattened country-major: x[c * n + y].

    objective "min_total": cooling >= gap for t >= x_from, minimise sum x.
    objective "min_shortfall": extra slack s[t] >= gap - cooling, s >= 0, minimise sum s (x_from ignored).
    start_2030=None drops the 2026-2030 caps (unit tests); growth applies to every year after the
    first then.
    """
    from scipy.optimize import linprog
    from scipy.sparse import lil_matrix

    n_c, n = eta.shape
    years = np.arange(2026, 2026 + n) if years is None else years
    nx = n_c * n
    slack = objective == "min_shortfall"
    nv = nx + (n if slack else 0)
    # cooling(t) = sum_{c,y} -K[y, t] * eta[c, y] * x[c, y]
    cool = np.zeros((n, nx))
    for c in range(n_c):
        cool[:, c * n:(c + 1) * n] = (-kernel * eta[c][:, None]).T
    a, b = [], []
    if slack:
        rows = np.hstack([-cool, -np.eye(n)])          # -cooling - s <= -gap
        a.append(rows); b.append(-gap)
    else:
        a.append(np.hstack([-cool[x_from:], np.zeros((n - x_from, nv - nx))])); b.append(-gap[x_from:])
    st = lil_matrix((n_c, nv))                          # storage per country
    for c in range(n_c):
        st[c, c * n:(c + 1) * n] = 1.0
    a.append(st.toarray()); b.append(storage)
    first = 1 if start_2030 is None else int(np.where(years == 2030)[0][0]) + 1
    gr = np.zeros((n - first, nv))                       # sum_c x[c, t] - growth * sum_c x[c, t-1] <= 0
    for j, t in enumerate(range(first, n)):
        gr[j, t::n][:n_c] = 1.0
        gr[j, t - 1::n][:n_c] = -growth
    a.append(gr); b.append(np.zeros(n - first))
    bounds = [(0.0, None)] * nv
    for c in range(n_c):
        for y in range(n):
            hi = None
            if start_2030 is not None and years[y] <= 2030:
                hi = start_2030 * (years[y] - 2025) / 5          # per-country cap; the sum cap follows below
            if eta[c, y] <= 0:
                hi = 0.0                                          # a plant that warms is never built
            bounds[c * n + y] = (0.0, hi)
    if start_2030 is not None:                                    # world caps 2026-2030
        for y in np.where(years <= 2030)[0]:
            row = np.zeros(nv); row[y:nx:n] = 1.0
            a.append(row[None, :]); b.append(np.array([START_2030_GT * (years[y] - 2025) / 5]))
    c_obj = np.r_[np.zeros(nx), np.ones(n)] if slack else np.r_[np.ones(nx), np.zeros(nv - nx)]
    res = linprog(c_obj, A_ub=np.vstack(a), b_ub=np.concatenate(b), bounds=bounds, method="highs")
    if res.status != 0:
        return False, None
    return True, res.x[:nx].reshape(n_c, n)


def solve(growth: float = GROWTH, stufe: str = "prudent", quantil: float = 0.9) -> dict:
    """Stage 1: earliest year X from which the gap stays closed; stage 2: least total removal at X.
    No feasible X: closest approach (least summed shortfall)."""
    from nbs.dac_storage import storage_by_country

    countries, eta = eta_by_country(quantil, stufe)
    store = storage_by_country(stufe)
    storage = np.array([store[c] for c in countries])
    k, gap = removal_kernel_matrix(), gap_series()

    def attempt(i):
        return build_and_solve(eta, k, gap, storage, i, growth, years=YEARS)

    lo, hi, best = 0, N_Y - 1, None
    ok, x = attempt(hi)
    if ok:
        best = (hi, x)
        while lo < hi:                       # feasibility is monotone in X: a later X drops constraints
            mid = (lo + hi) // 2
            ok, x = attempt(mid)
            if ok:
                hi, best = mid, (mid, x)
            else:
                lo = mid + 1
        jahr_x, x, status = int(YEARS[best[0]]), best[1], "geschlossen"
    else:
        ok, x = build_and_solve(eta, k, gap, storage, None, growth, objective="min_shortfall", years=YEARS)
        assert ok, "closest-approach LP must always be feasible (x = 0 is a solution)"
        jahr_x, status = None, "annaeherung"
    cooling = -np.einsum("yt,cy,cy->t", k, eta, x)
    return {"jahre": YEARS.tolist(), "laender": countries, "x": x.tolist(), "eta": eta.tolist(),
            "kuehlung_k": cooling.tolist(), "luecke_k": gap.tolist(), "jahr_x": jahr_x, "status": status,
            "wachstum": growth, "stufe": stufe, "quantil": quantil}
```

Hinweis zur Bisektion: Machbarkeit ist monoton in X, denn ein späteres X streicht Nebenbedingungen. Deshalb findet die Bisektion das kleinste X.

Hinweis zum Index `gr[j, t::n][:n_c]`: Die Spalten von Jahr t aller Länder sind `c * n + t`, also Schrittweite n ab t. `[:n_c]` begrenzt das auf die x-Spalten, damit keine Slack-Spalten getroffen werden.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_dac_optim.py -v`
Expected: alle Tests grün.


- [ ] **Step 5: Commit**

```bash
git add src/nbs/dac_optim.py tests/test_dac_optim.py
git commit -m "feat(dac): LP for the earliest year the 1.5 deg C gap stays closed, least total removal"
```

---

### Task 4: Export, Sensitivitäten, FaIR-Gegenprobe, Methodendoku

**Files:**
- Create: `scripts/dac_optim_export.py`
- Modify: `tests/test_dac_optim.py` (ein Test), `docs/methods/dac-modell.md` (Abschnitt 8)
- Output: `data/dac/optim.json`

**Interfaces:**
- Consumes:
  - `solve(growth, stufe, quantil)`, `removal_kernel_matrix`, `region_by_country`.
  - `nbs.fair_module.run_fair_baseline(scenario)` und `run_fair_perturbed(nee_gtco2_yr, albedo_rf_wm2, scenario)`. Beide Eingaben haben die Länge `T_END - T_START` (74), also die Jahre 2026…2099.
- Produces: `data/dac/optim.json` mit den Schlüsseln:
  - `"haupt"`: Ergebnis von `solve()`, ergänzt um `"region"` (Liste R5 je Land) und `"fair_kuehlung_k"` (74 Werte).
  - `"fair_abweichung_2100_rel"`: relative Abweichung FaIR gegen LP im letzten gemeinsamen Jahr.
  - `"sens"`: `{"wachstum_11": …, "technisch": …, "median": …}`, je Kurzform mit `jahr_x`, `status`, `kuehlung_k` und Summe Gt.

- [ ] **Step 1: Write the failing test**

```python
def test_export_file_is_complete():
    import json
    from pathlib import Path

    d = json.loads((Path(__file__).resolve().parents[1] / "data" / "dac" / "optim.json").read_text())
    h = d["haupt"]
    assert len(h["region"]) == len(h["laender"])
    assert len(h["fair_kuehlung_k"]) == 74
    assert np.isfinite(d["fair_abweichung_2100_rel"])
    assert set(d["sens"]) == {"wachstum_11", "technisch", "median"}
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/pytest tests/test_dac_optim.py::test_export_file_is_complete -v`
Expected: FAIL with `FileNotFoundError`

- [ ] **Step 3: Write `scripts/dac_optim_export.py`**

```python
"""Run the DAC optimisation (main case + sensitivities), cross-check with full FaIR, write data/dac/optim.json.

Run: .venv/bin/python scripts/dac_optim_export.py
"""

import json

import numpy as np

from nbs.dac_optim import ROOT, solve
from nbs.dac_storage import region_by_country
from nbs.fair_module import run_fair_baseline, run_fair_perturbed

OUT = ROOT / "data" / "dac" / "optim.json"


def short(r):
    return {"jahr_x": r["jahr_x"], "status": r["status"], "kuehlung_k": r["kuehlung_k"],
            "summe_gt": float(np.sum(r["x"]))}


main = solve()
reg = region_by_country()
main["region"] = [reg[c] for c in main["laender"]]
net = (np.array(main["x"]) * np.array(main["eta"])).sum(axis=0)        # Gt/a net removal, 2026..2100
n = len(run_fair_baseline())                                           # 74: FaIR study axis 2026..2099
fair = run_fair_perturbed(-net[:n], np.zeros(n)) - run_fair_baseline()
main["fair_kuehlung_k"] = (-fair).tolist()
lp_last = main["kuehlung_k"][n - 1]
dev = float((-fair[-1] - lp_last) / lp_last) if lp_last else float("nan")
out = {"haupt": main, "fair_abweichung_2100_rel": dev,
       "sens": {"wachstum_11": short(solve(growth=1.11)), "technisch": short(solve(stufe="technisch")),
                "median": short(solve(quantil=0.5))}}
OUT.write_text(json.dumps(out, ensure_ascii=False))
print("ok", main["status"], main["jahr_x"], f"{np.sum(main['x']):.0f} Gt brutto", f"FaIR-Abweichung {dev:+.1%}",
      {k: (v["status"], v["jahr_x"]) for k, v in out["sens"].items()})
```

- [ ] **Step 4: Run export and test**

Run: `.venv/bin/python scripts/dac_optim_export.py && .venv/bin/pytest tests/test_dac_optim.py -v`
Expected: Zeile `ok <status> <X> … Gt brutto FaIR-Abweichung …`, danach alle Tests grün.

Die Ausgabezeile notieren; sie liefert die Zahlen für die Folientexte in Task 5/6.

Liegt die FaIR-Abweichung über ±15 %, nicht stillschweigend weitermachen:
- In Notes und Methodendoku nennen.
- Dem Nutzer melden, bevor die Folien gebaut werden. Sie misst die Nichtlinearität aus Review Focus 4.

- [ ] **Step 5: Add section to `docs/methods/dac-modell.md`**

Vor „## Quellen“ einfügen; die Zahlen aus der Ausgabe von Step 4 eintragen:

```markdown
## 8  Optimierung: wo, wann, wie viel

Code: `src/nbs/dac_storage.py`, `src/nbs/dac_optim.py`, `scripts/fetch_storage_gidden.py`, `scripts/dac_optim_export.py`; Ergebnis `data/dac/optim.json`.

- **Frage:** Ab welchem Jahr X kann DAC die Lücke von Very Low zu 1,5 °C (nach Abzug der Bäume auf kühlenden Flächen, Folie 25) dauerhaft schließen, und mit welchem kleinsten Ausbau, wo und wann?
- **Variablen:** Brutto-Entnahme x[Land, Jahr] in Gt/a, 2026–2100.
- **Klima:** FaIR-Kernel derselben Kette wie beim Baum (1 t marginal, linear auf Gt skaliert). Gegenprobe mit vollem FaIR: Abweichung <Wert> in 2099.
- **η je Land:** Median der besten 10 % der DAC-tauglichen Zellen mit einem Sedimentbecken innerhalb von 100 km (Gidden-Raster).
- **Speicher:** Gidden et al. 2025, prudent limit je Land (Welt 1 460 Gt; Deutschland 1,3, Norwegen 6,9, UK 8,9, Russland 244, USA 141 Gt). Kein Transport über Grenzen.
- **Wachstum:** 8,8 Mt/a in 2030 (geplante Kapazität), danach ≤ +20 %/a (Wind-Analogie), beides Zurbriggen et al. 2026.
- **Ergebnis Hauptfall:** <status>, X = <Jahr>, <Summe> Gt brutto.
- **Sensitivitäten:** 11 %/a → <…>; technisches Potenzial → <…>; Median statt bestes Dezil → <…>.
- **Nicht enthalten:** Kosten, Strom- und Wasserverfügbarkeit, Injektionsraten je Becken, Anlagenlebensdauer, Basalt-Mineralisierung.
```

Die spitzen Klammern sind Pflichtfelder für die echten Zahlen aus Step 4. Ohne sie darf nicht committet werden.

Quellen am Ende ergänzen:

```markdown
- Gidden, M. J. et al. (2025): A prudent planetary limit for geologic carbon storage. Nature 645, 124–132. Daten: doi:10.5281/zenodo.18343187.
- Zurbriggen, T. et al. (2026): Short-term action is key for gigaton-scale Direct Air Capture by 2050. Nat. Commun. 17, 6184.
```

- [ ] **Step 6: Commit**

```bash
git add scripts/dac_optim_export.py tests/test_dac_optim.py data/dac/optim.json docs/methods/dac-modell.md
git commit -m "feat(dac): export the optimised DAC pathway with sensitivities and a FaIR cross-check"
```

---

### Task 5: Folie 30 „Optimierung: wo, wann, wie viel DAC?“

**Files:**
- Create: `<scratchpad>/patch_dac_optim.py`
- Modify: `<scratchpad>/new_vergleich.py` (zwei Zeilen vor `HTML.write_text`)

**Interfaces:**
- Consumes:
  - `data/dac/optim.json` (Task 4), `data/dac/speicher_gidden.json` (Task 1).
  - Deck-Helfer im Stil von `patch_story4.py`: `_sec(page, title)` (Regex-Match einer Folie über `data-title`), `_rep(text, a, b)` (Ersetzen mit Assert).
  - Highlight-Klasse `.hl`, Schritte über `data-step`, Takeaway `<p class="takeaway" data-step="N" style="--d:0">`.
- Produces: `patch(page) -> str` in `patch_dac_optim.py`; Folie `data-title="Optimierung von DAC"` direkt nach der Folie `data-title="Netto-Entnahme von DAC"`.

- [ ] **Step 1: Read the reference slides**

Run: `grep -n 'data-title="Strahlungsantrieb von CO₂"' -A60 docs/slides/html/dissvortrag_v2.html | head -90`

Damit den Aufbau der Wortformel mit `.hl`-Schritten auf Folie 17 lesen, außerdem `data-title="Netto-Entnahme von DAC"` (Folie 29) für die η-Karte (`data-chart`-Schlüssel). Notieren:
- CSS-Klassen der Wortformel.
- `data-chart`-Schlüssel der η-Karte.
- Wie Schritte (`data-step`) und `.hl` zusammenspielen (`:has()`-Regeln).

- [ ] **Step 2: Write `patch_dac_optim.py` with slide 30**

Die Folie besteht aus:
- **Linke Spalte (40 %):** drei Eingangs-Kärtchen untereinander, jedes mit `data-in="eta|speicher|luecke"`:
  1. η-Karte als Miniatur: dasselbe Bild bzw. Chart wie Folie 29, verkleinert, Titel „Netto-Wirkungsgrad je Ort“.
  2. Speicher: Weltkarte als SVG, Kreise je Land mit Fläche ∝ Gt aus `speicher_gidden.json`, Projektion equirectangular (x = (lon+180)/360·W, y = (90−lat)/180·H). Länder-Mittelpunkte aus `iso3_grid()` als Schwerpunkt der Zellen, vorab in Python berechnet. Beschriftet: RUS, USA, AUS, DEU (mit Zahl). Titel „Speicher je Land (Gidden 2025)“.
  3. Lücke: kleine ECharts-Linie `luecke` (Spec `EC_GAP`) mit `still: true`, nur Schritt 1 (rote Fläche). Titel „Lücke zu 1,5 °C“.
- **Rechte Spalte, Wortformel in fünf Schritten** (Schritt n hebt Zeile n mit `.hl` hervor und das passende Kärtchen links über eine `:has()`-Regel):
  1. `Gesucht: DAC-Entnahme je Land und Jahr` (x[Land, Jahr])
  2. `Minimiere: Gesamtentnahme Σ x`
  3. `Kühlung ≥ Lücke` → Kärtchen luecke und eta
  4. `Σ Einlagerung ≤ Speicher je Land` → Kärtchen speicher
  5. `Wachstum ≤ 20 %/a (wie Windkraft)` mit Quelle „Zurbriggen et al. 2026“ klein
- **Takeaway (Schritt 6):** Text aus dem Ergebnis, z. B. „Speicher reicht weltweit (1 460 Gt), aber kaum dort, wo der Strom am saubersten ist.“ Diese Aussage stimmt nur, wenn `optim.json` zeigt, dass Nordeuropa (NOR, SWE, FIN, FRA, DEU, GBR) zusammen < 10 % der Entnahme bekommt. Sonst den Takeaway an das tatsächliche Ergebnis anpassen.
- **Notes:**
  - Formulierung des LP.
  - Quellen Gidden 2025 und Zurbriggen 2026.
  - Hinweis „zusätzlich zu den 335 Gt in Very Low“.
  - Hinweis zur Speichernähe (100 km).

Die Folie wird mit `page = page[:m.end()] + NEW + page[m.end():]` hinter `_sec(page, "Netto-Entnahme von DAC")` eingefügt. Die Helfer `_sec`/`_rep` werden aus `patch_story4` importiert (`from patch_story4 import _sec, _rep`).

- [ ] **Step 3: Hook into the build chain**

In `<scratchpad>/new_vergleich.py` vor `HTML.write_text(...)` einfügen:

```python
import patch_dac_optim
page = patch_dac_optim.patch(page)
```

- [ ] **Step 4: Build and check**

Run: `cd <scratchpad> && /Users/timodiepers/Documents/Coding/dissvortrag/.venv/bin/python new_vergleich.py`
Expected: `ok 35` (eine Folie mehr als bisher, 34).

Screenshots aller Schritte von Folie 30 (Nummer im Deck prüfen, sollte 30 sein):

Run: `cd <scratchpad> && NODE_PATH=$(ls -d /private/tmp/claude-501/*/e3673260-*/scratchpad/node_modules | head -1) node steps.mjs 30 0 -1 -1 -1 -1 -1 -1`

Prüfen:
- Nichts überlappt.
- Schriften ≥ 19 px.
- Highlight-Rahmen ohne Layoutsprung.
- Nur der neue Schritt animiert.

- [ ] **Step 5: Commit des Repo-Teils entfällt** (Scratchpad liegt außerhalb des Repos). Weiter mit Task 6; veröffentlicht wird am Ende.

---

### Task 6: Folie 31 „DAC-Ausbau nach Ort und Zeit“, Backup, Texte, Veröffentlichung

**Files:**
- Modify: `<scratchpad>/patch_dac_optim.py`
- Output: `docs/slides/html/dissvortrag_v2.html`, `<scratchpad>/aufforstung_vortrag.html`

**Interfaces:**
- Consumes: `data/dac/optim.json` (`haupt.x`, `haupt.region`, `haupt.laender`, `haupt.kuehlung_k`, `haupt.luecke_k`, `haupt.jahr_x`, `haupt.status`); `EC_GAP`-Stil aus `patch_story4.py`; `EC_CHARTS`-Registrierung.
- Produces: Folie `data-title="DAC-Ausbau nach Ort und Zeit"` nach „Optimierung von DAC“; ECharts-Specs `EC_DAC_TEMP`, `EC_DAC_RAMP` in `EC_CHARTS` als `dactemp`, `dacramp`; `window.DAC_OPT`.

- [ ] **Step 1: Prepare compact data for the page**

In `patch_dac_optim.py` aus `optim.json` ableiten:
- `y`: Jahre.
- `gap_mk`: Lücke in mK.
- `cool_mk`: Kühlung durch DAC in mK.
- `rest_mk = max(0, gap − cool)`.
- `ramp`: Gt/a je R5-Region (Summe über Länder je Region).
- `bubbles`: je Land `[lon, lat, gt_kumuliert, region, iso]`, nur Länder mit > 1 Gt.

Mittelpunkte wie in Task 5. Als `window.DAC_OPT = {...}` vor `const EC_CHARTS` einsetzen, genau wie `patch_gap` es mit `LUECKE` macht (`_rep` auf die `const EC_CHARTS = {...}`-Zeile, die `patch_story4` zuletzt geschrieben hat, und `dactemp: EC_DAC_TEMP, dacramp: EC_DAC_RAMP` in das Objekt aufnehmen).

- [ ] **Step 2: Specs**

- **`EC_DAC_TEMP`** (rechts oben, `steps: 1`):
  - Achsen wie bei `EC_GAP`: x 2026–2100 mit Ticks 2026/2050/2075/2100, y in mK, Ticks ≥ 19 px.
  - k = 0: gestrichelte Linie „nötig für 1,5 °C“ (= `gap_mk`, Farbe `#8e0d16`), Fläche rot wie auf Folie 25.
  - k = 1: Linie „DAC kühlt“ (`cool_mk`, Bernstein `#9a6516`); die rote Fläche schrumpft auf `rest_mk`.
  - Bei `status == "geschlossen"`: markPoint am Jahr X mit „ab X: 1,5 °C gehalten“. Sonst ein Label am Ende mit „2100: noch N mK über 1,5 °C“.
- **`EC_DAC_RAMP`** (rechts unten, `steps: 0`):
  - Gestapelte Flächen je R5-Region in Gt/a, Farben fest je Region (fünf gut unterscheidbare, gedeckte Töne, R5OECD90+EU in Bernstein `#9a6516`).
  - Endlabels mit Regionsnamen auf Deutsch: OECD & EU, Asien, Lateinamerika, Naher Osten & Afrika, Reformländer.
- **Karte links:**
  - SVG mit equirectangularer Land-Silhouette (dieselbe Silhouette wie die übrigen Deck-Karten; vorhandenen Pfad oder vorhandenes Bild im Deck suchen: `grep -n "silhouette\|land.svg\|landmask" docs/slides/html/dissvortrag_v2.html`).
  - Darauf Kreise je Land: Fläche ∝ Gt kumuliert, Farbe = Region.
  - Beschriftet: die fünf größten Länder mit Gt.

- [ ] **Step 3: Slide markup and steps**

- Schritt 0: Temperatur, nur die Lücke.
- Schritt 1: Hochlauf und DAC-Kurve gleichzeitig. Der Hochlauf-Chart erscheint mit `data-step="1"`; im Temperatur-Chart ist das Schritt 1.
- Schritt 2: Kreise auf der Karte, gestaffelt einblenden (`--d` je Kreis), ohne frühere Elemente neu zu animieren.
- Schritt 3: Takeaway aus dem Ergebnis, z. B. „1,5 °C erst ab X – und nur mit Wachstum wie bei der Windkraft; bis 2050 kaum Wirkung.“ Bei `status == "annaeherung"`: „Selbst mit Wachstum wie bei der Windkraft bleibt 2100 eine Lücke von N mK.“
- Notes:
  - Sensitivitäten aus `optim.json["sens"]` als Sätze (11 %/a, technisches Potenzial, Median).
  - FaIR-Abweichung.
  - Hinweis, dass keine Kosten oder Stromverfügbarkeit eingehen.

- [ ] **Step 4: Move slides to backup and adapt texts**

- Die Folien „DAC in drei Strompfaden“ und „Priorisierung von Aufforstung und DAC“ ins Backup verschieben: `_sec`-Match ausschneiden und hinter `<!-- BACKUP:BEGIN -->` einsetzen.
- „Auf dem Holzweg? Nein.“: Den Aussage-Text lesen (`_sec(page, "Auf dem Holzweg? Nein.")`) und den DAC-Satz durch das Ergebnis ersetzen (Jahr X bzw. Rest-Lücke, Wachstumsannahme).
- „Methodischer Beitrag“: Punkt „Optimierung von DAC nach Ort und Zeit mit Speicher- und Wachstumsgrenzen“ ergänzen.
- Beide Texte vor dem Einbau dem Nutzer im Chat zeigen.

- [ ] **Step 5: Build, screenshot, check**

Run: `cd <scratchpad> && /Users/timodiepers/Documents/Coding/dissvortrag/.venv/bin/python new_vergleich.py`
Expected: `ok 36`.

Run: `cd <scratchpad> && NODE_PATH=$(ls -d /private/tmp/claude-501/*/e3673260-*/scratchpad/node_modules | head -1) node steps.mjs 31 0 -1 -1 -1 -1`

Prüfen:
- Schritte 0–3 korrekt.
- Lesbarkeit.
- Farben von Karte und Hochlauf identisch.
- Zahlen in Takeaway und Notes gleich wie in `optim.json`.

- [ ] **Step 6: Publish**

```bash
cp docs/slides/html/dissvortrag_v2.html <scratchpad>/aufforstung_vortrag.html
```

Dann `Artifact` publish mit `file_path=<scratchpad>/aufforstung_vortrag.html`, `url=https://claude.ai/artifact/9eyGdaGzKcobjEoTXqeREN`, ohne `icon`.

- [ ] **Step 7: Final test run**

Run: `.venv/bin/pytest tests/test_dac_storage.py tests/test_dac_optim.py tests/test_dac.py -v`
Expected: alle grün.
