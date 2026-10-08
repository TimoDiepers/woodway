"""Replace the plot images in the main part of dissvortrag.pptx with native charts.

Reads the CSVs that ``scripts/export_chart_data.py`` writes to
``docs/slides/chart_data/`` and puts each one on its slide as a PowerPoint
chart, in the frame the old picture occupied. The chart keeps its numbers in
the embedded workbook, so "Daten bearbeiten" in PowerPoint works.

Not converted, because PowerPoint has no chart type for them: the two maps
(slide 37, and the map half of slide 40 -- that picture is cropped to the
map and the bar panel next to it becomes a chart), the Carbon-Brief
screenshot on slide 2, and the picture on slide 18 that sits off the slide.

The script finds each picture by slide number and shape name and stops if
one is missing, so it runs once on a deck that still has the images. To run
it again, restore the snapshot it writes to ``docs/slides/workspace/``.

    uv run python scripts/build_native_charts.py
    uv run python scripts/build_native_charts.py --deck /tmp/copy.pptx   # Probelauf
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import pandas as pd
from lxml import etree
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import (
    XL_CHART_TYPE,
    XL_LABEL_POSITION,
    XL_LEGEND_POSITION,
    XL_MARKER_STYLE,
    XL_TICK_LABEL_POSITION,
)
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pptx_tools as T  # noqa: E402

DATA = T.REPO_ROOT / "docs" / "slides" / "chart_data"
TEXT = "1A2320"
MUTED = "6B7570"
GRID = "D9D6CC"
FONT = "Arial"
C_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

SPECIES_DE = {
    "enf_boreal": ("Gemeine Fichte (60°N)", "2166AC"),
    "dnf_boreal": ("Waldkiefer (52°N)", "8073AC"),
    "dbf_gemaessigt": ("Rotbuche (50°N)", "FDB863"),
    "ebf_subtropisch": ("Rosen-Eukalyptus (Plantage) (25°N)", "7FBC41"),
    "ebf_tropisch": ("Tropischer Mischbestand (0°N)", "1B7837"),
}


def csv(name: str) -> pd.DataFrame:
    hits = sorted(DATA.glob(f"{name}*.csv"))
    if len(hits) != 1:
        raise FileNotFoundError(f"{name}*.csv in {DATA}: {len(hits)} Treffer")
    return pd.read_csv(hits[0])


# ---------------------------------------------------------------------------
# Frame handling: find the picture, put charts where it was
# ---------------------------------------------------------------------------


class Frame:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)

    def cols(self, n, gap=Emu(91440)):
        w = (self.w - gap * (n - 1)) / n
        return [Frame(self.x + i * (w + gap), self.y, w, self.h) for i in range(n)]

    def rows(self, n, gap=Emu(45720), top=0):
        h = (self.h - top - gap * (n - 1)) / n
        return [Frame(self.x, self.y + top + i * (h + gap), self.w, h) for i in range(n)]

    def strip(self, h):
        """Split off a band of height h at the top (for a figure title)."""
        return Frame(self.x, self.y, self.w, h), Frame(self.x, self.y + h, self.w, self.h - h)


def take_shape(slide, name):
    """Return (frame, element) of the named top-level shape."""
    hits = [s for s in slide.shapes if s.name == name]
    if len(hits) != 1:
        raise LookupError(f"Folie {slide_no(slide)}: Form {name!r} {len(hits)}× gefunden")
    s = hits[0]
    return Frame(s.left, s.top, s.width, s.height), s._element


def slide_no(slide):
    return list(slide.part.package.presentation_part.presentation.slides).index(slide) + 1


def remove_picture(slide, el):
    """Remove a picture and, if nothing else uses it, its image relationship."""
    rids = [b.get(qn("r:embed")) for b in el.iter(qn("a:blip"))]
    el.getparent().remove(el)
    for rid in rids:
        if rid and not slide._element.xpath(f'.//*[@r:embed="{rid}"]'):
            slide.part.drop_rel(rid)


def place(slide, gf, anchor_el):
    """Move a freshly appended graphic frame to the anchor's z-position."""
    el = gf._element
    anchor_el.addprevious(el)
    return gf


def add_title_box(slide, frame, text, anchor_el, size=10.5):
    tb = slide.shapes.add_textbox(frame.x, frame.y, frame.w, frame.h)
    tb.name = "Diagrammtitel"
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.name = FONT
    r.font.color.rgb = RGBColor.from_string(TEXT)
    anchor_el.addprevious(tb._element)
    return tb


# ---------------------------------------------------------------------------
# Chart styling
# ---------------------------------------------------------------------------


def _sub(parent, tag, **attrs):
    ns, local = tag.split(":")
    el = etree.SubElement(parent, f"{{{C_NS if ns == 'c' else A_NS}}}{local}")
    for k, v in attrs.items():
        el.set(k, str(v))
    return el


def no_fill_spPr():
    sp = etree.Element(qn("c:spPr"))
    etree.SubElement(sp, qn("a:noFill"))
    ln = etree.SubElement(sp, qn("a:ln"))
    etree.SubElement(ln, qn("a:noFill"))
    return sp


