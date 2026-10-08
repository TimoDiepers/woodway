"""One rule for every tree and one source for every demand figure, in both decks.

Rule (2026-10-06): the tree is the cell's typical forest (Hasler et al. 2024, as in the
Bäume chapter), planted 2025 unless a slide compares years; it counts where it cools by
the horizon 2100 (0.42 Gha); comparisons over time plant until 2070. Over time (slides "DAC fährt mit …" and "Messlatte") the tree is planted
in the same year in which DAC runs. Demand = the CMIP7 data of slides 2-3, summed 2024-2100 (Very Low 335 Gt).

This script writes the slide texts that follow from docs/slides/chart_data/fakten.json
into dissvortrag_v2.pptx (Kurz gesagt, Quelle, notes) and into the HTML deck (takeaway,
source line; the HTML notes come from the pptx via scripts/export_html_v2.py --backup).
Snapshot to docs/slides/workspace/ first; rerunnable.

    uv run python scripts/build_consistent_numbers.py
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from pptx import Presentation

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_map_slides as B  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
HTML = REPO / "docs" / "slides" / "html" / "dissvortrag_v2.html"
F = json.loads((REPO / "docs" / "slides" / "chart_data" / "fakten.json").read_text())


def de(x: float, nd: int = 0) -> str:
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def pct(x: float, nd: int = 0) -> str:
    return de(100 * x, nd) + " %"


V, D, K = F["vergleich"], F["dac"], F["kaskade"]
COOL = V["bepflanzbar_kuehlt_gha"]
NET, GROSS, VL = V["baeume_netto_gtco2"], V["baeume_brutto_gtco2"], V["vl_gesamt_gtco2"]
TREE_AHEAD = {y: 1 - D["dac_besser_anteil"][y] - D["keins_kuehlt_anteil"][y] for y in ("2030", "2050")}
O = V["orte"]


def feasibility():
    import numpy as np
    from nbs import vergleich_figures as Vf
    from nbs.dac import dac_possible

    w = Vf.plantable_area_m2()
    eff = Vf.tree_efficiency_grid(2025)
    ok = dac_possible()
    p = w > 0
    cool = p & (eff > 0)
    t = w[p].sum()
    return {k: float(w[m].sum() / t) for k, m in
            [("beides", cool & ok), ("baum", cool & ~ok), ("dac", p & ~cool & ok), ("keins", p & ~cool & ~ok)]}


def switch():
    import numpy as np
    from nbs import dac_figures as Df

    sw, w = Df.switch_year_grid(), Df.plantable_area_m2()
    c = Df.switch_categories(sw, w)
    t = w[w > 0].sum()
    return {"dac": float(w[c == 0].sum() / t), "baum": float(w[c == 1].sum() / t),
            "jahr": int(np.median(sw[c == 0]))}


FE, SW = feasibility(), switch()
late = sorted(((n, o["umstieg"]) for n, o in O.items() if o["umstieg"] and o["umstieg"] > 2020), key=lambda x: x[1])
early = [n for n, o in O.items() if o["umstieg"] == 2020]
never = [n for n, o in O.items() if not o["umstieg"]]

# title -> (takeaway, source or None, [(old, new) in the notes])
SLIDES = {
    "Was ein Baum wo bewirkt": (None, None, [(
        "Mit dem typischen Wald kühlt ein Baum auf 44 % der Fläche; das Kapitel Vergleich nimmt je Zelle den Waldtyp "
        "mit der stärksten Kühlung und kommt so auf 0,39 Gha.",
        f"Ein Baum des typischen Waldes kühlt auf {pct(COOL / K['flaeche_land_gha'])} der wiederbewaldbaren Fläche "
        f"({de(COOL, 2)} Gha); mit genau diesem Baum und dieser Fläche rechnet auch das Kapitel Vergleich.")]),
    "Wo Bäume hinkönnen": (
        f"Wiederbewaldbar sind {de(K['flaeche_land_gha'], 2)} Gha, rund 6 % der eisfreien Landfläche, und dünn verteilt. "
        f"Kühlen tut der Baum, 2025 gepflanzt, davon nur auf {de(COOL, 2)} Gha; der Rest liegt im Norden und im "
        "Trockenen, wo die Albedo mehr frisst, als der Baum an CO₂ bindet.", None, [
            ("Von den 0,83 Gha bleiben 0,39 Gha, auf denen er kühlt.",
             f"Von den 0,83 Gha bleiben {de(COOL, 2)} Gha, auf denen ein 2025 gepflanzter Baum bis 2100 kühlt."),
            ("Ab hier nimmt das Kapitel je Zelle den Waldtyp mit der stärksten Kühlung: 0,39 Gha kühlen (mit dem typischen "
             "Wald der Vorfolie 0,36 Gha).",
             "Baum = typischer Wald der Zelle (Hasler et al. 2024), wie in allen Kapiteln; gepflanzt 2025, bewertet 2100."),
        ]),
    "Bäume reichen nicht": (
        f"Alle Flächen, auf denen der Baum kühlt, ab 2025 bewaldet, binden bis 2100 rund {de(GROSS)} Gt CO₂, nach Albedo "
        f"netto {de(NET)} Gt — {pct(NET / VL)} dessen, was selbst das niedrigste Szenario braucht ({de(VL)} Gt). "
        "Der Rest muss technisch kommen. Die Frage ist also nicht Baum oder Maschine, sondern: welche Tonne wann und wo.",
        "Bedarf: Modellergebnis CMIP7-Szenarien (van Vuuren et al. 2026), dieselben Daten wie Folie 3. Bäume: eigene "
        f"Rechnung, typischer Wald, gepflanzt 2025, auf den {de(COOL, 2)} Gha, auf denen er bis 2100 kühlt; netto = mit Albedo.",
        [("Gegen den Landanteil des VL-Szenarios (350 Gt) sind es 15 %.",
          f"Gegen den Landanteil des VL-Szenarios ({de(V['vl_land_gtco2'])} Gt) sind es "
          f"{pct(NET / V['vl_land_gtco2'])}. Bedarf aus den CMIP7-Daten wie auf Folie 3 "
          f"(Very Low {de(VL)} Gt, davon {de(V['vl_technisch_gtco2'])} neuartig).")]),
    "Wer wo entnehmen kann": (
        "DAC kann auf rund vier Fünfteln des Landes stehen, nur nicht im hohen Norden. Der Baum, 2025 gepflanzt, kühlt "
        f"nur auf {de(COOL, 2)} Gha. Auf der wiederbewaldbaren Fläche geht auf {pct(FE['beides'])} beides, auf "
        f"{pct(FE['baum'])} nur der Baum, auf {pct(FE['dac'])} nur DAC, auf {pct(FE['keins'])} keins von beiden.",
        "Eigene Rechnung. Baum: typischer Wald je Zelle (Hasler et al. 2024), gepflanzt 2025, kühlt bis 2100 (Fläche: "
        "Walker et al. 2022). DAC: kältester Monat nicht unter −15 °C (nach Sendi et al. 2022; Klima: CRU TS 4.09). "
        "Je 2°-Block die Gruppe mit der größten Fläche.",
        [("Anteile an der wiederbewaldbaren Fläche (0,83 Gha): beides 39 %, nur Baum 8 %, nur DAC 22 %, keins 32 %. "
          "Baum = empfohlene Waldart der Zelle, gepflanzt 2025, kühlt 2100.",
          f"Anteile an der wiederbewaldbaren Fläche (0,83 Gha): beides {pct(FE['beides'])}, nur Baum {pct(FE['baum'])}, "
          f"nur DAC {pct(FE['dac'])}, keins {pct(FE['keins'])}. Baum = typischer Wald der Zelle, gepflanzt 2025, kühlt 2100.")]),
    "Heute: der Holzweg": (
        "Netto-Wirkungsgrad: welcher Anteil einer entnommenen Tonne nach den eigenen Emissionen übrig bleibt. Mit dem "
        "Strom von 2020 emittiert DAC in Krakau, Peking und Kinshasa mehr, als es entnimmt; besser als ein 2025 "
        f"gepflanzter Baum ist es nur auf {pct(V['dac_2020_besser_anteil'])} der bepflanzbaren Fläche. Heute sind "
        "die Ingenieure auf dem Holzweg.",
        "Eigene Rechnung. Baum: typischer Wald, gepflanzt 2025, 1 − Albedo-Offset 2100. DAC: Ökobilanz mit premise "
        "(Modellergebnis), Strommix 2020 der REMIND-Region, Energie nach Klima.",
        [("Ausnahmen: In Joensuu ist der finnische Strom schon heute sauber, DAC liegt dort vorn. In Peking wärmt der "
          "Baum unterm Strich; DAC emittiert dort mit Kohlestrom zwar auch netto, aber weniger.",
          "Ausnahmen: In Joensuu ist der finnische Strom schon heute sauber, DAC liegt dort vorn. In Peking wärmt der "
          "Baum unterm Strich; DAC emittiert dort mit Kohlestrom zwar auch netto, aber weniger. Marabá (südöstlicher "
          "Amazonas) steht für die Tropen mit viel Fläche zum Wiederbewalden (rund 13 % im Umkreis) und viel Sonne. "
          "Manaus liegt mitten im Wald, dort gibt es kaum Fläche."),
         ("Ausnahme Joensuu: Dort wärmt der Baum, und der finnische Strom ist schon heute sauber.",
          "Ausnahmen: In Joensuu ist der finnische Strom schon heute sauber, DAC liegt dort vorn. In Peking wärmt der "
          "Baum unterm Strich; DAC emittiert dort mit Kohlestrom zwar auch netto, aber weniger.")]),
    "DAC fährt mit der Energiewende mit": (
        "Verglichen wird Jahr für Jahr: ein Baum, der in diesem Jahr gepflanzt wird, gegen DAC mit dem Strom dieses "
        "Jahres. DAC wird ohne eigenes Zutun besser, weil der Strom sauberer wird (Szenario mit heutigen Zusagen). "
        "Der Baum wird überholt: " + ", ".join(f"{n} {y}" for n, y in late) +
        (f"; in {' und '.join(early)} ist DAC schon heute vorn" if early else "") +
        (f"; in {' und '.join(never)} bleibt der Baum vorn (Pflanzung bis 2070)." if never else "."),
        "Eigene Rechnung; Strommix je Jahr: Modellergebnis REMIND-EU, SSP2-NDC, über premise; Baum (typischer Wald) "
        "im jeweiligen Jahr gepflanzt, bewertet 2100.", []),
    "Die Maschine wird zur Messlatte": (
        "Weil wir DAC ohnehin brauchen, muss jede Baum-Tonne mindestens so gut sein wie die Maschinen-Tonne. Wo beides "
        f"geht, überholt DAC den Baum fast überall, im Mittel {SW['jahr']}. Über alle Flächen liegt der Baum 2030 auf "
        f"{pct(TREE_AHEAD['2030'])} vorn, ab 2050 nur noch auf {pct(TREE_AHEAD['2050'])} — vor allem dort, wo es für "
        "DAC zu kalt ist.",
        "Eigene Rechnung, gleiches Modell wie die Vorfolien. Karte: Jahr des Umstiegs, wo beides geht. Rechts: Anteil der "
        "bepflanzbaren Fläche je bester Option, Baum jeweils im selben Jahr gepflanzt, in dem DAC läuft.",
        [("Karte und Flächenanteile zeigen dieselben drei Gruppen. Blau bis ocker: ab diesem Jahr entnimmt DAC sauberer "
          "als der Baum (59 % der bepflanzbaren Fläche bis 2100). Grün: Der Baum bleibt bis 2100 besser (19 %), meist "
          "weil es dort für Sorbens-DAC zu kalt ist (17 %). Dunkelgrau: keins kühlt — der Baum wärmt, und für DAC ist es "
          "zu kalt (23 %).",
          f"Die Karte färbt nur, wo beides geht ({pct(FE['beides'])} der bepflanzbaren Fläche): blau bis ocker = ab "
          f"diesem Jahr entnimmt DAC sauberer als der Baum ({pct(SW['dac'])}, im Mittel {SW['jahr']}), grün = der Baum "
          f"bleibt bis 2100 besser ({pct(SW['baum'], 1)}). Grau: nur eins von beiden oder keins (Vorfolie „Wer wo "
          "entnehmen kann“). Rechts je Jahr: Baum und DAC starten im selben Jahr.")]),
    "Die Antwort hängt an der Grenze": (None, None, []),
    "Was diese Arbeit neu zeigt": (None, None, []),
}
# text boxes besides "Kurz gesagt" (slides 41, 42): (old, new)
BOXES = [
    ("Alle nutzbaren Flächen: netto rund 52 Gt CO₂ bis 2100 — 8 % des niedrigsten Szenarios.",
     f"Alle Flächen, auf denen er kühlt: netto rund {de(NET)} Gt CO₂ bis 2100 — {pct(NET / VL)} des niedrigsten Szenarios."),
    ("Bis 2100 kühlen 0,39 der 0,83 Gha wiederbewaldbarer Fläche; im Norden und in trockenen Gebieten frisst die Albedo den Nutzen.",
     f"Bis 2100 kühlen {de(COOL, 2)} der 0,83 Gha wiederbewaldbarer Fläche; im Norden und in trockenen Gebieten frisst die Albedo den Nutzen."),
    ("Netto rund 52 Gt CO₂ bis 2100 — 8 % dessen, was selbst das niedrigste Szenario braucht.",
     f"Netto rund {de(NET)} Gt CO₂ bis 2100 — {pct(NET / VL)} dessen, was selbst das niedrigste Szenario braucht."),
]
NOTES_ANYWHERE = [
    ("Die Folien „Naive Rechnung“ und „Bäume reichen nicht“ rechnen weiter mit Carbon Briefs 655 Gt.",
     "Alle Folien rechnen mit diesen Daten (Very Low 591 Gt)."),
    ("(CMIP7 Very Low, 591 Gt bis 2100, aus den Originaldaten; Carbon Brief kommt mit Bodenkohlenstoff auf 655 Gt, damit "
     "rechnet bisher noch das Kapitel Vergleich)",
     "(CMIP7 Very Low, 591 Gt bis 2100, aus den Originaldaten wie im ganzen Vortrag; Carbon Brief kommt mit "
     "Bodenkohlenstoff auf 655 Gt)"),
]
BACKUP_V1 = (
    f"Von den 0,83 Gha wiederbewaldbarer Fläche kühlen bis 2100 {de(COOL, 2)} Gha; auf "
    f"{de(V['bepflanzbar_waermt_gha'], 2)} Gha — im Norden und in trockenen Gebieten — frisst die Albedo mehr, als der "
    "Baum an CO₂ bindet.",
    "Eigene Rechnung, Baum (typischer Wald) gepflanzt 2025, bewertet 2100. Fläche: Walker et al. 2022 (Modellergebnis: "
    "aus Inventur- und Satellitendaten hochgerechnet); Waldtyp: Hasler et al. 2024.")


def replace_runs(tf, old: str, new: str) -> bool:
    """Replace text inside one paragraph whose joined runs contain *old*; first run keeps the formatting."""
    for p in tf.paragraphs:
        t = "".join(r.text for r in p.runs)
        if old in t and p.runs:
            p.runs[0].text = t.replace(old, new)
            for r in p.runs[1:]:
                r.text = ""
            return True
    return False


def pptx() -> None:
    prs = Presentation(str(B.DECK))
    for slide in prs.slides:
        title = slide.shapes.title.text if slide.shapes.title is not None else None
        notes = slide.notes_slide.notes_text_frame if slide.has_notes_slide else None
        if notes is not None:
            t = notes.text
            for old, new in NOTES_ANYWHERE:
                t = t.replace(old, new)
            if t != notes.text:
                notes.text = t
        for sh in slide.shapes:
            if sh.has_text_frame:
                for old, new in BOXES:
                    replace_runs(sh.text_frame, old, new)
        if title == "Wo Bäume kühlen — und wo nicht":
            B.set_box(next(s for s in slide.shapes if s.name == "Kurz gesagt"), "Kurz gesagt", BACKUP_V1[0])
            B.set_box(next(s for s in slide.shapes if s.name == "Quelle"), None, BACKUP_V1[1])
        if title not in SLIDES:
            continue
        take, src, nrep = SLIDES[title]
        if take:
            B.set_box(next(s for s in slide.shapes if s.name == "Kurz gesagt"), "Kurz gesagt", take)
        if src:
            B.set_box(next(s for s in slide.shapes if s.name == "Quelle"), None, src)
        if nrep:
            t = notes.text
            for old, new in nrep:
                if old not in t:
                    print(f"  ! Notiz nicht gefunden auf „{title}“: {old[:50]}…")
                t = t.replace(old, new)
            notes.text = t
    prs.save(str(B.DECK))


def html_deck() -> None:
    s = HTML.read_text(encoding="utf-8")
    titles = {"Wo Bäume hinkönnen": "Wo Bäume hinkönnen", "Bäume reichen nicht": "Bäume reichen nicht",
              "Wer wo entnehmen kann": "Wer wo entnehmen kann", "Heute: der Holzweg": "Heute: der Holzweg",
              "DAC fährt mit der Energiewende mit": "DAC fährt mit der Energiewende mit",
              "Die Maschine wird zur Messlatte": "Die Maschine wird zur Messlatte"}
    for title, data_title in titles.items():
        take, src, _ = SLIDES[title]
        a = s.index(f'data-title="{data_title}"')
        b = s.index("</section>", a)
        sec = s[a:b]
        if take:
            sec = re.sub(r'(<p class="takeaway"[^>]*>).*?(</p>)', lambda m: m.group(1) + html.escape(take, quote=False) + m.group(2),
                         sec, count=1, flags=re.S)
        if src:
            sec = re.sub(r'(<p class="src">).*?(</p>)', lambda m: m.group(1) + html.escape(src, quote=False) + m.group(2),
                         sec, count=1, flags=re.S)
        s = s[:a] + sec + s[b:]
    for old, new in BOXES:
        s = s.replace(html.escape(old, quote=False), html.escape(new, quote=False)).replace(old, new)
    HTML.write_text(s, encoding="utf-8")


def main() -> None:
    if any(p.name.startswith("~$") for p in B.DECK.parent.iterdir()):
        sys.exit("Deck ist in PowerPoint geöffnet (~$-Datei) — erst schließen.")
    B.WORKSPACE.mkdir(exist_ok=True)
    shutil.copy2(B.DECK, B.WORKSPACE / f"dissvortrag_v2_vor_zahlen_{datetime.now():%Y%m%d_%H%M%S}.pptx")
    pptx()
    html_deck()
    for t, (take, _, _) in SLIDES.items():
        if take:
            print(f"{t}: {take}")


if __name__ == "__main__":
    main()
