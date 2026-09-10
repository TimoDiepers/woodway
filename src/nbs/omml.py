"""Build native PowerPoint equations (OMML), with a colour code per symbol.

**Why this exists.** Several slides carried LaTeX *source* as ordinary text,
so ``\\dot m_{Stör}(t) = p_{Stör}(T)\\, m(t)`` appeared literally on the
slide. That convention grew out of a real incident: hand-authored OMML once
left the deck unable to save at all. The lesson taken from it was "never
touch the math XML again", which is one lesson too many -- the actual fault
was ad-hoc XML, not OMML as such.

So this module does the opposite of ad-hoc: it emits only the constructs the
deck's own PowerPoint-authored equations already contain, in the same shape,
with the same run properties. Everything is built from a small expression
tree, and ``tests/test_omml.py`` checks the output against those existing
equations. Nothing here is typed by hand into a slide.

**The colour code.** Every run carries its own ``a:srgbClr``, which is how
PowerPoint itself stores per-symbol colour, so a symbol can be recognised
across slides and against the figures:

    ROLE_CARBON  #1b7837  the carbon channel        (= nbs.plots.C_CARBON)
    ROLE_ALBEDO  #d95f02  the albedo channel        (= nbs.plots.C_ALBEDO)
    ROLE_RISK    #b2182b  disturbance and its risk
    ROLE_CLIMATE #1a2320  balance and climate response -- the deck's ink
    ROLE_TIME    #7a7a7a  time and integration variables

The first two are the same values the result figures use for the same two
channels, so the green in an equation and the green curve are one statement.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lxml import etree

M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
A14 = "http://schemas.microsoft.com/office/drawing/2010/main"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NSMAP = {"m": M, "a": A, "a14": A14, "mc": MC, "p": P}

ROLE_CARBON = "1B7837"
ROLE_ALBEDO = "D95F02"
ROLE_RISK = "B2182B"
ROLE_CLIMATE = "1A2320"
ROLE_TIME = "7A7A7A"

ROLE_LABELS_DE: dict[str, str] = {
    ROLE_CARBON: "Kohlenstoff im Baum",
    ROLE_ALBEDO: "Albedo und Strahlung",
    ROLE_RISK: "Störung und Risiko",
    ROLE_CLIMATE: "Bilanz und Klimaantwort",
    ROLE_TIME: "Zeit",
}

DEFAULT_SIZE = 2400
"""Font size in hundredths of a point, matching the deck's equations (24 pt)."""


def _q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def _rpr(role: str, *, italic: bool, size: int) -> etree._Element:
    """The run properties PowerPoint writes for a math run, with our colour."""
    rpr = etree.Element(_q(A, "rPr"), nsmap=NSMAP)
    rpr.set("lang", "de-DE")
    rpr.set("sz", str(size))
    rpr.set("b", "1")
    rpr.set("i", "1" if italic else "0")
    rpr.set("dirty", "0")
    fill = etree.SubElement(rpr, _q(A, "solidFill"))
    clr = etree.SubElement(fill, _q(A, "srgbClr"))
    clr.set("val", role)
    latin = etree.SubElement(rpr, _q(A, "latin"))
    latin.set("typeface", "Cambria Math")
    latin.set("panose", "02040503050406030204")
    latin.set("pitchFamily", "18")
    latin.set("charset", "0")
    return rpr


def _ctrl(role: str, size: int) -> etree._Element:
    ctrl = etree.Element(_q(M, "ctrlPr"), nsmap=NSMAP)
    ctrl.append(_rpr(role, italic=True, size=size))
    return ctrl


# ---------------------------------------------------------------------------
# Expression tree
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Node:
    """Base class; every node knows how to emit its OMML elements."""

    def emit(self, size: int) -> list[etree._Element]:  # pragma: no cover
        raise NotImplementedError


