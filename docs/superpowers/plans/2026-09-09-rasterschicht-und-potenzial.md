# Rasterschicht und Potenzial — Implementierungsplan (Plan 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Einzelbaum-Kette auf ein globales 0,5°-Gitter heben, damit sich beantworten lässt, *wo* Aufforstung kühlt und *wie viel* davon nach Abzug aller Korrekturen übrig bleibt.

**Architecture:** Alles hinter der Baumtrajektorie ist **linear in der Baumzahl**, und φ_CO₂ hängt gar nicht vom Ort ab. Daraus folgt die Bezahlbarkeit: fünf Baumsimulationen und zehn Faltungen genügen für 259 200 Gitterzellen, exakt und ohne Näherung. Details unter „Der Hebel" unten.

**Tech Stack:** Python 3.11+, numpy, scipy, xarray + netCDF4 (neu), matplotlib, pytest, uv

**Spec:** `docs/superpowers/specs/2026-09-09-baum-klima-geo-potenzial-design.md`, Abschnitte 6 und 8
**Befunde aus Plan 1:** `docs/superpowers/specs/2026-09-09-befunde-fuer-plan-2-und-3.md` — Abschnitt 4 ist für diesen Plan bindend.

## Global Constraints

- Python ≥ 3.11; Abhängigkeiten ausschließlich über `uv`, niemals `pip`. Tests: `uv run pytest -q -m "not slow"`; langsame Tests tragen `@pytest.mark.slow`. **Ausgangsstand: 202 passed / 55 deselected — nicht unterschreiten.**
- Zeitachse `nbs.constants.YEARS`, 126 Einträge, 2025–2150 einschließlich.
- Einheiten strikt: Vorrat kgC **je Baum**, CO₂-Fluss kg CO₂/a je Baum, Antrieb W/m² global, Temperatur K, Fläche m², Einstrahlung W/m².
- Vorzeichen: Δα < 0 bedeutet dunklerer Wald, ergibt positiven (wärmenden) Antrieb.
- Evapotranspiration ist **kein** Antriebsterm. Der Duveiller-Datensatz enthält ΔLE — das ist ein Grund mehr, nur den Albedo-Kanal daraus zu ziehen.
- Code, Funktionsnamen und Docstrings auf Englisch; Abbildungs- und Notebook-Text auf Deutsch mit echten Umlauten, niemals `ue`/`oe`/`ae`.
- `src/nbs/fair_module.py` wird nicht verändert. Nichts wird gelöscht.
- **Toleranzen:** Größen liegen bei 10⁻¹³ bis 10⁻¹⁵. `np.allclose` nimmt `atol=1e-8`, `pytest.approx` nimmt `abs=1e-12`, und ein gesetztes `rel` löscht das voreingestellte `abs` **nicht**. Jede Zusicherung setzt ihre Toleranz explizit. Dieser Defekt trat in Plan 1 fünfmal auf.
- Alle Downloads landen unter `data/raw/` (bereits gitignored). Nichts über 50 MB wird committet.

---

## Der Hebel — warum das bezahlbar ist

Die Kette ist hinter der Trajektorie vollständig linear:

```
φ_CO₂(t)  hängt nur von (Art, Szenario) ab — CO₂ mischt sich global, kein Ortsterm
φ_α(t)    = closure_s(t) · τ · A_s/A_⊕ · P_c        mit P_c = ⟨Δα · q̇⟩_c
```

`P_c` ist die **einzige** ortsabhängige Größe, und sie geht linear ein. Für eine Zelle *c* mit `N_c` Bäumen der Art *s* gilt daher

```
ΔT_c(t) = N_c · [ ΔT_CO₂,s(t) + P_c · U_s(t) ]
```

mit den je Art **einmal** gefalteten Kurven

```
ΔT_CO₂,s = g_T ∗ φ_CO₂,s              U_s = g_T ∗ ( closure_s · τ · A_s/A_⊕ )
```

Fünf Arten → zehn Faltungen. Danach ist jede Zelle eine Multiplikation, und die globale Summe ist

```
ΔT_global(t) = Σ_s [ (Σ_{c∈s} N_c) · ΔT_CO₂,s(t) + (Σ_{c∈s} N_c·P_c) · U_s(t) ]
```

also zwei Skalare je Art. Das ist **exakt**, keine Näherung, und es ist die Rechtfertigung dafür, keine Zelle einzeln durch die Pipeline zu schicken. Task 5 baut genau das und prüft es gegen zellweises Durchrechnen einer kleinen Stichprobe.

---

### Task 1: Quellenregister, Fallback zuerst

Die Datenlage ist der unsicherste Teil dieses Plans. Deshalb entsteht **zuerst** ein lauffähiger Fallback-Pfad, gegen den alles Weitere testbar ist, und erst danach werden echte Quellen angebunden.

**Recherchestand vor Planbeginn, verifiziert:**

| Quelle | Stand |
|---|---|
| Duveiller, Zenodo `10.5281/zenodo.1182145` | erreichbar, CC-BY-4.0, 699,8 MB, klassisches netCDF. Dimensionen `Longitude, Latitude, Month, Transition, Source`. Enthält ΔLE, Δ(H+G), **ΔR_n** — **kein Δα**. Übergangscodes 1–15, README unter derselben DOI. |
| Bastin, ETH Research Collection | HTTP 429 beim Probelauf, nicht abschließend geprüft |
| FAO Global Ecological Zones | HTTP 404 unter der erwarteten URL |
| Zenodo, DataCite, JRC-Portal allgemein | erreichbar |
| Einstrahlung q̇ am Boden | **noch keine Quelle geprüft.** Der Duveiller-Datensatz enthält sie nicht. Kandidaten: CERES EBAF-Surface (Registrierung nötig), ERA5 über den Copernicus-Datenspeicher (API-Schlüssel nötig), oder eine analytische TOA-Einstrahlung mal Klarheitsindex-Klimatologie. |

