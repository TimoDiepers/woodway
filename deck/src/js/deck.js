/* ===========================================================
   KaTeX
   Symbol colours: the four carbon processes and the two
   parameter groups keep the deck's colour code.
   =========================================================== */
const TEX_MACROS = {
  "\\mB":  "\\boldsymbol{m}^{c}_{\\mathrm{Baum}}",
  "\\mPS": "\\textcolor{2f7a45}{\\boldsymbol{m}^{c}_{\\mathrm{PS}}}",
  "\\mRE": "\\textcolor{7e4a74}{\\boldsymbol{m}^{c}_{\\mathrm{RE}}}",
  "\\mZS": "\\textcolor{3d6698}{\\boldsymbol{m}^{c}_{\\mathrm{ZS}}}",
  "\\mST": "\\textcolor{c0392b}{\\boldsymbol{m}^{c}_{\\mathrm{ST}}}",
  "\\pc":  "\\textcolor{8a6a1e}{\\boldsymbol{#1}}",
  "\\sc":  "\\textcolor{c0392b}{\\boldsymbol{#1}}",
  "\\bq":  "\\textcolor{6b4a2b}{\\boldsymbol{#1}}",   // from the tree chapter
  "\\rq":  "\\textcolor{1f7a8c}{\\boldsymbol{#1}}",   // response functions g_C, g_T
  "\\cq":  "\\textcolor{1b7837}{\\boldsymbol{#1}}",   // CO2 path
  "\\aq":  "\\textcolor{d95f02}{\\boldsymbol{#1}}",   // albedo
  "\\tq":  "\\textcolor{b2182b}{\\boldsymbol{#1}}",   // temperature
  "\\gq":  "\\textcolor{5f7f48}{\\boldsymbol{#1}}",   // canopy closure
  "\\st":  "\\htmlData{step=#1}{#2}"          // \st{2}{…}: this term appears on click 2
};

function renderTex(root) {
  // Walk text nodes, replacing $$…$$ (display) and $…$ (inline).
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) if (walker.currentNode.nodeValue.includes('$') && !walker.currentNode.parentElement.closest('.notes, svg')) nodes.push(walker.currentNode);
  for (const node of nodes) {
    const parts = node.nodeValue.split(/(\$\$[\s\S]+?\$\$|\$[^$]+?\$)/g);
    if (parts.length === 1) continue;
    const frag = document.createDocumentFragment();
    for (const part of parts) {
      if (!part) continue;
      const display = part.startsWith('$$');
      if (part.startsWith('$') && part.endsWith('$') && part.length > 1) {
        const span = document.createElement('span');
        try {
          katex.render(part.slice(display ? 2 : 1, display ? -2 : -1), span,
            { displayMode: display, macros: TEX_MACROS, throwOnError: false, strict: false, trust: ctx => ctx.command === '\\htmlData' || ctx.command === '\\htmlClass' });
        } catch (e) { span.textContent = part; }
        frag.appendChild(span);
      } else frag.appendChild(document.createTextNode(part));
    }
    node.parentNode.replaceChild(frag, node);
  }
}

/* ===========================================================
   CHART HELPERS
   Every chart object has the same click interface: nSteps,
   play(k) animates up to click k, final(k) shows it at once.
   =========================================================== */
const SVGNS = 'http://www.w3.org/2000/svg';
function E(tag, attrs, parent) {
  const e = document.createElementNS(SVGNS, tag);
  for (const k in attrs) if (attrs[k] !== null && attrs[k] !== undefined) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
/* a chart text with a letter subscript (q̇_ein): rich text, the subscript smaller and lower */
function subRich(t, f) {
  if (!t.sub) return {};
  const n = f.fontSize, base = { fontFamily: f.fontFamily, fontWeight: f.fontWeight, color: t.c, verticalAlign: 'bottom' };
  return {
    formatter: t.sub.map(([x, low]) => `{${low ? 'lo' : 'up'}|${x.replace(/[{}|]/g, '')}}`).join(''),
    rich: { up: { ...base, fontStyle: f.fontStyle, fontSize: n, lineHeight: n * 1.18, padding: [0, 0, n * .22, 0] },
            lo: { ...base, fontStyle: 'normal', fontSize: n * .68, lineHeight: n * .8 } } };
}
const clamp01 = v => v < 0 ? 0 : v > 1 ? 1 : v;
const easeOut = p => 1 - Math.pow(1 - p, 3);
const easeInOut = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;

const T_START = 250, T_REVEAL = 1500, T_BAR = 650, T_BARS = 900, T_FADE = 450, T_GAP = 650;
const FAR = 1e6;
let chartUid = 0;

/* ===========================================================
   ECHARTS (pilot: slides 2 and 3)
   Each chart is a function step -> option; setOption with
   replaceMerge lets ECharts animate what is new and fade what
   goes. SVG renderer, so text stays sharp when the deck scales.
   =========================================================== */
const EC = {
  ink: '#1b2420', ink2: '#3f4a44', muted: '#5d665f', line: '#d6ccb6', grid: '#e4dccb', alb: '#c8602a',   // = --alb
  font: "'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif"
};
const ecNum = (v, d = 1) => v.toLocaleString('de-DE', { minimumFractionDigits: d, maximumFractionDigits: d });

function ecAxis(extra) {
  return Object.assign({
    axisLine: { lineStyle: { color: '#8a918c', width: 1 } },
    axisTick: { show: false },
    axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19 },
    splitLine: { show: false },
    nameTextStyle: { color: EC.muted, fontFamily: EC.font, fontSize: 19 }
  }, extra);
}
function ecTooltip(extra) {
  return Object.assign({
    backgroundColor: 'rgba(251,248,241,.97)', borderColor: EC.line, borderWidth: 1, padding: [8, 12],
    textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 17 },
    extraCssText: 'box-shadow:0 6px 18px -8px rgba(40,34,20,.35); border-radius:6px;'
  }, extra);
}
const ecDot = c => `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${c};margin-right:6px"></span>`;

/* slide 2: warming of the seven markers ------------------------------------ */
/* area under a curve: the colour half way to grey, a vertical fade from the line down */
function ecArea(hex, a) {
  const c = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)), g = (c[0] + c[1] + c[2]) / 3;
  const m = c.map(v => Math.round(v * .5 + g * .5)).join(',');
  return { origin: 'start', color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: `rgba(${m},${a})` }, { offset: .4, color: `rgba(${m},${a * .25})` }, { offset: 1, color: `rgba(${m},0)` }]) };
}
const EC_TEMPERATURE = {
  steps: 1,   // 0 observation, then the scenarios as its continuation · 1 focus on Very Low
  unitRange: [5, 30 + 44],   // y-axis span [°C] and grid top+bottom [px], for label offsets
  option(k) {
    const D = window.CMIP7, ext = D.ext, M = D.markers;
    const pts = (ys, vs, keep) => ys.map((y, i) => keep(y) ? [y, vs[i]] : null).filter(Boolean);
    const series = [{
      id: 'obs', name: 'Beobachtung', type: 'line', showSymbol: false, data: pts(D.obs.y, D.obs.v, () => true),
      lineStyle: { color: EC.ink, width: 2.2 }, itemStyle: { color: EC.ink }, z: 5, animationDuration: 4200, animationEasing: 'linear',
      markPoint: { silent: true, animation: false, symbol: 'circle', symbolSize: 0,
                   label: { show: true, position: 'inside', formatter: 'Beobachtung', color: EC.ink, fontFamily: EC.font, fontSize: 19 },
                   data: [{ coord: [1984, 1.05] }] },
      markLine: {
        silent: true, symbol: 'none', animation: false,
        lineStyle: { color: EC.muted, type: [6, 5], width: 1 },
        label: { color: EC.muted, fontFamily: EC.font, fontSize: 19, position: 'insideStartTop' },
        data: [{ yAxis: 1.5, label: { formatter: '1,5 °C' } }, { yAxis: 2, label: { formatter: '2 °C' } },
               { xAxis: 2100, lineStyle: { type: [2, 4] }, label: { formatter: '2100', position: 'end', distance: 6 } }]
      }
    }];
    // end labels at 2150, pushed apart where they would collide (min. 0.2 °C)
    const ends = M.map(m => ({ k: m.k, y: D.temp[m.k].med[D.temp[m.k].y.indexOf(2150)] })).sort((a, b) => a.y - b.y);
    ends.forEach((e, j) => { if (j) e.y = Math.max(e.y, ends[j - 1].y + 0.2); });
    const endY = Object.fromEntries(ends.map(e => [e.k, e.y]));
    M.forEach((m, i) => {
      const t = D.temp[m.k], dim = k >= 1 && m.k !== 'VL' ? .22 : 1;
      const style = { color: m.color, width: m.k === 'VL' && k >= 1 ? 3.4 : 2.4, opacity: dim };
      // the label hangs on the last point, so it appears when the line gets there
      const p = pts(t.y, t.med, y => y >= 2023), last = p.pop(), shift = (endY[m.k] - last[1]) * (EC_TEMPERATURE.pxPerUnit || 90);
      p.push({ value: last, symbol: 'circle', symbolSize: 1,
               label: { show: true, position: 'right', distance: 10, offset: [0, -shift], formatter: m.label, color: m.color, opacity: dim,
                        fontFamily: EC.font, fontSize: 19, fontWeight: 600 } });
      series.push({ id: `s${m.k}`, name: m.label, type: 'line', showSymbol: true, symbolSize: 0, z: 4,
                    data: p, lineStyle: style, itemStyle: { color: m.color, opacity: 0 },
                    animationDuration: 4200, animationEasing: 'linear', animationDelay: 0 });
    });
    {
      const at = M.map(m => ({ k: m.k, color: m.color, v: D.temp[m.k].med[D.temp[m.k].y.indexOf(2100)] })).sort((a, b) => a.v - b.v);
      at.forEach((e, j) => { e.y = j ? Math.max(e.v, at[j - 1].y + 0.19) : e.v; });
      series.push({ id: 'v2100', type: 'scatter', z: 7, tooltip: { show: false },
                    animationDuration: 400, animationDelay: j => 4200 + j * 60,
                    data: at.map(e => ({ value: [2100, e.v], symbolSize: 9,
                      itemStyle: { color: e.color, borderColor: '#f2ede2', borderWidth: 2, opacity: k >= 1 && e.k !== 'VL' ? .25 : 1 },
                      label: { show: true, position: 'left', distance: 8, offset: [0, -(e.y - e.v) * (EC_TEMPERATURE.pxPerUnit || 90)],
                               formatter: `${ecNum(e.v)} °C`, color: e.color, opacity: k >= 1 && e.k !== 'VL' ? .3 : 1,
                               fontFamily: EC.font, fontSize: 17, fontWeight: 600,
                               backgroundColor: 'rgba(242,237,226,.85)', padding: [1, 3], borderRadius: 3 } })) });
    }
    if (k >= 1) {
      const f = D.facts.VL;
      series.push({ id: 'peak', type: 'scatter', z: 6, data: [[f.peak_jahr, f.peak_k]], symbolSize: 11,
                    itemStyle: { color: '#2e7d4f', borderColor: '#fff', borderWidth: 2 }, tooltip: { show: false },
                    label: { show: true, position: 'top', distance: 10, color: '#24603d', fontFamily: EC.font, fontSize: 19, fontWeight: 600,
                             formatter: `Höchstwert ${ecNum(f.peak_k)} °C (${f.peak_jahr})` } });
    }
    return {
      animationEasing: 'cubicOut', animationEasingUpdate: 'cubicInOut', animationDurationUpdate: 700,
      grid: { left: 78, right: 200, top: 30, bottom: 44 },
      xAxis: ecAxis({ type: 'value', min: 1950, max: 2150, interval: 25, axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: 5, interval: 1, name: 'Erwärmung gegenüber 1850–1900', nameLocation: 'middle', nameGap: 52,
                      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, formatter: '{value} °C' },
                      splitLine: { show: true, lineStyle: { color: EC.grid } } }),
      tooltip: ecTooltip({
        trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: EC.muted, type: [3, 3] } },
        formatter: ps => {
          const year = ps[0].axisValue, rows = ps.filter(p => p.seriesName && p.seriesName.trim() && p.seriesType === 'line');
          const seen = new Set();
          return `<b>${year}</b><br>` + rows.sort((a, b) => b.value[1] - a.value[1])
            .filter(p => !seen.has(p.seriesName.trim()) && seen.add(p.seriesName.trim()))
            .map(p => `${ecDot(p.color)}${p.seriesName.trim()}: <b>${ecNum(p.value[1], 2)} °C</b>`).join('<br>');
        }
      }),
      series
    };
  }
};

/* slide 3: CO2 removal, per year and summed to 2100 ------------------------ */
const EC_REMOVAL = {
  steps: 0,   // per year and cumulative bars together
  option(k) {
    const D = window.CMIP7, ext = D.ext, M = D.markers, col = key => M.find(m => m.k === key).color;
    const lab = key => M.find(m => m.k === key).label;
    const neg = v => (v < 0 ? '−' : '') + ecNum(Math.abs(v), 0);   // removal drawn as a negative flow
    const series = [];
    M.forEach((m, i) => {
      const r = D.rem[m.k]; let acc = 0;
      const v = r.y.map((y, j) => [y, r.novel[j] + r.land[j]]).filter(p => p[0] >= 2024 && p[0] <= 2100).map(p => [p[0], -(acc += p[1]).toFixed(1)]);
      series.push({ id: `s${m.k}`, name: m.label, type: 'line', showSymbol: false, xAxisIndex: 0, yAxisIndex: 0,
                    data: v, lineStyle: { color: m.color, width: 2.4 }, itemStyle: { color: m.color }, z: 3,
                    markLine: i ? undefined : { silent: true, symbol: 'none', animation: false, lineStyle: { color: EC.muted, type: [2, 4], width: 1 },
                                                label: { formatter: '2100', position: 'end', distance: 6, color: EC.muted, fontFamily: EC.font, fontSize: 19 },
                                                data: [] },
                    animationDuration: 1800, animationEasing: 'cubicInOut', animationDelay: i * 110 });
    });
    M.forEach((m, i) => {
      const r = D.rem[m.k]; let acc = 0, N = 24;
      const v = r.y.map((y, j) => [y, r.novel[j] + r.land[j]]).filter(p => p[0] >= 2024 && p[0] <= 2100).map(p => [p[0], -(acc += p[1])]);
      const c = [1, 3, 5].map(j => parseInt(m.color.slice(j, j + 2), 16)).join(',');
      for (let b = 0; b < N; b++)
        series.push({ id: `a${m.k}${b}`, type: 'line', stack: `area${m.k}`, xAxisIndex: 0, yAxisIndex: 0, showSymbol: false, silent: true,
                      tooltip: { show: false }, z: 2, lineStyle: { width: 0 }, data: v.map(p => [p[0], p[1] / N]),
                      areaStyle: { color: `rgba(${c},${(.55 * ((b + 1) / N) ** 1.7).toFixed(3)})` },
                      animationDuration: 1800, animationEasing: 'cubicInOut', animationDelay: i * 110 });
    });
    // bars in the order in which the curves on the left end (category axis runs bottom-up: highest last)
    const endOf = key => D.cum.find(c => c.k === key).total;
    const order = M.map(m => m.k).sort((a, b) => endOf(a) - endOf(b));
    {
      series.push({ id: 'total', name: 'Summe 2024–2100', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, barWidth: '62%',
                    data: order.map(key => ({ value: -D.cum.find(c => c.k === key).total, itemStyle: { color: col(key), borderRadius: [10, 0, 0, 10] } })),
                    animationDuration: 900, animationDelay: i => i * 90,
                    label: { show: true, position: 'left', color: EC.ink, fontFamily: EC.font, fontSize: 20, formatter: p => neg(p.value) } });
    }
    const title = (text, left) => ({ text, left, top: 0, textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 21, fontWeight: 600 } });
    return {
      animationEasing: 'cubicOut', animationDurationUpdate: 700,
      title: [title('Negative CO₂-Emissionen, kumuliert seit 2024', 70), title('Summe 2024–2100', '58%')],
      grid: [{ left: 70, right: '47%', top: 46, bottom: 44 }, { left: '58%', right: 210, top: 46, bottom: 44 }],
      xAxis: [ecAxis({ type: 'value', gridIndex: 0, min: 2025, max: 2100, interval: 25, axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, formatter: v => String(v) } }),
              ecAxis({ type: 'value', gridIndex: 1, min: -400, max: 0, interval: 100, name: 'Gt CO₂, 2024–2100', nameLocation: 'middle', nameGap: 30,
                       axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, formatter: neg }, splitLine: { show: true, lineStyle: { color: EC.grid } } })],
      yAxis: [ecAxis({ type: 'value', gridIndex: 0, max: 0, name: 'Gt CO₂, kumuliert', nameLocation: 'middle', nameGap: 56, axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, formatter: neg }, splitLine: { show: true, lineStyle: { color: EC.grid } } }),
              ecAxis({ type: 'category', gridIndex: 1, position: 'right', data: order.map(lab),
                       axisLabel: { fontFamily: EC.font, fontSize: 19, fontWeight: 600, color: (v, i) => col(order[i]) } })],
      tooltip: ecTooltip({
        trigger: 'item',
        formatter: p => {
          if (p.seriesType === 'bar') {
            const c = D.cum.find(x => x.k === order[p.dataIndex]);
            return `<b>${lab(c.k)}</b><br>2024–2100: <b>${neg(-c.total)} Gt CO₂</b>`;
          }
          return `${ecDot(p.color)}${p.seriesName.trim()}, ${p.value[0]}: <b>${neg(p.value[1])} Gt CO₂ seit 2024</b>`;
        }
      }),
      series
    };
  }
};


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
window.LUECKE = {"co2": 262.3, "y": [2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042, 2043, 2044, 2045, 2046, 2047, 2048, 2049, 2050, 2051, 2052, 2053, 2054, 2055, 2056, 2057, 2058, 2059, 2060, 2061, 2062, 2063, 2064, 2065, 2066, 2067, 2068, 2069, 2070, 2071, 2072, 2073, 2074, 2075, 2076, 2077, 2078, 2079, 2080, 2081, 2082, 2083, 2084, 2085, 2086, 2087, 2088, 2089, 2090, 2091, 2092, 2093, 2094, 2095, 2096, 2097, 2098, 2099, 2100], "k": [-0.0, 0.03, 0.14, 0.34, 0.64, 1.01, 1.46, 1.98, 2.56, 3.19, 3.86, 4.57, 5.3, 6.04, 6.8, 7.56, 8.31, 9.06, 9.8, 10.51, 11.21, 11.89, 12.54, 13.16, 13.76, 14.33, 14.86, 15.37, 15.84, 16.28, 16.7, 17.08, 17.44, 17.76, 18.06, 18.34, 18.59, 18.81, 19.01, 19.19, 19.35, 19.49, 19.61, 19.72, 19.8, 19.88, 19.94, 19.98, 20.02, 20.04, 20.06, 20.06, 20.06, 20.05, 20.03, 20.01, 19.98, 19.95, 19.91, 19.87, 19.83, 19.78, 19.73, 19.68, 19.63, 19.58, 19.53, 19.48, 19.42, 19.37, 19.31, 19.26, 19.2, 19.14, 19.14], "al": [-0.0, 0.05, 0.21, 0.5, 0.92, 1.46, 2.11, 2.84, 3.64, 4.5, 5.41, 6.34, 7.28, 8.23, 9.17, 10.08, 10.97, 11.82, 12.63, 13.39, 14.1, 14.76, 15.36, 15.9, 16.38, 16.8, 17.17, 17.47, 17.73, 17.92, 18.07, 18.17, 18.22, 18.23, 18.19, 18.12, 18.01, 17.87, 17.7, 17.5, 17.28, 17.03, 16.76, 16.47, 16.17, 15.86, 15.53, 15.2, 14.85, 14.5, 14.15, 13.79, 13.43, 13.07, 12.71, 12.35, 11.99, 11.64, 11.29, 10.95, 10.61, 10.28, 9.95, 9.63, 9.32, 9.01, 8.72, 8.43, 8.14, 7.87, 7.6, 7.33, 7.08, 6.83, 6.83], "need": [0.0, 7.1, 19.7, 33.5, 60.3, 85.3, 109.1, 134.0, 155.5, 178.1, 197.0, 213.0, 230.4, 245.6, 258.2, 270.5, 282.2, 290.9, 300.6, 307.2, 314.8, 320.1, 322.6, 321.8, 322.9, 318.9, 316.7, 311.3, 304.6, 300.5, 296.9, 292.0, 290.2, 285.4, 282.8, 282.5, 278.6, 273.2, 268.4, 265.1, 261.9, 257.1, 253.4, 253.0, 249.0, 245.5, 240.5, 235.9, 232.8, 230.1, 224.1, 220.4, 217.1, 211.3, 205.8, 198.1, 188.3, 180.5, 175.2, 169.4, 163.4, 158.9, 154.1, 149.9, 145.8, 140.8, 132.3, 128.7, 123.7, 119.4, 115.2, 110.1, 107.0, 108.0, 105.8]};

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
      { id: 'al', type: 'line', showSymbol: false, data: P(D.al), lineStyle: { color: EC.alb, width: 3.4 }, itemStyle: { color: EC.alb }, z: 5,
        endLabel: end(`alle Flächen: ${ecNum(D.al[D.al.length - 1], 0)} mK`, EC.alb), labelLayout: { moveOverlap: 'shiftY' }, animationDuration: 1600, animationDelay: 200 }
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

