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
