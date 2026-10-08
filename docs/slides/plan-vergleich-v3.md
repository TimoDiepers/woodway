# Plan: Vergleich-Kapitel und Schluss neu (Storyline v3)

Stand 2026-10-06. Ausführbar von einem KI-Agenten ohne Vorwissen aus dem Chat. Alles in **beiden**
Fassungen umsetzen: `docs/slides/dissvortrag_v2.pptx` und `docs/slides/html/dissvortrag_v2.html`.

> **Stand 2026-10-07: Klima-Kapitel neu geordnet.** Bäume enden mit kg gegen W (Frage); Klima: Impulsantwort des
> Kohlenstoffkreislaufs → Impulsantwort auf die CO₂-Aufnahme eines Baums → Strahlungsantrieb von CO₂ (neu, k6, Formeln
> φ = 5,35 ln C/C₀, A_CO₂ = ∂φ/∂m, φ_CO₂ = A_CO₂ Δm) → Strahlungsantrieb aus CO₂ und Albedo → Temperaturantwort
> (C dT/dt = φ − ΛT) → FaIR → Temperaturwirkung je Ort. „Gemeinsame Währung“ und „Erwärmung wirkt zurück“ im Backup.
> Titel durchgehend sachlich (siehe patch_klima-Mapping in der Notiz zum Build).
>
> **Stand 2026-10-07: Szenarien.** FaIR rechnet zusätzlich mit den CMIP7-Emissionen (`cmip7-VL` …, Eingaben in
> data/cmip7/fair-inputs); „Entnahme-Bedarf der Szenarien“ (v2s) zeigt alle sieben Welten, Bedarf und Bäume aus demselben
> Szenario. DAC: neue premise-Datenbanken REMIND-EU SSP2-PkBudg650 und SSP2-NPi (scripts/build_premise_scenarios.py,
> Projekt ei312_REMIND_EU), Ökobilanz `dac_lca_precompute.py --pathway`, Folie „DAC in drei Strompfaden“ (d6).
> FaIR-Folie: Störungsrechnung auf das Szenario (nicht „Welt ohne Bäume“). Hauptteil 40 Folien.
>
> **Stand 2026-10-06 spät: HTML umgesetzt, pptx noch offen.** Hauptteil 39 Folien. Im Kapitel Klima neu: „Ozean und Land antworten“, danach „Das Erdsystem rechnen“
> (Schema s_fair: CO₂-Fluss als Emission, Albedo als Antrieb, FaIR mit und ohne Bäume, ΔT = Differenz) (k3: Impulsantwort g_C gespiegelt für Emission
> und Entnahme, Formel), „Was der Luft wirklich fehlt“ nur noch aufsummiert mit Faltungsformel. Neu im Ergebnisteil vor dem
> DAC-Vergleich: „Alle Bäume zusammen, Jahr für Jahr“ (w2: FaIR-Zeitreihen, Netto-Anteil 85 % 2050 → 59 % 2100, „überall“
> ab 2061 schlechter) und „Wann pflanzen?“ (w3: 5 Jahre Warten kosten 2050 ein Fünftel, 2100 fast nichts). Gegenüber dem Plan:
> Kapitel 1–2 gestrafft: 9/10 eine Folie (letzter Klick blendet die lokalen Wirkungen ab), „Was der Baum mit seiner
> Umgebung tauscht“ (kg gegen W) und die Leiter „Was jede Erweiterung der Systemgrenze kostet“ im Backup.
> „Die Erde erwärmt sich träge“ führt den **Netto-Anteil je Baum** ein (gestrichelt nur CO₂; Aachen 65 %, Joensuu 32 %,
> Marabá 83 %); an ihm hängen „netto 62 Gt“ und der DAC-Vergleich. Kapitel 3 heißt „Baum und Maschine“:
> Fläche (mit 1,7 Bio. Bäumen gegen 2 Bio. der naiven Rechnung) → Alle Bäume Jahr für Jahr → Wann pflanzen → Bäume reichen nicht (59 % netto, 62 von 335 Gt)
> → DAC-Prozess → DAC-Rechnung (Netto-Anteil) → animierte DAC-Karte 2025–2100 (Vergleich Baum 58 %) → Rangfolge
> → „Auf dem Holzweg? Nein.“ → Methodentabelle (FaIR zitiert). Folie 31 (Rangkurve) und „Zeit zählt“ im Backup.
> Abgelöste Folien liegen live hinter `<!-- BACKUP:END -->` (ohne data-n). Die HTML ist die Quelle für die pptx.
> Achtung: `export_html_v2.py --backup` erst laufen lassen, wenn die pptx nachgezogen ist (Notizen per data-n).

