"""Build docs/slides/dissvortrag_v2.pptx from dissvortrag.pptx following
docs/slides/dissvortrag-storyline-v2.md (expanding system boundary).

    .venv/bin/python scripts/build_storyline_v2_deck.py

Idempotent: every run starts from a fresh copy of the original deck, which is
only read, never written. House rules of this deck (see pptx_tools):
nothing is deleted -- cut slides move to the backup; new slides take their
layout from a neighbour of the same chapter; formulas are LaTeX text only,
never OMML and never rendered; work-in-progress notes become speaker notes.
"""

from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.util import Emu, Inches, Pt  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pptx_tools as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "slides" / "dissvortrag.pptx"
OUT = ROOT / "docs" / "slides" / "dissvortrag_v2.pptx"
FIG = ROOT / "docs" / "slides" / "figures"
# Every model number quoted in a text comes from here (scripts/export_slide_facts.py).
FAKTEN = json.loads((ROOT / "docs" / "slides" / "chart_data" / "fakten.json").read_text())
AC, JO = FAKTEN["orte"]["Aachen"], FAKTEN["orte"]["Joensuu"]
KA, UM, KARTEN, HA = FAKTEN["kaskade"], FAKTEN["umkehr"], FAKTEN["karten"], FAKTEN["hasler"]


def de(value: float, digits: int = 1) -> str:
    """German decimal comma."""
    return f"{value:.{digits}f}".replace(".", ",")


def pct(share: float, digits: int = 0) -> str:
    return de(100.0 * share, digits) + " %"


def share_words(share: float) -> str:
    """A share in words, for spoken text."""
    for limit, words in ((0.3, "knapp ein Drittel"), (0.37, "gut ein Drittel"), (0.45, "fast die Hälfte"),
                         (0.55, "rund die Hälfte"), (0.62, "gut die Hälfte"), (0.7, "fast zwei Drittel"),
                         (0.8, "rund drei Viertel")):
        if share < limit:
            return words
    return "fast alle"


JO_KUEHLT = JO["t_star"] is not None  # Joensuu: net cooling before 2150?
BA = FAKTEN["baeume"]["orte"]  # typical forest at both sites (nbs.forest_data)
B_AC, B_JO = BA["Aachen"], BA["Joensuu"]


def ab_wann(t_star) -> str:
    """'vom ersten Jahr an' / 'ab 2031' / 'nicht vor 2150' -- for 'kühlt ... '."""
    if t_star is None:
        return "nicht vor 2150"
    return "vom ersten Jahr an" if t_star <= 2025 else f"ab {t_star}"


def co2_ab(last_light_year) -> str:
    """When CO2 overtakes the light in the tree-only accounting (B10)."""
    return "vom ersten Jahr an" if last_light_year is None else f"ab {last_light_year + 1}"


def both(fn, a, b) -> str:
    """'an beiden Orten X' when both sites read the same, else 'in Aachen X, in Joensuu Y'."""
    fa, fb = fn(a), fn(b)
    return f"an beiden Orten {fa}" if fa == fb else f"in Aachen {fa}, in Joensuu {fb}"


def sci_de(value: float) -> str:
    """-9.0e-14 -> '−9·10⁻¹⁴' (one significant digit)."""
    sup = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    exp = int(np.floor(np.log10(abs(value))))
    mant = round(value / 10**exp)
    if abs(mant) == 10:
        mant, exp = mant // 10, exp + 1
    return f"{'−' if mant < 0 else ''}{abs(mant)}·10{str(exp).translate(sup)}"



INK = RGBColor(0x1A, 0x23, 0x20)
MUTED = RGBColor(0x5F, 0x6B, 0x66)

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def set_runs(paragraph, text: str) -> None:
    """Replace a paragraph's text, keeping the first run's formatting."""
    runs = paragraph.runs
    if not runs:
        paragraph.add_run().text = text
        return
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def set_title(slide, text: str) -> None:
    set_runs(slide.shapes.title.text_frame.paragraphs[0], text)
    for p in slide.shapes.title.text_frame.paragraphs[1:]:
        p._p.getparent().remove(p._p)


def shape(slide, name: str):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    raise KeyError(f"{name!r} not on slide {slide.shapes.title.text if slide.shapes.title else '?'}")


def remove_shape(slide, sh) -> None:
    sh._element.getparent().remove(sh._element)


def add_notes(slide, text: str, *, prepend: bool = True) -> None:
    tf = slide.notes_slide.notes_text_frame
    old = tf.text
    tf.text = (text + ("\n\n" + old if old and prepend else "")) if prepend else (old + "\n\n" + text)


def _next_id(slide) -> int:
    ids = [int(e.get("id")) for e in slide.shapes._spTree.iter() if e.tag.endswith("}cNvPr")]
    return max(ids + [1]) + 1


def clone_box(slide, template, *, x, y, w, h, heading: str | None, body: str):
    """Copy a styled text box (Kurz gesagt / Quelle) onto *slide*."""
    el = copy.deepcopy(template._element)
    el.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr").set("id", str(_next_id(slide)))
    slide.shapes._spTree.append(el)
    sh = slide.shapes[-1]
    sh.left, sh.top, sh.width, sh.height = Inches(x), Inches(y), Inches(w), Inches(h)
    paras = sh.text_frame.paragraphs
    if heading is None:
        set_runs(paras[0], body)
    else:
        set_runs(paras[0], heading)
        set_runs(paras[1], body)
    return sh


def kurz_height(text: str, width_in: float) -> float:
    """Box height [in] for heading + body at 11/13 pt (design-system rule of thumb)."""
    chars_per_line = max(20, int((width_in - 0.3) * 11.3))
    lines, cur = 0, 0
    for word in text.split():
        if cur + len(word) + 1 > chars_per_line:
            lines, cur = lines + 1, len(word)
        else:
            cur += len(word) + 1
    lines += 1
    return 0.25 + 0.19 + lines * 0.215


def kurz(slide, text: str, *, x=6.84, w=6.08, bottom=7.08):
    h = kurz_height(text, w)
    return clone_box(slide, KURZ, x=x, y=bottom - h, w=w, h=h, heading="Kurz gesagt", body=text)


def quelle(slide, text: str, *, x=3.15, y=6.87, w=3.5, h=0.55):
    return clone_box(slide, QUELLE, x=x, y=y, w=w, h=h, heading=None, body=text)


def replace_kurz(slide, text: str, name: str = "Kurz gesagt") -> None:
    sh = shape(slide, name)
    set_runs(sh.text_frame.paragraphs[1], text)
    bottom = (sh.top + sh.height) / 914400
    h = kurz_height(text, sh.width / 914400)
    sh.top, sh.height = Inches(bottom - h), Inches(h)


def picture(slide, path: Path, *, height=4.5, top=1.12):
    if not path.exists():
        raise FileNotFoundError(path)
    pic = slide.shapes.add_picture(str(path), Inches(0), Inches(top), height=Inches(height))
    pic.left = int((PRS.slide_width - pic.width) / 2)
    return pic


def latex(slide, text: str, *, x=0.42, y=5.85, w=6.2, h=0.45, size=16):
    box = T.add_latex_line(slide, text, left=Inches(x), top=Inches(y), width=Inches(w), height=Inches(h),
                           font_size=Pt(size))
    for p in box.text_frame.paragraphs:
        for r in p.runs:
            r.font.color.rgb = INK
    return box


def placeholder(slide, text: str, *, x=1.4, y=1.2, w=10.5, h=4.3):
    """Yellow box: figure not built yet. Visible on purpose."""
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0xFF, 0xF3, 0xCD)
    box.line.color.rgb = RGBColor(0x8A, 0x6D, 0x3B)
    box.line.width = Pt(1)
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = line
        r.font.size = Pt(13 if i else 15)
        r.font.bold = i == 0
        r.font.color.rgb = RGBColor(0x5A, 0x45, 0x1E)
    return box


def note_sticker(slide, text: str, *, x=9.6, y=1.15, w=3.3, h=0.9):
    return placeholder(slide, text, x=x, y=y, w=w, h=h)


def new_slide(ref_slide, title: str):
    """Append a slide with *ref_slide*'s layout (chapter master), title set,
    unused body placeholder removed."""
    s = PRS.slides.add_slide(ref_slide.slide_layout)
    set_title(s, title) if s.shapes.title is not None else None
    for ph in list(s.placeholders):
        if ph.placeholder_format.idx != 0 and not ph.has_text_frame or (ph.placeholder_format.idx != 0
                                                                        and not ph.text_frame.text):
            remove_shape(s, ph)
    return s


def rehang(slide, ref_slide) -> None:
    """Point *slide* at *ref_slide*'s layout (moves it to that chapter's master)."""
    for rel in slide.part.rels.values():
        if rel.reltype == RT.SLIDE_LAYOUT:
            rel._target = ref_slide.slide_layout.part
            return
    raise RuntimeError("slide has no layout relationship")


def unhide(slide) -> None:
    if slide._element.get("show") is not None:
        del slide._element.attrib["show"]


# --------------------------------------------------------------------------
# native equations
# --------------------------------------------------------------------------
# Built the way PowerPoint itself stores an equation (same wrapper as the
# deck's existing ones): mc:AlternateContent with the OMML in mc:Choice
# Requires="a14", and a picture of the formula in mc:Fallback. The OMML is
# not hand-written: pandoc (texmath) converts the LaTeX, we only add the
# PowerPoint run properties. LaTeX source goes to the speaker notes.

import subprocess  # noqa: E402
import tempfile  # noqa: E402

from lxml import etree  # noqa: E402

NS = {
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "a14": "http://schemas.microsoft.com/office/drawing/2010/main",
}
_TMP = Path(tempfile.mkdtemp(prefix="v2eq_"))


def _omml(latex: str):
    md = _TMP / "eq.md"
    docx = _TMP / "eq.docx"
    md.write_text(f"$${latex}$$\n", encoding="utf-8")
    subprocess.run(["pandoc", "-f", "markdown", "-t", "docx", "-o", str(docx), str(md)], check=True)
    import zipfile
    doc = etree.fromstring(zipfile.ZipFile(docx).read("word/document.xml"))
    para = doc.find(".//m:oMathPara", NS)
    if para is None:
        raise ValueError(f"pandoc produced no equation for {latex!r}")
    return para


GREEN, ORANGE, RED, DARK, GREY = "1B7837", "D95F02", "B2182B", "1A2320", "7A7A7A"
"""Colour code of the deck's formulas (commit 593b736): carbon, albedo,
disturbance, balance/climate response, time."""


def _rpr(size: int, color: str, *, italic: bool | None = None, tag: str = "rPr"):
    attrs = dict(lang="en-GB", sz=str(size * 100), b="1")
    if italic is not None:
        attrs["i"] = "1" if italic else "0"
    attrs["dirty"] = "0"
    rpr = etree.Element(f"{{{NS['a']}}}{tag}", **attrs)
    fill = etree.SubElement(rpr, f"{{{NS['a']}}}solidFill")
    etree.SubElement(fill, f"{{{NS['a']}}}srgbClr", val=color)
    etree.SubElement(rpr, f"{{{NS['a']}}}latin", typeface="Cambria Math", panose="02040503050406030204",
                     pitchFamily="18", charset="0")
    return rpr


def _math_italic(ch: str) -> str:
    """The code points PowerPoint itself stores for italic math letters.
    Greek capitals stay plain (Cambria Math renders the italic ones as gaps)."""
    if ch == "h":
        return "\u210e"
    if "a" <= ch <= "z":
        return chr(0x1D44E + ord(ch) - ord("a"))
    if "A" <= ch <= "Z":
        return chr(0x1D434 + ord(ch) - ord("A"))
    if "\u03b1" <= ch <= "\u03c9":
        return chr(0x1D6FC + ord(ch) - 0x3B1)
    return ch


def _tokens(text: str, upright: bool = False) -> list[str]:
    if upright and text.strip().isalpha():  # function names such as ln stay one run
        return [text.strip()]
    out, buf = [], ""
    for ch in text:
        if ch.isdigit() or (ch == "," and buf[-1:].isdigit()):
            buf += ch
            continue
        if buf:
            out.append(buf)
            buf = ""
        if ch != " ":
            out.append(ch)
    if buf:
        out.append(buf)
    return out


def _group_key(run) -> str | None:
    node = run.getparent()
    while node is not None and node.tag != f"{{{NS['m']}}}oMath":
        name = etree.QName(node).localname
        if name in ("sSub", "sSup"):
            base = "".join(node.find("m:e", NS).itertext()).strip()
            part = node.find("m:sub" if name == "sSub" else "m:sup", NS)
            return base + ("_" if name == "sSub" else "^") + "".join(part.itertext()).strip()
        node = node.getparent()
    return None


def style_omml(para, *, size=20, default=DARK, groups=None, runs=None, chars=None, time=GREY):
    """Restyle pandoc OMML like the deck's own equations: bold, math-italic
    letters (i=1), upright digits/operators (i=0), colour by meaning."""
    groups, runs, chars = groups or {}, runs or {}, chars or {}
    # group keys first: restyling a base letter would change the key of its subscript
    plan = [(run, _group_key(run)) for run in para.iter(f"{{{NS['m']}}}r")]
    for run, group in plan:
        t = run.find("m:t", NS)
        text = t.text or ""
        sty = run.find("m:rPr/m:sty", NS)
        upright = sty is not None and sty.get(f"{{{NS['m']}}}val") == "p"
        parent = run.getparent()
        pos = parent.index(run)
        parent.remove(run)
        for k, tok in enumerate(_tokens(text, upright)):
            if group in groups:
                color = groups[group]
            elif text.strip() in runs:
                color = runs[text.strip()]
            elif tok in chars:
                color = chars[tok]
            elif tok in ("t", "′") and time:
                color = time
            else:
                color = default
            has_letter = any(c.isalpha() for c in tok)
            italic = has_letter and not upright
            new = etree.Element(f"{{{NS['m']}}}r")
            if upright and has_letter:  # function names such as ln stay upright
                rp = etree.SubElement(new, f"{{{NS['m']}}}rPr")
                etree.SubElement(rp, f"{{{NS['m']}}}sty", {f"{{{NS['m']}}}val": "p"})
            new.append(_rpr(size, color, italic=italic))
            nt = etree.SubElement(new, f"{{{NS['m']}}}t")
            nt.text = "".join(_math_italic(c) for c in tok) if italic else tok
            parent.insert(pos + k, new)
    # Δ is an operator on what follows: it takes that symbol's colour
    runs_all = list(para.iter(f"{{{NS['m']}}}r"))
    for cur, nxt in zip(runs_all, runs_all[1:]):
        if cur.find("m:t", NS).text == "Δ":
            src = nxt.find("a:rPr/a:solidFill/a:srgbClr", NS)
            cur.find("a:rPr/a:solidFill/a:srgbClr", NS).set("val", src.get("val"))
    return para


def copy_omml(source_slide, index: int):
    """Deep copy of an equation the deck already holds (unchanged style)."""
    paras = list(source_slide._element.iter(f"{{{NS['m']}}}oMathPara"))
    return copy.deepcopy(paras[index])


def _fallback_png(lines: list[str], size: int) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = _TMP / f"eq_{abs(hash(tuple(lines)))}.png"
    fig = plt.figure(figsize=(0.01, 0.01), dpi=200)
    for k, line in enumerate(lines):
        fig.text(0, -k * 0.6, f"${line}$", fontsize=size, color="#1A2320")
    fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.02, transparent=True)
    plt.close(fig)
    return out


