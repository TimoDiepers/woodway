/* ===========================================================
   KaTeX
   Symbol colours: every coloured symbol carries a colour-role
   class (.c-co2, .c-alb, ... in deck.css), the same class the
   chips, frames and badges use, so a symbol and its chip always
   match and the dark slides recolour them through tokens.
   =========================================================== */
const TEX_MACROS = {
  // generic: a term in a role colour (\fc{par}{…}), a symbol of its own (\q{dm}{…}, bold), a framed term (\hl{dt on}{…})
  "\\fc":   "\\htmlClass{f c-#1}{#2}",
  "\\q":    "\\fc{#1}{\\boldsymbol{#2}}",
  "\\hl":   "\\htmlClass{hl c-#1}{#2}",              // lit by .on or a slide trigger (deck.css, "Highlight")
  "\\tm":   "\\boldsymbol{t}",                    // the time, a symbol like the others
  "\\tp":   "\\boldsymbol{t'}",                   // an earlier time (the integrals of the backup)
  "\\tz":   "\\boldsymbol{t_0}",                   // the start
  "\\st":   "\\htmlData{step=#1}{#2}",               // \st{2}{…}: this term appears on click 2
  // the symbols of the talk: one macro and one colour each (deck.css, "Symbol colours"); only the variable is coloured,
  // with its indices; d, dt, the brackets and (t) stay in ink. The heat flows are dotted (q̇, Q̇), the other rates written
  // bare (dm/dt); a function carries its argument (m(t)). Indices: B tree, W cloud, Bo ground, atm atmosphere, PS ZA ZS ST the four carbon fluxes
  "\\rate":  "\\dfrac{\\mathbf{d}\\,#1}{\\mathbf{d}\\tm}",   // \rate{\mB} = dm_B/dt
  // carbon in the tree
  "\\mB":   "\\q{mb}{m^{\\raisebox{0.05em}{$\\scriptscriptstyle\\mathrm{C}$}}_{\\mathrm{B}}}",   // carbon in the tree (C: the element, not the whole mass); C one size smaller, so it does not crowd the B
  "\\mBd":  "\\rate{\\mB}",
  "\\mBu":  "\\q{mb}{\\dot{m}^{\\raisebox{0.05em}{$\\scriptscriptstyle\\mathrm{C}$}}_{\\mathrm{B}}}",   // the tree's carbon uptake per year (F18, convolved with psi)                         // the balance, as a rate
  "\\mPS":  "\\q{ps}{\\dot{m}^{\\raisebox{0.05em}{$\\scriptscriptstyle\\mathrm{C}$}}_{\\mathrm{PS}}}",     // a flux: kg C per year
  "\\mZA":  "\\q{re}{\\dot{m}^{\\raisebox{0.05em}{$\\scriptscriptstyle\\mathrm{C}$}}_{\\mathrm{ZA}}}",
  "\\mZS":  "\\q{zs}{\\dot{m}^{\\raisebox{0.05em}{$\\scriptscriptstyle\\mathrm{C}$}}_{\\mathrm{ZS}}}",
  "\\mST":  "\\q{st}{\\dot{m}^{\\raisebox{0.05em}{$\\scriptscriptstyle\\mathrm{C}$}}_{\\mathrm{ST}}}",
  "\\mmax": "\\q{mmax}{m^{\\raisebox{0.05em}{$\\scriptscriptstyle\\mathrm{C}$}}_{\\mathrm{max}}}",   // carbon, as \mB
  "\\kw":   "\\q{kw}{k}",                             // growth rate
  "\\pw":   "\\q{pw}{p}",                             // shape parameter
  "\\sz":   "\\q{sz}{s_{0}}",                         // disturbance rate, pre-industrial
  "\\gam":  "\\q{gam}{\\gamma}",                      // rise of the disturbance rate
  "\\pd":   "\\q{pd}{p}",                             // disturbance probability
  "\\pdo":  "\\q{pdo}{p_0}",
  "\\md":   "\\rate{\\q{md}{m}}",                    // the tree's carbon uptake
  // sunlight, energy, albedo
  "\\qin":  "\\q{qin}{\\dot{q}_{\\mathrm{ein}}}",
  "\\alb":  "\\q{alb}{\\alpha}",
  "\\dal":  "\\q{dal}{\\Delta\\alpha_{\\mathrm{B}}}",   // B: Baum
  "\\daw":  "\\q{daw}{\\Delta\\alpha_{\\mathrm{W}}}",
  "\\alw":  "\\q{alw}{\\Delta\\alpha_{\\mathrm{Wolke}}}",   // a contrast: how much more a cloud reflects than the ground
  "\\dfw":  "\\q{dfw}{\\Delta f_{\\mathrm{W}}}",
  "\\dQ":   "\\q{dq}{\\dot{Q}_{\\alpha}}",
  "\\Ab":   "\\q{ab}{A_{\\mathrm{B}}}",
  "\\Ae":   "\\q{ae}{A_{\\mathrm{atm}}}",
  "\\tatm": "\\q{tau}{\\tau}",
  // radiative forcing: the sum, its two parts in their channel's colour
  "\\phit": "\\q{phi}{\\Delta\\varphi_{\\mathrm{B}}}",
  "\\phio": "\\q{phio}{\\Delta\\varphi_0}",
  "\\phia": "\\q{phia}{\\Delta\\varphi_\\alpha}",
  "\\phic": "\\q{phic}{\\Delta\\varphi_{\\mathrm{CO_2}}}",
  // the energy balance of the atmosphere (the system boundary at its top): E, the flux densities in and out, their difference
  "\\Een":  "\\q{e}{E}",
  "\\pin":  "\\q{pin}{\\varphi^{\\mathrm{kw}}_{\\mathrm{ein}}}",     // sunlight in, shortwave
  "\\pkw":  "\\q{pkw}{\\varphi^{\\mathrm{kw}}_{\\mathrm{ref}}}",     // reflected, shortwave out
  "\\plw":  "\\q{pout}{\\varphi^{\\mathrm{lw}}_{\\mathrm{ab}}}",    // heat radiation, longwave out
  "\\dphi": "\\q{dphi}{\\Delta\\varphi_{\\mathrm{ges}}}",
  "\\dphiO": "\\q{dphio}{\\Delta\\varphi^{\\mathrm{Base}}_{\\mathrm{ges}}}",   // the world without our tree: the reference
  "\\dphiM": "\\q{dphi}{\\Delta\\varphi^{\\mathrm{B}}_{\\mathrm{ges}}}",   // the same world with our additional tree
  // CO2 in the atmosphere
  "\\eps":  "\\q{eps}{\\varepsilon_{\\mathrm{CO_2}}}",
  "\\dm":   "\\q{dm}{\\Delta m_{\\mathrm{CO_2}}}",
  "\\psc":  "\\q{psi}{\\psi_{\\mathrm{CO_2}}}",                // impulse response of the earth: share of an emitted pulse still in the air
  "\\MCO":  "\\fc{par}{\\boldsymbol{M}_{\\mathrm{CO_2}}}",   // molar masses [g/mol]: C to CO2
  "\\MC":   "\\fc{par}{\\boldsymbol{M}_{\\mathrm{C}}}",
  "\\mco":  "\\q{mdc}{m_{\\mathrm{CO_2}}}",
  "\\mdc":  "\\rate{\\mco}",
  "\\gC":   "\\q{gc}{g_C}",
  "\\cc":   "\\q{conc}{c}",
  "\\cz":   "\\q{conco}{c_0}",
  "\\matm": "\\q{matm}{m}",
  "\\katm": "\\q{katm}{k}",
  "\\mch":  "\\q{ch4}{m_{\\mathrm{CH_4}}}",
  // temperature and the energy balance
  "\\dT":   "\\q{dt}{\\Delta T}",
  "\\T":    "\\q{dt}{T}",
  "\\dTw":  "\\q{dt}{\\Delta T_{\\mathrm{w}}}",
  "\\dTB":  "\\q{dt}{\\Delta T_{\\mathrm{B}}}",                         // the temperature effect of our tree alone
  "\\dTO":  "\\q{dt}{T^{\\mathrm{Base}}_{\\mathrm{ges}}}",      // the temperature of the world without our tree
  "\\dTM":  "\\q{dt}{T^{\\mathrm{B}}_{\\mathrm{ges}}}",         // the same world with it
  "\\Rf":   "\\q{rf}{R}",
  "\\Sk":   "\\q{sk}{S}",
  "\\fT":   "\\q{ft}{f}",
  // constants and other parameters
  "\\pc":   "\\q{par}{#1}",
  // family colours, kept for one-off symbols
  "\\sc":   "\\q{sz}{#1}",
  "\\bq":   "\\q{dq}{#1}",
  "\\rq":   "\\q{gc}{#1}",
  "\\cq":   "\\q{phic}{#1}",
  "\\mq":   "\\q{ch4}{#1}",
  "\\aq":   "\\q{phia}{#1}",
  "\\tq":   "\\q{dt}{#1}",
  "\\gq":   "\\q{ab}{#1}"
};

// the figures' own formula labels (mpl texts that are one $…$) and the colour role of the symbol they show
const CHART_TEX_ROLE = {
  '\\dot{q}_{\\mathrm{ein}}': 'qin', '\\Delta\\alpha_{\\mathrm{L}}': 'dal', '\\Delta\\alpha_{\\mathrm{B}}': 'dal',
  '\\Delta\\alpha_{\\mathrm{W}}': 'daw', '\\dot{Q}_{\\alpha}': 'dq'
};

/* y-axis titles: an HTML label (.axlab) in the deck's axis face (Plex, muted, 17-19px), set with KaTeX, so a symbol on
   an axis looks as in the formulas (macro, colour role, bold). A $…$ in the title marks the symbol; the words around
   it stay ("Kohlenstoffvorrat $\mB$ [kg C]"). ECharts: yAxis.nameTex; figures from matplotlib: every y title, with
   the formula version from the table below where there is one (keyed by the figure's own title) */
const MPL_AXIS_TEX = {
  'Kohlenstoffvorrat mᶜBaum [kg C]': 'Kohlenstoffvorrat $\\mB$ [kg C]',
  'Antrieb [W/m²]': 'Antrieb $\\phit(\\cc)$ [W/m²]',
  'Antrieb je kg [10⁻¹⁵ W/m²]': '$\\eps$ [10⁻¹⁵ W/m² je kg]',
  'Antrieb [10⁻¹⁵ W/m² je Baum]': 'Antrieb $\\phit$ [10⁻¹⁵ W/m² je Baum]',
  'Wirkung je Baum im Jahr 2100 [10⁻¹⁵ K]': '$\\dT$ je Baum 2100 [10⁻¹⁵ K]',
  'Temperatur je Baum 2100 [10⁻¹⁵ K]': '$\\dT$ je Baum 2100 [10⁻¹⁵ K]'
};
function axTex(host, key, tex, x, y, fontPx) {
  // one label per key, kept between pictures (no flicker), moved to (x, y) in the host's pixels, rotated as an axis title
  let el = host.querySelector(`:scope > .axlab[data-key="${key}"]`);
  if (!el) {
    el = document.createElement('span'); el.className = 'axlab'; el.dataset.key = key;
    for (const part of tex.split(/(\$[^$]+\$)/)) {
      if (!part) continue;
      const sp = document.createElement('span');
      if (part.startsWith('$') && window.katex) katex.render(part.slice(1, -1), sp, { macros: TEX_MACROS, throwOnError: false, strict: false, trust: c => c.command === '\\htmlClass' });
      else sp.innerHTML = supHTML(tipEsc(part.replace(/^\$|\$$/g, ''))).replace(/kg C(?![O₂])/g, 'kg<sub>C</sub>');   // carbon as the unit's index, as on the slides
      el.append(sp);
    }
    host.append(el);
  }
  Object.assign(el.style, { left: x + 'px', top: y + 'px', fontSize: fontPx ? fontPx + 'px' : '' });
  return el;
}

function renderTex(root) {
  // Walk text nodes, replacing $$…$$ (display) and $…$ (inline).
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) if (walker.currentNode.nodeValue.includes('$') && !walker.currentNode.parentElement.closest('.notes, svg')) nodes.push(walker.currentNode);
  let tk = 0;   // each formula numbered in the slide, its source kept: the editor (Deck.texEdit, deck/serve.py) finds it again
  for (const node of nodes) {
    const parts = node.nodeValue.split(/(\$\$[\s\S]+?\$\$|\$[^$]+?\$)/g);
    if (parts.length === 1) continue;
    const frag = document.createDocumentFragment();
    for (const part of parts) {
      if (!part) continue;
      const display = part.startsWith('$$');
      if (part.startsWith('$') && part.endsWith('$') && part.length > 1) {
        const span = document.createElement('span');
        span.dataset.tk = tk++; span.dataset.tsrc = part;
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
// The talk's three chapters, two parts each (data-ch, data-part on the slides). The disc is the overview's (index.html
// #e-…), the part icons #p-…; each part's colour is --p-<key> (fill) and --t-<key> (text)
const CHAPTERS = {
  baeume: { name: 'Baum-Modell', disc: 'e-baeume', col: 'var(--moss)', parts: [['co2', 'Zeitverlauf'], ['refl', 'Reflexionsänderung']] },
  klima: { name: 'Klima-Modell', disc: 'e-klima', col: 'var(--clay)', parts: [['bal', 'Strahlungshaushalt'], ['temp', 'Temperaturantwort']] },
  vergleich: { name: 'Potenziale', disc: 'e-potenzial', col: 'var(--fjord)', parts: [['one', 'Kühlung eines Baums'], ['world', 'Kühlung der Welt']] },
};
// A chapter's disc in its ring of two arcs, one per part (right: the first, left: the second). Each arc 'off' (not
// drawn yet), 'track' (still to come, pale), 'on' (the part we are in, in its colour) or 'done' (chapter colour).
// With a part (1, 2) the disc is that part's sign instead (#p-…, the same circle): the corner indicator
function ringSvg(ch, arcs, part) {
  const c = CHAPTERS[ch], sym = part ? `p-${c.parts[part - 1][0]}` : c.disc;
  return `<svg class="ring" viewBox="-14 -14 128 128" aria-hidden="true" style="--c:${c.col}"><use href="#${sym}" width="100" height="100"/>`
    + c.parts.map(([k], j) => `<circle class="arc ${arcs[j]}" style="--a:var(--p-${k})" cx="50" cy="50" r="57" pathLength="360" transform="rotate(${j ? 94 : -86} 50 50)"/>`).join('')
    + '</svg>';
}
function E(tag, attrs, parent) {
  const e = document.createElementNS(SVGNS, tag);
  for (const k in attrs) if (attrs[k] !== null && attrs[k] !== undefined) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
/* superscript numbers (10⁻¹⁵): Plex is loaded without the superscript block, so ⁰ ⁴–⁹ ⁻ would come from a fallback
   face of another height. Written as text with a raised, smaller run instead: <sup> in HTML, a rich-text token in charts */
const SUP_RE = /[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]*[⁰⁴⁵⁶⁷⁸⁹⁺⁻][⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]*/g;
const SUP_MAP = { '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁺': '+', '⁻': '−' };
const supPlain = r => [...r].map(c => SUP_MAP[c] || c).join('');
const supHTML = html => String(html).replace(SUP_RE, r => `<sup class="sx">${supPlain(r)}</sup>`);
function supText(root) {   // every text node outside drawings and formulas
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), hits = [];
  while (w.nextNode()) { const n = w.currentNode; SUP_RE.lastIndex = 0; if (SUP_RE.test(n.nodeValue) && !n.parentElement.closest('svg, .katex, script, style, template')) hits.push(n); }
  for (const n of hits) {
    const frag = document.createDocumentFragment();
    let last = 0; n.nodeValue.replace(SUP_RE, (r, at) => {
      if (at > last) frag.append(n.nodeValue.slice(last, at));
      const sup = document.createElement('sup'); sup.className = 'sx'; sup.textContent = supPlain(r); frag.append(sup); last = at + r.length; return r; });
    if (last < n.nodeValue.length) frag.append(n.nodeValue.slice(last));
    n.replaceWith(frag);
  }
}
/* Holzweg slide: it opens on the summary's last picture, takeaway 3 with two phrases in gold. As each card comes in,
   its heading flies out of the matching phrase into place, growing from the phrase's size to the heading's.
   Only when stepping forward on the open slide; a jump to the slide (or backwards) just shows the end state. */
function holzwegFly(slide) {
  const srcs = [...slide.querySelectorAll('.hw-fz3 .fz-k')];
  const pairs = [...slide.querySelectorAll('.hwv .hwk3')].map((card, i) => ({ card, src: srcs[i], dst: card.querySelector('.hw-h') })).filter(q => q.src && q.dst);
  // word by word: a phrase that wraps in takeaway 3 flies as its words, each from its own line
  const words = el => { el.innerHTML = el.textContent.trim().split(/\s+/).map(w => `<span>${w}</span>`).join(' '); return [...el.children]; };
  for (const q of pairs) { q.sw = words(q.src); q.dw = words(q.dst); }
  // coming from the summary, the first card follows at once; coming back (or a reload) nothing flies
  let ok = false;
  new MutationObserver(() => {
    if (!slide.classList.contains('active')) { ok = false; return; }
    if (ok) return;
    const d = window.deck;
    setTimeout(() => { ok = true; if (d && d.slides[d.i] === slide && d.step === 0 && !d.still) d.next(); }, 0);
  }).observe(slide, { attributes: true, attributeFilter: ['class'] });
  for (const q of pairs) {
    let was = q.card.classList.contains('shown');
    new MutationObserver(() => {
      const on = q.card.classList.contains('shown');
      if (on === was) return;
      was = on;
      q.src.style.visibility = on ? 'hidden' : '';
      q.dst.style.visibility = '';
      if (on && ok && slide.classList.contains('active') && !matchMedia('(prefers-reduced-motion: reduce)').matches) fly(q);
    }).observe(q.card, { attributes: true, attributeFilter: ['class'] });
  }
  function fly({ card, sw, dw, dst }) {
    const b = slide.getBoundingClientRect(), k = b.width / slide.offsetWidth, cs = getComputedStyle(dst);
    const at = el => { const r = el.getBoundingClientRect(); return [(r.left - b.left) / k, (r.top - b.top) / k]; };
    const sc0 = parseFloat(getComputedStyle(sw[0]).fontSize) / parseFloat(cs.fontSize);
    const from = sw.map(at);   // the takeaway stays put; the card is still rising, so its words are read every frame
    const clones = dw.map(w => {
      const c = document.createElement('span');
      c.textContent = w.textContent;
      Object.assign(c.style, { position: 'absolute', left: 0, top: 0, margin: 0, zIndex: 50, whiteSpace: 'nowrap', pointerEvents: 'none',
                               font: cs.font, lineHeight: 'normal', color: cs.color, transformOrigin: '0 0' });
      slide.append(c); return c;
    });
    dst.style.visibility = 'hidden';
    const T = 950, LAG = 35, t0 = performance.now(), ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    (function frame(now) {
      let done = true;
      clones.forEach((c, i) => {
        const t = Math.min(1, Math.max(0, (now - t0 - i * LAG) / T)), e = ease(t); if (t < 1) done = false;
        const [ex, ey] = at(dw[i]), [sx, sy] = from[i], sc = sc0 + (1 - sc0) * e;
        c.style.transform = `translate(${sx + (ex - sx) * e}px, ${sy + (ey - sy) * e}px) scale(${sc})`;
      });
      if (!done && slide.classList.contains('active')) return requestAnimationFrame(frame);
      clones.forEach(c => c.remove());
      if (card.classList.contains('shown')) dst.style.visibility = '';
    })(t0);
  }
}
/* the closing scene builds up as the night lifts: first the trees grow, left to right, then the animals, the people's
   things and the motion come in, and the labels last (after the headline). Each piece is wrapped in its own group,
   so the animations already on the pieces (walking, swinging, flying) keep running */
function endeStage(svg) {
  const LATE = '.deer, .fox, .ende-hare, .swing, .balance, .hammock, .logs, .squirrel, .pond, .frog, .cut';
  const wrap = (el, cls, d) => { const g = document.createElementNS('http://www.w3.org/2000/svg', 'g'); g.setAttribute('class', cls); g.style.setProperty('--d', d.toFixed(2) + 's'); el.before(g); g.append(el); };
  const x = el => { const m = /translate\(\s*(-?[\d.]+)/.exec(el.getAttribute('transform') || ''); return m ? +m[1] : 800; };
  let late = 0;
  const lateD = () => 2.6 + (late++ % 12) * 0.13;
  const box = [...svg.children].find(c => c.getAttribute('transform') === 'translate(0 -0)');
  if (box) for (const el of [...box.children]) {
    if (el.matches('.balance') || el.querySelector('.balance')) wrap(el, 'e-dank', 0.4);   // the vegan comparison: only with the thanks
    if (el.matches(LATE) || el.querySelector(LATE)) wrap(el, 'e-late', lateD());
    else if (el.querySelector('.m-sway') || /scale/.test(el.getAttribute('transform') || '')) {
      for (const owl of el.querySelectorAll('.owl')) wrap(owl, 'e-late', 3.4);
      wrap(el, 'e-tree', 0.5 + x(el) / 1600 * 1.8);
    }
    else if (el.tagName === 'g') wrap(el, 'e-late', lateD());   // a person
    else if (el.tagName === 'path' && !/^#(dde3cc|cbd6b4)$/.test(el.getAttribute('fill'))) wrap(el, 'e-dank e-branch', 0);   // the branch the balance hangs from: with the thanks, before the balance
  }
  for (const el of [...svg.children]) if (el.matches('.fly-l, .fly-r, .vapor, .tt-wander') || el.querySelector(':scope > .tt-co2, :scope > .tt-wander, .rain')) wrap(el, 'e-late', lateD());
}
function supRichText(text, f, color) {   // chart text with superscript runs as rich tokens; null when there are none
  SUP_RE.lastIndex = 0; if (!text || !SUP_RE.test(text)) return null;
  const n = f.fontSize, base = { fontFamily: f.fontFamily, fontWeight: f.fontWeight, fontStyle: f.fontStyle, color, verticalAlign: 'bottom' };
  const esc = x => x.replace(/[{}|]/g, '');
  const line = l => { let out = '', last = 0; l.replace(SUP_RE, (r, at) => { if (at > last) out += `{n|${esc(l.slice(last, at))}}`; out += `{sp|${supPlain(r)}}`; last = at + r.length; return r; });
                      if (last < l.length) out += `{n|${esc(l.slice(last))}}`; return out; };
  return { formatter: String(text).split('\n').map(line).join('\n'),
           rich: { n: { ...base, fontSize: n, lineHeight: n * 1.18 }, sp: { ...base, fontSize: n * .66, lineHeight: n * 1.18, padding: [0, 0, n * .42, 0] } } };
}
/* a chart text with a letter subscript (q̇_ein): rich text, the subscript smaller and lower */
function subRich(t, f) {
  if (!t.sub) return supRichText(t.s, f, t.c) || {};
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
  ink: '#1b2420', ink2: '#3f4a44', muted: '#5d665f', line: '#d6ccb6', grid: '#e4dccb', alb: '#706a19', alle: '#04455f', rodung: '#9a6b0a',   // = --s-phia
  font: "'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif"
};
/* one pace for every curve in the deck: a line or area is drawn in from the left in DRAW_MS at a constant speed
   (the forest sketch's CSS draw-in and the curve names of EChart.placeLabels use the same). Applied to every option
   before it is set; a series with keepPace (the observed warming on slide 2, drawn slowly on purpose) or a short
   entrance of its own (dots, < 1 s) keeps its timing */
const DRAW_MS = 1600;
function ecDraw(opt) {
  for (const sr of [].concat(opt.series || [])) {
    if (!sr || sr.type !== 'line' || sr.keepPace || sr.animation === false) continue;
    if (sr.animationDuration !== undefined && sr.animationDuration < 1000) continue;
    sr.animationDuration = DRAW_MS; sr.animationEasing = 'linear';
    if (sr.markPoint && typeof sr.markPoint.animationDelay === 'number' && sr.markPoint.animationDelay > DRAW_MS) sr.markPoint.animationDelay = DRAW_MS;
  }
  return opt;
}
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
/* Tooltips: one look for every chart in the deck. They live inside the 1600x900 canvas, which is scaled to the
   screen, so on a phone a 17px tooltip would end up at 7px: --tipk (Deck.fit) scales them back up. Hover on a
   desktop, tap on a touch screen (triggerOn click); confine keeps them inside the chart. */
function ecTooltip(extra) {
  return Object.assign({
    confine: true, triggerOn: 'mousemove|click', transitionDuration: .15, enterable: false, className: 'ectip',   // .ectip: H hides them (Deck.tips)
    backgroundColor: 'rgba(251,248,241,.97)', borderColor: EC.line, borderWidth: 1, padding: [8, 12],
    textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 17 },
    extraCssText: 'box-shadow:0 6px 18px -8px rgba(40,34,20,.35); border-radius:6px; font-size:calc(17px * var(--tipk, 1)) !important;'
                + 'line-height:1.45; padding:calc(8px * var(--tipk, 1)) calc(12px * var(--tipk, 1)) !important; max-width:calc(420px * var(--tipk, 1)); white-space:normal;'
  }, extra);
}
// a colour dot; a near-white line of the dark slides gets a dark ring, so it shows on the light tooltip
const ecDot = c => { const h = /^#([0-9a-f]{6})$/i.exec(c || ''), lum = h ? [0, 2, 4].map(i => parseInt(h[1].slice(i, i + 2), 16)).reduce((a, v) => a + v, 0) / 765 : 0;
  return `<span style="display:inline-block;width:.6em;height:.6em;border-radius:50%;background:${c};margin-right:.4em;box-sizing:border-box;${lum > .85 ? 'border:1.5px solid #5d665f' : ''}"></span>`; };
const ecSigned = (v, d) => ecNum(v, d).replace('-', '−');
/* The one layout of every tooltip in the deck (styles: .tc in deck.css): a bold head (the year, the place, the
   category), an optional grey line saying what is measured, then rows of colour dot, name and value. */
const tipEsc = t => supHTML(String(t ?? '').replace(/&(?![a-z#0-9]+;)/gi, '&amp;').replace(/</g, '&lt;'));
function tipCard({ head, sub, rows = [], note }) {
  if (sub && head && String(sub).trim() === String(head).trim()) sub = '';   // no line that says the head again
  const r = rows.filter(Boolean).map(({ c, name, v }) =>
    `<div class="tc-r">${c ? ecDot(c) : ''}${name ? `<span class="tc-n">${tipEsc(name)}</span>` : ''}${v !== undefined && v !== '' ? `<b class="tc-v">${v}</b>` : ''}</div>`).join('');
  return `<div class="tc">${head ? `<div class="tc-h">${tipEsc(head)}</div>` : ''}${sub ? `<div class="tc-s">${tipEsc(sub)}</div>` : ''}${r}${note ? `<div class="tc-s">${tipEsc(note)}</div>` : ''}</div>`;
}
const tipVal = (v, d, u) => `${ecSigned(v, d)}${u ? '\u202f' + supHTML(u) : ''}`;
// a place on a map, rounded to whole degrees, and the named site if it is right there
function tipPlace(lon, lat) {
  const ns = `${Math.abs(Math.round(lat))}° ${lat >= 0 ? 'N' : 'S'}`, ew = `${Math.abs(Math.round(lon))}° ${lon >= 0 ? 'O' : 'W'}`;
  const site = (window.MAPDATA && window.MAPDATA.sites || []).find(q => Math.abs(q.lon - lon) < 1.2 && Math.abs(q.lat - lat) < 1.2);
  return `${ns} · ${ew}${site ? ` (bei ${site.name.replace(/\s*\(.*\)/, '')})` : ''}`;
}
/* The default tooltip of a chart whose spec names its unit (spec.tip = { unit, dec, k }): the year, then every
   series that has a label (tipName, else its name without a trailing [unit]), at the value it shows there.
   A series can carry its own unit (tip: { unit, k, dec }), absolute values for a stacked band (tipData),
   or tip: false. spec.tip.item: a formatter for pie and other item charts instead. */
function ecAutoTip(opt, spec) {
  const T = spec && spec.tip;
  if (!T || opt.tooltip !== undefined) return opt;
  if (T.item) { opt.tooltip = ecTooltip({ trigger: 'item', formatter: T.item }); return opt; }
  const S = [].concat(opt.series || []);
  const lab = s => s && s.tip !== false && (s.tipName || (s.name || '').replace(/\s*\[[^\]]*\]\s*$/, '').trim());
  opt.tooltip = ecTooltip({ trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: EC.muted, type: [3, 3] } },
    formatter: ps => {
      const seen = new Set(), rows = [];
      for (const p of ps) {
        const sr = S[p.seriesIndex], name = lab(sr);
        if (!name || seen.has(name)) continue;
        const raw = sr.tipData ? sr.tipData[p.dataIndex] : (Array.isArray(p.value) ? p.value[1] : p.value);
        if (raw === null || raw === undefined || !isFinite(raw)) continue;
        const m = Object.assign({ unit: T.unit, k: T.k || 1, dec: T.dec === undefined ? 1 : T.dec }, sr.tip || {});
        const c = typeof p.color === 'string' ? p.color : (sr.itemStyle && sr.itemStyle.color) || EC.muted;
        seen.add(name); rows.push({ c, name, v: tipVal(raw * m.k, m.dec, m.unit) });
      }
      if (!rows.length) return '';
      const x = Array.isArray(ps[0].value) ? ps[0].value[0] : ps[0].axisValue;
      return tipCard({ head: String(Math.round(x)), sub: T.sub, rows });
    } });
  return opt;
}

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
      lineStyle: { color: EC.ink, width: 2.2 }, itemStyle: { color: EC.ink }, z: 5, animationDuration: 4200, animationEasing: 'linear', keepPace: true,
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
                    animationDuration: 4200, animationEasing: 'linear', animationDelay: 0, keepPace: true });
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
          return tipCard({ head: String(year), sub: 'Erwärmung, Median', rows: rows.sort((a, b) => b.value[1] - a.value[1])
            .filter(p => !seen.has(p.seriesName.trim()) && seen.add(p.seriesName.trim()))
            .map(p => ({ c: p.color, name: p.seriesName.trim(), v: tipVal(p.value[1], 2, '°C') })) });
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
            return tipCard({ head: lab(c.k), sub: 'CO₂-Entnahme 2024–2100', rows: [{ c: col(c.k), v: `${neg(-c.total)}\u202fGt CO₂` }] });
          }
          return tipCard({ head: String(p.value[0]), sub: 'CO₂-Entnahme seit 2024', rows: [{ c: p.color, name: p.seriesName.trim(), v: `${neg(p.value[1])}\u202fGt CO₂` }] });
        }
      }),
      series
    };
  }
};


/* slide 2, the problem: what the climate does, for everyone in the room, told with the UNEP Emissions Gap Report 2026
   and drawn with the CMIP7 curves that match it. Click 0 the observed warming up to today,
   1 the policies in force today (CMIP7 Medium, UNEP 2.8 deg C), 2 the best scenario (the reference of chapters 4 and 5: Very Low without its own
   removal, ZEIT.vl_c, same grey and dash as the anchor), 3 red the gap that stays above 1.5 deg C (the anchor's red band).
   Each series runs in on its own click and stands still afterwards. */
const KURS_COL = { obs: EC.ink, med: '#b5562e', vl: '#6d756f', rot: '#c4121f' };
const EC_KURS = { steps: 2,
  // every curve is drawn by the deck itself, frame by frame (tween): the line of the current click reaches year
  // t of its span, at the same pace for all of them (75 years in 2.6 s) and from its own first year, without the
  // lag of the ECharts entrance, which sweeps over the whole axis from 1950; the opening picture sweeps once over the
  // whole axis, the measurements and then the policy of today
  tween: 2600, intro: 4400, linear: true, tip: { unit: '°C', dec: 2 },
  option(k, t = 1) {
  const C = window.CMIP7, Z = window.ZEIT, vl = Z.vl_c, P = ys => Z.jahre.map((y, i) => [y, ys[i]]);
  const upto = (from, to, at) => k === at ? from + (to - from) * t : (k > at ? to : from);
  const cut = (pts, x) => {   // the points up to year x, the last one interpolated, so the tip moves smoothly
    const out = pts.filter(p => p[0] <= x), n = pts.find(p => p[0] > x), l = out[out.length - 1];
    if (l && n && x > l[0]) out.push([x, l[1] + (n[1] - l[1]) * (x - l[0]) / (n[0] - l[0])]);
    return out;
  };
  const iPeak = vl.indexOf(Math.max(...vl)), sweep = k === 0 ? 1950 + 150 * t : 2100;
  const series = [{
    id: 'obs', name: 'Beobachtung', type: 'line', showSymbol: false, data: cut(C.obs.y.map((y, i) => [y, C.obs.v[i]]), Math.min(2025, sweep)), z: 5,
    lineStyle: { color: KURS_COL.obs, width: 2.4 }, itemStyle: { color: KURS_COL.obs },
    // the 1.5 deg C line, and today (2026, where the scenarios start; the measurements end a year earlier)
    markLine: { silent: true, symbol: 'none', animation: false, lineStyle: { color: EC.ink, width: 1.6, type: 'solid', opacity: .7 },
                label: { show: false, color: EC.ink, fontFamily: EC.font, fontSize: 19 },
                data: [{ yAxis: 1.5 }, { xAxis: 2026, lineStyle: { color: EC.muted, width: 1.4, type: [4, 5], opacity: 1 },
                                         label: { show: true, position: 'end', distance: 8, color: EC.ink, fontWeight: 600, formatter: 'heute' } }] }
  }];
  if (sweep > 2026) {   // as today: CMIP7 Medium, about the policies in force now, straight on from the measurements; its label rides on the tip of the line
    const M = C.temp.M, pm = M.y.map((y, i) => [y, M.med[i]]).filter(p => p[0] >= 2026 && p[0] <= 2100);
    series.push({ id: 'med', name: 'heutige Politik', type: 'line', showSymbol: false, data: cut(pm, sweep), z: 4,
      lineStyle: { color: KURS_COL.med, width: 3, opacity: k >= 1 ? .45 : 1 }, itemStyle: { color: KURS_COL.med },
      endLabel: { show: true, align: 'right', offset: [-6, -20], color: KURS_COL.med, opacity: k >= 1 ? .55 : 1, fontFamily: EC.font, fontSize: 19, fontWeight: 600,
                  formatter: 'heutige Politik: 2,8 °C in 2100' } });   // the number is UNEP's (2.8), the curve CMIP7's (2.98)
  }
  if (k >= 1) {
    const x = upto(2026, 2100, 1);
    series.push({ id: 'vl', name: 'Best Case Szenario', type: 'line', showSymbol: false, data: cut(P(vl), x), z: 5,
      lineStyle: { color: KURS_COL.vl, width: 3, type: [8, 6] }, itemStyle: { color: KURS_COL.vl },
      // two lines, right-aligned above the tip: clear of the curve and of the peak's label at 2050
      endLabel: { show: true, align: 'right', offset: [-6, -40], color: KURS_COL.vl, fontFamily: EC.font, fontSize: 19, fontWeight: 600, lineHeight: 23,
                  formatter: 'Best Case Szenario*:\n1,7 °C in 2100' },   // UNEP's 2100 value, as for the policy line
      markPoint: { silent: true, symbol: 'circle', symbolSize: 11, itemStyle: { color: KURS_COL.vl, borderColor: '#f2ede2', borderWidth: 2 },
                   // left of the point and lifted off the rising curve, on a paper halo where it crosses the faint
                   // policy line: the curve's own label takes the space to the right
                   label: { show: true, position: 'left', distance: 10, offset: [0, -16], color: KURS_COL.vl, fontFamily: EC.font, fontSize: 19, fontWeight: 600,
                            textBorderColor: '#f2ede2', textBorderWidth: 4, formatter: `Spitze ${Z.jahre[iPeak]}: ${ecNum(vl[iPeak], 2)} °C` },
                   data: x >= Z.jahre[iPeak] ? [{ coord: [Z.jahre[iPeak], vl[iPeak]] }] : [] } });
  }
  if (k >= 2) {
    const over = vl.map(v => Math.max(v - 1.5, 0)), x = upto(2026, 2100, 2), i = Z.jahre.indexOf(2068);
    series.push({ id: 'rb', tip: false, type: 'line', stack: 'rot', stackStrategy: 'all', data: cut(P(vl.map(() => 1.5)), x), showSymbol: false, silent: true, lineStyle: { width: 0 } },
      { id: 'rr', tipName: 'Lücke über 1,5 °C', type: 'line', stack: 'rot', stackStrategy: 'all', data: cut(P(over), x), showSymbol: false, silent: true, z: 2, lineStyle: { width: 0 },
        itemStyle: { color: KURS_COL.rot }, areaStyle: { color: KURS_COL.rot, opacity: .28 },
        markPoint: { silent: true, symbol: 'circle', symbolSize: 0, data: x >= 2096 ? [{ coord: [2068, 1.5 + over[i] / 2] }] : [],
                     label: { show: true, position: 'inside', color: '#8e0d16', fontFamily: EC.font, fontSize: 20, fontWeight: 600, formatter: '320 Gt CO₂-Entnahme' } } });
  }
  const ax = { color: EC.muted, fontFamily: EC.font, fontSize: 19 };
  return {
    animation: false,
    grid: { left: 84, right: 30, top: 24, bottom: 44 },
    xAxis: ecAxis({ type: 'value', min: 1950, max: 2100, axisTick: { customValues: [1950, 1975, 2000, 2026, 2050, 2075, 2100] },   // 2026 under 'heute', not 2025
                    axisLabel: Object.assign({ customValues: [1950, 1975, 2000, 2026, 2050, 2075, 2100], formatter: v => String(v) }, ax) }),
    yAxis: ecAxis({ type: 'value', min: 0, max: 3, interval: .5, name: 'Erwärmung gegenüber vorindustriell', nameLocation: 'middle', nameGap: 62, nameTextStyle: ax,
                    axisLabel: Object.assign({ formatter: v => `${ecNum(v, 1)} °C` }, ax), splitLine: { show: true, lineStyle: { color: EC.grid } } }),
    series
  };
} };


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
        endLabel: end(`Bäume, kühlende Fl.: ${ecNum(D.k[D.k.length - 1], 0)} · 10⁻³ K`, '#2f7a45'), labelLayout: { moveOverlap: 'shiftY' }, animationDuration: 1600 },
      { id: 'al', type: 'line', showSymbol: false, data: P(D.al), lineStyle: { color: EC.alle, width: 3.4 }, itemStyle: { color: EC.alle }, z: 5,
        endLabel: end(`alle Flächen: ${ecNum(D.al[D.al.length - 1], 0)} · 10⁻³ K`, EC.alle), labelLayout: { moveOverlap: 'shiftY' }, animationDuration: 1600, animationDelay: 200 }
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
      grid: { left: 74, right: 310, top: 50, bottom: 46 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisTick: { show: true, customValues: [2026, 2050, 2075, 2100] }, axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: k >= 1 ? 120 : 25, interval: k >= 1 ? 20 : 5, name: 'Kühlung der Erde [10⁻³ K]', nameLocation: 'middle', nameGap: 52,
                      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19 }, splitLine: { show: true, lineStyle: { color: EC.grid } } }),
      tooltip: ecTooltip({ trigger: 'axis', formatter: ps => tipCard({ head: String(ps[0].value[0]), sub: 'Kühlung der Erde',
                    rows: ps.filter(p => ['k', 'al'].includes(p.seriesId)).map(p => ({ c: p.color, name: p.seriesId === 'k' ? 'kühlende Flächen' : 'alle Flächen', v: tipVal(p.value[1], 0, '· 10⁻³ K') })) }) }),
      series
    };
  }
};

