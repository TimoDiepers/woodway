"""Changes from the artifact comments of 2026-10-07 (applied last)."""

R = [
    # slide 3: both charts at once; bars in the order in which the curves end on the left (top = highest)
    ("""const EC_REMOVAL = {
  steps: 1,   // 0 per year · 1 cumulative bars""",
     """const EC_REMOVAL = {
  steps: 0,   // per year and cumulative bars together"""),
    ("""    const order = D.cum.map(c => c.k).reverse();   // largest at the top
    if (k >= 1) {""",
     """    // bars in the order in which the curves on the left end (category axis runs bottom-up: highest last)
    const endOf = key => { const r = D.rem[key]; const j = r.y.length - 1; return r.novel[j] + r.land[j]; };
    const order = M.map(m => m.k).sort((a, b) => endOf(a) - endOf(b));
    {"""),
    ("""ecAxis({ type: 'value', gridIndex: 1, show: k >= 1, min: 0, max: 1000, interval: 250,""", """ecAxis({ type: 'value', gridIndex: 1, min: 0, max: 400, interval: 100,"""),
    ("""ecAxis({ type: 'category', gridIndex: 1, data: order.map(lab), show: k >= 1,""", """ecAxis({ type: 'category', gridIndex: 1, data: order.map(lab),"""),
    # slide 3: the left chart cumulative since 2024 up to 2100, like the bars (Very Low ends on top)
    ("""const r = D.rem[m.k], v = r.y.map((y, j) => [y, +(r.novel[j] + r.land[j]).toFixed(2)]).filter(p => p[0] >= 2025);""",
     """const r = D.rem[m.k]; let acc = 0;
      const v = r.y.map((y, j) => [y, r.novel[j] + r.land[j]]).filter(p => p[0] >= 2024 && p[0] <= 2100).map(p => [p[0], +(acc += p[1]).toFixed(1)]);"""),
    ("""data: [{ xAxis: 2100 }] },
                    animationDuration: 1800""", """data: [] },
                    animationDuration: 1800"""),
    ("""    const endOf = key => { const r = D.rem[key]; const j = r.y.length - 1; return r.novel[j] + r.land[j]; };""",
     """    const endOf = key => D.cum.find(c => c.k === key).total;"""),
    ("""title('CO₂-Entnahme je Jahr', 70)""", """title('CO₂-Entnahme, kumuliert seit 2024', 70)"""),
    ("""ecAxis({ type: 'value', gridIndex: 0, min: 2025, max: 2150, interval: 25,""", """ecAxis({ type: 'value', gridIndex: 0, min: 2025, max: 2100, interval: 25,"""),
    ("""name: 'Gt CO₂ je Jahr', nameLocation: 'middle', nameGap: 44""", """name: 'Gt CO₂, kumuliert', nameLocation: 'middle', nameGap: 48"""),
    ("""<b>${ecNum(p.value[1], 1)} Gt CO₂/a</b>""", """<b>${ecNum(p.value[1], 0)} Gt CO₂ seit 2024</b>"""),
    ("Links pro Jahr: im Very-Low-Szenario rund 5 bis 6 Gigatonnen jährlich, in Low-to-Negative bis zu 30. Rechts aufsummiert bis 2100",
     "Links aufsummiert seit 2024: Very Low entnimmt bis 2100 rund 335 Gigatonnen, Medium-Low 279; rechts dieselben Summen als Balken. Bis 2100"),
    ("Linien mit Fortschreibung bis 2150, Summen 2024–2100.", "Linien und Balken kumuliert 2024–2100."),
    # four scenarios instead of seven on every slide (High, Medium, Medium-Low, Very Low)
    ('<script src="v2/cmip7.js"></script>',
     '<script src="v2/cmip7.js"></script>\n<script>/* the deck draws four of the seven CMIP7 markers */\n'
     '(function () { const keep = ["H", "M", "ML", "VL"], D = window.CMIP7; if (!D) return;\n'
     '  D.markers = D.markers.filter(m => keep.includes(m.k)); D.cum = D.cum.filter(c => keep.includes(c.k)); })();</script>'),
    ("mit den Emissionen der sieben CMIP7-Markerszenarien", "mit den Emissionen der CMIP7-Markerszenarien (gezeigt: vier von sieben)"),
    ("rechnen — sieben Wege, von Very Low bis High.", "rechnen. Wir zeigen vier der sieben Wege: Very Low, Medium-Low, Medium und High."),
    ("Werte (Median): VL 2100 1,60 °C, LN 1,70, L 1,86, ML 2,27, M 2,98, H 3,45, HL 2,87 °C.",
     "Werte (Median) 2100: VL 1,60 °C, ML 2,27, M 2,98, H 3,45 °C; nicht gezeigt LN 1,70, L 1,86, HL 2,87 °C."),
    ("Szenarien nahe 1,5 °C setzen große CO₂-Entnahme voraus: Very Low mit rund 335 Gt bis 2100, Low und Low-to-Negative mit 573 und 820 Gt.",
     "Je niedriger die Erwärmung, desto mehr CO₂-Entnahme setzen die Szenarien voraus: Very Low rund 335 Gt bis 2100, Medium-Low (2,3\u00a0°C) 279 Gt."),
    ("Kumuliert 2024–2100 (neuartig + Land): VL 109 + 226, L 244 + 329, ML 104 + 175, LN 786 + 34, HL 104 + 129 Gt CO₂.",
     "Kumuliert 2024–2100 (neuartig + Land): VL 109 + 226, ML 104 + 175 Gt CO₂, Medium und High praktisch null; nicht gezeigt L 244 + 329, LN 786 + 34, HL 104 + 129 Gt CO₂."),
    ("Bäume netto 57 bis 63 Gt, 8 % (Low-to-Negative) bis 26 % (High-to-Low) des Bedarfs bis 2100",
     "Bäume netto 57 bis 63 Gt; in Medium-Low 22 % des Bedarfs bis 2100, Medium und High setzen keine Entnahme voraus"),
    ("Bäume: Netto-Anteil 2100 der kühlenden Flächen in den sieben CMIP7-Welten.", "Bäume: Netto-Anteil 2100 der kühlenden Flächen in den vier gezeigten CMIP7-Szenarien."),
    ("in allen sieben Welten von eben.", "in den vier Szenarien vom Anfang."),
    ("Netto 57 bis 63 Gt CO₂ bis 2100, je nach Szenario 8 bis 26 % der Entnahme, mit der es rechnet",
     "Netto 57 bis 63 Gt CO₂ bis 2100, 19 bis 22 % der Entnahme, mit der die Szenarien rechnen"),
    # slide 2: the scenarios continue the observed line right away, no click of their own
    ("""  steps: 2,   // 0 observation · 1 scenarios · 2 focus on Very Low""",
     """  steps: 1,   // 0 observation, then the scenarios as its continuation · 1 focus on Very Low"""),
    ("""    if (k >= 1) M.forEach((m, i) => {
      const t = D.temp[m.k], dim = k >= 2 && m.k !== 'VL' ? .22 : 1;
      const style = { color: m.color, width: m.k === 'VL' && k >= 2 ? 3.4 : 2.4, opacity: dim };""",
     """    M.forEach((m, i) => {
      const t = D.temp[m.k], dim = k >= 1 && m.k !== 'VL' ? .22 : 1;
      const style = { color: m.color, width: m.k === 'VL' && k >= 1 ? 3.4 : 2.4, opacity: dim };"""),
    ("""animationDuration: 1800, animationEasing: 'cubicInOut', animationDelay: i * 110 });""",
     """animationDuration: 1800, animationEasing: 'cubicInOut', animationDelay: 1500 + i * 110 });"""),
    ("""    if (k >= 1) {
      const at = M.map(""", """    {
      const at = M.map("""),
    ("""animationDuration: 400, animationDelay: j => 1700 + j * 60,""", """animationDuration: 400, animationDelay: j => 3300 + j * 60,"""),
    ("""opacity: k >= 2 && e.k !== 'VL' ? .25 : 1 },""", """opacity: k >= 1 && e.k !== 'VL' ? .25 : 1 },"""),
    ("""color: e.color, opacity: k >= 2 && e.k !== 'VL' ? .3 : 1,""", """color: e.color, opacity: k >= 1 && e.k !== 'VL' ? .3 : 1,"""),
    ("""    if (k >= 2) {
      const f = D.facts.VL;""", """    if (k >= 1) {
      const f = D.facts.VL;"""),
]


