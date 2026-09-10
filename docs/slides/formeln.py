# -*- coding: utf-8 -*-
"""Every equation in the derivation part, as native PowerPoint math.

Run it to rewrite the deck's formulas:

    uv run python docs/slides/formeln.py                 # das echte Deck
    uv run python docs/slides/formeln.py --deck /tmp/x.pptx

Two things happen. Slides that carried LaTeX *source* as plain text get real
``<m:oMath>`` equations instead, built by ``nbs.omml``. And every equation in
the derivation part -- the new ones and the ones PowerPoint already held --
is recoloured to one code, so a symbol looks the same wherever it appears and
matches the curve colours in the result figures.

The colour code is defined once, in ``nbs.omml``; this file only says which
symbol belongs to which role.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from lxml import etree  # noqa: E402
from pptx.util import Pt  # noqa: E402

from copy import deepcopy  # noqa: E402

from nbs.omml import (  # noqa: E402
    A, M, MC, P, DEFAULT_SIZE, Delim, Dot, Frac, Nary, R, ROLE_ALBEDO, ROLE_CARBON,
    ROLE_CLIMATE, ROLE_RISK, ROLE_TIME, Seq, Sub, Sup, fallback_paragraph,
    label_paragraph, paragraph_with_math,
)
from pptx_tools import (  # noqa: E402
    DECK_PATH, backup, check_not_locked, open_deck, save_deck, verify_deck,
)

CB, AL, RI, CL, TI = ROLE_CARBON, ROLE_ALBEDO, ROLE_RISK, ROLE_CLIMATE, ROLE_TIME


def op(text: str) -> R:
    return R(text, CL, italic=False)


def t_(role: str = TI) -> Seq:
    return Seq(op("("), R("t", role), op(")"))


# --- die Bilanz, Folie 7-10 -------------------------------------------------
# Diese vier Folien tragen bereits einen eigenen Farbcode: die nummerierten
# Symbole und ihre Beschriftungen haben je Prozess eine Farbe. Die Formel
# folgt hier diesem lokalen Code statt dem kanalweiten, damit Term und Symbol
# sichtbar zusammengehoeren. Die vier Farben sind aus den Folien selbst
# ausgelesen, nicht neu erfunden.
PROC_PHOTO = "347B52"
PROC_RESP = "436CA2"
PROC_ZER = "8E547F"
PROC_STOER = "EC3327"


def balance(n_terms: int) -> Seq:
    parts = [R("m", CB), op(" = "), Sub(R("m", PROC_PHOTO), R("Photo", PROC_PHOTO), PROC_PHOTO)]
    for label, role in (("Res", PROC_RESP), ("Zer", PROC_ZER), ("Stör", PROC_STOER))[: n_terms - 1]:
        parts += [op(" − "), Sub(R("m", role), R(label, role), role)]
    return Seq(*parts)


# --- Folie 12: Wachstum und Störung ----------------------------------------
GROWTH = Seq(
    R("m", CB), t_(), op(" = "), Sub(R("m", CB), R("max", CB), CB),
    Sup(Delim(Seq(op("1 − "), Sup(R("e", CL), Seq(op("−"), R("k", CB), R("t", TI)), CL)), CL),
        R("p", CB), CL),
)
DISTURB = Seq(
    Sub(Dot(R("m", RI), RI), R("Stör", RI), RI), t_(),
    op(" = "), Sub(R("p", RI), R("Stör", RI), RI), op("("), R("T", CL), op(")"),
    R(" m", CB), t_(),
    op("        mit        "),
    Sub(R("p", RI), R("Stör", RI), RI), op("("), R("T", CL), op(")"), op(" = "),
    Sub(R("p", RI), R("0", RI, italic=False), RI),
    Sup(R("e", CL), Seq(R("γ", RI), R("T", CL)), CL),
)

# --- Folie 13: vom Baum in die Luft ----------------------------------------
FLUX = Seq(
    Sub(Dot(R("m", CB), CB), R("CO₂", CB), CB), t_(),
    op(" = − "), Frac(R("44", CB, italic=False), R("12", CB, italic=False), CB),
    op(" "), Dot(R("m", CB), CB), t_(),
)
GAP = Seq(
    op("Δ"), Sub(R("m", CB), R("CO₂", CB), CB), t_(), op(" = "),
    Nary(R("0", TI, italic=False), R("t", TI),
         Seq(Sub(R("g", CB), R("C", CB), CB),
             op("("), R("t", TI), op(" − "), R("t′", TI), op(")"), op(" "),
             Sub(Dot(R("m", CB), CB), R("CO₂", CB), CB),
             op("("), R("t′", TI), op(")"), op(" d"), R("t′", TI)),
         CL, op="∫"),
)

# --- Folie 24: vom Antrieb zur Temperatur -----------------------------------
RESPONSE = Seq(
    R("T", CL), t_(), op(" = "),
    Nary(R("0", TI, italic=False), R("t", TI),
         Seq(Sub(R("g", CL), R("T", CL), CL),
             op("("), R("t", TI), op(" − "), R("t′", TI), op(")"), op(" "),
             R("φ", CL), op("("), R("t′", TI), op(")"), op(" d"), R("t′", TI)),
         CL, op="∫"),
)

# --- Folie 17: erster Hauptsatz --------------------------------------------
FIRST_LAW = Seq(
    Frac(Seq(op("d("), R("U", CL), op(" + "), Sub(R("E", CL), R("a", CL), CL), op(")")),
         Seq(op("d"), R("t", TI)), CL),
    op(" = "),
    Nary(R("i", TI), R("", CL),
         Seq(Sub(Dot(R("m", CL), CL), R("i", TI), CL), op(" "),
             Delim(Seq(Sub(R("h", CL), R("i", TI), CL), op(" + "),
                       Sub(R("e", CL), R("a,i", TI), CL)), CL)),
         CL, op="∑", limloc="undOvr"),
    op(" + "),
    Nary(R("j", TI), R("", CL),
         Seq(Sub(Dot(R("Q", CL), CL), R("j", TI), CL)), CL, op="∑", limloc="undOvr"),
    op(" + "),
    Nary(R("k", TI), R("", CL),
         Seq(Sub(Dot(R("W", CL), CL), R("k", TI), CL)), CL, op="∑", limloc="undOvr"),
)
RADIATION_3 = Seq(
    Frac(Seq(op("d"), R("U", CL)), Seq(op("d"), R("t", TI)), CL), op(" = "),
    Sub(Dot(R("Q", AL), AL), R("SW", AL), AL), op(" − "),
    Sub(Dot(R("Q", AL), AL), R("SW,refl", AL), AL), op(" − "),
    Sub(Dot(R("Q", CL), CL), R("lang", CL), CL),
)
RADIATION_2 = Seq(
    Frac(Seq(op("d"), R("U", CL)), Seq(op("d"), R("t", TI)), CL), op(" = "),
    Sub(Dot(R("Q", AL), AL), R("kurz", AL), AL), op(" − "),
    Sub(Dot(R("Q", CL), CL), R("lang", CL), CL),
)

# --- Folie 18: vom Watt zum Grad -------------------------------------------
TANGENT = Seq(
    Sub(Dot(R("Q", CL), CL), R("lang", CL), CL), op("("), R("T", CL), op(")"),
    op(" ≈ "), Sub(Dot(R("Q", CL), CL), R("lang", CL), CL),
    op("("), Sub(R("T", CL), R("0", CL, italic=False), CL), op(")"), op(" + "),
    R("Λ", CL), op(" "), R("T", CL),
)
BALANCE_LIN = Seq(
    Frac(Seq(op("d"), R("U", CL)), Seq(op("d"), R("t", TI)), CL), op(" = "),
    R("φ", CL), t_(), op(" − "), R("Λ", CL), op(" "), R("T", CL), t_(),
)
TEMPERATURE = Seq(
    R("C", CL), op(" "),
    Frac(Seq(op("d"), R("T", CL)), Seq(op("d"), R("t", TI)), CL), op(" = "),
    R("φ", CL), t_(), op(" − "), R("Λ", CL), op(" "), R("T", CL), t_(),
)

# slide index (1-based) -> (marker in the LaTeX text box, [equations], size)
REPLACEMENTS: dict[int, tuple[str, list, int]] = {
    7: ("m = m_", [balance(1)], 2400),
    8: ("m = m_", [balance(2)], 2400),
    9: ("m = m_", [balance(3)], 2400),
    10: ("m = m_", [balance(4)], 2400),
    12: ("m(t) = m_{max}", [GROWTH, DISTURB], 2000),
    13: ("\\dot m_{CO_2}", [FLUX, GAP], 2000),
    17: ("\\frac{d(U + E_a)}", [FIRST_LAW], 1800),
    24: ("T(t) = \\int_0^t g_T", [RESPONSE], 2000),
}

STEP_REPLACEMENTS: dict[int, tuple[str, list[tuple[str, object]], int]] = {
    17: ("① nur Strahlung", [
        ("① nur Strahlung überquert die Grenze — drei Terme", RADIATION_3),
        ("② Reflexion und Absorption zusammengefasst", RADIATION_2),
    ], 1800),
    18: ("① Tangente", [
        ("① Tangente an die Abstrahlung", TANGENT),
        ("② Gleichgewichtszustand abziehen — die konstanten Terme heben sich weg", BALANCE_LIN),
        ("③ Wärmekapazität als Brücke von der Energie zur Temperatur:  U = C · T", TEMPERATURE),
    ], 1800),
}

# Which colour a symbol carries when recolouring the equations PowerPoint
# already held (slides 11, 14, 21, 22). Longest match wins.
SYMBOL_ROLES: list[tuple[str, str]] = [
    ("Stör", RI), ("Photo", CB), ("Res", CB), ("Zer", CB),
    ("Baum", AL), ("Erde", AL), ("kurz", AL), ("atm", AL), ("Wald", AL),
    ("offen", AL), ("α", AL), ("τ", AL), ("q", AL), ("f", AL),
    ("CO", CB), ("m", CB), ("Δ", CB),
    ("φ", CL), ("Λ", CL), ("T", CL), ("U", CL), ("Q", CL), ("A", CB),
    ("t", TI),
]


def role_for(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return None
    for needle, role in SYMBOL_ROLES:
        if needle in stripped:
            return role
    return None


def recolour_existing(slide) -> int:
    """Give the equations PowerPoint already held the same colour code."""
    changed = 0
    for omath in slide.shapes._spTree.findall(f".//{{{M}}}oMath"):
        for run in omath.findall(f".//{{{M}}}r"):
            t = run.find(f"{{{M}}}t")
            if t is None:
                continue
            role = role_for(t.text or "")
            if role is None:
                continue
            for clr in run.findall(f".//{{{A}}}srgbClr"):
                clr.set("val", role)
                changed += 1
    return changed


def _fill_txbody(sp, blocks, size: int, *, math: bool) -> None:
    """Replace a shape's paragraphs with the formula, in one of the two branches."""
    # Shapes carry <p:txBody>, not <a:txBody> -- the paragraphs inside it are
    # the ones in the a: namespace.
    txbody = sp.find(f"{{{P}}}txBody")
    for p in txbody.findall(f"{{{A}}}p"):
        txbody.remove(p)
    make = paragraph_with_math if math else fallback_paragraph
    for block in blocks:
        if isinstance(block, tuple):
            label, expr = block
            txbody.append(label_paragraph(label))
            txbody.append(make(expr, size=size))
        else:
            txbody.append(make(block, size=size))


