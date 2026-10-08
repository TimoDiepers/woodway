"""Chart data and backup pages for the HTML version of dissvortrag_v2.

Every chart of the main part is drawn by the same matplotlib code that made
the pictures in dissvortrag_v2.pptx. Instead of keeping the PNG, this script
catches each figure at ``savefig``, lays it out once, and writes every
artist in pixel coordinates to ``docs/slides/html/v2/charts.js``: lines,
bars, areas, markers and texts, each tagged with what it is (frame, series,
bar, annotation, legend). The deck draws them as SVG and animates them per
role -- lines are revealed along the time axis, bars grow from their base,
annotations fade in last. Map pixels cannot be animated piece by piece; the
axes that hold an image or mesh go into one transparent PNG per chart,
which the deck wipes in.

The backup part (after the closing slide) is not rebuilt: its pages are
rendered from the pptx and inserted with their speaker notes.

    uv run python scripts/export_html_v2.py            # charts + backup
    uv run python scripts/export_html_v2.py --charts   # charts only
    uv run python scripts/export_html_v2.py --only b6,k10
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.axis import Axis  # noqa: E402
from matplotlib.collections import Collection, LineCollection, QuadMesh  # noqa: E402
from matplotlib.colors import to_hex, to_rgba  # noqa: E402
from matplotlib.container import BarContainer  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.image import AxesImage  # noqa: E402
from matplotlib.legend import Legend  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Patch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
from matplotlib.spines import Spine  # noqa: E402
from matplotlib.text import Annotation, Text  # noqa: E402
from matplotlib.transforms import Affine2D  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SLIDES = REPO / "docs" / "slides"
OUT = SLIDES / "html" / "v2"
DECK = SLIDES / "dissvortrag_v2.pptx"
HTML = SLIDES / "html" / "dissvortrag_v2.html"
MAIN_SLIDES = 44  # slide 44 is the closing slide; the backup starts after it

# --------------------------------------------------------------------------
# mathtext -> runs of (text, shift, italic)
# --------------------------------------------------------------------------

_SYMBOLS = {
    "Delta": "Δ", "alpha": "α", "varphi": "φ", "phi": "φ", "tau": "τ", "gamma": "γ", "mu": "μ",
    "sigma": "σ", "lambda": "λ", "Lambda": "Λ", "beta": "β", "epsilon": "ε", "pi": "π", "rho": "ρ",
    "cdot": "·", "times": "×", "approx": "≈", "langle": "⟨", "rangle": "⟩", "infty": "∞", "pm": "±",
    "rightarrow": "→", "to": "→", "leq": "≤", "geq": "≥", "le": "≤", "ge": "≥", "circ": "°",
    "sum": "Σ", "int": "∫", "oplus": "⊕", "minus": "−", "%": "%", ",": " ", ";": " ", ":": " ",
    "!": "", " ": " ", "quad": "  ", "degree": "°", "Sigma": "Σ", "partial": "∂", "nabla": "∇",
}


def _group(s: str, i: int) -> tuple[str, int]:
    """Argument at s[i]: a {...} group or one character. Returns (text, next index)."""
    if i < len(s) and s[i] == "{":
        depth, j = 0, i
        while j < len(s):
            depth += {"{": 1, "}": -1}.get(s[j], 0)
            if depth == 0:
                return s[i + 1 : j], j + 1
            j += 1
        return s[i + 1 :], len(s)
    if i < len(s) and s[i] == "\\":
        m = re.match(r"\\([A-Za-z]+|.)", s[i:])
        return m.group(0), i + len(m.group(0))
    return (s[i], i + 1) if i < len(s) else ("", i)


def _math_runs(s: str, shift: int = 0, italic: bool = True) -> list[list]:
    runs: list[list] = []

    def add(t: str, sh: int = shift, it: bool = italic) -> None:
        if not t:
            return
        if runs and runs[-1][1] == sh and runs[-1][2] == it:
            runs[-1][0] += t
        else:
            runs.append([t, sh, it])

    i = 0
    while i < len(s):
        c = s[i]
        if c in "^_":
            arg, i = _group(s, i + 1)
            for t, _sh, it in _math_runs(arg, 1 if c == "^" else -1, italic):
                add(t, 1 if c == "^" else -1, it)
        elif c == "\\":
            m = re.match(r"\\([A-Za-z]+|.)", s[i:])
            name = m.group(1)
            i += len(m.group(0))
            if name in ("mathrm", "text", "mathregular", "rm", "mathsf", "textrm"):
                arg, i = _group(s, i)
                for t, sh, _it in _math_runs(arg, shift, False):
                    add(t, sh, False)
            elif name in ("mathbf", "mathit", "boldsymbol", "mathbfit"):
                arg, i = _group(s, i)
                for t, sh, it in _math_runs(arg, shift, name != "mathbf"):
                    add(t, sh, it)
            elif name == "dot":
                arg, i = _group(s, i)
                for t, sh, it in _math_runs(arg, shift, italic):
                    add(t + "̇", sh, it)
            elif name == "frac":
                a, i = _group(s, i)
                b, i = _group(s, i)
                for t, sh, it in _math_runs(a, shift, italic) + [["/", shift, False]] + _math_runs(b, shift, italic):
                    add(t, sh, it)
            elif name in ("left", "right", "big", "Big", "bigl", "bigr"):
                continue
            elif name in _SYMBOLS:
                add(_SYMBOLS[name], shift, False)
            else:
                add(name, shift, False)
        elif c in "{}":
            i += 1
        elif c == "-":
            add("−", shift, False)
            i += 1
        elif c.isalpha():
            add(c, shift, italic)
            i += 1
        else:
            add(c, shift, False)
            i += 1
    return runs


def text_runs(s: str) -> list[list]:
    """Plain text with $...$ math into runs; a run is [text, shift, italic]."""
    parts = re.split(r"(?<!\\)\$", s)
    runs: list[list] = []
    for k, part in enumerate(parts):
        if k % 2:
            runs += _math_runs(part)
        elif part:
            runs.append([part.replace("\\$", "$"), 0, False])
    return runs


# --------------------------------------------------------------------------
# figure -> scene
# --------------------------------------------------------------------------


def _hex(c) -> str | None:
    r = to_rgba(c)
    return None if r[3] == 0 else to_hex(r, keep_alpha=False)


def _alpha(c) -> float:
    return round(float(to_rgba(c)[3]), 3)


def _path_d(path: MPath, H: float) -> str:
    """SVG path data from a path already in display coordinates."""
    out, pen = [], False
    for verts, code in path.iter_segments(simplify=False, curves=True):
        pts = np.asarray(verts, dtype=float).reshape(-1, 2)
        if code != MPath.CLOSEPOLY and not np.all(np.isfinite(pts)):
            pen = False
            continue
        xy = " ".join(f"{x:.1f} {H - y:.1f}" for x, y in pts)
        if code == MPath.MOVETO or (not pen and code != MPath.CLOSEPOLY):
            out.append("M" + xy)
            pen = True
        elif code == MPath.LINETO:
            out.append("L" + xy)
        elif code == MPath.CURVE3:
            out.append("Q" + xy)
        elif code == MPath.CURVE4:
            out.append("C" + xy)
        elif code == MPath.CLOSEPOLY:
            out.append("Z")
    return "".join(out)


def _dash(pattern, scale: float):
    if not pattern or pattern[1] is None:
        return None
    seq = [round(v * scale, 1) for v in pattern[1]]
    return seq if any(seq) else None


class Scene:
    def __init__(self, fig: Figure):
        self.fig = fig
        fig.canvas.draw()
        self.r = fig.canvas.get_renderer()
        self.px = fig.dpi / 72.0
        self.W, self.H = fig.canvas.get_width_height()
        self.items: list[dict] = []
        self.clips: list[list[float]] = []
        self.axes: list[dict] = []
        self.raster_axes: list[Axes] = []
        self.seen: set[int] = set()
        self.bar_of: dict[int, dict] = {}

    # ---- helpers
    def clip_of(self, a) -> int | None:
        if not a.get_clip_on():
            return None
        box = a.get_clip_box()
        if box is None:
            return None
        b = [round(box.x0, 1), round(self.H - box.y1, 1), round(box.width, 1), round(box.height, 1)]
        if b not in self.clips:
            self.clips.append(b)
        return self.clips.index(b)

    def emit(self, item: dict, ctx: dict, a=None) -> None:
        item["ax"] = ctx.get("ax")
        item["role"] = item.get("role") or ctx.get("role", "series")
        # left edge in px: steps that reveal a chart part by part show an item once the edge has passed it
        if item["t"] == "path":
            nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", item["d"])]
            if nums:
                item["xl"] = round(min(nums[0::2]), 1)
        else:
            item["xl"] = item["x"]
        if a is not None:
            c = self.clip_of(a)
            if c is not None:
                item["clip"] = c
            z = a.get_zorder()
            item["z"] = z
            al = a.get_alpha()
            if al is not None and al < 1:
                item["op"] = round(float(al), 3)
        self.items.append(item)

    def style(self, face, edge, lw, dash=None, hatch=None, hatch_color=None) -> dict:
        s: dict = {}
        if face is not None and _hex(face):
            s["fill"] = _hex(face)
            if _alpha(face) < 1:
                s["fo"] = _alpha(face)
        if edge is not None and _hex(edge) and lw and lw > 0:
            s["stroke"] = _hex(edge)
            s["sw"] = round(lw * self.px, 2)
            if _alpha(edge) < 1:
                s["so"] = _alpha(edge)
            if dash:
                s["dash"] = dash
        if hatch:
            s["hatch"] = hatch
            s["hc"] = _hex(hatch_color) if hatch_color is not None else "#000000"
        return s

    # ---- leaves
    def line(self, ln: Line2D, ctx: dict) -> None:
        tpath = ln.get_transform().transform_path(ln.get_path())
        if ln.get_linestyle() not in ("None", "", " ", "none") and ln.get_linewidth() > 0:
            st = self.style(None, ln.get_color(), ln.get_linewidth(), _dash(ln._dash_pattern, self.px))
            st["cap"] = ln.get_solid_capstyle() if not st.get("dash") else ln.get_dash_capstyle()
            d = _path_d(tpath, self.H)
            if d:
                self.emit({"t": "path", "d": d, **st, "kind": "line"}, ctx, ln)
        mk = ln.get_marker()
        if mk not in (None, "None", "", " ", "none") and ln.get_markersize() > 0:
            m = ln._marker
            mpath = m.get_path()
            mtr = m.get_transform() + Affine2D().scale(ln.get_markersize() * self.px)
            verts = tpath.vertices
            face = ln.get_markerfacecolor() if m.is_filled() else "none"
            st = self.style(face, ln.get_markeredgecolor(), ln.get_markeredgewidth())
            every = ln.get_markevery()
            idx = range(len(verts))
            if isinstance(every, (int, np.integer)) and not isinstance(every, bool):
                idx = range(0, len(verts), int(every))
            elif isinstance(every, slice):
                idx = range(len(verts))[every]
            elif isinstance(every, (list, tuple, np.ndarray)) and len(every) and not isinstance(every[0], (bool, np.bool_)):
                idx = [int(k) for k in every if 0 <= int(k) < len(verts)]
            elif isinstance(every, (list, tuple, np.ndarray)) and len(every):
                idx = [k for k, on in enumerate(every) if on]
            for k in idx:
                x, y = verts[k]
                if not (np.isfinite(x) and np.isfinite(y)):
                    continue
                p = (mtr + Affine2D().translate(x, y)).transform_path(mpath)
                self.emit({"t": "path", "d": _path_d(p, self.H), **st, "kind": "marker", "cx": round(x, 1),
                           "cy": round(self.H - y, 1)}, ctx, ln)

    def patch(self, p: Patch, ctx: dict) -> None:
        if isinstance(p, FancyArrowPatch):
            paths, fillables = p._get_path_in_displaycoord()
        else:
            paths, fillables = [p.get_transform().transform_path(p.get_path())], [True]
        dash = None
        if p._dash_pattern and p._dash_pattern[1]:
            dash = [round(v * self.px, 1) for v in p._dash_pattern[1]]
        for path, fillable in zip(paths, fillables):
            face = p.get_facecolor() if (p.get_fill() and fillable) else None
            st = self.style(face, p.get_edgecolor(), p.get_linewidth(), dash, p.get_hatch(),
                            getattr(p, "_hatch_color", None))
            if not st:
                continue
            item = {"t": "path", "d": _path_d(path, self.H), **st, "kind": "patch"}
            bar = self.bar_of.get(id(p))
            if bar:
                item.update(bar)
                item["kind"] = "bar"
                item["role"] = "bar"
            self.emit(item, ctx, p)

    def collection(self, c: Collection, ctx: dict) -> None:
        paths = c.get_paths()
        if not len(paths):
            return
        master = c.get_transform()
        tfs = c.get_transforms()
        offs = c.get_offsets()
        otr = c.get_offset_transform()
        use_offs = offs is not None and len(offs) and not np.allclose(offs, 0)
        offs_d = otr.transform(offs) if use_offs else None
        n = max(len(paths), len(offs_d) if use_offs else 0)
        fcs, ecs = c.get_facecolor(), c.get_edgecolor()
        lws = c.get_linewidth()
        if isinstance(c, LineCollection):
            fcs = []
        dash = None
        ls = c.get_linestyle()
        if ls and ls[0][1]:
            dash = [round(v * self.px, 1) for v in ls[0][1]]
        hatch = c.get_hatch()
        for i in range(n):
            path = paths[i % len(paths)]
            tr = master
            if len(tfs):
                tr = Affine2D(tfs[i % len(tfs)]) + master
            dp = tr.transform_path(path)
            cx = cy = None
            if use_offs:
                ox, oy = offs_d[i % len(offs_d)]
                if not (np.isfinite(ox) and np.isfinite(oy)):
                    continue
                dp = Affine2D().translate(ox, oy).transform_path(dp)
                cx, cy = round(ox, 1), round(self.H - oy, 1)
            face = fcs[i % len(fcs)] if len(fcs) else None
            edge = ecs[i % len(ecs)] if len(ecs) else None
            lw = lws[i % len(lws)] if len(lws) else 0
            st = self.style(face, edge, lw, dash, hatch, getattr(c, "_hatch_color", None))
            if not st:
                continue
            item = {"t": "path", "d": _path_d(dp, self.H), **st, "kind": "marker" if use_offs else "area"}
            if cx is not None:
                item["cx"], item["cy"] = cx, cy
            self.emit(item, ctx, c)

    def text(self, t: Text, ctx: dict) -> None:
        s = t.get_text()
        if not s or not s.strip():
            return
        bp = t.get_bbox_patch()
        if bp is not None:
            self.patch(bp, ctx)
        bb = t.get_window_extent(self.r)
        rot = round(t.get_rotation(), 1) % 360
        lines = s.split("\n")
        size = round(t.get_fontsize() * self.px, 2)
        ha = t.get_horizontalalignment()
        family = "serif" if "Literata" in t.get_fontname() or "Serif" in t.get_fontname() else "sans"
        weight = t.get_weight()
        bold = weight in ("bold", "semibold", "demibold", "heavy", "black") or (isinstance(weight, (int, float)) and weight >= 600)
        item = {"t": "text", "lines": [text_runs(x) for x in lines], "size": size, "color": _hex(t.get_color()) or "#000",
                "rot": rot, "family": family}
        if bold:
            item["bold"] = 1
        if t.get_style() == "italic":
            item["italic"] = 1
        if rot in (0, 0.0):
            item["anchor"] = {"left": "start", "center": "middle", "right": "end"}[ha]
            item["x"] = round({"start": bb.x0, "middle": (bb.x0 + bb.x1) / 2, "end": bb.x1}[item["anchor"]], 1)
            n = len(lines)
            step = bb.height / n
            item["ys"] = [round(self.H - (bb.y1 - step * (k + 0.5)), 1) for k in range(n)]
        else:
            item["anchor"] = "middle"
            item["x"] = round((bb.x0 + bb.x1) / 2, 1)
            item["ys"] = [round(self.H - (bb.y0 + bb.y1) / 2, 1)]
            if len(lines) > 1:
                # rotated multi-line labels are rare; keep them on one line
                item["lines"] = [sum(item["lines"], [])]
        self.emit(item, ctx, t)
        if isinstance(t, Annotation) and t.arrow_patch is not None and id(t.arrow_patch) not in self.seen:
            self.seen.add(id(t.arrow_patch))
            self.patch(t.arrow_patch, ctx)

    # ---- walk
    def walk(self, a, ctx: dict) -> None:
        if id(a) in self.seen or not a.get_visible():
            return
        self.seen.add(id(a))
        if isinstance(a, Axes):
            if any(isinstance(ch, (AxesImage, QuadMesh)) for ch in a.get_children()) or any(
                isinstance(ch, Collection) and len(ch.get_paths()) > 400 for ch in a.get_children()
            ):
                bb = a.bbox
                self.axes.append({"x": round(bb.x0, 1), "y": round(self.H - bb.y1, 1), "w": round(bb.width, 1),
                                  "h": round(bb.height, 1), "raster": 1})
                self.raster_axes.append((len(self.axes) - 1, a))
                return
            k = len(self.axes)
            bb = a.bbox
            self.axes.append({"x": round(bb.x0, 1), "y": round(self.H - bb.y1, 1), "w": round(bb.width, 1),
                              "h": round(bb.height, 1)})
            for cont in a.containers:
                if isinstance(cont, BarContainer):
                    ci = a.containers.index(cont)
                    for rect in cont.patches:
                        if cont.orientation == "vertical":
                            oy = a.transData.transform((rect.get_x(), rect.get_y()))[1]
                            self.bar_of[id(rect)] = {"o": "v", "oy": round(self.H - oy, 1), "bx": rect.get_x(), "ci": ci}
                        else:
                            ox = a.transData.transform((rect.get_x(), rect.get_y()))[0]
                            self.bar_of[id(rect)] = {"o": "h", "ox": round(ox, 1), "bx": -rect.get_y(), "ci": ci}
            ctx = {"ax": k, "role": "series"}
            titles = {id(a.title), id(a._left_title), id(a._right_title)}
            if a.patch.get_visible() and _hex(a.patch.get_facecolor()) and _hex(a.patch.get_facecolor()) != _hex(
                self.fig.patch.get_facecolor()
            ):
                self.patch(a.patch, {**ctx, "role": "frame"})
            self.seen.add(id(a.patch))
            children = sorted(a.get_children(), key=lambda ch: ch.get_zorder())
            for ch in children:
                if id(ch) in titles:
                    self.walk(ch, {**ctx, "role": "frame"})
                else:
                    self.walk(ch, ctx)
            return
        if isinstance(a, Axis):
            # only the ticks matplotlib actually draws (inside the view interval)
            ctx = {**ctx, "role": "frame"}
            for tick in a._update_ticks():
                self.walk(tick, ctx)
            for ch in (a.label, a.offsetText):
                self.walk(ch, ctx)
            return
        if isinstance(a, Spine):
            ctx = {**ctx, "role": "frame"}
        if isinstance(a, Legend):
            ctx = {**ctx, "role": "legend"}
        if isinstance(a, Line2D):
            self.line(a, ctx)
        elif isinstance(a, Text):
            self.text(a, ctx if ctx.get("role") != "series" else {**ctx, "role": "anno"})
        elif isinstance(a, Patch):
            self.patch(a, ctx if ctx.get("role") != "series" or id(a) in self.bar_of or not isinstance(a, FancyArrowPatch)
                       else {**ctx, "role": "anno"})
        elif isinstance(a, Collection):
            self.collection(a, ctx)
        for ch in a.get_children():
            self.walk(ch, ctx)

    def build(self, key: str) -> dict:
        self.seen.add(id(self.fig.patch))
        for ch in sorted(self.fig.get_children(), key=lambda c: c.get_zorder()):
            self.walk(ch, {"ax": None, "role": "frame"})
        rasters = [self.render_raster(key, k, a) for k, a in self.raster_axes]
        return {"w": self.W, "h": self.H, "dpi": round(self.fig.dpi), "axes": self.axes, "clips": self.clips,
                "items": self.items, "rasters": [r for r in rasters if r]}

    def render_raster(self, key: str, k: int, axes: Axes) -> dict | None:
        """One transparent PNG per map/colour-bar axes, so each can come in on its own step."""
        from PIL import Image

        keep = {id(axes)}
        hidden = []
        for ch in self.fig.get_children():
            if id(ch) not in keep and ch.get_visible() and ch is not self.fig.patch:
                ch.set_visible(False)
                hidden.append(ch)
        fc = self.fig.patch.get_facecolor()
        self.fig.patch.set_alpha(0)
        tmp = Path(tempfile.mkstemp(suffix=".png")[1])
        _orig_savefig(self.fig, tmp, dpi=self.fig.dpi, transparent=True)
        for ch in hidden:
            ch.set_visible(True)
        self.fig.patch.set_facecolor(fc)
        im = Image.open(tmp).convert("RGBA")
        box = im.getbbox()
        if box is None:
            tmp.unlink()
            return None
        im = im.crop(box)
        name = f"r_{key}_{k}.png"
        im.save(OUT / name, optimize=True)
        tmp.unlink()
        x0, y0, x1, y1 = box
        return {"src": f"v2/{name}", "x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0, "ax": k}


# --------------------------------------------------------------------------
# capture
# --------------------------------------------------------------------------

SCENES: dict[str, dict] = {}
EC_SCENES: dict[str, dict] = {}   # the same figures in data coordinates, for ECharts (mpl_to_echarts)
_CURRENT: list[str] = []
_orig_savefig = Figure.savefig


def _capture(self: Figure, fname, *args, **kwargs):
    dpi = kwargs.get("dpi")
    if dpi and dpi != "figure":
        self.set_dpi(dpi)
    key = _CURRENT[-1]
    SCENES[key] = Scene(self).build(key)
    from mpl_to_echarts import data_scene

    EC_SCENES[key] = data_scene(self)
    kwargs.pop("dpi", None)
    ref = OUT / "ref"
    ref.mkdir(exist_ok=True)
    _orig_savefig(self, ref / f"{key}.png", *args, dpi=self.dpi, **kwargs)


def run(key: str, fn, *args) -> None:
    _CURRENT.append(key)
    try:
        with tempfile.TemporaryDirectory() as d:
            fn(str(Path(d) / f"{key}.png"), *args)
    finally:
        _CURRENT.pop()
        plt.close("all")
    print(f"  {key}: {len(SCENES.get(key, {}).get('items', []))} items", flush=True)


# --------------------------------------------------------------------------
# the two native PowerPoint charts (slides 11 and 12), in the same style
# --------------------------------------------------------------------------


def _series(title: str) -> list[tuple[str, list[float] | None, list[float]]]:
    """Series of the native charts on the slide with this title (slide numbers move)."""
    from pptx import Presentation

    hits = [s for s in Presentation(str(DECK)).slides if s.shapes.title is not None and s.shapes.title.text == title]
    if len(hits) != 1:
        raise LookupError(f"{len(hits)} Folien mit Titel {title!r}")
    s = hits[0]
    out = []
    for sh in s.shapes:
        if not sh.has_chart:
            continue
        for plot in sh.chart.plots:
            for ser in plot.series:
                xv = ser._element.xpath("./c:xVal//c:v/text()")
                out.append((ser.name, [float(v) for v in xv] if xv else None, [float(v) for v in ser.values]))
    return out


def timescales_figure(out_path: str) -> str:
    """Slide 10: net carbon flux of one tree on three time scales (illustrative), from the tree's point of
    view as in the formula above (positive = uptake). Each panel marks which terms act, in the colours of
    the formula: day = photosynthesis against respiration, year = respiration and decomposition in winter,
    decades = saturation and a disturbance event (stock with the Aachen model tree of the next slide)."""
    from nbs.animations import C_INK_MUTED, FIG_DPI, _clean_axes
    from nbs.storyline_figures import _setup

    _setup()
    c_ps, c_re, c_zs, c_st, c_ink = "#2f7a45", "#7e4a74", "#3d6698", "#c0392b", "#1a2320"
    fig = plt.figure(figsize=(12.0, 5.6), dpi=FIG_DPI)
    # three panels of equal size; the fourth place (bottom right) stays free for the takeaway on the slide
    gs = fig.add_gridspec(2, 2, left=0.07, right=0.97, bottom=0.1, top=0.92, hspace=0.62, wspace=0.22)
    a1, a2, a3 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 0])
    for ax in (a1, a2, a3):
        _clean_axes(ax)

    # all panels in kg C per tree and on one scale: a summer day sums to about 26 g C (July in the year panel),
    # the year to about 1 kg C net, the growth of the stand curve below (Aachen model tree, at most ~1 kg C/a)

    # day: photosynthesis only with light, respiration around the clock [g C per tree and hour]
    t = np.linspace(0, 24, 241)
    ps = np.where((t > 6) & (t < 20), 3.8 * np.sin(np.pi * (t - 6) / 14), 0.0)
    net = ps - 0.35
    a1.axhline(0, color=C_INK_MUTED, lw=0.8)
    a1.fill_between(t, 0, net, where=net > 0, color=c_ps, alpha=0.22, lw=0)
    a1.fill_between(t, 0, net, where=net < 0, color=c_re, alpha=0.25, lw=0)
    a1.plot(t, net, color=c_ink, lw=2.2)
    a1.text(13, 4.35, "Tag: Photosynthese (PS) > Respiration (RE)", ha="center", fontsize=12, color=c_ps, fontweight="bold")
    a1.text(0.4, -0.75, "Nacht: nur Respiration (RE) → Abgabe", ha="left", va="top", fontsize=12, color=c_re, fontweight="bold")
    a1.set_xlim(0, 24)
    a1.set_ylim(-2.0, 4.9)
    a1.set_xticks(range(0, 25, 4))
    a1.set_xlabel("Uhrzeit [h]")
    a1.set_ylabel("10$^{-3}$ kg C je Baum und h")
    a1.set_title("Über den Tag", loc="left", fontsize=19, fontweight="bold", color=c_ink)

    # year (deciduous forest): gross fluxes per month -- photosynthesis up, respiration down in every month
    # (strongest in the warm summer), decomposition of litter and dead wood (ZS) hatched below; the line is the
    # tree's net balance PS - RE: clearly positive in summer, only slightly negative in winter (no leaves,
    # respiration throttled by the cold). Illustrative, the model has no seasonal cycle.
    months = np.arange(1, 13)
    ps = 0.1 * np.array([0.0, 0.0, 0.3, 2.4, 7.0, 10.2, 11.4, 10.6, 7.6, 3.4, 0.2, 0.0])
    re_ = 0.1 * np.array([0.8, 0.8, 0.9, 1.4, 2.5, 3.4, 3.6, 3.4, 2.6, 1.6, 0.9, 0.8])
    zs = 0.17 * np.array([0.6, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.1, 1.1, 1.4, 1.3, 0.8])
    a2.axhline(0, color=C_INK_MUTED, lw=0.8)
    a2.bar(months, ps, color=c_ps, alpha=0.75, width=0.7)
    a2.bar(months, -re_, color=c_re, alpha=0.75, width=0.7)
    a2.bar(months, -zs, bottom=-re_, color="none", edgecolor=c_zs, hatch="///", lw=1.2, width=0.7)
    a2.plot(months, ps - re_, color=c_ink, lw=2.0, marker="o", ms=5, zorder=5)
    a2.text(0.6, 1.14, "Photosynthese (PS)", ha="left", fontsize=11.5, color=c_ps, fontweight="bold")
    a2.text(0.6, 0.92, "— Netto PS − RE", ha="left", fontsize=11.5, color=c_ink, fontweight="bold")
    a2.text(0.6, -0.56, "Respiration (RE)", ha="left", fontsize=11.5, color=c_re, fontweight="bold")
    a2.text(0.6, -0.79, "schraffiert: Zersetzung (ZS)", ha="left", fontsize=11.5, color=c_zs, fontweight="bold")
    a2.set_xticks(months)
    a2.set_xlim(0.4, 12.6)
    a2.set_ylim(-0.9, 1.3)
    a2.set_yticks([-0.5, 0, 0.5, 1.0])
    a2.set_xlabel("Monat")
    a2.set_ylabel("kg C je Baum und Monat")
    a2.set_title("Über das Jahr", loc="left", fontsize=19, fontweight="bold", color=c_ink)

    # decades: Chapman-Richards stock of the Aachen model tree (m_max 49 kg C, k 0.043/a, p 2), a
    # disturbance at age 55 removes 60 % of the stock, then the stand regrows along the same curve
    m_max, k, p = 49.0, 0.043, 2.0
    S = lambda a: m_max * (1 - np.exp(-k * np.clip(a, 0, None))) ** p  # noqa: E731
    age = np.linspace(0, 100, 501)
    stock = S(age)
    ev, keep = 55.0, 0.4
    rest = keep * S(ev)
    a_eq = -np.log(1 - (rest / m_max) ** (1 / p)) / k  # age on the curve with the residual stock
    dist = np.where(age < ev, stock, S(a_eq + (age - ev)))
    a3.plot(age, stock, color=c_ps, lw=2.6)
    a3.plot(age[age >= ev], dist[age >= ev], color=c_st, lw=2.6)
    a3.plot([ev, ev], [S(ev), rest], color=c_st, lw=2.6, ls=(0, (3, 2)))
    a3.text(ev - 2, 12, "Störung (ST)", ha="right", va="center", fontsize=12.5, color=c_st, fontweight="bold")
    a3.text(99, 4, "Sättigung: Zuwachs ≈ Zersetzung (ZS)", ha="right", va="center", fontsize=12.5,
            color=c_zs, fontweight="bold")
    a3.text(2, 44, "Aufbau: PS − RE", ha="left", va="center", fontsize=12, color=c_ps,
            fontweight="bold")
    a3.set_xlim(0, 100)
    a3.set_ylim(0, m_max * 1.08)
    a3.set_xlabel("Bestandesalter [a]")
    a3.set_ylabel("kg C je Baum (Vorrat)")
    a3.set_title("Über Jahrzehnte", loc="left", fontsize=19, fontweight="bold", color=c_ink)
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path


def growth_model_figure(out_path: str) -> str:
    """Slide 12: carbon stock of one tree, Aachen mixed forest, three variants."""
    from nbs.constants import T_START

    from nbs.animations import FIG_DPI, _clean_axes
    from nbs.storyline_figures import _setup

    _setup()
    fig, ax = plt.subplots(figsize=(7.8, 3.9), dpi=FIG_DPI)
    fig.subplots_adjust(left=0.1, right=0.67, bottom=0.15, top=0.93)
    _clean_axes(ax)
    styles = {
        "nur Wachstum": ("#2f7a45", "-", 2.6, "nur Wachstum"),
        "mit Störung, ΔT_w = 0": ("#d6604d", "-", 2.2, "mit Störung, $\\Delta T_w$ = 0"),
        "mit Störung, ΔT_w = 1 K (linear)": ("#a50f15", (0, (6, 4)), 2.2, "mit Störung, $\\Delta T_w$ = 1 K"),
    }
    # the curves of the former native chart (docs/slides/chart_data/s12_vorrat.json), shown to the horizon
    series = json.loads((REPO / "docs" / "slides" / "chart_data" / "s12_vorrat.json").read_text(encoding="utf-8"))
    for ser in series:
        name = ser["name"]
        # the series start at planting in 2025; shifted so that planting is the start year
        xs = [v + (T_START - 2025) for v in ser["x"]]
        x, y = [v for v in xs if v <= 2100], ser["y"][:len([v for v in xs if v <= 2100])]
        c, ls, lw, lab = styles[name]
        ax.plot(x, y, color=c, ls=ls, lw=lw)
        ax.annotate(lab, (x[-1], y[-1]), xytext=(8, {"nur Wachstum": 10, "mit Störung, ΔT_w = 0": -5}.get(name, -21)),
                    textcoords="offset points", fontsize=13.5, color=c, va="center", annotation_clip=False)
    ax.set_xlim(T_START, 2100)
    ax.set_ylim(0, 52)
    ax.set_xticks([T_START, 2050, 2075, 2100])
    ax.set_ylabel("Vorrat $m_{Baum}$ [kg C]")
    fig.savefig(out_path, dpi=FIG_DPI)
    plt.close(fig)
    return out_path


# --------------------------------------------------------------------------
# chart list: key -> function (the same functions that built the pptx pictures)
# --------------------------------------------------------------------------


def chart_jobs() -> list[tuple[str, object]]:
    from nbs import animations as an
    from nbs import dac_figures as df
    from nbs import storyline_figures as sf
    from nbs import vergleich_figures as vf

    return [
        ("s11", timescales_figure),
        ("s12", growth_model_figure),
        ("b5", sf.forest_type_map_figure),
        ("b6", sf.uptake_bars_figure),
        ("b6s", sf.uptake_panel_figure),
        ("b8a", an.albedo_ingredients_figure),
        ("b8", an.albedo_annual_map_figure),
        ("b9", sf.exchange_bars_figure),
        ("b10", sf.common_currency_bars_figure),
        ("k3", sf.irf_figure),
        ("k3s", sf.irf_side_figure),
        ("k5", sf.missing_air_bars_figure),
        ("k6", sf.co2_forcing_figure),
        ("k6e", sf.co2_efficiency_figure),
        ("k10", sf.forcing_two_sites_figure),
        ("k12b", sf.inertia_result_figure),
        ("k12s", sf.step_response_figure),
        ("k12t", sf.tree_temperature_figure),
        ("k13", sf.planting_year_figure),
        ("k14", sf.ladder_figure),
        ("k15", vf.tree_effect_figure),
        ("v0", vf.reforestable_share_figure),
        ("v1", vf.availability_map_figure),
        ("v1b", sf.literature_comparison_figure),
        ("w1", vf.planting_rank_figure),
        ("w2", vf.area_time_figure),
        ("w2b", vf.area_need_figure),
        ("w3", vf.planting_delay_figure),
        ("w4", vf.removal_gap_figure),
        ("v2s", vf.need_scenarios_figure),
        ("v2", vf.need_figure),
        ("d1", df.energy_map_figure),
        ("d0", vf.feasibility_figure),
        ("v3", vf.today_figure),
        ("v4", vf.over_time_figure),
        ("d4", df.switch_year_figure),
        ("d5", df.dac_net_figure),
        ("d6", df.dac_scenarios_figure),
        ("z1", sf.time_share_figure),
    ]


def export_charts(only: set[str] | None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    js = OUT / "charts.js"
    if only and js.exists():
        old = js.read_text(encoding="utf-8")
        SCENES.update(json.loads(old[old.index("=") + 1 :].rstrip().rstrip(";")))
    Figure.savefig = _capture
    try:
        for key, fn in chart_jobs():
            if only and key not in only:
                continue
            run(key, fn)
    finally:
        Figure.savefig = _orig_savefig
    js.write_text("window.CHARTS = " + json.dumps(SCENES, ensure_ascii=False, separators=(",", ":")) + ";\n",
                  encoding="utf-8")
    print(f"wrote {js} ({js.stat().st_size / 1e6:.1f} MB)")
    ec = OUT / "ec_charts.js"
    if only and ec.exists():
        old = ec.read_text(encoding="utf-8")
        EC_SCENES.update({k: v for k, v in json.loads(old[old.index("=") + 1 :].rstrip().rstrip(";")).items() if k not in EC_SCENES})
    ec.write_text("window.ECDATA = " + json.dumps(EC_SCENES, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + ";\n",
                  encoding="utf-8")
    print(f"wrote {ec} ({ec.stat().st_size / 1e6:.1f} MB)")


# --------------------------------------------------------------------------
# backup: rendered pages + notes
# --------------------------------------------------------------------------


def _notes_html(text: str) -> str:
    """pptx notes -> paragraphs; asides ("Falls Fragen kommen", "[v2]") set in the quiet style."""
    text = re.sub(r"^Sprechertext:?\s*", "", text.strip())
    out = []
    for p in (p.strip() for p in re.split(r"\n\s*\n", text)):
        if not p:
            continue
        p = re.sub(r"^Sprechertext:?\s*", "", p)
        if p.startswith("[v2] Formel (LaTeX)"):
            continue  # build note of the pptx script; the formula is on the slide
        quiet = p.startswith(("Falls Fragen kommen", "[v2]", "Achtung"))
        if p.startswith("Falls Fragen kommen\n"):
            p = "Falls Fragen kommen — " + p.split("\n", 1)[1]
        cls = ' class="q"' if quiet else ""
        out.append(f"<p{cls}>" + html.escape(p).replace("\n", "<br>") + "</p>")
    return "\n    ".join(out)


def fill_notes(page: str, pres) -> str:
    """Speaker notes of the main part, straight from the pptx (aside data-n = pptx slide number)."""

    def sub(m: re.Match) -> str:
        s = pres.slides[int(m.group(1)) - 1]
        notes = s.notes_slide.notes_text_frame.text if s.has_notes_slide else ""
        return f'<aside class="notes" data-n="{m.group(1)}">\n    {_notes_html(notes)}\n  </aside>'

    return re.sub(r'<aside class="notes" data-n="(\d+)">.*?</aside>', sub, page, flags=re.S)


def export_backup() -> None:
    from pptx import Presentation

    pres = Presentation(str(DECK))
    shown = [(k + 1, s) for k, s in enumerate(pres.slides) if s._element.get("show") != "0"]
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "deck.pptx"
        src.write_bytes(DECK.read_bytes())
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", d, str(src)], check=True,
                       capture_output=True)
        pdf = Path(d) / "deck.pdf"
        bdir = OUT / "backup"
        bdir.mkdir(parents=True, exist_ok=True)
        for f in bdir.glob("*.jpg"):
            f.unlink()
        first = next(i for i, (n, _s) in enumerate(shown) if n > MAIN_SLIDES)
        subprocess.run(["pdftoppm", "-r", "120", "-jpeg", "-jpegopt", "quality=82", "-f", str(first + 1), "-l",
                        str(len(shown)), str(pdf), str(bdir / "p")], check=True)
        pages = sorted(bdir.glob("p-*.jpg"))
    sections = []
    for (n, s), img in zip(shown[first:], pages):
        new = bdir / f"folie{n:03d}.jpg"
        img.rename(new)
        title = next((sh.text_frame.text.split("\n")[0] for sh in s.shapes if sh.has_text_frame
                      and sh.name.startswith(("Title", "Titel")) and sh.text_frame.text.strip()), f"Backup {n}")
        notes = s.notes_slide.notes_text_frame.text if s.has_notes_slide else ""
        sections.append(
            f'<section class="slide backup" data-title="{html.escape(title)}" data-pptx="{n}">\n'
            f'  <img class="page" src="v2/backup/{new.name}" alt="{html.escape(title)}" loading="lazy">\n'
            f'  <aside class="notes">\n    {_notes_html(notes)}\n  </aside>\n</section>'
        )
    page = fill_notes(HTML.read_text(encoding="utf-8"), pres)
    a, b = "<!-- BACKUP:BEGIN -->", "<!-- BACKUP:END -->"
    page = page[: page.index(a) + len(a)] + "\n" + "\n\n".join(sections) + "\n" + page[page.index(b) :]
    HTML.write_text(page, encoding="utf-8")
    print(f"backup: {len(sections)} pages")


def export_maps() -> None:
    """Per-cell values of the deck's maps and their palettes (nbs.map_fields), for the hexagon maps."""
    from nbs import map_fields

    data = map_fields.export()
    js = OUT / "maps.js"
    js.write_text("window.MAPDATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + ";\n",
                  encoding="utf-8")
    print(f"wrote {js} ({js.stat().st_size / 1e6:.1f} MB)")


