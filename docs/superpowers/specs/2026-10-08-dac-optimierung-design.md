# DAC-Optimierung: wo, wann, wie viel — Design

Stand: 2026-10-08

## Ziel

Das DAC-Kapitel (ab der Folie „Sind wir auf dem Holzweg?“) schließt die Lücke, die die Availability-Folie (25) zeigt: Very Low liegt auch mit den Bäumen über 1,5 °C. Statt DAC nur je Tonne mit dem Baum zu vergleichen, rechnet ein lineares Programm, **wo, wann und wie viel** DAC gebaut werden muss, damit die Temperatur ab einem möglichst frühen Jahr X dauerhaft bei 1,5 °C bleibt. Der Overshoot vor X wird gezeigt.

Erfolgskriterien:
- Zwei neue Folien zeigen das Problem und das Ergebnis kompakt (Ort, Zeit, Menge, Temperatur).
- Jede Annahme ist belegt (Speicher: Gidden et al. 2025; Wachstum: Zurbriggen et al. 2026) und steht auf der Folie oder in den Notes.
- Die Gegenprobe mit FaIR bestätigt das Ergebnis des LP.

## Festgelegte Entscheidungen

| Thema | Entscheidung |
|---|---|
| Zielgröße | Lücke(t) = Overshoot Very Low über 1,5 °C (Median, 7-Jahres-Mittel, `overshoot_series`) minus Kühlung der Bäume auf kühlenden Flächen (`area_series()["kuehlt"]`), für alle t ≥ X. DAC kommt zusätzlich zu den 335 Gt, die Very Low schon enthält (Notes). |
| Zielfunktion | Zieljahr X = 2100 (fest). Stufe 1: kleinste Kapazität = größte weltweite Jahresentnahme. Stufe 2: bei dieser Kapazität die kleinste Gesamtmenge. Zusätzlich die nötige Kapazität für X = 2085/2090/2095/2100. (Geändert 2026-10-08: „frühestes X, kleinste Gesamtmenge“ ballte die Entnahme auf bis zu 96 Gt/a.) |
| Räumliche Ebene | Länder (ISO3). Kein Transport über Landesgrenzen. |
| η je Land und Jahr | Median der besten 10 % der Zellen, die DAC-tauglich (`dac_possible`) und speichernah sind, aus `efficiency_grid(year)` (Wärmepumpe, SSP2-NDC). |
| speichernah | Sedimentbecken (onshore oder offshore, bewertet oder global) innerhalb von 100 km um den Zellmittelpunkt, aus dem Gidden-Raster. |
| Speicherbestand | Gidden et al. 2025, Tabelle S5, „prudent planetary limit“ je Land (onshore + offshore), Gt CO₂. Weltsumme 1 460 Gt. |
| Wachstum | Weltweite Brutto-Entnahme 2030 ≤ 8,8 Mt/a (Zurbriggen et al. 2026, Mittel der geplanten Kapazität). 2026–2029 linearer Anstieg auf diesen Wert. Danach je Jahr ≤ 1,2 × Vorjahr (Wind-Analogie, 20 %/a). |
| Klimawirkung | FaIR-Kernel, dieselbe Kette wie Baum und Lückenkurve (`green_carbon`, `phi_co2_background`, `green_temperature`, ssp245-Hintergrund). Kein `dynamic_characterization`. |
| Solver | `scipy.optimize.linprog`, Methode HiGHS. |

## Modell

Indizes: c ∈ Länder mit η > 0 und Speicher > 0; y, t ∈ 2026…2100.

Variablen: x[c, y] ≥ 0, Brutto-Entnahme durch DAC in Gt/a.

Kernel: K[y, t] = ΔT im Jahr t [K] je Gt CO₂ Netto-Entnahme im Jahr y (K[y, t] = 0 für t < y). Er erweitert `dac_compare._removal_kernel`, das bisher nur den Wert im Endjahr liefert, zur ganzen Zeitreihe.

Nebenbedingungen:

