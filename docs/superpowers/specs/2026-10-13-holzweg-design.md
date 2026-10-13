# Letztes Kapitel neu: „Sind wir auf dem Holzweg?“ — Waldspeicher, Störung und Holznutzung

Stand 2026-10-13, abgestimmt mit Timo im Gespräch.

## Ziel und Rahmen

- Das letzte Kapitel des Promotionsvortrags „Aufforstung als Klima-Technologie“ ersetzt das DAC-Kapitel. DAC wandert vollständig ins Backup (Folien bleiben dort, Woodway-Anker „DAC-Ausbau“ bleibt bestehen).
- Der Vortrag soll thematisch nicht zu nah an der Dissertation liegen: zeitexplizite Ökobilanz (Brightway, premise) und Optimierung dürfen benutzt werden, aber nur im Hintergrund. Auf den Folien stehen Physik und Ergebnisse, die Methoden nur in den Quellenzeilen und Notizen.
- Die wachsende Systemgrenze geht einen letzten Schritt: vom Wald in die Technosphäre (Holz) und zurück zum Klima (Störung mit der Erwärmung).

## Geschichte und Folien (etwa 5 neue Folien)

1. **„Sind wir auf dem Holzweg?“** (Kapitelstart, bleibt). Statt des Ingenieurs mit DAC die Frage: Der Wald wächst, und dann? Bleibt der Kohlenstoff dort?
2. **Der Speicher ist nicht sicher.** Störungen nehmen mit der Erwärmung zu. Karte: Anteil des im Wald gebundenen Kohlenstoffs, der bis 2100 durch Störung verloren geht, Very Low gegen Medium.
3. **Was man mit dem Holz machen kann.** Fünf Wege als Bild, je mit „wie lange gebunden“ und „was eingespart wird“: stehen lassen, Bauholz (begrenzt durch die Bau-Nachfrage), Energie, BECCS, Biokohle.
4. **Die beste Wahl je Ort (Very Low).** Karte der gewählten Option je 2°-Block; daneben die Kühlung 2050 und in Kelvin-Jahren gegenüber „alles stehen lassen“.
5. **Wie die Wahl mit der Erwärmung kippt.** Anteile der Wege (und Karte) in Very Low, Medium-Low, Medium.
6. **Wir wissen nicht, welche Welt kommt (Höhepunkt).** Ob „die anderen“ mitmachen, entscheidet die Welt. Kreuztabelle: Strategie optimiert für Welt X (Zeilen) gegen eintretende Welt Y (Spalten), Feld = Verlust gegenüber der richtigen Wahl; dazu die robuste Strategie (kleinstes größtes Bedauern).
7. **Fazit „Auf dem Holzweg? Nein.“** Punkt 3 neu, je nach Ergebnis (z. B. „Weil wir nicht wissen, ob die anderen mitmachen: nicht nur pflanzen, sondern auch für den Kohlenstoff im Holz sorgen“).

Backup: Bau-Grenze als Variante (mehr/weniger Holzbau), γ-Sensitivität, Methode in Kürze.

Erwartete Pointe (zu prüfen, nicht vorausgesetzt): Je wärmer die Welt, desto riskanter der Waldspeicher und desto mehr wandert in Holz und dauerhafte Speicher. Zeigen die Zahlen etwas anderes, wird die Geschichte angepasst, nicht das Modell (siehe wissenschaftlich ehrlich bleiben).

## Modell

**Einheit.** 2°-Blöcke mit kühlender Fläche (wie die Karten des Decks, rund 3 000), bepflanzt im Bonn-Tempo wie der Forst-Pfad des Kapitels Potenzial (`nbs.tree_paths`).

**Optionen je Block.**
- Stehen lassen: Wachstum bis zur Sättigung, Störung nach p = p₀·e^(γ·T) (`nbs.tree.disturbance_probability`, Waldtyp-Parameter aus `nbs.species`).
- Fällen mit Umtriebszeit ½×, 1× oder 1,5× der Zonen-Umtriebszeit (`ROTATION_BY_ZONE`), danach neu pflanzen. Das Stammholz (70 %, `STEM_SHARE`) wird frei aufgeteilt auf Bauholz, Energie, BECCS, Biokohle; Reste zerfallen wie bisher.

Entscheidungsvariablen: Flächenanteil je Block und Umtriebs-Option (Summe 1) und die Holzaufteilung je Block (Anteile, Summe 1). Die Wirkung ist linear in diesen Anteilen, daher ein lineares Programm.

