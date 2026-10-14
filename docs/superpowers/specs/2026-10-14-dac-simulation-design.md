# DACCS als Kostenoptimierung statt dreistufiger Optimierung

Stand 2026-10-14, mit Timo besprochen.

## Warum

Die dreistufige Optimierung (niedrigste Spitze → so früh wie möglich zurück → wenig Kapazität) lieferte kaum eigene Aussagen:

- Stufe 1 wirkte bei jeder Wachstumsgrenze praktisch nicht (Spitze 323,9 → 323,3 mK).
- Stufe 2 zwang den Ausbau an die Wachstumsgrenze, ohne Kosten zu kennen (66 Gt/a, 97 % der Speicher, Kosten über dem EU-BIP).
- Anlagen mussten 20 Jahre laufen; die Kurve fiel danach bis etwa 1,2 °C.

Eine reine Simulation („an der Wachstumsgrenze wachsen, bis es reicht“) funktioniert nicht: Exponentielles Wachstum baut die größten Mengen in den letzten Jahren (20 %/a: 138 Gt/a, 50 %/a: 444 Gt/a). Ohne Vorausschau gibt es keinen sinnvollen Stopp.

Danach „DACCS ohne Grenze, kleinste Weltkapazität“ (`solve_offset`). Timo: „ergibt keinen Sinn … was ist da das Ziel?“ und „bau es als Kostenoptimierung auf mit constraint cooling mindestens so dass die remaining Kurve vom Baum geoffsettet wird … nimm die optimistischen Kosten“.

## Rechnung

`nbs.dac_optim.solve_cost_offset`: Bau b[c, y] und Betrieb u[c, y] je Land und Jahr. Ziel: geringste Kosten (optimistischer Fall Okosun et al. 2026: Investition und Fixkosten je Anlage, Sorbens und Energie je Tonne). Bedingung: Kühlung ≥ Erwärmung über 1,5 °C nach den Bäumen, ab 2027. Anlagen höchstens 20 Jahre, Betrieb ≤ Kapazität, Speicher je Land, η_C je Land und Jahr, keine Wachstumsgrenze. `price_plan` bewertet denselben Plan mit Median und pessimistisch.

Ergebnis: 75 Gt/a, fast alles 2026–2028 gebaut, Betrieb bis 2047, 1 020 Gt (70 % der Speicher), 143 Bio. € (Median 247, pessimistisch 388), 2026 allein 26 Bio. €. Mit 20 %/a wären 75 Gt/a erst 2080 erreicht (nur als Satz auf der Folie). Vegan: 37 Gt/a bis 2037, 59 Bio. €. Nach 2050 sinkt die Kurve unter 1,5 °C: Very Low sinkt von selbst, entnommenes CO₂ bleibt entnommen.

## Story

Folie 28 „Die Lücke mit DACCS füllen“ (Rechnung, Ergebnis, Geht das?, Kosten) → „Was können wir anders machen?“ → 29 „Warum Ernährung?“ → 30 vegan, den Rest füllt dieselbe Kostenoptimierung.

## Begriffe

DACCS, wo Entnahme mit Speicherung gemeint ist (Ausbau, Mengen, Kosten, Vergleich); DAC für Prozess und Maschine (Sorbens-DAC, DAC-Modell, Energiebedarf).