def _in_slide(page: str, title: str, old: str, new: str) -> str:
    """Replace *old* once inside the section with data-title *title*."""
    import re

    m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(title) + r'"[^>]*>.*?</section>', page, flags=re.S)
    assert m and old in m.group(0), (title, old[:60])
    sec = m.group(0).replace(old, new, 1)
    return page[: m.start()] + sec + page[m.end():]


def patch(page: str) -> str:
    import re

    for old, new in R:
        pat = re.compile(re.escape(old).replace("\\ ", "[ \u00a0]"))
        page, k = pat.subn(lambda m: new, page)
        assert k >= 1, old[:70]
    page = _in_slide(page, "CMIP7: Erwärmung", '<p class="takeaway" data-step="2"', '<p class="takeaway" data-step="1"')
    # slide 4: bullets before the three lines on each side; no source line (comments 2026-10-07)
    title4 = "Wozu technische CO₂-Entnahme?"
    for y, txt in ((252, "seit Jahrmillionen"), (288, "durch Photosynthese"), (324, "wächst von selbst")):
        page = _in_slide(page, title4, f'<text x="440" y="{y}" font-size="23" fill="var(--ink)">{txt}</text>',
                         f'<circle cx="447" cy="{y - 8}" r="5" fill="var(--moss)"/><text x="464" y="{y}" font-size="23" fill="var(--ink)">{txt}</text>')
    for y, txt in ((252, "Direct Air Capture"), (288, "braucht Energie"), (324, "muss gebaut werden")):
        page = _in_slide(page, title4, f'<text x="1168" y="{y}" font-size="23" fill="var(--ink)">{txt}</text>',
                         f'<circle cx="1175" cy="{y - 8}" r="5" fill="var(--fjord)"/><text x="1192" y="{y}" font-size="23" fill="var(--ink)">{txt}</text>')
    page = _in_slide(page, title4, '<text x="796" y="398">Dampf, 100 °C</text>', '<text x="780" y="398">Dampf, 100 °C</text>')
    page = _in_slide(page, title4, '<p class="src">Schema. DAC = Direct Air Capture, hier das Sorbens-Verfahren der ersten großen Anlagen (Climeworks, Island).</p>', '')
    # slide 5: the Science box as text anchors instead of running text
    t5 = "Überschlagsrechnung"
    old_fazit = '<p style="font:400 23px/1.4 var(--serif); color:var(--ink)">Fazit: Aufforstung sei die wirksamste Klimaschutzmaßnahme. Darauf beriefen sich Kampagnen wie <i>Trillion Trees</i>.</p>'
    old_aber = '<p style="font:400 23px/1.4 var(--serif); color:var(--ink)">Die Arbeit wurde wissenschaftlich scharf kritisiert. Die Zahlen wurden rasch um rund 60&nbsp;% nach unten korrigiert, weil die Vereinfachung viele Fehler enthält.</p>'
    page = _in_slide(page, t5, old_fazit,
                     '<p style="font:400 24px/1.45 var(--serif); color:var(--ink)">Fazit: Aufforstung =<br>wirksamste Klimaschutzmaßnahme<br>→ Kampagne <i>Trillion Trees</i></p>')
    page = _in_slide(page, t5, old_aber,
                     '<p style="font:400 24px/1.45 var(--serif); color:var(--ink)">Scharfe wissenschaftliche Kritik<br>→ um rund 60&nbsp;% nach unten korrigiert<br>→ Rechnung zu stark vereinfacht</p>')
    m5 = re.search(r'(data-title="Überschlagsrechnung".*?<aside class="notes"[^>]*>\n?)', page, flags=re.S)
    assert m5
    page = page[: m5.end()] + ('    <p class="q">Kasten ausführlich: Bastin et al. (Science 2019) schlossen, Aufforstung sei die wirksamste Klimaschutzmaßnahme; '
                               'darauf beriefen sich Kampagnen wie Trillion Trees. Die Arbeit wurde wissenschaftlich scharf kritisiert, die Zahlen '
                               'rasch um rund 60 % nach unten korrigiert (205 → 81 GtC), weil die Vereinfachung viele Fehler enthält.</p>\n') + page[m5.end():]
    # chapter Bäume: carbon uptake and albedo are not yet known terms there
    for a, b in (('<p class="rise" style="--d:300">Kohlenstoffaufnahme und Albedo eines Baums</p>', '<p class="rise" style="--d:300">Was ein einzelner Baum bewirkt</p>'),
                 ('font-size="21">Kohlenstoffaufnahme und</text>', 'font-size="21">Was ein einzelner</text>'),
                 ('font-size="21">Albedo eines Baums</text>', 'font-size="21">Baum bewirkt</text>')):
        assert page.count(a) == 1, a
        page = page.replace(a, b)
    # slide 8: three lines from the crown to the shaded ground, in the direction of the light
    shade = '<path d="M352 466 L560 466" stroke="#7a7466" stroke-width="10" stroke-linecap="round" opacity=".45"/>'
    assert page.count(shade) == 1
    page = page.replace(shade, shade + '<g stroke="#7a7466" stroke-width="2.5" stroke-dasharray="7 6" stroke-linecap="round" opacity=".8">'
                        '<line x1="392" y1="352" x2="422" y2="419"/><line x1="424" y1="352" x2="454" y2="419"/><line x1="456" y1="352" x2="486" y2="419"/></g>')
    # slide 9: the tree stands exactly where it stood on slide 8 (same scale; shift the view by 10 px left, 40 px down)
    page = _in_slide(page, "Kohlenstoff-Aufnahme", 'data-export="s_kohlenstoff" viewBox="0 0 1424 470" style="flex:1; width:100%; min-height:0"',
                     'data-export="s_kohlenstoff" viewBox="10 -40 1424 470" style="flex:1; width:100%; min-height:0; overflow:visible"')
    page = _in_slide(page, "Kohlenstoff-Aufnahme",
                     '<rect x="40" y="440" width="600" height="30" fill="#d9cfb9"/><path d="M40 455 H640" stroke="#c3b79c" stroke-width="2"/><line x1="40" y1="440" x2="640" y2="440"',
                     '<rect x="70" y="440" width="560" height="30" fill="#d9cfb9"/><path d="M70 455 H630" stroke="#c3b79c" stroke-width="2"/><line x1="70" y1="440" x2="630" y2="440"')
    # slide 9: the fire sits on the crown (moved right only), the arrow starts at it again
    page = _in_slide(page, "Kohlenstoff-Aufnahme", '<path d="M190 196c-26 26', '<path d="M270 196c-26 26')
    page = _in_slide(page, "Kohlenstoff-Aufnahme", '<path d="M190 244c-10 10', '<path d="M270 244c-10 10')
    page = _in_slide(page, "Kohlenstoff-Aufnahme", '<path d="M160 214 C 140 190 124 168 112 146"', '<path d="M236 204 C 190 180 140 160 112 146"')
    # what was already on the previous slide does not animate again (comment on slide 9)
    page = _in_slide(page, "Kohlenstoff-Aufnahme", '<g class="grow" style="--d:0">', "<g>")
    page = _in_slide(page, "C-Aufnahme über die Zeit", '<div class="eq tex rise" style="text-align:center; font-size:32px">',
                     '<div class="eq tex" style="text-align:center; font-size:32px">')
    page = _in_slide(page, "C-Aufnahme im Modell", '<div class="eq tex rise" style="font-size:29px">',
                     '<div class="eq tex" style="font-size:29px">')
    # slide 10: full balance from the start; three equal panels, the takeaway in the free fourth place
    page = _in_slide(page, "C-Aufnahme über die Zeit",
                     r"$$\mB(t) = \mPS(t) - \mRE(t) \st{2}{{}- \mZS(t) - \mST(t)}$$",
                     r"$$\mB(t) = \mPS(t) - \mRE(t) - \mZS(t) - \mST(t)$$")
    page = _in_slide(page, "C-Aufnahme über die Zeit",
                     '<div class="chart" data-slot-steps="0,1,2" data-chart="s11" data-label="Netto-CO₂-Fluss eines Baums auf drei Zeitskalen: Tag, Jahr, Bestandesalter (illustrativ)"></div>',
                     '<div style="position:relative; flex:1; min-height:0; display:flex; flex-direction:column">'
                     '<div class="chart" data-slot-steps="0,1,2" data-chart="s11" data-label="Kohlenstoffflüsse eines Baums auf drei Zeitskalen: Tag, Jahr, Jahrzehnte (illustrativ)"></div>'
                     '<div style="position:absolute; right:1.5%; bottom:9%; width:45%">'
                     '<p class="takeaway" data-step="3" style="--d:0">Annahme: Für das Klima zählt nur der Jahresmittelwert.</p>'
                     '</div></div>')
    m = re.search(r'(data-title="C-Aufnahme über die Zeit".*?<aside class="notes" data-n="\d+">)(.*?)(</aside>)', page, flags=re.S)
    assert m
    page = page[: m.start(2)] + """
    <p>Oben die vollständige Bilanz eines Baums: Photosynthese nimmt Kohlenstoff auf, Respiration, Zersetzung und Störung geben ihn wieder ab. Diese vier Flüsse laufen auf ganz verschiedenen Zeitskalen.</p>
    <p>Über den Tag: Tagsüber überwiegt die Photosynthese, nachts bleibt nur die Respiration. Über das Jahr: Im Sommer nimmt der Baum kräftig auf, im Winter gibt er wenig ab; die Respiration läuft das ganze Jahr, dazu zersetzen sich Laub und Totholz. Über Jahrzehnte: Der Vorrat wächst, bis Zuwachs und Zersetzung sich ausgleichen, und eine Störung kann einen großen Teil auf einmal freisetzen.</p>
    <p>Für die Klimawirkung interessiert uns nicht der einzelne Tag, sondern was über Jahre und Jahrzehnte bleibt. Deshalb mitteln wir über Tag und Jahreszeit und modellieren die Jahreswerte. Wie, zeigt die nächste Folie.</p>
    <p class="q">Falls Fragen kommen — Alle drei Panels in kg C je Baum und aufeinander skaliert: Ein Sommertag ergibt rund 26 g C, ein Jahr netto gut 1 kg C, passend zum Zuwachs des Aachener Modellbaums (höchstens rund 1 kg C im Jahr). Verläufe illustrativ, keine Messdaten; das Modell hat keinen Jahresgang. Die Winterabgabe über Wäldern stammt vor allem aus der Zersetzung, der Baum selbst liegt im Winter nur knapp unter null. Flussbegriffe nach Chapin et al. (2006).</p>
  """ + page[m.end(2):]
    # the signpost line of the Klima chapter rises once, on its first slide
    head, sep, rest = page.partition('<div class="road rise" style="--d:200">')
    assert sep
    page = head + sep + rest.replace('<div class="road rise" style="--d:200">', '<div class="road">')
    return page
