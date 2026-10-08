"""Horizon 2100 in both decks (2026-10-06): every result is evaluated in 2100, the year
until which warming should stay low; the CMIP7 lines on slides 2-3 still run to 2150
with the 2100 marker, their sums run 2024-2100.

* pptx: the sum chart on slide 3 (native, 2024-2100), the slide texts and notes,
  the charts of the Bäume, Klima and Vergleich chapters as SVG from the HTML deck,
  and a new slide "Zeit zählt" (DAC removes at once, the tree only as it grows)
  after "Die Maschine wird zur Messlatte".
* HTML: the same texts in the main part; the new slide.

The numbers come from docs/slides/chart_data/fakten.json and the model (nbs). Run after
scripts/export_slide_facts.py, scripts/export_html_v2.py --charts and
scripts/export_deck_svgs.mjs; then scripts/build_consistent_numbers.py and
scripts/export_html_v2.py --backup. Snapshot to docs/slides/workspace/ first.

    uv run python scripts/build_horizon_2100.py
"""

from __future__ import annotations

import html
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_cmip7_slides as CM  # noqa: E402
import build_dac_slides as DS  # noqa: E402
import build_map_slides as B  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
HTML = REPO / "docs" / "slides" / "html" / "dissvortrag_v2.html"
F = json.loads((REPO / "docs" / "slides" / "chart_data" / "fakten.json").read_text())


def de(x: float, nd: int = 0) -> str:
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def pct(x: float, nd: int = 0) -> str:
    return de(100 * x, nd) + " %"


def model_numbers() -> dict:
    import numpy as np

    from nbs import dac_figures as Df
    from nbs import map_fields as M
    from nbs import vergleich_figures as Vf
    from nbs.cmip7_figures import cumulative_removal, facts
    from nbs.dac import dac_possible
    from nbs.storyline_figures import TROPICAL_SITE as BELEM, uptake_share_by_2100
    from nbs.animations import SITES

    sw, w = Df.switch_year_grid(), Df.plantable_area_m2()
    c = Df.switch_categories(sw, w)
    t = w[w > 0].sum()
    eff = Vf.tree_efficiency_grid(2025)
    ok = dac_possible()
    p = w > 0
    cool = p & (eff > 0)
    share = uptake_share_by_2100(SITES[0])
    return {
        "map": M.facts(), "cum": cumulative_removal(), "cmip": facts(),
        "fe": {k: float(w[m].sum() / t) for k, m in
               [("beides", cool & ok), ("baum", cool & ~ok), ("dac", p & ~cool & ok), ("keins", p & ~cool & ~ok)]},
        "sw": {"dac": float(w[c == 0].sum() / t), "baum": float(w[c == 1].sum() / t), "jahr": int(np.median(sw[c == 0]))},
        "z1": {y: float(share[y - 2025]) for y in (2035, 2050)},
        "belem_kg": float(np.cumsum(__import__("nbs.storyline_figures", fromlist=["_annual_uptake"])._annual_uptake(BELEM))[-1]),
    }


N = model_numbers()
O, V, K = F["orte"], F["vergleich"], F["kaskade"]
TREE = F["baeume"]["orte"]
CUM = N["cum"]
VL = float(CUM.loc["VL", "gesamt_gt"])
COOL = N["map"]["kuehlt_gha"]
LA = [round(-x * 1e15) for x in O["Aachen"]["leiter_dt_2150_K"]]
LJ = [round(-x * 1e15) for x in O["Joensuu"]["leiter_dt_2150_K"]]
A_KG, J_KG = TREE["Aachen"]["aufnahme_2150_kg_co2"], TREE["Joensuu"]["aufnahme_2150_kg_co2"]
A_DT, J_DT = N["map"]["orte"]["Aachen"], N["map"]["orte"]["Joensuu"]
TREES = VL / (A_KG / 1000) / 1000  # Billionen (1e12) trees
FE, SW = N["fe"], N["sw"]
cross = [o["umstieg"] for o in V["orte"].values() if o["umstieg"]]

