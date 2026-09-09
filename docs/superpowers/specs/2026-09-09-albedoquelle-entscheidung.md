# Albedoquelle für die Rasterschicht — Entscheidungsvorlage

**Datum:** 2026-09-09
**Kontext:** Plan 2, Task 2. Reine Recherche und Entscheidungsvorlage, keine
Umsetzung. Vollständiges Rechercheprotokoll (HTTP-Status, exakte Antworten):
`.superpowers/sdd/2026-09-09-rasterschicht-und-potenzial/task-2-report.md`.

## Worum es geht

φ_α = −Δα · q̇_sw · τ · f(t) · A_Baum / A_Erde braucht zwei Felder pro
Gitterzelle, **beide monatlich**, die **Monat für Monat multipliziert und
danach gemittelt** werden müssen — nicht umgekehrt. Grund (Befund aus Plan 1,
Abschnitt 4 der Vorgänger-Spec): Der boreale Albedo-Effekt entsteht durch
Schneemaskierung im Frühjahr, wenn Schnee liegt *und* die Sonne schon hoch
steht. Diese Gleichzeitigkeit geht verloren, wenn man zwei Jahresmittel
multipliziert.

- **Δα** — Albedoänderung durch Umwandlung von Offenland (Grasland) in Wald,
  je Waldtyp
- **q̇_sw** — kurzwellige Einstrahlung an der Oberfläche

## Δα — Kandidat 1: JRC-Datenportal (Duveiller et al. 2018, Version 2)

