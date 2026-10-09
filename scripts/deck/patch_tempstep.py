"""Slide 19 -> 20: a question as the bridge, and the temperature slide built up term by term.

- Slide 19 ends with a box: the forcing is known now, but how does a temperature follow from it?
- Slide 20: the road is shortened to phi = phi_alpha + phi_CO2 -> Delta T. The energy balance grows
  one term per click, each with its cue in the drawing and a sentence of explanation; the solution
  comes with a small inset in the drawing (one year of forcing, its decaying contribution).
  Then the chart per tree, then the problem box.
"""

import re

S19 = "Impulsantwort des Kohlenstoffkreislaufs"
S20 = "Temperaturantwort auf den Strahlungsantrieb"

ROAD = ('<div class="road" style="height:52px; margin-bottom:12px"><span>Antrieb des Baums</span><span class="tex" style="font-size:27px">'
        r'$\varphi(t) = \aq{\varphi_\alpha}(t) + \cq{\varphi_{\mathrm{CO_2}}}(t)\quad\longrightarrow\quad\htmlClass{hl on hl-t}{\tq{T}(t)\,?\vphantom{\sum_{t^{\prime} \le t} \varphi(t^{\prime})/\pc{C}\; e^{-\pc{\Lambda}(t-t^{\prime})/\pc{C}}}}$'
        '</span></div>')

RIGHT = r'''<div class="tstep" style="display:flex; flex-direction:column; gap:6px; align-self:start; min-width:0">
      <div class="eq tex" style="font-size:25px; text-align:left; margin:0">$$\st{2}{\htmlClass{hl hl-c}{\pc{C}}\;\;\;}\frac{\mathrm{d}\,\tq{T}}{\mathrm{d}t} \;\;=\;\; \htmlClass{hl hl-p}{\varphi(t)} \st{3}{\;\;\;-\;\;\; \htmlClass{hl hl-l}{\pc{\Lambda}\;\tq{T}(t)}}$$</div>
      <div class="rise ts1" data-step="1" style="--d:200"><p class="ghs"><b style="background:#1b2420">1</b><span class="tex">$\varphi < 0$</span>: Der Baum nimmt CO₂ auf.<br>→ Oben geht mehr Energie hinaus als herein.</p></div>
      <div class="rise ts2" data-step="2" style="--d:200"><p class="ghs"><b style="background:#8a6a1e">2</b>Fehlende Energie kommt aus dem Speicher <span class="tex">$\pc{C}$</span><br>→ Land und Ozean kühlen ab, langsam</p></div>
      <div class="rise ts3" data-step="3" style="--d:200"><p class="ghs"><b style="background:#6b5a1e">3</b><span class="tex">$\pc{\Lambda}$</span> ≈ 1,2 W/m² je K: kühlere Erde strahlt<br>weniger ab → bremst die Abkühlung</p></div>
      <div class="rise ts4" data-step="4" style="--d:200"><div class="eq tex" style="font-size:23px; text-align:left; margin:0 0 2px">$$\htmlClass{hl hl-r}{\tq{\Delta T}(t)} \;\;=\;\; \sum_{t' \le t} \frac{\varphi(t')}{\pc{C}}\; e^{-\frac{\pc{\Lambda}}{\pc{C}}\,(t-t')}$$</div><p class="ghs"><b style="background:#1f7a8c">4</b>Gelöst: jedes Jahr Antrieb ein Beitrag, der abklingt → alle Jahre addiert (Grafik)</p></div>
      <div class="rise ts5" data-step="7" style="--d:200"><p class="ghs"><b style="background:#b2182b">5</b>Je Baum: <span class="tex">$\tq{\Delta T} < 0$</span> an allen drei Orten (Grafik)</p></div>
    </div>'''

# inset in the sky of the drawing: one year of forcing phi(t') and its contribution to Delta T, decaying
# with C/Lambda; two later years faint, to show that they add up
CSS = """
/* slide 20: the fifth point frames Delta T of the solution as the fourth did */
.slide:has(.ts5.shown) .hl-r::before { border-color: #b2182b; background: rgba(178, 24, 43, .07); }
"""