def base_style(chart, *, legend=None, title=None, font_size=9):
    """Transparent background, deck font and colours, quiet frame."""
    cs = chart._chartSpace
    cs.find(qn("c:chart")).addnext(no_fill_spPr())
    plot_area = cs.find(qn("c:chart")).find(qn("c:plotArea"))
    old = plot_area.find(qn("c:spPr"))
    if old is not None:
        plot_area.remove(old)
    plot_area.append(no_fill_spPr())
    rc = cs.find(qn("c:roundedCorners"))
    if rc is None:
        rc = etree.Element(qn("c:roundedCorners"))
        cs.insert(0, rc)
    rc.set("val", "0")

    chart.font.name = FONT
    chart.font.size = Pt(font_size)
    chart.font.color.rgb = RGBColor.from_string(TEXT)

    chart.has_title = bool(title)
    if title:
        tf = chart.chart_title.text_frame
        tf.text = title
        for p in tf.paragraphs:
            for r in p.runs:
                r.font.size = Pt(font_size + 1)
                r.font.bold = True
                r.font.name = FONT
                r.font.color.rgb = RGBColor.from_string(TEXT)
    if legend is None:
        chart.has_legend = False
    else:
        chart.has_legend = True
        chart.legend.position = legend
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(font_size - 0.5)
        chart.legend.font.name = FONT


def style_axis(axis, *, title=None, minimum=None, maximum=None, major=None,
               fmt=None, grid=True, low_labels=False, size=9):
    axis.has_major_gridlines = grid
    if grid:
        gl = axis.major_gridlines.format.line
        gl.color.rgb = RGBColor.from_string(GRID)
        gl.width = Pt(0.5)
    axis.format.line.color.rgb = RGBColor.from_string("8A918C")
    axis.format.line.width = Pt(0.75)
    axis.tick_labels.font.size = Pt(size)
    axis.tick_labels.font.name = FONT
    axis.tick_labels.font.color.rgb = RGBColor.from_string(TEXT)
    if fmt:
        axis.tick_labels.number_format = fmt
        axis.tick_labels.number_format_is_linked = False
    if minimum is not None:
        axis.minimum_scale = minimum
    if maximum is not None:
        axis.maximum_scale = maximum
    if major is not None:
        axis.major_unit = major
    if low_labels:
        axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    if title:
        axis.has_title = True
        tf = axis.axis_title.text_frame
        tf.text = title
        for p in tf.paragraphs:
            for r in p.runs:
                r.font.size = Pt(size)
                r.font.bold = False
                r.font.name = FONT
                r.font.color.rgb = RGBColor.from_string(TEXT)


def style_line(series, color, *, width=1.75, dash=None, alpha=None, marker=False):
    ln = series.format.line
    ln.color.rgb = RGBColor.from_string(color)
    ln.width = Pt(width)
    if dash:
        ln.dash_style = dash
    if alpha is not None:
        clr = series.format.line._get_or_add_ln().find(qn("a:solidFill")).find(qn("a:srgbClr"))
        _sub(clr, "a:alpha", val=int(alpha * 100000))
    series.smooth = False
    if marker:
        series.marker.style = XL_MARKER_STYLE.CIRCLE
        series.marker.size = 5
        series.marker.format.fill.solid()
        series.marker.format.fill.fore_color.rgb = RGBColor.from_string(color)
        series.marker.format.line.color.rgb = RGBColor.from_string(color)
    else:
        series.marker.style = XL_MARKER_STYLE.NONE


def style_fill(target, color, alpha=None):
    target.format.fill.solid()
    target.format.fill.fore_color.rgb = RGBColor.from_string(color)
    if alpha is not None:
        sp = target.format._element.find(qn("c:spPr"))
        clr = sp.find(qn("a:solidFill")).find(qn("a:srgbClr"))
        _sub(clr, "a:alpha", val=int(alpha * 100000))


def hide_legend_entries(chart, indices):
    leg = chart._chartSpace.find(qn("c:chart")).find(qn("c:legend"))
    pos = leg.find(qn("c:legendPos"))
    for i in sorted(indices, reverse=True):
        e = etree.Element(qn("c:legendEntry"))
        _sub(e, "c:idx", val=i)
        _sub(e, "c:delete", val=1)
        pos.addnext(e)


def tick_skip(axis, n):
    ax = axis._element
    anchor = ax.find(qn("c:noMultiLvlLbl"))
    for tag in ("c:tickLblSkip", "c:tickMarkSkip"):
        el = etree.Element(qn(tag))
        el.set("val", str(n))
        if anchor is not None:
            anchor.addprevious(el)
        else:
            ax.append(el)


def no_gap_area(chart):
    """Treat blanks as zero in area charts."""
    c = chart._chartSpace.find(qn("c:chart"))
    d = c.find(qn("c:dispBlanksAs"))
    if d is None:
        d = etree.Element(qn("c:dispBlanksAs"))
        c.find(qn("c:plotArea")).addnext(d)
    d.set("val", "zero")


# ---------------------------------------------------------------------------
# Combo charts: move series into a second chart group
# ---------------------------------------------------------------------------

_NEXT_AX = [700000000]


def _new_ax_id():
    _NEXT_AX[0] += 1
    return str(_NEXT_AX[0])


