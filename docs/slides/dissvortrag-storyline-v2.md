# Storyline v2 — „Ingenieure auf dem Holzweg?“

Stand: 2026-10-01 · Bezug: `docs/slides/dissvortrag.pptx` (48 Folien, 45 sichtbar)
Ersetzt für Klima und Vergleich den Entwurf vom 20.09. (`dissvortrag-storyline-entwurf.md`). Das Kapitel Bäume bleibt im Kern, wie es ist.

---

## 1 · Der rote Faden: eine Systemgrenze, die wächst

Jedes Kapitel zieht die Bilanzgrenze eine Schale weiter. Innerhalb einer Schale wird nur das besprochen, was innerhalb dieser Grenze passiert. Alles, was draußen liegt, kommt erst dann vor, wenn die Grenze dorthin erweitert wird.

```
 ┌───────────────────────────────────────────────────────────────────── VERGLEICH ─┐
 │  Schale 5: alle Wege, CO₂ zu entnehmen (Baum ↔ DAC)                               │
 │  ┌────────────────────────────────────────────────────────────────── VERGLEICH ─┐ │
 │  │  Schale 4: alle Bäume auf der ganzen Landfläche                               │ │
 │  │  ┌───────────────────────────────────────────────────────────────── KLIMA ─┐ │ │
 │  │  │  Schale 3: die ganze Erde am Oberrand — Energie, Antrieb, Temperatur     │ │ │
 │  │  │  ┌──────────────────────────────────────────────────────────── KLIMA ─┐ │ │ │
 │  │  │  │  Schale 2: Kohlenstoffkreislauf — Luft + Ozean + Land               │ │ │ │
 │  │  │  │  ┌──────────────────────────────────────────────────────── BÄUME ─┐ │ │ │ │
 │  │  │  │  │  Schale 1: ein Baum — tauscht CO₂ und Licht mit der Umgebung    │ │ │ │ │
 │  │  │  │  └─────────────────────────────────────────────────────────────────┘ │ │ │ │
```

**These des Vortrags in einem Satz:** Die naive Rechnung ist nicht falsch gerechnet — sie zieht die Grenze um den Baum. Innerhalb dieser Grenze stimmt sie. Das Klima liegt aber außerhalb, und jede Schale, die man dazunimmt, verändert die Antwort. Für ein Ingenieurpublikum heißt das: Es geht um die richtige Wahl der Systemgrenze, wie in jeder Bilanz.

**Was jede Schale an die nächste übergibt:**

| Schale | Kapitel | rein | raus |
|---|---|---|---|
| 1 Baum | Bäume | — | ṁ_CO₂(t) [kg/a, Austausch mit der Luft] und ΔQ̇_Baum(t) [W, zusätzlich absorbiert] |
| 2 Kohlenstoffkreislauf | Klima | ṁ_CO₂(t) | Δm_CO₂(t) [kg CO₂, die der Luft wirklich fehlen] |
| 3 Erde am Oberrand | Klima | Δm_CO₂(t), ΔQ̇_Baum(t) | φ(t) [W/m²] → ΔT(t), t* |
| 4 ganze Landfläche | Vergleich | ΔT je Baum, je Ort | Potenzial [GtC, K], Abstand zu 1,5 °C |
| 5 alle Entnahmewege | Vergleich | Netto-Wirkung je Fläche | Einordnung gegen DAC, Antwort auf Folie 3 |

**Wiederkehrendes Bildelement:** Oben rechts auf jeder Inhaltsfolie ein kleines Schalen-Icon (5 konzentrische Ringe), die aktuelle Schale gefüllt. Es ersetzt die drei Kapitel-Icons nicht, sondern sitzt links daneben. Damit sieht das Publikum bei jeder Folie, wie groß das System gerade ist.

**Rückwirkungen gehören erst dorthin, wo ihre Schale beginnt.** Dass Ozean und Land CO₂ zurückgeben, kommt in Schale 2. Dass die übrige Menschheit die Atmosphäre auffüllt und dadurch jedes Kilogramm weniger bewirkt, kommt in Schale 3. Dass die Erwärmung die Störungsrate erhöht, kommt in Schale 3, wenn T bekannt ist. Im Kapitel Bäume kommt keins davon vor.

**Regel für jede Folie:** Jede Folie endet mit einer offenen Größe oder Frage, die die nächste aufgreift. Unten steht deshalb bei jeder Folie eine Zeile **→ Brücke**.

**Bewusste Vereinfachungen** (offen ansagen, Details ins Backup): Verdunstung nur als ein Satz an der Grenze von Schale 3 · Zweischichtmodell ins Backup · τ_atm = 0,8 ohne Strahlungskerne · GPP/NPP/NEP/NBP im Backup.

---

## 2 · Einstieg

| # | Folie | Änderung |
|---|---|---|
| 1 | Titel | — |
| 2 | CDR-Bedarf (Carbon Brief) | — |
| 3 | Frage: „Die Natur betreibt seit Jahrmillionen …“ | — |
| 4 | Naive Rechnung | **Zahl angleichen und Schlusssatz umformulieren**, siehe unten |
| 5 | Kein Strohmann (Bastin) | — |
| 6 | Überblick | Statt dreier gleichberechtigter Kacheln das Schalenbild: Bäume = innerste Schale, Klima = Schalen 2–3, Vergleich = Schalen 4–5 |

> **Folie 4, Zahl:** Die naive Rechnung arbeitet mit 2 t CO₂ je Baum, das Modell mit m_max = 50 kgC ≈ 183 kg CO₂ je Baum. Mit dem Modellbaum: 300 Gt ÷ 0,18 t ≈ **1,6 Billionen Bäume**. Das landet genau bei der „Billion Bäume“-Kampagne von Folie 5, und V8 vergleicht am Ende denselben Baum.
> **Folie 4, Schlusssatz:** statt „kennt keinen Ort, keine Zeit, kein Risiko“ → *„Diese Rechnung zieht die Grenze um den Baum. Wir ziehen sie Schritt für Schritt weiter, bis das Klima drin ist.“*

---

## 3 · Kapitel BÄUME — Schale 1: ein Baum

*Nur der Baum. Er tauscht mit seiner Umgebung CO₂ und Sonnenlicht aus. Was danach mit dem CO₂ in der Luft passiert, bleibt bewusst offen.*

