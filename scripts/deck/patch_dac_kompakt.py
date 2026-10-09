"""DAC part, compact: three slides instead of six.

1. "DAC-Modell": the machine (drawing from the backup slide on natural and technical removal), then the model as a
   flowchart, click by click: weather per place -> energy per tonne; electricity mix per region and year;
   time-explicit LCA -> net share per cell and year; the computing setup at the foot.
2. "Optimierung von DAC": the gap of the area slide again, then: the dynamic LCA model goes into an optimisation
   (where and when DAC, as few plants as possible), then the constraints.
3. "DAC-Ausbau nach Ort und Zeit": stacked capacity per country over time, the map of 2100, the warming above 1.5 C.

The process slide, the net-share map, the old result film and the target-year slide go to the backup.
Data: data/dac/optim.json, docs/slides/chart_data/luecke.json.
"""

import json
import re
from pathlib import Path

import dacfilm
from dacopt_v1 import _de

REPO = Path(__file__).resolve().parents[2]
TO_BACKUP = ["Sorbens-DAC: Prozess und Energiebedarf", "Netto-Entnahme von DAC", "DAC-Ausbau nach Ort und Zeit", "Strommix und Zieljahr"]


def _sec(page, title):
    m = re.search(r'<section class="slide[^"]*"(?: data-ch="[^"]*")? data-title="' + re.escape(title) + r'">.*?</section>\n', page, flags=re.S)
    assert m, title
    return m


def _rep(s, old, new):
    assert s.count(old) == 1, old[:90]
    return s.replace(old, new)


# ---------------------------------------------------------------- slide 1: the model
def _machine(page) -> str:
    """The DAC plant of the backup slide, without its text column, moved to the left of the flowchart."""
    s = _sec(page, "Wozu technische CO₂-Entnahme?").group(0)
    g = re.search(r'<!-- the machine: built, powered, complicated -->\s*<g class="pop" data-step="1">(.*?)\n          <text x="1168"', s, flags=re.S).group(1)
    co2 = "".join(f'<circle cx="{x}" cy="{y}" r="6" fill="#2e7d4f"/>' for x, y in ((716, 252), (744, 268), (770, 250)))
    flow = "".join(f'<circle cx="{x}" cy="{y}" r="5" fill="#2e7d4f"/>' for x, y in ((1030, 300), (1062, 322), (1065, 420), (1065, 446)))
    extra = (f'<path d="M690 262 H792" stroke="var(--muted)" stroke-width="3" stroke-dasharray="7 6" fill="none" marker-end="url(#ah-dk)"/>{co2}'
             f'<text x="690" y="232" font-size="19" fill="var(--muted)">Luft</text>{flow}'
             f'<ellipse cx="1065" cy="474" rx="26" ry="8" fill="#2e7d4f" opacity=".75"/>')
    return f'<g transform="translate(-612 -50) scale(.9)">{g}{extra}</g>'


def _box(x, y, w, h, title, lines, dark=False):
    fill, t1, t2 = ("var(--fjord)", "var(--paper)", "var(--fjord-soft)") if dark else ("var(--paper-deep)", "var(--ink)", "var(--muted)")
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}"' + ("" if dark else ' stroke="var(--paper-line)" stroke-width="2"') + '/>',
           f'<text x="{x + 18}" y="{y + 36}" font-size="23" font-weight="600" fill="{t1}">{title}</text>']
    for k, (txt, muted) in enumerate(lines):
        out.append(f'<text x="{x + 18}" y="{y + 68 + 27 * k}" font-size="19" fill="{t2 if muted else (t1 if dark else "var(--ink-2)")}">{txt}</text>')
    return "".join(out)


def _arrow(d):
    return f'<path class="m-flow" d="{d}" stroke="var(--muted)" stroke-width="3" fill="none" marker-end="url(#ah-dk)"/>'