**Files:**
- Create: `src/nbs/grid.py`
- Create: `src/nbs/datasources.py`
- Create: `scripts/fetch_data.py`
- Test: `tests/test_grid.py`, `tests/test_datasources.py`

**Interfaces:**
- Produces:
  - `nbs.grid.GRID_RESOLUTION_DEG: float = 0.5`
  - `nbs.grid.grid_lats() -> NDArray` — 360 Zellmittelpunkte, 89,75 bis −89,75
  - `nbs.grid.grid_lons() -> NDArray` — 720 Zellmittelpunkte, −179,75 bis 179,75
  - `nbs.grid.cell_area_m2() -> NDArray` — Form (360, 720), exakte Kugelkappen-Fläche
  - `nbs.datasources.Source` — eingefrorene Dataclass: `key`, `title`, `doi`, `url`, `sha256`, `license`, `size_mb`, `citation`
  - `nbs.datasources.SOURCES: dict[str, Source]`
  - `nbs.datasources.resolve(key) -> Path | None` — liefert den lokalen Pfad, wenn vorhanden und Prüfsumme stimmt; sonst `None`
  - `nbs.datasources.status() -> dict[str, str]` — je Quelle `"vorhanden"`, `"fehlt"` oder `"pruefsumme_falsch"`

- [ ] **Step 1: Test für das Gitter schreiben**

```python
# tests/test_grid.py
import numpy as np
import pytest

from nbs.grid import GRID_RESOLUTION_DEG, cell_area_m2, grid_lats, grid_lons
from nbs.constants import A_EARTH_M2


def test_grid_shape_is_half_degree_global():
    assert GRID_RESOLUTION_DEG == 0.5
    assert grid_lats().shape == (360,)
    assert grid_lons().shape == (720,)


def test_grid_cells_are_centres_not_edges():
    assert grid_lats()[0] == pytest.approx(89.75)
    assert grid_lats()[-1] == pytest.approx(-89.75)
    assert grid_lons()[0] == pytest.approx(-179.75)
    assert grid_lons()[-1] == pytest.approx(179.75)


def test_cell_areas_sum_to_the_earth_surface():
    """The whole potential calculation is an area-weighted sum, so a grid whose
    cells do not add up to the planet would bias every number downstream."""
    total = cell_area_m2().sum()
    assert total == pytest.approx(A_EARTH_M2, rel=1e-3)


def test_cell_area_shrinks_towards_the_poles():
    a = cell_area_m2()
    equator_row = int(np.argmin(np.abs(grid_lats())))
    assert a[equator_row, 0] > a[0, 0]
    assert a[equator_row, 0] > a[-1, 0]


def test_cell_area_is_constant_along_a_latitude_row():
    a = cell_area_m2()
    assert np.allclose(a[100, :], a[100, 0], rtol=1e-12)
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_grid.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.grid'`

- [ ] **Step 3: Gitter implementieren**

```python
# src/nbs/grid.py
"""The common 0.5-degree grid every raster is resampled onto.

Cell areas use the exact spherical-cap difference rather than a cosine
approximation: the potential calculation is an area-weighted sum over the
whole planet, so a systematic area error would bias every number downstream.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from nbs.constants import A_EARTH_M2

GRID_RESOLUTION_DEG = 0.5
N_LAT = 360
N_LON = 720

_R_EARTH_M = np.sqrt(A_EARTH_M2 / (4.0 * np.pi))
"""Earth radius consistent with the A_EARTH_M2 used everywhere else."""


def grid_lats() -> NDArray:
    """Cell-centre latitudes, north to south [degrees]."""
    edges = np.linspace(90.0, -90.0, N_LAT + 1)
    return 0.5 * (edges[:-1] + edges[1:])


def grid_lons() -> NDArray:
    """Cell-centre longitudes, west to east [degrees]."""
    edges = np.linspace(-180.0, 180.0, N_LON + 1)
    return 0.5 * (edges[:-1] + edges[1:])


def cell_area_m2() -> NDArray:
    """Area of every grid cell [m^2], shape (N_LAT, N_LON).

    A latitude band between phi1 and phi2 has area
    2 pi R^2 |sin(phi2) - sin(phi1)|, split evenly across the longitudes.
    """
    edges = np.deg2rad(np.linspace(90.0, -90.0, N_LAT + 1))
    band = 2.0 * np.pi * _R_EARTH_M**2 * np.abs(np.sin(edges[:-1]) - np.sin(edges[1:]))
    return np.repeat((band / N_LON)[:, None], N_LON, axis=1)
```

- [ ] **Step 4: Gittertests laufen lassen**

Run: `uv run pytest tests/test_grid.py -v`
Expected: PASS, 5 Tests

- [ ] **Step 5: Test für das Quellenregister schreiben**

```python
# tests/test_datasources.py
import pytest

from nbs.datasources import SOURCES, Source, resolve, status


def test_every_source_carries_provenance():
    """A number that reaches a slide must be traceable to a citable source."""
    assert SOURCES, "das Register ist leer"
    for key, src in SOURCES.items():
        assert isinstance(src, Source)
        assert src.doi or src.url, f"{key}: weder DOI noch URL"
        assert src.license, f"{key}: keine Lizenz"
        assert src.citation, f"{key}: keine Zitierangabe"


def test_status_reports_every_registered_source():
    st = status()
    assert set(st) == set(SOURCES)
    assert all(v in {"vorhanden", "fehlt", "pruefsumme_falsch"} for v in st.values())


def test_resolve_returns_none_for_a_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr("nbs.datasources.RAW_DIR", tmp_path)
    assert resolve(next(iter(SOURCES))) is None


def test_unknown_source_raises_with_the_known_keys_listed():
    with pytest.raises(KeyError, match="unbekannt"):
        resolve("gibt_es_nicht")
```

- [ ] **Step 6: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_datasources.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.datasources'`

- [ ] **Step 7: Quellenregister implementieren**

