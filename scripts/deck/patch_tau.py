"""tau_atm = 0.854 instead of 0.8 (Lenton & Vaughan 2009): every albedo-dependent number of the main part
(2026-10-07). Sources: docs/slides/chart_data/fakten.json, pflanzwahl.json, flaechen_zeitreihe.json,
pflanzjahr_global.json, szenarien_cmip7_baeume.json after the rerun; map percentiles, per-tree planting-year
sum and switch year recomputed (scratchpad tau_nums.py, pj.py, sw.py). Two numbers were stale before the
change already (map 5 % percentile -80 -> was -55; '18 % gegen 17 %' -> was 18/19 %).
"""

R = [
    # tau itself
    ("Anteil einer Reflexionsänderung an der Oberfläche, der am Oberrand ankommt — ≈ 0,8<",
     "Anteil einer Reflexionsänderung an der Oberfläche, der am Oberrand ankommt — 0,854<"),
    ("mit dem Anteil τ_atm ≈ 0,8 der Reflexionsänderung", "mit dem Anteil τ_atm = 0,854 der Reflexionsänderung"),
    ("τ_atm ≈ 0,8: Durchlässigkeit der Atmosphäre für Kurzwellenstrahlung von der Oberfläche nach oben, ein globaler Mittelwert (Annahme; Literatur 0,85: Lenton & Vaughan 2009, Cherubini et al. 2012).",
     "τ_atm = 0,854: Durchlässigkeit der Atmosphäre für Kurzwellenstrahlung von der Oberfläche nach oben, globales Jahresmittel bei klarem Himmel, Wurzel der zweiseitigen Transmission 0,730 (Lacis & Hansen 1974; Lenton & Vaughan 2009; Cherubini et al. 2012)."),
    ("Falls Fragen kommen — τ_atm ≈ 0,8: ΔQ̇_Baum gilt an der Oberfläche,", "Falls Fragen kommen — τ_atm = 0,854: ΔQ̇_Baum gilt an der Oberfläche,"),
    ("verlassen am Oberrand nur etwa 8 W weniger die Erde. Wir nehmen einen globalen Mittelwert (Literatur 0,85: Lenton & Vaughan 2009; Cherubini et al. 2012).",
     "verlassen am Oberrand nur etwa 8,5 W weniger die Erde. Wir nehmen den globalen Mittelwert von Lenton & Vaughan (2009), den auch Cherubini et al. (2012) nutzen: die Wurzel der zweiseitigen Transmission 0,730 bei klarem Himmel aus einem Strahlungstransfermodell (Lacis & Hansen 1974)."),
    ("τ_atm ≈ 0,8 (globaler Mittelwert, Annahme; Literatur 0,85: Lenton & Vaughan 2009);", "τ_atm = 0,854 (Lenton & Vaughan 2009);"),
    ("Falls Fragen kommen — τ_atm ≈ 0,8: Anteil einer Reflexionsänderung", "Falls Fragen kommen — τ_atm = 0,854: Anteil einer Reflexionsänderung"),
    # 12, 26: warming feedback per tree
    ("(Aachen −34 → −35 · 10⁻¹⁵ K)", "(Aachen −33 → −34 · 10⁻¹⁵ K)"),
    ("in Aachen von −34 auf −35 · 10⁻¹⁵ K.", "in Aachen von −33 auf −34 · 10⁻¹⁵ K."),
    ("Beide Wege liefern dasselbe (17 % gegen 18 % bis 2100).", "Beide Wege liefern dasselbe (Netto-Anteil aller Flächen 2100: 13 % je Baum summiert, 13 % im Flächenlauf)."),
    # 25: net share per tree
    ("Nach Albedo bleiben 2100 in Aachen (DE) 65 %, in Joensuu (FI) 32 %, bei Marabá (BR) 83 % — der Netto-Anteil.",
     "Nach Albedo bleiben 2100 in Aachen (DE) 62 %, in Joensuu (FI) 27 %, bei Marabá (BR) 82 % — der Netto-Anteil."),
    ("Größenordnung: bis 2100 etwa −3,5·10⁻¹⁴ K je Baum in Aachen, −1,2·10⁻¹⁴ K in Joensuu, −6,5·10⁻¹⁴ K bei Marabá.",
     "Größenordnung: bis 2100 etwa −3,4·10⁻¹⁴ K je Baum in Aachen, −1,0·10⁻¹⁴ K in Joensuu, −6,4·10⁻¹⁴ K bei Marabá."),
    ("für die ganze Fläche liefern beide Wege dasselbe (18 % gegen 17 % bis 2100).",
     "für die ganze Fläche liefern beide Wege dasselbe (Netto-Anteil aller Flächen 2100: je 13 %)."),
    # 27: map per tree
    ("Marabá (−65) liegt im kühlenden Gürtel, Aachen (−35) und Joensuu (−12 · 10⁻¹⁵ K) dazwischen.",
     "Marabá (−64) liegt im kühlenden Gürtel, Aachen (−34) und Joensuu (−10 · 10⁻¹⁵ K) dazwischen."),
    ("5 % der wiederbewaldbaren Fläche kühlen stärker als −80, 5 % wärmen stärker als +26 · 10⁻¹⁵ K.",
     "5 % der wiederbewaldbaren Fläche kühlen stärker als −54, 5 % wärmen stärker als +30 · 10⁻¹⁵ K."),
    ("kühlt auf 50 % der wiederbewaldbaren Fläche (0,42 Gha)", "kühlt auf 47 % der wiederbewaldbaren Fläche (0,39 Gha)"),
    # 29: area
    ("Kühlen tut der Baum, 2025 gepflanzt, davon nur auf 0,42 Gha (0,8 Billionen Bäume); auf der anderen Hälfte, im Norden und im Trockenen, wärmt er.",
     "Kühlen tut der Baum, 2025 gepflanzt, davon nur auf 0,39 Gha (0,8 Billionen Bäume); auf der übrigen, etwas größeren Hälfte, im Norden und im Trockenen, wärmt er."),
    ("Und nur die Hälfte davon kühlt: Von den 0,83 Gha bleiben 0,42 Gha, auf denen ein 2025 gepflanzter Baum bis 2100 kühlt, rund 0,8 Billionen Bäume.",
     "Und nur knapp die Hälfte davon kühlt: Von den 0,83 Gha bleiben 0,39 Gha, auf denen ein 2025 gepflanzter Baum bis 2100 kühlt, rund 0,8 Billionen Bäume."),
    # 30: area time series
    ("Auf den kühlenden 0,42 Gha kühlen sie 2050 um 15 mK, 2100 um 20 mK.", "Auf den kühlenden 0,39 Gha kühlen sie 2050 um 14 mK, 2100 um 19 mK."),
    ("Der Netto-Anteil fällt von 85 % (2050) auf 59 % (2100).", "Der Netto-Anteil fällt von 85 % (2050) auf 58 % (2100)."),
    ("ab 2061 schwächer, 2100 nur noch um 9 mK.", "ab 2060 schwächer, 2100 nur noch um 6,5 mK."),
    ("Grün: alle Bäume auf den 0,42 Gigahektar, auf denen der Baum bis 2100 kühlt, rund 800 Milliarden Bäume.",
     "Grün: alle Bäume auf den 0,39 Gigahektar, auf denen der Baum bis 2100 kühlt, rund 780 Milliarden Bäume."),
    ("2050 bleiben 85 % der Kühlung, 2100 nur noch 59 %.", "2050 bleiben 85 % der Kühlung, 2100 nur noch 58 %."),
    ("Dann holt die Albedo auf, und 2100 bleibt weniger als die Hälfte.", "Dann holt die Albedo auf, und 2100 bleibt nur ein Drittel davon."),
    ("dieselben wie für die 62 Gt auf der nächsten Folie", "dieselben wie für die 59 Gt auf der nächsten Folie"),
    ("Werte: kühlende Flächen 2035 −4,0, 2050 −14,9, 2075 −21,0, 2100 −20,0 mK; ohne Albedo −4,2 / −17,5 / −30,8 / −34,2 mK; alle Flächen −5,5 / −17,4 / −16,0 / −9,2 mK.",
     "Werte: kühlende Flächen 2035 −3,9, 2050 −14,3, 2075 −20,0, 2100 −19,1 mK; ohne Albedo −4,0 / −16,9 / −29,6 / −32,9 mK; alle Flächen −5,4 / −16,9 / −14,2 / −6,5 mK."),
    # 31: planting year
    ("typischer Wald je Zelle auf den 0,42 Gha", "typischer Wald je Zelle auf den 0,39 Gha"),
    ("absolut kühlt die Pflanzung 2025 so 2050 um 15,5 mK, fast wie im FaIR-Lauf mit der ganzen Fläche (14,9 mK).",
     "absolut kühlt die Pflanzung 2025 so 2050 um 14,9 mK, fast wie im FaIR-Lauf mit der ganzen Fläche (14,3 mK)."),
    # 32, 38: scenarios
    ("Unsere Bäume liefern in derselben Welt netto 60 bis 66 Gt, in wärmeren Welten etwas weniger — 8 bis 27 % dessen, was diese Szenarien voraussetzen.",
     "Unsere Bäume liefern in derselben Welt netto 57 bis 63 Gt, in wärmeren Welten etwas weniger — 8 bis 26 % dessen, was diese Szenarien voraussetzen."),
    ("(Kaskade, 106 Gt auf den kühlenden, 155 Gt auf allen Flächen)", "(Kaskade, 102 Gt auf den kühlenden, 155 Gt auf allen Flächen)"),
    ("Die übrigen Folien rechnen mit SSP2-4,5 als mittlerem Hintergrund; dort netto 62 Gt.", "Die übrigen Folien rechnen mit SSP2-4,5 als mittlerem Hintergrund; dort netto 59 Gt."),
    ("Netto 60 bis 66 Gt CO₂ bis 2100, je nach Szenario 8 bis 27 % der Entnahme", "Netto 57 bis 63 Gt CO₂ bis 2100, je nach Szenario 8 bis 26 % der Entnahme"),
    # 35: DAC vs tree
    ("Zum Vergleich: Bäume auf den kühlenden Flächen kommen auf 59 %.", "Zum Vergleich: Bäume auf den kühlenden Flächen kommen auf 58 %."),
    ("Zum Vergleich mit dem Baum, derselbe Netto-Anteil: Aachen 65 %, Joensuu 32 %, Marabá 83 %, über alle kühlenden Flächen 59 %.",
     "Zum Vergleich mit dem Baum, derselbe Netto-Anteil: Aachen 62 %, Joensuu 27 %, Marabá 82 %, über alle kühlenden Flächen 58 %."),
    # 37: ranking
    ("83 %, in Aachen (DE) 65 %, in Joensuu (FI) 32 %.", "82 %, in Aachen (DE) 62 %, in Joensuu (FI) 27 %."),
    ("0,42 Gha · netto 62 Gt CO₂", "0,39 Gha · netto 59 Gt CO₂"),
    ("sinkt die Wirkung von 62 auf 29 Gt CO₂.", "sinkt die Wirkung von 59 auf 21 Gt CO₂."),
    ("0,41 Gha wärmen bis 2100", "0,44 Gha wärmen bis 2100"),
    ("Mit dem Strom von 2020 die Maschine nur auf 21 % der bepflanzbaren Fläche", "Mit dem Strom von 2020 die Maschine nur auf 22 % der bepflanzbaren Fläche"),
    ("Die Zahlen 62 und 29 Gt sind netto nach Albedo bis 2100; 0,41 Gha =", "Die Zahlen 59 und 21 Gt sind netto nach Albedo bis 2100; 0,44 Gha ="),
    # 39
    ("Netto-Anteil je Ort (Aachen (DE) 65 %, Joensuu (FI) 32 %)", "Netto-Anteil je Ort (Aachen (DE) 62 %, Joensuu (FI) 27 %)"),
    ("Zeitverlauf: bis 2061 kühlt", "Zeitverlauf: bis 2060 kühlt"),
    ("käme Aachen auf −158 statt −35 · 10⁻¹⁵ K", "käme Aachen auf −158 statt −34 · 10⁻¹⁵ K"),
]


def patch(page: str) -> str:
    import re

    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)
    for old, new in R:
        # the page mixes plain and no-break spaces (before units); match either, write no-break before units
        pat = re.compile(re.escape(old).replace("\\ ", "[ \u00a0]"))
        new = re.sub(r" (?=(%|mK|Gha|Gt|K\b))", "\u00a0", new)
        main, n = pat.subn(lambda m: new, main)
        assert n >= 1, old[:80]
    main = re.sub(r"0,42([ \u00a0])(Gha|Gigahektar)", r"0,39\1\2", main)
    return main + "<!-- BACKUP:BEGIN -->" + backup
