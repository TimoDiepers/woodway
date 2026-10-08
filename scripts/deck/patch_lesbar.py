"""Readability in a large room with a projector (2026-10-07): no content text below about 18 px on the
1600 x 900 canvas. Sources and minor chart notes may stay small. Applied after patch_takeaway."""
import re

CSS = [
    (".legend.sm dt { font-size: 20px; }", ".legend.sm dt { font-size: 23px; }"),
    (".legend.sm dd { font-size: 15.5px; line-height: 1.3; }", ".legend.sm dd { font-size: 19px; line-height: 1.28; }"),
    (".legend dd { font-family: var(--sans); font-size: 18px;", ".legend dd { font-family: var(--sans); font-size: 20px;"),
    (".road { display: flex; gap: 16px; align-items: center; margin: 0 0 12px; font: 500 16px/1.2 var(--sans);",
     ".road { display: flex; gap: 16px; align-items: center; margin: 0 0 12px; font: 500 19px/1.2 var(--sans);"),
    (".road .tex { font-size: 22px;", ".road .tex { font-size: 25px;"),
]

# schema texts in the main part (drawn at about 1:1): small labels one to two px larger
SVG_MAP = {16: 17, 17: 19, 18: 19, 19: 20}
# the energy-balance schema of the Klima chapter is drawn at about 0.77
ANTRIEB = [
    ('<text x="112" y="58" font-size="16" letter-spacing="1.5" fill="var(--muted)">OBERRAND DER ATMOSPHÄRE</text>',
     '<text x="114" y="58" font-size="22" fill="var(--muted)">Oberrand der Atmosphäre</text>'),
    ('<text x="24" y="200" font-size="17"', '<text x="14" y="200" font-size="24"'),
    ('<text x="352" y="150" font-size="17"', '<text x="338" y="150" font-size="24"'),
    ('<text x="466" y="356" text-anchor="end" font-size="17"', '<text x="470" y="364" text-anchor="end" font-size="24"'),
    ('<text x="466" y="378" text-anchor="end" font-size="17"', '<text x="470" y="388" text-anchor="end" font-size="24"'),
]


def _section(page: str, title: str) -> re.Match:
    m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(title) + r'"[^>]*>.*?</section>', page, flags=re.S)
    assert m, title
    return m


def _sub_section(page: str, title: str, fn) -> str:
    m = _section(page, title)
    return page[: m.start()] + fn(m.group(0)) + page[m.end():]


def _k5_grid(sec: str) -> str:
    """Slide 'Impulsantwort auf die CO2-Aufnahme eines Baums': chart left, formulas right, as on the next slides."""
    chart = re.search(r'<div class="chart" data-chart="k5"[^>]*></div>', sec).group(0)
    foot = re.search(r'<div class="foot"><div class="rise" style="--d:1500">(<div class="eq tex"[^>]*>.*?</div>)(<dl class="legend sm tex rise"[^>]*>.*?</dl>)</div>(<p class="takeaway".*?</p>)</div>', sec, flags=re.S)
    assert foot
    eq, dl, take = foot.groups()
    eq = eq.replace('style="font-size:22px"', 'style="font-size:23px"')
    dl = dl.replace('style="--d:1800"', 'style="--d:1200"')
    grid = ('<div style="display:grid; grid-template-columns:minmax(0,1fr) 610px; gap:28px; flex:1; min-height:0; align-items:center">'
            + chart.replace('></div>', ' style="height:100%"></div>')
            + '<div class="rise" style="--d:900">' + eq + dl + '</div></div>\n    '
            + '<div class="foot"><div></div>' + take + '</div>')
    sec = sec.replace(chart, '', 1)
    return sec.replace(foot.group(0), grid, 1)


