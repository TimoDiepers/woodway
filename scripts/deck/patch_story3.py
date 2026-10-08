"""Storyline after the comments of 2026-10-08 (applied last):
- title without "Ingenieure auf dem Holzweg?"; that question becomes a break slide before the DAC part
- third chapter "Potenzial" (no DAC teaser in the overview)
- the per-place temperature map opens chapter 3 ("not negative everywhere"), then the availability map
  with the time curves as an overlay, the removal need of Very Low in the same plot (in mK)
- the old time-curve slide and the removal-gap slide go to the backup
- slide 4: DAC "noch in Entwicklung"; slide 5 framed as a myth check."""
import re

BACKUP_MARK = "<!-- KAPITEL 1-2, aus dem Hauptteil genommen"

CSS = """
/* availability map with the time curves as an overlay card */
.overlay { position: absolute; top: 0; right: 0; bottom: 6px; width: 900px; z-index: 3; display: flex; flex-direction: column; gap: 6px;
  padding: 18px 24px 18px; background: var(--paper); border: 1px solid var(--paper-line); border-radius: 12px;
  box-shadow: 0 22px 46px -24px rgba(30, 26, 18, .6); opacity: 0; transform: translateY(24px);
  transition: opacity .5s var(--ease), transform .6s var(--ease); }
.overlay.shown { opacity: 1; transform: none; }
.overlay .chart { flex: 1; min-height: 0; }
.overlay .takeaway { margin-top: 4px; font-size: 21px; }
.body:has(.overlay.shown) > .foot { opacity: 0; transition: opacity .3s; }
"""


def _sec(page, title):
    m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(title) + r'"[^>]*>.*?</section>\n*', page, flags=re.S)
    assert m, title
    return m


def _rep(text, a, b, count=1):
    pat = re.compile(re.escape(a).replace(r"\ ", " ").replace(" ", "[  ]"))
    text, k = pat.subn(lambda m: b, text, count=count)
    assert k >= 1, a[:70]
    return text


def _take(main, title):
    m = _sec(main, title)
    return main[: m.start()] + main[m.end():], m.group(0)


