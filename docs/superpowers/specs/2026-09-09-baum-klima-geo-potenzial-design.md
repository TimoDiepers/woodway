# Vom einzelnen Baum zur Weltkarte — Design

**Datum:** 2026-09-09
**Status:** Entwurf zur Freigabe
**Zweck:** Die Studienrechnungen unter `src/nbs/` auf die Physik-Kette des
Dissertationsvortrags (`docs/slides/dissvortrag.pptx`) umstellen, um
artenspezifische, geografisch und zeitlich aufgelöste Ergebnisse erweitern und
die Abschnitte „Ergebnisse" und „Potential" der Präsentation daraus füllen.

---

## 1. Ausgangslage

Die Präsentation ist neuer als der Code und hat die Modellstruktur bereits
weiterentwickelt. Sie ist die maßgebliche Referenz. Die Divergenzen:

| Thema | pptx (maßgeblich) | `src/nbs/` (Stand heute) |
|---|---|---|
| Bezugseinheit | **ein Baum**: m in kgC, Standfläche A_Baum ≈ 5 m² (≈ 2000 Bäume/ha) | Hektar bzw. Mha, CO₂-Puls in GtCO₂ |
| Albedo-Antrieb | hergeleitet: φ_α = −Δα · q̇_kurz · τ · f(t) · A_Baum/A_Erde, Bedeckungsgrad f(t) an das Wachstum gekoppelt | feste ΔF_α-Tabelle je Intervention und Breitengrad, lineare 3-Jahres-Rampe, vom Wachstum entkoppelt |
| Evapotranspiration | **kein Term in φ** — überquert die TOA-Grenze nicht, wirkt über Λ (Folie 18) | `et_module.py` liefert ΔF_ET als Antrieb — direkter Widerspruch |
| Störung | ṁ_Stör = p_Stör · m(t), als Risiko gerahmt | deterministischer Abzug mit linear steigender Rate |
| Gliederung | narrative Akte, Zerlegung von φ in zwei Kanäle | „Komplexitätslevel 0–6" plus Zertifikats-Rahmung |
| Baumarten | im Vortrag angelegt, nicht ausgeführt | nicht vorhanden |
| Geodaten | „die Antwort ist eine Karte" (Akt 8) | nur Breitenbänder 0/15/30/45/60°N |
| Potenzial | Akt 6: Bastin-Kritik, 205 → ~81 GtC, ~25 % boreal/Tundra | nicht vorhanden |

Zusätzlich ist der Bestand intern inkonsistent: `notebooks/01_energy_balance_and_carbon_credits.ipynb`
bezeichnet Level 4 als Evapotranspiration, `README.md` bezeichnet Level 4 als
„Shrinking Sink".

Umgekehrt enthält der Code Material, das im Vortrag fehlt und erhalten bleiben
soll: das Äquivalenzverhältnis, die Warming-Debt-Metrik, die Sobol-Analyse und
den Vergleich mit BECCS und vermiedener Entwaldung. Dieses Material wandert in
`legacy/` und speist Backup-Folien.

## 2. Getroffene Entscheidungen

| Frage | Entscheidung |
|---|---|
| Geodaten-Tiefe | echte globale Raster, gemeinsames 0,5°-Gitter |
| Artenset | fünf Arten, je Biom eine |
| Störungsrisiko | Monte-Carlo-Ensemble, Darstellung als Fächer |
| pptx-Umfang | Ergebnisse und Potential neu, zusätzlich Herleitungsfolien zahlenmäßig an den Code angleichen |
| Rechenkern | Faltung mit Impulsantworten statt wiederholter FaIR-Läufe |

## 3. Architektur

```
src/nbs/
  species.py      fünf Arten als eingefrorene Parametersätze
  tree.py         Wachstum, Kronenschluss, Störungspfade — je Baum
  forcing.py      φ_CO₂ und φ_α aus den Baumgrößen
  response.py     Impulsantworten g_C, g_T aus FaIR; Faltung
  fair_module.py  Basislauf, Pulsexperimente, Validierung (bestehend)
  grid.py         Rasterdaten, Artzuweisung, Aggregation über Zellen
  potential.py    Korrekturkaskade auf das Flächenpotenzial
  metrics.py      t*, Risikoprämie, Horizontfeld, Wasserfallzahlen
  plots.py        Abbildungen für den Vortrag
  legacy/         bisherige Module, Tests laufen unverändert weiter
scripts/
  fetch_data.py         Quellenregister auflösen, prüfen, cachen
  build_grid.py         Rohraster auf das 0,5°-Gitter bringen
  make_slide_figures.py Abbildungen nach docs/slides/figures/
  update_pptx.py        Folien schreiben, mit Sicherung
data/
  raw/        (gitignored)
  processed/  grid_0p5deg.nc
notebooks/
  01_einzelbaum.ipynb  02_arten_standorte.ipynb  03_potenzial_global.ipynb
  archiv/     die beiden bisherigen Notebooks
```

