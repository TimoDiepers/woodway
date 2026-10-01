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
import shutil
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.util import Emu, Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pptx_tools as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "slides" / "dissvortrag.pptx"
OUT = ROOT / "docs" / "slides" / "dissvortrag_v2.pptx"
FIG = ROOT / "docs" / "slides" / "figures"

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


def _rpr(size: int, color: str):
    rpr = etree.Element(f"{{{NS['a']}}}rPr", lang="de-DE", sz=str(size * 100), dirty="0")
    fill = etree.SubElement(rpr, f"{{{NS['a']}}}solidFill")
    etree.SubElement(fill, f"{{{NS['a']}}}srgbClr", val=color)
    etree.SubElement(rpr, f"{{{NS['a']}}}latin", typeface="Cambria Math", panose="02040503050406030204",
                     pitchFamily="18", charset="0")
    return rpr


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


def equation(slide, lines, *, x, y, w, h, size=20, align="left", color="1A2320", mathtext=None):
    """Native PowerPoint equation(s), one paragraph per LaTeX line."""
    lines = [lines] if isinstance(lines, str) else list(lines)
    sid = _next_id(slide)
    paras = []
    for latex in lines:
        para = _omml(latex)
        para.find("m:oMathParaPr/m:jc", NS).set(f"{{{NS['m']}}}val", "left" if align == "left" else "centerGroup")
        for run in para.iter(f"{{{NS['m']}}}r"):
            t = run.find("m:t", NS)
            t.addprevious(_rpr(size, color))
        paras.append(para)

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
        end = _rpr(size, color)
        end.tag = f"{{{NS['a']}}}endParaRPr"
        ap.append(end)
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
set_runs(paras[0], "Eine Fichte bindet bis zur Sättigung rund 180 kg CO₂ (50 kg Kohlenstoff).")
set_runs(paras[2], "300 Gt ÷ 0,18 t  ≈  1,6 Billionen Bäume.")
set_runs(paras[4], "Diese Rechnung zieht die Grenze um den Baum. Wir ziehen sie Schritt für Schritt weiter, "
         "bis das Klima drin ist — und schauen, was dann von ihr übrig bleibt.")
add_notes(s4, "[v2] Zahl an den Modellbaum angeglichen (m_max = 50 kgC ≈ 183 kg CO₂). 1,6 Billionen landet bei "
          "der Billion-Bäume-Kampagne der nächsten Folie.")
add_notes(O(6), "[v2] Überblick: drei Kapitel = wachsende Systemgrenze. Bäume = Schale 1 (ein Baum), Klima = "
          "Schalen 2–3 (Kohlenstoffkreislauf, Erde am Oberrand), Vergleich = Schalen 4–5 (alle Flächen, alle "
          "Wege). Das Schalenbild kommt ausführlich auf der ersten Klima-Folie.")

# ---- Bäume (Schale 1) ----------------------------------------------------
s12 = O(12)
sticker = shape(s12, "Rectangle 9533")
remove_shape(s12, sticker)
add_notes(s12, "[v2] Störung in Schale 1 mit fester Rate p₀: der Faktor e^{γ·ΔT} in der Gleichung setzt eine "
          "Erwärmung voraus, die es hier noch nicht gibt — in PowerPoint ausgrauen, eingelöst auf „Die Erwärmung "
          "wirkt auf den Baum zurück“. Danach folgt die Folie mit allen fünf Arten (gleiche Form, andere Zahlen).")

s34 = O(34)  # five species -> into Bäume, right after the model slide
rehang(s34, BAEUME)
set_title(s34, "Gleiche Form, andere Zahlen: was wo wächst")
replace_kurz(s34, "Wie schnell und wie viel ein Baum bindet, hängt davon ab, was wo wächst — m_max und k sind je "
             "Art verschieden. Weiter geht es mit einem Beispiel: der Fichte.", name="TextBox 5")
add_notes(s34, "[v2] Nur die Botschaft „gleiche Form, andere Zahlen“. Ergebnisse je Art erst in Schale 4.")

b6 = new_slide(BAEUME, "Was der Baum der Luft entnimmt")
picture(b6, FIG / "b6_kohlenstoff_kurve.png", height=4.45)
equation(b6, r"\dot m_{\mathrm{CO_2}}(t) = -\frac{44}{12}\,\dot m(t)", x=0.42, y=5.8, w=6.2, h=0.8)
kurz(b6, "Mit der Grenze um den Baum ist die naive Rechnung exakt: Was der Baum hat, fehlt der Luft — und zwar "
     "überall gleich. Beide Halbsätze halten nicht lange.")