def equation(slide, lines, *, x, y, w, h, size=20, align="center", mathtext=None, paras=None, **style):
    """Native PowerPoint equation(s), one paragraph per LaTeX line, styled
    like the deck's own (style_omml); or *paras* copied from the deck."""
    lines = [lines] if isinstance(lines, str) else list(lines)
    sid = _next_id(slide)
    if paras is None:
        paras = []
        for latex in lines:
            para = style_omml(_omml(latex), size=size, **style)
            para.find("m:oMathParaPr/m:jc", NS).set(f"{{{NS['m']}}}val", "centerGroup")
            paras.append(para)
    color = style.get("default", DARK)

    png = _fallback_png(mathtext or lines, size)
    _img_part, rid = slide.part.get_or_add_image_part(str(png))
    from PIL import Image
    iw, ih = Image.open(png).size
    fb_h = min(h, w * ih / iw, ih / 200.0)  # never stretch, never larger than drawn at 200 dpi
    fb_w = fb_h * iw / ih
    fb_x = x if align == "left" else x + (w - fb_w) / 2
    fb_off = dict(x=str(int(Inches(fb_x))), y=str(int(Inches(y + (h - fb_h) / 2))))
    fb_ext = dict(cx=str(int(Inches(fb_w))), cy=str(int(Inches(fb_h))))

    E = lambda tag, **kw: etree.Element(tag, **kw)  # noqa: E731
    ac = etree.Element(f"{{{NS['mc']}}}AlternateContent", nsmap={"mc": NS["mc"], "a14": NS["a14"]})
    choice = etree.SubElement(ac, f"{{{NS['mc']}}}Choice", Requires="a14")
    off = dict(x=str(int(Inches(x))), y=str(int(Inches(y))))
    ext = dict(cx=str(int(Inches(w))), cy=str(int(Inches(h))))
    algn = "l" if align == "left" else "ctr"
    choice.append(etree.fromstring(
        f'<p:sp xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}"><p:nvSpPr><p:cNvPr id="{sid}" name="Formel"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{off["x"]}" y="{off["y"]}"/>'
        f'<a:ext cx="{ext["cx"]}" cy="{ext["cy"]}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f'<a:noFill/></p:spPr><p:txBody><a:bodyPr wrap="square" rtlCol="0"><a:normAutofit/></a:bodyPr>'
        f'<a:lstStyle/></p:txBody></p:sp>'))
    body = choice.find(".//p:txBody", NS)
    for para in paras:
        ap = etree.SubElement(body, f"{{{NS['a']}}}p")
        etree.SubElement(ap, f"{{{NS['a']}}}pPr", algn=algn)
        m = etree.SubElement(ap, f"{{{NS['a14']}}}m")
        m.append(para)
        ap.append(_rpr(size, color, tag="endParaRPr"))
    fallback = etree.SubElement(ac, f"{{{NS['mc']}}}Fallback")
    fallback.append(etree.fromstring(
        f'<p:sp xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}" xmlns:r="{NS["r"]}"><p:nvSpPr>'
        f'<p:cNvPr id="{sid}" name="Formel"/><p:cNvSpPr txBox="1"><a:spLocks noRot="1" noChangeAspect="1" '
        f'noMove="1" noResize="1" noEditPoints="1" noAdjustHandles="1" noChangeArrowheads="1" '
        f'noChangeShapeType="1" noTextEdit="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm>'
        f'<a:off x="{fb_off["x"]}" y="{fb_off["y"]}"/><a:ext cx="{fb_ext["cx"]}" cy="{fb_ext["cy"]}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:blipFill><a:blip r:embed="{rid}"/><a:stretch>'
        f'<a:fillRect/></a:stretch></a:blipFill></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r>'
        f'<a:rPr lang="de-DE"><a:noFill/></a:rPr><a:t> </a:t></a:r></a:p></p:txBody></p:sp>'))
    slide.shapes._spTree.append(ac)
    add_notes(slide, "[v2] Formel (LaTeX): " + "  |  ".join(lines), prepend=False)
    return ac


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

if len(sys.argv) > 1:  # optional output path, e.g. a scratch copy while the real one is open
    OUT = Path(sys.argv[1]).resolve()
T.check_not_locked(deck_path=OUT)  # before the copy: never overwrite a deck PowerPoint has open
shutil.copyfile(SRC, OUT)
PRS = T.open_deck(deck_path=OUT)
ORIG = list(PRS.slides)  # 1-based numbering below: O(n) = ORIG[n-1]


def O(n: int):
    return ORIG[n - 1]


KURZ = shape(O(22), "Kurz gesagt")
QUELLE = shape(O(22), "Quelle")
BAEUME, KLIMA, VERGLEICH = O(12), O(22), O(40)

# ---- Einstieg ------------------------------------------------------------
s4 = O(4)
paras = s4.placeholders[12].text_frame.paragraphs
_sat_t = B_AC["saettigung_kg_co2"] / 1000.0
_need = FAKTEN["vergleich"]["vl_gesamt_gtco2"]
set_runs(paras[0], f"Ein Baum in einem Aachener Mischwald bindet bis zur Sättigung rund {B_AC['saettigung_kg_co2']:.0f} kg "
         f"CO₂ ({B_AC['saettigung_kgc']:.0f} kg Kohlenstoff).")
set_runs(paras[1], f"Gebraucht werden bis 2150 rund {_need:.0f} Gt CO₂ Entnahme (niedrigstes Szenario, Folie 2).")
set_runs(paras[2], f"{_need:.0f} Gt ÷ {de(_sat_t, 2)} t  ≈  {de(_need / _sat_t / 1000.0, 1)} Billionen Bäume — mehr, als heute "
         "auf der Erde stehen.")
set_runs(paras[4], "Diese Rechnung zieht die Grenze um den Baum. Wir ziehen sie Schritt für Schritt weiter, "
         "bis das Klima drin ist — und schauen, was dann von ihr übrig bleibt.")
add_notes(s4, "[v2] Zahl = Modellbaum in Aachen: typischer Wald dort ist Mischwald (Hasler et al. 2024), zusätzlicher "
          "Kohlenstoff je Hektar aus Walker et al. (2022), 2000 Bäume je Hektar. Bedarf wie auf Folie 2 "
          "(CMIP7 Very Low, 655 Gt bis 2150), derselbe, gegen den das Kapitel Vergleich rechnet. Heute stehen rund "
          "3 Billionen Bäume auf der Erde (Crowther et al. 2015, Nature 525, 201). Die nächste Folie zeigt, dass "
          "diese Rechnung so publiziert und politisch wirksam wurde.")
add_notes(O(6), "[v2] Überblick: drei Kapitel = wachsende Systemgrenze. Bäume = ein Baum, Klima = "
          "Kohlenstoffkreislauf und Energiebilanz der Erde, Vergleich = alle Flächen, alle Wege.")

# ---- Bäume (Schale 1) ----------------------------------------------------
s12 = O(12)
sticker = shape(s12, "Rectangle 9533")
remove_shape(s12, sticker)
add_notes(s12, "[v2] Störung am Baum mit fester Rate p₀: der Faktor e^{γ·ΔT} in der Gleichung setzt eine "
          "Erwärmung voraus, die es hier noch nicht gibt — in PowerPoint ausgrauen, eingelöst auf „Die Erwärmung "
          "wirkt auf den Baum zurück“. Danach folgt die Karte der Waldtypen. "
          "Woher die Zahlen kommen: m_max = zusätzlicher Kohlenstoff je Hektar am Ort (Walker et al. 2022, ober- und "
          "unterirdisch, ohne Boden) ÷ 2000 Bäume; k aus der Zuwachsrate der ersten 30 Jahre (Cook-Patton et al. "
          "2020), begrenzt durch Poorter et al. (2016): 90 % der Biomasse nach 66 Jahren. "
          f"Aachen {B_AC['saettigung_kgc']:.0f} kg C je Baum, Joensuu {B_JO['saettigung_kgc']:.0f} kg C.")

s34 = O(34)  # five species -> into Bäume, right after the model slide
rehang(s34, BAEUME)
set_title(s34, "Welcher Wald wo wächst")
for _sh in list(s34.shapes):
    if _sh.has_chart or (_sh.has_text_frame and _sh.text_frame.text.startswith(("Was hier zu sehen ist", "Chapman"))):
        remove_shape(s34, _sh)
picture(s34, FIG / "b5_waldtypen_karte.png", height=4.45)
replace_kurz(s34, "Gepflanzt wird, was dort von Natur aus wächst: der typische Wald je Ort. Aachen und Joensuu "
             "liegen beide im Mischwald — gemäßigt und boreal. Wie viel Kohlenstoff dazukommt, hängt am Ort, "
             "nicht am Waldtyp.", name="TextBox 5")
quelle(s34, "Waldtyp: Hasler et al. 2024 (wahrscheinlichster Wald); Fläche: Walker et al. 2022 (Wiederbewaldung "
       "ohne Acker und Siedlung)", x=0.42, y=6.2, w=6.1)
add_notes(s34, "[v2] Fünf Waldtypen statt fünf gesetzter Arten. Kohlenstoff ist je Ort für alle Typen gleich: Die "
          "IPCC-Tabellen (2019) zeigen keinen belastbaren Unterschied zwischen Typen am selben Ort. Die Typen "
          "unterscheiden sich in der Albedo (Duveiller et al. 2018 je IGBP-Klasse) und in der Störung. Kräftige "
          "Farbe: mindestens 30 % der Fläche wiederbewaldbar; blass: wenig Fläche.")

b6 = new_slide(BAEUME, "Was der Baum der Luft entnimmt")
picture(b6, FIG / "b6_aufnahme_balken.png", height=4.45)
equation(b6, r"\dot m_{CO_2}(t) = -\frac{44}{12}\,\dot m(t)", x=0.42, y=5.8, w=6.2, h=0.8,
         paras=[copy_omml(O(18), 0)])  # identical to the deck's own equation
kurz(b6, "Jeder Balken: so viel CO₂ holt ein Baum in diesem Jahr aus der Luft. Mit der Grenze um den Baum gilt: Was "
     f"der Baum hat, fehlt der Luft. Wie viel, hängt am Ort — der Mischwald in Aachen holt "
     f"{de(B_AC['aufnahme_2150_kg_co2'] / B_JO['aufnahme_2150_kg_co2'], 1)}-mal so viel wie der im finnischen Joensuu.")
quelle(b6, "Typischer Wald je Ort (Hasler et al. 2024), Kohlenstoff je Ort aus Walker et al. (2022), Tempo nach "
       "Cook-Patton et al. (2020); Störung mit heutiger Rate")
add_notes(b6, "Sprechertext: Jeder Jahreszuwachs ist eine kleine negative Emission — Kohlenstoff mal 44/12, "
          f"Vorzeichen gedreht. Aufsummiert holt ein Baum bis 2150 in Aachen rund {B_AC['aufnahme_2150_kg_co2']:.0f} kg "
          f"CO₂ aus der Luft, in Joensuu (Ostfinnland) rund {B_JO['aufnahme_2150_kg_co2']:.0f} kg: kürzere "
          "Vegetationsperiode, kälter, weniger Licht — der Wald dort trägt weniger Biomasse. Methode: "
          "docs/methods/waldtypen.md.")

s13 = O(13)
note13 = shape(s13, "Rectangle 9533") if any(sh.name == "Rectangle 9533" for sh in s13.shapes) else None
for sh in list(s13.shapes):
    if sh.has_text_frame and sh.text_frame.text.startswith("Wir haben wachstum"):
        remove_shape(s13, sh)
add_notes(s13, "Sprechertext: Der Baum wächst — und je größer er wird, desto mehr Boden verdeckt er. Das ändert, "
          "wie viel Sonnenlicht reflektiert wird. Hellerer Boden (Schnee) und mehr Sonne sind genau die zwei "
          "Ortsgrößen, die gleich die Karte färben.")

b8a = new_slide(BAEUME, "Zwei Zutaten: Sonne und Schnee")
picture(b8a, FIG / "b8a_albedo_zutaten.png", height=4.75)
kurz(b8a, "Wie viel Licht ein Baum zusätzlich schluckt, hängt an zwei Dingen: wie viel Sonne ankommt (im Süden "
     "mehr) und wie viel dunkler der Wald ist als die Fläche, die er ersetzt (wo Schnee liegt, viel dunkler).")
add_notes(b8a, "Sprechertext: Links die Sonne am Boden, im Jahresmittel — von Süden nach Norden weniger. Rechts, wie "
          "viel dunkler ein ausgewachsener Wald ist als Wiese oder Acker: im Norden viel, weil der Wald den "
          "Schnee verdeckt. Die nächste Karte ist das Produkt, Monat für Monat gerechnet. Grau: Für diese Zellen "
          "gibt es keine lokale Messung — Duveiller vergleicht Wald und Offenland, die direkt nebeneinander "
          "liegen, und das geht nur, wo es beides gibt. Im Modell werden graue Zellen mit dem Median ihres "
          "Breitenbandes gerechnet. Jede Zelle mit ihrem typischen Waldtyp.")

b8 = new_slide(BAEUME, "Zusätzlich absorbiertes Licht: je nach Ort")
picture(b8, FIG / "b8_albedo_jahreskarte.png", height=4.45)
equation(b8, r"\Delta\dot Q_{Baum} = A_{Baum}\,\langle \dot q_{kurz}\,(-\Delta\alpha)\rangle\, f(t)", x=0.42, y=5.8, w=6.2,
         h=0.8, groups={"q_kurz": ORANGE, "q̇_kurz": ORANGE}, chars={"α": ORANGE})
kurz(b8, "Beim Licht ist es umgekehrt: Wo Schnee liegt und die Sonne kräftig ist, schluckt der Baum am meisten — "
     f"Aachen {B_AC['licht_w']:.0f} W, Joensuu {B_JO['licht_w']:.0f} W im Jahresmittel.")
quelle(b8, "Δα und Einstrahlung: Duveiller et al. (2018), nur lokal gemessene Zellen; ausgewachsener typischer Wald "
       "statt Wiese oder Acker")
add_notes(b8, "Sprechertext: Aachen hat kaum Schnee — dort folgt der Effekt der Sonne, breites Maximum im "
          "Sommer. Joensuu hat im April eine Spitze von rund 150 W: noch Schnee, Sonne schon hoch. Im Jahresmittel "
          "unterscheiden sich die Orte weniger als im Jahresgang. Zusammen mit dem langsameren Wachstum im "
          "Norden entscheidet das später über das Vorzeichen. Grau: wiederbewaldbar, aber ohne lokale Messung.")

b9 = new_slide(BAEUME, "Was der Baum mit seiner Umgebung tauscht")
picture(b9, FIG / "b9_austausch_balken.png", height=4.55)
kurz(b9, "Kilogramm und Watt lassen sich nicht direkt vergleichen. Um zu sehen, was überwiegt, brauchen beide "
     "eine gemeinsame Währung: Energie.")
quelle(b9, "Mischwald in Aachen und Joensuu; rechts: Jahresmittel aus der Karte × Kronenschluss f(t)", x=0.42, y=6.2,
       w=6.1)
add_notes(b9, "Balken heißen in diesem Vortrag immer: was ein Baum in einem Jahr mit seiner Umgebung tauscht. Links "
          "Kilogramm CO₂ je Jahr, rechts Watt zusätzlich geschlucktes Licht. Durchgehende Linien kommen erst im "
          "Kapitel Klima, wenn das Klimasystem antwortet.")

_lu = FAKTEN["licht_ueberwiegt_bis"]
b10 = new_slide(BAEUME, "Gemeinsame Währung: Energie")
picture(b10, FIG / "b10_waehrung_balken.png", height=4.3)
equation(b10, r"\dot Q_{CO_2} = A_{CO_2}\,A_{Erde}\,m_{CO_2}", x=0.42, y=5.55, w=6.2, h=0.7,
         groups={"A_CO2": GREEN, "m_CO2": GREEN, "Q̇_CO2": GREEN, "CO_2": GREEN}, chars={"Q̇": GREEN})
kurz(b10, "Beides jetzt in Watt, in einem Bild: Licht wärmt (oben), das bisher entnommene CO₂ kühlt (unten) — rund "
     f"0,9 W je kg. So gerechnet überwiegt das CO₂ {both(co2_ab, _lu['Aachen'], _lu['Joensuu'])}; in Joensuu holt "
     "das Licht aber viel davon wieder auf."
     + " Offen bleiben zwei Fragen, die nicht der Baum beantwortet, sondern das Klimasystem: Wie lange fehlt das CO₂ "
     "der Luft? Und wie stark wirkt jedes Kilogramm?")
quelle(b10, "Naiv: alles entnommene CO₂ fehlt der Luft für immer, jedes kg wirkt mit dem Lehrbuchwert A_CO₂ = 1,76·10⁻¹⁵ "
       "W m⁻² kg⁻¹ über A_Erde = 5,1·10¹⁴ m². Albedo wie auf der Vorfolie.", x=0.42, y=6.35, w=6.1)
