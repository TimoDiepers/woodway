# DAC-Modell und Vergleich mit Aufforstung

Stand: 2026-10-13

- **Code:** `src/nbs/dac_climate.py`, `src/nbs/dac.py`, `src/nbs/dac_compare.py`, `src/nbs/dac_figures.py`.
- **LCA-Vorberechnung:** `scripts/dac_lca_precompute.py`, läuft in einer Brightway-Umgebung.
- **Folien:** im Kapitel Vergleich „DAC: Strom je Tonne …“ bis „Ab wann DAC sauberer entnimmt“.

## Kurz

Für jede 0,5°-Landzelle und jedes Jahr von 2025 bis 2100 wird gerechnet, wie viel einer mit Direct Air Capture (DAC) entnommenen Tonne CO₂ netto übrig bleibt. Abgezogen werden die Lebenszyklus-Emissionen der Anlage und ihrer Energie. Dieselbe Größe wird für den an diesem Ort empfohlenen Baum gebildet, mit der Albedo als Abzug. Wo und ab wann DAC den höheren Netto-Wirkungsgrad hat, zeigen die Karten.

## 1  Technologie und Niveau: premise

Grundlage ist der premise-Datensatz *carbon dioxide, captured and stored, with a sorbent-based direct air capture system, 100ktCO2*. Er stammt aus dem Brightway-Projekt `ei312_REMIND_EU` (ecoinvent 3.12 cut-off, premise mit REMIND-EU, SSP2-NDC, Vintages 2020/2030/2040/2050/2075/2100).

- **Energie je t CO₂ (premise):**
  - 0,5 MWh Strom und 5,4 GJ (1,5 MWh) Wärme.
  - Die Wärmepumpen-Variante braucht insgesamt 1,02 MWh Strom; daraus folgt ein COP von rund 2,9.
- **Alles andere je kg CO₂:** Sorbens (Amin auf Silica), Anlage und ihr Rückbau, Verdichtung, Transport und Speicherung.
  - Diese Teile bleiben, wie premise sie verknüpft. Bau-Inputs laufen über die globalen bzw. regionalen Märkte des Datensatzes.
  - Ihr GWP100 ist der „Rest“: 0,088 (2020) → 0,021 kg CO₂e je kg (2100).

## 2  Abhängigkeit vom Klima: Sendi et al. (2022)

Quelle: Sendi, Bui, Mac Dowell, Fennell (2022): *Geospatial analysis of regional climate impacts to accelerate cost-efficient direct air capture deployment.* One Earth 5, 1153–1164, doi:10.1016/j.oneear.2022.09.003 (CC-BY).

Die Autoren simulieren denselben Prozesstyp mit stündlichem Wetter weltweit: Amin-Sorbens Lewatit VP OC 1065, dampfunterstützte Temperatur-Vakuum-Wechseladsorption. Die Wärme liefern Luft-Wärmepumpen.

**Wärmepumpe (ihre Gl. 29–31):**

$$COP = \eta\,\frac{T_H}{T_H - T_C},\quad \eta = 0{,}5,\; T_H = 110\,°C + 10\,K,\; T_C = T_{Umgebung} - 10\,K$$

Daraus ergibt sich ein COP von 1,5 (bei ≤ 1 °C; darunter wird die Leistung wie bei Sendi festgehalten) bis 2,0 (bei 30 °C). Der COP ist niedriger als in premise; er entspricht dem, was Hochtemperatur-Wärmepumpen bei rund 100 K Hub erreichen (Marktübersicht: 2,2–2,8 bei 70 K).

**Wärmebedarf:** Sendi et al. geben den Gesamtstrombedarf (Wärmepumpen eingerechnet) nur als Mittel von vier Klimaklassen an. Die Grenzen liegen bei 18 °C und 65 % relativer Feuchte (Table 1):

| Klasse | Sendi Table 1 [MWh/t] | dieses Modell |
|---|---|---|
| kalt-trocken | 1,76 | 1,77 |
| kalt-feucht | 2,15 | 2,14 |
| warm-trocken | 1,64 | 1,63 |
| warm-feucht | 2,11 | 2,12 |

**Anpassung:** Gesucht ist ein linearer Faktor für den Wärmebedarf:

$$Q(T, RH) = Q_{ref}\,[1 + a_T\,(T-20)/10 + a_{RH}\,(RH-50)/10]$$

- Er wird so angepasst, dass das flächengewichtete Mittel über unsere Zellen je Klasse die vier Werte trifft. Dabei gelten Sendis COP und seine 0,32 MWh/t für Vakuum, Verdichter und Gebläse.
- **Ergebnis:**
  - Wärmebedarf +12,6 % je 10 Prozentpunkte Feuchte: Wasser wird mitadsorbiert und muss wieder desorbiert werden.
  - +9,4 % je 10 K.
  - Größter Fehler: 0,012 MWh/t.

**Übertragung auf premise:** Das Modell verwendet nur den *relativen* Faktor Q/Q_ref, angewandt auf premises 1,5 MWh Wärme. Strom je t = 0,5 + 1,5·Q/Q_ref/COP(T). Ergebnis: 1,1–1,9 MWh/t, Median 1,5.

**Ausschluss:** Sendi et al. schließen Gebiete aus, die an mehr als 30 Tagen im Jahr unter −15 °C liegen. Hier stehen nur Monatsmittel zur Verfügung, deshalb lautet die Regel: kältester Monat im Mittel unter −15 °C. Das betrifft 20 % der Landfläche (Sendi: rund 25 %) und 40 % der bepflanzbaren Fläche, nämlich den borealen Gürtel.

**Klima:** CRU TS 4.09 (Harris et al. 2020), Monatsmittel 2011–2020 auf 0,5°.
- Temperatur direkt.
- Relative Feuchte aus Dampfdruck und Sättigungsdampfdruck nach Magnus (WMO).
- Beides jeweils als Jahresmittel.

## 3  Strom: premise mit REMIND-EU, je Land

- **GWP100 je kWh:** aus dem Markt „electricity, medium voltage“ des jeweiligen Landes, je Vintage. Zwischen den Vintages wird linear interpoliert.
- **Ländermix = Regionsmix:** premise verknüpft jeden Ländermarkt mit dem Markt seiner **REMIND-EU-Region**. Länder einer Region teilen sich also einen Mix. In Europa ist das fein aufgelöst: Deutschland, Frankreich und UK sind eigene Regionen; Nordeuropa (NEN) und Mittel-/Osteuropa (ECE) sind zusammengefasst. Anderswo sind die Regionen groß (z. B. SSA, LAM, OAS).
- **Länder ohne eigenen Markt (50 Stück):** Sie erhalten den Regionsmarkt nach der premise-Topologie (`data/dac/remind-eu-topology.json`, premise-Commit 82b7475). Dazu gehören z. B. Tschad → SSA und Grönland → NEN.
- **Länderzuordnung:** Natural Earth 1:50m. Küstenzellen ohne Treffer erhalten den häufigsten Code im Umkreis von bis zu 3 Zellen. 358 Inselzellen bleiben ohne Land und erhalten den Weltmix.
- **Methode:** IPCC 2021, climate change: total (excl. biogenic CO₂), GWP100.
- **Rechnung:** `bw2calc.JacobiGMRESLCA` mit Warmstart. Je Vintage ist das eine Matrix mit rund 190 Nachfragen; das Ergebnis stimmt mit dem direkten Löser überein.
- **Was das Szenario annimmt:** REMIND-EU SSP2-NDC dekarbonisiert sehr schnell. Deutschland: 0,42 (2020) → 0,09 (2030) → 0,013 kg/kWh (2050). Polen 0,92 → 0,16 → 0,011. Das trägt die Aussage „DAC wird schnell sauber“ wesentlich.

## 4  Netto-Wirkungsgrad

$$\eta_{DAC}(Zelle, Jahr) = 1 - \big(E_{Strom}\cdot GWP_{Strom}(Land, Jahr) + GWP_{Rest}(Jahr)\big) \;/\; 1\,t$$

$$\eta_{Baum}(Zelle, Pflanzjahr) = \frac{\Delta T_{CO_2} + \Delta T_{Albedo}}{\Delta T_{CO_2}}\Big|_{2150} = 1 - \text{Albedo-Offset}$$

