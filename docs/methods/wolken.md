# Wolken über Wald

Stand 2026-10-14. Entwurf und Plan: `docs/superpowers/specs/2026-10-14-wolken-design.md`,
`docs/superpowers/plans/2026-10-14-wolken.md`.

## Was abgebildet ist

Wald verdunstet mehr und ist rauer als Wiese oder Acker. Die durchmischte Luftschicht
erreicht am Nachmittag früher die Wolkenbasis, über Wald stehen mehr niedrige Haufenwolken.
Sie werfen Sonnenlicht zurück und wirken der dunkleren Albedo entgegen.

## Daten

Duveiller, G. et al. (2021): Revealing the widespread potential of forests to increase low
level cloud cover. Nat. Commun. 12, 4337, doi:10.1038/s41467-021-24551-5. Daten:
Zenodo 10.5281/zenodo.4727774 (CC-BY-4.0), Datei `data_for_figures.zip`,
`df_dCFC_MOD05_{EFO,DFO}.Rdata`:

- absolute Änderung der Wolkenbedeckung Δf beim Übergang krautige Vegetation → Wald,
  MODIS Aqua 13:30 (Cloud CCI 2004–2014), je Monat, 0,35°-Zellen,
- getrennt für immergrünen (EFO) und laubabwerfenden Wald (DFO),
- von den Autoren gefiltert (Unsicherheit ≤ 0,1, Flächenanteil ≥ 0,2, 0,5/99,5-%-Kappung).

`scripts/prepare_clouds.py` mittelt die Werte in das 1°-Gitter von Duveiller et al. 2018
(`data/clouds/duveiller2021_dcfc_1deg.npz`, eingecheckt).

## Umrechnung (vor dem Rechnen festgelegt)

    Δα_W(Monat) = Δf(Monat) · r_W · d,   r_W = 0,5,  d = 0,5

- r_W: zusätzliche Reflexion einer Wolke (Cerasoli et al. 2021, PNAS 118, e2026241118: f_C = 0,5).
- d: Anteil des Tageslichts nach Entstehen der Haufenwolken (Duveiller misst um 13:30, Cerasoli lässt
  die Wolken bis Sonnenuntergang stehen).

Das Produkt mit der Einstrahlung q̇_ein (Duveiller 2018, Quotient ΔSW/Δα, sonst Median des
10°-Breitenbands) wird Monat für Monat gebildet und gemittelt (`nbs.cloud_grid`). Es addiert sich
zum Albedo-Produkt (`nbs.light.light_product`); Kronenschluss, Standfläche und τ_atm wie bei der Albedo.

Typen: ENF, EBF → EFO; DNF, DBF → DFO; Mischwald → Mittel aus beiden (wo nur einer, dieser).
Lücken: lokal → Median des 10°-Breitenbands je Monat und Typ → 0 (kein Signal bekannt).
Negative Werte (weniger Wolken über Wald unter Schnee, Amazonas-Trockenzeit) bleiben.

Schalter: `NBS_CLOUDS=0` (bzw. `ModelConfig(clouds=False)`) rechnet ohne Wolken, bitgleich zum
Modell vor 2026-10-14. Die Caches in `deck/chart_data` tragen dann das Suffix `_ohne_wolken`.

## Ergebnis (`scripts/check_clouds.py`)

| | Albedo | Wolken | netto | Wolken / Albedo |
|---|---|---|---|---|
| Aachen (DE) | 34,2 W | −5,2 W | 29,0 W | 15 % |
| Joensuu (FI) | 45,3 W | −1,1 W | 44,2 W | 2,5 % |
| Marabá (BR) | 20,7 W | +0,7 W | 21,4 W | −3,5 % |
| Fläche (Mittel) | | | | 7 % |

W je ausgewachsenem Baum, Jahresmittel; positiv = die Erde absorbiert mehr. Joensuu: im Frühjahr
weniger Wolken über Wald (Schnee), im Sommer mehr. Marabá: in der Trockenzeit weniger.

Folgen für das Deck (gleiche Regel: 2026 gepflanzt, 2100 bewertet): kühlende Fläche 0,39 → 0,42 Gha,
Netto-Entnahme 59 → 66 Gt CO₂, Netto-Anteil Aachen 63 → 68 %, Joensuu 28 → 30 %, Marabá 82 → 81 %
(`deck/chart_data/fakten.json` gegen `fakten_ohne_wolken.json`).

Abgleich Cerasoli et al. 2021: Vorzeichen in 30–45° N gleich (Wolken kühlen). Cerasoli finden dort,
dass die Wolken die Albedo überwiegen; hier gleichen sie sie zu rund einem Zehntel aus. Cerasoli
vergleichen ganze Breitenkreise (mit großräumigen Unterschieden), Duveiller nur Nachbarflächen.

## Grenzen

- Nur lokale, niedrige, konvektive Wolken; Advektion verwischt das Signal (eher Unterschätzung).
- Langwellige Wirkung niedriger Wolken vernachlässigt.
- Großräumige Wolkenantworten (Luo et al. 2024, Hua et al. 2023) nicht enthalten.
- Keine Änderung von Wolken oder Schnee mit dem Klima.
- BVOC nicht getrennt, steckt aber in der Messung.
- Die beiden Faktoren 0,5 sind einfache Annahmen mit Quelle.