**Gefunden.** Der Weg dorthin: Die Zenodo-Volltextsuche nach "duveiller
albedo" führte zu einem Code-Repository (10.5281/zenodo.4293904), dessen
Beschreibung explizit auf den daraus erzeugten Datensatz verweist — eine
**Version 2** des Duveiller-Datensatzes, veröffentlicht über eine
JRC-eigene DOI (10.2905-Präfix), die die Zenodo-Version (10.5281/zenodo.1182145)
laut Landing Page vollständig ersetzt ("this version 2 ... entirely
supersedes version 1").

- **URL/DOI:** `10.2905/F97E4216-E81C-4DFB-B42D-D0C19070D029`, Landing Page
  `https://data.jrc.ec.europa.eu/dataset/f97e4216-e81c-4dfb-b42d-d0c19070d029`.
  Direkter Datei-Zugriff: `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/ECOCLIM/Biophysical-effects-vgt-change/v2.0/`
  (nur über HTTPS erreichbar, HTTP liefert Fehler 500).
- **Lizenz:** CC BY 4.0 (per `copyright.txt` im selben Verzeichnis).
- **Zugang:** ohne Registrierung, ohne Anmeldung, direkter Download.
- **Format/Größe:** HDF5-basiertes netCDF4, pro Variable eine eigene Datei.
  `albedo_IGBPgen_ext.nc` (6,0 MB) und `albedo_IGBPdet_ext.nc` (14,4 MB)
  wurden vollständig geladen und geöffnet.
- **Räumliche Auflösung:** 1° × 1° (nicht 0,5° — muss auf das Zielgitter
  interpoliert/verdoppelt werden).
- **Zeitliche Auflösung:** monatlich (`mon`-Dimension, 12 Werte), keine
  Jahresdimension — es ist bereits eine über den Beobachtungszeitraum
  gemittelte Monatsklimatologie.
- **Variablen:** `Delta_albedo` (Rohdaten aus Satellitenbeobachtung),
  `Delta_albedo_ext` (räumlich per ML-Verfahren gefüllte Version),
  `SD_Delta_albedo`, `N_Delta_albedo`. Dimensionen `iTr, mon, lat, lon`.
- **Transitionscodes:** Die "IGBPdet"-Datei hat 45 Codes für alle Paare aus
  10 Klassen (`12,13,...,910`). Aus der Anzahl und der Standard-IGBP-Reihenfolge
  lässt sich ableiten: 1 EvgNeedle, 2 EvgBroad, 3 DecNeedle, 4 DecBroad,
  5 MixedForest, 6 ClosedShrub, 7 OpenShrub, 8 WoodySavanna, 9 Savanna,
  10 Grassland. **Wichtig: Diese Zuordnung steht nirgends als Legende im
  NetCDF selbst** — sie ist aus der Struktur erschlossen, nicht gegen eine
  Dokumentationsquelle verifiziert. Vor produktivem Einsatz sollte sie anhand
  der MCD12C1-IGBP-Nomenklatur oder der Methodik-Sektion des Papers
  bestätigt werden.
- **Der entscheidende Befund — Datenlücken:** Die Abdeckung ist dünn (nur
  ca. 1–3 % der Gitterzellen global belegt, auch in der ML-erweiterten
  Version), weil der Datensatz auf tatsächlich beobachteten
  Landbedeckungsübergängen beruht, nicht auf einer flächendeckenden Modellierung.
  Für die Transition EvgNeedle→Grassland (Code 110, der für *Picea abies* am
  nächsten läge) gibt es **im gesamten Breitenband 55–65°N in keinem Monat
  einen einzigen gültigen Wert**, auch nicht in der erweiterten Version. Für
  die vier verwandten Übergänge (EvgBroad→Grass, DecNeedle→Grass,
  DecBroad→Grass, MixedForest→Grass) gibt es dort dagegen Daten, mit
  physikalisch plausiblem Jahresgang (groß im Winter, ~0 im Sommer — siehe
  Rechercheprotokoll für die Zahlen). Für einen borealen Nadelwald wie
  *Picea abies* würde man also auf einen Proxy ausweichen müssen (z. B.
  MixedForest→Grass oder DecNeedle→Grass), was eine dokumentationspflichtige
  Modellannahme ist, keine direkte Messung für genau diesen Waldtyp.

## Δα — Kandidat 2: MODIS MCD43C3 + MCD12C1

- **MCD43C3** (jetzt als "MODIS/Terra+Aqua BRDF/Albedo Albedo Daily L3
  Global 0.05Deg CMG V061" geführt, CMR-ID `C2532068039-LPCLOUD`) — Albedo,
  0,05°, täglich, auf Monatsmittel aggregierbar.
- **MCD12C1** ("MODIS/Terra+Aqua Land Cover Type Yearly L3 Global 0.05Deg
  CMG V061", CMR-ID `C2484078896-LPCLOUD`) — IGBP-Landbedeckung, jährlich,
  0,05°.
- **Zugang:** Ein direkter Downloadversuch auf eine konkrete Granule
  (`https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/...hdf`)
  ergab **HTTP 401, "HTTP Basic: Access denied."** — bestätigt: Zugriff
  erfordert einen kostenlosen NASA-Earthdata-Login (Registrierung bei
  `urs.earthdata.nasa.gov`) und damit Zugangsdaten/Token in jeder
  automatisierten Pipeline.
- **Was hier fehlt, das der JRC-Datensatz schon liefert:** MODIS liefert nur
  Rohreflektanz/Albedo und Landbedeckungsklassen — **kein fertiges Δα**. Δα
  müsste selbst konstruiert werden: Wald- und Offenland-Pixel innerhalb
  derselben Klimazone identifizieren (z. B. über Köppen-Klassen oder
  räumliche Nachbarschaft), statistisch die Albedo-Differenz bilden, das für
  jeden Monat und jeden Waldtyp wiederholen. Das ist eine eigenständige
  Datenverarbeitungs-Pipeline, kein Download.
- **Vorteil gegenüber JRC:** flächendeckend (0,05°, kein Beobachtungslücken-
  Problem wie bei Duveiller, weil man nicht auf tatsächlich stattgefundene
  Landnutzungsübergänge angewiesen ist, sondern jede Pixel-Kombination bilden
  kann) und feiner aufgelöst.

## Δα — Kandidat 3: ΔR_n aus dem bereits erschlossenen Zenodo-Datensatz

Bereits aus Plan 1 bekannt (10.5281/zenodo.1182145, 699,8 MB, CC-BY-4.0,
klassisches netCDF, `Longitude, Latitude, Month, Transition, Source`).
Enthält ΔLE, Δ(H+G), ΔR_n — **kein Δα**. ΔR_n mischt kurz- und langwellige
Strahlung an der Oberfläche; φ_α ist aber ein reiner kurzwelliger
TOA-Antrieb. Nur zulässig, wenn Kandidat 1 und 2 beide ausfallen — was hier
nicht der Fall ist, da Kandidat 1 tatsächlich Δα liefert.

## q̇_sw — Kandidat 1: CERES EBAF-Surface

- CMR-Suche findet `C3880496704-LARC_CLOUD`, "CERES Energy Balanced and
  Filled (EBAF) TOA and Surface Monthly means ... Edition 4.2.1". Eine
  einzige Datei deckt den gesamten Zeitraum 2000.03–2025.12 ab.
- **Zugang:** Direkter Downloadversuch auf die Granule ergab **HTTP 401,
  "HTTP Basic: Access denied."** — dasselbe Muster wie MODIS. Erfordert
  NASA-Earthdata-Login.
- Auflösung (1°×1°, monatlich) ist nur aus der öffentlich dokumentierten
  Produktbeschreibung bekannt, nicht selbst per Header-Peek verifiziert
  (der 401 verhindert das).

## q̇_sw — Kandidat 2: ERA5 / Copernicus CDS

- `reanalysis-era5-single-levels-monthly-means` — Variable "Surface solar
  radiation downwards" bestätigt vorhanden. Reanalyse-Gitter **0,25° × 0,25°**
  (Zitat von der CDS-Seite: "Data has been regridded to a regular lat-lon
  grid of 0.25 degrees for the reanalysis").
- **Zugang:** Die Seite verlangt sichtbar "Sign in" und Zustimmung zu
  "Terms of Use" / "Licence". Für die CDS-API ist ein kostenloses
  ECMWF/Copernicus-Konto mit persönlichem API-Token nötig — Reibung in einer
  automatisierten Pipeline, wie im Auftrag vermutet.

## q̇_sw — Kandidat 3: analytischer Weg, konkret über NASA POWER

Der Auftrag verlangt, den analytischen Weg (TOA-Einstrahlung aus Deklination
und Breite, mal Klarheitsindex-Klimatologie) als vollwertige Option zu
prüfen, nicht nur als Notnagel. Statt die Klarheitsindex-Klimatologie selbst
aus Grund auf zu bauen, wurde geprüft, ob es eine fertige, freie Quelle für
genau diese Größe gibt — und es gibt eine:

- **NASA POWER Climatology API**
  (`https://power.larc.nasa.gov/api/temporal/climatology/...`). Liefert
  `ALLSKY_SFC_SW_DWN` — die tatsächliche (wolkenbehaftete) kurzwellige
  Einstrahlung an der Oberfläche als 20-Jahres-Monatsklimatologie
  (2001–2020), abgeleitet aus CERES SYN1deg, FLASHFlux und SRB.
- **Zugang:** getestet ohne jede Anmeldung — HTTP 200, sofortige Antwort in
  JSON. Kein API-Key, kein Login.
- **Auflösung:** laut Methodikseite 1° × 1° für die Strahlungsprodukte
  (dieselbe Quellauflösung wie CERES SYN1deg, da direkt daraus abgeleitet).
  Auch hier: Interpolation auf 0,5° nötig, genau wie beim JRC-Δα — die beiden
  Felder landen damit auf vergleichbarer nativer Auflösung.
- **Format:** JSON, CSV, ASCII, NetCDF laut Dokumentation.
- **Limit:** Regionale Abfragen sind auf 10°×10°-Kacheln begrenzt (getestet:
  eine globale Abfrage schlägt mit HTTP 422 fehl, Fehlermeldung nennt das
  Limit explizit). Für eine globale Abdeckung braucht es 36×18 = 648
  Einzelabfragen — reine Fleißarbeit, keine grundsätzliche Hürde.
- **Was diese Variante nicht kann:** Es ist kein rein first-principles
  analytisches Modell (Deklination × Breite × Klarheitsindex-Formel), sondern
  eine vorprozessierte, auf realer Satellitenbeobachtung beruhende
  Klimatologie. Das ist inhaltlich **besser** als eine selbstgebaute
  Klarheitsindex-Näherung (reale Bewölkungsmuster statt einer
  Pauschalannahme), aber es ist damit kein Weg mehr, der komplett ohne
  externe Datenquelle auskommt — es hängt weiterhin von der Verfügbarkeit
  des POWER-Dienstes ab, nur eben ohne Zugangsschranke.

Ein rein first-principles-analytischer Fallback (TOA-Einstrahlung aus
Deklination und Breite, multipliziert mit einer selbst angesetzten
Klarheitsindex-Konstante oder -Tabelle) bliebe zusätzlich möglich und wäre
vollständig unabhängig von jeder externen Quelle — würde aber Wolkenbedeckung
gar nicht regional/saisonal abbilden, nur eine grobe Pauschale. Das ist
strukturell dieselbe Schwäche wie die bisherigen Ersatztabellen aus Plan 1:
plausibel, aber nicht gemessen.

## Empfehlung

**Δα:** JRC-Datensatz (Duveiller et al. 2018, Version 2,
`Delta_albedo_ext` aus `albedo_IGBPdet_ext.nc`), mit dokumentierter
Proxy-Regel für Waldtypen ohne direkte Abdeckung im Zielbreitenband
(insbesondere borealer Nadelwald: MixedForest→Grass oder DecNeedle→Grass als
Stellvertreter für EvgNeedle→Grass verwenden und das explizit so
kennzeichnen).

**q̇_sw:** NASA POWER Climatology API (`ALLSKY_SFC_SW_DWN`).

**Warum diese Kombination:** Beide Quellen sind ohne Registrierung, ohne
API-Key und ohne Anmeldeschritt automatisiert abrufbar — das eliminiert
genau die Reibung, die CERES, ERA5 und MODIS in einer automatisierten
Pipeline erzeugen würden (für alle drei wurde die Zugangsschranke direkt
beobachtet, nicht nur vermutet: HTTP 401 bei MODIS und CERES, sichtbare
Sign-in-Pflicht bei ERA5/CDS). Beide liefern echte, monatlich aufgelöste
Klimatologien auf vergleichbarer nativer Auflösung (1°), sodass ⟨Δα · q̇⟩
tatsächlich Monat für Monat gebildet werden kann, bevor gemittelt wird — die
im Auftrag geforderte Reihenfolge lässt sich mit beiden Quellen einhalten.

**Was diese Kombination nicht kann:**

- Beide Felder liegen nativ bei 1° Auflösung, nicht bei den geforderten
  0,5°. Das Zielgitter muss durch Interpolation (z. B. bilinear oder
  Nearest-Neighbour-Verdopplung) erzeugt werden — das ist eine reale, wenn
  auch überschaubare Umsetzungsaufgabe, kein reiner Download.
- Der JRC-Δα deckt nicht jede Waldtyp/Breiten-Kombination direkt ab. Für den
  borealen Nadelwald der Folie (*Picea abies*, 60°N) gibt es keine direkte
  Beobachtung in diesem Datensatz — nur in verwandten Waldklassen. Jede Zahl,
  die daraus für Nadelwald bei 60°N berechnet wird, beruht auf einer
  Substitutionsannahme, die auf der Folie oder im begleitenden Text genannt
  werden muss.
- Die IGBP-Klassenzuordnung der Transitionscodes im JRC-Datensatz ist aus der
  Struktur abgeleitet, nicht durch eine im Datensatz enthaltene Legende
  bestätigt. Vor der ersten Berechnung sollte das gegen eine unabhängige
  Quelle (z. B. die Methodik-Sektion des Papers oder die MCD12C1-Doku)
  geprüft werden.
- NASA POWER ist eine abgeleitete, geglättete 20-Jahres-Klimatologie
  (2001–2020), kein Echtzeit- oder einzeljahresspezifisches Feld — für einen
  Faktor, der ohnehin als langfristiges Monatsmittel in die Formel eingeht,
  ist das angemessen, aber es ist explizit keine Momentaufnahme.
- Keine der beiden Quellen wurde bereits vollständig auf das Zielgitter
  heruntergerechnet oder im Code verankert — das bleibt Umsetzungsarbeit von
  Plan 3, nicht dieser Recherche.

## Aufwand je Weg, ehrlich beziffert

| Weg | Aufwand |
|---|---|
| JRC Δα (empfohlen) | Gering bis mittel: zwei Dateien laden (~20 MB), IGBP-Legende gegenprüfen, Proxy-Regel für fehlende Waldtyp/Breiten-Kombinationen festlegen und dokumentieren, 1°→0,5°-Interpolation schreiben. Größter Einzelposten ist die Proxy-Entscheidung, weil sie inhaltlich (nicht nur technisch) zu begründen ist. |
| NASA POWER q̇_sw (empfohlen) | Gering bis mittel: 648 Kachel-Abfragen (10°×10°) skriptieren, zusammenfügen, 1°→0,5°-Interpolation (dieselbe Routine wie oben wiederverwendbar). Kein Login-Handling nötig. |
| MODIS-basiertes Δα | Hoch: Earthdata-Konto anlegen, Auth-Token-Handling in der Pipeline, Rohreflektanz+Landbedeckung für mehrere Jahre laden, Wald/Offenland-Pixelpaare je Klimazone definieren und statistisch differenzieren — das ist eine eigenständige Datenverarbeitungs-Pipeline, real mehrere Arbeitstage, nicht Stunden. Dafür: flächendeckend, keine Beobachtungslücken wie bei Duveiller. |
| CERES EBAF-Surface / ERA5 für q̇_sw | Mittel bis hoch: Kontoerstellung, Token-/Credential-Management in einer automatisierten Pipeline, bei ERA5 zusätzlich CDS-API-Client-Handling und Warteschlangen (asynchrone Anfragen). Technisch gut dokumentiert, aber Reibung genau dort, wo der Auftrag sie vermutet hat. |
| ΔR_n-Fallback | Sehr gering (Datensatz liegt bereits vor), aber inhaltlich unsauber: Antrieb würde langwellige Anteile enthalten, die φ_α laut Formel nicht vorsieht. Nur im Notfall, mit explizitem Vorbehalt im Text jeder darauf beruhenden Zahl. |

## Falls nichts davon greift — der Fallback bleibt, und er ist keine Messung

Sollte sich in Plan 3 herausstellen, dass weder der JRC-Datensatz noch NASA
POWER praktikabel sind (z. B. weil die Proxy-Substitution für Nadelwald
inhaltlich nicht zu rechtfertigen ist, oder die Interpolation auf 0,5° zu
Artefakten führt, die die Kernaussage verzerren), bleiben die
Ersatz-Breitentabellen aus Plan 1 (`_DELTA_ALPHA_TABLE`, `_Q_SW_TABLE` in
`src/nbs/forcing.py`) die einzige Grundlage. Das muss dann so benannt werden,
wie es die Docstrings, das Notebook und die betroffenen Tests bereits tun:
Diese Tabellen sind eine **gemeinsame Kalibrierung gegen eine auf einer Folie
zitierte Zahl** (die 70-W-Glühbirne), keine unabhängige Messung. Jede Karte,
die auf ihnen aufbaut, zeigt eine plausible **Struktur** — dass der Effekt
mit der Breite variiert, in welche Richtung, ungefähr wie stark — aber keine
**gemessene Geographie**. Jede Abbildung, jede Folie und jeder Satz Text, der
auf diesen Tabellen beruht, muss das so sagen, nicht nur in einem Docstring,
sondern an der Stelle, wo die Zahl gezeigt wird.

## Entscheidung

**Offen — liegt beim Autor.** Diese Recherche empfiehlt JRC-Δα + NASA-POWER-
q̇_sw als die Kombination mit dem geringsten Reibungsverlust und der besten
Nachvollziehbarkeit, macht aber die Lücken (Proxy-Substitution für Nadelwald,
unbestätigte Klassenlegende, 1°→0,5°-Interpolation) nicht kleiner, als sie
sind. Task 3 beginnt erst, nachdem diese Entscheidung getroffen ist.

---

# Nachtrag des Controllers — Legende belegt, Befund korrigiert

**Datum:** 2026-09-09, nach eigener Prüfung am Datensatz und an der
Veröffentlichung.

## Die Legende, belegt

Aus Duveiller, Hooker & Cescatti (2018), Sci. Data 5, 180014, Open-Access-
Fassung über PubMed Central (PMC5819485):

**IGBPdet, 10 Klassen:**

| Index | Klasse |
|---|---|
| 1 | Evergreen Broadleaf Forest (EBF) — **tropisch** |
| 2 | Deciduous Broadleaf Forest (DBF) |
| 3 | Evergreen Needleleaf Forest (ENF) — **boreal** |
| 4 | Deciduous Needleleaf Forest (DNF) |
| 5 | Mixed Forest (MF) |
| 6 | Savannas (SAV) |
| 7 | Shrublands (SHR) |
| 8 | Grasslands (GRA) |
| 9 | Cropland (CRO) |
| 10 | Wetlands (WET) |

**IGBPgen, 4 Klassen:** 1 Forests, 2 Shrublands, 3 Crops & Grasses, 4 Savannas.

Der Übergangscode `iTr` ist die Verkettung von Ursprungs- und Zielklasse.

## Der gemeldete boreale Datenmangel existiert nicht

Der Untersuchungsbericht meldete „null gültige Zellen für den Übergang
immergrüner Nadelwald → Grasland zwischen 55 und 65°N" und schloss daraus, die
Fichte müsse über einen Ersatzübergang laufen. **Das war ein Artefakt einer
geratenen Legende.** Klasse 1 ist nicht Nadelwald, sondern *tropischer*
Breitlaubwald — dass sie im borealen Band fehlt, ist die korrekte Abwesenheit
einer tropischen Klasse in der Taiga, kein Loch im Datensatz.

Der tatsächlich benötigte Übergang ist **Code 38** (ENF → Grasland), und er hat
im Band 55–65°N **2 825 satellitenbeobachtete** und 8 637 räumlich erweiterte
Zellen. Kein Ersatz nötig, keine Fußnote nötig.

## Zuordnung Art → Übergang

Aufforstung ist die Umkehrung des dokumentierten Übergangs, das Vorzeichen
dreht sich also.

| Art | `igbp_class` | Klasse | Übergang auf Grasland | auf Acker |
|---|---|---|---|---|
| picea_abies | evergreen_needleleaf | 3 | 38 | 39 |
| pinus_sylvestris | evergreen_needleleaf | 3 | 38 | 39 |
| fagus_sylvatica | deciduous_broadleaf | 2 | 28 | 29 |
| eucalyptus_grandis | evergreen_broadleaf | 1 | 18 | 19 |
| tropical_mixed | evergreen_broadleaf | 1 | 18 | 19 |

## Gemessene Werte, Jahresmittel über das jeweilige Band

| Übergang | Δα (Entwaldung) | ΔSW_reflektiert |
|---|---|---|
| 18, Tropen ±10° | +0,0151 | +3,469 W/m² |
| 28, 55–65°N | +0,0907 | +6,961 W/m² |
| 38, 55–65°N | +0,1159 | +10,717 W/m² |

Aufforstung kehrt das Vorzeichen um: die boreale Fichte verdunkelt also um
Δα = −0,116 und absorbiert 10,7 W/m² mehr.

## Folge für Folie 14

Die Ersatztabelle aus Plan 1 gibt bei 60°N Δα = −0,130 und q̇ = 110 W/m², also
71,5 W je Baum. Die gemessenen Daten geben **10,717 W/m² × 5 m² = 53,6 W**.

Die Kalibrierung lag also in der richtigen Größenordnung, überschätzt aber um
etwa ein Drittel. Die implizite Einstrahlung des Datensatzes ist
10,717 / 0,1159 = **92,5 W/m²** gegen 110 W/m² in der Ersatztabelle.

**Die Folie sollte auf die gemessene Zahl umgestellt werden.** Rund 54 W ist
immer noch „eine Glühbirne, die nie ausgeht", und die Zahl ist dann belegt
statt kalibriert — der Zirkelschluss aus Plan 1 löst sich damit auf.

## Entscheidung

JRC-Datensatz, Version 2, `IGBPdet`. **Beide** Größen getrennt modellieren:
`Delta_albedo` und die daraus mit `Delta_SWreflected` implizierte Einstrahlung.
Damit bleibt Δα eine eigene Stellschraube für die Sensitivitätsanalyse, die
Kovarianz des Anbieters bleibt über das Produkt prüfbar, und es wird keine
zweite Datenquelle mit fremdem Gitter und fremder Periode gebraucht.
