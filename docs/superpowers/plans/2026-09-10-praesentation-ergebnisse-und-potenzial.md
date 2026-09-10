# Präsentation: Ergebnisse und Potenzial — Implementierungsplan (Plan 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Platzhalterfolien 25–29 durch die tatsächlich gerechneten Ergebnisse ersetzen und die Herleitungsfolien auf die Zahlen bringen, die der Code liefert — damit Vortrag und Rechnung dieselbe Geschichte erzählen.

**Architecture:** `python-pptx` bearbeitet `docs/slides/dissvortrag.pptx` an Ort und Stelle. Jeder Schreibschritt wird zuvor gesichert. Formeln als LaTeX-Text, niemals handgeschriebenes OMML.

**Tech Stack:** python-pptx, die fertigen Abbildungen unter `docs/slides/figures/`

**Spec:** `docs/superpowers/specs/2026-09-09-baum-klima-geo-potenzial-design.md`, Abschnitt 10
**Zahlen und Befunde:** `docs/superpowers/specs/2026-09-09-befunde-fuer-plan-2-und-3.md` — **bindend, jede Zahl auf einer Folie muss dort belegt sein**

## Global Constraints

- **`docs/slides/~$dissvortrag.pptx` ist PowerPoints Sperrdatei.** Vor jedem Schreibzugriff prüfen. Ist sie da, ist die Präsentation geöffnet und PowerPoint überschreibt beim Speichern alles — dann anhalten und den Nutzer bitten, sie zu schließen.
- **Vor jedem Task** Sicherung nach `docs/slides/workspace/dissvortrag_pre_<schritt>_<zeitstempel>.pptx`. Diese Sicherungen sind gitignored.
- **Formeln als LaTeX-Text**, kein handgeschriebenes OMML. Handgeschriebenes OMML hat in diesem Projekt schon einmal das Speichern der Datei zerstört.
- Deutscher Folientext mit echten Umlauten, niemals `ue`/`oe`/`ae`. Sieben Umlautfehler wurden in diesem Projekt bereits gefunden, zwei davon auf dem Weg zu einer Folie.
- Vorhandene Layouts, Schriften und Farben der Präsentation übernehmen. Kein neues Design.
- Abbildungen aus `docs/slides/figures/` einbetten, nicht neu erzeugen.
- Nichts löschen: ersetzte Platzhalterfolien wandern in den Backup-Teil ab Folie 30, sie werden nicht entfernt.
- Nach jedem Task: Datei mit `python-pptx` erneut öffnen und die Folienzahl prüfen. Öffnet sie nicht, ist sie beschädigt — aus der Sicherung zurückrollen.

## Die Zahlen, die auf Folien gehen

Alle aus `docs/superpowers/specs/2026-09-09-befunde-fuer-plan-2-und-3.md`.

| Größe | Wert |
|---|---|
| Glühbirne boreal, **gemessen** | 53,6 W (nicht 71,5 W — das war kalibriert) |
| Restanteil nach 75 a, vorindustriell (Joos) | 0,4388 |
| Restanteil nach 75 a, SSP2-4.5 | 0,700 |
| Albedo-Spitzenmonat 60°N | April, ~3× Jahresmittel |
| Albedo-Spitzenmonat 45°N | Februar, ~1,4× |
| t\* boreale Fichte, volles Modell | 2071 |
| Leiter t\* | 2025 → 2048 → 2048 → 2049 → 2071 |
| wärmende Zellen 2030 → 2125 | 62,5 % → 2,9 % |
| bepflanzbare Fläche | 0,9488 Gha |
| nutzbares Potenzial | 78,2 GtC (69,8–84,7), 38,2 % von Bastins 205 |
| Umkehrrechnung 1,5 °C | ~10,3× die gesamte bepflanzbare Fläche |

---

### Task 1: Werkzeug und Sicherung

**Files:**
- Create: `scripts/pptx_tools.py`
- Test: `tests/test_pptx_tools.py`

**Interfaces:**
- `backup(step: str) -> Path` — Sicherung mit Zeitstempel, gibt den Pfad zurück
- `check_not_locked() -> None` — wirft, wenn die Sperrdatei existiert
- `open_deck() -> Presentation` und `save_deck(prs) -> None`
- `add_slide(prs, layout_name_or_index) -> slide`
- `set_title(slide, text)`, `add_body(slide, lines)`, `add_picture_slide(slide, png_path, caption)`
- `add_latex_line(slide, latex: str, ...)` — setzt die Formel **als Text**, dokumentiert im Docstring, warum kein OMML
- `move_slide(prs, from_idx, to_idx)` — für das Verschieben ersetzter Folien in den Backup-Teil
- `verify_deck(path) -> int` — öffnet die Datei erneut und gibt die Folienzahl zurück; wirft bei Beschädigung

