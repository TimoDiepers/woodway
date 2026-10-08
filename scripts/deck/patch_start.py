"""Start year 2026 instead of 2025 (2026-10-07): planting, DAC start and every time axis; numbers of the
main part after the rerun (fakten.json, chart_data caches, vals2026.py, tau_nums.py, pj.py, sw.py).
Applied after patch_tau. Slide 14 as a continuous line."""
import re

R = [
    # 5: naive calculation
    ("bindet bis 2100 rund <strong>164 kg CO₂</strong> (45 kg Kohlenstoff).", "bindet bis 2100 rund <strong>163 kg CO₂</strong> (44 kg Kohlenstoff)."),
    ('335 Gt ÷ 0,164 t ≈ <span class="count" data-to="2.0" data-dec="1" data-delay="200">2,0</span> Billionen Bäume',
     '335 Gt ÷ 0,163 t ≈ <span class="count" data-to="2.1" data-dec="1" data-delay="200">2,1</span> Billionen Bäume'),
    ("Aufnahme 2025–2100 (bis zur Sättigung", "Aufnahme 2026–2100 (bis zur Sättigung"),
    # 14: line instead of bars
    ('data-label="CO₂, das ein Baum je Jahr aus der Luft holt, Aachen (DE), Joensuu (FI) und Marabá (BR), jedes zehnte Jahr"',
     'data-label="CO₂-Aufnahme eines Baums je Jahr von 2026 bis 2100, Aachen (DE), Joensuu (FI) und Marabá (BR)"'),
    ("Jeder Balken: so viel CO₂ holt ein Baum in diesem Jahr aus der Luft. Mit der Grenze um den Baum gilt:",
     "Die Linie zeigt, wie viel CO₂ ein Baum in jedem Jahr aufnimmt: jung immer mehr, am meisten um 2041, danach weniger, bis er gesättigt ist. Mit der Grenze um den Baum gilt:"),
    ("Aufsummiert holt ein Baum bis 2100 in Aachen rund 164 kg CO₂ aus der Luft, bei Marabá (südöstlicher Amazonas) rund 233 kg, in Joensuu (Ostfinnland) rund 111 kg:",
     "Jeder Punkt der Linie ist ein Jahr; die Fläche darunter ist, was der Baum insgesamt aufnimmt. Aufsummiert holt ein Baum, 2026 gepflanzt, bis 2100 in Aachen rund 163 kg CO₂ aus der Luft, bei Marabá (südöstlicher Amazonas) rund 232 kg, in Joensuu (Ostfinnland) rund 111 kg:"),
    # 21, 22, 23
    ("eines Pulses von 2025 noch in der Luft", "eines Pulses von 2026 noch in der Luft"),
    ("in Aachen (DE) 84 von 164 kg.", "in Aachen (DE) 84 von 163 kg."),
    ("1,65 → 1,31 · 10⁻¹⁵ (2025 → 2100)", "1,64 → 1,31 · 10⁻¹⁵ (2026 → 2100)"),
    ("im Szenario SSP2-4.5 1,65 · 10⁻¹⁵ W/m² im Jahr 2025,", "im Szenario SSP2-4.5 1,64 · 10⁻¹⁵ W/m² im Jahr 2026,"),
    ("2025 ist sie steiler als 2100", "2026 ist sie steiler als 2100"),
    ("Rechts diese Steigung über die Zeit: 1,65 heute,", "Rechts diese Steigung über die Zeit: 1,64 heute,"),
    # 25, 26, 39: per tree
    ("Nach Albedo bleiben 2100 in Aachen (DE) 62 %, in Joensuu (FI) 27 %, bei Marabá (BR) 82 %",
     "Nach Albedo bleiben 2100 in Aachen (DE) 63 %, in Joensuu (FI) 28 %, bei Marabá (BR) 82 %"),
    ("(Netto-Anteil aller Flächen 2100: je 13 %)", "(Netto-Anteil aller Flächen 2100: je 14 %)"),
    ("(Netto-Anteil aller Flächen 2100: 13 % je Baum summiert, 13 % im Flächenlauf)", "(Netto-Anteil aller Flächen 2100: 14 % je Baum summiert, 14 % im Flächenlauf)"),
    ("käme Aachen auf −158 statt −34", "käme Aachen auf −157 statt −34"),
    ("Netto-Anteil je Ort (Aachen (DE) 62 %, Joensuu (FI) 27 %)", "Netto-Anteil je Ort (Aachen (DE) 63 %, Joensuu (FI) 28 %)"),
    ("Zeitverlauf: bis 2060 kühlt", "Zeitverlauf: bis 2061 kühlt"),
    # 27
    ("5 % wärmen stärker als +30 · 10⁻¹⁵ K", "5 % wärmen stärker als +29 · 10⁻¹⁵ K"),
    ("kühlt auf 47 % der wiederbewaldbaren Fläche", "kühlt auf 48 % der wiederbewaldbaren Fläche"),
    # 29
    ("die naive Rechnung brauchte 2 Billionen", "die naive Rechnung brauchte 2,1 Billionen"),
    ("die naive Rechnung vom Anfang brauchte 2 Billionen", "die naive Rechnung vom Anfang brauchte 2,1 Billionen"),
    ("rund 780 Milliarden Bäume", "rund 790 Milliarden Bäume"),
    # 30
    ("Der Netto-Anteil fällt von 85 % (2050) auf 58 % (2100).", "Der Netto-Anteil fällt von 86 % (2050) auf 58 % (2100)."),
    ("ab 2060 schwächer, 2100 nur noch um 6,5 mK.", "ab 2061 schwächer, 2100 nur noch um 6,8 mK."),
    ("2050 bleiben 85 % der Kühlung, 2100 nur noch 58 %.", "2050 bleiben 86 % der Kühlung, 2100 nur noch 58 %."),
    ("Werte: kühlende Flächen 2035 −3,9, 2050 −14,3, 2075 −20,0, 2100 −19,1 mK; ohne Albedo −4,0 / −16,9 / −29,6 / −32,9 mK; alle Flächen −5,4 / −16,9 / −14,2 / −6,5 mK.",
     "Werte: kühlende Flächen 2035 −3,2, 2050 −13,8, 2075 −20,0, 2100 −19,1 mK; ohne Albedo −3,3 / −16,1 / −29,4 / −33,0 mK; alle Flächen −4,5 / −16,4 / −14,5 / −6,8 mK."),
    # 31, 37, 38: planting year
    ("ob 2025 oder 2045 gepflanzt wird.", "ob 2026 oder 2046 gepflanzt wird."),
    ("Fünf Jahre Warten kosten dort ein Fünftel der Kühlung, zehn Jahre fast die Hälfte, zwanzig Jahre fast alles.",
     "Fünf Jahre Warten kosten dort knapp ein Viertel der Kühlung, zehn Jahre die Hälfte, zwanzig Jahre fast alles."),
    ("Ob 2025 oder 2045 gepflanzt — fast gleich;", "Ob 2026 oder 2046 gepflanzt — fast gleich;"),
    ("Kühlung 2050 relativ zur Pflanzung 2025: 2030 78 %, 2035 54 %, 2040 29 %, 2045 9 %.",
     "Kühlung 2050 relativ zur Pflanzung 2026: 2031 77 %, 2036 51 %, 2041 25 %, 2046 6 %."),
    ("absolut kühlt die Pflanzung 2025 so 2050 um 14,9 mK, fast wie im FaIR-Lauf mit der ganzen Fläche (14,3 mK).",
     "absolut kühlt die Pflanzung 2026 so 2050 um 14,4 mK, fast wie im FaIR-Lauf mit der ganzen Fläche (13,8 mK)."),
    ("Spätere Pflanzjahre als 2045", "Spätere Pflanzjahre als 2046"),
    ("Früh: 5 Jahre Warten kosten 2050 ein Fünftel.", "Früh: 5 Jahre Warten kosten 2050 knapp ein Viertel."),
    ("Fünf Jahre Warten kosten um 2050 ein Fünftel der Kühlung", "Fünf Jahre Warten kosten um 2050 knapp ein Viertel der Kühlung"),
    ("Fünf Jahre später gepflanzt, fehlt um 2050 ein Fünftel der Kühlung", "Fünf Jahre später gepflanzt, fehlt um 2050 knapp ein Viertel der Kühlung"),
    # 35-38: DAC with the electricity of the start year
    ("Mit dem Strom von 2025 bleiben im Median 41 % der entnommenen Tonne netto; auf 3 % des Landes,",
     "Mit dem Strom von 2026 bleiben im Median 46 % der entnommenen Tonne netto; auf 2 % des Landes,"),
    ("Mit dem Strom von heute im Median gut 40 %.", "Mit dem Strom von heute im Median knapp die Hälfte."),
    ("In Joensuu mit finnischem Strom schon 84 %,", "In Joensuu mit finnischem Strom schon 86 %,"),
    ("Mit Kohlestrom bleibt fast nichts: Krakau 5 %, Kinshasa 16 %, Peking 18 %;", "Mit Kohlestrom bleibt wenig: Krakau 17 %, Kinshasa 23 %, Peking 24 %;"),
    ("Aachen 62 %, Joensuu 27 %, Marabá 82 %, über alle kühlenden Flächen 58 %.", "Aachen 63 %, Joensuu 28 %, Marabá 82 %, über alle kühlenden Flächen 58 %."),
    ("Mit dem Strom von 2025 bleiben im Median 36 bis 41 % der Tonne,", "Mit dem Strom von 2026 bleiben im Median 40 bis 46 % der Tonne,"),
    ("Heute liegen alle drei bei knapp 40 %.", "Heute liegen alle drei zwischen 40 und 46 %."),
    ("Median Netto-Anteil 2025 / 2030 / 2040 / 2050: PkBudg650 39 / 62 / 93 / 96 %, NDC 41 / 65 / 91 / 94 %, NPi 36 / 55 / 80 / 89 %.",
     "Median Netto-Anteil 2026 / 2030 / 2040 / 2050: PkBudg650 44 / 62 / 93 / 96 %, NDC 46 / 65 / 91 / 94 %, NPi 40 / 55 / 80 / 89 %."),
    ("Netto emittierend mit dem Strom von 2025: 3 / 4 / 5 % des Landes.", "Netto emittierend mit dem Strom von 2026: 2 / 2 / 3 % des Landes."),
    ("Dass der 1,5-°C-Pfad 2025 knapp unter", "Dass der 1,5-°C-Pfad 2026 knapp unter"),
    ("82 %, in Aachen (DE) 62 %, in Joensuu (FI) 27 %.", "82 %, in Aachen (DE) 63 %, in Joensuu (FI) 28 %."),
    ("sinkt die Wirkung von 59 auf 21 Gt CO₂.", "sinkt die Wirkung von 59 auf 22 Gt CO₂."),
    ("0,44 Gha wärmen bis 2100", "0,43 Gha wärmen bis 2100"),
    ("Joensuu (FI): 84 % der Tonne netto.", "Joensuu (FI): 86 % der Tonne netto."),
    ("Median 2025: 41 % · 2040: 91 %", "Median 2026: 46 % · 2040: 91 %"),
    ("Mit dem Strom von 2025: Krakau (PL) 5 %,", "Mit dem Strom von 2026: Krakau (PL) 17 %,"),
    ("Kinshasa (CD) 16 %, Peking (CN) 18 % netto.", "Kinshasa (CD) 23 %, Peking (CN) 24 % netto."),
    ("Die Zahlen 59 und 21 Gt sind netto nach Albedo bis 2100; 0,44 Gha =", "Die Zahlen 59 und 22 Gt sind netto nach Albedo bis 2100; 0,43 Gha ="),
    ("Mit dem Strom von 2025 bleiben im Median 41 % der Tonne.", "Mit dem Strom von 2026 bleiben im Median 46 % der Tonne."),
    ("In Aachen bleiben zwei Drittel, in Joensuu ein Drittel, bei Marabá über vier Fünftel.",
     "In Aachen bleiben knapp zwei Drittel, in Joensuu gut ein Viertel, bei Marabá über vier Fünftel."),
    ("fünf Jahre Warten kosten ein Fünftel, zehn Jahre die Hälfte.", "fünf Jahre Warten kosten knapp ein Viertel, zehn Jahre die Hälfte."),
]
# every remaining start-year mention (may already be gone)
OPTIONAL = [("Kohlenstoffvorrat eines Baums 2025–2100", "Kohlenstoffvorrat eines Baums 2026–2100"), ("gemessen an der Pflanzung 2025", "gemessen an der Pflanzung 2026"),
            ("Tangenten 2025 und 2100", "Tangenten 2026 und 2100"), ("Antrieb je kg CO₂ 2025 bis 2100", "Antrieb je kg CO₂ 2026 bis 2100"),
            ("gepflanzt 2025", "gepflanzt 2026"), ("2025 gepflanzt", "2026 gepflanzt"), ("2025 bis 2100", "2026 bis 2100")]
KEEP = ("Global Climate Change 2025", "Liang et al. 2025", "Riley et al. 2025", "Fahrenbach", "2025JG")


def patch(page: str) -> str:
    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)
    for old, new in R:
        pat = re.compile(re.escape(old).replace("\\ ", "[  ]"))
        new = re.sub(r" (?=(%|mK|Gha|Gt|kg|K\b))", " ", new) if "<" not in new else new
        main, n = pat.subn(lambda m: new, main)
        assert n >= 1, old[:80]
    for old, new in OPTIONAL:
        main = re.sub(re.escape(old).replace("\\ ", "[ \u00a0]"), new, main)
    # no start year 2025 left in the visible text (references excepted)
    text = re.sub(r"<[^>]+>", " ", main)
    left = [text[max(0, m.start() - 60):m.end() + 30] for m in re.finditer("2025", text)
            if not any(k in text[max(0, m.start() - 40):m.end() + 10] for k in KEEP)]
    assert not left, left
    return main + "<!-- BACKUP:BEGIN -->" + backup