/* temperature slide: one year -> every fifth year -> sum = the tree -> three sites; the axis fits each click */
window.TEMPSUM = @@TEMPSUM@@;
const EC_TEMPSUM = {
  steps: 3, tip: { unit: '· 10⁻¹⁵ K', dec: 1 },
  option(k) {
    const D = window.TEMPSUM, A = D.sites[0], red = '#902b3c';   // = --s-dt
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
      series.push({ id: 'one', tipName: `ein Jahr Antrieb (${D.one.year})`, type: 'line', data: pulse(D.one), showSymbol: false, z: 6,
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
      series.push({ id: 'every', tip: false, type: 'line', data, connectNulls: false, showSymbol: false, z: 4,
                    lineStyle: { color: red, width: 1.6, opacity: .45 }, animationDuration: 900 });
      series.push({ id: 'every-dots', type: 'scatter', z: 5, silent: true, symbolSize: 8, itemStyle: { color: red },
                    data: [D.one, ...D.pulses].map(p => [p.year, p.v[0]]), animationDuration: 400 });
    }
    // the site name at the end of its curve, once the three sites are shown
    const site = (s, i) => ({
      id: 'site' + i, tipName: s.name, type: 'line', data: D.years.map((y, j) => [y, s.dt[j]]), showSymbol: false, z: 7, clip: false,
      lineStyle: { color: s.color, width: 3.4 }, itemStyle: { color: s.color }, animationDuration: 2200, animationEasing: 'linear',
      markPoint: { silent: true, symbol: 'circle', symbolSize: 0, animationDelay: 2200,
                   data: k >= 3 ? [{ coord: [D.years[D.years.length - 1], s.dt[s.dt.length - 1]],
                                     label: { show: true, position: 'right', distance: 10, formatter: s.label, color: s.color,
                                              fontFamily: EC.font, fontSize: 19, fontWeight: 600 } }] : [] } });
    if (k >= 2) series.push(site(A, 0));
    if (k >= 3) {
      D.sites.slice(1).forEach((s, i) => series.push(site(s, i + 1)));
    }
    const titles = [
      `Ein Jahr Antrieb (${A.name}, ${D.one.year})`,
      `Jedes ${D.every}. Jahr: Der Baum wächst, sein Antrieb wird größer`,
      'Summe aller Jahre = ΔT des Baums',
      'Je Baum: sein Antrieb φ → ΔT'];
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

/* first slide of the potential chapter: Delta T of one tree at the three sites, side by side on one axis (Aachen,
   Marabá, Fairbanks); click by click the causes come in, in all three at once: CO2 uptake, the leaves' albedo, the
   clouds, then the net. The parts as tinted areas from zero, the net as a dark line on top. Colours: the site's own
   for its name (as on the map), the parts in the symbol colours of the formulas (deck.css --s-*) */
const cssColor = (name, fallback) => (getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback);
const EC_ORTE3 = {
  steps: 3, tip: { unit: '· 10⁻¹⁵ K', dec: 1, sub: 'ΔT je Baum' }, drawMs: 1600, x0: 2026, x1: 2100,
  // the typical forest at each site, as on the forest-type map (slide "Wachstumskurven im globalen Vergleich")
  order: [{ name: 'Aachen', forest: 'Mischwald' }, { name: 'Marabá', forest: 'Immergrüner Laubwald' }, { name: 'Fairbanks', forest: 'Immergrüner Nadelwald' }],
  // the curves and the name each carries on the plot
  parts: [
    { key: 'co2', name: 'CO₂', role: 'phic' },
    { key: 'laub', name: 'Albedo direkt (Baum)', role: 'dal' },
    { key: 'wolke', name: 'Albedo indirekt (Wolken)', role: 'daw' },
    { key: 'dt', name: 'netto', role: 'ink', net: true }],
  // a name on each curve, outside its area: CO2 under its curve, the leaves above theirs, the clouds, which stay near
  // zero, just under the zero line, the net late above its line; never on each other
  labels(k) {
    const D = window.TEMPSUM, out = [];
    const at = { co2: [2048, 'below'], laub: [2056, 'above'], wolke: [2074, 'below'], dt: [2090, 'above'] };
    this.order.forEach((o, g) => {
      const s = D.sites.find(x => x.name === o.name);
      this.parts.slice(0, k + 1).forEach(pt => {
        let [x, how] = at[pt.key], y = s[pt.key][D.years.indexOf(x)];
        // above or below a curve: clear it over the label's own width (in years either side), not only at its centre
        const half = { co2: 5, laub: 15, dt: 7 }[pt.key];
        if (half && (how === 'above' || how === 'below')) {
          const span = s[pt.key].filter((_, j) => Math.abs(D.years[j] - x) <= half);
          y = how === 'above' ? Math.max(...span) : Math.min(...span);
        }
        if (how === 'inside' && Math.abs(y) < 8) how = y > 0 ? 'above' : 'below';   // a thin area: beside its curve
        if (how === 'inside') y /= 2;
        out.push({ key: pt.key + g, grid: g, x, y, tex: pt.tex, text: pt.tex ? null : pt.name, role: pt.role, side: how });
      });
    });
    return out;
  },
  option(k) {
    const D = window.TEMPSUM, n = D.years.length - 1;
    const sites = this.order.map(o => Object.assign({ forest: o.forest }, D.sites.find(x => x.name === o.name)));
    const all = sites.flatMap(x => [...x.dt, ...x.co2, ...x.laub, ...x.wolke]);
    const span = Math.max(...all) - Math.min(...all), yst = span > 300 ? 100 : span > 120 ? 50 : 20;   // a grid line per step
    const ymin = Math.floor(Math.min(...all) / yst) * yst, ymax = Math.ceil(Math.max(...all) / yst) * yst;
    // values in femtokelvin (1 fK = 10⁻¹⁵ K): the tree's effect is that small
    const sg = v => (v > 0.05 ? '+' : v < -0.05 ? '−' : '±') + ecNum(Math.abs(v), Math.abs(v) < 5 ? 1 : 0);
    const parts = this.parts.map(pt => Object.assign({ color: pt.role === 'ink' ? EC.ink : cssColor('--s-' + pt.role, EC.ink) }, pt));
    // three panels: the first two leave room only for a number at their end, the last one for the names too
    // (it carries the key for all three); the y labels only at the first
    const L = [5.0, 37.2, 69.4], W = '25.6%', last = sites.length - 1;   // the full width: only a value after each panel (the unit is on the axis)
    const grid = sites.map((_, i) => ({ left: L[i] + '%', width: W, top: 74, bottom: 44 }));
    const xAxis = sites.map((_, i) => ecAxis({ gridIndex: i, type: 'value', min: 2026, max: 2100,
      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }));
    const yAxis = sites.map((_, i) => ecAxis({ gridIndex: i, type: 'value', min: ymin, max: ymax, interval: yst,
      name: i === 0 ? 'ΔT je Baum [10⁻¹⁵ K]' : '', nameTex: i === 0 ? '$\\dT$ je Baum [10⁻¹⁵ K]' : undefined, nameLocation: 'middle', nameGap: 66,
      axisLabel: { show: i === 0, color: EC.muted, fontFamily: EC.font, fontSize: 19, formatter: v => v === 0 ? '0' : ecNum(v, 0).replace('-', '−') },
      splitLine: { show: true, lineStyle: { color: EC.grid } } }));
    // the parts' areas fade from the curve towards zero, at every year relative to the curve's own value there: ten
    // stacked bands of a tenth of the value each, the outermost as strong as the old flat fill, the innermost almost clear
    const BANDS = 10, A = .26, DUR = this.drawMs;
    const series = [];
    sites.forEach((s, i) => parts.slice(0, k + 1).forEach(pt => {
      const ys = s[pt.key], common = { xAxisIndex: i, yAxisIndex: i, showSymbol: false, clip: false, silent: false,
        animationDuration: DUR, animationEasing: 'linear' };   // drawn at a constant pace, so the names know when to come
      if (!pt.net) for (let b = 1; b <= BANDS; b++)
        series.push(Object.assign({ id: `${pt.key}${i}-b${b}`, tip: false, type: 'line', stack: `${pt.key}${i}`, z: 2,
          data: D.years.map((y, j) => [y, ys[j] / BANDS]), lineStyle: { width: 0 }, silent: true, symbol: 'none',
          emphasis: { disabled: true }, tooltip: { show: false },   // only paint: no hover dot, no tooltip row
          areaStyle: { color: pt.color, opacity: A * b / BANDS } }, common));
      series.push(Object.assign({ id: pt.key + i, name: pt.name, type: 'line', z: pt.net ? 6 : 4,
        data: D.years.map((y, j) => [y, ys[j]]),
        lineStyle: { color: pt.color, width: pt.net ? 4.4 : 2, opacity: pt.net ? 1 : .85 }, itemStyle: { color: pt.color },
        endLabel: { show: true, formatter: sg(ys[n]), color: pt.color, fontFamily: EC.font, fontSize: 18, fontWeight: pt.net ? 700 : 600, distance: 8 },
        labelLayout: { moveOverlap: 'shiftY' },
        markLine: pt.key === 'co2' ? { silent: true, symbol: 'none', animation: false, lineStyle: { color: EC.ink2, width: 1 }, label: { show: false }, data: [{ yAxis: 0 }] } : undefined }, common));
    }));
    return {
      animationDurationUpdate: 900, animationEasingUpdate: 'cubicInOut',
      title: sites.map((s, i) => ({ text: `{a|${s.label}}  {b|${s.forest}}`, left: L[i] + '%', top: 0,
        textStyle: { rich: { a: { color: s.color, fontFamily: EC.font, fontSize: 26, fontWeight: 600 },
                             b: { color: EC.muted, fontFamily: EC.font, fontSize: 19, fontWeight: 400 } } } })),
      grid, xAxis, yAxis, series
    };
  }
};

/* slide "Netto-Energieänderung durch Albedo": the extra absorbed light of a tree planted 2026 (chart_data/licht.json,
   scripts/build_licht_data.py). Aachen alone, the axis made for it: the leaves' albedo with its name (0), the clouds
   with theirs (1); both step back and Aachen's sum stays, named (2); the axis grows to Fairbanks, the Aachen curve is
   the same, only scaled, and the other two places fade in (3). The end values are the map's (2100). */
window.LICHT = @@LICHT@@;
const EC_LICHT = {
  steps: 1, tip: { unit: 'W', dec: 0, sub: 'je Baum' }, labelMs: 1100,
  // pictures: 0 the net curve of all three sites (with the map); 1 Fairbanks alone, split into the tree's and the clouds' albedo
  // a name on each curve (HTML, placeLabels): where the curve is, outside its area
  labels(k) {
    const D = window.LICHT, F = D.sites.find(x => x.name === 'Fairbanks'), at = (ys, x) => ys[D.years.indexOf(x)], out = [];
    D.sites.forEach(st => {
      if (k >= 1 && st.name !== 'Fairbanks') return;
      const x = st.name === 'Marabá' ? 2072 : st.name === 'Fairbanks' ? 2046 : 2080;
      out.push({ key: 'n' + st.name, grid: 0, x, y: at(st.dt, x), text: st.name, role: 'ink', color: st.color, side: st.name === 'Marabá' ? 'below' : 'above' });
    });
    if (k >= 1) out.push({ key: 'laub', grid: 0, x: 2082, y: at(F.laub, 2082) * .62, text: 'Albedo (Baum)', role: 'dal', side: 'above' });
    if (k >= 1) out.push({ key: 'wolke', grid: 0, x: 2062, y: at(F.wolke, 2062), text: 'Albedo (Wolken)', role: 'daw', side: 'below' });
    return out;
  },
  option(k) {
    const D = window.LICHT, n = D.years.length - 1, hex = (c, a) => { const v = [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16)); return `rgba(${v.join(',')},${a})`; };
    const cLeaf = cssColor('--s-dal', EC.ink), cCloud = cssColor('--s-daw', EC.ink);
    const val = v => ecNum(Math.abs(v), 0) + ' W', sg = v => (v < -0.5 ? '−' : '+') + ecNum(Math.abs(v), 0) + ' W';
    const series = [], pts = ys => D.years.map((y, j) => [y, ys[j]]);
    const F = D.sites.find(x => x.name === 'Fairbanks');
    // Fairbanks' two parts, each with its click, under its net curve
    const part = (id, name, col, ys) => series.push({ id, name, tipName: name, type: 'line', z: 3, showSymbol: false, smooth: false, data: pts(ys),
      lineStyle: { color: col, width: 2.4 }, itemStyle: { color: col }, areaStyle: { color: col, opacity: .2, origin: 'auto' },
      endLabel: { show: true, formatter: sg(ys[n]), color: col, fontFamily: EC.font, fontSize: 18, fontWeight: 600, distance: 8, offset: id === 'laub' ? [0, 18] : [0, 0] },
      labelLayout: { moveOverlap: 'shiftY' }, animationDuration: 1300, animationEasing: 'cubicInOut' });
    if (k >= 1) part('laub', 'Albedo (Baum)', cLeaf, F.laub);
    if (k >= 1) part('wolke', 'Albedo (Wolken)', cCloud, F.wolke);
    D.sites.forEach(st => {
      // with the split, the other two sites go
      const a = k >= 1 && st.name !== 'Fairbanks' ? 0 : 1;
      series.push({ id: 'n_' + st.name, name: st.name, tipName: st.name, type: 'line', z: 6, showSymbol: false, smooth: false, data: pts(st.dt),
        lineStyle: { color: st.color, width: 4.4, opacity: a }, itemStyle: { color: st.color }, silent: !a, tip: a ? undefined : false,
        endLabel: { show: true, formatter: val(st.dt[n]), color: hex(st.color, a), fontFamily: EC.font, fontSize: 19, fontWeight: 700, distance: 8, offset: st.name === 'Fairbanks' && k >= 1 ? [0, -10] : [0, 0] },
        labelLayout: { moveOverlap: 'shiftY' }, animationDuration: 1500, animationEasing: 'cubicInOut' });
    });
    return {
      animationDurationUpdate: 1100, animationEasingUpdate: 'cubicInOut',
      grid: { left: 98, right: 92, top: 20, bottom: 44, containLabel: false },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2060, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: -50, max: 300, interval: 50, name: 'W je Baum', nameTex: '$\\dQ$ je Baum [W]', nameLocation: 'middle', nameGap: 62,
        axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, formatter: v => (v % 100 === 0 ? String(v).replace('-', '−') : '') },
        splitLine: { show: true, lineStyle: { color: EC.grid } } }),
      series
    };
  }
};

/* the gap chart on a dark slide: light text and lines, the colours of the curves stay */
function ecDark(o) {
  const map = { [EC.ink]: '#f2ede2', [EC.ink2]: '#d6dbd6', [EC.muted]: '#9aa39d', [EC.grid]: '#2c3437', [EC.line]: '#3a4447', '#8a918c': '#6d756f', '#8e0d16': '#ff7a6e', '#c4121f': '#ff5a4f', '#2f7a45': '#6cc28a', [EC.alb]: '#ef8a52', [EC.alle]: '#7fb6cf' };
  const walk = v => { if (Array.isArray(v)) return v.map(walk); if (v && typeof v === 'object' && v.constructor === Object) { for (const k in v) v[k] = walk(v[k]); return v; }
                      return typeof v === 'string' && map[v] ? map[v] : v; };
  return walk(o);
}
const EC_GAP_END = { steps: 0, option() { return ecDark(EC_GAP.option(EC_GAP.steps)); } };
window.ZEIT = @@ZEIT@@;

/* chapter 3: trees all planted in 2026, three ways; then the warming of Very Low above 1.5 deg C */
const EC_ZEIT = {
  steps: 8, tip: { unit: '· 10⁻³ K', dec: 0 },
  option(k) {   // pictures: 0 all land; 1 its turning point marked; 2 the cooling land; 6 the managed forest; 8 what a
                // harvest does to the curve, at the last one (EC_ZEIT27, EC_ZEIT28 pick them per slide)
    const D = window.ZEIT, P = ys => D.jahre.map((y, i) => [y, ys[i]]), n = D.jahre.length - 1;
    // shown as the temperature change Delta T (cooling < 0, downwards), as for the single tree on slide 21; second
    // label line: the path by cause in 2100: CO2 uptake, release at felling, albedo (data: cooling > 0, so negated)
    const sg = v => (v > 0 ? '−' : v < 0 ? '+' : '') + ecNum(Math.abs(v), 0);
    const parts = key => { const T = D.pfade_teile[key];
      return `CO₂ ${sg(T.co2_aufnahme[n])}` + (Math.abs(T.co2_verlust[n]) >= .5 ? ` · Fällen ${sg(T.co2_verlust[n])}` : '') + ` · Albedo ${sg(T.albedo[n])}`; };
    // two lines, the bold first one at the tip of its curve, also while the curve is drawn: an empty line above as
    // tall as the second one makes the block symmetric, so centring it on the tip centres the bold line
    const end = (text, color, key) => ({ show: true, formatter: key ? `{e|}\n{a|${text}}\n{b|${parts(key)}}` : text, color, fontFamily: EC.font, fontSize: 21, fontWeight: 600, distance: 10,
      rich: { e: { lineHeight: 24, fontSize: 19 }, a: { color, fontFamily: EC.font, fontSize: 21, fontWeight: 600, lineHeight: 27 },
              b: { color: EC.muted, fontFamily: EC.font, fontSize: 19, fontWeight: 400, lineHeight: 24 } } });
    const line = (id, ys, color, text, key, extra) => Object.assign({ id, type: 'line', showSymbol: false, data: P(ys.map(v => -v)), z: 5,
      lineStyle: { color, width: 3.4 }, itemStyle: { color }, endLabel: end(text, color, key), labelLayout: { moveOverlap: 'shiftY' },
      animationDuration: 1800 }, extra || {});
    const p = D.pfade, f = v => (v > 0 ? '−' : '') + ecNum(Math.abs(v), 0);
    // the turning point of all land: from here on the albedo adds more warming each year than the CO2 adds cooling
    // (the cooling is largest where the two rates are equal; the CO2 part is still the larger one there)
    const ip = p.alle.indexOf(Math.max(...p.alle)), turn = k === 1 ? { silent: true, symbol: 'circle', symbolSize: 16,
      itemStyle: { color: EC.alle, borderColor: '#f2ede2', borderWidth: 3 },
      label: { show: true, position: 'bottom', distance: 14, color: EC.alle, fontFamily: EC.font, fontSize: 19, fontWeight: 600, lineHeight: 24,
               formatter: `${D.jahre[ip]}: Albedo wärmt mehr als CO₂ kühlt` },
      data: [{ coord: [D.jahre[ip], -p.alle[ip]] }] } : undefined;
    const series = [
      line('al', p.alle, EC.alle, `alle Flächen: ${f(p.alle[n])} · 10⁻³ K`, 'alle', { lineStyle: { color: EC.alle, width: 3, type: [8, 6] }, tipName: 'alle Flächen', markPoint: turn })];
    // the point all tiles gathered into (Deck.gather) stays at the end of the curve, its label beside it
    series[0].endLabel.distance = 16;
    series[0].markPoint = { silent: true, symbol: 'circle', animation: false, data: [
      { coord: [D.jahre[n], -p.alle[n]], symbolSize: 14, itemStyle: { color: EC.alle }, label: { show: false } },
      ...(turn ? turn.data.map(d => Object.assign({}, d, { symbolSize: turn.symbolSize, itemStyle: turn.itemStyle, label: turn.label })) : [])] };
    if (k >= 2) {
      const s = line('k', p.kuehlt, '#2f7a45', `kühlende Flächen: ${f(p.kuehlt[n])} · 10⁻³ K`, 'kuehlt', { tipName: 'kühlende Flächen' });
      s.endLabel.distance = 16;   // as all land: a point at the end, its label beside it
      s.markPoint = { silent: true, symbol: 'circle', animation: false, data: [{ coord: [D.jahre[n], -p.kuehlt[n]], symbolSize: 14, itemStyle: { color: '#2f7a45' }, label: { show: false } }] };
      series.push(s);
    }
    if (k >= 6) {
      // the last harvest (2086) in three moves: the cleared land is bright at once (a step to more cooling), the
      // residues go up as CO2 (the bump), then the young forest takes up fast (the steep part)
      // the three places as numbered dots on the curve, each with its text beside it (no further marker): the first
      // to the left (the plot is empty there), the other two level to the right
      const pt = year => [year, -p.forst[D.jahre.indexOf(year)]];
      const notes = [[2086, 'Weniger Albedo\ngerodeter Flächen', 'left'], [2090, 'Reste → CO₂', 'right'], [2095, 'junger Wald nimmt schnell auf', 'right']];
      const marks = k >= 8 ? { silent: true, symbol: 'circle', symbolSize: 22, z: 20,   // above the curve, so it does not cross the digit
        itemStyle: { color: '#14532d', borderColor: '#f2ede2', borderWidth: 2 },
        label: { show: true, position: 'inside', color: '#f2ede2', fontFamily: EC.font, fontSize: 14, fontWeight: 700 },
        data: notes.flatMap(([year, text, side], i) => [
          { coord: pt(year), label: { formatter: String(i + 1) } },
          { coord: pt(year), symbolSize: 0, label: { position: side, distance: 18, formatter: text, color: '#14532d', fontSize: 17, fontWeight: 600,
            lineHeight: 21, align: side === 'left' ? 'right' : 'left', backgroundColor: 'rgba(242, 237, 226, .9)', padding: [2, 4], borderRadius: 4 } }]) } : undefined;
      series.push(line('fo', p.forst, '#14532d', `als Forst: ${f(p.forst[n])} · 10⁻³ K`, 'forst', { lineStyle: { color: '#14532d', width: 3.8 }, tipName: 'als Forst', markPoint: marks }));
    }
    return {
      animationDurationUpdate: 1100, animationEasingUpdate: 'cubicInOut',
      title: { text: 'ΔT der Erde, alle Bäume 2026 gepflanzt', left: 74, top: 0,
               textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 21, fontWeight: 600 } },
      grid: { left: 74, right: 345, top: 50, bottom: 46 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisTick: { show: true, customValues: [2026, 2050, 2075, 2100] },
                      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: -35, max: 0, interval: 5, name: 'ΔT [10⁻³ K]', nameTex: '$\\dT$ [10⁻³ K]', nameLocation: 'middle', nameGap: 52,
                      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, formatter: v => v < 0 ? `−${ecNum(-v, 0)}` : String(v) }, splitLine: { show: true, lineStyle: { color: EC.grid } } }),
      series
    };
  }
};

/* slide 24, clicks 3 and 4 frame by frame, in K on one axis whose limits move: click 3 zooms out from the Delta T
   picture ([-35, 0] mK) until Very Low is in view, the tree curves stay at 0, tiny now; click 4 zooms in on the warming
   ([1.4, 1.9] deg C) while the tree curves move up onto Very Low minus their cooling. The ticks are recomputed every
   frame, so the numbers move with the scale; they read in mK while the span is small */
const AUF_TITLE = 'Alle Bäume 2026 gepflanzt', AUF_WIDE = [-.1, 2], AUF_DT = [-.035, 0];   // AUF_DT: the Delta T axis of slide 24
// one y title through all of slide 24, in deg C from the start: only the scale moves, never the label
const AUF_KR = '+ Rodung wärmender Wälder\n& permanente Speicherung';   // the stacked case's name in deg C pictures
const AUF_Y = { name: 'ΔT [°C]', nameTex: '$\\dT$ [°C]', nameLocation: 'middle', nameGap: 86 }, AUF_LEFT = 108;
function aufMorph(phase, t) {
  const D = window.ZEIT, p = D.pfade, vl = D.vl_c, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
  const bk = vl.map((v, i) => v - p.kuehlt[i] / 1000), ext = vl.concat(bk, vl.map((v, i) => v - p.kuehlt_rodung[i] / 1000));   // the axis of pictures 3-5
  const lo = Math.floor(Math.min(...ext) * 10) / 10, hi = Math.ceil(Math.max(...ext) * 10 + .5) / 10;
  const mix = (a, b) => a + (b - a) * t;
  // 'direct': from the Delta T picture straight to the warming, the tree curves moving onto Very Low as the axis goes
  const [l0, l1] = phase === 3 ? [AUF_DT, AUF_WIDE] : phase === 'direct' ? [AUF_DT, [lo, hi]] : [AUF_WIDE, [lo, hi]];
  const min = mix(l0[0], l1[0]), max = mix(l0[1], l1[1]), span = max - min;
  const lift = phase === 3 ? 0 : t, on = d => vl.map((v, i) => lift * v - d[i] / 1000);   // 4: the tree curves move up onto Very Low
  // a round step for the ticks every frame (1, 2, 5 x 10^n, about six of them), on its multiples
  const step = (() => { const r = span / 6, e = Math.pow(10, Math.floor(Math.log10(r))), m = r / e; return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * e; })();
  const ticks = []; for (let v = Math.ceil(min / step - 1e-6) * step; v <= max + 1e-9; v += step) ticks.push(+v.toFixed(6));
  const dec = Math.max(0, -Math.floor(Math.log10(step) + 1e-9));
  // Very Low and the 1.5 deg C line fade in as they come into view (the top of the axis passes 1.5 deg C)
  const muted = a => `rgba(93, 102, 95, ${a})`, vlIn = phase === 4 ? 1 : Math.max(0, Math.min(1, (max - 1.3) / .5));
  const iPk = vl.indexOf(Math.max(...vl)), pv = D.jahre[iPk], tv = vl[iPk], peak = phase === 3 ? 0 : phase === 'direct' ? vlIn * Math.max(0, (t - .85) / .15) : Math.max(0, (t - .7) / .3);   // the band only once Very Low is in view
  const end = (text, color) => ({ show: true, formatter: text, color, fontFamily: EC.font, fontSize: 21, fontWeight: 600, distance: 10 });
  const named = phase !== 3 || t >= .5;
  return {
    title: { text: AUF_TITLE, left: AUF_LEFT, top: 0, textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 21, fontWeight: 600 } },
    grid: { left: AUF_LEFT, right: 345, top: 50, bottom: 34 },
    xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisTick: { show: true, customValues: [2026, 2050, 2075, 2100] },
                    axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
    yAxis: [ecAxis(Object.assign({ type: 'value', min, max, axisTick: { show: false, customValues: ticks },
                     axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: ticks,
                                  formatter: v => Math.abs(v) < 1e-9 ? '0' : ecSigned(v, dec) },
                     splitLine: { show: true, lineStyle: { color: EC.grid } } }, AUF_Y))],
    series: [
      { id: 'vl', type: 'line', data: P(vl), showSymbol: false, z: 4, labelLayout: { moveOverlap: 'shiftY' }, lineStyle: { color: '#6d756f', width: 2.6, type: [8, 6], opacity: vlIn },
        itemStyle: { color: '#6d756f' }, endLabel: { show: true, formatter: 'Best Case Szenario', color: muted(vlIn), fontFamily: EC.font, fontSize: 21, fontWeight: 600, distance: 10 },
        markPoint: { silent: true, symbol: 'circle', symbolSize: 11, itemStyle: { color: '#6d756f', borderColor: '#f2ede2', borderWidth: 2, opacity: peak },
          label: { show: true, position: [16, -4], align: 'left', verticalAlign: 'bottom', color: muted(peak), fontFamily: EC.font, fontSize: 21, fontWeight: 600,   // as in the picture after the move
                   backgroundColor: `rgba(242, 237, 226, ${peak})`, borderColor: `rgba(109, 117, 111, ${.35 * peak})`, borderWidth: 1, padding: [3, 7], borderRadius: 4, formatter: `${ecNum(tv, 2)} °C` },
          data: [{ coord: [pv, tv] }] },
        markLine: { silent: true, symbol: 'none', animation: false, lineStyle: { color: '#1b2420', width: 1.6, type: 'solid', opacity: .7 * vlIn },
          label: { show: true, position: 'insideStartBottom', color: `rgba(27, 36, 32, ${vlIn})`, fontFamily: EC.font, fontSize: 19, formatter: '1,5 °C' }, data: [{ yAxis: 1.5 }] } },
      { id: 'al', type: 'line', data: P(on(p.alle)), showSymbol: false, z: 5, labelLayout: { moveOverlap: 'shiftY' },
        lineStyle: { color: EC.alle, width: 3, type: [8, 6] }, itemStyle: { color: EC.alle }, endLabel: end(named ? 'alle Flächen' : `alle Flächen: −${ecNum(p.alle.at(-1) / 1000, 3)} K`, EC.alle) },
      { id: 'k', type: 'line', data: P(on(p.kuehlt)), showSymbol: false, z: 6, labelLayout: { moveOverlap: 'shiftY' },
        lineStyle: { color: '#2f7a45', width: 3.4 }, itemStyle: { color: '#2f7a45' }, endLabel: end(named ? 'kühlende Flächen' : `kühlende Flächen: −${ecNum(p.kuehlt.at(-1) / 1000, 3)} K`, '#2f7a45') },
      ...(phase !== 3 ? [
        { id: 'tB', type: 'line', stack: 't', stackStrategy: 'all', data: P(on(p.kuehlt)), showSymbol: false, silent: true, lineStyle: { width: 0 } },
        { id: 'tG', type: 'line', stack: 't', stackStrategy: 'all', data: P(vl.map((v, i) => (phase === 'direct' ? lift * v : v) - on(p.kuehlt)[i])), showSymbol: false, silent: true, z: 2,
          lineStyle: { width: 0 }, areaStyle: { color: '#2f7a45', opacity: .3 * (phase === 'direct' ? 1 : peak) } }] : [])]
  };
}

/* slides 24-25 in one chart: 0-2 the Delta T of the trees as before (all land, its turning point, the cooling land);
   3 in one move the axis goes from the trees' Delta T to the warming in deg C, Very Low without its removal comes into
   view and the tree curves move onto it, as Very Low minus their cooling (same series, so they glide there), ending on
   the cooling as a band and its size at the peak; 4 a what-if, dashed: the cooling land plus today's warming forest
   cut and buried (one FaIR run), its extra cooling as a hatched band; 5 what still stays above 1.5 deg C; 6 the what-if
   gone again, the red up to the cooling land */