**Laufendes Beispiel ab hier: die Gemeine Fichte (Picea abies) an zwei Orten.** **Aachen** (50,8°N, 6,1°E) steht für „bei uns“, mit wenig Schnee. **Archangelsk** (64,5°N, 40,6°E) steht für den verschneiten Norden. Beide Zellen haben eine echte lokale Albedo-Messung (Duveiller, Stufe „lokal“). Die beiden Orte tauchen auf jeder Folie als dieselben zwei Punkte auf: auf den Karten als Marker, in den Kurven als zwei Linien. Farben fest vergeben, z. B. Aachen dunkel, Archangelsk hell.

**Die Kartenform führt hier ein.** Die Albedokarte in B8 zeigt *eine* Art, die Fichte, überall dort, wo sie wachsen kann (Breitenhülle 35–70° über Land, `recommend.candidate_lat_range("picea_abies")`), im Ausschnitt Europa + westliches Russland. Auf der Folie heißt das ausdrücklich „ein Beispiel“. Die t*-Karte in V3 verwendet denselben Ausschnitt und dieselben Marker. Wer B8 gelesen hat, liest V3 ohne neue Erklärung. Für den Kohlenstoff gibt es bewusst keine Karte (siehe B6).

Folien 7–11 bleiben. Neu sind die Kohlenstoffkurve B6, die Albedokarte B8 und der Kapitelabschluss B9.

### B1 · Trennblatt Bäume (7) — unverändert

### B2 · Was Bäume tun (8/9) — unverändert
→ Brücke: „Zwei Wirkungen reichen über den Standort hinaus: Kohlenstoff und Reflexion. Zuerst der Kohlenstoff.“

### B3 · Kohlenstoff-Aufnahme (10) — unverändert
→ Brücke: „Die vier Flüsse laufen auf völlig verschiedenen Zeitskalen.“

### B4 · C-Aufnahme über die Zeit (11) — unverändert
→ Brücke: „Einzeln messen ist aussichtslos — also das Netto-Ergebnis modellieren.“

### B5 · C-Aufnahme im Modell (12) — kleine Änderungen
Chapman-Richards × Störung, Fichte als Beispiel.
- **Wachstum hängt davon ab, was wo wächst.** Animationsschritt nach der Fichte: dieselbe Gleichung, die vier anderen Arten (Bild von Folie 34, `34_wachstumskurven_arten.csv`), jede Kurve mit ihrem Breitengrad beschriftet. Botschaft nur: „Gleiche Form, andere Zahlen.“ Ergebnisse je Art erst in Schale 4. Damit ist der orangefarbene Notizkasten („ggf. andere Bäume zeigen“) erledigt.
- **Störung hier mit fester Rate p₀.** Der Faktor e^{γ·ΔT} in der Gleichung von Folie 12 setzt eine Erwärmung voraus, die es in Schale 1 noch nicht gibt. Hier ausgrauen mit „→ Schale 3“, eingelöst in K13.
→ Brücke: „Was der Baum einlagert, hat er der Luft entnommen — jedes Jahr ein Stück.“

### B6 · NEU · Was der Baum der Luft entnimmt — eine Kurve für beide Orte
**Aussage:** C → CO₂ mit 44/12, Vorzeichen aus Sicht der Luft gedreht: ṁ_CO₂(t) = −(44/12)·ṁ(t). Über die Jahre aufsummiert: 163 kg CO₂ je Fichte bis 2150. Für Aachen und Archangelsk ist es *dieselbe* Kurve.
**Bild:** `figures/b6_kohlenstoff_kurve.png`. Eine Kurve, am Ende „163 kg“, daneben „gilt für ● Aachen ■ Archangelsk“. **Bewusst keine Karte:** Im Modell hängt das Wachstum an der Art, nicht am Ort, und eine Karte wäre überall gleich gefärbt.
**Kurz gesagt:** „Mit der Grenze um den Baum ist die naive Rechnung exakt: Was der Baum hat, fehlt der Luft — überall gleich.“ Beide Halbsätze sind Absicht. „Fehlt der Luft“ bricht K3 auf, „überall gleich“ bricht B8 auf.
**Fußzeile:** Gemeine Fichte, Störung mit heutiger Rate. Im Modell wächst eine Art überall gleich schnell.
→ Brücke: „Der zweite Austausch mit der Umgebung ist das Licht.“

### B7 · Albedo, Aufbau (13 + 14 zusammen)
Dunkler Baum gegen hellen Boden, dann die drei Varianten (hellerer Baum / hellerer Boden / mehr Sonne). Den Notizkasten streichen, sein Inhalt wird Sprechertext: „Je größer der Baum, desto mehr Boden verdeckt er.“ Die Varianten „hellerer Boden“ (Schnee) und „mehr Sonne“ sind genau die zwei Ortsgrößen, die auf der nächsten Folie die Karte färben.
→ Brücke: „Wie viel ist das in Watt — und wo?“

### B8 · NEU (ersetzt 15/16) · Was ein Baum zusätzlich absorbiert — Karte + Jahresgang
**Aussage:** Beim Licht ist es nicht überall gleich. Wie viel eine ausgewachsene Fichte zusätzlich schluckt, hängt am Ort, und zwar an Schnee und Sonne. Jahresmittel: **Aachen 44 W, Archangelsk 65 W.** Der Grund steht rechts. Aachen hat kaum Schnee, dort folgt der Effekt der Sonne (breites Maximum Mai–Juli, ≈ 80 W). Archangelsk hat im April eine scharfe Spitze (≈ 250 W), weil noch Schnee liegt und die Sonne schon hoch steht.
**Bild:** `figures/b8_albedo_jahreskarte.png`.
- *links:* Karte Europa + westliches Russland, Jahresmittel je Baum. Gefärbt sind nur lokal gemessene Zellen (Duveiller), das übrige Fichtengebiet ist grau („nicht gemessen“). Die Farbskala reicht von 20 bis 100 W, weil sich fast alle Werte zwischen 30 und 100 W ballen. Bei einer Skala ab 0 verschwindet der Nord-Süd-Unterschied, obwohl 44 gegen 65 W am Ende 20 Jahre t* ausmachen.
- *rechts:* Monatswerte beider Orte (ungeglättet) und gestrichelt die Jahresmittel.
**Kurz gesagt:** „Kohlenstoff ist überall gleich, Licht nicht: Wo Schnee liegt und die Sonne kräftig ist, schluckt der Baum am meisten.“
**Beobachtung für den Sprechertext:** Im Jahresmittel unterscheiden sich die Orte weniger, als der Jahresgang vermuten lässt, weil die dunklen Monate die Frühjahrsspitze teilweise ausgleichen. Der Unterschied ist trotzdem groß genug, um t* um 20 Jahre zu verschieben (K12).
→ Brücke: „Und über die Jahre wächst dieser Effekt mit der Krone mit.“