```python
# src/nbs/datasources.py
"""Registry of external raster datasets, with provenance and integrity checks.

Every dataset that contributes a number to a slide is registered here with its
DOI, licence and citation, so a figure can always be traced back to what it
came from. Files live under data/raw/, which is git-ignored: nothing large is
committed, and a fresh checkout falls back to the parametrised stand-ins in
nbs.forcing until scripts/fetch_data.py has run.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


@dataclass(frozen=True)
class Source:
    key: str
    title: str
    doi: str
    url: str
    sha256: str
    """Empty string means the checksum has not been pinned yet."""
    license: str
    size_mb: float
    citation: str
    filename: str


SOURCES: dict[str, Source] = {
    "duveiller_bph": Source(
        key="duveiller_bph",
        title="Biophysical effects of vegetation cover change from satellite and models",
        doi="10.5281/zenodo.1182145",
        url="https://zenodo.org/api/records/1182145/files/LULCC-bph_LSM-vs-RS.nc/content",
        sha256="",
        license="CC-BY-4.0",
        size_mb=699.8,
        citation="Duveiller, G., Hooker, J., Cescatti, A. (2018), Sci. Data 5, 180014",
        filename="LULCC-bph_LSM-vs-RS.nc",
    ),
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve(key: str) -> Path | None:
    """Local path of a downloaded dataset, or None if it is not usable.

    Returns None both when the file is absent and when its checksum does not
    match a pinned one, so a caller can fall back without distinguishing the
    two. Use status() when the difference matters.
    """
    try:
        src = SOURCES[key]
    except KeyError:
        known = ", ".join(sorted(SOURCES))
        raise KeyError(f"Quelle {key!r} unbekannt; bekannt sind: {known}") from None

    path = RAW_DIR / src.filename
    if not path.exists():
        return None
    if src.sha256 and _sha256(path) != src.sha256:
        return None
    return path


def status() -> dict[str, str]:
    """Per source: 'vorhanden', 'fehlt' or 'pruefsumme_falsch'."""
    out: dict[str, str] = {}
    for key, src in SOURCES.items():
        path = RAW_DIR / src.filename
        if not path.exists():
            out[key] = "fehlt"
        elif src.sha256 and _sha256(path) != src.sha256:
            out[key] = "pruefsumme_falsch"
        else:
            out[key] = "vorhanden"
    return out
```

- [ ] **Step 8: Downloadskript schreiben**

```python
# scripts/fetch_data.py
"""Resolve and download the registered raster datasets into data/raw/.

Run with no arguments to see what is present and what is missing:

    uv run python scripts/fetch_data.py

Pass keys to download them:

    uv run python scripts/fetch_data.py duveiller_bph

Nothing here is required to run the model: every consumer falls back to the
parametrised stand-ins when a source is missing, and says so on the figure.
"""

from __future__ import annotations

import sys
import urllib.request

from nbs.datasources import RAW_DIR, SOURCES, status


def report() -> None:
    st = status()
    width = max(len(k) for k in SOURCES)
    for key, src in SOURCES.items():
        print(f"{key:<{width}}  {st[key]:<18}  {src.size_mb:7.1f} MB  {src.license}")
        print(f"{'':<{width}}  {src.citation}")


def download(key: str) -> None:
    src = SOURCES[key]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    target = RAW_DIR / src.filename
    print(f"lade {key} ({src.size_mb:.1f} MB) -> {target}")
    urllib.request.urlretrieve(src.url, target)  # noqa: S310
    print("fertig")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        report()
    else:
        for key in sys.argv[1:]:
            download(key)
```

- [ ] **Step 9: Tests laufen lassen und Bericht ansehen**

Run: `uv run pytest tests/test_datasources.py tests/test_grid.py -v`
Expected: PASS, 9 Tests

Run: `uv run python scripts/fetch_data.py`
Expected: eine Zeile je Quelle mit Status `fehlt`, Größe, Lizenz und Zitierangabe.

- [ ] **Step 10: Commit**

```bash
git add src/nbs/grid.py src/nbs/datasources.py scripts/fetch_data.py tests/test_grid.py tests/test_datasources.py
git commit -m "feat: add the common half-degree grid and a dataset registry

The fallback path comes first: every consumer must run without any download,
so the model stays testable offline and a missing source degrades to the
parametrised stand-ins rather than to a crash."
```

---

### Task 2: Die Albedo-Frage entscheiden

**Dies ist ein Entscheidungspunkt, keine Routineaufgabe.** Der Duveiller-Datensatz liefert ΔR_n, nicht Δα. Unsere Formel braucht Δα, weil φ_α ein kurzwelliger TOA-Antrieb ist; ΔR_n mischt kurz- und langwellig an der Oberfläche.

**Files:**
- Create: `docs/superpowers/specs/2026-09-09-albedoquelle-entscheidung.md`

- [ ] **Step 1: Die drei Wege prüfen und beziffern**

Untersuche, in dieser Reihenfolge, und halte je Weg fest, was tatsächlich verfügbar ist:

**Zwei Größen, nicht eine.** Das Produkt Δα·q̇ braucht beide Faktoren monatlich
auf demselben Gitter. Für q̇ ist noch gar keine Quelle geprüft; CERES und ERA5
verlangen beide eine Registrierung, was in einer automatisierten Pipeline
Reibung erzeugt. Der analytische Weg — TOA-Einstrahlung aus Deklination und
Breite, mal einer Klarheitsindex-Klimatologie — ist ohne Anmeldung
reproduzierbar und für einen Faktor, der ohnehin als Monatsmittel eingeht,
vertretbar. Prüfe ihn als vollwertige Option, nicht nur als Notnagel.

Für Δα, in dieser Reihenfolge:

