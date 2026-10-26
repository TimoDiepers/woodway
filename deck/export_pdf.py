"""Export the built deck (deck/dist) as a PDF, one page per slide in its last click state.

    uv run python deck/build.py
    uv run --with playwright --with pypdf python deck/export_pdf.py [out.pdf] [--main]

Drives the real deck in the installed Google Chrome (no browser download): every slide is
opened with deck.go(i, 'end'), as the presenter's "back" key shows it, its charts and formulas
built, and printed alone as one vector page (text stays selectable). --main leaves out the backup.
A slide whose last click lays something over its content (a closing card, the summary's dusk) gets one page more
before that: the same slide one click earlier, so on paper its content stands on its own.
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

# the click that covers the slide (closing card, dusk); the page before it is printed too
COVER = """i => { const s = deck.slides[i], o = s.querySelector('.ovl[data-step], .fz-dusk[data-step]');
                    return o ? +o.dataset.step - 1 : null; }"""


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
        def shot() -> None:
            pdf = page.pdf(width="1600px", height="900px", print_background=True, page_ranges="1")
            writer.add_page(PdfReader(io.BytesIO(pdf)).pages[0])

        for i in range(n):
            page.evaluate("i => deck.go(i, 'end')", i)
            # images of the slide loaded, then a moment for charts and late layout
            page.wait_for_function("""i => [...deck.slides[i].querySelectorAll('img')]
                                         .every(im => !im.getAttribute('src') || im.complete)""", arg=i)
            page.wait_for_timeout(600)
            before = page.evaluate(COVER, i)
            if before is not None:
                # stepped back from the end, as the presenter's back key does: no entrances replay, the cover fades out
                page.evaluate("k => { while (deck.step > k) deck.prev(); }", before)
                page.wait_for_timeout(1800)
                shot()
                page.evaluate("i => deck.go(i, 'end')", i)
                page.wait_for_timeout(1800)
            shot()
            print(f"\r{i + 1}/{n}", end="", flush=True)
        browser.close()
    with out.open("wb") as f:
        writer.write(f)
    print(f"\n{out}")


if __name__ == "__main__":
    main()