### B9 · NEU · Was der Baum mit seiner Umgebung tauscht — Kapitelabschluss
**Aussage:** Zwei Zeitreihen in zwei Währungen, an beiden Orten. Links die CO₂-Entnahme [kg]: *eine* Linie, an beiden Orten gleich. Rechts das zusätzlich absorbierte Licht [W], das mit der Krone wächst (f(t)): *zwei* Linien, Archangelsk über Aachen. Welcher Effekt überwiegt, lässt sich an der Grenze des Baums nicht entscheiden. Kilogramm und Watt lassen sich nicht verrechnen, und was das CO₂ in der Luft bewirkt, liegt außerhalb dieser Grenze.
**Bild (Mockup):** zwei Plots, gleiche Zeitachse 2025–2150, links grün, rechts orange. Das sind schon die Farben von φ_CO₂ und φ_α ab K10. Daten: links aus B6, rechts f(t) × Jahresmittel aus B8. In der Mitte „⚖ ?“. Das Schalen-Icon zeigt die innerste Schale gefüllt und einen Pfeil nach außen.
**Kurz gesagt:** „Der Baum ist nicht allein. Um seine Wirkung zu bewerten, müssen wir die Grenze erweitern.“
→ Brücke ins Kapitel Klima.

```
┌─ Was der Baum mit seiner Umgebung tauscht ──────────────── ◉○○○○ 🌲 ─┐
│   CO₂ aus der Luft geholt [kg]          zusätzlich absorbiert [W]      │
│   0 ┼──────────────►t                   ┌────────── 65,3 Archangelsk   │
│     │╲   Aachen = Archangelsk  ⚖ ?      │     ╱‾‾‾‾‾‾ 43,6 Aachen      │
│     │ ╲                                 │   ╱ ╱‾‾‾‾‾‾                  │
│     │  ‾‾‾‾╲______________              │__╱╱                          │
│                                          0 ┼──────────►t               │
│  ┌Kurz gesagt──────────────────────────────────────────────────────┐  │
│  │ Kilogramm gegen Watt — an der Grenze des Baums nicht             │  │
│  │ entscheidbar. Der Baum ist nicht allein: Grenze erweitern.       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### Abbildungen und optionale Clips (Stand 2026-10-01)
- **Im Hauptteil, statisch:** `figures/b6_kohlenstoff_kurve.png` und `figures/b8_albedo_jahreskarte.png`, je 1920 × 900 px.
- **Entscheidung gegen die Videos im Hauptteil:** Die Kohlenstoffkarte ist per Konstruktion überall gleich gefärbt. Sie ist eine verkleidete Kurve und lenkt den Blick auf eine Modellschwäche („wächst die Fichte in Spanien wie in Archangelsk?“). Der Monatsclip zur Albedo zeigt den richtigen Mechanismus, aber die Folge braucht das *Jahresmittel*, und zwei Drittel der Karte wären ohne Jahresgang grau. Ein Loop konkurriert außerdem mit dem Vortragenden. Eine statische Jahreskarte bereitet die t*-Karte in V3 besser vor, weil beide denselben Typ haben: ein Wert je Ort.
- **Optional (Backup oder als 6-Sekunden-Einschub auf Nachfrage „warum Frühjahr?“):** `figures/b6_kohlenstoff_karte.mp4` und `figures/b8_albedo_karte.mp4` mit Posterbildern.
- **Neu erzeugen:** `.venv/bin/python scripts/build_animations.py` (Code `src/nbs/animations.py`, Tests `tests/test_animations.py`). `imageio-ffmpeg` steckt nur in der venv, nicht in `pyproject.toml`, und wird nur für die Clips gebraucht.
- **Gemeinsamer Rahmen für alle Karten des Vortrags:** Ausschnitt 12°W–65°E, 35–72°N. Marker Aachen `#2f6fb7` (Kreis), Archangelsk `#b8357f` (Quadrat). Rampen grün (Kohlenstoff) und orange (Albedo), gegen den Folienhintergrund `#f3eee6` geprüft.

---

## 4 · Kapitel KLIMA — Schalen 2 und 3: der Baum im Erdsystem

*Erst die Masse (wohin geht das CO₂?), dann die Energie (was bewirkt es?), dann die Antwort der Erde. Jede Rückwirkung des Systems kommt genau an der Stelle, an der ihre Schale dazukommt.*

### K1 · Trennblatt Klima (17)
Untertitel: „Der Baum ist nicht allein“.

### K2 · NEU · Der Baum ist Teil eines Systems
**Aussage:** Was der Baum tauscht, landet in Teilen der Erde, die selbst reagieren: Luft, Ozean, Landbiosphäre und am Ende die Strahlung ins All. Um den Netto-Effekt zu sehen, ziehen wir die Grenze in zwei Schritten weiter. Zuerst um den Kohlenstoffkreislauf: Wo bleibt das CO₂? Dann um die ganze Erde: Was macht es mit der Energie?
**Bild:** das Schalenbild aus Abschnitt 1 als Grafik, groß, Schalen 2 und 3 hervorgehoben, 4 und 5 blass.
→ Brücke: „Schale 2: Was passiert mit dem CO₂, das der Baum der Luft entnimmt?“

### K3 · Schale 2 · Eine Tonne raus ist nicht eine Tonne weg (Rebound, alt B7 / Folie 18)
**Aussage:** Ozean und Landbiosphäre stehen mit der Luft im Austausch. Seit der Industrialisierung haben sie rund die Hälfte unserer Emissionen geschluckt. Fehlt der Luft CO₂, schlucken sie weniger und geben teilweise zurück. Von einem entnommenen Kilogramm fehlt der Luft nach der Zeit t nur noch der Anteil g_C(t). Das ist der erste Rebound.
**Bild:** g_C(t) nach einem Puls von 1 kg, 0–125 a. Fläche zwischen 100 % und Kurve beschriftet mit „von Ozean und Land zurückgegeben“. Vorlage `fig_irf.png`, Daten `nbs.response.green_carbon("ssp245")`.
**Vereinfachung:** Im Hauptteil nur *eine* Kurve. Ob das die SSP2-4,5-Kurve (70 % nach 75 a) oder die vorindustrielle Joos-Kurve (44 %) ist, hängt davon ab, wo der Hintergrund eingeführt wird: Die SSP-Kurve setzt die übrige Menschheit voraus, die erst in K8 auftritt. **Vorschlag:** hier Joos (der Kreislauf allein), in K8 dann die Bemerkung „und in einer volleren Welt bleibt die Lücke sogar länger offen“. Die Rechnung selbst bleibt bei SSP2-4,5.
→ Brücke: „Der Baum entnimmt aber jedes Jahr, nicht einmal.“

