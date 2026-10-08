# Standortabhängiges Wachstum

Stand: 2026-10-05 (Anker vereinheitlicht) · Code: `src/nbs/site_factor.py` · Schalter: `ModelConfig(site_growth=True)` (Standard)

## Kurz

Dieselbe Art wächst weiter nördlich langsamer: Die Vegetationsperiode ist kürzer, es ist kälter, es gibt weniger Licht. Das Modell bildet das mit **einem Faktor je Art und Breitengrad** ab, der das Wachstumsniveau skaliert. Die Form der Wachstumskurve bleibt, wie sie auf der Folie „C-Aufnahme über die Zeit im Modell" steht.

## Formel

Wachstumskurve je Baum (Chapman-Richards, unverändert):

$$m(t) = m_{max}\,\big(1 - e^{-k t}\big)^{p}$$

Neu ist allein, dass das Niveau vom Pflanzort φ abhängt:

$$m_{max}(\varphi) = m_{max} \cdot f(\varphi), \qquad f(\varphi) = \frac{I(\varphi)}{I(\varphi_{ref})}$$

- **I(φ):** mittlerer jährlicher Holzzuwachs dieser Art am Ort [m³ je ha und Jahr].
- **φ_ref:** Referenzstandort der Art (`nbs.species.REFERENCE_SITES`), Fichte 60°N, Kiefer 52°N. Dort ist f = 1, und die Folienwerte gelten unverändert (Fichte: m_max = 50 kgC, k = 0,030 1/a, p = 2,0).
- **k und p bleiben gleich.** Damit ändert sich nur, wie viel ein Baum bindet, nicht wie schnell er in die Sättigung läuft.

## Die eine Annahme

> **Wo eine Art x-mal schneller Holz zuwächst, speichert ein Baum dort auch x-mal so viel Kohlenstoff.**

Was daraus folgt, und warum das so einfach bleibt:

- **CO₂-Kanal:** Vorrat, Netto-Aufnahme und Störungsverluste skalieren genau linear mit f (Störungsverlust ∝ Vorrat). Der CO₂-Antrieb skaliert damit ebenfalls linear.
- **Albedo-Kanal:** Der Bedeckungsgrad f_Krone = (m/m_max)^β hängt nur vom *Verhältnis* zu m_max ab und bleibt unverändert. Der Baum schließt seine Krone im Norden also genauso schnell wie im Süden; das ist eine Vereinfachung.
- **Rechnung über die Karte:** bleibt exakt. Je Zelle wird die CO₂-Kurve der Art mit f der Zelle multipliziert (`nbs.aggregate.co2_factor_grid`). Ein Test rechnet das gegen einzeln simulierte Bäume nach (`tests/test_aggregate.py::test_site_factor_scaling_of_the_co2_channel_is_exact`).

## Woher die Werte kommen (Fassung vom 2026-10-05)

Überall dieselbe Größe: **gemessener mittlerer jährlicher Holzzuwachs, alle Baumarten zusammen**, aus nationalen Waldinventuren.

| Region | ≈ Breite | Zuwachs [m³/ha/a] | Quelle |
|---|---|---|---|
| Deutschland | 51°N | 11,2 | Bundeswaldinventur 2012, alle Baumarten |
| Südfinnland | 61,8°N | 6,5 | Finnische Waldinventur VMI13, 2019–2023 (Korhonen et al. 2024) |
| Nordkarelien (Joensuu) | 62,8°N | 5,8 | Luke, Regionales Waldprogramm 2020 (VMI12, 2014–2018), Wald- und Kümmerwaldfläche |
| Nordfinnland | 66,5°N | 3,1 | VMI13 (Korhonen et al. 2024) |

- **Interpolation:** Zwischen den Ankerpunkten wird linear interpoliert, jenseits der äußeren Punkte bleibt der Wert konstant. Zwischen 51 und 61,8°N (Dänemark, Südschweden) gibt es keinen eigenen Anker.
- **Arten:** Fichte und Kiefer nutzen dieselbe Kurve, jeweils auf ihren Referenzstandort bezogen (Fichte 60°N, Kiefer 52°N). Der Faktor ist damit ein **Produktivitätsindex des Standorts**, kein artspezifischer Wert.
- **Was vorher anders war:** Der deutsche Anker war fichtenspezifisch (15,3), der schwedische eine Standortgüte, also ein Potenzial (Skåne 11), die nordischen Werte dagegen gemessene Mittel über alle Arten. Das hat Aachen überschätzt (f = 2,27) und Joensuu unterschätzt (0,71).
- **Ergebnis jetzt:** f = 1,54 in Aachen, 1,0 bei 60°N, 0,82 in Joensuu.
- **IPCC 2019, Tab. 4.11:** Die Spannen dienen nur noch als Plausibilitätsrahmen. Alle Werte liegen in der Fichtenspanne (1,5–15). Es wird nicht mehr begrenzt, weil die Anker kein Artwert sind.
- **Verfeinerung möglich:** Werte je finnischer Landschaft (Luke-Statistikdatenbank, Tabelle 1.24) und je schwedischem Landesteil (SLU Skogsdata) statt der Landesteile bzw. der Interpolation.

## Wie gemessen wird (kurz)