def split_series(chart, indices, kind, *, secondary=False, y_title=None):
    """Move the series with the given idx into a new line/scatter group.

    kind: "line" (category axis) or "scatter" (XY). With secondary=True the
    group gets its own pair of axes, the value axis drawn on the right.
    Returns the new group element.
    """
    plot_area = chart._chartSpace.find(qn("c:chart")).find(qn("c:plotArea"))
    first = next(el for el in plot_area if el.tag.endswith("Chart"))
    ax_ids = [a.get("val") for a in first.findall(qn("c:axId"))]

    tag = {"line": "c:lineChart", "scatter": "c:scatterChart"}[kind]
    grp = etree.Element(qn(tag))
    if kind == "line":
        _sub(grp, "c:grouping", val="standard")
    else:
        _sub(grp, "c:scatterStyle", val="lineMarker")
    _sub(grp, "c:varyColors", val=0)

    for ser in list(first.findall(qn("c:ser"))):
        if int(ser.find(qn("c:idx")).get("val")) not in indices:
            continue
        first.remove(ser)
        if kind == "line":
            inv = ser.find(qn("c:invertIfNegative"))
            if inv is not None:
                ser.remove(inv)
            for t in ("c:shape",):
                el = ser.find(qn(t))
                if el is not None:
                    ser.remove(el)
            if ser.find(qn("c:marker")) is None:
                m = etree.Element(qn("c:marker"))
                _sub(m, "c:symbol", val="none")
                anchor = ser.find(qn("c:spPr"))
                (anchor if anchor is not None else ser.find(qn("c:tx"))).addnext(m)
            if ser.find(qn("c:smooth")) is None:
                _sub(ser, "c:smooth", val=0)
        grp.append(ser)

    if kind == "line":
        _sub(grp, "c:marker", val=1)

    if not secondary:
        for a in ax_ids:
            _sub(grp, "c:axId", val=a)
        first.addnext(grp)
        return grp

    x_id, y_id = _new_ax_id(), _new_ax_id()
    _sub(grp, "c:axId", val=x_id)
    _sub(grp, "c:axId", val=y_id)
    first.addnext(grp)

    last_ax = [el for el in plot_area if el.tag.endswith("Ax")][-1]
    x_tag = "c:catAx" if kind == "line" else "c:valAx"
    x_ax = etree.Element(qn(x_tag))
    _sub(x_ax, "c:axId", val=x_id)
    sc = _sub(x_ax, "c:scaling")
    _sub(sc, "c:orientation", val="minMax")
    _sub(x_ax, "c:delete", val=1)
    _sub(x_ax, "c:axPos", val="b")
    _sub(x_ax, "c:majorTickMark", val="none")
    _sub(x_ax, "c:minorTickMark", val="none")
    _sub(x_ax, "c:tickLblPos", val="nextTo")
    _sub(x_ax, "c:crossAx", val=y_id)
    _sub(x_ax, "c:crosses", val="autoZero")
    if kind == "scatter":
        _sub(x_ax, "c:crossBetween", val="midCat")
    else:
        _sub(x_ax, "c:auto", val=1)
        _sub(x_ax, "c:lblAlgn", val="ctr")
        _sub(x_ax, "c:lblOffset", val=100)
        _sub(x_ax, "c:noMultiLvlLbl", val=0)

    y_ax = etree.Element(qn("c:valAx"))
    _sub(y_ax, "c:axId", val=y_id)
    sc = _sub(y_ax, "c:scaling")
    _sub(sc, "c:orientation", val="minMax")
    _sub(y_ax, "c:delete", val=0)
    _sub(y_ax, "c:axPos", val="r")
    _sub(y_ax, "c:numFmt", formatCode="General", sourceLinked=1)
    _sub(y_ax, "c:majorTickMark", val="out")
    _sub(y_ax, "c:minorTickMark", val="none")
    _sub(y_ax, "c:tickLblPos", val="nextTo")
    _sub(y_ax, "c:crossAx", val=x_id)
    _sub(y_ax, "c:crosses", val="max")
    _sub(y_ax, "c:crossBetween", val="midCat" if kind == "scatter" else "between")
    last_ax.addnext(x_ax)
    x_ax.addnext(y_ax)
    return grp


def primary_value_axis(chart):
    from pptx.chart.axis import ValueAxis

    plot_area = chart._chartSpace.find(qn("c:chart")).find(qn("c:plotArea"))
    vals = plot_area.findall(qn("c:valAx"))
    return ValueAxis(vals[1] if plot_area.find(qn("c:scatterChart")) is not None else vals[0])


def horizontal_labels(axis):
    """Keep category labels horizontal so PowerPoint wraps them instead of rotating."""
    body = axis._element.find(qn("c:txPr")).find(qn("a:bodyPr"))
    body.set("rot", "0")
    body.set("vert", "horz")


def secondary_value_axis(chart):
    from pptx.chart.axis import ValueAxis

    plot_area = chart._chartSpace.find(qn("c:chart")).find(qn("c:plotArea"))
    return ValueAxis(plot_area.findall(qn("c:valAx"))[-1])


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def xy_chart(slide, frame, anchor, series, *, title=None, legend=None, x_title=None,
             y_title=None, x_min=None, x_max=None, x_major=None, y_min=None,
             y_max=None, y_major=None, y_fmt=None, x_fmt="0", low_x=False, size=9):
    """series: list of (name, xs, ys, style-dict)."""
    data = XyChartData()
    for name, xs, ys, _ in series:
        s = data.add_series(name)
        for x, y in zip(xs, ys):
            if pd.notna(x) and pd.notna(y):
                s.add_data_point(float(x), float(y))
    gf = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS,
                                frame.x, frame.y, frame.w, frame.h, data)
    place(slide, gf, anchor)
    ch = gf.chart
    base_style(ch, legend=legend, title=title, font_size=size)
    for ser, (_, _, _, st) in zip(ch.series, series):
        style_line(ser, **st)
    style_axis(ch.category_axis, title=x_title, minimum=x_min, maximum=x_max, major=x_major,
               fmt=x_fmt, grid=False, low_labels=low_x, size=size)
    style_axis(ch.value_axis, title=y_title, minimum=y_min, maximum=y_max, major=y_major,
               fmt=y_fmt, size=size)
    return gf


