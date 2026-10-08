"""Scientific register on the visible slides of the main part (2026-10-07): no "schluckt", "holt aus der
Luft", "Maschine", "sauberer Strom", "Strohmann" ... The author's own titles ("Ingenieure auf dem
Holzweg?", "Auf dem Holzweg? Nein.") stay. Applied last; speaker notes are left as spoken text."""
import re

R = [
    # chapters and navigation
    ("Was ein Baum mit Kohlenstoff und Sonnenlicht macht", "Kohlenstoffaufnahme und Albedo eines Baums"),
    (">Was ein Baum mit Kohlenstoff</text>", ">Kohlenstoffaufnahme und</text>"),
    (">und Sonnenlicht macht</text>", ">Albedo eines Baums</text>"),
    (">Was alle Bäume bewirken —</text>", ">Globale Wirkung der Aufforstung</text>"),
    (">und wozu die Maschine?</text>", ">und Vergleich mit DAC</text>"),
    ("Was alle Bäume zusammen bewirken — und wozu die Maschine", "Globale Wirkung der Aufforstung und Vergleich mit DAC"),
    ("Baum und Maschine", "Bäume und DAC"),
    # 3
    ("Wer 1,5 °C nahekommt, rechnet mit großer CO₂-Entnahme:", "Szenarien nahe 1,5 °C setzen große CO₂-Entnahme voraus:"),
    # 4
    ('data-title="Wozu eine Maschine?"', 'data-title="Wozu technische CO₂-Entnahme?"'),
    ("<h2>Die Natur kann das schon — wozu eine Maschine?</h2>", "<h2>Natürliche und technische CO₂-Entnahme</h2>"),
    (">mit Sonnenlicht</text>", ">durch Photosynthese</text>"),
    (">Die Maschine</text>", ">DAC-Anlage</text>"),
    ("Braucht es die Maschine überhaupt?", "Wozu technische CO₂-Entnahme, wenn Bäume CO₂ binden?"),
    ("Ingenieure bauen dafür eine Maschine mit Gebläsen, Wärme, Strom und Speicher. Braucht es die?",
     "Direct Air Capture braucht Gebläse, Wärme, Strom und Speicher. Wozu technische Entnahme?"),
    # 5, 6
    ('data-title="Naive Rechnung"', 'data-title="Überschlagsrechnung"'),
    ("<h2>Naive Rechnung</h2>", "<h2>Überschlagsrechnung mit Bilanzgrenze um den Baum</h2>"),
    ("Diese Rechnung zieht die Grenze um den Baum. Wir ziehen sie Schritt für Schritt weiter, bis das Klima drin ist — und schauen, was dann von ihr übrig bleibt.",
     "Diese Rechnung zieht die Bilanzgrenze um den Baum. Wir erweitern sie schrittweise, bis das Klimasystem enthalten ist, und prüfen, was von ihrem Ergebnis bleibt."),
    ('data-title="Kein Strohmann"', 'data-title="Die Rechnung in der Literatur"'),
    ("<h2>Kein Strohmann: so stand die Rechnung in Science</h2>", "<h2>Dieselbe Rechnung in der Literatur: Bastin et al. (2019)</h2>"),
    ("Der Rest der Kritik kam als Kriterienkatalog.", "Weitere Kritik wurde als Kriterienkatalog formuliert."),
    ("Die naive Rechnung ist kein Strohmann: Sie ist publiziert, hoch zitiert und politisch wirksam geworden. Genau deshalb lohnt es sich, nicht ihr Ergebnis zu korrigieren, sondern ihre Bilanz.",
     "Die Überschlagsrechnung ist publiziert, vielfach zitiert und politisch wirksam geworden. Wir korrigieren deshalb nicht ihr Ergebnis, sondern ihre Bilanzgrenze."),
    # 10
    ("holt CO₂ aus der Luft, baut daraus Zucker und Holz", "nimmt CO₂ aus der Atmosphäre auf und baut daraus Biomasse auf"),
    # 14
    ("Mit der Grenze um den Baum gilt: Was der Baum hat, fehlt der Luft. Wie viel, hängt am Ort — der Mischwald in Aachen (DE) holt 1,5-mal so viel wie der im finnischen Joensuu (FI); der Regenwald bei Marabá (BR) holt am meisten, 1,4-mal so viel wie Aachen (DE).",
     "Mit der Bilanzgrenze um den Baum gilt: Was der Baum aufnimmt, wird der Atmosphäre entzogen. Die Menge hängt vom Ort ab: Der Mischwald in Aachen (DE) nimmt 1,5-mal so viel auf wie der in Joensuu (FI), der Regenwald bei Marabá (BR) 1,4-mal so viel wie Aachen (DE)."),
    ("jung immer mehr, am meisten um 2041, danach weniger, bis er gesättigt ist.", "Sie steigt in der Jugendphase, erreicht um 2041 ihr Maximum und nimmt bis zur Sättigung ab."),
    # 15
    ('aria-label="Schema: Sonnenlicht auf Baum und Boden, zurückgeworfener und geschluckter Anteil"', 'aria-label="Schema: Sonnenstrahlung auf Baum und Boden, reflektierter und absorbierter Anteil"'),
    (">Was geschluckt wird</text>", ">Absorbierter Anteil</text>"),
    (">wirft 30 % zurück, schluckt 70 %</text>", ">reflektiert 30 %, absorbiert 70 %</text>"),
    (">wirft 70 % zurück, schluckt 30 %</text>", ">reflektiert 70 %, absorbiert 30 %</text>"),
    (">Baum schluckt 40 % mehr Licht</text>", ">Wald: +40 Prozentpunkte</text>"),
    (">Je größer der Baum, desto mehr Boden</text>", ">Mit wachsendem Kronenschluss bedeckt der</text>"),
    (">verdeckt er — und desto mehr Licht bleibt.</text>", ">Baum mehr Boden und absorbiert mehr Strahlung.</text>"),
    # 16
    (">BAUM SCHLUCKT MEHR</text>", ">ZUSÄTZLICH ABSORBIERT</text>"),
    (">Mehr Sonne</text>", ">Höhere Einstrahlung</text>"),
    (">1000 W Sonne</text>", ">1000 W Einstrahlung</text>"),
    (">Helles Laub wirft mehr zurück:</text>", ">Helleres Laub reflektiert mehr:</text>"),
    (">Schnee wirft fast alles zurück:</text>", ">Schnee reflektiert fast alles:</text>"),
    # 17
    ("Wie viel Licht ein Baum zusätzlich schluckt, hängt an zwei Dingen: wie viel Sonne ankommt (im Süden mehr) und wie viel dunkler der Wald ist als die Fläche, die er ersetzt (wo Schnee liegt, viel dunkler).",
     "Die zusätzlich absorbierte Strahlung hängt von zwei Größen ab: von der Einstrahlung an der Oberfläche (in niedrigen Breiten höher) und vom Albedo-Kontrast zwischen Wald und der Fläche, die er ersetzt (bei Schneebedeckung besonders groß)."),
    ("Karte: zusätzlich absorbiertes Sonnenlicht je Baum", "Karte: zusätzlich absorbierte Sonnenstrahlung je Baum"),
    # 21, 22
    ("Impulsantwort: was von einer emittierten Tonne in der Luft bleibt und was von einer entnommenen Tonne der Luft fehlt, 75 Jahre",
     "Impulsantwort: atmosphärischer Anteil einer emittierten und einer entnommenen Tonne CO₂ über 75 Jahre"),
    ("Je Baum: bisher geholtes CO₂ (Balken) und was davon der Luft fehlt (Linien)", "Je Baum: kumulierte CO₂-Aufnahme (Balken) und Abnahme des atmosphärischen CO₂ (Linien)"),
    # 24, 26, 27
    ("abgeschwächt durch Impulsantwort und vollere Atmosphäre.", "abgeschwächt durch die Impulsantwort und die steigende CO₂-Konzentration."),
    (">CO₂ wirkt je kg schwächer, je voller die Luft<", ">Strahlungseffizienz sinkt mit der CO₂-Konzentration<"),
    ("im hohen Norden und in trockenen Gebieten wärmt er unterm Strich.", "in hohen Breiten und Trockengebieten wirkt er netto erwärmend."),
    ("Wachstum, Albedo, Rückgabe an Ozean und Land, vollere Atmosphäre, Störung", "Wachstum, Albedo, Rückgabe durch Ozean und Land, steigende CO₂-Konzentration, Störung"),
    # 29
    ("Platz für rund 1,7 Billionen Bäume — die naive Rechnung brauchte 2,1 Billionen. Kühlen tut der Baum, 2026 gepflanzt, davon nur auf",
     "das entspricht rund 1,7 Billionen Bäumen; die Überschlagsrechnung setzte 2,1 Billionen voraus. Kühlend wirkt ein 2026 gepflanzter Baum davon nur auf"),
    ("auf der übrigen, etwas größeren Hälfte, im Norden und im Trockenen, wärmt er.", "auf der übrigen, etwas größeren Hälfte, in hohen Breiten und Trockengebieten, wirkt er erwärmend."),
    # 30
    ("Die Albedo holt mit dem Kronenschluss auf:", "Der Albedo-Effekt wächst mit dem Kronenschluss:"),
    ("Welche Fläche richtig ist, hängt davon ab, wann man fragt.", "Welche Fläche günstiger ist, hängt vom Bewertungszeitpunkt ab."),
    # 31
    ("Für die Spitze der Erwärmung um 2050 nicht: Fünf Jahre Warten kosten dort knapp ein Viertel der Kühlung, zehn Jahre die Hälfte, zwanzig Jahre fast alles. Bäume müssen also jetzt gepflanzt werden.",
     "Für das Maximum der Erwärmung um 2050 nicht: Eine Verzögerung um fünf Jahre verringert die Kühlung dort um knapp ein Viertel, um zehn Jahre um die Hälfte, um zwanzig Jahre fast vollständig. Für die Wirkung um 2050 ist der Pflanzzeitpunkt entscheidend."),
    # 32
    ("Wer die Erwärmung niedrig halten will, setzt auf Entnahme:", "Szenarien mit geringer Erwärmung setzen CO₂-Entnahme voraus:"),
    ("Unsere Bäume liefern in derselben Welt netto", "Aufforstung auf den kühlenden Flächen liefert im selben Szenario netto"),
    ("in wärmeren Welten etwas weniger", "in wärmeren Szenarien etwas weniger"),
    ("Es braucht also auch Maschinen.", "Technische Entnahme ist daher zusätzlich nötig."),
    # 33
    (">Luft ohne CO₂</text>", ">CO₂-arme Abluft</text>"),
    (">Kammer zu: Vakuum und<", ">Unter Vakuum und mit<"),
    (">Dampf um 100 °C lösen<", ">Dampf (100 °C) desorbiert<"),
    (">Je nach Wetter 1,1 bis 1,9 MWh:<", ">Je nach Klima 1,1 bis 1,9 MWh:<"),
    (">Gebläse drücken Luft durch</text>", ">Gebläse fördern Luft durch</text>"),
    (">Kalte Luft drückt die Wärmepumpe,</text>", ">Niedrige Temperatur senkt den COP,</text>"),
    (">feuchte Luft kostet Wärme.</text>", ">hohe Feuchte erhöht den Wärmebedarf.</text>"),
    ("Der Prozess braucht vor allem Energie. Mit einer Wärmepumpe wird daraus nur Strom: rund 1,5 MWh je Tonne CO₂. Wie sauber DAC entnimmt, hängt damit am Strom; wie viel davon nötig ist, am Wetter.",
     "Der Prozess ist energieintensiv. Mit Wärmepumpe wird der gesamte Bedarf elektrisch: rund 1,5 MWh je Tonne CO₂. Der Netto-Anteil hängt damit von der Emissionsintensität des Stroms ab, der Strombedarf vom lokalen Klima."),
    # 36
    ("Wie schnell der Strom sauber wird, verschiebt DAC um einige Jahre, nicht das Bild:", "Das Tempo der Dekarbonisierung verschiebt die Ergebnisse um einige Jahre, ändert sie aber qualitativ nicht:"),
    # 37
    ("<h2>Rangfolge für Bäume und DAC: wo zuerst, wo nicht</h2>", "<h2>Priorisierung von Aufforstung und DAC nach Ort und Zeit</h2>"),
    ('data-title="Rangfolge für Bäume und DAC"', 'data-title="Priorisierung von Aufforstung und DAC"'),
    (">MASCHINE (DAC)</text>", ">DIRECT AIR CAPTURE</text>"),
    (">Wo er am stärksten kühlt, und früh</text>", ">Kühlende Flächen, frühe Pflanzung</text>"),
    (">Wo der Strom sauber ist</text>", ">Emissionsarmer Strom</text>"),
    ("Früh: 5 Jahre Warten kosten 2050 knapp ein Viertel.", "Früh: 5 Jahre Verzögerung kosten 2050 knapp ein Viertel."),
    ("Dazu bringt der Wald vor Ort, was keine Maschine liefert: Schatten, Verdunstung, Windschutz, Lebensraum.",
     "Zusätzlich hat Wald lokale Wirkungen, die DAC nicht hat: Beschattung, Verdunstung, Windschutz, Lebensraum."),
    ("Beim Baum begrenzt die Albedo, bei der Maschine der Strom.", "Beim Baum begrenzt die Albedo, bei DAC die Emissionsintensität des Stroms."),
    ('aria-label="Zwei mal zwei: Bäume und DAC, jeweils wo zuerst und wo nicht"', 'aria-label="Priorisierung von Aufforstung und DAC nach Ort und Zeit"'),
    # 38
    ("Maschinen werden gebraucht, aber nicht überall", "DAC wird gebraucht, aber nicht an jedem Ort"),
    ("Zuerst dort, wo der Strom sauber ist;", "Zuerst dort, wo der Strom emissionsarm ist;"),
    ("Bäume früh, Maschinen mit der Energiewende", "Aufforstung früh, DAC mit der Energiewende"),
    ("dazu bringt der Wald vor Ort Schatten und Lebensraum.", "zusätzlich hat Wald lokale Wirkungen wie Beschattung und Lebensraum."),
    ("DAC wirkt ab Betrieb und wird mit sauberem Strom besser.", "DAC wirkt ab Inbetriebnahme; sein Netto-Anteil steigt mit emissionsärmerem Strom."),
    ("Ohne Maschinen lässt sich der Bedarf", "Ohne technische Entnahme lässt sich der Bedarf"),
    ("Für Bäume und DAC hängt die Wirkung je Tonne am Ort und am Zeitpunkt.", "Für Aufforstung und DAC hängt die Wirkung je Tonne von Ort und Zeitpunkt ab."),
    ("Die naive Rechnung zog die Grenze um den Baum; mit der vollen Systemgrenze heißt die Antwort: beides, jeweils am richtigen Ort.",
     "Die Überschlagsrechnung zog die Bilanzgrenze um den Baum; mit der erweiterten Systemgrenze lautet die Antwort: beides, jeweils am geeigneten Ort."),
    # 39
    (">Maschine (DAC)</th>", ">DAC</th>"),
    ("dieselbe zeitaufgelöste Rechnung je Ort für Bäume und DAC", "dieselbe zeitaufgelöste Rechnung je Ort für Aufforstung und DAC"),
    ("Warten kostet vor allem um 2050.", "Eine Verzögerung wirkt vor allem um 2050."),
]


