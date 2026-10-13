# Vegane Welt ab 2026

## Kurz

Gedankenexperiment für Kapitel 5: Die ganze Welt isst ab 2026 vegan, ohne Übergang. Das ist ein Grenzfall, eine obere Schranke. Gerechnet wird gegen CMIP7 Very Low, die Erwärmung über 1,5 °C nach den Bäumen (als Forst, Holz gebunden) ist die Lücke. Code: `src/nbs/vegan.py`, Daten: `data/vegan/` (Quellen in `data/vegan/QUELLE.md`), Zahlen im Deck: `deck/chart_data/zeitpfade.json`, Schlüssel `vegan`.

Ergebnis: netto 0,20 K kühler schon 2050 (−203 mK), 2100 −207 mK, am stärksten Mitte der 2060er (−251 mK). Fast alles ist Methan. Ohne jedes DAC sinkt die Spitze über 1,5 °C von 0,31 auf 0,13 K (2044), ab 2065 gilt wieder 1,5 °C. Mit DAC im Hauptfall (niedrigste Spitze, dann so früh wie möglich zurück, 20 %/a) bleiben 0,1 statt 49 Gt/a; gespart bis 2100 im Median 222 Bio. € (134–338).

## 1  Emissionen nach Ursache (`emission_parts`)

Alle Anteile stammen aus FAOSTAT Emissions Totals 2022 (Welt, FAO TIER 1) und werden konstant auf die Pfade von Very Low angewendet, nicht auf heutige Emissionen. Was Very Low ohnehin senkt, zählt so nicht doppelt.

| Teil | Grundlage | Bezugspfad |
|---|---|---|
| CH₄ der Tierhaltung | Enteric Fermentation + Manure Management, 114 Mt; Anteil am landwirtschaftlichen CH₄ 82 % | CH₄ `AFOLU\|Agriculture` von Very Low (IIASA ScenarioMIP-CMIP7) |
| N₂O vermieden | N₂O der Tierhaltung (Dung im Stall, auf der Weide, ausgebracht) 4,07 Mt + 38 % des Acker-N₂O (Futteranbau) | N₂O `AFOLU\|Agriculture` von Very Low |
| CO₂ bis zum Hoftor | 38 % von On-farm energy use + Dünger- und Pestizidherstellung (1,48 Gt) | fossiles CO₂ von Very Low (`CO2 FFI`) |
| CO₂ aus Entwaldung | 41 % der Net Forest conversion (2,81 Gt), Anteil Rindfleisch nach Singh & Persson 2026 | positiver Teil von `CO2 AFOLU`; ab etwa 2035 Senke, danach nichts mehr |
| Ersatzprodukte (wärmt) | 19 % des Acker-N₂O und des CO₂ bis zum Hoftor | wie oben |

- **Acker:** 38 % des Ackers tragen heute Futter (Poore & Nemecek 2018, Tabelle S10, über Our World in Data). Netto werden in einer veganen Welt 19 % frei (dieselbe Quelle). Die Ersatzprodukte brauchen also 19 Prozentpunkte wieder. Acker-N₂O und CO₂ bis zum Hoftor werden proportional zur Fläche angesetzt.
- **Nach dem Hoftor** (Verarbeitung, Transport, Verpackung, Handel) gilt für Ersatzprodukte dasselbe wie für tierische Produkte.
- **Anteil konstant:** vorsichtig, weil Very Low Energie-Methan schneller senkt als Agrar-Methan. Ohne `data/vegan/vl_agrar.json` fällt das Modell auf den Anteil an den Gesamtemissionen von Very Low zurück.
- **Gegenprobe:** IIASA führt für Very Low auch `…|Agriculture|Livestock` direkt (CH₄ 145 Mt 2025). Der FAOSTAT-Anteil auf dem Agrarpfad ergibt 132 Mt, also etwas weniger. Größenordnung der Temperatur passt zu Ivanovich et al. 2023 (Ernährung zusammen knapp 1 K bis 2100, vor allem Methan der Wiederkäuer).
- **Auffällig:** N₂O der Tierhaltung nach FAOSTAT 4,07 Mt, mehr als oft zitiert (1–2 Mt), weil Dung auf der Weide und ausgebrachter Dung mitzählen.