NOTES20 = (
    "    <p>Oben der Antrieb des Baums, kurz: Albedo-Anteil plus CO₂-Anteil, beide kennen wir. Die Frage dieser Folie: Wie wird daraus eine Temperatur? Rechts der Kern: Der Antrieb ändert die Temperatur, dT/dt gleich φ. Den Rest der Energiebilanz bauen wir Stück für Stück daran an.</p>\n"
    "    <p>Klick: Erster Baustein, der Antrieb selbst. Der Baum nimmt CO₂ auf, sein Antrieb ist negativ; die Albedo wärmt dagegen, aber netto überwiegt die Aufnahme. Oben am Rand geht also mehr Energie hinaus als herein — der Baum ist dort eine Energiesenke.</p>\n"
    "    <p>Klick: Woher kommt die fehlende Energie? Aus dem Wärmespeicher der Erde, vor allem aus dem Ozean. Land und Ozean kühlen ab. Deshalb kommt C vor die Änderungsrate der Temperatur: Weil der Ozean so viel Wärme speichert, ist C groß, und die Temperatur ändert sich nur langsam.</p>\n"
    "    <p>Klick: Die Rückkopplung. Eine kühlere Erde strahlt weniger Wärme ab, Λ mal T. Λ heißt Klimarückkopplungsparameter: Je Kelvin Temperaturänderung strahlt die Erde rund 1,2 W/m² mehr oder weniger ab, so in unserem FaIR-Lauf — rechts wird die Wärmeabstrahlung schwächer. Das bremst die Abkühlung. T sinkt deshalb nicht immer weiter, sondern nähert sich φ durch Λ, wo sich beides aufhebt.</p>\n"
    "    <p>Klick: Die Gleichung gelöst — ΔT, die Temperaturänderung durch den Baum. Links jetzt der Rahmen der Ergebnisgrafik, erst für ein einzelnes Jahr in Aachen: Eins, der Antrieb des Baums nur in diesem Jahr. Zwei, die Erde wird sofort kühler. Drei, danach klingt das ab — schnell die Oberfläche, ein kleiner Rest hält lange, weil der tiefe Ozean nachzieht.</p>\n"
    "    <p>Klick: Dasselbe für jedes fünfte Jahr. Der Baum wächst, sein Antrieb wird größer, also auch die Beiträge.</p>\n"
    "    <p>Klick: Die Summe über alle Jahre — das ist die Temperaturwirkung des Baums in Aachen. Die einzelnen Beiträge sind klein, aber ihre langen Reste addieren sich über die Jahrzehnte. Dasselbe Prinzip wie eben beim CO₂: dort die Impulsantwort des Kohlenstoffkreislaufs, hier die der Temperatur. Die Kurven hier sind mit der Temperaturantwort von FaIR gerechnet, die Summe ist genau das FaIR-Ergebnis.</p>\n"
    "    <p>Klick: Dasselbe an den drei Orten. In Joensuu kühlt der Baum zuerst stärker; ab etwa 2060 wird die Kühlung schwächer. Der Grund ist der Antrieb: Ab etwa 2050 wächst der Baum langsamer, sein CO₂-Antrieb nimmt nur noch wenig zu (2055 bis 2100 von −52 auf −66), die Albedo aber wärmt mit dem Kronenschluss über dem Schnee weiter zu (von +20 auf +51, je 10⁻¹⁵ W/m²). Der Netto-Antrieb wird schwächer, die Temperatur folgt verzögert. In Aachen halten sich beide Zuwächse etwa die Waage, bei Marabá ist die Albedo klein — dort bleibt die Kühlung.</p>\n"
    "    <p>Klick: Das Problem — C und Λ sind in Wirklichkeit nicht konstant, und die CO₂-Senken hängen selbst von der Temperatur ab. Deshalb rechnen wir mit einem Klimamodell.</p>\n")


def _rep(s, old, new):
    assert s.count(old) == 1, old[:90]
    return s.replace(old, new)


def _sec(page, title):
    m = re.search(r'<section class="slide[^"]*" data-ch="klima" data-title="' + re.escape(title) + r'">.*?</section>', page, flags=re.S)
    assert m, title
    return m


def _slide19(page):
    m = _sec(page, S19)
    sec = m.group(0)
    # room for the box: point 3 on one line, a little less space between the points
    sec = _rep(sec, 'Wie schnell? → 60 % nach 20, 41 % nach 100 Jahren', 'Tempo: 60 % nach 20, 41 % nach 100 Jahren')
    sec = _rep(sec, '<div style="display:flex; flex-direction:column; gap:14px; align-self:start">',
               '<div style="display:flex; flex-direction:column; gap:10px; align-self:start">')
    sec = _rep(sec, '[kg]</p></div></div></div>\n  </div>',
               '[kg]</p></div><p class="takeaway" data-step="5" style="--d:0; font-size:21px; margin:2px 0 0">'
               'Den Antrieb φ kennen wir jetzt. Wie wird daraus eine Temperatur?</p></div></div>\n  </div>')
    sec = _rep(sec, '<p class="q">Ausführlich: Nach einer Zusatzemission',
               '<p>Klick: Damit haben wir beide Teile des Antriebs, Albedo und CO₂. Bleibt die Frage, wie aus dem Antrieb eine Temperatur wird — nächste Folie.</p>\n    '
               '<p class="q">Ausführlich: Nach einer Zusatzemission')
    return page[: m.start()] + sec + page[m.end():]


def _slide20(page):
    m = _sec(page, S20)
    sec = m.group(0)
    sec, k = re.subn(r'<div class="road" style="height:52px; margin-bottom:12px">.*?</span></div>', lambda _: ROAD, sec, count=1, flags=re.S)
    assert k == 1
    r = re.search(r'<div style="display:flex; flex-direction:column; gap:8px; align-self:start; min-width:0">.*?\n    </div>', sec, flags=re.S)
    assert r
    sec = sec[: r.start()] + RIGHT + sec[r.end():]
    # the solution in the frame of the tree result: one year (4), every fifth year (5), their sum (6); the
    # three sites take over the same frame on click 7
    sec = _rep(sec, '<div class="chart" data-step="4" data-chart="k12t"',
               '<div class="chart" data-step="4" data-slot-steps="0,1,2" data-chart="k12p" data-label="Ein Baum in Aachen: '
               'Temperaturantwort auf den Antrieb eines Jahres, dann jedes fünften Jahres, dann die Summe aller Jahre"></div>'
               '<div class="chart" data-step="7" data-chart="k12t"')
    sec = _rep(sec, '<p class="takeaway" data-step="5"', '<p class="takeaway" data-step="8"')
    sec = _rep(sec, 'fill="#8a6a1e">Λ·ΔT: kühler →</text>', 'fill="#8a6a1e">Λ·T: kühler →</text>')
    n = re.search(r'(<aside class="notes" data-n="\d+">\n?)(.*?)(    <p class="q">Ausführlich)', sec, flags=re.S)
    assert n
    sec = sec[: n.start(2)] + NOTES20 + sec[n.start(3):]
    return page[: m.start()] + sec + page[m.end():]


def patch(page: str) -> str:
    head, sep, tail = page.partition("</style>")
    page = head + CSS + sep + tail
    page = _slide19(page)
    page = _slide20(page)
    return page