1. **JRC-Datenportal.** Duveiller sitzt am JRC; das Albedo-Produkt zu Duveiller et al. (2018) könnte dort liegen. Durchsuche `https://data.jrc.ec.europa.eu` nach dem Datensatz zur DOI `10.1038/sdata.2018.14`. Wenn er existiert: Lizenz, Größe, zeitliche Auflösung, Variablennamen.
2. **MODIS MCD43C3** (Albedo, 0,05°, 16-tägig oder monatlich aggregierbar) kombiniert mit **MCD12C1** (Landbedeckung, IGBP). Δα ergibt sich als Differenz der Albedo zwischen Waldklassen und Offenlandklassen innerhalb derselben Klimazone. Aufwändiger, aber vollständig belegbar und monatlich.
3. **ΔR_n aus dem vorhandenen Duveiller-Datensatz** mit dokumentiertem Vorbehalt.

- [ ] **Step 2: Entscheidung schriftlich festhalten**

Schreibe `docs/superpowers/specs/2026-09-09-albedoquelle-entscheidung.md` mit: was je Weg gefunden wurde (URL, Lizenz, Auflösung, Größe), welcher gewählt wurde, warum, und was der gewählte Weg **nicht** kann.

Weg 3 ist nur zulässig, wenn 1 und 2 beide ausfallen — und dann muss im Dokument stehen, dass der Albedoterm damit langwellige Anteile enthält und die Zahlen entsprechend zu lesen sind.

- [ ] **Step 3: Dem Auftraggeber vorlegen**

**Halte hier an und lege die Entscheidung vor, bevor Task 3 beginnt.** Welche Datengrundlage die zentrale Karte des Vortrags trägt, ist eine Entscheidung des Autors, nicht der Umsetzung.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-09-09-albedoquelle-entscheidung.md
git commit -m "docs: record which albedo source the map rests on, and why"
```

---

### Task 3: Das Produkt ⟨Δα·q̇⟩ je Zelle

**Der bindende Befund aus Plan 1, Abschnitt 4.** Ein höherer Breitengrad verstärkt den Albedo-Effekt *nicht*: in der Ersatztabelle fällt |Δα|·q̇ von 14,3 bei 60°N auf 9,6 am Pol, weil die Einstrahlung schneller abnimmt als Δα zunimmt. Der reale Mechanismus ist Schneemaskierung im Frühjahr — Schnee liegt **und** die Sonne steht schon hoch. Diese Gleichzeitigkeit verschwindet beim Multiplizieren zweier Jahresmittel.

Deshalb: **monatlich multiplizieren, dann mitteln.** Niemals ⟨Δα⟩·⟨q̇⟩.

**Files:**
- Create: `src/nbs/albedo_grid.py`
- Modify: `src/nbs/forcing.py` (eine neue Funktion, bestehende bleiben unberührt)
- Test: `tests/test_albedo_grid.py`

**Interfaces:**
- Consumes: `nbs.grid`, `nbs.datasources`, `nbs.species.Species`
- Produces:
  - `nbs.albedo_grid.alpha_q_product(species_key: str, *, source: str | None = None) -> NDArray` — Form (360, 720), Einheit W/m², das jährliche Mittel des **monatlichen Produkts** Δα·q̇. Negativ, wo der Wald dunkler ist als das Offenland, das er ersetzt.
  - `nbs.albedo_grid.product_provenance() -> str` — `"raster"` oder `"fallback"`, für die Fußzeile jeder Abbildung
  - `nbs.forcing.phi_albedo_from_product(closure, alpha_q_product_w_m2: float, sp: Species) -> NDArray` — wie `phi_albedo`, aber mit dem bereits gebildeten Produkt. Bestehendes `phi_albedo` bleibt unverändert.

- [ ] **Step 1: Test schreiben — der Kern ist der Vergleich der beiden Mittelungswege**

```python
# tests/test_albedo_grid.py
import numpy as np
import pytest

from nbs.albedo_grid import alpha_q_product, product_provenance
from nbs.forcing import fallback_delta_alpha, fallback_q_sw, phi_albedo, phi_albedo_from_product
from nbs.grid import grid_lats
from nbs.species import get_species


def test_product_has_grid_shape():
    p = alpha_q_product("picea_abies")
    assert p.shape == (360, 720)


def test_product_is_negative_where_forest_is_darker():
    """Sign convention: a darker forest gives a negative delta_alpha, so the
    product is negative and the resulting forcing positive (warming)."""
    p = alpha_q_product("picea_abies")
    boreal = p[np.argmin(np.abs(grid_lats() - 60.0)), :]
    assert np.nanmean(boreal) < 0.0


def test_monthly_product_differs_from_product_of_annual_means():
    """The load-bearing property of this module.

    Spring snow masking needs albedo change and insolation to be multiplied
    month by month, because they peak together. Multiplying two annual means
    loses exactly that covariance. If these two agree, the monthly path is not
    being taken and the boreal effect is understated.
    """
    from nbs.albedo_grid import _annual_mean_of_monthly_product, _product_of_annual_means

    monthly = _annual_mean_of_monthly_product("picea_abies")
    annual = _product_of_annual_means("picea_abies")
    boreal_row = np.argmin(np.abs(grid_lats() - 60.0))
    a, b = monthly[boreal_row, :], annual[boreal_row, :]
    finite = np.isfinite(a) & np.isfinite(b)
    assert finite.any(), "keine gueltigen borealen Zellen"
    assert not np.allclose(a[finite], b[finite], rtol=1e-3)
    assert np.nanmean(np.abs(a[finite])) > np.nanmean(np.abs(b[finite]))


def test_provenance_is_reported():
    assert product_provenance() in {"raster", "fallback"}


def test_forcing_from_product_matches_the_two_argument_form():
    """phi_albedo_from_product must be the same physics, differently fed."""
    sp = get_species("picea_abies")
    closure = np.linspace(0.0, 1.0, 126)
    d_alpha, q = fallback_delta_alpha(60.0), fallback_q_sw(60.0)
    a = phi_albedo(closure, d_alpha, q, sp)
    b = phi_albedo_from_product(closure, d_alpha * q, sp)
    scale = np.abs(a).max()
    assert np.allclose(a, b, rtol=0.0, atol=1e-9 * scale)