add_notes(b10, "Sprechertext: Watt sind Watt. Die Albedo liefert sie direkt. Für das CO₂ fragen wir: Wie viel "
          "Wärmestrahlung hält ein Kilogramm in der Luft zurück? Lehrbuchwert mal Erdoberfläche: knapp ein Watt je "
          "Kilogramm. Damit sind beide Kurven in derselben Einheit. Diese Rechnung hat zwei stille Annahmen — dass "
          "das CO₂ in der Luft bleibt und dass jedes Kilogramm gleich wirkt. Beides hängt nicht vom Baum ab, sondern "
          "vom Rest des Klimasystems. Das ist das nächste Kapitel. (Die Albedo kommt dort noch mit dem Faktor "
          "τ_atm ≈ 0,8 für den Weg nach oben.)")

# ---- Klima (Schalen 2 und 3) ---------------------------------------------
set_runs(O(17).placeholders[1].text_frame.paragraphs[0], "Wie lange fehlt das CO₂ — und wie stark wirkt es?")

k2 = new_slide(KLIMA, "Der Baum ist Teil eines Systems")
shells = [
    ("Schale 5 · alle Wege, CO₂ zu entnehmen", "Vergleich", RGBColor(0xEA, 0xE4, 0xD4)),
    ("Schale 4 · alle Bäume auf der Landfläche", "Vergleich", RGBColor(0xE2, 0xDA, 0xC6)),
    ("Schale 3 · Erde am Oberrand: Energie", "Klima", RGBColor(0xEB, 0xCF, 0xCB)),
    ("Schale 2 · Luft, Ozean, Land", "Klima", RGBColor(0xE3, 0xBC, 0xB7)),
    ("Schale 1 · ein Baum", "Bäume", RGBColor(0xC9, 0xD8, 0xBF)),
]
x0, y0, w0, h0, step = 0.5, 1.15, 7.6, 5.6, 0.42
for k, (label, chapter, color) in enumerate(shells):
    box = k2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x0 + k * step), Inches(y0 + k * 0.5),
                              Inches(w0 - 2 * k * step), Inches(h0 - 2 * k * 0.5))
    box.adjustments[0] = 0.06
    box.fill.solid()
    box.fill.fore_color.rgb = color
    box.line.color.rgb = RGBColor(0x8A, 0x81, 0x72) if chapter == "Klima" else RGBColor(0xC9, 0xC0, 0xAE)
    box.line.width = Pt(2.0 if chapter == "Klima" else 0.75)
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = 1  # top
    tf.margin_left, tf.margin_top = Inches(0.15), Inches(0.06)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = label
    r.font.size = Pt(13)
    r.font.bold = chapter == "Klima"
    r.font.color.rgb = INK
panel = k2.shapes.add_textbox(Inches(8.4), Inches(1.3), Inches(4.5), Inches(3.6))
tf = panel.text_frame
tf.word_wrap = True
for i, line in enumerate([
    "Bisher: nur der Baum.",
    "Was er tauscht, landet in Teilen der Erde, die selbst reagieren.",
    "Zuerst: Wo bleibt das CO₂? → Schale 2",
    "Dann: Was macht es mit der Energie? → Schale 3",
]):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(10)
    r = p.add_run()
    r.text = line
    r.font.size = Pt(16)
    r.font.bold = i == 0
    r.font.color.rgb = INK
kurz(k2, "Um den Netto-Effekt zu sehen, ziehen wir die Grenze in zwei Schritten weiter: erst um den "
     "Kohlenstoffkreislauf, dann um die ganze Erde.", x=8.4, w=4.5)
add_notes(k2, "Das Schalenbild ist der rote Faden. Jede Rückwirkung des Systems kommt genau dort, wo ihre Schale "
          "beginnt: Ozean/Land in Schale 2, die übrige Menschheit und die Erwärmung in Schale 3.")

s18 = O(18)  # g_C slide, hidden in the original
unhide(s18)
rehang(s18, KLIMA)
set_title(s18, "Wie lange fehlt das CO₂ der Luft?")
remove_shape(s18, shape(s18, "Rectangle 3"))
eq = s18.placeholders[12]
eq.left = Inches(13.8)  # parked off-canvas like other boxes in this deck: ṁ_CO₂ and the convolution live on B6/K4 now
pic = shape(s18, "Picture 9010")
_part, _rid = s18.part.get_or_add_image_part(str(FIG / "k3_restanteil_joos.png"))
pic._element.blipFill.blip.rEmbed = _rid
pic.width = Inches(9.6)
pic.height = int(Inches(9.6) * 5.1 / 12.0)
pic.left, pic.top = int((PRS.slide_width - pic.width) / 2), Inches(1.1)
set_runs(shape(s18, "Formelzeichen").text_frame.paragraphs[0],
         "g_C(t) Anteil eines entnommenen Kilogramms, der der Luft nach t Jahren noch fehlt — vor einem "
         "unveränderten Hintergrund (Joos et al. 2013). Mit steigendem Hintergrund rechnet das Modell später mit FaIR.")
for _extra in shape(s18, "Formelzeichen").text_frame.paragraphs[1:]:
    _extra._p.getparent().remove(_extra._p)
replace_kurz(s18, "Fehlt der Luft CO₂, nehmen Ozean und Landbiosphäre weniger auf und geben teilweise zurück. Von "
             "einem entnommenen Kilogramm fehlt nach 20 Jahren nur noch gut die Hälfte, nach 75 Jahren 44 %.")
add_notes(s18, "Kapiteleinstieg. Sprechertext: Die naive Rechnung hat angenommen, dass alles entnommene CO₂ der Luft "
          "fehlt, für immer. Aber Ozean und Landbiosphäre stehen mit der Luft im Austausch: Fehlt dort CO₂, nehmen "
          "sie weniger auf und geben teilweise zurück. Nach 20 Jahren fehlt nur noch gut die Hälfte, nach 75 Jahren "
          "44 %. Die Gleichungen (ṁ_CO₂ = −44/12·ṁ und die Faltung) liegen rechts neben der Folie geparkt; sie "
          "stehen auf „Was der Baum der Luft entnimmt“ und „Das CO₂-Profil in der Luft“.")

k3p = new_slide(KLIMA, "Was der Baum entnimmt, bleibt nicht ganz weg")
picture(k3p, FIG / "k3_ein_jahr_puls.png", height=4.55)
kurz(k3p, "Links die bekannten Bäume in Aachen und Joensuu, Jahr für Jahr. Rechts, was mit einem einzigen "
     "Jahr geschieht: Fehlt "
     "der Luft CO₂, nehmen Ozean und Land weniger auf und geben teilweise zurück. Nach 20 Jahren fehlt nur noch gut "
     "die Hälfte, nach 75 Jahren 44 %.")
quelle(k3p, "Wachstum wie im Kapitel Bäume (typischer Wald je Ort, Störung mit heutiger Rate). Rückgabe: Impulsantwort "
       "g_C nach Joos et al. (2013), vorindustrieller Hintergrund.", x=0.42, y=6.2, w=6.1)
add_notes(k3p, "Kapiteleinstieg, Frage 1: Wie lange fehlt das CO₂ der Luft? Sprechertext: Die Kurve links kennen Sie "
          "— so viel holt der Baum jedes Jahr aus der Luft. Am Baum bilanziert wäre jedes dieser Kilogramm für immer "
          "weg, die gestrichelte Linie rechts. Tatsächlich stehen Luft, Ozean und Landbiosphäre im Austausch: Fehlt "
          "oben CO₂, gast der Ozean weniger ein und gibt zurück. Die durchgezogene Linie ist das, was der Luft "
          "wirklich fehlt. Diese Kurve heißt g_C. Nächste Folie: dasselbe für jedes Jahr, aufsummiert.")

k4 = new_slide(KLIMA, "Alle Jahre zusammen: das CO₂-Profil")
picture(k4, FIG / "k4_co2_profil.png", height=4.55)
equation(k4, r"\Delta m_{CO_2}(t) = \int_0^t g_C(t-t')\,\dot m_{CO_2}(t')\,dt'", x=0.42, y=5.7, w=6.2, h=0.95,
         paras=[copy_omml(O(18), 1)])  # identical to the deck's own equation
kurz(k4, "Jedes Jahr ein solcher Puls, alle zusammen: Gestrichelt, was der Baum geholt hat (die Kurve aus dem "
     "Kapitel Bäume), durchgezogen, was der Luft davon wirklich fehlt. Es ist deutlich weniger — und die Lücke "
     "schließt sich wieder, sobald der Baum kaum noch zuwächst.")
quelle(k4, "Impulsantwort g_C: Joos et al. (2013), vorindustriell; Mischwald in Aachen und Joensuu, Störung mit heutiger Rate")
add_notes(k4, "Sprechertext: Jede Jahresentnahme klingt mit g_C ab, die Summe ist das CO₂, das der Luft "
          "wirklich fehlt. Bis 2150 fehlen der Luft in Aachen noch 165 der 370 geholten kg, in Joensuu 52 "
          "von 116 kg.")

s19 = O(19)
set_title(s19, "Systemgrenze: die ganze Erde")
red = shape(s19, "TextBox 30")
paras = red.text_frame.paragraphs
lines = ["Über die Grenze geht nur Strahlung:", "kurzwellig rein, ein Teil gleich wieder raus (reflektiert),",
         "langwellig raus.", "",
         "Verdunstung verschiebt Energie nur innerhalb der Grenze — lokal kühlt sie, global steckt sie in den "
         "Rückkopplungen."]
for i, p in enumerate(paras):
    if i < len(lines):
        set_runs(p, lines[i])
        for r in p.runs:
            r.font.color.rgb = INK
    else:
        p._p.getparent().remove(p._p)
for line in lines[len(paras):]:
    p = red.text_frame.add_paragraph()
    r = p.add_run()
    r.text = line
    r.font.color.rgb = INK
red.width = Inches(5.4)
red.height = Inches(2.6)
add_notes(s19, "[v2] Rote Arbeitsnotizen durch Text ersetzt; Folie 26 (Verdunstung) liegt im Backup, hier nur der "
          "eine Satz.")

s22 = O(22)
set_title(s22, "Beides in einer Bilanz: der Antrieb")
replace_kurz(s22, "Über die Grenze der Erde geht nur Strahlung. Antrieb φ: wie stark ein Eingriff „rein − raus“ "
             "verschiebt [W/m²]; solange rein ≠ raus, ändert sich der Energieinhalt. CO₂ dreht an der Abstrahlung, "
             "die Albedo am reflektierten Licht — in dieser Bilanz werden beide vergleichbar.")

s25 = O(25)
set_title(s25, "Antrieb aus der Albedo")
replace_kurz(s25, "Die Watt aus dem Bäume-Kapitel sind schon Energie: × τ_atm für den Weg nach oben, ÷ A_Erde. "
             "Die Albedo wirkt sofort und nur so lange, wie der Baum steht — einen Rebound gibt es hier nicht.")
add_notes(s25, "[v2] In PowerPoint die Zeile φ = φ_CO₂ + φ_α entfernen — die Summe kommt erst, wenn CO₂ "
          "hergeleitet ist. Gleichung als φ_α(t) = τ_atm · ΔQ̇_Baum(t) / A_Erde lesen (ΔQ̇_Baum aus B8).")

k7 = new_slide(KLIMA, "Warum CO₂ wärmt")
picture(k7, FIG / "k7_abstrahlhoehe.png", height=4.55)
kurz(k7, "Die Erde gibt ihre Wärme nicht vom Boden ins All ab, sondern aus etwa 5 km Höhe — dort, wo die Luft für "
     "Wärmestrahlung durchsichtig wird. Mehr CO₂ schiebt diese Höhe nach oben, wo es kälter ist, und Kälteres "
     "strahlt weniger. Bei doppelt so viel CO₂ bleiben 3,7 W/m² drin.")
quelle(k7, "Vereinfachtes Bild der Abstrahlhöhe: Temperaturgradient 6,5 K/km, Abstrahltemperatur 255 K (σT⁴ = "
       "240 W/m²); 3,7 W/m² = 5,35·ln 2 (Myhre et al. 1998). Siehe z. B. Pierrehumbert (2011), Physics Today 64(1).",
       x=0.42, y=6.2, w=6.1)
add_notes(k7, "Sprechertext: Nach oben wird es kälter, jeder kennt das vom Berg. Die Wärme der Erde geht nicht vom Boden "
          "ins All, sondern aus der Höhe, ab der darüber kaum noch CO₂ und Wasserdampf liegt — im Mittel rund 5 km, "
          "−18 °C. Mehr CO₂ heißt: Diese Höhe wandert nach oben, in kältere Luft. Kälteres strahlt weniger. Es kommt "
          "also gleich viel Sonne herein, aber weniger Wärme hinaus — die Erde wärmt sich auf, bis das wieder "
          "ausgeglichen ist. Ein Baum, der CO₂ entnimmt, senkt diese Höhe ein winziges Stück. Spektrum mit "
          "CO₂-Bande: Backup.")

k7s = new_slide(KLIMA, "Warum CO₂ wärmt: das Spektrum")
picture(k7s, FIG / "k7_co2_spektrum.png", height=4.55)
quelle(k7s, "Schematisch: Planck-Kurven für 288 K und 220 K mit einem CO₂-Band um 15 µm, keine "
       "Strahlungstransportrechnung", x=0.42, y=6.2, w=6.1)
kurz(k7s, "Im CO₂-Band strahlt nicht der warme Boden ins All, sondern kalte Luft in großer Höhe — und Kaltes "
     "strahlt weniger. Ein Baum, der CO₂ entnimmt, macht die Kerbe ein winziges Stück schmaler.")

k8 = new_slide(KLIMA, "Wie stark wirkt jedes Kilogramm?")
picture(k8, FIG / "k8_co2_saettigung.png", height=4.3)
equation(k8, r"\varphi = 5{,}35\,\ln\left(C/C_0\right)", x=0.42, y=5.6, w=6.2, h=0.7,
         groups={"C_0": GREEN}, chars={"φ": GREEN, "C": GREEN})
kurz(k8, "Je mehr CO₂ schon in der Luft ist, desto weniger bewirkt jedes weitere Kilogramm — der Antrieb wächst "
     f"nur logarithmisch. Unter SSP2-4,5 sinkt die Wirkung je kg von {de(FAKTEN['a_co2']['start'], 2)} auf "
     f"{de(FAKTEN['a_co2']['ende'], 2)}·10⁻¹⁵ W/m². Wer heute pflanzt, entnimmt in eine Atmosphäre, in der jedes "
     "Kilogramm später weniger zählt.")
_gf, _gj = FAKTEN["a_co2"]["g_c_fair_2100"], FAKTEN["a_co2"]["g_c_joos_2100"]
add_notes(k8, "Ab hier rechnet die Rücknahme durch Ozean und Land mit FaIR unter SSP2-4,5 statt mit Joos. Von einem "
          f"Impuls 2025 sind 2100 noch {pct(_gf)} in der Luft (Joos: {pct(_gj)}) — "
          + ("Ozean und Land nehmen im kalibrierten FaIR also etwas mehr auf, nicht weniger; die vollere Atmosphäre "
             "wirkt hier vor allem über den Antrieb je kg." if _gf < _gj else
             "in der volleren Welt nehmen Ozean und Land also schlechter auf; das wirkt zugunsten des Baums."))

s24 = O(24)
set_title(s24, "Antrieb aus CO₂")
add_notes(s24, "Zur Wirkung je kg: Der Antrieb wächst logarithmisch, φ = 5,35·ln(C/C₀); jedes weitere Kilogramm "
          "wirkt also umso weniger, je mehr schon in der Luft ist (Backup: „Wie stark wirkt jedes Kilogramm?“, "
          "„Warum CO₂ wärmt“). Zur Antwort von Ozean und Land: Ab hier rechnet das Modell mit FaIR unter SSP2-4,5 statt "
          f"mit der vorindustriellen Kurve; von einem Impuls 2025 sind 2100 noch {pct(FAKTEN['a_co2']['g_c_fair_2100'])} "
          f"in der Luft statt {pct(FAKTEN['a_co2']['g_c_joos_2100'])} — der größere Effekt ist die Wirkung je kg.")
