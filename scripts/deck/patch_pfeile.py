"""Shorter texts with arrows (2026-10-07): like slide 18, wherever running text can become "A -> B".
Applied last."""
import re

NB = " "


def _sec(page, title):
    m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(title) + r'"[^>]*>.*?</section>', page, flags=re.S)
    assert m, title
    return m


def _edit(page, title, pairs, svg=False):
    m = _sec(page, title)
    sec = m.group(0)
    for a, b in pairs:
        a, b = a.replace("~", NB), b.replace("~", NB)
        if svg:
            a, b = ">" + a + "</text>", ">" + b + "</text>"
        pat = re.compile(re.escape(a.replace(NB, " ")).replace("\\ ", " ").replace(" ", "[ \u00a0]"))
        sec, k = pat.subn(lambda m: b, sec, count=1)
        assert k == 1, (title, a[:70])
    return page[: m.start()] + sec + page[m.end():]


def patch(page: str) -> str:
    page = _edit(page, "Strahlungsantrieb: Energiebilanz am Oberrand", [
        ("Strahlungsantrieb: Änderung der Energiebilanz am Oberrand in W je m² Erde; positiv wärmt, negativ kühlt.",
         "Strahlungsantrieb φ: Änderung der Energiebilanz am Oberrand [W je m² Erde]<br>→ φ &gt; 0 wärmt, φ &lt; 0 kühlt"),
    ])
    page = _edit(page, "Impulsantwort des Kohlenstoffkreislaufs", [
        ("<b>2</b>Natürliche Kreisläufe (runde Pfeile) tauschen ständig CO₂ aus. Kommt eine Tonne dazu, nehmen Land und Ozean über die Jahre einen Teil davon auf.",
         "<b>2</b>Natürliche Kreisläufe (runde Pfeile)<br>→ Land und Ozean nehmen einen Teil auf"),
        ("<b>3</b>Wie schnell? Nach 20 Jahren sind noch 60 % in der Atmosphäre, nach 100 Jahren 41 %.",
         "<b>3</b>Wie schnell? → 60 % nach 20, 41 % nach 100 Jahren"),
        ("<b>4</b>Entnahme genauso, spiegelbildlich: Ozean und Land geben CO₂ ab.",
         "<b>4</b>Entnahme: genauso, spiegelbildlich"),
    ])
    page = _edit(page, "Auf dem Holzweg? Nein.", [
        ("<p>Netto 57 bis 63 Gt CO₂ bis 2100, 19 bis 22 % der Entnahme, mit der die Szenarien rechnen — und das nur, wenn ausschließlich dort gepflanzt wird, wo der Baum kühlt.</p>",
         "<p>Netto 57 bis 63 Gt CO₂ bis 2100<br>→ 19 bis 22 % der Entnahme, mit der die Szenarien rechnen<br>→ nur bei Pflanzung ausschließlich auf kühlenden Flächen</p>"),
        ("<p>Mit dem Strom von 2026 bleiben im Median 46 % der Tonne. Zuerst dort, wo der Strom emissionsarm ist; nicht mit fossilem Strom und nicht im hohen Norden.</p>",
         "<p>Strom von 2026: im Median 46 % der Tonne netto<br>→ zuerst bei emissionsarmem Strom<br>→ nicht mit fossilem Strom, nicht im hohen Norden</p>"),
        ("<p>Fünf Jahre später gepflanzt, fehlt um 2050 knapp ein Viertel der Kühlung; zusätzlich hat Wald lokale Wirkungen wie Beschattung und Lebensraum. DAC wirkt ab Inbetriebnahme; sein Netto-Anteil steigt mit emissionsärmerem Strom.</p>",
         "<p>Baum: 5 Jahre später gepflanzt → 2050 fehlt knapp ein Viertel der Kühlung<br>→ dazu lokale Wirkungen: Schatten, Lebensraum<br>"
         "DAC: wirkt ab Inbetriebnahme<br>→ Netto-Anteil steigt mit emissionsärmerem Strom</p>"),
    ])
    page = _edit(page, "Methodischer Beitrag", [
        ("Wachstum, Albedo, Rückgabe durch Ozean und Land, steigende CO₂-Konzentration, Störung",
         "Wachstum, Albedo, Ozean und Land, steigende CO₂-Konzentration, Störung"),
        ("Netto-Anteil je Ort (Aachen (DE) 63 %, Joensuu (FI) 28 %); auf der Hälfte der Fläche wärmt der Baum",
         "Netto-Anteil je Ort: Aachen 63 %, Joensuu 28 %<br>→ auf der Hälfte der Fläche wärmt der Baum"),
        ("FaIR (Leach et al. 2021; Smith et al. 2024): Entnahme als negative Emission, Albedo als Antrieb, im Szenario SSP2-4,5; bewertet 2100",
         "FaIR: Entnahme als negative Emission, Albedo als Antrieb<br>→ Szenario SSP2-4,5, bewertet 2100"),
        ("Entnahme je Jahr, netto nach den eigenen Emissionen (diese mit GWP100)",
         "Entnahme je Jahr<br>→ netto nach eigenen Emissionen (GWP100)"),
        ("Zeitverlauf: bis 2061 kühlt „überall pflanzen“ stärker, danach schwächer; Eine Verzögerung wirkt vor allem um 2050. Statische Bilanzen und GWP100 liefern eine Zahl",
         "Zeitverlauf statt einer Zahl<br>→ bis 2061 kühlt „überall pflanzen“ stärker, danach schwächer<br>→ Verzögerung wirkt vor allem um 2050"),
    ])
    page = _edit(page, "Priorisierung von Aufforstung und DAC", [
        ("Tropen, wenig Schnee: netto bleiben bei Marabá (BR)", "Tropen, wenig Schnee → netto: Marabá (BR) 82~%,"),
        ("82~%, in Aachen (DE) 63~%, in Joensuu (FI) 28~%.", "Aachen (DE) 63~%, Joensuu (FI) 28~%"),
        ("Früh: 5 Jahre Verzögerung kosten 2050 knapp ein Viertel.", "Früh: 5 Jahre später → 2050 knapp ¼ weniger Kühlung"),
        ("Schneereicher Norden und Trockengebiete: Dort", "Schneereicher Norden, Trockengebiete"),
        ("wärmt der Baum bis 2100. Auf allen Flächen", "→ der Baum wärmt bis 2100"),
        ("sinkt die Wirkung von 59 auf 22~Gt CO₂.", "→ auf allen Flächen nur 22 statt 59~Gt CO₂"),
        ("Heute z. B. Joensuu (FI): 86~% der Tonne netto.", "Heute z. B. Joensuu (FI): 86~% netto"),
        ("Mit der Energiewende fast überall: 2040 bleiben", "→ mit der Energiewende fast überall:"),
        ("im Median 91~% der Tonne.", "2040 im Median 91~% netto"),
        ("Mit dem Strom von 2026: Krakau (PL) 17~%,", "Strom von 2026: Krakau (PL) 17~%,"),
        ("Im Norden ist es für Sorbens-DAC zu kalt.", "→ im Norden zu kalt für Sorbens-DAC"),
    ], svg=True)
    page = _edit(page, "Das Erdsystem rechnen: FaIR", [
        ("geht als negative Emission", "→ als negative Emission"),
        ("zu allen anderen Emissionen", "zu allen übrigen Emissionen"),
        ("geht getrennt als zusätzlicher", "→ getrennt als zusätzlicher"),
        ("Strahlungsantrieb ein", "Strahlungsantrieb"),
    ], svg=True)
    page = _edit(page, "Sorbens-DAC: Prozess und Energiebedarf", [
        ("Gebläse fördern Luft durch", "Gebläse: Luft durch"),
        ("ein Sorbens (Amin). Das CO₂", "ein Sorbens (Amin)"),
        ("bleibt daran haften.", "→ CO₂ bindet daran"),
        ("Unter Vakuum und mit", "Vakuum, Dampf (100 °C)"),
        ("Dampf (100 °C) desorbiert", "→ CO₂ löst sich ab"),
        ("das CO₂ wieder ab.", ""),
        ("und in tiefen Gesteins-", "→ Einlagerung in tiefe"),
        ("schichten einlagern.", "Gesteinsschichten"),
        ("Je nach Klima 1,1 bis 1,9 MWh:", "Je nach Klima 1,1 bis 1,9 MWh"),
        ("Niedrige Temperatur senkt den COP,", "→ kalt: COP sinkt"),
        ("hohe Feuchte erhöht den Wärmebedarf.", "→ feucht: mehr Wärmebedarf"),
    ], svg=True)
    # slide 19: coloured step numbers, as on slide 18
    m = _sec(page, "Impulsantwort des Kohlenstoffkreislaufs")
    sec = m.group(0)
    for k, c in (("1", "#8c6d5a"), ("2", "#2e7d4f"), ("3", "#1f7a8c"), ("4", "#5e8f3a")):
        assert sec.count(f'<p class="ghs"><b>{k}</b>') == 1, k
        sec = sec.replace(f'<p class="ghs"><b>{k}</b>', f'<p class="ghs"><b style="background:{c}">{k}</b>')
    page = page[: m.start()] + sec + page[m.end():]
    old = '<p class="who rise" style="--d:500"><b>Timo Diepers</b><br>Lehrstuhl für Technische Thermodynamik · RWTH Aachen (DE)</p>'
    assert page.count(old) == 1
    page = page.replace(old, '<p class="who rise" style="--d:500"><b>Timo Diepers</b> · Promotionsvortrag<br>Lehrstuhl für Technische Thermodynamik · RWTH Aachen University</p>')
    page = page.replace("Lehrstuhl für Technische Thermodynamik · RWTH Aachen (DE)<br>", "Lehrstuhl für Technische Thermodynamik · RWTH Aachen University<br>", 1)
    return _highlights(_round_bars(_ec_timing(page)))


