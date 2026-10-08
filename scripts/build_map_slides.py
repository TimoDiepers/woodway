"""Put the HTML deck's maps into dissvortrag_v2.pptx, as SVG with a PNG fallback.

The maps are drawn once, by the HTML deck (ECharts, hexagon tiles, palettes of
nbs.map_fields); scripts/export_deck_svgs.mjs writes them to
docs/slides/figures/hex_<key>.svg/.png. This script

* replaces the map picture on the map slides by that SVG (PowerPoint shows the
  SVG, older viewers the PNG),
* inserts "Was ein Baum wo bewirkt" (k15) at the end of the Klima chapter,
* inserts "Wo Bäume hinkönnen" (v0, reforestable share) in front of the
  cooling map, which becomes "Wo Bäume kühlen — und wo nicht" (v1, without the
  DAC hatching: DAC comes later).

It writes a snapshot to docs/slides/workspace/ first and refuses to run twice.

    uv run python scripts/build_map_slides.py
    uv run python scripts/build_map_slides.py --deck /tmp/copy.pptx   # Probelauf
"""

from __future__ import annotations

import argparse
import copy
import shutil
import sys
from datetime import datetime
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import Part
from pptx.oxml.ns import qn
from pptx.util import Inches

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
DECK = REPO / "docs" / "slides" / "dissvortrag_v2.pptx"
FIG = REPO / "docs" / "slides" / "figures"
WORKSPACE = REPO / "docs" / "slides" / "workspace"
SVG_EXT = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
ASVG = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"

MAP_SLIDES = {  # title -> map key
    "Welcher Wald wo wächst": "b5",
    "Zwei Zutaten: Sonne und Schnee": "b8a",
    "Zusätzlich absorbiertes Licht: je nach Ort": "b8",
    "Wo Bäume hinkönnen": "v1",
    "Was eine Maschine braucht": "d1",
    "Die Maschine wird zur Messlatte": "d4",
}
FRAME = (0.42, 1.05, 12.5, 4.45)  # x, y, max w, max h [in]: under the title, above the Kurz-gesagt box


def de(x: float, nd: int = 0) -> str:
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def svg_picture(slide, key: str, frame=FRAME, stem: str | None = None):
    """PNG picture with the SVG as the preferred image (a:blip/a:extLst/asvg:svgBlip);
    the files are FIG/<stem>.svg/.png, by default hex_<key>."""
    from PIL import Image

    stem = stem or f"hex_{key}"
    png, svg = FIG / f"{stem}.png", FIG / f"{stem}.svg"
    w_px, h_px = Image.open(png).size
    x, y, mw, mh = frame
    w = min(mw, mh * w_px / h_px)
    h = w * h_px / w_px
    pic = slide.shapes.add_picture(str(png), Inches(x + (mw - w) / 2), Inches(y), Inches(w), Inches(h))
    pic.name = f"Karte {key}"
    package = slide.part.package
    part = Part(package.next_image_partname("svg"), "image/svg+xml", package, svg.read_bytes())
    rid = slide.part.relate_to(part, RT.IMAGE)
    blip = pic._element.find(".//" + qn("a:blip"))
    ext_lst = blip.find(qn("a:extLst"))
    if ext_lst is None:
        ext_lst = etree.SubElement(blip, qn("a:extLst"))
    ext = etree.SubElement(ext_lst, qn("a:ext"))
    ext.set("uri", SVG_EXT)
    sb = etree.SubElement(ext, f"{{{ASVG}}}svgBlip", nsmap={"asvg": ASVG})
    sb.set(qn("r:embed"), rid)
    return pic


def remove_pictures(slide):
    for sh in [s for s in slide.shapes if s.shape_type == 13]:
        rids = [b.get(qn("r:embed")) for b in sh._element.iter(qn("a:blip"))]
        sh._element.getparent().remove(sh._element)
        for rid in rids:
            if rid and not slide._element.xpath(f'.//*[@r:embed="{rid}"]'):
                slide.part.drop_rel(rid)