def export_cmip7() -> None:
    """The CMIP7 tables (data/cmip7, scripts/fetch_cmip7_data.py) for the D3 charts on slides 2 and 3."""
    from nbs import cmip7_figures as C

    t, obs, rem, cum = C.temperature(), C.observations(), C.removal(), C.cumulative_removal()
    r2 = lambda v: [round(float(x), 3) for x in v]  # noqa: E731
    out = {
        "ext": C.EXTENSION_FROM,
        "markers": [{"k": k, "label": lab, "color": col} for k, (lab, col) in C.MARKERS.items()],
        "obs": {"y": [int(v) for v in obs.jahr], "v": r2(obs.erwaermung_k)},
        "temp": {k: {"y": [int(v) for v in g.jahr], "med": r2(g["median"]), "p05": r2(g.p05), "p95": r2(g.p95)}
                 for k, g in t.groupby("szenario")},
        "rem": {k: {"y": [int(v) for v in g.jahr], "novel": r2(g.neuartig_gt), "land": r2(g.land_gt)}
                for k, g in rem.groupby("szenario")},
        "cum": [{"k": k, "novel": round(float(r.neuartig_gt), 1), "land": round(float(r.land_gt), 1),
                 "total": round(float(r.gesamt_gt), 1)} for k, r in cum.iterrows()],
        "facts": C.facts(),
    }
    js = OUT / "cmip7.js"
    js.write_text("window.CMIP7 = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"wrote {js} ({js.stat().st_size / 1e3:.0f} kB)")


def main() -> None:
    sys.path.insert(0, str(REPO / "src"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--charts", action="store_true", help="charts only, no backup pages")
    ap.add_argument("--backup", action="store_true", help="backup pages only")
    ap.add_argument("--only", help="comma-separated chart keys")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    export_cmip7()
    if not a.backup:
        export_maps()
        export_charts(set(a.only.split(",")) if a.only else None)
    if not a.charts and not a.only:
        export_backup()


if __name__ == "__main__":
    main()