---

## 1  Worum es geht

Der Vortrag heißt „Ingenieure auf dem Holzweg? Aufforstung als Klima-‚Technologie‘“. Das Intro endet mit
der Frage „Braucht es die Maschine überhaupt?“ (Folie 4). Das Vergleich-Kapitel beantwortet sie bisher mit
einem Pro-Ort-Wettbewerb „Baum oder DAC“. Das ist die falsche Frage, weil man an fast jedem Ort beides tun
kann (DAC braucht kaum Fläche) und weil das Modell keine Kosten rechnet.

**Neue Leitlinie (vom Autor so festgelegt):**

1. **Baum oder DAC?** Es gibt nicht genug Fläche, auf der Bäume kühlen. Bäume reichen nicht, wir brauchen
   **auch** DAC.
2. **Ingenieure sind nicht auf dem Holzweg.** DAC muss erst einmal aufgebaut werden, und das lohnt sich.
   Aber DAC geht **nicht überall** (zu kalt) und ist **nicht immer netto negativ** (fossiler Strom).
3. **Rangordnung für beide.** Wie beim Baum gibt es auch bei DAC eine Reihenfolge, wo zuerst und wo nie.
   Bäume: nur wo sie kühlen, am stärksten zuerst; nie, wo sie wärmen. DAC: zuerst, wo der Strom sauber ist;
   nie mit fossilem Strom und nicht im hohen Norden.
4. **Zeit.** DAC wirkt ab dem ersten Betriebsjahr, der Wald erst mit dem Wachstum. Deshalb Bäume früh
   pflanzen; sie bringen außerdem Mitnahmeeffekte (Lebensraum, Schatten, Verdunstung, Windschutz,
   Folie 9).
5. **Methodische Frage am Schluss:** Was hat es für diese Antworten gebraucht, und was fügt die Arbeit hinzu?
   Aus den bisherigen Folien synthetisieren (wachsende Systemgrenze, zeitaufgelöst, je Ort, gleicher Horizont
   und gleiche Klimakette für Baum und DAC).

Das Wort „Holzweg“ nur noch als Frage im Titel und in der Antwort („Nein — aber …“) verwenden, nicht als
Urteil über DAC.

---

## 2  Regeln, die überall gelten (nicht verletzen)

- **Eine Regel für alle Zahlen:** Baum = typischer Wald der Zelle (`nbs.landscape.assign_species`), gepflanzt
  2025, bewertet im Horizont 2100 (`nbs.constants.T_END = 2100`). Bedarf = CMIP7-Daten 2024–2100
  (Very Low 335 Gt). Zahlen nur aus `docs/slides/chart_data/fakten.json` (erzeugt von
  `scripts/export_slide_facts.py`) oder direkt aus `nbs`. Nie Zahlen aus Carbon Brief ablesen.
- **Laufende Beispielorte mit Länderkürzel** auf Folien und in Diagrammen: Aachen (DE), Joensuu (FI),
  Marabá (BR); im Ortsvergleich auch Krakau (PL), Peking (CN), Manaus (BR), Kinshasa (CD). In Sprechernotizen
  ohne Kürzel. Code: `Site.label` / `Place.label`.
