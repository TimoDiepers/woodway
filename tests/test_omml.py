"""The equation builder, checked against the deck's own PowerPoint equations.

Everything here exists because the first attempt produced XML that was well
formed, saved without complaint, and displayed nothing at all. Structure is
the thing to pin, not appearance.
"""

import unicodedata
from pathlib import Path

import pytest
from lxml import etree

from nbs.omml import (
    A,
    A14,
    M,
    Delim,
    Dot,
    Frac,
    Nary,
    R,
    ROLE_ALBEDO,
    ROLE_CARBON,
    ROLE_CLIMATE,
    ROLE_RISK,
    ROLE_TIME,
    Seq,
    Sub,
    Sup,
    build_omath,
    fallback_paragraph,
    flatten,
    paragraph_with_math,
)

DECK = Path("docs/slides/dissvortrag.pptx")


def test_paragraph_nests_the_a14_wrapper():
    """a:p > a14:m > m:oMathPara > m:oMath. Without the a14:m wrapper the
    file still saves and no renderer shows the equation -- the exact failure
    this test exists to prevent."""
    p = paragraph_with_math(R("m", ROLE_CARBON))
    assert etree.QName(p).localname == "p"
    wrapper = p.find(f"{{{A14}}}m")
    assert wrapper is not None, "a14:m fehlt — die Formel wäre unsichtbar"
    para = wrapper.find(f"{{{M}}}oMathPara")
    assert para is not None
    assert para.find(f"{{{M}}}oMath") is not None


def test_every_run_carries_its_colour():
    expr = Seq(R("m", ROLE_CARBON), R(" = ", ROLE_CLIMATE), R("α", ROLE_ALBEDO))
    omath = build_omath(expr)
    colours = [c.get("val") for c in omath.findall(f".//{{{A}}}srgbClr")]
    assert colours == [ROLE_CARBON, ROLE_CLIMATE, ROLE_ALBEDO]


def test_operators_are_upright_and_letters_italic():
    """PowerPoint's own equations set variables italic and operators upright;
    matching that is what makes a generated equation look native."""
    omath = build_omath(Seq(R("m", ROLE_CARBON), R(" = ", ROLE_CLIMATE)))
    italics = [r.get("i") for r in omath.findall(f".//{{{A}}}rPr")]
    assert italics == ["1", "0"]


def test_nary_without_an_upper_limit_emits_no_caret():
    """A sum carries only a lower limit. An unconditional "^" put a stray
    caret on the slide."""
    total = Nary(R("i", ROLE_TIME), R("", ROLE_CLIMATE), R("x", ROLE_CLIMATE),
                 ROLE_CLIMATE, op="∑")
    text = "".join(t for t, _ in flatten(total))
    assert "^" not in text
    assert "_" in text


def test_fallback_reproduces_the_formula_as_text():
    expr = Seq(Sub(Dot(R("m", ROLE_CARBON), ROLE_CARBON), R("CO₂", ROLE_CARBON), ROLE_CARBON),
               R(" = ", ROLE_CLIMATE),
               Frac(R("44", ROLE_CARBON), R("12", ROLE_CARBON), ROLE_CARBON))
    # The dot is a combining accent (m + U+0307), not the precomposed ṁ, so
    # the comparison has to normalise before it means anything.
    text = unicodedata.normalize("NFC", "".join(t for t, _ in flatten(expr)))
    assert text.startswith(unicodedata.normalize("NFC", "ṁ_CO₂"))
    assert "(44)/(12)" in text


def test_fallback_runs_do_not_force_cambria_math():
    """In the fallback branch that font makes readers outside PowerPoint
    substitute glyphs, and "+" came out as a dagger."""
    p = fallback_paragraph(Seq(R("a", ROLE_CARBON), R(" + ", ROLE_CLIMATE)))
    assert p.findall(f".//{{{A}}}latin") == []


def test_math_runs_do_use_cambria_math():
    omath = build_omath(R("m", ROLE_CARBON))
    faces = [el.get("typeface") for el in omath.findall(f".//{{{A}}}latin")]
    assert faces == ["Cambria Math"]


def test_no_empty_subscript_bases():
    """An sSub with an empty base renders as an empty box in PowerPoint. The
    dotted symbols must be built as Sub(Dot(x), i), not Dot(x) then Sub("", i)."""
    good = Sub(Dot(R("m", ROLE_RISK), ROLE_RISK), R("Stör", ROLE_RISK), ROLE_RISK)
    omath = build_omath(good)
    for base in omath.findall(f".//{{{M}}}e"):
        assert len(base) > 0, "leere Basis in sSub"


def test_delimiters_and_superscripts_build():
    expr = Sup(Delim(Seq(R("1 − ", ROLE_CLIMATE), R("x", ROLE_CARBON)), ROLE_CLIMATE),
               R("p", ROLE_CARBON), ROLE_CLIMATE)
    omath = build_omath(expr)
    assert omath.findall(f".//{{{M}}}d")
    assert omath.findall(f".//{{{M}}}sSup")


@pytest.mark.skipif(not DECK.exists(), reason="Foliensatz nicht vorhanden")
def test_generated_nesting_matches_the_decks_own_equations():
    """The deck holds equations PowerPoint itself wrote. The generated ones
    must sit in the same chain of elements, or PowerPoint will not treat them
    as equations."""
    from pptx import Presentation

    prs = Presentation(str(DECK))
    chains = set()
    for slide in prs.slides:
        for omath in slide.shapes._spTree.findall(f".//{{{M}}}oMath"):
            node, chain = omath, []
            for _ in range(4):
                chain.append(etree.QName(node).localname)
                node = node.getparent()
            chains.add(tuple(chain))
    assert chains, "keine Gleichung im Foliensatz gefunden"
    assert ("oMath", "oMathPara", "m", "p") in chains

    generated = paragraph_with_math(R("m", ROLE_CARBON))
    omath = generated.findall(f".//{{{M}}}oMath")[0]
    node, chain = omath, []
    for _ in range(4):
        chain.append(etree.QName(node).localname)
        node = node.getparent()
    assert tuple(chain) == ("oMath", "oMathPara", "m", "p")