picture(s24, FIG / "k8_co2_saettigung.png", height=2.75, top=2.1)
replace_kurz(s24, "φ_CO₂ ist das CO₂-Profil in der Luft mal die Wirkung je Kilogramm. Beides hängt davon ab, wie viel "
             "die Menschheit noch emittiert: Je voller die Atmosphäre, desto weniger wirkt jedes Kilogramm — unter "
             f"SSP2-4,5 von {de(FAKTEN['a_co2']['start'], 2)} auf {de(FAKTEN['a_co2']['ende'], 2)}·10⁻¹⁵ W/m² —, und "
             "auch Ozean und Land antworten anders. Das Modell rechnet beides mit diesem Szenario.")
set_runs(shape(s24, "Formelzeichen").text_frame.paragraphs[0],
         f"A_CO₂(t) Strahlungswirkung je kg zusätzliches CO₂ — sinkt unter SSP2-4,5 von {de(FAKTEN['a_co2']['start'], 2)} "
         f"auf {de(FAKTEN['a_co2']['ende'], 2)}·10⁻¹⁵ W m⁻² kg⁻¹  ·  Δm_CO₂(t) CO₂-Profil in der Luft")
add_notes(s24, "[v2] In PowerPoint die Gleichung zeitabhängig lesen: φ_CO₂(t) = A_CO₂(t) · Δm_CO₂(t). Die alte "
          "Konstante 1,76·10⁻¹⁵ ist durch die abnehmende Wirkung der vorigen Folie ersetzt.")

k10 = new_slide(KLIMA, "Jetzt vergleichbar: Kohlenstoff gegen Licht")
picture(k10, FIG / "k10_antrieb_zwei_orte.png", height=4.55)
kurz(k10, f"Jetzt ist Kilogramm gegen Watt entschieden. In Aachen kühlt der Wald {ab_wann(AC['t_star'])}. In "
     f"Joensuu hätte am Baum allein {co2_ab(FAKTEN['licht_ueberwiegt_bis']['Joensuu'])} das CO₂ gewonnen — mit Ozean, "
     "Land und vollerer Atmosphäre überwiegt dort "
     + (f"bis {JO['phi_negativ_ab']} das Licht." if JO["phi_negativ_ab"] is not None else "bis 2150 das Licht."))
quelle(k10, "Mischwald, SSP2-4,5, volles Modell; Albedo je Ort aus der lokal gemessenen Zelle",
       x=0.42, y=6.2, w=6.1)

k11 = new_slide(KLIMA, "Von Watt zu Grad")
picture(k11, FIG / "k11_antrieb_zu_temperatur.png", height=4.1)
equation(k11, r"\Delta T(t) = \int_0^t g_T(t-t')\,\varphi(t')\,dt'", x=0.42, y=5.35, w=6.2, h=0.85,
         groups={"g_T": DARK}, chars={"φ": DARK, "T": DARK})
kurz(k11, "Ein Antrieb wirkt wie eine zusätzliche Herdplatte: Die Erde wird wärmer, bis sie die Mehrleistung "
     "wieder abstrahlt (links). Ein einzelnes Jahr Antrieb erwärmt kurz und klingt ab (rechts, g_T). Die Temperatur "
     "ist die Summe aller Jahre — dasselbe Prinzip wie beim CO₂-Profil.")
quelle(k11, "Sprungantwort und g_T aus FaIR 2.2 (fair-calibrate 1.4.1, Mitglied "
       f"{FAKTEN['klima']['fair_mitglied']}); Λ = {de(FAKTEN['klima']['lambda_w_m2_k'], 2)} W m⁻² K⁻¹",
       x=0.42, y=6.2, w=6.1)
add_notes(k11, "Sprechertext: Stellen Sie sich einen Topf auf der Herdplatte vor. Der Antrieb ist die zusätzliche "
          "Leistung der Platte. Der Topf wird wärmer — und je wärmer er ist, desto mehr Wärme gibt er wieder ab. "
          "Irgendwann ist beides gleich: Gleichgewicht. Bei der Erde ist das „Abgeben“ die Abstrahlung ins All, "
          "Λ·T, und der Topf hat zwei Teile: eine dünne Oberfläche, die in Jahren folgt, und einen riesigen tiefen "
          "Ozean, der Jahrhunderte braucht. Links: Platte bleibt an. Rechts: Platte ein Jahr an und wieder aus — "
          "die Temperatur springt und klingt ab. Das ist g_T. Unsere Bäume sind eine Folge solcher kurzen Stöße, "
          "jedes Jahr ein neuer — Impuls, Antwort, Summe, genau wie beim CO₂. Herleitung (C·dT/dt = φ − Λ·T) und "
          "die Kalibrierung von g_T: Backup.")

s23 = O(23)
replace_kurz(s23, "Dieselbe Herdplatte als Gleichung: ① Wärmer heißt mehr Abstrahlung (Λ·T). ② Was nicht abgestrahlt "
             "wird, bleibt als Energie drin (dU/dt). ③ Mehr Energie heißt höhere Temperatur (U = C·T). Zusammen: "
             "C·dT/dt = φ − Λ·T.")
add_notes(s23, "[v2] Erst die Herdplatte (Vorfolie), dann die drei Schritte. Λ auf der Folie nach Sherwood et al. "
          f"(2020) ≈ 1,3; im Modell (FaIR-Mitglied) {de(FAKTEN['klima']['lambda_w_m2_k'], 2)} W m⁻² K⁻¹.")

s29 = O(29)
set_title(s29, "Die Erde antwortet")
# The old chart showed illustrative curves (a large slow tail) that contradict
# the model's own g_T on "Vom Antrieb zur Temperatur"; show that one instead.
_old = next(sh for sh in s29.shapes if sh.has_chart)
_x, _y, _w, _h = _old.left, _old.top, _old.width, _old.height
_old._element.getparent().remove(_old._element)
s29.shapes.add_picture(str(FIG / "k11b_g_T.png"), _x, _y, _w, _h)
add_notes(s29, "[v2] Zusammen mit „Von Energie zu Temperatur“ lesen: C·dT/dt = φ − Λ·T, Antwort g_T. Rückverweis "
          "auf g_C — Impuls, Antwort, Summe.")

k12 = new_slide(KLIMA, "Ergebnis: ein Baum, voll bilanziert")
picture(k12, FIG / "k12_temperatur_zwei_orte.png", height=4.55)
kurz(k12, f"Jetzt ist Kilogramm gegen Watt entschieden. In Aachen kühlt der Wald {ab_wann(AC['t_star'])}. "
     + (f"In Joensuu wärmt sie {JO['t_star'] - 2025} Jahre lang und kühlt erst ab {JO['t_star']}: langsamer Zuwachs "
        f"gegen Schnee unter der Krone. Der Versatz zum Antrieb ({JO['phi_negativ_ab']}) ist die Trägheit der Erde."
        if JO_KUEHLT else
        f"In Joensuu hätte am Baum allein {co2_ab(FAKTEN['licht_ueberwiegt_bis']['Joensuu'])} das CO₂ gewonnen — "
        "mit dem Klimasystem wärmt sie dort bis 2150."))
quelle(k12, "Mischwald, gepflanzt 2025, SSP2-4,5, volles Modell", x=0.42, y=6.2, w=6.1)
add_notes(k12, f"Größenordnung einmal laut sagen: bis 2150 etwa {sci_de(AC['delta_t_2150_K'])} K je Baum in Aachen, "
          f"{sci_de(JO['delta_t_2150_K']).replace('−', '+') if JO['delta_t_2150_K'] > 0 else sci_de(JO['delta_t_2150_K'])}"
          " K in Joensuu. Bis zum Vergleich bleiben wir bei „je Baum“. Joensuu liegt auf der Kippe: Ob der Baum dort "
          "vor 2150 kühlt, hängt am Parametersatz des Klimamodells (mit einem anderen, ebenso zentralen "
          "FaIR-Mitglied kippt er um 2110).")

k13 = new_slide(KLIMA, "Die Erwärmung wirkt auf den Baum zurück")
picture(k13, FIG / "k13_pflanzjahr_zwei_orte.png", height=4.1)
equation(k13, r"p(t) = p_0\,e^{\gamma\,T(t)}", x=0.42, y=5.8, w=6.2, h=0.8,
         groups={"p_0": RED}, chars={"p": RED, "γ": RED})
_dist_step = AC["leiter_dt_2150_K"][-1] - AC["leiter_dt_2150_K"][-2]  # < 0: disturbance adds cooling
kurz(k13, "Und die Erwärmung wirkt zurück: Je wärmer es wird, desto häufiger Feuer, Sturm und Käfer. Störungen "
     "kosten Kohlenstoff, lichten aber auch den Wald — dann schluckt er weniger Licht. "
     + ("Unterm Strich kühlt der Wald dadurch 2150 sogar etwas mehr. " if _dist_step < 0 else
        "Unterm Strich kostet das Kühlung. ")
     + ("Ein später gepflanzter Baum kühlt 2150 "
        + ("gleich viel oder mehr" if min(AC["anteil_pflanzjahr_2085"], JO["anteil_pflanzjahr_2085"]) >= 0.98 else
           f"in Aachen noch {pct(AC['anteil_pflanzjahr_2085'])}")
        + ": Von seinem CO₂ ist noch wenig zurückgeflossen, und sein Kronendach ist noch nicht ganz geschlossen."))
add_notes(k13, "Balken: Wirkung je Baum im Jahr 2150 nach Pflanzjahr. Enthalten sind höhere Störungsrate, "
          "vollere Atmosphäre und weniger verbleibende Zeit; getrennt zeigt sie die Leiter auf der nächsten Folie.")

k14 = new_slide(KLIMA, "Was jede Erweiterung der Systemgrenze kostet")
picture(k14, FIG / "k14_leiter_schalen.png", height=4.55)
_steps = ["Albedo", "Ozean und Land geben zurück", "vollere Atmosphäre", "Erwärmung erhöht Störung"]
_ac = [v * 1e15 for v in AC["leiter_dt_2150_K"]]
_jo = [v * 1e15 for v in JO["leiter_dt_2150_K"]]
_drop = [b_ - a_ for a_, b_ in zip(_ac, _ac[1:])]
add_notes(k14, "Leiter: Temperaturwirkung je Baum in 2150 nach jeder Erweiterung der Systemgrenze, kumulativ "
          "(nbs.storyline_figures.ladder_delta_t). Aachen: " + " → ".join(f"{v:.0f}" for v in _ac) + "; Joensuu: "
          + " → ".join(f"{v:+.0f}" for v in _jo) + " (·10⁻¹⁵ K). Bewusst nicht das Jahr t*: In Joensuu liegen "
          "Kohlenstoff und Albedo nur rund 20 % auseinander, eine moderate Änderung kippt dort das Jahr von 2048 auf "
          "„nie“, obwohl sich die Temperaturwirkung nur von −13 auf +4 verschiebt. „Vollere Atmosphäre“ umfasst den "
          "Schritt vom Lehrbuchwert 1,76 (entspricht 389 ppm) auf den logarithmischen Antrieb mit SSP2-4,5-Hintergrund "
          "und den Wechsel von der Joos- auf die FaIR-Rückgabe.")
_jo_l = [v * 1e15 for v in JO["leiter_dt_2150_K"]]
kurz(k14, f"Jede Erweiterung kostet Kühlung: in Aachen von {abs(_ac[0]):.0f} auf {abs(_ac[-1]):.0f} "
     "(·10⁻¹⁵ K je Baum); den größten Schritt macht "
     f"{['die Albedo', 'die Rückgabe durch Ozean und Land', 'die vollere Atmosphäre', 'die häufigere Störung'][int(np.argmax(_drop))]}"
     f". In Joensuu bleiben von {abs(_jo_l[0]):.0f} nur {abs(_jo_l[-1]):.0f}. "
     + ("Nur die Störung gibt etwas zurück: Sie lichtet den Wald, der dann weniger Licht schluckt. "
        if _ac[-1] < _ac[-2] else "")
     + "Eine Ökobilanz mit GWP100 sieht nur einen Teil davon: Sie mittelt die Rückgabe über 100 Jahre bei festem "
     "CO₂-Hintergrund — vollere Atmosphäre und Rückkopplung auf den Baum fehlen ihr.")

# ---- Vergleich (Schalen 4 und 5) -----------------------------------------
set_runs(O(39).placeholders[1].text_frame.paragraphs[0], "Ingenieure auf dem Holzweg?") if O(39).placeholders[1].text_frame.paragraphs[0].runs else O(39).placeholders[1].text_frame.paragraphs[0].add_run().__setattr__("text", "Ingenieure auf dem Holzweg?")

for n in (35, 37, 38):
    rehang(O(n), VERGLEICH)
set_title(O(35), "Dieselbe Kette, andere Orte")
add_notes(O(35), "[v2] Kein neues Konzept — Wachstum (Bäume-Kapitel) und Albedo-Karte sind bekannt, jetzt die volle "
          "Kette je Ort. Balken: Jahre mit Erwärmung je Art an ihrem Referenzstandort.")
add_notes(O(37), "[v2] Laut Storyline: erstes Bild im selben Kartenausschnitt wie die Albedokarte (Europa + "
          "westliches Russland, Marker Aachen/Joensuu), dann global; Farbskala auf 4 Klassen.")
set_title(O(42), "Reicht das? Die Umkehrrechnung")

s46 = O(46)
naiv = shape(s46, "Naiv").text_frame.paragraphs
set_runs(naiv[1], f"•  Ein Baum im Aachener Mischwald bindet bis zur Sättigung rund {B_AC['saettigung_kg_co2']:.0f} kg CO₂.")
set_runs(naiv[2], "•  300 Gt ÷ 0,18 t ≈ 1,6 Billionen Bäume — gültig, solange die Grenze um den Baum liegt.")
set_runs(naiv[3], "•  Kein Rebound, keine Albedo, kein Ort, keine Zeit.")
modell = shape(s46, "Modell").text_frame.paragraphs
set_runs(modell[0], "Dieselbe Frage, mit wachsender Systemgrenze")
set_runs(modell[1], "+ Kohlenstoffkreislauf: Ozean und Land geben zurück — der Luft fehlt weniger.")
set_runs(modell[2], "+ Erde am Oberrand: Albedo wirkt dagegen, jedes kg wirkt später weniger, Erwärmung erhöht "
         f"die Störung. Mischwald: kühlt in Aachen {ab_wann(AC['t_star'])}, in Joensuu "
         + (f"erst ab {JO['t_star']}." if JO_KUEHLT else "bis 2150 nicht."))
set_runs(modell[3], f"+ ganze Landfläche: {de(KA['kohlenstoff_gtc'])} GtC, {de(abs(KA['delta_t_2150_K']), 2)} K bis 2150.")
set_runs(modell[4], f"→ Für 1,5 °C ab 2050: das {de(UM['vielfaches'])}-Fache dieser Fläche, "
         + ("mehr als alles eisfreie Land." if UM["anteil_eisfrei"] > 1 else
            f"rund {pct(UM['anteil_eisfrei'])} des eisfreien Landes."))
for _name in ("Naiv", "Modell"):
    shape(s46, _name).height = Inches(2.3)
replace_kurz(s46, "Die naive Rechnung ist nicht falsch gerechnet — sie zieht die Grenze um den Baum. Jede Erweiterung, "
             "die man dazunimmt, verändert die Antwort.")

s47 = O(47)
set_title(s47, "Die Antwort hängt an der Grenze")
for name, head, body in [
    ("These 1", "1 — Bäume reichen nicht",
     f"Alle nutzbaren Flächen: netto rund {FAKTEN['vergleich']['baeume_netto_gtco2']:.0f} Gt CO₂ bis 2150 — "
     f"{pct(FAKTEN['vergleich']['anteil_netto_an_vl'])} des niedrigsten Szenarios."),
    ("These 2", "2 — Heute Holzweg, morgen Messlatte",
     "Mit heutigem Strom ist DAC fast nirgends besser. Mit sauberem Strom setzt es die Latte, die jeder Baum "
     "überspringen muss."),
    ("These 3", "3 — Beides, in der richtigen Reihenfolge",
     "Bäume jetzt, wo sie kühlen. DAC, wo und sobald der Strom sauber ist. Emissionen senken in jedem Fall."),
]:
    ps = shape(s47, name).text_frame.paragraphs
    set_runs(ps[0], head)
    set_runs(ps[1], body)
    for extra in ps[2:]:
        extra._p.getparent().remove(extra._p)