def vline(name, x, y0, y1, color=TEXT):
    return (name, [x, x], [y0, y1], dict(color=color, width=1.0, dash=MSO_LINE_DASH_STYLE.ROUND_DOT))


def label_point(series, i, text, pos=XL_LABEL_POSITION.RIGHT, size=8.5, color=TEXT):
    dl = series.points[i].data_label
    dl.has_text_frame = True
    dl.text_frame.text = text
    if pos is not None:
        dl.position = pos
    for p in dl.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(size)
            r.font.name = FONT
            r.font.color.rgb = RGBColor.from_string(color)


YEAR_AXIS = dict(x_min=2025, x_max=2150, x_major=25)
SOLID, DASH, DOT = None, MSO_LINE_DASH_STYLE.DASH, MSO_LINE_DASH_STYLE.ROUND_DOT


# -- slide 11 -----------------------------------------------------------------


def slide_11(slide):
    pics = {n: take_shape(slide, n) for n in ("Picture 4", "Picture 5", "Picture 6")}

    d = csv("11a_")
    f, a = pics["Picture 4"]
    xy_chart(slide, f, a, [("Netto-CO₂-Fluss", d.stunde, d.iloc[:, 1], dict(color="1E5631", width=2.25))],
             title="A. Diurnal Time Scale (24 Hours): Photosynthesis vs. Respiration Balance",
             x_title="Hour of Day", y_title="Net CO₂ Flux [µmol/m²/s]",
             x_min=0, x_max=24, x_major=2, y_min=-20, y_max=6, y_major=5, low_x=True)

    d = csv("11b_")
    f, a = pics["Picture 5"]
    data = CategoryChartData()
    data.categories = list(d.monat)
    data.add_series("Monthly Net CO₂ Exchange", [float(v) for v in d.iloc[:, 1]])
    gf = slide.shapes.add_chart(XL_CHART_TYPE.LINE, f.x, f.y, f.w, f.h, data)
    place(slide, gf, a)
    ch = gf.chart
    base_style(ch, title="B. Seasonal Time Scale (12 Months): Growth Peak, Decoupling & Winter Respiration")
    style_line(ch.series[0], "2E7D32", width=2.25)
    style_axis(ch.category_axis, title="Month of Year", grid=False, low_labels=True)
    style_axis(ch.value_axis, title="Net CO₂ Balance [kg CO₂/tree/month]", minimum=-90, maximum=60, major=20)

    d = csv("11c_")
    f, a = pics["Picture 6"]
    gf = xy_chart(slide, f, a, [
        ("Cumulative Carbon Stored (Undisturbed S-Curve)", d.alter_a, d.gespeichert_kg_co2_je_baum,
         dict(color="1E5631", width=2.25)),
        ("Disturbance Reversal (Fire/Disease/Logging)", d.alter_a, d.stoerung_kg_co2_je_baum,
         dict(color="D32F2F", width=2.0, dash=DASH)),
        ("Annual Sequestration Rate (kg CO₂/yr)", d.alter_a, d.jaehrliche_aufnahme_kg_co2_je_baum_a,
         dict(color="0288D1", width=2.0)),
    ], title="C. Decadal & Stand Age Scale (100 Years): S-Curve Growth, Aging Turnover & Disturbance Risks",
        legend=XL_LEGEND_POSITION.BOTTOM, x_title="Tree / Stand Age [Years]",
        y_title="Cumulative Carbon Stored [kg CO₂/tree]", x_min=0, x_max=100, x_major=20,
        y_min=0, y_max=2800, y_major=500)
    ch = gf.chart
    split_series(ch, {2}, "scatter", secondary=True)
    style_axis(secondary_value_axis(ch), title="Annual Sequestration Rate [kg CO₂/tree/yr]",
               minimum=0, maximum=55, major=10, grid=False)

    for _, el in pics.values():
        remove_picture(slide, el)


# -- slide 12 -----------------------------------------------------------------


def slide_12(slide):
    f, el = take_shape(slide, "Group 9530")
    d = csv("12_")
    xy_chart(slide, f, el, [
        ("nur Wachstum", d.jahr, d.nur_wachstum_kgC, dict(color="1B7837", width=2.0)),
        ("mit Störung, ΔT_w = 0", d.jahr, d.mit_stoerung_dTw_0_kgC, dict(color="D6604D", width=2.0)),
        ("mit Störung, ΔT_w = 1 K (linear)", d.jahr, d.mit_stoerung_dTw_1K_linear_kgC,
         dict(color="A50F15", width=2.0)),
    ], legend=XL_LEGEND_POSITION.BOTTOM, x_title="Jahr", y_title="m_Baum [kgC]",
        x_min=2025, x_max=2150, x_major=25, y_min=0, y_max=55, y_major=10)
    el.getparent().remove(el)