const EC_AUFF = { steps: 6, tip: EC_ZEIT.tip, tween: 2400, tweenAt: [3],
  option(k, t = 1) {
  // one title through all pictures: the scenario stays, only the axis changes
  if (k <= 2) {
    const o = EC_ZEIT.option(k); o.title.text = AUF_TITLE; o.title.left = AUF_LEFT; o.grid.bottom = 34; o.grid.left = AUF_LEFT;
    Object.assign(o.yAxis, AUF_Y);
    o.yAxis.axisLabel.formatter = v => (v === 0 ? '0' : ecSigned(v / 1000, 3));   // the data in mK, read in deg C
    // the end labels as the axis reads: in K, not in 10^-3 K (name line and the parts below it)
    const inK = n => ecNum(+n / 1000, 3);
    for (const sr of o.series) if (sr.endLabel && typeof sr.endLabel.formatter === 'string')
      sr.endLabel.formatter = sr.endLabel.formatter.replace(/(\d+) · 10⁻³ K/g, (_, n) => `${inK(n)} K`)
        .replace(/\{b\|[^}]*\}/, b => b.replace(/([−+])(\d+)/g, (_, g, n) => g + inK(n)));
    return o;
  }
  const D = window.ZEIT, P = ys => D.jahre.map((y, i) => [y, ys[i]]), p = D.pfade, vl = D.vl_c;
  if (k === 3 && t < 1) return aufMorph('direct', t);   // the move; its last frame is the picture below
  const iPk = vl.indexOf(Math.max(...vl)), pv = D.jahre[iPk], tv = vl[iPk];
  const ba = vl.map((v, i) => v - p.alle[i] / 1000), bc = vl.map((v, i) => v - p.kuehlt[i] / 1000), tip = { unit: '°C', dec: 2 };
  const br = vl.map((v, i) => v - p.kuehlt_rodung[i] / 1000);   // the what-if: only a dashed line
  const bk = bc;   // the case on the table: band, peak, what stays above 1.5 deg C
  const lab = (text, color) => ({ show: true, formatter: text, color, fontFamily: EC.font, fontSize: 21, fontWeight: 600, distance: 10 });
  const series = [
    { id: 'vl', name: 'Best Case Szenario', type: 'line', data: P(vl), showSymbol: false, z: 4, tip, animationDuration: 1600,
      lineStyle: { color: '#6d756f', width: 2.6, type: [8, 6] }, itemStyle: { color: '#6d756f' }, endLabel: { show: true, formatter: 'Best Case Szenario',
        color: '#6d756f', fontFamily: EC.font, fontSize: 21, fontWeight: 600, distance: 10 }, labelLayout: { moveOverlap: 'shiftY' },
      markPoint: { silent: true, symbol: 'circle', symbolSize: 11, itemStyle: { color: '#6d756f', borderColor: '#f2ede2', borderWidth: 2 },
        label: { show: true, position: [16, -4], align: 'left', verticalAlign: 'bottom', color: '#6d756f', fontFamily: EC.font, fontSize: 21, fontWeight: 600,   // top right of its dot
                 backgroundColor: '#f2ede2', borderColor: 'rgba(109, 117, 111, .35)', borderWidth: 1, padding: [3, 7], borderRadius: 4, formatter: `${ecNum(tv, 2)} °C` },
        data: [{ coord: [pv, tv] }] },
      markLine: { silent: true, symbol: 'none', animation: false, lineStyle: { color: EC.ink, width: 1.6, type: 'solid', opacity: .7 },
        label: { show: true, position: 'insideStartBottom', color: EC.ink, fontFamily: EC.font, fontSize: 19, formatter: '1,5 °C' }, data: [{ yAxis: 1.5 }] } },
    { id: 'al', type: 'line', data: P(ba), showSymbol: false, z: 5, tip, tipName: 'alle Flächen', animationDurationUpdate: 1600,
      lineStyle: { color: EC.alle, width: 3, type: [8, 6] }, itemStyle: { color: EC.alle }, endLabel: lab('alle Flächen', EC.alle), labelLayout: { moveOverlap: 'shiftY' } },
    { id: 'k', type: 'line', data: P(bc), showSymbol: false, z: 6, tip, tipName: 'kühlende Flächen', animationDurationUpdate: 1600,
      lineStyle: { color: '#2f7a45', width: 3.4 }, itemStyle: { color: '#2f7a45' }, endLabel: lab('kühlende Flächen', '#2f7a45'), labelLayout: { moveOverlap: 'shiftY' } }];
  const fell = k === 4 || k === 5;   // the what-if stands in pictures 4-5; in 6 it is gone again
  if (fell) series.push(   // what if: the cooling land plus today's warming forest cut, its wood buried (one FaIR run)
    { id: 'kr', type: 'line', data: P(br), animationDuration: 1600, showSymbol: false, z: 6, tip, tipName: '+ Rodung wärmender Wälder & permanente Speicherung', animationDurationUpdate: 1600,
      lineStyle: { color: EC.rodung, width: 5, type: [4, 6], cap: 'round' }, itemStyle: { color: EC.rodung }, endLabel: Object.assign(lab(AUF_KR, EC.rodung), { lineHeight: 25 }), labelLayout: { moveOverlap: 'shiftY' } });
  if (k >= 3) {   // the cooling as a band under Very Low, its size at the peak
    const iK = bk.indexOf(Math.max(...bk));   // the new peak, with the trees
    series.push({ id: 'tB', type: 'line', stack: 't', stackStrategy: 'all', data: P(bk), showSymbol: false, silent: true, lineStyle: { width: 0 }, animation: false,
                  markPoint: { silent: true, z: 20,   // above the curves
                    symbol: 'circle', symbolSize: 11, itemStyle: { color: '#2f7a45', borderColor: '#f2ede2', borderWidth: 2 },
                    // at its dot, to the bottom right, on a solid paper box (it sits on the hatch)
                    label: { show: true, position: [16, 14], align: 'left', verticalAlign: 'top', color: '#2f7a45', fontFamily: EC.font, fontSize: 21, fontWeight: 600,
                             backgroundColor: '#f2ede2', borderColor: 'rgba(47, 122, 69, .35)', borderWidth: 1, padding: [3, 7], borderRadius: 4,
                             formatter: `${ecNum(bk[iK], 2)} °C` }, data: [{ coord: [D.jahre[iK], bk[iK]] }] } },
                { id: 'tG', type: 'line', stack: 't', stackStrategy: 'all', data: P(vl.map((v, i) => v - bk[i])), showSymbol: false, silent: true, z: 2,
                  lineStyle: { width: 0 }, itemStyle: { color: '#2f7a45' }, areaStyle: { color: '#2f7a45', opacity: .3 }, animationDuration: 1200 });
  }
  if (fell) {  // the felling's extra cooling, between the cooling land and the what-if line: hatched ochre, drawn in with the line
    const iR = br.indexOf(Math.max(...br));   // its peak, labelled at the dot
    series.push({ id: 'hB', type: 'line', stack: 'h', stackStrategy: 'all', data: P(br), showSymbol: false, silent: true, lineStyle: { width: 0 }, animation: false,
                  markPoint: { silent: true, z: 20,   // above the curves
                    symbol: 'circle', symbolSize: 11, animationDelay: 900, itemStyle: { color: EC.rodung, borderColor: '#f2ede2', borderWidth: 2 },
                    label: { show: true, position: [16, 14], align: 'left', verticalAlign: 'top', color: EC.rodung, fontFamily: EC.font, fontSize: 21, fontWeight: 600,
                             backgroundColor: '#f2ede2', borderColor: 'rgba(154, 107, 10, .35)', borderWidth: 1, padding: [3, 7], borderRadius: 4,   // bottom right of its dot, solid box
                             formatter: `${ecNum(br[iR], 2)} °C` }, data: [{ coord: [D.jahre[iR], br[iR]] }] } },
                { id: 'hG', type: 'line', stack: 'h', stackStrategy: 'all', data: P(bc.map((v, i) => v - br[i])), showSymbol: false, silent: true, z: 2,
                  lineStyle: { width: 0 }, itemStyle: { color: EC.rodung }, areaStyle: { color: aufHatch(), opacity: 1 }, animationDuration: 1600 });
  }
  const low = fell ? br : bk;   // red: what is still missing below the lowest curve shown (6: grows back up to the cooling land)
  if (k >= 5) {   // what stays above 1.5 deg C
    series.push({ id: 'rb', type: 'line', stack: 'rot', stackStrategy: 'all', data: P(low.map(() => 1.5)), showSymbol: false, silent: true, lineStyle: { width: 0 }, animation: false },
                { id: 'rr', type: 'line', stack: 'rot', stackStrategy: 'all', data: P(low.map(v => Math.max(v - 1.5, 0))), showSymbol: false, silent: true, z: 1,
                  lineStyle: { width: 0 }, areaStyle: { color: '#c4121f', opacity: .16 }, animationDuration: 1200,
                  markPoint: { silent: true, symbol: 'circle', symbolSize: 0, animationDelay: 500, data: [{ coord: [2075, 1.5 + (low[D.jahre.indexOf(2075)] - 1.5) * .4] }],
                    label: { show: true, color: '#8e0d16', fontFamily: "'Literata', Georgia, serif", fontStyle: 'italic', fontWeight: 500, fontSize: 25, formatter: 'fehlende Kühlung' } } });
  }
  const ext = vl.concat(bc, br), lo = Math.floor(Math.min(...ext) * 10) / 10, hi = Math.ceil(Math.max(...ext) * 10 + .5) / 10;
  return {
    animationDurationUpdate: 1600, animationEasingUpdate: 'cubicInOut',
    title: { text: AUF_TITLE, left: AUF_LEFT, top: 0, textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 21, fontWeight: 600 } },
    grid: { left: AUF_LEFT, right: 345, top: 50, bottom: 34 },
    xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisTick: { show: true, customValues: [2026, 2050, 2075, 2100] },
                    axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
    yAxis: ecAxis(Object.assign({ type: 'value', min: lo, max: hi, interval: .1,
                    axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, formatter: v => ecNum(v, 1) }, splitLine: { show: true, lineStyle: { color: EC.grid } } }, AUF_Y)),
    series
  };
} };

/* the same chart on two slides: 27 builds it up to the cooling land (pictures 0-2), the forest slide stands on that
   picture, adds the managed forest (6), then what a harvest does to it (8) */
/* slide 25 builds the cooling of all trees up (pictures 0-2); the next slide stands on that picture and goes on to the warming
   in deg C and what stays above 1.5 deg C (pictures 3-4 of the full chart) */
// the cooling of the cooling land as an area from 0 down to its curve: the band the next slide moves under the warming
function aufFill(o, id = 'k') {
  const k = o.series.find(x => x.id === id);
  if (!k) return o;
  const mid = k.data[Math.round(k.data.length * .72)];
  o.series.push({ id: 'tB', type: 'line', stack: 't', stackStrategy: 'all', data: k.data, showSymbol: false, silent: true, z: 2, lineStyle: { width: 0 } },
    { id: 'tG', type: 'line', stack: 't', stackStrategy: 'all', data: k.data.map(([x, y]) => [x, -y]), showSymbol: false, silent: true, z: 2,
      lineStyle: { width: 0 }, areaStyle: { color: '#2f7a45', opacity: .3 }, animationDuration: 900,
      markPoint: { silent: true, symbol: 'circle', symbolSize: 0, data: [{ coord: [mid[0], mid[1] / 2] }],
        label: { show: true, color: '#1f5e33', fontFamily: "'Literata', Georgia, serif", fontStyle: 'italic', fontWeight: 500, fontSize: 25, formatter: 'Kühlung der Bäume' } } });
  return o;
}
const EC_AUFF1 = { steps: 3, tip: EC_ZEIT.tip, option: k => k < 3 ? EC_AUFF.option(k) : aufFill(EC_AUFF.option(2)) };
// slide 25: 1 the move to deg C, 2 what if the warming forest were cut too (dotted ochre line, hatched band), 3 what
// still stays above 1.5 deg C, 4 the what-if gone again, the red grows up to the cooling land
const EC_AUFF2 = { steps: 4, tip: EC_ZEIT.tip, tween: 2400, tweenAt: [1], calmStart: true, option: (k, t) => k === 0 ? aufFill(EC_AUFF.option(2)) : EC_AUFF.option(k + 2, t) };
// the hatch of the felling's band: diagonal ochre lines on a faint ochre tint, one tile repeated
let aufHatchTile;
function aufHatch() {
  if (aufHatchTile) return aufHatchTile;
  const n = 16, c = document.createElement('canvas'); c.width = c.height = 2 * n;
  const g = c.getContext('2d'); g.scale(2, 2);
  g.fillStyle = 'rgba(176, 130, 28, .13)'; g.fillRect(0, 0, n, n);
  g.strokeStyle = 'rgba(154, 107, 10, .75)'; g.lineWidth = 2.2; g.lineCap = 'square';
  for (const d of [-n, 0, n]) { g.beginPath(); g.moveTo(d, n); g.lineTo(d + n, 0); g.stroke(); }
  return (aufHatchTile = { image: c, repeat: 'repeat' });
}

const EC_ZEIT27 = { steps: 4, tip: EC_ZEIT.tip, option: k => EC_ZEIT.option(Math.min(k, 2)) };
const EC_ZEIT28 = { steps: 4, tip: EC_ZEIT.tip, calmStart: true, option: k => EC_ZEIT.option([2, 2, 2, 6, 8][k]) };

/* a small dark chart beside the DAC map (result of the optimisation), from deck/chart_data/zeitpfade.json
   (key dac); line names at the line ends */
function ecDacSmall(title, yMax, yFmt, lines, tip) {
  return { steps: 0, tip, option() {
    const D = window.ZEIT, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const series = lines(D).map(([id, ys, color, name, dash, area]) => ({ id, tipName: name, type: 'line', showSymbol: false, data: P(ys), z: area ? 4 : 5,
      lineStyle: { color, width: dash ? 2.4 : 3.2, type: dash || 'solid' }, itemStyle: { color }, animationDuration: 1400,
      areaStyle: area ? { color, opacity: .28 } : undefined,
      endLabel: { show: true, formatter: name, color, fontFamily: EC.font, fontSize: 18, fontWeight: 600, distance: 8 }, labelLayout: { moveOverlap: 'shiftY' } }));
    return {
      grid: { left: 64, right: 150, top: 16, bottom: 32 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: yMax, interval: yMax / 4, axisLine: { lineStyle: { color: '#4a524d' } }, name: title, nameGap: 44, nameLocation: 'middle', nameTextStyle: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19 },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18, formatter: yFmt }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  } };
}
const kOf = v => v ? ecNum(v / 1000, 1) : '0';   // data in mK, read in K
/* DACCS at most 20 %/a: world capacity per year (key dac.g20) */
const EC_DACTEMP = ecDacSmall('Kapazität weltweit [Gt CO₂/a]', 100, v => String(v), D => [['d', D.dac.g20.w, '#ff5a4f', 'DACCS', null, true]], { unit: 'Gt CO₂/a', dec: 1 });
/* costs of the DAC path after the fact (key kosten_pfad): median per year with the optimistic-pessimistic band;
   then the explicit fossil subsidies and the EU-27 GDP as reference lines, in trillion EUR per year */
const EC_KOSTEN = {
  steps: 2, tip: { unit: 'Bio. €/a', dec: 2 },
  option(k) {
    const D = window.ZEIT, K = D.kosten_pfad, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const lo = K.optimistisch.je_jahr_bio, hi = K.pessimistisch.je_jahr_bio;
    const ref = (v, name, color, show) => ({ yAxis: v, lineStyle: { color, width: 2.6, type: [8, 6], opacity: show ? 1 : 0 },
      label: { show, position: 'insideStartTop', distance: 6, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, formatter: name } });
    const series = [
      { id: 'lo', tipName: 'optimistisch', type: 'line', stack: 'band', data: P(lo), showSymbol: false, lineStyle: { opacity: 0 }, itemStyle: { color: '#ff9a92' }, silent: true, animationDuration: 1600 },
      { id: 'band', tipName: 'pessimistisch', tipData: hi, itemStyle: { color: '#ff9a92' }, type: 'line', stack: 'band', data: P(hi.map((v, i) => v - lo[i])), showSymbol: false, silent: true,
        lineStyle: { opacity: 0 }, areaStyle: { color: '#ff5a4f', opacity: .22 }, animationDuration: 1600 },
      { id: 'med', tipName: 'DACCS, Median', type: 'line', data: P(K.median.je_jahr_bio), showSymbol: false, z: 5, animationDuration: 1600,
        lineStyle: { color: '#ff5a4f', width: 3.4 }, itemStyle: { color: '#ff5a4f' },
        endLabel: { show: true, formatter: 'DACCS', color: '#ff5a4f', fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 10 },
        markLine: { silent: true, symbol: 'none', animationDuration: 700, data: [
          ref(K.fossil_subv_bio, `fossile Subventionen: ${ecNum(K.fossil_subv_bio, 2)}`, '#f0b04a', k >= 1),
          ref(K.eu27_bip_bio, `BIP der EU-27: ${ecNum(K.eu27_bip_bio, 1)}`, '#9fc4e8', k >= 2)] } }];
    return {
      animationDurationUpdate: 700,
      grid: { left: 70, right: 70, top: 20, bottom: 40 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: Math.ceil(Math.max(...hi, K.eu27_bip_bio) / 5) * 5, interval: 5, axisLine: { lineStyle: { color: '#4a524d' } },
                      name: 'Kosten von DACCS [Bio. € pro Jahr]', nameGap: 44, nameLocation: 'middle', nameTextStyle: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19 },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, formatter: v => String(v) }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  }
};
/* the vegan world from 2026 by cause (key vegan.beitraege, mK, < 0 = cooler): cooling stacked above zero,
   warming below, the net as a line; built up in steps */
const EC_VEGAN = {
  steps: 3, tip: { unit: '· 10⁻³ K', dec: 0 },
  option(k) {
    const D = window.ZEIT, B = D.vegan.beitraege, P = ys => D.jahre.map((y, i) => [y, -ys[i]]);
    const co2 = B.co2_hof.map((v, i) => v + B.co2_entwaldung[i]);
    const A = (id, ys, color, name, stack, show) => ({ id, name, type: 'line', stack, data: P(show ? ys : ys.map(() => 0)), showSymbol: false,
      lineStyle: { width: 0 }, areaStyle: { color, opacity: show ? .85 : 0 }, itemStyle: { color }, animationDuration: 1400, z: 3, tip: show ? undefined : false });
    const series = [
      A('ch4', B.ch4_tier, '#4f9fc7', 'Methan der Tierhaltung', 'kuehl', true),
      A('n2o', B.n2o_vermieden, '#86c6e4', 'Lachgas: Tierhaltung, Futteranbau', 'kuehl', k >= 1),
      A('co2', co2, '#c3e3f2', 'CO₂: Futteranbau, Entwaldung', 'kuehl', k >= 1),
      A('wco2', B.wald_co2, '#5fae76', 'Wald auf freier Fläche: CO₂', 'kuehl', k >= 2),
      A('ers', B.ersatz, '#e0903e', 'Ersatzprodukte', 'waerm', k >= 2),
      A('alb', B.wald_albedo, '#d0644a', 'Wald auf freier Fläche: Albedo', 'waerm', k >= 2),
      { id: 'net', name: 'netto', type: 'line', data: P(B.netto), showSymbol: false, z: 6,
        lineStyle: { color: '#f2ede2', width: 3.4, opacity: k >= 3 ? 1 : 0 }, itemStyle: { color: '#f2ede2' }, animationDuration: 1200, tip: k >= 3 ? undefined : false,
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
      grid: { left: 70, right: 84, top: 20, bottom: 40 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: -50, max: 300, interval: 50, axisLine: { lineStyle: { color: '#4a524d' } },
                      name: 'Kühlung gegenüber Very Low [K]', nameGap: 52, nameLocation: 'middle', nameTextStyle: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19 },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, formatter: v => v ? ecNum(v / 1000, 2) : '0' },
                      splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  }
};
/* the vegan world without DAC: warming above 1.5 °C after the trees and with the vegan world (mK, read in K) */
const EC_VEGAN_LUECKE = {
  steps: 1, tip: { unit: 'K', k: .001, dec: 2 },
  option(k) {
    const D = window.ZEIT, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const end = (text, color) => ({ show: true, formatter: text, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 10 });
    const peak = (ys, color, text) => { const i = ys.indexOf(Math.max(...ys));
      return { silent: true, symbol: 'circle', symbolSize: 11, itemStyle: { color, borderColor: '#14181a', borderWidth: 2 },
        label: { show: true, position: 'top', distance: 10, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, formatter: text },
        data: [{ coord: [D.jahre[i], ys[i]] }] }; };
    const v = D.vegan.gap, iv = v.findIndex((x, i) => i > v.indexOf(Math.max(...v)) && x <= 0);
    const series = [
      { id: 'b', tipName: 'nur Bäume', type: 'line', data: P(D.baeume_rest), showSymbol: false, z: 4, lineStyle: { color: '#7fbf8c', width: 2.6, type: [8, 6] },
        itemStyle: { color: '#7fbf8c' }, endLabel: end('nur Bäume', '#7fbf8c'), animationDuration: 1200,
        markPoint: peak(D.baeume_rest, '#7fbf8c', `${ecNum(Math.max(...D.baeume_rest) / 1000, 2)} K`) }];
    if (k >= 1) series.push({ id: 'v', tipName: 'mit veganer Welt', type: 'line', data: P(v), showSymbol: false, z: 5, lineStyle: { color: '#7fd0e0', width: 3.4 },
      areaStyle: { color: '#7fd0e0', opacity: .25 }, itemStyle: { color: '#7fd0e0' }, animationDuration: 1600,
      markPoint: { silent: true, symbol: 'circle', symbolSize: 11, itemStyle: { color: '#7fd0e0', borderColor: '#14181a', borderWidth: 2 },
        label: { show: true, distance: 10, color: '#7fd0e0', fontFamily: EC.font, fontSize: 19, fontWeight: 600 },
        data: [{ coord: [D.jahre[v.indexOf(Math.max(...v))], Math.max(...v)], label: { position: 'top', formatter: `${ecNum(Math.max(...v) / 1000, 2)} K` } },
               { coord: [D.jahre[iv], 0], label: { position: 'insideBottomLeft', offset: [14, -16], formatter: `ab ${D.jahre[iv]}` } }] } });
    return {
      animationDurationUpdate: 900,
      grid: { left: 70, right: 130, top: 20, bottom: 40 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: 400, interval: 100, axisLine: { lineStyle: { color: '#4a524d' } },
                      name: 'Erwärmung über 1,5 °C [K]', nameGap: 48, nameLocation: 'middle', nameTextStyle: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19 },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, formatter: kOf }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  }
};
/* the anchor of chapters 4 and 5: Very Low without its own CO2 removal (vl_series) in deg C with the 1.5 deg C line, and a curve per measure (Very Low plus
   the trees plus the measure), never clipped. Phases: 'k4' chapter 4 (light, Very Low and trees), 0 the DAC model,
   1 DACCS at the fastest build-out (linear to 8.8 Mt/a in 2030, then +20 %/a), shown up to the peak (click 1),
   2 the vegan world (click 1; the DACCS line steps back). What stood on the slide before stands again without an entrance; only new lines are drawn in (a series'
   own `animation: true` would replay on every click, so new ones leave it unset and follow the deck). */
const ANKER_COL = { vl: '#9aa39d', b: '#7fbf8c', d: '#ff5a4f', v: '#f0b04a' };
const ANKER_COL_LIGHT = { vl: '#6d756f', b: '#14532d' };   // b as the forest curve on the left of the same slide   // the light slide of chapter 4: the dark-slide tones would read faded
function ecAnker(phase) {
  const light = phase === 'k4' || phase === 'k4f';
  const col = id => (light && ANKER_COL_LIGHT[id]) || ANKER_COL[id];
  return { steps: { k4: 1, k4f: 2, 0: 0, 1: 1, 2: 5 }[phase], tip: { unit: '°C', dec: 2 }, option(k) {
    const D = window.ZEIT, W = D.wirkung, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const vl = D.vl_c, b = vl.map((v, i) => v + W.baeume[i] / 1000), on = key => b.map((v, i) => v + W[key][i] / 1000);
    const iPeak = D.jahre.indexOf(2050);
    const order = ['k4', 0, 1, 2], rank = order.indexOf(phase);
    const born = { vl: 'k4', b: 'k4', d: 1, v: 2 };
    const later = { d: 1, v: 2 };                                              // the click within its phase
    const has = id => order.indexOf(born[id]) < rank || (born[id] === phase && k >= (later[id] || 0));
    const isNew = id => born[id] === phase, dim = () => false;
    const ink = light ? EC.ink : '#f2ede2', mut = light ? EC.muted : '#9aa39d', grid = light ? EC.grid : '#2c3437';
    const dot = (color, data, id) => ({ silent: true, symbol: 'circle', symbolSize: 11, animation: isNew(id) ? undefined : false,
      itemStyle: { color, borderColor: light ? '#f2ede2' : '#14181a', borderWidth: 2, opacity: dim(id) ? .35 : 1 },
      label: { show: true, color, fontFamily: EC.font, fontSize: 18, fontWeight: 600, distance: 9, opacity: dim(id) ? .45 : 1 }, data });
    const L = (id, ys, name, o = {}) => Object.assign({ id, name, type: 'line', data: P(ys), showSymbol: false, z: 5,
      animation: isNew(id) ? undefined : false, animationDuration: 1600,
      lineStyle: Object.assign({ color: col(id), width: 3, opacity: dim(id) ? .35 : 1 }, o.line || {}), itemStyle: { color: col(id) },
      markPoint: o.mark ? dot(col(id), o.mark, id) : undefined }, o.extra || {});
    const peak = ys => { const i = ys.indexOf(Math.max(...ys)); return [D.jahre[i], ys[i]]; };
    const series = [];
    const [pv, tv] = peak(vl);
    series.push(L('vl', vl, 'Best Case Szenario', { line: { width: 2.4, type: [8, 6] },
      mark: [{ coord: [pv, tv], label: { position: 'top', formatter: `Spitze ${pv}: ${ecNum(tv, 2)} °C` } }],
      extra: { markLine: { silent: true, symbol: 'none', animation: false, lineStyle: { color: ink, width: 1.6, type: 'solid', opacity: .7 },
        label: { show: true, position: 'insideStartBottom', color: ink, fontFamily: EC.font, fontSize: 18, formatter: '1,5 °C' }, data: [{ yAxis: 1.5 }] } } }));
    const base = (id, ys, stack) => ({ id, type: 'line', stack, stackStrategy: 'all', data: P(ys), showSymbol: false, silent: true, lineStyle: { width: 0 }, animation: false });
    // a band runs in from the left together with its line (same entrance), or stands still
    const fill = (id, ys, stack, color, op, anim) => ({ id, type: 'line', stack, stackStrategy: 'all', data: P(ys), showSymbol: false, silent: true, z: 2,
      lineStyle: { width: 0 }, itemStyle: { color }, areaStyle: { color, opacity: op }, animation: anim ? undefined : false, animationDuration: 1600 });
    // what the trees take off Very Low as a band, as every measure after it
    const trees = (id, ys, color, name, mark, anim) => {
      const l = L(id, ys, name, mark ? { mark: [mark] } : {});
      Object.assign(l.lineStyle, { color }); l.itemStyle = { color }; if (l.markPoint) l.markPoint.itemStyle.color = color;
      l.animation = anim ? undefined : false; if (l.markPoint) l.markPoint.animation = l.animation;
      series.push(l, base(id + 'B', ys, id), fill(id + 'G', vl.map((v, i) => v - ys[i]), id, color, light ? .3 : .4, anim));
    };
    const atPeak = (ys, cool) => ({ coord: [pv, ys[D.jahre.indexOf(pv)]], label: { position: 'bottom', distance: 150, offset: [90, 0], color: '#2f7a45', fontSize: 20,
      formatter: `Aufforstung an der Spitze: −${ecNum(cool * 1000, 0)} · 10⁻³ K` } });
    if (!light) trees('b', b, col('b'), 'Globale Aufforstung', null, false);
    else {   // slide 27 (k4): k 0 Very Low alone; k 1 all land (dashed) and the cooling land, the band under the cooling
      // land. The forest slide (k4f): k 0 that picture standing; k 1 the cooling land as managed forest runs in, the
      // band glides onto it; k 2 red: what stays above 1.5 deg C. Below, kk counts in the pictures of both.
      const kk = phase === 'k4f' ? [1, 6, 7][Math.min(k, 2)] : k;
      k = kk;
      const ip = D.jahre.indexOf(pv), anim1 = phase === 'k4' && k === 1;
      const ba = vl.map((v, i) => v - D.pfade.alle[i] / 1000), bk = vl.map((v, i) => v - D.pfade.kuehlt[i] / 1000);
      const bf = vl.map((v, i) => v - D.pfade.forst[i] / 1000);   // the managed forest (backup only; the trees of chapter 5 are the cooling land)
      const plain = (id, ys, color, name, dash) => { const l = L(id, ys, name, { line: dash ? { width: 3, type: [8, 6] } : {} });
        Object.assign(l.lineStyle, { color }); l.itemStyle = { color }; l.animation = anim1 ? undefined : false; return l; };
      if (k >= 1) {
        series.push(plain('ba', ba, EC.alle, 'alle Flächen', true), plain('bk', bk, '#2f7a45', 'kühlende Flächen'));
        if (k >= 6) { const l = plain('b', bf, col('b'), 'kühlende Flächen als Forst'); l.animation = k === 6 ? undefined : false; series.push(l); }
        // one band for the case on the table: on click 3 its lower edge glides from the cooling land onto the forest
        // (same ids, so the data morphs instead of the band being drawn anew); the peak label rides on it
        const cur = k >= 6 ? bf : bk, cool = (k >= 6 ? D.pfade.forst : D.pfade.kuehlt)[ip] / 1000;
        const edge = Object.assign(base('tB', cur, 't'), { animationDurationUpdate: 1600 });
        edge.markPoint = dot('#2f7a45', [atPeak(cur, cool)], 'tB'); edge.markPoint.animation = anim1 ? undefined : false;
        series.push(edge, Object.assign(fill('tG', vl.map((v, i) => v - cur[i]), 't', '#2f7a45', .3, anim1), { animationDurationUpdate: 1600 }));
      }
      if (k >= 7) { const i = D.jahre.indexOf(2080), red = [fill('rr', bf.map(v => Math.max(v - 1.5, 0)), 'rot', '#c4121f', .28, k === 7)];
        red[0].markPoint = { silent: true, symbol: 'circle', symbolSize: 0, data: [{ coord: [2080, 1.5 + (bf[i] - 1.5) / 5] }],
          label: { show: true, position: 'inside', color: '#8e0d16', fontFamily: "'Literata', Georgia, serif", fontStyle: 'italic', fontWeight: 500, fontSize: 25, formatter: 'über 1,5 °C' } };
        series.push(base('rb', bf.map(() => 1.5), 'rot'), ...red); }
    }
    if (has('d') && phase === 1) { const d = on('dac_max'), iv = D.jahre.indexOf(D.dac.max.speicher_voll);   // slide 28 only
      series.push(L('d', d, 'DACCS, +20 %/a', { line: { width: 3, type: [10, 5] },
        mark: [{ coord: [2050, d[iPeak]], label: { position: 'bottom', distance: 40, offset: [90, 0], formatter: `bis 2050: −${ecNum(-W.dac_max[iPeak], 1)} · 10⁻³ K` } },
               { coord: [D.dac.max.speicher_voll, d[iv]], label: { position: 'left', distance: 10, formatter: `Speicher voll ${D.dac.max.speicher_voll}` } }] })); }
    if (phase === 2 && k >= 1) {   // the vegan world by cause, one click each: the new forest alone (net of its
      // albedo), then what the animals themselves emit, then what growing their feed emits, the replacement crops
      // (red) back up; then the net curve
      const B = D.vegan.beitraege, parts = ['ch4_tier', 'n2o_tier', 'n2o_acker', 'co2_hof', 'co2_entwaldung', 'wald_co2', 'ersatz', 'wald_albedo'];
      const wald = B.wald_co2.map((x, i) => x + B.wald_albedo[i]);
      const co2 = B.netto.map((x, i) => B.co2_hof[i] + B.co2_entwaldung[i] + x - parts.reduce((a, p) => a + B[p][i], 0));   // what FaIR does not add up exactly goes with the small CO2 band
      const band = (id, ys, color, name, at, op = .5) => ({ id, name, type: 'line', stack: 'veg', stackStrategy: 'all', data: P(ys.map(x => x / 1000)), showSymbol: false, z: 3,
        animationDuration: 1400, animation: k === at, lineStyle: { width: 1.4, color, opacity: .9 }, itemStyle: { color }, areaStyle: { color, opacity: op },
        tip: { unit: '· 10⁻³ K', k: 1000, dec: 0 } });
      series.push({ id: 'vb', type: 'line', stack: 'veg', stackStrategy: 'all', data: P(b), showSymbol: false, silent: true, lineStyle: { width: 0 }, animation: false },
        band('vw', wald, '#e4d84a', 'Aufforstung neuer Flächen', 1, .45));
      if (k >= 2) series.push(band('vm', B.ch4_tier, '#4f9fc7', 'Tiere: Methan', 2), band('vn', B.n2o_tier, '#6fb2d6', 'Tiere: Lachgas', 2));
      if (k >= 3) series.push(band('va', B.n2o_acker, '#9fd0e6', 'Anbau: Lachgas', 3), band('vc', co2, '#c3e3f2', 'Anbau: CO₂', 3));
      if (k >= 4) series.push(band('ve', B.ersatz, '#d0443a', 'Ersatz (wärmt)', 4, .7));
    }
    if (phase === 2 && k >= 5) { const v = on('vegan'), [pw, tw] = peak(v);
      series.push(L('v', v, 'netto: pflanzlich', { line: { width: 3 }, mark: [{ coord: [pw, tw], label: { position: 'bottom', distance: 30, offset: [-20, 0], fontSize: 24,
        formatter: `netto: ${ecNum(tw, 2)} °C` } }] })); }
    // y range from all curves of the main part, so that it stays the same on every slide
    // DACCS (phase 1) is a backup slide; the main part keeps its own range
    const ext = (phase === 1 ? ['vegan', 'dac_max'] : ['vegan']).map(on).concat([vl, b]).flat(), lo = Math.floor(Math.min(...ext) * 10) / 10, hi = Math.ceil(Math.max(...ext) * 10 + .5) / 10;
    return {
      animationDurationUpdate: 800,
      legend: { left: 66, top: 0, itemGap: 12, itemWidth: 22, icon: 'path://M0,4 H28 V7 H0 Z', textStyle: { color: light ? EC.ink : '#d6dbd6', fontFamily: EC.font, fontSize: 18 },
                data: series.filter(x => x.name).map(x => x.name) },
      grid: { left: 70, right: 24, top: 116, bottom: 40 },   // room for a legend of three rows on every slide
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: light ? EC.muted : '#4a524d' } },
                      axisLabel: { color: mut, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: lo, max: hi, interval: .1, axisLine: { lineStyle: { color: light ? EC.muted : '#4a524d' } },
                      name: 'Erwärmung gegenüber vorindustriell [°C]', nameLocation: 'middle', nameGap: 50, nameTextStyle: { color: mut, fontFamily: EC.font, fontSize: 19 },
                      axisLabel: { color: mut, fontFamily: EC.font, fontSize: 19, formatter: v => ecNum(v, 1) }, splitLine: { show: true, lineStyle: { color: grid } } }),
      series
    };
  } };
}
const EC_ANKER4 = ecAnker('k4'), EC_ANKER4F = ecAnker('k4f'), EC_ANKER0 = ecAnker(0), EC_ANKER1 = ecAnker(1), EC_ANKER2 = ecAnker(2);
/* the vegan world by cause, all at once, as a block beside the anchor (EC_VEGAN builds it up over three clicks) */
const EC_VEGAN_ALL = { steps: 0, option() {
  const o = EC_VEGAN.option(3);
  delete o.title;
  o.grid = { left: 64, right: 70, top: 12, bottom: 64 };
  o.legend = { bottom: 0, left: 58, itemGap: 14, itemWidth: 14, itemHeight: 12, textStyle: { color: '#d6dbd6', fontFamily: EC.font, fontSize: 17 },
               data: ['Lachgas: Tierhaltung, Futteranbau', 'CO₂: Futteranbau, Entwaldung', 'Wald auf freier Fläche: CO₂', 'Ersatzprodukte', 'Wald auf freier Fläche: Albedo'] };
  for (const x of o.series) x.name = ({ n2o: 'Lachgas', co2: 'CO₂ Futter, Rodung', wco2: 'Wald: CO₂', ers: 'Ersatz', alb: 'Albedo' })[x.id] || x.name;
  o.legend.data = ['Lachgas', 'CO₂ Futter, Rodung', 'Wald: CO₂', 'Ersatz', 'Albedo'];
  o.xAxis.axisLabel.fontSize = 18; o.yAxis.axisLabel.fontSize = 18;
  return o;
} };
/* slide 28: the fastest DACCS build-out -- what is removed each year (gross) and net; until 2030 the planned capacity
   (Zurbriggen et al. 2026), shaded, then +20 %/a until the safe storage is full (marked) */
