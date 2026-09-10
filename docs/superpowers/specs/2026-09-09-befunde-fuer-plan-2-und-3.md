# Befunde aus Plan 1 — was Plan 2 und 3 wissen müssen

**Datum:** 2026-09-09
**Quelle:** Umsetzung von `2026-09-09-einzelbaum-physikkette.md`, 29 Commits,
Abschlussreview und Reparaturrunden.

Dieses Dokument hält fest, was beim Bauen der Einzelbaum-Kette herauskam und
über sie hinaus gilt. Es ersetzt die Wegwerf-Berichte des Arbeitsbereichs.

---

## 1. Zahlen, die auf Folien gehören

Alle Werte für *Picea abies* bei 60°N bzw. tropischen Mischbestand bei 0°N,
SSP2-4.5, Horizont 2025–2150, je **ein Baum**.

| Größe | Wert |
|---|---|
| Glühbirne boreal (Folie 14) | 71,50 W |
| Glühbirne tropisch | 34,65 W, Verhältnis 0,485 |
| ΔT(2150) boreal, volles Modell | −2,24·10⁻¹⁴ K |
| ΔT(2150) tropisch | −4,07·10⁻¹³ K |
| Wärmefenster boreal | 2026–2048 |

### Die Leiter — Folie P2 (Wasserfall)

| Stufe | t\* | ΔT(2150) [K] |
|---|---|---|
| naive Kohlenstoffrechnung | 2025 | −1,4245·10⁻¹³ |
| + Albedo | 2048 | −3,1532·10⁻¹⁴ |
| + Störung | 2048 | −2,9611·10⁻¹⁴ |
| + Senkensättigung | 2049 | −9,0036·10⁻¹⁴ |
| + Hintergrundkonzentration (voll) | **2071** | −2,2405·10⁻¹⁴ |

Zwei Aussagen daraus, beide eigenständig:

- **Albedo kostet 23 Jahre** bis zum Break-even (2025 → 2048).
- **Die steigende Hintergrundkonzentration kostet nochmal 22 Jahre**
  (2049 → 2071). Fast so viel wie Albedo, und in der Aufforstungsliteratur
  praktisch nie mitgerechnet, weil dort mit fester Strahlungswirkung gearbeitet
  wird. *Wer heute pflanzt, pflanzt in eine Atmosphäre, in der jede Tonne
  weniger bewirkt.*
- **Senkensättigung wirkt entgegengesetzt zur Intuition**: sie verstärkt die
  Kühlung, weil die Lücke einer Entnahme langsamer aufgefüllt wird.

## 2. Folie 13 — der CO₂-Restanteil

Die Folie zitiert „rund 40 % nach 100 Jahren" nach Joos et al. (2013). Das ist
die **vorindustrielle** Impulsantwort: `green_carbon_preindustrial()[75] = 0,4388`.

Die eigene Rechnung auf SSP2-4.5 liefert `green_carbon()[75] = 0,700`, weil der
Puls auf gesättigtere Senken trifft. Szenarienabhängigkeit, geprüft:

| Szenario | Restanteil nach 75 a |
|---|---|
| SSP1-2.6 | 0,567 |
| SSP2-4.5 | 0,700 |
| SSP3-7.0 | 0,816 |

Beide Kurven sind über den Schalter `carbon_sink` rechenbar. Empfehlung für die
Folie: beide zeigen, die Differenz benennen. Der Restanteil hat unter SSP2-4.5
ein Minimum von 0,6615 im Jahr 2046 und steigt danach wieder — die schnellen
Moden des Pulses klingen ab, danach dominiert die nachlassende Senkenwirkung.
Das ist eine Kurve, die mehr erzählt als eine Zahl.

## 3. Folie 14 — die Glühbirne ist ein Zirkelschluss, bis die Raster da sind