def test_fallback_product_reproduces_the_latitude_table():
    """With no raster present the product must equal the Plan 1 stand-ins, so
    the two plans cannot silently disagree about the same latitude."""
    if product_provenance() != "fallback":
        pytest.skip("Raster vorhanden, Fallback wird nicht geprueft")
    p = alpha_q_product("picea_abies")
    row = np.argmin(np.abs(grid_lats() - 60.0))
    expected = fallback_delta_alpha(60.0) * fallback_q_sw(60.0)
    assert np.nanmean(p[row, :]) == pytest.approx(expected, rel=1e-6, abs=0)
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_albedo_grid.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.albedo_grid'`

- [ ] **Step 3: `phi_albedo_from_product` ergänzen**

An `src/nbs/forcing.py` anhängen, Importblock oben ergänzen falls nötig:

```python
def phi_albedo_from_product(closure, alpha_q_product_w_m2: float, sp: Species) -> NDArray:
    """Albedo forcing [W/m^2] from a pre-formed delta_alpha * q_sw product.

    Identical physics to phi_albedo; the difference is that the product arrives
    already formed. The grid needs this because delta_alpha and the insolation
    must be multiplied month by month before being averaged — spring snow
    masking depends on the two peaking together, and multiplying annual means
    loses that covariance. See the Plan 1 findings document, section 4.
    """
    f = np.asarray(closure, dtype=float)
    return -alpha_q_product_w_m2 * TAU_ATM * f * sp.stand_area_m2 / A_EARTH_M2
```

- [ ] **Step 4: `albedo_grid` implementieren**

Zwei Pfade, dieselbe Schnittstelle. Der Fallback muss ohne jeden Download laufen und die Breitentabelle aus Plan 1 exakt reproduzieren, damit beide Pläne für denselben Breitengrad nicht auseinanderlaufen.

Struktur:
- `_product_of_annual_means(species_key)` — der **falsche** Weg, nur damit der Test ihn vergleichen kann. Docstring muss das sagen.
- `_annual_mean_of_monthly_product(species_key)` — der richtige Weg.
- `alpha_q_product(species_key, source=None)` — wählt Raster oder Fallback, cacht das Ergebnis.
- Die Zuordnung Art → Duveiller-Übergang läuft über `Species.igbp_class`: `evergreen_needleleaf` → NedTr, `deciduous_broadleaf` → DecTr, `evergreen_broadleaf` → EvgTr. Aufforstung ist der **umgekehrte** Übergang, also das negative Vorzeichen des Codes „Wald → Gras" (Codes 11, 8, 4).
- Ausgangs-Landbedeckung ist zunächst Grasland; Ackerland als Variante vorsehen, aber nicht ausbauen.

- [ ] **Step 5: Tests laufen lassen**

Run: `uv run pytest tests/test_albedo_grid.py -v`
Expected: PASS. Schlägt `test_monthly_product_differs_from_product_of_annual_means` fehl, wird nicht monatlich multipliziert — das ist der Fehler, gegen den dieser Task existiert. Nicht die Toleranz lockern.

- [ ] **Step 6: Die beiden Wege beziffern**

Run: ein kurzes Skript, das für 45°N, 60°N und 75°N beide Mittelungswege ausgibt.
Halte die Zahlen im Bericht fest. Erwartung nach dem Plan-1-Befund: der monatliche Weg liefert bei hohen Breiten deutlich größere Beträge. Trifft das nicht zu, melde es — dann stimmt entweder die Erwartung nicht oder die Umsetzung.

- [ ] **Step 7: Commit**

```bash
git add src/nbs/albedo_grid.py src/nbs/forcing.py tests/test_albedo_grid.py
git commit -m "feat: form the albedo-insolation product monthly, not from annual means

Spring snow masking depends on albedo change and insolation peaking together.
Multiplying two annual means loses that covariance and understates the boreal
effect exactly where the argument depends on it."
```

---

### Task 4: Artzuweisung und Flächenpotenzial je Zelle

**Files:**
- Create: `src/nbs/landscape.py`
- Test: `tests/test_landscape.py`

**Interfaces:**
- Produces:
  - `nbs.landscape.assign_species() -> NDArray` — Form (360, 720), `dtype=object` oder Index-Array plus Legende; welche Art in welcher Zelle stehen kann, `None` wo keine
  - `nbs.landscape.plantable_area_m2() -> NDArray` — Aufforstungsfähige Fläche je Zelle [m²]
  - `nbs.landscape.tree_count() -> NDArray` — Bäume je Zelle, `plantable_area / stand_area_m2` der zugewiesenen Art
  - `nbs.landscape.exclusion_mask() -> dict[str, NDArray]` — je Ausschlussgrund eine boolesche Maske: `"kein_land"`, `"bestehender_wald"`, `"savanne_grasland"`, `"kryosphaere"`, `"landwirtschaft"`
  - `nbs.landscape.provenance() -> str`

Fallback ohne Raster: Breitenband-Zuordnung nach `Species.valid_gez`, Flächen je Biom aus den Veröffentlichungen hart kodiert und als solche gekennzeichnet.

- [ ] **Step 1: Test schreiben**