- **HTML und pptx gleich halten.** Neue oder geänderte Folien immer in beiden. Diagramme und Karten werden
  in der HTML gezeichnet (ECharts) und als SVG in die pptx übernommen: `scripts/export_deck_svgs.mjs`
  (Diagramme/Karten, Dateien `docs/slides/figures/hex_<key>.svg/.png`) und `scripts/export_deck_schematics.mjs`
  (Inline-SVG-Schemata mit `data-export`, Ebenen je Klick). Einsetzen mit `build_map_slides.svg_picture`.
- **Folien nie löschen.** Nicht mehr gebrauchte Folien in der pptx ins Backup verschieben (Eintrag in
  `prs.slides._sldIdLst` hinter die Folie mit der Form `BackupTitel` verschieben). In der HTML die `<section>`
  aus dem Hauptteil entfernen; die Backup-Seiten erzeugt `scripts/export_html_v2.py --backup` aus der pptx.
- **Neue pptx-Folie im richtigen Kapitel:** `build_map_slides.new_slide_after(prs, ref, title)` nutzt das
  Layout der Nachbarfolie (Kapitel-Master). Danach Zip auf doppelte Namen prüfen.
- **Vor jedem Schreiben in die pptx:** prüfen, dass keine `~$dissvortrag_v2.pptx` existiert (PowerPoint offen),
  und eine Sicherung nach `docs/slides/workspace/` kopieren.
- **Notizen:** In der pptx pflegen. Die HTML übernimmt sie mit `uv run python scripts/export_html_v2.py --backup`
  (füllt `<aside class="notes" data-n="N">` aus der pptx). Nach jeder Änderung der Folienzahl: `data-n` im
  HTML-Hauptteil fortlaufend neu nummerieren und `MAIN_SLIDES` in `scripts/export_html_v2.py` anpassen.
- **Stil der Schemata:** wie die DAC-Schemata (flache Zeichnung, IBM Plex Sans, Kapitälchen-Labels, runde
  Nummern-Badges, Pillen `#efcfae`, Kästen `var(--paper-deep)`). Siehe Folien 9–12, 16, 17, 33, 34.
- **Wissenschaftlich ehrlich:** Annahmen auf der Folie oder in der Quelle nennen (u. a. schnelle
  Dekarbonisierung im Szenario REMIND-EU SSP2-NDC, keine Kosten im Modell).
- Keine Claude-Attribution in Commits. Nur committen, wenn der Autor es verlangt.

**Werkzeuge** (lokal, nicht in der Cloud verfügbar): Server `cd docs/slides/html && python3 -m http.server 8765`;
puppeteer liegt im Scratchpad (`NODE_PATH=<scratchpad>/node_modules`); LibreOffice (`soffice`) zum Rendern der
pptx; `uv run` für Python.

---

## 3  Zielstruktur (Hauptteil 40 Folien)

Folien 1–28 bleiben unverändert. Ab 29:

| Nr. | Titel | Status | Inhalt |
|---|---|---|---|
| 29 | Vergleich | anpassen | Kapitelfolie, Untertitel „Baum oder Maschine?“ |
| 30 | Wo Bäume hinkönnen | bleibt | Fläche (Karte v0) |
| 31 | Klug oder dumm gepflanzt | **neu** | Rangordnung Bäume, Kosten falschen Pflanzens |
| 32 | Bäume reichen nicht | überarbeiten | nur kühlende Fläche; → es braucht **auch** DAC |
| 33 | Wie eine Maschine CO₂ aus der Luft holt | bleibt | Schema |
| 34 | Wie wir DAC rechnen: je Ort und je Jahr | bleibt | Schema |
| 35 | Nicht überall, nicht immer netto negativ | **neu** | DAC-Karten: heute und Rangordnung |
| 36 | Zeit zählt | überarbeiten | DAC sofort, Wald langsam; Mitnahmeeffekte |
| 37 | Was wo zuerst — und was nie | **neu** | Tun/Lassen für Baum und DAC |
| 38 | Ingenieure auf dem Holzweg? | ersetzt „Die Antwort hängt an der Grenze“ | drei Antworten |
| 39 | Was es dafür gebraucht hat | ersetzt „Was diese Arbeit neu zeigt“ | methodische Synthese |
| 40 | Danke | bleibt | |