const EC_DACCS_AUSBAU = { steps: 0, tip: { unit: 'Gt CO₂/a', dec: 2 }, option() {
  const D = window.ZEIT, M = D.dac.max, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
  return {
    grid: { left: 64, right: 16, top: 34, bottom: 30 },
    legend: { left: 50, top: 0, itemGap: 14, itemWidth: 22, icon: 'path://M0,4 H28 V7 H0 Z', textStyle: { color: '#d6dbd6', fontFamily: EC.font, fontSize: 17 } },
    xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                    axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 17, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
    yAxis: ecAxis({ type: 'value', min: 0, max: 250, interval: 125, axisLine: { lineStyle: { color: '#4a524d' } },
                    name: 'Entnahme [Gt CO₂/a]', nameGap: 40, nameLocation: 'middle', nameTextStyle: { color: '#9aa39d', fontFamily: EC.font, fontSize: 17 },
                    axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 17 }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
    series: [
      { id: 'w', name: 'entnommen [Gt CO₂/a]', type: 'line', data: P(M.entnahme), showSymbol: false, lineStyle: { color: '#ff5a4f', width: 3 }, itemStyle: { color: '#ff5a4f' },
        areaStyle: { color: '#ff5a4f', opacity: .28 },
        markArea: { silent: true, itemStyle: { color: 'rgba(240,176,74,.14)' }, label: { show: true, position: 'insideTopLeft', color: '#f0b04a', fontFamily: EC.font, fontSize: 15, formatter: 'geplant' },
                    data: [[{ xAxis: 2026 }, { xAxis: 2030 }]] },
        markLine: { silent: true, symbol: 'none', lineStyle: { color: '#f2ede2', width: 1.6, type: [4, 4] },
                    label: { show: true, position: 'end', rotate: 0, distance: 4, color: '#f2ede2', fontFamily: EC.font, fontSize: 15, formatter: `Speicher voll ${M.speicher_voll}` },
                    data: [{ xAxis: M.speicher_voll }] } },
      { id: 'n', name: 'netto', type: 'line', data: P(M.netto), showSymbol: false, lineStyle: { color: '#f2ede2', width: 2, type: [6, 5] }, itemStyle: { color: '#f2ede2' } }]
  };
} };
/* Holzweg, "es fehlt Platz": the land of the Earth as a donut, agriculture split from the start into the animals' land
   (pasture and feed crops: "Futtermittel") and the fields for our own food ("Lebensmittel"); click 2 (the answer) adds
   an outer ring over the animals' land: what a world without them frees. Fixed series ids: a click
   merges and only the new ring enters. */
const EC_LANDDONUT = {
  steps: 1,
  tip: { item: p => p.name ? tipCard({ head: p.name.trim(), sub: 'Landfläche', rows: [{ c: p.color, v: tipVal(p.value * 10, p.value < 1 ? 1 : 0, 'Mio. km²') }] }) : '' },
  option(k) {
    const V = window.ZEIT.vegan, L = V.land;
    const rest = L.gesamt - L.wald - L.tiere - L.acker - L.wiederbewaldbar;
    const gha = v => `${ecNum(v * 10, v < 1 ? 1 : 0)} Mio. km²`;   // the data in Gha, shown in million km²
    const rich = (c, op = 1) => ({ n: { color: c, fontFamily: EC.font, fontSize: 19, fontWeight: 600, lineHeight: 22, opacity: op },
                         v: { color: c, fontFamily: EC.font, fontSize: 18, lineHeight: 20, opacity: .85 * op } });
    // what share of each land use could carry forest (Walker et al. 2022: 15.8 % of its 2.06 Gha grazing land, 61.7 % of
    // its 1.81 Gha cropland pass the reforestation rule; results/_tools/land_shares.py), applied to the parts of this
    // ring: our own fields are 62 % of cropland, the feed crops 38 % of it (Poore & Nemecek 2018), the rest of the
    // animals' land is pasture. Here only what is afforestable: what a world without animals frees, and what its
    // plant replacement needs, comes later in the talk
    const sWeide = 0.158, sAcker = 0.617, futter = L.acker * 0.38 / 0.62;
    const aTier = sWeide * (L.tiere - futter) + sAcker * futter;
    const front = ['Tierhaltung', 'aufforstbar', 'nicht aufforstbar'];   // at the answer only these stay in front (names, not labels)
    const dim = name => k >= 1 && !front.includes(name);
    const item = (name, value, color, lab, ink, label) => ({ name, value, itemStyle: { color, opacity: dim(name) ? .25 : 1 },
            label: lab ? { position: lab === 'in' ? 'inside' : 'outside', formatter: `{n|${label || name.trim()}}\n{v|${gha(value)}}`, rich: rich(ink || '#f2ede2', dim(name) ? .35 : 1) }
                       : { show: false },
            labelLine: { show: lab === 'out', lineStyle: { color: '#6d756f', opacity: dim(name) ? .35 : 1 } } });
    const base = { type: 'pie', center: ['53%', '44%'], startAngle: 90, padAngle: 1.2, itemStyle: { borderRadius: 7 }, emphasis: { disabled: true },
                   labelLine: { length: 12, length2: 14 }, label: { overflow: 'none' }, animationDuration: 1100, animationDurationUpdate: 700 };
    const series = [Object.assign({}, base, { id: 'heute', radius: ['40%', '71%'], data: [
      item('Wald', L.wald, '#2f6b45', 'in'),
      item('frei, aufforstbar', L.wiederbewaldbar, '#6b8f5e', 'out', '#c9d8c0'),
      ((x) => (x.label && (x.label.offset = [0, -10]), x))(item('Tierhaltung', L.tiere, '#c98a2b', 'in', '#14181a', 'Futtermittel')),   // a little up, clear of the ring's outer edge
      item('Lebensmittel', L.acker, '#e3c46e', 'out'),
      item('übriges Land', rest, '#30383b', 'in', '#b9c0bb')] })];
    // the second ring: what of the animals' land could carry forest
    const green = (name, v, c, lab, label) => item(name, v, c, lab, '#a6e3b4', label);
    // only agriculture gets the second ring: the rest stays an invisible spacer, so the ring lines up with the first
    const spacer = (name, v) => ({ name, value: v, itemStyle: { color: 'rgba(0, 0, 0, 0)' }, label: { show: false }, labelLine: { show: false }, tooltip: { show: false } });
    if (k >= 1) series.push(Object.assign({}, base, { id: 'ring', radius: ['75%', '86%'], animationType: 'scale', animationEasing: 'cubicOut', animationDuration: 900,
      data: [spacer('Wald ', L.wald), spacer('frei ', L.wiederbewaldbar),
             // the animals' land: what could carry forest, what could not anyway
             green('aufforstbar', aTier, '#8fe0a0', 'out'),
             item('nicht aufforstbar', L.tiere - aTier, '#4a4a40', 'out', '#9aa39d'),
             spacer('Lebensmittel ', L.acker), spacer('übriges Land ', rest)] }));
    return {
      animationDurationUpdate: 700,
      title: { text: `${ecNum(L.gesamt * 10, 0)} Mio.`, subtext: 'km² Land', left: '53%', textAlign: 'center', top: '37%',
               textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 28, fontWeight: 600 },
               subtextStyle: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18 } },
      series
    };
  }
};

/* Holzweg: the donut on the left card, held while the right card has its clicks; what a world without animals frees
   comes after them */
const EC_LANDDONUT_HOLD = Object.assign({}, EC_LANDDONUT, { steps: 5, option: k => EC_LANDDONUT.option([0, 0, 1, 1, 1, 1][k]) });   // to the slide's last click (6), no further: one more would be a click that changes nothing
/* backup "Energiebilanz Jahr für Jahr": the energy balance year by year, as FaIR counts it, for one year of
   forcing (a pulse: φ = −1 W/m² in year 1, i.e. −31,6 MJ/m², then nothing): the response f of the formula above it, the
   tree's ΔT being the sum of such responses over its years. One layer, the FaIR member: heat capacity 1/S = 3,7 W·a/(m²·K)
   ≈ 117 MJ/(m²·K), feedback R = 1,2 W/(m²·K).
   Top, energy per year and m² (+ the Earth keeps it, − it loses it), two columns a year: at the boundary the forcing φ
   (down) and the feedback −R·ΔT (up: a cooler Earth radiates less); beside them the change of the store's heat content,
   exactly their sum (first law for each year). Bottom: ΔT, dots at each year's end; S turns the store's change into it.
   Click 1: the pulse. 2 (S, no feedback): the store takes it, ΔT drops by S·φ ≈ −0,27 K and stays there. 3 (R): from the
   cooler Earth less heat leaves, year by year; the store gets it back, ΔT returns to today's in a few years
   (1/(S·R) ≈ 3,1 a), and over the years the feedback brings back exactly what φ took. Exact integrals of the
   continuous solution, so the columns add up. */
const EC_TBAL = {
  steps: 2, tip: { unit: '', dec: 1 }, drawMs: 2400, x0: 0, x1: 12,
  P: { C: 3.7, R: 1.2, phi: -1, Y: 12, MJ: 31.557 },
  T(k) {   // ΔT [K] over time [a], and its integral, for the pulse in year 1; without the feedback (k < 2) or with it
    const { C, R, phi } = this.P, tau = C / R, Teq = phi / R, T1 = Teq * (1 - Math.exp(-1 / tau));
    if (k < 2) return { at: t => phi / C * Math.min(t, 1), int: (a, b) => 0 };
    const at = t => t <= 1 ? Teq * (1 - Math.exp(-t / tau)) : T1 * Math.exp(-(t - 1) / tau);
    const int = (a, b) => a >= 1 ? T1 * tau * (Math.exp(-(a - 1) / tau) - Math.exp(-(b - 1) / tau)) : Teq * (1 - tau * (1 - Math.exp(-1 / tau))) + int(1, b);
    return { at, int };
  },
  model(k) {
    const { C, R, phi, Y, MJ } = this.P, T = this.T(k);
    return Array.from({ length: Y }, (_, i) => {
      const n = i + 1;
      return { n, phi: n === 1 ? phi * MJ : 0, fb: -R * T.int(n - 1, n) * MJ, store: C * (T.at(n) - T.at(n - 1)) * MJ, T: T.at(n) };
    });
  },
  option(k) {
    const { Y } = this.P, STEP = 180, DELAY = 300;
    const sk = cssColor('--s-sk', '#a23b72'), rf = cssColor('--s-rf', '#1f5b94'), ph = cssColor('--s-phi', '#6a3d9a');
    const font = { fontFamily: EC.font, fontSize: 18 }, E = { unit: 'MJ/m²', dec: 1 }, K = { unit: 'K', dec: 2 };
    const yrs = this.model(k);
    const bar = (id, tipName, x, ys, style, extra) => Object.assign({ id, tipName, tip: E, type: 'bar', xAxisIndex: 0, yAxisIndex: 0,
      barWidth: 11, barGap: '-100%', data: yrs.map(d => [d.n - x, ys(d)]), itemStyle: style }, extra || {});
    const series = [];
    // top: at the boundary φ (down) and the feedback (up), one column; the store's change beside it
    series.push(bar('phi', 'Antrieb φ', .68, d => d.phi, { color: ph }, { animationDuration: 500, z: 4 }));
    if (k >= 2) series.push(bar('fb', 'Rückkopplung R', .68, d => d.fb, { color: rf, opacity: .55, borderColor: rf, borderWidth: 1.5 },
      { animationDuration: 420, animationDelay: i => DELAY + i * STEP, z: 4 }));
    if (k >= 1) series.push(bar('store', 'Speicher S: Änderung', .32, d => d.store, { color: sk },
      { animationDuration: 420, animationDelay: i => DELAY + i * STEP, animationDurationUpdate: 420, animationDelayUpdate: i => DELAY + i * STEP, z: 5 }));
    // bottom: ΔT, the curve and a dot at each year's end (under its year)
    const curve = (id, tipName, T, style, extra) => Object.assign({ id, tipName, tip: K, type: 'line', xAxisIndex: 1, yAxisIndex: 1, keepPace: true,
      showSymbol: false, z: 6, data: Array.from({ length: 241 }, (_, i) => { const x = Y * i / 240; return [x, T.at(x)]; }),
      lineStyle: style, animationDuration: DELAY + Y * STEP, animationEasing: 'linear' }, extra || {});
    const dots = (id, rows, color) => ({ id, tip: false, type: 'scatter', xAxisIndex: 1, yAxisIndex: 1, silent: true, z: 8, symbolSize: 9,
      data: [{ value: [0, 0], itemStyle: { color: color(0) } }, ...rows.map((d, i) => ({ value: [d.n, d.T], itemStyle: { color: color(i + 1) } }))],
      animationDuration: 260, animationDelay: i => i === 0 ? 0 : DELAY + (i - 1) * STEP + STEP * .7 });
    if (k >= 1) {
      const fade = k >= 2 ? .45 : 1;
      series.push(curve('S', 'ΔT nur mit Speicher', this.T(1), { color: sk, width: 2.4, type: [8, 6], opacity: fade }));
      series.push(dots('Sd', this.model(1), () => k >= 2 ? 'rgba(162,59,114,.45)' : sk));
    } else series.push({ id: 'T0', tip: false, type: 'scatter', xAxisIndex: 1, yAxisIndex: 1, silent: true, symbolSize: 9, data: [[0, 0]], itemStyle: { color: '#b2182b' } });
    if (k >= 2) {
      // it cools and warms back: blue at the dip, red again as it returns
      const tone = v => { const f = Math.min(1, -v / .27), a = [178, 24, 43], b = [79, 134, 166];
        return `rgb(${a.map((c, j) => Math.round(c + (b[j] - c) * f)).join(',')})`; };
      series.push(curve('T', 'ΔT mit Rückkopplung', this.T(2), { width: 3.4, color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: '#b2182b' }, { offset: 1, color: '#4f86a6' }] } }, { z: 7 }));
      series.push(dots('Td', yrs, i => tone(i === 0 ? 0 : yrs[i - 1].T)));
    }
    const L = 96, Rr = 18, yLab = Object.assign({ color: EC.muted, showMinLabel: true }, font);
    const ytitle = text => ({ name: text, nameLocation: 'middle', nameGap: 62, nameTextStyle: Object.assign({ color: EC.ink }, font) });
    const xa = (gi, shown) => ecAxis(Object.assign({ type: 'value', gridIndex: gi, min: 0, max: Y, interval: 1,
      axisLabel: shown ? Object.assign({ color: EC.muted, formatter: v => v % 5 === 0 ? String(v) : '', showMinLabel: true, showMaxLabel: false }, font) : { show: false },
      splitLine: { show: true, lineStyle: { color: EC.grid, opacity: .6 } }, axisTick: { show: false } },
      shown ? { name: 'Jahr', nameLocation: 'middle', nameGap: 30, nameTextStyle: Object.assign({ color: EC.muted }, font) } : {}));
    return {
      animationEasing: 'cubicOut', animationEasingUpdate: 'cubicInOut', animationDurationUpdate: 600,
      grid: [{ left: L, right: Rr, top: 40, height: 150 }, { left: L, right: Rr, top: 226, bottom: 50 }],
      xAxis: [xa(0, false), xa(1, true)],
      yAxis: [ecAxis(Object.assign({ type: 'value', gridIndex: 0, min: -40, max: 20, interval: 10,
                axisLabel: Object.assign({ formatter: v => v === 0 ? '0' : v % 20 ? '' : (v > 0 ? '+' : '−') + Math.abs(v) }, yLab),
                splitLine: { show: true, lineStyle: { color: EC.grid } } }, ytitle('Energie je Jahr [MJ/m²]'))),
              ecAxis(Object.assign({ type: 'value', gridIndex: 1, min: -0.3, max: 0, interval: .1,
                axisLabel: Object.assign({ formatter: v => Math.abs(v) < 1e-9 ? '0' : ecNum(v, 1).replace('-', '−') }, yLab),
                splitLine: { show: true, lineStyle: { color: EC.grid } } }, ytitle('ΔT [K]'), { nameTex: '$\\dT$ [K]' }))],
      series
    };
  },
  // a key above the balance (the symbols' boxes), and the names of the temperature curves
  labels(k) {
    const top = 33, T2 = this.T(2);
    const out = [{ key: 'phi', grid: 0, x: 1.25, y: top, tex: '\\phit\\ \\text{Antrieb}', role: 'phi' }];
    if (k >= 1) out.push({ key: 'S', grid: 0, x: 4.5, y: top, tex: '\\Sk\\ \\text{Speicher}', role: 'sk' });
    if (k >= 2) out.push({ key: 'R', grid: 0, x: 8.8, y: top, tex: '\\Rf\\ \\text{Rückkopplung}', role: 'rf' });
    if (k >= 1) out.push({ key: 'onlyS', grid: 1, x: 9.4, y: this.T(1).at(9.4), tex: '\\text{nur }\\Sk', role: 'sk', side: 'above' });
    if (k >= 2) out.push({ key: 'withR', grid: 1, x: 7.6, y: T2.at(7.6), tex: '\\Sk\\text{ und }\\Rf', role: 'dt', side: 'below' });
    return out;
  }
};

const EC_CHARTS = { kurs: EC_KURS, landdonut: EC_LANDDONUT, landdonut5: EC_LANDDONUT_HOLD, temperatur: EC_TEMPERATURE, entnahme: EC_REMOVAL, luecke: EC_GAP, tempsum: EC_TEMPSUM, orte3: EC_ORTE3, licht: EC_LICHT, lueckeend: EC_GAP_END, zeit: EC_ZEIT27, auff: EC_AUFF, auff1: EC_AUFF1, auff2: EC_AUFF2, zeitforst: EC_ZEIT28, dactemp: EC_DACTEMP, kosten: EC_KOSTEN, vegan: EC_VEGAN, veganluecke: EC_VEGAN_LUECKE, anker4: EC_ANKER4, anker4f: EC_ANKER4F, anker0: EC_ANKER0, anker1: EC_ANKER1, anker2: EC_ANKER2, veganall: EC_VEGAN_ALL, daccsausbau: EC_DACCS_AUSBAU, tbal: EC_TBAL };

class EChart {
  constructor(host) {
    this.spec = EC_CHARTS[host.dataset.ec];
    // data-k0 starts the chart at one of its later pictures (the same chart again on a later slide)
    this.k0 = +host.dataset.k0 || 0;
    this.nSteps = this.spec ? this.spec.steps - this.k0 : 0;
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
    cancelAnimationFrame(this.raf);   // a tween still running (e.g. the opening sweep) must not paint over this picture
    k = Math.max(0, Math.min(k, this.nSteps));
    if (fresh) this.chart.clear();
    // the curves are drawn anew from the start: their names, already placed by the finished picture, go too and come
    // again as the sweep reaches them (placeLabels)
    if (fresh && animate) for (const el of this.host.querySelectorAll(':scope > .mtex.ectex')) el.remove();
    const opt = ecDraw(ecAutoTip(this.spec.option(k + this.k0), this.spec));
    // a click that changes nothing in this chart leaves it alone: setting the same option again would fade its labels in anew
    const same = JSON.stringify(opt);
    if (!fresh && same === this.last) { this.k = k; return; }
    this.last = same;
    opt.animation = animate && !this.spec.still && !(this.spec.calmStart && k === 0);   // calmStart: no entrance, the picture stands
    // a y title with a formula symbol: the axis keeps its gap, the title itself is set as HTML (axTex)
    const yAx = [].concat(opt.yAxis || []), texAx = yAx.map((a, i) => a && a.nameTex ? [i, a] : null).filter(Boolean);
    for (const [, a] of texAx) a.name = '';
    this.chart.setOption(opt, { replaceMerge: ['series'] });
    this.k = k;
    if (this.spec.labels) this.placeLabels(k, animate);
    if (texAx.length) this.placeAxTex(texAx);
    for (const el of this.host.querySelectorAll(':scope > .axlab')) if (!texAx.some(([i]) => el.dataset.key === 'y' + i)) el.remove();
  }
  placeAxTex(texAx) {
    if (!window.katex) { clearTimeout(this.axWait); this.axWait = setTimeout(() => this.placeAxTex(texAx), 300); return; }
    for (const [i, a] of texAx) {
      const g = this.chart.getModel().getComponent('grid', a.gridIndex || 0), r = g && g.coordinateSystem && g.coordinateSystem.getRect();
      if (!r) continue;
      axTex(this.host, 'y' + i, a.nameTex, r.x - (a.nameGap ?? 15), r.y + r.height / 2);
    }
  }
  placeLabels(k, animate) {
    // spec.labels(k): [{ key, grid, x, y, tex | text, role, side }] -> a formula symbol at that point of the data, in the
    // box of the figures' symbols (.chart .mtex); new ones fade in after their curve has been drawn
    if (!window.katex) { clearTimeout(this.labelWait); this.labelWait = setTimeout(() => this.placeLabels(k, false), 300); return; }
    const old = new Map([...this.host.querySelectorAll(':scope > .mtex')].map(e => [e.dataset.key, e]));
    for (const L of this.spec.labels(k + this.k0)) {
      let el = old.get(L.key); old.delete(L.key);
      if (!el) {
        el = document.createElement('span'); el.className = 'mtex ectex c-' + L.role; el.dataset.key = L.key;
        if (L.color) el.style.setProperty('--c', L.color);
        if (this.spec.labelMs) el.style.transition = `left ${this.spec.labelMs}ms cubic-bezier(.65,0,.35,1), top ${this.spec.labelMs}ms cubic-bezier(.65,0,.35,1)`;
        if (L.tex) katex.render(L.tex, el, { macros: TEX_MACROS, throwOnError: false, strict: false, trust: c => c.command === '\\htmlClass' });
        else el.textContent = L.text;
        // a new name comes once its curve has been drawn to it (the curves are drawn at a constant pace: spec.drawMs
        // from spec.x0 to spec.x1), then fades in
        if (animate && !deckCalm.matches) {
          const S = this.spec, f = S.drawMs ? Math.max(0, Math.min(1, (L.x - S.x0) / (S.x1 - S.x0))) : 1;
          el.classList.add('late'); el.style.setProperty('--ld', Math.round((S.drawMs || 1100) * f) + 'ms');
        }
        this.host.append(el);
      }
      const [px, py] = this.chart.convertToPixel({ gridIndex: L.grid }, [L.x, L.y]);
      Object.assign(el.style, { left: px + 'px', top: py + 'px', transform: `translate(-50%, ${L.side === 'above' ? 'calc(-100% - 6px)' : L.side === 'below' ? '6px' : '-50%'})` });
    }
    for (const e of old.values()) e.remove();
  }
  play(k) {
    // a chart with a tween (spec.tween ms) eases from one click to the next frame by frame, e.g. an axis that grows
    // (spec.intro ms: the first picture is drawn the same way, e.g. a curve and the labels it reaches)
    if (this.chart && this.spec.tween && !deckCalm.matches) {
      if (k === 0 && this.spec.intro) { this.chart.clear(); return this.tween(0, this.spec.intro); }
      if (this.k !== null && k === this.k + 1 && k <= this.nSteps && (!this.spec.tweenAt || this.spec.tweenAt.includes(k))) return this.tween(k, this.spec.tween);
    }
    this.set(k, true, k === 0 || this.k === null || k < this.k);
  }
  tween(k, dur) {
    cancelAnimationFrame(this.raf);
    this.last = null;   // its frames are other pictures: a set() after it must always draw
    const t0 = performance.now(), ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    const frame = now => {
      // a tween that swaps its axes (spec.tweenAt) ends on the click's own picture, drawn afresh
      if (this.spec.tweenAt && now - t0 >= dur) { this.set(k, false, true); return; }
      const t = Math.min(1, (now - t0) / dur), opt = ecAutoTip(this.spec.option(k + this.k0, this.spec.linear ? t : ease(t)), this.spec);   // linear: a constant pace, e.g. years per second
      opt.animation = false;
      // a y title with a formula symbol is set as HTML (axTex), as in set(): the axis keeps only its gap
      const texAx = [].concat(opt.yAxis || []).map((a, i) => a && a.nameTex ? [i, a] : null).filter(Boolean);
      for (const [, a] of texAx) a.name = '';
      this.chart.setOption(opt, { replaceMerge: ['series'] });
      if (texAx.length) this.placeAxTex(texAx);
      for (const el of this.host.querySelectorAll(':scope > .axlab')) if (!texAx.some(([i]) => el.dataset.key === 'y' + i)) el.remove();
      if (this.spec.frame) this.spec.frame(this.host, t, opt);
      if (t < 1) this.raf = requestAnimationFrame(frame); else this.last = JSON.stringify(ecAutoTip(this.spec.option(k + this.k0), this.spec));
    };
    this.k = k; this.raf = requestAnimationFrame(frame);
  }
  final(k) { cancelAnimationFrame(this.raf); this.set(k < 0 ? 0 : k, false, true); }
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
/* A map that grows out of the one before it (data-from on its host, same grid): each cell starts in its colour
   there, holds it while the slide changes and then blends straight into its own colour, all cells together, so
   the same land visibly changes meaning (not through the scale's pale middle: the whole map would blank out) */
const MAP_HOLD = 600, MAP_BLEND = 1400;
function mapFrom(c0, c1) {
  const dur = MAP_HOLD + MAP_BLEND, n = 6;
  return { dur, frames: [{ percent: 0, style: { fill: c0 } },
    ...Array.from({ length: n + 1 }, (_, q) => ({ percent: (MAP_HOLD + q / n * MAP_BLEND) / dur, style: { fill: mapMix(c0, c1, (1 - Math.cos(Math.PI * q / n)) / 2) } }))] };
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
    // single lines and labels can wait for a click of their own (gid "step:N" in the figure)
    for (const a of d.axes) for (const it of [...(a.items || []), ...(a.texts || [])]) if (it.stp) this.nSteps = Math.max(this.nSteps, it.stp);
    // the three sites' names on a map can wait for a click of their own (data-site-step="N")
    this.siteStep = +host.dataset.siteStep || 0;
    this.siteFirst = (host.dataset.siteFirst || '').split(',').map(x => x.trim()).filter(Boolean);   // sites shown from the start (data-site-first)
    this.nSteps = Math.max(this.nSteps, this.siteStep);
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
    this.svg = !this.isMap || host.dataset.renderer === 'svg';
    this.mount();
    this.k = null;
    this.timeLayer = this.mapSpec && this.mapSpec.panels[0].layers.find(L => L.frames);
    if (this.timeLayer) { this.year = this.timeLayer.years[0]; if (host.dataset.renderer !== 'svg') this.player(); }
    this.final(this.nSteps);
    new ResizeObserver(() => { if (this.size()) { this.chart.resize(); this.final(this.k ?? this.nSteps); } }).observe(host);
    if (!this.svg) {
      // the deck scales with the window (a transform the host's own size does not show): a canvas map is drawn again
      // at the new sharpness when the deck moves to another screen
      let t; addEventListener('resize', () => { clearTimeout(t); t = setTimeout(() => { if (this.dprFit() !== this.dpr) { this.mount(); this.final(this.k ?? this.nSteps); } }, 300); });
      // the cells' entrance worked out while the deck rests (a few hundred ms for a large map: never during an
      // entrance, as the background chart builder), so the slide's arrival only replays it (replay)
      if (!this.nSteps && !this.timeLayer && !this.stops) {
        const later = () => {
          if (this.runCache) return;
          if (performance.now() - ((window.deck && window.deck.movedAt) || 0) < 2500) return setTimeout(later, 700);
          (window.requestIdleCallback || setTimeout)(() => (performance.now() - ((window.deck && window.deck.movedAt) || 0) < 2500 ? later() : this.prepRuns()));
        };
        setTimeout(later, 700);
      }
    }
  }

