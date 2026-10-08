"""Storyline fixes in chapters 1-2 (HTML only); applied by new_vergleich.py after the chapter rebuild.

* slides 9/10 become one slide: the last click dims the local effects
* "Was der Baum mit seiner Umgebung tauscht" (kg against W) and the ladder go to the live backup
* "Gemeinsame Währung" asks the kg-or-W question itself
* "Die Erde erwärmt sich träge" introduces the net share per tree (used for trees and DAC later)
* notes of the main part numbered 1..n again
"""
import re


def _take(page: str, title: str) -> tuple[str, str]:
    m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(title) + r'"[^>]*>.*?</section>\n\n?',
                  page, flags=re.S)
    assert m, title
    return page[: m.start()] + page[m.end():], m.group(0)


def patch(page: str) -> str:
    def rep(old, new):
        nonlocal page
        assert old in page, old[:70]
        page = page.replace(old, new, 1)

    moved = []
    page, s10 = _take(page, "Was Bäume tun: zwei globale Wirkungen")
    page, s20 = _take(page, "Was der Baum mit seiner Umgebung tauscht")
    page, s27 = _take(page, "Was jede Erweiterung der Systemgrenze kostet")
    moved += [s10, s20, s27]

    # 9: one more click, the local effects step back (what slide 10 did)
    rep('<div class="body"><svg class="trees-do" data-export="s_baeume_tun" viewBox="0 0 1424 540" style="flex:1; width:100%; min-height:0" aria-label="Wirkungen eines Baums"></svg></div>',
        '<div class="body"><svg class="trees-do" data-export="s_baeume_tun" viewBox="0 0 1424 540" style="flex:1; width:100%; min-height:0" aria-label="Wirkungen eines Baums"></svg><span class="dimtrigger" data-step="7" aria-hidden="true"></span></div>')
    rep("/* slide 9: the local effects step back */",
        "/* slide 9: the local effects step back (last click on slide 9, or the whole of a data-tree=\"dim\" slide) */\n"
        ".slide:has(.dimtrigger.shown) .dimmable { opacity: .22 !important; transition: opacity .8s var(--ease); }\n"
        ".dimtrigger { display: none; }")
    rep('<p>Wenn man hier aufhört, hat man genau die naive Rechnung: Der Baum ist ein Speicher, und was hineingeht, bleibt drin. Die nächsten Folien zeigen, was dabei fehlt.</p>\n    <p class="q">Falls Fragen kommen — Einheiten: alle Größen in kg Kohlenstoff, bezogen auf einen Baum und auf den betrachteten Zeitraum.<br>Der hochgestellte Index C sagt: Wir bilanzieren das Element Kohlenstoff, nicht die Gesamtmasse.</p>\n  </aside>\n</section>\n\n<section class="slide" data-ch="baeume" data-title="Kohlenstoff-Aufnahme">',
        '<p>Wenn man hier aufhört, hat man genau die naive Rechnung: Der Baum ist ein Speicher, und was hineingeht, bleibt drin. Die nächsten Folien zeigen, was dabei fehlt.</p>\n    <p>Letzter Klick: Für das globale Klima zählen nur die beiden oberen Wirkungen, Kohlenstoff und Licht. Verdunstung, Windschutz, Lebensraum und Schatten wirken vor Ort; sie kommen ganz am Ende wieder vor.</p>\n    <p class="q">Falls Fragen kommen — Einheiten: alle Größen in kg Kohlenstoff, bezogen auf einen Baum und auf den betrachteten Zeitraum.<br>Der hochgestellte Index C sagt: Wir bilanzieren das Element Kohlenstoff, nicht die Gesamtmasse.</p>\n  </aside>\n</section>\n\n<section class="slide" data-ch="baeume" data-title="Kohlenstoff-Aufnahme">')

    # 21 (was 22): the question of slide 20 is asked here
    rep('<p class="takeaway" data-step="1" style="--d:0; font-size:21px">Beides jetzt in Watt, in einem Bild: Licht wärmt (oben), das bisher entnommene CO₂ kühlt (unten) — rund 0,9 W je kg.',
        '<p class="takeaway" data-step="1" style="--d:0; font-size:21px">Kilogramm CO₂ und Watt Licht lassen sich nur in einer gemeinsamen Währung vergleichen: Energie. Licht wärmt (oben), das bisher entnommene CO₂ kühlt (unten) — rund 0,9 W je kg.')

    # 25: the net share per tree
    rep('Ein zusätzliches Watt je m² erwärmt die Erde nicht sofort: die Oberfläche in Jahren, den tiefen Ozean über Jahrhunderte (links). So wird aus dem Antrieb die Temperatur (rechts). Mit dem Klimasystem kühlt der Wald an allen drei Orten vom ersten Jahr an — in Joensuu (FI) aber 2100 nur mit 34 % der Kühlung von Aachen (DE), bei Marabá (BR) fast doppelt so stark.</p>',
        'Ein zusätzliches Watt je m² erwärmt die Erde nicht sofort, sondern über Jahrzehnte (links). So wird aus dem Antrieb die Temperatur (rechts). Gestrichelt: was das CO₂ allein brächte. Nach Albedo bleibt davon 2100 in Aachen (DE) 65 %, in Joensuu (FI) 32 %, bei Marabá (BR) 83 % — der Netto-Anteil. An ihm messen wir später auch die Maschine.</p>')
    rep('<p>Rechnerisch ist die Temperatur die Summe aller Jahre Antrieb,',
        '<p>Links: So reagiert die Erde auf ein dauerhaft zusätzliches Watt je Quadratmeter — die Oberfläche in Jahren, der tiefe Ozean über Jahrhunderte. Rechts das Ergebnis je Baum. Gestrichelt, was der Baum mit seinem Kohlenstoff allein bewirken würde; durchgezogen, was nach der Albedo übrig bleibt. Das Verhältnis nenne ich den Netto-Anteil: In Aachen bleiben zwei Drittel, in Joensuu ein Drittel, bei Marabá über vier Fünftel. Diese eine Zahl brauchen wir am Ende wieder — für die ganze Fläche und für die Maschine, die dieselbe Frage beantworten muss: Welcher Anteil der entnommenen Tonne wirkt netto?</p>\n    <p>Rechnerisch ist die Temperatur die Summe aller Jahre Antrieb,')

    rep("getrennt zeigt sie die Leiter auf der nächsten Folie.",
        "getrennt zeigt sie die Leiter im Backup („Was jede Erweiterung der Systemgrenze kostet“).")

    # the moved slides behind the backup, without note numbers
    block = "".join(re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', s) for s in moved)
    rep("<!-- VERGLEICH-ALT:", "<!-- KAPITEL 1-2, aus dem Hauptteil genommen (2026-10-06): live im Backup. -->\n" + block + "\n<!-- VERGLEICH-ALT:")

    # notes of the main part numbered 1..n
    head, tail = page.split("<!-- BACKUP:BEGIN -->", 1)
    n = iter(range(1, 1000))
    head = re.sub(r'<aside class="notes" data-n="\d+">', lambda m: f'<aside class="notes" data-n="{next(n)}">', head)
    return head + "<!-- BACKUP:BEGIN -->" + tail
