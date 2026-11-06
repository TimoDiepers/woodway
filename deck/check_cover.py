"""Check the built deck for clicks that put something over what a slide already shows.

    uv run python deck/build.py
    uv run --with playwright --with pillow python deck/check_cover.py [--main] [--slides=12,25]

A slide is meant to be complete in its last click state (deck/export_pdf.py prints exactly that): where a click
lays a card or picture over earlier content, the slide is split in two (data-end on the first half, data-start and
data-carry on the second, as slides 12 and 19). This lists the places that would need such a split.

Drives the real deck in the installed Google Chrome (no browser download), in print media, so the check sees what
the paper shows. Every slide is stepped through click by click (deck.go(i, k), entrances finished, loops held).

Each click is compared with the next one: if the next click lays something opaque (a card, an overlay, a picture)
over content the slide already shows (text, an image, a chart as a whole), it is listed. What does not count: content added in free
space, content that fades out, is dimmed or replaced (the later page is complete in itself), and changes inside a
chart (its picture is redrawn, not covered).

Badges swapped in place (a tree's \"?\" becoming a tick) show up too; they need no split.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from playwright.sync_api import sync_playwright

DECK = Path(__file__).resolve().parent
PAGE = (DECK / "dist" / "index.html").as_uri()

# only the current slide goes to paper; live embeds (the Woodway app) give way to their poster image. Every element
# takes part in hit testing, so the check also sees overlays that ignore the pointer.
STYLE = """@media print { #deck > .slide:not(.active), #deck iframe { display: none !important; } }
#deck * { pointer-events: auto !important; }"""

SETTLE_MS = 700    # entrances and CSS transitions are finished by hand; this is for layout and images
CHART_MS = 2600    # an ECharts update tweens up to 2.4 s
COVERED_MIN = 2    # covered elements that make an earlier click a page of its own
CHART_LOST = 800   # chart pixels (at full size) that showed content and now show something else
DIFF = 40          # colour distance (0..441) that counts as a change


def _chart_lost(old: np.ndarray, new: np.ndarray, noise: np.ndarray) -> int:
    """Pixels of a chart that showed content in *old* and show something else in *new*, beyond a fade towards
    the chart's paper (a dimmed curve stays readable)."""
    q = (old // 8).reshape(-1, 3)
    keys, counts = np.unique(q[:, 0] * 1024 + q[:, 1] * 32 + q[:, 2], return_counts=True)
    k = keys[counts.argmax()]
    bg = np.array([k // 1024, (k // 32) % 32, k % 32]) * 8 + 4
    dist = lambda x, y: np.sqrt(((x - y) ** 2).sum(axis=-1))
    d = (bg - old).astype(float)
    t = ((new - old) * d).sum(axis=-1) / np.maximum((d * d).sum(axis=-1), 1)
    faded = (t > 0) & (t < 0.85) & (dist(new.astype(float), old + t[..., None] * d) < DIFF / 2)
    return int(((dist(old, bg) > DIFF) & (dist(old, new) > DIFF) & ~faded & ~noise).sum())

# every finite animation to its end, every loop held at its start
FREEZE = """() => { for (const a of document.getAnimations()) {
  try { const t = a.effect && a.effect.getComputedTiming();
        if (t && t.iterations === Infinity) { a.pause(); a.currentTime = 0; } else a.finish(); } catch (e) {} } }"""

# the visible elements of slide i (kept in window.__pdfVis[k]) and, later, which of them another state covers
PROBE = r"""
(() => {
  // content: text, pictures, charts; bare drawing shapes are left out (backdrops like the forest silhouette)
  const SHAPES = new Set(['img', 'canvas', 'text', 'image']);
  const rendered = el => {
    if (!el.isConnected) return false;
    let op = 1;
    for (let e = el; e && e.nodeType === 1; e = e.parentElement || (e.parentNode && e.parentNode.host)) {
      const cs = getComputedStyle(e);
      if (cs.display === 'none' || cs.visibility === 'hidden') return false;
      op *= +cs.opacity;
    }
    return op > 0.15;
  };
  const ownText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  const leaf = el => el.matches('.chart') || SHAPES.has(el.localName) || ownText(el);
  // what can cover: anything that paints, shapes included (a card's frame, a filled drawing)
  const DRAWN = new Set(['path', 'rect', 'circle', 'ellipse', 'polygon', 'use']);
  const alpha = c => { const m = /rgba?\(([^)]+)\)/.exec(c || ''); if (!m) return 0; const p = m[1].split(/[ ,/]+/).filter(Boolean); return p.length > 3 ? +p[3] : 1; };
  // does element a paint over the point (opaque enough to hide what lies below)?
  const paints = a => {
    if (!rendered(a) || a.localName === 'svg' || a.localName === 'g') return false;
    if (leaf(a)) return true;
    if (DRAWN.has(a.localName)) { const f = getComputedStyle(a).fill; return f && f !== 'none' && alpha(f) > 0.5; }
    const cs = getComputedStyle(a);
    return alpha(cs.backgroundColor) > 0.5 || (cs.backgroundImage && cs.backgroundImage !== 'none');
  };
  const box = el => { const r = el.getBoundingClientRect(); return r.width * r.height > 4 ? r : null; };
  // the share of the element's sample points where something opaque lies on top of it
  const covered = el => {
    const r = box(el); if (!r) return 0;
    let hits = 0, under = 0;
    for (const fx of [.25, .5, .75]) for (const fy of [.25, .5, .75]) {
      const x = r.left + fx * r.width, y = r.top + fy * r.height;
      if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) continue;
      const stack = document.elementsFromPoint(x, y), j = stack.findIndex(s => s === el || el.contains(s));
      if (j < 0) continue;
      hits++;
      if (stack.slice(0, j).some(a => !el.contains(a) && !a.contains(el) && paints(a))) under++;
    }
    return hits ? under / hits : 0;
  };
  const name = el => (el.localName + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '')
                      + (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40).replace(/^(.+)$/, ' "$1"'));
  window.__pdfVis = window.__pdfVis || {};
  window.__pdfCollect = (i, k) => {
    const s = deck.slides[i];
    const els = [...s.querySelectorAll('*')].filter(el => !el.closest('aside, .notes, script, style, nav.path')
      && !(el.closest('.chart') && !el.matches('.chart')) && leaf(el) && rendered(el) && box(el) && covered(el) < .5);
    window.__pdfVis[k] = els;
    return els.length;
  };
  window.__pdfCovered = k => (window.__pdfVis[k] || []).filter(el => rendered(el) && covered(el) >= .5).map(name);
})();
"""


def main() -> None:
    found: list[tuple[int, str]] = []   # (slide number, line)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.goto(PAGE)
        page.emulate_media(media="print")
        page.add_style_tag(content=STYLE)
        page.evaluate("() => { window.__deckDataNow(); return window.DECK_DATA; }")
        page.wait_for_function("() => window.__ensureCharts && window.katex && document.fonts.status === 'loaded'")
        page.evaluate(PROBE)
        n = page.evaluate("main => main ? deck.mainEnd : deck.slides.length", "--main" in sys.argv)

        def show(i: int, k) -> None:
            page.evaluate("([i, k]) => deck.go(i, k)", [i, k])
            page.wait_for_function("""i => [...deck.slides[i].querySelectorAll('img')]
                                         .every(im => !im.getAttribute('src') || im.complete)""", arg=i)
            charts = page.evaluate("i => !!deck.slides[i].querySelector('.chart')", i)
            page.wait_for_timeout(CHART_MS if charts else SETTLE_MS)
            page.evaluate(FREEZE)
            page.wait_for_timeout(120)

        def charts(i: int) -> dict[str, tuple[np.ndarray, np.ndarray]]:
            """Each visible chart of the slide as a picture, and its pixels that move on their own."""
            out = {}
            boxes = page.evaluate("""i => [...deck.slides[i].querySelectorAll('.chart')].map((h, n) => {
                const r = h.getBoundingClientRect(); return [h.dataset.ec || h.dataset.chart || String(n), r.x, r.y, r.width, r.height,
                  getComputedStyle(h).visibility !== 'hidden' && +getComputedStyle(h).opacity > .5 && h.offsetParent !== null]; })""", i)
            for name, x, y, w, h, vis in boxes:
                if not vis or w < 20 or h < 20:
                    continue
                clip = {"x": max(0, x), "y": max(0, y), "width": min(w, 1600 - max(0, x)), "height": min(h, 900 - max(0, y))}
                a = np.asarray(Image.open(io.BytesIO(page.screenshot(clip=clip))).convert("RGB"), dtype=np.int32)
                page.wait_for_timeout(150)
                b = np.asarray(Image.open(io.BytesIO(page.screenshot(clip=clip))).convert("RGB"), dtype=np.int32)
                out[name] = (a, np.sqrt(((a - b) ** 2).sum(axis=-1)) > DIFF)
            return out

        only = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--slides=")), "")
        todo = [int(x) - 1 for x in only.split(",") if x.strip()] if only else range(n)   # --slides=12,25: these only
        for i in todo:
            last = page.evaluate("i => { deck.go(i, 'end'); return deck.step; }", i)
            start = page.evaluate("i => deck.slides[i].dataset.start === undefined ? -1 : +deck.slides[i].dataset.start", i)
            title = page.evaluate("i => deck.slides[i].dataset.title || ''", i)
            # forward, click by click: what does click k+1 lay over what click k shows?
            page.evaluate("() => { window.__pdfVis = {}; }")
            show(i, 0)
            page.evaluate("i => window.__pdfCollect(i, 0)", i)
            prev = charts(i)
            for k in range(last):
                show(i, k + 1)
                cov = page.evaluate("k => window.__pdfCovered(k)", k)
                cur = charts(i)
                # a chart redrawn over its own earlier picture (curves gone, another picture in their place)
                lost = [n for n, (a, na) in prev.items() if n in cur and a.shape == cur[n][0].shape
                        and _chart_lost(a, cur[n][0], na | cur[n][1]) >= CHART_LOST]
                # a split slide's second half covers the picture it opens on on purpose: the first half prints it
                if (len(cov) >= COVERED_MIN or lost) and k != start:
                    what = (" ".join(cov[:6]) + (" …" if len(cov) > 6 else "")) if len(cov) >= COVERED_MIN else ""
                    what += "".join(f" [chart {n} redrawn]" for n in lost)
                    found.append((i + 1, f"slide {i + 1} {title!r}: click {k} covered by click {k + 1}: {what.strip()}"))
                page.evaluate("([i, k]) => window.__pdfCollect(i, k)", [i, k + 1])
                prev = cur
            print(f"\r{i + 1}/{n}", end="", flush=True)
        browser.close()
    print()
    for _, line in found:
        print(line)
    print(f"{len(found)} covering clicks on {len({num for num, _ in found})} slides")

if __name__ == "__main__":
    main()