`_DELTA_ALPHA_TABLE` und `_Q_SW_TABLE` in `src/nbs/forcing.py` sind **gemeinsam
auf die 70-W-Zahl der Folie kalibriert**. Beide gehen nur als Produkt in die
Rechnung ein. Solange sie in Kraft sind, ist jede Prüfung gegen die Folie eine
Konsistenzkontrolle, keine Bestätigung. Das steht so in den Docstrings, im
Notebook und in den beiden betroffenen Tests — und muss dranbleiben, bis die
Duveiller-Raster sie ersetzen.

## 4. Der Albedo-Effekt ist ein Frühjahrsereignis — korrigiert am 2026-09-09

**Dieser Abschnitt hat ursprünglich das Falsche behauptet. Die Korrektur steht
unten und ist an den Duveiller-Rastern gemessen, nicht hergeleitet.**

### Was hier zuerst stand, und warum es falsch war

Die ursprüngliche Fassung schloss aus der kalibrierten Ersatztabelle, dass ein
höherer Breitengrad den Albedo-Effekt nicht verstärkt, und forderte, das
Produkt Δα·q̇ monatlich zu bilden, weil das Multiplizieren zweier Jahresmittel
den borealen Effekt **unterschätze**.

Die Forderung war richtig. Die Begründung war in der Richtung falsch.

### Was die Daten sagen

Gemessen am JRC-Datensatz (Duveiller et al. 2018, v2.0), Übergang 38
(immergrüner Nadelwald ↔ Grasland), Zonalmittel:

| Breite | mean(Δα·q̇) / [mean(Δα)·mean(q̇)] | Spitzenmonat | Spitze / Jahresmittel |
|---|---|---|---|
| 45°N | 0,87 | Februar | 1,4× |
| 55°N | 0,80 | März | 2,7× |
| 60°N | 0,80 | April | 3,0× |
| 65°N | 0,70 | April | 4,3× |

Die Spitze **wandert mit der Breite von Februar nach April**, und ihre Dominanz
wächst dabei. Im Süden liegt zwar Schnee, aber die Sonne ist noch schwach;
weiter nördlich fällt der späte Schnee mit der bereits kräftigen
Frühjahrssonne zusammen. Das ist die Schneemaskierung, als Wanderung sichtbar.

*(Werte für eine Gitterzeile; ein Band von ±2,5° verschiebt die Verhältnisse
um wenige Zehntel, nicht die Aussage. Wer eine Wattzahl für einen einzelnen
Monat zitiert, muss die Bandbreite dazusagen.)*

Das Multiplizieren von Jahresmitteln **überschätzt** den borealen Antrieb um
20 bis 30 Prozent, und der Fehler wächst polwärts. Der Grund: der
Albedokontrast ist im Hochwinter am größten (Δα ≈ 0,25 im Januar bei 60°N),
aber dort steht die Sonne kaum über dem Horizont (q̇ ≈ 16 W/m²). Diese Monate
blähen das Jahresmittel von Δα auf, ohne zum Produkt beizutragen.

### Der Mechanismus stimmt, und er ist schärfer als gedacht

Der Monatsgang bei 60°N zeigt ihn unmittelbar:

| Monat | Δα | q̇ [W/m²] | Δα·q̇ [W/m²] |
|---|---|---|---|
| Januar | 0,25 | 16 | 4,0 |
| März | 0,21 | 131 | 26,9 |
| **April** | **0,23** | **196** | **44,3** |
| Mai | 0,10 | 221 | 21,6 |
| Juli | 0,06 | 214 | 13,3 |

Im April liegt noch Schnee **und** die Sonne steht schon hoch. Dieser eine
Monat trägt rund das Dreifache des Jahresmittels. Bei 45°N ist das Muster viel
schwächer und liegt im Februar: dort schmilzt der Schnee, bevor die Sonne
Kraft hat.

### Folge für die Rechnung