# (old, new): texts on the slides and in the notes (pptx), and in the HTML main part
PAIRS = [
    # slide 5, naive calculation
    ("bindet bis zur Sättigung rund 180 kg CO₂ (49 kg Kohlenstoff).",
     f"bindet bis 2100 rund {de(A_KG)} kg CO₂ ({de(A_KG * 12 / 44)} kg Kohlenstoff)."),
    ("bindet bis zur Sättigung rund <strong>180 kg CO₂</strong> (49 kg Kohlenstoff).",
     f"bindet bis 2100 rund <strong>{de(A_KG)} kg CO₂</strong> ({de(A_KG * 12 / 44)} kg Kohlenstoff)."),
    ("Gebraucht werden bis 2150 591 Gt CO₂ Entnahme", f"Gebraucht werden bis 2100 {de(VL)} Gt CO₂ Entnahme"),
    ("werden bis 2150 <strong>591 Gt CO₂</strong> Entnahme", f"werden bis 2100 <strong>{de(VL)} Gt CO₂</strong> Entnahme"),
    ("591 Gt ÷ 0,18 t  ≈  3,3 Billionen Bäume — mehr, als heute auf der Erde stehen.",
     f"{de(VL)} Gt ÷ {de(A_KG / 1000, 3)} t  ≈  {de(TREES, 1)} Billionen Bäume — zwei Drittel aller Bäume, "
     "die heute auf der Erde stehen."),
    ('591 Gt ÷ 0,18 t ≈ <span class="count" data-to="3.3" data-dec="1" data-delay="200">3,3</span> Billionen Bäume',
     f'{de(VL)} Gt ÷ {de(A_KG / 1000, 3)} t ≈ <span class="count" data-to="{TREES:.1f}" data-dec="1" data-delay="200">'
     f'{de(TREES, 1)}</span> Billionen Bäume'),
    ("— mehr, als heute auf der Erde stehen.", "— zwei Drittel aller Bäume, die heute auf der Erde stehen."),
    ("(CMIP7 Very Low, 591 Gt bis 2150, aus den Originaldaten wie im ganzen Vortrag",
     f"(CMIP7 Very Low, {de(VL)} Gt bis 2100, aus den Originaldaten wie im ganzen Vortrag"),
    ("Zahl = Modellbaum in Aachen:", "Zahl = Modellbaum in Aachen, Aufnahme 2025–2100 (bis zur Sättigung wären es 180 kg):"),
    # slide 15
    ("bis 2150 in Aachen rund 176 kg CO₂ aus der Luft, in Joensuu (Ostfinnland) rund 119 kg",
     f"bis 2100 in Aachen rund {de(A_KG)} kg CO₂ aus der Luft, in Joensuu (Ostfinnland) rund {de(J_KG)} kg"),
    # slide 23
    ("über alle Jahre bis 2150 weniger als die Hälfte.", "über alle Jahre bis 2100 gut die Hälfte."),
    # slide 24
    ("1,65 → 1,32·10⁻¹⁵ W/m² je kg bis 2150", f"1,65 → {de(F['a_co2']['ende'], 2)}·10⁻¹⁵ W/m² je kg bis 2100"),
    # slide 25
    ("in Joensuu aber 2150 nur mit 26 % der Kühlung von Aachen.",
     f"in Joensuu aber 2100 nur mit {pct(J_DT / A_DT)} der Kühlung von Aachen."),
    ("bis 2150 etwa −3·10⁻¹⁴ K je Baum in Aachen, −9·10⁻¹⁵ K in Joensuu",
     f"bis 2100 etwa −{de(-A_DT / 10, 1)}·10⁻¹⁴ K je Baum in Aachen, −{de(-J_DT / 10, 1)}·10⁻¹⁴ K in Joensuu"),
    # slide 26
    ("Unterm Strich kühlt der Wald dadurch 2150 sogar etwas mehr. Ein später gepflanzter Baum kühlt 2150 gleich viel "
     "oder mehr: Von seinem CO₂ ist noch wenig zurückgeflossen, und sein Kronendach ist noch nicht ganz geschlossen.",
     "Unterm Strich kühlt der Wald dadurch 2100 sogar etwas mehr. Ein später gepflanzter Baum kühlt bis 2100 "
     f"deutlich weniger, ihm bleibt weniger Zeit: 2085 gepflanzt in Aachen nur noch {pct(O['Aachen']['anteil_pflanzjahr_2085'])}."),
    # slide 27
    ("in Aachen von 186 auf 35", f"in Aachen von {LA[0]} auf {LA[-1]}"),
    ("In Joensuu bleiben von 126 nur 9.", f"In Joensuu bleiben von {LJ[0]} nur {LJ[-1]}."),
    ("Aachen: -186 → -159 → -56 → -32 → -35; Joensuu: -126 → -91 → -21 → -4 → -9",
     "Aachen: " + " → ".join(f"-{v}" for v in LA) + "; Joensuu: " + " → ".join(f"-{v}" for v in LJ)),
    # slide 28
    ("Aachen (−35) und Joensuu (−9 · 10⁻¹⁵ K)", f"Aachen (−{de(-A_DT)}) und Joensuu (−{de(-J_DT)} · 10⁻¹⁵ K)"),
    ("5 % der wiederbewaldbaren Fläche kühlen stärker als −82, 5 % wärmen stärker als +33 · 10⁻¹⁵ K.",
     f"5 % der wiederbewaldbaren Fläche kühlen stärker als −{de(-N['map']['p05'])}, 5 % wärmen stärker als "
     f"+{de(N['map']['p95'])} · 10⁻¹⁵ K."),
    ("Ein Baum des typischen Waldes kühlt auf 44 % der wiederbewaldbaren Fläche (0,36 Gha)",
     f"Ein Baum des typischen Waldes kühlt auf {pct(N['map']['kuehlt_anteil'])} der wiederbewaldbaren Fläche "
     f"({de(COOL, 2)} Gha)"),
    # slide 30
    ("Von den 0,83 Gha bleiben 0,36 Gha, auf denen ein 2025 gepflanzter Baum bis 2150 kühlt.",
     f"Von den 0,83 Gha bleiben {de(COOL, 2)} Gha, auf denen ein 2025 gepflanzter Baum bis 2100 kühlt."),
    # slide 32
    ("Bäume brutto 95 Gt CO₂ = Kaskade (25,9 GtC × 44/12).",
     f"Bäume brutto {de(V['baeume_brutto_gtco2'])} Gt CO₂ = Kaskade ({de(K['kohlenstoff_gtc'], 1)} GtC × 44/12)."),
    ("Gegen den Landanteil des VL-Szenarios (341 Gt) sind es 15 %. Bedarf aus den CMIP7-Daten wie auf Folie 3 "
     "(Very Low 591 Gt, davon 249 neuartig).",
     f"Gegen den Landanteil des VL-Szenarios ({de(V['vl_land_gtco2'])} Gt) sind es "
     f"{pct(V['baeume_netto_gtco2'] / V['vl_land_gtco2'])}. Bedarf aus den CMIP7-Daten wie auf Folie 3 "
     f"(Very Low {de(VL)} Gt bis 2100, davon {de(V['vl_technisch_gtco2'])} neuartig)."),
    # slide 36
    ("beides 37 %, nur Baum 7 %, nur DAC 23 %, keins 33 %",
     f"beides {pct(FE['beides'])}, nur Baum {pct(FE['baum'])}, nur DAC {pct(FE['dac'])}, keins {pct(FE['keins'])}"),
    # slide 39
    ("Die Karte färbt nur, wo beides geht (37 % der bepflanzbaren Fläche): blau bis ocker = ab diesem Jahr entnimmt DAC "
     "sauberer als der Baum (35 %, im Mittel 2030), grün = der Baum bleibt bis 2100 besser (1,5 %).",
     f"Die Karte färbt nur, wo beides geht ({pct(FE['beides'])} der bepflanzbaren Fläche): blau bis ocker = ab diesem "
     f"Jahr entnimmt DAC sauberer als der Baum ({pct(SW['dac'])}, im Mittel {SW['jahr']}), grün = der Baum bleibt "
     f"besser, wenn bis 2070 gepflanzt wird ({pct(SW['baum'], 1)}). Gepflanzt wird nur bis 2070, damit jeder Baum bis "
     "2100 mindestens 30 Jahre wächst; ein später gepflanzter Baum sähe je Tonne nur deshalb gut aus, weil er noch "
     "jung ist."),
    # slides 41, 42
    ("netto rund 52 Gt CO₂ bis 2150 — 9 % des niedrigsten Szenarios.",
     f"netto rund {de(V['baeume_netto_gtco2'])} Gt CO₂ bis 2100 — {pct(V['baeume_netto_gtco2'] / VL)} des niedrigsten "
     "Szenarios."),
    ("Netto rund 52 Gt CO₂ bis 2150 — 9 % dessen,",
     f"Netto rund {de(V['baeume_netto_gtco2'])} Gt CO₂ bis 2100 — {pct(V['baeume_netto_gtco2'] / VL)} dessen,"),
    ("Bis 2150 kühlen 0,36 der 0,83 Gha", f"Bis 2100 kühlen {de(COOL, 2)} der 0,83 Gha"),
    ("zwischen 2020 und 2041", f"zwischen 2020 und {max(cross)}"),
]