def patch(page: str) -> str:
    for old, new in CSS:
        assert old in page, old
        page = page.replace(old, new, 1)

    # ECharts of the CMIP7 slides
    a, b = page.index("function ecAxis(extra)"), page.index("const EC_CHARTS")
    ec = re.sub(r"fontSize: (1[4-7])\b", lambda m: "fontSize: " + {"14": "17", "15": "19", "16": "20", "17": "21"}[m.group(1)], page[a:b])
    page = page[:a] + ec + page[b:]

    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)

    def schemas(sec: str) -> str:
        def one(m):
            svg = m.group(0)
            if 'data-export="s_antrieb"' in svg:
                for old, new in ANTRIEB:
                    assert old in svg, old
                    svg = svg.replace(old, new)
                return svg
            return re.sub(r'font-size="(\d+)"', lambda f: f'font-size="{SVG_MAP.get(int(f.group(1)), int(f.group(1)))}"', svg)
        return re.sub(r'<svg class="schema".*?</svg>', one, sec, flags=re.S)

    main = re.sub(r'<section class="slide.*?</section>', lambda m: schemas(m.group(0)), main, flags=re.S)

    # small inline labels
    main = _sub_section(main, "Strahlungsantrieb: Energiebilanz am Oberrand",
                        lambda s: s.replace("font:600 15px/1.2 var(--sans)", "font:600 18px/1.2 var(--sans)")
                                   .replace('<div class="eq tex" style="font-size:22px; text-align:center">', '<div class="eq tex" style="font-size:24px; text-align:center">'))
    # slide 20: the removal curve comes with the removal schema (second axes of k3 = second slot)
    main = _sub_section(main, "Impulsantwort des Kohlenstoffkreislaufs",
                        lambda s: s.replace('<div class="chart" data-chart="k3"', '<div class="chart" data-slot-steps="0,1" data-chart="k3"')
                                   .replace('über 75 Jahre', 'über 150 Jahre'))
    main = _sub_section(main, "Gesamter Strahlungsantrieb je Baum",
                        lambda s: s.replace('<div class="eq tex" style="font-size:28px">', '<div class="eq tex" style="font-size:24px">'))
    main = _sub_section(main, "Methodischer Beitrag", lambda s: s.replace('<td style="font-size:18px">', '<td style="font-size:20px">'))
    main = _sub_section(main, "Impulsantwort auf die CO₂-Aufnahme eines Baums", _k5_grid)
    # larger labels that no longer fit their box
    main = _sub_section(main, "DAC-Modell", lambda s: s.replace(">CRU TS 4.09, Mittel 2011–2020<", ">CRU TS 4.09, 2011–2020<"))
    main = _sub_section(main, "Sorbens-DAC: Prozess und Energiebedarf",
                        lambda s: s.replace('text-anchor="middle" font-size="19" fill="#fff">Strom 0,5', 'text-anchor="middle" font-size="18" fill="#fff">Strom 0,5'))

    def pills(sec: str) -> str:
        """the number pills 28 units wider, the centred text with them"""
        return re.sub(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="36" rx="18" fill="#efcfae"/><text x="([\d.]+)"',
                      lambda m: f'<rect x="{m[1]}" y="{m[2]}" width="{float(m[3]) + 28:g}" height="36" rx="18" fill="#efcfae"/><text x="{float(m[4]) + 14:g}"', sec)
    main = _sub_section(main, "Priorisierung von Aufforstung und DAC", pills)
    # slide 20: the larger legend must not push the schema into the signpost line
    def irf(sec: str) -> str:
        for old, new in [
            ('viewBox="0 0 620 400" style="width:100%; height:auto"', 'viewBox="0 0 620 400" style="width:100%; height:100%"'),
            # the schema now draws at about 0.82: its labels larger
            ('font-size="17" letter-spacing="1.5" fill="var(--muted)">EMISSION', 'font-size="21" letter-spacing="1.5" fill="var(--muted)">EMISSION'),
            ('font-size="17" letter-spacing="1.5" fill="var(--muted)">ENTNAHME', 'font-size="21" letter-spacing="1.5" fill="var(--muted)">ENTNAHME'),
            ('<text x="292" y="168" text-anchor="middle" font-size="20" font-weight="600" fill="var(--co2)">nehmen einen Teil auf',
             '<text x="292" y="180" text-anchor="middle" font-size="24" font-weight="600" fill="var(--co2)">nehmen einen Teil auf'),
            ('<text x="292" y="378" text-anchor="middle" font-size="20" font-weight="600" fill="var(--co2)">geben einen Teil ab',
             '<text x="292" y="390" text-anchor="middle" font-size="24" font-weight="600" fill="var(--co2)">geben einen Teil ab'),
            ('<div class="eq tex" style="font-size:26px">', '<div class="eq tex" style="font-size:23px">'),
            ("<dd>Anteil, der t Jahre nach Emission oder Entnahme in der Atmosphäre bleibt</dd>", "<dd>Anteil, der t Jahre danach noch in der Atmosphäre ist</dd>"),
            ("Zeitkonstanten 394 · 37 · 4 Jahre</dd>", "Zeitkonstanten 394 · 37 · 4 a</dd>"),
        ]:
            assert old in sec, old
            sec = sec.replace(old, new)
        return sec
    main = _sub_section(main, "Impulsantwort des Kohlenstoffkreislaufs", irf)
    return main + "<!-- BACKUP:BEGIN -->" + backup
