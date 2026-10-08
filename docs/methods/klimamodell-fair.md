# Klimamodell: FaIR mit kalibriertem Parametersatz

Stand: 2026-10-05 · Code: `src/nbs/fair_module.py` · Auswahl: `scripts/select_fair_member.py` · Daten: `data/fair_calibrate_1.4.1/`

## Kurz

Hintergrunderwärmung, CO₂-Hintergrund C_bg(t), Kohlenstoff-Impulsantwort g_C und Temperatur-Impulsantwort g_T kommen aus FaIR 2.2.4. Bis 2026-10-04 lief FaIR mit **von Hand gesetzten** Parametern für das Energiebilanzmodell. Deren Klimarückkopplung (0,65 W m⁻² K⁻¹) ergibt eine Klimasensitivität (ECS) von etwa 5,6 K und unter SSP2-4,5 rund 3,5 K Erwärmung bis 2100. Das liegt weit über der IPCC-Bewertung (ECS 3 K, *likely* 2,5–4 K; SSP2-4,5 2081–2100: 2,7 K).

Jetzt läuft FaIR mit dem **kalibrierten und beobachtungsbeschränkten Parametersatz fair-calibrate 1.4.1** (Smith et al. 2024). Das ist der Satz, den die FaIR-Dokumentation selbst verwendet: 841 Mitglieder, beschränkt durch die beobachtete Erwärmung, Ozeanwärme, CO₂-Konzentration und die IPCC-Bewertungen von ECS, TCR und Antrieb.

## Ein Mitglied, nicht das Ensemble

Das Modell braucht *einen* Parametersatz: Baseline und Impulsantworten müssen zusammenpassen. Gewählt ist das Mitglied, das **gleichzeitig** am nächsten am Ensemble-Median liegt, und zwar in

- der historischen Erwärmung 2011–2020 und 2015–2024 gegenüber 1850–1900 und
- der Erwärmung 2081–2100 unter SSP1-2,6, SSP2-4,5, SSP3-7,0 und SSP5-8,5.

Jede Größe wird in Einheiten der 5–95-%-Spanne des Ensembles gemessen. Die Regel wurde zweimal nachgeschärft, beide Male aus Gründen auf der Klimaseite:

1. Die erste Fassung kannte nur 2011–2020 und die Szenarien. Das gewählte Mitglied lag 2025 bei 1,15 K (Median 1,31 K). Deshalb kam 2015–2024 hinzu.
2. Das Rauschen wurde abgeschaltet und die Auswahl danach wiederholt.

Das Mitglied wurde nicht danach ausgewählt, was es für die Bäume ergibt. Für die Geschichte ist es sogar das ungünstigere (siehe unten).

| | Mitglied 787474 | Ensemble-Median | 5–95 % | Beobachtung / IPCC AR6 |
|---|---|---|---|---|
| Erwärmung 2011–2020 | 1,08 K | 1,06 K | 0,84–1,24 K | 1,09 K |
| Erwärmung 2025 | 1,32 K | 1,31 K | 1,07–1,53 K | — |
| SSP1-2,6, 2081–2100 | 1,83 K | 1,80 K | 1,32–2,53 K | 1,8 K |
| SSP2-4,5, 2081–2100 | 2,62 K | 2,56 K | 1,91–3,39 K | 2,7 K |
| SSP3-7,0, 2081–2100 | 3,21 K | 3,20 K | 2,49–4,00 K | 3,6 K |
| SSP5-8,5, 2081–2100 | 4,10 K | 4,06 K | 3,06–5,33 K | 4,4 K |
| ECS | 2,90 K | 2,96 K | | 3 K (2,5–4) |

## Weitere Festlegungen

- **Bezugszeitraum 1850–1900.** Temperaturen sind gegenüber 1850–1900 angegeben, dem Bezug des 1,5-°C-Ziels und des IPCC. Bisher war der Bezug 1750; der Unterschied beträgt rund 0,07 K. Die Störungsrate p = p₀ e^{γT} nutzt dieselbe Hintergrunderwärmung.
- **Ohne interne Variabilität.** Die Kalibrierung zieht Zufallsrauschen mit (`stochastic_run`). Für das Modell ist es abgeschaltet: Die Baseline soll die erzwungene Antwort sein, und Impulsantworten dürfen keine Differenzen von Rauschen sein.
- **Emissionen aus RCMIP**, wie im SSP-Beispiel der FaIR-Dokumentation. Damit erreicht das ganze Ensemble 2020 etwa 403 ppm CO₂ (beobachtet 412 ppm). Die Wirkung je kg CO₂ ist dadurch um rund 2 % zu hoch. Neuere FaIR-Beispieldaten gibt es nur für die CMIP7-Szenarien, nicht für SSP2-4,5.

## Was sich physikalisch mit verschiebt

- **CO₂-Hintergrund:** Das ganze kalibrierte Ensemble bleibt mit den RCMIP-Emissionen unter dem offiziellen SSP2-4,5-Konzentrationspfad, den MAGICC liefert. 2100: Mitglied 521 ppm, Ensemble-Median 533 ppm (5–95 %: 488–560), MAGICC rund 603 ppm. Ein niedrigerer Hintergrund heißt eine stärkere Wirkung je kg (A_CO₂ 2150: 1,32 statt rund 1,15). Das begünstigt die Bäume leicht.
- **Aufnahme durch Ozean und Land:** Im kalibrierten FaIR sind von einem Impuls 2025 im Jahr 2100 noch 42 % in der Luft, bei Joos (2013) 44 %. Die frühere Aussage „in der volleren Welt nehmen Ozean und Land schlechter auf“ galt nur für die alten Handparameter und ist aus den Folien genommen. Außerdem nimmt FaIR schon im Impulsjahr rund 10 % auf (g_C[0] ≈ 0,90). Bei Joos ist g_C[0] = 1, die beiden Kurven sind also um etwa ein Jahr gegeneinander versetzt (Schale 2 gegen Schale 3).
- **Temperaturantwort:** g_T hat sein Maximum schon im Impulsjahr. Die Wärmekapazität der Mischschicht beträgt 3,7 W a m⁻² K⁻¹ (Ensemble-Median 4,1).