@dataclass(frozen=True)
class R(Node):
    """A run of literal characters in one colour.

    ``italic`` defaults to True for anything that is not an operator or a
    number, which is the convention PowerPoint's equation editor follows.
    """

    text: str
    role: str = ROLE_CLIMATE
    italic: bool | None = None

    def _italic(self) -> bool:
        if self.italic is not None:
            return self.italic
        stripped = self.text.strip()
        if not stripped:
            return False
        return not all(ch in "0123456789+-−=()[]/,.·:;<>≈±∙ " for ch in stripped)

    def emit(self, size: int) -> list[etree._Element]:
        r = etree.Element(_q(M, "r"), nsmap=NSMAP)
        r.append(_rpr(self.role, italic=self._italic(), size=size))
        t = etree.SubElement(r, _q(M, "t"))
        t.text = self.text
        # Leading/trailing spaces are meaningful in a formula and would
        # otherwise be normalised away by the XML writer.
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return [r]


@dataclass(frozen=True)
class Seq(Node):
    """Several nodes side by side."""

    parts: tuple[Node, ...]

    def __init__(self, *parts: Node):
        object.__setattr__(self, "parts", tuple(parts))

    def emit(self, size: int) -> list[etree._Element]:
        out: list[etree._Element] = []
        for part in self.parts:
            out.extend(part.emit(size))
        return out


def _wrap(tag: str, size: int, role: str, children: dict[str, Node]) -> etree._Element:
    el = etree.Element(_q(M, tag), nsmap=NSMAP)
    pr = etree.SubElement(el, _q(M, f"{tag}Pr"))
    pr.append(_ctrl(role, size))
    for name, node in children.items():
        sub = etree.SubElement(el, _q(M, name))
        for child in node.emit(size):
            sub.append(child)
    return el


@dataclass(frozen=True)
class Sub(Node):
    """Subscript: ``base_sub``."""

    base: Node
    sub: Node
    role: str = ROLE_CLIMATE

    def emit(self, size: int) -> list[etree._Element]:
        return [_wrap("sSub", size, self.role, {"e": self.base, "sub": self.sub})]


@dataclass(frozen=True)
class Sup(Node):
    """Superscript: ``base^sup``."""

    base: Node
    sup: Node
    role: str = ROLE_CLIMATE

    def emit(self, size: int) -> list[etree._Element]:
        return [_wrap("sSup", size, self.role, {"e": self.base, "sup": self.sup})]


@dataclass(frozen=True)
class Frac(Node):
    """A built-up fraction."""

    num: Node
    den: Node
    role: str = ROLE_CLIMATE

    def emit(self, size: int) -> list[etree._Element]:
        return [_wrap("f", size, self.role, {"num": self.num, "den": self.den})]


@dataclass(frozen=True)
class Dot(Node):
    """An overdot accent -- the time derivative the whole talk is built on."""

    base: Node
    role: str = ROLE_CLIMATE

    def emit(self, size: int) -> list[etree._Element]:
        acc = etree.Element(_q(M, "acc"), nsmap=NSMAP)
        pr = etree.SubElement(acc, _q(M, "accPr"))
        chr_el = etree.SubElement(pr, _q(M, "chr"))
        chr_el.set(_q(M, "val"), "̇")
        pr.append(_ctrl(self.role, size))
        e = etree.SubElement(acc, _q(M, "e"))
        for child in self.base.emit(size):
            e.append(child)
        return [acc]


@dataclass(frozen=True)
class Delim(Node):
    """Parentheses that grow with their content."""

    inner: Node
    role: str = ROLE_CLIMATE
    beg: str = "("
    end: str = ")"

    def emit(self, size: int) -> list[etree._Element]:
        d = etree.Element(_q(M, "d"), nsmap=NSMAP)
        pr = etree.SubElement(d, _q(M, "dPr"))
        if self.beg != "(":
            b = etree.SubElement(pr, _q(M, "begChr"))
            b.set(_q(M, "val"), self.beg)
        if self.end != ")":
            e2 = etree.SubElement(pr, _q(M, "endChr"))
            e2.set(_q(M, "val"), self.end)
        pr.append(_ctrl(self.role, size))
        e = etree.SubElement(d, _q(M, "e"))
        for child in self.inner.emit(size):
            e.append(child)
        return [d]