- **Baum:**
  - Es ist der typische Wald der Zelle (Hasler et al. 2024, `nbs.landscape.assign_species`), derselbe Baum wie in allen anderen Kapiteln. Gepflanzt im Entscheidungsjahr, mit Störung bei deterministischer Rate. (Bis 2026-10-06 stand hier die je Zelle am stärksten kühlende Art; vereinheitlicht, damit alle Folien dieselbe Regel und dieselbe Fläche von 0,36 Gha nutzen.)
  - Der Albedo-Offset ist dieselbe Größe wie in der Hasler-Gegenprobe.
  - Für spätere Pflanzjahre wird die Wachstumskurve mit dem Pflanzjahr neu gerechnet. Bewertet wird immer 2150, der Horizont des Modells. Für sehr späte Pflanzjahre ist dieser Horizont kurz.
- **DAC:** Betrieb im Entscheidungsjahr. Emissionen und Entnahme fallen zeitgleich an; GWP100 macht Nicht-CO₂-Gase vergleichbar.
- **Bessere Option je Zelle und Jahr:** die mit dem höheren η, sofern η > 0. Sonst heißt es „keins kühlt“.
- **Karten:** Je 2°-Block zeigen sie die Option mit dem größten Anteil an der bepflanzbaren Fläche, wie die Pflanzkarte. Wo keine Bäume möglich sind, ist DAC die einzige Option; dort zeigen die Vergleichskarten grau.

## 5  Ergebnis (Hauptfall: Wärmepumpe, premise-Niveau)

| | 2025 | 2030 | 2040 | 2050 | 2100 |
|---|---|---|---|---|---|
| η_DAC, Median über Land | 42 % | 65 % | 92 % | 94 % | 95 % |
| DAC besser auf … der bepflanzbaren Fläche | 34 % | 45 % | 57 % | 59 % | 59 % |
| keins kühlt (bepflanzbar) | 34 % | 33 % | 32 % | 32 % | 24 % |

- Baum, η Median 2025: 13 %.
- Woher der Sprung gegenüber älteren Fassungen dieser Tabelle kommt (dort 8 % / 20 % / 43 % / 53 % / 54 %): Sie stammten von vor dem Wechsel auf Walkers Fläche und Kohlenstoff und auf die Waldtypen (2026-10-05). Seitdem bindet der Baum etwa halb so viel Kohlenstoff, und die Fläche liegt öfter im Norden und im Trockenen, wo er wärmt; der Baum-Median fiel von 40 % auf 20 %. Die Vereinheitlichung auf den typischen Wald (2026-10-06) verschob den DAC-Anteil 2025 nur noch von 32 % auf 34 %.
- Zusammensetzung der 34 % (2025): auf 22 Prozentpunkten wärmt der Baum ohnehin, auf 12 Prozentpunkten kühlt er, aber DAC mit dem Strommix 2025 entnimmt sauberer (vor allem Nordeuropa, Frankreich, Teile Amerikas).
- **Umstieg** (Median-Jahr, ab dem DAC auf der bepflanzbaren Fläche eines Landes besser ist): Norwegen, Schweden, Finnland, Frankreich, Spanien, USA, Brasilien 2025; Deutschland 2026; China 2027; Polen 2029; Indien 2032; Indonesien 2040; DR Kongo 2040 (Stand 2026-10-06, `fakten.json`).
- **Wo der Baum bis 2100 vorn bleibt:** vor allem dort, wo es für Sorbens-DAC zu kalt ist. Wo beides geht (37 % der bepflanzbaren Fläche), überholt DAC den Baum bis 2100 fast überall (im Mittel 2030); nur auf 1,5 % bleibt der Baum vorn.

## 6  Sensitivitäten (Median η_DAC)

| Variante | 2025 | 2050 |
|---|---|---|
| Hauptfall | 42 % | 94 % |
| Wärme aus Industriedampf (Erdgas-dominierter Wärmemarkt, DEU) statt Wärmepumpe | 62 % | 96 % |
| gemessene Climeworks-Energie (3,31 MWh Wärme + 0,70 MWh Strom, Sendi SI) | **−5 %** | 90 % |

