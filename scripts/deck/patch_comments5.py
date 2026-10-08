"""Artifact comments of 2026-10-08 afternoon: date on the title, slide 21 wording and solved form, slide 25 caption,
'Zwei Wirkungen' out, closing slide with an outlook and 'go plant trees', then the end (method slide to backup)."""

from __future__ import annotations

import re

from patch_story4 import _rep, _sec

CSS = """
.mapnote { font: 400 19px/1.35 var(--sans); color: var(--muted); margin: 0; }
.ptab { width: 100%; border-collapse: collapse; font: 400 18px/1.3 var(--sans); color: var(--ink-2); margin: 2px 0 6px; }
.ptab th, .ptab td { padding: 2px 6px; text-align: right; border: 0; }
.ptab th:first-child, .ptab td:first-child { text-align: left; }
.ptab thead th { font-weight: 600; color: var(--muted); font-size: 17px; border-bottom: 1px solid var(--line, #d6ccb6); }
.pnote { font: italic 400 18px/1.3 var(--serif); color: var(--ink-2); margin: 0 0 2px; }
.outlook { border-left: 4px solid var(--ch); padding: 10px 0 10px 22px; margin-top: 18px; }
.outlook h4 { font: 600 23px/1.3 var(--sans); color: var(--ch); margin: 0 0 6px; }
.outlook p { font: 400 21px/1.45 var(--sans); color: var(--ink-2); margin: 0; }
"""