### K4 · Schale 2 · Das CO₂-Profil in der Luft
**Aussage:** Jede Jahresentnahme aus B6 klingt mit g_C ab, und die Summe ist das CO₂, das der Luft wirklich fehlt. Zum Vergleich gestrichelt, was an der Grenze des Baums bilanziert wurde (B6). Der Abstand zwischen beiden ist der Rebound.
**Bild (Mockup):** oben klein die Balken aus B6. Darunter dünne abklingende Einzelkurven, dick die Summe Δm_CO₂(t), gestrichelt −(44/12)·m(t). Vorlage `fig_faltung.png`, Daten `nbs.response.convolve_response`.
**Gleichung:** Δm_CO₂(t) = ∫ g_C(t−t′) · ṁ_CO₂(t′) dt′
**Kurz gesagt:** „Schale 1 sagt: Was im Baum ist, fehlt der Luft. Schale 2 sagt: Es fehlt deutlich weniger.“
→ Brücke: „Jetzt wissen wir, wie viel CO₂ fehlt. Was das bewirkt, ist eine Frage der Energie — Grenze um die ganze Erde.“

```
┌─ Das CO₂-Profil in der Luft ────────────────────────────── ◉◉○○○ 🌡 ─┐
│  ṁ_CO₂ [kg/a]   ▁▂▄▆▇▇▆▅▄▄▃▃▂▂▂▂▁▁▁▁▁   (aus B6)                      │
│  [kg]  0 ┼──────────────────────────────────────────────►t            │
│          │╲╲╲ dünn: jede Jahresentnahme klingt mit g_C ab             │
│          │ ╲ ╲╲__________________________  ← fehlt der Luft wirklich  │
│          │  ╲  ╲                   ↕ Rebound: Ozean + Land            │
│          │   ╲___ ___ ___ ___ ___ ___ ← Bilanz am Baum (Schale 1)     │
│   Δm_CO₂(t) = ∫ g_C(t−t′) ṁ_CO₂(t′) dt′                               │
└───────────────────────────────────────────────────────────────────────┘
```

### K5 · Schale 3 · Grenze um die Erde: Energiebilanz und Antrieb (19 fertigstellen + 22 + 21)
**Aussage:** Kontrollvolumen um Erde und Atmosphäre. Über die Grenze geht nur Strahlung, Masse- und Arbeitsterm fallen weg: dU/dt = Q̇_kurz − Q̇_lang, mit Q̇_kurz := einfallend − reflektiert.
**Die Definition, die das Kapitel trägt:** **Antrieb φ** = wie stark ein Eingriff „rein − raus“ verschiebt, *bevor* sich die Erde erwärmt [W/m²]. Zwei Hebel: Die Albedo dreht am reflektierten Teil, CO₂ dreht an Q̇_lang.
**Bild:** die Erdgrafik von Folie 19 (Erde, Atmosphärenring, Baum, CO₂) mit drei Pfeilen. Daneben die Gleichung, Massen- und Arbeitsterm durchgestrichen. Unter Q̇_kurz,refl ein oranger Pfeil („Albedo“), unter Q̇_lang ein grüner („CO₂“). Die roten Arbeitsnotizen ersetzen.
**Ein Satz zur Verdunstung** (Folie 26 → Backup): „Verdunstung verschiebt Energie nur innerhalb dieser Grenze. Lokal kühlt sie, global steckt sie in den Rückkopplungen.“
Bei Bedarf als zwei Folien (Grenze | Bilanz); auf einer Folie ist die Aussage aber kompakter.
→ Brücke: „Der Albedo-Hebel ist der einfache.“

### K6 · Schale 3 · Albedo: aus Watt am Baum werden Watt pro m² Erde (25, umgebaut)
**Aussage:** Die Jahresmittel aus B8 (43,6 W Aachen, 65,3 W Archangelsk) sind schon Energie. Mit zwei Korrekturen werden sie zum Antrieb: Von dem, was der Baum nicht reflektiert, wären rund 80 % durch die Atmosphäre nach oben gekommen (τ_atm), und es wird auf die ganze Erdoberfläche bezogen.
**Gleichung:** φ_α(t) = τ_atm · ΔQ̇_Baum(t) / A_Erde
**Bild:** Zwei Glühbirnen „43,6 W“ und „65,3 W“ am Baum → „× 0,8 nach oben“ → „÷ 5,1·10¹⁴ m²“ → φ_α in W/m². Darunter φ_α(t), das ΔQ̇_Baum(t) ohne Verzögerung folgt.
**Kurz gesagt:** „Die Albedo wirkt sofort und nur so lange, wie der Baum steht. Einen Rebound gibt es hier nicht.“
→ Brücke: „Beim CO₂ gibt es keine Watt, nur Kilogramm. Was macht CO₂ mit der Abstrahlung?“

### K7 · Schale 3 · Was CO₂ mit der Abstrahlung macht (NEU)
**Aussage:** In einem Band um 15 µm ist CO₂ für Wärmestrahlung undurchsichtig. Dort strahlt nicht der warme Boden ins All ab, sondern kalte Luft in großer Höhe, und kalte Luft strahlt weniger. Die „Kerbe“ im Spektrum ist fehlende Abstrahlung. Mehr CO₂ → breitere Kerbe → weniger Q̇_lang. Der Baum macht die Kerbe ein winziges Stück schmaler.
**Bild (Mockup):** Abstrahlspektrum der Erde mit zwei Planck-Referenzen (≈ 288 K Boden, ≈ 220 K Höhe) und der CO₂-Kerbe, dazu eine zweite Kontur für mehr CO₂. Schematisch in `plots.py` (Planck + Bandmodell) oder als gemessenes Spektrum (Nimbus-4 IRIS, Hanel et al. 1972).
**Sprechertext-Alternative:** „CO₂ hebt die Höhe, aus der die Erde in diesem Band abstrahlt. Höher heißt kälter, kälter heißt weniger.“
→ Brücke: „Die Mitte der Kerbe ist aber schon schwarz. Was bringt das nächste Kilogramm?“