replace_kurz(s47, "Sind die Ingenieure auf dem Holzweg? Heute ja — mit dem Strom von heute entnimmt die Maschine kaum "
             "netto etwas. Aber die Bäume reichen nicht, und die Maschine wird mit der Energiewende besser. Die naive "
             "Rechnung vom Anfang zog die Grenze um den Baum; mit der ganzen Grenze heißt die Antwort: beides, "
             "zur richtigen Zeit am richtigen Ort.")


# ---- contribution: what this work adds (before the closing slide) ---------
KA_ = FAKTEN["kaskade"]
VG_ = FAKTEN["vergleich"]
_switch = {n: o.get("umstieg") for n, o in VG_["orte"].items()}
_sw = sorted(y for y in _switch.values() if y)
n1 = new_slide(VERGLEICH, "Was diese Arbeit neu zeigt")
_tpl = shape(s47, "These 1")
clone_box(n1, _tpl, x=0.42, y=1.3, w=6.1, h=2.3, heading="Methode: eine Kette, Jahr für Jahr, je Ort",
          body="Vom einzelnen Baum bis zur globalen Temperatur, für jede 0,5°-Zelle der Erde: Wachstum, gemessene "
               "Albedo mit ihrem Zeitverlauf und Störung — und alles zusammen in einem Lauf des Klimamodells FaIR: "
               "Entnahme als negative Emission, Albedo als Antrieb. Dass sich Senken füllen und jedes kg bei mehr "
               "CO₂ schwächer wirkt, rechnet das Modell selbst, statt es wie GWP100 festzuschreiben. Dazu dieselbe "
               "Rechnung für DAC mit prospektiver Ökobilanz je Land und Jahr.")
clone_box(n1, _tpl, x=6.84, y=1.3, w=6.1, h=2.2, heading="Warum das zählt",
          body="Statische Bilanzen vergleichen Endzustände; Erdsystemmodelle rechnen ganze Szenarien, nicht den "
               "einzelnen Ort. Erst beides zusammen zeigt, wann ein Baum an welchem Ort zu kühlen beginnt — und "
               "ab wann die Maschine dort die bessere Tonne liefert.")
clone_box(n1, _tpl, x=0.42, y=3.75, w=4.05, h=1.5, heading="Bäume kühlen nur auf einem Teil",
          body=f"Bis 2150 kühlen {de(VG_['bepflanzbar_kuehlt_gha'], 2)} der "
               f"{de(VG_['bepflanzbar_kuehlt_gha'] + VG_['bepflanzbar_waermt_gha'], 2)} Gha wiederbewaldbarer Fläche; "
               "im Norden und in trockenen Gebieten frisst die Albedo den Nutzen.")
clone_box(n1, _tpl, x=4.72, y=3.75, w=4.05, h=1.5, heading="Bäume reichen nicht",
          body=f"Netto rund {VG_['baeume_netto_gtco2']:.0f} Gt CO₂ bis 2150 — {pct(VG_['anteil_netto_an_vl'])} dessen, "
               "was selbst das niedrigste Szenario braucht.")
clone_box(n1, _tpl, x=9.02, y=3.75, w=4.05, h=1.5, heading="Erst Bäume, dann Maschine",
          body="DAC ist mit heutigem Strom meist der Holzweg, überholt den Baum aber je nach Ort zwischen "
               f"{_sw[0]} und {_sw[-1]}, sobald der Strom sauber wird.")
kurz(n1, "Neu ist nicht die einzelne Zutat, sondern die Kette: dieselbe zeitaufgelöste Rechnung für Baum und "
     "Maschine, an jedem Ort der Erde. Sie macht aus „Baum oder Maschine?“ die Frage „welche Tonne wann und wo?“.")
add_notes(n1, "Einordnung, ehrlich: Zeitaufgelöst rechnen auch andere — Kirschbaum et al. 2011 (ein Standort), "
          "Arora & Montenegro 2011, Weber et al. 2024 und Liang et al. 2025 (Erdsystem- bzw. dynamische Modelle, "
          "ganze Szenarien). Statisch und je Ort rechnen Hasler et al. 2024 und Rohatyn et al. 2022. Das Tempo der "
          "Albedo stammt aus Williams et al. 2026. Unseres Wissens neu ist die Kombination: je Ort und Jahr, vom Baum "
          "bis zur Temperatur, mit Szenario-Hintergrund und Störung, und derselbe Rahmen für DAC.")

# ---- existing LaTeX-text formulas -> native equations ----------------------
for n, sid in ((29, 4014), (58, 3002)):
    sl = O(n)
    box = next(sh for sh in sl.shapes if sh.shape_id == sid)
    src = box.text_frame.text
    lines = [ln.strip() for ln in src.split("\n") if ln.strip()]
    x, y, w, h = (v / 914400 for v in (box.left, box.top, box.width, box.height))
    remove_shape(sl, box)
    equation(sl, lines, x=x, y=y, w=w, h=max(h, 0.75 * len(lines)), align="center")

# ---- result charts regenerated from the current model (2026-10-05) --------
# Data: scripts/export_chart_data.py -> docs/slides/chart_data/*.csv; maps:
# nbs.map_plots (p0, p5). Swapped into the existing native charts/pictures so
# their formatting stays.
import pandas as pd  # noqa: E402
from pptx.chart.data import CategoryChartData  # noqa: E402
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION  # noqa: E402

CHART_DATA = ROOT / "docs" / "slides" / "chart_data"


def chart_of(slide):
    return next(sh for sh in slide.shapes if sh.has_chart)


# slide 12: example parametrisation = the running example (mixed forest, Aachen)
from pptx.chart.data import XyChartData  # noqa: E402
from nbs.species import get_species as _gs  # noqa: E402

_SP_AC = _gs(B_AC["art"])

d12 = pd.read_csv(CHART_DATA / "12_vorrat_fichte_verlustterm.csv")
c12 = chart_of(s12).chart
xy = XyChartData()
for _name, _col in (("nur Wachstum", "nur_wachstum_kgC"), ("mit Störung, ΔT_w = 0", "mit_stoerung_dTw_0_kgC"),
                    ("mit Störung, ΔT_w = 1 K (linear)", "mit_stoerung_dTw_1K_linear_kgC")):
    _se = xy.add_series(_name)
    for _x, _y in zip(d12["jahr"], d12[_col]):
        _se.add_data_point(float(_x), float(_y))
c12.replace_data(xy)
c12.value_axis.maximum_scale = float(np.ceil(d12["nur_wachstum_kgC"].max() / 10.0) * 10.0)
set_runs(shape(s12, "Quelle").text_frame.paragraphs[0],
         "Chapman-Richards ist die Standardform der Ertragskunde. m_max aus Walker et al. (2022), k aus Cook-Patton "
         "et al. (2020) mit Grenze nach Poorter et al. (2016); Störung an Seidl et al. (2017) orientiert, gesetzt")
set_runs(shape(s12, "TextBox 9532").text_frame.paragraphs[0],
         "Beispiel: Mischwald in Aachen (gemäßigt), ein Baum")
set_runs(shape(s12, "Formelzeichen").text_frame.paragraphs[0],
         f"m_max = {B_AC['saettigung_kgc']:.0f} kgC Sättigungsvorrat  ·  k = {de(B_AC['k'], 3)} 1/a Wachstumsrate  ·  "
         f"p = 2,0 Formparameter  ·  p₀ = {de(_SP_AC.p_disturb, 4)} 1/a Störungsrate heute  ·  γ = "
         f"{de(_SP_AC.gamma_warming, 2)} 1/K Anstieg der Störungsrate je Kelvin Hintergrunderwärmung  ·  vom verlorenen "
         f"Vorrat entweichen ε ≈ {de(_SP_AC.eps_immediate, 2)} sofort, der Rest zerfällt mit τ ≈ "
         f"{_SP_AC.tau_decay_yr:.0f} a")


def swap_picture(slide, name, png):
    pic = shape(slide, name)
    _part, rid = slide.part.get_or_add_image_part(str(png))
    pic._element.blipFill.blip.rEmbed = rid


def set_kurz(slide, name, text):
    sh = shape(slide, name)
    for extra in sh.text_frame.paragraphs[2:]:
        extra._p.getparent().remove(extra._p)
    replace_kurz(slide, text, name=name)  # also recomputes the box height, bottom edge fixed


def set_bullets(slide, name, lines):
    sh = shape(slide, name)
    paras = sh.text_frame.paragraphs
    for i, line in enumerate(lines):
        set_runs(paras[i + 1], line)
    for extra in paras[len(lines) + 1:]:
        extra._p.getparent().remove(extra._p)


def chart_text(chart, old_new: dict[str, str]) -> None:
    """Replace fixed texts (titles, manual data labels) inside a native chart."""
    for t in chart._chartSpace.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t"):
        for old, new in old_new.items():
            if t.text and old in t.text:
                t.text = t.text.replace(old, new)


# slide 38: cascade
d38 = pd.read_csv(CHART_DATA / "38_kaskade_potenzial.csv")
c38 = chart_of(O(38)).chart
cd = CategoryChartData()
cd.categories = list(c38.plots[0].categories)
cd.add_series(c38.plots[0].series[0].name, [float(v) for v in d38["kohlenstoff_GtC"]])
c38.replace_data(cd)
chart_text(c38, {"205 GtC → 78,2 GtC (38,2 % des Rohwerts)":
                 f"205 GtC → {de(KA['kohlenstoff_gtc'])} GtC ({pct(KA['anteil_bastin'], 1)} des Rohwerts)"})
set_kurz(O(38), "TextBox 4",
         "Bastins Rohwert (205 GtC) schrumpft in zwei Literaturkorrekturen auf 81 GtC (mit Boden) — bereits 2019 so "
         f"korrigiert, nicht unser Ergebnis. Unser Modell zählt nur Biomasse: {de(KA['flaeche_land_gha'], 2)} Gha "
         f"wiederbewaldbar mit {de(KA['kohlenstoff_land_gtc'])} GtC (Walker et al. 2022). Albedo-Filter und "
         "Störungspuffer ergeben "
         f"{de(KA['kohlenstoff_gtc'])} GtC auf {de(KA['flaeche_nutzbar_gha'], 2)} Gha, {pct(KA['anteil_bastin'])} von "
         f"Bastins Rohwert — {de(abs(KA['delta_t_2150_K']), 2)} K Abkühlung bis 2150 unter SSP2-4,5. Der Albedo-Filter "
         f"nimmt {pct(KA['albedo_filter_anteil_flaeche'])} der Fläche heraus: im Norden wächst der Baum zu langsam, um "
         "seine Albedo-Strafe bis 2150 auszugleichen.")
set_bullets(O(38), "TextBox 6", [
    "•  Balken = verbleibender Kohlenstoff [GtC], von links nach rechts.",
    "•  Grau: Literaturkorrekturen, nicht von uns gerechnet. Blau: eigene Modellstufen. Grün: Ergebnis.",
    f"•  Größter eigener Schritt: der Albedo-Filter ({de(KA['kohlenstoff_land_gtc'])} → "
    f"{de(KA['kohlenstoff_nach_albedo_gtc'])} GtC). Störung: "
    f"5–95 % zwischen {de(KA['band_gtc'][0])} und {de(KA['band_gtc'][1])} GtC.",
])
add_notes(O(38), "[v2] Neu gerechnet mit Waldtypen (Walker-Fläche und -Kohlenstoff, Hasler-Waldtyp), Offenland-Albedo, "
          "FaIR mit fair-calibrate 1.4.1. Störungsband: 5–95 % des Ensembles je Waldtyp an einer typischen "
          "verbliebenen Zelle, über die Typen aufsummiert — "
          "als würden alle Bäume gemeinsam getroffen. Das ist eine obere Grenze der Streuung; unabhängige Störungen "
          "über Millionen Bäume mitteln sich zum Mittelwert.")

# slide 40: recommendation map + area per species
swap_picture(O(40), "Picture 6", FIG / "p5_flaeche_und_artenwahl.png")
d40 = pd.read_csv(CHART_DATA / "40_flaeche_je_art.csv").set_index("art")
c40 = chart_of(O(40)).chart
cats = list(d40.index)  # five forest types (was: five species)
cd = CategoryChartData()
cd.categories = cats
cd.add_series(c40.plots[0].series[0].name, [float(d40.loc[c, "empfohlen_Gha"]) for c in cats])
cd.add_series(c40.plots[0].series[1].name, [float(d40.loc[c, "breitenband_Gha"]) for c in cats])
c40.replace_data(cd)
chart_text(c40, {"25,4 % mehr Kühlung": f"{pct(KARTEN['artenwahl_gewinn'], 1)} mehr Kühlung"})
set_kurz(O(40), "TextBox 4",
         f"{de(KA['flaeche_land_gha'], 2)} Gha bepflanzbare Fläche — vor Albedo-Filter und Störungspuffer (die machen "
         f"daraus {de(KA['flaeche_nutzbar_gha'], 2)} Gha). Die Farbe "
         "zeigt den Waldtyp mit der stärksten Kühlung je Hektar bis 2100, unter den Typen, die in der Nachbarschaft "
         f"vorkommen. Die Wahl bringt {pct(KARTEN['artenwahl_gewinn'])} mehr Kühlung als überall der typische Wald.")
set_bullets(O(40), "TextBox 7", [
    "•  Farbton = empfohlener Waldtyp, Sättigung = verfügbarer Anteil der 2°-Zelle. Grau: Land ohne verfügbare Fläche.",
    "•  Rechts die Fläche je Typ: voll = empfohlen, gestrichelt = typischer Wald (Hasler et al. 2024).",
    "•  Kohlenstoff ist je Ort für alle Typen gleich; die Wahl wirkt über Albedo und Störung.",
])
set_runs(shape(O(40), "Kartenquelle").text_frame.paragraphs[0],
         "Albedo: Duveiller et al. 2018 (JRC v2.0, Wald→Wiese und Wald→Acker)  |  Fläche: Walker et al. 2022  |  "
         "Waldtyp: Hasler et al. 2024  |  Grenzen: Natural Earth 1:110m (public domain)")
add_notes(O(40), "[v2] Zulässig ist ein Waldtyp in einer Zelle, wenn er in der 3×3-Nachbarschaft auf mindestens 10 % "
          "der klassifizierten Fläche der wahrscheinlichste Wald ist (Hasler et al. 2024).")

# slide 42: reverse calculation
d42 = pd.read_csv(CHART_DATA / "42_umkehrrechnung_flaeche.csv")
c42 = chart_of(O(42)).chart
cd = CategoryChartData()
cd.categories = list(c42.plots[0].categories)
cd.add_series(c42.series[0].name, [float(v) for v in d42["flaeche_Gha"]])
cd.add_series(c42.series[1].name, [float(v) for v in d42["eisfreie_landflaeche_Gha"]])
c42.replace_data(cd)
chart_text(c42, {"9,58": f"{d42['flaeche_Gha'][1]:.2f}".replace(".", ","),
                 "9,76": f"{d42['flaeche_Gha'][2]:.2f}".replace(".", ",")})
old42 = chart_of(O(42))
old42._element.getparent().remove(old42._element)
picture(O(42), FIG / "v6_temperaturpfad.png", height=4.25)
set_bullets(O(42), "TextBox 6", [
    "•  Grau: globale Erwärmung unter SSP2-4,5 (FaIR, wie im Modell).",
    f"•  Grün: dieselbe Welt mit allen nutzbaren Flächen aufgeforstet (Kaskade, "
    f"−{de(abs(KA['delta_t_2150_K']), 2)} K bis 2150).",
    "•  Rot gestrichelt: 1,5 °C. Die Flächen-Balken der Umkehrrechnung stehen weiter in dissvortrag.pptx.",
])
add_notes(O(42), f"[v2] FaIR 2.2 mit dem kalibrierten Parametersatz fair-calibrate 1.4.1 (Smith et al. 2024), Mitglied "
          f"{FAKTEN['klima']['fair_mitglied']}, nahe am Ensemble-Median: {de(FAKTEN['klima']['erwaermung_2025_K'], 2)} K "
          f"2025, {de(FAKTEN['klima']['erwaermung_2081_2100_K'], 1)} K für 2081–2100 (IPCC AR6: 2,7 K), gegenüber "
          "1850–1900. Dieselbe Baseline, gegen die die Umkehrrechnung rechnet; kritisch ist das Jahr "
          f"{UM['kritisches_jahr']}.")
