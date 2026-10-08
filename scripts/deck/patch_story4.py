"""Comments of 2026-10-08, second round (applied after patch_story3):
- slide 5: label as before, "Die Kritik"
- slide 4 without DAC: the bars of slide 3 stay, the tree as "the natural solution?" on the left
- overview and chapter 3: name, icon (globe), divider art (globe with land, water, small trees)
- availability overlay: the limit (cooling needed for 1.5 deg C in Very Low) instead of the removal need
- the break "Sind wir auf dem Holzweg?": dark, centred, no DAC; from here on its own accent (data-ch dac)."""
import math
import re

BACKUP_MARK = "<!-- KAPITEL 1-2, aus dem Hauptteil genommen"

CSS = """
[data-ch="dac"] { --ch: #9a6516; --ch-soft: #e8cb92; }
/* the break: dark, centred, a path that ends in the forest */
.slide.chapter.brk { background: #14181a; }
.slide.chapter.brk .ctext { left: 0; right: 0; top: 250px; max-width: none; text-align: center; }
.slide.chapter.brk h1 { font-size: 112px; color: #f2ede2; }
.slide.chapter.brk h1 em { font-style: normal; color: #e0a83e; }
.slide.chapter.brk .eng { opacity: 0; transform: translateX(380px); transition: transform 1.4s var(--ease), opacity .6s; }
.slide.chapter.brk .eng.shown { opacity: 1; transform: none; }
.slide.chapter.brk .eng .bubble { opacity: 0; transform: scale(.85); transform-box: fill-box; transform-origin: 90% 100%; transition: opacity .4s 1.3s, transform .5s 1.3s var(--ease); }
.slide.chapter.brk .eng.shown .bubble { opacity: 1; transform: none; }
/* slide 4: the tree over the empty left half of the removal chart */
.natur { position: absolute; left: 0; top: 0; width: 57%; height: 100%; pointer-events: none; }
"""

ICON_GLOBE = ('<symbol id="i-vergleich" viewBox="0 0 24 24"><path d="M21.54 15H17a2 2 0 0 0-2 2v4.54"/>'
              '<path d="M7 3.34V5a3 3 0 0 0 3 3a2 2 0 0 1 2 2c0 1.1.9 2 2 2a2 2 0 0 0 2-2c0-1.1.9-2 2-2h3.17"/>'
              '<path d="M11 21.95V18a2 2 0 0 0-2-2a2 2 0 0 1-2-2v-1a2 2 0 0 0-2-2H2.05"/><circle cx="12" cy="12" r="10"/></symbol>'
              '<symbol id="i-dac" viewBox="0 0 24 24"><path d="M10.827 16.379a6.082 6.082 0 0 1-8.618-7.002l5.412 1.45a6.082 6.082 0 0 1 '
              '7.002-8.618l-1.45 5.412a6.082 6.082 0 0 1 8.618 7.002l-5.412-1.45a6.082 6.082 0 0 1-7.002 8.618l1.45-5.412Z"/><path d="M12 12v.01"/></symbol>')