```
┌─ Was CO₂ mit der Abstrahlung macht ────────────────────── ◉◉◉○○ 🌡 ─┐
│  Leistung                                                           │
│   │      ...‾‾‾‾‾‾‾‾...             ← Planck, Boden 288 K           │
│   │   .‾‾              ‾‾.                                          │
│   │  /  ____      ____    \         ← tatsächliche Abstrahlung      │
│   │ /  /    \____/    \    \                                        │
│   │/  /   ▓▓ CO₂ ▓▓     \   \       ▓ Kerbe: hier strahlt kalte     │
│   │  /    ░ mehr CO₂ ░    \  \        Höhenluft, nicht der Boden    │
│   └──────────── 15 µm ─────────────► Wellenlänge                   │
└─────────────────────────────────────────────────────────────────────┘
```

### K8 · Schale 3 · Der Baum ist nicht allein in der Atmosphäre (NEU, ersetzt den Kern von 24)
**Aussage:** Zweiter Rebound, diesmal von der übrigen Menschheit. Die Kerbe wächst nur noch an den Rändern, deshalb steigt der Antrieb logarithmisch: φ = 5,35 · ln(C/C₀). Ein Kilogramm wirkt so viel, wie die Steigung dieser Kurve angibt. Die Steigung wird flacher, je voller die Atmosphäre ist, und unter SSP2-4,5 füllen die übrigen Emittenten sie von 424 auf 624 ppm.
**Bild (zweigeteilt):** links φ über C (280–700 ppm) mit Tangenten bei 424 ppm (2025) und 624 ppm (≈ 2150). Rechts A_CO₂(t) unter SSP2-4,5, fallend von 1,61·10⁻¹⁵ auf 1,10·10⁻¹⁵ W m⁻² kg⁻¹, gestrichelt die Lehrbuchkonstante 1,76·10⁻¹⁵. Daten: `nbs.forcing.phi_co2_background`, `nbs.response.background_co2_ppm`.
**Kurz gesagt:** „Wer heute pflanzt, pflanzt in eine Atmosphäre, in der jedes Kilogramm später weniger bewirkt.“ Sprechertext dazu (siehe K3): In derselben volleren Welt nehmen Ozean und Land schlechter auf, deshalb bleibt die Lücke länger offen. Das wirkt zugunsten des Baums.
Löst nebenbei den Widerspruch, dass Folie 24 eine konstante A_CO₂ herleitet, alle Ergebnisse aber logarithmisch gerechnet sind.
→ Brücke: „Jetzt haben wir beides: wie viel CO₂ fehlt (K4) und was jedes Kilogramm wert ist (K8).“

### K9 · Schale 3 · Vom CO₂-Profil zum Antrieb
**Aussage:** φ_CO₂ ist das CO₂-Profil mal die Wirkung je Kilogramm. In der Formel steht keine Fläche, weil CO₂ sich global mischt. Bei der Albedo (K6) stand dagegen A_Erde im Nenner, und der Wert hing am Standort.
**Bild:** drei gestapelte Mini-Plots mit gemeinsamer Zeitachse: Δm_CO₂(t) **×** A_CO₂(t) **=** φ_CO₂(t).
→ Brücke: „Beide Kanäle sind jetzt in derselben Währung.“

### K10 · Schale 3 · Die Frage aus B9, beantwortet: der Antrieb eines Baums (32, oberes Panel)
**Aussage:** φ_α (orange) steigt sofort an und bleibt, φ_CO₂ (grün) wird langsam negativ. Die grüne Kurve ist an beiden Orten dieselbe, die orange nicht. Deshalb wird die Summe in Aachen 2036 dauerhaft negativ, in Archangelsk erst 2053.
**Bild:** Antriebs-Panel wie Folie 32, aber zwei kleine Plots nebeneinander (Aachen | Archangelsk) mit gleicher y-Achse. Fläche unter der Summe rot bis zum Vorzeichenwechsel, danach blau. Neu rechnen: `run_single_tree("picea_abies", lat, delta_alpha=alpha_q_product[Zelle], q_sw=1)`.
**Kurz gesagt:** „Kilogramm gegen Watt ist entschieden: erst wärmt das Licht, dann kühlt der Kohlenstoff — in Aachen ab 2036, in Archangelsk ab 2053.“
Folie 27 (Flussdiagramm) → Backup oder als 10-Sekunden-Zusammenfassung direkt danach.
→ Brücke: „Ein Antrieb ist noch keine Temperatur. Wie antwortet die Erde?“

### K11 · Schale 3 · Die Erde antwortet (23 + 29 zusammen, 28 → Backup)
**Aussage:** Eine wärmere Erde strahlt mehr ab (Λ·T), und sie reagiert träge (C): C·dT/dt = φ − Λ·T. In Λ und C stecken Wasserdampf, Wolken, Eis und Ozean, das Erdsystem in zwei Zahlen. Die Antwort auf einen Energiestoß ist g_T, mit derselben Struktur wie g_C in Schale 2.
**Bild:** zwei Mini-Plots im selben Layout. Links g_C (grau, „kennen wir aus Schale 2“), rechts g_T (`29_temperaturantwort_gT_illustrativ.csv`). Darunter beide Faltungsintegrale untereinander.
→ Brücke: „Damit ist die Kette geschlossen. Was kommt für die Fichte heraus?“

### K12 · Schale 3 · Ergebnis: ein Baum, voll bilanziert (32 unten; 30/31 aufgelöst)
**Aussage:** Fichte, gepflanzt 2025, SSP2-4,5: In Aachen kühlt sie ab t* = 2039 dauerhaft (14 Jahre Erwärmung), in Archangelsk ab t* = 2059 (34 Jahre). Der Versatz zum Antrieb (3 bzw. 6 Jahre) kommt von der Trägheit C. Größenordnung je Baum: einige 10⁻¹⁵ K Erwärmung, dann bis 2150 etwa −5·10⁻¹⁴ K. Das einmal laut sagen.
**Bild:** ΔT_CO₂, ΔT_α, ΔT netto, wieder als zwei Plots nebeneinander. Erwärmungsphase rot schattiert, graue Marke beim Vorzeichenwechsel des Antriebs. Die Setzungen (Art, Ort, Szenario) als Untertitel; die Textfolie 30 entfällt.
→ Brücke: „Und das System wirkt auf den Baum zurück.“

### K13 · Schale 3 · Die Erwärmung wirkt auf den Baum zurück (33, vereinfacht)
**Aussage:** Dritter Rebound. In Schale 1 hatte die Störung eine feste Rate. Jetzt ist T bekannt, und die Störungsrate wächst mit der Erwärmung: p = p₀·e^{γT}. Wer 60 Jahre später pflanzt (2085 statt 2025), wartet länger auf t*, als er gewartet hat: Aachen 2039 → 2107 (+68 Jahre), Archangelsk 2059 → 2134 (+75 Jahre). Die Werte sind mit dem vollen Modell gerechnet. Welcher Anteil auf γ entfällt und welcher auf die vollere Atmosphäre, zeigt die Leiter in K14.
**Bild:** t* je Pflanzjahr 2025/45/65/85 als gruppierte Balken (Aachen | Archangelsk), Diagonale „t* = Pflanzjahr“ als Referenz. Linkes und mittleres Panel von 33 → Backup.
→ Brücke: „Was hat jede Schale an der Antwort geändert?“

