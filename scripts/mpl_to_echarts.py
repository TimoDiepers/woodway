"""A drawn matplotlib figure as data for ECharts.

The HTML deck (docs/slides/html/dissvortrag_v2.html) redraws the model's
figures with ECharts, so they get hover read-outs and per-element animation
while keeping exactly what matplotlib decided: limits, ticks, colours, labels,
annotations, legends. Everything is taken from the figure after it has been
drawn and expressed in each axes' *data* coordinates (texts and arrows too);
only legends and figure texts use figure fractions. Maps are axes holding an
image or a mesh: their cells go out as colour runs per row, the borders as
simplified polylines.

    data_scene(fig) -> dict    (JSON-ready)

Used by scripts/export_html_v2.py at savefig time.
"""

from __future__ import annotations

import re

import matplotlib
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import Collection, LineCollection, PathCollection, PolyCollection, QuadMesh
from matplotlib.colors import to_hex, to_rgba
from matplotlib.container import BarContainer
from matplotlib.image import AxesImage
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Patch, Rectangle
from matplotlib.text import Annotation, Text

_SUP = str.maketrans("0123456789+-−=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁼⁽⁾ⁿ")
_SUB = str.maketrans("0123456789+-−=()", "₀₁₂₃₄₅₆₇₈₉₊₋₋₌₍₎")


def plain(s: str) -> str:
    """mathtext -> unicode (super/subscript digits where they exist)."""
    import export_html_v2 as E  # reuse the run parser

    out = []
    for line in s.split("\n"):
        txt = ""
        for t, sh, _it in E.text_runs(line):
            if sh > 0:
                txt += t.translate(_SUP) if all(c in "0123456789+-−=()n " for c in t) else "^" + t
            elif sh < 0:
                txt += t.translate(_SUB) if all(c in "0123456789+-−=() " for c in t) else t
            else:
                txt += t
        out.append(txt)
    return "\n".join(out)


def _col(c):
    r = to_rgba(c)
    return None if r[3] == 0 else to_hex(r, keep_alpha=False)


def _alpha(c) -> float:
    return round(float(to_rgba(c)[3]), 3)


def _r(v, nd=4):
    return None if v is None or not np.isfinite(v) else round(float(v), nd)


def _dash(pattern, px_per_pt):
    if not pattern or not pattern[1]:
        return None
    return [round(v * px_per_pt, 1) for v in pattern[1]]


_MARKERS = {"o": "circle", "s": "rect", "D": "diamond", "d": "diamond", "^": "triangle", "v": "triangle",
            "p": "circle", "h": "circle", "*": "pin", ".": "circle", "<": "triangle", ">": "triangle"}