HL_CSS = """
/* one highlight for formula terms everywhere (as on slide 17): a coloured, rounded frame with an even tint.
   A layer behind the term's own box (accents like the dot over Q do not bend it); it takes no space,
   so switching it on never moves the layout. */
.hl { display: inline-block; position: relative; isolation: isolate; }
.hl::before { content: ""; position: absolute; inset: -6px -9px; border-radius: 10px; border: 2.5px solid transparent;
  z-index: -1; transition: border-color .4s, background-color .4s; }
.hl.on.hl-t::before { border-color: #b2182b; background: rgba(178, 24, 43, .07); }
.slide:has(.locstep.shown) .hl-q::before { border-color: #6b4a2b; background: rgba(107, 74, 43, .08); }
.slide:has(.locstep.shown) .hl-m::before { border-color: #1b7837; background: rgba(27, 120, 55, .07); }
"""


def _highlights(page: str) -> str:
    old = "trust: ctx => ctx.command === '\\\\htmlData'"
    assert page.count(old) == 1, "trust"
    page = page.replace(old, "trust: ctx => ctx.command === '\\\\htmlData' || ctx.command === '\\\\htmlClass'")
    old = r"\boxed{\tq{\Delta T}(t)}"
    assert page.count(old) == 1, "dT"
    page = page.replace(old, r"\htmlClass{hl on hl-t}{\tq{\Delta T}(t)}")
    head, sep, tail = page.partition("</style>")
    return head + HL_CSS + sep + tail