### K14 · Was jede Schale gekostet hat (Leiter, aus Backup 60, neu gerechnet) — Kapitelabschluss
**Aussage:** Die Leiter fasst Bäume und Klima zusammen. Jede Sprosse ist eine Erweiterung der Grenze. Mit der Grenze um den Baum kühlt die Fichte ab Jahr 1, mit allen Schalen in Aachen ab 2039, in Archangelsk ab 2059.
**Bild:** Wasserfall auf t*, zwei Reihen (Aachen, Archangelsk), kumulativ, **in Schalen-Reihenfolge** (heute: Albedo, Störung, Senke, Hintergrund). Neu rechnen mit `nbs.config`/`nbs.variants`:
1. **Schale 1:** Kohlenstoff im Baum, Störung mit fester Rate, konstante Wirkung je kg (= naive Rechnung)
2. **Schale 1:** + Albedo
3. **Schale 2:** + Rebound von Ozean und Land (g_C)
4. **Schale 3:** + volle Atmosphäre: jedes kg wirkt weniger (log, Hintergrund)
5. **Schale 3:** + Erwärmung erhöht die Störung (γ)
Unter jeder Sprosse das Schalen-Icon mit der jeweils gefüllten Schale.
**Achtung:** Die Zwischenwerte ändern sich gegenüber heute, weil die Leiter kumulativ ist und die Reihenfolge wechselt. Endpunkte 2039 und 2059. Ob Schritt 5 im heutigen Modell einzeln schaltbar ist, prüfen (γ = 0 setzen).
→ Brücke: „Das war ein Baum an einem Ort. Schale 4: alle Bäume auf der ganzen Landfläche.“

---

## 5 · Kapitel VERGLEICH — Schalen 4 und 5

*Schale 4: von einem Baum auf die ganze Landfläche. Schale 5: Aufforstung neben den anderen Wegen, CO₂ zu entnehmen.*

### V1 · Trennblatt Vergleich (39)
Untertitel: „Alle Bäume, alle Wege“.

### V2 · Schale 4 · Dieselbe Kette, andere Orte (35, neues Bild)
**Aussage:** Hier kommt kein neues Konzept dazu, nur die Auswertung. Dass Wachstum (B5) und Albedo-Wirkung (B8) vom Standort abhängen, ist seit Schale 1 bekannt. Jetzt läuft die vollständige Kette aus Schale 2 und 3 für jeden Standort durch. Erst die Fichte über ihr ganzes Gebiet, dann alle fünf Arten. Die heutigen Zahlen (Fichte 60°N 45 a, Rotbuche 14 a, Kiefer 11 a, Eukalyptus und Tropen 0 a) stammen aus der Breitentabelle und müssen mit den Zellwerten neu gerechnet werden (siehe Offene Punkte).
**Bild:** Das heutige Bild zeigt nur die Fichte sichtbar über Null. Ersetzen durch horizontale Balken „Erwärmungsphase [Jahre]“, eine Zeile je Art, sortiert nach Breite, Balken von 2025 bis t* (`35_temperatur_arten.csv`).
→ Brücke: „Und auf der ganzen Landfläche?“

### V3 · Schale 4 · Die Karte: wann kippt jede Fläche? (37)
t* je Rasterzelle. Tropen kippen im Median 2025, boreale Zellen im Median 2059, und 4,8 % der borealen Zellen kippen bis 2150 gar nicht.
**Bild:** **Erstes Bild = derselbe Kartenausschnitt wie B6/B8**: nur das Fichtengebiet, eingefärbt nach t*, mit den Markern Aachen und Archangelsk. Das Publikum kennt den Rahmen und liest nur die neue Farbe. Zweites Bild (Animationsschritt): alle Arten, je Zelle die zugeordnete, auf der ganzen bepflanzbaren Fläche. Farbskala auf 4 Klassen vereinfacht (sofort · bis 2050 · bis 2100 · nicht bis 2150). Hinweis zum synthetischen Streumuster in die Fußzeile.
→ Brücke: „Wenn man je Ort die beste Art wählt?“

### V4 · Schale 4 · Wo ist Platz — und was gehört dorthin? (40, vereinfacht)
0,95 Gha bepflanzbar, je Zelle die Art mit der stärksten Kühlung je Hektar bis 2100. Durch die Artenwahl kühlt es 25 % stärker als bei Zuordnung nach Breitenband.
**Bild:** nur die Karte, groß. Das Balkendiagramm rechts durch die eine Zahl „+25 %“ ersetzen.
→ Brücke: „Was ergibt das in Summe?“

### V5 · Schale 4 · Vom Rohwert zum Potenzial (38, als Wasserfall)
205 GtC (Bastin) → 81 GtC (Literaturkorrektur) → 78,2 GtC auf 0,93 Gha (Landmaske, Albedo-Filter, Störungspuffer) → **0,24 K** Abkühlung bis 2150.
**Bild:** Wasserfall mit hängenden Abzügen, Literaturschritte grau, Modellschritte farbig. Weil die Modellschritte in GtC winzig sind, rechts groß das Endergebnis in Kelvin.
→ Brücke: „Ist 0,24 K viel?“

### V6 · Schale 4 · Reicht das? Der Temperaturpfad (NEU, ersetzt das Bild von 42)
**Aussage:** Unter SSP2-4,5 liegt die Welt weit über 1,5 °C. Alle bepflanzbaren Flächen zusammen ziehen die Kurve um 0,24 K nach unten. Um ab 2050 dauerhaft unter 1,5 °C zu bleiben, bräuchte es das 10,3-Fache dieser Fläche, rund 75 % des eisfreien Landes.
**Bild (Mockup):** x = 2025–2150, y = Erwärmung [°C]. Grau SSP2-4,5 (`fair_module.run_fair_baseline`), grün dieselbe mit voller Aufforstung, gestrichelt 1,5 °C. Die Umkehrrechnung steht als Annotation daneben. Die heutigen Gha-Balken → Backup.
**Kurz gesagt:** „Aufforstung ist ein Beitrag, kein Ersatz für Emissionsminderung.“
→ Brücke: „Schale 5: Wie schneidet die Alternative ab?“

