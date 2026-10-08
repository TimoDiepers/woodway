# Waldtypen statt gesetzter Arten (2026-10-05)

Ersetzt die fünf frei parametrierten Arten (Fichte, Kiefer, Buche, Eukalyptus,
tropischer Mischbestand), die Breitenbänder und den Standortfaktor aus
Waldinventuren (`docs/methods/standortabhaengiges-wachstum.md`, überholt).
Code: `nbs.forest_data`, `nbs.species`, `nbs.site_factor`, `nbs.landscape`,
Aufbereitung: `scripts/prepare_forest_data.py`, `scripts/prepare_cookpatton.py`.

## Daten und Regeln

| Frage | Quelle | Regel |
|---|---|---|
| Wo darf gepflanzt werden? | Walker et al. 2022 (PNAS), NCS-Kategorien R/L + R/H | ohne Flächen für Ernährung und Siedlung; 0,931 Gha |
| Welcher Wald wächst dort? | Hasler et al. 2024 (Nat. Commun.), wahrscheinlichster Wald | häufigste Klasse je 0,5°-Zelle; Savanne → häufigste echte Waldklasse; ohne Klasse → 3×3-, dann 5×5-Nachbarschaft, sonst ausgeschlossen (0,10 Gha) |
| Welche Typen sind zulässig? | Hasler | ≥ 10 % der klassifizierten Fläche in der 3×3-Nachbarschaft |
| Wie viel Kohlenstoff kommt dazu? | Walker, nicht realisiertes Potenzial ober- + unterirdisch | je Zelle; ohne Boden; für alle Typen am Ort gleich |
| Wie schnell? | Cook-Patton et al. 2020 (Nature), Zuwachs der ersten 30 Jahre | Wurzel:Spross 0,25; relativ zu Walkers Potenzial; ≤ 55 % nach 30 Jahren (Poorter et al. 2016: 90 % nach 66 Jahren); Median je Typ × Zone |
| Klimazone | Walker-Bioklimazonen (aus FAO GEZ) | Codes 1/5 im README vertauscht (Breite geprüft); polar → boreal |
| Albedo | Duveiller et al. 2018 | Übergang je IGBP-Klasse, ENF 38/39, EBF 18/19, DNF 48/49, DBF 28/29, MF 58/59 |
| Störung | bisherige Werte; Anstieg mit Erwärmung aus Grünig et al. 2026 | ENF ← Fichte, DNF ← Kiefer, DBF ← Buche, EBF ← trop. Mischbestand, MF ← Mittel Fichte/Buche; γ = 0,26/K |
| Tempo der Albedo | Williams et al. 2026 | Kronenschluss erreicht die Hälfte nach 40 Jahren |

Je Baum: 2000 Bäume/ha (5 m² Standfläche). Registry: ein Eintrag je Typ × Zone
mit dem Median-Kohlenstoff seiner Zellen; je Zelle skaliert der Faktor
`M(Zelle) / M_ref(Typ×Zone)` nur m_max, deshalb bleibt die Aggregation exakt.

## Warum Kohlenstoff je Ort typgleich

Die IPCC-Tabellen 4.7–4.10 (2019) zeigen am selben Ort keinen belastbaren
Unterschied zwischen Waldtypen. Ein Typ-Aufschlag wäre eine Setzung. Die
Typen unterscheiden sich daher in Albedo und Störung.

## Laufendes Beispiel

Aachen: gemäßigter Mischwald, 98 t C/ha zusätzlich → 49 kg C bzw. 180 kg CO₂ je
Baum. Joensuu: borealer Mischwald, 66 t C/ha → 33 kg C bzw. 121 kg CO₂.

## Bekannte Grenzen

* Tempo: In 73 % der Zellen greift die Poorter-Grenze; das Tempo trennt die
  Typen kaum.
* 11 % der wiederbewaldbaren Fläche ohne Waldtyp in der Nähe bleiben außen vor.
* Albedo statisch (keine abnehmende Schneedecke).
* Literaturstand und weitere Grenzen: `docs/methods/literaturstand-2026.md`.
* Abgleich gegen die Literatur: `docs/methods/abgleich-hasler-waldtypen.md`.