SLIDE3_TAKE = (f"Wer 1,5 °C nahekommt, rechnet mit großer CO₂-Entnahme: Very Low mit rund {de(VL)} Gt bis 2100, "
               f"Low und Low-to-Negative mit {de(CUM.loc['L', 'gesamt_gt'])} und {de(CUM.loc['LN', 'gesamt_gt'])} Gt. "
               f"Die Szenarien ohne Entnahme (Medium, High) liegen 2100 bei {de(N['cmip']['M']['k_2100'], 1)} und "
               f"{de(N['cmip']['H']['k_2100'], 1)} °C.")
SLIDE3_SRC = ("Modellergebnis: CMIP7-Markerszenarien (van Vuuren et al. 2026; Daten: Zenodo 20713982), Linien mit "
              "Fortschreibung bis 2150, Summen 2024–2100. Neuartig = BECCS, Direct Air Capture, Gesteinsverwitterung, "
              "Ozean; Land = Nettosenke der Landnutzung. Carbon Brief zählt bis 2150 und mit Bodenkohlenstoff "
              "(Very Low: 655 Gt).")
cum_txt = ", ".join(f"{k} {de(CUM.loc[k, 'neuartig_gt'])} + {de(CUM.loc[k, 'land_gt'])}" for k in ("VL", "L", "ML", "LN", "HL"))
SLIDE3_NOTES = (
    "Sprechertext: Und selbst in die Nähe von 1,5 °C kommen die Szenarien nur, weil sie annehmen, dass wir CO₂ wieder "
    "aus der Luft holen. Links pro Jahr: im Very-Low-Szenario rund 5 bis 6 Gigatonnen jährlich, in Low-to-Negative bis "
    "zu 30. Rechts aufsummiert bis 2100 — bis dahin soll die Erwärmung klein bleiben, und bis dahin rechnet der ganze "
    "Vortrag. Das ist der Bedarf, gegen den er am Ende rechnet.\n\n"
    "Falls Fragen kommen\n"
    f"Kumuliert 2024–2100 (neuartig + Land): {cum_txt} Gt CO₂. Carbon Brief zählt bis 2150 und mit Bodenkohlenstoff "
    f"und kommt für Very Low auf 655 Gt. Alle Folien rechnen mit diesen Daten bis 2100 (Very Low {de(VL)} Gt).")