## Ein Fehler, der dabei aufgefallen ist

`nbs.aggregate.unit_curves` hat den Schalter `albedo=False` ignoriert. Die Variante „nur Kohlenstoff“ der Umkehrrechnung enthielt deshalb die Albedo; daher kamen die fast gleichen 11,44 und 11,39 Gha. Korrigiert: Mit Albedo und Störung braucht es 19,4 Gha, mit Kohlenstoff allein 9,6 Gha. Albedo und Störung verdoppeln also den Flächenbedarf.

Die alte FaIR-Konfiguration startete außerdem 1750 mit 0 ppm CO₂ statt 278 ppm (`initialise(concentration, 0)`).

## Wie empfindlich die Ergebnisse sind

Aachen und die Kaskade sind robust. **Joensuu liegt auf der Kippe.** Dort halten sich Kohlenstoff und Albedo am Horizont fast genau die Waage. Mit dem gewählten Mitglied kühlt die Fichte dort bis 2150 nicht. Mit einem anderen, ähnlich zentralen Mitglied (26795, ausgewählt ohne die Dekade 2015–2024 und mit Rauschen) kippt sie um 2111. Auf der Folie heißt das: „kühlt bis 2150 nicht“, mit diesem Hinweis in den Notizen. Eine Ensemble-Aussage („in x % der Parametersätze“) wäre der saubere nächste Schritt.

## Wirkung auf die Kernzahlen (SSP2-4,5)

| | alte Handparameter | fair-calibrate 1.4.1 |
|---|---|---|
| Erwärmung 2081–2100 | 3,5 K (Bezug 1750) | 2,6 K (Bezug 1850–1900) |
| A_CO₂ 2025 → 2150 [10⁻¹⁵ W m⁻² kg⁻¹] | 1,61 → 1,10 | 1,65 → 1,32 |
| Joensuu kühlt ab | 2071 | nicht bis 2150 |
| Kaskade | 62,0 GtC, −0,22 K | 54,5 GtC (49,0–56,4), −0,08 K |
| Umkehrrechnung 1,5 °C | 12,1-fache Fläche | 20,4-fache Fläche (mehr als alles eisfreie Land) |
| Hasler-Gegenprobe: Median-Offset / über 50 % | 38 % / 44 % | 54 % / 51 % (Hasler: 52 % / 48 %) |

Die Abkühlung der Kaskade sinkt etwa auf ein Drittel. Das passt zur Größenordnung über die TCRE: 54 GtC ≈ 200 Gt CO₂ ≈ 0,09 K, abzüglich Albedo. Die alten −0,22 K kamen vor allem von der zu hohen Klimasensitivität.

## Quellen

- Smith, C. et al. (2024): fair-calibrate v1.4.1: calibration, constraining, and validation of the FaIR simple climate model for reliable future climate projections. Geosci. Model Dev. 17, 8569–8592. Daten: doi:10.5281/zenodo.10566813; Parameterdateien aus `OMS-NetZero/FAIR/examples/data/calibrated_constrained_ensemble`.
- IPCC (2021): AR6 WG1, SPM Tab. SPM.1 (Erwärmung je SSP), Kap. 7 (ECS).

## Direkter FaIR-Lauf für Flächensummen (2026-10-05)

Zwei Wege, je nach Größe des Signals:

* **Ein Baum, eine Rasterzelle** (Leiter, Karten, t* je Zelle): Faltung mit
  FaIRs Antwort auf einen kleinen CO₂-Puls im Szenario-Hintergrund
  (`nbs.response.green_carbon`) und auf 1 W/m² (`green_temperature`). Ein
  Baum verschiebt die Welttemperatur um ~10⁻¹⁵ K. Das liegt unter der
  numerischen Genauigkeit eines FaIR-Laufs, und für so kleine Störungen ist
  die Faltung genau das, was FaIR rechnet.
* **Alle Flächensummen** (Kaskade, Literaturvergleich, Bedarf,
  Umkehrrechnung): `nbs.potential.fair_global_delta_t`. Die Entnahme aller
  Bäume geht als negative CO₂-Emission in FaIR, die Albedo als zusätzlicher
  Antrieb. FaIR rechnet dann alles zustandsabhängig: Senken, die sich
  füllen, und eine Wirkung je kg, die mit dem CO₂ sinkt.
* Varianten, die FaIR nicht direkt kann (Joos-Impulsantwort, konstante
  Wirkung je kg), bleiben bei der Faltung (`_convolved_global_delta_t`).

**Gegenprobe:** Ganze Fläche, bis 2100. Nur Kohlenstoff: FaIR −0,0486 K,
Faltung −0,0476 K. Anteil, der nach der Albedo bleibt: 18 % gegen 17 %
(Test `test_direct_fair_run_agrees_with_the_convolution_for_the_whole_area`).

**Umkehrrechnung:** Dort weicht die lineare Hochrechnung deutlich ab. Für
1,5 °C unter SSP2-4.5 braucht es das 65-Fache der kühlenden Fläche. Linear
hochgerechnet wäre es das 77-Fache. Bei so großen Flächen füllen sich die
Senken weniger, jede weitere Tonne wirkt dann etwas länger. Deshalb sucht
die Umkehrrechnung das Vielfache jetzt mit FaIR-Läufen (Bisektion).
