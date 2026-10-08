"""Slide overview: jump to any slide from a grid of small previews.

Desktop: key M opens/closes (Esc closes, arrows move, Enter jumps).
Touch devices: a floating button at the bottom right.
Previews are made in the browser, no build step: a hidden copy of the deck
(embed mode, no animations; an iframe built from a snapshot of this page via
srcdoc, so it is same-origin even when opened from file://) steps to each slide's end state; the slide is cloned
(canvases as small images) and shown scaled down in its card. Visible cards
first, then the rest in the background.
"""

CSS = r"""
/* ---------- slide overview (M) ---------- */
#menu-fab { position: fixed; right: 16px; bottom: 16px; z-index: 65; width: 52px; height: 52px; border-radius: 50%;
  border: 0; background: #1f2823; color: var(--paper); display: none; place-items: center; cursor: pointer;
  box-shadow: 0 4px 14px rgba(0,0,0,.28); -webkit-tap-highlight-color: transparent; }
#menu-fab svg { width: 22px; height: 22px; }
@media (hover: none), (pointer: coarse) { #menu-fab { display: grid; } }
body:has(#menu.open) #menu-fab { display: none; }
.embed #menu-fab, .embed #menu { display: none !important; }
#menu { position: fixed; inset: 0; z-index: 70; background: rgba(23, 30, 27, .94); color: #e8e3d6;
  display: flex; flex-direction: column; opacity: 0; visibility: hidden; transition: opacity .2s var(--ease), visibility 0s .2s;
  font-family: var(--sans); }
#menu.open { opacity: 1; visibility: visible; transition: opacity .2s var(--ease); }
#menu .menu-head { display: flex; align-items: center; gap: 16px; padding: 18px 28px 14px; border-bottom: 1px solid #34413a; }
#menu .menu-head h2 { font: 600 20px/1 var(--sans); margin: 0; color: #fff; }
#menu .menu-head span { font-size: 13px; color: #9aa79f; }
#menu .menu-head span kbd { border-color: #56625a; color: #cfd6cf; }
#menu .menu-close { margin-left: auto; background: none; border: 0; color: #cfd6cf; font: 400 30px/1 var(--sans);
  width: 44px; height: 44px; border-radius: 8px; cursor: pointer; }
#menu .menu-close:hover { background: #2c3832; }
#menu .menu-body { flex: 1; overflow-y: auto; padding: 8px 28px 40px; scrollbar-color: #56625a transparent; overscroll-behavior: contain; }
#menu h3 { font: 600 13px/1 var(--sans); letter-spacing: .08em; text-transform: uppercase; color: #9fb294; margin: 22px 0 12px; }
#menu .menu-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(216px, 1fr)); gap: 18px 16px; }
#menu .card { all: unset; box-sizing: border-box; display: flex; flex-direction: column; gap: 7px; cursor: pointer; min-width: 0; }
#menu .card .pv { position: relative; aspect-ratio: 16 / 9; border-radius: 6px; overflow: hidden; background: var(--paper);
  outline: 2px solid transparent; outline-offset: 2px; transition: outline-color .15s, transform .15s; }
#menu .card { content-visibility: auto; contain-intrinsic-size: auto 160px; }
#menu .card .pv b { position: absolute; inset: 0; display: grid; place-items: center; font: 600 34px/1 var(--sans); color: #b9b19c; }
#menu .tdeck { position: absolute; left: 0; top: 0; width: 1600px; height: 900px; transform-origin: 0 0;
  transform: scale(var(--k, .14)); pointer-events: none; }
#menu .tdeck .slide { visibility: visible; opacity: 1; }
#menu .tdeck, #menu .tdeck * { animation: none !important; transition: none !important; }
#menu .card .pv .tdeck + b { display: none; }
#menu .card .cap { display: flex; gap: 8px; font-size: 14px; line-height: 1.3; color: #d9d4c6; }
#menu .card .cap i { font-style: normal; font-variant-numeric: tabular-nums; color: #9aa79f; min-width: 2.2ch; }
#menu .card .cap span { overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
#menu .card:hover .pv, #menu .card:focus-visible .pv { outline-color: #cfd6cf; }
#menu .card.cur .pv { outline-color: var(--moss-soft); }
#menu .card.cur .cap { color: #fff; }
@media (max-width: 700px) {
  #menu .menu-head { padding: 14px 16px 10px; }
  #menu .menu-head span { display: none; }
  #menu .menu-body { padding: 4px 16px 90px; }
  #menu .menu-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 14px 12px; }
  #menu .card .cap { font-size: 13px; }
}
@media (prefers-reduced-motion: reduce) { #menu, #menu .card .pv { transition: none; } }
"""

HTML = r"""
<button id="menu-fab" type="button" aria-label="Folienübersicht" aria-haspopup="dialog" aria-controls="menu">
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="3" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.5"/></svg>
</button>
<div id="menu" role="dialog" aria-modal="true" aria-label="Folienübersicht">
  <div class="menu-head"><h2>Folien</h2><span><kbd>M</kbd> oder <kbd>Esc</kbd> schließen · Pfeile wählen · <kbd>↵</kbd> springen</span>
    <button class="menu-close" type="button" aria-label="Schließen">×</button></div>
  <div class="menu-body"></div>
</div>
"""

JS = r"""
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
    if (this.maker) return;
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
    this.el.classList.add('open'); this.fab.setAttribute('aria-expanded', 'true');
    this.scale();
    const cur = this.cards[this.deck.i];
    cur.scrollIntoView({ block: 'center' }); cur.focus({ preventScroll: true });
  }
  close() { this.el.classList.remove('open'); this.fab.setAttribute('aria-expanded', 'false'); document.activeElement?.blur(); }
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
    else if (k === 'Tab') return;
  }
}
"""


def _rep(page, old, new):
    assert page.count(old) == 1, old[:80]
    return page.replace(old, new)


def patch(page: str) -> str:
    page = _rep(page, "#jump-badge { position: fixed;", CSS + "\n#jump-badge { position: fixed;")
    page = _rep(page, '<div class="hint" id="hint">', HTML + '<div class="hint" id="hint">')
    page = _rep(page, '<kbd>F</kbd> Vollbild ·', '<kbd>F</kbd> Vollbild · <kbd>M</kbd> Übersicht ·')
    page = _rep(page, "function slideJumper(count, titleOf, jump) {", JS + "\nfunction slideJumper(count, titleOf, jump) {")
    page = _rep(page, "    this.embed = location.search.includes('embed');", "    this.embed = location.search.includes('embed') || !!window.__EMBED;")
    page = _rep(page, "  if (location.search.includes('embed')) document.documentElement.classList.add('embed');",
                "  if (location.search.includes('embed') || window.__EMBED) document.documentElement.classList.add('embed');")
    page = _rep(page, "<script>\nwindow.DAC_PLAY = ", '<script id="deck-snap">window.__SNAP = document.documentElement.cloneNode(true);</script>\n<script>\nwindow.DAC_PLAY = ')
    page = _rep(page, "    if (!this.embed) this.bind();", "    if (!this.embed) { this.bind(); this.menu = new SlideMenu(this); }")
    return page