set_kurz(O(42), "TextBox 4",
         "Um SSP2-4,5 ab 2050 dauerhaft unter 1,5 °C zu halten, müsste die bepflanzbare Fläche rund "
         f"{UM['vielfaches']:.0f}-fach überplant werden — {de(UM['flaeche_gha'])} Gha. "
         + ("Das ist mehr als die gesamte eisfreie Landfläche der Erde (~13 Gha, Näherung). "
            if UM["anteil_eisfrei"] > 1 else
            f"Das sind rund {pct(UM['anteil_eisfrei'])} der eisfreien Landfläche der Erde (~13 Gha, Näherung), "
            "Ackerland, Städte, Wüsten und bestehende Wälder eingeschlossen. ")
         + "Aufforstung ist damit nicht wertlos — nur keine Alleinlösung neben Emissionsminderung.")

# slide 37: t* map
swap_picture(O(37), "Picture 6", FIG / "p0_ausgleichsjahr_karte.png")
set_kurz(O(37), "TextBox 4",
         "t* je Zelle über das gesamte bepflanzbare Raster: Tropische, subtropische und gemäßigte Zellen kippen "
         f"fast alle sofort (Median {KARTEN['median_t_star_ausserhalb_boreal']:.0f}). In der Boreale wächst der Baum "
         f"langsam — dort erreichen {share_words(KARTEN['boreal_nie_anteil'])} der Zellen bis 2150 keinen Ausgleich. "
         "Genau diese Zellen zieht die Kaskade ab.")
set_bullets(O(37), "TextBox 7", [
    "•  Farbe = Jahr des dauerhaften Vorzeichenwechsels, hell früh, dunkel spät.",
    f"•  Dunkelrot: kein Ausgleich bis 2150 — {pct(KARTEN['boreal_nie_anteil'])} der borealen Zellen (50–70°).",
    "•  Das Streumuster innerhalb der Kontinente ist gewollt: die Aufteilung je Zeile ist synthetisch (Backup: Datengrundlage).",
])

# slide 41: Hasler table
tbl = next(sh for sh in O(41).shapes if sh.has_table).table
new_model = {
    "Median Albedo-Offset": (pct(HA["median_offset_pct"] / 100), "deckt sich"),
    "Fläche mit über 50 % Offset": (pct(HA["ueber_50"]), "deckt sich"),
    "davon Tropen": (pct(HA["tropen_ueber_50"], 1), "deckt sich"),
    "davon boreal": (pct(HA["boreal_ueber_50"]), "hier strenger"),
    "Kohlenstoffdichte": ("119 tC/ha", "hier knapp doppelt"),
    "Trockengebiete netto klimanegativ": (pct(HA["trockengebiet_netto_negativ"], 1), "hier kaum abbildbar"),
}
for row in tbl.rows:
    key = row.cells[0].text
    if key in new_model:
        val, verdict = new_model[key]
        set_runs(row.cells[2].text_frame.paragraphs[0], val)
        set_runs(row.cells[3].text_frame.paragraphs[0], verdict)
add_notes(O(41), "[v2] Modellspalte neu gerechnet mit Waldtypen und Walker-Fläche: nbs.aggregate.albedo_offset_summary, "
          "Anteile über 50 % Offset in 0–35° bzw. 60–70°. Einordnung gegen weitere Studien: Folie „Einordnung: andere "
          "Studien“; Zerlegung: docs/methods/abgleich-hasler-waldtypen.md.")

# slide 35: species bars instead of lines
d35 = pd.read_csv(CHART_DATA / "35_temperatur_arten.csv")
order = [("ebf_tropisch", "Immergrüner Laubwald, tropisch", "1BAF7A"),
         ("ebf_subtropisch", "Immergrüner Laubwald, subtropisch", "1BAF7A"),
         ("dbf_gemaessigt", "Sommergrüner Laubwald, gemäßigt", "EB6834"),
         ("dnf_boreal", "Lärchenwald, boreal", "EDA100"),
         ("enf_boreal", "Immergrüner Nadelwald, boreal", "2A78D6")]
years = d35["jahr"].to_numpy()
warm = []
for key, _label, _c in order:
    dt = d35[f"{key}_dT_1e-15_K"].to_numpy()
    pos = (dt > 0).nonzero()[0]
    warm.append(0 if pos.size == 0 else int(years[pos[-1]] - years[0]))
old = chart_of(O(35))
x, y, w, h = old.left, old.top, old.width, old.height
old._element.getparent().remove(old._element)
cd = CategoryChartData()
cd.categories = [lab for _k, lab, _c in order]
cd.add_series("Jahre mit Erwärmung", warm)
gf = O(35).shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, x, y, w, h, cd)
ch = gf.chart
ch.has_legend = False
ch.font.name = "Arial"
ch.font.size = Pt(12)
ch.font.color.rgb = INK
plot = ch.plots[0]
plot.gap_width = 60
plot.has_data_labels = True
plot.data_labels.font.size = Pt(12)
plot.data_labels.number_format = '0" Jahre"'
plot.data_labels.number_format_is_linked = False
plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
for i, (_k, _l, col) in enumerate(order):
    pt = plot.series[0].points[i]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = RGBColor.from_string(col)
va = ch.value_axis
va.has_major_gridlines = False
va.visible = False
va.maximum_scale = max(warm) * 1.25
ch.category_axis.format.line.color.rgb = RGBColor(0xC9, 0xC0, 0xAE)
set_kurz(O(35), "TextBox 4",
         "Das Erwärmungsfenster ist kein Ja/Nein, sondern ein Verlauf über die Breite: borealer Nadelwald wärmt "
         + ("bis 2150" if warm[4] >= int(years[-1] - years[0]) else f"{warm[4]} Jahre")
         + f", Lärchenwald {warm[3]}, gemäßigter Laubwald {warm[2]} Jahre. Subtropischer und tropischer "
         "Laubwald "
         + ("kühlen ab dem ersten Jahr — kein Schnee, viel Wachstum." if warm[0] == warm[1] == 0 else
            f"wärmen {warm[1]} bzw. {warm[0]} Jahre."))
set_bullets(O(35), "TextBox 6", [
    "•  Balken = Jahre, in denen der Baum netto wärmt, bevor er dauerhaft kühlt.",
    "•  Jeder Waldtyp an seiner mittleren Zelle, gepflanzt 2025, volles Modell.",
    "•  Je Baum; im Norden wiegt der Schnee unter der Krone schwerer als der langsame Zuwachs.",
])
add_notes(O(42), "[v2] Neu gerechnet mit Waldtypen (Walker-Fläche) und Offenland-Albedo (nbs.potential.reverse_1p5).")

for sh in O(44).shapes:
    if sh.has_text_frame:
        for para in sh.text_frame.paragraphs:
            if "78,2 GtC nutzbares Potenzial" in para.text:
                set_runs(para, f"•  Fläche: {de(KA['flaeche_land_gha'], 2)} Gha bepflanzbar, "
                         f"{de(KA['flaeche_nutzbar_gha'], 2)} Gha nutzbar, {de(KA['kohlenstoff_gtc'])} GtC.")
            elif "t* = 2071 für die boreale Fichte" in para.text:
                _tf = FAKTEN["boreal_referenz"]["t_star"]
                set_runs(para, "•  Zeit bis zur Netto-Kühlung: "
                         + (f"t* = {_tf}" if _tf is not None else "nicht vor 2150")
                         + " für den borealen Mischwald (Joensuu), sofort in den Tropen.")
            elif "59,5 % Wahrscheinlichkeit" in para.text:
                set_runs(para, f"•  Risiko: {pct(FAKTEN['boreal_referenz']['stoerung_50_jahre'], 1)} Wahrscheinlichkeit "
                         "mindestens einer Störung in 50 Jahren.")


# ---- DAC (Vergleich): own model, nbs.dac / nbs.dac_compare / nbs.dac_figures ----
DA = FAKTEN["dac"]


def movie(slide, path: Path, poster: Path, *, width=10.4, top=1.12, left=None):
    """Embedded mp4 with a poster frame (what the PDF export shows)."""
    from PIL import Image

    w_px, h_px = Image.open(poster).size
    h = width * h_px / w_px
    x = (PRS.slide_width / 914400 - width) / 2 if left is None else left
    return slide.shapes.add_movie(str(path), Inches(x), Inches(top), Inches(width), Inches(h),
                                  poster_frame_image=str(poster), mime_type="video/mp4")


def _y(year) -> str:
    return "nie" if year is None else str(year)


d1 = new_slide(VERGLEICH, "DAC: Strom je Tonne, je nach Klima")
picture(d1, FIG / "d1_dac_energie.png", height=4.55)
kurz(d1, "Sorbens-DAC braucht Wärme um 110 °C und Strom für Gebläse und Vakuum. Mit einer Wärmepumpe wird daraus "
     f"nur Strom: {de(DA['strom_mwh']['min'])}–{de(DA['strom_mwh']['max'])} MWh je t CO₂. Feuchte Luft kostet mehr, "
     "kalte Luft senkt den Wirkungsgrad der Wärmepumpe. Wo der kälteste Monat unter −15 °C liegt "
     f"({pct(DA['zu_kalt_anteil_land'])} des Landes), ist Sorbens-DAC nicht vorgesehen.")
quelle(d1, "Niveau: premise, Sorbens-DAC 100 kt/a (0,5 MWh Strom + 1,5 MWh Wärme je t). Klimaabhängigkeit und "
       "Wärmepumpe: Sendi et al. (2022), One Earth 5, 1153. Klima: CRU TS 4.09, 2011–2020.", x=0.42, y=6.2, w=6.1)
add_notes(d1, "Sprechertext: Die Energie ist der Hebel. Ich nehme das Niveau aus der premise-Datenbank und lasse es mit "
          "dem Klima am Ort schwanken, so wie Sendi et al. es für denselben Prozess (Amin-Sorbens, Dampf-unterstützte "
          "Temperatur-Vakuum-Wechseladsorption) mit stündlichem Wetter weltweit gerechnet haben. Deren vier "
          "Klimaklassen treffe ich auf 0,01 MWh genau: Wärmebedarf +"
          f"{pct(DA['fit']['a_rh_pro_10pp'])} je 10 Prozentpunkte Luftfeuchte, +{pct(DA['fit']['a_t_pro_10k'])} je 10 K; "
          "Wärmepumpe mit 50 % des Carnot-Werts (COP 1,5–2,0). Zum Vergleich: Climeworks meldet für Hinwil 3,3 MWh "
          "Wärme und 0,7 MWh Strom je t, also etwa doppelt so viel Wärme wie premise — das ist eine Sensitivität. "
          "Details: docs/methods/dac-modell.md.")

d2 = new_slide(VERGLEICH, "DAC wird mit dem Strom sauber")
movie(d2, FIG / "d2_dac_wirkungsgrad.mp4", FIG / "d2_dac_wirkungsgrad_poster.png", width=10.6)
_wg = DA["wirkungsgrad_median"]
kurz(d2, "Netto-Wirkungsgrad: welcher Anteil der entnommenen Tonne nach den eigenen Emissionen übrig bleibt. Im "
     f"Median {pct(_wg['2025'])} im Jahr 2025, {pct(_wg['2030'])} 2030, {pct(_wg['2040'])} 2040 — so schnell wird der "
     "Strom im Szenario sauber. Wo heute schon Wasserkraft oder Kernkraft liefert, liegt DAC sofort über 90 %.")
quelle(d2, "Strom: premise mit REMIND-EU, SSP2-NDC; je Land der Mix seiner REMIND-Region. GWP100, IPCC 2021. Video: "
       "ein Bild je Jahr, 2025–2100; Standbild 2040.", x=0.42, y=6.2, w=6.1)
add_notes(d2, "Sensitivitäten (Median): Wärme aus Industriedampf statt Wärmepumpe "
          f"{pct(DA['wirkungsgrad_median_dampf']['2025'])} (2025) / {pct(DA['wirkungsgrad_median_dampf']['2050'])} (2050); "
          "mit den gemessenen Climeworks-Energiewerten "
          f"{pct(DA['wirkungsgrad_median_climeworks']['2025'])} (2025) / "
          f"{pct(DA['wirkungsgrad_median_climeworks']['2050'])} (2050) — heute also im Median netto emittierend. "
          "Achtung: REMIND-EU dekarbonisiert sehr schnell, Deutschland etwa "
          f"{de(DA['strom_kg_pro_kwh_2020_2030_2050']['DE'][0], 2)} → "
          f"{de(DA['strom_kg_pro_kwh_2020_2030_2050']['DE'][1], 2)} kg CO₂e/kWh von 2020 bis 2030.")

d3 = new_slide(VERGLEICH, "Baum oder DAC: wer entnimmt wo sauberer?")
movie(d3, FIG / "d3_baum_oder_dac.mp4", FIG / "d3_baum_oder_dac_poster.png", width=9.9, left=0.42)
_leg = d3.shapes.add_picture(str(FIG / "d3_legende.png"), Inches(10.4), Inches(1.5), height=Inches(2.6))
_um = DA["umstieg"]
kurz(d3, "Heute gewinnt fast überall der Baum, außer im Norden Europas mit sauberem Strom. Danach kippt es Land für "
     f"Land: Deutschland {_y(_um['DE']['median_jahr'])}, USA {_y(_um['US']['median_jahr'])}, Brasilien "
     f"{_y(_um['BR']['median_jahr'])}, China {_y(_um['CN']['median_jahr'])}, Indien {_y(_um['IN']['median_jahr'])}. "
     "Vorn bleibt der Baum vor allem in den Tropen. Im Norden kühlt oft keins von beiden: Der Baum wärmt, für DAC "
     "ist es zu kalt.")
quelle(d3, "Je 2°-Zelle die Option, die auf dem größten Teil der bepflanzbaren Fläche netto mehr übrig lässt. Baum: "
       "empfohlene Art, 1 − Albedo-Offset in 2150. Video 2025–2100, Standbild 2040.", x=0.42, y=6.2, w=6.1)
add_notes(d3, "Sprechertext: Die Frage ist nicht „Baum oder Maschine“, sondern „wann und wo“. Jahr für Jahr: Wer "
          "lässt von einer entnommenen Tonne netto mehr übrig? Beim Baum frisst die Albedo einen Teil, bei DAC die "
          "Emissionen von Strom und Anlage. Mit sauberem Strom wird DAC fast überall besser als der Baum — außer in den "
          "Tropen, wo der Baum ohne Albedo-Strafe wächst, und im Norden, wo keins von beiden funktioniert.")

d4 = new_slide(VERGLEICH, "Ab wann DAC sauberer entnimmt")
picture(d4, FIG / "d4_ab_wann_dac.png", height=4.55)
_an = DA["dac_besser_anteil"]
_twh = f"{round(DA['strom_mwh']['median'] * 10) * 100:,.0f}".replace(",", " ")  # MWh/t x 1e9 t, rounded
kurz(d4, f"Auf der bepflanzbaren Fläche ist DAC 2025 auf {pct(_an['2025'])} besser, 2030 auf {pct(_an['2030'])}, 2040 "
     f"auf {pct(_an['2040'])}, ab 2050 auf rund {pct(_an['2050'])}. Ein Vergleich je Tonne, nicht der Menge: 1 Gt CO₂ "
     f"mit DAC braucht rund {_twh} TWh Strom.")
quelle(d4, "Rechts: Anteil der bepflanzbaren Fläche je bester Option. Gleiches Modell wie die Vorfolie.",
       x=0.42, y=6.2, w=6.1)