```
┌─ Reicht das? ─────────────────────────────────────────── ◉◉◉◉○ ⚖ ─┐
│  °C                                                                 │
│  2,5┤                               ____‾‾‾‾‾‾  SSP2-4,5            │
│     │                      ____‾‾‾‾    ___‾‾‾‾  + alle Bäume        │
│  2,0┤             ____‾‾‾‾  ___‾‾‾‾‾          ↕ 0,24 K             │
│     │      __‾‾‾‾ ___‾‾‾‾                                           │
│  1,5┤- - -_‾-‾- - - - - - - - - - - - - - - - - - - 1,5 °C          │
│     └────────────────────────────────────────────► 2150            │
│   nötig für 1,5 °C ab 2050: 10,2 × Fläche ≈ 74 % des eisfreien Landes │
└─────────────────────────────────────────────────────────────────────┘
```

### V7 · Schale 5 · Woran man zwei Entnahmewege misst (43)
Dieselbe Systemgrenze für beide Wege: Netto-Wirkung am Oberrand der Atmosphäre, nicht die Tonne.
| | Baum | DAC |
|---|---|---|
| Netto-Wirkung | Albedo zieht ab, ortsabhängig | Emissionen der Energie ziehen ab |
| bis zur Wirkung | Jahrzehnte (t*) | ab Inbetriebnahme |
| Dauerhaftigkeit | Störung, wächst mit T | Leckage des Speichers |
| Ressource | Fläche | Energie |
Die Albedo-Zeile hervorheben: Diesen Posten hat nur eine Seite.
→ Brücke: „In Zahlen:“

### V8 · Schale 5 · Aufforstung gegen DAC (44, Platzhalter füllen)
**Bildvorschlag:** kumulierte Netto-Entnahme je Hektar über die Zeit, über den Antrieb in CO₂-Äquivalent zurückgerechnet. Kurven für Wald boreal (startet positiv, kippt spät), Wald tropisch und DAC mit PV auf derselben Fläche (Gerade ab Inbetriebnahme).
**Braucht von außen:** Energiebedarf je t CO₂, Emissionsfaktor der Energie, PV-Ertrag je ha. Bis die Zahlen da sind, bleibt es eine Strukturfolie.
→ Brücke: „Wie belastbar sind unsere Zahlen?“

### V9 · Wie belastbar ist das? (41 + 45 zusammengelegt)
Gegenprobe Hasler et al. 2024: Der Albedo-Offset liegt in derselben Größenordnung. Abweichungen: Die Kohlenstoffdichte ist etwa doppelt so hoch, Trockengebiete kann das Modell nicht abbilden. Links die Hasler-Tabelle auf 4 Zeilen gekürzt, rechts drei Grenzen des Modells. Die Langfassungen → Backup.
→ Brücke: „Also noch einmal die Rechnung vom Anfang.“

### V10 · Dieselbe Rechnung, noch einmal (46, nach Schalen gebaut)
Die Rechnung von Folie 4, eine Zeile je Schale:
- **Baum:** 1,6 Billionen Bäume à 183 kg CO₂ — stimmt, solange die Grenze um den Baum liegt.
- **+ Kohlenstoffkreislauf:** Ozean und Land geben einen Teil zurück, der Luft fehlt weniger.
- **+ Erde am Oberrand:** Die Albedo wirkt dagegen, jedes kg wirkt später weniger, und die Erwärmung erhöht die Störung. Boreal kühlt der Baum erst nach Jahrzehnten.
- **+ ganze Landfläche:** 78 GtC, 0,24 K. Für 1,5 °C bräuchte es das 10-Fache der Fläche.
**Bild:** links Folie 4 verkleinert und grau, rechts die vier Zeilen neben dem Schalen-Icon.
→ Brücke: „Was heißt das für die Frage von Folie 3?“

### V11 · Die Antwort hängt an der Grenze (47, umformuliert)
Drei Sätze:
1. *Der Baum ist kein Speicher, sondern Teil eines Systems.* Was er bindet, bewirkt erst im Kohlenstoffkreislauf und in der Energiebilanz etwas.
2. *Jede Schale nimmt etwas weg:* Rebound, Albedo, volle Atmosphäre, Störung.
3. *Was übrig bleibt, ist real, aber ortsabhängig und begrenzt* — ein Beitrag, kein Ersatz.
Kurz gesagt beantwortet Folie 3: „Warum Maschinen, wenn die Natur das kann? Weil die Natur es nur dort gut kann, wo kein Schnee liegt, nur langsam und nie in der Menge, die wir brauchen.“

### V12 · Abschluss (48)

---

## 6 · Folienbilanz

| Kapitel | heute (sichtbar) | neu |
|---|---|---|
| Einstieg | 6 | 6 |
| Bäume | 10 (7–16) | 10 (+B6 Karte, B9; 13/14 zusammengelegt, 15/16 durch die Albedokarte B8 ersetzt) |
| Klima | 19 (17–38 ohne ausgeblendete) | 14 |
| Vergleich | 10 (39–48) | 12 |
| **Summe** | **45** | **42** |

Ins Backup, nicht löschen: 26 Verdunstung · 27 Antrieb-Flussdiagramm (optional) · 28 Klimamodell-Diagramm · 30 Aufbau-Textfolie · 31 Eingangsgrößen · 33 linke/mittlere Panels · 36 Überleitung Fläche · Langfassungen von 41/45 · 42 Gha-Balken.

---

## 7 · Grafiken