- **Dampf heute besser:** Mit heutigem Strom ist Wärme aus Dampf sauberer als über die Wärmepumpe.
- **Climeworks-Werte:** Mit dem heute gemessenen Energiebedarf wäre DAC 2025 im Median netto emittierend.

## 7  Was nicht enthalten ist

- **Kosten, Flächenbedarf, Tempo und Mengen:** Der Vergleich gilt je Tonne. 1 Gt CO₂ mit DAC braucht rund 1 500 TWh Strom, etwa 5 % der heutigen Weltstromerzeugung.
- **Produktivität:** Die Klimaabhängigkeit der Produktivität (Sendi: ±10 %) und damit der Bauaufwand je Tonne bleibt fest.
- **Zeitliche Auflösung:** Stundenwetter und Teillast gehen nicht ein, nur Jahresmittel (Jensen-Effekt beim COP). Ein künftig wärmeres Klima ebenfalls nicht (Klimanormal 2011–2020).
- **Andere DAC-Wege:** Flüssig-DAC (KOH) ist nicht enthalten. Sie verhält sich klimatisch anders: Sie leidet unter Trockenheit und funktioniert in der Kälte.
- **Stromverfügbarkeit:** DAC bezieht den durchschnittlichen Netzmix, keine zusätzlich gebaute Erzeugung.

## 8  Optimierung: wo, wann, wie viel

Code: `src/nbs/dac_storage.py`, `src/nbs/dac_optim.py`, `scripts/fetch_storage_gidden.py`, `scripts/dac_optim_export.py`; Ergebnis `data/dac/optim.json`.

- **Frage:** Wie viel DAC-Kapazität braucht es mindestens, wo und wann, damit Very Low 2100 bei 1,5 °C liegt?
  - Dafür muss DAC 2100 zusätzlich zu den Bäumen auf kühlenden Flächen 87 mK kühlen (Folie 25).
  - Der Overshoot davor bleibt.
- **Variablen:** Brutto-Entnahme x[Land, Jahr] in Gt/a, 2026–2100.
- **Ziel auf CO₂-Ebene (Hauptfall seit 2026-10-08):** Bis 2100 netto **262 Gt CO₂** entnehmen.
  - Das ist die Nettomenge, die über die Klimaantwort (FaIR-Kernel) 2100 genau die 87 mK kühlt, bestimmt aus dem Pfad mit der kleinsten Kapazität und dem Temperaturziel (`co2_target_gt`).
  - Die Rahmenbedingung lautet dann: kumulierte Netto-Entnahme ≥ 262 Gt.
  - Die Temperaturwirkung ist Ergebnis, nicht Bedingung: 2100 genau 87 mK, bis 2050 aber erst 1,9 Gt entnommen.
- **Zielfunktion:**
  1. Kleinste Kapazität, also die größte Jahresentnahme weltweit.
  2. Bei dieser Kapazität die kleinste Gesamtmenge.
- **Nebenbedingungen:**
  - **Speicher:** Gidden et al. 2025, prudent limit je Land (Welt 1 460 Gt; Deutschland 1,3, Norwegen 6,9, UK 8,9, Russland 244, USA 141 Gt). Kein Transport über Grenzen. Länder ohne Gitterzelle (z. B. Kaspisches Meer, 14,9 Gt) fallen heraus.
  - **Wachstum:** 8,8 Mt/a in 2030 (geplante Kapazität), danach ≤ +20 %/a (Wind-Analogie), beides Zurbriggen et al. 2026.
  - **Lebensdauer 20 Jahre (seit 2026-10-13):** Jede Anlage läuft 20 Jahre ab ihrem Baujahr, danach wird sie ersetzt oder stillgelegt. Im LP: Zubau b = R·x ≥ 0 je Land (`builds_matrix`, b[t] = x[t] − x[t−1] + b[t−20]); vorher galt „Anlagen laufen bis 2100“ (x nie fallend). Die Bedingung legt zugleich fest, welches Land wann entnimmt, sonst sprängen die Regionen hin und her. Die Emissionen je Tonne (Bau eingeschlossen) zählen weiter im Jahr der Entnahme.
