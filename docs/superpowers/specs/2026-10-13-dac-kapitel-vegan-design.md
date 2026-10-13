# DAC-Kapitel neu: Spitze, Tempo, Kosten, vegane Welt

Stand 2026-10-13, abgestimmt mit Timo im Brainstorming.

## Ziel

Der Schluss des Vortrags (Kapitel 5, `deck/src/slides/05_dac.html`) erzählt neu:

1. DAC wird so optimiert, dass die Erwärmungsspitze über 1,5 °C so niedrig wie möglich bleibt und danach so früh wie möglich wieder 1,5 °C erreicht ist.
2. Nur ein schnellerer Ausbau senkt die Spitze; die Spitze zählt (Kipppunkte, Extremereignisse).
3. Die Kosten des optimierten Pfads werden im Nachgang berechnet und mit dem BIP der EU-27 und den expliziten fossilen Subventionen verglichen. Erwartung: DAC bleibt teuer.
4. Zwischenfazit: Tempo ist der Hebel.
5. Was sofort geht: Die ganze Welt ernährt sich ab 2026 vegan. Kein technisches Hindernis, keine direkten Kosten, schnelle Wirkung über Methan. Gezeigt werden die Kühlung, die Kurve über der Aufforstung, wie viel weniger DAC nötig ist und wie viel Geld das spart.

Erfolg: Alle Zahlen kommen aus einem Lauf von `scripts/build_zeitpfade_data.py` nach `deck/chart_data/zeitpfade.json`; die Folien zeigen nur diese Zahlen; der unsichere Teil (Wald auf frei werdenden Flächen) ist auf der Folie als solcher benannt.

## Festgelegte Annahmen

- **Bezug:** CMIP7 Very Low, Erwärmung über 1,5 °C bis 2100 (`overshoot_series()["noetig_k"]`), wie bisher.
- **Bäume ab 2026:** Das Bonn-Challenge-Tempo entfällt überall (Kapitel 4, Lücke für DAC, vegane Welt, Folien und Notizen). Alle Flächen werden 2026 gepflanzt. Einfache Annahme, auf der Folie so genannt.
- **Vegan sofort:** vollständig ab 2026, keine Übergangszeit (Grenzfall „was wäre drin“, so benannt).
- **Vegan mit Flächen:** Methan und N₂O fallen weg, und auf den frei werdenden Flächen wächst Wald nach unserem Baummodell. Die Flächen sind ausdrücklich der größere und unsicherere Teil (Radrapu 2025, Leip et al. 2019).
- **Frei werdende Flächen:** ab 2026 alle gleichzeitig, gleiche Regeln wie Kapitel 2–3 (typischer Wald nach Hasler 2024, Kohlenstoff Walker 2022, Tempo Cook-Patton 2020, Albedo); es zählt nur, was kühlt.
- **Kosten:** Okosun et al. 2026 (`COST_CASES`: Median, optimistisch, pessimistisch), reale EUR 2024, unverzinst; ausgewiesen als Jahreskosten in der Spitze und Summe 2026–2100.
- **Vergleichsgrößen:** BIP EU-27 2024 (Eurostat, rund 18 Bio. EUR); explizite fossile Subventionen nach IEA/OECD (auf der Folie). IMF inklusive impliziter Kosten (rund 7 Bio. USD 2022) nur in den Notizen.

## Folienbogen (Kapitel 5)

1. DAC-Modell: bleibt.
2. Optimierung: neues Ziel „niedrigste Spitze, dann so früh wie möglich zurück auf 1,5 °C“; Rahmen η, Speicher, Wachstum 20 %/a, Lebensdauer 20 a.
3. Wo und wann: Karte bleibt, neue Zahlen.
4. Ausbautempo: 20, 30, 50 %/a und ohne Grenze; Spitze und Rückkehrjahr je Fall; ein Satz, warum die Spitze zählt.
5. Was kostet das: Kosten des Hauptpfads (Spanne der drei Fälle) als Bio. EUR/a in der Spitze und Summe bis 2100, daneben Balken EU-27-BIP und fossile Subventionen.
6. Zwischenfazit: Tempo ist der Hebel.
7. Was geht sofort: Überleitung vegane Welt (Frage als Takeaway erlaubt).
8. Kühlung der veganen Welt: Temperaturpfad gestapelt nach Methan/N₂O und Wald auf frei werdenden Flächen; Hinweis auf die Unsicherheit der Flächen.
9. Vegan plus Bäume: die Kurve über der Aufforstungskurve, verbleibende Lücke.
10. Weniger DAC: Optimierung mit der kleineren Lücke, Kapazität und Spitze vorher und nachher.
11. Gesparte Kosten: DAC-Kosten mit und ohne vegane Welt, Differenz in Bio. EUR.
12. Finale: Text angepasst.

Sollte die vegane Welt die Lücke fast ganz schließen, zeigen die Folien 10–11 genau das.