1. Kühlung: Σ_c Σ_y −K[y, t] · η[c, y] · x[c, y] ≥ Lücke(t) für alle t ≥ X.
2. Speicher: Σ_y x[c, y] ≤ S[c] für alle c. Das Lager füllt sich mit der Brutto-Entnahme.
3. Wachstum: Σ_c x[c, t] ≤ 1,2 · Σ_c x[c, t−1] für t > 2030; Σ_c x[c, 2030] ≤ 0,0088; für 2026–2029 Obergrenze 0,0088 · (y − 2025)/5.

Ziel: min P mit P ≥ Σ_c x[c, t] für alle t; danach bei P die Summe Σ_c Σ_y x[c, y] minimieren.

Ist kein X ≤ 2100 machbar, löst ein Ersatzproblem die bestmögliche Annäherung: min Σ_t max(0, Lücke(t) − Kühlung(t)) über 2026–2100, mit den Nebenbedingungen 2 und 3. Die Folie zeigt dann diese Annäherung; das ist die Aussage.

Gegenprobe: Der optimale Pfad (Netto-Entnahme je Jahr, weltweit summiert) läuft einmal durch das volle FaIR-Modul des Repos, und die Temperatur wird mit der LP-Kurve verglichen. Abweichung in den Notes.

## Sensitivitäten (Backup und Notes)

- Wachstum 11 %/a (Ammoniak-Analogie).
- Speicher: technisches Potenzial statt „prudent limit“.
- η: Median aller DAC-tauglichen, speichernahen Zellen statt bestes Dezil.

## Bausteine im Code

| Datei | Aufgabe |
|---|---|
| `scripts/fetch_storage_gidden.py` | Lädt Zenodo-Record 18343187 (Raster, Excel, Readme) nach `data/raw/gidden/` (gitignored). Schreibt `data/dac/speicher_gidden.json` (Land → onshore/offshore/total für technisches Potenzial, prudent limit, Öl/Gas) und `data/dac/speicher_maske.npz` ((360, 720) bool, Becken ≤ 100 km). |
| `src/nbs/dac_storage.py` | `storage_by_country(stufe)`, `storage_mask()`, `country_grid()` (vorhandene Länderzuordnung wiederverwenden). |
| `src/nbs/dac_optim.py` | `eta_by_country(year, quantil)`, `removal_kernel_matrix()`, `gap_series()`, `solve(growth, storage_stufe, quantil)` → Ergebnis-Dict (Jahre, Länder, x, η, Temperatur ohne/mit DAC, X, Status). |
| `scripts/dac_optim_export.py` | Rechnet Haupt- und Sensitivitätsfälle, schreibt `data/dac/optim.json`. |
| `tests/test_dac_optim.py` | Siehe Tests. |
| `docs/methods/dac-modell.md` | Neuer Abschnitt „Optimierung“. |
| `scratchpad/patch_dac_optim.py` | Folien 30/31, Backup-Verschiebungen, Takeaways, in die Build-Kette von `new_vergleich.py` nach `patch_story4`. |

## Folien

DAC-Kapitel neu:

| # | Folie | Status |
|---|---|---|
| 27 | Sorbens-DAC: Prozess und Energiebedarf | bleibt |
| 28 | DAC-Modell je Ort und Jahr | bleibt |
| 29 | Netto-Entnahme von DAC 2026–2100 | bleibt |
| 30 | Optimierung: wo, wann, wie viel DAC? | neu |
| 31 | DAC-Ausbau nach Ort und Zeit | neu |
| 32 | Auf dem Holzweg? Nein. | Text an das Ergebnis anpassen |
| 33 | Methodischer Beitrag | Punkt „Optimierung mit Speicher- und Wachstumsgrenzen“ |

Ins Backup: „DAC in drei Strompfaden“, „Priorisierung von Aufforstung und DAC“, neu eine große Speicherkarte, die FaIR-Gegenprobe und die Sensitivitäten.