quelle(b6, "Gemeine Fichte, Störung mit heutiger Rate; im Modell wächst eine Art überall gleich schnell")
add_notes(b6, "Sprechertext: Jeder Jahreszuwachs ist eine kleine negative Emission — Kohlenstoff mal 44/12, "
          "Vorzeichen gedreht. Aufsummiert holt eine Fichte bis 2150 rund 160 kg CO₂ aus der Luft. Unsere "
          "beiden Beispielorte, Aachen und Archangelsk, liegen exakt auf derselben Kurve. Keine Karte: sie wäre "
          "überall gleich gefärbt.")

s13 = O(13)
note13 = shape(s13, "Rectangle 9533") if any(sh.name == "Rectangle 9533" for sh in s13.shapes) else None
for sh in list(s13.shapes):
    if sh.has_text_frame and sh.text_frame.text.startswith("Wir haben wachstum"):
        remove_shape(s13, sh)
add_notes(s13, "Sprechertext: Der Baum wächst — und je größer er wird, desto mehr Boden verdeckt er. Das ändert, "
          "wie viel Sonnenlicht reflektiert wird. Hellerer Boden (Schnee) und mehr Sonne sind genau die zwei "
          "Ortsgrößen, die gleich die Karte färben.")

b8 = new_slide(BAEUME, "Zusätzlich absorbiertes Licht: je nach Ort")
picture(b8, FIG / "b8_albedo_jahreskarte.png", height=4.45)
equation(b8, r"\Delta\dot Q_{\mathrm{Baum}} = A_{\mathrm{Baum}}\,\langle \dot q_{\mathrm{kurz}}\,(-\Delta\alpha) \rangle\, f(t)", x=0.42, y=5.8, w=6.2, h=0.8)
kurz(b8, "Kohlenstoff ist überall gleich, Licht nicht: Wo Schnee liegt und die Sonne kräftig ist, schluckt der "
     "Baum am meisten — Aachen 44 W, Archangelsk 65 W im Jahresmittel.")
quelle(b8, "Δα und Einstrahlung: Duveiller et al. (2018), nur lokal gemessene Zellen; ausgewachsene Fichte statt Wiese")
add_notes(b8, "Sprechertext: Aachen hat kaum Schnee — dort folgt der Effekt der Sonne, breites Maximum im "
          "Sommer. Archangelsk hat im April eine scharfe Spitze: noch Schnee, Sonne schon hoch. Im Jahresmittel "
          "unterscheiden sich die Orte weniger als im Jahresgang, aber 44 gegen 65 W verschieben später den "
          "Zeitpunkt, ab dem der Baum kühlt, um 20 Jahre. Grau: Fichtengebiet ohne lokale Messung.")

b9 = new_slide(BAEUME, "Was der Baum mit seiner Umgebung tauscht")
picture(b9, FIG / "b9_kg_gegen_watt.png", height=4.55)
kurz(b9, "Kilogramm gegen Watt — an der Grenze des Baums nicht entscheidbar. Was das CO₂ in der Luft bewirkt, "
     "liegt außerhalb dieser Grenze. Der Baum ist nicht allein: Grenze erweitern.")
quelle(b9, "Gemeine Fichte; rechts: Jahresmittel aus der Karte × Kronenschluss f(t)", x=0.42, y=6.2, w=6.1)
add_notes(b9, "Kapitelabschluss Schale 1. Links eine Linie für beide Orte, rechts zwei. Die Farben grün/orange "
          "sind ab jetzt CO₂ und Albedo — sie kommen im Antrieb wieder.")

# ---- Klima (Schalen 2 und 3) ---------------------------------------------
set_runs(O(17).placeholders[1].text_frame.paragraphs[0], "Der Baum ist nicht allein")

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
set_title(s18, "Eine Tonne raus ist nicht eine Tonne weg")
remove_shape(s18, shape(s18, "Rectangle 3"))
eq = s18.placeholders[12]
eq.left = Inches(13.8)  # parked off-canvas like other boxes in this deck: ṁ_CO₂ and the convolution live on B6/K4 now
pic = shape(s18, "Picture 9010")
pic.height = int(pic.height * Inches(7.4) / pic.width)
pic.width = Inches(7.4)
pic.left, pic.top = int((PRS.slide_width - pic.width) / 2), Inches(1.15)
replace_kurz(s18, "Fehlt der Luft CO₂, schlucken Ozean und Landbiosphäre weniger und geben teilweise zurück. "
             "Von einem entnommenen Kilogramm fehlt nach der Zeit t nur noch der Anteil g_C(t) — der erste Rebound.")