Jedes neue Modul hat eine Aufgabe und eine schmale Schnittstelle: `tree.py`
kennt keine Raster, `grid.py` kennt keine Klimaphysik, `response.py` kennt
weder Bäume noch Orte.

## 4. Physikkern

### 4.1 Wachstum in Bestandsform

Chapman-Richards in geschlossener Form beschreibt einen ungestörten Baum:

```
m(t) = m_max · (1 − e^(−k t))^p        [kgC je Baum]
```

Für gestörte Bestände wird die Ableitung in Bestandskoordinaten gebraucht.
Mit u = (m/m_max)^(1/p) folgt e^(−kt) = 1 − u und damit

```
dm/dt = k · p · m_max · u^(p−1) · (1 − u)
```

Diese Form hängt nur von m ab, nicht von t. Ein Baum, der die Hälfte seines
Vorrats verloren hat, wächst dadurch mit der Rate weiter, die zu seinem
verbliebenen Vorrat gehört — was mit der geschlossenen Form nicht darstellbar
wäre. Der ungestörte Fall muss die geschlossene Lösung reproduzieren; das ist
ein Test.

### 4.2 Kronenschluss

```
f(t) = min(1, (m(t)/m_max)^β)
```

Startwert β = 0,5, also Kronenschluss schneller als Vorratsaufbau — ein Baum
beschattet seine Standfläche, lange bevor er ausgewachsen ist. β geht in die
Sensitivitätsanalyse ein, weil es unmittelbar steuert, wie früh die
Albedo-Strafe voll wirkt.

f koppelt die Albedo-Wirkung an den Wachstumsstand: ein junger Baum verdunkelt
die Fläche noch nicht, ein abgebrannter Bestand verdunkelt sie wieder weniger.

### 4.3 Antrieb

```
ṁ_CO₂(t) = −(44/12) · ṁ(t)                                [kg CO₂ / a]
Δm_CO₂(t) = ∫₀ᵗ g_C(t−t′) · ṁ_CO₂(t′) dt′                  [kg CO₂]
φ_CO₂(t)  = A_CO₂ · Δm_CO₂(t)                              [W/m²]  — kein Flächenterm
φ_α(t)    = −Δα · q̇_kurz · τ · f(t) · A_Baum/A_Erde        [W/m²]
φ(t)      = φ_CO₂(t) + φ_α(t)
```

Vorzeichen: Wald ist dunkler als die offene Fläche, also Δα < 0 und φ_α > 0
(Erwärmung). Evapotranspiration erscheint nicht — sie überquert die
Bilanzgrenze am Oberrand der Atmosphäre nicht und steckt im
Rückkopplungsparameter Λ. Folie 18 begründet das im Vortrag bereits; der Code
folgt dieser Grenzziehung, statt ihr zu widersprechen.

### 4.4 Temperatur über Faltung

```
ΔT(t) = ∫₀ᵗ g_T(t−t′) · φ(t′) dt′
```

g_T und g_C werden **einmal** aus FaIR gewonnen — als Differenz zwischen einem
Puls-Lauf und dem Basislauf desselben SSP-Szenarios. Danach sind Ensembles und
globale Raster reine Numerik. Das ist zugleich exakt die Gleichung auf
Folie 24: der Code rechnet sichtbar das, was im Vortrag hergeleitet wurde.

**Verifikation:** Für mindestens drei Konfigurationen (tropisch, gemäßigt,
boreal) wird die Faltung gegen einen vollen FaIR-Lauf mit demselben Antrieb
geprüft. Die zulässige Abweichung wird als Test festgeschrieben; wird sie
überschritten, ist die Linearitätsannahme verletzt und muss in den Grenzen der
Studie stehen.