def patch(page: str) -> str:
    head, sep, tail = page.partition("</style>")
    page = head + CSS + sep + tail
    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)

    # ---- title: without the question (it comes back before DAC)
    main = _rep(main, '    <p class="q rise">Ingenieure auf dem Holzweg?</p>\n', "")

    # ---- slide 4: DAC still in development
    main = _rep(main, '>Direct Air Capture</text>', '>noch in Entwicklung</text>')

    # ---- slide 5: myth check
    main = _rep(main, 'SO GERECHNET IN <i>SCIENCE</i> (BASTIN ET AL. 2019)</p>', 'DER MYTHOS · <i>SCIENCE</i> (BASTIN ET AL. 2019)</p>')
    main = _rep(main, 'color:var(--clay); margin-bottom:10px">ABER</p>', 'color:var(--clay); margin-bottom:10px">DER CHECK</p>')
    main = _rep(main, '<p class="takeaway" data-step="5" style="--d:0">Umstritten → Bilanzgrenze schrittweise bis zum Klimasystem erweitern.</p>',
                '<p class="takeaway" data-step="5" style="--d:0">So einfach ist es nicht → wir rechnen nach: Bilanzgrenze schrittweise bis zum Klimasystem erweitern.</p>')
    main = _rep(main, "Es gibt also Diskussionsbedarf. Deshalb sehen wir uns die Rechnung jetzt genauer an",
                "So einfach ist es also nicht. Wir machen den Mythen-Check: Wir sehen uns die Rechnung genauer an")

    # ---- third chapter "Potenzial": chapter slides (pills), overview, divider
    main = main.replace('<rect x="398" y="110" width="252" height="44" rx="22"', '<rect x="398" y="110" width="150" height="44" rx="22"')
    main = re.sub(r'(<text x="442" y="139" font-size="20" font-weight="(?:400|600)" fill="[^"]*">)Bäume und DAC</text>', r'\1Potenzial</text>', main)
    main = _rep(main, '<text y="390" fill="var(--fjord)" font-size="44">Bäume und DAC</text>', '<text y="390" fill="var(--fjord)">Potenzial</text>')
    main = _rep(main, '<text y="436" fill="var(--muted)" font-family="IBM Plex Sans" font-weight="400" font-size="21">Globale Wirkung der Aufforstung</text>',
                '<text y="436" fill="var(--muted)" font-family="IBM Plex Sans" font-weight="400" font-size="21">Alle Bäume, alle Flächen:</text>')
    main = _rep(main, '<text y="464" fill="var(--muted)" font-family="IBM Plex Sans" font-weight="400" font-size="21">und Vergleich mit DAC</text>',
                '<text y="464" fill="var(--muted)" font-family="IBM Plex Sans" font-weight="400" font-size="21">globale Wirkung</text>')
    main = _rep(main, 'aria-label="Drei Kapitel: Bäume, Klima, Bäume und DAC — eine wachsende Systemgrenze"',
                'aria-label="Drei Kapitel: Bäume, Klima, Potenzial — eine wachsende Systemgrenze"')
    main = _rep(main, "Baum und Maschine = alle Flächen, beide Entnahmewege.", "Potenzial = alle Bäume auf allen Flächen.")
    main = _rep(main, 'data-title="Bäume und DAC"', 'data-title="Potenzial"')
    main = _rep(main, '<h1 class="rise">Bäume und DAC</h1><p class="rise" style="--d:300">Globale Wirkung der Aufforstung und Vergleich mit DAC</p>',
                '<h1 class="rise">Potenzial</h1><p class="rise" style="--d:300">Globale Wirkung der Aufforstung</p>')
    main = _rep(main, "Erst die Ergebnisse für den Wald: Wo ist Platz, wie wirkt er über die Zeit, wann muss man pflanzen, und reicht das? Dann die Frage vom Anfang: Braucht es die Maschine — und wo und ab wann lohnt sie sich?",
                "Wo kühlt der Baum, wo ist Platz, wie wirkt der ganze Wald über die Zeit — und reicht das für das, was die Szenarien voraussetzen?")

    # ---- the per-place map opens chapter 3
    main, place = _take(main, "Temperaturwirkung eines Baums je Ort")
    place = place.replace('data-ch="klima"', 'data-ch="vergleich"', 1)
    place = _rep(place, ">Tropen: stärkste Kühlung. Hohe Breiten, Trockengebiete: netto erwärmend.</p>",
                 ">Gar nicht überall negativ! Problem: viele Flächen liegen dort, wo der Baum wärmt.</p>")
    place = _rep(place, "Das ist die Wirkung je Baum. Im nächsten Kapitel nehmen wir alle Flächen zusammen, auf denen Wald wachsen kann, und vergleichen das Ergebnis mit dem, was die Szenarien an Entnahme voraussetzen, und mit DAC.",
                 "Gar nicht überall kühlt der Baum. Die Frage ist also: Wo gibt es überhaupt Platz für Wald — und liegt der dort, wo er kühlt?")
    place = _rep(place, "Bisher drei Orte. Jetzt dieselbe Kette für jeden Ort:", "Bisher drei Orte. Jetzt dieselbe Kette für jeden Ort der Erde:")
    div = _sec(main, "Potenzial")
    main = main[: div.end()] + place + main[div.end():]

    # ---- time curves and need as an overlay on the availability map; old slides to the backup
    main, w2 = _take(main, "Globale Temperaturwirkung über die Zeit")
    main, w4 = _take(main, "Beitrag der Aufforstung zum Entnahmebedarf")
    moved = "".join(re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', x) for x in (w2, w4))
    assert BACKUP_MARK in backup
    backup = backup.replace(BACKUP_MARK, moved + BACKUP_MARK, 1)

    m = _sec(main, "Wiederbewaldbare Fläche")
    sec = m.group(0)
    sec = sec.replace('<div class="body">', '<div class="body" style="position:relative">', 1)
    overlay = ('<div class="overlay" data-step="2">'
               '<div class="chart" data-chart="w2b" data-label="Kühlung der Erde 2026 bis 2100 durch alle Bäume (kühlende und alle Flächen) '
               'gegen die Kühlung, die die Entnahme des Szenarios Very Low bringen würde"></div>'
               '<p class="takeaway" data-step="3" style="--d:0">2100: Bäume 19 mK, Bedarf 114 mK → große Lücke.</p></div>')
    sec = _rep(sec, '<div class="foot"><div></div>', overlay + '<div class="foot"><div></div>')
    sec = _rep(sec, '</p>\n  <aside', ' Kühlung: FaIR je Fläche, SSP2-4,5; Bedarf: Entnahme von Very Low (van Vuuren et al. 2026), dieselbe Kette.</p>\n  <aside')
    notes_add = (
        "    <p>Klick: Was bringt das über die Zeit, und reicht es? Grün alle Bäume auf den kühlenden Flächen, orange auf allen Flächen. "
        "Schwarz die Kühlung, die die Entnahme bringen würde, mit der das Szenario Very Low rechnet — umgerechnet in dieselbe Einheit, Millikelvin. "
        "Bis etwa 2050 liegen die Bäume in derselben Größenordnung; danach steigt der Bedarf steil, die Bäume sind ausgewachsen und die Albedo holt auf. "
        "2100: 19 Millikelvin von den Bäumen, 114 nötig.</p>\n"
        "    <p class=\"q\">Falls Fragen kommen — Bedarf: Entnahme von Very Low ab 2026, rund 335 Gt CO₂ bis 2100, als negative Emission "
        "über die Impulsantwort des Kohlenstoffkreislaufs, den logarithmischen Antrieb gegen den SSP2-4.5-Hintergrund und die Temperaturantwort; "
        "2050 rund 16 mK, 2100 rund 114 mK. Bäume: vier FaIR-Läufe wie auf den Backup-Folien „Globale Temperaturwirkung über die Zeit“ "
        "und „Beitrag der Aufforstung zum Entnahmebedarf“ (dort in Gt: 59 von 335 Gt).</p>\n"
        "    <p>Die Lücke ist groß. Und damit die Frage vom Anfang.</p>\n")
    sec = re.sub(r'(<aside class="notes" data-n="\d+">.*?)(</aside>)', lambda n: n.group(1) + notes_add + n.group(2), sec, count=1, flags=re.S)
    sec = _rep(sec, "Die Karte davor hat gezeigt, was ein Baum wo bewirkt.", "Die Karte davor: Gar nicht überall kühlt der Baum.")
    main = main[: m.start()] + sec + main[m.end():]

    # ---- break before the DAC part: the question of the title
    ch = _sec(main, "Potenzial").group(0)
    deco = re.search(r'<svg class="deco[^"]*"[^>]*>.*?</svg>', ch, flags=re.S).group(0)
    deco = re.sub(r'<g font-family="IBM Plex Sans">.*?</g>(?=<path d="M1010 900)', "", deco, count=1, flags=re.S)
    deco = deco.replace('data-export="s_kapitel_vergleich"', 'data-export="s_holzweg"', 1)
    brk = ('<section class="slide chapter" data-ch="vergleich" data-title="Sind wir auf dem Holzweg?">\n'
           '  <div class="ctext"><h1 class="rise">Sind wir auf dem Holzweg?</h1>'
           '<p class="rise" style="--d:300">Technische CO₂-Entnahme: Direct Air Capture</p></div>\n  ' + deco + '\n'
           '  <aside class="notes" data-n="0">\n'
           '    <p>Bäume allein schließen die Lücke nicht. Die Frage vom Anfang: Sind wir Ingenieure auf dem Holzweg, wenn wir an technischer '
           'Entnahme arbeiten? Rechnen wir Direct Air Capture mit derselben Systemgrenze.</p>\n  </aside>\n</section>\n\n')
    m = _sec(main, "Sorbens-DAC: Prozess und Energiebedarf")
    main = main[: m.start()] + brk + main[m.start():]
    main = _rep(main, "Die Lücke von eben muss technische Entnahme schließen. Am weitesten entwickelt ist Direct Air Capture",
                "Die Lücke muss technische Entnahme schließen. Am weitesten entwickelt ist Direct Air Capture")

    n = iter(range(1, 1000))
    main = re.sub(r'<aside class="notes" data-n="\d+">', lambda mm: f'<aside class="notes" data-n="{next(n)}">', main)
    return main + "<!-- BACKUP:BEGIN -->" + backup