- [ ] **Step 1: Tests schreiben** — gegen eine Kopie in `tmp_path`, niemals gegen die echte Präsentation. Prüfen: Sicherung entsteht und ist lesbar; `check_not_locked` wirft bei angelegter Sperrdatei; `add_slide` erhöht die Folienzahl; `verify_deck` erkennt eine absichtlich beschädigte Datei.
- [ ] **Step 2: Fehlschlag bestätigen**
- [ ] **Step 3: Implementieren**
- [ ] **Step 4: Tests laufen lassen**
- [ ] **Step 5: Commit**

---

### Task 2: Herleitungsfolien auf die gerechneten Zahlen bringen

Vier Folien tragen Zahlen, die der Code inzwischen widerlegt oder belegt hat.

**Folie 12** — Wachstumsparameter. Die Werte aus `nbs.species.SPECIES` einsetzen (m_max, k, p, p_Stör für die gezeigte Art) und die Art benennen, statt generisch zu bleiben.

**Folie 13** — „von einer Tonne sind nach 100 Jahren noch rund 40 % wirksam". Das ist die **vorindustrielle** Joos-Kurve. Die eigene Rechnung liefert unter SSP2-4.5 nach 75 Jahren 0,700. Beide zeigen, die Differenz benennen, und die Aussage ergänzen: *je heißer die Welt, desto länger wirkt jede Tonne nach.* Abbildung: eine Kurve mit beiden Verläufen — falls noch nicht vorhanden, in diesem Task erzeugen, mit `nbs.response.green_carbon` und `green_carbon_preindustrial`.

**Folie 14** — „rund 70 W". **Auf 53,6 W ändern**, mit der Quelle Duveiller et al. 2018 statt der eigenen Kalibrierung. Und die Aussage schärfen: die Albedo-Strafe ist kein Dauerzustand, sondern ein **Frühjahrsereignis** — bei 60°N liegt die Spitze im April und trägt rund das Dreifache des Jahresmittels. Das Bild der „Glühbirne, die nie ausgeht" durch den Scheinwerfer ersetzen, der im April brennt. Abbildung: der Monatsgang aus dem Notebook.

**Folie 22** — die Konstanten A_Baum, A_Erde, τ aus `nbs.constants` und `nbs.species` bestätigen; wo sie abweichen, korrigieren.

- [ ] **Step 1: Vorher-nachher-Liste erstellen** — jede Zahl, die geändert wird, mit altem Wert, neuem Wert und Beleg. Diese Liste kommt in den Bericht.
- [ ] **Step 2: Sicherung, dann ändern**
- [ ] **Step 3: `verify_deck`, Folienzahl unverändert**
- [ ] **Step 4: Commit**

---

### Task 3: Der Ergebnisteil

Folie 25 ist ein Platzhalter. Sie wird durch sieben Folien ersetzt; die alte wandert in den Backup-Teil.

| | Inhalt | Abbildung |
|---|---|---|
| E1 | Aufbau: fünf Arten, Standorte, SSP2-4.5, Horizont 2025–2150, ein Baum als Bezugseinheit | — |
| E2 | Ein Baum an einem Ort: m(t), ṁ_CO₂(t), Bedeckungsgrad | `e2_eingangsgroessen_boreal.png` |
| **E3** | **Zerlegung: ΔT_CO₂, ΔT_Albedo, ΔT_netto.** Kernfolie | `e3_zerlegung_boreal.png` |
| E4 | Störungsfächer: Median, 5–95 %, Risikoprämie | `e4_stoerungsfaecher_boreal.png` |
| E5 | Fünf Arten, Vorzeichenwechsel mit der Breite | `e5_arten.png` |
| E6 | Horizontfeld: Nulllinie ist t\*(Breite) | `e6_horizontfeld.png` |
| E7 | Die Leiter: was jede Modellschicht kostet | Wasserfall aus `run_ladder` |