```python
# tests/test_landscape.py
import numpy as np
import pytest

from nbs.grid import cell_area_m2
from nbs.landscape import (
    assign_species, exclusion_mask, plantable_area_m2, provenance, tree_count,
)
from nbs.species import SPECIES


def test_shapes_match_the_grid():
    assert plantable_area_m2().shape == (360, 720)
    assert tree_count().shape == (360, 720)


def test_plantable_area_never_exceeds_the_cell():
    """An area-weighted sum that oversubscribes cells inflates every downstream
    number, and nothing later would catch it."""
    assert np.all(plantable_area_m2() <= cell_area_m2() + 1.0)


def test_plantable_area_is_non_negative():
    assert np.all(plantable_area_m2() >= 0.0)


def test_assigned_species_are_registered_ones():
    assigned = {s for s in np.unique(assign_species()) if s is not None}
    assert assigned <= set(SPECIES)


def test_no_trees_where_no_species_is_assigned():
    sp = assign_species()
    assert np.all(tree_count()[sp == None] == 0)  # noqa: E711


def test_tree_count_follows_area_and_stand_area():
    from nbs.species import get_species
    sp, area, n = assign_species(), plantable_area_m2(), tree_count()
    idx = np.argwhere(sp != None)  # noqa: E711
    assert len(idx), "keine Zelle bepflanzbar"
    i, j = idx[0]
    expected = area[i, j] / get_species(sp[i, j]).stand_area_m2
    assert n[i, j] == pytest.approx(expected, rel=1e-9, abs=0)


def test_every_exclusion_reason_is_a_boolean_grid():
    for reason, mask in exclusion_mask().items():
        assert mask.dtype == bool, reason
        assert mask.shape == (360, 720), reason


def test_excluded_cells_have_no_plantable_area():
    area = plantable_area_m2()
    for reason, mask in exclusion_mask().items():
        assert np.all(area[mask] == 0.0), f"{reason}: ausgeschlossen, aber bepflanzbar"


def test_global_plantable_area_is_plausible():
    """Bastin's headline is about 0.9 Gha before corrections. Anything far
    outside a few Gha means the mask or the units are wrong."""
    gha = plantable_area_m2().sum() / 1e4 / 1e9
    assert 0.05 < gha < 5.0, f"{gha:.2f} Gha ist ausserhalb jeder Plausibilitaet"


def test_provenance_is_reported():
    assert provenance() in {"raster", "fallback"}
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_landscape.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.landscape'`

- [ ] **Step 3: Implementieren**

Ausschlussgründe sind die Terme, die Akt 6 des Vortrags aufzählt. Jeder Grund bekommt eine eigene Maske, damit der Wasserfall in Task 7 sie einzeln beziffern kann statt nur eine Summe zu zeigen.

- [ ] **Step 4: Tests laufen lassen**

Run: `uv run pytest tests/test_landscape.py -v`
Expected: PASS, 10 Tests

- [ ] **Step 5: Commit**

```bash
git add src/nbs/landscape.py tests/test_landscape.py
git commit -m "feat: assign species and plantable area per grid cell

Each exclusion reason gets its own mask, so the potential cascade can put a
number on every correction the talk claims rather than one lumped total."
```

---

### Task 5: Aggregation — der Hebel, und sein Beweis

**Files:**
- Create: `src/nbs/aggregate.py`
- Test: `tests/test_aggregate.py`

**Interfaces:**
- Produces:
  - `nbs.aggregate.unit_curves(species_key, scenario="ssp245", config=None) -> tuple[NDArray, NDArray]` — `(delta_t_co2_per_tree, delta_t_albedo_per_unit_product)`, beide Länge 126. Die zweite ist ΔT je Baum **je Einheit** des Produkts Δα·q̇.
  - `nbs.aggregate.delta_t_per_cell(scenario="ssp245", config=None) -> NDArray` — Form (360, 720, 126) wäre 1,5 GB, daher stattdessen: `delta_t_at_year(year, ...) -> NDArray` Form (360, 720), und `delta_t_field(years_subset, ...)` für wenige Stützjahre.
  - `nbs.aggregate.global_delta_t(scenario="ssp245", config=None) -> NDArray` — Länge 126, die Summe über alle Zellen
  - `nbs.aggregate.aggregate_by_species() -> dict[str, tuple[float, float]]` — je Art `(Σ N_c, Σ N_c·P_c)`

- [ ] **Step 1: Test schreiben — der Äquivalenzbeweis ist der wichtigste**

```python
# tests/test_aggregate.py
import numpy as np
import pytest

from nbs.aggregate import aggregate_by_species, delta_t_at_year, global_delta_t, unit_curves
from nbs.constants import YEARS


@pytest.mark.slow
def test_unit_curves_have_the_study_length():
    a, b = unit_curves("picea_abies")
    assert a.shape == YEARS.shape and b.shape == YEARS.shape


@pytest.mark.slow
def test_aggregation_equals_cellwise_computation_on_a_sample():
    """The load-bearing test of this module.

    The whole grid is affordable only because everything past the tree
    trajectory is linear in tree count, so the aggregate can be formed from two
    scalars per species instead of running 259 200 cells. This test takes a
    random sample of cells, runs each one explicitly through the same unit
    curves, and checks the sum matches the aggregate. If it fails, the shortcut
    is not exact and no result on the map can be trusted.
    """
    from nbs.albedo_grid import alpha_q_product
    from nbs.landscape import assign_species, tree_count

    rng = np.random.default_rng(0)
    sp_grid, n_grid = assign_species(), tree_count()
    idx = np.argwhere((sp_grid != None) & (n_grid > 0))  # noqa: E711
    assert len(idx) > 20, "zu wenige bepflanzbare Zellen fuer die Stichprobe"
    sample = idx[rng.choice(len(idx), size=20, replace=False)]

    year_idx = -1
    explicit = 0.0
    for i, j in sample:
        key = sp_grid[i, j]
        co2, alb = unit_curves(key)
        p = alpha_q_product(key)[i, j]
        explicit += n_grid[i, j] * (co2[year_idx] + p * alb[year_idx])

    # same cells, via the aggregate route
    aggregate = 0.0
    for key in {sp_grid[i, j] for i, j in sample}:
        co2, alb = unit_curves(key)
        n_sum = sum(n_grid[i, j] for i, j in sample if sp_grid[i, j] == key)
        np_sum = sum(
            n_grid[i, j] * alpha_q_product(key)[i, j]
            for i, j in sample
            if sp_grid[i, j] == key
        )
        aggregate += n_sum * co2[year_idx] + np_sum * alb[year_idx]

    scale = abs(explicit)
    assert aggregate == pytest.approx(explicit, rel=1e-9, abs=1e-12 * scale)


@pytest.mark.slow
def test_global_delta_t_has_the_study_length_and_is_finite():
    dt = global_delta_t()
    assert dt.shape == YEARS.shape
    assert np.all(np.isfinite(dt))


@pytest.mark.slow
def test_map_has_both_signs():
    """The talk's claim is that the same measure has opposite signs in
    different places. If the map is single-signed, either the albedo product or
    the species assignment is wrong."""
    field = delta_t_at_year(2125)
    finite = field[np.isfinite(field) & (field != 0.0)]
    assert (finite < 0).any(), "keine kuehlende Zelle"
    assert (finite > 0).any(), "keine waermende Zelle"


@pytest.mark.slow
def test_species_aggregates_are_positive_counts():
    for key, (n_sum, np_sum) in aggregate_by_species().items():
        assert n_sum >= 0.0, key
        assert np.isfinite(np_sum), key
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_aggregate.py -v -m slow`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.aggregate'`