def set_box(shape, heading: str | None, body: str) -> None:
    """Replace the text of a Kurz-gesagt/Quelle box, keeping its run formatting."""
    paras = shape.text_frame.paragraphs
    if heading is not None:
        paras[0].runs[0].text = heading
        for r in paras[0].runs[1:]:
            r.text = ""
        target, rest = paras[1], paras[2:]
    else:
        target, rest = paras[0], paras[1:]
    target.runs[0].text = body
    for r in target.runs[1:]:
        r.text = ""
    for p in rest:
        p._p.getparent().remove(p._p)


def new_slide_after(prs, ref, title: str):
    """A slide in ref's layout (= its chapter master), placed right after ref, with ref's text boxes."""
    s = prs.slides.add_slide(ref.slide_layout)
    lst = prs.slides._sldIdLst
    el = lst[-1]
    lst.remove(el)
    lst.insert(list(prs.slides).index(ref) + 1, el)
    s.shapes.title.text = title
    for name in ("Kurz gesagt", "Quelle"):
        src = next(sh for sh in ref.shapes if sh.name == name)
        s.shapes._spTree.append(copy.deepcopy(src._element))
    return s


def by_title(prs, title):
    hits = [s for s in prs.slides if s.shapes.title is not None and s.shapes.title.text == title]
    if len(hits) != 1:
        sys.exit(f"{len(hits)} Folien mit Titel {title!r}")
    return hits[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", type=Path, default=DECK)
    deck = ap.parse_args().deck
    if any(p.name.startswith("~$") for p in deck.parent.iterdir()):
        sys.exit("PowerPoint hat das Deck offen (~$-Datei) — erst schließen.")
    prs = Presentation(str(deck))
    if any(s.shapes.title is not None and s.shapes.title.text == "Was ein Baum wo bewirkt" for s in prs.slides):
        sys.exit("Schon umgebaut — Snapshot aus docs/slides/workspace/ wiederherstellen.")
    if deck == DECK:
        WORKSPACE.mkdir(parents=True, exist_ok=True)
        snap = WORKSPACE / f"{deck.stem}_vor_karten_{datetime.now():%Y%m%d_%H%M%S}.pptx"
        shutil.copy2(deck, snap)
        print("Snapshot:", snap)

    from nbs import map_fields

    f = map_fields.facts()

    # 1  maps from the HTML deck
    for title, key in MAP_SLIDES.items():
        s = by_title(prs, title)
        remove_pictures(s)
        svg_picture(s, key)

    # 2  cooling map: own title, no DAC sentence
    cool = by_title(prs, "Wo Bäume hinkönnen")
    cool.shapes.title.text = "Wo Bäume kühlen — und wo nicht"
    shapes = {sh.name: sh for sh in cool.shapes}
    set_box(shapes["Kurz gesagt"], "Kurz gesagt",
            f"Von den {de(f['flaeche_gha'], 2)} Gha wiederbewaldbarer Fläche kühlen bis 2150 0,39 Gha; auf 0,44 Gha — "
            "im Norden und in trockenen Gebieten — frisst die Albedo mehr, als der Baum an CO₂ bindet.")
    set_box(shapes["Quelle"], None,
            "Eigene Rechnung, Baum gepflanzt 2025, bewertet 2150, je Zelle der Waldtyp mit der stärksten Kühlung. "
            "Fläche: Walker et al. 2022 (Modellergebnis: aus Inventur- und Satellitendaten hochgerechnet); "
            "Waldtyp: Hasler et al. 2024.")

    # 3  area map in front of it (same chapter layout and boxes as the cooling slide)
    area = new_slide_after(prs, cool, "Wo Bäume hinkönnen")
    lst = prs.slides._sldIdLst
    el = lst[list(prs.slides).index(area)]
    lst.remove(el)
    lst.insert(list(prs.slides).index(cool), el)
    remove_pictures(area)
    svg_picture(area, "v0")
    shapes = {sh.name: sh for sh in area.shapes}
    set_box(shapes["Kurz gesagt"], "Kurz gesagt",
            f"Wiederbewaldbar sind {de(f['flaeche_gha'], 2)} Gha, rund {de(100 * f['anteil_eisfrei'])} % der eisfreien "
            "Landfläche — nicht Wald, Acker, Stadt oder offene Landschaft. Der Platz ist dünn verteilt: In der Hälfte "
            "der Blöcke mit Platz ist weniger als 3 % des Landes frei.")
    set_box(shapes["Quelle"], None,
            "Fläche: Walker et al. 2022 (Modellergebnis: aus Inventur- und Satellitendaten hochgerechnet), Zellen mit "
            "typischem Waldtyp (Hasler et al. 2024); Anteil an der Landfläche je 2°-Block.")
    area.notes_slide.notes_text_frame.text = (
        "Sprechertext: Jetzt von zwei Orten zur ganzen Erde. Zuerst nur die Frage: Wo ist überhaupt Platz? Grün heißt: "
        "Dieser Anteil des Landes ist wiederbewaldbar — kein Wald, kein Acker, keine Stadt, keine offene Landschaft. "
        "Grau: Land ohne Platz. Der Platz ist dünn verteilt, kräftig grün wird es nur im hohen Norden und in einzelnen "
        "Regionen der Tropen.\n\n"
        "Falls Fragen kommen\n"
        "Fläche nach Walker et al. (2022), nur Zellen mit einem typischen Waldtyp nach Hasler et al. (2024). Gezeigt als "
        "Anteil an der Landfläche je 2°-Block; Blöcke mit weniger als 3 von 16 Landzellen sind ausgeblendet (Inselchen, "
        "einzelne Landzellen im Klimadatensatz), die Flächensummen enthalten sie.")

    # 4  Klima chapter: what one tree does where
    ladder = by_title(prs, "Was jede Erweiterung der Systemgrenze kostet")
    k15 = new_slide_after(prs, ladder, "Was ein Baum wo bewirkt")
    remove_pictures(k15)
    svg_picture(k15, "k15")
    shapes = {sh.name: sh for sh in k15.shapes}
    shapes["Kurz gesagt"].top = Inches(5.57)
    shapes["Kurz gesagt"].height = Inches(1.51)
    set_box(shapes["Kurz gesagt"], "Kurz gesagt",
            "Dieselbe Rechnung für jeden Ort der Erde: Baum gepflanzt 2025, Wirkung im Jahr 2150. In den Tropen kühlt er "
            "am stärksten, im hohen Norden und in trockenen Gebieten wärmt er unterm Strich. Aachen "
            f"({de(f['orte']['Aachen'])}) und Joensuu ({de(f['orte']['Joensuu'])} · 10⁻¹⁵ K) liegen dazwischen."
            .replace("(-", "(−"))
    set_box(shapes["Quelle"], None,
            "Eigene Rechnung, volles Modell, SSP2-4,5; typischer Wald je Ort (Hasler et al. 2024), Kohlenstoff der Zelle "
            "(Walker et al. 2022), Albedo lokal gemessen oder Breitenband (Duveiller et al. 2018); Mittel je 2°-Block, "
            "gewichtet mit der wiederbewaldbaren Fläche.")
    k15.notes_slide.notes_text_frame.text = (
        "Sprechertext: Bisher zwei Orte. Jetzt dieselbe Kette für jeden Ort: Wachstum, Albedo, Rückgabe durch Ozean und "
        "Land, vollere Atmosphäre, Störung — und am Ende die Temperatur im Jahr 2150. Grün kühlt, orange wärmt. "
        "Aachen und Joensuu sind die beiden Punkte, die wir kennen.\n\n"
        "Falls Fragen kommen\n"
        f"Je Baum des typischen Waldes am Ort, gepflanzt 2025. 5 % der wiederbewaldbaren Fläche kühlen stärker als "
        f"{de(f['p05'])}, 5 % wärmen stärker als +{de(f['p95'])} · 10⁻¹⁵ K. Mit dem typischen Wald kühlt ein Baum auf "
        f"{de(100 * f['kuehlt_anteil'])} % der Fläche; das Kapitel Vergleich nimmt je Zelle den Waldtyp mit der stärksten "
        "Kühlung und kommt so auf 0,39 Gha.".replace(" -", " −"))

    prs.save(str(deck))
    print("gespeichert:", deck)


if __name__ == "__main__":
    main()