Weiterhin gilt: **monatlich multiplizieren, dann mitteln.** Niemals
⟨Δα⟩·⟨q̇⟩. Nur die Richtung des Fehlers ist umgekehrt zur ursprünglichen
Annahme, und er ist mit 20–30 % groß genug, um Zahlen auf einer Folie zu
verschieben.

### Folge für den Vortrag

Das Bild der „Glühbirne, die nie ausgeht" (Folie 14) trifft die Sache nicht.
Die Albedo-Strafe eines borealen Waldes ist **ein Scheinwerfer, der im April
brennt** — und je weiter nördlich, desto ausschließlicher. Das ist anschaulicher
als eine Jahresmittelzahl und lässt sich als Monatsgang unmittelbar zeigen.

## 5. Grenze der Kette, dokumentiert

Der Spiegeltest gegen einen direkten FaIR-Lauf (Fluss → Antrieb → Temperatur):

| CO₂-Variante | Abweichung von FaIR |
|---|---|
| linear (`A_CO₂` fest) | 34,68 % |
| logarithmisch (Hintergrund) | 15,35 % |

Der Rest der logarithmischen Abweichung ist zugeordnet: Pulsüberlagerung beim
Falten eines kontinuierlichen Flusses mit einem Einzelpuls-Kern, plus die
separat gemessenen ~4,2 % der Temperaturfaltung. Letztere rührt von einer
echten Kohlenstoff-Klima-Rückkopplung her: ein reiner Solar-Antrieb ohne
Emissionsänderung verschiebt in FaIR die CO₂-Konzentration um bis zu 0,73 ppm.

`a = 5,35` (Myhre 1998) ist **nicht**, was FaIR rechnet — FaIR nutzt
`meinshausen2020`. Gemessener Unterschied: 0,08 % bei 424 ppm, 2,46 % bei
624 ppm. Bewusst nicht übernommen: 2,5 % rechtfertigen keine zustandsabhängige
Formel in einem Modell, dessen Herleitung auf eine Folie passen soll.

## 6. Folienbefund E3 — die zwei Zeilen zeigen dasselbe