- [ ] **Step 3: Implementieren**

`unit_curves` baut auf `nbs.pipeline.run_single_tree` auf, muss aber die beiden Kanäle getrennt falten. Nutze `nbs.response.green_temperature` und `convolve_response` direkt; der Albedo-Einheitsanteil ist `convolve_response(g_T, -τ · A_s/A_⊕ · closure_s)`, also φ_α je Einheit Produkt.

Achte auf: `run_single_tree` liefert `phi_albedo` bereits mit dem Fallback-Produkt multipliziert — für `unit_curves` darf das nicht doppelt eingehen. Baue den Einheitsanteil aus `trajectory.closure` neu auf, statt `result.phi_albedo` zu teilen.

- [ ] **Step 4: Tests laufen lassen**

Run: `uv run pytest tests/test_aggregate.py -v -m slow`
Expected: PASS, 5 Tests

- [ ] **Step 5: Laufzeit prüfen**

Run: ein Skript, das `global_delta_t()` und `delta_t_at_year(2125)` zeitet.
Expected: beide deutlich unter einer Minute. Dauert es länger, wird irgendwo doch je Zelle simuliert — das ist der Fehler, gegen den der Hebel existiert.

- [ ] **Step 6: Commit**

```bash
git add src/nbs/aggregate.py tests/test_aggregate.py
git commit -m "feat: aggregate the grid exactly with two scalars per species

Everything past the tree trajectory is linear in tree count and the CO2
channel carries no location, so 259 200 cells reduce to five simulations and
ten convolutions. The equivalence test against explicit cellwise computation
is what licenses the shortcut."
```

---

### Task 6: Karte und Horizontfeld

**Files:**
- Create: `src/nbs/map_plots.py`
- Test: `tests/test_map_plots.py`

**Interfaces:**
- Produces:
  - `nbs.map_plots.plot_sign_map(year: int, out_path: str, *, scenario="ssp245") -> str` — Folie P1
  - `nbs.map_plots.footer_text() -> str` — nennt die Herkunft beider Datenschichten, wird in jede Abbildung gesetzt
  - `nbs.map_plots.plot_horizon_field(out_path: str, *, species_key, scenario="ssp245") -> str` — Folie E6: x kontinuierlicher Zeithorizont, y Breitengrad, Farbe netto ΔT, weiße Nullkontur. Die Kontur *ist* t\*(Breite).

Kartenprojektion: einfache Plattkarte genügt; keine zusätzliche Abhängigkeit wie cartopy einführen. Küstenlinien sind verzichtbar, ein Gitternetz mit Breitenbeschriftung reicht — die Aussage ist das Vorzeichenmuster, nicht die Geografie.

Jede Abbildung trägt in der Fußzeile die Herkunft (`product_provenance()` und `landscape.provenance()`), damit nie unklar ist, ob echte Raster oder Ersatztabellen dahinterstehen.

- [ ] **Step 1: Test schreiben**

```python
# tests/test_map_plots.py
import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

from nbs.map_plots import plot_horizon_field, plot_sign_map  # noqa: E402


@pytest.mark.slow
def test_sign_map_is_written(tmp_path):
    p = plot_sign_map(2125, str(tmp_path / "p1.png"))
    assert (tmp_path / "p1.png").stat().st_size > 10_000


@pytest.mark.slow
def test_horizon_field_is_written(tmp_path):
    p = plot_horizon_field(str(tmp_path / "e6.png"), species_key="picea_abies")
    assert (tmp_path / "e6.png").stat().st_size > 10_000


def test_footer_names_both_data_provenances():
    """A figure built on fallback tables must say so, or a reader will take a
    calibrated stand-in for a measurement.

    Checked on the composed footer string rather than on the rendered figure:
    the plotting helpers close their figure when they save it, so there is no
    live artist to interrogate afterwards.
    """
    from nbs.albedo_grid import product_provenance
    from nbs.landscape import provenance as landscape_provenance
    from nbs.map_plots import footer_text

    footer = footer_text()
    assert product_provenance() in footer
    assert landscape_provenance() in footer
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `uv run pytest tests/test_map_plots.py -v -m slow`
Expected: FAIL — `ModuleNotFoundError: No module named 'nbs.map_plots'`

- [ ] **Step 3: Implementieren, Step 4: Tests, Step 5: ansehen**

Nach bestandenen Tests beide Abbildungen nach `docs/slides/figures/` erzeugen und **mit den Augen prüfen**: hat die Karte beide Vorzeichen, liegt die Nullkontur des Horizontfelds dort, wo `t_star` es sagt, sind die deutschen Beschriftungen unbeschnitten. Eine Abbildung, die eine Dateigrößenprüfung besteht, kann trotzdem unlesbar sein.

- [ ] **Step 6: Commit**

```bash
git add src/nbs/map_plots.py tests/test_map_plots.py docs/slides/figures
git commit -m "feat: add the sign map and the horizon field

