"""Which texts on a slide can be edited in the page (deck/serve.py), and where they are in the source.

A target is a text element (heading, paragraph, list item, legend entry, table cell) of a slide's source section
whose content is plain text with simple inline markup only: no formulas ($…$), no elements of their own (a step,
a highlight, a drawing). Those stay as they are in the page and in the source. The build numbers the targets of
each section (data-e="k"); the server finds target k again in the same way and replaces its content.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

INLINE = re.compile(r"</?(b|i|em|strong|sub|sup|br|a|small|u|s|mark)(\s[^>]*)?/?>", re.I)   # allowed inside a text target
SKIP = {"script", "style", "template", "aside", "title", "desc", "button", "kbd", "option", "select", "textarea"}
VOID = {"br", "img", "input", "meta", "link", "hr", "wbr", "source", "col", "area", "base", "embed", "param", "track",
        "path", "circle", "rect", "line", "polyline", "polygon", "ellipse", "use", "stop", "image"}


class _Finder(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=False)
        self.lines = [0] + [m.end() for m in re.finditer("\n", text)]
        self.stack: list[tuple[str, int, int]] = []
        self.found: list[tuple[int, int, int, bool]] = []   # start tag start, inner start, inner end, in a drawing
        self.skip = 0
        self.svg = 0

    def _off(self) -> int:
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        a = self._off()
        b = a + len(self.get_starttag_text())
        if tag in VOID:
            return
        self.stack.append((tag, a, b))
        self.skip += tag in SKIP
        self.svg += tag == "svg"

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        while self.stack:
            t, a, b = self.stack.pop()
            self.skip -= t in SKIP
            self.svg -= t == "svg"
            if not self.skip and (t == "text" if self.svg else t not in ("svg", "section", "header")):
                self.found.append((a, b, self._off(), bool(self.svg)))
            if t == tag:
                return


def targets(section: str) -> list[tuple[int, int, int]]:
    """(start tag start, inner start, inner end) of each editable text of a section, in document order: an element
    with nothing but text and simple inline markup in it (no formula, no elements of its own), or, in a drawing, a
    text label with whatever it holds; the outermost one where they nest."""
    f = _Finder(section)
    f.feed(section)
    out = []
    for a, b, c, svg in sorted(f.found):
        inner = section[b:c]
        if "$" in inner or not re.sub(r"<[^>]+>|&nbsp;|&#?\w+;|\s", "", inner):
            continue
        if not svg and re.sub(INLINE, "", inner).count("<"):
            continue
        if any(a0 < a and c <= c0 for a0, _, c0 in out):   # inside another target
            continue
        out.append((a, b, c))
    return out


def text_of(html: str) -> str:
    """What a text reads, for checking that the source still has it: tags out, entities and spaces as in the page."""
    import html as H
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", html))).strip()


def tag(section: str) -> str:
    """The section with each target numbered: data-e="k" on its start tag."""
    out, last = [], 0
    for k, (a, b, _) in enumerate(targets(section)):
        start = section[a:b]
        out.append(section[last:a] + re.sub(r"^<(\w+)", rf'<\1 data-e="{k}"', start))
        last = b
    return "".join(out) + section[last:]


def sections(text: str) -> list[tuple[int, int]]:
    """Start and end of each slide section of a slide file."""
    starts = [m.start() for m in re.finditer(r"<section ", text)] + [len(text)]
    return list(zip(starts, starts[1:]))


FORMULA = re.compile(r"\$\$[\s\S]+?\$\$|\$[^$]+?\$")   # as the page splits them (deck.js renderTex)


def formulas(section: str) -> list[tuple[int, int]]:
    """Start and end of each formula ($…$, $$…$$) of a section, in the order the page renders them: text outside
    tags and comments, not in drawings (svg) or the notes."""
    out, depth = [], {"svg": 0, "aside": 0}
    for m in re.finditer(r"<!--.*?-->|<(/?)(\w+)[^>]*?(/?)>|([^<]+)", section, re.S):
        if m.group(4) is not None:
            if not any(depth.values()):
                out += [(m.start(4) + f.start(), m.start(4) + f.end()) for f in FORMULA.finditer(m.group(4))]
        elif m.group(2) and m.group(2).lower() in depth and not m.group(3):
            depth[m.group(2).lower()] += -1 if m.group(1) else 1
    return out