**Ins Backup verschieben** (pptx: hinter `BackupTitel`; HTML: aus dem Hauptteil entfernen):
„Einordnung: andere Studien“, „Was eine Maschine braucht“ (Energiekarte d1), „Wer wo entnehmen kann“ (d0),
„Heute: der Holzweg“ (v3), „DAC fährt mit der Energiewende mit“ (v4), „Die Maschine wird zur Messlatte“ (d4),
„Beides — in der richtigen Reihenfolge“. Die Ersetzten („Die Antwort hängt an der Grenze“,
„Was diese Arbeit neu zeigt“) ebenfalls ins Backup, nicht überschreiben.

---

## 4  Folie für Folie

### 29  Kapitelfolie Vergleich
- Untertitel ändern: „Baum oder Maschine?“ (pptx: Subtitle-Platzhalter; HTML: `<p class="rise">` in der
  Kapitel-Section). Motiv und Kapitelleiste bleiben.

### 31  Klug oder dumm gepflanzt (neu)
**Botschaft:** Wo gepflanzt wird, entscheidet mehr als wie viel. Ein Baum am falschen Ort ist schlechter als
keiner. Das ist die Rangordnung für Bäume.

**Zahlen** (mit Horizont 2100 bereits gerechnet; im Skript neu aus `nbs` holen, nicht abschreiben):

| Variante | Fläche | CO₂ brutto | netto nach Albedo | Kühlung 2100 global |
|---|---|---|---|---|
| nur wo der Baum kühlt | 0,42 Gha | 106 Gt | 62 Gt | −0,020 K |
| alle wiederbewaldbaren Flächen | 0,83 Gha | 155 Gt | 29 Gt | −0,009 K |

Rechenweg: `nbs.potential._masked_global_delta_t(mask, "ssp245")[-1]` (voll) und mit
`ModelConfig(albedo=False)` (nur CO₂); Masken `assign_species() != None` (alle) und
`... & np.isfinite(nbs.map_plots._breakeven_year_field("ssp245"))` (kühlend). Brutto = Kohlenstoff der
Kaskade (`nbs.potential.cascade()`, Schritt „Nicht-Wald-Biome ausgeschlossen“ bzw. „Nutzbares Potenzial“)
× 44/12; netto = brutto × (ΔT voll / ΔT nur CO₂).

**Grafik (neues Diagramm, Schlüssel `w1`):** zwei Balkenpaare oder ein „Doppelte Fläche, halbe Wirkung“-
Vergleich: links Fläche (0,42 / 0,83 Gha), rechts Kühlung 2100 (−0,020 / −0,009 K). Funktion in
`src/nbs/vergleich_figures.py` (`planting_choice_figure`), Eintrag in `chart_jobs()` in
`scripts/export_html_v2.py`. Optional darunter die Rangordnung als Satz: „zuerst die Tropen (Marabá (BR):
−65 · 10⁻¹⁵ K je Baum), nie im Norden und im Trockenen“.

**Takeaway:** „Wer nur dort pflanzt, wo der Baum kühlt, braucht die halbe Fläche und kühlt mehr als doppelt so
stark. Auf der anderen Hälfte frisst die Albedo mehr, als der Baum bindet.“

**Notizen:** Bogen zur Karte „Was ein Baum wo bewirkt“ (Folie 28); Rechenweg in „Falls Fragen kommen“.

### 32  Bäume reichen nicht (überarbeiten, Diagramm v2)
- Im Diagramm (`need_figure` in `src/nbs/vergleich_figures.py`) die Baum-Zeile umbenennen in
  „Bäume, nur wo sie kühlen (0,42 Gha)“ statt „alle nutzbaren Flächen“. Optional zweite Zeile „Bäume überall
  (0,83 Gha)“ mit netto 29 Gt, damit die Folie 31 nachklingt.