  /* canvas pixels per CSS pixel: the screen's ratio times the deck's scale, in halves, 1 to 3 (a fixed 3 painted
     up to 9x the pixels a projector needs, on every frame of a map's entrance) */
  dprFit() {
    const r = this.inner.getBoundingClientRect(), k = r.width && this.inner.offsetWidth ? r.width / this.inner.offsetWidth : 1;
    return Math.min(3, Math.max(1, Math.ceil(2 * (window.devicePixelRatio || 1) * k) / 2));
  }
  mount() {
    if (this.chart) { cancelAnimationFrame(this.runRaf); this.chart.dispose(); this.k = null; }
    const host = this.host;
    this.dpr = this.svg ? 1 : this.dprFit();
    this.chart = echarts.init(this.inner, null, this.svg ? { renderer: 'svg' } : { renderer: 'canvas', devicePixelRatio: this.dpr });
    // a figure with bars or maps has an item tooltip; inside a panel of curves the pointer anywhere snaps to the
    // nearest x of its curves (hover on a desktop, tap or drag on a touch screen), as an axis tooltip would
    const snap = e => {
      const S = this.series, c = this.chart;
      if (!S || !this.d || !this.d.axes.some(a => a.map || a.items.some(it => ['bar', 'cells', 'points'].includes(it.t)))) return;
      const xy = [e.offsetX, e.offsetY];
      for (let i = 0; i < this.d.axes.length; i++) {
        const a = this.d.axes[i];
        if (a.map || a.items.some(it => ['bar', 'cells', 'points'].includes(it.t))) continue;
        if (!c.containPixel({ gridIndex: i }, xy)) continue;
        let k = -1;   // the curve of the panel with the most points
        S.forEach((q, n) => { if (q.tipLine && q.xAxisIndex === i && (q.data || []).length > (k < 0 ? 0 : S[k].data.length)) k = n; });
        if (k < 0) return;
        const x = c.convertFromPixel({ gridIndex: i }, xy)[0], d = S[k].data.map(e2 => Array.isArray(e2) ? e2 : e2 && e2.value);
        let j = 0, best = Infinity;
        d.forEach((q, n) => { if (q && isFinite(q[0]) && Math.abs(q[0] - x) < best) { best = Math.abs(q[0] - x); j = n; } });
        clearTimeout(this.snapT);   // after ECharts' own (throttled) hide of the item tooltip, not before it
        this.snapT = setTimeout(() => { if (!document.documentElement.matches('.zoomed, .pinching')) c.dispatchAction({ type: 'showTip', seriesIndex: k, dataIndex: j }); }, 30);
        return;
      }
    };
    this.chart.getZr().on('mousemove', snap);
    this.chart.getZr().on('click', snap);
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
    this.mapRuns = [];   // map cells with an entrance (hexSeries), played after the option is set
    const d = this.d, s = this.s, W = this.W, H = this.H;
    this.texs = [];
    const grid = [], xAxis = [], yAxis = [], series = [], graphic = [];
    const stopX = this.stops ? this.stops[Math.max(0, Math.min(k, this.stops.length - 1))] : Infinity;
    // a map's legend and labels in the deck's face and the size of the other charts' labels (a full-width map would scale them up)
    const font = (it, base) => ({ fontFamily: it.serif ? MPL_SERIF : this.isMap ? EC.font : MPL_FONT, fontSize: this.isMap ? Math.min((it.fs || base) * s, 19) : (it.fs || base) * s,
                                  fontWeight: it.b ? 600 : 400, fontStyle: it.i ? 'italic' : 'normal' });
    const legendLabel = {}, legendName = {};
    for (const lg of d.legends) for (const e of lg.entries) { if (e.k === 'patch' && e.col) legendLabel[e.col] = e.s; if (e.col) legendName[String(e.col).toLowerCase()] = e.s; }
    this.legendName = legendName;
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
                     color: A.lc || '#5d665f', fontFamily: this.isMap ? EC.font : MPL_FONT, fontSize: this.isMap ? Math.min((A.lfs || 17) * s, 19) : (A.lfs || 17) * s, margin: 7 * s, hideOverlap: false },
        splitLine: { show: !!A.grid, lineStyle: { color: A.grid ? A.grid.c : '#ddd', width: A.grid ? Math.max(.6, A.grid.lw * s) : 1 } },
        splitArea: { show: false }, silent: true, animation: false
      };
    };
    // bars, maps or points somewhere in the figure: one item tooltip for all, with the curves made hoverable
    const mixed = d.axes.some(a => a.map || a.items.some(it => ['bar', 'cells', 'points'].includes(it.t)));
    this.series = series;
    d.axes.forEach((a, i) => {
      const show = this.visible(i, k), [bx, by, bw, bh] = a.box;
      grid.push({ left: bx * W, top: by * H, width: bw * W, height: bh * H, containLabel: false, show: false });
      xAxis.push(axisFor(a, 'x', i, show));
      yAxis.push(axisFor(a, 'y', i, show));
      if (!show) return;
      const base = t0(i), id = n => `a${i}_${n}`, Z = it => 2 + (it.z || 0);
      const inX = x => x <= stopX;
      if (a.bg) graphic.push({ id: id('bg'), type: 'rect', z: -1, shape: { x: bx * W, y: by * H, width: bw * W, height: bh * H }, style: { fill: a.bg }, silent: true });
      a.labels.forEach((t, j) => {
        // every y title as an HTML axis title (placeAxTex): the deck's axis face and size, a formula symbol where the
        // table has one; as on the charts built in ECharts
        if (t.rot === 90) (this.axTexs = this.axTexs || []).push({ key: id('lab' + j), tex: MPL_AXIS_TEX[t.s] || t.s, x: t.f[0] * W, y: t.f[1] * H,
                                                                     fs: Math.max(17, Math.min(19, font(t, 16).fontSize)) });
        else graphic.push(this.textEl(id('lab' + j), t, font, W, H));
      });
      const bars = [], cells = [];
      a.items.forEach((it, j) => {
        if (it.t === 'line') {
          if (it.stp > k) return;   // waits for its click
          // a site's marker comes with its name (data-site-step)
          if (this.siteStep > k && a.map && it.mk && !it.lw && it.xy.length === 1 && window.MAPDATA
            && window.MAPDATA.sites.some(q => Math.abs(q.lon - it.xy[0][0]) < .5 && Math.abs(q.lat - it.xy[0][1]) < .5 && !this.siteFirst.some(n => q.name.startsWith(n)))) return;
          const faded = it.fade !== undefined && it.fade <= k;   // the other places step back (gid "fade:N")
          const pts = it.xy.filter(p => p[0] === null || inX(p[0])).map(p => (p[0] === null || p[1] === null) ? [NaN, NaN] : p);
          if (!pts.length) return;
          const mk = it.mk, onlyMk = !it.lw;
          const sym = mk ? mk.sym : 'none';
          const site = a.map && mk && window.MAPDATA && it.xy.length === 1 && window.MAPDATA.sites.find(q => Math.abs(q.lon - it.xy[0][0]) < .3 && Math.abs(q.lat - it.xy[0][1]) < .3);
          const symStyle = site ? { color: site.color, borderColor: '#ffffff', borderWidth: 2.2 * s }
                         : mk ? { color: mk.fc || 'transparent', borderColor: mk.ec || mk.fc, borderWidth: (mk.ew || 0) * s } : { color: it.c };
          const dataPts = mk && mk.idx ? pts.map((p, q) => mk.idx.includes(q) ? { value: p } : { value: p, symbolSize: 0 }) : pts;
          series.push({
            id: id('l' + j), name: it.name || ' ', tipLine: !(pts.length <= 2 && !it.name && !legendName[String(it.c).toLowerCase()] && !this.textName(i, it.c)), tipName: it.name || legendName[String(it.c).toLowerCase()] || this.textName(i, it.c), type: onlyMk ? 'scatter' : 'line', xAxisIndex: i, yAxisIndex: i, z: Z(it),
            data: dataPts, showSymbol: !!mk, symbol: sym, symbolSize: mk ? mk.size * s : 0, itemStyle: symStyle,
            lineStyle: { color: it.c, width: it.lw * s, type: it.dash ? it.dash.map(v => v * s) : 'solid', opacity: (it.a ?? 1) * (faded ? .22 : 1), cap: 'round' },
            connectNulls: false, clip: !it.noclip, smooth: false, emphasis: { disabled: true },
            ...(mixed && !mk && it.lw ? { showSymbol: true, symbol: 'circle', symbolSize: 22 * s, itemStyle: { color: it.c, opacity: 0 } } : {}),
            animationDuration: onlyMk ? 500 : 1500, animationEasing: 'cubicInOut', animationDelay: base + (site ? 0 : onlyMk ? 900 : 0)
          });
        } else if (it.t === 'bar') {
          if (!inX(it.r[0])) return;
          bars.push(it);
        } else if (it.t === 'cells') {
          if (!this.mapSpec) cells.push(it);
        } else if (it.t === 'poly') {
          if (it.stp > k) return;   // waits for its click
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
        itemStyle: { opacity: 1 },   // a scatter series is 80 % opaque by default: the names' boxes would be seen through
        data: list.map(t => ({ value: [t.x, t.y], label: { show: true, position: 'inside', formatter: t.s, color: t.c, align: t.al, ...subRich(t, font(t, 16)),
          verticalAlign: 'middle', rotate: t.rot || 0, lineHeight: (t.fs || 16) * s * 1.18, ...font(t, 16),
          backgroundColor: t.bg ? (t.bga < 1 ? `rgba(${parseInt(t.bg.slice(1, 3), 16)},${parseInt(t.bg.slice(3, 5), 16)},${parseInt(t.bg.slice(5, 7), 16)},${t.bga})` : t.bg) : 'transparent',
          // dark labels get a paper halo so they stay readable over lines and bars; light ones sit on colour and need none
          textBorderColor: 'rgba(242,237,226,.92)', textBorderWidth: t.bg || mapHex(t.c).reduce((q, v) => q + v, 0) > 560 ? 0 : 3.2 * s,
          padding: t.pill ? [3 * s, 8 * s] : t.bg ? [2 * s, 4 * s] : 0, borderColor: t.ring || 'transparent', borderWidth: t.ring ? 1.6 * s : 0, borderRadius: t.pill ? 8 * s : t.ring ? 4 * s : 0 } })),
        animationDuration: 500, animationDelay: delay
      });
      // a curve's or place's name (bold, in a colour) sits in a box of its colour, as the names on the ECharts figures (.mtex.ectex)
      const paper = mapHex(cssColor('--paper', '#f2ede2')), mix = (c, d, w) => '#' + mapHex(c).map((v, q) => Math.round(v * w + mapHex(d)[q] * (1 - w)).toString(16).padStart(2, '0')).join(''),
        tint = c => mix(c, '#' + paper.map(v => v.toString(16).padStart(2, '0')).join(''), .18), fg = c => mix(c, '#1b2420', .5);   // one look for every name: its colour darkened (readable), on a tint of it
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
        return { ...t, s: s2, c: fg(site.color), b: 1, pill: 1, bg: tint(site.color), bga: 1 };
      };
      // a formula symbol on its own goes over the chart in KaTeX, in the slides' formula face (placeTex)
      for (const t of a.texts) if (t.tex && inX(t.x) && window.katex) this.texs.push({ t, a, key: i + ':' + t.tex });
      const shown = a.texts.filter(t => !(t.stp > k) && !(this.siteStep > k && siteText(t) && !this.siteFirst.some(n => t.s.trim().startsWith(n))) && !(t.fade <= k) && inX(t.x) && !(t.tex && window.katex)), siteTexts = () => shown.map(siteText).filter(Boolean);
      const pill = t => {
        const c = !a.map && !t.bg && !t.rot && !t.ring && t.b && /^#[0-9a-f]{6}$/i.test(t.c || '') && mapHex(t.c);
        if (!c || Math.max(...c) - Math.min(...c) < 50) return t;
        return { ...t, pill: 1, c: fg(t.c), bg: tint(t.c), bga: 1 };
      };
      const texts = shown.filter(t => !siteText(t)).map(pill);
      // texts that wait for a click each in a series of their own: a later click adds its text without the earlier ones fading in again
      for (const g of [...new Set(texts.map(t => t.stp || 0))]) { const part = texts.filter(t => (t.stp || 0) === g); if (part.length) series.push(textSeries(id(g ? 't' + g : 't'), part, base + 1300)); }
      if (siteTexts().length) {
        // the sites shown from the start (data-site-first) in a series of their own: when the others come, they stay put
        const first = t => this.siteFirst.some(n => t.s.trim().startsWith(n));
        const st0 = siteTexts().filter(first), st1 = siteTexts().filter(t => !first(t));
        if (st0.length) series.push(textSeries(id('ts0'), st0, base));
        if (st1.length) series.push(textSeries(id('ts'), st1, base));
        if (this.timeLayer && this.mapAxes.includes(i)) this.siteSeries = () => ({ ...textSeries(id('ts'), siteTexts(), 0), animation: false });
      }
    });
    d.texts.forEach((t, j) => graphic.push(this.textEl(`ft${j}`, t, font, W, H)));
    d.legends.forEach((lg, j) => graphic.push(this.legendEl(`lg${j}`, lg, W, H, s)));
    if (this.isMap && !this.svg) {   // on a canvas map, everything but the cells is drawn once, on the top layer (hexSeries)
      for (const sr of series) if (sr.zlevel === undefined) sr.zlevel = 2;
      for (const g of graphic) if (!/bg$/.test(g.id || '')) g.zlevel = 2;
    }
    return {
      // maps have more than ECharts' default 2000 shapes per series, above which it skips the entry animation
      animation: animate, animationThreshold: 100000, animationDurationUpdate: 600, grid, xAxis, yAxis, series, graphic,
      // a figure of curves only: an axis tooltip (every curve of the panel under the pointer, at that x);
      // with bars, maps or points the tooltip names the bar, cell or point under the pointer
      tooltip: mixed
        ? ecTooltip({ trigger: 'item', hideDelay: 0, formatter: p => this.tip(p) })   // hide at once: the snap of a curve panel shows it again in the same move
        : ecTooltip({ trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: '#5d665f', type: [3, 3] } },
                      formatter: ps => this.axisTip(+(/^a(\d+)_/.exec(ps[0] && ps[0].seriesId || '') || [0, 0])[1], ps, series) })
    };
  }

  /* what axis i measures, read off the figure: the y label "Größe [Einheit]" gives the quantity and its unit,
     the x label its unit; tick labels name the categories of bar charts */
  axisInfo(i) {
    this.axInfo = this.axInfo || {};
    if (this.axInfo[i]) return this.axInfo[i];
    const a = this.d.axes[i], split = t => { const m = /\[([^\]]+)\]/.exec(t || ''); return { q: (t || '').replace(/\s*\[[^\]]*\]\s*/, ' ').replace(/\s+/g, ' ').trim(), u: m ? m[1] : '' }; };
    const yl = (a.labels.find(l => l.rot === 90) || {}).s, xl = (a.labels.find(l => !l.rot && /\[[^\]]+\]/.test(l.s)) || {}).s;
    const title = (a.labels.find(l => !l.rot && !/\[/.test(l.s)) || {}).s;
    const I = { y: split(yl), x: split(xl), title: title ? title.split('\n')[0] : '' };
    // a row of panels often labels only its first y axis: the others measure the same
    if (!I.y.u) { const o = this.d.axes.find(b => b !== a && /\[[^\]]+\]/.test((b.labels.find(l => l.rot === 90) || {}).s || '')); if (o) I.y = split(o.labels.find(l => l.rot === 90).s); }
    return (this.axInfo[i] = I);
  }
  // a curve labelled in place: the text in its own colour names it (first line, without a value after a colon)
  textName(i, c) {
    const same = t => t.c && c && t.c.toLowerCase() === String(c).toLowerCase();
    const t = (this.d.axes[i].texts || []).find(same) || this.d.axes.flatMap(a => a.texts || []).find(same);   // or the panel next to it
    return t ? t.s.split('\n')[0].replace(/[:=]\s*[−-]?[\d,.]+.*$/, '').replace(/^[—–-]\s*/, '').trim() : '';   // without a value after it or a dash before it
  }
  num(v, u) { return `${mplNum(v).replace('-', '−')}${u ? '\u202f' + u : ''}`; }
  xText(x, u) { return (Math.abs(x - Math.round(x)) < 1e-6 && Math.abs(x) > 1000) ? String(Math.round(x)) : this.num(x, u); }
  axisTip(i, ps, series) {
    const I = this.axisInfo(i), rows = [], seen = new Set();
    for (const p of ps) {
      const sr = series[p.seriesIndex], v = Array.isArray(p.value) ? p.value : p.data && p.data.value;
      if (!sr || !sr.tipLine || !v || !isFinite(v[1])) continue;
      const name = sr.tipName || '', key = name || this.num(v[1], '');   // a marker on a curve: once
      if (seen.has(key) || (!name && rows.some(r => r.v === this.num(v[1], I.y.u)))) continue; seen.add(key);
      const c = sr.lineStyle && sr.lineStyle.color || '#5d665f';
      rows.push({ c, name, v: this.num(v[1], I.y.u) });
    }
    if (!rows.length) return '';
    const x = Array.isArray(ps[0].value) ? ps[0].value[0] : ps[0].axisValue;
    return tipCard({ head: this.xText(+x, I.x.u), sub: [this.d.axes.length > 1 ? I.title : '', I.y.q].filter(Boolean).join(' · '), rows });
  }
  tip(p) {
    if (p.seriesType === 'custom') return !p.data ? '' : p.data.tip || (p.data.tipf ? p.data.tipf() : '');
    const v = Array.isArray(p.value) ? p.value : p.data && p.data.value;
    if (!v) return '';
    const i = +(/^a(\d+)_/.exec(p.seriesId || '') || [0, 0])[1], I = this.axisInfo(i), sr = this.series && this.series[p.seriesIndex];
    // a curve in a figure with bars or a map: hovering it shows every curve of its panel at that x, as an axis tooltip would
    if (sr && sr.tipLine && this.series) {
      const ps = this.series.map((q, k) => q.tipLine && q.xAxisIndex === i ? { seriesIndex: k, value: this.at(q, v[0]) } : null).filter(q => q && q.value);
      return this.axisTip(i, ps, this.series);
    }
    const a = this.d.axes[i], name = (p.seriesName || '').trim() || (sr && sr.tipName) || '';
    if (a.map) return tipCard({ head: tipPlace(v[0], v[1]), sub: name, rows: [] });
    return tipCard({ head: name || this.xText(v[0], I.x.u), sub: I.y.q, rows: [{ c: p.color, name: name ? this.xText(v[0], I.x.u) : '', v: this.num(v[1], I.y.u) }] });
  }
  // a curve's value at x (straight between its points), for the tooltip of a curve under the pointer
  at(q, x) {
    const d = (q.data || []).map(e => Array.isArray(e) ? e : e && e.value).filter(e => e && isFinite(e[0]) && isFinite(e[1]));
    if (!d.length || x < d[0][0] - 1e-9 || x > d[d.length - 1][0] + 1e-9) return null;
    const j = d.findIndex(e => e[0] >= x);
    if (j <= 0) return [x, d[Math.max(0, j)][1]];
    const [a, b] = [d[j - 1], d[j]];
    return [x, a[1] + (b[1] - a[1]) * (x - a[0]) / ((b[0] - a[0]) || 1)];
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
      { const r = supRichText(e.s, { fontSize: this.isMap ? Math.min(lg.fs * s, 19) : lg.fs * s, fontFamily: this.isMap ? EC.font : MPL_FONT, fontWeight: 400, fontStyle: 'normal' }, e.c || '#1b2420') || {};
        children.push({ type: 'text', x, y, style: { text: r.formatter || e.s, rich: r.rich, fill: e.c || '#1b2420', textVerticalAlign: 'middle', font: `400 ${lg.fs * s}px ${MPL_FONT}`, lineHeight: lg.fs * s * 1.15 } }); }
    }
    if (lg.title) { const r = supRichText(lg.title.s, { fontSize: this.isMap ? Math.min(lg.title.fs * s, 19) : lg.title.fs * s, fontFamily: this.isMap ? EC.font : MPL_FONT, fontWeight: 600, fontStyle: 'normal' }, lg.title.c) || {};
      children.push({ type: 'text', x: lg.title.f[0] * W, y: lg.title.f[1] * H, style: { text: r.formatter || lg.title.s, rich: r.rich, fill: lg.title.c, textAlign: lg.title.al, textVerticalAlign: 'middle', font: `600 ${lg.title.fs * s}px ${MPL_FONT}` } }); }
    if (!this.isMap && !this.host.closest('.dark, .brk') && lg.entries.length && !lg.title) {   // a line chart's legend sits on top of the grid lines: a paper-coloured plate hides them
      const fs = lg.fs * s, xs = lg.entries.map(e => e.f[0] * W), ys = lg.entries.map(e => e.f[1] * H);
      const x0 = Math.min(...xs) - lg.pad * s - lg.hl * s - 6, x1 = Math.max(...lg.entries.map(e => e.f[0] * W + String(e.s).length * fs * .42)) + 4;
      children.unshift({ type: 'rect', shape: { x: x0, y: Math.min(...ys) - fs * .7, width: x1 - x0, height: Math.max(...ys) - Math.min(...ys) + fs * 1.4, r: 4 }, style: { fill: 'rgba(242, 237, 226, .92)' } });
    }
    if (!this.isMap && !this.host.closest('.dark, .brk')) children.forEach(c => { c.z = 3000; });   // graphic children take their own z
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

  // a hexagon of a map: where it is (rounded), what the panel shows, its class or value
  mapTip(i, li, lon, lat, tip, col) {
    const [first, ...rest] = String(tip).split('<br>'), I = this.axisInfo(i);
    const cb = this.cbarAxes && this.cbarAxes[this.mapAxes.indexOf(i)];
    // what the map shows: its title, else the colour bar's label without the unit and the explanation after a colon
    const what = (I.title || (cb !== undefined ? this.axisInfo(cb).y.q || ((this.d.axes[cb].labels[0] || {}).s || '') : ''))
      .replace(/\s*\[[^\]]*\]/g, '').split(/:\s/)[0].split('\n')[0].trim();
    return tipCard({ head: tipPlace(lon, lat), sub: what, rows: [{ c: col, v: first }], note: rest.join(' ') });
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
    // canvas layers: the cells with an entrance (1) repaint alone; static cells below them (0), all else above (2)
    const anim = L => L.kind === 'num' || L.kind === 'cat', firstAnim = panel.layers.findIndex(anim);
    const F = enter && this.host.dataset.from && M.maps[this.host.dataset.from], fp = F && F.panels[this.mapSpec.panels.indexOf(panel)];
    panel.layers.forEach((L, li) => {
      const FL = fp && fp.layers[li] && fp.layers[li].kind === 'num' ? fp.layers[li] : null;
      const fromLook = FL && new Map(FL.cells.map((cell, j) => [cell[0] * g.nx + cell[1], j]));
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
          tip = () => cat.label + (L.cats === 'waldtyp' ? `<br>${Math.round(Math.min(1, share) * 30)}${share >= 1 ? '+' : ''} % der Landfläche wiederbewaldbar` : '');
        } else {
          const sc = M.scales[L.scale], v = L.frames ? this.frameValue(L, j) : cell[2];
          col = mapScale(sc, v); tip = () => mapFmt(v, sc) + (L.frames ? ` (${Math.round(this.year ?? L.years[0])})` : '');   // its text only when hovered: toLocaleString for 45 000 cells cost a click
          if (enter) run = mapRun(sc, v);
          const fj = FL ? fromLook.get(r * g.nx + c) : undefined;
          if (run && fj !== undefined) run = mapFrom(mapScale(M.scales[FL.scale], FL.cells[fj][2]), col);
        }
        const it = tip ? { value: [lon, lat], col, tipf: () => this.mapTip(i, li, lon, lat, typeof tip === 'function' ? tip() : tip, col) } : { value: [lon, lat], col, tooltip: { show: false } };
        if (run) it.run = run;
        items.push(it);
      }
      (this.hexItems ||= {})[id('hex' + li)] = { i, items, kind: L.kind, R };   // for Deck.gather: the cells as drawn
      const hatch = L.kind === 'hatch';
      if (items.some(it => it.run)) this.mapRuns.push({ sid: id('hex' + li), items, delay: base + 250 });
      series.push({
        id: id('hex' + li), type: 'custom', xAxisIndex: i, yAxisIndex: i, z: 3 + li, clip: true, silent: hatch || L.kind === 'mask' && !L.label,
        data: items,
        renderItem: (p, api) => {
          const it = items[p.dataIndex], [x, y] = api.coord(it.value);
          if (hatch) return { type: 'line', shape: { x1: x - R * .6, y1: y + R * .6, x2: x + R * .6, y2: y - R * .6 }, style: { stroke: it.col, lineWidth: Math.max(.8, 1.1 * s), opacity: .75 } };
          const shape = { points: pts.map(([u, v]) => [x + Rr * u, y + Rr * v]) };
          if (!it.run) return { type: 'polygon', shape, style: { fill: it.col }, enterFrom: { style: { opacity: 0 } } };
          // starts on the scale's neutral colour, so nothing shows its end colour before its turn (playRuns)
          return { type: 'polygon', shape, style: { fill: it.run.frames[0].style.fill } };
        },
        animationDuration: 450, animationDelay: base + li * 60, progressive: 0,
        zlevel: anim(L) ? 1 : li < firstAnim || firstAnim < 0 ? 0 : 2
      });
    });
  }

  /* The cells' entrances, driven here and not as ECharts keyframes: a few thousand keyframe animators parse their
     colours anew every frame, and zrender fills every cell on its own (a 1-degree map has 8000 of them: 20-40 ms a
     frame on a fast laptop). Here the colours come from precomputed RGB stops (same timing, same linear steps), and
     the moving cells are painted straight onto their own canvas layer (hexSeries: zlevel 1), one fill per colour
     (and per 48 cells), the colour rounded to 32 steps a channel while it moves; the last frame hands the exact colours back to zrender. */
  stopRuns() {   // a run cut short still ends on the exact colours, drawn by zrender again
    cancelAnimationFrame(this.runRaf);
    if (this.runDone && this.chart && !this.chart.isDisposed()) this.runDone();
    this.runDone = null;
  }
  playRuns(runs) {
    this.stopRuns();
    const model = this.chart.getModel(), zr = this.chart.getZr(), groups = [];
    for (const { sid, items, delay } of runs) {
      const sr = model.queryComponents({ mainType: 'series', id: sid })[0], data = sr && sr.getData(), jobs = [];
      if (!data) continue;
      items.forEach((it, q) => {
        const el = it.run && data.getItemGraphicEl(q);
        if (!el) return;
        const fr = it.run.frames;
        if (!fr.every(f => /^#[0-9a-f]{6}$/i.test(f.style.fill))) { el.style.fill = it.col; return; }
        el.style.fill = fr[0].style.fill;
        jobs.push({ el, p: el.shape.points, end: fr[fr.length - 1].style.fill, s: fr.map(f => [delay + f.percent * it.run.dur, ...mapHex(f.style.fill)]) });
      });
      const area = sr.coordinateSystem && sr.coordinateSystem.getArea && sr.coordinateSystem.getArea();
      if (jobs.length) groups.push({ jobs, area });
    }
    const all = groups.flatMap(g => g.jobs), layer = zr.painter.getLayer && zr.painter.getLayer(1);
    const done = () => { this.runDone = null; for (const j of all) { j.el.style.fill = j.end; j.el.markRedraw(); } zr.flush(); };
    if (!all.length) return;
    if (!layer || !layer.ctx) return done();   // no canvas layer to paint on: the finished picture at once
    const ctx = layer.ctx, cv = layer.dom, dpr = layer.dpr || 1, t0 = performance.now(), end = Math.max(...all.map(j => j.s[j.s.length - 1][0]));
    const frame = now => {
      const t = now - t0;
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      for (const { jobs, area } of groups) {
        const buckets = new Map();
        for (const j of jobs) {
          const s = j.s, n = s.length - 1;
          let r, g, b;
          if (t <= s[0][0]) [, r, g, b] = s[0];
          else if (t >= s[n][0]) [, r, g, b] = s[n];
          else {
            let q = 1; while (s[q][0] < t) q++;
            const A = s[q - 1], B = s[q], f = (t - A[0]) / (B[0] - A[0] || 1);
            r = A[1] + (B[1] - A[1]) * f; g = A[2] + (B[2] - A[2]) * f; b = A[3] + (B[3] - A[3]) * f;
          }
          const key = ((r | 0) >> 3) << 10 | ((g | 0) >> 3) << 5 | ((b | 0) >> 3);
          let list = buckets.get(key); if (!list) buckets.set(key, list = []);
          list.push(j.p);
        }
        ctx.save();
        if (area) { ctx.beginPath(); ctx.rect(area.x, area.y, area.width, area.height); ctx.clip(); }
        for (const [key, list] of buckets) {
          ctx.fillStyle = `rgb(${(key >> 10 & 31) * 8 + 4},${(key >> 5 & 31) * 8 + 4},${(key & 31) * 8 + 4})`;
          // at most 48 cells a path: one path of thousands of cells (all of them at the start) fills ~100x slower
          for (let c = 0; c < list.length; c += 48) {
            ctx.beginPath();
            for (const p of list.slice(c, c + 48)) { ctx.moveTo(p[0][0], p[0][1]); for (let k = 1; k < p.length; k++) ctx.lineTo(p[k][0], p[k][1]); ctx.closePath(); }
            ctx.fill();
          }
        }
        ctx.restore();
      }
      if (t < end && this.chart && !this.chart.isDisposed()) this.runRaf = requestAnimationFrame(frame);
      else done();
    };
    this.runDone = done;
    this.runRaf = requestAnimationFrame(frame);
  }

  /* data-pulse: once the cells have settled, two rings go out from each of the three sites, in the site's colour on
     a paper halo (so the ring reads on cells of its own colour too), so the places of the slide before are found */
  pulse() {
    const S = (window.MAPDATA && window.MAPDATA.sites) || [], i = this.mapAxes[0], s = this.s, zr = this.chart.getZr();
    if (!S.length || i === undefined) return;
    const r0 = 6 * s, r1 = 48 * s, rings = [];
    S.forEach((q, n) => {
      const [x, y] = this.chart.convertToPixel({ gridIndex: i }, [q.lon, q.lat]);
      for (const [stroke, lw] of [['#fbf8f1', 7.5], [q.color, 3.4]]) {
        const c = new echarts.graphic.Circle({ shape: { cx: x, cy: y, r: r0 }, style: { fill: 'none', stroke, lineWidth: lw * s, opacity: 0 }, silent: true, zlevel: 2, z: 100 });
        zr.add(c); rings.push({ c, at: 1900 + n * 220 });
      }
    });
    const D = 2200, ease = t => 1 - Math.pow(1 - t, 3), t0 = performance.now();
    const frame = now => {
      let live = false;
      for (const { c, at } of rings) {
        const t = (now - t0 - at) / D;
        if (t < 0) { live = true; continue; }
        if (t >= 1) { c.attr({ style: { opacity: 0 } }); continue; }
        live = true;
        const u = t < .5 ? t / .5 : (t - .5) / .5, e = ease(u);   // two rings, one after the other
        c.attr({ shape: { r: r0 + (r1 - r0) * e }, style: { opacity: .95 * (1 - e) } });
      }
      if (live && this.chart && !this.chart.isDisposed()) this.pulseRaf = requestAnimationFrame(frame);
      else rings.forEach(({ c }) => zr.remove(c));
    };
    cancelAnimationFrame(this.pulseRaf);
    this.pulseRaf = requestAnimationFrame(frame);
  }

  /* the entrance of a map already drawn: the same cells, set back to their first colour and run again (playRuns),
     without clearing and building the figure anew (some 100 series: a frame of a few hundred ms on arrival) */
  prepRuns() {
    if (this.runCache || !this.chart) return;
    const keep = [this.texs, this.series, this.legendName, this.siteSeries];
    this.option(0, true);
    this.runCache = this.mapRuns;
    [this.texs, this.series, this.legendName, this.siteSeries] = keep;
  }
  replay() {
    this.prepRuns();
    this.playRuns(this.runCache);
    if ('pulse' in this.host.dataset) this.pulse();
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

  barTip(i, b) {
    const a = this.d.axes[i], I = this.axisInfo(i), v = b.o === 'v', at = v ? (b.r[0] + b.r[2]) / 2 : (b.r[1] + b.r[3]) / 2;
    const ticks = (v ? a.x : a.y).ticks.filter(t => t[1] && t[1].trim());
    const near = ticks.length ? ticks.reduce((m, t) => Math.abs(t[0] - at) < Math.abs(m[0] - at) ? t : m) : null;
    const span = v ? Math.abs(b.r[2] - b.r[0]) : Math.abs(b.r[3] - b.r[1]);
    const cat = near && Math.abs(near[0] - at) <= span ? near[1].replace(/\n/g, ' ') : '';
    const part = this.legendName && this.legendName[String(b.fc || '').toLowerCase()] || '';
    const val = v ? b.r[3] - b.r[1] : b.r[2] - b.r[0], q = I.y.q && !part ? I.y.q : '';
    return tipCard({ head: cat || part || I.y.q, sub: [I.title && this.d.axes.length > 1 ? I.title : '', q].filter(Boolean).join(' · '),
                     rows: [{ c: b.fc, name: cat ? part : '', v: this.num(val, v ? I.y.u : I.x.u || I.y.u) }] });
  }
  barSeries(id, i, bars, base, s) {
    const xs = [...new Set(bars.map(b => b.o === 'v' ? b.r[0] : -b.r[1]))].sort((a, b) => a - b);
    return {
      id, type: 'custom', xAxisIndex: i, yAxisIndex: i, z: 2 + (bars[0].z || 0), clip: true,
      data: bars.map((b, q) => ({ value: [(b.r[0] + b.r[2]) / 2, (b.r[1] + b.r[3]) / 2], b, tip: this.barTip(i, b) })),
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
        const x = c.x[r[1]], y = c.y[r[0]][0], I = this.axisInfo(i), col = c.pal[r[3]];
        const val = v !== null ? this.num(v, I.y.u) : lab;
        const tip = val ? tipCard({ head: a.map ? tipPlace(x, y) : this.xText(x, I.x.u), sub: I.title || I.y.q, rows: [{ c: typeof col === 'string' ? col : null, v: val }] }) : null;
        return tip ? { value: [x, y], tip } : { value: [x, y], tooltip: { show: false } };
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
    this.stopRuns();
    if (fresh) { this.chart.clear(); for (const e of this.inner.querySelectorAll(':scope > .mtex')) e.remove(); }
    this.axTexs = [];
    this.chart.setOption(ecDraw(this.option(k, animate)), { replaceMerge: ['series', 'graphic', 'grid', 'xAxis', 'yAxis'] });
    if (animate && this.mapRuns.length) this.playRuns(this.mapRuns);
    if (animate && this.isMap && 'pulse' in this.host.dataset) this.pulse();
    this.placeAxTex();
    this.k = k;
    this.placeTex(animate);
  }
  placeAxTex() {
    if (!this.axTexs || !this.axTexs.length) return;
    if (!window.katex) { clearTimeout(this.axWait); this.axWait = setTimeout(() => this.placeAxTex(), 300); return; }
    for (const L of this.axTexs) axTex(this.inner, L.key, L.tex, L.x, L.y, L.fs);
  }
  placeTex(animate) {
    // formula symbols of the figure (its texts that are one $…$), set with KaTeX at their place, boxed in their
    // colour like the highlighted terms of the formulas (.hl.on); they come with their panel and its title,
    // without an entrance of their own, and one already there stays as it is
    const old = new Map([...this.inner.querySelectorAll(':scope > .mtex')].map(e => [e.dataset.key, e]));
    for (const { t, a, key } of this.texs) {
      const W = this.W, H = this.H, left = a.box[0] * W, top = a.box[1] * H, bw = a.box[2] * W, bh = a.box[3] * H;
      const x = left + (t.x - a.x.min) / (a.x.max - a.x.min) * bw, y = top + (a.y.max - t.y) / (a.y.max - a.y.min) * bh;
      let el = old.get(key); old.delete(key);
      if (!el) {
        // a symbol of the talk takes its colour role (as in the formulas); anything else keeps the figure's colour
        const role = CHART_TEX_ROLE[t.tex];
        el = document.createElement('span'); el.className = 'mtex' + (role ? ' c-' + role : ''); el.dataset.key = key;
        if (!role) el.style.setProperty('--c', t.c);
        katex.render(t.b ? `\\boldsymbol{${t.tex}}` : t.tex, el, { throwOnError: false, strict: false });
        this.inner.append(el);
      }
      const tx = t.al === 'right' ? '-100%' : t.al === 'center' ? '-50%' : '0';
      // KaTeX sets its formulas at 1.21 em: divided out, the symbol is as large as the figure's text of that size
      Object.assign(el.style, { left: x + 'px', top: y + 'px', transform: `translate(${tx},-50%)`, fontSize: (t.fs || 16) * this.s / 1.21 + 'px' });
    }
    for (const e of old.values()) e.remove();
  }
  play(k) {
    // a canvas map that already shows its one picture only runs its cells' entrance again (replay)
    if (!this.svg && this.chart && k === 0 && this.k === 0 && !this.nSteps && !this.timeLayer && !this.stops) return this.replay();
    this.set(Math.min(k, this.nSteps), true, k === 0 || this.k === null || k < this.k);
  }
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
/* light as a wave, like the heat radiation but with a shorter wavelength: the straight ray (.ray-l) keeps
   only its arrow tip, the dots (.ray-p, next to it) become the wave with running dashes. A straight tail
   lets the tip point along the ray. */
function waveRay(l) {
  const p = l.nextElementSibling;
  if (!p || !p.classList.contains('ray-p')) return;
  const [x1, y1, x2, y2] = l.getAttribute('d').match(/-?[\d.]+/g).map(Number);
  const w = parseFloat(l.style.getPropertyValue('--srw')) || 3, amp = 5;
  const len = Math.hypot(x2 - x1, y2 - y1), ux = (x2 - x1) / len, uy = (y2 - y1) / len;
  // a whole number of half-waves (wavelength about 26, stretched to fit), then a short straight end under the tip
  const waveLen = Math.max(0, len - 3.1 * w - 9), lam = 2 * waveLen / Math.max(1, Math.round(waveLen / 13));
  const pt = (s, o) => `${(x1 + ux * s - uy * o).toFixed(1)} ${(y1 + uy * s + ux * o).toFixed(1)}`;
  let d = 'M' + pt(0, 0);
  for (let s = lam / 16; s <= waveLen + 1e-6; s += lam / 16) d += ' L' + pt(s, amp * Math.sin(2 * Math.PI * s / lam));
  l.setAttribute('d', d + ' L' + pt(len, 0));
  p.setAttribute('d', d + ' L' + pt(len - 2.8 * w, 0));
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

/* count-up numbers: <span class="count" data-to="3.6" data-dec="1">; data-from starts at an earlier value */
function countUp(el, embed) {
  const to = +el.dataset.to, from = +(el.dataset.from || 0), dec = +(el.dataset.dec || 0), delay = +(el.dataset.delay || 0);
  const fmt = v => v.toLocaleString('de-DE', { minimumFractionDigits: dec, maximumFractionDigits: dec }).replace(/\./g, ' ');
  cancelAnimationFrame(el._raf);
  if (embed) { el.textContent = fmt(to); return; }
  const t0 = performance.now() + delay;
  const tick = now => {
    const p = easeOut(clamp01((now - t0) / 1400));
    el.textContent = fmt(from + (to - from) * p);
    if (p < 1) el._raf = requestAnimationFrame(tick);
  };
  el.textContent = fmt(from); el._raf = requestAnimationFrame(tick);
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
    // what the keys do, for a touch screen: replay, full screen, hover effects, notes, backup
    this.acts = this.el.querySelector('.menu-acts');
    if (!document.documentElement.requestFullscreen) this.acts.querySelector('[data-act="full"]').remove();   // iPhone Safari
    this.acts.addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      const d = this.deck, a = b.dataset.act;
      if (a === 'replay') { this.close(); d.go(d.i, d.step); }
      else if (a === 'full') d.fullscreen();
      else if (a === 'hover') d.tips(!document.documentElement.classList.contains('notips'));
      else if (a === 'notes') { this.close(); d.notes(); }
      else if (a === 'backup') { this.close(); d.go(d.mainEnd, 0); }
      this.state();
    });
    addEventListener('fullscreenchange', () => this.state());
    this.body.addEventListener('click', e => { const c = e.target.closest('.card'); if (c) this.jump(+c.dataset.i); });
    // keep the deck's wheel and swipe navigation out of the overview
    for (const t of ['wheel', 'touchstart', 'touchend']) this.el.addEventListener(t, e => e.stopPropagation(), { passive: true });
    addEventListener('keydown', e => this.key(e), true);
    addEventListener('resize', () => { if (this.isOpen) this.scale(); });
  }
  get isOpen() { return this.el.classList.contains('open'); }
  state() {
    const q = a => this.acts.querySelector(`[data-act="${a}"]`), set = (a, on) => q(a) && q(a).setAttribute('aria-pressed', on);
    set('hover', !document.documentElement.classList.contains('notips'));
    set('notes', this.deck.drawer.classList.contains('open'));
    set('full', !!document.fullscreenElement);
  }
  build() {
    const d = this.deck, seen = new Set(); let html = '', grid = false;
    const names = { baeume: 'Bäume', klima: 'Klima', vergleich: 'Potenzial' };
    const open = t => { if (grid) html += '</div>'; html += `<h3>${t}</h3><div class="menu-grid">`; grid = true; };
    d.slides.forEach((s, i) => {
      if (i === 0) open('Vortrag');
      if (i === d.mainEnd) open('Backup');
      else if (s.classList.contains('chapter') && i > 0 && i < d.mainEnd) open(s.dataset.title || 'Kapitel');
      else if (i < d.mainEnd && names[s.dataset.ch] && !seen.has(s.dataset.ch)) open(names[s.dataset.ch]);   // where a chapter begins
      if (s.dataset.ch) seen.add(s.dataset.ch);
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
    this.el.classList.add('open'); this.fab.setAttribute('aria-expanded', 'true'); this.state();
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
    if (e.metaKey || e.ctrlKey || e.altKey || e.target.isContentEditable || e.target.closest('input, textarea, select')) return;
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
    // live iframes (woodway): only on this slide and the next, and only in the projector window. Opened from a local
    // file (offline in the hall) the app is not one level up, the folder is: the poster stands instead
    if (!document.documentElement.classList.contains('embed') && !deckLean && location.protocol !== 'file:')
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
    this.drawer.querySelector('.dr-pop')?.addEventListener('click', () => this.openNotesWindow());
    this.progress = document.querySelector('.progress');
    this.i = 0; this.step = 0; this.showAll = location.search.includes('all');
    this.embed = location.search.includes('embed') || !!window.__EMBED;   // slide preview inside the presenter view
    this.host = location.search.includes('host');      // inside the React deck: it supplies the chrome
    if (this.host) document.documentElement.classList.add('host');
    this.still = this.embed || this.showAll;
    if (this.showAll) document.documentElement.classList.add('all');
    this.peer = null;                                 // the presenter window, once it has spoken
    this.peers = new Set();                           // every window that follows the talk (presenter, notes)
    this.mainEnd = this.slides.findIndex(s => s.classList.contains('backup'));
    if (this.mainEnd < 0) this.mainEnd = this.slides.length;
    this.decorate();
    this.fit(); addEventListener('resize', () => this.fit());
    if (window.visualViewport) visualViewport.addEventListener('resize', () => this.fit());   // mobile toolbars, the phone's pinch zoom
    addEventListener('message', e => this.onMessage(e));
    if (!this.embed) { this.bind(); this.menu = new SlideMenu(this); }
    const h = parseInt(location.hash.slice(1), 10);
    this.go(Number.isFinite(h) ? h - 1 : 0, 0);
    this.booted = true;
    this.hint(5000);
    this.rotateHint();
    this.notesEditor();
  }
  hint(ms) {
    // the shortcut line at the top: on arrival, and again with I, then it fades
    const h = document.getElementById('hint'); h.classList.remove('gone');
    clearTimeout(this._hint); this._hint = setTimeout(() => h.classList.add('gone'), ms);
  }
  rotateHint() {
    // a phone held upright shows the 16:9 slide at a quarter of its size: say so once, gently
    if (this.embed || !matchMedia('(pointer: coarse)').matches) return;
    try { if (sessionStorage.getItem('dv-rotate')) return; } catch (e) { /* no storage */ }
    const portrait = matchMedia('(orientation: portrait) and (max-width: 820px)');
    const show = () => {
      if (!portrait.matches || document.getElementById('rotate')) return;
      const r = document.createElement('button'); r.id = 'rotate'; r.type = 'button';
      r.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="7" y="3" width="10" height="18" rx="2"/><path d="M3 13a9 9 0 0 0 7 8M21 11a9 9 0 0 0-7-8"/></svg>Quer halten für größere Folien';
      const done = () => { r.classList.add('gone'); setTimeout(() => r.remove(), 400); try { sessionStorage.setItem('dv-rotate', '1'); } catch (e) { /* */ } };
      r.addEventListener('click', done); setTimeout(done, 7000);
      document.body.appendChild(r);
    };
    show(); portrait.addEventListener('change', () => { if (!portrait.matches) { const r = document.getElementById('rotate'); if (r) r.click(); } });
  }
  toast(text) {
    // a toggle confirmed, small, bottom right, for a moment
    let t = document.getElementById('toast');
    if (!t) { t = document.createElement('div'); t.id = 'toast'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
    t.textContent = text; t.classList.add('on');
    clearTimeout(this._toast); this._toast = setTimeout(() => t.classList.remove('on'), 1600);
  }
  onMessage(e) {
    const d = e.data;
    // embedded woodway hands back the paging keys once a click has put focus into it
    if (d && d.src === 'woodway-key' && !this.embed) { if (d.dir === 'next') this.next(); else if (d.dir === 'prev') this.prev(); return; }
    if (!d || d.src !== 'dv') return;
    if (this.embed) { if ('goto' in d) { this.go(d.goto, d.step); this.markNew(d.mark ? d.step : 0); } return; }
    if (e.source) this.peers.add(e.source);
    if (d.cmd === 'next') this.next(); else if (d.cmd === 'prev') this.prev();
    else if (d.cmd === 'first') this.go(0, 0); else if (d.cmd === 'last') this.go(this.mainEnd - 1, 0);
    else if (d.cmd === 'replay') this.go(this.i, this.step);
    else if (d.cmd === 'notes' && this.canEdit && Number.isInteger(d.n) && typeof d.html === 'string') this.saveNotesFrom(d.n, d.html, e.source);
    else if (d.cmd === 'goto' && Number.isInteger(d.n)) {
      const n = Math.max(0, Math.min(this.slides.length - 1, d.n));
      this.go(n, d.step === 'end' ? 'end' : Number.isInteger(d.step) ? d.step : 0);   // 'end' like prev(): the last state, drawn without replaying the slide
    }
    else if (d.cmd === 'hello') this.sync();
    else if (d.cmd === 'cursor') this.cursor(!!d.off);
  }
  cursor(off) {
    // C: the mouse pointer off over the whole page (a laser pointer draws its own), kept for the session
    document.documentElement.classList.toggle('nocursor', off);
    if (this.booted) this.toast(off ? 'Mauszeiger aus' : 'Mauszeiger an');
    try { sessionStorage.setItem('dv-nocursor', off ? '1' : ''); } catch (e) { /* private mode: only for this page */ }
  }
  async notesEditor() {
    // E: edit mode, when the deck is served by deck/serve.py on this computer: the notes and the texts on the slides
    // become editable and are saved as you type, into the slide sources. The hosted deck has no such endpoint, so
    // there is no edit mode there.
    if (this.embed || !/^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname)) return;
    try { const r = await fetch('/__notes', { cache: 'no-store' }); if (!r.ok || !(await r.json()).edit) return; } catch (e) { return; }
    this.canEdit = true;
    const bar = this.drawer.querySelector('.dr-edit'); bar.hidden = false;
    bar.addEventListener('click', e => { if (e.target.closest('[data-ed="edit"]')) this.edit(!this.editing); });
    // typing: each changed text saved shortly after the last key (Cmd+Z is the browser's own, and is saved the same way)
    document.addEventListener('input', e => {
      if (!this.editing) return;
      const el = e.target.closest && e.target.closest('.slide [data-e], #drawer-body .ned');
      if (el) this.queueSave(el);
      if (el && el.classList.contains('ned')) { this.typedAt = performance.now(); requestAnimationFrame(() => this.noteGutter()); }
    }, true);
    // Cmd+Z in the notes: a click assignment made after the last typing is undone here (the browser's own undo knows only the text)
    this.clickHist = []; this.clickRedo = []; this.typedAt = 0;
    document.addEventListener('keydown', e => {
      if (!this.editing || !(e.metaKey || e.ctrlKey) || e.key.toLowerCase() !== 'z' || !e.target.closest || !e.target.closest('#drawer-body .ned')) return;
      const redo = e.shiftKey, from = redo ? this.clickRedo : this.clickHist, to = redo ? this.clickHist : this.clickRedo;
      const op = from[from.length - 1];
      if (!op || (!redo && op.t < this.typedAt)) return;   // the last change was typing: the browser undoes it
      e.preventDefault(); from.pop();
      this.applyClick(op.p, redo ? op.after : op.before); op.t = performance.now(); to.push(op);
      this.queueSave(op.p.closest('.ned')); this.markNotes();
    }, true);
    // Esc leaves the text (the arrows turn pages again); Enter in a slide text does not start a new block
    document.addEventListener('keydown', e => {
      if (!e.target.isContentEditable) return;
      if (e.key === 'Escape') { e.preventDefault(); e.target.blur(); }
      else if (e.key === 'Enter' && e.target.closest('.slide [data-e]')) e.preventDefault();
    }, true);
    this.saveQ = Promise.resolve(); this.pending = new Map();
    // a click on a formula opens its code
    document.addEventListener('click', e => {
      if (!this.editing || e.target.closest('#texed')) return;
      const f = e.target.closest('.slide.active [data-tk]') || e.target.closest('.slide.active svg [data-e]');
      if (f) { e.preventDefault(); e.stopPropagation(); this.texEdit(f); }
    }, true);
  }
  texEdit(span) {
    // a formula, or a drawing's label: its code in a small window beside it; typing shows it at once and saves like the texts
    this.texClose();
    const label = span instanceof SVGElement;
    const src = label ? span.innerHTML : span.dataset.tsrc, disp = !label && src.startsWith('$$'), r = span.getBoundingClientRect();
    const w = document.createElement('div'); w.id = 'texed';
    w.innerHTML = '<textarea spellcheck="false"></textarea><span class="te-msg">Esc schließt · ⌘Z rückgängig</span>';
    const ta = w.querySelector('textarea'); ta.value = label ? src.trim() : src.slice(disp ? 2 : 1, disp ? -2 : -1);
    document.body.append(w);
    const top = r.bottom + 10 + w.offsetHeight < innerHeight ? r.bottom + 10 : Math.max(10, r.top - 10 - w.offsetHeight);
    w.style.left = `${Math.max(10, Math.min(innerWidth - w.offsetWidth - 10, r.left))}px`; w.style.top = `${top}px`;
    ta.style.height = `${Math.min(220, ta.scrollHeight + 4)}px`;
    ta.focus();
    span.classList.add('tex-on');
    let old = src, t;
    const render = () => {
      if (label) {   // the label as typed, saved as the text's content in the source
        span.innerHTML = ta.value;
        clearTimeout(t); t = setTimeout(() => {
          if (!span.textContent.trim()) return;
          const item = { src: span.closest('.slide').dataset.src, e: span.dataset.e, old: span._old, html: ta.value }, now = span.textContent;
          this.editStatus('speichert …');
          this.saveQ = this.saveQ.then(async () => {
            try {
              const q = await fetch('/__notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ items: [item] }) });
              const j = await q.json(); if (!q.ok) throw new Error(j.error || q.status);
              span._old = now; this.editStatus('gespeichert');
            } catch (e) { this.editStatus(`nicht gespeichert: ${e.message}`, true); }
          });
        }, 700);
        return;
      }
      const code = ta.value, full = disp ? `$$${code}$$` : `$${code}$`, holder = document.createElement('span');
      try { katex.render(code, holder, { displayMode: disp, macros: TEX_MACROS, throwOnError: true, strict: false, trust: c => c.command === '\\htmlData' || c.command === '\\htmlClass' }); }
      catch (e) { w.querySelector('.te-msg').textContent = e.message.replace(/^KaTeX parse error: /, ''); w.classList.add('bad'); return; }
      w.classList.remove('bad'); w.querySelector('.te-msg').textContent = 'Esc schließt · ⌘Z rückgängig';
      span.replaceChildren(...holder.childNodes); span.dataset.tsrc = full;
      for (const e of span.querySelectorAll('[data-step]')) e.classList.toggle('shown', (+e.dataset.step || 0) <= this.step);
      clearTimeout(t); t = setTimeout(() => {
        if (full === old) return;
        const item = { src: span.closest('.slide').dataset.src, tk: span.dataset.tk, old, tex: full };
        this.editStatus('speichert …');
        this.saveQ = this.saveQ.then(async () => {
          try {
            const q = await fetch('/__notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ items: [item] }) });
            const j = await q.json(); if (!q.ok) throw new Error(j.error || q.status);
            old = full; this.editStatus('gespeichert');
          } catch (e) { this.editStatus(`nicht gespeichert: ${e.message}`, true); }
        });
      }, 700);
    };
    ta.addEventListener('input', render);
    ta.addEventListener('keydown', e => { if (e.key === 'Escape') { e.preventDefault(); this.texClose(); } });
    this._texOff = e => { if (!w.contains(e.target) && !e.target.closest('[data-tk], svg [data-e]')) this.texClose(); };
    setTimeout(() => document.addEventListener('pointerdown', this._texOff, true));
    this._texSpan = span;
  }
  texClose() {
    const w = document.getElementById('texed'); if (w) w.remove();
    if (this._texSpan) this._texSpan.classList.remove('tex-on'); this._texSpan = null;
    if (this._texOff) document.removeEventListener('pointerdown', this._texOff, true);
  }
  edit(on) {
    if (!this.canEdit) return;
    if (!on) this.texClose();
    this.editing = on;
    document.documentElement.classList.toggle('editmode', on);
    this.drawer.querySelector('[data-ed="edit"]').textContent = on ? 'Fertig' : 'Bearbeiten';
    if (!on) { this.flushSave(); if (document.activeElement && document.activeElement.isContentEditable) document.activeElement.blur(); }
    this.editSlide(this.slides[this.i], on);
    if (!on) { const n = this.slides[this.i].querySelector('.notes'); this.drawerBody.innerHTML = n && n.innerHTML.trim() ? n.innerHTML : '<p class="q">Keine Notizen.</p>'; }
    this.editStatus(on ? 'Bearbeiten: Texte und Notizen' : '');
    this.toast(on ? 'Bearbeiten an' : 'Bearbeiten aus');
  }
  editSlide(s, on) {
    // the slide's texts, and its notes in an editor of their own (kept per slide: Cmd+Z still has its history)
    for (const el of s.querySelectorAll('[data-e]')) {
      if (el instanceof SVGElement) { if (on && el._old === undefined) el._old = el.textContent; continue; }   // a drawing's label: its code in a window (texEdit)
      el.contentEditable = on ? 'true' : 'false'; el.spellcheck = false;
      if (on && el._old === undefined) el._old = el.textContent;
    }
    if (!on) return;
    let box = this.drawerBody.querySelector(':scope > .neds');
    if (!box) { this.drawerBody.innerHTML = '<div class="neds"></div>'; box = this.drawerBody.firstChild; }
    for (const n of box.children) n.hidden = true;
    let ed = [...box.children].find(n => n.dataset.src === s.dataset.src);
    if (!ed) {
      const n = s.querySelector('.notes');
      ed = document.createElement('div'); ed.className = 'ned'; ed.dataset.src = s.dataset.src; ed.contentEditable = 'true'; ed.spellcheck = false;
      ed.innerHTML = n && n.innerHTML.trim() ? n.innerHTML : '<p><br></p>';
      box.append(ed);
    }
    ed.hidden = false;
    document.execCommand('defaultParagraphSeparator', false, 'p');
    this.markNotes();
  }
  noteGutter() {
    // edit mode: beside each paragraph of the notes a chip with its click; a click on the chip opens the choice
    const box = this.drawerBody.querySelector(':scope > .neds'), ed = box && box.querySelector(':scope > .ned:not([hidden])');
    if (!box) return;
    let g = box.querySelector(':scope > .ned-gut');
    if (!g) {
      g = document.createElement('div'); g.className = 'ned-gut'; box.append(g);
      g.addEventListener('mousedown', e => e.preventDefault());   // the cursor stays where it was
      g.addEventListener('click', e => { const c = e.target.closest('.nck'); if (c) this.clickMenu(c); });
    }
    g.innerHTML = ''; if (!ed || !this.editing) return;
    const s = this.slides[this.i];
    for (const x of noteItems([...ed.querySelectorAll(':scope > p')], +s.dataset.start || 0, this.steps(s))) {
      const c = document.createElement('button'); c.type = 'button'; c._p = x.el;
      c.className = 'nck' + (x.q ? ' q' : '') + (!x.q && !x.el.hasAttribute('data-click') ? ' auto' : '') + (x.el.classList.contains('now') ? ' now' : '');
      c.textContent = x.q ? 'Hintergrund' : noteLabel(x);
      c.title = 'Klick wählen'; c.style.top = x.el.offsetTop + 'px'; g.append(c);
    }
  }
  clickMenu(chip) {
    // the choice for one paragraph: the slide's clicks (Shift: up to this click, for a paragraph that stays), background
    document.querySelector('.nck-menu')?.remove();
    const p = chip._p, s = this.slides[this.i], start = +s.dataset.start || 0, total = Math.max(this.steps(s), start);
    const [lo, hi] = (p.getAttribute('data-click') || '').split('-').map(Number);
    const m = document.createElement('div'); m.className = 'nck-menu';
    let h = '';
    for (let k = start; k <= total; k++) h += `<button type="button" data-k="${k}" class="${k >= lo && k <= (hi || lo) && !p.classList.contains('q') ? 'on' : ''}${k === this.step ? ' here' : ''}">${k === 0 ? 'Start' : k}</button>`;
    m.innerHTML = `<div class="nm-row">${h}</div><div class="nm-row"><button type="button" data-k="q" class="${p.classList.contains('q') ? 'on' : ''}">Hintergrund</button><span class="nm-hint">Shift+Klick: bis zu diesem Klick · gelb umrandet: jetzt</span></div>`;
    m.style.top = (chip.offsetTop + chip.offsetHeight + 4) + 'px';
    chip.parentElement.append(m);
    m.addEventListener('mousedown', e => e.preventDefault());
    m.addEventListener('click', e => {
      const b = e.target.closest('[data-k]'); if (!b) return;
      if (b.dataset.k === 'q') this.setClick(p, { q: true });
      else {
        const k = +b.dataset.k, a = isNaN(lo) || p.classList.contains('q') ? k : lo;
        this.setClick(p, { click: e.shiftKey && a !== k ? `${Math.min(a, k)}-${Math.max(a, k)}` : String(k) });
      }
      m.remove();
    });
    const off = e => { if (!m.contains(e.target) && e.target !== chip) { m.remove(); document.removeEventListener('pointerdown', off, true); } };
    document.addEventListener('pointerdown', off, true);
  }
  readClick(p) { return { click: p.getAttribute('data-click'), q: p.classList.contains('q') }; }
  applyClick(p, v) {
    p.classList.toggle('q', !!v.q);
    if (v.q || v.click === null || v.click === undefined) p.removeAttribute('data-click'); else p.setAttribute('data-click', v.click);
  }
  setClick(p, v) {
    const before = this.readClick(p);
    this.applyClick(p, v);
    this.clickHist.push({ p, before, after: this.readClick(p), t: performance.now() }); this.clickRedo = [];
    this.queueSave(p.closest('.ned')); this.markNotes();
  }
  clean(html) {
    // the page's own additions taken out again: subscript digits (subDigits) back to the characters of the source
    const SUP = { 0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶', 7: '⁷', 8: '⁸', 9: '⁹', '+': '⁺', '−': '⁻' };
    return html.replace(/<span class="subd">(\d+)<\/span>/g, (_, d) => [...d].map(c => String.fromCharCode(c.charCodeAt(0) + 0x2050)).join(''))
      .replace(/<sup class="sx">([^<]+)<\/sup>/g, (_, d) => [...d].map(c => SUP[c] || c).join(''))   // supText's superscripts
      .replace(/ class="(?:now| *)"/g, '').replace(/ class="(q) now"| class="now (q)"/g, ' class="q"')   // the lit paragraph of this click is the page's own mark
      .replace(/(<br>)+(?=<\/p>|$)/g, '').replace(/&nbsp;/g, ' ');
  }
  queueSave(el) {
    this.pending.set(el, true); this.editStatus('ungespeichert …');
    clearTimeout(this._saveT); this._saveT = setTimeout(() => this.flushSave(), 700);
  }
  flushSave() {
    clearTimeout(this._saveT);
    if (!this.pending || !this.pending.size) return;
    const els = [...this.pending.keys()]; this.pending.clear();
    const items = [], done = [];
    for (const el of els) {
      const html = this.clean(el.innerHTML);
      if (el.classList.contains('ned')) { items.push({ src: el.dataset.src, html }); done.push(() => { const n = this.slides.find(x => x.dataset.src === el.dataset.src)?.querySelector('.notes'); if (n) n.innerHTML = html; this.sync(); }); }
      else {
        if (!el.textContent.trim()) continue;   // an emptied text is not saved (Cmd+Z brings it back)
        const now = el.textContent;
        items.push({ src: el.closest('.slide').dataset.src, e: el.dataset.e, old: el._old, html }); done.push(() => { el._old = now; });
      }
    }
    if (!items.length) { this.editStatus('gespeichert'); return; }
    this.editStatus('speichert …');
    this.saveQ = this.saveQ.then(async () => {
      try {
        const r = await fetch('/__notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ items }) });
        const j = await r.json(); if (!r.ok) throw new Error(j.error || r.status);
        done.forEach(f => f()); this.editStatus(this.pending.size ? 'ungespeichert …' : 'gespeichert');
      } catch (e) { this.editStatus(`nicht gespeichert: ${e.message}`, true); }
    });
  }
  editStatus(t, bad) {
    const m = this.drawer.querySelector('.dr-msg'); m.textContent = t; m.classList.toggle('bad', !!bad);
    let b = document.getElementById('edit-badge');
    if (!b) { b = document.createElement('div'); b.id = 'edit-badge'; b.setAttribute('role', 'status'); document.body.appendChild(b); }
    b.textContent = this.editing ? `Bearbeiten · ${t === 'Bearbeiten: Texte und Notizen' ? 'Text anklicken' : t}` : ''; b.classList.toggle('bad', !!bad);
  }
  notes() { this.drawer.inert = !this.drawer.classList.toggle('open'); this.toast(this.drawer.inert ? 'Notizen aus' : 'Notizen an'); }
  fullscreen() {
    const on = !document.fullscreenElement;
    on ? document.documentElement.requestFullscreen?.() : document.exitFullscreen();
    this.toast(on ? 'Vollbild an' : 'Vollbild aus');
  }
  tips(off) {
    // H: the charts' hover effects off (presenting with a pointer): no tooltip, no dashed line, no hover dots. Kept for the session
    document.documentElement.classList.toggle('notips', off);
    if (off && this.hideTips) this.hideTips();
    try { sessionStorage.setItem('dv-notips', off ? '1' : ''); } catch (e) { /* private mode: only for this page */ }
    this.toast(off ? 'Hover-Effekte aus' : 'Hover-Effekte an');
  }
  sync() {
    // Tell the presenter window where we are and what comes next.
    this.markNotes();
    if (this.embed) return;
    for (const w of [...this.peers]) if (!w || w.closed) this.peers.delete(w);
    if (!this.peers.size) return;
    let ni = this.i, ns = this.step + 1;
    if (ns > this.steps(this.slides[this.i])) { ni = this.i + 1; ns = 0; }
    const cs = this.slides[this.i], nt = cs.querySelector('.notes');
    const msg = { src: 'dv', state: { i: this.i, step: this.step, ni, ns, n: this.slides.length, main: this.mainEnd, start: +cs.dataset.start || 0, steps: this.steps(cs), notes: nt ? nt.innerHTML : '' } };
    for (const w of this.peers) w.postMessage(msg, '*');
  }
  saveNotesFrom(n, html, from) {
    // notes typed in the presenter window: into the slide's source (serve.py), and into the page; the presenter hears back
    const s = this.slides[n]; if (!s) return;
    html = this.clean(html);
    const nt = s.querySelector('.notes'); if (nt) nt.innerHTML = html;
    const ed = this.drawerBody.querySelector(`.ned[data-src="${s.dataset.src}"]`); if (ed && ed !== document.activeElement) ed.innerHTML = html;
    if (n === this.i && !this.editing) this.drawerBody.innerHTML = html.trim() ? html : '<p class="q">Keine Notizen.</p>';
    this.saveQ = this.saveQ.then(async () => {
      try {
        const r = await fetch('/__notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ items: [{ src: s.dataset.src, html }] }) });
        const j = await r.json(); if (!r.ok) throw new Error(j.error || r.status);
        from && !from.closed && from.postMessage({ src: 'dv', saved: true }, '*'); this.sync();
      } catch (e) { from && !from.closed && from.postMessage({ src: 'dv', saved: false, error: e.message }, '*'); }
    });
    this.markNotes();
  }
  markNew(step) {
    // the presenter's preview of the next click: what this click brings in, framed in red (not the whole slide, not the
    // invisible markers that only switch a state)
    for (const el of document.querySelectorAll('.pv-new')) el.classList.remove('pv-new');
    if (!step) return;
    const s = this.slides[this.i], sb = s.getBoundingClientRect(), area = sb.width * sb.height;
    for (const el of s.querySelectorAll(`[data-step="${step}"]`)) {
      if (el.closest('.notes') || el.hidden) continue;
      const r = el.getBoundingClientRect(); if (r.width < 2 || r.height < 2 || r.width * r.height > .7 * area) continue;
      el.classList.add('pv-new');
    }
  }
  markNotes() {
    // the paragraphs of this click lit in the notes drawer (and in the editor)
    const s = this.slides[this.i]; if (!s || this.embed) return;
    const box = this.drawerBody.querySelector(':scope > .neds > .ned:not([hidden])') || this.drawerBody;
    const els = [...box.querySelectorAll(':scope > p')]; if (!els.length) return;
    const foc = noteFocus(noteItems(els, +s.dataset.start || 0, this.steps(s)), this.step);
    for (const el of els) el.classList.remove('now');
    for (const [x, k] of foc) if (k === 'cur') x.el.classList.add('now');
    if (this.editing) this.noteGutter();
  }
  openPresenter() {
    // presenting: no hover effects on the charts, no mouse pointer on the slides (as H and C)
    if (!document.documentElement.classList.contains('notips')) this.tips(true);
    if (!document.documentElement.classList.contains('nocursor')) this.cursor(true);
    if (this.peer && !this.peer.closed) { this.peer.focus(); return; }
    this.peer = window.open(location.href.split(/[?#]/)[0] + '?presenter', 'dv-presenter', 'width=1440,height=900');
    if (this.peer) this.peers.add(this.peer);
  }
  openNotesWindow() {
    // O: the notes alone in a window of their own, to put beside the slides (and edit there, on the local server)
    if (this.notesWin && !this.notesWin.closed) { this.notesWin.focus(); return; }
    this.notesWin = window.open(location.href.split(/[?#]/)[0] + '?presenter&notes', 'dv-notes', 'width=760,height=900');
    if (this.notesWin) this.peers.add(this.notesWin);
  }
  decorate() {
    // Where the talk stands, top right: the three chapter discs in order, the current one larger in its ring with the
    // part we are in lit, and left of them the chapter and the part by name. Only in the three chapters' main slides;
    // a click opens the chapter
    const opener = c => this.slides.findIndex(s => s.dataset.ch === c);   // a chapter's first slide
    const path = (ch, part) => {
      const el = document.createElement('nav'); el.className = 'path'; el.setAttribute('aria-label', 'Kapitel');
      const at = Object.keys(CHAPTERS).indexOf(ch);
      el.dataset.at = `${ch}:${part}`;
      el.innerHTML = Object.keys(CHAPTERS).map((c, k) => {
        const arcs = k !== at ? ['track', 'track'] : part === 1 ? ['on', 'track'] : ['track', 'on'];   // only the part we are in lit
        const where = k === at ? `<span class="where"><i>${CHAPTERS[ch].name}</i><b>${CHAPTERS[ch].parts[part - 1][1]}</b></span>` : '';
        return `<button type="button" class="pc${k === at ? ' on' : ''}" data-ch="${c}" aria-label="Kapitel ${CHAPTERS[c].name}"${k === at ? ' aria-current="true"' : ''}>${ringSvg(c, arcs, k === at ? part : 0)}${where}</button>`;
      }).join('');
      el.addEventListener('click', e => {
        const b = e.target.closest('.pc'); if (!b) return;
        e.stopPropagation(); const n = opener(b.dataset.ch); if (n >= 0) this.go(n, 0);
      });
      return el;
    };
    subDigits(this.deck);
    // the chapter discs on the closing cards in their rings too: a finished chapter's closed, the others pale
    for (const d of this.deck.querySelectorAll('.ovtrail .ic > svg[data-fly]')) {
      const c = d.dataset.fly, done = d.closest('.st').classList.contains('done');
      d.insertAdjacentHTML('beforebegin', ringSvg(c, done ? ['done', 'done'] : ['track', 'track']));
      d.previousElementSibling.querySelector('use').dataset.fly = c; d.remove();
    }
    // a chapter's disc in its ring: on an opener both parts in their colours (it flies on into the corner of the
    // first slide); each disc can fly into its chapter
    for (const d of this.deck.querySelectorAll('[data-ring]')) {
      d.innerHTML = ringSvg(d.dataset.ring, ['on', 'on']);
      d.querySelector('use').dataset.fly = d.dataset.ring;
    }
    for (const d of this.deck.querySelectorAll('[data-disc]')) {   // the bare disc, no ring yet (slide 4)
      d.innerHTML = `<svg viewBox="0 0 100 100" aria-hidden="true"><use href="#${CHAPTERS[d.dataset.disc].disc}" width="100" height="100" data-fly="${d.dataset.disc}"/></svg>`;
    }
    this.slides.forEach((s, n) => {
      const ch = s.dataset.ch, h = s.querySelector('.sh');
      if (h && CHAPTERS[ch] && s.dataset.part && !s.hasAttribute('data-nonav') && n < this.mainEnd) h.appendChild(path(ch, +s.dataset.part));
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
    const plain = !s.matches('.chapter, .title'), cs = getComputedStyle(s);
    const v = { '--stage': bg, '--ground': plain ? cs.getPropertyValue('--ch') : 'transparent',
      '--bar': cs.getPropertyValue(plain && !s.matches('.dark') ? '--ch' : '--ch-soft') };
    // set only what changed: a property on the root restyles the whole page
    const root = document.documentElement.style;
    for (const [k, x] of Object.entries(v)) if (root.getPropertyValue(k) !== x) root.setProperty(k, x);
    document.querySelector('meta[name="theme-color"]').setAttribute('content', bg);
  }
  fit() {
    // the visible viewport where there is one (mobile toolbars), the window otherwise; never while the phone is
    // pinch-zoomed in: iOS then reports the zoomed-in part as the window, and fitting the deck to it would undo the zoom
    this.zoomState();
    if (pinchZoomed() && this.k) return;
    const W = window.visualViewport ? visualViewport.width : innerWidth;
    const H = window.visualViewport ? visualViewport.height : innerHeight;
    const k = Math.min(W / 1600, H / 900);
    this.k = k; this.W = W; this.H = H;
    this.place();
    document.documentElement.style.setProperty('--tipk', Math.min(2.6, Math.max(1, .8 / k)).toFixed(3));   // tooltips at least ~14px on screen
  }
  place() {
    // fitted to the window, then the deck's own zoom (z, around the deck centre shifted by tx, ty), the shift kept so
    // the slide never leaves an empty edge
    const z = this.z || 1, w = 1600 * this.k * z, h = 900 * this.k * z;
    const cx = Math.max(0, (w - this.W) / 2), cy = Math.max(0, (h - this.H) / 2);
    this.tx = Math.max(-cx, Math.min(cx, this.tx || 0)); this.ty = Math.max(-cy, Math.min(cy, this.ty || 0));
    this.deck.style.transform = `translate(${this.tx}px, ${this.ty}px) translate(-50%, -50%) scale(${this.k * z})`;
    this.zoomState();
  }
  zoomState() {
    // zoomed in, by the deck (laptop) or by the phone's own pinch: the charts let the pointer and fingers through
    document.documentElement.classList.toggle('zoomed', (this.z || 1) > 1.001 || pinchZoomed());
  }
  zoomAt(f, x = this.W / 2, y = this.H / 2) {
    // zoom by f around the screen point (x, y): that point of the slide stays under it. Pinch on a trackpad,
    // Ctrl/Cmd + wheel, Ctrl/Cmd + plus/minus; 1 to 6 times
    const z0 = this.z || 1, z = Math.max(1, Math.min(6, z0 * f)), r = z / z0;
    const px = x - this.W / 2, py = y - this.H / 2;
    this.tx = px - (px - (this.tx || 0)) * r; this.ty = py - (py - (this.ty || 0)) * r;
    this.z = z; this.place();
  }
  zoomReset() { if ((this.z || 1) > 1.001) { this.z = 1; this.tx = this.ty = 0; this.place(); } }
  pan(dx, dy) { this.tx = (this.tx || 0) + dx; this.ty = (this.ty || 0) + dy; this.place(); }
  steps(s) {
    // clicks on this slide: the highest data-step, including chart panels behind their host's step
    if (s._steps === undefined) {
      let n = 0;
      for (const e of s.querySelectorAll('[data-step]')) n = Math.max(n, +e.dataset.step || 0);
      for (const h of s.querySelectorAll('.chart')) if (h._chart) n = Math.max(n, (+h.dataset.step || 0) + h._chart.nSteps);
      if (s.dataset.end !== undefined) n = Math.min(n, +s.dataset.end);   // data-end: a split slide stops here, the next slide goes on
      s._steps = n;
    }
    return s._steps;
  }
  go(n, step) {
    n = Math.max(0, Math.min(this.slides.length - 1, n));
    if (this.hideTips && this.slides[this.i]) this.hideTips();   // no tooltip stays open over the next slide
    if (this.booted && window.__deckDataNow) window.__deckDataNow();   // the speaker moves on: load the charts now
    if (window.__ensureCharts) { window.__ensureCharts(this.slides[n]); delete this.slides[n]._steps; }
    if (window.__ensureTex) window.__ensureTex(this.slides[n]);
    // the second half of a split slide (data-start) is made ready before we get there: formulas set and charts
    // built, so the cut shows the same picture from its first frame
    const nx = this.slides[n + 1];
    if (nx && nx.dataset.start !== undefined) { if (window.__ensureTex) window.__ensureTex(nx); if (window.__ensureCharts) window.__ensureCharts(nx); }
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
    if (n !== this.i) this.zoomReset();   // a new slide starts whole
    // slides of one drawing (data-carry): what the previous slide already shows stays as it is, it does not enter again
    s.classList.toggle('carry', !!(prev && prev !== s && !this.still && s.dataset.carry && s.dataset.carry === prev.dataset.carry));
    this.slides.forEach((x, k) => x.classList.toggle('active', k === n));
    if (prev && prev !== s && !this.still) this.swapPart(prev, s);
    s.classList.toggle('settled', step === 'end' || !!this.still || !s.classList.contains('arrive') && n !== this.i + 1);   // a chapter opener reached backwards or by a jump: its entrance stays still
    // a slide that plays its first clicks by itself (data-auto) is entered again from its finished state: its parts must
    // not first run back to the start (a visible flicker) before the auto clicks play them forward again
    if ((s.dataset.auto || s.dataset.start) && !this.still && step === 0) { s.classList.add('rearm'); requestAnimationFrame(() => requestAnimationFrame(() => s.classList.remove('rearm'))); }
    this.i = n; this.step = (step === 'end' || this.showAll) ? this.steps(s) : Math.max(step, +s.dataset.start || 0);   // data-start: the slide opens with its first clicks already played (a split slide: the same state as the one before)
    this.applyStep(!this.still && step !== 'end', true);
    if (s.dataset.gather && prev && prev !== s && this.slides.indexOf(prev) === n - 1 && step === 0 && !this.still && !deckCalm.matches) this.gather(prev, s);
    // data-auto="k": on arrival the slide plays its clicks up to k by itself (a change that belongs to the transition)
    clearTimeout(this._auto);
    if (s.dataset.auto && !this.still && step === 0) this._auto = setTimeout(() => {
      if (this.i === n && this.step < +s.dataset.auto) {
        if (s.dataset.morph && !deckCalm.matches) this.morphTerm(s);
        this.step = +s.dataset.auto; this.applyStep(true, false); this.schedulePlan();
      }
    }, 150);
    if (s.dataset.morphBack && prev && prev !== s && this.slides.indexOf(prev) === n - 1 && step === 0 && !this.still && !deckCalm.matches) this.morphBack(prev, s);
    this.schedulePlan();
    this.progress.style.transform = `scaleX(${Math.min(1, (n + 1) / this.mainEnd)})`;
    if (this.flying) this.staged = s; else this.stage(s);   // in a flight: after the landing (Deck.flyHome)
    if (!this.embed) history.replaceState(null, '', `#${n + 1}`);
    if (!this.embed && n !== this.said) { this.said = n; document.getElementById('sr-status').textContent = `Folie ${n + 1} von ${this.slides.length}: ${s.dataset.title || ''}`; }
    const notes = s.querySelector('.notes');
    if (this.editing) { if (prev && prev !== s) { this.texClose(); this.flushSave(); this.editSlide(prev, false); } this.editSlide(s, true); }   // editing goes on here
    else this.drawerBody.innerHTML = notes && notes.innerHTML.trim() ? notes.innerHTML : '<p class="q">Keine Notizen.</p>';
    this.sync();
  }
  morphTerm(s) {
    // one element: the highlighted term of the header line (data-morph) grows into the chip of the line that takes over.
    // A copy of the chip lies over the line, shown only through a window that starts as the term's own box and opens to
    // the whole chip; the term inside slides from its old place to its slot, the label and the unit come in from the left
    // and the right as the window widens. The old line fades; the rest of the new line follows when it is done.
    const line = s.querySelector('.fline.head'); if (!line) return;
    const src = line.querySelector('.part:not(.next) .' + s.dataset.morph), chip = line.querySelector('.part.next .chip');
    const dst = chip && chip.querySelector('.tex'); if (!src || !dst) return;
    const S = line.getBoundingClientRect(), sc = S.width / line.offsetWidth;
    const rel = r => ({ x: (r.left - S.left) / sc, y: (r.top - S.top) / sc, w: r.width / sc, h: r.height / sc });
    const a = rel(src.getBoundingClientRect()), b = rel(dst.getBoundingClientRect()), c = rel(chip.getBoundingClientRect());
    const box = { x: a.x - 9, y: a.y - 6, w: a.w + 18, h: a.h + 12 };   // the tint of the lit term reaches a little beyond its text
    const bg = document.createElement('div'), px = r => `left:${r.x}px; top:${r.y}px; width:${r.w}px; height:${r.h}px`;
    bg.className = 'morph-ghost';
    bg.style.cssText = `position:absolute; ${px(box)}; z-index:39; pointer-events:none; border-radius:10px; background:${getComputedStyle(chip).backgroundColor}`;
    const g = chip.cloneNode(true); g.classList.add('morph-ghost');
    g.style.cssText = `position:absolute; ${px(c)}; margin:0; z-index:40; pointer-events:none; box-sizing:border-box; background:none`;
    line.append(bg, g);
    src.style.visibility = 'hidden'; s.classList.add('morphing');
    const D = 950, ease = 'cubic-bezier(.45, 0, .25, 1)';
    bg.animate([{ left: box.x + 'px', top: box.y + 'px', width: box.w + 'px', height: box.h + 'px' }, { left: c.x + 'px', top: c.y + 'px', width: c.w + 'px', height: c.h + 'px' }], { duration: D, easing: ease, fill: 'both' });
    // the content is seen only through the same window as the tint: the label and the unit show as the box reaches them
    const win = (t, r, bt, l) => `inset(${t}px ${r}px ${bt}px ${l}px)`;
    g.animate([{ clipPath: win(box.y - c.y, c.x + c.w - box.x - box.w, c.y + c.h - box.y - box.h, box.x - c.x) }, { clipPath: win(0, 0, 0, 0) }], { duration: D, easing: ease, fill: 'both' });
    const tex = g.querySelector('.tex'); tex.style.transformOrigin = '0 0';
    tex.animate([{ transform: `translate(${a.x - b.x}px, ${a.y - b.y}px) scale(${a.w / b.w})` }, { transform: 'none' }], { duration: D, easing: ease, fill: 'both' });
    const lab = g.firstElementChild, un = g.querySelector('.u');
    if (lab && lab !== tex) lab.animate([{ opacity: 0, transform: 'translateX(-26px)' }, { opacity: 1, transform: 'none' }], { duration: 520, delay: 200, easing: ease, fill: 'both' });
    if (un) un.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 400, delay: 540, easing: ease, fill: 'both' });
    setTimeout(() => {
      s.classList.add('morph-in', 'morph-rest'); g.remove(); bg.remove(); src.style.visibility = '';
      setTimeout(() => s.classList.remove('morphing', 'morph-in', 'morph-rest'), 480);
    }, D);
  }
  morphBack(prev, s) {
    // morphTerm in reverse: the chip of the slide before (its CO₂ line) shrinks into its term in the sum line this slide
    // starts with (data-morph-back = the term's class). The same window as there, now closing from the whole chip to the
    // term's box; the term travels to its place, label and unit fade out; then the sum line comes in around it.
    const line = s.querySelector('.fline.head'), pl = prev.querySelector('.fline.head');
    const chip = pl && pl.querySelector('.part:not(.next) .chip'), dst = line && line.querySelector('.part.cont .' + s.dataset.morphBack);
    if (!chip || !dst) return;
    const S = line.getBoundingClientRect(), sc = S.width / line.offsetWidth, P = pl.getBoundingClientRect();
    const rel = (r, O) => ({ x: (r.left - O.left) / sc, y: (r.top - O.top) / sc, w: r.width / sc, h: r.height / sc });
    const c = rel(chip.getBoundingClientRect(), P), a = rel(dst.getBoundingClientRect(), S);
    const k = dst.querySelector('.katex'), b = rel((k || dst).getBoundingClientRect(), S), t0 = chip.querySelector('.tex').getBoundingClientRect();
    if (!c.w || !a.w) return;
    const box = { x: a.x - 9, y: a.y - 6, w: a.w + 18, h: a.h + 12 };
    const bg = document.createElement('div'), px = r => `left:${r.x}px; top:${r.y}px; width:${r.w}px; height:${r.h}px`;
    bg.className = 'morph-ghost';
    bg.style.cssText = `position:absolute; ${px(c)}; z-index:39; pointer-events:none; border-radius:10px; background:${getComputedStyle(chip).backgroundColor}`;
    const g = chip.cloneNode(true); g.classList.add('morph-ghost');
    g.style.cssText = `position:absolute; ${px(c)}; margin:0; z-index:40; pointer-events:none; box-sizing:border-box; background:none`;
    line.append(bg, g);
    s.classList.add('morph-back');
    const D = 950, ease = 'cubic-bezier(.45, 0, .25, 1)';
    bg.animate([{ left: c.x + 'px', top: c.y + 'px', width: c.w + 'px', height: c.h + 'px' }, { left: box.x + 'px', top: box.y + 'px', width: box.w + 'px', height: box.h + 'px' }], { duration: D, easing: ease, fill: 'both' });
    const win = (t, r, bt, l) => `inset(${t}px ${r}px ${bt}px ${l}px)`;
    g.animate([{ clipPath: win(0, 0, 0, 0) }, { clipPath: win(box.y - c.y, c.x + c.w - box.x - box.w, c.y + c.h - box.y - box.h, box.x - c.x) }], { duration: D, easing: ease, fill: 'both' });
    const tex = g.querySelector('.tex'), tw = t0.width / sc, tx = t0.left - P.left, ty = t0.top - P.top;
    tex.style.transformOrigin = '0 0';
    tex.animate([{ transform: 'none' }, { transform: `translate(${b.x - tx / sc}px, ${b.y - ty / sc}px) scale(${b.w / tw})` }], { duration: D, easing: ease, fill: 'both' });
    const lab = g.firstElementChild, un = g.querySelector('.u');
    if (lab && lab !== tex) lab.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateX(-26px)' }], { duration: 520, delay: 150, easing: ease, fill: 'both' });
    if (un) un.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 400, delay: 0, easing: ease, fill: 'both' });
    setTimeout(() => {
      s.classList.add('morph-back-in');
      const f = [bg, g].map(x => x.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 400, easing: 'ease', fill: 'both' }));
      setTimeout(() => { g.remove(); bg.remove(); s.classList.remove('morph-back', 'morph-back-in'); }, 420);
    }, D);
  }
  gather(prev, s) {
    // the map of the slide before is summed up: its cells fly together into one point, the cooling of all of them in
    // 2100 at the end of the curve; then the curve is drawn through the years up to that point (data-gather)
    const src = prev.querySelector('.chart[data-chart]')?._chart, dst = s.querySelector('.chart[data-ec]')?._chart;
    if (!src || !src.hexItems || !src.chart || !dst || !dst.chart) return;
    const S = s.getBoundingClientRect(), sc = S.width / s.offsetWidth, rel = (el, [x, y]) => {
      const r = el.getBoundingClientRect(); return [(r.left - S.left) / sc + x, (r.top - S.top) / sc + y]; };
    const al = (dst.chart.getOption().series || []).find(x => x.id === 'al');
    if (!al) return;
    const end = al.data[al.data.length - 1], T = rel(dst.host, dst.chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, end));
    const lab = String(al.endLabel?.formatter || ''), labelA = (lab.match(/\{a\|([^}]*)\}/) || [])[1] || '', labelB = (lab.match(/\{b\|([^}]*)\}/) || [])[1] || '';
    let shown = false;
    const cells = [];
    const land = [];   // the grey land stays where it is and fades, only the cells with a value fly
    for (const g of Object.values(src.hexItems)) {
      if (g.kind !== 'num' && g.kind !== 'mask') continue;
      for (const it of g.items) { const p = src.chart.convertToPixel({ xAxisIndex: g.i, yAxisIndex: g.i }, it.value); if (p) (g.kind === 'num' ? cells : land).push({ p: rel(src.inner, p), c: it.col, R: g.R }); }
    }
    if (!cells.length) return;
    const dmax = Math.max(...cells.map(c => Math.hypot(c.p[0] - T[0], c.p[1] - T[1])));
    const cv = document.createElement('canvas'), dpr = Math.min(2, devicePixelRatio || 1), W = s.offsetWidth, H = s.offsetHeight;
    cv.className = 'gather'; cv.width = W * dpr; cv.height = H * dpr; s.append(cv);
    const cx = cv.getContext('2d'); cx.scale(dpr, dpr);
    dst.host.style.transition = 'none'; dst.host.style.opacity = 0;
    const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2, FLY = 1500, HOLD = 450, LABEL = 1820, t0 = performance.now();
    const hex = (x, y, r) => { cx.beginPath(); for (let k = 0; k < 6; k++) { const a = Math.PI / 180 * (60 * k - 90); cx.lineTo(x + r * Math.cos(a), y + r * Math.sin(a)); } cx.closePath(); cx.fill(); };
    let started = false;
    const frame = now => {
      const e = now - t0;
      cx.clearRect(0, 0, W, H);
      if (e < 500) { cx.globalAlpha = 1 - e / 500; for (const c of land) { cx.fillStyle = c.c; hex(c.p[0], c.p[1], c.R); } }
      if (e < FLY) {
        for (const c of cells) {
          const d = Math.hypot(c.p[0] - T[0], c.p[1] - T[1]) / dmax, u = ease(Math.max(0, Math.min(1, (e - 150 - d * 500) / (FLY - 650))));   // the far cells start last: the map pours into the point
          cx.globalAlpha = 1 - .55 * u; cx.fillStyle = u > .6 ? EC.alle : c.c;
          hex(c.p[0] + (T[0] - c.p[0]) * u, c.p[1] + (T[1] - c.p[1]) * u, c.R * (1 - .8 * u));
        }
      }
      // the sum: one point, then the curve comes through the years to it
      const a = e < FLY ? Math.max(0, (e - FLY * .7) / (FLY * .3)) : e < FLY + HOLD + 1600 ? 1 : Math.max(0, 1 - (e - FLY - HOLD - 1600) / 400);
      cx.globalAlpha = a; cx.fillStyle = EC.alle; cx.beginPath(); cx.arc(T[0], T[1], 7, 0, 2 * Math.PI); cx.fill();
      // the curve's final label stands at the point from the start; the chart's own label, which rides the tip of the
      // curve, stays hidden until the curve has arrived there and takes over in place
      if (e < FLY + HOLD + LABEL) {
        cx.globalAlpha = e < FLY ? a : 1; cx.textAlign = 'left'; cx.textBaseline = 'middle';
        cx.font = `600 21px ${EC.font}`; cx.fillStyle = EC.alle; cx.fillText(labelA, T[0] + 16, T[1] + 2);
        cx.font = `400 19px ${EC.font}`; cx.fillStyle = EC.muted; cx.fillText(labelB, T[0] + 16, T[1] + 26.5);
      }
      if (!started && e >= FLY + HOLD) {
        started = true; dst.host.style.transition = 'opacity .35s'; dst.host.style.opacity = 1; dst.set(0, true, true);
        dst.chart.setOption({ series: [{ id: 'al', endLabel: { show: false } }] });
      }
      if (started && !shown && e >= FLY + HOLD + LABEL) { shown = true; dst.chart.setOption({ series: [{ id: 'al', endLabel: { show: true } }] }); }
      if (e < FLY + HOLD + 2000) this._gather.raf = requestAnimationFrame(frame); else this.endGather();
    };
    this._gather = { cv, host: dst.host, raf: requestAnimationFrame(frame), chart: dst, started: () => started };
  }
  endGather() {
    const g = this._gather; if (!g) return;
    this._gather = null; cancelAnimationFrame(g.raf); g.cv.remove();
    if (!g.started()) { g.host.style.transition = ''; g.host.style.opacity = ''; g.chart.final(g.chart.k ?? 0); }
    else { g.host.style.transition = ''; g.host.style.opacity = ''; g.chart.chart.setOption({ series: [{ id: 'al', endLabel: { show: true } }] }); }
  }
  swapPart(prev, s) {
    // the corner indicator, from one slide to the next in the same chapter: when the part changes, right away the sign
    // turns like a coin to the new part's, the old arc goes pale and the new one lights up, the name changes and the
    // pill takes its new width. The old slide's pill, still under the new one while that fades in, plays the same, so
    // the two stay one picture
    const a = prev.querySelector('.sh > .path'), b = s.querySelector('.sh > .path');
    for (const p of [a, b]) if (p && p._swap) { p._swap.forEach(x => x.cancel()); p.querySelectorAll('.swap-tmp').forEach(x => x.remove()); p._swap = null; }
    if (!a || !b || a.dataset.at === b.dataset.at || a.dataset.at.split(':')[0] !== b.dataset.at.split(':')[0]) return;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const A = a.querySelector('.pc.on'), B = b.querySelector('.pc.on');
    const oldHref = A.querySelector('.ring > use').getAttribute('href'), newHref = B.querySelector('.ring > use').getAttribute('href');
    const oldName = A.querySelector('.where b').textContent, newName = B.querySelector('.where b').textContent;
    const arcFrom = [...A.querySelectorAll('.arc')].map(c => getComputedStyle(c).stroke), arcTo = [...B.querySelectorAll('.arc')].map(c => getComputedStyle(c).stroke);
    const w0 = A.offsetWidth, w1 = B.offsetWidth, HALF = 240, ease = 'cubic-bezier(.45, 0, .2, 1)';
    for (const [p, P] of [[a, A], [b, B]]) {
      const all = [], anim = (e, kf, o) => all.push(e.animate(kf, { fill: 'both', ...o }));
      // both signs and both names in this pill, the real ones hidden underneath until it is over
      const use = P.querySelector('.ring > use'), mk = h => { const u = use.cloneNode(); u.setAttribute('href', h); u.classList.add('swap-tmp'); use.before(u); return u; };
      const uOld = mk(oldHref), uNew = mk(newHref);
      anim(use, [{ opacity: 0 }, { opacity: 0 }], { duration: HALF * 2 + 60 });
      anim(uOld, [{ transform: 'scaleX(1)' }, { transform: 'scaleX(0)' }], { duration: HALF, easing: 'cubic-bezier(.5, 0, 1, 1)' });
      anim(uNew, [{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }], { duration: HALF + 60, delay: HALF, easing: 'cubic-bezier(0, 0, .3, 1)' });
      P.querySelectorAll('.arc').forEach((c, k) => anim(c, [{ stroke: arcFrom[k] }, { stroke: arcTo[k] }], { duration: 600, easing: 'ease' }));
      const nb = P.querySelector('.where b'), mb = t => { const x = nb.cloneNode(); x.textContent = t; x.classList.add('swap-tmp'); nb.before(x); return x; };
      const bOld = mb(oldName), bNew = mb(newName);
      anim(nb, [{ opacity: 0 }, { opacity: 0 }], { duration: 700 });
      anim(bOld, [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(-10px)' }], { duration: 260, easing: 'ease-in' });
      anim(bNew, [{ opacity: 0, transform: 'translateY(10px)' }, { opacity: 1, transform: 'none' }], { duration: 420, delay: 200, easing: 'ease-out' });
      if (Math.abs(w0 - w1) > 1) anim(P, [{ width: `${w0}px` }, { width: `${w1}px` }], { duration: 520, easing: ease });
      p._swap = all;
      setTimeout(() => { if (p._swap === all) { all.forEach(x => x.cancel()); p.querySelectorAll('.swap-tmp').forEach(x => x.remove()); p._swap = null; } }, 760);
    }
  }
  onward() {
    // the next slide; from the overview or a chapter's closing card its discs fly into the chapter marks of that
    // slide first (top right), the big overview becoming the small one
    if (this.flying) return;
    clearTimeout(this._planT);   // a plan still pending from the last step must not run in the middle of the flight
    const disc = this.chapterDisc();   // into a chapter opener: its disc glides to its place there and grows
    if (disc) return this.enterChapter(disc, this.slides[this.i + 1]);
    const plan = this.plan && this.plan.i === this.i ? this.plan : this.planFlight();
    if (plan) this.flyHome(plan); else this.go(this.i + 1, 0);
  }
  schedulePlan() {
    // the flight prepared while the speaker talks: the next slide built (charts, formulas, media), every start and end
    // measured; the click then only starts animations, nothing to compute or lay out
    clearTimeout(this._planT); this.plan = null;
    if (this.primed && !this.flying) { this.primed.classList.remove('primed'); this.primed = null; }
    if (this.still || this.flying) return;
    this._planT = setTimeout(() => { this.plan = this.planFlight(); }, 1100);   // after the disc row's own entrance
  }
  planFlight() {
    const i = this.i, prev = this.slides[i], s = this.slides[i + 1];
    if (this.flying || !s || this.still || matchMedia('(prefers-reduced-motion: reduce)').matches) return null;
    const path = s.matches('.chapter') ? null : s.querySelector('.path');   // a chapter opener is entered otherwise (Deck.enterChapter)
    const discs = path ? [...prev.querySelectorAll('[data-fly]')].filter(e => !e.closest('[data-step]:not(.shown)')) : [];
    if (!discs.length) return null;
    if (window.__deckDataNow) window.__deckDataNow();
    if (window.__ensureCharts) { window.__ensureCharts(s); delete s._steps; }
    if (window.__ensureTex) window.__ensureTex(s);
    deckMedia.around(this.slides, i + 1);
    // the marks where the copies land
    s.classList.add('measure');
    const legs = discs.map(e => {
      const m = path.querySelector(`.pc[data-ch="${e.dataset.fly}"] .ring > use`);   // the disc inside its ring
      return m && { disc: e, c: e.dataset.fly, from: this.discBox(e), to: this.discBox(m), o: +getComputedStyle(m.closest('.pc')).opacity };
    }).filter(Boolean);
    // where the current chapter's disc first lands: as it stands with its pill still folded to the disc (the indicator
    // right-aligned, so the disc and what is left of it sit further right by the pill's width); the unfolding pill
    // then pushes them into place (Deck.flyHome)
    const k = this.deck.offsetWidth / this.deck.getBoundingClientRect().width, on = path.querySelector('.pc.on');
    const shift = on ? (on.getBoundingClientRect().width - on.querySelector('.ring').getBoundingClientRect().width) * k : 0;
    s.classList.remove('measure');
    // and painted already, unseen under this one: at the hand-over it only has to become visible
    s.classList.add('primed'); this.primed = s;
    return { i, legs, shift };
  }
  discBox(e) {
    // where a chapter disc is drawn, in deck coordinates: the circle, not the bounding box of its drawing (whose trees
    // and ground reach past the clip); in a ring (viewBox -14 -14 128 128) the inner 100 of 128
    const D = this.deck.getBoundingClientRect(), k = this.deck.offsetWidth / D.width;
    const svg = e.closest('svg'), r = (e.tagName === 'use' ? svg : e).getBoundingClientRect();
    const f = svg && svg.classList.contains('ring') ? 100 / 128 : 1, w = r.width * f, pad = (r.width - w) / 2;
    return [(r.left + pad - D.left) * k, (r.top + pad - D.top) * k, w * k];
  }
  chapterDisc() {
    // on the overview or a chapter's closing card, before a chapter opener: the disc of that chapter, if it is shown
    const prev = this.slides[this.i], s = this.slides[this.i + 1];
    if (!s || this.still || !s.querySelector(':scope > .cdisc') || matchMedia('(prefers-reduced-motion: reduce)').matches) return null;
    return [...prev.querySelectorAll(`[data-fly="${s.dataset.ch}"]`)].find(e => !e.closest('[data-step]:not(.shown)')) || null;
  }
  enterChapter(e, s) {
    // one element, one move: the chapter's disc glides from where it is (overview, closing card) to its place on the
    // opener and grows there, while the slide left fades; the opener's own entrance (title, ring, parts) follows
    this.flying = true;
    const prev = this.slides[this.i];
    const [x0, y0, w0] = this.discBox(e);
    s.classList.add('measure'); const [x1, y1, w1] = this.discBox(s.querySelector('.cdisc .ring > use')); s.classList.remove('measure');
    const layer = document.createElement('div'); layer.className = 'flyer';
    layer.innerHTML = `<div class="fly" style="left:${x0}px; top:${y0}px; width:${w0}px; height:${w0}px; transform-origin: 0 0">`
      + `<svg viewBox="0 0 100 100"><use href="#${CHAPTERS[s.dataset.ch].disc}" width="100" height="100"/></svg></div>`;
    this.deck.append(layer);
    const DUR = 1000;
    layer.firstChild.animate([{ transform: 'none' }, { transform: `translate(${x1 - x0}px, ${y1 - y0}px) scale(${w1 / w0})` }],
      { duration: DUR, easing: 'cubic-bezier(.45, 0, .2, 1)', fill: 'forwards' });   // even: starts gently, settles softly
    const gone = e.closest('.ic') || e; gone.style.visibility = 'hidden';
    const fade = prev.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 340, easing: 'cubic-bezier(.3, 0, .2, 1)', fill: 'forwards' });
    setTimeout(() => {
      s.classList.add('arrive'); this.go(this.i + 1, 0);
      setTimeout(() => {   // the opener's disc painted under the copy: the copy goes
        layer.remove(); gone.style.visibility = ''; fade.cancel();
        setTimeout(() => {
          s.classList.remove('arrive'); this.flying = false;
          if (this.staged) { this.stage(this.staged); this.staged = null; }
        }, 600);
      }, 120);
    }, DUR - 120);
  }
  flyHome(plan) {
    // From a chapter opener into its first slide, one timeline, every move scheduled at once on the elements that stay
    // (nothing hands over half-way):
    //   0     the opener's disc, in its ring, glides into the corner, far right; the parts' colours go pale on the way;
    //         the opener dissolves, the slide comes up under the copy
    //   flight the other chapters fade in, so they are there when the disc lands
    //   land  the copy gives way to the indicator, which stands exactly there: its pill folded to the disc, the
    //         chapter's drawing on the disc
    //   then  together: the disc turns like a coin, the first part's sign comes round from the other side and its arc
    //         lights up; the pill unfolds with its words and pushes the disc and what is left of it into place
    const leg = plan.legs.find(l => l.disc.closest('.cdisc'));
    if (!leg) return this.go(this.i + 1, 0);
    this.flying = true;
    const prev = this.slides[this.i], s = this.slides[this.i + 1];
    const path = s.querySelector('.path'), on = path.querySelector('.pc.on'), ring = on.querySelector('.ring');
    const part = ring.querySelector(':scope > use'), where = on.querySelector('.where');
    const others = [...path.querySelectorAll('.pc:not(.on)')], arcs = [...on.querySelectorAll('.arc')];
    const { c, from: [x0, y0, w0], to: [x1, y1, w1] } = leg, dx = plan.shift;
    const ease = 'cubic-bezier(.4, 0, .25, 1)', push = 'cubic-bezier(.25, .6, .2, 1)', FLY = 900, LAND = FLY, HOLD = 150, GO = LAND + HOLD, HALF = 220, PUSH = 700;
    const all = [], anim = (e, kf, o) => { const a = e.animate(kf, { fill: 'both', ...o }); all.push(a); return a; };
    // the copy: the opener's ring, moved and scaled in one go (ring box = disc box widened by 14 / 100 each side)
    const R = 1.28, X0 = x0 - w0 * .14, Y0 = y0 - w0 * .14, X1 = x1 + dx - w1 * .14, Y1 = y1 - w1 * .14;
    const layer = document.createElement('div'); layer.className = 'flyer';
    layer.innerHTML = `<div class="fly" style="left:${X0}px; top:${Y0}px; width:${w0 * R}px; height:${w0 * R}px; transform-origin: 0 0">${ringSvg(c, ['on', 'on'])}</div>`;
    this.deck.append(layer);
    const track = getComputedStyle(document.documentElement).getPropertyValue('--track').trim();
    anim(layer.firstChild, [{ transform: 'none' }, { transform: `translate(${X1 - X0}px, ${Y1 - Y0}px) scale(${w1 / w0})` }], { duration: FLY, easing: ease });
    for (const a of layer.querySelectorAll('.arc')) anim(a, [{ stroke: getComputedStyle(a).stroke }, { stroke: track }], { duration: FLY, easing: 'ease-in-out' });
    // the indicator, set up as it will stand when the copy lands, and its moves after
    const chap = document.createElementNS(SVGNS, 'use');   // the chapter's drawing on the coin's front
    chap.setAttribute('href', `#${CHAPTERS[c].disc}`); chap.setAttribute('width', '100'); chap.setAttribute('height', '100');
    part.before(chap);
    const ringW = ring.getBoundingClientRect().width * this.deck.offsetWidth / this.deck.getBoundingClientRect().width;
    const pcs = [...path.querySelectorAll('.pc')], left = pcs.slice(0, pcs.indexOf(on) + 1);   // the pill and what is left of it move
    for (const e of left) anim(e, [{ transform: `translateX(${dx}px)` }, { transform: 'none' }], { duration: PUSH, delay: GO, easing: push });
    anim(on, [{ clipPath: `inset(0 calc(100% - ${ringW}px) 0 0 round 40px)` }, { clipPath: 'inset(0 0 0 0 round 40px)' }], { duration: PUSH, delay: GO, easing: push });
    anim(where, [{ opacity: 0 }, { opacity: 1 }], { duration: 400, delay: GO + 260, easing: 'ease' });
    // the other chapters are there when the disc lands: the slide (and its indicator) only comes up at the end, so
    // they fade in as copies on this layer, where they stand at first, and give way to the real ones with the disc
    const D = this.deck.getBoundingClientRect(), kk = this.deck.offsetWidth / D.width;
    const layer2 = document.createElement('div'); layer2.className = 'flyer'; this.deck.append(layer2);
    others.forEach((o, n) => {
      const r = o.querySelector('.ring').getBoundingClientRect();   // measured with the pill's moves already applied
      const cp = document.createElement('div'); cp.className = 'fly';
      cp.style.cssText = `left:${(r.left - D.left) * kk}px; top:${(r.top - D.top) * kk}px; width:${r.width * kk}px; height:${r.height * kk}px`;
      cp.innerHTML = ringSvg(o.dataset.ch, ['track', 'track']); layer2.append(cp);
      anim(cp, [{ opacity: 0 }, { opacity: +getComputedStyle(o).opacity }], { duration: 450, delay: 220 + n * 80, easing: 'ease-out' });
      // the real one stays out until the copy goes: the same animation, so the swap is one frame (no brighter overlap)
      o.animate([{ opacity: 0 }, { opacity: 0 }], { duration: LAND, fill: 'backwards' }).finished.then(() => { if (n === others.length - 1) layer2.remove(); }, () => layer2.remove());
    });
    anim(chap, [{ transform: 'scaleX(1)' }, { transform: 'scaleX(0)' }], { duration: HALF, delay: GO, easing: 'cubic-bezier(.5, 0, 1, 1)' });
    anim(part, [{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }], { duration: HALF + 60, delay: GO + HALF, easing: 'cubic-bezier(0, 0, .3, 1)' });
    for (const a of arcs) anim(a, [{ stroke: track }, { stroke: getComputedStyle(a).stroke }], { duration: 600, delay: GO + HALF, easing: 'ease' });
    // the slide left goes, the new one comes up under the copy; the copy goes when the indicator stands under it
    const fade = prev.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 340, easing: 'cubic-bezier(.3, 0, .2, 1)', fill: 'forwards' });
    leg.disc.closest('.ring').style.visibility = 'hidden';
    const at = (ms, fn) => setTimeout(fn, ms);
    at(LAND - 120, () => { s.classList.add('arrive'); this.go(this.i + 1, 0); s.classList.remove('primed'); this.primed = null; });
    at(LAND, () => layer.remove());
    at(GO + PUSH + 80, () => {
      all.forEach(a => a.cancel()); chap.remove();   // everything at its own resting state now
      s.classList.remove('arrive'); leg.disc.closest('.ring').style.visibility = ''; fade.cancel();
      this.flying = false;
      if (this.staged) { this.stage(this.staged); this.staged = null; }
    });
  }
  dataReady() {
    // charts exist now: recount the clicks and draw the current slide in its present state
    for (const s of this.slides) delete s._steps;
    this.ready = true;
    if (this.still) this.go(this.i, this.step); else this.applyStep(false, false, true);
    if (!this.embed) setTimeout(() => deckMedia.rest(this.slides), 300);
  }
  applyStep(animate, entering, late) {
    this.endGather();
    // late: the charts were not there when the slide came up; they play their entrance now, the rest stays put
    if (animate) this.movedAt = performance.now();   // the background chart builder waits until this has played
    // everything with data-step <= step is shown; charts run the part that belongs to this click
    const s = this.slides[this.i];
    for (const e of s.querySelectorAll('[data-step]')) e.classList.toggle('shown', (+e.dataset.step || 0) <= this.step);
    this.rest(s);
    for (const h of s.querySelectorAll('.chart')) {
      const ch = h._chart; if (!ch) continue;
      const k = this.step - (+h.dataset.step || 0);
      // a split slide's second half (data-start) opens on the picture the first half ended on: its charts stand
      const cont = entering && s.dataset.start !== undefined && this.step === +s.dataset.start;
      if ((animate || late) && !cont && !deckCalm.matches && k >= 0 && k <= ch.nSteps) {
        ch.play(k);
      } else if (entering || ch.k == null || ch.k !== Math.max(0, Math.min(k, ch.nSteps || 0))) ch.final(k);
      // else: this click does not change the chart's picture (it stands at its last part, or has not started yet):
      // no redraw, which on a world map cost 100-150 ms per click
    }
    for (const c of s.querySelectorAll('.count')) {
      const host = c.closest('[data-step]'), k = host ? +host.dataset.step : 0;
      if (k > this.step) continue;
      countUp(c, !(animate && k === this.step) || deckCalm.matches);
    }
    this.syncSw(s);
    this.sync();
  }
  syncSw(s) {
    // the Ohne / Mit words (slide 4): the word's box has the width of the one showing, so what follows it moves when
    // they swap (a width transition)
    for (const w of s.querySelectorAll('.sw')) {
      const mit = !!w.closest('.ovw')?.querySelector('.kc-r.shown'), o = w.querySelector('.sw-o'), m = w.querySelector('.sw-m');
      w.style.width = `${(mit ? m : o).offsetWidth}px`;
    }
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
  next() { if (this.flying) return; if (window.__deckDataNow) window.__deckDataNow(); if (this.step < this.steps(this.slides[this.i])) { this.step++; this.applyStep(!this.still, false); this.schedulePlan(); } else if (this.i < this.slides.length - 1) this.onward(); }
  prev() { if (this.flying) return; this.schedulePlan(); if (this.step > +(this.slides[this.i].dataset.auto || this.slides[this.i].dataset.start || 0)) { this.step--; this.applyStep(false, false); } else if (this.i > 0) this.go(this.i - 1, 'end'); }
  bind() {
    try { if (sessionStorage.getItem('dv-nocursor')) this.cursor(true); } catch (e) { /* no storage */ }
    try { if (sessionStorage.getItem('dv-notips')) document.documentElement.classList.add('notips'); } catch (e) { /* no storage */ }
    const jumper = slideJumper(() => this.slides.length, n => this.slides[n].dataset.title, n => this.go(n, 0));
    addEventListener('keydown', e => {
      if (e.target.isContentEditable || e.target.closest('input, textarea, select')) return;   // typing in a text or field
      const k = e.key;
      if ((e.metaKey || e.ctrlKey) && !e.altKey && ['+', '=', '-', '0'].includes(k)) {   // the browser's zoom keys zoom the slide
        e.preventDefault(); k === '0' ? this.zoomReset() : this.zoomAt(k === '-' ? 1 / 1.25 : 1.25); return;
      }
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (jumper(e)) { e.preventDefault(); return; }
      if (k === 'Escape' && (this.z || 1) > 1.001) { this.zoomReset(); return; }
      if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); this.next(); }
      else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); this.prev(); }
      else if (k === 'Home') this.go(0, 0);
      else if (k === 'End') this.go(this.mainEnd - 1, 0);
      else if (k === 'b' || k === 'B') this.go(this.mainEnd, 0);
      else if (k === 'r' || k === 'R') this.go(this.i, this.step);
      else if (k === 'n' || k === 'N') this.notes();
      else if (k === 'p' || k === 'P') this.openPresenter();
      else if (k === 'o' || k === 'O') this.openNotesWindow();
      else if (k === 'f' || k === 'F') this.fullscreen();
      else if (k === 'i' || k === 'I') this.hint(6000);
      else if (k === 'c' || k === 'C') this.cursor(!document.documentElement.classList.contains('nocursor'));
      else if (k === 'h' || k === 'H') this.tips(!document.documentElement.classList.contains('notips'));
      else if ((k === 'e' || k === 'E') && this.canEdit) this.edit(!this.editing);
    });
    let lock = 0;
    addEventListener('wheel', e => {
      if (this.drawer.contains(e.target) || (this.menu && this.menu.isOpen)) return;
      // a trackpad pinch and Ctrl/Cmd + wheel arrive as a wheel with ctrlKey: zoom the slide, not the page
      if (e.ctrlKey || e.metaKey) { e.preventDefault(); this.zoomAt(Math.exp(-e.deltaY * (e.deltaMode ? .05 : .01)), e.clientX, e.clientY); return; }
      if ((this.z || 1) > 1.001) { e.preventDefault(); this.pan(-e.deltaX, -e.deltaY); return; }   // zoomed in: the wheel moves the slide
      const now = Date.now(); if (now < lock || Math.abs(e.deltaY) < 12) return;
      lock = now + 650; e.deltaY > 0 ? this.next() : this.prev();
    }, { passive: false });
    // Safari's trackpad pinch (gesture events): the same zoom; only without a touch screen (on an iPhone or iPad the
    // pinch stays the browser's own)
    if (!navigator.maxTouchPoints) {
      let g0 = 1;
      addEventListener('gesturestart', e => { e.preventDefault(); g0 = 1; });
      addEventListener('gesturechange', e => { e.preventDefault(); this.zoomAt(e.scale / g0, e.clientX, e.clientY); g0 = e.scale; });
    }
    // zoomed in: drag with the mouse to move the slide
    let drag = null;
    addEventListener('pointerdown', e => {
      if (e.pointerType !== 'mouse' || e.button !== 0 || (this.z || 1) <= 1.001 || e.target.closest('a, button, input, .drawer, #menu')) return;
      drag = [e.clientX, e.clientY];
    });
    addEventListener('pointermove', e => { if (!drag) return; this.pan(e.clientX - drag[0], e.clientY - drag[1]); drag = [e.clientX, e.clientY]; });
    addEventListener('pointerup', () => { drag = null; });
    let x0 = null, y0 = null;
    const hideTips = () => {   // tooltip and pointer line, on every chart of the slide
      for (const h of this.slides[this.i].querySelectorAll('.chart')) {
        const c = h._chart && h._chart.chart; if (!c) continue;
        c.dispatchAction({ type: 'hideTip' }); c.dispatchAction({ type: 'updateAxisPointer', currTrigger: 'leave' });
      }
    };
    this.hideTips = hideTips;
    // touch: swipe, or tap the left third to go back and anywhere else to go on; what has its own touch keeps it
    // (a chart scrubs its tooltip, links, buttons, the chapter marks, the map player, the embedded Woodway)
    const own = 'a, button, input, select, textarea, iframe, label, .path, .player, #menu, #menu-fab, .drawer, #rotate, [contenteditable="true"]';
    // Zoom on a touch screen is the browser's own pinch zoom (smooth, and always reversible); the deck keeps out of it:
    // two fingers are never a swipe or a tap, and while zoomed in one finger moves the view, so nothing navigates
    let t0 = 0, multi = false;
    addEventListener('touchstart', e => {
      if (this.menu && this.menu.isOpen) { x0 = null; return; }
      if (e.touches.length > 1) { multi = true; x0 = null; document.documentElement.classList.add('pinching'); hideTips(); return; }
      if (pinchZoomed() || (e.target.closest && e.target.closest(own))) { x0 = null; return; }   // zoomed in, or a control
      const host = e.target.closest && e.target.closest('.chart');
      if (host && !document.documentElement.classList.contains('notips')) {   // inside a chart: scrub its tooltip, no swipe; the other charts close theirs
        for (const h of this.slides[this.i].querySelectorAll('.chart')) if (h !== host && h._chart && h._chart.chart) h._chart.chart.dispatchAction({ type: 'hideTip' });
        x0 = null; return;
      }
      hideTips(); x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; t0 = Date.now();
    }, { passive: true });
    // a pinch is the browser's: the charts under the fingers do not see it (no tooltip scrubbing while zooming)
    addEventListener('touchmove', e => { if (e.touches.length > 1) e.stopPropagation(); }, { passive: true, capture: true });
    addEventListener('touchend', e => {
      if (multi) {
        if (!e.touches.length) { multi = false; setTimeout(() => { document.documentElement.classList.remove('pinching'); hideTips(); this.zoomState(); }, 150); }
        x0 = null; return;
      }
      if (x0 === null || e.touches.length || pinchZoomed()) { x0 = null; return; }
      const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
      if (Math.max(Math.abs(dx), Math.abs(dy)) > 50) (Math.abs(dx) > Math.abs(dy) ? dx : dy) < 0 ? this.next() : this.prev();
      else if (Math.hypot(dx, dy) < 12 && Date.now() - t0 < 450) (x0 < innerWidth / 3) ? this.prev() : this.next();
      x0 = null;
    }, { passive: true });
    addEventListener('touchcancel', () => { x0 = null; multi = false; document.documentElement.classList.remove('pinching'); }, { passive: true });
    addEventListener('hashchange', () => { const h = parseInt(location.hash.slice(1), 10); if (h - 1 !== this.i) this.go(h - 1, 0); });
  }
}

// the browser's own pinch zoom (phones, tablets) is in: the visible part is smaller than the page
function pinchZoomed() { return !!window.visualViewport && visualViewport.scale > 1.01; }

addEventListener('DOMContentLoaded', () => {
  if (location.search.includes('presenter')) return new Presenter();
  if (location.search.includes('embed') || window.__EMBED) document.documentElement.classList.add('embed');
  const deckEl = document.getElementById('deck');
  const tpl = document.getElementById('tpl-trees');
  deckEl.querySelectorAll('svg.trees-do').forEach((svg, k) => {
    for (const n of tpl.content.firstElementChild.childNodes) svg.appendChild(n.cloneNode(true));
    // ids per copy: arrowheads and symbols must resolve inside their own (visible) drawing
    // (only the drawing's own ids: the deck-wide cloud and ray tips stay as they are)
    const own = new Set([...svg.querySelectorAll('[id]')].map(e => e.id));
    for (const e of svg.querySelectorAll('[id]')) e.id += '-' + k;
    for (const e of svg.querySelectorAll('[marker-end], use')) {
      const me = e.getAttribute('marker-end'), m = me && me.match(/^url\(#(.+)\)$/);
      if (m && own.has(m[1])) e.setAttribute('marker-end', `url(#${m[1]}-${k})`);
      const h = e.getAttribute('href');
      if (h && own.has(h.slice(1))) e.setAttribute('href', h + '-' + k);
    }
    // slide 8 builds effect by effect; slide 9 shows them all at once
    if (svg.closest('[data-tree="dim"]')) for (const e of svg.querySelectorAll('[data-step]')) e.removeAttribute('data-step');
    // slide 13 opens on slide 8's last picture: everything there at once, the global effects numbered
    if (svg.closest('[data-tree="recap"]')) { for (const e of svg.querySelectorAll('[data-step]')) e.removeAttribute('data-step'); svg.classList.add('recap'); }
  });
  for (const l of deckEl.querySelectorAll('path.ray-l')) waveRay(l);
  for (const svg of deckEl.querySelectorAll('svg.albedo')) drawAlbedo(svg);
  supText(deckEl);
  for (const s of deckEl.querySelectorAll('.slide.holzweg')) holzwegFly(s);
  for (const svg of deckEl.querySelectorAll('svg.ende-scene')) endeStage(svg);
for (const sl of deckEl.querySelectorAll('.slide[data-start]')) for (const e of sl.querySelectorAll('[data-step]')) if ((+e.dataset.step || 0) <= +sl.dataset.start) e.classList.add('pre');   // played before the slide opens: no entrance
  window.deck = new Deck();
  // formulas, typeset one slide per task (the current one first): they carry click steps, so the slide counts again
  const texed = new WeakSet(), texOne = s => {
    if (!window.katex || texed.has(s)) return false; texed.add(s);
    if (!s.textContent.includes('$')) return false;
    renderTex(s); delete s._steps;
    // a split slide's second half: the formula parts its first clicks already show stand without an entrance (as .pre above)
    if (s.dataset.start !== undefined) for (const e of s.querySelectorAll('.katex [data-step]')) if ((+e.dataset.step || 0) <= +s.dataset.start) e.classList.add('pre');
    return true;
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
/* NOTES, ONE PARAGRAPH PER CLICK. A paragraph of a slide's notes carries data-click="3" (or "1-2": it stays for two clicks);
   class q = background, for questions, no click. A paragraph without data-click follows the old way of writing: the first
   is the slide as it opens, every one starting with "Klick" is the next click, the others stay with the one before. */
function noteItems(els, start, total) {
  const out = []; let cur = start;
  for (const el of els) {
    const q = el.classList.contains('q'); let steps = [];
    if (!q) {
      const a = (el.getAttribute('data-click') || '').trim();
      if (a) for (const part of a.split(',')) { const m = /^(\d+)(?:-(\d+))?$/.exec(part.trim()); if (m) for (let k = +m[1]; k <= +(m[2] || m[1]); k++) steps.push(k); }
      else { if (/^\s*Klick/.test(el.textContent)) cur++; steps = [Math.min(cur, Math.max(total, start))]; }
      if (steps.length) cur = steps[steps.length - 1];
    }
    out.push({ el, steps, q, lo: steps[0], hi: steps[steps.length - 1] });
  }
  return out;
}
function noteLabel(x) { return x.lo === x.hi ? (x.lo === 0 ? 'Start' : 'Klick ' + x.lo) : 'Klick ' + x.lo + '–' + x.hi; }
/* which paragraphs are said now (the ones for this click; if this click has none, the last that had), which were before, which come next */
function noteFocus(items, step) {
  const main = items.filter(x => !x.q && x.steps.length), res = new Map();
  let cur = main.filter(x => x.lo <= step && step <= x.hi);
  if (!cur.length) { const before = main.filter(x => x.hi < step); if (before.length) { const m = Math.max(...before.map(x => x.hi)); cur = before.filter(x => x.hi === m); } }
  const lo = cur.length ? Math.min(...cur.map(x => x.lo)) : step + 1, hi = cur.length ? Math.max(...cur.map(x => x.hi)) : step;
  const prevs = main.filter(x => x.hi < lo), nexts = main.filter(x => x.lo > hi);
  const pm = prevs.length ? Math.max(...prevs.map(x => x.hi)) : null, nm = nexts.length ? Math.min(...nexts.map(x => x.lo)) : null;
  for (const x of main) res.set(x, cur.includes(x) ? 'cur' : (pm !== null && x.hi === pm && prevs.includes(x)) ? 'prev' : (nm !== null && x.lo === nm && nexts.includes(x)) ? 'next' : 'far');
  return res;
}
class Presenter {
  constructor() {
    const slides = [...document.querySelectorAll('#deck .slide')];
    this.notes = slides.map(s => (s.querySelector('.notes') || {}).innerHTML || '');
    this.titles = slides.map(s => s.dataset.title || '');
    const base = location.href.split(/[?#]/)[0] + '?embed';
    this.only = /[?&]notes\b/.test(location.search);
    document.title = (this.only ? 'Notizen · ' : 'Referentenansicht · ') + document.title;
    document.documentElement.classList.add('presenter'); if (this.only) document.documentElement.classList.add('pv-only');
    document.body.innerHTML = `
      <div class="pv">
        <header class="pv-bar">
          <span id="pv-count">–</span>
          <span id="pv-title"></span>
          <span class="pv-spacer"></span>
          <button id="pv-replay" title="Animation der aktuellen Folie neu abspielen (R)">↻</button>
          <button id="pv-edit" hidden title="Notizen bearbeiten (E); gespeichert wird in die Folienquelle">Bearbeiten</button><i id="pv-msg"></i>
          <button id="pv-tele" title="Teleprompter: nur der aktuelle Klick groß, davor und danach blass. Aus: alle Notizen (T)">Teleprompter</button>
          <button id="pv-small" title="Notizen kleiner">A−</button>
          <button id="pv-big" title="Notizen größer">A+</button>
                                                </header>
        <section class="pv-prev">
          <div class="pv-box"><h5>Aktuelle Folie <button id="pv-live" title="Den Projektor-Bildschirm live zeigen, mit allem, was dort zu sehen ist (Laserpointer, Markierungen des Presenters)">Live-Bild</button></h5><div class="pv-fr pv-cur"><video id="pv-video" muted playsinline hidden></video><iframe id="pv-cur" src="${base}#1" title="Aktuelle Folie" tabindex="-1"></iframe></div></div>
          <div class="pv-box"><h5>Als Nächstes</h5><div class="pv-fr pv-next"><iframe id="pv-next" src="${base}#2" title="Nächste Folie" tabindex="-1"></iframe><div id="pv-end">Ende des Vortrags</div></div></div>
          <div class="pv-time"><span id="pv-timer" title="Klick: pausieren / fortsetzen">00:00</span><span id="pv-clock"></span><div class="pv-tbtn"><button id="pv-reset">Zurücksetzen</button><button id="pv-tsmall" title="Uhr kleiner">−</button><button id="pv-tbig" title="Uhr größer">+</button></div><label id="pv-marks" title="Zeitmarken, durch Komma getrennt, als Minuten oder mm:ss; die letzte färbt den Timer rot, die anderen gelb">Zeitmarken <input id="pv-marks-in" spellcheck="false"></label></div>
        </section>
        <div id="pv-split" title="Ziehen: Vorschau größer oder kleiner" role="separator" aria-orientation="horizontal"></div>
        <section class="pv-notesbox">
          <h5>Notizen</h5>
          <div id="pv-notes"></div>
          <div id="pv-edwrap" hidden><div class="ned-gut"></div><div id="pv-ned" contenteditable="true" spellcheck="false"></div></div>
          <div class="pv-nw l" title="Ziehen: Notizen breiter oder schmaler · Doppelklick: zurück"></div><div class="pv-nw r" title="Ziehen: Notizen breiter oder schmaler · Doppelklick: zurück"></div>
        </section>
        <div id="pv-title-note" hidden><b>Timer zurücksetzen!</b><span>kurz vor dem ersten Wort</span><button id="pv-reset2">Jetzt zurücksetzen</button></div>
        <div id="pv-alert" hidden></div>
        <p id="pv-lost" hidden>Keine Verbindung zur Präsentation. Öffne die Referentenansicht mit <kbd>P</kbd> aus dem Präsentationsfenster.</p>
      </div>`;
    this.cur = document.getElementById('pv-cur');
    this.nxt = document.getElementById('pv-next');
    this.state = null;
    try { this.tele = localStorage.getItem('pv-tele') !== '0'; } catch (e) { this.tele = true; }
    this.fontPx = 24; this.applyFont(); this.applyTele();
    try { this.prevH = +localStorage.getItem('pv-prev-h') || 0; } catch (e) { this.prevH = 0; }
    this.applyPrev();
    try { this.noteW = +localStorage.getItem('pv-note-w') || 0; } catch (e) { this.noteW = 0; }
    this.applyNoteW();
    this.t0 = Date.now(); this.paused = null;
    this.bind();
    [this.cur, this.nxt].forEach(f => f.addEventListener('load', () => { f._k = null; this.render(); }));
    setInterval(() => this.tick(), 500); this.tick();
    this.send('hello');
    setTimeout(() => { if (!this.state) document.getElementById('pv-lost').hidden = false; }, 1500);
  }
  send(cmd, n, html) { if (window.opener && !window.opener.closed) window.opener.postMessage({ src: 'dv', cmd, n, html }, '*'); }
  bind() {
    addEventListener('message', e => {
      const d = e.data; if (d && d.src === 'dv' && 'saved' in d) { this.msg(d.saved ? 'gespeichert' : 'nicht gespeichert: ' + d.error, !d.saved); return; }
      if (!d || d.src !== 'dv' || !d.state) return;
      this.state = d.state; document.getElementById('pv-lost').hidden = true; this.titleNote();
      if (this.only && this.canEdit && !this.editing) { this.editNotes(true); }
      this.render(); if (this.editing && this.state.i === this.edI) this.gutter();
    });
    const jumper = slideJumper(() => this.titles.length, n => this.titles[n], n => this.send('goto', n));
    addEventListener('keydown', e => {
      if (e.target.isContentEditable) { if (e.key === 'Escape') { e.preventDefault(); e.target.blur(); } return; }   // typing in the notes
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const k = e.key;
      if ((k === 'e' || k === 'E') && this.canEdit) { e.preventDefault(); this.editNotes(!this.editing); return; }
      if (jumper(e)) { e.preventDefault(); return; }
      if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); this.send('next'); }
      else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); this.send('prev'); }
      else if (k === 'Home') this.send('first'); else if (k === 'End') this.send('last');
      else if (k === 'r' || k === 'R') this.send('replay');
      else if (k === 't' || k === 'T') this.toggleTele();
    });
    document.getElementById('pv-replay').onclick = () => this.send('replay');
    const reset = () => { this.t0 = Date.now(); this.paused = null; this.hit = new Set(); this.resetAt = Date.now(); document.getElementById('pv-alert').hidden = true; this.tick(); this.titleNote(); setTimeout(() => this.titleNote(), 1300); };
    document.getElementById('pv-reset').onclick = reset; document.getElementById('pv-reset2').onclick = reset;
    document.getElementById('pv-timer').onclick = () => {
      if (this.paused === null) this.paused = Date.now(); else { this.t0 += Date.now() - this.paused; this.paused = null; }
      this.tick();
    };
    const split = document.getElementById('pv-split');
    split.addEventListener('pointerdown', e => {
      e.preventDefault(); split.setPointerCapture(e.pointerId);
      const prev = document.querySelector('.pv-prev').getBoundingClientRect().top;
      const move = ev => { this.prevH = ev.clientY - prev - 6; this.applyPrev(); };
      const up = () => { split.removeEventListener('pointermove', move); split.removeEventListener('pointerup', up); try { localStorage.setItem('pv-prev-h', String(this.prevH)); } catch (er) {} };
      split.addEventListener('pointermove', move); split.addEventListener('pointerup', up);
    });
    split.addEventListener('dblclick', () => { this.prevH = 0; this.applyPrev(); try { localStorage.removeItem('pv-prev-h'); } catch (er) {} });
    addEventListener('resize', () => { this.applyPrev(); this.applyNoteW(); });
    for (const hnd of document.querySelectorAll('.pv-nw')) {
      hnd.addEventListener('pointerdown', e => {
        e.preventDefault(); hnd.setPointerCapture(e.pointerId);
        const box = document.querySelector('.pv-notesbox').getBoundingClientRect(), mid = box.left + box.width / 2;
        const move = ev => { this.noteW = 2 * Math.abs(ev.clientX - mid) - 30; this.applyNoteW(); };
        const up = () => { hnd.removeEventListener('pointermove', move); hnd.removeEventListener('pointerup', up); try { localStorage.setItem('pv-note-w', String(this.noteW)); } catch (er) {} };
        hnd.addEventListener('pointermove', move); hnd.addEventListener('pointerup', up);
      });
      hnd.addEventListener('dblclick', () => { this.noteW = 0; this.applyNoteW(); try { localStorage.removeItem('pv-note-w'); } catch (er) {} });
    }
    document.getElementById('pv-tele').onclick = () => this.toggleTele();
    // the timer's size, separately from the notes (kept in this browser)
    try { this.tScale = +localStorage.getItem('pv-tscale') || 1; } catch (e) { this.tScale = 1; }
    const tSize = d => { this.tScale = Math.min(1.8, Math.max(.4, Math.round((this.tScale + d) * 10) / 10)); document.documentElement.style.setProperty('--pv-tscale', this.tScale); try { localStorage.setItem('pv-tscale', String(this.tScale)); } catch (e) { /* only for this page */ } };
    tSize(0);
    document.getElementById('pv-tsmall').onclick = () => tSize(-.1);
    document.getElementById('pv-tbig').onclick = () => tSize(.1);
    document.getElementById('pv-live').onclick = () => this.live(!this.stream);
    document.getElementById('pv-edit').onclick = () => this.editNotes(!this.editing);
    const mi = document.getElementById('pv-marks-in');
    try { mi.value = localStorage.getItem('pv-marks') || '30, 40'; } catch (e) { mi.value = '30, 40'; }
    mi.addEventListener('keydown', e => { e.stopPropagation(); if (e.key === 'Enter' || e.key === 'Escape') mi.blur(); });
    mi.addEventListener('change', () => { try { localStorage.setItem('pv-marks', mi.value); } catch (e) { /* only for this page */ } this.hit = new Set(this.marks().filter(m => (this.paused ?? Date.now()) - this.t0 >= m.s * 1000).map(m => m.s)); this.tick(); });
    document.getElementById('pv-ned').addEventListener('input', () => { this.typedAt = performance.now(); this.msg('ungespeichert …'); clearTimeout(this._edT); this._edT = setTimeout(() => this.flushNotes(), 700); requestAnimationFrame(() => this.gutter()); });
    const gut = document.querySelector('#pv-edwrap .ned-gut');
    gut.addEventListener('mousedown', e => e.preventDefault());
    gut.addEventListener('click', e => { const c = e.target.closest('.nck'); if (c) this.clickMenu(c); });
    // Cmd+Z: a click assignment made after the last typing is undone here; text is the browser's own undo
    this.hist = []; this.redo = []; this.typedAt = 0;
    addEventListener('keydown', e => {
      if (!this.editing || !(e.metaKey || e.ctrlKey) || e.key.toLowerCase() !== 'z') return;
      const back = !e.shiftKey, from = back ? this.hist : this.redo, to = back ? this.redo : this.hist, op = from[from.length - 1];
      if (!op || (back && op.t < this.typedAt)) return;
      e.preventDefault(); from.pop(); this.applyClick(op.p, back ? op.before : op.after); op.t = performance.now(); to.push(op);
      this.flushNotes(); this.gutter();
    }, true);
    // served by deck/serve.py on this computer: the notes can be edited here too
    if (/^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname))
      fetch('/__notes', { cache: 'no-store' }).then(r => r.ok ? r.json() : null).then(j => { if (j && j.edit) { this.canEdit = true; document.getElementById('pv-edit').hidden = false; if (this.only && this.state && !this.editing) this.editNotes(true); } }).catch(() => {});
    document.getElementById('pv-small').onclick = () => { this.fontPx = Math.max(14, this.fontPx - 2); this.applyFont(); };
    document.getElementById('pv-big').onclick = () => { this.fontPx = Math.min(40, this.fontPx + 2); this.applyFont(); };
  }
  applyNoteW() {   // width of the notes column [px], centred
    const w = this.noteW ? Math.min(innerWidth - 60, Math.max(360, this.noteW)) : Math.min(innerWidth - 60, 1100);
    document.documentElement.style.setProperty('--pv-nw', w + 'px');
  }
  applyPrev() {   // height of the preview row [px]; the two slides keep 16:9 and shrink with it
    // as high as asked, but never so high that the two 16:9 slides no longer fit side by side in the window's width
    const fitW = Math.floor((innerWidth - 40 - 28) / 2 * 9 / 16) + 20;
    const max = Math.max(120, Math.min(innerHeight - 260, fitW)), h = this.prevH ? Math.min(max, Math.max(60, this.prevH)) : Math.round(Math.min(max, innerHeight * .36));
    document.documentElement.style.setProperty('--pv-h', h + 'px');
  }
  msg(t, bad) { const m = document.getElementById('pv-msg'); m.textContent = t; m.classList.toggle('bad', !!bad); }
  editNotes(on) {
    // the notes of this slide as an editable text in place of the teleprompter; typing is sent to the projector window,
    // which saves it into the slide's source. Turning the page keeps editing, with that slide's notes
    if (on && !this.state) return;
    if (!on) this.flushNotes();
    this.editing = on;
    document.documentElement.classList.toggle('pv-editing', on);
    document.getElementById('pv-edit').textContent = on ? 'Fertig' : 'Bearbeiten';
    document.getElementById('pv-edwrap').hidden = !on; document.getElementById('pv-notes').hidden = on;
    if (on) this.loadEditor(); else { this.msg(''); this._nk = null; this.render(); }
  }
  loadEditor() {
    const st = this.state, ed = document.getElementById('pv-ned');
    this.edI = st.i;
    const html = (st.notes !== undefined ? st.notes : this.notes[st.i] || '').trim();
    ed.innerHTML = html || '<p><br></p>'; this.edMeta = { start: st.start || 0, steps: st.steps || 0 }; this.hist = []; this.redo = [];
    document.execCommand('defaultParagraphSeparator', false, 'p');
    // open at the paragraph of this click
    const items = noteItems([...ed.querySelectorAll(':scope > p')], st.start || 0, st.steps || 0), foc = noteFocus(items, st.step);
    const cur = items.find(x => foc.get(x) === 'cur');
    const wrap = document.getElementById('pv-edwrap'); this.gutter();
    wrap.scrollTop = cur ? Math.max(0, cur.el.offsetTop - wrap.clientHeight * .25) : 0;
  }
  flushNotes() {
    clearTimeout(this._edT);
    if (!this.editing || this.edI === undefined) return;
    const ed = document.getElementById('pv-ned');
    const html = ed.innerHTML.replace(/(<br>)+(?=<\/p>|$)/g, '').replace(/&nbsp;/g, ' ')
      .replace(/ class="(?:now| *)"/g, '').replace(/ class="(q) now"| class="now (q)"/g, ' class="q"');   // the lit paragraph is this window's own mark
    if (html === this._sentHtml && this.edI === this._sentI) return;
    this._sentHtml = html; this._sentI = this.edI;
    this.notes[this.edI] = html;
    this.msg('speichert …'); this.send('notes', this.edI, html);
  }
  gutter() {
    // a chip beside each paragraph with its click; the one of the click now lit
    const ed = document.getElementById('pv-ned'), g = document.querySelector('#pv-edwrap .ned-gut');
    g.innerHTML = ''; if (!this.editing || !this.edMeta) return;
    const items = noteItems([...ed.querySelectorAll(':scope > p')], this.edMeta.start, this.edMeta.steps);
    const foc = this.state && this.state.i === this.edI ? noteFocus(items, this.state.step) : new Map();
    for (const x of items) x.el.classList.toggle('now', foc.get(x) === 'cur');
    for (const x of items) {
      const c = document.createElement('button'); c.type = 'button'; c._p = x.el;
      c.className = 'nck' + (x.q ? ' q' : '') + (!x.q && !x.el.hasAttribute('data-click') ? ' auto' : '') + (foc.get(x) === 'cur' ? ' now' : '');
      c.textContent = x.q ? 'Hintergrund' : noteLabel(x); c.title = 'Klick wählen';
      c.style.top = (ed.offsetTop + x.el.offsetTop) + 'px'; g.append(c);
    }
  }
  clickMenu(chip) {
    document.querySelector('.nck-menu')?.remove();
    const p = chip._p, start = this.edMeta.start, total = Math.max(this.edMeta.steps, start), now = this.state && this.state.i === this.edI ? this.state.step : -1;
    const [lo, hi] = (p.getAttribute('data-click') || '').split('-').map(Number);
    let h = '';
    for (let k = start; k <= total; k++) h += `<button type="button" data-k="${k}" class="${k >= lo && k <= (hi || lo) && !p.classList.contains('q') ? 'on' : ''}${k === now ? ' here' : ''}">${k === 0 ? 'Start' : k}</button>`;
    const m = document.createElement('div'); m.className = 'nck-menu';
    m.innerHTML = `<div class="nm-row">${h}</div><div class="nm-row"><button type="button" data-k="q" class="${p.classList.contains('q') ? 'on' : ''}">Hintergrund</button><span class="nm-hint">Shift+Klick: bis zu diesem Klick · gelb umrandet: jetzt</span></div>`;
    m.style.top = (chip.offsetTop + chip.offsetHeight + 4) + 'px'; chip.parentElement.append(m);
    m.addEventListener('mousedown', e => e.preventDefault());
    m.addEventListener('click', e => {
      const b = e.target.closest('[data-k]'); if (!b) return;
      let v;
      if (b.dataset.k === 'q') v = { q: true };
      else { const k = +b.dataset.k, a = isNaN(lo) || p.classList.contains('q') ? k : lo; v = { click: e.shiftKey && a !== k ? `${Math.min(a, k)}-${Math.max(a, k)}` : String(k) }; }
      const before = { click: p.getAttribute('data-click'), q: p.classList.contains('q') };
      this.applyClick(p, v); this.hist.push({ p, before, after: { click: p.getAttribute('data-click'), q: p.classList.contains('q') }, t: performance.now() }); this.redo = [];
      m.remove(); this.flushNotes(); this.gutter();
    });
    const off = e => { if (!m.contains(e.target) && e.target !== chip) { m.remove(); document.removeEventListener('pointerdown', off, true); } };
    document.addEventListener('pointerdown', off, true);
  }
  applyClick(p, v) { p.classList.toggle('q', !!v.q); if (!p.classList.length) p.removeAttribute('class'); if (v.q || v.click == null) p.removeAttribute('data-click'); else p.setAttribute('data-click', v.click); }
  async live(on) {
    // the current slide as the projector shows it: a capture of that screen (the browser asks which one), so whatever a
    // presenter remote draws over the slide (spotlight, circle, laser) shows here too. Off again: the deck preview
    const v = document.getElementById('pv-video'), btn = document.getElementById('pv-live');
    if (!on) {
      if (this.stream) this.stream.getTracks().forEach(t => t.stop());
      this.stream = null; v.srcObject = null; v.hidden = true; this.cur.style.visibility = ''; btn.classList.remove('on'); return;
    }
    try {
      this.stream = await navigator.mediaDevices.getDisplayMedia({ video: { displaySurface: 'monitor', frameRate: 30 }, audio: false });
    } catch (e) { this.msg('Live-Bild nicht freigegeben', true); return; }
    v.srcObject = this.stream; v.hidden = false; await v.play().catch(() => {});
    this.cur.style.visibility = 'hidden'; btn.classList.add('on');
    this.stream.getVideoTracks()[0].addEventListener('ended', () => this.live(false));   // "Freigabe beenden" in the browser
  }
  applyTele() { document.getElementById('pv-notes').classList.toggle('all', !this.tele); document.getElementById('pv-tele').classList.toggle('on', this.tele); }
  toggleTele() { this.tele = !this.tele; try { localStorage.setItem('pv-tele', this.tele ? '1' : '0'); } catch (e) { /* only for this page */ } this.applyTele(); this.paintNotes(true); }
  renderNotes(st) {
    // the notes of the slide as a teleprompter: the paragraphs of this click large, the one before and the one after pale,
    // the rest barely there (all of them stay in the list, scroll up or down if you lose the place); the paragraphs for
    // questions in a fold at the end. Rebuilt only when the slide or its text changes (the projector sends the live notes)
    const html = (st.notes !== undefined ? st.notes : this.notes[st.i] || '').trim(), box = document.getElementById('pv-notes');
    const key = st.i + '|' + html;
    if (this._nk !== key) {
      this._nk = key; box.scrollTop = 0;
      const doc = new DOMParser().parseFromString('<body>' + html + '</body>', 'text/html');
      const ps = [...doc.body.querySelectorAll(':scope > p')];
      box.innerHTML = '<div class="pn-list"></div>'; const list = box.firstChild;
      this.items = noteItems(ps, st.start || 0, st.steps || 0);
      const bg = document.createElement('details'); bg.className = 'pn-bg'; bg.innerHTML = '<summary>Hintergrund (bei Fragen)</summary>';
      for (const x of this.items) {
        const d = document.createElement('p'); d.className = 'pn'; x.dom = d;
        const lab = x.q ? '' : `<span class="pn-k">${noteLabel(x)}</span>`;
        d.innerHTML = lab + x.el.innerHTML;
        (x.q ? bg : list).append(d);
      }
      if (!ps.length) list.innerHTML = '<p class="pn q">Keine Notizen.</p>';
      if (bg.children.length > 1) box.append(bg);
    }
    this.curStep = st.step; this.paintNotes();
  }
  paintNotes(jump) {
    if (!this.items) return;
    const foc = noteFocus(this.items, this.curStep ?? 0), box = document.getElementById('pv-notes');
    let first = null;
    let ahead = false;   // far paragraphs after the current one stay faintly visible, those before it go
    for (const x of this.items) { if (x.q) continue; const k = foc.get(x) || 'far'; if (k === 'cur' || k === 'next') ahead = true; x.dom.classList.remove('cur', 'prev', 'next', 'far', 'after'); x.dom.classList.add(k); if (k === 'far' && ahead) x.dom.classList.add('after'); if (k === 'cur' && !first) first = x.dom; }
    if (!first) first = this.items.map(x => x.dom).find(d => d.classList.contains('next'));
    // every paragraph is set at the size of the current one and only scaled down: its line breaks never change when
    // it moves into focus. The room a scaled paragraph leaves below it is taken back with a negative margin
    const SC = { cur: 1, next: .8, prev: .62, far: .66 }, GAP = 16;
    for (const x of this.items) {
      if (x.q) continue;
      const k = this.tele ? ['cur', 'next', 'prev', 'far'].find(c => x.dom.classList.contains(c)) : 'cur', f = SC[k];
      x.dom.style.transform = f === 1 ? '' : `scale(${f})`;
      x.dom.style.marginBottom = (GAP - (1 - f) * x.dom.offsetHeight) + 'px';
      const lab = x.dom.querySelector('.pn-k'); if (lab) lab.style.transform = f === 1 ? '' : `translateX(${-112 * (1 - f) / f}px) scale(${Math.max(.75, .9 / f) * f / f})`;
    }
    if (first && this.tele) {
      // the current click at the top: what comes next has the room; of what was said only the last line stays in view
      const prevs = this.items.map(x => x.dom).filter(d => d.classList.contains('prev')), pv = prevs[prevs.length - 1];
      const keep = pv ? parseFloat(getComputedStyle(pv).lineHeight) * SC.prev + 12 : 0;
      box.scrollTo({ top: Math.max(0, first.offsetTop - keep), behavior: jump ? 'auto' : 'smooth' });
    }
  }
  applyFont() { document.documentElement.style.setProperty('--pv-notes', this.fontPx + 'px'); }
  render() {
    const st = this.state; if (!st) return;
    // the notes and the bar first: they must answer the click at once; the two previews (whole decks, sharing this
    // window's thread) follow a moment later, the current one before the next
    document.getElementById('pv-count').textContent = st.i < st.main ? `${st.i + 1} / ${st.main}` : `Backup ${st.i + 1 - st.main}`;
    document.getElementById('pv-title').textContent = this.titles[st.i];
    if (this.editing) { if (st.i !== this.edI) { this.flushNotes(); this.loadEditor(); } }
    else this.renderNotes(st);
    const post = (f, i, step, mark) => f.contentWindow && f.contentWindow.postMessage({ src: 'dv', goto: i, step, mark: !!mark }, '*');
    // a preview is only steered when its slide or click changes (each move is a full page step inside it)
    const key = (f, i, step) => { const k = i + ':' + step; if (f._k === k) return false; f._k = k; return true; };
    const end = st.ni >= st.n || (st.i < st.main && st.ni >= st.main);
    document.getElementById('pv-end').hidden = !end; this.nxt.style.visibility = end ? 'hidden' : 'visible';
    clearTimeout(this._pvT1); clearTimeout(this._pvT2);   // fast clicking: only the last state is drawn
    this._pvT1 = setTimeout(() => { if (key(this.cur, st.i, st.step)) post(this.cur, st.i, st.step); }, 420);   // after the notes have scrolled
    this._pvT2 = setTimeout(() => { if (!end && key(this.nxt, st.ni, st.ns)) post(this.nxt, st.ni, st.ns, true); }, 650);
  }
  marks() {
    // the time marks, kept in this browser (edited in edit mode, E): "30, 40" or "0:15, 30:00"; the last one is red
    let txt; try { txt = localStorage.getItem('pv-marks'); } catch (e) { /* only for this page */ }
    const secs = (txt || '30, 40').split(/[,;\s]+/).map(x => x.trim()).filter(Boolean).map(x => {
      const m = /^(\d+)(?::(\d{1,2}))?$/.exec(x); return m ? +m[1] * 60 + (+m[2] || 0) : NaN;
    }).filter(x => x > 0).sort((a, b) => a - b);
    const name = v => v % 60 ? `${Math.floor(v / 60)}:${String(v % 60).padStart(2, '0')} min` : `${v / 60} Minuten`;
    return secs.map((v, j) => ({ s: v, cls: j === secs.length - 1 ? 'm2' : 'm1', text: name(v) + ' vorbei' }));
  }
  titleNote() {
    // on the title slide: a red reminder to start the timer from zero; once reset there, it turns green
    const el = document.getElementById('pv-title-note'), on = this.state && this.state.i === 0 && !(this.resetAt && Date.now() - this.resetAt > 1200);
    el.hidden = !on; if (!on) return;
    const fresh = this.resetAt && this.state && Date.now() - this.resetAt < 10 * 60 * 1000;
    el.classList.toggle('ok', !!fresh);
    el.querySelector('b').textContent = fresh ? 'Timer läuft ab Null ✓' : 'Timer zurücksetzen!';
  }
  tick() {
    const ms = (this.paused ?? Date.now()) - this.t0, m = Math.floor(ms / 60000), sec = Math.floor(ms / 1000) % 60;
    const t = document.getElementById('pv-timer');
    t.textContent = `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
    t.classList.toggle('paused', this.paused !== null);
    // time marks: from 30 min the timer turns amber, from 40 min red, and each mark is announced once in a banner
    // (the 15 s mark only to try it out)
    const MARKS = this.marks();
    this.hit = this.hit || new Set();
    const passed = MARKS.filter(m => ms >= m.s * 1000);
    t.classList.toggle('m1', passed.some(m => m.cls === 'm1') && !passed.some(m => m.cls === 'm2'));
    t.classList.toggle('m2', passed.some(m => m.cls === 'm2'));
    for (const m of passed) if (!this.hit.has(m.s)) {
      this.hit.add(m.s);
      const a = document.getElementById('pv-alert'); a.textContent = m.text; a.className = m.cls; a.hidden = false;
      clearTimeout(this._alT); this._alT = setTimeout(() => { a.hidden = true; }, 12000);
    }
    document.getElementById('pv-clock').textContent = new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  }
}