def slide_model(page, n_cells: int) -> str:
    svg = f'''<svg class="schema mo" data-export="s_dac_modell" viewBox="0 0 1424 560" style="width:100%; flex:1; min-height:0" aria-label="DAC-Anlage; Rechenweg: Wetter je Ort ergibt den Energiebedarf je Tonne, der Strommix je Region und Jahr die Emissionen je kWh; die zeitexplizite Ökobilanz ergibt den Netto-Anteil je Zelle und Jahr">
      <defs><marker id="ah-dk" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="var(--muted)"/></marker></defs>
      <g font-family="IBM Plex Sans">
        <g class="pop" style="--d:100">{_machine(page)}
          <text x="20" y="430" font-size="21" font-weight="600" fill="var(--fjord-soft)">Sorbens-DAC</text>
          <text x="20" y="458" font-size="19" fill="var(--ink-2)">Sorbens bindet CO₂, Dampf löst es,</text>
          <text x="20" y="484" font-size="19" fill="var(--ink-2)">verdichten, im Gestein speichern</text>
        </g>
        <g class="pop" data-step="1">
          <text x="470" y="40" font-size="17" letter-spacing="1.5" fill="var(--muted)">JE ORT · 0,5°-ZELLE</text>
          {_box(470, 56, 250, 124, "Wetter", [("Temperatur, Feuchte", 0), ("CRU TS 4.09", 1)])}
          {_arrow("M724 118 H760")}
          {_box(768, 56, 280, 124, "Energie je Tonne", [("1,1 bis 1,9 MWh Strom", 0), ("Prozessmodell, Sendi 2022", 1)])}
        </g>
        <g class="pop" data-step="2">
          <text x="470" y="250" font-size="17" letter-spacing="1.5" fill="var(--muted)">JE JAHR · 2026–2100</text>
          {_box(470, 266, 250, 124, "Strommix", [("je Region und Jahr", 0), ("REMIND-EU über premise", 1)])}
        </g>
        <g class="pop" data-step="3">
          {_arrow("M724 328 H760")}
          {_arrow("M908 184 V258")}
          {_box(768, 266, 280, 124, "Zeitexplizite Ökobilanz", [("Strom je t × Mix des Jahres", 0), ("+ Anlage, Sorbens, Lager", 1)])}
          {_arrow("M1052 328 H1084")}
          {_box(1092, 250, 332, 156, "Netto-Anteil η", [("je Zelle und Jahr", 0), ("η = 1 − Emissionen je t", 0), ("Median: 46 % 2026, 91 % 2040", 1)], dark=True)}
        </g>
        <g class="pop" data-step="4">
          <rect x="0" y="508" width="1424" height="52" rx="10" fill="var(--paper-deep)"/>
          <text x="20" y="541" font-size="19" font-weight="600" fill="var(--ink)">Rechensetup</text>
          <text x="160" y="541" font-size="19" fill="var(--ink-2)">Brightway + premise · ecoinvent 3.12 · REMIND-EU SSP2-NDC, 6 Stützjahre · {_de(n_cells)} Zellen × 75 Jahre · Jacobi-GMRES</text>
        </g>
      </g>
    </svg>'''
    return f'''<section class="slide" data-ch="dac" data-title="DAC-Modell">
  <header class="sh"><h2>DAC-Modell: je Ort und je Jahr</h2></header>
  <div class="body">
    {svg}
  </div>
  <p class="src">Prozess: Sorbens-DAC mit dampfunterstützter Temperatur-Vakuum-Wechseladsorption (Sendi et al. 2022), Wärme aus Wärmepumpe. Klima: CRU TS 4.09 (Harris et al. 2020), Mittel 2011–2020. Strommix: Modellergebnis REMIND-EU, SSP2-NDC, über premise (Sacchi et al. 2022) mit ecoinvent 3.12. GWP100 nach IPCC 2021.</p>
  <aside class="notes" data-n="0">
    <p>Die Maschine: Gebläse drücken Luft durch ein Sorbens, ein Amin, an dem das CO₂ haften bleibt. Dann wird die Kammer geschlossen, Dampf um 100 °C löst das CO₂ wieder ab; es wird verdichtet und in tiefe Gesteinsschichten gepresst. Mit Wärmepumpe braucht das rund 1,5 Megawattstunden Strom je Tonne.</p>
    <p>Klick: Wie viel genau, hängt vom Ort ab. Aus dem Wetter jeder Zelle, Temperatur und Feuchte, rechnet das Prozessmodell den Energiebedarf: 1,1 bis 1,9 MWh. Kalte Luft drückt die Wärmepumpe, feuchte Luft kostet Wärme, weil Wasser mitadsorbiert wird.</p>
    <p>Klick: Und vom Jahr. Woher der Strom kommt, ändert sich: Strommix je Region und Jahr aus REMIND-EU, über premise in ecoinvent eingebaut.</p>
    <p>Klick: Beides zusammen in einer zeitexpliziten Ökobilanz: Strom je Tonne mal Emissionen je kWh im jeweiligen Jahr, dazu Anlage, Sorbens und Lager. Was von einer entnommenen Tonne netto bleibt, ist der Netto-Anteil, je Zelle und Jahr: im Median 46 % heute, 91 % 2040, wenn der Strom sauberer wird.</p>
    <p>Klick: Gerechnet mit Brightway und premise: ecoinvent 3.12 mit REMIND-EU-Strompfaden, sechs Stützjahre, dazwischen interpoliert; {_de(n_cells)} Landzellen mal 75 Jahre. Die Ökobilanzen löst ein iterativer Löser mit Warmstart, rund 80-mal schneller als der direkte.</p>
    <p class="q">Falls Fragen kommen — Ausschluss: Zellen mit kältestem Monat unter −15 °C (borealer Gürtel), wie bei Sendi et al. Niveau aus premise (0,5 MWh Strom + 1,5 MWh Wärme je t), nur die Klimaabhängigkeit aus Sendi. Prozessfolie und Karte des Netto-Anteils im Anhang.</p>
  </aside>
</section>
'''


