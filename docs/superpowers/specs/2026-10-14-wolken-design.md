# Wolken über Wald: dritte Wirkung im Modell und im Kapitel Bäume

Stand 2026-10-14, abgestimmt mit Timo im Gespräch.

## Ziel und Rahmen

- Wald verdunstet mehr und ist rauer als Wiese oder Acker. Die Luftschicht über ihm erreicht am Nachmittag früher die Wolkenbasis, es bilden sich mehr niedrige Haufenwolken, die Sonnenlicht zurückwerfen. Das wirkt der dunkleren Albedo entgegen.
- Der Effekt kommt **ins Hauptmodell**: Alle Zahlen des Decks (kühlende Fläche, Netto-Anteil, Gt, Kapitel 4/5, Holzweg) werden mit ihm neu gerechnet. Ohne Wolken bleibt als Sensitivität (Backup) erhalten.
- Die Umrechnung von Wolkenbedeckung in Antrieb wird **vor dem Rechnen** festgelegt (diese Spec) und danach nicht nach Ergebnis verändert (siehe wissenschaftlich ehrlich bleiben).

## Quellen

- **Duveiller et al. 2021**, Nat. Commun. 12, 4337, doi:10.1038/s41467-021-24551-5. Daten: Zenodo 10.5281/zenodo.4727774 (CC-BY-4.0), Code: 10.5281/zenodo.4727822. Größe: absolute Änderung der Wolkenbedeckung Δf (MODIS-Aqua, 13:30 Ortszeit, Cloud CCI 2004–2014) beim Übergang von krautiger Vegetation (Gras, Acker) zu Wald; je Monat, 0,35°-Gitter, getrennt für immergrünen (EFO) und laubabwerfenden (DFO) Wald, mit der Qualitätsfilterung der Autoren (σ ≤ 0,1, Flächenanteil ≥ 0,2, 0,5/99,5-%-Kappung). Nur niedrige, konvektive Wolken; nur der lokale Effekt (Advektion verwischt, eher Unterschätzung).
- **Cerasoli et al. 2021**, PNAS 118, e2026241118, doi:10.1073/pnas.2026241118. Liefert die Umrechnung: Wolke erhöht die Reflexion um f_C = 0,5; Wolken bestehen vom Entstehen am Nachmittag bis Sonnenuntergang. Dazu ein qualitativer Abgleich: Mittelbreiten 30–45° netto kühlend durch Wolken.
- Hintergrund (nur Notizen): Xu et al. 2022 (Vorzeichen regional verschieden), Luo et al. 2024 und Hua et al. 2023 (nichtlokale Effekte in Modellen), Teuling et al. 2017.

## Modell

**Wolken als Aufhellung.** Die Wolke wird wie eine Albedo-Änderung behandelt, mit umgekehrtem Vorzeichen:

    Δα_W(Monat) = Δf(Monat) · r_W · d
    r_W = 0,5   zusätzliche Reflexion einer Wolke (Cerasoli f_C)
    d   = 0,5   Anteil des Tageslichts nach Entstehen der Haufenwolken (Nachmittag)

Das Produkt mit der Einstrahlung wird wie bei der Albedo Monat für Monat gebildet, dann gemittelt:

    P_W = mean_Monat( Δα_W · q̇_ein )        q̇_ein: Duveiller 2018 (bereits im Modell)
    P_netto = P_α + P_W                       P_α = Δα · q̇_ein (heute alpha_q_product, < 0 für dunkleren Wald)

Antrieb, Kronenschluss, Standfläche und τ_atm = 0,854 bleiben wie bei der Albedo (`phi_albedo_from_product`); der Wolkenantrieb wächst also mit dem Kronenschluss. Langwellige Wirkung niedriger Wolken: vernachlässigt (klein), genannt.

**Waldtypen.** ENF und EBF → EFO; DNF und DBF → DFO; MF → Mittel aus EFO und DFO (wo beide fehlen, das vorhandene).