add_notes(d4, f"{pct(DA['zu_kalt_anteil_bepflanzbar'])} der bepflanzbaren Fläche ist für Sorbens-DAC zu kalt (boreal). "
          "Was der Vergleich nicht enthält: Kosten, Flächenbedarf, Tempo, Dauerhaftigkeit der Speicherung, Mengen. Der "
          "Strom für eine Gigatonne entspricht rund 5 % der heutigen Weltstromerzeugung. Methode: "
          "docs/methods/dac-modell.md.")

# static snapshots of the two clips, for the backup / the PDF
dB2 = new_slide(VERGLEICH, "DAC-Wirkungsgrad: vier Momentaufnahmen")
picture(dB2, FIG / "d2_dac_wirkungsgrad.png", height=5.2)
dB3 = new_slide(VERGLEICH, "Baum oder DAC: vier Momentaufnahmen")
picture(dB3, FIG / "d3_baum_oder_dac.png", height=5.2)
add_notes(O(44), "[v2] Ersetzt durch das eigene DAC-Modell (vier Folien davor).")


# ---- Vergleich, Neuordnung 2026-10-05: nicht genug Land -> beides -> die Maschine als Messlatte ----
VG = FAKTEN["vergleich"]


def big_number(slide, x, y, w, number, label, color):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(1.9))
    tf = box.text_frame
    tf.word_wrap = True
    p0 = tf.paragraphs[0]
    r = p0.add_run()
    r.text = number
    r.font.size = Pt(40)
    r.font.bold = True
    r.font.color.rgb = RGBColor.from_string(color)
    p1 = tf.add_paragraph()
    r = p1.add_run()
    r.text = label
    r.font.size = Pt(15)
    r.font.color.rgb = INK
    return box


# opening slide 2: the need, named once
kurz(O(2), f"Selbst im niedrigsten Szenario (Very Low, 1,6 °C in 2100) müssen bis 2150 rund "
     f"{VG['vl_gesamt_gtco2']:.0f} Gt CO₂ wieder aus der Luft — etwa die Hälfte über Land und Boden, die andere "
     "Hälfte technisch.", x=8.95, w=4.0, bottom=6.6)
add_notes(O(2), "[v2] Das ist der Bedarf, gegen den der Vortrag am Ende rechnet (Folie „Bäume reichen nicht“). Werte: "
          "Carbon Brief (Hausfather 2026) nach den CMIP7-Markerszenarien (van Vuuren et al. 2026); Aufteilung "
          "technisch/Land aus dem Balkendiagramm abgelesen (±10 Gt).")

v1 = new_slide(VERGLEICH, "Wo Bäume hinkönnen")
picture(v1, FIG / "v1_wo_baum_wo_dac.png", height=4.55)
kurz(v1, "Von einem Baum an zwei Orten zur ganzen Erde: Wiederbewaldbar sind "
     f"{de(VG['bepflanzbar_kuehlt_gha'] + VG['bepflanzbar_waermt_gha'], 2)} Gha — nicht "
     "Wald, Acker, Stadt oder offene Landschaft. Davon kühlen "
     f"{de(VG['bepflanzbar_kuehlt_gha'], 2)} Gha; auf {de(VG['bepflanzbar_waermt_gha'], 2)} Gha — im Norden und in "
     "trockenen Gebieten — frisst die Albedo mehr, als der Baum bis 2150 an CO₂ bindet. Im Norden ist es für DAC "
     "oft auch zu kalt.")
quelle(v1, "Baum gepflanzt 2025, bester zulässiger Waldtyp, bewertet 2150. Fläche: Walker et al. 2022 "
       "(Wiederbewaldung ohne Acker und Siedlung), Waldtyp: Hasler et al. 2024. DAC: kältester Monat unter −15 °C (Sendi et al. 2022).", x=0.42, y=6.2, w=6.1)

LIT = FAKTEN["literatur"]["dieses_modell"]
v1b = new_slide(VERGLEICH, "Einordnung: andere Studien")
picture(v1b, FIG / "v1b_literatur.png", height=4.1)
kurz(v1b, "Alle Studien sehen dasselbe: Die Albedo frisst einen großen Teil des Kohlenstoffnutzens. Wir liegen am "
     "strengen Ende, aus drei Gründen: Die wiederbewaldbare Fläche liegt oft im Norden und im Trockenen; unser "
     "Kohlenstoff ist aus Messungen hochgerechnet, etwa halb so viel wie im Erdsystemmodell; und wir bewerten 2150 "
     f"bei steigendem CO₂. Mit Haslers statischer Formel kämen wir auf {pct(LIT['statisch'])}.")
quelle(v1b, "Riley et al. 2025, Nat. Commun. 16, 8810; Weber et al. 2024, Science 383, 860; Fahrenbach et al. 2026, "
       "Commun. Earth Environ. 7, 204; Hasler et al. 2024, Nat. Commun. 15, 2275; Liang et al. 2025, Sci. Adv. "
       "adn7915; Rohatyn et al. 2022, Science 377, 1436", x=0.42, y=6.2, w=6.1)
add_notes(v1b, "Einheit: welcher Anteil des reinen Kohlenstoffnutzens nach der Albedo übrig bleibt. Gemeinsam haben "
          "alle: den Rückfluss von CO₂ aus Ozean und Land über eine Impulsantwort (Hasler: Joos-Mittel, Restanteil "
          "über 100 Jahre). Was dieses Modell zusätzlich abbildet: (1) den Zeitverlauf — Wachstum und Kronenschluss "
          "Jahr für Jahr, bewertet als Erwärmung in einem genannten Jahr; Hasler vergleicht maximalen Kohlenstoff mit "
          "maximaler Albedo und nennt den Zeitverlauf selbst als offene Lücke („ignores the time frame over which "
          "both unfold … additional work is urgently needed“); (2) einen Hintergrund, der sich ändert: SSP2-4,5 statt "
          "fester 400 ppm, mit einem Kohlenstoffkreislauf, dessen Senken nachlassen (FaIR); (3) Störungen, die mit "
          "der Erwärmung zunehmen (Hasler: keine). Liang et al. rechnen Klima und Feuer ebenfalls dynamisch und "
          "landen mit 30 % am nächsten. Fahrenbach et al. (CESM2, voll gekoppelt) enthalten zusätzlich die Kühlung "
          "durch Verdunstung in den Tropen, die unser Modell nicht hat — dort sind wir eher zu streng. Riley et al. "
          "werten bestehende Projekte aus, die schon dort liegen, wo Albedo wenig kostet. Woher die Abweichungen kommen: "
          "Hasler — vor allem die Fläche (auf Walkers Karte rechnet er selbst mit mehr Offset), dann der Horizont 2150 "
          "statt Endzustand. Fahrenbach — vor allem die Kohlenstoffmenge: CESM2 lässt etwa doppelt so viel wachsen "
          "(≈ 100 statt 51 t C/ha); mit dieser Menge kämen auch wir auf rund 65 %. Gegenprobe: Die ganze Entnahme als "
          "Zeitreihe in einen vollen FaIR-Lauf gegeben, liefert dasselbe wie unsere Rechnung (18 % gegen 17 % bis "
          "2100). Eine Annahme mit Gewicht: Störungen lichten den Wald, der dann weniger Licht schluckt — das bringt "
          "bis 2100 rund 20 Prozentpunkte zurück. Warum wir strenger sind: 2150 ist der Baum längst gesättigt, der größte Teil "
          "seiner Entnahme liegt Jahrzehnte zurück, die Albedo wirkt dagegen voll; dazu die Fläche (Walker et al. "
          "2022), boreal- und trockengebietslastig — für genau diese Karte findet Hasler auf 65 % der Fläche über "
          "50 % Offset, wir mit seiner Formel 73 %. Grenze dieses Modells: Die Schneedecke ist statisch, boreal fällt "
          "die Albedo-Strafe späterer Jahrzehnte daher eher zu hoch aus. Methode: "
          "docs/methods/abgleich-hasler-waldtypen.md.")

v2 = new_slide(VERGLEICH, "Bäume reichen nicht")
picture(v2, FIG / "v2_bedarf_cmip7.png", height=4.3)
kurz(v2, f"Alle nutzbaren Flächen bewaldet binden bis 2150 rund {VG['baeume_brutto_gtco2']:.0f} Gt CO₂, nach Albedo "
     f"netto {VG['baeume_netto_gtco2']:.0f} Gt — {pct(VG['anteil_netto_an_vl'])} dessen, was selbst das niedrigste "
     "Szenario braucht. Der Rest muss technisch kommen. Die Frage ist also nicht Baum oder Maschine, sondern: "
     "welche Tonne wann und wo.")
quelle(v2, "Bedarf: Carbon Brief nach CMIP7 (van Vuuren et al. 2026), Aufteilung aus der Grafik auf Folie 2. Bäume: "
       "Kaskade dieses Modells, netto = mit Albedo.", x=0.42, y=6.2, w=6.1)
add_notes(v2, f"Bäume brutto {VG['baeume_brutto_gtco2']:.0f} Gt CO₂ = Kaskade ({de(KA['kohlenstoff_gtc'])} GtC × 44/12). Netto: um das "
          "Verhältnis der Kühlung mit und ohne Albedo auf den behaltenen Flächen verringert. Gegen den Landanteil des "
          f"VL-Szenarios ({VG['vl_land_gtco2']:.0f} Gt) sind es {pct(VG['baeume_netto_gtco2'] / VG['vl_land_gtco2'])}. "
          "Die Umkehrrechnung (1,5 °C unter SSP2-4,5) liegt jetzt im Backup.")

set_title(d1, "Was eine Maschine braucht")
v3 = new_slide(VERGLEICH, "Heute: der Holzweg")
picture(v3, FIG / "v3_heute_sechs_orte.png", height=4.55)
_neg = [n for n, o in VG["orte"].items() if o["dac_2020"] < 0]
kurz(v3, "Netto-Wirkungsgrad: welcher Anteil einer entnommenen Tonne nach den eigenen Emissionen übrig bleibt. Mit "
     f"dem Strom von 2020 emittiert DAC in {', '.join(_neg[:-1])} und {_neg[-1]} mehr, als es entnimmt; besser als der "
     f"Baum ist es nur auf {pct(VG['dac_2020_besser_anteil'])} der bepflanzbaren Fläche. Heute sind die Ingenieure "
     "auf dem Holzweg.")
quelle(v3, "Baum: 1 − Albedo-Offset in 2150, empfohlene Art. DAC: premise-Datensatz, Strommix 2020 der jeweiligen "
       "REMIND-Region, Energie nach Klima (Folie davor).", x=0.42, y=6.2, w=6.1)
add_notes(v3, "Ausnahme Joensuu: Dort wärmt der Baum, und der finnische Strom ist schon heute sauber. Auf "
          f"{pct(VG['dac_2020_netto_emittierend_land'])} der Landfläche wäre DAC mit dem Strom von 2020 netto "
          "emittierend.")

v4 = new_slide(VERGLEICH, "DAC fährt mit der Energiewende mit")
picture(v4, FIG / "v4_zeit_sechs_orte.png", height=4.55)
_o = VG["orte"]
kurz(v4, "Ohne eigenes Zutun wird DAC besser, weil der Strom sauberer wird — im Szenario mit heutigen Zusagen, ohne "
     f"Zusatzpolitik. Der Baum wird überholt: Aachen {_y(_o['Aachen']['umstieg'])}, Krakau "
     f"{_y(_o['Krakau']['umstieg'])}, Peking {_y(_o['Peking']['umstieg'])}, Manaus {_y(_o['Manaus']['umstieg'])}, "
     f"Kinshasa {_y(_o['Kinshasa']['umstieg'])}.")
quelle(v4, "Strom: premise mit REMIND-EU, SSP2-NDC. Baum: im jeweiligen Jahr gepflanzt.", x=0.42, y=6.2, w=6.1)
add_notes(v4, "Achtung, Annahme: REMIND-EU dekarbonisiert schnell (Deutschland 0,42 → 0,09 kg CO₂e/kWh von 2020 bis "
          "2030). Mit langsamerer Energiewende verschieben sich die Jahre nach hinten. Mit den gemessenen "
          "Climeworks-Energiewerten statt premise ebenfalls (Backup, Methodendoku).")

set_title(d4, "Die Maschine wird zur Messlatte")
replace_kurz(d4, "Weil wir DAC ohnehin brauchen, muss jede Baum-Tonne mindestens so gut sein wie die Maschinen-Tonne. "
             f"Diese Messlatte steigt: 2030 liegt der Baum auf {pct(1 - DA['dac_besser_anteil']['2030'] - DA['keins_kuehlt_anteil']['2030'])} "
             f"der bepflanzbaren Fläche darüber, ab 2050 nur noch auf {pct(1 - DA['dac_besser_anteil']['2050'] - DA['keins_kuehlt_anteil']['2050'])} — "
             "vor allem in den Tropen.")
add_notes(d4, "Messlatte = DAC am selben Ort mit dem Strom seiner Region (wenn jedes Land seine eigene Entnahme "
          "leistet). Würde Entnahme weltweit gehandelt, wäre die Messlatte DAC am besten Standort (z. B. Norwegen, "
          "schon heute rund 90 %) — dann wäre der Baum fast überall sofort unterlegen. "
          f"{pct(DA['zu_kalt_anteil_bepflanzbar'])} der bepflanzbaren Fläche sind für Sorbens-DAC zu kalt.")

v8 = new_slide(VERGLEICH, "Beides — in der richtigen Reihenfolge")
_gt_tree = VG["gt_pro_jahr_baeume_gha"]
big_number(v8, 0.6, 1.4, 5.9, f"{de(_gt_tree, 1)} Gha", "Land je Gt CO₂ pro Jahr — Bäume (im Mittel bis 2150). "
           "Ein Vorrat, der sich füllt und dann sättigt.", GREEN)
big_number(v8, 6.9, 1.4, 5.9, f"{_twh} TWh", "Strom je Gt CO₂ pro Jahr — DAC, etwa 5 % der heutigen "
           "Weltstromerzeugung. Läuft, solange sie betrieben wird.", "01A8A8")
big_number(v8, 0.6, 3.6, 12.2, "Bäume jetzt, DAC mit sauberem Strom",
           "Bäume brauchen Jahrzehnte bis zur vollen Wirkung — sie müssen zuerst. DAC lohnt sich erst, wo der Strom "
           "sauber ist, und wächst dann in die Rolle hinein.", DARK)
kurz(v8, "Baum und Maschine konkurrieren nicht um Fläche, sondern um sauberen Strom und Geld. Bäume nur dort, wo sie "
     "kühlen; DAC dort, wo es warm genug und der Strom sauber ist; im hohen Norden keins von beiden.",
     x=0.42, w=12.5)


# ---- Klima, kompakt (2026-10-05): was der Luft fehlt -> eine Währung -> träge Erde ----
kA = new_slide(KLIMA, "Was der Luft wirklich fehlt")
picture(kA, FIG / "k5_luft_balken_linie.png", height=4.55)
kurz(kA, "Balken: was der Baum geholt hat, wie im Kapitel Bäume. Linien: was der Luft davon wirklich fehlt, wenn "
     "Ozean und Land antworten. Von einem Jahr fehlt nach 20 Jahren noch 60 %, nach 75 Jahren 44 % — über alle "
     "Jahre bis 2150 weniger als die Hälfte.")
quelle(kA, "Wachstum wie im Kapitel Bäume (typischer Wald je Ort, Störung mit heutiger Rate). Rückgabe: Impulsantwort g_C "
       "nach Joos et al. (2013).", x=0.42, y=6.2, w=6.1)
add_notes(kA, "Frage 1: Wie lange fehlt das CO₂ der Luft? Sprechertext: Links ein einziges Jahr Zuwachs, 2050. Am Baum "
          "bilanziert wäre es für immer weg, gestrichelt. Aber Luft, Ozean und Landbiosphäre stehen im Austausch: "
          "Fehlt oben CO₂, nehmen Ozean und Land weniger auf und geben zurück. Was übrig bleibt, die durchgezogene "
          "Linie, heißt g_C. Rechts dasselbe für jedes Jahr, aufsummiert.")