Z1 = dict(
    title="Zeit zählt: DAC wirkt sofort, der Baum wächst erst",
    key="hex_z1",
    takeaway=(f"Ein 2025 gepflanzter Baum hat bis 2035 erst {pct(N['z1'][2035])} und bis 2050 {pct(N['z1'][2050])} "
              "dessen entnommen, was er bis 2100 schafft. DAC entnimmt jede Tonne in dem Jahr, in dem die Anlage läuft. "
              "Für schnelles Gegensteuern ist der Baum langsam — wertvoll bleibt er trotzdem: Er braucht keinen Strom "
              f"und kühlt bis 2100 auf {de(COOL, 2)} Gha mit."),
    source=("Eigene Rechnung: Wachstumskurve je Ort (Kohlenstoff: Walker et al. 2022; Tempo: Cook-Patton et al. 2020), "
            "Störung bei heutiger Rate; Baum gepflanzt 2025, Anteil der bis 2100 entnommenen Menge."),
    notes=("Sprechertext: Ein Punkt, den die Wirkungsgrade je Tonne verdecken: die Zeit. Wir bewerten 2100 — bis dahin "
           "soll die Erwärmung klein bleiben. Eine Tonne, die DAC heute entnimmt, fehlt der Luft ab heute. Ein Baum, "
           f"den wir heute pflanzen, braucht Jahrzehnte: Bis 2035 hat er erst {pct(N['z1'][2035])} seiner Entnahme bis "
           f"2100 geschafft, bis 2050 {pct(N['z1'][2050])}. Das gilt in Aachen, in Joensuu und in den Tropen gleich: "
           "Überall braucht der Wald rund 25 Jahre bis zur Hälfte. Für schnelles Gegensteuern bis zur Jahrhundertmitte "
           "ist der Baum also langsam. Wertvoll bleibt er trotzdem: kein Strom, keine Anlage, und wo er kühlt, kühlt er "
           "bis 2100 mit. Deshalb heißt die Reihenfolge: Bäume jetzt pflanzen — gerade weil sie langsam sind.\n\n"
           "Falls Fragen kommen\n"
           "Kurve = kumulierte Netto-Aufnahme je Baum (Wachstum mit Störung bei heutiger Rate), geteilt durch die Menge "
           f"bis 2100: Aachen {de(A_KG)} kg, Joensuu {de(J_KG)} kg, Belém {de(N['belem_kg'])} kg CO₂. Der Wirkungsgrad je "
           "Tonne auf den Vorfolien sagt nichts über das Tempo; dort zählt nur, welcher Anteil einer entnommenen Tonne "
           "netto bleibt."),
)