- **Klima:** FaIR-Kernel derselben Kette wie beim Baum (1 t marginal, linear auf Gt skaliert; 1 Gt entnommen 2026 → −0,34 mK in 2100).
  - Gegenprobe mit vollem FaIR auf derselben Jahresachse (FaIR-Zeitgrenze j+1 = LP-Jahr j): 2098 kühlt der Pfad um 7,7 % stärker als im LP gerechnet. Die Linearisierung ist also konservativ.
  - Eine frühere Fassung verglich die Achsen um ein Jahr versetzt und meldete 4,7 %.
- **η je Land:** Median der besten 10 % der DAC-tauglichen Zellen mit einem Sedimentbecken innerhalb von 100 km (Gidden-Raster, bewertete und nicht bewertete Becken; 39 % der Gitterzellen). 148 Länder kommen in Frage.
- **Ergebnis Hauptfall (Strompfad SSP2-NDC):**
  - Nötig sind **6,9 Gt/a**, voll ab 2067, insgesamt 272 Gt.
  - **2040:** vor allem Frankreich (0,04 Gt/a).
  - **2050:** 0,34 Gt/a, davon Algerien 0,24.
  - **2060:** 2,1 Gt/a (Libyen 1,0, Ägypten 0,3, Algerien 0,2, USA 0,2).
  - **Ab 2070:** USA 3,75, Australien 1,25, Libyen 1,0, Ägypten 0,3, Algerien 0,2 Gt/a (CO₂-Ziel; mit dem Temperaturziel ist die Aufteilung leicht anders, die Kapazität gleich).
  - Der Netto-Anteil der genutzten Anlagen liegt in jedem Jahrzehnt bei 96–97 %. Gebaut wird dort, wo der Strom dann schon sauber ist.
- **Kapazität nach Zieljahr** (dieselben 262 Gt netto schon bis zum Zieljahr): 2085: 12,9 Gt/a; 2090: 9,9 Gt/a; 2095: 8,1 Gt/a; 2100: 6,9 Gt/a. Mit dem Temperaturziel ab dem Zieljahr wäre es mehr (2085: 32 Gt/a), weil die Lücke vor 2100 größer ist.
- **Strompfade** (Netto-Anteil, Median über die Länder 2026 → 2040 → 2060; nötige Kapazität):

  | Strompfad | Netto-Anteil | Kapazität |
  |---|---|---|
  | SSP2-NPi | 37 → 81 → 90 % | 7,1 Gt/a |
  | SSP2-NDC | 43 → 92 → 94 % | 6,9 Gt/a |
  | SSP2-PkBudg650 | 41 → 93 → 96 % | 6,9 Gt/a |

  Der Strommix ändert die Menge kaum: Wegen der Wachstumsgrenze wird DAC erst groß, wenn der Strom ohnehin sauber ist.
- **Sensitivitäten:**
  - 11 %/a (Ammoniak-Analogie): 2100 nicht erreichbar, 128 von 262 Gt (Temperaturziel: es bleiben 50 von 87 mK).
  - Technisches Potenzial statt prudent limit: 6,9 Gt/a.
  - Median statt bestes Dezil: 6,9 Gt/a.
- **Einordnung:** 6,9 Gt/a liegen über den vorsichtigen Schätzungen (3–4 Gt/a, Chiquier et al. 2025) und im Bereich der optimistischen Modelle. Mit rund 1,5 MWh/t braucht das etwa 10 000 TWh Strom, ein Drittel der heutigen Weltstromerzeugung.
- **Nicht enthalten:** Kosten, Strom- und Wasserverfügbarkeit, Injektionsraten je Becken, Anlagenlebensdauer, Basalt-Mineralisierung.

### Deck-Fassung (Stand 2026-10-13, Umbau): niedrigste Spitze, dann so früh wie möglich zurück

Die Folien nutzen `solve_min_peak(…, danach="frueh")` (`scripts/build_zeitpfade_data.py`, `scripts/build_dacfilm_data.py`), Lücke nach den Bäumen als Forst, alle Bäume 2026 gepflanzt. Die LPs löst Gurobi, wenn installiert und lizenziert, sonst HiGHS (`_lp`, `NBS_LP=highs` erzwingt HiGHS).

