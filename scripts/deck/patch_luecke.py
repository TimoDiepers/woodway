"""Planting-year bars and scenario bars become one slide (2026-10-07): the trees' cumulative net
removal against the cumulative removal the scenario needs, year by year (chart w4). The gap leads to
DAC. Transitions between the sections in takeaways and notes. Applied after patch_naiv."""
import re

SLIDE = '''<section class="slide" data-ch="vergleich" data-title="Beitrag der Aufforstung zum Entnahmebedarf">
  <header class="sh"><h2>Beitrag der Aufforstung zum Entnahmebedarf über die Zeit</h2></header>
  <div class="body">
    <div class="chart" data-chart="w4" data-label="Kumulierte CO₂-Entnahme bis 2100: Bedarf des Szenarios Very Low gegen die Netto-Entnahme der Bäume auf den kühlenden Flächen, gepflanzt 2026 und 2036"></div>
    <p class="takeaway" data-step="1" style="--d:0">Bis 2050 entnehmen die Bäume auf den kühlenden Flächen netto 43 Gt CO₂; das Szenario Very Low setzt bis dahin 53 Gt voraus. Bis 2100 steigt der Bedarf auf 335 Gt, die Bäume liefern 59 Gt (18 %). Zehn Jahre später gepflanzt, sind es 2050 nur 25 Gt. Die Lücke von 276 Gt muss technische Entnahme schließen.</p>
  </div>
  <p class="src">Bedarf: CMIP7-Markerszenario Very Low, neuartige Entnahme und Landsenke, kumuliert ab 2024 (van Vuuren et al. 2026). Bäume: eigene Rechnung, typischer Wald auf den kühlenden Flächen (0,39 Gha); Zeitverlauf aus dem Baummodell, Niveau wie Folie „Wiederbewaldbare Fläche“; netto = brutto × Netto-Anteil (FaIR, SSP2-4.5).</p>
  <aside class="notes" data-n="0">
    <p>Was heißt das in Tonnen, gemessen an dem, was die Szenarien voraussetzen? Schwarz die Entnahme, mit der das Szenario Very Low rechnet, aufsummiert ab heute. Grün die Bäume auf den kühlenden Flächen, 2026 gepflanzt: gepunktet brutto, also das, was im Holz steckt, durchgezogen netto nach Albedo. Hellgrün dieselben Bäume, zehn Jahre später gepflanzt.</p>
    <p>Bis 2050 decken die Bäume einen großen Teil dessen, was das Szenario bis dahin voraussetzt: 43 von 53 Gigatonnen. Danach steigt der Bedarf steil, die Bäume sind ausgewachsen und die Albedo holt auf: 2100 sind es 59 von 335 Gigatonnen. Wer zehn Jahre wartet, hat 2050 nur gut die Hälfte; bis 2100 holt der spätere Wald auf. Die graue Fläche, 276 Gigatonnen, muss also anders entnommen werden. Damit sind wir bei der Frage vom Anfang: Wie gut ist die technische Entnahme, je Tonne?</p>
    <p class="q">Falls Fragen kommen — Andere Szenarien (CMIP7, je mit eigenem FaIR-Hintergrund): Bäume netto 57 bis 63 Gt, 8 % (Low-to-Negative) bis 26 % (High-to-Low) des Bedarfs bis 2100 (Backup „Entnahme-Bedarf der Szenarien“). Pflanzjahr: fünf Jahre später kosten 2050 knapp ein Viertel der Kühlung, zehn Jahre die Hälfte; 2100 fast nichts (Backup „Einfluss des Pflanzjahres“). Der Bedarf enthält die Landsenke der Szenarien, also auch dort schon angenommene Aufforstung; die Bäume hier sind ein Maß für das Potenzial, keine Addition.</p>
  </aside>
</section>

'''


def _take(page: str, title: str) -> tuple[str, str]:
    m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(title) + r'"[^>]*>.*?</section>\n\n?', page, flags=re.S)
    assert m, title
    return page[: m.start()] + page[m.end():], m.group(0)


def _notes_append(main: str, title: str, text: str, first: bool = False) -> str:
    m = re.search(r'data-title="' + re.escape(title) + r'"[^>]*>.*?<aside class="notes" data-n="\d+">\n(.*?)</aside>', main, flags=re.S)
    assert m, title
    if first:
        pos = m.start(1)
    else:
        pos = m.end(1)
    return main[:pos] + f"    <p>{text}</p>\n" + main[pos:]


def patch(page: str) -> str:
    def rep(old, new):
        nonlocal main
        assert old in main, old[:80]
        main = main.replace(old, new, 1)

    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)
    main, pj = _take(main, "Einfluss des Pflanzjahres")
    main, need = _take(main, "Bäume reichen nicht")
    need = need.replace('data-title="Bäume reichen nicht"', 'data-title="Entnahme-Bedarf der Szenarien"')
    anchor = re.search(r'<section class="slide[^"]*"[^>]*data-title="Globale Temperaturwirkung über die Zeit"[^>]*>.*?</section>\n\n?', main, flags=re.S)
    assert anchor
    main = main[: anchor.end()] + SLIDE + main[anchor.end():]
    moved = "".join(re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', x) for x in (pj, need))
    backup = backup.replace("<!-- KAPITEL 1-2, aus dem Hauptteil genommen", moved + "<!-- KAPITEL 1-2, aus dem Hauptteil genommen", 1)

    # transition to DAC: visible on the process slide, spoken in the notes
    rep('Der Prozess ist energieintensiv. Mit Wärmepumpe',
        'Für die Lücke kommt vor allem Direct Air Capture in Frage. Der Prozess ist energieintensiv. Mit Wärmepumpe')
    rep("Bäume reichen nicht, also brauchen wir die Maschine. Wie funktioniert sie?",
        "Die Lücke von eben muss technische Entnahme schließen. Am weitesten entwickelt ist Direct Air Capture, hier das Sorbens-Verfahren. Wie funktioniert es?")
    rep("Lohnt sich die Maschine? Die Karte zeigt,", "Jetzt dieselbe Frage wie beim Baum: Welcher Anteil der entnommenen Tonne bleibt netto? Die Karte zeigt,")
    # references to the slides that moved
    main = main.replace("„Entnahme-Bedarf der Szenarien“", "„Beitrag der Aufforstung zum Entnahmebedarf“")
    # bridges in the notes between the sections
    main = _notes_append(main, "Temperaturwirkung eines Baums je Ort",
                         "Das ist die Wirkung je Baum. Im nächsten Kapitel nehmen wir alle Flächen zusammen, auf denen Wald wachsen kann, und vergleichen das Ergebnis mit dem, was die Szenarien an Entnahme voraussetzen, und mit DAC.")
    main = _notes_append(main, "Globale Temperaturwirkung über die Zeit",
                         "Millikelvin sind schwer einzuordnen. Die nächste Folie rechnet dieselben Bäume in Tonnen CO₂ um und stellt sie dem Bedarf der Szenarien gegenüber.")
    main = _notes_append(main, "Netto-Entnahme von DAC",
                         "Diese Karte setzt einen Strompfad voraus. Wie robust ist das? Die nächste Folie rechnet drei Pfade.")
    main = _notes_append(main, "DAC in drei Strompfaden",
                         "Damit haben wir für Baum und DAC dieselbe Größe, je Ort und Jahr. Daraus folgt eine Priorisierung.")
    n = iter(range(1, 1000))
    main = re.sub(r'<aside class="notes" data-n="\d+">', lambda m: f'<aside class="notes" data-n="{next(n)}">', main)
    return main + "<!-- BACKUP:BEGIN -->" + backup