def _round_bars(page: str) -> str:
    """All bar charts: square at the axis, rounded at the far end. Stacked segments keep square ends where
    they touch the next segment."""
    old = "        const kids = [{ type: 'rect', shape, style, enterFrom: from }];"
    assert page.count(old) == 1
    new = ('''        // rounded at the far end (the end away from zero), unless another segment is stacked onto it
        const v = b.o === 'v', lo = v ? b.r[1] : b.r[0], hi = v ? b.r[3] : b.r[2];
        const outer = Math.abs(hi) >= Math.abs(lo) ? hi : lo, inner = outer === hi ? lo : hi;
        const pos = (v ? b.r[0] : b.r[1]).toFixed(4), stacked = bars.some(o => o !== b && (o.o === 'v' ? o.r[0] : o.r[1]).toFixed(4) === pos
          && [o.o === 'v' ? o.r[1] : o.r[0], o.o === 'v' ? o.r[3] : o.r[2]].some(e => Math.abs(e - outer) < 1e-9 * (1 + Math.abs(outer))));
        if (!stacked && outer !== inner) {
          const thick = v ? shape.width : shape.height, len = v ? shape.height : shape.width, R = Math.min(thick / 2, len, 10);
          const po = api.coord(v ? [b.r[0], outer] : [outer, b.r[1]]), pi = api.coord(v ? [b.r[0], inner] : [inner, b.r[1]]);
          shape.r = v ? (po[1] < pi[1] ? [R, R, 0, 0] : [0, 0, R, R]) : (po[0] > pi[0] ? [0, R, R, 0] : [R, 0, 0, R]);
        }
''' + old)
    page = page.replace(old, new)
    old = "data: order.map(key => ({ value: D.cum.find(c => c.k === key).total, itemStyle: { color: col(key) } })),"
    assert page.count(old) == 1
    page = page.replace(old, "data: order.map(key => ({ value: D.cum.find(c => c.k === key).total, itemStyle: { color: col(key), borderRadius: [0, 10, 10, 0] } })),")
    # filled areas (fill_between, e.g. slide 20): fade in together with the lines instead of standing there
    old = "const el = [{ type: 'polygon', shape: { points: pts }, style: { fill: it.fc || 'none', opacity: (it.fa ?? 1) * (it.a ?? 1), stroke: it.ec || 'none', lineWidth: (it.ew || 0) * s } }];"
    assert page.count(old) == 1
    page = page.replace(old, old[:-3] + ", enterFrom: { style: { opacity: 0 } } }];")
    old = "            animationDuration: 900, animationDelay: base + 400\n          });\n        } else if (it.t === 'polyline') {"
    assert page.count(old) == 1, "poly timing"
    page = page.replace(old, "            animationDuration: 1500, animationEasing: 'cubicInOut', animationDelay: base + 200\n          });\n        } else if (it.t === 'polyline') {")
    # outlined bars (stacked segments start away from zero): the collapsed outline must not show before the bar grows
    old = "const from = b.o === 'v' ? { shape: { y: ya, height: 0 } } : { shape: { x: xa, width: 0 } };"
    assert page.count(old) == 1
    page = page.replace(old, "const from = b.o === 'v' ? { shape: { y: ya, height: 0 }, style: { opacity: 0 } } : { shape: { x: xa, width: 0 }, style: { opacity: 0 } };")
    # hatching (e.g. decomposition on slide 10) fades in with its bar instead of standing there from the start
    old = "const line = (ax, ay, bx, by) => kids.push({ type: 'line', shape: { x1: ax, y1: ay, x2: bx, y2: by }, style: { stroke: color, lineWidth: lw } });"
    assert page.count(old) == 1
    page = page.replace(old, "const line = (ax, ay, bx, by) => kids.push({ type: 'line', shape: { x1: ax, y1: ay, x2: bx, y2: by }, style: { stroke: color, lineWidth: lw }, enterFrom: { style: { opacity: 0 } } });")
    return page