EC_BARS = """
/* slide 4: only the bars of slide 3, at the same place and without a new entrance */
const EC_REMOVAL_BARS = {
  steps: 0,
  still: true,   // already on screen on the slide before
  option(k) {
    const o = EC_REMOVAL.option(k);
    o.series = o.series.filter(s => s.xAxisIndex === 1);
    o.xAxis[0].show = false; o.yAxis[0].show = false;
    o.title = [o.title[1]];
    o.animation = false;
    return o;
  }
};
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


def _globe(cx, cy, r):
    """Globe sitting in the corner: water, land masses, small trees; the surface turns slowly."""
    land = ("M-0.62 -0.55 C -0.42 -0.72 -0.12 -0.68 0.02 -0.52 C 0.16 -0.38 0.02 -0.2 -0.16 -0.18 C -0.34 -0.16 -0.4 0.02 -0.56 0.06 "
            "C -0.74 0.1 -0.86 -0.12 -0.82 -0.3 Z "
            "M0.22 -0.12 C 0.42 -0.26 0.7 -0.2 0.78 0.02 C 0.86 0.24 0.66 0.42 0.46 0.38 C 0.3 0.34 0.32 0.16 0.18 0.12 C 0.06 0.06 0.08 -0.04 0.22 -0.12 Z "
            "M-0.44 0.34 C -0.26 0.26 -0.08 0.34 -0.04 0.5 C 0 0.66 -0.2 0.78 -0.36 0.7 C -0.52 0.62 -0.6 0.42 -0.44 0.34 Z")
    def tr(x, y, s):
        return (f'<g class="m-sway"><rect x="{x - 2.5 * s:.1f}" y="{y - 8 * s:.1f}" width="{5 * s:.1f}" height="{12 * s:.1f}" fill="#3b3024"/>'
                f'<circle cx="{x:.1f}" cy="{y - 14 * s:.1f}" r="{9 * s:.1f}" fill="#7f9c64"/></g>')
    trees = "".join(tr(cx + r * px, cy + r * py, 2.4) for px, py in ((-0.5, -0.5), (-0.3, -0.42), (-0.62, -0.28), (0.4, -0.06), (0.6, 0.06),
                                                                     (0.32, 0.18), (-0.3, 0.46)))
    return (f'<defs><clipPath id="glb"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath></defs>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="color-mix(in srgb, var(--paper) 22%, var(--ch))"/>'
            f'<g clip-path="url(#glb)"><g class="glb-turn" style="transform-origin:{cx}px {cy}px">'
            f'<path transform="translate({cx} {cy}) scale({r})" d="{land}" fill="color-mix(in srgb, var(--paper) 30%, #5f7f48)"/>'
            + trees + '</g></g>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="color-mix(in srgb, var(--paper) 40%, var(--ch))" stroke-width="3"/>')


def _break_svg():
    """Dark forest in the deck's tree shape along the bottom; on the first click an engineer (amber) walks in
    and offers "the solution"."""
    def tree(x, base, s, c1, c2, c3):
        return (f'<g class="m-sway"><rect x="{x - 9 * s:.0f}" y="{base - 120 * s:.0f}" width="{18 * s:.0f}" height="{120 * s:.0f}" fill="#0f1412"/>'
                f'<circle cx="{x:.0f}" cy="{base - 150 * s:.0f}" r="{70 * s:.0f}" fill="{c1}"/>'
                f'<circle cx="{x - 44 * s:.0f}" cy="{base - 100 * s:.0f}" r="{48 * s:.0f}" fill="{c2}"/>'
                f'<circle cx="{x + 44 * s:.0f}" cy="{base - 98 * s:.0f}" r="{45 * s:.0f}" fill="{c3}"/></g>')
    back = "".join(tree(x, 830, 0.8 + 0.25 * ((i * 7) % 3), "#1d2823", "#18221d", "#212d27")
                   for i, x in enumerate(range(-40, 1700, 150)))
    front = "".join(tree(x, 880, 1.05 + 0.2 * ((i * 5) % 3), "#26342d", "#212e28", "#2b3a32")
                    for i, x in enumerate(range(30, 1700, 230)) if not 1120 < x < 1420)
    ground = '<path d="M0 900 V830 C 300 812 700 820 1000 826 C 1250 832 1450 822 1600 818 V900 Z" fill="#101513"/>'
    eng = ('<g class="eng" data-step="1"><g transform="translate(1290 848)">'
           # legs, body, arms, head, hard hat
           '<path d="M-14 0 L-8 -70 M14 0 L8 -70" stroke="#c48a22" stroke-width="13" stroke-linecap="round"/>'
           '<rect x="-30" y="-150" width="60" height="88" rx="22" fill="#e0a83e"/>'
           '<path d="M-26 -132 L-58 -96" stroke="#e0a83e" stroke-width="12" stroke-linecap="round"/>'
           '<path d="M26 -134 L58 -186" stroke="#e0a83e" stroke-width="12" stroke-linecap="round"/>'
           '<circle cx="62" cy="-192" r="9" fill="#f2c86a"/>'
           '<circle cx="0" cy="-178" r="24" fill="#f2c86a"/>'
           '<path d="M-29 -186 A29 27 0 0 1 29 -186 Z" fill="#c48a22"/><rect x="-36" y="-189" width="72" height="7" rx="3.5" fill="#c48a22"/>'
           '</g>'
           # the DAC box held up in the raised hand: housing, a turning fan, a little outlet
           '<g><rect x="1324" y="584" width="84" height="62" rx="9" fill="#e0a83e" stroke="#c48a22" stroke-width="3"/>'
           '<circle cx="1354" cy="615" r="20" fill="#14181a"/>'
           '<g class="m-fan"><path d="M1354 598 V632 M1337 615 H1371" stroke="#e0a83e" stroke-width="5" stroke-linecap="round"/></g>'
           '<path d="M1386 600 v30 M1396 600 v30" stroke="#c48a22" stroke-width="3" stroke-linecap="round"/></g>'
           '<g class="bubble">'
           '<path d="M932 510 h276 a22 22 0 0 1 22 22 v84 a22 22 0 0 1 -22 22 h-40 l72 26 l-112 -26 h-196 a22 22 0 0 1 -22 -22 v-84 a22 22 0 0 1 22 -22 Z" fill="#f2ede2"/>'
           '<text x="1070" y="560" text-anchor="middle" font-family="IBM Plex Sans" font-size="26" fill="#14181a">Ich hab die Lösung:</text>'
           '<text x="1070" y="600" text-anchor="middle" font-family="Literata" font-size="32" font-weight="600" fill="#9a6516">Direct Air Capture!</text>'
           '</g>'
           '</g></g>')
    return ('<svg class="deco mo" data-export="s_holzweg" viewBox="0 0 1600 900" aria-hidden="true">'
            + back + ground + front + eng + '</svg>')


def patch(page: str) -> str:
    head, sep, tail = page.partition("</style>")
    page = head + CSS + "" + sep + tail
    # icons: chapter 3 is a globe; the DAC part gets its own (shown only on its slides)
    page = re.sub(r'<symbol id="i-vergleich" viewBox="0 0 24 24">.*?</symbol>', ICON_GLOBE, page, count=1, flags=re.S)
    page = _rep(page, "const chapters = ['baeume', 'klima', 'vergleich'];", "const chapters0 = ['baeume', 'klima', 'vergleich'];")
    page = _rep(page, "path.innerHTML = chapters.map(", "const chapters = ch === 'dac' ? [...chapters0, 'dac'] : chapters0;\n        path.innerHTML = chapters.map(")
    page = _rep(page, "opt.animation = animate;", "opt.animation = animate && !this.spec.still;")
    page = _rep(page, "const EC_CHARTS = { temperatur: EC_TEMPERATURE, entnahme: EC_REMOVAL };",
                EC_BARS + "const EC_CHARTS = { temperatur: EC_TEMPERATURE, entnahme: EC_REMOVAL, entnahmebalken: EC_REMOVAL_BARS };")
    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)

    # ---- slide 5
    main = _rep(main, 'DER MYTHOS · <i>SCIENCE</i> (BASTIN ET AL. 2019)</p>', 'SO GERECHNET IN <i>SCIENCE</i> (BASTIN ET AL. 2019)</p>')
    main = _rep(main, '>DER CHECK</p>', '>DIE KRITIK</p>')

    # ---- slide 4: the tree next to the bars of slide 3
    m = _sec(main, "Wozu technische CO₂-Entnahme?")
    old4 = m.group(0)
    s3 = _sec(main, "CMIP7: CO₂-Entnahme").group(0)
    hdr = '<header class="sh"><h2>Bäume: die natürliche Lösung<br>für die CO₂-Entnahme?</h2></header>'
    tree = re.search(r'<!-- the tree: there already, by itself -->\s*<g class="pop" style="--d:100">(.*?)<text x="440" y="150"', old4, flags=re.S).group(1)
    k = iter(range(10))
    tree = re.sub(r'(<g class="m-sway">.*?</g>)', lambda mm: f'<g class="grow" style="--d:{150 + 350 * next(k)}">' + mm.group(1) + '</g>', tree, flags=re.S)
    natur = ('<svg class="natur mo" viewBox="0 0 900 560" aria-label="Der Baum: die natürliche Lösung?"><g font-family="IBM Plex Sans">'
             '<g transform="translate(0 50) scale(.92)">' + tree + '</g>'
             '<g class="rise" style="--d:900">'
             '<text x="430" y="200" font-family="Literata" font-size="46" font-weight="600" fill="var(--moss)">Der Baum</text>'
             '<text x="430" y="250" font-family="Literata" font-style="italic" font-size="32" fill="var(--clay)">Die natürliche Lösung?</text></g>'
             '<g class="rise" style="--d:1300" font-size="23" fill="var(--ink)">'
             '<circle cx="437" cy="300" r="5" fill="var(--moss)"/><text x="454" y="308">von der Natur über</text><text x="454" y="336">Jahrmillionen perfektioniert</text>'
             '<circle cx="437" cy="372" r="5" fill="var(--moss)"/><text x="454" y="380">CO₂-Aufnahme durch</text><text x="454" y="408">Photosynthese</text>'
             '<circle cx="437" cy="444" r="5" fill="var(--moss)"/><text x="454" y="452">wächst „von selbst“</text></g></g></svg>')
    new4 = ('<section class="slide" data-title="Die natürliche Lösung?">\n  ' + hdr + '\n  <div class="body">\n'
            '    <div style="position:relative; flex:1; min-height:0; display:flex; flex-direction:column">'
            '<div class="chart" data-ec="entnahmebalken" data-label="Summe der CO₂-Entnahme 2024–2100 in vier CMIP7-Szenarien"></div>' + natur + '</div>\n'
            '    <div class="foot"><div></div><p class="takeaway" style="visibility:hidden" aria-hidden="true">Weniger Erwärmung → mehr Entnahme: Very Low setzt 335 Gt CO₂ bis 2100 voraus.</p></div>\n  </div>\n'
            '  <p class="src">Entnahme: CMIP7-Markerszenarien (van Vuuren et al. 2026), Summe 2024–2100.</p>\n'
            '  <aside class="notes" data-n="0">\n'
            '    <p>Rechts noch einmal, was die Szenarien an Entnahme voraussetzen: bis zu 335 Gigatonnen CO₂. Und links das, woran die meisten '
            'zuerst denken: der Baum. Von der Natur über Jahrmillionen perfektioniert, er nimmt CO₂ durch Photosynthese auf und wächst von selbst. '
            'Die natürliche Lösung? Rechnen wir das einmal ganz einfach durch.</p>\n  </aside>\n</section>\n\n')
    main = main[: m.start()] + new4 + main[m.end():]
    backup = backup.replace(BACKUP_MARK, re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', old4) + BACKUP_MARK, 1)

    # ---- overview: name and icon of chapter 3
    main = _rep(main, '>Alle Bäume, alle Flächen:</text>', '>Globale Aufforstungs-</text>')
    main = _rep(main, '>globale Wirkung</text>', '>potenziale</text>')

    # ---- chapter 3 divider: a globe with land, water and small trees instead of trees and DAC
    m = _sec(main, "Potenzial")
    sec = m.group(0)
    deco = re.search(r'<svg class="deco[^"]*"[^>]*>.*?</svg>', sec, flags=re.S).group(0)
    pills = re.search(r'<g font-family="IBM Plex Sans">.*?</g>(?=<path d="M1010 900)', deco, flags=re.S).group(0)
    sun = re.search(r'<g class="t" style="--d:0"><g class="m-rays".*?</g><circle [^>]*/></g>', deco, flags=re.S)
    sun = sun.group(0) if sun else ""
    new_deco = (re.match(r'<svg[^>]*>', deco).group(0) + pills + sun + '<g class="t" style="--d:100">' + _globe(1430, 960, 430) + '</g></svg>')
    sec = sec.replace(deco, new_deco, 1)
    main = main[: m.start()] + sec + main[m.end():]

    # ---- availability overlay: the limit instead of the removal need
    m = _sec(main, "Wiederbewaldbare Fläche")
    sec = m.group(0)
    sec = _rep(sec, 'gegen die Kühlung, die die Entnahme des Szenarios Very Low bringen würde"',
               'gegen die Kühlung, die nötig wäre, um im Szenario Very Low unter 1,5 °C zu bleiben"')
    sec = _rep(sec, '>2100: Bäume 19 mK, Bedarf 114 mK → große Lücke.</p>', '>Grenzwert 1,5 °C: 2050 fehlen 323 mK, die Bäume bringen 14 mK.</p>')
    sec = _rep(sec, " Kühlung: FaIR je Fläche, SSP2-4,5; Bedarf: Entnahme von Very Low (van Vuuren et al. 2026), dieselbe Kette.</p>",
               " Kühlung: FaIR je Fläche, SSP2-4,5. Grenzwert: Erwärmung von Very Low über 1,5 °C (Median, van Vuuren et al. 2026).</p>")
    a = sec.index("    <p>Klick: Was bringt das über die Zeit, und reicht es?")
    b = sec.index("    <p>Die Lücke ist groß. Und damit die Frage vom Anfang.</p>")
    sec = sec[:a] + (
        "    <p>Klick: Was bringt das über die Zeit, und reicht es? Grün alle Bäume auf den kühlenden Flächen, orange auf allen Flächen. "
        "Gestrichelt der Grenzwert aus den Szenarien: Selbst Very Low liegt um 2050 gut 0,3 Grad über 1,5 °C — so viel Kühlung wäre nötig, um 1,5 °C "
        "nicht zu überschreiten. Die Bäume bringen dann 14 Millikelvin; 2100 fehlen noch rund 106, die Bäume liefern 19.</p>\n"
        "    <p class=\"q\">Falls Fragen kommen — Grenzwert: Median-Erwärmung von Very Low (FaIR-Ensemble der CMIP7-Marker, 7-Jahres-Mittel) minus 1,5 °C; Höchstwert ungeglättet 336 mK (2049); "
        "Very Low enthält bereits 335 Gt Entnahme, auch Landsenke, der Grenzwert ist also zusätzlich. Bäume: vier FaIR-Läufe wie auf den "
        "Backup-Folien „Globale Temperaturwirkung über die Zeit“ und „Beitrag der Aufforstung zum Entnahmebedarf“ (dort in Gt: 59 von 335 Gt).</p>\n") + sec[b:]
    main = main[: m.start()] + sec + main[m.end():]

    # ---- the break: dark, centred, no DAC; from here on its own accent
    m = _sec(main, "Sind wir auf dem Holzweg?")
    brk = ('<section class="slide chapter brk" data-ch="dac" data-title="Sind wir auf dem Holzweg?">\n'
           '  <div class="ctext"><h1 class="rise">Sind wir auf dem Holzweg<em>?</em></h1></div>\n  ' + _break_svg() + '\n'
           '  <aside class="notes" data-n="0">\n'
           '    <p>Bäume allein schließen die Lücke nicht. Sind wir also auf dem Holzweg, wenn wir auf den Wald setzen?</p>\n'
           '    <p>Klick: Und da kommt der Ingenieur — wir haben uns bisher aus fast allem herausentwickelt. Sein Vorschlag: Direct Air Capture. '
           'Rechnen wir die Technik mit derselben Systemgrenze.</p>\n'
           '  </aside>\n</section>\n\n')
    main = main[: m.start()] + brk + main[m.end():]
    i = main.index('data-title="Sind wir auf dem Holzweg?"')
    rest = re.sub(r'(<section class="slide[^"]*" )data-ch="vergleich"', r'\1data-ch="dac"', main[i:])
    main = main[:i] + rest

    n = iter(range(1, 1000))
    main = re.sub(r'<aside class="notes" data-n="\d+">', lambda mm: f'<aside class="notes" data-n="{next(n)}">', main)
    return patch_gap(main + "<!-- BACKUP:BEGIN -->" + backup)


EC_GAP = r"""
/* slide 25 overlay: first the trees alone (own scale), then the limit (scale grows), then the gap in red */
const EC_GAP = {
  steps: 1,
  option(k) {
    const D = window.LUECKE, P = (ys) => D.y.map((y, i) => [y, ys[i]]);
    const ip = D.need.indexOf(Math.max(...D.need));
    const end = (text, color) => ({ show: true, formatter: text, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 10 });
    const series = [
      { id: 'k', type: 'line', showSymbol: false, data: P(D.k), lineStyle: { color: '#2f7a45', width: 3.4 }, itemStyle: { color: '#2f7a45' }, z: 5,
        endLabel: end(`Bäume, kühlende Fl.: ${ecNum(D.k[D.k.length - 1], 0)} mK`, '#2f7a45'), labelLayout: { moveOverlap: 'shiftY' }, animationDuration: 1600 },
      { id: 'al', type: 'line', showSymbol: false, data: P(D.al), lineStyle: { color: '#c8602a', width: 3.4 }, itemStyle: { color: '#c8602a' }, z: 5,
        endLabel: end(`alle Flächen: ${ecNum(D.al[D.al.length - 1], 0)} mK`, '#c8602a'), labelLayout: { moveOverlap: 'shiftY' }, animationDuration: 1600, animationDelay: 200 }
    ];
    if (k >= 1) {
      /* the limit as one number: how far Very Low ends above 1.5 deg C in 2100, and what the trees close of it */
      const n = D.y.length - 1, need = D.need[n], kk = D.k[n];
      series.push({ id: 'need', type: 'scatter', data: [[2100, need]], symbolSize: 14, z: 6, clip: false,
                    itemStyle: { color: '#8e0d16', borderColor: '#fff', borderWidth: 2 }, animationDelay: 700,
                    label: { show: true, position: 'right', distance: 12, color: '#8e0d16', fontFamily: EC.font, fontSize: 19, fontWeight: 600,
                             formatter: `nötig für 1,5 °C in 2100:\n${ecNum(need / kk, 1)}-mal die Bäume` },
                    markLine: { silent: true, symbol: 'none', animationDuration: 900, animationDelay: 1100,
                                lineStyle: { color: 'rgba(196,18,31,.85)', width: 12, type: 'solid', cap: 'butt' },
                                label: { show: true, position: 'middle', distance: 14, color: '#c4121f', fontFamily: EC.font, fontSize: 19, fontWeight: 600,
                                         formatter: `es fehlen\n≈ ${ecNum(D.co2, 0)} Gt CO₂ Entnahme`, rotate: 0, align: 'right', offset: [-18, 0], lineHeight: 24 },
                                data: [[{ coord: [2100, kk] }, { coord: [2100, need] }]] } });
    }
    return {
      animationDurationUpdate: 900, animationEasingUpdate: 'cubicInOut',
      title: { text: 'Kühlung Jahr für Jahr, gepflanzt 2026', left: 74, top: 0, textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 21, fontWeight: 600 } },
      grid: { left: 74, right: 270, top: 50, bottom: 46 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisTick: { show: true, customValues: [2026, 2050, 2075, 2100] }, axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: k >= 1 ? 120 : 25, interval: k >= 1 ? 20 : 5, name: 'Kühlung der Erde [mK]', nameLocation: 'middle', nameGap: 52,
                      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19 }, splitLine: { show: true, lineStyle: { color: EC.grid } } }),
      tooltip: ecTooltip({ trigger: 'axis', formatter: ps => `<b>${ps[0].value[0]}</b><br>` + ps.filter(p => ['k', 'al'].includes(p.seriesId))
                    .map(p => `${ecDot(p.color)}${ecNum(p.value[1], 0)} mK`).join('<br>') }),
      series
    };
  }
};
"""


def patch_gap(page: str) -> str:
    """The overlay chart of slide 25 as a staged ECharts chart."""
    import json
    from pathlib import Path

    data = json.loads((Path(__file__).resolve().parents[2] / "docs/slides/chart_data/luecke.json").read_text())
    page = _rep(page, "const EC_CHARTS = { temperatur: EC_TEMPERATURE, entnahme: EC_REMOVAL, entnahmebalken: EC_REMOVAL_BARS };",
                "window.LUECKE = " + json.dumps(data) + ";\n" + EC_GAP +
                "const EC_CHARTS = { temperatur: EC_TEMPERATURE, entnahme: EC_REMOVAL, entnahmebalken: EC_REMOVAL_BARS, luecke: EC_GAP };")
    m = re.search(r'<div class="chart" data-chart="w2b"[^>]*></div>', page)
    assert m
    page = page[: m.start()] + ('<div class="chart" data-ec="luecke" data-step="2" data-label="Kühlung der Erde 2026 bis 2100 durch alle Bäume; '
                                'dann die Kühlung, die nötig wäre, um im Szenario Very Low unter 1,5 °C zu bleiben"></div>') + page[m.end():]
    page = _rep(page, '<p class="takeaway" data-step="3" style="--d:0">Grenzwert 1,5 °C:', '<p class="takeaway" data-step="4" style="--d:0">Grenzwert 1,5 °C:')
    page = _rep(page, "    <p>Klick: Was bringt das über die Zeit, und reicht es? Grün alle Bäume auf den kühlenden Flächen, orange auf allen Flächen. "
                      "Gestrichelt der Grenzwert aus den Szenarien:",
                "    <p>Klick: Was bringt das über die Zeit? Grün alle Bäume auf den kühlenden Flächen, orange auf allen Flächen: rund 20 Millikelvin.</p>\n"
                "    <p>Klick: Und reicht das? Gestrichelt der Grenzwert aus den Szenarien, die Achse wächst mit:")
    return page