add_notes(s18, "[v2] Die beiden Gleichungen (ṁ_CO₂ = −44/12·ṁ und die Faltung) liegen jetzt rechts neben der Folie geparkt — sie gehören auf „Was der Baum der Luft entnimmt“ und „Das CO₂-Profil in der Luft“. Laut Storyline hier nur die vorindustrielle Joos-Kurve zeigen (Schale 2 kennt noch keinen "
          "steigenden Hintergrund); die SSP-Kurve und warum sie höher liegt, kommt mit der übrigen Menschheit in "
          "Schale 3. Prüfen, ob das Bild beide Kurven zeigt — ggf. in der Abbildung die SSP-Kurve ausblenden.")

k4 = new_slide(KLIMA, "Schale 2: Das CO₂-Profil in der Luft")
picture(k4, FIG / "k4_co2_profil.png", height=4.55)
equation(k4, r"\Delta m_{\mathrm{CO_2}}(t) = \int_0^t g_{\mathrm{C}}(t-t')\,\dot m_{\mathrm{CO_2}}(t')\,dt'", x=0.42, y=5.7, w=6.2, h=0.95)
kurz(k4, "Schale 1 sagt: Was im Baum ist, fehlt der Luft. Schale 2 sagt: Es fehlt deutlich weniger — und die "
     "Lücke schließt sich wieder, sobald der Baum kaum noch zuwächst.")
quelle(k4, "Impulsantwort g_C: Joos et al. (2013), vorindustriell; Gemeine Fichte, Störung mit heutiger Rate")
add_notes(k4, "Sprechertext: Jede Jahresentnahme klingt mit g_C ab, die Summe ist das CO₂, das der Luft "
          "wirklich fehlt. Bis 2150 hat die Fichte 163 kg geholt, der Luft fehlen davon noch rund 73 kg.")

s19 = O(19)
set_title(s19, "Schale 3: Grenze um die ganze Erde")
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
set_title(s22, "Schale 3: Energiebilanz und Antrieb")
replace_kurz(s22, "Antrieb φ: wie stark ein Eingriff „rein − raus“ verschiebt, bevor sich die Erde erwärmt "
             "[W/m²]. Zwei Hebel: Die Albedo dreht am reflektierten Teil, CO₂ an Q̇_lang.")

s25 = O(25)
set_title(s25, "Albedo: aus Watt am Baum werden Watt pro m² Erde")
replace_kurz(s25, "Die Watt aus dem Bäume-Kapitel sind schon Energie: × τ_atm für den Weg nach oben, ÷ A_Erde. "
             "Die Albedo wirkt sofort und nur so lange, wie der Baum steht — einen Rebound gibt es hier nicht.")
add_notes(s25, "[v2] In PowerPoint die Zeile φ = φ_CO₂ + φ_α entfernen — die Summe kommt erst, wenn CO₂ "
          "hergeleitet ist. Gleichung als φ_α(t) = τ_atm · ΔQ̇_Baum(t) / A_Erde lesen (ΔQ̇_Baum aus B8).")

k7 = new_slide(KLIMA, "Was CO₂ mit der Abstrahlung macht")
placeholder(k7, "Platzhalter — Abbildung: Abstrahlspektrum der Erde mit CO₂-Kerbe\n"
            "x: Wellenlänge (5–30 µm) · y: abgestrahlte Leistung. Zwei Planck-Referenzen (Boden ≈ 288 K, "
            "Höhe ≈ 220 K), dazwischen das Spektrum mit der Kerbe um 15 µm; zweite Kontur: Kerbe bei mehr CO₂ "
            "breiter, Fläche dazwischen „weniger raus“.\n"
            "Schematisch rechnen (Planck + einfaches Bandmodell) oder gemessenes Spektrum (Nimbus-4 IRIS, "
            "Hanel et al. 1972).", h=4.4)