## Bausteine

### 0. Bäume ab 2026 (`src/nbs/tree_paths.py`)

Die Pflanzung nach Bonn-Rate entfällt; alle Kohorten starten in `T_START`. `delta_t(...)` und `forcing(...)` liefern die Pfade für Pflanzung 2026. Danach `gap = noetig − Bäume` neu. Texte in `04_potenzial.html`, `05_dac.html`, `07_backup.html` und `deck/src/js/deck.js` ohne Bonn-Bezug.

### 1. Optimierung (`src/nbs/dac_optim.py`, vorhanden)

Hauptfall `solve_min_peak(gap, danach="frueh")`. Tempo-Fälle mit demselben Ziel: `growth` 1,2 / 1,3 / 1,5 und `growth=1e6, limit_start=False`. Ausgabe je Fall: Spitze, Rückkehrjahr (`ab_jahr`), Kapazität, Weltpfad, Länderanteile für die Karte.

### 2. Kosten im Nachgang (`src/nbs/dac_optim.py`, neu)

`path_cost(w, c=COST, rate=0.0) -> dict`: Weltpfad `w` [Gt/a je Jahr] mal `cost_per_gt(rate, c)`; Rückgabe Kosten je Jahr [Bio. EUR], `spitze_bio_a`, `summe_bio`, `eur_t`. Vergleichsgrößen als Konstanten mit Quelle (`EU27_BIP_BIO_EUR`, `FOSSIL_SUBV_BIO_EUR`; USD in EUR 2024 umgerechnet, Kurs mit Quelle).

### 3. Vegane Welt, Emissionen (`src/nbs/vegan.py`, neu)

- Tierhaltung je Land aus FAOSTAT Emissions Totals: CH₄ (Verdauung, Gülle), N₂O (Gülle, Weide-Dung), dazu der Futteranbau.
- Mehremissionen der Ersatzkost nach Poore & Nemecek 2018 (je Protein-Äquivalent) abziehen.
- Bereinigung gegen Very Low: Das Delta ist der Tierhaltungsanteil am AFOLU-CH₄/N₂O-Pfad des Very-Low-Szenarios (Anteil aus FAOSTAT, Zeitverlauf aus CMIP7), nicht der heutige Wert.
- FaIR-Lauf Very Low gegen Very Low minus Delta ab 2026 → `dt_gase(t)` [K].
- Gegenprobe: globale Summe gegen FAOSTAT und Ivanovich et al. 2023.

### 4. Vegane Welt, Flächen (`src/nbs/vegan.py` mit vorhandenem Baummodell)

- Weide je 0,5°-Zelle aus HYDE 3.3, Futteranteil der Äcker (Cassidy et al. 2013 oder FAOSTAT-Länderanteile), minus Mehrbedarf der Pflanzenkost → frei werdende Fläche je Zelle.
- Prüfen, ob Walker 2022 R/L+R/H diese Flächen ausschließt; Überlappung sonst abziehen.
- Baumkette wie Kapitel 2–3 auf diesen Zellen, nur kühlende Zellen, voller FaIR-Lauf → `dt_flaeche(t)` [K].
- Rohdaten unter `data/raw/` (gitignored), abgeleitete Raster in `data/vegan/`.

### 5. Zusammenführen (`scripts/build_zeitpfade_data.py`)

`gap_vegan = gap + dt_gase + dt_flaeche` (Abkühlung als negative ΔT). Darauf erneut Hauptfall der Optimierung und `path_cost`. Neuer Schlüssel `vegan` in `zeitpfade.json`: beide ΔT-Pfade, `gap_vegan`, Fall-Ergebnis, Kosten, Differenzen zu ohne vegan (Kapazität, Gesamtmenge, Kosten). Neuer Schlüssel `kosten_pfad` für Folie 5.

### 6. Deck und Doku

Folien 2–12 in `deck/src/slides/05_dac.html`, Diagramme aus `zeitpfade.json`. Methode in `docs/methods/vegan-modell.md`; `docs/methods/dac-modell.md` um Ziel und Kosten im Nachgang ergänzt.

## Fehler und Tests

- `path_cost`: bekannter Pfad, bekannte Summe; Null-Pfad → 0.
- Flächenbilanz: frei werdende Fläche ≤ Weide + Futteracker je Zelle; global plausibel (Größenordnung 2–3 Gha).
- Emissionsdelta: global gegen FAOSTAT-Summe der Tierhaltung (Toleranz in Test genannt).
- Optimierung ohne Lösung → Status `unmoeglich`, nie stilles Null.
- Bestehende Tests in `tests/test_dac_optim.py` bleiben grün.

## Nicht Teil davon

- Keine Übergangszeit der Ernährung, kein Teil-Szenario (flexitarisch).
- Keine Kosten der veganen Welt (Annahme: keine direkten Kosten, so benannt).
- Keine Verzinsung im Hauptfall.