def _ec_timing(page: str) -> str:
    """Slide 2: observation and scenarios as one sweep. ECharts animates a line by widening a clip over the
    whole grid, so equal duration, no delay and linear easing make the scenarios continue the observed line
    seamlessly. Slide 3: its lines start at once again (the shared replacement had delayed them too)."""
    T = 4200
    a, b = page.index("const EC_TEMPERATURE"), page.index("const EC_REMOVAL")
    t = page[a:b]
    for old, new in [
        ("z: 5, animationDuration: 1600,", f"z: 5, animationDuration: {T}, animationEasing: 'linear',"),
        ("animationDuration: 1800, animationEasing: 'cubicInOut', animationDelay: 1500 + i * 110 });", f"animationDuration: {T}, animationEasing: 'linear', animationDelay: 0 }});"),
        ("animationDelay: j => 3300 + j * 60,", f"animationDelay: j => {T} + j * 60,"),
    ]:
        assert t.count(old) == 1, old
        t = t.replace(old, new)
    # areas under the curves: desaturated, strongest right under the line, fading towards the x axis
    for old, new in [
    ]:
        assert t.count(old) == 1, old
        t = t.replace(old, new)
    t = ('''/* area under a curve: the colour half way to grey, a vertical fade from the line down */
function ecArea(hex, a) {
  const c = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)), g = (c[0] + c[1] + c[2]) / 3;
  const m = c.map(v => Math.round(v * .5 + g * .5)).join(',');
  return { origin: 'start', color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: `rgba(${m},${a})` }, { offset: .4, color: `rgba(${m},${a * .25})` }, { offset: 1, color: `rgba(${m},0)` }]) };
}
''' + t)
    c = page.index("const EC_CHARTS")
    r = page[b:c]
    old = "animationDelay: 1500 + i * 110 });"
    assert r.count(old) == 1
    r = r.replace(old, "animationDelay: i * 110 });")
    old = "data: v, lineStyle: { color: m.color, width: 2.4 }, itemStyle: { color: m.color },"
    assert r.count(old) == 1
    r = r.replace(old, "data: v, lineStyle: { color: m.color, width: 2.4 }, itemStyle: { color: m.color }, z: 3,")
    # area under each curve in its own colour, fading downwards at every year: 24 stacked bands,
    # each 1/24 of the curve's height, opaque at the top band and clear at the bottom
    old = "    // bars in the order in which the curves on the left end"
    assert r.count(old) == 1
    r = r.replace(old, '''    M.forEach((m, i) => {
      const r = D.rem[m.k]; let acc = 0, N = 24;
      const v = r.y.map((y, j) => [y, r.novel[j] + r.land[j]]).filter(p => p[0] >= 2024 && p[0] <= 2100).map(p => [p[0], (acc += p[1])]);
      const c = [1, 3, 5].map(j => parseInt(m.color.slice(j, j + 2), 16)).join(',');
      for (let b = 0; b < N; b++)
        series.push({ id: `a${m.k}${b}`, type: 'line', stack: `area${m.k}`, xAxisIndex: 0, yAxisIndex: 0, showSymbol: false, silent: true,
                      tooltip: { show: false }, z: 2, lineStyle: { width: 0 }, data: v.map(p => [p[0], p[1] / N]),
                      areaStyle: { color: `rgba(${c},${(.55 * ((b + 1) / N) ** 1.7).toFixed(3)})` },
                      animationDuration: 1800, animationEasing: 'cubicInOut', animationDelay: i * 110 });
    });
''' + old)
    return page[:a] + t + r + page[c:]