# -- slides 15/16 -------------------------------------------------------------


def albedo_season(slide, no, pic_name):
    f, el = take_shape(slide, pic_name)
    head, body = f.strip(Emu(int(0.24 * 914400)))
    add_title_box(slide, head, "Der Albedo-Effekt ist ein Frühjahrsereignis — Gemeine Fichte "
                               "(Picea abies), Duveiller et al. 2018", el, size=9)
    panels = [("a_", "Δα [-] (Winterkontrast)", "0.00"),
              ("b_", "q̇ [W/m²] (Sommermaximum)", "0"),
              ("c_", "Δα · q̇ [W/m²] (Frühjahrsspitze)", "0")]
    for (suffix, y_title, fmt), sub in zip(panels, body.cols(3)):
        d = csv(f"{no}{suffix}")
        data = CategoryChartData()
        data.categories = list(d.monat)
        data.add_series("45°N", [float(v) for v in d.iloc[:, 1]])
        data.add_series("60°N", [float(v) for v in d.iloc[:, 2]])
        if suffix == "c_":
            data.add_series("Jahresmittel 45°N", [float(v) for v in d.jahresmittel_45N])
            data.add_series("Jahresmittel 60°N", [float(v) for v in d.jahresmittel_60N])
        gf = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, sub.x, sub.y, sub.w, sub.h, data)
        place(slide, gf, el)
        ch = gf.chart
        base_style(ch, legend=XL_LEGEND_POSITION.BOTTOM if suffix == "a_" else None, font_size=8)
        style_line(ch.series[0], "1B9E77", width=1.75, marker=True)
        style_line(ch.series[1], "7570B3", width=1.75, marker=True)
        if suffix == "c_":
            style_line(ch.series[2], "1B9E77", width=1.0, dash=DOT)
            style_line(ch.series[3], "7570B3", width=1.0, dash=DOT)
        style_axis(ch.category_axis, grid=False, low_labels=True, size=8)
        style_axis(ch.value_axis, title=y_title, fmt=fmt, size=8)
    remove_picture(slide, el)


# -- slide 29 -----------------------------------------------------------------


def slide_29(slide):
    f, el = take_shape(slide, "fig_impulsantwort.png")
    d = csv("29_")
    xy_chart(slide, f, el, [
        ("schnell: Deckschicht", d.jahre_nach_stoss, d.schnell_deckschicht,
         dict(color="3F6AA1", width=1.5, dash=DASH)),
        ("langsam: Tiefsee", d.jahre_nach_stoss, d.langsam_tiefsee,
         dict(color="8B4A7A", width=1.5, dash=DASH)),
        ("g_T(t) = Summe", d.jahre_nach_stoss, d.gT_summe, dict(color="2F7D4F", width=2.75)),
    ], legend=XL_LEGEND_POSITION.RIGHT, x_title="Zeit nach dem Energiestoß [Jahre]",
        y_title="Temperaturantwort [-]", x_min=0, x_max=300, x_major=50, y_min=0, y_max=1.0,
        y_major=0.2, y_fmt="0.0")
    remove_picture(slide, el)


# -- slides 31/32 -------------------------------------------------------------


def slide_31(slide):
    f, el = take_shape(slide, "Picture 3")
    head, body = f.strip(Emu(int(0.24 * 914400)))
    add_title_box(slide, head, "Gemeine Fichte (Picea abies), 60°N, SSP245", el, size=9)
    rows = body.rows(3)
    d = csv("31a_")
    xy_chart(slide, rows[0], el, [("Vorrat", d.jahr, d.vorrat_kgC_je_baum, dict(color="1B7837"))],
             y_title="Vorrat m [kgC je Baum]", y_min=0, y_major=10, size=8, **YEAR_AXIS)
    d = csv("31b_")
    xy_chart(slide, rows[1], el, [("CO₂-Fluss", d.jahr, d.co2_fluss_kg_je_a, dict(color="1B7837"))],
             y_title="ṁ_CO₂ [kg CO₂/a]", y_fmt="0.0", low_x=True, size=8, **YEAR_AXIS)
    d = csv("31c_")
    xy_chart(slide, rows[2], el, [("Bedeckungsgrad", d.jahr, d.bedeckungsgrad, dict(color="D95F02"))],
             x_title="Jahr", y_title="Bedeckungsgrad f [-]", y_min=0, y_max=1.0, y_major=0.2,
             y_fmt="0.0", size=8, **YEAR_AXIS)
    remove_picture(slide, el)


def _t_star(years, values):
    sign = values > 0
    flips = [i for i in range(1, len(values)) if sign[i] != sign[i - 1]]
    return int(years[flips[-1]]) if flips else None