## 5. Baumarten

Fünf Arten, je Biom eine, als eingefrorene Datensätze in `species.py`:

| Art | Rolle | IGBP-Klasse für Δα-Lookup |
|---|---|---|
| *Picea abies* | boreal, Nadelbaum immergrün | evergreen needleleaf |
| *Pinus sylvestris* | gemäßigt, Nadelbaum immergrün | evergreen needleleaf |
| *Fagus sylvatica* | gemäßigt, Laubbaum sommergrün | deciduous broadleaf |
| *Eucalyptus grandis* | subtropische Plantage | evergreen broadleaf |
| tropischer Mischbestand | tropisch immergrün | evergreen broadleaf |

Felder je Art: `m_max_kgC`, `k`, `p`, `beta_closure`, `stand_area_m2`,
`alpha_canopy`, `igbp_class`, `p_disturb`, `severity_beta`, `gamma_warming`,
`eps_immediate`, `tau_decay_yr`, `valid_gez`, plus Quellenangabe je Parameter. Die Parameterwerte stammen aus Ertragstafeln und dem IPCC-2019-Refinement
und werden vor der Übernahme auf die Folien geprüft.

## 6. Datenschicht

Gemeinsames Gitter: **0,5°**, 720 × 360, gecacht als
`data/processed/grid_0p5deg.nc`. `scripts/fetch_data.py` führt ein
Quellenregister mit DOI, URL, Prüfsumme und Lizenz und meldet für jede Schicht,
ob die Primärquelle aufgelöst werden konnte.

| Schicht | Primärquelle | Fallback |
|---|---|---|
| Δα Wald ↔ offenes Land, je Übergang | Duveiller et al. 2018, Sci Data, 0,05° | Δα(Breite, Schnee) nach Bonan 2008 |
| q̇_kurz an der Oberfläche | CERES EBAF-Surface bzw. ERA5 | analytische TOA-Einstrahlung × Klarheitsindex-Klimatologie |
| Aufforstungspotenzial | Bastin et al. 2019, 1 km; Walker et al. 2022 als Zweitschätzung | Flächen je Biom aus den Veröffentlichungen |
| Landbedeckung, Ausgangszustand und Ausschluss | ESA CCI LC bzw. MODIS MCD12C1 IGBP | Olson-Ökoregionen als Biomkarte |
| Wachstumsparameter je Zone | IPCC 2019 Refinement × FAO Global Ecological Zones | Literaturtabelle je Art |

Duveiller liefert Δα **je Landbedeckungsübergang**. Damit hängt die
Albedo-Änderung sowohl am Ort als auch an der gepflanzten Art — genau die
Kopplung, die die Karte in Akt 6 trägt.

**Reihenfolge:** Das Auflösen und Prüfen der Quellen läuft, bevor irgendeine
Rechnung darauf aufsetzt. Schichten, die auf den Fallback zurückfallen, werden
in der Fußzeile der betroffenen Folie als solche gekennzeichnet.

## 7. Störung als Risiko

Ereignismodell je Jahr und Baum:

- Eintritt: Bernoulli mit `p_Stör(t) = p₀ · exp(γ · T_hintergrund(t))`.
  T_hintergrund stammt aus dem SSP-Basislauf — das Risiko steigt mit der
  Erwärmung, statt einem gesetzten linearen Trend zu folgen.
- Schwere: Verlustanteil `s ~ Beta(a, b)` des stehenden Vorrats, je Art
  parametriert (`severity_beta`).
- Verbleib des Kohlenstoffs: Anteil ε sofort freigesetzt (Verbrennung), der
  Rest zerfällt mit Zeitkonstante τ_dec. Beides geht als positiver ṁ_CO₂
  zurück in die Bilanz. Startwerte: γ in der Größenordnung 0,1–0,3 K⁻¹ nach
  Seidl et al. 2017, ε ≈ 0,3 für Feuer und deutlich kleiner für Sturm und
  Käfer, τ_dec ≈ 10–30 a je nach Klimazone. Alle drei sind Artparameter, keine
  globalen Konstanten, und gehen in die Sensitivitätsanalyse ein.
- Rückwirkung auf die Albedo: f(t) fällt mit m, die Verdunklung geht teilweise
  zurück. Beide Kanäle bleiben ohne Zusatzannahme gekoppelt.