class DataScene:
    def __init__(self, fig):
        self.fig = fig
        fig.canvas.draw()
        self.r = fig.canvas.get_renderer()
        self.W, self.H = fig.canvas.get_width_height()
        self.px = fig.dpi / 72.0  # figure px per pt
        self.axes: list[dict] = []
        self.seen: set[int] = set()

    # ---- coordinates
    def frac(self, x, y):
        """display -> figure fraction, origin top-left."""
        return [round(x / self.W, 5), round(1 - y / self.H, 5)]

    def to_data(self, ax, xy):
        return ax.transData.inverted().transform(np.asarray(xy, dtype=float).reshape(-1, 2))

    # ---- text
    def text(self, t: Text, ax=None) -> dict | None:
        s = t.get_text()
        if not s or not s.strip() or not t.get_visible():
            return None
        bb = t.get_window_extent(self.r)
        rot = round(t.get_rotation(), 1) % 360
        ha = t.get_horizontalalignment()
        if rot:
            x, y = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
            align = "center"
        else:
            align = {"left": "left", "center": "center", "right": "right"}[ha]
            x = {"left": bb.x0, "center": (bb.x0 + bb.x1) / 2, "right": bb.x1}[align]
            y = (bb.y0 + bb.y1) / 2
        w = t.get_weight()
        d = {"s": plain(s), "c": _col(t.get_color()) or "#000000", "fs": round(t.get_fontsize() * self.px, 2), "al": align}
        if rot:
            d["rot"] = rot if rot <= 180 else rot - 360
        if w in ("bold", "semibold", "demibold", "heavy", "black") or (isinstance(w, (int, float)) and w >= 600):
            d["b"] = 1
        if t.get_style() == "italic":
            d["i"] = 1
        if "Literata" in t.get_fontname() or "Serif" in t.get_fontname():
            d["serif"] = 1
        bp = t.get_bbox_patch()
        if bp is not None and _col(bp.get_facecolor()):
            d["bg"] = _col(bp.get_facecolor())
            d["bga"] = _alpha(bp.get_facecolor())
        if ax is None:
            d["f"] = self.frac(x, y)
        else:
            d["x"], d["y"] = (round(float(v), 5) for v in self.to_data(ax, (x, y))[0])
        return d

    # ---- axes contents
    def line(self, ax, ln: Line2D) -> dict | None:
        if not ln.get_visible():
            return None
        disp = ln.get_transform().transform_path(ln.get_path()).vertices
        xy = self.to_data(ax, disp)
        has_line = ln.get_linestyle() not in ("None", "", " ", "none") and ln.get_linewidth() > 0
        mk = ln.get_marker()
        has_mk = mk not in (None, "None", "", " ", "none") and ln.get_markersize() > 0
        if not has_line and not has_mk:
            return None
        d = {"t": "line", "xy": [[_r(x), _r(y)] for x, y in xy], "c": _col(ln.get_color()) or "#000000",
             "lw": round(ln.get_linewidth() * self.px, 2) if has_line else 0, "z": ln.get_zorder()}
        dash = _dash(ln._dash_pattern, self.px) if has_line else None
        if dash:
            d["dash"] = dash
        if ln.get_alpha() is not None and ln.get_alpha() < 1:
            d["a"] = round(ln.get_alpha(), 3)
        lab = ln.get_label()
        if lab and not lab.startswith("_"):
            d["name"] = plain(lab)
        if not ln.get_clip_on():
            d["noclip"] = 1
        if has_mk:
            every = ln.get_markevery()
            idx = list(range(len(xy)))
            if isinstance(every, (int, np.integer)) and not isinstance(every, bool):
                idx = idx[:: int(every)]
            elif isinstance(every, (list, tuple, np.ndarray)) and len(every):
                idx = [int(k) for k in every] if not isinstance(every[0], (bool, np.bool_)) else [k for k, on in enumerate(every) if on]
            d["mk"] = {"sym": _MARKERS.get(str(mk), "circle"), "size": round(ln.get_markersize() * self.px, 2),
                       "fc": _col(ln.get_markerfacecolor()) if ln._marker.is_filled() else None,
                       "ec": _col(ln.get_markeredgecolor()), "ew": round(ln.get_markeredgewidth() * self.px, 2),
                       "idx": idx if len(idx) != len(xy) else None}
        return d

    def poly_from_display(self, ax, path) -> list:
        out = []
        for poly in path.to_polygons(closed_only=False):
            if len(poly) < 2:
                continue
            out.append([[_r(x), _r(y)] for x, y in self.to_data(ax, poly)])
        return out

    def patch(self, ax, p: Patch, bars: dict) -> dict | None:
        if not p.get_visible():
            return None
        if isinstance(p, FancyArrowPatch):
            paths, _ = p._get_path_in_displaycoord()
            v = self.to_data(ax, paths[0].vertices)
            return {"t": "arrow", "from": [_r(v[0][0]), _r(v[0][1])], "to": [_r(v[-1][0]), _r(v[-1][1])],
                    "c": _col(p.get_edgecolor()) or "#000000", "lw": round(p.get_linewidth() * self.px, 2)}
        fc, ec = _col(p.get_facecolor()) if p.get_fill() else None, _col(p.get_edgecolor())
        lw = p.get_linewidth()
        if not fc and not (ec and lw):
            return None
        style = {"fc": fc, "fa": _alpha(p.get_facecolor()) if fc else None, "ec": ec if lw else None,
                 "ew": round(lw * self.px, 2) if lw else 0, "z": p.get_zorder()}
        if p.get_alpha() is not None:
            style["a"] = round(p.get_alpha(), 3)
        if p.get_hatch():
            style["hatch"] = p.get_hatch()
            style["hc"] = _col(getattr(p, "_hatch_color", "#000000")) or "#000000"
        if id(p) in bars:
            o, ci = bars[id(p)]
            x0, y0 = p.get_x(), p.get_y()
            x1, y1 = x0 + p.get_width(), y0 + p.get_height()
            return {"t": "bar", "o": o, "ci": ci, "r": [_r(x0), _r(y0), _r(x1), _r(y1)], **style}
        path = p.get_transform().transform_path(p.get_path())
        return {"t": "poly", "pts": self.poly_from_display(ax, path), **style}

    def collection(self, ax, c: Collection) -> list[dict]:
        if not c.get_visible():
            return []
        out = []
        paths = c.get_paths()
        if not len(paths):
            return out
        fcs, ecs, lws = c.get_facecolor(), c.get_edgecolor(), c.get_linewidth()
        offs = c.get_offsets()
        use_offs = isinstance(c, PathCollection) and offs is not None and len(offs) and not np.allclose(offs, 0)
        if use_offs:   # scatter
            disp = c.get_offset_transform().transform(offs)
            data = self.to_data(ax, disp)
            sizes = c.get_sizes()
            pts = []
            for i, (x, y) in enumerate(data):
                fc = fcs[i % len(fcs)] if len(fcs) else None
                ec = ecs[i % len(ecs)] if len(ecs) else None
                s = sizes[i % len(sizes)] if len(sizes) else 36
                pts.append({"x": _r(x), "y": _r(y), "fc": _col(fc) if fc is not None else None,
                            "ec": _col(ec) if ec is not None else None,
                            "s": round(float(np.sqrt(s)) * self.px, 2)})
            v = paths[0].vertices
            sym = "rect" if len(v) in (5, 4) and np.allclose(np.abs(v[:4]), np.abs(v[0])) else "circle"
            out.append({"t": "points", "pts": pts, "sym": sym, "ew": round(float(lws[0]) * self.px, 2) if len(lws) else 0,
                        "z": c.get_zorder(), "a": round(c.get_alpha(), 3) if c.get_alpha() is not None else None,
                        "name": plain(c.get_label()) if c.get_label() and not c.get_label().startswith("_") else None})
            return out
        tr = c.get_transform()
        hatches = getattr(c, "hatches", None) or ([c.get_hatch()] if c.get_hatch() else [])
        hatch_col = _col(getattr(c, "_hatch_color", None) or matplotlib.rcParams["hatch.color"])
        if hatches and hatches[0] and (not len(fcs) or all(to_rgba(f)[3] == 0 for f in fcs)):
            # hatching without fill (contourf(..., colors="none", hatches=[...])): an overlay
            polys = []
            for path in paths:
                polys += [simplify(q, 0.05) for q in self.poly_from_display(ax, tr.transform_path(path))]
            return [{"t": "poly", "pts": polys, "fc": None, "hatch": hatches[0], "hc": hatch_col or "#000000",
                     "z": c.get_zorder()}]
        line_like = isinstance(c, LineCollection) or not len(fcs) or all(to_rgba(f)[3] == 0 for f in fcs)
        many = len(paths) > 300
        for i, path in enumerate(paths):
            dp = tr.transform_path(path)
            polys = self.poly_from_display(ax, dp)
            if many:
                polys = [simplify(p, 0.08) for p in polys]
            fc = fcs[i % len(fcs)] if len(fcs) else None
            ec = ecs[i % len(ecs)] if len(ecs) else None
            lw = float(lws[i % len(lws)]) if len(lws) else 0
            if line_like:
                if ec is None or not lw or _col(ec) is None:
                    continue
                out.append({"t": "polyline", "lines": polys, "c": _col(ec), "lw": round(lw * self.px, 2),
                            "z": c.get_zorder(), "a": _alpha(ec)})
            else:
                out.append({"t": "poly", "pts": polys, "fc": _col(fc), "fa": _alpha(fc),
                            "ec": _col(ec) if (ec is not None and lw) else None, "ew": round(lw * self.px, 2),
                            "z": c.get_zorder(), "hatch": c.get_hatch() or None,
                            "hc": _col(getattr(c, "_hatch_color", "#000000")) if c.get_hatch() else None})
        if many:  # merge borders into one item per style
            merged = {}
            for it in out:
                key = (it["t"], it.get("c"), it.get("fc"), it.get("lw"), it.get("ec"))
                if key in merged:
                    merged[key]["lines" if it["t"] == "polyline" else "pts"] += it["lines" if it["t"] == "polyline" else "pts"]
                else:
                    merged[key] = it
            out = list(merged.values())
        return out

    def raster_image(self, ax, im: AxesImage) -> dict | None:
        arr = im.get_array()
        if arr is None:
            return None
        rgba = im.to_rgba(arr, bytes=True) if arr.ndim == 2 else (
            (np.asarray(arr) * (255 if np.asarray(arr).dtype.kind == "f" else 1)).astype(np.uint8))
        vals = np.ma.filled(np.ma.masked_invalid(arr.astype(float)), np.nan) if arr.ndim == 2 else None
        x0, x1, y0, y1 = im.get_extent()
        ny, nx = rgba.shape[:2]
        dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
        top_first = im.origin == "upper"
        ys = [(y1 - (j + 1) * dy, y1 - j * dy) if top_first else (y0 + j * dy, y0 + (j + 1) * dy) for j in range(ny)]
        return self._cells(rgba, vals, [x0 + i * dx for i in range(nx + 1)], ys, z=im.get_zorder())

    def raster_mesh(self, ax, m: QuadMesh) -> dict | None:
        coords = m._coordinates
        arr = m.get_array()
        if arr is None:
            return None
        arr = np.ma.asarray(arr).reshape(coords.shape[0] - 1, coords.shape[1] - 1)
        if np.ptp(coords[0, :, 0]) == 0 and np.ptp(coords[:, 0, 0]) > 0:   # e.g. horizontal colour bars
            coords, arr = coords.transpose(1, 0, 2), arr.T
        xe, ye = coords[0, :, 0], coords[:, 0, 1]
        ny, nx = len(ye) - 1, len(xe) - 1
        rgba = m.to_rgba(arr, bytes=True).reshape(ny, nx, 4)
        vals = np.ma.filled(np.ma.masked_invalid(arr.astype(float)), np.nan)
        ys = [(min(ye[j], ye[j + 1]), max(ye[j], ye[j + 1])) for j in range(ny)]
        return self._cells(rgba, vals, list(xe), ys, z=m.get_zorder())

    def _cells(self, rgba, vals, xedges, yspans, z) -> dict:
        """Runs of equal colour per row: [row, col0, col1, colourIndex(, value)]."""
        palette, pidx, runs = [], {}, []
        ny, nx = rgba.shape[:2]
        for j in range(ny):
            row = rgba[j]
            i = 0
            while i < nx:
                if row[i, 3] == 0:
                    i += 1
                    continue
                k = i + 1
                same_val = vals is not None
                while k < nx and np.array_equal(row[k], row[i]) and (vals is None or not np.isfinite(vals[j, i])
                                                                      or vals[j, k] == vals[j, i]):
                    k += 1
                key = tuple(int(v) for v in row[i])
                if key not in pidx:
                    pidx[key] = len(palette)
                    palette.append("#%02x%02x%02x" % key[:3] if key[3] == 255 else
                                   "rgba(%d,%d,%d,%.3f)" % (key[0], key[1], key[2], key[3] / 255))
                run = [j, i, k, pidx[key]]
                if same_val and np.isfinite(vals[j, i]):
                    run.append(round(float(vals[j, i]), 3))
                runs.append(run)
                i = k
        return {"t": "cells", "x": [round(float(v), 4) for v in xedges],
                "y": [[round(float(a), 4), round(float(b), 4)] for a, b in yspans],
                "pal": palette, "runs": runs, "z": z}

    def legend(self, lg: Legend) -> dict:
        texts = lg.get_texts()
        handles = lg.legend_handles
        entries = []
        fs = round(texts[0].get_fontsize() * self.px, 2) if texts else 12
        for t, h in zip(texts, handles):
            if not t.get_text():
                continue
            bb = t.get_window_extent(self.r)
            e = {"s": plain(t.get_text()), "f": self.frac(bb.x0, (bb.y0 + bb.y1) / 2), "c": _col(t.get_color())}
            if isinstance(h, Line2D):
                has_line = h.get_linestyle() not in ("None", "", " ", "none")
                e["k"] = "line" if has_line else "marker"
                e["col"] = _col(h.get_color()) if has_line else _col(h.get_markerfacecolor()) or _col(h.get_color())
                e["lw"] = round(h.get_linewidth() * self.px, 2)
                if has_line and _dash(h._dash_pattern, self.px):
                    e["dash"] = _dash(h._dash_pattern, self.px)
                if h.get_marker() not in (None, "None", "", " ", "none"):
                    e["sym"] = _MARKERS.get(str(h.get_marker()), "circle")
            elif isinstance(h, Patch):
                e["k"] = "patch"
                e["col"] = _col(h.get_facecolor()) if h.get_fill() else None
                e["a"] = _alpha(h.get_facecolor())
                e["ec"] = _col(h.get_edgecolor()) if h.get_linewidth() else None
                if h.get_hatch():
                    e["hatch"], e["hc"] = h.get_hatch(), _col(getattr(h, "_hatch_color", "#000000"))
            elif isinstance(h, Collection):
                e["k"] = "marker"
                fc = h.get_facecolor()
                e["col"] = _col(fc[0]) if len(fc) else None
                e["sym"] = "circle"
            entries.append(e)
        lt = lg.get_title()
        out = {"entries": entries, "fs": fs, "hl": round(lg.handlelength * fs, 1), "pad": round(lg.handletextpad * fs, 1)}
        if lt.get_text():
            out["title"] = self.text(lt)
        return out

    def axis_info(self, ax, which: str) -> dict:
        axis = ax.xaxis if which == "x" else ax.yaxis
        lim = ax.get_xlim() if which == "x" else ax.get_ylim()
        lo, hi = min(lim), max(lim)
        ticks = []
        for tk in axis.get_major_ticks():
            if not tk.get_visible():
                continue
            v = tk.get_loc()
            if v is None or not (lo - 1e-9 <= v <= hi + 1e-9):
                continue
            lab = tk.label1 if tk.label1.get_visible() else tk.label2
            ticks.append([_r(v, 6), plain(lab.get_text()) if lab.get_visible() else ""])
        lab0 = next((tk.label1 for tk in axis.get_major_ticks() if tk.label1.get_visible() and tk.label1.get_text()),
                    next((tk.label2 for tk in axis.get_major_ticks() if tk.label2.get_visible() and tk.label2.get_text()), None))
        grid = axis.get_gridlines()
        gl = next((g for g in grid if g.get_visible()), None)
        sp = ax.spines["bottom" if which == "x" else "left"]
        pos = axis.get_ticks_position() if which == "y" else "bottom"
        if which == "y" and ax.spines["right"].get_visible() and not ax.spines["left"].get_visible():
            pos = "right"
        if which == "y" and pos == "right":
            sp = ax.spines["right"]
        if which == "x" and ax.spines["top"].get_visible() and not ax.spines["bottom"].get_visible():
            sp, pos = ax.spines["top"], "top"
        out = {"min": _r(lo, 6), "max": _r(hi, 6), "inv": bool(lim[0] > lim[1]), "scale": axis.get_scale(),
               "ticks": ticks, "pos": pos,
               "line": _col(sp.get_edgecolor()) if sp.get_visible() else None,
               "lc": _col(lab0.get_color()) if lab0 is not None else None,
               "lfs": round(lab0.get_fontsize() * self.px, 2) if lab0 is not None else None,
               "tick": bool(axis.get_major_ticks() and axis.get_major_ticks()[0].tick1line.get_visible()
                            and axis.get_major_ticks()[0].tick1line.get_markersize() > 0)}
        if gl is not None:
            out["grid"] = {"c": _col(gl.get_color()), "lw": round(gl.get_linewidth() * self.px, 2)}
        return out

    def ax_scene(self, ax: Axes) -> dict:
        bb = ax.get_position()   # figure fraction, origin bottom-left
        d = {"box": [round(bb.x0, 5), round(1 - bb.y1, 5), round(bb.width, 5), round(bb.height, 5)],
             "on": bool(ax.axison), "x": self.axis_info(ax, "x"), "y": self.axis_info(ax, "y"), "items": [], "texts": []}
        bars = {}
        for ci, cont in enumerate(ax.containers):
            if isinstance(cont, BarContainer):
                for rect in cont.patches:
                    bars[id(rect)] = ("v" if cont.orientation == "vertical" else "h", ci)
        labels = []
        for t in (ax.title, ax._left_title, ax._right_title):
            td = self.text(t)
            if td:
                labels.append(td)
        for t in (ax.xaxis.label, ax.yaxis.label):
            td = self.text(t)
            if td:
                labels.append(td)
        d["labels"] = labels
        if ax.patch.get_visible() and _col(ax.patch.get_facecolor()) and _col(ax.patch.get_facecolor()) != _col(self.fig.patch.get_facecolor()):
            d["bg"] = _col(ax.patch.get_facecolor())
        for ch in sorted(ax.get_children(), key=lambda a: a.get_zorder()):
            if id(ch) in self.seen or not ch.get_visible():
                continue
            self.seen.add(id(ch))
            if ch in (ax.title, ax._left_title, ax._right_title, ax.patch, ax.xaxis, ax.yaxis) or ch in ax.spines.values():
                continue
            if isinstance(ch, Legend):
                d["legend"] = self.legend(ch)
            elif isinstance(ch, Line2D):
                it = self.line(ax, ch)
                if it:
                    d["items"].append(it)
            elif isinstance(ch, AxesImage):
                it = self.raster_image(ax, ch)
                if it:
                    d["items"].append(it)
            elif isinstance(ch, QuadMesh):
                it = self.raster_mesh(ax, ch)
                if it:
                    d["items"].append(it)
            elif isinstance(ch, Text):
                td = self.text(ch, ax)
                if td:
                    td["noclip"] = 1
                    d["texts"].append(td)
                if isinstance(ch, Annotation) and ch.arrow_patch is not None and ch.arrow_patch.get_visible():
                    it = self.patch(ax, ch.arrow_patch, bars)
                    if it:
                        d["items"].append(it)
            elif isinstance(ch, Patch):
                it = self.patch(ax, ch, bars)
                if it:
                    d["items"].append(it)
            elif isinstance(ch, Collection):
                d["items"] += self.collection(ax, ch)
        d["map"] = any(it["t"] == "cells" for it in d["items"])
        return d

    def build(self) -> dict:
        axes = [a for a in self.fig.get_axes() if a.get_visible()]
        out = {"w": self.W, "h": self.H, "axes": [self.ax_scene(a) for a in axes], "texts": [], "legends": []}
        for t in self.fig.texts:
            td = self.text(t)
            if td:
                out["texts"].append(td)
        for lg in self.fig.legends:
            out["legends"].append(self.legend(lg))
        for a in out["axes"]:
            if "legend" in a:
                out["legends"].append(a.pop("legend"))
        return out


def simplify(pts, tol):
    """Douglas-Peucker in data units, for map borders."""
    if len(pts) < 3:
        return pts
    a = np.asarray([p for p in pts if p[0] is not None and p[1] is not None], dtype=float)
    if len(a) < 3:
        return pts
    keep = np.zeros(len(a), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(a) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        p, q = a[i], a[j]
        seg = q - p
        n = np.hypot(*seg)
        rel = a[i + 1:j] - p
        dist = np.abs(seg[0] * rel[:, 1] - seg[1] * rel[:, 0]) / n if n else np.hypot(rel[:, 0], rel[:, 1])
        k = int(np.argmax(dist))
        if dist[k] > tol:
            keep[i + 1 + k] = True
            stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return [[round(float(x), 3), round(float(y), 3)] for x, y in a[keep]]


def data_scene(fig) -> dict:
    return DataScene(fig).build()


_ = re  # kept for callers that post-process labels
_ = Rectangle
_ = PolyCollection