| Folie | Grafik | Status | Datenquelle |
|---|---|---|---|
| B5 | m(t) + ṁ(t), danach fünf Arten (Folie 34) als Animationsschritt | anpassen | `12_vorrat_fichte_verlustterm.csv`, `31b_co2_fluss_fichte.csv` |
| B6 | Kurve: kumulierte Entnahme je Baum, gilt für beide Orte | **fertig** `b6_kohlenstoff_kurve.png` | `animations.carbon_curve_figure` |
| B8 | Jahreskarte (nur gemessene Zellen) ‖ Jahresgang beider Orte | **fertig** `b8_albedo_jahreskarte.png` | `animations.albedo_annual_map_figure` |
| B9 | kg (eine Linie) ‖ W (zwei Linien) nebeneinander | neu, aus B6/B8 | f(t) × Jahresmittel 43,6 / 65,3 W |
| K2 / alle | Schalenbild + Schalen-Icon | neu, Vektor auf der Folie | — |
| K3 | g_C (Joos) | anpassen (`fig_irf.png`) | `nbs.response.green_carbon_preindustrial` |
| K4 | Faltung: Einzelkurven + Summe + Schale-1-Linie | anpassen (`fig_faltung.png`) | `nbs.response.convolve_response` |
| K6 | φ_α(t) + Glühbirnen-Schema | neu | `nbs.forcing.phi_albedo` |
| K7 | Spektrum mit CO₂-Kerbe | neu, schematisch | Planck + Bandmodell oder IRIS |
| K8 | ln-Kurve mit Tangenten ‖ A_CO₂(t) | neu | `nbs.forcing.phi_co2_background`, `background_co2_ppm` |
| K9 | Δm_CO₂ × A_CO₂ = φ_CO₂ | neu, aus K4/K8 | — |
| K10 | φ_CO₂, φ_α, φ, Aachen ‖ Archangelsk | neu rechnen | `run_single_tree` mit Zellwert |
| K11 | g_C ‖ g_T | anpassen | `29_temperaturantwort_gT_illustrativ.csv` |
| K12 | ΔT-Zerlegung + Schattierung, Aachen ‖ Archangelsk | neu rechnen | `run_single_tree` mit Zellwert |
| K13 | t* je Pflanzjahr, zwei Orte | neu rechnen | `run_single_tree(..., plant_year=…)` |
| K14 | Leiter in Schalen-Reihenfolge | neu rechnen | `nbs.variants`, `nbs.config` |
| V2 | Erwärmungsphase je Art (Balken) | neu | `35_temperatur_arten.csv` |
| V3 | t*-Karte, erst nur Fichtengebiet im B6/B8-Rahmen, dann alle Arten, 4 Klassen | anpassen | `nbs.map_plots` |
| V4 | Empfehlungskarte ohne Balken | anpassen | `40_flaeche_je_art.csv` |
| V5 | Kaskade als Wasserfall + Kelvin | anpassen | `38_kaskade_potenzial.csv` |
| V6 | Temperaturpfad SSP2-4,5 ± Aufforstung | neu | `fair_module.run_fair_baseline` + Kaskaden-ΔT |
| V8 | Netto-Entnahme je ha: Wald vs. DAC | neu, wartet auf DAC-Zahlen | extern |

---

## 8 · Offene Punkte

1. **2 t vs. 183 kg je Baum** (Folie 4) — sonst vergleicht V10 zwei verschiedene Bäume.
2. **g_C in K3:** Joos (System ohne Hintergrund) zeigen, gerechnet wird mit SSP2-4,5. Die Abweichung (44 % vs. 70 % nach 75 a) im Sprechertext von K8 auflösen. Außerdem nennt Folie 18 andere Zahlen als ihr Sprechertext („nach hundert Jahren rund vierzig Prozent“), dort eine Zahl festlegen.
3. **Störung in Schale 1:** Die Gleichung auf Folie 12 enthält schon e^{γ·ΔT}. Mit der strikten Schalentrennung gehört dieser Faktor nach K13.
4. **Linear vs. logarithmisch:** Folie 24 leitet A_CO₂ konstant her, gerechnet wird logarithmisch. K8 löst den Widerspruch auf.
5. **Leiter neu rechnen** in Schalen-Reihenfolge und prüfen, ob γ einzeln schaltbar ist.
6. **Größenordnung je Baum:** ΔT ≈ 10⁻¹⁴ K. Das in K12 einmal laut sagen und bis Schale 4 bei „je Baum“ bleiben.
7. **Laufendes Beispiel neu rechnen.** Alle Einzelbaum-Ergebnisse im Deck (Fichte 60°N: 53,6 W, φ-Wechsel 2063, t* 2071, Pflanzjahr 2071 → 2146, Leiter) kommen aus der **Breitentabelle** (`fallback_delta_alpha`). Die Karten zeigen dagegen **Zellwerte** (Duveiller). Damit die Kurven zu den Markern auf der Karte passen, Aachen und Archangelsk mit dem Zellwert rechnen: `run_single_tree("picea_abies", lat, delta_alpha=alpha_q_product("picea_abies")[i, j], q_sw=1.0)`. Vorab gerechnet (SSP2-4,5, Standardkonfiguration):

   | | Aachen (50,8°N) | Archangelsk (64,5°N) |
   |---|---|---|
   | Albedo-Stufe der Zelle | lokal | lokal |
   | ΔQ̇_Baum, Jahresmittel, volle Krone | 43,6 W | 65,3 W |
   | Monatsmaximum | Mai, ≈ 80 W | April, ≈ 250 W |
   | φ dauerhaft negativ ab | 2036 | 2053 |
   | t* (gepflanzt 2025) | 2039 | 2059 |
   | t* gepflanzt 2045 / 2065 / 2085 | 2063 / 2086 / 2107 | 2089 / 2112 / 2134 |
   | Vorrat 2150 | 33,2 kgC | 33,2 kgC |

   Dieselbe Frage stellt sich für V2 (fünf Arten) und für die Kaskade: Rechnen die schon mit Zellwerten oder mit der Tabelle? Prüfen.
8. **Monatslücken der Albedo — behoben (2026-10-01).** Lokal gemessene Zellen hatten einzelne Monate ohne Wert (Fichte: 47 % der lokalen Zellen, v. a. Nov–Feb). Das Jahresmittel lief deshalb nur über die Monate mit Daten. Jetzt werden fehlende Monate zyklisch aus den Nachbarmonaten derselben Zelle interpoliert (`albedo_grid._interpolate_missing_months`), bevor das Jahresmittel gebildet wird. Die Werte im Deck verschieben sich leicht: Kaskade 78,2 → 78,6 GtC (Band 70,1–85,1), 0,2393 → 0,2411 K, Fläche 0,931 → 0,936 Gha, Umkehrrechnung 10,3 → 10,2-fach (≈ 74 %), Artenwahl +25,4 → +25,3 %. `tests/test_slide_numbers.py` schlägt dafür absichtlich fehl, bis die Folien angepasst sind.
   **Noch offen, nur für die Animation:** Die Monatswerte bleiben sprunghaft (Archangelsk April 248 W, Mai 44 W). Für die Schleife leicht glätten (zeitlich 3 Monate, räumlich 1 Zelle) und das in der Fußzeile sagen. Zahlen auf den Folien weiter aus den ungeglätteten Jahresmitteln.
9. **Beispielart:** Die Rotbuche hätte zu Aachen gepasst, kühlt aber fast überall sofort (laubwerfend, im Winter scheint der Schnee durch; Aachen t* = 2027, selbst Archangelsk 2034). Deshalb die Fichte. Das lässt sich in Schale 4 (V2) als Pointe nutzen: Die Art entscheidet mit.