- Takeaway neu: „Selbst klug gepflanzt binden Bäume bis 2100 netto rund 62 Gt CO₂ — 18 % dessen, was das
  niedrigste Szenario braucht. Für mehr fehlt die Fläche, auf der Bäume kühlen. Es braucht also auch
  Maschinen.“
- Quelle: „nur Flächen, auf denen der Baum (typischer Wald, gepflanzt 2025) bis 2100 kühlt“.
- Notizen: beantwortet die Frage von Folie 4 („Braucht es die Maschine überhaupt?“): Ja.

### 33, 34  DAC-Schemata
Unverändert. Nur prüfen, dass der Text von 34 nicht mehr auf „Karte auf der nächsten Folie“ (Energiekarte)
verweist; ggf. auf Folie 35 umformulieren („Strom je Tonne 1,1 bis 1,9 MWh“).

### 35  Nicht überall, nicht immer netto negativ (neu)
**Botschaft:** DAC lohnt sich, aber wie beim Baum gibt es eine Rangordnung. Im hohen Norden geht es nicht
(Sorbens-DAC, kältester Monat unter −15 °C, rund 20 % des Landes). Mit heutigem Strom bleibt vielerorts
wenig, teils ist DAC netto emittierend. Zuerst dort, wo der Strom sauber ist.

**Grafik (neue Karte, Schlüssel `d5`):** zwei Weltkarten nebeneinander, Hexagon-Stil wie die anderen
Weltkarten (`nbs.map_fields`, 2°-Blöcke, `_keep_blocks`).
- Links „heute (Strom 2025)“: Anteil einer entnommenen Tonne, der netto bleibt,
  `nbs.dac.efficiency_grid(2025)`. Divergierende Skala mit Mitte 0: unter 0 = netto emittierend (warm, z. B.
  orange/rot), über 0 türkis bis dunkel. Grau = zu kalt (`~nbs.dac.dac_possible()`).
- Rechts „Rangordnung“: erstes Jahr, ab dem netto mindestens 80 % bleiben (Schwelle vorab festlegen und
  nennen), aus `efficiency_grid(y)` für y = 2025…2100; Skala früh (dunkel) → spät (hell); „nie bis 2100“
  eigene Farbe; zu kalt grau.
- Neue Map-Funktion in `src/nbs/map_fields.py` (in `MAPS` eintragen), Skelett-Figur für das Layout in
  `src/nbs/dac_figures.py` (Muster: `_world_map_skeleton` in `vergleich_figures.py`), Eintrag `d5` in
  `chart_jobs()`. Orte Aachen (DE), Joensuu (FI), Marabá (BR) markieren.
- Zahlen für den Text: Flächenanteil netto emittierend heute; Median heute; Anteil des Landes, der 2030 /
  2040 die 80 % erreicht; Werte der drei Orte. Aus den Grids berechnen, flächengewichtet
  (`nbs.grid.cell_area_m2`, Land = `np.isfinite(nbs.dac_climate.climate_grid()["t_mean_c"])`).
- Annahme auf der Folie nennen: Strommix REMIND-EU SSP2-NDC (heutige Zusagen), dekarbonisiert schnell.

**Takeaway (Entwurf):** „Ingenieure sind nicht auf dem Holzweg — die Maschine muss nur an den richtigen Ort.
Mit heutigem Strom bleibt im Median nur gut 40 % der Tonne; wo Kohlestrom läuft, emittiert DAC sogar.
Zuerst also dort, wo der Strom sauber ist; mit der Energiewende fast überall — nur nicht im hohen Norden.“
(Zahlen aus der Rechnung einsetzen.)

