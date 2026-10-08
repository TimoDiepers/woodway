"""Put the HTML deck's schematic drawings into dissvortrag_v2.pptx, click by click.

The drawings live in the HTML deck (inline SVG, the style of the DAC slides);
scripts/export_deck_schematics.mjs writes them to docs/slides/figures/ as
<key>.svg/.png and one layer per build step, <key>@<n>.svg/.png. This script

* removes the old drawing from each slide (everything on the slide except the
  title, the Kurz-gesagt and Quelle boxes, off-slide parking and the equations,
  which python-pptx does not list and therefore never touches),
* stacks the layers as SVG pictures (PNG fallback) in the same frame,
* and replaces the slide's animation by one fade-in per click, in the order of
  the HTML build steps; a Kurz-gesagt box with its own step in the HTML comes in
  on the click after the drawing.

Rerunnable: it only ever replaces the drawing it put there itself. Snapshot to
docs/slides/workspace/ first.

    uv run python scripts/build_schema_slides.py
    uv run python scripts/build_schema_slides.py --deck /tmp/copy.pptx   # Probelauf
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_map_slides as B  # noqa: E402

KEEP = ("Kurz gesagt", "Quelle")
SLIDE_W, SLIDE_H = 13.333, 7.5

# (title, occurrence) -> (key, frame, takeaway on its own click)
SLIDES = {
    ("Die Natur kann das schon — wozu eine Maschine?", 0): ("s_zwei_wege", (0.42, 1.05, 12.5, 5.5), False),
    ("Was Bäume tun", 0): ("s_baeume_tun", (0.42, 1.2, 12.5, 5.3), False),
    ("Was Bäume tun", 1): ("s_baeume_tun_global", (0.42, 1.2, 12.5, 5.3), False),
    ("Kohlenstoff-Aufnahme", 0): ("s_kohlenstoff", (0.42, 1.15, 12.5, 4.9), False),
    ("Albedo-Änderung", 0): ("s_albedo", (0.42, 1.25, 12.5, 5.2), False),
    ("Albedo-Änderung", 1): ("s_albedo_faelle", (0.42, 1.2, 12.5, 5.5), False),
    ("Wie eine Maschine CO₂ aus der Luft holt", 0): ("s_dac_prozess", (0.42, 1.0, 12.5, 4.3), True),
    ("Wie wir DAC rechnen: je Ort und je Jahr", 0): ("s_dac_rechnung", (0.42, 1.0, 12.5, 4.3), True),
}


def on_slide(sh) -> bool:
    x, y = sh.left / 914400, sh.top / 914400
    return -0.5 < x < SLIDE_W and -0.5 < y < SLIDE_H


def clear_drawing(slide) -> None:
    """Remove every listed shape but the title, the boxes and off-slide parking; drop orphaned image rels."""
    gone = []
    for sh in list(slide.shapes):
        if slide.shapes.title is not None and sh.shape_id == slide.shapes.title.shape_id:
            continue
        if sh.name in KEEP or not on_slide(sh):
            continue
        gone += [e.get(qn("r:embed")) for e in sh._element.iter() if e.get(qn("r:embed"))]
        sh._element.getparent().remove(sh._element)
    for rid in set(gone):
        if not slide._element.xpath(f'.//*[@r:embed="{rid}"]'):
            slide.part.drop_rel(rid)


def layers(key: str) -> list[int]:
    return sorted(int(p.stem.split("@")[1]) for p in B.FIG.glob(f"{key}@*.svg"))


# --------------------------------------------------------------------------
# click animations
# --------------------------------------------------------------------------

P = "http://schemas.openxmlformats.org/presentationml/2006/main"


def _fade(ids, spid: int, first: bool) -> str:
    return (f'<p:par><p:cTn id="{next(ids)}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" '
            f'nodeType="{"clickEffect" if first else "withEffect"}"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f'<p:childTnLst><p:set><p:cBhvr><p:cTn id="{next(ids)}" dur="1" fill="hold"><p:stCondLst>'
            f'<p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst>'
            f'<p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/>'
            f'</p:to></p:set><p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{next(ids)}" dur="500"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>')


def set_clicks(slide, clicks: list[list[int]]) -> None:
    """Replace the slide's animation: one fade-in per click for the given shape ids."""
    old = slide._element.find(qn("p:timing"))
    if old is not None:
        slide._element.remove(old)
    if not clicks:
        return
    ids = iter(range(3, 10_000))
    pars = ''.join(
        f'<p:par><p:cTn id="{next(ids)}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
        f'<p:childTnLst><p:par><p:cTn id="{next(ids)}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
        f'<p:childTnLst>{"".join(_fade(ids, s, i == 0) for i, s in enumerate(c))}</p:childTnLst></p:cTn></p:par>'
        f'</p:childTnLst></p:cTn></p:par>' for c in clicks)
    xml = (f'<p:timing xmlns:p="{P}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
           f'<p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq">'
           f'<p:childTnLst>{pars}</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl>'
           f'<p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl>'
           f'<p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')
    timing = etree.fromstring(xml)
    ext = slide._element.find(qn("p:extLst"))
    if ext is not None:
        ext.addprevious(timing)
    else:
        slide._element.append(timing)


def build(slide, key: str, frame, takeaway_click: bool) -> int:
    clear_drawing(slide)
    steps = layers(key)
    clicks = []
    if not steps:
        B.svg_picture(slide, key, frame, stem=key)
        slide.shapes[-1].name = f"Schema {key}"
    for n in steps:
        B.svg_picture(slide, key, frame, stem=f"{key}@{n}")
        pic = slide.shapes[-1]
        pic.name = f"Schema {key}@{n}"
        if n:
            clicks.append([pic.shape_id])
    # the pictures belong under the boxes
    tree = slide.shapes._spTree
    for sh in [s for s in slide.shapes if s.name in KEEP]:
        tree.append(sh._element)
    if takeaway_click:
        box = next((s for s in slide.shapes if s.name == "Kurz gesagt" and on_slide(s)), None)
        if box is not None:
            clicks.append([box.shape_id])
    set_clicks(slide, clicks)
    return len(clicks)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", type=Path, default=B.DECK)
    deck = ap.parse_args().deck
    if any(p.name.startswith("~$") for p in deck.parent.iterdir()):
        sys.exit("Deck ist in PowerPoint geöffnet (~$-Datei) — erst schließen.")
    prs = Presentation(str(deck))
    if deck == B.DECK:
        B.WORKSPACE.mkdir(exist_ok=True)
        snap = B.WORKSPACE / f"dissvortrag_v2_vor_schemata_{datetime.now():%Y%m%d_%H%M%S}.pptx"
        shutil.copy2(deck, snap)
        print("Snapshot:", snap.name)
    seen: dict[str, int] = {}
    for no, slide in enumerate(prs.slides, 1):
        title = slide.shapes.title.text if slide.shapes.title is not None else None
        if title is None:
            continue
        k = seen.get(title, 0)
        seen[title] = k + 1
        spec = SLIDES.get((title, k))
        if spec:
            print(f"Folie {no}: {spec[0]}, {build(slide, *spec)} Klicks")
    prs.save(str(deck))
    print("gespeichert:", deck)


if __name__ == "__main__":
    main()
