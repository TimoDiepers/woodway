"""Temperature slide, left: one native chart from the single year to the three sites.

Clicks 4-7 of the slide (chart steps 0-3): the answer to one year of forcing (Aachen, 2041), the same for
every fifth year of the growing tree, their sum (the tree's curve), then the three sites. The y-axis fits
what is shown and grows smoothly with each click. Data: docs/slides/chart_data/tempsum.json
(scripts/build_tempsum_data.py), temperature response g_T of the FaIR member.
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

JS = r"""
/* temperature slide: one year -> every fifth year -> sum = the tree -> three sites; the axis fits each click */
window.TEMPSUM = %s;
const EC_TEMPSUM = {
  steps: 3,
  option(k) {
    const D = window.TEMPSUM, A = D.sites[0], red = '#b2182b';
    const pulse = p => [[p.year, 0], ...p.v.map((v, i) => [p.year + i, v])];
    const font = { fontFamily: EC.font, fontSize: 19 };
    const series = [];
    // y range: the lowest point shown, rounded out to a nice step; a little room above zero
    let lo = Math.min(...D.one.v);
    if (k >= 1) lo = Math.min(lo, ...D.pulses.flatMap(p => p.v));
    if (k >= 2) lo = Math.min(lo, ...A.dt);
    if (k >= 3) lo = Math.min(lo, ...D.sites.flatMap(s => s.dt));
    const step = [1, 2, 5, 10, 20, 50].find(s => -lo * 1.08 / s <= 6.5) || 100;
    const ymin = Math.floor(lo * 1.08 / step) * step, ymax = step * 0.35;
    if (k <= 2) {
      series.push({ id: 'one', type: 'line', data: pulse(D.one), showSymbol: false, z: 6,
                    lineStyle: { color: red, width: 3.2 }, animationDuration: 900 });
      const v0 = D.one.v[0], y = D.one.year;
      const num = (x, yv, t, pos) => ({ value: [x, yv], symbolSize: 0,
        label: { show: true, position: pos, distance: 6, formatter: t, color: EC.ink, fontFamily: EC.font, fontSize: 22, fontWeight: 700 } });
      series.push({ id: 'one-k', type: 'scatter', z: 8, silent: true, animationDuration: 300, animationDelay: 600,
                    data: [{ value: [y, 0], symbol: 'rect', symbolSize: [12, 7], itemStyle: { color: EC.ink } },
                          ] });
    }
    if (k >= 1 && k <= 2) {
      const data = D.pulses.flatMap(p => [...pulse(p), null]);
      series.push({ id: 'every', type: 'line', data, connectNulls: false, showSymbol: false, z: 4,
                    lineStyle: { color: red, width: 1.6, opacity: .45 }, animationDuration: 900 });
      series.push({ id: 'every-dots', type: 'scatter', z: 5, silent: true, symbolSize: 8, itemStyle: { color: red },
                    data: [D.one, ...D.pulses].map(p => [p.year, p.v[0]]), animationDuration: 400 });
    }
    // the site name at the end of its curve, once the three sites are shown
    const site = (s, i) => ({
      id: 'site' + i, type: 'line', data: D.years.map((y, j) => [y, s.dt[j]]), showSymbol: false, z: 7, clip: false,
      lineStyle: { color: s.color, width: 3.4 }, itemStyle: { color: s.color }, animationDuration: 2200, animationEasing: 'linear',
      markPoint: { silent: true, symbol: 'circle', symbolSize: 0, animationDelay: 2200,
                   data: k >= 3 ? [{ coord: [D.years[D.years.length - 1], s.dt[s.dt.length - 1]],
                                     label: { show: true, position: 'right', distance: 10, formatter: s.label, color: s.color,
                                              fontFamily: EC.font, fontSize: 19, fontWeight: 600 } }] : [] } });
    if (k >= 2) series.push(site(A, 0));
    if (k >= 3) {
      D.sites.slice(1).forEach((s, i) => series.push(site(s, i + 1)));
      // Joensuu: the dip, why the cooling gets weaker
      const J = D.sites[1], jmin = J.dt.indexOf(Math.min(...J.dt)), jx = D.years[jmin], jy = J.dt[jmin];
      series.push({ id: 'jnote', type: 'line', data: [[jx + 11, jy - 3.2], [jx + 0.6, jy - 0.6]], z: 6, silent: true,
                    showSymbol: false, symbol: ['none', 'arrow'], symbolSize: 9,
                    lineStyle: { color: J.color, width: 1.6 }, animationDelay: 2200, animationDuration: 400,
                    markPoint: { silent: true, symbol: 'circle', symbolSize: 0, animationDelay: 2200,
                                 data: [{ coord: [jx + 11.5, jy - 3.2],
                                          label: { show: true, position: 'right', distance: 0, align: 'left', verticalAlign: 'top',
                                                   formatter: 'Antrieb wird schwächer:\nAlbedo wärmt weiter,\nBaum bindet kaum noch CO₂',
                                                   color: J.color, fontFamily: EC.font, fontSize: 17, lineHeight: 21 } }] } });
    }
    const titles = [
      `Ein Jahr Antrieb (${A.name}, ${D.one.year})`,
      `Jedes ${D.every}. Jahr: Der Baum wächst, sein Antrieb wird größer`,
      'Summe aller Jahre = ΔT des Baums',
      'Je Baum: sein Antrieb φ(t) → ΔT(t)'];
    return {
      animationEasing: 'cubicOut', animationEasingUpdate: 'cubicInOut', animationDurationUpdate: 900,
      title: { text: titles[k], left: 96, top: 4, textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 19, fontWeight: 400 } },
      grid: { left: 96, right: 150, top: 48, bottom: 48 },
      xAxis: ecAxis({ type: 'value', min: 2025, max: D.years[D.years.length - 1], interval: 25,
                      axisLabel: Object.assign({ color: EC.muted, formatter: v => String(v), showMinLabel: true, showMaxLabel: true }, font),
                      axisTick: { show: false } }),
      yAxis: ecAxis({ type: 'value', min: ymin, max: ymax, interval: step,
                      axisLabel: Object.assign({ color: EC.muted, showMaxLabel: false, formatter: v => v === 0 ? '0' : ecNum(v, 0).replace('-', '−') }, font),
                      splitLine: { show: true, lineStyle: { color: EC.grid } } }),
      series
    };
  }
};
"""


def _rep(s, old, new):
    assert s.count(old) == 1, old[:90]
    return s.replace(old, new)


def patch(page: str) -> str:
    data = json.loads((REPO / "docs/slides/chart_data/tempsum.json").read_text(encoding="utf-8"))
    m = re.search(r"const EC_CHARTS = \{([^}]*)\};", page)
    assert m
    page = page[: m.start()] + JS % json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n" + \
        "const EC_CHARTS = {" + m.group(1).rstrip() + ", tempsum: EC_TEMPSUM };" + page[m.end():]
    # the mpl panels of the temperature slide go; the slide ends with the solved formula (click 4), the
    # chart gets a slide of its own right after it
    old = re.search(r'<div class="chart" data-step="4" data-slot-steps="0,1,2" data-chart="k12p"[^>]*></div><div class="chart" data-step="7" data-chart="k12t"[^>]*></div>', page)
    assert old
    page = page[: old.start()] + page[old.end():]
    m = re.search(r'<section class="slide" data-ch="klima" data-title="Temperaturantwort auf den Strahlungsantrieb">.*?</section>\n', page, flags=re.S)
    assert m
    a = m.group(0)
    road = re.search(r'<div class="road" style="height:52px; margin-bottom:12px">.*?</span></div>', a).group(0)
    src = re.search(r'<p class="src">.*?</p>', a).group(0)
    take = re.search(r'<p class="takeaway" data-step="8"[^>]*>(.*?)</p>', a, flags=re.S).group(1)
    a = re.sub(r'\n      <div class="rise ts5" data-step="7".*?</div>', '', a, count=1, flags=re.S)
    a, k4 = re.subn(r'<p class="ghs"><b style="background:#1f7a8c">4</b>.*?</p>', '', a, count=1, flags=re.S)
    assert k4 == 1
    a = _rep(a, '<div class="tstep" style="display:flex; flex-direction:column; gap:6px;', '<div class="tstep" style="display:flex; flex-direction:column; gap:24px;')
    a = _rep(a, 'style="font-size:23px; text-align:left; margin:0 0 2px">$$\\htmlClass{hl hl-r}', 'style="font-size:23px; text-align:left; margin:0">$$\\htmlClass{hl hl-r}')
    a = re.sub(r'\n    <div class="foot"><div></div><p class="takeaway" data-step="8".*?</p></div>', '', a, count=1, flags=re.S)
    n = re.search(r'(<aside class="notes" data-n="\d+">\n)(.*?)(  </aside>)', a, flags=re.S)
    paras = re.findall(r'    <p.*?</p>\n', n.group(2), flags=re.S)
    keep = [q for q in paras[:5]] + [q for q in paras if q.startswith('    <p>Oben die Energiebilanz')]
    keep[4] = ("    <p>Klick: Die Gleichung gelöst — ΔT, die Temperaturänderung durch den Baum. Jedes Jahr Antrieb liefert einen Beitrag, "
               "der danach abklingt; alle Jahre zusammen ergeben ΔT. Wie das für einen Baum aussieht, auf der nächsten Folie.</p>\n")
    a = a[: n.start(2)] + "".join(keep) + a[n.start(3):]

    tex = road[road.index('$'): road.rindex('$') + 1]
    box = re.search(r'\\htmlClass\{hl on hl-t\}\{.*\}\$$', tex).group(0)
    tex = tex.replace(box, r"\htmlClass{hl on hl-t}{\tq{\Delta T}(t) = \sum_{t' \le t} \varphi(t')/\pc{C}\; e^{-\pc{\Lambda}(t-t')/\pc{C}}}$")
    road_b = road[: road.index('$')] + tex + '</span></div>'
    pts = [("#b2182b", 0, 'Ein Jahr Antrieb: sofort kühler, dann Abklingen<br>→ ein kleiner Rest bleibt lange (tiefer Ozean)'),
           ("#b2182b", 1, 'Jedes Jahr ein solcher Beitrag<br>→ Baum wächst: Antrieb und Beitrag größer'),
           ("#2f6fb7", 2, 'Summe aller Jahre = ΔT des Baums<br>→ die langen Reste addieren sich'),
]
    # the points centred beside the plot, the problem box at the foot of the column
    right = ('<div style="display:flex; flex-direction:column; align-self:stretch; min-width:0">'
             '<div style="display:flex; flex-direction:column; gap:30px; margin:auto 0">') + "".join(
        '<div class="rise"' + ('' if s == 0 else f' data-step="{s}"') + f' style="--d:{300 if s == 0 else 200}"><p class="ghs"><b style="background:{c}">{s + 1}</b>{txt}</p></div>'
        for c, s, txt in pts) + ('</div><p class="takeaway" data-step="4" style="--d:0; font-size:22px; line-height:1.45; margin:0; '
                                 'padding-top:26px; padding-bottom:26px">' + take + '</p></div>')
    chart = ('<div class="chart" data-step="0" data-ec="tempsum" data-label="Ein Baum in Aachen: Temperaturantwort auf den Antrieb '
             'eines Jahres, jedes fünften Jahres, die Summe aller Jahre; dann die Temperaturwirkung je Baum an drei Orten"></div>')
    notes_b = (
        "    <p>Oben ist jetzt die Lösung eingesetzt: ΔT als Summe über alle Jahre Antrieb. Links, was das heißt — erst für ein einzelnes Jahr in Aachen: "
        "Eins, der Antrieb des Baums nur in diesem Jahr. Zwei, die Erde wird sofort kühler. Drei, danach klingt das ab — schnell die Oberfläche, "
        "ein kleiner Rest hält lange, weil der tiefe Ozean nachzieht.</p>\n"
        "    <p>Klick: Dasselbe für jedes fünfte Jahr. Der Baum wächst, sein Antrieb wird größer, also auch die Beiträge. Die Achse wächst mit.</p>\n"
        "    <p>Klick: Die Summe über alle Jahre — das ist die Temperaturwirkung des Baums in Aachen. Die einzelnen Beiträge sind klein, aber ihre langen "
        "Reste addieren sich über die Jahrzehnte. Dasselbe Prinzip wie beim CO₂: dort die Impulsantwort des Kohlenstoffkreislaufs, hier die der Temperatur. "
        "Gerechnet mit der Temperaturantwort von FaIR, die Summe ist genau das FaIR-Ergebnis.</p>\n"
        + paras[7] + paras[8] + "".join(q for q in paras if q.startswith('    <p>Rechnerisch') or q.startswith('    <p>Warum ein Klimamodell')))
    b = ('<section class="slide" data-ch="klima" data-title="Temperaturwirkung je Baum">\n'
         '  <header class="sh"><h2>Vom Strahlungsantrieb zur Temperatur</h2></header>\n'
         '  <div class="body">\n    ' + road_b + '\n'
         '    <div style="display:grid; grid-template-columns:860px 1fr; gap:34px; flex:1; min-height:0; align-items:center">'
         '<div class="ghwrap">' + chart + '<div class="axlab" style="left:22px; top:50%"><span class="tex">$\\tq{\\Delta T}(t)$</span> je Baum [10⁻¹⁵ K]</div></div>' + right + '</div>\n'
         '  </div>\n  ' + src + '\n'
         '  <aside class="notes" data-n="0">\n' + notes_b + '  </aside>\n</section>\n')
    page = page[: m.start()] + a + "\n" + b + page[m.end():]
    # notes numbers follow the slides again; the gap slide moved one on
    k = iter(range(1, 1000))
    page = re.sub(r'<aside class="notes" data-n="\d+">', lambda _: f'<aside class="notes" data-n="{next(k)}">', page)
    page = _rep(page, "(Folie 25; Klimaantwort", "(Folie 26; Klimaantwort")
    return page