# ---------------------------------------------------------------- slide 2: gap -> optimisation -> constraints
OPT_CSS = """
.opt2 { display: grid; grid-template-columns: 640px 1fr; gap: 40px; flex: 1; min-height: 0; }
.opt2 > .chart { height: 100%; min-height: 0; }
.opt2 .right { display: flex; flex-direction: column; gap: 22px; min-width: 0; }
.opt2 .bridge { font: 400 24px/1.4 var(--sans); color: var(--ink); margin: 6px 0 0; }
.opt2 .bridge b { color: #6b4410; font-weight: 600; }
.opt2 .chips { display: flex; align-items: center; gap: 12px; font: 600 19px/1 var(--sans); color: var(--ink); }
.opt2 .chips span { padding: 10px 14px; border-radius: 10px; background: var(--paper-deep); border: 2px solid var(--paper-line); }
.opt2 .chips span.hot { background: #9a6516; border-color: #9a6516; color: var(--paper); }
.opt2 .chips i { font-style: normal; color: var(--muted); }
.opt2 .inputs { grid-template-columns: 1fr 1fr; gap: 20px 24px; }
.opt2 .inp .v { font-size: 40px; }
"""


def slide_opt(goal: float) -> str:
    cards = [("η(Ort, Jahr)", "Netto-Anteil", "aus dem DAC-Modell", "vorige Folie"),
             ("1 460 <small>Gt</small>", "Speicher je Land", "sicher nutzbar weltweit; Deutschland 1,3 Gt", "Gidden et al. 2025, Nature"),
             ("≤ 20 <small>% pro Jahr</small>", "Hochlauf", "ab 8,8 Mt/a (2030), so schnell wie einst die Windkraft", "Zurbriggen et al. 2026, Nat. Commun."),
             ("bis 2100", "Anlagen laufen weiter", "einmal gebaut, bleibt eine Anlage in Betrieb", "Annahme")]
    inputs = "".join(f'<div class="inp rise" data-step="2" style="--d:{150 + 250 * k}"><div class="v">{v}</div><h4>{h}</h4><p>{p}</p><span class="q">{q}</span></div>'
                     for k, (v, h, p, q) in enumerate(cards))
    return f'''<section class="slide" data-ch="dac" data-title="Optimierung von DAC">
  <header class="sh"><h2>Die Lücke schließen: wo und wann DAC?</h2></header>
  <div class="body">
    <div class="opt2">
      <div class="chart" data-ec="lueckeend" data-label="Kühlung der Erde 2026 bis 2100 durch die Bäume und die Kühlung, die für 1,5 °C 2100 nötig wäre"></div>
      <div class="right">
        <p class="bridge rise" data-step="1">Das dynamische LCA-Modell geht in ein Optimierungsproblem: <b>wo und wann</b> DAC gebaut wird, damit bis 2100 netto {_de(goal)} Gt CO₂ entnommen sind, mit möglichst wenig Anlagen.</p>
        <div class="chips rise" data-step="1" style="--d:300"><span>DAC-Modell</span><i>→</i><span class="hot">Optimierung</span><i>→</i><span>Ausbau je Land und Jahr</span></div>
        <div class="inputs">{inputs}</div>
      </div>
    </div>
  </div>
  <p class="src">Lineares Programm, eigene Rechnung: Netto-Entnahme bis 2100 ≥ Vorgabe; kleinste Kapazität (größte Jahresentnahme), dann kleinste Gesamtmenge; Variablen: Kapazität je Land und Jahr. Netto-Anteil: beste 10 % der Zellen je Land mit Sedimentbecken in höchstens 100 km. Klimaantwort: FaIR, wie bei den Bäumen.</p>
  <aside class="notes" data-n="0">
    <p>Zur Erinnerung die Lücke: Mit den Bäumen auf allen kühlenden Flächen fehlen 2100 noch 87 Millikelvin bis 1,5 °C. Mit derselben Klimaantwort wie beim Baum heißt das: Es müssten bis 2100 zusätzlich netto {_de(goal)} Gigatonnen CO₂ entnommen werden.</p>
    <p>Klick: Das dynamische LCA-Modell von eben geht jetzt in ein Optimierungsproblem. Gesucht ist, wo und wann DAC gebaut wird, sodass bis 2100 genug netto entnommen ist — mit möglichst wenig Anlagen.</p>
    <p>Klick: Die Rahmenbedingungen. Der Netto-Anteil je Ort und Jahr aus dem Modell. Wie viel CO₂ jedes Land sicher speichern kann, nach Gidden et al. weltweit 1 460 Gigatonnen, Deutschland nur 1,3. Wie schnell DAC hochlaufen kann: höchstens 20 Prozent im Jahr, wie einst die Windkraft, ausgehend von den 8,8 Megatonnen, die für 2030 geplant sind. Und gebaute Anlagen laufen weiter.</p>
    <p class="q">Falls Fragen kommen — Ein lineares Programm: Kapazität je Land und Jahr als Variablen, Netto-Entnahme bis 2100 als Vorgabe. Die Umrechnung von Millikelvin in Gigatonnen nutzt die Klimaantwort aus FaIR, linear je Tonne; mit vollem FaIR nachgerechnet kühlt der Pfad um 7,7 % stärker, die Rechnung ist also konservativ. DAC kommt zusätzlich zu den 335 Gt Entnahme, die in Very Low schon stecken. Kein Transport über Landesgrenzen; Basalt-Mineralisierung (Island) ist bei Gidden nicht enthalten. Ein früheres Zieljahr braucht deutlich mehr Anlagen (2085: 12,9 statt 6,9 Gt/a; Anhang), der Strommix ändert kaum etwas.</p>
  </aside>
</section>
'''