**Notizen:** Energie 1,1–1,9 MWh Strom je t mit Wärmepumpe (aus der alten Energiefolie), Strombedarf einer
Gigatonne ≈ 5 % der Weltstromerzeugung, Netzmittel statt Zusatzstrom (siehe `docs/methods/dac-modell.md`).

### 36  Zeit zählt (überarbeiten, Diagramm z1)
- Diagramm bleibt (Anteil der Entnahme bis 2100, den ein 2025 gepflanzter Baum schon geschafft hat; DAC
  sofort).
- Ergänzen: eine schmale Leiste mit vier Mitnahmeeffekten des Waldes (Icons/Zeilen aus dem Schema
  `s_baeume_tun`, Folie 9: Verdunstung, Windschutz, Lebensraum, Schatten), Überschrift „Was der Wald
  zusätzlich bringt“. Im HTML als Inline-SVG mit `data-export`, in die pptx über
  `scripts/export_deck_schematics.mjs` und `scripts/build_schema_slides.py` (Eintrag in dessen `SLIDES`).
- Takeaway neu: „DAC wirkt ab dem ersten Betriebsjahr, der Wald erst mit dem Wachstum: bis 2035 ein
  Sechstel, bis 2050 die Hälfte. Bäume also früh pflanzen — dort, wo sie kühlen. Dazu bringen sie, was
  keine Maschine kann: Lebensraum, Schatten, Verdunstung.“

### 37  Was wo zuerst — und was nie (neu)
Schema im Stil der Tun/Lassen-Karten (Inline-SVG, 2×2), Spalten **Baum** und **Maschine**, Zeilen
**zuerst** und **nie**. Jede Zelle: Titel, ein Satz, eine Zahl, Pille.
- Baum · zuerst: wo er am stärksten kühlt, früh (Tropen; Marabá (BR) −65 · 10⁻¹⁵ K je Baum) — Pille
  „0,42 Gha“.
- Baum · nie: wo er wärmt (Norden, Trockengebiete) — Pille „sonst halbe Wirkung“.
- Maschine · zuerst: wo der Strom sauber ist; mit der Energiewende fast überall — Pille mit Anteil, der
  heute ≥ 80 % erreicht.
- Maschine · nie: mit fossilem Strom (heute netto emittierend, z. B. Krakau (PL), Peking (CN), Kinshasa (CD) —
  Werte aus `vergleich_figures.dac_eta_at(place, 2025, 2020)` oder 2025-Mix) und im hohen Norden (zu kalt).
- Unterzeile: „Und keines von beiden ersetzt Emissionsminderung: zusammen zielen sie auf den Rest.“
- In die pptx über `export_deck_schematics.mjs` + `build_schema_slides.py` (Klick-Aufbau: Baum-Spalte,
  Maschinen-Spalte, Unterzeile).

### 38  Ingenieure auf dem Holzweg? (ersetzt „Die Antwort hängt an der Grenze“)
Drei Antwort-Kästen (Layout wie die bisherige Thesen-Folie, `cols`):
1. „Bäume reichen nicht“ — nur 18 % des niedrigsten Szenarios, und nur, wenn klug gepflanzt.
2. „Also auch Maschinen — aber an den richtigen Ort“ — sauberer Strom zuerst, nie mit fossilem Strom,
   nicht im Norden.
3. „Bäume jetzt, Maschinen mit der Energiewende“ — Zeit und Mitnahmeeffekte.
Kurz gesagt: „Nein, die Ingenieure sind nicht auf dem Holzweg — sie müssen erst noch hin. Für beide
Wege gilt: Wo und wann entscheidet mehr als wie viel.“

### 39  Was es dafür gebraucht hat (ersetzt „Was diese Arbeit neu zeigt“)
Methodische Synthese aus den bisherigen Folien; keine neuen Rechnungen. Drei Zeilen „gebraucht → zeigt“:
1. **Die Systemgrenze schrittweise erweitern** (Leiter, Folie 27): vom Baum über Ozean und Land, volle
   Atmosphäre und Rückkopplung → erst so wird sichtbar, dass von −158 in Aachen (DE) −35 bleiben.