**Gitter und Lücken.** 0,35° → 0,5°-Modellgitter flächengewichtet. Lücken (Daten nur, wo Wald und Offenland nebeneinander liegen, ca. 4 % der Zellen) wie bei der Albedo: lokal → Mittel des Breitenbands je Monat und Waldtyp; Herkunft (lokal/zonal) wird ausgewiesen wie `product_provenance_grid`. Negative Werte (weniger Wolken über Wald unter Schnee, Amazonas-Trockenzeit) bleiben drin.

**Schalter.** `ModelConfig.clouds: bool = True`; `False` reproduziert die heutigen Zahlen (Regressionstest).

**Bekannte Grenzen (Notizen, Backup).** Nur lokale niedrige Wolken; keine Änderung von Wolken oder Schnee mit dem Klima; BVOC nicht getrennt (steckt in den Messdaten); die beiden Faktoren 0,5 sind einfache Annahmen mit Quelle.

## Folien

1. **„Was Bäume tun“**: Das Verdunstungs-Symbol bekommt einen Pfeil zu einer Wolke. Notiz: Verdunstung wirkt vor Ort *und* über Wolken global. Drei global wirksame Effekte, weiterhin zwei Einheiten.
2. Albedo-Konzept und Karten „Einstrahlung und Albedo-Kontrast“ bleiben.
3. **Neu: „Mehr Wolken über Wald“** (Schema im DAC-Stil, Klick für Klick): Wiese gegen Wald → Verdunstung und Turbulenz → Luftschicht wächst, erreicht früher die Wolkenbasis → Haufenwolke am Nachmittag wirft Licht zurück → im Modell: Δα_W = Δf · 0,5 · 0,5. Zahl für Aachen (DE) im Vergleich zur Albedo. Quellen Duveiller 2021, Cerasoli 2021.
4. **„Zusätzlich absorbierte Strahlung je Baum“**: Karte zeigt netto (Albedo + Wolken). Orts-Panels zeigen den Jahresgang getrennt: Albedo nach oben, Wolken nach unten, Summe als Linie. Takeaway: zwei Wirkungen, zwei Einheiten (kg CO₂, W netto).
5. Klima-Kapitel: Energiebilanz am Oberrand nennt Wolken als Teil von ΔQ̇; sonst unverändert.
6. Einordnung (andere Studien): „Wolken: nicht abgebildet“ wird zu „lokale niedrige Wolken abgebildet“.
7. Backup: „Ohne Wolken“ (kühlende Fläche, Netto-Anteil, Gt mit/ohne) und Abgleich mit Cerasoli (Breitenprofil).

Alle Zahlen aus `fakten.json` neu, über die bestehenden Skripte in die Folien.

## Umsetzung (Grobstruktur)

- `scripts/fetch_data.py`: Eintrag `duveiller_clouds` (Zenodo `study_results.zip`; daraus die 0,35°-Datei mit `delta`, `uncertainty`, `fraction` je Waldtyp).
- `src/nbs/cloud_grid.py`: Laden, Filtern wie die Autoren, Regridding, Typzuordnung, Lückenfüllung, `cloud_q_product(species_key)` und `monthly_cloud_product`; Konstanten `R_CLOUD`, `D_AFTERNOON` in `nbs.constants`.
- `nbs.albedo_grid` / `nbs.aggregate` / `nbs.pipeline.typical_product`: Netto-Produkt über eine Funktion `light_product(species_key, config)`; Komponenten bleiben einzeln abrufbar.
- Tests: Vorzeichen und Formel, Typzuordnung, Lückenfüllung, `clouds=False` gleich heute, Ortswerte Aachen/Joensuu/Marabá plausibel (Aachen Sommer Δf ≈ 0,02–0,04).
- Danach: Fakten, Karten, Diagramme neu exportieren; Folien anpassen; Deck bauen; Screenshots der neuen/geänderten Folien zur Freigabe vor dem Commit.