**Wirkung je Option** (je ha, Jahr für Jahr, 2026–2100):
- CO₂: Wachstum, Störungsverluste (sofort verbrannter Anteil + Totholz), Ernte, Abbau der Produkte. Bauholz: Lebensdauer 50 Jahre (Halbwertszeit wie IPCC-Holzprodukte, „sawnwood“ 35 Jahre als Sensitivität), danach Energie.
- Einsparung: eingesparter Zement und Stahl (Bauholz), eingesparte Wärme/Strom (Energie), je Region und Jahr aus einer zeitexpliziten Ökobilanz (ecoinvent 3.12, premise-Hintergründe, Brightway-Projekt `ei312_REMIND_EU`). Funktionelle Einheiten: Brettsperrholz-Decke gegen Stahlbeton-Decke; Holzhackschnitzel-Wärme gegen den regionalen Wärmemix.
- BECCS: dauerhaft gespeichertes CO₂ abzüglich Energieaufwand für Abscheidung und Transport; Strom als Gutschrift wie Energie.
- Biokohle: stabiler Anteil 75 % über 100 Jahre (Lehmann et al.), Rest zerfällt.
- Albedo: Kahlschlag setzt den Bestand zurück, die Albedo-Wirkung folgt dem Nachwachsen wie im bestehenden Modell.
- Temperatur: lineare FaIR-Antwort je Tonne bzw. je W/m² wie bei den Bäumen (Kernel aus `nbs.response`), szenarioabhängig.

**Ziel (lexikografisch).** 1. Kühlung durch die Bäume im Jahr 2050 maximal. 2. Bei dieser Kühlung die Summe der Kühlung 2026–2100 (Kelvin-Jahre) maximal.

**Grenze.** Bauholz je Jahr höchstens die Holzbau-Nachfrage einer Literaturstudie (Kandidaten: Churkina et al. 2020, Mishra et al. 2022; Auswahl wird Timo vor dem Rechnen vorgelegt). Energie, BECCS und Biokohle ohne Mengengrenze; BECCS innerhalb des Speichers je Land (Gidden et al. 2025).

**Welten.** Very Low, Medium-Low, Medium (CMIP7). Die Welt bestimmt zugleich die Hintergrund-Erwärmung (Störungsrisiko), den CO₂-Hintergrund der Klimaantwort und den premise-Hintergrund der Einsparung: Very Low ↔ REMIND-EU SSP2-PkBudg650, Medium-Low ↔ SSP2-NDC, Medium ↔ SSP2-NPi (alle drei liegen schon für DAC vor).

**Robuste Strategie.** Ein weiteres lineares Programm über alle drei Welten zugleich: minimiere das größte Bedauern (Kühlungsverlust gegenüber der für die eintretende Welt optimalen Wahl), in derselben Reihenfolge 2050, dann Kelvin-Jahre.

**Sensitivität.** γ = 0,1 / 0,2 / 0,3 je K (γ ist gesetzt, siehe `nbs.species`).

**Bewusste Vereinfachung.** Die Wahl wirkt nicht auf die globale Erwärmung zurück (Effekt im Millikelvin-Bereich); die Erwärmung kommt aus der jeweiligen Welt. Wird so in den Notizen genannt.

## Umsetzung (Grobstruktur)

- `src/nbs/holz.py`: Optionen und ihre Wirkung je Block (CO₂-Flüsse, Albedo), Produktpools, Biokohle, BECCS.
- `scripts/holz_lca_precompute.py` (im h2-transport-lco-venv wie die DAC-Ökobilanz): Einsparung je t Holz für Bauholz und Energie, je REMIND-Region, Jahr und Pfad → `data/holz/einsparung.json`.
- `src/nbs/holz_optim.py`: das lineare Programm (je Welt, robust), Ergebnis je Block.
- `scripts/build_holz_data.py` → `deck/chart_data/holz.json` (Karten, Anteile, Kreuztabelle).
- Folien in `deck/src/slides/05_holz.html` (statt `05_dac.html`; DAC-Folien ins Backup), Karten über die bestehende Hex-Karten-Pipeline (`nbs.map_fields`), Diagramme als ECharts wie im Deck.
- Tests: Massenbilanz je Option (Kohlenstoff bleibt erhalten), Grenzfälle (keine Ernte = Pfad „kuehlt“ mit Störung), Bau-Grenze greift, robuste Lösung liegt zwischen den Einzellösungen.

## Offene Entscheidungen vor dem Rechnen

- Wahl der Holzbau-Nachfragestudie (wird vorgelegt).
- Ob ecoinvent 3.12 eine passende Brettsperrholz- und Stahlbeton-Decke enthält; sonst Ersatz über Schnittholz und Beton/Bewehrungsstahl je m³, wird vorgelegt.
