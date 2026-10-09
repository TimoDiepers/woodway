"""Axis labels of the charts that show a quantity of a formula: set on the slide as text with the formula
symbol in its colour (KaTeX), not inside the plot, so the symbol looks as in the formulas above it.

Slide 18: epsilon_CO2 (the radiative efficiency), slide 19: Delta m_CO2, slide 21: Delta T (in patch_tempsum).
"""

import re

CSS = """
/* y label over a chart: rotated, centred on its own point; the symbol as in the formulas */
.axlab { position: absolute; transform: translate(-50%, -50%) rotate(-90deg); white-space: nowrap; pointer-events: none;
         font: 400 19px/1 var(--sans); color: var(--muted); }
.axlab .katex { font-size: 1.2em; }
"""


def _rep(s, old, new):
    assert s.count(old) == 1, old[:90]
    return s.replace(old, new)


def patch(page: str) -> str:
    head, sep, tail = page.partition("</style>")
    page = head + CSS + sep + tail
    # slide 18: the efficiency curve appears on click 5 together with its label
    m = re.search(r'<div class="chart" data-step="5" data-chart="k6e"[^>]*></div>', page)
    assert m
    page = page[: m.end()] + ('<div data-step="5" style="position:absolute; inset:0; pointer-events:none">'
                              '<div class="axlab" style="left:34px; top:49%"><span class="tex">$\\cq{\\varepsilon_{\\mathrm{CO_2}}}(t)$</span>'
                              ' [10⁻¹⁵ W/m² je kg]</div></div>') + page[m.end():]
    # slide 19: what the air lacks after the removal
    page = _rep(page, '<div class="rise" data-step="2" style="--d:0"><div class="chart" data-step="2" style="height:270px; margin-top:4px" data-slot-steps="0" data-chart="k3s"',
                '<div class="rise" data-step="2" style="--d:0; position:relative"><div class="chart" data-step="2" style="height:270px; margin-top:4px" data-slot-steps="0" data-chart="k3s"')
    m = re.search(r'data-chart="k3s"[^>]*></div>', page)
    page = page[: m.end()] + ('<div class="axlab" style="left:62px; top:45%"><span class="tex">$\\cq{\\Delta m_{\\mathrm{CO_2}}}(t)$</span></div>') + page[m.end():]
    return page