## 2  Wald auf frei werdenden Flächen

- **Fläche:** Walker et al. 2022, Societal Constraints: Weide ganz, Acker zu 19 %. Wald nur dort, wo Walkers Regel für Wiederbewaldung gilt (Potenzial ≥ 10 Mg C/ha, Bestand/Potenzial ≤ 0,25, ohne Einschränkung). Grund: Die NCS-Schicht ist innerhalb der Societal Constraints null; die Regel trifft Walkers eigene Zuordnung zu 98,4 %. Disjunkt von der wiederbewaldbaren Fläche der Bäume-Kapitel. `scripts/prepare_forest_data.py --only-freed` → `data/vegan/frei_0p5.npz`.
- **Kohlenstoff:** nicht realisiertes AGB+BGB (Walker, ohne Einschränkung).
- **Klimawirkung:** dieselbe Baumkette wie in den Kapiteln 2–4 (`forcing_cells`), alle 2026 gepflanzt, nur kühlende Zellen. FaIR auf SSP2-4.5 wie bei den Bäumen.
- **Ergebnis:** 0,537 Gha frei, davon kühlen 0,210 Gha. CO₂ −8 mK (2050), −16 mK (2100); Albedo +1 bzw. +7 mK; netto −7 bzw. −9 mK.

## 3  Klimaantwort

Jeder Teil läuft als eigener FaIR-Lauf (`contributions`); netto ist `dt_gase + dt_flaeche` aus gemeinsamen Läufen. Die Teile addieren sich bis auf höchstens 3 mK zum Netto.

| Kühlung [mK] | 2050 | 2100 |
|---|---|---|
| Methan | 174 | 158 |
| Lachgas | 21 | 41 |
| CO₂ Hof und Entwaldung | 4 | 4 |
| Wald: CO₂ | 8 | 16 |
| Ersatzprodukte | −4 | −6 |
| Wald: Albedo | −1 | −7 |
| **netto** | **203** | **207** |

## 4  DAC mit veganer Welt

Dieselbe Optimierung wie im Hauptfall auf der Lücke mit veganer Welt: 0,11 Gt/a, 1,5 °C ab 2064 statt 2065 ohne DAC. Gespart gegenüber dem Hauptfall: 48,9 Gt/a Kapazität, 1 050 Gt Entnahme, 222 Bio. € (Median; 134 optimistisch, 338 pessimistisch). Die beiden Fälle haben verschiedene Rückkehrjahre (2064 gegen 2083); die Ersparnis für dasselbe Jahr wäre eher größer.

## 5  Was nicht enthalten ist

- Bodenkohlenstoff auf den frei werdenden Flächen.
- Ersatz von Wirtschaftsdünger durch Mineraldünger (Leip et al. 2019).
- Handel, Rebound, Ernährungsübergang; alles sofort ist eine obere Schranke. Ein halber Wechsel bringt grob die Hälfte des Methan-Effekts.
- Entwaldung über 2035 hinaus: Bliebe die Entwaldung für Rinder bestehen, statt mit Very Low zu enden, kämen grob 20 mK hinzu.
- Die Spec erwartete die Flächen als größeren, unsichereren Teil (Radrapu 2025; Leip et al. 2019). Hier sind sie klein, weil nur kühlende Zellen zählen und die Albedo knapp die Hälfte der CO₂-Kühlung des Waldes aufzehrt.

## Quellen

- FAOSTAT Emissions Totals (Domäne GT), Stand 2025-12-06, Jahr 2022.
- IIASA ScenarioMIP-CMIP7 (Release 2026), REMIND-MAgPIE 3.5-4.11, „Very Low - SSP1 (Marker)“.
- Poore, J., Nemecek, T. (2018): Reducing food's environmental impacts through producers and consumers. Science 360, 987–992.
- Singh, C., Persson, U. M. (2026), über Our World in Data: What has driven deforestation in the 21st century.
- Walker, W. S. et al. (2022): The global potential for increased storage of carbon on land. PNAS 119, e2111312119.
- Ivanovich, C. C. et al. (2023): Future warming from global food consumption. Nature Climate Change 13, 297–302.
- Leip, A. et al. (2019); Radrapu (2025): wie in der Spec zitiert.