2. **Je Ort und Jahr rechnen** (Karten 28, 30, 31, 35): Wachstum, gemessene Albedo mit Zeitverlauf,
   Störung; prospektive Ökobilanz je Region und Jahr → erst so entstehen Rangordnungen statt Mittelwerte.
3. **Ein Horizont und eine Klimakette für Baum und Maschine** (FaIR, Horizont 2100, Folie 36) → erst so
   lassen sich Tempo und Wirkung vergleichen; GWP100 und statische Bilanzen vergleichen Endzustände.
Abschließend ehrlich einordnen (aus den Notizen der alten Folie übernehmen): wer zeitaufgelöst oder je Ort
schon rechnet (Kirschbaum 2011, Weber 2024, Liang 2025; Hasler 2024, Rohatyn 2022), und was neu ist: die
Kombination. Grenzen nennen: keine Kosten, Netzmittel-Strom, statische Schneedecke, Klimanormal 2011–2020.

---

## 5  Umsetzung Schritt für Schritt

1. **Sicherung:** `docs/slides/dissvortrag_v2.pptx` nach `docs/slides/workspace/` kopieren; HTML-Datei ebenso
   (z. B. ins Scratchpad).
2. **Rechnen und Diagramme:** neue Funktionen `planting_choice_figure` (w1), DAC-Kartenfeld + Skelett (d5);
   `need_figure` anpassen. `uv run python scripts/export_html_v2.py --charts --only w1,d5,v2,z1`.
3. **HTML:** Sections für 31, 35, 37, 38, 39 schreiben (Muster: bestehende Sections; Karten mit
   `<div class="chart" data-chart="…">`, Schemata als Inline-SVG mit `data-export` und `data-step`); 32 und 36
   anpassen; Backup-Folien aus dem Hauptteil entfernen; Kapitel-Untertitel 29.
4. **pptx:** ein Skript `scripts/build_vergleich_v3.py` (Muster: `scripts/build_dac_slides.py`,
   `scripts/build_horizon_2100.py`): Folien ins Backup verschieben, neue Folien mit `new_slide_after`, Texte
   (`set_box`, `fit_box`), Notizen, Bilder (`svg_picture`). Vorher SVGs exportieren:
   `NODE_PATH=… node scripts/export_deck_svgs.mjs w1 d5 v2 z1` und
   `NODE_PATH=… node scripts/export_deck_schematics.mjs <neue Schema-Keys>`, dann
   `uv run python scripts/build_schema_slides.py` (Einträge ergänzen).
5. **Nummerierung:** `data-n` im HTML-Hauptteil fortlaufend; `MAIN_SLIDES = 40` in
   `scripts/export_html_v2.py`; `uv run python scripts/export_html_v2.py --backup`.
6. **Prüfen:**
   - HTML: Screenshots der Folien 29–40 (puppeteer, Sprung per Nummer + Enter) und ein Klick-Durchlauf
     ohne Fehler.
   - pptx: mit `soffice --headless --convert-to pdf` rendern und die Seiten 29–40 ansehen; Zip auf doppelte
     Namen prüfen.
   - Tests: `uv run pytest -q tests/test_slide_numbers.py tests/test_dac.py` (Erwartungen ggf. an neue
     Folien anpassen).
   - Querverweise: keine Folie verweist mehr auf ins Backup verschobene Inhalte („nächste Folie“, „Folie N“).
7. **Veröffentlichen:** HTML-Artefakt neu bauen und veröffentlichen (bestehender Link des Autors).

---

## 6  Offene Punkte für den Autor (nicht selbst entscheiden)

- Schwelle der DAC-Rangordnung (Vorschlag 80 % netto) bestätigen lassen.
- Ob „Klug oder dumm gepflanzt“ eine eigene Folie bleibt oder in Folie 32 aufgeht.
- Formulierung des Titels der Schlussfolie (38).
