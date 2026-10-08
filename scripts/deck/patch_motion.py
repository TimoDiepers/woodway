"""Gentle motion in the schema drawings (2026-10-08): sun rays turn, arrows and radiation flow, steam
rises, fans turn, trees sway, molecules jiggle. Step by step: what belongs to the current click moves,
everything of earlier clicks stops. Applied last."""
import re

SCHEMAS = ["s_zwei_wege", "s_kapitel_baeume", "s_kapitel_klima", "s_kapitel_vergleich", "s_kohlenstoff",
           "s_albedo_faelle", "s_dac_prozess", "s_fair", "s_dac_rechnung"]

CSS = """
/* ---- gentle motion in schema drawings (svg.mo) ---- */
svg.mo .m-flow { stroke-dasharray: 22 6; animation: mflow 1.3s linear infinite; }
@keyframes mflow { to { stroke-dashoffset: -28; } }
svg.mo .m-flowd { animation: mflowd 2s linear infinite; }
@keyframes mflowd { to { stroke-dashoffset: -24; } }
svg.mo .m-rays { transform-box: fill-box; transform-origin: center; animation: mspin 28s linear infinite; }
@keyframes mspin { to { transform: rotate(360deg); } }
svg.mo .m-fan { transform-box: fill-box; transform-origin: center; animation: mspin 2.4s linear infinite; }
svg.mo .m-steam { animation: msteam 1.8s ease-in-out infinite alternate; }
@keyframes msteam { from { transform: translateY(2px); opacity: .55; } to { transform: translateY(-4px); opacity: 1; } }
svg.mo .m-sway { transform-box: fill-box; transform-origin: 50% 100%; animation: msway 4.5s ease-in-out infinite alternate; }
@keyframes msway { from { transform: rotate(-1.2deg); } to { transform: rotate(1.2deg); } }
svg.mo .m-mol { animation: mjig 2.6s ease-in-out infinite alternate; animation-delay: var(--ph, 0s); }
@keyframes mjig { from { transform: translate(-2px, -1px); } to { transform: translate(2px, 1px); } }
svg.mo .m-bob { animation: mbob 1.7s ease-in-out infinite alternate; animation-delay: var(--ph, 0s); }
@keyframes mbob { from { transform: translateY(-2px); } to { transform: translateY(2px); } }
svg.mo .m-drift { animation: mdrift 2.4s ease-in-out infinite alternate; }
@keyframes mdrift { from { transform: translateX(-4px); } to { transform: translateX(4px); } }
svg.mo .m-pulse { transform-box: fill-box; transform-origin: center; animation: mpulse 2.2s ease-in-out infinite alternate; }
@keyframes mpulse { from { transform: scale(.96); } to { transform: scale(1.04); } }
@media (prefers-reduced-motion: reduce) { svg.mo :is(.m-drift, .m-flow, .m-flowd, .m-rays, .m-fan, .m-steam, .m-sway, .m-mol, .m-bob, .m-pulse) { animation: none; } }
"""

ANIM = ":is(.m-drift, .m-flow, .m-flowd, .m-rays, .m-fan, .m-steam, .m-sway, .m-mol, .m-bob, .m-pulse)"


def _step_css() -> str:
    """Only the current click moves: the base stops with the first click, a step's elements with the next."""
    rules = [f'.slide:has([data-step="1"].shown) svg.mo {ANIM}:not([data-step] *) {{ animation-play-state: paused; }}']
    for k in range(1, 10):
        rules.append(f'.slide:has([data-step="{k + 1}"].shown) svg.mo [data-step="{k}"] {ANIM} {{ animation-play-state: paused; }}')
    return "\n".join(rules) + "\n"


def _add_class(tag: str, cls: str) -> str:
    if ' class="' in tag[:tag.index(">") if ">" in tag else len(tag)]:
        return re.sub(r' class="', f' class="{cls} ', tag, count=1)
    return re.sub(r"^<(\w+) ", rf'<\1 class="{cls}" ', tag, count=1)