# charts drawn in the HTML deck, into the pptx as SVG: title -> key
CHARTS = {
    "C-Aufnahme über die Zeit im Modell": "s12",
    "Was der Baum der Luft entnimmt": "b6",
    "Was der Baum mit seiner Umgebung tauscht": "b9",
    "Gemeinsame Währung: Energie": "b10",
    "Was der Luft wirklich fehlt": "k5",
    "Kohlenstoff und Licht in einer Währung": "k10",
    "Die Erde erwärmt sich träge": "k12b",
    "Die Erwärmung wirkt auf den Baum zurück": "k13",
    "Was jede Erweiterung der Systemgrenze kostet": "k14",
    "Einordnung: andere Studien": "v1b",
}


def replace_in_tf(tf, pairs) -> None:
    for p in tf.paragraphs:
        t = "".join(r.text for r in p.runs)
        n = t
        for old, new in pairs:
            n = n.replace(old, new)
        if n != t and p.runs:
            p.runs[0].text = n
            for r in p.runs[1:]:
                r.text = ""


def chart_frame(slide):
    """Position of the old chart (picture or native chart), to put the SVG in the same place."""
    for s in slide.shapes:
        if s.shape_type == 13 or getattr(s, "has_chart", False):
            return s
    return None


def pptx() -> None:
    prs = Presentation(str(B.DECK))
    slides = list(prs.slides)
    # slide 3: sums 2024-2100 (native bar chart), texts
    s3 = slides[2]
    bars = [s for s in s3.shapes if getattr(s, "has_chart", False) and "Summe" in (s.chart.chart_title.text_frame.text
                                                                                   if s.chart.has_title else "")]
    if bars:
        old = bars[0]
        right = CM.N.Frame(old.left, old.top, old.width, old.height)
        old._element.getparent().remove(old._element)
        CM.sum_chart(s3, right, next(s for s in s3.shapes if s.name == "Kurz gesagt")._element)
    B.set_box(next(s for s in s3.shapes if s.name == "Kurz gesagt"), "Kurz gesagt", SLIDE3_TAKE)
    B.set_box(next(s for s in s3.shapes if s.name == "Quelle"), None, SLIDE3_SRC)
    s3.notes_slide.notes_text_frame.text = SLIDE3_NOTES

    pairs = PAIRS + [("2150", "2100")]
    for no, slide in enumerate(slides, 1):
        if no < 4 or no > 43:
            continue
        for sh in slide.shapes:
            if sh.has_text_frame:
                replace_in_tf(sh.text_frame, pairs)
        if slide.has_notes_slide:
            t = slide.notes_slide.notes_text_frame.text
            n = t
            for old, new in pairs:
                n = n.replace(old, new)
            if n != t:
                slide.notes_slide.notes_text_frame.text = n

    # charts as SVG from the HTML deck
    for title, key in CHARTS.items():
        slide = B.by_title(prs, title)
        old = chart_frame(slide)
        if old is None:
            print("  ! kein Diagramm auf", title)
            continue
        frame = (old.left / 914400, old.top / 914400, old.width / 914400, old.height / 914400)
        rids = [e.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed") for e in old._element.iter()]
        old._element.getparent().remove(old._element)
        for rid in filter(None, rids):
            if not slide._element.xpath(f'.//*[@r:embed="{rid}"]'):
                slide.part.drop_rel(rid)
        B.svg_picture(slide, key, frame)
        pic = slide.shapes[-1]
        tree = slide.shapes._spTree
        tree.remove(pic._element)
        tree.insert(2, pic._element)
        print(f"{title}: hex_{key}")

    # new slide "Zeit zählt"
    titles = [s.shapes.title.text for s in prs.slides if s.shapes.title is not None]
    if Z1["title"] not in titles:
        ref = B.by_title(prs, "Die Maschine wird zur Messlatte")
        DS.fill(B.new_slide_after(prs, ref, Z1["title"]), Z1, B.FRAME)
    prs.save(str(B.DECK))


def html_deck() -> None:
    s = HTML.read_text(encoding="utf-8")
    a = s.index('data-title="Wozu eine Maschine?"')
    b = s.index("<!-- BACKUP:BEGIN -->")
    main = s[a:b]
    for old, new in PAIRS + [("2150", "2100")]:
        main = main.replace(old, new)
    s = s[:a] + main + s[b:]
    # slide 3 takeaway
    i = s.index('data-title="CMIP7: CO₂-Entnahme"')
    j = s.index("</section>", i)
    sec = s[i:j]
    import re
    sec = re.sub(r'(<p class="takeaway"[^>]*>).*?(</p>)', lambda m: m.group(1) + html.escape(SLIDE3_TAKE, quote=False) + m.group(2), sec, count=1, flags=re.S)
    sec = re.sub(r'(<p class="src">).*?(</p>)', lambda m: m.group(1) + html.escape(SLIDE3_SRC, quote=False) + m.group(2), sec, count=1, flags=re.S)
    s = s[:i] + sec + s[j:]
    # new slide after "Die Maschine wird zur Messlatte"
    if 'data-title="Zeit zählt"' not in s:
        i = s.index('data-title="Die Maschine wird zur Messlatte"')
        j = s.index("</section>", i) + len("</section>")
        new = (f'\n\n<section class="slide" data-ch="vergleich" data-title="Zeit zählt">\n'
               f'  <header class="sh"><h2>{html.escape(Z1["title"])}</h2></header>\n'
               '  <div class="body">\n'
               '    <div class="chart" data-chart="z1" data-label="Anteil der Entnahme bis 2100, den ein 2025 gepflanzter '
               'Baum schon geschafft hat, gegen DAC"></div>\n'
               f'    <div class="foot"><div></div><p class="takeaway" data-step="1" style="--d:0">'
               f'{html.escape(Z1["takeaway"], quote=False)}</p></div>\n'
               '  </div>\n'
               f'  <p class="src">{html.escape(Z1["source"], quote=False)}</p>\n'
               '  <aside class="notes" data-n="0"></aside>\n</section>')
        s = s[:j] + new + s[j:]
    HTML.write_text(s, encoding="utf-8")


def main() -> None:
    if any(p.name.startswith("~$") for p in B.DECK.parent.iterdir()):
        sys.exit("Deck ist in PowerPoint geöffnet (~$-Datei) — erst schließen.")
    B.WORKSPACE.mkdir(exist_ok=True)
    shutil.copy2(B.DECK, B.WORKSPACE / f"dissvortrag_v2_vor_horizont2100_{datetime.now():%Y%m%d_%H%M%S}.pptx")
    pptx()
    html_deck()
    print("Very Low bis 2100:", de(VL), "Gt; Bäume:", de(TREES, 1), "Billionen; kühlend:", de(COOL, 2), "Gha")


if __name__ == "__main__":
    main()