The horizon field's zero contour is t*(latitude) drawn directly, which is the
continuous version of the discrete break-even years the talk quotes."
```

---

### Task 7: Die Korrekturkaskade

**Files:**
- Create: `src/nbs/potential.py`
- Test: `tests/test_potential.py`

**Interfaces:**
- Produces:
  - `nbs.potential.cascade(scenario="ssp245") -> list[dict]` — geordnete Stufen, je Stufe `name_de`, `area_gha`, `carbon_gtc`, `delta_t_2150`, `note`
  - `nbs.potential.reverse_1p5(scenario="ssp245") -> dict` — nötige Baumzahl und Fläche, um 2050 unter 1,5 °C zu landen und dort zu bleiben; mit und ohne Albedo und Störung

Die Stufen folgen Akt 6 des Vortrags:

| Stufe | Wirkung |
|---|---|
| Bastin, Rohwert | 205 GtC |
| realistische C-Dichten und Bodenkohlenstoff | → etwa 81 GtC — **Achtung:** die Kette modelliert keinen Bodenkohlenstoff (Spec §4 führt ihn nicht), diese Stufe ist daher eine aus der Literatur übernommene Korrektur und **nicht** aus dem eigenen Modell gerechnet. Im Ergebnis als solche kennzeichnen. |
| Nicht-Wald-Biome ausgeschlossen | Flächenabzug |
| Albedo-Filter: Zellen mit netto ΔT > 0 am Horizont | Abzug, teils negativ |
| Störungspuffer aus dem Ensemble | Abzug mit Band |
| nutzbares Potenzial | Zahl mit Spanne |

**Alle Literaturzahlen sind vor der Übernahme gegen Originalveröffentlichung und die publizierten Kommentare zu prüfen** — die Spec markiert sie in Abschnitt 13 mit [prüfen]. Wo eine Zahl nicht belegt werden kann, wird sie im Ergebnis als unbelegt gekennzeichnet, nicht stillschweigend übernommen.

- [ ] **Step 1: Test schreiben**

```python
# tests/test_potential.py
import numpy as np
import pytest

from nbs.potential import cascade, reverse_1p5


@pytest.mark.slow
def test_cascade_is_ordered_and_labelled():
    steps = cascade()
    assert len(steps) >= 5
    for s in steps:
        assert s["name_de"] and isinstance(s["name_de"], str)
        # Slide text: no ASCII stand-ins for umlauts. One of these reached a
        # figure title in Plan 1.
        for bad in ("Stoerung", "Saettigung", "fuer", "ueber", "groesser"):
            assert bad not in s["name_de"], s["name_de"]


@pytest.mark.slow
def test_area_never_grows_along_the_cascade():
    """Every step is a correction downward. A step that increases the area
    means a sign or bookkeeping error."""
    areas = [s["area_gha"] for s in cascade() if s["area_gha"] is not None]
    assert all(b <= a + 1e-9 for a, b in zip(areas, areas[1:]))


@pytest.mark.slow
def test_final_potential_is_a_fraction_of_the_raw_claim():
    steps = cascade()
    raw, final = steps[0]["carbon_gtc"], steps[-1]["carbon_gtc"]
    assert 0.0 < final < raw


@pytest.mark.slow
def test_reverse_calculation_reports_both_variants():
    r = reverse_1p5()
    assert "mit_albedo_und_stoerung" in r and "nur_kohlenstoff" in r
    assert r["mit_albedo_und_stoerung"]["n_trees"] > r["nur_kohlenstoff"]["n_trees"]
```

- [ ] **Step 2–4: Fehlschlag bestätigen, implementieren, Tests**

- [ ] **Step 5: Zahlen gegen die Literatur prüfen**

Jede aus der Literatur übernommene Zahl im Bericht mit Quelle und geprüftem Wert auflisten. Wo Originalveröffentlichung und Kommentare voneinander abweichen, beide nennen.

- [ ] **Step 6: Commit**

```bash
git add src/nbs/potential.py tests/test_potential.py
git commit -m "feat: compute the Bastin correction cascade from the model

Every step is a term the talk derives, so the criticism of the field's most
cited tree-planting paper is line by line the list of what carbon-only
accounting leaves out."
```

---

### Task 8: Notebook und Dokumentation

**Files:**
- Create: `notebooks/03_potenzial_global.ipynb`
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-09-09-befunde-fuer-plan-2-und-3.md` (Befunde aus diesem Plan ergänzen)

Das Notebook fährt die Kette einmal durch: Quellenstatus, Produktbildung mit dem Vergleich der beiden Mittelungswege, Karte, Horizontfeld, Kaskade, Umkehrrechnung. Prosa auf Deutsch mit echten Umlauten.

**Ehrlichkeitsgebot:** Wo der Fallback-Pfad läuft, muss das Notebook es an der Stelle sagen, an der die Zahl entsteht — nicht nur einmal am Anfang. In Plan 1 stand ein Zirkelschluss in einer Überschrift, weil das versäumt wurde.

- [ ] **Step 1–4: Notebook bauen, ausführen, Abbildungen ansehen, README ergänzen**

- [ ] **Step 5: Volle Suite**

Run: `uv run pytest -q -m "not slow"` und die langsamen Tests der neuen Module.
Expected: keine Regression gegen 202 passed / 55 deselected.

- [ ] **Step 6: Commit**

---

## Was dieser Plan bewusst offen lässt

- **Die Albedoquelle** ist bis Task 2 nicht entschieden. Fällt sie auf ΔR_n zurück, enthält der Albedoterm langwellige Anteile, und jede Zahl der Karte ist entsprechend zu lesen.
- **Kein Erdsystemmodell.** Bei kontinentaler Aufforstung verschiebt sich Λ, und die Emulator-Näherung trägt nicht mehr. Für die Kaskade, die genau solche Flächen betrachtet, ist das als Grenze zu benennen — nicht zu beheben.
- **Ausgangs-Landbedeckung ist Grasland.** Ackerland als Variante ist vorgesehen, aber nicht ausgebaut.
- **Der pptx-Umbau** ist Plan 3.