@dataclass(frozen=True)
class Nary(Node):
    """A big operator with limits: integral, sum.

    The operator itself is the ``op`` character; there is deliberately no
    separate node for it, because OMML takes it as an attribute of the nary
    element rather than as a run.
    """

    sub: Node
    sup: Node
    body: Node
    role: str = ROLE_CLIMATE
    op: str = "∫"
    limloc: str = "subSup"

    def emit(self, size: int) -> list[etree._Element]:
        nary = etree.Element(_q(M, "nary"), nsmap=NSMAP)
        pr = etree.SubElement(nary, _q(M, "naryPr"))
        chr_el = etree.SubElement(pr, _q(M, "chr"))
        chr_el.set(_q(M, "val"), self.op)
        loc = etree.SubElement(pr, _q(M, "limLoc"))
        loc.set(_q(M, "val"), self.limloc)
        pr.append(_ctrl(self.role, size))
        for name, node in (("sub", self.sub), ("sup", self.sup), ("e", self.body)):
            el = etree.SubElement(nary, _q(M, name))
            for child in node.emit(size):
                el.append(child)
        return [nary]


# ---------------------------------------------------------------------------
# Placing an equation on a slide
# ---------------------------------------------------------------------------


def build_omath(node: Node, *, size: int = DEFAULT_SIZE) -> etree._Element:
    """One ``<m:oMath>`` element for *node*."""
    omath = etree.Element(_q(M, "oMath"), nsmap=NSMAP)
    for child in node.emit(size):
        omath.append(child)
    return omath


def paragraph_with_math(node: Node, *, size: int = DEFAULT_SIZE,
                        align: str = "ctr") -> etree._Element:
    """An ``<a:p>`` holding one centred equation, ready to append to a txBody.

    The nesting matters and is not guessable: PowerPoint writes
    ``a:p > a14:m > m:oMathPara > m:oMath``. The ``a14:m`` wrapper is the
    piece that is easy to miss -- without it the XML is still well formed and
    still saves, but no renderer shows the equation at all. This is exactly
    how the deck's own equations are stored; ``tests/test_omml.py`` compares
    against one of them.
    """
    p = etree.Element(_q(A, "p"), nsmap=NSMAP)
    ppr = etree.SubElement(p, _q(A, "pPr"))
    ppr.set("algn", align)
    spc = etree.SubElement(ppr, _q(A, "spcBef"))
    pts = etree.SubElement(spc, _q(A, "spcPts"))
    pts.set("val", "180")
    wrapper = etree.SubElement(p, _q(A14, "m"))
    para = etree.SubElement(wrapper, _q(M, "oMathPara"))
    props = etree.SubElement(para, _q(M, "oMathParaPr"))
    just = etree.SubElement(props, _q(M, "jc"))
    just.set(_q(M, "val"), "centerGroup")
    para.append(build_omath(node, size=size))
    return p