Ensemblegröße 1000 je Standort und Art. Ausgaben:

- Median und 5–95 %-Band von ΔT(t)
- P(ΔT > 0 im Jahr 2100)
- **Risikoprämie**: Differenz zwischen dem Erwartungswert des Ensembles und dem
  deterministischen Lauf. Der deterministische Lauf überschätzt die Wirkung
  systematisch; diese Differenz beziffert, um wie viel.

## 8. Potenzial und Hochskalierung

Je Gitterzelle: Art nach ökologischer Zone zugewiesen, Fläche aus der
Potenzialkarte, Baumzahl = Zellfläche / A_Baum. Die φ-Beiträge aller Zellen
werden aufsummiert; **eine** Faltung liefert das globale ΔT.

Korrekturkaskade, jeder Schritt aus einem im Vortrag hergeleiteten Term:

| Schritt | Wirkung |
|---|---|
| Bastin, Rohwert | 205 GtC |
| realistische Kohlenstoffdichten und Bodenkohlenstoff | → etwa 81 GtC |
| Nicht-Wald-Biome ausgeschlossen (Savanne, Grasland) | Flächenabzug |
| Albedo-Filter: Zellen mit netto ΔT > 0 am Horizont | Abzug, teils negativer Beitrag |
| Störungspuffer aus dem Ensemble | Abzug mit Unsicherheitsband |
| **nutzbares Potenzial** | Zahl mit Spanne |

Alle Bastin-Zahlen werden gegen Originalveröffentlichung und die publizierten
Kommentare geprüft, bevor sie auf eine Folie kommen. Das Strukturdokument
markiert sie bereits mit **[prüfen]**.

Umkehrrechnung für die Schlussfolie: welcher Baumbestand nötig wäre, um 2050
bei 1,5 °C zu landen und darunter zu bleiben — gerechnet mit und ohne Albedo
und Störung, gestellt neben die verfügbare Fläche.

## 9. Metriken

| Metrik | Definition |
|---|---|
| ΔT(t) | Nettotemperaturwirkung, zerlegt nach Kanal |
| t* | Jahr, ab dem ΔT dauerhaft negativ bleibt; ∞, wenn das nie eintritt |
| Horizontfeld | ΔT als Funktion von Zeithorizont und Breitengrad, Nullkontur eingezeichnet |
| Risikoprämie | Erwartungswert des Ensembles minus deterministischer Lauf |
| Glühbirnen-Zahl | dauerhaft zusätzlich absorbierte Leistung je Baum [W], Anker von Folie 14 |
| nutzbares Potenzial | Endzahl der Kaskade, mit Spanne |

## 10. Umbau der Präsentation

### 10.1 Technische Regeln

- `docs/slides/~$dissvortrag.pptx` ist PowerPoints Sperrdatei. Ist die Datei
  geöffnet, überschreibt PowerPoint beim Speichern jede Änderung. Vor dem
  ersten Schreibzugriff prüfen und den Nutzer gegebenenfalls bitten, sie zu
  schließen.
- Vor jedem Schreibschritt Sicherung nach
  `docs/slides/workspace/dissvortrag_pre_<schritt>_<zeitstempel>.pptx`.
- Formeln als LaTeX-Text. Kein handgeschriebenes OMML — das hat in der
  Vergangenheit das Speichern der Datei zerstört.
- Abbildungen als PNG mit 300 dpi nach `docs/slides/figures/`, eingefügt über
  python-pptx.

### 10.2 Neue Folien — Ergebnisse

| | Inhalt |
|---|---|
| E1 | Aufbau: Arten, Standorte, Szenario, Ausgangsvegetation, Zeithorizont |
| E2 | Ein Baum an einem Ort: m(t), ṁ_CO₂(t), Δα·f(t) als Eingangsgrößen |
| **E3** | Zweizeilig: oben φ(t) zerlegt in φ_CO₂ und φ_α, unten ΔT(t) zerlegt. Kernfolie — zeigt, dass ΔT die verzögerte, geglättete Fassung von φ ist |
| E4 | Störungsfächer: Median, 5–95 %-Band, P(ΔT > 0), Risikoprämie |
| E5 | Fünf Arten an ihren Standorten: Vorzeichenwechsel mit dem Breitengrad |
| E6 | Horizontfeld: x kontinuierlicher Zeithorizont, y Breitengrad, Farbe netto ΔT, weiße Nullkontur — die Kontur *ist* t*(Breite) |
| E7 | Externe Bestätigung: Hasler et al. 2024, 172 Projekte des freiwilligen Marktes |

