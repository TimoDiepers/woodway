"""Title and chapter slides of dissvortrag_v2.pptx in the style of the schematics.

The pictures are drawn in the HTML deck (title, chapter and closing slides, svg.deco)
and exported by scripts/export_deck_schematics.mjs (s_titel, s_kapitel_*). This script
hides the layout's old tree drawing on those slides ("Hintergrundgrafiken ausblenden"),
puts the exported picture over the whole slide behind the text, and gives the title
slide the author line of the HTML deck. Rerunnable; snapshot to docs/slides/workspace/.

    uv run python scripts/build_deco_slides.py
    uv run python scripts/build_deco_slides.py --deck /tmp/copy.pptx   # Probelauf
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_map_slides as B  # noqa: E402

FULL = (0.0, 0.0, 13.333, 7.5)
CHAPTERS = {"Bäume": "s_kapitel_baeume", "Klima": "s_kapitel_klima", "Vergleich": "s_kapitel_vergleich"}
AUTHOR = ("Timo Diepers", "Lehrstuhl für Technische Thermodynamik · RWTH Aachen")


def deco(slide, key: str) -> None:
    for sh in [s for s in slide.shapes if s.name.startswith(("Deko ", "Autor"))]:
        rids = [e.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                for e in sh._element.iter()]
        sh._element.getparent().remove(sh._element)
        for rid in filter(None, rids):
            if not slide._element.xpath(f'.//*[@r:embed="{rid}"]'):
                slide.part.drop_rel(rid)
    slide._element.set("showMasterSp", "0")
    B.svg_picture(slide, key, FULL, stem=key)
    pic = slide.shapes[-1]
    pic.name = f"Deko {key}"
    tree = slide.shapes._spTree
    tree.remove(pic._element)
    tree.insert(2, pic._element)  # right after nvGrpSpPr/grpSpPr: behind every text


def author(slide) -> None:
    box = slide.shapes.add_textbox(Inches(1.0), Inches(6.05), Inches(7.0), Inches(0.62))
    box.name = "Autor"
    tf = box.text_frame
    tf.word_wrap = True
    for i, (text, bold, size, col) in enumerate([(AUTHOR[0], True, 14, "1B2420"), (AUTHOR[1], False, 13, "3A4540")]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = text
        r.font.bold, r.font.size, r.font.name = bold, Pt(size), "Arial"
        r.font.color.rgb = RGBColor.from_string(col)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", type=Path, default=B.DECK)
    deck = ap.parse_args().deck
    if any(p.name.startswith("~$") for p in deck.parent.iterdir()):
        sys.exit("Deck ist in PowerPoint geöffnet (~$-Datei) — erst schließen.")
    prs = Presentation(str(deck))
    if deck == B.DECK:
        B.WORKSPACE.mkdir(exist_ok=True)
        snap = B.WORKSPACE / f"dissvortrag_v2_vor_deko_{datetime.now():%Y%m%d_%H%M%S}.pptx"
        shutil.copy2(deck, snap)
        print("Snapshot:", snap.name)
    first = prs.slides[0]
    deco(first, "s_titel")
    author(first)
    for slide in prs.slides:
        t = slide.shapes.title.text if slide.shapes.title is not None else None
        if t in CHAPTERS and slide.slide_layout.name.startswith("1_Titel"):
            deco(slide, CHAPTERS[t])
            print("Kapitel:", t)
    prs.save(str(deck))
    print("gespeichert:", deck)


if __name__ == "__main__":
    main()