def flatten(node: "Node") -> list[tuple[str, str]]:
    """Linear ``(text, role)`` fragments for the fallback branch.

    A PowerPoint equation is stored twice: once as real math for readers that
    understand it, and once as plain text for readers that do not. Everything
    that is not PowerPoint -- LibreOffice, the PDF export this project checks
    its slides with, most viewers -- shows the second one. So the fallback is
    not a formality; for a good part of the audience it *is* the formula, and
    it carries the same colour code.
    """
    if isinstance(node, R):
        return [(node.text, node.role)]
    if isinstance(node, Seq):
        out: list[tuple[str, str]] = []
        for part in node.parts:
            out.extend(flatten(part))
        return out
    if isinstance(node, Sub):
        return flatten(node.base) + [("_", node.role)] + flatten(node.sub)
    if isinstance(node, Sup):
        return flatten(node.base) + [("^", node.role)] + flatten(node.sup)
    if isinstance(node, Frac):
        return ([("(", node.role)] + flatten(node.num) + [(")/(", node.role)]
                + flatten(node.den) + [(")", node.role)])
    if isinstance(node, Dot):
        inner = flatten(node.base)
        if inner:
            head, role = inner[0]
            inner = [(head + "\u0307", role)] + inner[1:]
        return inner
    if isinstance(node, Delim):
        return [(node.beg, node.role)] + flatten(node.inner) + [(node.end, node.role)]
    if isinstance(node, Nary):
        out = [(node.op, node.role)]
        # A sum usually carries only a lower limit; emitting a bare "^" for the
        # missing upper one puts a stray caret on the slide.
        sub, sup = flatten(node.sub), flatten(node.sup)
        if any(text.strip() for text, _ in sub):
            out += [("_", node.role)] + sub
        if any(text.strip() for text, _ in sup):
            out += [("^", node.role)] + sup
        return out + [(" ", node.role)] + flatten(node.body)
    raise TypeError(f"kein Fallback fuer {type(node).__name__}")


def fallback_paragraph(node: "Node", *, size: int = DEFAULT_SIZE,
                       align: str = "ctr") -> etree._Element:
    """An ``<a:p>`` with the formula as coloured plain text."""
    p = etree.Element(_q(A, "p"), nsmap=NSMAP)
    ppr = etree.SubElement(p, _q(A, "pPr"))
    ppr.set("algn", align)
    spc = etree.SubElement(ppr, _q(A, "spcBef"))
    pts = etree.SubElement(spc, _q(A, "spcPts"))
    pts.set("val", "180")
    for text, role in flatten(node):
        if not text:
            continue
        r = etree.SubElement(p, _q(A, "r"))
        rpr = etree.SubElement(r, _q(A, "rPr"))
        rpr.set("lang", "de-DE")
        rpr.set("sz", str(size))
        rpr.set("b", "1")
        rpr.set("dirty", "0")
        fill = etree.SubElement(rpr, _q(A, "solidFill"))
        clr = etree.SubElement(fill, _q(A, "srgbClr"))
        clr.set("val", role)
        # Deliberately no <a:latin typeface="Cambria Math"> here. In the math
        # branch that font is right; in the fallback it makes readers outside
        # PowerPoint substitute a font whose glyph slots differ, and "+" and
        # "−" came out as a dagger and a middle dot. The theme font renders
        # them correctly.
        t = etree.SubElement(r, _q(A, "t"))
        t.text = text
    return p


def label_paragraph(text: str, *, size: int = 1400,
                    role: str = ROLE_TIME) -> etree._Element:
    """A small centred caption line above a formula step."""
    p = etree.Element(_q(A, "p"), nsmap=NSMAP)
    ppr = etree.SubElement(p, _q(A, "pPr"))
    ppr.set("algn", "ctr")
    r = etree.SubElement(p, _q(A, "r"))
    rpr = etree.SubElement(r, _q(A, "rPr"))
    rpr.set("lang", "de-DE")
    rpr.set("sz", str(size))
    rpr.set("dirty", "0")
    fill = etree.SubElement(rpr, _q(A, "solidFill"))
    clr = etree.SubElement(fill, _q(A, "srgbClr"))
    clr.set("val", role)
    t = etree.SubElement(r, _q(A, "t"))
    t.text = text
    return p


__all__ = [
    "A",
    "MC",
    "P",
    "A14",
    "DEFAULT_SIZE",
    "M",
    "Delim",
    "Dot",
    "Frac",
    "Nary",
    "Node",
    "R",
    "ROLE_ALBEDO",
    "ROLE_CARBON",
    "ROLE_CLIMATE",
    "ROLE_LABELS_DE",
    "ROLE_RISK",
    "ROLE_TIME",
    "Seq",
    "Sub",
    "Sup",
    "build_omath",
    "fallback_paragraph",
    "flatten",
    "label_paragraph",
    "paragraph_with_math",
]