def tag_svg(svg: str, key: str = "") -> str:
    k = iter(range(10000))
    ph = lambda: f"-{(next(k) * 0.37) % 2.6:.2f}s"
    # sun rays
    svg = re.sub(r'<g stroke="#d9a441" stroke-width="\d(?:\.\d)?" stroke-linecap="round">',
                 lambda m: m.group(0).replace("<g ", '<g class="m-rays" ', 1), svg)
    # arrows with an arrowhead: flowing dashes (an existing dash pattern keeps its pattern and just moves)
    def arrow(m):
        tag = m.group(0)
        if "marker-end" not in tag:
            return tag
        return _add_class(tag, "m-flowd" if "stroke-dasharray" in tag else "m-flow")
    svg = re.sub(r"<path [^>]*>", arrow, svg)
    # dashed supply lines (electricity)
    svg = re.sub(r'<path [^>]*stroke-dasharray="2 6"[^>]*>', lambda m: _add_class(m.group(0), "m-flowd") if "m-flow" not in m.group(0) else m.group(0), svg)
    # steam / heat squiggles
    svg = re.sub(r'<path d="M[\d.]+ [\d.]+ q-?\d+ -\d+ 0 -\d+ q-?\d+ -\d+ 0 -\d+[^"]*"[^>]*>', lambda m: _add_class(m.group(0), "m-steam"), svg)
    # fan blades: a plus sign drawn as one path
    svg = re.sub(r'<path d="M\d+ \d+ V\d+ M\d+ \d+ H\d+"[^>]*>', lambda m: _add_class(m.group(0), "m-fan"), svg)
    # trees: a trunk (narrow, tall rect) followed by three crown circles
    def tree(m):
        w, h = float(m.group(2)), float(m.group(3))
        if w > 30 or h < 90:
            return m.group(0)
        return '<g class="m-sway">' + m.group(0) + "</g>"
    svg = re.sub(r'(<rect x="[\d.]+" y="[\d.]+" width="([\d.]+)" height="([\d.]+)" fill="[^"]*"/>)\s*(<circle [^>]*/>\s*){3}', tree, svg)
    # molecules: line-and-circle groups and <use> of the molecule symbol
    svg = re.sub(r"<g><line ", lambda m: f'<g class="m-mol" style="--ph:{ph()}"><line ', svg)
    # <use> keeps its x/y outside the CSS transform, so its box centre would be off: wrap it in a group
    svg = re.sub(r'<use href="#co2[^"]*"[^>]*/>', lambda m: f'<g class="m-mol" style="--ph:{ph()}">' + m.group(0) + '</g>', svg)
    if key == "s_dac_prozess":
        svg = re.sub(r'<circle cx="[\d.]+" cy="[\d.]+" r="6"/>', lambda m: m.group(0).replace("<circle ", f'<circle class="m-bob" style="--ph:{ph()}" ', 1), svg)
    return svg


def _albedo_cases(svg: str) -> str:
    """Slide with the four albedo cases: the reference moves completely; in each further case only the arrow
    that changes moves (brighter tree: its reflection; brighter ground: the ground's reflection; more sun:
    both incoming beams and the sun)."""
    svg = re.sub(r'class="m-flowd? ?', 'class="', svg)
    svg = svg.replace(' class=""', "")
    changed = {"1": ["M132 156 L170 76"], "2": ["M408 322 L446 200"], "3": ["M64 72 L118 156", "M346 122 L396 322"]}
    parts = re.split(r'(<g class="(?:pop zoomnext|pop)" data-step="\d"[^>]*>)', svg)
    out = parts[0]
    # reference: all four arrows flow
    out = re.sub(r"<path [^>]*marker-end[^>]*>", lambda m: _add_class(m.group(0), "m-flowd" if "dasharray" in m.group(0) else "m-flow"), out)
    for i in range(1, len(parts), 2):
        step = re.search(r'data-step="(\d)"', parts[i]).group(1)
        body = parts[i + 1]
        for d in changed.get(step, []):
            body = re.sub(r'<path d="' + re.escape(d) + r'"[^>]*>', lambda m: _add_class(m.group(0), "m-flowd" if "dasharray" in m.group(0) else "m-flow"), body)
        if step != "3":
            body = body.replace('<g class="m-rays" ', "<g ")
        out += parts[i] + body
    return out


def patch(page: str) -> str:
    head, sep, tail = page.partition("</style>")
    page = head + CSS + _step_css() + sep + tail
    for key in SCHEMAS:
        for m in list(re.finditer(r'<svg class="([^"]*)" data-export="' + key + r'"[^>]*>.*?</svg>', page, flags=re.S))[::-1]:
            svg = m.group(0)
            svg = tag_svg(svg, key)
            if key == "s_albedo_faelle":
                svg = _albedo_cases(svg)
            svg = svg.replace(f'<svg class="{m.group(1)}"', f'<svg class="{m.group(1)} mo"', 1)
            page = page[: m.start()] + svg + page[m.end():]
    # the "what trees do" drawing comes from a template, filled at runtime
    t = re.search(r'<template id="tpl-trees">.*?</template>', page, flags=re.S)
    assert t
    tpl = tag_svg(t.group(0))
    # local effects: the wind drifts, the bird bobs, the shade lines flow down
    tpl = re.sub(r'(<g transform="translate\(70 270\) scale\(2\.4\)"[^>]*>.*?</g>)', r'<g class="m-drift">\1</g>', tpl, count=1, flags=re.S)
    tpl = tpl.replace('<g transform="translate(96 372) scale(2.2)"', '<g transform="translate(200 352) scale(2.2)"', 1)   # the bird close to the tree
    tpl = re.sub(r'(<g transform="translate\(200 352\) scale\(2\.2\)"[^>]*>.*?</g>)', r'<g class="m-bob">\1</g>', tpl, count=1, flags=re.S)
    tpl = re.sub(r'<g stroke="#7a7466" stroke-width="2\.5" stroke-dasharray="7 6"', '<g class="m-flowd" stroke="#7a7466" stroke-width="2.5" stroke-dasharray="7 6"', tpl, count=1)
    page = page[: t.start()] + tpl + page[t.end():]
    page = re.sub(r'<svg class="trees-do"', '<svg class="trees-do mo"', page)
    return page