**Zu E3, wichtig:** die zweizeilige Fassung (Antrieb oben, Temperatur unten) zeigt nahezu deckungsgleiche Kurven, weil g_T kurzes Gedächtnis hat. Der einzige echte Unterschied ist der Versatz von rund vier Jahren zwischen dem Nulldurchgang des Antriebs und t\*. **Entweder** auf eine Zeile eindampfen **oder** die Verzögerung sichtbar machen (Ausschnitt um den Nulldurchgang, beide Nulldurchgänge markiert). Entscheiden und begründen.

**Zu E7:** die Leiter ist das Ergebnis, das der Nutzer ausdrücklich wollte — Sensitivität gegenüber Modellkomplexität. Sie zeigt, dass Albedo 23 Jahre kostet und die steigende Hintergrundkonzentration nochmal 22. Der zweite Effekt ist in der Aufforstungsliteratur praktisch nie mitgerechnet; das gehört als Satz auf die Folie.

- [ ] **Step 1–5:** Sicherung, Folien anlegen, Abbildungen einbetten, `verify_deck`, Commit

---

### Task 4: Der Potenzialteil

Folien 26–28 sind Platzhalter. Ersetzen durch fünf Folien; die alten wandern in den Backup-Teil.

| | Inhalt | Abbildung |
|---|---|---|
| P1 | Die Karte: Ausgleichsjahr t\* je Zelle. Tropen um 2030, boreal 2060–2080 | `p0_ausgleichsjahr_karte.png` |
| P2 | Dieselbe Frage, ein Jahr: 2050 wärmen 48 %, kühlen 52 % | `p1_vorzeichenkarte_2050.png` |
| P3 | Die Kaskade: Bastins 205 GtC → 78,2 GtC nutzbar | Wasserfall aus `nbs.potential.cascade` |
| P4 | Datengrundlage, ehrlich: was gemessen, was extrapoliert ist | — |
| P5 | Die Umkehrrechnung: ~10,3× die bepflanzbare Fläche der Erde | — |

**P4 ist nicht verhandelbar.** Die Karte beruht zu rund 29 % auf lokalen Satellitenmessungen und zu 71 % auf zonaler Extrapolation, weil Duveillers Verfahren beide Landbedeckungen lokal nebeneinander braucht und deshalb nur 4 % der Landfläche direkt abdeckt. Eine Folie, die das verschweigt, ist in einer Verteidigung angreifbar; eine, die es sagt, ist es nicht. Die Fußzeile der Abbildung trägt es bereits — auf P4 gehört es in ganzen Sätzen.

**Zu P5:** die Zahl beantwortet die Frage von Folie 28 („Heute x Bäume pflanzen"). Die Antwort ist, dass x größer ist als die Erde hergibt. Das ist die Pointe des Vortrags und darf nicht relativiert werden — aber sie braucht den Zusatz, dass Aufforstung damit nicht wertlos ist, sondern nur keine Alleinlösung.

- [ ] **Step 1–5:** wie Task 3

---

### Task 5: Durchsehen und Abschluss

- [ ] **Step 1: Jede geänderte und jede neue Folie als Bild rendern und ansehen.** In diesem Projekt wurden drei Fehler ausschließlich durchs Hinsehen gefunden, zuletzt eine Weltkarte, deren Fläche zu 71 % im Ozean lag, bei grüner Testsuite. Prüfen: keine abgeschnittenen Umlaute, keine überlappenden Textfelder, Abbildungen nicht verzerrt, Schriftgrößen lesbar, Formeln als Text vorhanden.
- [ ] **Step 2: Zahlenabgleich.** Jede Zahl auf jeder neuen Folie gegen das Befundedokument prüfen. Abweichungen sind Fehler, keine Rundungen.
- [ ] **Step 3: `verify_deck`** und Folienzahl gegen die Erwartung.
- [ ] **Step 4: Bericht** mit der Vorher-nachher-Liste aller geänderten Zahlen.
- [ ] **Step 5: Commit**

---

## Was dieser Plan bewusst offen lässt

- **Kein Redesign.** Layout, Schriften und Farben bleiben, wie sie sind.
- **Der Herleitungsteil bleibt inhaltlich unangetastet** über die Zahlenangleichung hinaus.
- **Die Karte bleibt punktförmig.** Die Artzuweisung kommt aus Breitenbändern, nicht aus einer Landbedeckungskarte; die Zellen liegen daher verstreut über den Kontinenten. Für die Folienwirkung wäre eine gröbere Bündelung (etwa 2°) besser — das ist eine reine Darstellungsfrage und darf in Task 4 gemacht werden, ändert aber kein Ergebnis.
- **Sprechernotizen** werden nicht geschrieben.