kurz(k7, "Im CO₂-Band strahlt nicht der warme Boden ins All, sondern kalte Luft in großer Höhe — und Kaltes "
     "strahlt weniger. Ein Baum, der CO₂ entnimmt, macht die Kerbe ein winziges Stück schmaler.")
add_notes(k7, "Alternative ohne Spektroskopie: CO₂ hebt die Höhe, aus der die Erde in diesem Band abstrahlt. "
          "Höher heißt kälter, kälter heißt weniger.")

k8 = new_slide(KLIMA, "Der Baum ist nicht allein in der Atmosphäre")
placeholder(k8, "Platzhalter — Abbildung, zweigeteilt\n"
            "links: φ über C (280–700 ppm), Logarithmus, Tangenten bei 424 ppm (2025) und 624 ppm (≈ 2150).\n"
            "rechts: A_CO₂(t) unter SSP2-4,5, fällt von 1,61·10⁻¹⁵ auf 1,10·10⁻¹⁵ W m⁻² kg⁻¹; gestrichelt die "
            "Lehrbuchkonstante 1,76·10⁻¹⁵.\n"
            "Daten: nbs.forcing.phi_co2_background, nbs.response.background_co2_ppm.", h=4.1)
equation(k8, r"\varphi = 5{,}35\,\ln\left(C/C_0\right)", x=0.42, y=5.55, w=6.2, h=0.7)
kurz(k8, "Zweiter Rebound, diesmal von der übrigen Menschheit: Je voller die Atmosphäre, desto weniger bewirkt "
     "jedes weitere Kilogramm. Wer heute pflanzt, pflanzt in eine Atmosphäre, in der jedes Kilogramm später "
     "weniger zählt.")
add_notes(k8, "Sprechertext dazu: In derselben volleren Welt nehmen Ozean und Land schlechter auf, deshalb bleibt "
          "die Lücke aus Schale 2 sogar länger offen — das wirkt zugunsten des Baums (SSP- statt Joos-Kurve).")

s24 = O(24)
set_title(s24, "Vom CO₂-Profil zum Antrieb")
replace_kurz(s24, "φ_CO₂ ist das CO₂-Profil aus Schale 2 mal die Wirkung je Kilogramm. Keine Fläche in der Formel: "
             "CO₂ mischt sich global — anders als die Albedo, die am Standort hängt.")
set_runs(shape(s24, "Formelzeichen").text_frame.paragraphs[0],
         "A_CO₂(t) Strahlungswirkung je kg zusätzliches CO₂ — sinkt unter SSP2-4,5 von 1,61 auf 1,10·10⁻¹⁵ "
         "W m⁻² kg⁻¹  ·  Δm_CO₂(t) CO₂-Profil aus Schale 2")
add_notes(s24, "[v2] In PowerPoint die Gleichung zeitabhängig lesen: φ_CO₂(t) = A_CO₂(t) · Δm_CO₂(t). Die alte "
          "Konstante 1,76·10⁻¹⁵ ist durch die abnehmende Wirkung der vorigen Folie ersetzt.")

k10 = new_slide(KLIMA, "Antrieb: Kilogramm gegen Watt")
picture(k10, FIG / "k10_antrieb_zwei_orte.png", height=4.55)
kurz(k10, "Kilogramm gegen Watt ist entschieden: Erst wärmt das Licht, dann kühlt der Kohlenstoff — in Aachen "
     "ab 2036, in Archangelsk erst ab 2053. Die grüne Kurve ist an beiden Orten dieselbe, die orange nicht.")
quelle(k10, "Gemeine Fichte, SSP2-4,5, volles Modell; Albedo je Ort aus der lokal gemessenen Zelle",
       x=0.42, y=6.2, w=6.1)

s29 = O(29)
set_title(s29, "Die Erde antwortet")
add_notes(s29, "[v2] Zusammen mit „Von Energie zu Temperatur“ lesen: C·dT/dt = φ − Λ·T, Antwort g_T. Rückverweis "
          "auf g_C aus Schale 2 — Impuls, Antwort, Summe.")

k12 = new_slide(KLIMA, "Ergebnis: ein Baum, voll bilanziert")
picture(k12, FIG / "k12_temperatur_zwei_orte.png", height=4.55)
kurz(k12, "Die Fichte wärmt zuerst: in Aachen 14 Jahre, in Archangelsk 34. Ab 2039 bzw. 2059 kühlt sie "
     "dauerhaft. Der Versatz zum Antrieb (3 bzw. 6 Jahre) ist die Trägheit der Erde.")
