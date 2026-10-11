window.DACFILM = @@DACFILM@@;

/* DAC film: the 2100 path (click 1), the 2085 path (click 2), everything the storage allows (click 3) */
(function () {
  const D = window.DACFILM, sec = document.querySelector('section[data-title="DAC-Ausbau"]');
  if (!D || !sec) return;
  const box = sec.querySelector('.film'), cv = sec.querySelector('.fmap canvas'), svg = sec.querySelector('.strip');
  const trig = [sec.querySelector('.ftrig1')];
  const yr = sec.querySelector('.yr'), nCap = sec.querySelector('.n-cap'), nCum = sec.querySelector('.n-cum'), goal = sec.querySelector('.goal');
  const cumNote = nCum.querySelector('small');
  const W = 1424, H = 483, S = 2, NS = 'http://www.w3.org/2000/svg', Y0 = D.years[0], NY = D.years.length;
  cv.width = W * S; cv.height = H * S;
  const g = cv.getContext('2d'); g.scale(S, S);
  const XY = D.cells.map(([lo, la]) => [(lo + 180) / 360 * W, (82 - la) / 122 * H]);
  const mk = (key, col, light) => { const p = Object.assign({}, D.paths[key]);
    p.cell = D.cells.map((_, i) => p.cc[D.owner[i]].map(v => v / D.n[D.owner[i]]));
    p.col = col; p.light = light; return p; };
  const P = { a: mk('opt', '#f0b04a', '#f0b04a') };
  const PH = [{ p: P.a, ym: 7.6, tmin: 0, chip: 'Wachstum ≤ 20 %/a', cls: '' }, { p: P.a, ym: 7.6, tmin: 0, chip: 'Wachstum ≤ 20 %/a', cls: '' }];
  const lerp = (arr, t) => { const i = Math.min(arr.length - 2, Math.floor(t)), f = t - i; return arr[i] + f * (arr[i + 1] - arr[i]); };
  const fmt = (v, d) => v.toLocaleString('de-DE', { minimumFractionDigits: d, maximumFractionDigits: d }).replace(/\./g, '\u202f');

  // two strips below the map: world capacity (left), warming above 1.5 C (right)
  const SH = 185, T = 40, B = 28, el = (n, a, p) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); (p || svg).append(e); return e; };
  svg.setAttribute('viewBox', `0 0 ${W} ${SH}`);
  const F = { 'font-family': 'IBM Plex Sans' };
  const panel = (x0, x1, title) => {
    const X = y => x0 + (y - Y0) / (NY - 1) * (x1 - x0);
    el('text', Object.assign({ x: x0, y: 20, 'font-size': 19, 'font-weight': 600, fill: '#f2ede2' }, F)).textContent = title;
    for (const y of [2026, 2050, 2075, 2100]) el('text', Object.assign({ x: X(y), y: SH - 4, 'text-anchor': 'middle', 'font-size': 18, fill: '#8d958f' }, F)).textContent = y;
    return X;
  };
  const XA = panel(40, 560, 'Kapazität weltweit [Gt CO₂/a]'), XB = panel(800, 1270, 'Erwärmung über 1,5 °C [mK]');
  el('line', { x1: 40, x2: 560, y1: SH - B, y2: SH - B, stroke: '#4a524d', 'stroke-width': 1.5 });
  const area = el('path', {}), ghost = el('path', { fill: 'none', stroke: '#f0b04a', 'stroke-width': 2.5, 'stroke-dasharray': '2 5' });
  const lim = el('path', { fill: 'none', stroke: '#b9c0bb', 'stroke-width': 2, 'stroke-dasharray': '6 5' });
  const lab = el('text', Object.assign({ 'font-size': 19, 'font-weight': 600 }, F)), glab = el('text', Object.assign({ 'font-size': 18, fill: '#f0b04a' }, F));
  const lab2 = el('text', Object.assign({ 'font-size': 18, fill: '#b9c0bb', 'text-anchor': 'end' }, F)); lab2.textContent = 'höchstens +20 %/a';
  const zero = el('line', { x1: 800, x2: 1270, stroke: '#4a524d', 'stroke-width': 1.5 });
  const zlab = el('text', Object.assign({ x: 794, 'text-anchor': 'end', 'font-size': 17, fill: '#8d958f' }, F)); zlab.textContent = '1,5 °C';
  const vlP = el('path', { fill: 'none', stroke: '#e0645a', 'stroke-width': 2.5, 'stroke-dasharray': '8 6' }), trP = el('path', { fill: 'none', stroke: '#6cc28a', 'stroke-width': 2.5 });
  const tArea = el('path', { 'fill-opacity': .32 }), tLine = el('path', { fill: 'none', 'stroke-width': 3.2 });
  const tGhost = el('path', { fill: 'none', stroke: '#f0b04a', 'stroke-width': 2.5, 'stroke-dasharray': '2 5' });
  const tl = (txt, c) => { const e = el('text', Object.assign({ x: XB(2100) + 10, 'font-size': 18, 'font-weight': 600, fill: c }, F)); e.textContent = txt; return e; };
  const lVL = tl('Very Low', '#e0645a'), lTr = tl('+ Bäume (Forst)', '#6cc28a'), lDac = tl('', '#ff5a4f');
  const ip = P.a.dac.indexOf(Math.max(...P.a.dac));
  const over = el('text', Object.assign({ 'font-size': 18, 'font-weight': 600, fill: '#ffd2c8' }, F));
  // at the peak DAC is still tiny: that is why it cannot lower it
  over.textContent = `Spitze ${Y0 + ip}: ${fmt(P.a.dac[ip], 0)} mK, DAC erst ${fmt(P.a.tot[ip], 1)} Gt/a`;
  const below = el('text', Object.assign({ 'font-size': 18, 'font-weight': 600, fill: '#6fe3c8', 'text-anchor': 'end' }, F));
  // capacity: the year the growth limit first allows 1 Gt/a, and the year the final capacity is reached
  const i1 = P.a.tot.findIndex(v => v >= 1), iMax = P.a.tot.findIndex(v => v >= P.a.peak - 0.01);
  const dot1 = el('circle', { r: 6, fill: '#f0b04a', stroke: '#14181a', 'stroke-width': 2 });
  const lab1 = el('text', Object.assign({ 'font-size': 18, 'font-weight': 600, fill: '#f0b04a', 'text-anchor': 'end' }, F));
  lab1.textContent = `1 Gt/a erst ${Y0 + i1}`;
  const curA = el('line', { stroke: '#f2ede2', 'stroke-width': 2, y1: T, y2: SH - B }), curB = el('line', { stroke: '#f2ede2', 'stroke-width': 2, y1: T, y2: SH - B });

  function strip(ph, upto, ymax, tmin) {
    const p = ph.p, Y = v => SH - B - Math.min(v, ymax) / ymax * (SH - B - T), f = Math.min(upto, NY - 1), k = Math.floor(f);
    const YT = v => SH - B - (Math.max(tmin, Math.min(v, 350)) - tmin) / (350 - tmin) * (SH - B - T);
    const pts = (arr, X, Yf) => { let d = ''; for (let i = 0; i <= k; i++) d += `${i ? 'L' : 'M'}${X(Y0 + i).toFixed(1)},${Yf(arr[i]).toFixed(1)} `;
      if (f > k) d += `L${X(Y0 + f).toFixed(1)},${Yf(lerp(arr, f)).toFixed(1)} `; return d; };
    const full = (arr, X, Yf) => arr.map((v, i) => `${i ? 'L' : 'M'}${X(Y0 + i).toFixed(1)},${Yf(v).toFixed(1)}`).join(' ');
    area.setAttribute('d', upto > 0 ? `M${XA(Y0)},${Y(0)} ` + pts(p.tot, XA, Y).replace(/^M/, 'L') + `L${XA(Y0 + f).toFixed(1)},${Y(0)} Z` : '');
    area.setAttribute('fill', p.col);
    ghost.setAttribute('d', ph.ghost ? full(P.a.tot, XA, Y) : '');
    glab.setAttribute('x', XA(2100) + 10); glab.setAttribute('y', Y(P.a.peak) + 6); glab.textContent = ph.ghost ? `7-Gt-Pfad` : '';
    let d = '', lx = 0, ly = 0;
    D.lim.forEach((v, i) => { if (v <= ymax * 1.02) { d += `${d ? 'L' : 'M'}${XA(Y0 + i).toFixed(1)},${Y(v).toFixed(1)} `; lx = XA(Y0 + i); ly = Y(v); } });
    lim.setAttribute('d', d); lab2.setAttribute('x', lx - 10); lab2.setAttribute('y', ly + 4);
    lab.setAttribute('x', XA(2100) + 10); lab.setAttribute('y', Y(lerp(p.tot, f)) - 6); lab.setAttribute('fill', p.light);
    lab.textContent = upto >= NY - 1 ? `${fmt(p.peak, 1)} Gt/a ab ${Y0 + iMax}` : '';
    dot1.setAttribute('cx', XA(Y0 + i1)); dot1.setAttribute('cy', Y(1)); lab1.setAttribute('x', XA(Y0 + i1) - 12); lab1.setAttribute('y', Y(1) - 12);
    dot1.style.opacity = lab1.style.opacity = upto >= i1 ? 1 : 0;
    // warming: Very Low and trees are known, the DAC line runs with the film; below zero only for "everything"
    zero.setAttribute('y1', YT(0)); zero.setAttribute('y2', YT(0)); zlab.setAttribute('y', YT(0) + 6);
    vlP.setAttribute('d', full(D.vl, XB, YT)); trP.setAttribute('d', full(D.tree, XB, YT));
    tLine.setAttribute('d', upto > 0 ? pts(p.dac, XB, YT) : ''); tLine.setAttribute('stroke', p === P.c ? '#6fe3c8' : '#ff5a4f');
    tArea.setAttribute('d', upto > 0 ? `M${XB(Y0)},${YT(0)} ` + pts(p.dac, XB, YT).replace(/^M/, 'L') + `L${XB(Y0 + f).toFixed(1)},${YT(0)} Z` : '');
    tArea.setAttribute('fill', p === P.c ? '#3fd0b0' : '#ff5a4f');
    tGhost.setAttribute('d', ph.ghost ? full(P.a.dac, XB, YT) : '');
    lVL.setAttribute('y', YT(D.vl[NY - 1]) - 8); lTr.setAttribute('y', YT(D.tree[NY - 1]) + 14);
    const end = p.dac[NY - 1];
    lDac.textContent = end < -5 ? `+ DAC: −${fmt(-end / 1000, 2)} K` : '+ DAC'; lDac.setAttribute('fill', p === P.c ? '#6fe3c8' : '#ff5a4f');
    lDac.setAttribute('y', YT(Math.min(0, end)) + (end < -5 ? 4 : 6)); lDac.style.opacity = upto >= NY - 1 ? 1 : 0;
    const low = tmin < -50; over.setAttribute('x', low ? XB(2027) : XB(Y0 + ip) - 60); over.setAttribute('y', low ? YT(0) + 24 : YT(70)); over.style.opacity = upto > ip + 6 ? 1 : 0;
    below.setAttribute('x', low ? XB(2027) : XB(Y0 + ip) - 60); below.setAttribute('y', low ? YT(0) + 48 : YT(70) + 24); below.setAttribute('text-anchor', 'start');
    below.textContent = p.below ? `1,5 °C ab ${p.below}` : ''; below.setAttribute('fill', p.light); below.style.opacity = p.below && upto > p.below - Y0 ? 1 : 0;
    for (const [c, X] of [[curA, XA], [curB, XB]]) { const xc = X(Y0 + f); c.setAttribute('x1', xc); c.setAttribute('x2', xc); c.style.opacity = upto > 0 && upto < NY - 1 ? 1 : 0; }
  }
  // hexagons as on the deck's other world maps: a pixel lattice the size of a 2° block, each hex the block under
  // its centre, coloured by the capacity in that block (sum of its cells), dim amber to full
  const PX = W / 360, R = Math.sqrt((2 * PX) ** 2 / 2.598), HW = Math.sqrt(3) * R;
  const blockOf = (x, y) => Math.floor(x / (2 * PX)) + ':' + Math.floor(y / (2 * PX));
  const members = new Map();
  XY.forEach(([x, y], i) => { const k = blockOf(x, y); if (!members.has(k)) members.set(k, []); members.get(k).push(i); });
  const HEX = [];
  for (let j = 0, py = 0; py <= H + R; j++, py = j * 1.5 * R)
    for (let px = j % 2 ? HW / 2 : 0; px <= W + HW; px += HW) { const m = members.get(blockOf(px, py)); if (m) HEX.push({ x: px, y: py, m }); }
  const corner = Array.from({ length: 6 }, (_, k) => [Math.cos(Math.PI / 180 * (60 * k - 90)), Math.sin(Math.PI / 180 * (60 * k - 90))]);
  // multi-hue ramp, dark red over orange and amber to pale yellow: neighbouring capacities stay apart on the dark map
  const STOPS = [[122, 38, 52], [205, 78, 45], [240, 176, 74], [255, 240, 190]];
  const ramp = (f) => { const x = Math.max(0, Math.min(1, f)) * (STOPS.length - 1), i = Math.min(STOPS.length - 2, Math.floor(x)), u = x - i;
    return `rgb(${STOPS[i].map((v, k) => Math.round(v + (STOPS[i + 1][k] - v) * u)).join(',')})`; };
  for (const q of Object.values(P)) q.bmax = Math.max(...HEX.map(h => h.m.reduce((n, i) => n + q.cell[i][NY - 1], 0)));   // plants run on: the last year is the largest
  const leg = document.createElement('div'); leg.className = 'leg';
  leg.innerHTML = `<span>Kapazität je 2°-Block</span><i style="background:linear-gradient(90deg,${[0, .25, .5, .75, 1].map(f => ramp(Math.sqrt(f))).join(',')})"></i><span>0</span><span>${fmt(P.a.bmax, 1)} Gt/a</span>`;
  sec.querySelector('.hud').append(leg);
  function map(p, t) {
    g.clearRect(0, 0, W, H);
    for (const h of HEX) {
      const v = h.m.reduce((q, i) => q + lerp(p.cell[i], t), 0); if (v <= 1e-6) continue;
      g.beginPath(); corner.forEach(([u, w], k) => g[k ? 'lineTo' : 'moveTo'](h.x + (R + .45) * u, h.y + (R + .45) * w)); g.closePath();
      g.fillStyle = ramp(Math.sqrt(v / p.bmax)); g.fill();
    }
  }
  function frame(ph, year, ymax, tmin) {
    const t = Math.max(0, Math.min(NY - 1, year - Y0)), p = ph.p;
    map(p, t); strip(ph, year > Y0 ? t : 0, ymax, tmin);
    yr.textContent = Math.floor(year);
    const cap = lerp(p.tot, t), cum = lerp(p.cum, t);
    nCap.firstChild.nodeValue = fmt(cap, cap < 1 ? 2 : 1) + ' ';
    nCum.firstChild.nodeValue = fmt(cum, 0) + ' ';
    cumNote.textContent = p === P.c ? `von ${fmt(P.c.speicher, 0)} Gt Speicher` : 'Gt netto entnommen';
  }
  const ease = f => f < .5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2;
  const DUR = 12000;
  // `drawn` names the resting picture on the canvas (a phase played out, or held still off screen): while it stays
  // the same nothing is drawn, since every write to the film's numbers restyles the whole deck
  let start = null, phase = -1, from = PH[0], drawn = null;
  function tick(now) {
    requestAnimationFrame(tick);
    const live = sec.classList.contains('active') && !(window.deck && window.deck.still);
    const k = trig.reduce((n, e, i) => e.classList.contains('shown') ? i + 1 : n, 0);
    if (k !== phase) { from = PH[Math.max(0, phase)] || PH[0]; phase = k; start = now;
      box.classList.toggle('late', PH[k].cls === 'late'); box.classList.toggle('max', PH[k].cls === 'max'); goal.textContent = PH[k].chip; }
    const f = live ? Math.min(1, (now - start) / DUR) : 1, e = ease(f), s = ease(Math.min(1, f * 4)), ph = PH[k];
    const rest = f < 1 ? null : (live ? 'live' : 'still') + k;
    if (rest !== null && rest === drawn) return;
    drawn = rest;
    const ym = from.ym + (ph.ym - from.ym) * s, tm = from.tmin + (ph.tmin - from.tmin) * s;
    if (k === 0) { frame(ph, Y0, ph.ym, 0); g.clearRect(0, 0, W, H); }
    else frame(ph, Y0 + e * (NY - 1), ym, tm);
  }
  requestAnimationFrame(tick);
})();
