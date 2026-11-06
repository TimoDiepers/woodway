"""Export the built deck (deck/dist) as a PDF, one page per slide in its last click state.

    uv run python deck/build.py
    uv run --with playwright --with pypdf python deck/export_pdf.py [out.pdf] [--main]

Drives the real deck in the installed Google Chrome (no browser download): every slide is opened with
deck.go(i, 'end'), as the presenter's "back" key shows it, its charts and formulas built, and printed alone as one
vector page (text stays selectable). --main leaves out the backup. Every slide is complete in its last state: where
a click would lay something over earlier content, the slide is split in two (data-end / data-start, see
deck/check_cover.py), so its end state is all the paper needs.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

DECK = Path(__file__).resolve().parent
PAGE = (DECK / "dist" / "index.html").as_uri()

# only the current slide goes to paper; live embeds (the Woodway app) give way to their poster image
ONLY_ACTIVE = "@media print { #deck > .slide:not(.active), #deck iframe { display: none !important; } }"

# entrances that are still running (a card's parts rise in one after the other) jump to their end; loops stay put
FINISH = """() => { for (const a of document.getAnimations()) {
  try { const t = a.effect && a.effect.getComputedTiming(); if (t && t.iterations !== Infinity) a.finish(); } catch (e) {} } }"""


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(args[0]) if args else DECK / "dist" / "woodway.pdf"
    writer = PdfWriter()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.goto(PAGE)
        page.add_style_tag(content=ONLY_ACTIVE)
        page.evaluate("() => { window.__deckDataNow(); return window.DECK_DATA; }")
        page.wait_for_function("() => window.__ensureCharts && window.katex && document.fonts.status === 'loaded'")
        n = page.evaluate("main => main ? deck.mainEnd : deck.slides.length", "--main" in sys.argv)
        for i in range(n):
            page.evaluate("i => deck.go(i, 'end')", i)
            # images of the slide loaded, then a moment for charts and late layout
            page.wait_for_function("""i => [...deck.slides[i].querySelectorAll('img')]
                                         .every(im => !im.getAttribute('src') || im.complete)""", arg=i)
            page.wait_for_timeout(600)
            page.evaluate(FINISH)
            page.wait_for_timeout(100)
            pdf = page.pdf(width="1600px", height="900px", print_background=True, page_ranges="1")
            writer.add_page(PdfReader(io.BytesIO(pdf)).pages[0])
            print(f"\r{i + 1}/{n}", end="", flush=True)
        browser.close()
    with out.open("wb") as f:
        writer.write(f)
    print(f"\n{out}")


if __name__ == "__main__":
    main()
