# Literaturstand und was davon ins Modell ging (2026-10-05)

Suche nach neuer Literatur zu Albedo gegen Kohlenstoff bei Wiederbewaldung,
Störungen und DAC. Regel: Was einen Modellparameter direkt belegt, ersetzt die
Setzung (nach einer vorab genannten Regel, nicht nach dem Ergebnis). Was
dieselbe Frage anders rechnet, kommt auf die Vergleichsfolie. Was fehlt, ist
als Grenze dokumentiert.

## Ins Modell übernommen

| Quelle | Was | Parameter | Regel |
|---|---|---|---|
| Williams et al. 2026, JGR Biogeosci. 131 | Tempo des Albedo-Rückgangs nach Pflanzung (Satellit, weltweit): Hälfte in 40 Jahren, 80 % nach 50–120 Jahren | `beta_closure` | f(40 a) = 0,5 je Typ × Zone (vorher fest 0,5 → zu schneller Albedo-Effekt) |
| Grünig et al. 2026, Science | Bestandsersetzende Störungen in Europa bis 2100: +31 / +61 / +122 % (RCP2.6 / 4.5 / 8.5) | `gamma_warming` | ln(1 + Zunahme) / globale Erwärmung (AR6), Mittel = 0,26/K (vorher 0,20/K gesetzt) |
| Walker et al. 2022; Hasler et al. 2024; Cook-Patton et al. 2020; Poorter et al. 2016 | Fläche, Waldtyp, Kohlenstoff, Tempo | siehe `waldtypen.md` | |

Wirkung des Albedo-Tempos allein (Test mit sonst gleichem Modell): kühlende
Fläche bis 2150 0,28 → 0,35 Gha; die ganze Fläche netto +0,013 K → etwa 0 K.

## Zum Vergleich (Folie „Einordnung: andere Studien“)

Gemeinsame Einheit: Anteil des reinen Kohlenstoffnutzens, der nach der Albedo bleibt.

* Riley et al. 2025, Nat. Commun. 16, 8810: 172 Projekte, Median-Abzug 18 % → 82 %.
* Weber et al. 2024, Science 383, 860: Albedo + Luftchemie bis zu ⅓ → ≥ 67 %.
* Fahrenbach et al. 2026, Commun. Earth Environ. 7, 204: CESM2, SSP2-4.5,
  Bastin-Fläche bis 2100: −0,22 K aus Kohlenstoff, −0,13 K netto → 59 %.
  Enthält Verdunstung und nicht-lokale Effekte; anfangs ~20 Jahre netto warm.
* Hasler et al. 2024: 47 % (Bastin-Fläche, statisch).
* Liang et al. 2025, Sci. Adv.: 30 % (Feuer + Albedo, bis 2100, SSP1-2.6).
* Rohatyn et al. 2022, Science 377, 1436: 30 % (Trockengebiete).
* Zeitaufgelöst, aber ohne Ortsauflösung bzw. nur ein Ort: Kirschbaum et al.
  2011 (ein Standort), Arora & Montenegro 2011 (Erdsystemmodell).

## Bekannte Grenzen, die die Literatur benennt

* **Verdunstung und Rauigkeit** (Fahrenbach 2026; Windisch et al. 2021):
  kühlen vor allem in den Tropen. Fehlen hier → Tropen eher zu streng.
* **Abnehmende Schneedecke** (Hasler 2024, Diskussion): Die boreale
  Albedo-Strafe sinkt in einer wärmeren Welt. Δα·q̇ ist hier statisch → boreal
  eher zu streng.
* **Luftchemie und Wolken** (Weber 2024: BVOC, Aerosole): nicht abgebildet,
  Vorzeichen je nach Region.
* **Tempo je Typ** (Williams 2026): langsamer in Außertropen und Laubwald,
  schneller in Tropen und Nadel-/Mischwald — hier eine globale Regel.
* **Störung außerhalb Europas**: Anderegg et al. 2022 (USA) erwarten bis 2090
  Feuer ×4–14, Trockenstress und Insekten ×1,3–1,8; γ hier aus Europa.
* Synthese zum Forschungsstand: Stephan et al. 2026, ERL 21.
