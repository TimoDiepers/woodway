"""Fast first slide: data and images load in the background.

- The chart data (charts.js, cmip7.js, ec_charts.js, maps.js) and ECharts no
  longer block parsing. They load async; the charts are built once all are in
  (window.DECK_DATA, a promise) and the current slide is redrawn.
- Slide images (<img src="v2/..."> etc., not data: URIs) become data-src. The
  deck loads the current slide and its neighbours on every go(); after the
  data is in, the rest follows slide by slide in the background.
"""

import re

DATA = ["v2/charts.js", "v2/cmip7.js", "v2/ec_charts.js", "v2/maps.js", "vendor/echarts/echarts.min.js"]

LOADER = r"""<script>/* chart data and ECharts load in the background; the first slide does not wait for them */
window.DECK_DATA = Promise.all(%s.map(src => new Promise(ok => {
  const s = document.createElement('script'); s.src = src; s.async = true; s.dataset.dyn = 1;
  s.onload = s.onerror = ok; document.head.appendChild(s);
}))).then(() => { /* the deck draws four of the seven CMIP7 markers */
  const keep = ["H", "M", "ML", "VL"], D = window.CMIP7; if (!D) return;
  D.markers = D.markers.filter(m => keep.includes(m.k)); D.cum = D.cum.filter(c => keep.includes(c.k)); });</script>"""

MEDIA_JS = r"""
/* ---------- images: current slide first, the rest in the background ---------- */
const deckMedia = {
  load(s) {
    if (!s || s._media) return; s._media = true;
    for (const im of s.querySelectorAll('img[data-src]')) { im.src = im.dataset.src; im.removeAttribute('data-src'); }
  },
  around(slides, n) { for (const k of [n, n + 1, n - 1, n + 2]) this.load(slides[k]); },
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
"""


def _rep(page, old, new):
    assert page.count(old) == 1, old[:80]
    return page.replace(old, new)


def patch(page: str) -> str:
    # 1) data scripts: drop the blocking tags, add the async loader in their place
    for src in DATA:
        page = _rep(page, f'<script src="{src}"></script>\n', "")
    cm = re.search(r'<script>/\* the deck draws four of the seven CMIP7 markers \*/.*?</script>\n', page, re.S)
    assert cm
    page = page[:cm.start()] + LOADER % ("[" + ", ".join(f'"{s}"' for s in DATA) + "]") + "\n" + page[cm.end():]

    # 2) charts are built when the data is in; the deck shows the first slide before
    old = ("  for (const h of deckEl.querySelectorAll('.chart')) h._chart = h.dataset.ec ? new EChart(h) : window.ECDATA ? new MplChart(h) : new Chart(h);\n"
           "  window.deck = new Deck();\n")
    new = ("  window.deck = new Deck();\n"
           "  window.DECK_DATA.then(() => {\n"
           "    for (const h of deckEl.querySelectorAll('.chart')) h._chart = h.dataset.ec ? new EChart(h) : window.ECDATA ? new MplChart(h) : new Chart(h);\n"
           "    window.deck.dataReady();\n"
           "  });\n")
    page = _rep(page, old, new)
    page = _rep(page, "  go(n, step) {\n    n = Math.max(0, Math.min(this.slides.length - 1, n));\n",
                "  go(n, step) {\n    n = Math.max(0, Math.min(this.slides.length - 1, n));\n    deckMedia.around(this.slides, n);\n")
    page = _rep(page, "  applyStep(animate, entering) {",
                "  dataReady() {\n"
                "    // charts exist now: recount the clicks and draw the current slide in its present state\n"
                "    for (const s of this.slides) delete s._steps;\n"
                "    this.ready = true;\n"
                "    if (this.still) this.go(this.i, this.step); else this.applyStep(false, false);\n"
                "    if (!this.embed) setTimeout(() => deckMedia.rest(this.slides), 300);\n"
                "  }\n"
                "  applyStep(animate, entering) {")
    page = _rep(page, "class Deck {", MEDIA_JS + "\nclass Deck {")

    # 3) images: src -> data-src (inline data: URIs stay)
    page, n = re.subn(r'(<img\b[^>]*?)\ssrc="(?!data:|\$\{)([^"]+)"', r'\1 data-src="\2"', page)
    assert n > 50, n
    return page
