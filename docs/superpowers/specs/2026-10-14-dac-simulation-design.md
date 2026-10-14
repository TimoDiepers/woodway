# DACCS ohne Grenze statt dreistufiger Optimierung

Stand 2026-10-14, mit Timo besprochen.

## Warum

Die dreistufige Optimierung (niedrigste Spitze → so früh wie möglich zurück → wenig Kapazität) lieferte kaum eigene Aussagen:

- Stufe 1 wirkte bei jeder Wachstumsgrenze praktisch nicht (Spitze 323,9 → 323,3 mK).
- Stufe 2 zwang den Ausbau an die Wachstumsgrenze, ohne Kosten zu kennen (66 Gt/a, 97 % der Speicher, Kosten über dem EU-BIP).
- Anlagen mussten 20 Jahre laufen; die Kurve fiel danach bis etwa 1,2 °C.

Eine reine Simulation („an der Wachstumsgrenze wachsen, bis es reicht“) funktioniert nicht: Exponentielles Wachstum baut die größten Mengen in den letzten Jahren (20 %/a: 138 Gt/a, 50 %/a: 444 Gt/a). Ohne Vorausschau gibt es keinen sinnvollen Stopp.

Timo: „können wir die wachstumsgrenze einfach weglassen und so tun als könnten wir so viel dac machen wie wir wollen um den rest zu offsetten, und dann nachträglich nur qualitativ sagen ‚so schnell könnten wir nie upscalen‘, und die kosten natürlich weiterhin ausrechnen“.

## Rechnung

`nbs.dac_optim.solve_offset`: ohne Wachstumsgrenze die kleinste Weltkapazität, die die Kurve ab 2027 in jedem Jahr bei höchstens 1,5 °C hält, dann bei dieser Kapazität möglichst wenig insgesamt. Länder nach η_C mit sicherem Speicher (Gidden et al. 2025). Anlagen dürfen stillstehen; die Kapazität ist der bisherige Höchststand bis zum Abschalten (`capacity_from_run`). Kosten im Nachgang mit `path_cost_run`: Investition einmal je gebauter Anlage, Fixkosten auf die stehende Kapazität, Sorbens und Energie auf die Entnahme.

Ergebnis (Very Low ohne seine Entnahme, mit Bäumen): 67 Gt/a von 2026 bis 2041, 970 Gt, 221 Bio. € (130–339); 2026 allein 59 Bio. € für den Bau. Mit veganer Welt: 35 Gt/a bis 2036, 390 Gt, 93 Bio. €. Mit 20 %/a ab 8,8 Mt/a 2030 wären 67 Gt/a erst 2079 erreicht (nur als Satz auf der Folie).

## Begriffe

DACCS, wo Entnahme mit Speicherung gemeint ist (Ausbau, Mengen, Kosten, Vergleich); DAC für Prozess und Maschine (Sorbens-DAC, DAC-Modell, Energiebedarf).