def slide_32(slide):
    f, el = take_shape(slide, "Picture 3")
    head, body = f.strip(Emu(int(0.24 * 914400)))
    rows = body.rows(2)
    specs = [
        (csv("32a_"), "Antrieb [10⁻¹⁵ W/m² je Baum]", ["φ_CO₂ (kühlt)", "φ_α (wärmt)", "φ netto"], "φ"),
        (csv("32b_"), "Temperatur [10⁻¹⁵ K je Baum]", ["ΔT_CO₂", "ΔT_α", "ΔT netto"], "ΔT"),
    ]
    stars = []
    for i, ((d, y_title, names, sym), sub) in enumerate(zip(specs, rows)):
        cols = d.columns[1:]
        lo, hi = float(d[cols].min().min()), float(d[cols].max().max())
        ts = _t_star(d.jahr.values, d[cols[2]].values)
        stars.append(ts)
        series = [
            (names[0], d.jahr, d[cols[0]], dict(color="1B7837")),
            (names[1], d.jahr, d[cols[1]], dict(color="D95F02")),
            (names[2], d.jahr, d[cols[2]], dict(color="252525", width=2.5)),
        ]
        if ts:
            series.append(vline(f"t*_{sym}", ts, lo, hi))
        gf = xy_chart(slide, sub, el, series, legend=XL_LEGEND_POSITION.TOP if i == 0 else None,
                      x_title="Jahr" if i == 1 else None, y_title=y_title, low_x=True, size=8,
                      **YEAR_AXIS)
        ch = gf.chart
        if ts:
            label_point(ch.series[3], 1, f"t* = {ts}")
            if i == 0:
                hide_legend_entries(ch, [3])
    add_title_box(slide, head, f"Gemeine Fichte (Picea abies), 60°N, SSP245 — thermische Trägheit: "
                               f"φ wird {stars[1] - stars[0]} Jahre vor ΔT dauerhaft negativ", el, size=9)
    remove_picture(slide, el)


# -- slide 33 -----------------------------------------------------------------

COHORT = ("08519C", "3182BD", "E6550D", "A63603")


def slide_33(slide):
    f, el = take_shape(slide, "Picture 6")
    head, body = f.strip(Emu(int(0.26 * 914400)))
    add_title_box(slide, head, "Gemeine Fichte (Picea abies), 60°N, SSP245: derselbe Baum, vier Pflanzjahre",
                  el, size=10)
    left, mid, right = body.cols(3, gap=Emu(int(0.15 * 914400)))
    c = csv("33c_")
    years_planted = [int(v) for v in c.pflanzjahr]

    # left: hazard curve with each cohort's window shaded
    d = csv("33a_")
    data = CategoryChartData()
    data.categories = [int(v) for v in d.jahr]
    for py in years_planted:
        data.add_series(f"Fenster {py}", [None if pd.isna(v) else float(v) for v in d[f"fenster_{py}_pct_a"]])
    data.add_series("jährliche Störungswahrscheinlichkeit", [float(v) for v in d.stoerungswahrscheinlichkeit_pct_a])
    gf = slide.shapes.add_chart(XL_CHART_TYPE.AREA, left.x, left.y, left.w, left.h, data)
    place(slide, gf, el)
    ch = gf.chart
    base_style(ch, title="Das Risiko steigt mit der Erwärmung (γ = 0,20 1/K)", font_size=8)
    ch.plots[0].vary_by_categories = False
    grouping = ch.plots[0]._element.find(qn("c:grouping"))
    grouping.set("val", "standard")
    no_gap_area(ch)
    for i, color in enumerate(COHORT):
        style_fill(ch.series[i], color, alpha=0.3)
        ch.series[i].format.line.fill.background()
    split_series(ch, {len(COHORT)}, "line")
    style_line(ch.series[len(COHORT)], "252525", width=1.75)
    for i, py in enumerate(years_planted):
        window = d[f"fenster_{py}_pct_a"]
        j = int(window.idxmax())
        label_point(ch.series[i], j, f"×{c.risikofaktor[i]:.2f}".replace(".", ","),
                    pos=None, color=COHORT[i])
    style_axis(ch.category_axis, title="Jahr", grid=False, size=8)
    tick_skip(ch.category_axis, 25)
    style_axis(ch.value_axis, title="jährl. Störungswahrscheinlichkeit [%]", minimum=0, fmt="0.0", size=8)

    # middle: stock per cohort, with and without disturbance
    d = csv("33b_")
    series = [(f"gepflanzt {py}", d.jahr, d[f"mit_stoerung_{py}_kgC"], dict(color=COHORT[i], width=1.75))
              for i, py in enumerate(years_planted)]
    series += [(f"ohne Störung {py}", d.jahr, d[f"ohne_stoerung_{py}_kgC"],
                dict(color=COHORT[i], width=1.0, dash=DOT)) for i, py in enumerate(years_planted)]
    gf = xy_chart(slide, mid, el, series, title="Vorrat: durchgezogen mit Störung, gepunktet ohne",
                  legend=XL_LEGEND_POSITION.TOP, x_title="Jahr", y_title="Kohlenstoffvorrat [kgC]",
                  y_min=0, size=8, x_min=2020, x_max=2150, x_major=20)
    hide_legend_entries(gf.chart, range(4, 8))

    # right: risk as bars, t* as diamonds on the second axis
    data = CategoryChartData()
    data.categories = [str(py) for py in years_planted]
    data.add_series("P(mind. 1 Störung in 50 a)", [float(v) for v in c.p_stoerung_in_50a_pct])
    data.add_series("Ausgleichsjahr t*", [float(v) for v in c.ausgleichsjahr_t_star])
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, right.x, right.y, right.w, right.h, data)
    place(slide, gf, el)
    ch = gf.chart
    base_style(ch, title="Später pflanzen kostet zweimal: Risiko (Balken) und Zeit (t*, Rauten)", font_size=8)
    ch.plots[0].gap_width = 60
    bars = ch.series[0]
    for i, color in enumerate(COHORT):
        style_fill(bars.points[i], color)
        label_point(bars, i, f"−{c.vorratsverlust_pct[i]:.1f} %".replace(".", ","),
                    pos=XL_LABEL_POSITION.OUTSIDE_END, size=8)
    split_series(ch, {1}, "line", secondary=True)
    t = ch.series[1]
    style_line(t, "252525", width=1.25)
    t.marker.style = XL_MARKER_STYLE.DIAMOND
    t.marker.size = 8
    t.marker.format.fill.solid()
    t.marker.format.fill.fore_color.rgb = RGBColor.from_string("252525")
    style_axis(ch.category_axis, title="Pflanzjahr", grid=False, size=8)
    style_axis(primary_value_axis(ch), title="P(mind. 1 Störung in 50 a) [%]", minimum=0, maximum=100,
               major=20, size=8)
    style_axis(secondary_value_axis(ch), title="Ausgleichsjahr t*", minimum=2060, maximum=2150,
               major=10, fmt="0", grid=False, size=8)
    remove_picture(slide, el)