1. Niedrigste Spitze der Erwärmung über 1,5 °C.
2. Bei dieser Spitze das früheste Jahr, ab dem bis 2100 höchstens 1,5 °C gilt (Bisektion: ist ein Jahr möglich, dann jedes spätere).
3. In diesem Jahr möglichst wenig Kapazität (größte Jahresentnahme weltweit), dann bei dieser Kapazität möglichst wenig Entnahme insgesamt.

| | Spitze | 1,5 °C ab | Kapazität |
|---|---|---|---|
| ≤ 20 %/a (Hauptfall) | 0,31 K | 2083 | 49 Gt/a |
| ≤ 30 %/a | 0,31 K | 2072 | 63 Gt/a |
| ≤ 50 %/a | 0,30 K | 2063 | 61 Gt/a |
| ohne Grenze | 0,04 K | 2041 | 72 Gt/a 2026–2045 |

- **Zieljahr statt frühestens** (≤ 20 %/a, gleiche Spitze): 2085: 31 Gt/a; 2090: 16; 2095: 8,8; 2100: 6,0 Gt/a.
- **Wo:** 1 050 Gt bis 2100, 72 % der sicheren Speicher; die Speicher je Land binden, darum 110 Länder: USA 13 %, Australien 11 %, Kanada 7 %, China 5 %, Algerien 4 %.
- **Spitze:** ohne DAC 311,3 mK, mit DAC 310,9 mK; um 2048 sind erst 0,2 Gt/a gebaut.

### Kosten im Nachgang

`path_cost` rechnet die Kosten des optimierten Pfads, ohne sie mitzuoptimieren: Investition bei jedem Bau und Ersatz, Betrieb, Sorbens und Energie je Jahr, Kostenannahmen nach Okosun et al. 2026 (optimistisch/Median/pessimistisch, reale EUR 2024, unverzinst).

| Kosten | €/t | teuerstes Jahr (2077) | Summe bis 2100 |
|---|---|---|---|
| optimistisch | 128 | 7,4 Bio. € | 134 Bio. € |
| Median | 212 | 13,8 Bio. € | 223 Bio. € |
| pessimistisch | 322 | 21,3 Bio. € | 339 Bio. € |

- **Vergleich:** BIP der EU-27 2024: 18,1 Bio. € (Eurostat `nama_10_gdp`, 18 101 412 Mio. €). Explizite Subventionen fossiler Energie weltweit 2023: 620 Mrd. USD (IEA Fossil Fuel Subsidies Database), mit dem EZB-Jahresmittel 2024 (1,0824 USD/€) 0,57 Bio. €. Das teuerste Jahr kostet im Median 76 % des EU-BIP, das 24-Fache der Subventionen; die Summe sind gut zwölf Jahre EU-BIP. Die IMF-Zahl mit nicht bezahlten Schäden (rund 7 Bio. USD 2022) ist kein ausgegebenes Geld und steht nur in den Notizen.
- **Kostenoptimal mit Zieljahr 2100** (`solve_cost`, Backup): rund 225 Gt, 29–72 Bio. €, Median 48 Bio. €; 1,5 °C ab 2090 kostet rund 70 % mehr.

## Quellen

- Sendi, M., Bui, M., Mac Dowell, N., Fennell, P. (2022): One Earth 5, 1153–1164. Supplement: Vergleich mit Climeworks-Daten.
- Harris, I., Osborn, T. J., Jones, P., Lister, D. (2020): Version 4 of the CRU TS monthly high-resolution gridded multivariate climate dataset. Sci. Data 7, 109.
- Sacchi, R. et al. (2022): PRospective EnvironMental Impact asSEment (premise). Renew. Sustain. Energy Rev. 160, 112311. REMIND-EU-Szenarien über premise.
- Natural Earth, Admin 0 Countries 1:50m (public domain).
- Hasler, N. et al. (2024): Nat. Commun. 15, 2275 (Albedo-Offset).
- Gidden, M. J. et al. (2025): A prudent planetary limit for geologic carbon storage. Nature 645, 124–132. Daten: doi:10.5281/zenodo.18343187.
- Zurbriggen, T. et al. (2026): Short-term action is key for gigaton-scale Direct Air Capture by 2050. Nat. Commun. 17, 6184.