Die Zerlegungsabbildung setzt Antrieb oben, Temperatur unten. Die Kurven sind
nahezu deckungsgleich, weil g_T kurzes Gedächtnis gegenüber der Zeitskala von φ
hat, also ΔT ≈ φ · Gleichgewichtsempfindlichkeit. Die ursprüngliche Begründung
(„im Antrieb schärfer sichtbar") trägt nicht.

Der einzige echte Unterschied: der Antrieb kreuzt die Null etwa vier Jahre vor
der Temperatur. Das *ist* die thermische Trägheit, verschwindet aber in der
Linienbreite. **Für Plan 3 entscheiden:** eine Zeile, oder die Verzögerung
sichtbar machen (Ausschnitt um den Nulldurchgang, oder beide Nulldurchgänge
markiert).

## 7. Legacy-Abbildungen stimmen nicht mehr

`docs/slides/figures/05_level0_vs_level1.png`,
`10_progressive_complexity_45N.png` und `11_equivalence_by_latitude.png` stammen
aus einem Stand, den der Code nicht mehr reproduziert. Neu erzeugt hat
`11_equivalence_by_latitude` eine **leere rechte Tafel**, weil die
Legacy-Analyse heute bei allen Breiten `t* = inf` liefert
(ΔT endet bei +7,2·10⁻⁴ bis +1,0·10⁻³ K).

Kein Widerspruch zur neuen Kette: Legacy rechnet Referenzpuls **plus**
Ausgleichsfläche, dort heißt ΔT > 0 nur „der Ausgleich ist unvollständig".
Inhaltlich sogar dieselbe Botschaft wie die Leiter, nur in Zertifikats-Sprache.

Die PNGs wurden auf den Ursprungsstand zurückgerollt. Wenn diese Abbildungen
für Backup-Folien gebraucht werden, braucht `plot_breakeven_by_level` denselben
Umgang mit dem Unendlich-Fall wie die neue `plots.py`: „kein t\* im Horizont"
hinschreiben statt eine leere Tafel zu zeichnen. **Autorenentscheidung.**

## 8. Werkzeugwarnung: Toleranzen

Größen in diesem Modell liegen bei 10⁻¹³ bis 10⁻¹⁵. Die Standardtoleranzen sind
gröber: `np.allclose` nimmt `atol=1e-8`, `pytest.approx` nimmt `abs=1e-12` —
und **ein gesetztes `rel` löscht das voreingestellte `abs` nicht**.

Fünf Zusicherungen konnten deshalb nicht fehlschlagen, darunter jedes Mal die
wichtigste des jeweiligen Moduls. Eine akzeptierte selbst `0.0` als „nah genug"
an 1,61·10⁻¹⁵.

**Regel für dieses Projekt:** jede Toleranz explizit setzen — `abs=0` bei
`pytest.approx`, `atol` am Signal skaliert bei `np.allclose`. Und nach jeder
Verschärfung den Gegenbeweis führen: ein Vorzeichen verdrehen und zeigen, dass
der Test jetzt fällt.

## 9. Offene Kleinigkeiten

Bewusst zurückgestellt, keine blockiert etwas:

- Artparameter tragen nur für 5 von 12 Feldern eine Quelle, und alle fünf Arten
  teilen dieselben drei Zitate. **Vor dem Zitieren auf Folien präzisieren**
  (Spec §13 nennt das bereits als [prüfen]).
- Drei der vier Abbildungstests prüfen nur, dass eine PNG-Datei über 10 kB
  entstand. Vertauschte Achsen oder ein falsches Vorzeichen bestünden.
  Visuelle Richtigkeit hängt an Sichtprüfung.
- `test_response.py`: `g[0] == approx(1.0, abs=0.06)` gegen tatsächliche 0,9461
  — 0,6 % Marge, spröde gegen einen FaIR-Versionswechsel.
- Kein Test deckt südliche Breiten oder das Klemmen außerhalb der
  Breitentabelle ab.
- Risikoprämien-Test hat real ~3,2 Standardfehler Marge, nicht die große
  Reserve, die der Bericht nahelegt.
- `T_START`, `T_END`, `A_EARTH_M2` stehen doppelt in `nbs.constants` und
  `nbs.legacy.parameters`. Durch Längenwächter jetzt laut statt still.

---

# Befunde aus Plan 2 — was Plan 3 wissen muss

**Datum:** 2026-09-10
**Quelle:** Umsetzung von `2026-09-09-rasterschicht-und-potenzial.md`, Tasks
1–8. Dieser Abschnitt setzt Abschnitte 1–9 oben fort (Plan 1) und ist für
jemanden geschrieben, der an Plan 2 nicht beteiligt war.

Plan 2 hat die Einzelbaum-Kette aus Plan 1 über das gesamte 0,5°-Gitter
aufsummiert: eine Landmaske, echte Albedo-Raster, eine Korrekturkaskade auf
Bastin et al. (2019) und eine Umkehrrechnung gegen 1,5 °C. Der vollständige,
ausgeführte Durchlauf steht in `notebooks/03_potenzial_global.ipynb`.

## 10. Die Landmaske hatte einen schweren Defekt — und kein Test fing ihn

`nbs.landscape` wies bepflanzbare Fläche ursprünglich **ohne jede
Landmaske** zu: jede Breitenzeile wurde per Zufallspermutation in
Ozean/Wald/Savanne/Landwirtschaft/bepflanzbar aufgeteilt, mit erfundenen
Landanteilen je Breitenband. Gemessen vor der Korrektur: von 5740 als
bepflanzbar markierten Zellen lagen **4092 (71,3 %) im Ozean**; die
Ausgleichsjahr-Karte zeigte grüne (bepflanzbare) Zellen bei 60° Süd, also
im Südpolarmeer.

**Gefunden nur durch Ansehen der Abbildung.** Weder
`test_plantable_area_never_exceeds_the_cell` noch die
0,05–5-Gha-Plausibilitätsgrenze schlugen an — beide sind mit Unsinn
erfüllbar, der zufällig die richtige Größenordnung hat. Das ist das dritte
Mal in diesem Projekt (nach zwei Fällen in Plan 1), dass eine reine
Sichtprüfung einen Fehler fand, den die grüne Testsuite nicht auffing. Für
Plan 3: **jede neue Karte vor der Übernahme in eine Folie ansehen, nicht
nur testen.**

**Der Fix** (`src/nbs/landscape.py`, Task 7): `land_mask()` ist jetzt die
Vereinigung aller 45 Duveiller-Landbedeckungsübergänge über alle 12 Monate
— wo immer der Duveiller-Datensatz irgendeinen Wert trägt, ist die Zelle
vegetiertes Land. Gemessen: **52 688 von 259 200 Halbgrad-Zellen, 20,3 %
der Erdoberfläche** — plausibel unterhalb der üblichen ~29 % Landanteil,
weil das Raster nur vegetiertes Land erfasst (Wüste, Eis, Fels bleiben
außen vor, da kein Wald↔Gras/Acker-Übergang dort Signal hat). Ohne die
Raster fällt die Funktion sichtbar auf ein Alles-Land-Gitter zurück
(`land_mask_provenance() == "fallback_alles_land"`), statt eine plausibel
aussehende, aber erfundene Küstenlinie zu zeichnen.

**Was der Fix NICHT behebt:** Innerhalb einer Landzeile ist die Aufteilung
in Wald/Savanne/Landwirtschaft/bepflanzbar weiterhin eine per Zeilenindex
geseedete Zufallspermutation der *echten* Landspalten — es gibt keine
Landbedeckungs-/GEZ-Rasterquelle, nur fünf Breitenbänder
(`nbs.landscape.provenance()` meldet immer `"fallback"`, unabhängig von
`land_mask_provenance()`). Das erzeugt ein sichtbares "Konfetti"-Muster
innerhalb der Kontinente auf jeder Karte dieses Plans — erwartet,
dokumentiert, aber wer eine Karte auf eine Folie nimmt, sollte den
Unterschied kennen: die Landmaske ist gemessen, die Verteilung *innerhalb*
des Landes ist es nicht.

**Neue Gesamtzahl:** bepflanzbare Fläche fiel von 1,08 Gha (Task 4, vor dem
Fix) auf **0,9488 Gha** — ein Rückgang von nur ~12 %, kleiner als der
71,3-Prozent-Zellbefund vermuten lässt, weil die alten, erfundenen
Landanteile je Breitenband zufällig grob mit den heute gemessenen realen
Anteilen übereinstimmten (die *Menge* Land pro Zeile war ungefähr richtig
kalibriert, nur die *Lage* nicht). 0,9488 Gha liegt bemerkenswert nah an
Bastins eigener 0,9-Gha-Angabe — das ist ein Zufall zweier unabhängiger,
vergleichbar unsicherer Schätzungen, **keine Bestätigung der Präzision
dieses Modells.**

## 11. Die Duveiller-Daten: was gemessen ist, was nicht

Der JRC-Datensatz (Duveiller, Hooker, Cescatti 2018, *Sci. Data* 5, 180014,
v2.0, CC-BY-4.0) liefert `Delta_albedo` und `Delta_SWreflected` für 45
Landbedeckungsübergänge auf einem 1°-Gitter, aus Satelliten-Ko-Vorkommen
zweier benachbarter Landbedeckungen. **Die Legende der 45 Übergangscodes
steht nicht in der Datei selbst** — sie musste aus der Begleitveröffentlichung
(PMC5819485) rekonstruiert werden; eine geratene Legende hätte in Task 2
beinahe zu einer falschen Übergangswahl für die Fichte geführt (Code 38,
Nadelwald↔Gras, wurde erst nach Prüfung der echten Legende bestätigt).

**Abdeckungslücke:** Der Datensatz braucht lokale Ko-Vorkommen beider
Landbedeckungen, um einen Übergang an einer Zelle zu retrieven. Für den
Fichten-Übergang hat selbst die räumlich erweiterte Fassung
(`_ext`-Variante) nur an einem kleinen Teil der bepflanzbaren
Fichten-Zellen ein echtes lokales Retrieval — ursprünglich (Task 5) fehlten
dadurch ~91 % der bepflanzbaren Zellen jeglichen Albedowert, was still zu
0 gerundet worden wäre und die Kernaussage des Vortrags (Albedo als
Gegenspieler) auf der Karte gelöscht hätte.

**Die Lösung, dreistufige Füllung** (`nbs.albedo_grid.alpha_q_product`,
Task 5): jede Zelle wird aus einer von drei Quellen gefüllt, in
Prioritätsreihenfolge —

1. **lokal**: echtes Duveiller-Retrieval an dieser Zelle,
2. **zonal**: Median über alle anderen Retrievals derselben Art im selben
   Breitenband,
3. **tabelle**: die Plan-1-Breitentabelle als letzter Rückfall.

Jede Zelle trägt ihre Provenienz-Stufe (`product_provenance_grid`), und
jede Art hat einen aggregierten Anteil pro Stufe
(`provenance_fractions`). Gemessen (Task 8, mit den jetzt vorhandenen
Rastern):

| Art | lokal | zonal | tabelle |
|---|---|---|---|
| Gemeine Fichte (*Picea abies*) | 29,3 % | 70,7 % | 0,0 % |
| Waldkiefer | 46,7 % | 52,2 % | 1,0 % |
| Rotbuche | 29,3 % | 70,7 % | 0,0 % |
| Rosen-Eukalyptus | 21,2 % | 78,8 % | 0,0 % |
| Tropischer Mischbestand | 63,2 % | 36,8 % | 0,0 % |

**Bei vier von fünf Arten ist die zonale Extrapolation die Mehrheit der
Fläche.** Nur der tropische Mischbestand hat eine lokale Mehrheit, weil
sein Übergang deutlich mehr Ko-Vorkommen-Zellen im Datensatz hat. Für
Plan 3: **jede Karte und jede Zahl, die auf `alpha_q_product` beruht, trägt
diese Zusammensetzung.** `nbs.map_plots.footer_text()` schreibt sie
automatisch in die Fußzeile jeder Kartenabbildung — beim Export auf eine
Folie darf diese Fußzeile nicht wegfallen, ohne dass die Aussage anderswo
auf der Folie steht.

## 12. Der Albedo-Effekt ist ein Frühjahrsereignis — bestätigt, mit einer Nuance

Plan 1 hatte (Abschnitt 4 oben) bereits korrigiert festgehalten: das
Produkt Δα·q̇ muss monatlich gebildet werden, dann gemittelt — die
Jahresmittelbildung überschätzt den borealen Antrieb um 20–30 %, weil der
Winterkontrast das Δα-Jahresmittel aufbläht, ohne zum Produkt beizutragen.
Task 8 hat das mit `nbs.albedo_grid.seasonal_profile` direkt an der Fichte
sichtbar gemacht: bei 45°N liegt die Spitze im Februar (1,6-fache
Jahresmittelspitze), bei 60°N deutlich schärfer im Übergang März/April
(2,8-fache Spitze).

**Nuance für Plan 3:** Bei 60°N liegen März (−33,36 W/m²) und April
(−33,13 W/m²) mit unter 1 % Unterschied praktisch gleichauf — welcher der
beiden Monate nominell "gewinnt", hängt an der gewählten Bandbreite
(`half_width_deg`) und ob die räumlich erweiterte Fassung des Rasters
verwendet wird (`extended`), nicht an der physikalischen Aussage. Das
korrigierte Plan-1-Befund-Dokument (Abschnitt 4 oben) nennt April mit
~3,0-facher Spitze; Task 8 misst mit den Standardparametern von
`seasonal_profile` (±2,5°-Band, erweiterte Daten) den März, bei praktisch
identischem Verhältnis (2,8-fach). **Für eine Folie:** die Verschiebung
und Schärfung von Februar (45°N) nach März/April (60°N) ist robust und
belegt; ein einzelner Kalendermonat für 60°N sollte nicht ohne den Zusatz
"März/April, nahezu gleichauf" zitiert werden.

## 13. Die Kaskade (Akt 6) — Zahlen mit Quellen

`nbs.potential.cascade()` liefert sechs Stufen. Die ersten beiden sind
reine Literaturzahlen, **nicht von diesem Modell gerechnet** (die Kette
hat keinen Bodenkohlenstoff-Term); erst ab Stufe 3 rechnet das Modell
selbst:

| # | Stufe | Fläche [Gha] | Kohlenstoff [GtC] | ΔT(2150) [K] | Quelle |
|---|---|---|---|---|---|
| 1 | Bastin, Rohwert | — (0,9 laut Bastin) | 205,0 | — | Bastin et al. 2019, *Science* 365(6448):76–79, geprüft gegen Original und Sekundärquellen |
| 2 | Realistische C-Dichten + Bodenkohlenstoff | — | 81,0 | — | Science-Kommentare (Veldman et al. 2019, doi:10.1126/science.aay7976; Friedlingstein et al. 2019, doi:10.1126/science.aay8060); exakte Primärquelle der 81-GtC-Zahl hinter Bezahlschranke **nicht im Volltext geprüft**, als unbelegt gekennzeichnet |
| 3 | Nicht-Wald-Biome ausgeschlossen | 0,9488 | 81,0 | −0,2425 | `nbs.landscape` (Modell) |
| 4 | Albedo-Filter (kein Ausgleich bis 2150) | 0,9313 | 79,51 | −0,2432 | `nbs.map_plots._breakeven_year_field` (Modell) |
| 5 | Störungspuffer (Ensemble) | 0,9313 | 78,23 | −0,2393 | `nbs.pipeline.run_single_tree_ensemble` (Modell) |
| 6 | **Nutzbares Potenzial** | **0,9313** | **78,2** (Band 69,8–84,7) | **−0,2393** | Kaskadenergebnis |

**Nutzbares Potenzial: 78,2 GtC, entsprechend 38,2 % von Bastins
unkorrigiertem Rohwert (205 GtC), bei 0,2393 K globaler Abkühlung 2150
unter SSP245 auf 0,9313 Gha.**

Die Größenordnungen der Stufen sind für eine Folie wichtig: der große
Sprung liegt bei der **Literaturkorrektur** (205 → 81 GtC, −60 %), nicht
bei den drei modellgerechneten Stufen (81 → 78,2 GtC, weitere nur −3,4 %).
Landmaske, Albedo-Filter und Störungspuffer verfeinern eine bereits stark
korrigierte Zahl; sie tragen nicht den Hauptteil der Kritik an Bastin.
**Wer diese Kaskade als "unsere Korrektur von Bastin" präsentiert, sollte
sagen, dass der größte Teil davon bereits 2019 in der Fachdiskussion
stand** — das Modell in diesem Projekt liefert die drei kleineren, aber
eigenständig hergeleiteten Korrekturstufen 3–5.

Modellierungsentscheidung, die auf einer Folie erklärungsbedürftig ist: die
Kohlenstoffdichte für Stufen 3–5 ist an die *gemessene* Fläche von Stufe 3
(0,9488 Gha) verankert, nicht an Bastins eigene 0,9-Gha-Angabe — sonst
würde Stufe 3 einen höheren Kohlenstoffwert als Stufe 2 tragen, was der
Kaskaden-Erzählung ("jede Stufe eine Korrektur nach unten") widerspräche.

## 14. Die Umkehrrechnung: mehr Fläche als die Erde hat

`nbs.potential.reverse_1p5()` beantwortet: wie viele Vielfache der von
diesem Modell identifizierten, korrigierten Art-/Flächenmischung
(0,9488 Gha) wären nötig, um die SSP245-Basislinie ab 2050 unter 1,5 °C zu
bringen und bis 2150 dort zu halten? Zwei Varianten:

| Variante | Vielfaches der Modellfläche | Fläche [Gha] | kritisches Jahr |
|---|---|---|---|
| Mit Albedo und Störung (volles Modell) | 10,28 | 9,76 | 2149 |
| Nur Kohlenstoff (kein Albedo, keine Störung) | 10,10 | 9,58 | 2149 |

**Verhältnis (volles Modell / nur Kohlenstoff): 1,018.** Das volle Modell
braucht durchweg mehr Fläche, weil der boreale Erwärmungsanteil und der
Störungspuffer beide die Nettokühlung je Baum senken — der Effekt ist bei
diesem global gemischten Artenportfolio mit ~2 % moderat, weil sich
borealer Erwärmungsanteil und tropischer/gemäßigter Kühlungsvorteil in der
Flächensumme teilweise ausgleichen (ein reiner Fichten-Fall würde einen
deutlich größeren Unterschied zeigen, siehe der Stufe-5-Faktor in
Abschnitt 13).

**Für eine Folie, die einzige Zahl, die zählt:** beide Varianten liegen
bereits beim rund **Zehnfachen der von diesem Modell identifizierten
bepflanzbaren Fläche** — 9,76 bzw. 9,58 Gha, mehr als die gesamte eisfreie
Landfläche der Erde (rund 13 Gha, gerundete literaturübliche Näherung,
nicht aus diesem Modell gerechnet). Baumpflanzung allein hält SSP245 nicht
unter 1,5 °C, selbst wenn jede identifizierte bepflanzbare Zelle mehrfach
überplant würde. Das ist keine Modellschwäche, sondern die erwartete
Schlussfolgerung eines Vortrags, der die Bastin-Kritik nachvollzieht:
Aufforstung ist ein Baustein, kein Ersatz für Emissionsminderung.

## 15. Für Plan 3, kurz zusammengefasst

- Jede Karte aus `nbs.map_plots` trägt ihre Provenienz in der Fußzeile
  (`footer_text()`) — beim Übertragen in eine Folie diese Angabe nicht
  weglassen, sondern gegebenenfalls in Sprechertext oder Fußnote überführen.
- Die Landmaske selbst ist gemessen (20,3 %, `"raster"`); die Verteilung
  von Wald/Savanne/Landwirtschaft/bepflanzbar *innerhalb* des Landes ist es
  nicht (`"fallback"`, Breitenbänder) — beide Aussagen sind unabhängig
  voneinander und beide gehören auf eine Folie, die eine dieser Karten
  zeigt.
- Die 81-GtC-Zwischenstufe der Kaskade ist Literatur, keine Modellrechnung
  — auf einer Folie nicht als "unser Ergebnis" neben den echten
  Modellstufen 3–5 darstellen, ohne den Unterschied zu benennen.
- Bei der Frühjahrsspitze (Abschnitt 12) den Kalendermonat für 60°N nicht
  ohne den Zusatz "praktisch gleichauf März/April" zitieren.
- Alle Zahlen dieses Abschnitts sind reproduzierbar über
  `notebooks/03_potenzial_global.ipynb` — bei Zweifel an einer Zahl auf
  einer Folie: Notebook neu ausführen, nicht die hier notierte Zahl
  vertrauen.