# -- slides 34/35 -------------------------------------------------------------

def slide_34(slide):
    from nbs.species import get_species

    f, el = take_shape(slide, "Picture 3")
    d = csv("34_")
    solid, dotted, sat = [], [], []
    for key, (name, color) in SPECIES_DE.items():
        sp = get_species(key)
        k = f"{sp.k:.3f}".replace(".", ",")
        solid.append((f"{name} · m_max {sp.m_max_kgC:.0f} kgC · k {k} 1/a", d.jahr,
                      d[f"{key}_mit_stoerung_kgC"], dict(color=color, width=2.25)))
        dotted.append((f"{name} ohne Störung", d.jahr, d[f"{key}_ohne_stoerung_kgC"],
                       dict(color=color, width=1.0, dash=DOT)))
        sat.append((f"{name} m_max", [2025, 2150], [sp.m_max_kgC] * 2,
                    dict(color=color, width=0.75, dash=DASH, alpha=0.45)))
    gf = xy_chart(slide, f, el, solid + dotted + sat,
                  title="Eine Wachstumsform, fünf Parametersätze\n"
                        "durchgezogen mit Störung, gepunktet ohne — gestrichelt die Sättigung m_max",
                  legend=XL_LEGEND_POSITION.BOTTOM, x_title="Jahr",
                  y_title="Kohlenstoffvorrat je Baum [kgC]", y_min=0, y_max=105, y_major=20,
                  **YEAR_AXIS)
    hide_legend_entries(gf.chart, range(5, 15))
    remove_picture(slide, el)


def slide_35(slide):
    f, el = take_shape(slide, "Picture 3")
    d = csv("35_")
    colors = ("1F77B4", "FF7F0E", "2CA02C", "D62728", "9467BD")
    series = [(name, d.jahr, d[f"{key}_dT_1e-15_K"], dict(color=c, width=1.75))
              for (key, (name, _)), c in zip(SPECIES_DE.items(), colors)]
    xy_chart(slide, f, el, series, legend=XL_LEGEND_POSITION.BOTTOM, x_title="Jahr",
             y_title="ΔT [10⁻¹⁵ K je Baum]", low_x=True, **YEAR_AXIS)
    remove_picture(slide, el)


# -- slide 38 -----------------------------------------------------------------


def slide_38(slide):
    f, el = take_shape(slide, "Picture 3")
    d = csv("38_")
    data = CategoryChartData()
    data.categories = list(d.stufe)
    data.add_series("Kohlenstoff [GtC]", [float(v) for v in d.kohlenstoff_GtC])
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, f.x, f.y, f.w, f.h, data)
    place(slide, gf, el)
    ch = gf.chart
    first, last = float(d.kohlenstoff_GtC.iloc[0]), float(d.kohlenstoff_GtC.iloc[-1])
    base_style(ch, title=(f"Die Korrekturkaskade: von Bastins Rohwert zum nutzbaren Potenzial\n"
                          f"{first:.0f} GtC → {last:.1f} GtC ({100 * last / first:.1f} % des Rohwerts)"
                          ).replace(".", ","))
    ch.plots[0].gap_width = 70
    s = ch.series[0]
    for i, art in enumerate(d.art):
        color = "999999" if art == "Literatur" else "3B7DD8"
        style_fill(s.points[i], "1B7A3D" if i == len(d) - 1 else color)
    plot = ch.plots[0]
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = "0.0"
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(9)
    dl.font.bold = True
    style_axis(ch.category_axis, grid=False, size=8)
    horizontal_labels(ch.category_axis)
    style_axis(ch.value_axis, title="Kohlenstoff [GtC]", minimum=0, maximum=220, major=50)
    remove_picture(slide, el)


# -- slide 40 -----------------------------------------------------------------


