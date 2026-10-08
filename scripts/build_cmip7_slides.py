"""Replace the Carbon Brief screenshot (slide 2 of dissvortrag_v2.pptx) by two
slides with native charts from the original CMIP7 data:

    2  Selbst die ehrgeizigsten Szenarien verfehlen 1,5 °C      (warming)
    3  … und kommen nur mit CO₂-Entnahme in die Nähe            (removal)

Slide 3 is the old slide 2 (its Kurz-gesagt and source boxes are reused);
slide 2 is new, in the same layout. Every later slide moves down by one, so
the in-text references "Folie 2"/"Folie 3" on slides 4 and 8-10 are updated.

Data: data/cmip7/*.csv (scripts/fetch_cmip7_data.py), read through
nbs.cmip7_figures. Charts keep their numbers in the embedded workbook.

The script runs once on a deck that still has the screenshot; it writes a
snapshot to docs/slides/workspace/ first. To run again, restore that.

    uv run python scripts/build_cmip7_slides.py
    uv run python scripts/build_cmip7_slides.py --deck /tmp/copy.pptx   # Probelauf
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
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import build_native_charts as N  # noqa: E402  (styling helpers of the other native charts)
from nbs import cmip7_figures as C  # noqa: E402

DECK = REPO / "docs" / "slides" / "dissvortrag_v2.pptx"
WORKSPACE = REPO / "docs" / "slides" / "workspace"
TITLE_T = "Selbst die ehrgeizigsten Szenarien verfehlen 1,5 °C"
TITLE_C = "… und kommen nur mit CO₂-Entnahme in die Nähe"


def de(x: float, nd: int = 1) -> str:
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def hexc(k: str) -> str:
    return C.MARKERS[k][1].lstrip("#").upper()


def set_text_keep_style(shape, heading: str | None, body: str) -> None:
    """Replace the text of a Kurz-gesagt/Quelle box, keeping its run formatting."""
    tf = shape.text_frame
    paras = tf.paragraphs
    if heading is not None:
        paras[0].runs[0].text = heading
        for r in paras[0].runs[1:]:
            r.text = ""
        target = paras[1]
    else:
        target = paras[0]
    target.runs[0].text = body
    for r in target.runs[1:]:
        r.text = ""
    for p in paras[(2 if heading is not None else 1):]:
        p._p.getparent().remove(p._p)


def mid_cat(chart):
    """Lines start at the axis, not half a category in."""
    for v in chart._chartSpace.iter(qn("c:crossBetween")):
        v.set("val", "midCat")


def year_labels(years):
    """Only every 25th year carries a label: PowerPoint and LibreOffice then agree
    (LibreOffice ignores tickLblSkip)."""
    return [str(y) if y % 25 == 0 else " " for y in years]


def year_axis(chart):
    ax = chart.category_axis
    N.style_axis(ax, grid=False, size=10)
    N.horizontal_labels(ax)
    ax._element.find(qn("c:majorTickMark")).set("val", "none")


def gaps(chart):
    """Empty cells are gaps (line series end at 2100 and start there), not zeros."""
    c = chart._chartSpace.find(qn("c:chart"))
    d = c.find(qn("c:dispBlanksAs"))
    if d is None:
        d = etree.Element(qn("c:dispBlanksAs"))
        c.find(qn("c:plotArea")).addnext(d)
    d.set("val", "gap")


def no_fill(series):
    series.format.fill.background()
    series.format.line.fill.background()


# ---------------------------------------------------------------------------
# slide 2: warming
# ---------------------------------------------------------------------------


def temperature_chart(slide, frame, anchor):
    t = C.temperature()
    obs = C.observations()
    keys = list(C.MARKERS)
    labelled = ("VL", "ML", "M", "H")   # 2100 values that do not collide on the slide

    def med(k):
        s = t[(t.szenario == k) & (t.jahr >= 2023)]
        return list(s.jahr), list(s["median"])

    series = []
    for k in keys:
        xs, ys = med(k)
        series.append((C.MARKERS[k][0], xs, ys, dict(color=hexc(k), width=2.0)))
    # not the first series: LibreOffice drops the first XY series when its x-range differs from the rest
    series.append(("Beobachtung", list(obs.jahr), list(obs.erwaermung_k), dict(color="1A2320", width=1.75)))
    series += [("1,5 °C", [1950, 2150], [1.5, 1.5], dict(color="6B7570", width=1.0, dash=N.DASH)),
               ("2 °C", [1950, 2150], [2.0, 2.0], dict(color="6B7570", width=1.0, dash=N.DASH)),
               N.vline("2100", 2100, 0, 5, color="6B7570")]
    gf = N.xy_chart(slide, frame, anchor, series, legend=XL_LEGEND_POSITION.TOP,
                    y_title="Erwärmung gegenüber 1850–1900 [°C]", x_min=1950, x_max=2150, x_major=25,
                    y_min=0, y_max=5, y_major=1, y_fmt="0", size=10)
    ch = gf.chart
    ser = {s.name: s for s in ch.series}
    for lvl in ("1,5 °C", "2 °C"):
        N.label_point(ser[lvl], 0, lvl, pos=XL_LABEL_POSITION.ABOVE, size=9, color="6B7570")
    N.label_point(ser["2100"], 1, "2100", pos=XL_LABEL_POSITION.ABOVE, size=9, color="6B7570")
    for k in labelled:
        xs, ys = med(k)
        i = xs.index(2100)
        N.label_point(ser[C.MARKERS[k][0]], i, f"{de(ys[i])} °C", pos=XL_LABEL_POSITION.LEFT, size=9, color=hexc(k))
    names = [s.name for s in ch.series]
    N.hide_legend_entries(ch, [i for i, n in enumerate(names) if n.endswith("°C") or n == "2100"])
    return gf


# ---------------------------------------------------------------------------
# slide 3: removal
# ---------------------------------------------------------------------------


def removal_charts(slide, frame, anchor):
    e = C.removal()
    cum = C.cumulative_removal()
    keys = list(C.MARKERS)
    left, right = frame.cols(2, gap=Emu(int(0.35 * 914400)))
    left = N.Frame(left.x, left.y, left.w * 1.12, left.h)
    right = N.Frame(left.x + left.w + Emu(int(0.3 * 914400)), right.y, frame.x + frame.w - (left.x + left.w + Emu(int(0.3 * 914400))), right.h)

    tot = {k: (e[e.szenario == k].set_index("jahr").neuartig_gt + e[e.szenario == k].set_index("jahr").land_gt)
           for k in keys}
    series = [(C.MARKERS[k][0], [y for y in tot[k].index if y >= 2025], [float(tot[k][y]) for y in tot[k].index if y >= 2025],
               dict(color=hexc(k), width=2.0)) for k in keys]
    series.append(N.vline("2100", 2100, 0, 32, color="6B7570"))
    gf = N.xy_chart(slide, left, anchor, series, title="CO₂-Entnahme je Jahr", legend=XL_LEGEND_POSITION.TOP,
                    y_title="Gt CO₂ je Jahr", x_min=2025, x_max=2150, x_major=25, y_min=0, y_max=32, y_major=5,
                    y_fmt="0", size=10)
    ch = gf.chart
    N.label_point(ch.series[len(keys)], 1, "2100", pos=XL_LABEL_POSITION.ABOVE, size=9, color="6B7570")
    N.hide_legend_entries(ch, [len(keys)])

    return sum_chart(slide, right, anchor)


def sum_chart(slide, right, anchor):
    """Bars: CO2 removed 2024-2100 per marker (the horizon the talk evaluates at)."""
    cum = C.cumulative_removal(2024, 2100)
    order = list(cum.index)[::-1]  # bar charts draw the first category at the bottom
    data = CategoryChartData()
    data.categories = [C.MARKERS[k][0] for k in order]
    data.add_series("Summe 2024–2100", [float(cum.loc[k, "gesamt_gt"]) for k in order])
    gf = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, right.x, right.y, right.w, right.h, data)
    N.place(slide, gf, anchor)
    ch = gf.chart
    N.base_style(ch, title="Summe 2024–2100", font_size=10)
    ch.plots[0].gap_width = 45
    bars = ch.series[0]
    for i, k in enumerate(order):
        N.style_fill(bars.points[i], hexc(k))
        N.label_point(bars, i, de(cum.loc[k, "gesamt_gt"], 0), pos=XL_LABEL_POSITION.OUTSIDE_END, size=10)
    N.style_axis(ch.category_axis, grid=False, size=10)
    N.style_axis(ch.value_axis, title="Gt CO₂", minimum=0, maximum=1000, major=250, fmt="#,##0", size=10)
    return gf


# ---------------------------------------------------------------------------


def snapshot(deck: Path) -> Path:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    dst = WORKSPACE / f"{deck.stem}_vor_cmip7_{datetime.now():%Y%m%d_%H%M%S}.pptx"
    shutil.copy2(deck, dst)
    return dst


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", type=Path, default=DECK)
    a = ap.parse_args()
    deck = a.deck
    if any(p.name.startswith("~$") for p in deck.parent.iterdir()):
        sys.exit("PowerPoint hat das Deck offen (~$-Datei) — erst schließen.")
    prs = Presentation(str(deck))
    old = prs.slides[1]
    pics = [s for s in old.shapes if s.shape_type == 13]
    if len(pics) != 1 or not any("carbonbrief" in s.text_frame.text for s in old.shapes if s.has_text_frame):
        sys.exit("Folie 2 ist nicht mehr der Carbon-Brief-Screenshot — Snapshot aus docs/slides/workspace/ wiederherstellen.")
    print("Snapshot:", snapshot(deck))
    f = C.facts()
    vl, ln, l_, ml = f["VL"], f["LN"], f["L"], f["ML"]

    shapes = {s.name: s for s in old.shapes}
    frame = N.Frame(Inches(0.42), Inches(1.12), Inches(12.5), Inches(4.55))

    # --- new slide 2 (warming), built in the layout of the old one ---
    new = prs.slides.add_slide(old.slide_layout)
    sldIdLst = prs.slides._sldIdLst
    el = sldIdLst[-1]
    sldIdLst.remove(el)
    sldIdLst.insert(1, el)
    new.shapes.title.text = TITLE_T
    kurz = copy.deepcopy(shapes["Kurz gesagt"]._element)
    quelle = copy.deepcopy(shapes["Quelle"]._element)
    new.shapes._spTree.append(kurz)
    new.shapes._spTree.append(quelle)
    nk = [s for s in new.shapes if s.name == "Kurz gesagt"][0]
    nq = [s for s in new.shapes if s.name == "Quelle"][0]
    for s, (x, y, w, h) in ((nk, (6.84, 5.78, 6.08, 1.3)), (nq, (0.42, 5.95, 6.1, 1.0))):
        s.left, s.top, s.width, s.height = Inches(x), Inches(y), Inches(w), Inches(h)
    set_text_keep_style(nk, "Kurz gesagt",
                        f"Selbst im ehrgeizigsten Szenario (Very Low) steigt die Erwärmung im Median auf "
                        f"{de(vl['peak_k'])} °C ({vl['peak_jahr']}) und liegt 2100 noch bei {de(vl['k_2100'])} °C — "
                        f"unter 1,5 °C erst nach {vl['unter_15_ab'] // 5 * 5}. Alle anderen Szenarien bleiben darüber.")
    set_text_keep_style(nq, None,
                        "Modellergebnis: FaIR v2.2, 841 Mitglieder, fair-calibrate 1.5.0, mit den Emissionen der "
                        "sieben CMIP7-Markerszenarien (van Vuuren et al. 2026, GMD 19, 2627; Daten: Zenodo 20713982); "
                        "Linie = Median; nach 2100 Fortschreibung der Szenarien. Beobachtung: "
                        "Indicators of Global Climate Change 2025. Darstellung nach Carbon Brief (Hausfather 2026).")
    anchor = nk._element
    temperature_chart(new, frame, anchor)
    new.notes_slide.notes_text_frame.text = (
        "Sprechertext: Das sind die neuen Szenarien, mit denen die Klimamodelle für den nächsten IPCC-Bericht "
        "rechnen — sieben Wege, von Very Low bis High. Selbst der ehrgeizigste Weg, Very Low, überschreitet 1,5 °C: "
        f"Im Median steigt die Erwärmung auf {de(vl['peak_k'])} °C um {round(vl['peak_jahr'], -1)} und kommt erst im "
        "nächsten Jahrhundert wieder darunter.\n\n"
        "Falls Fragen kommen\n"
        f"Werte (Median): VL 2100 {de(vl['k_2100'], 2)} °C, LN {de(ln['k_2100'], 2)}, L {de(l_['k_2100'], 2)}, "
        f"ML {de(ml['k_2100'], 2)}, M {de(f['M']['k_2100'], 2)}, H {de(f['H']['k_2100'], 2)}, "
        f"HL {de(f['HL']['k_2100'], 2)} °C. Quelle der Läufe: FaIR-Ensemble des ScenarioMIP-Beschreibungspapiers "
        "(fair-calibrate 1.5.0); Carbon Brief nutzt 1.4.5, die Mediane weichen um wenige Hundertstel ab. "
        "Neu gerechnet mit scripts/fetch_cmip7_data.py.")

    # --- old slide 2 becomes slide 3 (removal) ---
    old.shapes.title.text = TITLE_C
    for name in ("Picture 3", "TextBox 4"):
        s = shapes[name]
        s._element.getparent().remove(s._element)
    for rel in [r for r in old.part.rels.values() if r.reltype.endswith("/image")]:
        old.part.drop_rel(rel.rId)
    k, q = shapes["Kurz gesagt"], shapes["Quelle"]
    k.left, k.top, k.width, k.height = Inches(6.84), Inches(5.78), Inches(6.08), Inches(1.3)
    q.left, q.top, q.width, q.height = Inches(0.42), Inches(5.95), Inches(6.1), Inches(1.0)
    set_text_keep_style(k, "Kurz gesagt",
                        f"Wer 1,5 °C nahekommt, rechnet mit großer CO₂-Entnahme: Very Low mit rund "
                        f"{de(vl['gesamt_gt'], 0)} Gt bis 2150, Low und Low-to-Negative mit "
                        f"{de(l_['gesamt_gt'], 0)} und {de(ln['gesamt_gt'], 0)} Gt. Die Szenarien ohne Entnahme "
                        "(Medium, High) landen bei 3 bis 4,7 °C.")
    set_text_keep_style(q, None,
                        "Modellergebnis: CMIP7-Markerszenarien mit Fortschreibung bis 2150 (van Vuuren et al. 2026; "
                        "Daten: Zenodo 20713982). Neuartig = BECCS, Direct Air Capture, Gesteinsverwitterung, Ozean; "
                        "Land = Nettosenke der Landnutzung. Carbon Brief zählt Bodenkohlenstoff mit und kommt für "
                        "Very Low auf 655 Gt. Nach 2100 Fortschreibung der Szenarien.")
    removal_charts(old, frame, k._element)
    old.notes_slide.notes_text_frame.text = (
        "Sprechertext: Und selbst in die Nähe von 1,5 °C kommen die Szenarien nur, weil sie annehmen, dass wir CO₂ "
        "wieder aus der Luft holen. Links pro Jahr: im Very-Low-Szenario rund 5 bis 6 Gigatonnen jährlich, in "
        "Low-to-Negative bis zu 30. Rechts aufsummiert bis 2150. Das ist der Bedarf, gegen den der Vortrag am Ende "
        "rechnet.\n\n"
        "Falls Fragen kommen\n"
        f"Kumuliert 2024–2150 (neuartig + Land): VL {de(vl['neuartig_gt'], 0)} + {de(vl['land_gt'], 0)}, "
        f"L {de(l_['neuartig_gt'], 0)} + {de(l_['land_gt'], 0)}, ML {de(ml['neuartig_gt'], 0)} + {de(ml['land_gt'], 0)}, "
        f"LN {de(ln['neuartig_gt'], 0)} + {de(ln['land_gt'], 0)}, HL {de(f['HL']['neuartig_gt'], 0)} + "
        f"{de(f['HL']['land_gt'], 0)} Gt CO₂. Carbon Brief kommt auf 655 / 1.356 / 1.447 / 2.358 / 1.665 Gt, weil "
        "dort auch Bodenkohlenstoff und weitere Landentnahme aus der vollen IAM-Datenbank zählen; die Fortschreibungen "
        "bis 2150 weisen diese nicht getrennt aus. Die Folien „Naive Rechnung“ und „Bäume reichen nicht“ rechnen "
        "weiter mit Carbon Briefs 655 Gt.")

    # --- references to slide numbers that moved ---
    def fix(slide, old_txt, new_txt):
        hit = False
        for s in slide.shapes:
            if s.has_text_frame:
                for p in s.text_frame.paragraphs:
                    for r in p.runs:
                        if old_txt in r.text:
                            r.text = r.text.replace(old_txt, new_txt)
                            hit = True
        if slide.has_notes_slide:
            for p in slide.notes_slide.notes_text_frame.paragraphs:
                for r in p.runs:
                    if old_txt in r.text:
                        r.text = r.text.replace(old_txt, new_txt)
                        hit = True
        return hit

    slides = list(prs.slides)
    assert fix(slides[4], "Folie 2", "Folie 3"), "Folie 5 (Naive Rechnung): Verweis nicht gefunden"
    # the naive calculation uses the same need as the removal chart on slide 3
    need = round(vl["gesamt_gt"])
    trees = need / 0.18 / 1000  # Billionen (10^12) Bäume bei 0,18 t CO₂ je Baum
    assert fix(slides[4], "rund 655 Gt CO₂ Entnahme", f"{need} Gt CO₂ Entnahme")
    assert fix(slides[4], "655 Gt ÷ 0,18 t  ≈  3,6 Billionen", f"{need} Gt ÷ 0,18 t  ≈  {de(trees)} Billionen")
    assert fix(slides[4], "(CMIP7 Very Low, 655 Gt bis 2150), derselbe, gegen den das Kapitel Vergleich rechnet",
               f"(CMIP7 Very Low, {need} Gt bis 2150, aus den Originaldaten; Carbon Brief kommt mit Bodenkohlenstoff "
               "auf 655 Gt, damit rechnet bisher noch das Kapitel Vergleich)")
    for i in (8, 9, 10):
        assert fix(slides[i], "Folie 3", "Folie 4"), f"Folie {i + 1}: Verweis nicht gefunden"

    prs.save(str(deck))
    print("gespeichert:", deck)


if __name__ == "__main__":
    main()