def _replace_textbox(slide, marker: str, blocks, size: int) -> bool:
    """Swap a LaTeX text box for real equations, keeping its position.

    The shape is replaced by an ``mc:AlternateContent`` pair, exactly as
    PowerPoint stores its own equations: ``mc:Choice`` holds the OMML that
    PowerPoint renders, ``mc:Fallback`` the coloured plain-text version every
    other reader shows. Writing only the Choice branch produces a file that
    saves cleanly and displays nothing outside PowerPoint -- which is how the
    first attempt at this failed.
    """
    target = None
    for shape in slide.shapes:
        if shape.has_text_frame and marker in shape.text_frame.text:
            target = shape
            break
    if target is None:
        return False

    sp = target._element
    parent = sp.getparent()
    alt = etree.Element(f"{{{MC}}}AlternateContent", nsmap={"mc": MC})
    choice = etree.SubElement(alt, f"{{{MC}}}Choice")
    choice.set("Requires", "a14")
    fallback = etree.SubElement(alt, f"{{{MC}}}Fallback")

    sp_math = deepcopy(sp)
    sp_text = deepcopy(sp)
    _fill_txbody(sp_math, blocks, size, math=True)
    _fill_txbody(sp_text, blocks, size, math=False)
    choice.append(sp_math)
    fallback.append(sp_text)

    parent.replace(sp, alt)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck", type=Path, default=DECK_PATH)
    args = parser.parse_args()

    if args.deck == DECK_PATH:
        check_not_locked()
        backup("formeln_omml")
    prs = open_deck(deck_path=args.deck)
    slides = list(prs.slides)

    for idx, (marker, blocks, size) in REPLACEMENTS.items():
        ok = _replace_textbox(slides[idx - 1], marker, blocks, size)
        print(f"  Folie {idx:2d}: Formel gesetzt" if ok else f"  Folie {idx:2d}: MARKER FEHLT")
    for idx, (marker, steps, size) in STEP_REPLACEMENTS.items():
        ok = _replace_textbox(slides[idx - 1], marker, steps, size)
        print(f"  Folie {idx:2d}: Schritte gesetzt" if ok else f"  Folie {idx:2d}: MARKER FEHLT")

    total = 0
    for i, slide in enumerate(slides, 1):
        if i > 43:
            break
        total += recolour_existing(slide)
    print(f"  Farbcode auf {total} Läufe angewandt")

    save_deck(prs, deck_path=args.deck)
    print("Folien:", verify_deck(args.deck))


if __name__ == "__main__":
    main()
