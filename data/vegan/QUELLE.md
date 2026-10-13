# Quellen der veganen Welt

## FAOSTAT – `faostat_tierhaltung.json`

- Datensatz: FAOSTAT Emissions Totals (Domäne GT), Bulk-Download
  https://bulks-faostat.fao.org/production/Emissions_Totals_E_All_Data_(Normalized).zip
  (Dateistand 2025-12-06), heruntergeladen 2026-10-13 nach `data/raw/faostat/` (gitignored).
- Filter: Area = World, Year = 2022, Source = FAO TIER 1. Element „Emissions (CH4)“ bzw. „Emissions (N2O)“
  (N₂O direkt + indirekt).
- Tierhaltung CH₄: Enteric Fermentation, Manure Management → 114,2 Mt.
- Tierhaltung N₂O: Manure Management, Manure left on Pasture, Manure applied to Soils → 4,07 Mt.
- Acker-N₂O: Synthetic Fertilizers, Crop Residues → 3,02 Mt; davon zählt der Anteil der frei werdenden
  Ackerfläche, 19 % (Poore & Nemecek 2018, Science 360, 987, doi:10.1126/science.aaq0216).
- Agrar-Summen (Nenner des Anteils, passend zum IAM-Sektor `AFOLU|Agriculture`):
  CH₄ = Enteric Fermentation + Manure Management + Rice Cultivation → 138,9 Mt (ohne Verbrennung von
  Ernteresten und Savannenfeuer, die im IAM unter `Agricultural Waste Burning` bzw. `Land|Fires` liegen);
  N₂O = alle fünf Items oben → 7,09 Mt.
- Aufteilung nach Ursache (`vegan.emission_parts`): Brutto fällt das Acker-N₂O des Futteranbaus weg, 38 % des
  Ackers (Poore & Nemecek 2018, Tabelle S10, über Our World in Data, https://ourworldindata.org/global-land-for-agriculture);
  die Ersatzprodukte brauchen davon 19 Prozentpunkte wieder, netto bleiben die 19 %.
- CO₂ bis zum Hoftor (Element „Emissions (CO2)“): On-farm energy use, Fertilizers Manufacturing, Pesticides
  Manufacturing → 1,48 Gt; davon Futter 38 %, Ersatzprodukte 19 %. Folgt dem fossilen CO₂ von Very Low (`CO2 FFI`).
- CO₂ aus Entwaldung: Net Forest conversion → 2,81 Gt; davon Rindfleisch 41 % (Singh & Persson 2026, globale
  Entwaldung durch Landwirtschaft 2001–2023, über Our World in Data,
  https://ourworldindata.org/what-has-driven-deforestation-in-the-21st-century). Folgt dem positiven Teil des
  Landnutzungs-CO₂ von Very Low (`CO2 AFOLU`), das ab etwa 2035 zur Senke wird: danach keine vermiedene Entwaldung mehr.
- CO₂ nach dem Hoftor (Verarbeitung, Transport, Handel) gilt für die Ersatzprodukte als gleich.

## Agrar-Pfad von Very Low – `vl_agrar.json`

- Quelle: IIASA-Datenbank ScenarioMIP-CMIP7 (Release 2026), Plattform `scenariomip-cmip7` (ixmp4),
  Modell REMIND-MAgPIE 3.5-4.11, Szenario „Very Low - SSP1 (Marker)“, Region World, abgerufen 2026-10-13.
- Variablen: `Emissions|CH4|AFOLU|Agriculture` [Mt CH4/yr], `Emissions|N2O|AFOLU|Agriculture` [kt N2O/yr].
- Werte: CH₄ 154 (2020), 161 (2025), 104 (2050), 42 Mt (2100); N₂O 6,6 / 7,1 / 3,6 / 1,5 Mt.
- Gegenprobe: Die Datenbank führt auch `…|Agriculture|Livestock` direkt (CH₄ 145 Mt 2025). Der FAOSTAT-Anteil
  (114,2 / 138,9 = 82 %) auf den Agrar-Pfad ergibt 132 Mt 2025 – etwas weniger, also vorsichtig.
- Abruf: `uv run --with pyam-iamc python scripts/prepare_vegan_data.py --vl-agrar`.