GLOBAL = [
    # ECharts appends its tooltip to the chart host as well: only the chart's own container fills the host
    (".chart[data-ec] > div { position: absolute !important; inset: 0; }",
     ".chart[data-ec] > div:first-child { position: absolute !important; inset: 0; }"),
    # slide 8 lives in a <template> outside the sections
    (">Reflexion von Sonnenlicht</text>", ">Reflexion von Sonnenstrahlung</text>"),
    (">CO₂ aus der Luft wird zu Holz.</text>", ">CO₂ aus der Atmosphäre wird zu Biomasse.</text>"),
]


def patch(page: str) -> str:
    for old, new in GLOBAL:
        assert old in page, old[:70]
        page = page.replace(old, new)
    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)
    # visible part only: keep the speaker notes as they are
    parts = re.split(r'(<aside class="notes".*?</aside>)', main, flags=re.S)
    vis = "\x00".join(parts[0::2])
    for old, new in R:
        pat = re.compile(re.escape(old).replace("\\ ", "[  ]"))
        vis, n = pat.subn(lambda m: new, vis)
        assert n >= 1, old[:80]
    vparts = vis.split("\x00")
    out = []
    for i, v in enumerate(vparts):
        out.append(v)
        if i < len(parts[1::2]):
            out.append(parts[1::2][i])
    return "".join(out) + "<!-- BACKUP:BEGIN -->" + backup