def patch(page: str) -> str:
    page = page.replace("</style>", CSS + "</style>", 1)
    page = _rep(page, "<b>Timo Diepers</b> · Promotionsvortrag<br>", "<b>Timo Diepers</b> · Promotionsvortrag · 13.11.2026<br>")
    page = _rep(page, "Je Baum: Aachen 34 W, Joensuu 45 W, Marabá 21 W. Zwei Wirkungen, zwei Einheiten.</p>",
                "Je Baum: Aachen 34 W, Joensuu 45 W, Marabá 21 W.</p>")
    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)

    # slide 20 (total forcing per tree) folded into slide 21: the total forcing becomes the road of the
    # temperature slide, the slide itself goes to the backup
    m = _sec(main, "Temperaturantwort auf den Strahlungsantrieb")
    sec = m.group(0)
    road21 = ('<div class="road" style="height:52px; margin-bottom:12px"><span>Antrieb des Baums</span><span class="tex" style="font-size:25px">'
                     '$\\varphi(t) = \\pc{\\tau_{\\mathrm{atm}}}\\,\\bq{\\Delta\\dot Q_{\\mathrm{Baum}}}(t)\\,/\\,\\pc{A_{\\mathrm{Erde}}}'
                     ' + \\cq{\\varepsilon_{\\mathrm{CO_2}}}(t)\\;\\cq{\\Delta m_{\\mathrm{CO_2}}}(t)\\quad\\longrightarrow\\quad'
                     '\\htmlClass{hl on hl-t}{\\tq{\\Delta T}(t)}$</span></div>')
    sec, k = re.subn(r'<div class="road" style="height:52px; margin-bottom:12px">.*?</div>', lambda _: road21, sec, count=1, flags=re.S)
    assert k == 1
    sec = _rep(sec, "<h2>Temperaturantwort auf den Strahlungsantrieb</h2>", "<h2>Vom Strahlungsantrieb zur Temperatur</h2>")
    sec = _rep(sec, "<p>Dasselbe Bild, jetzt mit der Frage: Wie wird aus dem Antrieb eine Temperatur?",
               "<p>Oben die beiden Terme zusammen: Albedo und CO₂ ergeben den Antrieb des Baums φ. Und gleich die eigentliche Frage: Wie wird aus dem Antrieb eine Temperatur?")
    sec = sec.replace("seinen Antrieb von der letzten Folie ein", "seinen Antrieb von oben ein")
    main = main[: m.start()] + sec + main[m.end():]
    m = _sec(main, "Gesamter Strahlungsantrieb je Baum")
    moved20 = re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', m.group(0))
    main = main[: m.start()] + main[m.end():]

    # forest-type slide: the growth formula of the slide before, its parameters filled in per place
    m = _sec(main, "Typischer Waldtyp je Ort")
    sec = _rep(m.group(0), '<div class="sidepanel" data-step="1"><p class="ptitle">CO₂-Aufnahme je Baum, gepflanzt 2026</p>',
               '<div class="sidepanel" data-step="1"><p class="ptitle">CO₂-Aufnahme je Baum, gepflanzt 2026</p>'
               '<div class="eq tex" style="font-size:17px; margin:2px 0 4px">$$\\mB(t) = \\pc{m^{c}_{\\mathrm{max}}}\\left(1 - e^{-\\pc{k}\\cdot t}\\right)^{\\pc{p}} \\cdot \\left(1 - \\sc{s_{0}}\\, \\textcolor{aaaaaa}{e^{\\gamma\\cdot \\Delta T_{\\mathrm{w}}}}\\right)$$</div>'
               '<table class="ptab tex"><thead><tr><th></th><th>$\\pc{m^{c}_{\\mathrm{max}}}$ [kg C]</th><th>$\\pc{k}$ [1/a]</th><th>$\\pc{p}$</th><th>$\\sc{s_{0}}$ [1/a]</th></tr></thead><tbody>'
               '<tr><td style="color:#2f6fb7">Aachen</td><td>49</td><td>0,043</td><td>2,0</td><td>0,0085</td></tr>'
               '<tr><td style="color:#b8357f">Joensuu</td><td>33</td><td>0,045</td><td>2,0</td><td>0,0085</td></tr>'
               '<tr><td style="color:#6a4c9c">Marabá</td><td>69</td><td>0,045</td><td>2,0</td><td>0,005</td></tr></tbody></table>')
    sec, k = re.subn(r'<div class="eq tex" style="font-size:22px; margin:0">\$\$\\dot m_\{\\mathrm\{CO_2\}\}.*?\$\$</div>', '', sec, count=1, flags=re.S)
    assert k == 1
    sec = _rep(sec, "<p>Diese Folie ist bewusst die einfachste des Analyseteils.",
               "<p>Das ist die Formel von der Folie davor, jetzt mit den Parametern des Ortes befüllt: Sättigungsvorrat aus Walker et al. für die Zelle, Rate aus Cook-Patton et al., Störungsrate je Waldtyp. Aachen 49 kg Kohlenstoff, Joensuu 33, Marabá 69.</p>\n    <p>Diese Folie ist bewusst die einfachste des Analyseteils.")
    main = main[: m.start()] + sec + main[m.end():]

    # slide 25: what is not reforestable
    m = _sec(main, "Wiederbewaldbare Fläche")
    sec = m.group(0)
    sec = _rep(sec, '<div class="foot"><div></div><p class="takeaway" data-step="1" style="--d:0; font-size:22px">0,83 Gha',
               '<div class="foot"><div><p class="mapnote">Nicht wiederbewaldbar: bestehender Wald, Acker, Stadt, Wüste und offenes Grasland</p></div>'
               '<p class="takeaway" data-step="1" style="--d:0; font-size:22px">0,83 Gha')
    sec = sec.replace("kein Wald, kein Acker, keine Stadt, keine offene Landschaft.",
                      "kein bestehender Wald, kein Acker, keine Stadt, keine Wüste und kein natürlich offenes Grasland.")
    main = main[: m.start()] + sec + main[m.end():]

    # closing slide: outlook, then 'go plant trees'; the method slide goes to the backup -> the talk ends here
    m = _sec(main, "Auf dem Holzweg? Nein.")
    sec = m.group(0)
    sec, k = re.subn(r'\s*<div style="flex:1"></div>\s*<p class="takeaway" data-step="3"[^>]*>.*?</p>',
                     '\n    <div class="outlook rise" data-step="3"><h4>Ausblick: was noch nicht drin ist</h4>'
                     '<p>Nutzung des Holzes, etwa Bauholz statt Beton und Stahl → hilft den Bäumen wahrscheinlich noch mehr<br>'
                     'Lebensraum und Artenvielfalt · lokale Kühlung durch Schatten und Verdunstung · Wasser und Boden</p></div>\n'
                     '    <div style="flex:1"></div>\n'
                     '    <p class="takeaway" data-step="4" style="--d:0; font-size:25px">Also: Geht Bäume pflanzen, dort, wo sie kühlen.</p>',
                     sec, count=1, flags=re.S)
    assert k == 1
    sec = _rep(sec, "Mit der vollen Grenze ist die Antwort: beides, und beides jetzt.</p>",
               "Mit der vollen Grenze ist die Antwort: beides, und beides jetzt.</p>\n"
               "    <p>Klick: Ausblick. Was noch nicht drin ist: die Nutzung des Holzes. Wird es verbaut statt Beton und Stahl, bleibt der Kohlenstoff gebunden und spart Emissionen; das hilft den Bäumen wahrscheinlich noch mehr. Und Bäume tun viel, das hier nicht zählt: Lebensraum, Schatten und lokale Kühlung, Wasser, Boden.</p>\n"
               "    <p>Klick: Also: Geht Bäume pflanzen, dort, wo sie kühlen. Danke.</p>")
    main = main[: m.start()] + sec + main[m.end():]
    m = _sec(main, "Methodischer Beitrag")
    moved = re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', m.group(0))
    main = main[: m.start()] + main[m.end():]
    from patch_story3 import BACKUP_MARK
    backup = backup.replace(BACKUP_MARK, moved + moved20 + BACKUP_MARK, 1)
    n = iter(range(1, 1000))
    main = re.sub(r'<aside class="notes" data-n="\d+">', lambda mm: f'<aside class="notes" data-n="{next(n)}">', main)
    return main + "<!-- BACKUP:BEGIN -->" + backup