- **Waldinventuren (Deutschland, Schweden, Finnland):** Ein festes Netz von Stichprobenpunkten über das ganze Land wird alle 5–10 Jahre erneut aufgesucht. An jedem Punkt werden Durchmesser und Höhe aller Bäume gemessen, und über Formfunktionen wird daraus das Holzvolumen berechnet. Der Zuwachs ist die Volumenzunahme zwischen zwei Aufnahmen, einschließlich der Bäume, die dazwischen gefällt wurden oder abgestorben sind, je Hektar und Jahr. Das ist ein Mittel über alle Altersklassen und Standorte einer Region, also das, was dort tatsächlich wächst.
- **Standortgüte (Bonität, Schweden):** wie viel Holz ein Standort bei voller Bestockung im Mittel einer Umtriebszeit produzieren kann. Sie wird aus der Höhe der Bäume bei einem Bezugsalter abgeleitet und ist ein Potenzial, kein Momentanwert.
- **FAO 2006 / IPCC Tab. 4.11:** Länder haben per Fragebogen für ihre Hauptbaumarten den kleinsten und größten mittleren Zuwachs gemeldet, also schlechte und gute Standorte im Land. Die Tabelle zeigt die Spanne über alle meldenden Länder. Deutschland hat nicht teilgenommen. Die Spanne vermischt Standortgüte innerhalb eines Landes und Unterschiede zwischen Ländern. Eine Breitenabhängigkeit lässt sich daraus nicht ablesen, deshalb die Inventuren für die Lage.

## Was das Modell damit nicht abbildet

- **Feuchte, Boden und Höhenlage:** Der Faktor hängt nur von der Breite ab. Ost-West-Unterschiede (atlantisch gegenüber kontinental) und Trockenheit im Süden sind nicht enthalten.
- **Kronenschluss:** Im Norden schließt sich die Krone vermutlich langsamer und bleibt lichter. Das Modell lässt sie gleich schnell schließen und überschätzt damit dort eher die Albedo-Strafe.
- **Südlich von 51°N** gilt der deutsche Wert unverändert weiter. Ob die Bäume dort (Gebirge, Südeuropa) wirklich so wachsen, ist nicht belegt.
- **Alle Arten statt einer Art:** Der Faktor überträgt die Standortproduktivität aller Arten auf die Fichte. Auf ihren eigenen Standorten wächst Fichte in Nordeuropa eher schneller als das Mittel, das von Kiefer auf armen Böden geprägt ist.
- **Bewirtschaftung:** Inventurzuwachs stammt aus bewirtschafteten Wäldern. Das Modell wendet ihn auf eine unbewirtschaftete Aufforstung an.

## Wirkung (SSP2-4,5, volles Modell)

Rechte Spalte: mit Standortfaktor **und** der Albedo aus Wiese und Acker (beides am 2026-10-02 eingeführt). Gerechnet noch mit den alten FaIR-Handparametern; die heutigen Werte (kalibriertes FaIR) stehen in `klimamodell-fair.md`.

| | ohne Standortfaktor | mit Standortfaktor |
|---|---|---|
| Fichte Aachen: Vorrat 2150 je Baum | 33 kgC | 75 kgC |
| Fichte Aachen: dauerhaft kühlend ab | 2039 | sofort (2025) |
| Fichte Joensuu: Vorrat 2150 je Baum | 33 kgC | 24 kgC |
| Fichte Joensuu: dauerhaft kühlend ab | 2056 | 2071 (Antrieb ab 2063 negativ) |
| Kaskade: nutzbare Fläche / Kohlenstoff | 0,936 Gha / 78,6 GtC | 0,733 Gha / 62,0 GtC |
| Kaskade: Abkühlung bis 2150 | 0,241 K | 0,215 K |
| Umkehrrechnung 1,5 °C | 10,2-fache Fläche | 12,1-fache Fläche |

Vergleich mit dem alten Verhalten: `ModelConfig(site_growth=False)`.

**Nebenbefund beim Testen:** Der logarithmische CO₂-Antrieb (`nbs.forcing.phi_co2_background`) rechnete `log((C + ΔC)/C)`. Bei einem einzelnen Baum ist ΔC ≈ 10⁻¹³ ppm, der Quotient liegt dann bei 1 + 10⁻¹⁶ und wird gerundet. Das ergab 0,3 % (bis 2,7 %) Rundungsrauschen je Baum. Jetzt steht dort `log1p(ΔC/C)`, mathematisch identisch und numerisch exakt. Die Zahlen oben sind mit dieser Korrektur gerechnet.

## Quellen

- IPCC (2019): 2019 Refinement to the 2006 IPCC Guidelines, Vol. 4, Ch. 4 Forest Land, Table 4.11.
- FAO (2006): Global planted forests thematic study — results and analysis. Del Lungo, Ball, Carle. Planted Forests and Trees Working Paper FP38, Tab. 13.
- BMEL / Thünen-Institut (2014): Der Wald in Deutschland — Ausgewählte Ergebnisse der dritten Bundeswaldinventur (Zuwachs Fichte 15,3, Buche 10,3, Kiefer 8,1 m³/ha/a).
- SLU / Swedish Wood: Standortgüte 11 m³sk/ha/a in Skåne, 5 in Gästrikland, 2–3 im inneren Norrland.
- Korhonen et al. (2024): Forests of Finland 2019–2023 and their development 1921–2023. Silva Fennica 58(5), 24045 (Zuwachs Süd 6,5, Nord 3,1 m³/ha/a).