quelle(k12, "Gemeine Fichte, gepflanzt 2025, SSP2-4,5, volles Modell", x=0.42, y=6.2, w=6.1)
add_notes(k12, "Größenordnung einmal laut sagen: einige 10⁻¹⁵ K Erwärmung je Baum, bis 2150 etwa −5·10⁻¹⁴ K. "
          "Bis Schale 4 bleiben wir bei „je Baum“.")

k13 = new_slide(KLIMA, "Die Erwärmung wirkt auf den Baum zurück")
picture(k13, FIG / "k13_pflanzjahr_zwei_orte.png", height=4.55)
equation(k13, r"p(t) = p_0\,e^{\gamma\,T(t)}", x=0.42, y=5.8, w=6.2, h=0.8)
kurz(k13, "Dritter Rebound: Je wärmer es wird, desto häufiger Feuer, Sturm und Käfer. Wer 60 Jahre später "
     "pflanzt, wartet länger auf die Kühlung, als er gewartet hat — Aachen +68, Archangelsk +75 Jahre.")
add_notes(k13, "Die Balken enthalten beide späten Effekte (höhere Störungsrate und vollere Atmosphäre); getrennt "
          "zeigt sie die Leiter auf der nächsten Folie.")

k14 = new_slide(KLIMA, "Was jede Schale gekostet hat")
placeholder(k14, "Platzhalter — Abbildung: Leiter auf t*, kumulativ, in Schalen-Reihenfolge, Aachen und "
            "Archangelsk\n"
            "1 Schale 1: Kohlenstoff im Baum, feste Störung, konstante Wirkung je kg (= naive Rechnung)\n"
            "2 Schale 1: + Albedo\n"
            "3 Schale 2: + Rebound Ozean/Land (g_C)\n"
            "4 Schale 3: + volle Atmosphäre (log, Hintergrund)\n"
            "5 Schale 3: + Erwärmung erhöht die Störung (γ)\n"
            "Neu rechnen mit nbs.config / nbs.variants; Endpunkte 2039 (Aachen) und 2059 (Archangelsk).", h=4.4)
kurz(k14, "Mit der Grenze um den Baum kühlt die Fichte ab dem ersten Jahr. Mit allen Schalen erst ab 2039 in "
     "Aachen und ab 2059 in Archangelsk.")

# ---- Vergleich (Schalen 4 und 5) -----------------------------------------
set_runs(O(39).placeholders[1].text_frame.paragraphs[0], "Alle Bäume, alle Wege") if O(39).placeholders[1].text_frame.paragraphs[0].runs else O(39).placeholders[1].text_frame.paragraphs[0].add_run().__setattr__("text", "Alle Bäume, alle Wege")

for n in (35, 37, 38):
    rehang(O(n), VERGLEICH)
set_title(O(35), "Schale 4: dieselbe Kette, andere Orte")
note_sticker(O(35), "Platzhalter: Bild ersetzen durch Balken „Jahre bis zur Kühlung“ je Art (mit Zellwerten "
             "neu rechnen)", x=9.9, y=1.2, w=3.1, h=1.2)
add_notes(O(35), "[v2] Kein neues Konzept — Wachstum (Bäume-Kapitel) und Albedo-Karte sind bekannt, jetzt die volle "
          "Kette je Ort. Zahlen auf dieser Folie stammen noch aus der Breitentabelle.")
add_notes(O(37), "[v2] Laut Storyline: erstes Bild im selben Kartenausschnitt wie die Albedokarte (Europa + "
          "westliches Russland, Marker Aachen/Archangelsk), dann global; Farbskala auf 4 Klassen.")
note_sticker(O(42), "Platzhalter: Bild ersetzen durch Temperaturpfad SSP2-4,5 mit/ohne Aufforstung gegen 1,5 °C",
             x=9.9, y=1.2, w=3.1, h=1.2)
set_title(O(42), "Reicht das? Die Umkehrrechnung")