/* temperature slide: one year -> every fifth year -> sum = the tree -> three sites; the axis fits each click */
window.TEMPSUM = @@TEMPSUM@@;
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


/* the gap chart on a dark slide: light text and lines, the colours of the curves stay */
function ecDark(o) {
  const map = { [EC.ink]: '#f2ede2', [EC.ink2]: '#d6dbd6', [EC.muted]: '#9aa39d', [EC.grid]: '#2c3437', [EC.line]: '#3a4447', '#8a918c': '#6d756f', '#8e0d16': '#ff7a6e', '#c4121f': '#ff5a4f', '#2f7a45': '#6cc28a', [EC.alb]: '#ef8a52' };
  const walk = v => { if (Array.isArray(v)) return v.map(walk); if (v && typeof v === 'object' && v.constructor === Object) { for (const k in v) v[k] = walk(v[k]); return v; }
                      return typeof v === 'string' && map[v] ? map[v] : v; };
  return walk(o);
}
const EC_GAP_END = { steps: 0, option() { return ecDark(EC_GAP.option(EC_GAP.steps)); } };
window.ZEIT = @@ZEIT@@;

/* chapter 3: trees all planted in 2026, three ways; then the warming of Very Low above 1.5 deg C */
const EC_ZEIT = {
  steps: 2,
  option(k) {
    const D = window.ZEIT, P = ys => D.jahre.map((y, i) => [y, ys[i]]), n = D.jahre.length - 1;
    // second label line: the path by cause in 2100 (cooling > 0): CO2 uptake, release at felling, albedo
    const sg = v => (v < 0 ? '−' : '') + ecNum(Math.abs(v), 0);
    const parts = key => { const T = D.pfade_teile[key];
      return `CO₂ ${sg(T.co2_aufnahme[n])}` + (Math.abs(T.co2_verlust[n]) >= .5 ? ` · Fällen ${sg(T.co2_verlust[n])}` : '') + ` · Albedo ${sg(T.albedo[n])}`; };
    const end = (text, color, key) => ({ show: true, formatter: key ? `{a|${text}}\n{b|${parts(key)}}` : text, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 10,
      rich: { a: { color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, lineHeight: 24 }, b: { color: EC.muted, fontFamily: EC.font, fontSize: 17, fontWeight: 400, lineHeight: 22 } } });
    const line = (id, ys, color, text, key, extra) => Object.assign({ id, type: 'line', showSymbol: false, data: P(ys), z: 5,
      lineStyle: { color, width: 3.4 }, itemStyle: { color }, endLabel: end(text, color, key), labelLayout: { moveOverlap: 'shiftY' },
      animationDuration: 1800 }, extra || {});
    const p = D.pfade, f = v => ecNum(v, 0);
    const series = [
      line('al', p.alle, EC.alb, `alle Flächen: ${f(p.alle[n])} mK`, 'alle'),
      line('k', p.kuehlt, '#2f7a45', `kühlende Flächen: ${f(p.kuehlt[n])} mK`, 'kuehlt', { animationDelay: 200 })];
    if (k >= 1) {
      series.push(line('fo', p.forst, '#14532d', `+ Forst, Holz gebunden: ${f(p.forst[n])} mK`, 'forst', { lineStyle: { color: '#14532d', width: 3.8 }, animationDelay: 300 }));
      series.push(line('ff', p.forst_frei, '#14532d', `Holz freigesetzt: ${f(p.forst_frei[n])} mK`, 'forst_frei',
                       { lineStyle: { color: '#14532d', width: 2.4, type: [8, 6] }, animationDelay: 600 }));
    }
    if (k >= 2) {
      for (const s of series) s.endLabel = Object.assign({}, s.endLabel, { show: s.id === 'fo', formatter: `{a|Bäume: ${f(p.forst_frei[n])}–${f(p.forst[n])} mK}` });
      const ip = D.noetig.indexOf(Math.max(...D.noetig));
      series.push({ id: 'need', type: 'line', showSymbol: false, data: P(D.noetig), z: 3, lineStyle: { color: '#8e0d16', width: 3 },
        areaStyle: { color: 'rgba(196,18,31,.16)' }, itemStyle: { color: '#8e0d16' }, animationDuration: 1800, animationDelay: 500,
        endLabel: end('Very Low über 1,5 °C', '#8e0d16'),
        markPoint: { silent: true, symbol: 'circle', symbolSize: 12, itemStyle: { color: '#8e0d16', borderColor: '#fff', borderWidth: 2 },
          label: { show: true, position: 'top', distance: 10, color: '#8e0d16', fontFamily: EC.font, fontSize: 19, fontWeight: 600,
                   formatter: `um ${D.jahre[ip]}: ${ecNum(D.noetig[ip] / 1000, 2)} K zu warm` },
          data: [{ coord: [D.jahre[ip], D.noetig[ip]] }] } });
    }
    return {
      animationDurationUpdate: 1100, animationEasingUpdate: 'cubicInOut',
      title: { text: 'Kühlung Jahr für Jahr, alle Bäume 2026 gepflanzt', left: 74, top: 0,
               textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 21, fontWeight: 600 } },
      grid: { left: 74, right: 330, top: 50, bottom: 46 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisTick: { show: true, customValues: [2026, 2050, 2075, 2100] },
                      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: k >= 2 ? 350 : 35, interval: k >= 2 ? 50 : 5, name: k >= 2 ? 'Kühlung bzw. Erwärmung [mK]' : 'Kühlung der Erde [mK]', nameLocation: 'middle', nameGap: 52,
                      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19 }, splitLine: { show: true, lineStyle: { color: EC.grid } } }),
      series
    };
  }
};