def slide_40(slide):
    from nbs.map_plots import _SPECIES_COLORS, footer_text

    s = next(sh for sh in slide.shapes if sh.name == "Picture 6")
    el = s._element
    f = Frame(s.left, s.top, s.width, s.height)
    # crop to the map: the bar panel becomes a chart, the provenance footer text
    crop_l, crop_r, crop_b = 0.10, 0.325, 0.115
    src = el.find(qn("p:blipFill")).find(qn("a:srcRect"))
    if src is None:
        src = etree.Element(qn("a:srcRect"))
        el.find(qn("p:blipFill")).find(qn("a:blip")).addnext(src)
    src.set("l", str(int(crop_l * 100000)))
    src.set("r", str(int(crop_r * 100000)))
    src.set("b", str(int(crop_b * 100000)))
    footer_h = Emu(int(0.30 * 914400))
    map_h = f.h - footer_h
    aspect = (1 - crop_l - crop_r) / (1 - crop_b) * (f.w / f.h)
    map_w = int(map_h * aspect)
    s.left, s.top, s.width, s.height = f.x, f.y, map_w, map_h

    chart_frame = Frame(f.x + map_w + Emu(91440), f.y, f.w - map_w - Emu(91440), map_h)
    d = csv("40_").iloc[::-1].reset_index(drop=True)  # bar charts draw bottom-up
    data = CategoryChartData()
    data.categories = list(d.art)
    data.add_series("empfohlen", [float(v) for v in d.empfohlen_Gha])
    data.add_series("Breitenband-Zuordnung", [float(v) for v in d.breitenband_Gha])
    gf = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, chart_frame.x, chart_frame.y,
                                chart_frame.w, chart_frame.h, data)
    el.addnext(gf._element)
    ch = gf.chart
    base_style(ch, title="Artenwahl statt Breitenband: 25,4 % mehr Kühlung in 2100",
               legend=XL_LEGEND_POSITION.BOTTOM)
    ch.plots[0].gap_width = 50
    ch.plots[0].overlap = 100
    style_fill(ch.series[0], "7F7F7F")  # legend swatch; points keep their own colour
    for i, key in enumerate(d.art_key):
        style_fill(ch.series[0].points[i], _SPECIES_COLORS[key].lstrip("#").upper())
    hollow = ch.series[1]
    hollow.format.fill.background()
    hollow.format.line.color.rgb = RGBColor.from_string("404040")
    hollow.format.line.width = Pt(1.25)
    hollow.format.line.dash_style = DASH
    style_axis(ch.category_axis, grid=False, size=8.5)
    style_axis(ch.value_axis, title="verfügbare Fläche [Gha]", minimum=0, maximum=0.4,
               major=0.1, fmt="0.0")

    tb = slide.shapes.add_textbox(f.x, f.y + map_h, f.w, footer_h)
    tb.name = "Kartenquelle"
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    r = tf.paragraphs[0].add_run()
    r.text = footer_text()
    r.font.size = Pt(7)
    r.font.name = FONT
    r.font.color.rgb = RGBColor.from_string(MUTED)
    gf._element.addnext(tb._element)


# -- slide 42 -----------------------------------------------------------------


def slide_42(slide):
    f, el = take_shape(slide, "Picture 3")
    d = csv("42_")
    data = CategoryChartData()
    data.categories = list(d.groesse)
    data.add_series("Fläche [Gha]", [float(v) for v in d.flaeche_Gha])
    data.add_series("eisfreie Landfläche der Erde (~13 Gha, Näherung)",
                    [float(v) for v in d.eisfreie_landflaeche_Gha])
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, f.x, f.y, f.w, f.h, data)
    place(slide, gf, el)
    ch = gf.chart
    base_style(ch, title="Umkehrrechnung: benötigte vs. bepflanzbare Fläche\nSSP245, 2050–2150",
               legend=XL_LEGEND_POSITION.BOTTOM)
    ch.plots[0].gap_width = 40
    bars = ch.series[0]
    for i, color in enumerate(("2B7A4B", "3B7DD8", "C0392B")):
        style_fill(bars.points[i], color)
        label_point(bars, i, f"{d.flaeche_Gha[i]:.2f}".replace(".", ","),
                    pos=XL_LABEL_POSITION.OUTSIDE_END, size=9)
    split_series(ch, {1}, "line")
    style_line(ch.series[1], "000000", width=1.25, dash=DASH)
    hide_legend_entries(ch, [0])
    style_axis(ch.category_axis, grid=False)
    style_axis(ch.value_axis, title="Fläche [Gha]", minimum=0, maximum=14, major=2)
    remove_picture(slide, el)


BUILDERS = {
    11: slide_11,
    12: slide_12,
    15: lambda s: albedo_season(s, 15, "Picture 64"),
    16: lambda s: albedo_season(s, 16, "Picture 9015"),
    29: slide_29,
    31: slide_31,
    32: slide_32,
    33: slide_33,
    34: slide_34,
    35: slide_35,
    38: slide_38,
    40: slide_40,
    42: slide_42,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck", type=Path, default=T.DECK_PATH)
    parser.add_argument("--out", type=Path, default=None, help="Ziel (Standard: --deck überschreiben)")
    args = parser.parse_args()
    out = args.out or args.deck

    if out == T.DECK_PATH:
        T.check_not_locked(deck_path=out)
        print(f"Sicherung: {T.backup('native_charts', deck_path=args.deck)}")

    prs = T.open_deck(deck_path=args.deck)
    slides = list(prs.slides)
    for no, build in BUILDERS.items():
        print(f"Folie {no}")
        build(slides[no - 1])
    T.save_deck(prs, deck_path=out)
    print(f"{T.verify_deck(out)} Folien in {out}")


if __name__ == "__main__":
    main()