s46 = O(46)
naiv = shape(s46, "Naiv").text_frame.paragraphs
set_runs(naiv[1], "•  Eine Fichte bindet bis zur Sättigung rund 180 kg CO₂.")
set_runs(naiv[2], "•  300 Gt ÷ 0,18 t ≈ 1,6 Billionen Bäume — gültig, solange die Grenze um den Baum liegt.")
set_runs(naiv[3], "•  Kein Rebound, keine Albedo, kein Ort, keine Zeit.")
modell = shape(s46, "Modell").text_frame.paragraphs
set_runs(modell[0], "Dieselbe Frage, Schale für Schale")
set_runs(modell[1], "+ Kohlenstoffkreislauf: Ozean und Land geben zurück — der Luft fehlt weniger.")
set_runs(modell[2], "+ Erde am Oberrand: Albedo wirkt dagegen, jedes kg wirkt später weniger, Erwärmung erhöht "
         "die Störung. Fichte: Kühlung ab 2039 (Aachen) bzw. 2059 (Archangelsk).")
set_runs(modell[3], "+ ganze Landfläche: 78,2 GtC, 0,239 K bis 2150.")
set_runs(modell[4], "→ Für 1,5 °C ab 2050: das 10,3-Fache dieser Fläche, rund 75 % des eisfreien Landes.")
replace_kurz(s46, "Die naive Rechnung ist nicht falsch gerechnet — sie zieht die Grenze um den Baum. Jede Schale, "
             "die man dazunimmt, verändert die Antwort.")

s47 = O(47)
set_title(s47, "Die Antwort hängt an der Grenze")
for name, head, body in [
    ("These 1", "1 — Der Baum ist Teil eines Systems",
     "Was er bindet, bewirkt erst im Kohlenstoffkreislauf und in der Energiebilanz etwas."),
    ("These 2", "2 — Jede Schale nimmt etwas weg",
     "Rebound von Ozean und Land, Albedo, volle Atmosphäre, Störung durch Erwärmung."),
    ("These 3", "3 — Was bleibt, ist real, aber begrenzt",
     "Ortsabhängig, spät und nie in der Menge, die wir brauchen — ein Beitrag, kein Ersatz."),
]:
    ps = shape(s47, name).text_frame.paragraphs
    set_runs(ps[0], head)
    set_runs(ps[1], body)
    for extra in ps[2:]:
        extra._p.getparent().remove(extra._p)
replace_kurz(s47, "Warum Maschinen, wenn die Natur das kann? Weil die Natur es nur dort gut kann, wo kein Schnee "
             "liegt, nur langsam und nie in der Menge, die wir brauchen. Emissionsminderung ersetzt sie in keinem "
             "Fall.")


# ---- existing LaTeX-text formulas -> native equations ----------------------
for n, sid in ((29, 4014), (58, 3002)):
    sl = O(n)
    box = next(sh for sh in sl.shapes if sh.shape_id == sid)
    src = box.text_frame.text
    lines = [ln.strip() for ln in src.split("\n") if ln.strip()]
    x, y, w, h = (v / 914400 for v in (box.left, box.top, box.width, box.height))
    remove_shape(sl, box)
    equation(sl, lines, x=x, y=y, w=w, h=max(h, 0.75 * len(lines)), align="center")

# ---- order ---------------------------------------------------------------
NEW = {"b6": b6, "b8": b8, "b9": b9, "k2": k2, "k4": k4, "k7": k7, "k8": k8, "k10": k10, "k12": k12,
       "k13": k13, "k14": k14}
MAIN = [1, 2, 3, 4, 5, 6,
        7, 8, 9, 10, 11, 12, 34, "b6", 13, 14, "b8", "b9",
        17, "k2", 18, "k4", 19, 22, 25, "k7", "k8", 24, "k10", 23, 29, "k12", "k13", "k14",
        39, 35, 37, 40, 38, 42, 43, 44, 41, 45, 46, 47, 48]
TO_BACKUP = [15, 16, 20, 21, 26, 27, 28, 30, 31, 32, 33, 36]
for n in TO_BACKUP:
    add_notes(O(n), "[v2] Aus dem Hauptteil genommen (Storyline v2), hierher verschoben, nicht gelöscht.")

used = {n for n in MAIN if isinstance(n, int)} | set(TO_BACKUP) | {49}
rest = [n for n in range(1, len(ORIG) + 1) if n not in used]
order = [O(n) if isinstance(n, int) else NEW[n] for n in MAIN] + [O(49)] + [O(n) for n in TO_BACKUP] + \
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