/* variants of the optimisation: trees alone, DAC at the 20 %/a growth limit, DAC without a growth limit */
const EC_TEMPO = {
  steps: 2,
  option(k) {
    const D = window.ZEIT, T = D.tempo, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const peak = (ys, color, text, pos) => { const i = ys.indexOf(Math.max(...ys));
      return { silent: true, symbol: 'circle', symbolSize: 11, itemStyle: { color, borderColor: '#14181a', borderWidth: 2 },
        label: { show: true, position: pos, distance: 10, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, formatter: text },
        data: [{ coord: [D.jahre[i], ys[i]] }] }; };
    const L = (id, ys, color, name, extra) => Object.assign({ id, name, type: 'line', showSymbol: false, data: P(ys), z: 5,
      lineStyle: { color, width: 3.2 }, itemStyle: { color }, animationDuration: 1600 }, extra || {});
    const series = [
      L('base', D.baeume_rest, '#7fbf8c', 'nur Bäume', { lineStyle: { color: '#7fbf8c', width: 2.4, type: [8, 6] } }),
      L('g20', T.g20.rest, '#f0b04a', 'Wachstum ≤ 20 %/a',
        { markPoint: peak(T.g20.rest, '#f0b04a', `Spitze ${ecNum(Math.max(...T.g20.rest) / 1000, 2)} K`, 'top') })];
    if (k >= 2) series.push(L('frei', T.frei.rest, '#3fd0b0', 'ohne Wachstumsgrenze',
      { lineStyle: { color: '#3fd0b0', width: 3.4 }, markPoint: peak(T.frei.rest, '#3fd0b0', `${ecNum(Math.max(...T.frei.rest) / 1000, 2)} K`, 'top') }));
    return {
      animationDurationUpdate: 900,
      title: { text: 'Erwärmung über 1,5 °C [K]', left: 70, top: 0, textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
      grid: { left: 70, right: 24, top: 64, bottom: 40 },
      legend: { orient: 'vertical', right: 24, top: 60, itemGap: 12, itemWidth: 28, icon: 'path://M0,4 H28 V7 H0 Z',
                textStyle: { color: '#d6dbd6', fontFamily: EC.font, fontSize: 19 }, data: series.map(s => s.name) },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: 350, interval: 100, axisLine: { lineStyle: { color: '#4a524d' } },   // data in mK, read in K
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, formatter: v => v ? ecNum(v / 1000, 1) : '0' }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  }
};
/* a small dark chart beside the DAC map (result of the optimisation), from deck/chart_data/zeitpfade.json
   (key dac); line names at the line ends */
function ecDacSmall(title, yMax, yFmt, lines) {
  return { steps: 0, option() {
    const D = window.ZEIT, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const series = lines(D).map(([id, ys, color, name, dash, area]) => ({ id, type: 'line', showSymbol: false, data: P(ys), z: area ? 4 : 5,
      lineStyle: { color, width: dash ? 2.4 : 3.2, type: dash || 'solid' }, itemStyle: { color }, animationDuration: 1400,
      areaStyle: area ? { color, opacity: .28 } : undefined,
      endLabel: { show: true, formatter: name, color, fontFamily: EC.font, fontSize: 18, fontWeight: 600, distance: 8 }, labelLayout: { moveOverlap: 'shiftY' } }));
    return {
      title: { text: title, left: 60, top: 0, textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
      grid: { left: 60, right: 150, top: 42, bottom: 32 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: yMax, interval: yMax / 4, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18, formatter: yFmt }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  } };
}
const kOf = v => v ? ecNum(v / 1000, 1) : '0';   // data in mK, read in K
/* result of the optimisation: warming above 1.5 °C, trees alone and with DAC */
const EC_DACTEMP_BASE = ecDacSmall('Erwärmung über 1,5 °C [K]', 400, kOf, D => [
  ['b', D.baeume_rest, '#7fbf8c', 'nur Bäume', [8, 6]], ['d', D.dac.opt_20.temp, '#ff5a4f', '+ DAC', null, true]]);
// the two numbers of the slide named in the chart: the peak that stays, the year back at 1.5 °C
const EC_DACTEMP = { steps: 0, option() {
  const o = EC_DACTEMP_BASE.option(), D = window.ZEIT, d = D.dac.opt_20, t = d.temp, ip = t.indexOf(Math.max(...t));
  o.series[1].markPoint = { silent: true, symbol: 'circle', symbolSize: 10, itemStyle: { color: '#ff5a4f', borderColor: '#14181a', borderWidth: 2 },
    label: { show: true, color: '#f2ede2', fontFamily: EC.font, fontSize: 18, fontWeight: 600, distance: 8 },
    data: [{ coord: [D.jahre[ip], t[ip]], label: { position: 'top', formatter: `Spitze ${D.jahre[ip]}: ${ecNum(t[ip] / 1000, 2)} K` } },
           { coord: [d.ab, 0], label: { show: false } }] };   // the year stands large above the chart
  return o; } };
/* the lever: world capacity of the optimisation at faster growth limits and without one, and the warming above
   1.5 °C that follows (two charts, one above the other) */
function ecDacTempo(title, key, yMax, yFmt, trees) {
  return { steps: 1, option(k) {   // click 0: the 20 %/a case alone; click 1: the faster ones beside it
    const D = window.ZEIT, C = D.dac, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const L = (id, ys, color, name, w, dash) => ({ id, name, type: 'line', showSymbol: false, data: P(ys), z: 5, lineStyle: { color, width: w || 3, type: dash || 'solid' },
      itemStyle: { color }, animationDuration: 1600,
      endLabel: { show: true, formatter: name, color, fontFamily: EC.font, fontSize: 18, fontWeight: 600, distance: 10 }, labelLayout: { moveOverlap: 'shiftY' } });
    const series = [L('g20', C.opt_20[key], '#f0b04a', '≤ 20 %/a', 3.4)];
    if (k >= 1) series.push(L('g30', C.opt_30[key], '#e0903e', '≤ 30 %/a'), L('g50', C.opt_50[key], '#cc6f34', '≤ 50 %/a'),
                            L('frei', C.opt_frei[key], '#3fd0b0', 'ohne Grenze', 3.4));
    // the capacity paths all fall back towards zero by 2100: named in a legend in the right margin instead
    if (!trees) for (const x of series) x.endLabel.show = false;
    if (trees) {   // the warming paths all end at 1.5 °C: their names stand on the capacity chart above, in the same colours
      for (const x of series) x.endLabel.show = false;
      const peak = (x, ys, pos, off) => { const i = ys.indexOf(Math.max(...ys));
        x.markPoint = { silent: true, symbol: 'circle', symbolSize: 10, itemStyle: { color: x.lineStyle.color, borderColor: '#14181a', borderWidth: 2 },
          label: { show: true, position: pos, distance: 8, offset: off || [0, 0], color: x.lineStyle.color, fontFamily: EC.font, fontSize: 18, fontWeight: 600,
                   formatter: `Spitze ${ecNum(ys[i] / 1000, 2)} K` }, data: [{ coord: [D.jahre[i], ys[i]] }] }; };
      peak(series[0], C.opt_20[key], 'top');
      if (k >= 1) peak(series[3], C.opt_frei[key], 'right', [2, -16]);   // in the gap between the cyan and the orange paths
      series.unshift(L('b', D.baeume_rest, '#7fbf8c', 'nur Bäume', 2.4, [8, 6]));
    }
    return {
      title: { text: title, left: 60, top: 0, textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
      legend: trees ? undefined : { orient: 'vertical', right: 0, top: 44, itemGap: 10, itemWidth: 26, icon: 'path://M0,4 H28 V7 H0 Z',
                textStyle: { color: '#d6dbd6', fontFamily: EC.font, fontSize: 18 }, data: series.map(s => s.name) },
      grid: { left: 60, right: 150, top: 40, bottom: 34 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: yMax, interval: yMax / 4, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18, formatter: yFmt }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  } };
}
const EC_DACTEMPO = ecDacTempo('Kapazität weltweit [Gt CO₂/a]', 'w', 80, v => String(v), false);
const EC_DACTEMPO_T = ecDacTempo('Erwärmung über 1,5 °C [K]', 'temp', 400, kOf, true);
/* costs of the DAC path after the fact (key kosten_pfad): median per year with the optimistic-pessimistic band;
   then the explicit fossil subsidies and the EU-27 GDP as reference lines, in trillion EUR per year */
const EC_KOSTEN = {
  steps: 2,
  option(k) {
    const D = window.ZEIT, K = D.kosten_pfad, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const lo = K.optimistisch.je_jahr_bio, hi = K.pessimistisch.je_jahr_bio;
    const ref = (v, name, color, show) => ({ yAxis: v, lineStyle: { color, width: 2.6, type: [8, 6], opacity: show ? 1 : 0 },
      label: { show, position: 'insideStartTop', distance: 6, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, formatter: name } });
    const series = [
      { id: 'lo', type: 'line', stack: 'band', data: P(lo), showSymbol: false, lineStyle: { opacity: 0 }, silent: true, animationDuration: 1600 },
      { id: 'band', type: 'line', stack: 'band', data: P(hi.map((v, i) => v - lo[i])), showSymbol: false, silent: true,
        lineStyle: { opacity: 0 }, areaStyle: { color: '#ff5a4f', opacity: .22 }, animationDuration: 1600 },
      { id: 'med', type: 'line', data: P(K.median.je_jahr_bio), showSymbol: false, z: 5, animationDuration: 1600,
        lineStyle: { color: '#ff5a4f', width: 3.4 }, itemStyle: { color: '#ff5a4f' },
        endLabel: { show: true, formatter: 'DAC', color: '#ff5a4f', fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 10 },
        markLine: { silent: true, symbol: 'none', animationDuration: 700, data: [
          ref(K.fossil_subv_bio, `fossile Subventionen: ${ecNum(K.fossil_subv_bio, 2)}`, '#f0b04a', k >= 1),
          ref(K.eu27_bip_bio, `BIP der EU-27: ${ecNum(K.eu27_bip_bio, 1)}`, '#9fc4e8', k >= 2)] } }];
    return {
      animationDurationUpdate: 700,
      title: { text: 'Kosten des DAC-Pfads [Bio. € pro Jahr]', left: 70, top: 0, textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
      grid: { left: 70, right: 70, top: 56, bottom: 40 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: 25, interval: 5, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, formatter: v => String(v) }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  }
};
/* the vegan world from 2026 by cause (key vegan.beitraege, mK, < 0 = cooler): cooling stacked above zero,
   warming below, the net as a line; built up in steps */
const EC_VEGAN = {
  steps: 3,
  option(k) {
    const D = window.ZEIT, B = D.vegan.beitraege, P = ys => D.jahre.map((y, i) => [y, -ys[i]]);
    const co2 = B.co2_hof.map((v, i) => v + B.co2_entwaldung[i]);
    const A = (id, ys, color, name, stack, show) => ({ id, name, type: 'line', stack, data: P(show ? ys : ys.map(() => 0)), showSymbol: false,
      lineStyle: { width: 0 }, areaStyle: { color, opacity: show ? .85 : 0 }, itemStyle: { color }, animationDuration: 1400, z: 3 });
    const series = [
      A('ch4', B.ch4_tier, '#4f9fc7', 'Methan der Tierhaltung', 'kuehl', true),
      A('n2o', B.n2o_vermieden, '#86c6e4', 'Lachgas: Tierhaltung, Futteranbau', 'kuehl', k >= 1),
      A('co2', co2, '#c3e3f2', 'CO₂: Futteranbau, Entwaldung', 'kuehl', k >= 1),
      A('wco2', B.wald_co2, '#5fae76', 'Wald auf freier Fläche: CO₂', 'kuehl', k >= 2),
      A('ers', B.ersatz, '#e0903e', 'Ersatzprodukte', 'waerm', k >= 2),
      A('alb', B.wald_albedo, '#d0644a', 'Wald auf freier Fläche: Albedo', 'waerm', k >= 2),
      { id: 'net', name: 'netto', type: 'line', data: P(B.netto), showSymbol: false, z: 6,
        lineStyle: { color: '#f2ede2', width: 3.4, opacity: k >= 3 ? 1 : 0 }, itemStyle: { color: '#f2ede2' }, animationDuration: 1200,
        endLabel: { show: k >= 3, formatter: 'netto', color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 8 } }];
    // the two large bands named inside them, where they are widest
    const band = (x, base, ys, year, text) => { const i = D.jahre.indexOf(year);
      x.markPoint = { silent: true, symbol: 'circle', symbolSize: 0, data: [{ coord: [year, base[i] - ys[i] / 2] }],
        label: { show: true, position: 'inside', color: '#0f2430', fontFamily: EC.font, fontSize: 19, fontWeight: 600, formatter: text } }; };
    const zero = B.ch4_tier.map(() => 0);
    band(series[0], zero, B.ch4_tier, 2072, 'Methan der Tierhaltung');
    if (k >= 1) band(series[1], B.ch4_tier.map(v => -v), B.n2o_vermieden, 2090, 'Lachgas');
    return {
      animationDurationUpdate: 900,
      title: { text: 'Kühlung gegenüber Very Low [K]', left: 70, top: 0, textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
      grid: { left: 70, right: 84, top: 56, bottom: 40 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: -50, max: 300, interval: 50, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, formatter: v => v ? ecNum(v / 1000, 2) : '0' },
                      splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  }
};
/* the vegan world without DAC: warming above 1.5 °C after the trees, with the vegan world, and for comparison
   with DAC at 20 %/a (mK, read in K) */
const EC_VEGAN_LUECKE = {
  steps: 2,
  option(k) {
    const D = window.ZEIT, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const end = (text, color) => ({ show: true, formatter: text, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 10 });
    const peak = (ys, color, text) => { const i = ys.indexOf(Math.max(...ys));
      return { silent: true, symbol: 'circle', symbolSize: 11, itemStyle: { color, borderColor: '#14181a', borderWidth: 2 },
        label: { show: true, position: 'top', distance: 10, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, formatter: text },
        data: [{ coord: [D.jahre[i], ys[i]] }] }; };
    const v = D.vegan.gap, iv = v.findIndex((x, i) => i > v.indexOf(Math.max(...v)) && x <= 0);
    const series = [
      { id: 'b', type: 'line', data: P(D.baeume_rest), showSymbol: false, z: 4, lineStyle: { color: '#7fbf8c', width: 2.6, type: [8, 6] },
        itemStyle: { color: '#7fbf8c' }, endLabel: end('nur Bäume', '#7fbf8c'), animationDuration: 1200,
        markPoint: peak(D.baeume_rest, '#7fbf8c', `${ecNum(Math.max(...D.baeume_rest) / 1000, 2)} K`) }];
    if (k >= 1) series.push({ id: 'v', type: 'line', data: P(v), showSymbol: false, z: 5, lineStyle: { color: '#7fd0e0', width: 3.4 },
      areaStyle: { color: '#7fd0e0', opacity: .25 }, itemStyle: { color: '#7fd0e0' }, animationDuration: 1600,
      markPoint: { silent: true, symbol: 'circle', symbolSize: 11, itemStyle: { color: '#7fd0e0', borderColor: '#14181a', borderWidth: 2 },
        label: { show: true, distance: 10, color: '#7fd0e0', fontFamily: EC.font, fontSize: 19, fontWeight: 600 },
        data: [{ coord: [D.jahre[v.indexOf(Math.max(...v))], Math.max(...v)], label: { position: 'top', formatter: `${ecNum(Math.max(...v) / 1000, 2)} K` } },
               { coord: [D.jahre[iv], 0], label: { position: 'insideBottomLeft', offset: [14, -16], formatter: `ab ${D.jahre[iv]}` } }] } });
    if (k >= 2) series.push({ id: 'd', type: 'line', data: P(D.dac.opt_20.temp), showSymbol: false, z: 4, lineStyle: { color: '#ff5a4f', width: 2.6 },
      itemStyle: { color: '#ff5a4f' }, animationDuration: 1200 });   // named in the table beside the chart
    return {
      animationDurationUpdate: 900,
      title: { text: 'Erwärmung über 1,5 °C [K]', left: 70, top: 0, textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
      grid: { left: 70, right: 130, top: 56, bottom: 40 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: 400, interval: 100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, formatter: kOf }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  }
};
/* chapter 5 anchor: the warming above 1.5 °C after the trees, the same chart at the same place on four slides
   (phase 0 DAC model, 1 result, 3 pace, 2 vegan world, in this order). What stood on the slide before stands again
   without any entrance (lines and their marks); only the lines a slide adds are drawn in. On the vegan slide the
   DAC lines step back and the vegan curve is named at itself, so the legend stays as on the pace slide. */
const TEMPO_COL = { g30: '#f5894a', g50: '#f2b04b', frei: '#ff9a8f' };   // growth limits, the same in the anchor and the capacity chart
function ecAnker(phase) {
  // clicks the chart itself uses: the faster growth limits come on click 1 (pace), the vegan curve on click 2
  return { steps: { 0: 0, 1: 0, 2: 2, 3: 1 }[phase], option(k) {
    const D = window.ZEIT, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const b = D.baeume_rest, d = D.dac.opt_20.temp, f = D.dac.opt_frei.temp, t30 = D.dac.opt_30.temp, t50 = D.dac.opt_50.temp, v = D.vegan.gap;
    const ib = b.indexOf(Math.max(...b)), iff = f.indexOf(Math.max(...f)), iv = v.indexOf(Math.max(...v));
    // the order of the slides: which lines a phase inherits (stand still) and which it draws in
    const order = [0, 1, 3, 2], rank = order.indexOf(phase);
    const born = { b: 0, d: 1, t30: 3, t50: 3, f: 3, v: 2 };                     // the phase a line first appears in
    const has = id => order.indexOf(born[id]) < rank || (born[id] === phase && (id === 'v' ? k >= 2 : ['t30', 't50', 'f'].includes(id) ? k >= 1 : true));
    const isNew = id => born[id] === phase;
    // inherited lines and marks: animation false; new ones leave it unset and follow the deck, which animates only
    // the click that brings them (a series' own `animation: true` would override that and replay on every click)
    const dot = (color, data, anim, dim) => ({ silent: true, symbol: 'circle', symbolSize: 11, animation: anim ? undefined : false,
      itemStyle: { color, borderColor: '#14181a', borderWidth: 2, opacity: dim ? .35 : 1 },
      label: { show: true, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 9, opacity: dim ? .45 : 1 }, data });
    const L = (id, ys, color, name, o) => {
      const dim = phase === 2 && !['b', 'v'].includes(id);
      return Object.assign({ id, name, type: 'line', data: P(ys), showSymbol: false, z: 5, animation: isNew(id) ? undefined : false, animationDuration: 1600,
        lineStyle: Object.assign({ color, width: 3.2, opacity: dim ? .35 : 1 }, o.line || {}), itemStyle: { color },
        markPoint: o.mark ? dot(color, o.mark, isNew(id), dim) : undefined }, o.extra || {}); };
    const series = [];
    if (has('b')) series.push(L('b', b, '#7fbf8c', 'Bäume', { line: { width: 2.6, type: [8, 6] },
      mark: [{ coord: [D.jahre[ib], b[ib]], label: { position: 'top', formatter: `Spitze ${D.jahre[ib]}: ${ecNum(b[ib] / 1000, 2)} K` } }] }));
    if (has('d')) series.push(L('d', d, '#ff5a4f', 'DAC 20 %/a', {
      mark: [{ coord: [D.dac.opt_20.ab, 0], label: { position: 'right', offset: [4, -18], formatter: `1,5 °C ab ${D.dac.opt_20.ab}` } }] }));
    if (has('t30')) series.push(L('t30', t30, TEMPO_COL.g30, '30 %/a', {}), L('t50', t50, TEMPO_COL.g50, '50 %/a', {}));
    if (has('f')) series.push(L('f', f, TEMPO_COL.frei, 'unbegrenzt', { line: { width: 2.6, type: [4, 5] },
      mark: [{ coord: [D.jahre[iff], f[iff]], label: { position: 'right', offset: [2, -16], formatter: `${ecNum(f[iff] / 1000, 2)} K` } }] }));
    if (has('v')) series.push(L('v', v, '#7fd0e0', 'vegan', { line: { width: 3.4 }, extra: { areaStyle: { color: '#7fd0e0', opacity: .22 } },
      mark: [{ coord: [D.jahre[iv], v[iv]], label: { position: 'top', offset: [34, 0], formatter: `vegan: Spitze ${ecNum(v[iv] / 1000, 2)} K` } },
             { coord: [D.vegan.ohne_dac.ab, 0], label: { position: 'top', offset: [16, 0], formatter: `ab ${D.vegan.ohne_dac.ab}` } }] }));
    return {
      animationDurationUpdate: 800,
      title: { text: 'Erwärmung über 1,5 °C [K]', left: 70, top: 0, textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
      legend: { left: 66, top: 34, itemGap: 12, itemWidth: 22, icon: 'path://M0,4 H28 V7 H0 Z', textStyle: { color: '#d6dbd6', fontFamily: EC.font, fontSize: 18 },
                data: series.filter(x => x.id !== 'v').map(x => x.name) },
      grid: { left: 70, right: 24, top: 92, bottom: 40 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: 400, interval: 100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, formatter: kOf }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  } };
}
const EC_ANKER0 = ecAnker(0), EC_ANKER1 = ecAnker(1), EC_ANKER2 = ecAnker(2), EC_ANKER3 = ecAnker(3);
/* the pace slide, right: world capacity per growth limit, in the anchor's colours; click 1 adds the faster ones */
const EC_TEMPOKAP = { steps: 1, option(k) {
  const D = window.ZEIT, C = D.dac, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
  const L = (id, ys, color, name, dash) => ({ id, name, type: 'line', showSymbol: false, data: P(ys), z: 5, animationDuration: 1400,
    lineStyle: { color, width: 3, type: dash || 'solid' }, itemStyle: { color } });
  const series = [L('g20', C.opt_20.w, '#ff5a4f', '20 %/a')];
  if (k >= 1) series.push(L('g30', C.opt_30.w, TEMPO_COL.g30, '30 %/a'), L('g50', C.opt_50.w, TEMPO_COL.g50, '50 %/a'), L('frei', C.opt_frei.w, TEMPO_COL.frei, 'unbegrenzt', [4, 5]));
  return {
    legend: { left: 56, top: 0, itemGap: 14, itemWidth: 24, icon: 'path://M0,4 H28 V7 H0 Z', textStyle: { color: '#d6dbd6', fontFamily: EC.font, fontSize: 18 }, data: series.map(x => x.name) },
    grid: { left: 56, right: 16, top: 40, bottom: 32 },
    xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                    axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
    yAxis: ecAxis({ type: 'value', min: 0, max: 80, interval: 20,
                    axisLine: { lineStyle: { color: '#4a524d' } }, axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18 }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
    series };
} };
/* why the peak stays: world capacity at 20 %/a, the year of the peak marked */
const EC_ANKERKAP = { steps: 0, option() {
  const o = ecDacSmall('Kapazität weltweit [Gt CO₂/a]', 60, v => String(v), D => [['w', D.dac.opt_20.w, '#ff5a4f', '20 %/a', null, true]]).option();
  const D = window.ZEIT, w = D.dac.opt_20.w, i = D.jahre.indexOf(2048);
  o.series[0].markPoint = { silent: true, symbol: 'circle', symbolSize: 10, itemStyle: { color: '#f2ede2', borderColor: '#14181a', borderWidth: 2 },
    label: { show: true, position: 'top', distance: 10, offset: [10, -58], color: '#f2ede2', fontFamily: EC.font, fontSize: 18, fontWeight: 600, formatter: `Spitze 2048: erst ${ecNum(w[i], 1)} Gt/a` },
    data: [{ coord: [2048, w[i]] }] };
  return o; } };
const EC_CHARTS = { temperatur: EC_TEMPERATURE, entnahme: EC_REMOVAL, entnahmebalken: EC_REMOVAL_BARS, luecke: EC_GAP, tempsum: EC_TEMPSUM, lueckeend: EC_GAP_END, zeit: EC_ZEIT, tempo: EC_TEMPO, dactemp: EC_DACTEMP, dactempo: EC_DACTEMPO, dactempot: EC_DACTEMPO_T, kosten: EC_KOSTEN, vegan: EC_VEGAN, veganluecke: EC_VEGAN_LUECKE, anker0: EC_ANKER0, anker1: EC_ANKER1, anker2: EC_ANKER2, anker3: EC_ANKER3, tempokap: EC_TEMPOKAP, ankerkap: EC_ANKERKAP };

class EChart {
  constructor(host) {
    this.spec = EC_CHARTS[host.dataset.ec];
    this.nSteps = this.spec ? this.spec.steps : 0;
    if (!this.spec || !window.echarts || !window.CMIP7) { host.textContent = 'Diagramm fehlt (echarts / data/cmip7.js).'; return; }
    this.host = host;
    this.chart = echarts.init(host, null, { renderer: 'svg', width: host.clientWidth || 1400, height: host.clientHeight || 560 });
    this.k = null;
    this.final(this.nSteps);
    // the box settles only after fonts and formulas are laid out
    // (its first call comes when the slide is first drawn; a resize to the same size would cut the entrance short)
    new ResizeObserver(() => {
      if (!host.clientWidth || !host.clientHeight) return;
      if (host.clientWidth === this.chart.getWidth() && host.clientHeight === this.chart.getHeight()) return;
      this.chart.resize({ width: host.clientWidth, height: host.clientHeight });
      if (this.spec.unitRange) this.spec.pxPerUnit = (host.clientHeight - this.spec.unitRange[1]) / this.spec.unitRange[0];
      this.final(this.k ?? this.nSteps);   // a resize stops a running entrance part-way: draw the whole click instead
    }).observe(host);
  }
  set(k, animate, fresh) {
    if (!this.chart) return;
    k = Math.max(0, Math.min(k, this.nSteps));
    if (fresh) this.chart.clear();
    const opt = this.spec.option(k);
    opt.animation = animate && !this.spec.still;
    this.chart.setOption(opt, { replaceMerge: ['series'] });
    this.k = k;
  }
  play(k) { this.set(k, true, k === 0 || this.k === null || k < this.k); }
  final(k) { this.set(k < 0 ? 0 : k, false, true); }
}

/* ===========================================================
   MODEL FIGURES IN ECHARTS
   window.ECDATA (data/ec_charts.js, deck/mpl_to_echarts.py) holds
   every matplotlib figure of the talk in data coordinates: axes
   with limits and ticks, lines, bars, areas, points, texts, map
   cells, legends. MplChart rebuilds it as an ECharts option, one
   grid per axes at the same place as in the figure, and keeps the
   click interface of the deck (nSteps, play(k), final(k)):
     data-slot-steps="0,1,…"  a click per panel (reading order)
     data-stops="auto"        a single panel, category by category
   =========================================================== */
const MPL_FONT = "Arial, 'Helvetica Neue', Helvetica, sans-serif";   // the figures' own face: layout stays as in matplotlib
const MPL_SERIF = "Literata, Georgia, serif";
const mplNum = v => {
  if (v === null || v === undefined || !isFinite(v)) return '–';
  const a = Math.abs(v), d = a >= 100 ? 0 : a >= 10 ? 1 : a >= 1 ? 2 : 3;
  return v.toLocaleString('de-DE', { maximumFractionDigits: d });
};
const mplPatterns = {};
function mplHatch(h, color, s) {
  // a tile with the matplotlib hatch, used as pattern fill (works in both renderers)
  const key = h + color + s.toFixed(2);
  if (mplPatterns[key]) return mplPatterns[key];
  const n = Math.max(1, h.length), size = Math.max(4, 160 / (6 * n) * s), c = document.createElement('canvas');
  c.width = c.height = Math.round(size * 2);
  const g = c.getContext('2d'); g.strokeStyle = color; g.lineWidth = Math.max(1, 2.2 * s * 2); g.scale(2, 2);
  const L = (x0, y0, x1, y1) => { g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); };
  const ch = h[0];
  if (ch === '/' || ch === 'x' || ch === 'X') { L(0, size, size, 0); L(-size / 2, size / 2, size / 2, -size / 2); L(size / 2, size * 1.5, size * 1.5, size / 2); }
  if (ch === '\\' || ch === 'x' || ch === 'X') { L(0, 0, size, size); L(-size / 2, size / 2, size / 2, size * 1.5); L(size / 2, -size / 2, size * 1.5, size / 2); }
  if (ch === '-' || ch === '+') L(0, size / 2, size, size / 2);
  if (ch === '|' || ch === '+') L(size / 2, 0, size / 2, size);
  if (ch === '.' || ch === 'o') { g.fillStyle = color; g.beginPath(); g.arc(size / 2, size / 2, size / 6, 0, 7); g.fill(); }
  return (mplPatterns[key] = { image: c, repeat: 'repeat' });
}

/* matplotlib hatching as real lines, clipped to the shape (pattern fills do not
   reach custom shapes in every renderer) */
function mplHatchLines(h, color, s, clip, bbox) {
  const n = Math.max(1, h.length), step = Math.max(5, 160 / (6 * n) * s), lw = Math.max(1, 1.1 * s);
  const [x0, y0, x1, y1] = bbox, kids = [], ch = h[0], span = (x1 - x0) + (y1 - y0);
  const line = (ax, ay, bx, by) => kids.push({ type: 'line', shape: { x1: ax, y1: ay, x2: bx, y2: by }, style: { stroke: color, lineWidth: lw }, enterFrom: { style: { opacity: 0 } } });
  for (let t = -span; t <= span; t += step) {
    if (ch === '/' || ch === 'x' || ch === 'X') line(x0 + t, y1, x0 + t + (y1 - y0), y0);
    if (ch === '\\' || ch === 'x' || ch === 'X') line(x0 + t, y0, x0 + t + (y1 - y0), y1);
  }
  if (ch === '-' || ch === '+') for (let y = y0; y <= y1; y += step) line(x0, y, x1, y);
  if (ch === '|' || ch === '+') for (let x = x0; x <= x1; x += step) line(x, y0, x, y1);
  return { type: 'group', clipPath: clip, children: kids, silent: true };
}
const mplBox = pts => { let a = Infinity, b = Infinity, c = -Infinity, d = -Infinity; for (const [x, y] of pts) { a = Math.min(a, x); b = Math.min(b, y); c = Math.max(c, x); d = Math.max(d, y); } return [a, b, c, d]; };
const mplRgb = c => { if (!c) return null; const m = c.match(/^#(..)(..)(..)/); if (m) return [1, 2, 3].map(i => parseInt(m[i], 16)); const r = c.match(/rgba?\(([^)]+)\)/); return r ? r[1].split(',').slice(0, 3).map(Number) : null; };

/* ---------- maps: hexagon tiles and the deck's colour scales (nbs.map_fields) ---------- */
const mapHex = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const mapMix = (a, b, t) => { const p = mapHex(a), q = mapHex(b); return '#' + p.map((v, i) => Math.round(v + (q[i] - v) * t).toString(16).padStart(2, '0')).join(''); };
function mapPos(sc, v) {
  // where a value sits on its colour scale, 0..1; a diverging scale puts its middle stop at `mid`
  const [lo, hi] = sc.domain;
  let t = sc.mid !== undefined ? (v < sc.mid ? .5 * (v - lo) / (sc.mid - lo) : .5 + .5 * (v - sc.mid) / (hi - sc.mid)) : (v - lo) / (hi - lo);
  t = Math.max(0, Math.min(1, t));
  return sc.gamma ? Math.pow(t, sc.gamma) : t;   // gamma bends a sequential scale (nbs.map_fields.scale_t)
}
function mapAt(sc, t) {   // piecewise linear over evenly spaced stops
  const n = sc.stops.length - 1, k = Math.min(n - 1, Math.floor(t * n));
  return mapMix(sc.stops[k], sc.stops[k + 1], t * n - k);
}
const mapScale = (sc, v) => mapAt(sc, mapPos(sc, v));
/* A map cell's entrance: its colour runs along the scale from the neutral end (sequential: the paper, then the
   lightest stop; diverging: the middle) to its own value, every cell at the same pace, so low values settle
   first and high ones keep darkening. Keyframes for the cell's fill and the time that takes. */
const MAP_PACE = 1500;   // ms from the neutral end to the far end of the scale
function mapRun(sc, v) {
  const t = mapPos(sc, v), t0 = sc.mid !== undefined ? .5 : 0, span = Math.abs(t - t0) / (sc.mid !== undefined ? .5 : 1);
  const lead = sc.mid !== undefined ? 0 : 220, n = Math.max(1, Math.ceil(span * 6)), dur = lead + span * MAP_PACE;
  const frames = lead ? [{ percent: 0, style: { fill: MAP_PAPER } }] : [];
  for (let q = 0; q <= n; q++) frames.push({ percent: (lead + q / n * span * MAP_PACE) / Math.max(1, dur), style: { fill: mapAt(sc, t0 + (t - t0) * q / n) } });
  return { frames, dur };
}
const MAP_PAPER = '#f2ede2';
const mapFmt = (v, sc) => (sc.unit === '' ? String(Math.round(v)) : v.toLocaleString('de-DE', { maximumFractionDigits: Math.abs(v) >= 10 ? 0 : 2 }) + ' ' + sc.unit);

class MplChart {
  constructor(host) {
    this.host = host;
    this.d = window.ECDATA && window.ECDATA[host.dataset.chart];
    this.nSteps = 0;
    if (!this.d || !window.echarts) { host.textContent = `Abbildung ${host.dataset.chart} fehlt — scripts/export_html_v2.py ausführen.`; return; }
    const d = this.d;
    this.isMap = d.axes.some(a => a.map);
    this.mapSpec = window.MAPDATA && window.MAPDATA.maps[host.dataset.chart];
    this.mapAxes = []; this.cbarAxes = [];
    d.axes.forEach((a, i) => { if (a.map) (a.items.some(it => it.t === 'polyline') ? this.mapAxes : this.cbarAxes).push(i); });
    // panels in reading order; twins (same box) share their slot
    const order = d.axes.map((a, i) => ({ b: a.box, i })).sort((p, q) => Math.abs(p.b[1] - q.b[1]) > 0.03 ? p.b[1] - q.b[1] : p.b[0] - q.b[0]);
    const slots = []; this.slot = [];
    for (const { b, i } of order) {
      const twin = slots.findIndex(s => Math.abs(s[0] - b[0]) < .003 && Math.abs(s[1] - b[1]) < .003 && Math.abs(s[2] - b[2]) < .003);
      if (twin >= 0) this.slot[i] = twin; else { this.slot[i] = slots.length; slots.push(b); }
    }
    const given = (host.dataset.slotSteps || '').split(',').filter(s => s.trim() !== '').map(Number);
    this.slotStep = slots.map((_, k) => given[k] ?? 0);
    this.nSteps = Math.max(0, ...this.slotStep);
    if (host.dataset.stops === 'auto') {
      // category positions of the first panel, from its markers and bars
      const xs = [];
      for (const it of d.axes[0].items) {
        if (it.t === 'line' && it.mk) it.xy.forEach(p => p[0] !== null && xs.push(p[0]));
        if (it.t === 'bar') xs.push((it.r[0] + it.r[2]) / 2);
      }
      xs.sort((a, b) => a - b);
      const span = d.axes[0].x.max - d.axes[0].x.min, cl = [];
      for (const x of xs) if (!cl.length || x - cl[cl.length - 1][cl[cl.length - 1].length - 1] > 0.06 * span) cl.push([x]); else cl[cl.length - 1].push(x);
      const mid = cl.map(g => (g[0] + g[g.length - 1]) / 2), half = 0.04 * span;
      this.stops = mid.slice(0, -1).map(m => m + half).concat([Infinity]);
      this.nSteps = this.stops.length - 1;
    }
    // the figure keeps its aspect inside the slide's box
    this.inner = document.createElement('div');
    this.inner.style.cssText = 'position:absolute';
    host.appendChild(this.inner);
    this.size();
    const svg = !this.isMap || host.dataset.renderer === 'svg';
    this.chart = echarts.init(this.inner, null, svg ? { renderer: 'svg' } : { renderer: 'canvas', devicePixelRatio: 3 });
    this.k = null;
    this.timeLayer = this.mapSpec && this.mapSpec.panels[0].layers.find(L => L.frames);
    if (this.timeLayer) { this.year = this.timeLayer.years[0]; if (host.dataset.renderer !== 'svg') this.player(); }
    this.final(this.nSteps);
    new ResizeObserver(() => { if (this.size()) { this.chart.resize(); this.final(this.k ?? this.nSteps); } }).observe(host);
  }

  /* Maps with one frame per year (nbs.map_fields: "years" + "frames"): values glide between the years.
     A play button and a timeline under the map, as in woodway's TimeSlider: a full sweep takes 10 s,
     advanced per animation frame by elapsed time, so it moves continuously instead of in yearly jumps. */
  frameValue(L, j) {
    const y0 = L.years[0], n = L.years.length - 1, t = Math.max(0, Math.min(n, (this.year ?? y0) - y0));
    const k = Math.min(n - 1, Math.floor(t)), f = t - k;
    return L.frames[k][j] * (1 - f) + L.frames[k + 1][j] * f;
  }
  player() {
    const L = this.timeLayer, y0 = L.years[0], y1 = L.years[L.years.length - 1], perSec = (y1 - y0) / 10;
    const bar = document.createElement('div');
    bar.className = 'player';
    bar.innerHTML = `<button type="button" aria-label="Abspielen"><svg viewBox="0 0 24 24"><path class="i-play" d="M7 4.5v15l12-7.5z"/><g class="i-pause"><rect x="6" y="4.5" width="4" height="15" rx="1"/><rect x="14" y="4.5" width="4" height="15" rx="1"/></g></svg></button>
      <div class="track"><input type="range" min="${y0}" max="${y1}" step="1" value="${y0}" aria-label="Jahr"><div class="ticks">${[y0, 2050, 2075, 2100].map(y => `<span style="left:calc(7px + (100% - 14px) * ${(y - y0) / (y1 - y0)})">${y}</span>`).join('')}</div></div>
      <span class="yr">${y0}</span>`;
    this.host.after(bar);
    const btn = bar.querySelector('button'), range = bar.querySelector('input'), label = bar.querySelector('.yr');
    let raf = null, last = null;
    const show = y => { this.setYear(y); range.value = Math.round(y); label.textContent = Math.round(y); };
    const stop = () => { if (raf) cancelAnimationFrame(raf); raf = null; last = null; bar.classList.remove('playing'); btn.setAttribute('aria-label', 'Abspielen'); };
    const tick = ts => {
      if (last === null) last = ts;
      const next = this.year + perSec * (ts - last) / 1000; last = ts;
      if (next >= y1) { show(y1); stop(); return; }
      show(next); raf = requestAnimationFrame(tick);
    };
    btn.addEventListener('click', () => {
      btn.blur();
      if (raf) { stop(); return; }
      if (this.year >= y1) show(y0);   // a finished sweep starts again
      bar.classList.add('playing'); btn.setAttribute('aria-label', 'Pause');
      raf = requestAnimationFrame(tick);
    });
    range.addEventListener('input', () => { stop(); show(+range.value); });
    range.addEventListener('change', () => range.blur());
    // leaving the slide: stop and go back to the first year
    const slide = this.host.closest('.slide');
    if (slide) new MutationObserver(() => { if (!slide.classList.contains('active')) { stop(); if (this.year !== y0) show(y0); } })
      .observe(slide, { attributes: true, attributeFilter: ['class'] });
  }
  setYear(y) {
    this.year = y;
    if (!this.chart || this.k === null) return;
    const i = this.mapAxes[0], out = [];
    this.hexSeries(out, n => `a${i}_${n}`, i, this.mapSpec.panels[0], 0, this.s);
    out.forEach(x => { x.animation = false; });
    if (this.siteSeries) out.push(this.siteSeries());
    this.chart.setOption({ series: out });
  }
  size() {
    const W0 = this.host.clientWidth, H0 = this.host.clientHeight;
    if (!W0 || !H0) return false;
    const r = this.d.w / this.d.h, W = Math.min(W0, H0 * r), H = W / r;
    // centred again on every call: the host can change height without the figure changing size
    // (a map's player inserted below it takes room), and a stale offset pushes the figure over it
    const place = () => Object.assign(this.inner.style, { left: Math.round((W0 - this.W) / 2) + 'px', top: Math.round((H0 - this.H) / 2) + 'px' });
    if (this.W && Math.abs(this.W - W) < 1 && Math.abs(this.H - H) < 1) { place(); return false; }
    this.W = Math.round(W); this.H = Math.round(H); this.s = this.W / this.d.w;
    Object.assign(this.inner.style, { width: this.W + 'px', height: this.H + 'px' });
    place();
    return true;
  }
  visible(i, k) {
    if (this.stops) return k >= 0;
    return this.slotStep[this.slot[i]] <= k;
  }
  fresh(i, k) { return !this.stops && this.slotStep[this.slot[i]] === k; }

  option(k, animate) {
    const d = this.d, s = this.s, W = this.W, H = this.H;
    this.texs = [];
    const grid = [], xAxis = [], yAxis = [], series = [], graphic = [];
    const stopX = this.stops ? this.stops[Math.max(0, Math.min(k, this.stops.length - 1))] : Infinity;
    const font = (it, base) => ({ fontFamily: it.serif ? MPL_SERIF : MPL_FONT, fontSize: (it.fs || base) * s,
                                  fontWeight: it.b ? 600 : 400, fontStyle: it.i ? 'italic' : 'normal' });
    const legendLabel = {};
    for (const lg of d.legends) for (const e of lg.entries) if (e.k === 'patch' && e.col) legendLabel[e.col] = e.s;
    // within one click the panels follow each other
    const newSlots = [...new Set(d.axes.map((a, i) => this.fresh(i, k) ? this.slot[i] : -1).filter(v => v >= 0))].sort((a, b) => a - b);
    const t0 = i => (this.fresh(i, k) ? newSlots.indexOf(this.slot[i]) : 0) * 450;
    const axisFor = (a, which, i, show) => {
      // matplotlib writes 1.75; the talk is German: 1,75 (years and integers stay as they are)
      const A = a[which], labels = Object.fromEntries(A.ticks.map(t => [t[0], /^[−-]?\d+\.\d+$/.test(t[1]) ? t[1].replace('.', ',') : t[1]]));
      const vals = A.ticks.map(t => t[0]);
      return {
        gridIndex: i, type: A.scale === 'log' ? 'log' : 'value', min: A.min, max: A.max, inverse: A.inv, show: show && a.on,
        position: A.pos === 'right' ? 'right' : A.pos === 'top' ? 'top' : which === 'x' ? 'bottom' : 'left',
        axisLine: { show: !!A.line, onZero: false, lineStyle: { color: A.line || '#8a918c', width: Math.max(1, 1.1 * s) } },
        axisTick: { show: A.tick, customValues: vals, length: 5 * s, lineStyle: { color: A.line || '#8a918c' } },
        axisLabel: { show: vals.length > 0, customValues: vals, formatter: v => labels[v] ?? labels[Math.round(v * 1e6) / 1e6] ?? '',
                     color: A.lc || '#5d665f', fontFamily: MPL_FONT, fontSize: (A.lfs || 17) * s, margin: 7 * s, hideOverlap: false },
        splitLine: { show: !!A.grid, lineStyle: { color: A.grid ? A.grid.c : '#ddd', width: A.grid ? Math.max(.6, A.grid.lw * s) : 1 } },
        splitArea: { show: false }, silent: true, animation: false
      };
    };
    d.axes.forEach((a, i) => {
      const show = this.visible(i, k), [bx, by, bw, bh] = a.box;
      grid.push({ left: bx * W, top: by * H, width: bw * W, height: bh * H, containLabel: false, show: false });
      xAxis.push(axisFor(a, 'x', i, show));
      yAxis.push(axisFor(a, 'y', i, show));
      if (!show) return;
      const base = t0(i), id = n => `a${i}_${n}`, Z = it => 2 + (it.z || 0);
      const inX = x => x <= stopX;
      if (a.bg) graphic.push({ id: id('bg'), type: 'rect', z: -1, shape: { x: bx * W, y: by * H, width: bw * W, height: bh * H }, style: { fill: a.bg }, silent: true });
      a.labels.forEach((t, j) => graphic.push(this.textEl(id('lab' + j), t, font, W, H)));
      const bars = [], cells = [];
      a.items.forEach((it, j) => {
        if (it.t === 'line') {
          const pts = it.xy.filter(p => p[0] === null || inX(p[0])).map(p => (p[0] === null || p[1] === null) ? [NaN, NaN] : p);
          if (!pts.length) return;
          const mk = it.mk, onlyMk = !it.lw;
          const sym = mk ? mk.sym : 'none';
          const site = a.map && mk && window.MAPDATA && it.xy.length === 1 && window.MAPDATA.sites.find(q => Math.abs(q.lon - it.xy[0][0]) < .3 && Math.abs(q.lat - it.xy[0][1]) < .3);
          const symStyle = site ? { color: site.color, borderColor: '#ffffff', borderWidth: 2.2 * s }
                         : mk ? { color: mk.fc || 'transparent', borderColor: mk.ec || mk.fc, borderWidth: (mk.ew || 0) * s } : { color: it.c };
          const dataPts = mk && mk.idx ? pts.map((p, q) => mk.idx.includes(q) ? { value: p } : { value: p, symbolSize: 0 }) : pts;
          series.push({
            id: id('l' + j), name: it.name || ' ', type: onlyMk ? 'scatter' : 'line', xAxisIndex: i, yAxisIndex: i, z: Z(it),
            data: dataPts, showSymbol: !!mk, symbol: sym, symbolSize: mk ? mk.size * s : 0, itemStyle: symStyle,
            lineStyle: { color: it.c, width: it.lw * s, type: it.dash ? it.dash.map(v => v * s) : 'solid', opacity: it.a ?? 1, cap: 'round' },
            connectNulls: false, clip: !it.noclip, smooth: false, emphasis: { disabled: true },
            animationDuration: onlyMk ? 500 : 1500, animationEasing: 'cubicInOut', animationDelay: base + (site ? 0 : onlyMk ? 900 : 0)
          });
        } else if (it.t === 'bar') {
          if (!inX(it.r[0])) return;
          bars.push(it);
        } else if (it.t === 'cells') {
          if (!this.mapSpec) cells.push(it);
        } else if (it.t === 'poly') {
          if (this.mapSpec && (this.cbarAxes.includes(i) || this.mapAxes.includes(i))) return;   // old colour-bar ends and hatching: the map layers draw their own
          const rings = it.pts.filter(r => r.length > 2);
          if (!rings.length) return;
          series.push({
            id: id('p' + j), type: 'custom', xAxisIndex: i, yAxisIndex: i, z: Z(it), silent: true, data: [0], clip: !a.map,
            renderItem: (p, api) => ({ type: 'group', children: rings.flatMap(r => {
              const pts = r.filter(q => q[0] !== null).map(q => api.coord(q));
              const el = [{ type: 'polygon', shape: { points: pts }, style: { fill: it.fc || 'none', opacity: (it.fa ?? 1) * (it.a ?? 1), stroke: it.ec || 'none', lineWidth: (it.ew || 0) * s } , enterFrom: { style: { opacity: 0 } } }];
              if (it.hatch) el.push(mplHatchLines(it.hatch, it.hc || '#000', s, { type: 'polygon', shape: { points: pts } }, mplBox(pts)));
              return el;
            }) }),
            animationDuration: 1500, animationEasing: 'cubicInOut', animationDelay: base + 200
          });
        } else if (it.t === 'polyline') {
          const pts = [];
          for (const r of it.lines) { for (const q of r) pts.push(q); pts.push([NaN, NaN]); }
          const quiet = this.mapSpec && a.map;
          series.push({ id: id('b' + j), type: 'line', xAxisIndex: i, yAxisIndex: i, z: quiet ? 12 : Z(it), silent: true, data: pts, showSymbol: false,
                        lineStyle: { color: quiet ? '#8f877a' : it.c, width: quiet ? Math.max(.6, .9 * s) : Math.max(.5, it.lw * s), opacity: quiet ? .75 : it.a ?? 1 },
                        connectNulls: false, animation: false, clip: true });
        } else if (it.t === 'points') {
          const pts = it.pts.filter(p => inX(p.x));
          series.push({ id: id('s' + j), name: it.name || ' ', type: 'scatter', xAxisIndex: i, yAxisIndex: i, z: Z(it), symbol: it.sym,
                        data: pts.map(p => ({ value: [p.x, p.y], symbolSize: p.s * s, itemStyle: { color: p.fc || 'transparent', borderColor: p.ec || p.fc, borderWidth: (it.ew || 0) * s, opacity: it.a ?? 1 } })),
                        animationDuration: 500, animationDelay: q => base + 900 + q * 40 });
        } else if (it.t === 'arrow') {
          series.push({ id: id('r' + j), type: 'custom', xAxisIndex: i, yAxisIndex: i, z: Z(it) + 5, silent: true, data: [0], clip: false,
            renderItem: (p, api) => {
              const [x0, y0] = api.coord(it.from), [x1, y1] = api.coord(it.to), ang = Math.atan2(y1 - y0, x1 - x0), L = 9 * s, w = 4.5 * s;
              return { type: 'group', children: [
                { type: 'line', shape: { x1: x0, y1: y0, x2: x1 - L * .6 * Math.cos(ang), y2: y1 - L * .6 * Math.sin(ang) }, style: { stroke: it.c, lineWidth: Math.max(1, it.lw * s) } },
                { type: 'polygon', shape: { points: [[x1, y1], [x1 - L * Math.cos(ang) - w * Math.sin(ang), y1 - L * Math.sin(ang) + w * Math.cos(ang)], [x1 - L * Math.cos(ang) + w * Math.sin(ang), y1 - L * Math.sin(ang) - w * Math.cos(ang)]] }, style: { fill: it.c } }] };
            }, animationDuration: 500, animationDelay: base + 1300 });
        }
      });
      if (bars.length) series.push(this.barSeries(id('bars'), i, bars, base, s));
      if (this.mapSpec && this.mapAxes.includes(i)) this.hexSeries(series, id, i, this.mapSpec.panels[this.mapAxes.indexOf(i)], base, s, animate && this.fresh(i, k));
      if (this.mapSpec && this.cbarAxes.includes(i)) this.colourBar(series, id, i, a, this.mapSpec.panels[this.cbarAxes.indexOf(i)], s);
      cells.forEach((c, q) => series.push(this.cellSeries(id('c' + q), i, a, c, base, s, legendLabel)));
      // texts in data coordinates, once their part of the chart is there; the three sites' labels come with
      // the map, and on a map played year by year their value follows the year (setYear)
      const sites = window.MAPDATA ? window.MAPDATA.sites : [];
      const textSeries = (sid, list, delay) => ({
        id: sid, type: 'scatter', xAxisIndex: i, yAxisIndex: i, z: 30, silent: true, clip: false, symbolSize: 0,
        data: list.map(t => ({ value: [t.x, t.y], label: { show: true, position: 'inside', formatter: t.s, color: t.c, align: t.al, ...subRich(t, font(t, 16)),
          verticalAlign: 'middle', rotate: t.rot || 0, lineHeight: (t.fs || 16) * s * 1.18, ...font(t, 16),
          backgroundColor: t.bg ? (t.bga < 1 ? `rgba(${parseInt(t.bg.slice(1, 3), 16)},${parseInt(t.bg.slice(3, 5), 16)},${parseInt(t.bg.slice(5, 7), 16)},${t.bga})` : t.bg) : 'transparent',
          // dark labels get a paper halo so they stay readable over lines and bars; light ones sit on colour and need none
          textBorderColor: 'rgba(242,237,226,.92)', textBorderWidth: t.bg || mapHex(t.c).reduce((q, v) => q + v, 0) > 560 ? 0 : 3.2 * s,
          padding: t.bg ? [2 * s, 4 * s] : 0, borderColor: t.ring || 'transparent', borderWidth: t.ring ? 1.6 * s : 0, borderRadius: t.ring ? 4 * s : 0 } })),
        animationDuration: 500, animationDelay: delay
      });
      const siteText = t => {
        const site = a.map && sites.find(q => t.s.trim().startsWith(q.name));
        if (!site) return null;
        let s2 = t.s;
        const L = this.mapSpec && this.mapAxes.includes(i) && this.mapSpec.panels[this.mapAxes.indexOf(i)].layers.find(l => l.frames);
        if (L) {   // the value of the site's cell in the year on show
          const g = this.mapSpec.panels[this.mapAxes.indexOf(i)].grid, r = Math.floor((g.lat0 - site.lat) / g.d), c = Math.floor((site.lon - g.lon0) / g.d);
          const j = L.cells.findIndex(q => q[0] === r && q[1] === c);
          if (j >= 0) s2 = site.name + (t.s.includes('\n') ? '\n' : ': ') + mapFmt(this.frameValue(L, j), window.MAPDATA.scales[L.scale]);
        }
        return { ...t, s: s2, c: '#1b2420', b: 1, bg: '#fbf8f1', bga: .94, ring: site.color };
      };
      // a formula symbol on its own goes over the chart in KaTeX, in the slides' formula face (placeTex)
      for (const t of a.texts) if (t.tex && inX(t.x) && window.katex) this.texs.push({ t, a, key: i + ':' + t.tex });
      const shown = a.texts.filter(t => inX(t.x) && !(t.tex && window.katex)), siteTexts = () => shown.map(siteText).filter(Boolean);
      const texts = shown.filter(t => !siteText(t));
      if (texts.length) series.push(textSeries(id('t'), texts, base + 1300));
      if (siteTexts().length) {
        series.push(textSeries(id('ts'), siteTexts(), base));
        if (this.timeLayer && this.mapAxes.includes(i)) this.siteSeries = () => ({ ...textSeries(id('ts'), siteTexts(), 0), animation: false });
      }
    });
    d.texts.forEach((t, j) => graphic.push(this.textEl(`ft${j}`, t, font, W, H)));
    d.legends.forEach((lg, j) => graphic.push(this.legendEl(`lg${j}`, lg, W, H, s)));
    return {
      // maps have more than ECharts' default 2000 shapes per series, above which it skips the entry animation
      animation: animate, animationThreshold: 100000, animationDurationUpdate: 600, grid, xAxis, yAxis, series, graphic,
      tooltip: { trigger: 'item', confine: true, backgroundColor: 'rgba(251,248,241,.97)', borderColor: '#d6ccb6', padding: [6, 10],
                 textStyle: { color: '#1b2420', fontFamily: MPL_FONT, fontSize: 14 }, extraCssText: 'box-shadow:0 6px 18px -8px rgba(40,34,20,.35);border-radius:6px;',
                 formatter: p => this.tip(p) }
    };
  }

  tip(p) {
    if (p.seriesType === 'custom') return p.data && p.data.tip ? p.data.tip : '';
    const v = Array.isArray(p.value) ? p.value : p.data && p.data.value;
    if (!v) return '';
    const x = v[0], y = v[1], xs = Number.isInteger(x) || Math.abs(x - Math.round(x)) < 1e-6 && Math.abs(x) > 1000 ? String(Math.round(x)) : mplNum(x);
    const name = (p.seriesName || '').trim();
    return `${name ? `<b>${name}</b><br>` : ''}${xs}: <b>${mplNum(y)}</b>`;
  }

  textEl(id, t, font, W, H) {
    const f = font(t, 16);
    const r = subRich(t, f);
    return { id, type: 'text', x: t.f[0] * W, y: t.f[1] * H, rotation: (t.rot || 0) * Math.PI / 180, silent: true, z: 40,
             style: { text: r.formatter || t.s, rich: r.rich, fill: t.c, textAlign: t.al, textVerticalAlign: 'middle', font: `${f.fontStyle} ${f.fontWeight} ${f.fontSize}px ${f.fontFamily}`, lineHeight: f.fontSize * 1.18 } };
  }

  legendEl(id, lg, W, H, s) {
    const children = [];
    for (const e0 of lg.entries) {
      const e = this.recolour(e0);
      const x = e.f[0] * W, y = e.f[1] * H, hl = lg.hl * s, pad = lg.pad * s, x1 = x - pad, x0 = x1 - hl;
      if (e.k === 'line') children.push({ type: 'line', shape: { x1: x0, y1: y, x2: x1, y2: y }, style: { stroke: e.col, lineWidth: Math.max(1.5, (e.lw || 2) * s), lineDash: e.dash ? e.dash.map(v => v * s) : null } });
      if (e.k === 'patch') {
        const h = lg.fs * s * .7, r = { x: x0, y: y - h / 2, width: hl, height: h };
        children.push({ type: 'rect', shape: r, style: { fill: e.col || 'none', opacity: e.a ?? 1, stroke: e.ec || null } });
        if (e.hatch) children.push(mplHatchLines(e.hatch, e.hc || '#000', s, { type: 'rect', shape: r }, [r.x, r.y, r.x + r.width, r.y + r.height]));
      }
      if (e.k === 'marker' || (e.k === 'line' && e.sym)) children.push({ type: 'circle', shape: { cx: (x0 + x1) / 2, cy: y, r: lg.fs * s * .3 }, style: { fill: e.col } });
      children.push({ type: 'text', x, y, style: { text: e.s, fill: e.c || '#1b2420', textVerticalAlign: 'middle', font: `400 ${lg.fs * s}px ${MPL_FONT}`, lineHeight: lg.fs * s * 1.15 } });
    }
    if (lg.title) children.push({ type: 'text', x: lg.title.f[0] * W, y: lg.title.f[1] * H, style: { text: lg.title.s, fill: lg.title.c, textAlign: lg.title.al, textVerticalAlign: 'middle', font: `600 ${lg.title.fs * s}px ${MPL_FONT}` } });
    return { id, type: 'group', silent: true, z: 40, children };
  }

  recolour(e) {
    // legend entries of a map name the category or mask they stand for: give them its new colour
    if (!this.mapSpec || e.k !== 'patch') return e;
    const first = e.s.split('\n')[0].replace(/,$/, '').trim().toLowerCase(), M = window.MAPDATA;
    for (const p of this.mapSpec.panels) for (const L of p.layers) {
      if (L.kind === 'cat') for (const c of M.categories[L.cats]) if (first.startsWith(c.label.toLowerCase().split(' (')[0].split(',')[0])) return { ...e, col: c.color, a: 1 };
      if ((L.kind === 'mask' || L.kind === 'hatch') && L.label && first.startsWith(L.label.toLowerCase().slice(0, 12)))
        return L.kind === 'hatch' ? { ...e, col: '#fbf8f1', hatch: '////', hc: L.color } : { ...e, col: L.color, a: 1 };
    }
    return e;
  }

  hexSeries(series, id, i, panel, base, s, enter) {
    // enter: the panel comes in with this click; its cells fade in along their colour scale (mapRun)
    // regular hexagons on a pixel lattice over the map; each takes the value of the data cell under its
    // centre. Hexes about as large as a cell, so the resolution stays that of the data, without the
    // stretching that cell-shaped hexes get where the map is not square in degrees (Europe maps).
    const M = window.MAPDATA, g = panel.grid, d = g.d, a = this.d.axes[i], W = this.W, H = this.H;
    const left = a.box[0] * W, top = a.box[1] * H, bw = a.box[2] * W, bh = a.box[3] * H;
    const { min: x0, max: x1 } = a.x, { min: y0, max: y1 } = a.y;
    const cw = bw * d / (x1 - x0), ch = bh * d / (y1 - y0), R = Math.sqrt(cw * ch / 2.598), hw = Math.sqrt(3) * R;
    const lattice = [];
    for (let j = 0, py = top; py <= top + bh + R; j++, py = top + j * 1.5 * R)
      for (let px = left + (j % 2 ? hw / 2 : 0); px <= left + bw + hw; px += hw)
        lattice.push([x0 + (px - left) / bw * (x1 - x0), y1 - (py - top) / bh * (y1 - y0)]);
    const pts = Array.from({ length: 6 }, (_, k) => [Math.cos(Math.PI / 180 * (60 * k - 90)), Math.sin(Math.PI / 180 * (60 * k - 90))]);
    const Rr = R + .45;   // a hair of overlap, no seams between tiles
    panel.layers.forEach((L, li) => {
      const look = new Map(L.cells.map((cell, j) => [cell[0] * g.nx + cell[1], j]));
      const items = [];
      for (const [lon, lat] of lattice) {
        const r = Math.floor((g.lat0 - lat) / d), c = Math.floor((lon - g.lon0) / d), j = look.get(r * g.nx + c);
        if (j === undefined) continue;
        const cell = L.cells[j];
        let col, tip = null, run = null;
        if (L.kind === 'mask') { col = L.color; tip = L.label || null; }
        else if (L.kind === 'hatch') col = L.color;
        else if (L.kind === 'cat') {
          const cat = M.categories[L.cats][cell[2]], share = cell.length > 3 ? cell[3] : 1;
          // intensity = free area; square root so thinly covered blocks still show their colour
          const f = L.cats === 'waldtyp' ? Math.sqrt(Math.min(1, share)) : L.cats === 'wirkung' ? Math.sqrt(Math.max(0, (share - .3) / .7)) : 1;
          const share2 = L.cats === 'umstieg' ? 1 : .32 + .68 * f;
          col = mapMix('#ddd6c7', cat.color, share2);
          if (enter) run = { dur: 220 + share2 * MAP_PACE, frames: [{ percent: 0, style: { fill: MAP_PAPER } }, { percent: .1, style: { fill: '#ddd6c7' } }, { percent: 1, style: { fill: col } }] };
          tip = cat.label + (L.cats === 'waldtyp' ? `<br>${Math.round(Math.min(1, share) * 30)}${share >= 1 ? '+' : ''} % der Landfläche wiederbewaldbar` : '');
        } else {
          const sc = M.scales[L.scale], v = L.frames ? this.frameValue(L, j) : cell[2];
          col = mapScale(sc, v); tip = mapFmt(v, sc) + (L.frames ? ` (${Math.round(this.year ?? L.years[0])})` : '');
          if (enter) run = mapRun(sc, v);
        }
        const it = tip ? { value: [lon, lat], col, tip: `<b>${tip}</b>` } : { value: [lon, lat], col, tooltip: { show: false } };
        if (run) it.run = run;
        items.push(it);
      }
      const hatch = L.kind === 'hatch';
      series.push({
        id: id('hex' + li), type: 'custom', xAxisIndex: i, yAxisIndex: i, z: 3 + li, clip: true, silent: hatch || L.kind === 'mask' && !L.label,
        data: items,
        renderItem: (p, api) => {
          const it = items[p.dataIndex], [x, y] = api.coord(it.value);
          if (hatch) return { type: 'line', shape: { x1: x - R * .6, y1: y + R * .6, x2: x + R * .6, y2: y - R * .6 }, style: { stroke: it.col, lineWidth: Math.max(.8, 1.1 * s), opacity: .75 } };
          const shape = { points: pts.map(([u, v]) => [x + Rr * u, y + Rr * v]) };
          if (!it.run) return { type: 'polygon', shape, style: { fill: it.col }, enterFrom: { style: { opacity: 0 } } };
          // starts on the scale's neutral colour, so nothing shows its end colour before its turn
          return { type: 'polygon', shape, style: { fill: it.run.frames[0].style.fill },
                   keyframeAnimation: { duration: it.run.dur, delay: base + 250, easing: 'linear', keyframes: it.run.frames } };
        },
        animationDuration: 450, animationDelay: base + li * 60, progressive: 0
      });
    });
  }

  colourBar(series, id, i, a, panel, s) {
    const L = panel && panel.layers.find(l => l.kind === 'num');
    if (!L) return;
    const sc = window.MAPDATA.scales[L.scale], horiz = a.box[2] > a.box[3], lim = horiz ? a.x : a.y, n = 120;
    const [lo, hi] = [lim.min, lim.max], step = (hi - lo) / n;
    series.push({
      id: id('cbar'), type: 'custom', xAxisIndex: i, yAxisIndex: i, z: 5, silent: true, clip: false, data: [0],
      renderItem: (p, api) => ({ type: 'group', children: Array.from({ length: n }, (_, q) => {
        const v0 = lo + q * step, v1 = v0 + step * 1.02;
        const [ax, ay] = api.coord(horiz ? [v0, a.y.max] : [a.x.min, v1]), [bx, by] = api.coord(horiz ? [v1, a.y.min] : [a.x.max, v0]);
        return { type: 'rect', shape: { x: Math.min(ax, bx), y: Math.min(ay, by), width: Math.abs(bx - ax), height: Math.abs(by - ay) }, style: { fill: mapScale(sc, v0 + step / 2) } };
      }) }),
      animationDuration: 600
    });
  }

  barSeries(id, i, bars, base, s) {
    const xs = [...new Set(bars.map(b => b.o === 'v' ? b.r[0] : -b.r[1]))].sort((a, b) => a - b);
    return {
      id, type: 'custom', xAxisIndex: i, yAxisIndex: i, z: 2 + (bars[0].z || 0), clip: true,
      data: bars.map((b, q) => ({ value: [(b.r[0] + b.r[2]) / 2, (b.r[1] + b.r[3]) / 2], b,
        tip: `<b>${mplNum(b.o === 'v' ? b.r[3] - b.r[1] : b.r[2] - b.r[0])}</b>` })),
      renderItem: (p, api) => {
        const b = bars[p.dataIndex];
        const [xa, ya] = api.coord([b.r[0], b.r[1]]), [xb, yb] = api.coord([b.r[2], b.r[3]]);
        const shape = { x: Math.min(xa, xb), y: Math.min(ya, yb), width: Math.abs(xb - xa), height: Math.abs(yb - ya) };
        const from = b.o === 'v' ? { shape: { y: ya, height: 0 }, style: { opacity: 0 } } : { shape: { x: xa, width: 0 }, style: { opacity: 0 } };
        const style = { fill: b.fc || 'none', opacity: (b.fa ?? 1) * (b.a ?? 1), stroke: b.ec || 'none', lineWidth: (b.ew || 0) * s };
        // rounded at the far end (the end away from zero), unless another segment is stacked onto it
        const v = b.o === 'v', lo = v ? b.r[1] : b.r[0], hi = v ? b.r[3] : b.r[2];
        const outer = Math.abs(hi) >= Math.abs(lo) ? hi : lo, inner = outer === hi ? lo : hi;
        const pos = (v ? b.r[0] : b.r[1]).toFixed(4), stacked = bars.some(o => o !== b && (o.o === 'v' ? o.r[0] : o.r[1]).toFixed(4) === pos
          && [o.o === 'v' ? o.r[1] : o.r[0], o.o === 'v' ? o.r[3] : o.r[2]].some(e => Math.abs(e - outer) < 1e-9 * (1 + Math.abs(outer))));
        if (!stacked && outer !== inner) {
          const thick = v ? shape.width : shape.height, len = v ? shape.height : shape.width, R = Math.min(thick / 2, len, 10);
          const po = api.coord(v ? [b.r[0], outer] : [outer, b.r[1]]), pi = api.coord(v ? [b.r[0], inner] : [inner, b.r[1]]);
          shape.r = v ? (po[1] < pi[1] ? [R, R, 0, 0] : [0, 0, R, R]) : (po[0] > pi[0] ? [0, R, R, 0] : [R, 0, 0, R]);
        }
        const kids = [{ type: 'rect', shape, style, enterFrom: from }];
        if (b.hatch) kids.push(mplHatchLines(b.hatch, b.hc || '#000', s, { type: 'rect', shape }, [shape.x, shape.y, shape.x + shape.width, shape.y + shape.height]));
        return { type: 'group', children: kids };
      },
      animationDuration: 650, animationEasing: 'cubicOut',
      animationDelay: q => base + (xs.length > 1 ? xs.indexOf(bars[q].o === 'v' ? bars[q].r[0] : -bars[q].r[1]) / (xs.length - 1) : 0) * 900 + (bars[q].ci || 0) * 160
    };
  }

  cellSeries(id, i, a, c, base, s, legendLabel) {
    const x0 = c.x[0], span = (c.x[c.x.length - 1] - x0) || 1;
    return {
      id, type: 'custom', xAxisIndex: i, yAxisIndex: i, z: 2 + (c.z || 0), clip: true,
      data: c.runs.map(r => {
        const v = r.length > 4 ? r[4] : null, lab = v === null ? this.nearestLabel(c.pal[r[3]], legendLabel) : null;
        const tip = v !== null ? `<b>${mplNum(v)}</b>` : lab ? `<b>${lab}</b>` : null;
        return tip ? { value: [c.x[r[1]], c.y[r[0]][0]], tip } : { value: [c.x[r[1]], c.y[r[0]][0]], tooltip: { show: false } };
      }),
      renderItem: (p, api) => {
        const r = c.runs[p.dataIndex], [ya, yb] = c.y[r[0]];
        const [xa, y1] = api.coord([c.x[r[1]], yb]), [xb, y2] = api.coord([c.x[r[2]], ya]);
        return { type: 'rect', shape: { x: xa, y: y1, width: xb - xa + .4, height: y2 - y1 + .4 }, style: { fill: c.pal[r[3]] },
                 enterFrom: { style: { opacity: 0 } } };
      },
      animationDuration: 500, animationDelay: q => base + (c.x[c.runs[q][1]] - x0) / span * 1100,
      progressive: 0, silent: !c.runs.some(r => r.length > 4) && !Object.keys(legendLabel).length
    };
  }

  nearestLabel(col, legendLabel) {
    // categorical map cells are shades of their legend colour (lighter where little area is free)
    const c = mplRgb(col); if (!c) return null;
    let best = null, bd = Infinity;
    for (const [lc, lab] of Object.entries(legendLabel)) {
      const l = mplRgb(lc); if (!l) continue;
      const n = v => { const m = Math.max(...v), q = Math.min(...v); return v.map(x => (x - q) / ((m - q) || 1)); };
      const a = n(c), b = n(l), dist = Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]) + Math.hypot(c[0] - l[0], c[1] - l[1], c[2] - l[2]) / 400;
      if (dist < bd) { bd = dist; best = lab; }
    }
    return bd < .6 ? best : null;
  }

  set(k, animate, fresh) {
    if (!this.chart) return;
    if (fresh) { this.chart.clear(); for (const e of this.inner.querySelectorAll(':scope > .mtex')) e.remove(); }
    this.chart.setOption(this.option(k, animate), { replaceMerge: ['series', 'graphic', 'grid', 'xAxis', 'yAxis'] });
    this.k = k;
    this.placeTex(animate);
  }
  placeTex(animate) {
    // formula symbols of the figure (its texts that are one $…$), set with KaTeX at their place, boxed in their
    // colour like the highlighted terms of the formulas (.froad .fw.cur); they come with their panel and its title,
    // without an entrance of their own, and one already there stays as it is
    const old = new Map([...this.inner.querySelectorAll(':scope > .mtex')].map(e => [e.dataset.key, e]));
    for (const { t, a, key } of this.texs) {
      const W = this.W, H = this.H, left = a.box[0] * W, top = a.box[1] * H, bw = a.box[2] * W, bh = a.box[3] * H;
      const x = left + (t.x - a.x.min) / (a.x.max - a.x.min) * bw, y = top + (a.y.max - t.y) / (a.y.max - a.y.min) * bh;
      let el = old.get(key); old.delete(key);
      if (!el) {
        el = document.createElement('span'); el.className = 'mtex'; el.dataset.key = key;
        katex.render(t.b ? `\\boldsymbol{${t.tex}}` : t.tex, el, { throwOnError: false, strict: false });
        this.inner.append(el);
      }
      const tx = t.al === 'right' ? '-100%' : t.al === 'center' ? '-50%' : '0';
      // KaTeX sets its formulas at 1.21 em: divided out, the symbol is as large as the figure's text of that size
      Object.assign(el.style, { left: x + 'px', top: y + 'px', transform: `translate(${tx},-50%)`, color: t.c,
        borderColor: t.c, background: `color-mix(in srgb, ${t.c} 8%, transparent)`, fontSize: (t.fs || 16) * this.s / 1.21 + 'px' });
    }
    for (const e of old.values()) e.remove();
  }
  play(k) { this.set(Math.min(k, this.nSteps), true, k === 0 || this.k === null || k < this.k); }
  final(k) { this.set(Math.max(0, Math.min(k, this.nSteps)), false, true); }

}

/* ===========================================================
   ALBEDO TILES (slides 15, 16)
   A tree on its patch of ground; sunlight comes in (solid) and
   part of it goes back out (dotted). "!" marks a changed value.
   =========================================================== */
function arrow(g, x1, y1, x2, y2, dotted, d0, red) {
  const col = '#ec9a2b';
  const ang = Math.atan2(y2 - y1, x2 - x1), L = 16, W = 9;
  const bx = x2 - L * Math.cos(ang), by = y2 - L * Math.sin(ang);
  const line = E('path', { d: `M${x1} ${y1}L${bx} ${by}`, stroke: col, 'stroke-width': 4.5, fill: 'none', 'stroke-linecap': 'round' }, g);
  if (dotted) { line.setAttribute('stroke-dasharray', '1 9'); line.setAttribute('class', 'pop'); line.style.setProperty('--d', d0); }
  else { line.setAttribute('pathLength', 1); line.setAttribute('class', 'draw'); line.style.setProperty('--d', d0); line.style.setProperty('--dur', 500); }
  const nx = -Math.sin(ang), ny = Math.cos(ang);
  E('path', { d: `M${x2} ${y2}L${bx + nx * W} ${by + ny * W}L${bx - nx * W} ${by - ny * W}Z`, fill: col, class: 'pop', style: `--d:${d0 + (dotted ? 0 : 420)}` }, g);
}
function label(g, x, y, s, d0) {
  const red = s.startsWith('!');
  const t = E('text', { x, y, 'font-family': 'Literata', 'font-style': 'italic', 'font-weight': 700, 'font-size': 27, fill: red ? '#a3121b' : '#1b2420', class: 'pop', style: `--d:${d0}` }, g);
  t.textContent = red ? s.slice(1) : s;
}
function drawAlbedo(svg) {
  const tiles = JSON.parse(svg.dataset.tiles);
  tiles.forEach((tl, k) => {
    const d0 = tl.step ? 0 : k * 900;
    const g = E('g', { transform: `translate(${tl.x} ${tl.y})` }, svg);
    const inner = tl.step ? E('g', { 'data-step': tl.step }, g) : g;
    E('ellipse', { cx: 250, cy: 290, rx: 185, ry: 26, fill: tl.snow ? '#ffffff' : '#cfe8bb', stroke: tl.snow ? '#cfe8bb' : 'none', 'stroke-width': 3 }, inner);
    const tree = E('g', { class: 'grow', style: `--d:${d0}` }, inner);
    E('path', { d: 'M205 290V215l-14-14 6-6 14 13 14-13 6 6-14 14v75z', fill: '#6b4422' }, tree);
    const c = tl.light ? ['#cfe6bb', '#b3c9a0', '#8fa97c'] : ['#3c5d32', '#2f4a26', '#1f3416'];
    E('circle', { cx: 212, cy: 168, r: 38, fill: c[0] }, tree);
    E('circle', { cx: 190, cy: 196, r: 27, fill: c[1] }, tree);
    E('circle', { cx: 233, cy: 200, r: 27, fill: c[2] }, tree);
    arrow(inner, 150, 70, 200, 158, false, d0 + 400);
    arrow(inner, 210, 152, 238, 92, true, d0 + 1000);
    label(inner, 90, 58, tl.tree[0], d0 + 400); label(inner, 252, 86, tl.tree[1], d0 + 1000);
    const gr = tl.groundStep ? E('g', { 'data-step': tl.groundStep }, inner) : inner, d1 = tl.groundStep ? -400 : d0;
    arrow(gr, 330, 180, 372, 282, false, d1 + 600);
    arrow(gr, 382, 276, 410, 210, true, d1 + 1200);
    label(gr, 290, 172, tl.ground[0], d1 + 600); label(gr, 424, 222, tl.ground[1], d1 + 1200);
    if (tl.caption) {
      const t = E('text', { x: 250, y: 342, 'text-anchor': 'middle', 'font-family': 'Literata', 'font-style': 'italic', 'font-weight': 700, 'font-size': 34, fill: '#a3121b', class: 'pop', style: `--d:${d0 + 1400}` }, inner);
      t.textContent = tl.caption;
    }
  });
}

/* count-up numbers: <span class="count" data-to="3.6" data-dec="1"> */
function countUp(el, embed) {
  const to = +el.dataset.to, dec = +(el.dataset.dec || 0), delay = +(el.dataset.delay || 0);
  const fmt = v => v.toLocaleString('de-DE', { minimumFractionDigits: dec, maximumFractionDigits: dec }).replace(/\./g, ' ');
  cancelAnimationFrame(el._raf);
  if (embed) { el.textContent = fmt(to); return; }
  const t0 = performance.now() + delay;
  const tick = now => {
    const p = easeOut(clamp01((now - t0) / 1400));
    el.textContent = fmt(to * p);
    if (p < 1) el._raf = requestAnimationFrame(tick);
  };
  el.textContent = fmt(0); el._raf = requestAnimationFrame(tick);
}

/* ===========================================================
   PRESENTATION CONTROLLER
   Keys, wheel, touch; fragments; hash deep links; notes drawer.
   =========================================================== */
/* Jump to a slide like in PowerPoint: type its number, press Enter.
   A badge shows the number and the slide's title while typing; Esc cancels,
   Backspace removes a digit, after 4 s without input the number is dropped. */

/* ---------- slide overview (M / floating button) ---------- */
class SlideMenu {
  constructor(deck) {
    this.deck = deck; this.el = document.getElementById('menu'); this.body = this.el.querySelector('.menu-body');
    this.fab = document.getElementById('menu-fab'); this.built = false; this.thumbs = false;
    this.fab.addEventListener('click', () => this.toggle());
    this.el.querySelector('.menu-close').addEventListener('click', () => this.close());
    this.body.addEventListener('click', e => { const c = e.target.closest('.card'); if (c) this.jump(+c.dataset.i); });
    // keep the deck's wheel and swipe navigation out of the overview
    for (const t of ['wheel', 'touchstart', 'touchend']) this.el.addEventListener(t, e => e.stopPropagation(), { passive: true });
    addEventListener('keydown', e => this.key(e), true);
    addEventListener('resize', () => { if (this.isOpen) this.scale(); });
  }
  get isOpen() { return this.el.classList.contains('open'); }
  build() {
    const d = this.deck; let html = '', grid = false;
    const open = t => { if (grid) html += '</div>'; html += `<h3>${t}</h3><div class="menu-grid">`; grid = true; };
    d.slides.forEach((s, i) => {
      if (i === 0) open('Vortrag');
      if (i === d.mainEnd) open('Backup');
      else if (s.classList.contains('chapter') && i > 0 && i < d.mainEnd) open(s.dataset.title || 'Kapitel');
      const t = (s.dataset.title || '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
      html += `<button class="card" type="button" data-i="${i}"><span class="pv"><b>${i + 1}</b></span><span class="cap"><i>${i + 1}</i><span>${t}</span></span></button>`;
    });
    this.body.innerHTML = html + '</div>';
    this.cards = [...this.body.querySelectorAll('.card')];
    this.built = true;
  }
  loadThumbs() {
    if (this.maker || deckLean) return;   // cards keep their numbers and titles
    const f = this.maker = document.createElement('iframe');
    f.setAttribute('aria-hidden', 'true'); f.tabIndex = -1;
    f.style.cssText = 'position:fixed;left:-20000px;top:0;width:1600px;height:900px;border:0;pointer-events:none';
    f.srcdoc = this.copyHtml();
    document.body.appendChild(f);
    this.queue = this.cards.map((c, i) => i); this.done = new Set();
    this.io = new IntersectionObserver(es => { for (const e of es) if (e.isIntersecting) this.want(+e.target.dataset.i); },
                                       { root: this.body, rootMargin: '300px 0px' });
    this.cards.forEach(c => this.io.observe(c));
    let tries = 0;
    const wait = () => {
      let ok = false; try { const w = f.contentWindow; ok = !!(w && w.deck && w.deck.ready); } catch (e) { return; }   // blocked: cards keep their numbers
      ok ? this.pump() : ++tries < 400 && setTimeout(wait, 150);
    };
    f.addEventListener('load', wait);
  }
  copyHtml() {
    // the page as parsed (snapshot before any script touched it), plus the scripts after the snapshot, in embed mode
    const snap = window.__SNAP.cloneNode(true), mark = document.getElementById('deck-snap');
    snap.querySelectorAll('script[data-dyn], #deck-snap').forEach(e => e.remove());
    const all = [...document.scripts], body = snap.querySelector('body');
    for (const s of all.slice(all.indexOf(mark) + 1)) if (!s.dataset.dyn) body.append(s.cloneNode(true));
    snap.querySelector('head').insertAdjacentHTML('afterbegin', '<script>window.__EMBED = 1<\/script>');
    return '<!doctype html>' + snap.outerHTML;
  }
  want(i) {   // a card came into view: make its preview next
    if (!this.done || this.done.has(i)) return;
    this.queue = this.queue.filter(x => x !== i); this.queue.unshift(i);
  }
  async pump() {
    if (this.busy) return; this.busy = true;
    const d = this.maker.contentWindow.deck, sleep = ms => new Promise(r => setTimeout(r, ms));
    while (this.queue.length) {
      const i = this.queue.shift(); if (this.done.has(i)) continue;
      d.go(i, 'end');
      await sleep(90);                                   // charts draw on the next frame
      this.place(i, d.slides[i]); this.done.add(i);
      await sleep(this.isOpen ? 10 : 60);
    }
    this.io.disconnect(); this.maker.remove();           // all previews made: the copy is no longer needed
  }
  place(i, src) {
    const cl = document.importNode(src, true);
    const from = src.querySelectorAll('canvas'), to = cl.querySelectorAll('canvas');
    from.forEach((c, k) => {
      const im = document.createElement('img');
      try {
        const s = document.createElement('canvas'), f = 4;
        s.width = Math.max(1, Math.round(c.width / f)); s.height = Math.max(1, Math.round(c.height / f));
        s.getContext('2d').drawImage(c, 0, 0, s.width, s.height); im.src = s.toDataURL();
      } catch (e) { /* tainted canvas: leave empty */ }
      im.style.cssText = c.style.cssText; im.style.width = c.style.width || c.clientWidth + 'px'; im.style.height = c.style.height || c.clientHeight + 'px';
      to[k].replaceWith(im);
    });
    cl.querySelectorAll('.notes, video, audio').forEach(e => e.remove());
    // own ids: clip paths, gradients and markers must resolve inside the copy, not in the (unplayed) original
    const ids = new Map();
    for (const e of cl.querySelectorAll('[id]')) { const v = e.id + '-t' + i; ids.set(e.id, v); e.id = v; }
    if (ids.size) {
      const fix = v => v.replace(/url\(\s*["']?#([^"')\s]+)["']?\s*\)/g, (m, id) => ids.has(id) ? `url(#${ids.get(id)})` : m)
                        .replace(/^#(.+)$/, (m, id) => ids.has(id) ? '#' + ids.get(id) : m);
      for (const e of cl.querySelectorAll('*')) for (const a of [...e.attributes]) {
        if (a.value.includes('#')) { const v = fix(a.value); if (v !== a.value) e.setAttribute(a.name, v); }
      }
    }
    cl.classList.add('active'); cl.removeAttribute('data-title');
    const wrap = document.createElement('div'); wrap.className = 'tdeck embed';   // the presenter preview's rules: end state, no entrances
    wrap.setAttribute('aria-hidden', 'true'); wrap.append(cl);
    this.cards[i].querySelector('.pv').prepend(wrap);
  }
  scale() {
    const pv = this.cards[0].querySelector('.pv');
    this.body.style.setProperty('--k', (pv.clientWidth / 1600).toFixed(4));
  }
  open() {
    if (!this.built) this.build();
    this.loadThumbs();
    this.cards.forEach((c, i) => c.classList.toggle('cur', i === this.deck.i));
    this.back = document.activeElement;
    this.el.classList.add('open'); this.fab.setAttribute('aria-expanded', 'true');
    document.querySelector('main').inert = true;
    this.scale();
    const cur = this.cards[this.deck.i];
    cur.scrollIntoView({ block: 'center' }); cur.focus({ preventScroll: true });
  }
  close() {
    this.el.classList.remove('open'); this.fab.setAttribute('aria-expanded', 'false');
    document.querySelector('main').inert = false;
    // focus goes back where it came from (the button on touch screens); after a key press there was nothing to return to
    if (this.back && this.back !== document.body && this.back.isConnected) this.back.focus({ preventScroll: true }); else document.activeElement?.blur();
    this.back = null;
  }
  toggle() { this.isOpen ? this.close() : this.open(); }
  jump(i) { this.close(); this.deck.go(i, 0); }
  cols() {
    const g = this.cards[0].parentElement, w = this.cards[0].getBoundingClientRect().width;
    const gap = parseFloat(getComputedStyle(g).columnGap) || 0;
    return Math.max(1, Math.round((g.clientWidth + gap) / (w + gap)));
  }
  key(e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const k = e.key;
    if (!this.isOpen) { if (k === 'm' || k === 'M') { e.preventDefault(); e.stopImmediatePropagation(); this.open(); } return; }
    e.stopImmediatePropagation();
    const i = Math.max(0, this.cards.indexOf(document.activeElement)), n = this.cards.length;
    const move = j => { j = Math.min(n - 1, Math.max(0, j)); this.cards[j].focus(); this.cards[j].scrollIntoView({ block: 'nearest' }); };
    if (k === 'Escape' || k === 'm' || k === 'M') { e.preventDefault(); this.close(); }
    else if (k === 'Enter' || k === ' ') { e.preventDefault(); this.jump(i); }
    else if (k === 'ArrowRight') { e.preventDefault(); move(i + 1); }
    else if (k === 'ArrowLeft') { e.preventDefault(); move(i - 1); }
    else if (k === 'ArrowDown') { e.preventDefault(); move(i + this.cols()); }
    else if (k === 'ArrowUp') { e.preventDefault(); move(i - this.cols()); }
    else if (k === 'Home') { e.preventDefault(); move(0); }
    else if (k === 'End') { e.preventDefault(); move(n - 1); }
    else if (k === 'Tab') {   // modal: Tab runs round the close button and the cards
      const ring = [this.el.querySelector('.menu-close'), ...this.cards], j = ring.indexOf(document.activeElement);
      e.preventDefault(); ring[(j + (e.shiftKey ? -1 : 1) + ring.length) % ring.length].focus();
    }
  }
}

function slideJumper(count, titleOf, jump) {
  let buf = '', timer = null;
  const badge = () => {
    let b = document.getElementById('jump-badge');
    if (!b) { b = document.createElement('div'); b.id = 'jump-badge'; b.setAttribute('role', 'status'); document.body.appendChild(b); }
    return b;
  };
  const show = () => {
    const b = badge(), n = +buf, ok = n >= 1 && n <= count();
    b.innerHTML = buf ? `<b>${buf}</b><span>${ok ? (titleOf(n - 1) || '') : 'keine solche Folie'}</span><kbd>↵</kbd>` : '';
    b.classList.toggle('on', !!buf); b.classList.toggle('bad', !!buf && !ok);
    clearTimeout(timer); if (buf) timer = setTimeout(() => { buf = ''; show(); }, 4000);
  };
  return e => {   // true when the key was used for jumping
    const k = e.key;
    if (/^[0-9]$/.test(k)) { if (buf.length < 3) buf += k; show(); return true; }
    if (!buf) return false;
    if (k === 'Enter') { const n = +buf; buf = ''; show(); if (n >= 1 && n <= count()) jump(n - 1); return true; }
    if (k === 'Backspace') { buf = buf.slice(0, -1); show(); return true; }
    if (k === 'Escape') { buf = ''; show(); return true; }
    return false;
  };
}


/* phones and tablets: no second deck copy for the overview's previews and no live woodway — together they
   exceed what iOS grants a tab, and Safari kills the page ("a problem repeatedly occurred") */
const deckLean = matchMedia('(hover: none), (pointer: coarse)').matches;
/* reduced motion: charts and numbers arrive in their end state, as the CSS entrances do */
const deckCalm = matchMedia('(prefers-reduced-motion: reduce)');

/* ---------- images: current slide first, the rest in the background ---------- */
const deckMedia = {
  load(s) {
    if (!s || s._media) return; s._media = true;
    for (const im of s.querySelectorAll('img[data-src]')) { im.src = im.dataset.src; im.removeAttribute('data-src'); }
  },
  around(slides, n) {
    for (const k of [n, n + 1, n - 1, n + 2]) this.load(slides[k]);
    // live iframes (woodway): only on this slide and the next, and only in the projector window
    if (!document.documentElement.classList.contains('embed') && !deckLean)
      for (const k of [n, n + 1]) for (const f of slides[k]?.querySelectorAll('iframe[data-live-src]') ?? []) {
        f.addEventListener('load', () => f.classList.add('on'), { once: true });
        f.src = f.dataset.liveSrc; f.removeAttribute('data-live-src');
      }
  },
  rest(slides) {   // a few slides at a time, so a jump still gets the line quickly
    let k = 0;
    const tick = () => {
      const pending = document.querySelectorAll('img[src]:not([data-src])');
      let busy = 0; for (const im of pending) if (!im.complete) busy++;
      while (k < slides.length && busy < 6) { const s = slides[k++]; if (!s._media) { this.load(s); busy += s.querySelectorAll('img').length; } }
      if (k < slides.length) setTimeout(tick, 250);
    };
    tick();
  },
};

/* Literata's web subset has no subscript digits, so CO₂ in a serif line fell back to Georgia's full-size 2.
   In HTML text (not SVG, not KaTeX) a subscript digit becomes a small digit of the line's own face. */
function subDigits(root) {
  const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: t =>
    /[\u2080-\u2089]/.test(t.data) && !t.parentElement.closest('svg, .katex, script, style, .notes') ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT });
  const hits = []; while (walk.nextNode()) hits.push(walk.currentNode);
  for (const t of hits) {
    const frag = document.createDocumentFragment();
    for (const part of t.data.split(/([\u2080-\u2089]+)/)) {
      if (!part) continue;
      if (/[\u2080-\u2089]/.test(part)) {
        const el = document.createElement('span'); el.className = 'subd';
        el.textContent = [...part].map(c => String.fromCharCode(c.charCodeAt(0) - 0x2050)).join('');
        frag.append(el);
      } else frag.append(part);
    }
    t.replaceWith(frag);
  }
}

class Deck {
  constructor() {
    this.deck = document.getElementById('deck');
    this.slides = [...this.deck.querySelectorAll('.slide')];
    this.drawer = document.getElementById('drawer');
    this.drawerBody = document.getElementById('drawer-body');
    this.progress = document.querySelector('.progress');
    this.i = 0; this.step = 0; this.showAll = location.search.includes('all');
    this.embed = location.search.includes('embed') || !!window.__EMBED;   // slide preview inside the presenter view
    this.host = location.search.includes('host');      // inside the React deck: it supplies the chrome
    if (this.host) document.documentElement.classList.add('host');
    this.still = this.embed || this.showAll;
    if (this.showAll) document.documentElement.classList.add('all');
    this.peer = null;                                 // the presenter window, once it has spoken
    this.mainEnd = this.slides.findIndex(s => s.classList.contains('backup'));
    if (this.mainEnd < 0) this.mainEnd = this.slides.length;
    this.decorate();
    this.fit(); addEventListener('resize', () => this.fit());
    addEventListener('message', e => this.onMessage(e));
    if (!this.embed) { this.bind(); this.menu = new SlideMenu(this); }
    const h = parseInt(location.hash.slice(1), 10);
    this.go(Number.isFinite(h) ? h - 1 : 0, 0);
    this.booted = true;
    setTimeout(() => document.getElementById('hint').classList.add('gone'), 5000);
  }
  onMessage(e) {
    const d = e.data;
    // embedded woodway hands back the paging keys once a click has put focus into it
    if (d && d.src === 'woodway-key' && !this.embed) { if (d.dir === 'next') this.next(); else if (d.dir === 'prev') this.prev(); return; }
    if (!d || d.src !== 'dv') return;
    if (this.embed) { if ('goto' in d) this.go(d.goto, d.step); return; }
    this.peer = e.source;
    if (d.cmd === 'next') this.next(); else if (d.cmd === 'prev') this.prev();
    else if (d.cmd === 'first') this.go(0, 0); else if (d.cmd === 'last') this.go(this.mainEnd - 1, 0);
    else if (d.cmd === 'replay') this.go(this.i, this.step);
    else if (d.cmd === 'goto' && Number.isInteger(d.n)) {
      const n = Math.max(0, Math.min(this.slides.length - 1, d.n));
      this.go(n, d.step === 'end' ? 'end' : Number.isInteger(d.step) ? d.step : 0);   // 'end' like prev(): the last state, drawn without replaying the slide
    }
    else if (d.cmd === 'hello') this.sync();
  }
  sync() {
    // Tell the presenter window where we are and what comes next.
    if (this.embed || !this.peer || this.peer.closed) return;
    let ni = this.i, ns = this.step + 1;
    if (ns > this.steps(this.slides[this.i])) { ni = this.i + 1; ns = 0; }
    this.peer.postMessage({ src: 'dv', state: { i: this.i, step: this.step, ni, ns, n: this.slides.length, main: this.mainEnd } }, '*');
  }
  openPresenter() {
    if (this.peer && !this.peer.closed) { this.peer.focus(); return; }
    this.peer = window.open(location.href.split(/[?#]/)[0] + '?presenter', 'dv-presenter', 'width=1440,height=900');
  }
  decorate() {
    // Where the talk stands: the chapters as on the overview slide, each its icon in its own colour, the current
    // one named. Content slides carry it top right, the chapter openers top left (on their colour, inverted).
    const chapters0 = ['baeume', 'klima', 'vergleich'];
    const names = { baeume: 'Bäume', klima: 'Klima', vergleich: 'Potenzial', dac: 'Optionen' };   // chapter 5: DAC and the vegan world
    const path = ch => {
      const el = document.createElement('div'); el.className = 'path'; el.setAttribute('aria-hidden', 'true');
      el.innerHTML = (ch === 'dac' ? [...chapters0, 'dac'] : chapters0).map(c =>
        `<span class="pc${c === ch ? ' on' : ''}" data-ch="${c}"><svg><use href="#i-${c}"/></svg>${c === ch ? `<b>${names[c]}</b>` : ''}</span>`).join('');
      return el;
    };
    subDigits(this.deck);
    this.slides.forEach((s, n) => {
      const ch = s.dataset.ch, h = s.querySelector('.sh');
      if (h) h.appendChild(path(ch));
      else if (s.matches('.chapter:not(.brk):not(.backup)')) s.appendChild(path(ch));
      if (!s.classList.contains('chapter') && !s.classList.contains('title')) {
        const num = document.createElement('span'); num.className = 'num'; num.textContent = n + 1; s.appendChild(num);
      }
      s.setAttribute('role', 'group'); s.setAttribute('aria-roledescription', 'Folie');
      s.setAttribute('aria-label', `${n + 1}: ${s.dataset.title || ''}`);
    });
  }
  stage(s) {
    // page background and mobile browser bar = colour of the current slide
    let bg = getComputedStyle(s).backgroundColor;
    if (!bg || bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') bg = '#f2ede2';
    document.documentElement.style.setProperty('--stage', bg);
    document.querySelector('meta[name="theme-color"]').setAttribute('content', bg);
    const plain = !s.matches('.chapter, .title');
    document.documentElement.style.setProperty('--ground', plain ? getComputedStyle(s).getPropertyValue('--ch') : 'transparent');
    document.documentElement.style.setProperty('--bar', getComputedStyle(s).getPropertyValue(plain && !s.matches('.dark') ? '--ch' : '--ch-soft'));
  }
  fit() {
    const k = Math.min(innerWidth / 1600, innerHeight / 900);
    this.deck.style.transform = `translate(-50%, -50%) scale(${k})`;
  }
  steps(s) {
    // clicks on this slide: the highest data-step, including chart panels behind their host's step
    if (s._steps === undefined) {
      let n = 0;
      for (const e of s.querySelectorAll('[data-step]')) n = Math.max(n, +e.dataset.step || 0);
      for (const h of s.querySelectorAll('.chart')) if (h._chart) n = Math.max(n, (+h.dataset.step || 0) + h._chart.nSteps);
      s._steps = n;
    }
    return s._steps;
  }
  go(n, step) {
    n = Math.max(0, Math.min(this.slides.length - 1, n));
    if (this.booted && window.__deckDataNow) window.__deckDataNow();   // the speaker moves on: load the charts now
    if (window.__ensureCharts) { window.__ensureCharts(this.slides[n]); delete this.slides[n]._steps; }
    if (window.__ensureTex) window.__ensureTex(this.slides[n]);
    deckMedia.around(this.slides, n);
    const s = this.slides[n], again = n === this.i && s.classList.contains('active');
    if (again && !this.still) { s.classList.remove('active'); void s.offsetWidth; }   // restart CSS entrances
    const prev = this.slides[this.i];
    if (prev && prev !== s && prev.classList.contains('active')) {   // drawn while it fades out
      prev.classList.add('leaving'); clearTimeout(prev._leave);
      prev._leave = setTimeout(() => prev.classList.remove('leaving', 'hold'), 400);
      // the old slide stays fully under the new one while that fades in: what both show (a chart, a drawing, a title
      // that stays) does not dip in brightness; what differs still cross-fades
      prev.classList.add('hold');
    }
    this.slides.forEach((x, k) => x.classList.toggle('active', k === n));
    this.i = n; this.step = (step === 'end' || this.showAll) ? this.steps(s) : step;
    this.applyStep(!this.still && step !== 'end', true);
    this.progress.style.transform = `scaleX(${Math.min(1, (n + 1) / this.mainEnd)})`;
    this.stage(s);
    if (!this.embed) history.replaceState(null, '', `#${n + 1}`);
    if (!this.embed && n !== this.said) { this.said = n; document.getElementById('sr-status').textContent = `Folie ${n + 1} von ${this.slides.length}: ${s.dataset.title || ''}`; }
    const notes = s.querySelector('.notes');
    this.drawerBody.innerHTML = notes && notes.innerHTML.trim() ? notes.innerHTML : '<p class="q">Keine Notizen.</p>';
    this.sync();
  }
  dataReady() {
    // charts exist now: recount the clicks and draw the current slide in its present state
    for (const s of this.slides) delete s._steps;
    this.ready = true;
    if (this.still) this.go(this.i, this.step); else this.applyStep(false, false, true);
    if (!this.embed) setTimeout(() => deckMedia.rest(this.slides), 300);
  }
  applyStep(animate, entering, late) {
    // late: the charts were not there when the slide came up; they play their entrance now, the rest stays put
    if (animate) this.movedAt = performance.now();   // the background chart builder waits until this has played
    // everything with data-step <= step is shown; charts run the part that belongs to this click
    const s = this.slides[this.i];
    for (const e of s.querySelectorAll('[data-step]')) e.classList.toggle('shown', (+e.dataset.step || 0) <= this.step);
    this.rest(s);
    for (const h of s.querySelectorAll('.chart')) {
      const ch = h._chart; if (!ch) continue;
      const k = this.step - (+h.dataset.step || 0);
      if ((animate || late) && !deckCalm.matches && k >= 0 && k <= ch.nSteps) {
        ch.play(k);
      } else ch.final(k);
    }
    for (const c of s.querySelectorAll('.count')) {
      const host = c.closest('[data-step]'), k = host ? +host.dataset.step : 0;
      if (k > this.step) continue;
      countUp(c, !(animate && k === this.step) || deckCalm.matches);
    }
    this.sync();
  }
  rest(s) {
    // only the newest click moves: endless loops of earlier clicks (and of the opening picture) stop in a still
    // frame, so the eye goes to what just arrived; a loop that fades in and out stops where it is most visible
    if (s.matches('.ende')) return;   // the closing slide keeps its scene alive through the questions
    for (const a of document.getAnimations()) {
      const t = a.effect && a.effect.target;
      if (!t || !s.contains(t) || a.effect.getComputedTiming().iterations !== Infinity) continue;
      const host = t.closest('[data-step]'), k = host ? +host.dataset.step || 0 : 0;
      if (k >= this.step) { if (a.playState === 'paused') a.play(); continue; }
      if (a.playState === 'paused') continue;
      const fade = a.effect.getKeyframes().filter(f => f.opacity !== undefined);
      if (fade.length) {
        const f = fade.reduce((b, x) => +x.opacity > +b.opacity ? x : b);
        a.currentTime = (a.effect.getTiming().delay || 0) + f.computedOffset * a.effect.getComputedTiming().duration;
      }
      a.pause();
    }
  }
  next() { if (window.__deckDataNow) window.__deckDataNow(); if (this.step < this.steps(this.slides[this.i])) { this.step++; this.applyStep(!this.still, false); } else if (this.i < this.slides.length - 1) this.go(this.i + 1, 0); }
  prev() { if (this.step > 0) { this.step--; this.applyStep(false, false); } else if (this.i > 0) this.go(this.i - 1, 'end'); }
  bind() {
    const jumper = slideJumper(() => this.slides.length, n => this.slides[n].dataset.title, n => this.go(n, 0));
    addEventListener('keydown', e => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const k = e.key;
      if (jumper(e)) { e.preventDefault(); return; }
      if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); this.next(); }
      else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); this.prev(); }
      else if (k === 'Home') this.go(0, 0);
      else if (k === 'End') this.go(this.mainEnd - 1, 0);
      else if (k === 'b' || k === 'B') this.go(this.mainEnd, 0);
      else if (k === 'r' || k === 'R') this.go(this.i, this.step);
      else if (k === 'n' || k === 'N') this.drawer.inert = !this.drawer.classList.toggle('open');
      else if (k === 'p' || k === 'P') this.openPresenter();
      else if (k === 'f' || k === 'F') document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen?.();
    });
    let lock = 0;
    addEventListener('wheel', e => {
      if (this.drawer.contains(e.target)) return;
      const now = Date.now(); if (now < lock || Math.abs(e.deltaY) < 12) return;
      lock = now + 650; e.deltaY > 0 ? this.next() : this.prev();
    }, { passive: true });
    let x0 = null, y0 = null;
    addEventListener('touchstart', e => { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
    addEventListener('touchend', e => {
      if (x0 === null) return;
      const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
      if (Math.max(Math.abs(dx), Math.abs(dy)) > 50) (Math.abs(dx) > Math.abs(dy) ? dx : dy) < 0 ? this.next() : this.prev();
      x0 = null;
    }, { passive: true });
    addEventListener('hashchange', () => { const h = parseInt(location.hash.slice(1), 10); if (h - 1 !== this.i) this.go(h - 1, 0); });
  }
}

addEventListener('DOMContentLoaded', () => {
  if (location.search.includes('presenter')) return new Presenter();
  if (location.search.includes('embed') || window.__EMBED) document.documentElement.classList.add('embed');
  const deckEl = document.getElementById('deck');
  const tpl = document.getElementById('tpl-trees');
  deckEl.querySelectorAll('svg.trees-do').forEach((svg, k) => {
    for (const n of tpl.content.firstElementChild.childNodes) svg.appendChild(n.cloneNode(true));
    // ids per copy: arrowheads and symbols must resolve inside their own (visible) drawing
    for (const e of svg.querySelectorAll('[id]')) e.id += '-' + k;
    for (const e of svg.querySelectorAll('[marker-end], use')) {
      if (e.hasAttribute('marker-end')) e.setAttribute('marker-end', e.getAttribute('marker-end').replace(/\)$/, `-${k})`));
      if (e.hasAttribute('href')) e.setAttribute('href', e.getAttribute('href') + '-' + k);
    }
    // slide 8 builds effect by effect; slide 9 shows them all at once
    if (svg.closest('[data-tree="dim"]')) for (const e of svg.querySelectorAll('[data-step]')) e.removeAttribute('data-step');
    // slide 13 opens on slide 8's last picture: everything there at once, the global effects numbered
    if (svg.closest('[data-tree="recap"]')) { for (const e of svg.querySelectorAll('[data-step]')) e.removeAttribute('data-step'); svg.classList.add('recap'); }
  });
  for (const svg of deckEl.querySelectorAll('svg.albedo')) drawAlbedo(svg);
  window.deck = new Deck();
  // formulas, typeset one slide per task (the current one first): they carry click steps, so the slide counts again
  const texed = new WeakSet(), texOne = s => {
    if (!window.katex || texed.has(s)) return false; texed.add(s);
    if (!s.textContent.includes('$')) return false;
    renderTex(s); delete s._steps; return true;
  };
  window.__ensureTex = texOne;
  const tex = () => {
    const d = window.deck;
    const s = d.slides[d.i];
    if (texOne(s)) for (const e of s.querySelectorAll('.katex [data-step]')) e.classList.toggle('shown', (+e.dataset.step || 0) <= d.step);
    const rest = [...d.slides];
    (function next() { while (rest.length && !texOne(rest.shift())); if (rest.length) setTimeout(next, 30); })();
  };
  if (window.katex) tex(); else document.getElementById('katex-js').addEventListener('load', tex, { once: true });
  window.DECK_DATA.then(() => {
    // Charts are built in slices: building all of them at once is another long block on the main thread, and one
    // chart takes ~200 ms on a phone. The current slide's charts come at once; the slides around it (one back,
    // three ahead) only while the deck rests (no slide change for QUIET ms, the entrances played out); the far
    // ones after a longer rest and never on the title slide, whose scene keeps moving while people come in.
    // A slide that is opened before its turn builds its own (Deck.go).
    const QUIET = 2500, QUIET_FAR = 8000;
    const d = window.deck, build = h => { if (!h._chart) h._chart = h.dataset.ec ? new EChart(h) : new MplChart(h); };
    const all = [...deckEl.querySelectorAll('.chart')];
    const at = h => d.slides.indexOf(h.closest('.slide')), dist = h => Math.abs(at(h) - d.i);
    const near = h => at(h) - d.i >= -1 && at(h) - d.i <= 3;
    window.__ensureCharts = s => { for (const h of s.querySelectorAll('.chart')) build(h); };
    all.filter(h => dist(h) === 0).forEach(build);
    d.dataReady();
    let rest = all.filter(h => !h._chart);
    const slice = () => {
      rest = rest.filter(h => !h._chart);
      if (!rest.length) { for (const s of d.slides) delete s._steps; return; }   // click counts include every chart now
      const idle = performance.now() - (d.movedAt || 0);
      const far = idle >= QUIET_FAR && !d.slides[d.i].matches('.title');
      const next = rest.filter(h => near(h) || far).sort((a, b) => dist(a) - dist(b))[0];
      if (!next || idle < QUIET) { setTimeout(slice, Math.max(250, QUIET - idle)); return; }
      build(next); delete next.closest('.slide')._steps;
      setTimeout(slice, 120);   // one chart per task, with frames in between for whatever still moves
    };
    setTimeout(slice, 0);   // not in the same task as the data scripts
  });
});

/* ===========================================================
   PRESENTER VIEW  (opened with P from the projector window)
   Current slide, next build step, notes, timer. It holds no
   state of its own: keys are sent to the projector window,
   which answers with its position; the two previews are the
   same deck in ?embed mode, steered by postMessage.
   =========================================================== */
class Presenter {
  constructor() {
    const slides = [...document.querySelectorAll('#deck .slide')];
    this.notes = slides.map(s => (s.querySelector('.notes') || {}).innerHTML || '');
    this.titles = slides.map(s => s.dataset.title || '');
    const base = location.href.split(/[?#]/)[0] + '?embed';
    document.title = 'Referentenansicht · ' + document.title;
    document.documentElement.classList.add('presenter');
    document.body.innerHTML = `
      <div class="pv">
        <header class="pv-bar">
          <span id="pv-count">–</span>
          <span id="pv-title"></span>
          <span class="pv-spacer"></span>
          <button id="pv-replay" title="Animation der aktuellen Folie neu abspielen (R)">↻ Animation</button>
          <button id="pv-small" title="Notizen kleiner">A−</button>
          <button id="pv-big" title="Notizen größer">A+</button>
          <span id="pv-timer" title="Klick: pausieren / fortsetzen">00:00</span>
          <button id="pv-reset">Timer zurücksetzen</button>
          <span id="pv-clock"></span>
        </header>
        <section class="pv-main">
          <iframe id="pv-cur" src="${base}#1" title="Aktuelle Folie" tabindex="-1"></iframe>
          <h5>Notizen</h5>
          <div id="pv-notes"></div>
        </section>
        <section class="pv-side">
          <h5>Als Nächstes</h5>
          <div class="pv-next"><iframe id="pv-next" src="${base}#2" title="Nächste Folie" tabindex="-1"></iframe><div id="pv-end">Ende des Vortrags</div></div>
        </section>
        <p id="pv-lost" hidden>Keine Verbindung zur Präsentation. Öffne die Referentenansicht mit <kbd>P</kbd> aus dem Präsentationsfenster.</p>
      </div>`;
    this.cur = document.getElementById('pv-cur');
    this.nxt = document.getElementById('pv-next');
    this.state = null;
    this.fontPx = 22; this.applyFont();
    this.t0 = Date.now(); this.paused = null;
    this.bind();
    [this.cur, this.nxt].forEach(f => f.addEventListener('load', () => this.render()));
    setInterval(() => this.tick(), 500); this.tick();
    this.send('hello');
    setTimeout(() => { if (!this.state) document.getElementById('pv-lost').hidden = false; }, 1500);
  }
  send(cmd, n) { if (window.opener && !window.opener.closed) window.opener.postMessage({ src: 'dv', cmd, n }, '*'); }
  bind() {
    addEventListener('message', e => {
      const d = e.data; if (!d || d.src !== 'dv' || !d.state) return;
      this.state = d.state; document.getElementById('pv-lost').hidden = true; this.render();
    });
    const jumper = slideJumper(() => this.titles.length, n => this.titles[n], n => this.send('goto', n));
    addEventListener('keydown', e => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const k = e.key;
      if (jumper(e)) { e.preventDefault(); return; }
      if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); this.send('next'); }
      else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); this.send('prev'); }
      else if (k === 'Home') this.send('first'); else if (k === 'End') this.send('last');
      else if (k === 'r' || k === 'R') this.send('replay');
    });
    document.getElementById('pv-replay').onclick = () => this.send('replay');
    document.getElementById('pv-reset').onclick = () => { this.t0 = Date.now(); this.paused = null; this.tick(); };
    document.getElementById('pv-timer').onclick = () => {
      if (this.paused === null) this.paused = Date.now(); else { this.t0 += Date.now() - this.paused; this.paused = null; }
      this.tick();
    };
    document.getElementById('pv-small').onclick = () => { this.fontPx = Math.max(14, this.fontPx - 2); this.applyFont(); };
    document.getElementById('pv-big').onclick = () => { this.fontPx = Math.min(40, this.fontPx + 2); this.applyFont(); };
  }
  applyFont() { document.documentElement.style.setProperty('--pv-notes', this.fontPx + 'px'); }
  render() {
    const st = this.state; if (!st) return;
    const post = (f, i, step) => f.contentWindow && f.contentWindow.postMessage({ src: 'dv', goto: i, step }, '*');
    post(this.cur, st.i, st.step);
    const end = st.ni >= st.n || (st.i < st.main && st.ni >= st.main);
    document.getElementById('pv-end').hidden = !end; this.nxt.style.visibility = end ? 'hidden' : 'visible';
    if (!end) post(this.nxt, st.ni, st.ns);
    document.getElementById('pv-count').textContent = st.i < st.main ? `${st.i + 1} / ${st.main}` : `Backup ${st.i + 1 - st.main}`;
    document.getElementById('pv-title').textContent = this.titles[st.i];
    const html = this.notes[st.i].trim();
    const box = document.getElementById('pv-notes');
    box.innerHTML = html || '<p class="q">Keine Notizen.</p>'; box.scrollTop = 0;
  }
  tick() {
    const ms = (this.paused ?? Date.now()) - this.t0, m = Math.floor(ms / 60000), sec = Math.floor(ms / 1000) % 60;
    const t = document.getElementById('pv-timer');
    t.textContent = `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
    t.classList.toggle('paused', this.paused !== null);
    document.getElementById('pv-clock').textContent = new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  }
}
