"""Slides merged from the artifact comments of 2026-10-07 (applied after patch_lesbar):
the albedo slide becomes the first state of the four-case slide (the reference case large, it shrinks
into its corner on the first click), and the uptake curves join the forest-type map as a side panel.
The slides taken out stay live in the backup."""
import re

BACKUP_MARK = "<!-- KAPITEL 1-2, aus dem Hauptteil genommen"

CSS = """
/* merged albedo slide: the reference case starts large and shrinks into its corner */
.zoomref { transform: translate(0px, 6px) scale(2.05); transition: transform .9s var(--ease); }
svg:has(.zoomnext.shown) .zoomref { transform: none; }
/* merged forest-type slide: the uptake curves come in as a panel at the right */
.sidepanel { position: absolute; top: 0; right: 0; bottom: 0; width: 470px; z-index: 3;
  display: flex; flex-direction: column; gap: 8px; padding: 20px 24px 22px;
  background: var(--paper); border: 1px solid var(--paper-line); border-radius: 10px;
  box-shadow: 0 18px 40px -22px rgba(30, 26, 18, .55);
  opacity: 0; transform: translateX(48px); transition: opacity .45s var(--ease), transform .6s var(--ease); }
.sidepanel.shown { opacity: 1; transform: none; }
.sidepanel .ptitle { font: 600 21px/1.25 var(--sans); color: var(--ink); }
.sidepanel .chart { flex: 1; min-height: 0; }
"""


def _sec(page: str, title: str) -> re.Match:
    m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(title) + r'"[^>]*>.*?</section>\n\n?', page, flags=re.S)
    assert m, title
    return m


def _to_backup(main: str, backup: str, title: str) -> tuple[str, str, str]:
    m = _sec(main, title)
    sec = re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', m.group(0))
    notes = re.search(r'<aside class="notes">\n?(.*?)</aside>', sec, flags=re.S).group(1)
    assert BACKUP_MARK in backup
    backup = backup.replace(BACKUP_MARK, sec + BACKUP_MARK, 1)
    return main[: m.start()] + main[m.end():], backup, notes


def _edit(main: str, title: str, fn) -> str:
    m = _sec(main, title)
    return main[: m.start()] + fn(m.group(0)) + main[m.end():]


def patch(page: str) -> str:
    head, sep, tail = page.partition("</style>")
    assert sep
    page = head + CSS + sep + tail
    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)

    # albedo: one slide
    main, backup, notes14 = _to_backup(main, backup, "Albedo-Änderung")

    def faelle(sec: str) -> str:
        first = '<g class="pop"><rect x="0" y="0" width="692" height="276"'
        second = '<g class="pop" data-step="1">'
        assert first in sec and second in sec
        sec = sec.replace(first, '<g class="zoomref">' + first, 1)
        sec = sec.replace(second, '</g><g class="pop zoomnext" data-step="1" style="--d:800">', 1)
        n = re.search(r'<aside class="notes" data-n="\d+">\n?', sec)
        add = (notes14 + "    <p>Erst der Referenzfall, in absoluten Zahlen: 1000 Watt kommen an, das dunkle Laub wirft 300 zurück, "
               "die Wiese 700. Der Baum absorbiert also 400 Watt mehr. Klick: Der Fall rückt in die Ecke, und wir ändern je eine Größe.</p>\n")
        return sec[: n.end()] + add + sec[n.end():]
    main = _edit(main, "Albedo-Änderung: vier Fälle", faelle)

    # forest type and uptake: one slide, the curves in a side panel
    main, backup, notes13 = _to_backup(main, backup, "CO₂-Aufnahme je Baum")

    def wald(sec: str) -> str:
        foot = '<div class="foot"><div></div><p class="takeaway" data-step="1" style="--d:0">Gepflanzt wird der typische Wald des Ortes; der Kohlenstoff hängt am Ort, nicht am Typ.</p></div>'
        assert foot in sec, "foot"
        panel = ('<div class="sidepanel" data-step="1">'
                 '<p class="ptitle">CO₂-Aufnahme je Baum, gepflanzt 2026</p>'
                 '<div class="chart" data-chart="b6s" data-label="CO₂-Aufnahme eines Baums je Jahr von 2026 bis 2100, Aachen (DE), Joensuu (FI) und Marabá (BR)"></div>'
                 '<div class="eq tex" style="font-size:22px; margin:0">$$\\dot m_{\\mathrm{CO_2}}(t) = -\\tfrac{44}{12}\\,\\dot m(t)$$</div>'
                 '<p class="takeaway" data-step="2" style="--d:0; margin-top:6px; font-size:21px">Typischer Wald des Ortes. Bis 2100 je Baum: '
                 'Aachen 163, Joensuu 111, Marabá 232 kg CO₂.</p></div>')
        sec = sec.replace(foot, panel, 1)
        sec = sec.replace('<div class="body">', '<div class="body" style="position:relative">', 1)
        sec = sec.replace('<h2>Typischer Waldtyp je Ort</h2>', '<h2>Typischer Waldtyp und CO₂-Aufnahme je Ort</h2>', 1)
        sec = sec.replace('beides auf 0,5° zusammengefasst.</p>', 'beides auf 0,5° zusammengefasst. Kurven: eigene Rechnung, Wachstumskurve mit Kohlenstoff der Zelle '
                          '(Walker et al. 2022) und Tempo (Cook-Patton et al. 2020); Störung: Annahme, heutige Rate.</p>', 1)
        n = re.search(r'<aside class="notes" data-n="\d+">\n?', sec)
        add = ('    <p>Klick: Rechts kommen die Kurven für die drei markierten Orte — so viel CO₂ nimmt ein Baum des typischen Waldes dort je Jahr auf.</p>\n'
               + notes13)
        return sec[: n.end()] + sec[n.end():].replace('</aside>', add + '  </aside>', 1)
    main = _edit(main, "Typischer Waldtyp je Ort", wald)

    n = iter(range(1, 1000))
    main = re.sub(r'<aside class="notes" data-n="\d+">', lambda m: f'<aside class="notes" data-n="{next(n)}">', main)
    return main + "<!-- BACKUP:BEGIN -->" + backup