### 10.3 Neue Folien — Potential

| | Inhalt |
|---|---|
| P1 | Weltkarte: Vorzeichen von ΔT nach 100 Jahren |
| P2 | Bastin-Wasserfall, gerechnet |
| P3 | Nutzbare Obergrenze mit Unsicherheitsband |
| P4 | Umkehrrechnung 1,5 °C: nötige Bäume gegen verfügbare Fläche |

### 10.4 Angleichung der Herleitungsfolien

Folien 12, 14 und 22 tragen Zahlenwerte, die heute unabhängig vom Code gesetzt
sind: m_max, k, p, p_Stör, A_Baum, Δα, q̇_kurz, τ und die 70-Watt-Glühbirne.
Diese Werte werden aus `species.py` und der Datenschicht übernommen, damit
Herleitung und Ergebnis dieselben Zahlen zeigen.

### 10.5 Diskrete Zeithorizonte

Feste Horizonte (20/50/100 Jahre, GWP100) erscheinen nur dort, wo
Bilanzierungsstandards sie erzwingen — als Backup-Folie, nicht im Hauptstrang.
Der Hauptstrang zeigt durchgehende Kurven und das kontinuierliche Horizontfeld.

## 11. Migration

Nichts wird gelöscht. `carbon_module`, `albedo_module`, `et_module`,
`credit_analysis`, `credit_figures`, `scenario_runner`, `sensitivity`,
`figures` und `parameters` wandern nach `src/nbs/legacy/`, ihre Tests laufen
unverändert weiter. Äquivalenzverhältnis, Warming Debt, Sobol-Indizes und der
Vergleich mit BECCS und vermiedener Entwaldung bleiben damit verfügbar und
liefern Material für Backup-Folien.

`et_module` bleibt erhalten, wird aber ausdrücklich als **nicht Teil von φ**
dokumentiert — mit Verweis auf die Begründung in Folie 18.

Die bestehenden Notebooks wandern nach `notebooks/archiv/`.

## 12. Tests und Verifikation

Neue Module nach testgetriebener Entwicklung. Mindestens:

- Bestandsform des Wachstums reproduziert die geschlossene Lösung im
  ungestörten Fall
- Störung reduziert den Vorrat, das anschließende Wachstum setzt am Restvorrat
  an, der Kohlenstoff erscheint in der Atmosphärenbilanz wieder
- Faltung gegen vollen FaIR-Lauf, drei Konfigurationen, festgeschriebene
  Toleranz
- Vorzeichenkonventionen: boreale Aufforstung erzeugt φ_α > 0, tropische ein
  betragsmäßig kleineres φ_α
- Rasterpipeline: Flächensumme bleibt beim Resampling erhalten, keine
  stillschweigend verworfenen Zellen
- Fallback-Pfad der Datenschicht liefert lauffähige Ergebnisse ohne Netzzugang

## 13. Zu prüfen vor Übernahme auf Folien

- Bastin-Zahlen 205 GtC, ~81 GtC, ~72–100 GtC, ~25 % Tundra/boreal — gegen
  Originalveröffentlichung und Kommentare
- Hasler et al. 2024: die Anteile von 10 %, einem Viertel und 9 %
- Auflösbarkeit jeder Primärdatenquelle, sonst dokumentierter Fallback
- Artparameter gegen Ertragstafeln und IPCC-2019-Refinement
- Gültigkeit der Linearitätsannahme für die Faltung bei globaler Aufforstung —
  bei sehr großen Flächen ist sie zu prüfen und gegebenenfalls als Grenze der
  Studie zu benennen

## 14. Nicht im Umfang

- Evapotranspiration als Antriebsterm — durch die Wahl der Systemgrenze
  ausgeschlossen, im Vortrag begründet
- Erdsystemmodell statt Emulator — die Frage betrifft globale Mitteltemperatur
  über Jahrhunderte an vielen Standorten, das Regime, für das Emulatoren gebaut
  sind
- BVOC, N₂O- und CH₄-Flüsse, indirekte Landnutzungsänderung
- Neugestaltung des Herleitungsteils der Präsentation über die Angleichung der
  Zahlenwerte hinaus