kB = new_slide(KLIMA, "Kohlenstoff und Licht in einer Währung")
picture(kB, FIG / "k10_antrieb_zwei_orte.png", height=4.1)
equation(kB, r"\varphi_{CO_2}(t) = A_{CO_2}(t)\,\Delta m_{CO_2}(t)", x=0.42, y=5.3, w=6.2, h=0.6,
         groups={"φ_CO2": GREEN, "A_CO2": GREEN, "m_CO2": GREEN, "CO_2": GREEN}, chars={"φ": GREEN})
equation(kB, r"\varphi_\alpha(t) = \tau_{atm}\,\Delta\dot Q(t)\,/\,A_{Erde}", x=0.42, y=5.95, w=6.2, h=0.6,
         groups={"φ_α": ORANGE, "Q̇": ORANGE}, chars={"φ": ORANGE, "α": ORANGE})
kurz(kB, "Antrieb: wie viele Watt je m² Erde zusätzlich drin bleiben (wärmt) oder hinausgehen (kühlt). CO₂: was der "
     "Luft fehlt, mal Wirkung je kg — die sinkt, je voller die Atmosphäre ist "
     f"({de(FAKTEN['a_co2']['start'], 2)} → {de(FAKTEN['a_co2']['ende'], 2)}·10⁻¹⁵ W/m² je kg bis 2150). Albedo: das "
     "zusätzlich geschluckte Licht, verteilt auf die ganze Erde.")
add_notes(kB, "Frage 2: Wie stark wirkt jedes Kilogramm? Wirkung je kg nach Myhre et al. (1998), 5,35·ln(C/C₀), mit dem "
          "CO₂-Hintergrund aus SSP2-4,5 (FaIR); Albedo mit τ_atm ≈ 0,8 für den Weg nach oben. Auch die Rückgabe durch "
          "Ozean und Land hängt am Szenario; ab hier rechnet das Modell sie mit FaIR "
          f"({pct(FAKTEN['a_co2']['g_c_fair_2100'])} statt {pct(FAKTEN['a_co2']['g_c_joos_2100'])} eines Impulses 2025 "
          "im Jahr 2100 noch in der Luft). Energiebilanz und Herleitung: Backup.")

kC = new_slide(KLIMA, "Die Erde erwärmt sich träge")
picture(kC, FIG / "k12b_traege_erde_ergebnis.png", height=4.55)
kurz(kC, "Ein zusätzliches Watt je m² erwärmt die Erde nicht sofort: die Oberfläche in Jahren, den tiefen Ozean über "
     "Jahrhunderte (links). So wird aus dem Antrieb die Temperatur (rechts). Mit dem Klimasystem kühlt der Wald "
     f"{both(ab_wann, AC['t_star'], JO['t_star'])} — in Joensuu aber 2150 nur mit "
     f"{pct(JO['delta_t_2150_K'] / AC['delta_t_2150_K'])} der Kühlung von Aachen.")
quelle(kC, "Links: Antwort des Modell-FaIR auf 1 W/m² dauerhaft (fair-calibrate 1.4.1, Mitglied "
       f"{FAKTEN['klima']['fair_mitglied']}). Rechts: Mischwald, gepflanzt 2025, SSP2-4,5, volles Modell.",
       x=0.42, y=6.2, w=6.1)
add_notes(kC, "Warum ein Klimamodell und nicht GWP100 wie in der Ökobilanz: GWP100 rechnet jede Tonne mit einer festen "
          "Impulsantwort bei festem CO₂-Hintergrund und mittelt über 100 Jahre — egal, wann die Tonne fällt. Die "
          "Albedo passt nur über eine Umrechnung hinein. Wir geben stattdessen alles in einen Lauf von FaIR: die "
          "Entnahme aller Bäume als negative Emission, die Albedo als Antrieb. FaIR rechnet dann selbst, dass sich "
          "die Senken füllen, dass jedes kg bei mehr CO₂ schwächer wirkt und wie die Temperatur folgt — und das "
          "Ergebnis ist eine Temperatur in einem genannten Jahr, keine Tonne CO₂-Äquivalent. Für einen einzelnen "
          "Baum (10⁻¹⁵ K) nutzen wir FaIRs Antwort auf einen kleinen Puls; für die ganze Fläche liefern beide Wege "
          "dasselbe (18 % gegen 17 % bis 2100).")
add_notes(kC, "Rechnerisch ist die Temperatur die Summe aller Jahre Antrieb, jedes gewichtet mit der Antwort der Erde: "
          "ΔT(t) = ∫ g_T(t−t′) φ(t′) dt′ — dasselbe Prinzip wie beim CO₂. Größenordnung: bis 2150 etwa "
          f"{sci_de(AC['delta_t_2150_K'])} K je Baum in Aachen, {sci_de(JO['delta_t_2150_K'])} K in Joensuu. Seit das "
          "Tempo der Albedo an Messungen angepasst ist (Williams et al. 2026: Hälfte nach 40 Jahren), kühlt auch "
          "Joensuu vom ersten Jahr an — der Baum bindet, bevor sein Kronendach den Schnee verdeckt.")

# ---- order ---------------------------------------------------------------
NEW = {"kA": kA, "kB": kB, "kC": kC, "b6": b6, "b8a": b8a, "b8": b8, "b9": b9, "b10": b10, "k11": k11, "k3p": k3p, "d1": d1, "d2": d2, "d3": d3,
       "d4": d4, "n1": n1, "v1": v1, "v1b": v1b, "v2": v2, "v3": v3, "v4": v4, "v8": v8, "k4": k4, "k7": k7, "k8": k8, "k10": k10, "k12": k12,
       "k13": k13, "k14": k14}
MAIN = [1, 2, 3, 4, 5, 6,
        7, 8, 9, 10, 11, 12, 34, "b6", 13, 14, "b8a", "b8", "b9", "b10",
        17, "kA", "kB", "kC", "k13", "k14",
        39, "v1", "v1b", "v2", "d1", "v3", "v4", "d4", "v8", 47, "n1", 48]
# ---- source lines: name the KIND of data, not only where it comes from ------
# Messdaten (measured; say if interpolated or averaged) / Modellergebnis
# übernommen (another model's output) / Annahme (set by us) / eigene Rechnung
# (this model) / Schema (illustration, no data). One place, applied last.
_CRU = "Messdaten CRU TS 4.09 (Wetterstationen, auf 0,5° interpoliert)"
_WALKER = "Walker et al. 2022 (Modellergebnis: aus Inventur- und Satellitendaten hochgerechnet)"
_HASLER_T = "Hasler et al. 2024 (Klassifikation aus Satelliten-Landbedeckung MODIS)"
_CP = "Cook-Patton et al. 2020 (Modellergebnis: aus über 13 000 Feldmessungen hochgerechnet)"
QUELLEN = {
    2: "Modellergebnisse übernommen: CMIP7-Szenarien aus Integrated-Assessment-Modellen (van Vuuren et al. "
       "2026); Grafik: Carbon Brief (Hausfather 2026).",
    4: "Eigene Rechnung mit dem Modellbaum (Folie „C-Aufnahme im Modell“); Bedarf: Modellergebnis CMIP7 (Folie 2); "
       "Bäume heute: Hochrechnung aus Inventurdaten (Crowther et al. 2015).",
    5: "Bastin et al. 2019, Science 365, 76 (Modellergebnis: aus Satelliten-Stichproben der Baumbedeckung "
       "hochgerechnet); Korrektur: Kommentare von Veldman et al. und Friedlingstein et al. 2019, Science 366.",
    8: "Schema; Übersicht der Waldwirkungen aus der Literatur (Lawrence et al. 2022; Hasler et al. 2024).",
    9: "Schema; Übersicht der Waldwirkungen aus der Literatur (Lawrence et al. 2022; Hasler et al. 2024).",
    11: "Schema mit illustrativen Verläufen, keine Messdaten; Flussbegriffe nach Chapin et al. (2006).",
    12: "Form: Chapman-Richards (Standard der Ertragskunde). m_max: " + _WALKER + "; k: " + _CP + ", begrenzt durch "
        "Feldmessungen (Poorter et al. 2016). Störung: Annahme (an Seidl et al. 2017 orientiert); Anstieg mit "
        "Erwärmung aus Modellprojektionen für Europa (Grünig et al. 2026).",
    34: "Waldtyp: " + _HASLER_T + "; Fläche: " + _WALKER + "; beides auf 0,5° zusammengefasst.",
    "b6": "Eigene Rechnung: Wachstumskurve mit Kohlenstoff der Zelle (" + _WALKER + ") und Tempo (" + _CP + "); "
          "Störung: Annahme, heutige Rate.",
    13: "Schema mit gerundeten Beispielwerten, keine Daten.",
    14: "Schema mit gerundeten Beispielwerten, keine Daten.",
    "b8a": "Messdaten: Satellit MODIS, Albedo von Wald gegen Offenland aus benachbarten Flächen verglichen, auf 0,5° "
           "gemittelt (Duveiller et al. 2018); Einstrahlung aus demselben Datensatz. Grau: keine lokale Messung.",
    "b8": "Messdaten wie Vorfolie, Monat für Monat multipliziert (eigene Rechnung); typischer Wald je Zelle. Grau: "
          "keine lokale Messung, im Modell mit dem Median des Breitenbandes gefüllt (Annahme).",
    "b9": "Eigene Rechnung. Links wie „Was der Baum der Luft entnimmt“; rechts Messdaten der Karte × Kronenschluss — "
          "Tempo an Satellitenmessungen angepasst (Williams et al. 2026).",
    "b10": "Eigene Rechnung. Naiv: alles entnommene CO₂ fehlt der Luft für immer; Wirkung je kg: Lehrbuchwert "
           "A_CO₂ = 1,76·10⁻¹⁵ W m⁻² kg⁻¹ (IPCC AR6, aus Strahlungstransfer-Modellen) über A_Erde = 5,1·10¹⁴ m².",
    "kA": "Eigene Rechnung; Rückgabe an Ozean und Land: Modellergebnis, Impulsantwort als Mittel mehrerer Erdsystem- "
          "und Kohlenstoffkreislaufmodelle (Joos et al. 2013).",
    "kB": "Eigene Rechnung; Wirkung je kg: Formel 5,35·ln(C/C₀) (Myhre et al. 1998, aus Strahlungstransfer-Modellen); "
          "CO₂-Pfad SSP2-4,5: Modellergebnis FaIR.",
    "kC": "Links Modellergebnis: FaIR, ein Klima-Emulator, kalibriert auf Messungen und CMIP6-Modelle (fair-calibrate "
          f"1.4.1, Mitglied {FAKTEN['klima']['fair_mitglied']}). Rechts eigene Rechnung: Mischwald, gepflanzt 2025, "
          "SSP2-4,5.",
    "k13": "Eigene Rechnung, volles Modell, SSP2-4,5; Anstieg der Störung mit der Erwärmung aus Modellprojektionen "
           "für Europa (Grünig et al. 2026).",
    "k14": "Eigene Rechnung, volles Modell, SSP2-4,5; jede Stufe schaltet einen Prozess dazu.",
    "v1": "Eigene Rechnung, Baum gepflanzt 2025, bewertet 2150. Fläche: " + _WALKER + "; Waldtyp: Hasler et al. "
          "2024. DAC-Grenze: Annahme aus Sendi et al. 2022 (kältester Monat unter −15 °C), angewendet auf " + _CRU + ".",
    "v1b": "Literaturwerte: Riley 2025 (Auswertung bestehender Projekte); Weber 2024, Fahrenbach 2026 "
           "(Erdsystemmodelle); Hasler 2024, Rohatyn 2022 (statische Bilanzen aus Satelliten- und Kartendaten); "
           "Liang 2025 (dynamisches Vegetationsmodell). Dieses Modell: eigene Rechnung.",
    "v2": "Bedarf: Modellergebnis CMIP7-Szenarien (van Vuuren et al. 2026), Aufteilung aus der Grafik abgelesen "
          "(±10 Gt). Bäume: eigene Rechnung (Kaskade), netto = mit Albedo.",
    "d1": "Energie je t: Modellergebnis premise (Sorbens-DAC, aus ecoinvent) mit Prozessmodell von Sendi et al. 2022 "
          "für Klima und Wärmepumpe (übernommen); Klima: " + _CRU + ", Mittel 2011–2020.",
    "v3": "Eigene Rechnung. Baum: 1 − Albedo-Offset 2150. DAC: Ökobilanz mit premise (Modellergebnis), Strommix 2020 "
          "der REMIND-Region, Energie nach Klima (Vorfolie).",
    "v4": "Eigene Rechnung; Strommix je Jahr: Modellergebnis REMIND-EU, SSP2-NDC, über premise; Baum im jeweiligen "
          "Jahr gepflanzt.",
    "d4": "Eigene Rechnung, gleiches Modell wie die Vorfolie; rechts Anteil der bepflanzbaren Fläche je bester Option.",
}
QUELLE_POS = {  # where the default bottom-left spot collides with figure or equation
    2: dict(x=0.42, y=6.2, w=3.9, h=0.75),
    13: dict(x=8.6, y=6.95, w=4.3, h=0.35),
    14: dict(x=8.6, y=6.95, w=4.3, h=0.35),
    "kB": dict(x=2.3, y=6.75, w=4.3, h=0.45),
    "k13": dict(x=2.3, y=6.75, w=4.3, h=0.45),
}


def set_quelle(slide, text: str, pos: dict | None = None) -> None:
    """Replace the slide's source line, or add one bottom left (or at *pos*)."""
    boxes = [sh for sh in slide.shapes if sh.has_text_frame and sh.name.startswith("Quelle")]
    if boxes:
        set_runs(boxes[0].text_frame.paragraphs[0], text)
        if pos:
            boxes[0].left, boxes[0].top = Inches(pos["x"]), Inches(pos["y"])
            boxes[0].width, boxes[0].height = Inches(pos["w"]), Inches(pos["h"])
        for extra in boxes[0].text_frame.paragraphs[1:]:
            extra._p.getparent().remove(extra._p)
        for sh in boxes[1:]:
            remove_shape(slide, sh)
    else:
        quelle(slide, text, **(pos or dict(x=0.42, y=6.25, w=6.1, h=0.6)))


for _key, _text in QUELLEN.items():
    set_quelle(O(_key) if isinstance(_key, int) else NEW[_key], _text, QUELLE_POS.get(_key))

TO_BACKUP = [15, 16, 20, 21, 26, 27, 28, 30, 31, 32, 33, 36, 44, 35, 37, 40, 38, 42, 43, 41, 45, 46, 19, 18, 23, 29,
             22, 24, 25]
for n in TO_BACKUP:
    add_notes(O(n), "[v2] Aus dem Hauptteil genommen (Storyline v2), hierher verschoben, nicht gelöscht.")
for n in (30, 31, 32, 33, 36):  # spruce-era slides whose numbers the builder does not regenerate
    note_sticker(O(n), "Altes Modell (Fichte, vor 2026-10-05) — Zahlen überholt, aktuell: Hauptteil",
                 x=9.0, y=0.35, w=3.9, h=0.55)

used = {n for n in MAIN if isinstance(n, int)} | set(TO_BACKUP) | {49}
rest = [n for n in range(1, len(ORIG) + 1) if n not in used]
add_notes(k2, "[v2] Aus dem Hauptteil genommen: Die Systemgrenze wird im Vortrag erzählt, nicht als Schalenbild "
          "gezeigt.")
order = [O(n) if isinstance(n, int) else NEW[n] for n in MAIN] + [O(49)] + [d2, d3, dB2, dB3, k2, k7, k7s, k8, k10, k3p, k4, k11, k12] + \
        [O(n) for n in TO_BACKUP] + \
        [O(n) for n in rest]
assert len(order) == len(PRS.slides) and len({id(s) for s in order}) == len(order)

lst = PRS.slides._sldIdLst
by_slide = {s.slide_id: el for s, el in zip(PRS.slides, list(lst))}
wanted = [s.slide_id for s in order]
for el in list(lst):
    lst.remove(el)
for sid in wanted:
    lst.append(by_slide[sid])

T.save_deck(PRS, deck_path=OUT)
print(f"{OUT}: {T.verify_deck(OUT)} Folien, Hauptteil {len(MAIN)}")