**Folie 30, Optimierung.**
- Links drei Eingänge als Miniaturen untereinander: η-Karte (wie Folie 29), Speicherkarte (Gidden-Becken plus Kreise je Land), Lückenkurve (wie Folie 25).
- Rechts eine Wortformel im Stil von Folie 17, Schritt für Schritt mit den Highlight-Kästen (`.hl`):
  1. Gesucht: DAC je Land und Jahr.
  2. Minimiere die Gesamtentnahme.
  3. Kühlung ≥ Lücke.
  4. Σ Einlagerung ≤ Speicher je Land.
  5. Wachstum ≤ 20 %/a (wie Windkraft).
- Mit jedem Schritt wird der passende Eingang links hervorgehoben.
- Takeaway nach Ergebnis, z. B. „Speicher global reichlich, aber nicht dort, wo der Strom sauber ist“.

**Folie 31, Ergebnis.**
- Links eine Weltkarte mit Kreisen je Land: Fläche = kumulierte Gt bis 2100, Farbe = R5-Region.
- Rechts oben die Temperatur über 1,5 °C ohne DAC (wie Folie 25) und mit DAC; der restliche Overshoot ist rot, Jahr X markiert.
- Rechts unten der Hochlauf in Gt/a als gestapelte Fläche nach R5-Region, in denselben Farben wie die Karte.
- Klicks:
  1. Kurve ohne DAC.
  2. Hochlauf und Kurve mit DAC wachsen zusammen.
  3. Kreise auf der Karte.
  4. Takeaway.
- Takeaway nach Ergebnis, z. B. „1,5 °C erst ab X, nur mit dem Tempo der Windkraft; bis 2050 kaum Wirkung“.

Technik:
- ECharts-Specs `EC_DAC_TEMP`, `EC_DAC_RAMP`, `EC_DAC_MAP`; Daten aus `data/dac/optim.json` als `window.DAC_OPT`, wie `LUECKE`.
- Karten-Hintergrund: die vorhandene Land-Silhouette der Deck-Karten, Kreise als ECharts-Scatter.
- Es gelten die Regeln des Decks: Lesbarkeit im großen Saal, nur Neues animieren, Highlight-Stil, Bernstein-Akzent (`data-ch="dac"`).
- Die pptx bleibt zurückgestellt.

## Tests

- Gidden-Tabelle: Weltsumme des „prudent limit“ 1 460 ± 1 Gt; DEU 1,3 Gt; „Total“-Zeilen nicht als Land gezählt.
- Maske: Nordsee-Anrainerzellen (z. B. Nordwestdeutschland) speichernah; Schweiz-Inneres nicht.
- Kernel: K[y, t] = 0 für t < y; K[y, 2100] stimmt mit `_removal_kernel()` überein.
- LP-Minifall: zwei Länder, konstanter Kernel, bekannte Lösung (das bessere Land zuerst, bis sein Speicher voll ist).
- Ergebnis Hauptfall: Wachstumsgrenze und Speichergrenzen nie verletzt (Toleranz 1e-9), Kühlung ≥ Lücke für t ≥ X.

## Nicht enthalten (Notes)

- Kosten, Strom- und Wasserverfügbarkeit, zusätzliche Erzeugung für DAC.
- Transport über Landesgrenzen; Basalt-Mineralisierung (Island = 0 bei Gidden).
- Injektionsraten je Becken (nur Bestand je Land).
- Lebensdauer der Anlagen; die Variable ist die jährliche Entnahme, nicht gebaute Anlagen.
- Klimawandel-Rückwirkung auf η (Klimanormal 2011–2020).

## Quellen

- Gidden, M. J. et al. (2025): A prudent planetary limit for geologic carbon storage. Nature 645, 124–132. Daten: Zenodo 10.5281/zenodo.18343187 (CC-BY 4.0).
- Zurbriggen, T. et al. (2026): Short-term action is key for gigaton-scale Direct Air Capture by 2050. Nat. Commun. 17, 6184.
- Bestehendes DAC-Modell: `docs/methods/dac-modell.md`.