# ---------------------------------------------------------------- slide 3: result (dacfilm.py)
GAP_END_JS = "const EC_GAP_END = { steps: 0, option() { return EC_GAP.option(EC_GAP.steps); } };\n"


# ---------------------------------------------------------------- patch
def patch(page: str) -> str:
    from nbs.dac import dac_possible

    res = json.loads((REPO / "data/dac/optim.json").read_text())
    gap = json.loads((REPO / "docs/slides/chart_data/luecke.json").read_text())
    head, sep, tail = page.partition("</style>")
    film_css, film_js, film_html = dacfilm.slide()
    page = head + OPT_CSS + film_css + sep + tail
    m = re.search(r"const EC_CHARTS = \{([^}]*)\};", page)
    page = (page[: m.start()] + GAP_END_JS + "const EC_CHARTS = {" + m.group(1).rstrip() + ", lueckeend: EC_GAP_END };" + page[m.end():])
    # the film runs once the page is there (after the deck script)
    page = _rep(page, "</body>", "<script>" + film_js + "</script>\n</body>")

    # old slides to the backup, notes without a number
    moved = []
    for t in TO_BACKUP:
        m = _sec(page, t)
        moved.append(re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', m.group(0)))
        page = page[: m.start()] + page[m.end():]
    page = _rep(page, "<!-- BACKUP:BEGIN -->\n", "<!-- BACKUP:BEGIN -->\n" + "".join(moved))

    # new model, optimisation and result slides in place of the old model and optimisation slides
    m = _sec(page, "DAC-Modell")
    page = page[: m.start()] + slide_model(page, int(dac_possible().sum())) + page[m.end():]
    m = _sec(page, "Optimierung von DAC")
    page = page[: m.start()] + slide_opt(res["haupt"]["co2_ziel_gt"]) + film_html + page[m.end():]

    k = iter(range(1, 1000))
    page = re.sub(r'<aside class="notes" data-n="\d+">', lambda _: f'<aside class="notes" data-n="{next(k)}">', page)
    return page
