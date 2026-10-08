"""Introduce DAC properly in dissvortrag_v2.pptx (same slides as the HTML deck).

* Intro, after the CMIP7 removal slide: "Zwei Wege, CO₂ aus der Luft zu holen"
  (tree and machine side by side), so the question slide's "Maschinen" has a face.
* Vergleich, after "Bäume reichen nicht":
  - "Wie eine Maschine CO₂ aus der Luft holt" (sorbent DAC in three steps, energy per t),
  - "Wie wir DAC rechnen: je Ort und je Jahr" (weather -> process model -> electricity;
    electricity mix -> LCA -> net efficiency, the same measure as for the tree),
  - the energy map "Was eine Maschine braucht" keeps its place, its takeaway no longer
    explains the process,
  - "Wer wo entnehmen kann" (map d0: where the tree, DAC, both or neither can go).
* "Die Maschine wird zur Messlatte": map d4 again (new colour for "keins kühlt").

The drawings come from the HTML deck: scripts/export_deck_schematics.mjs (s_*.svg) and
scripts/export_deck_svgs.mjs (hex_*.svg). Snapshot to docs/slides/workspace/ first;
refuses to run twice.

    uv run python scripts/build_dac_slides.py
    uv run python scripts/build_dac_slides.py --deck /tmp/copy.pptx   # Probelauf
"""

from __future__ import annotations

import argparse
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_map_slides as B  # noqa: E402

SCHEMA_FRAME = (0.42, 1.0, 12.5, 4.3)

INTRO = dict(
    title="Zwei Wege, CO₂ aus der Luft zu holen",
    key="s_zwei_wege",
    takeaway=("Beide holen CO₂ aus der Luft: der Baum mit Sonnenlicht, die Maschine mit Energie. "
              "Beide stecken in der Entnahme der Szenarien. Dieser Vortrag rechnet sie gegeneinander."),
    source="Schema. DAC: Sorbens-Verfahren wie in den ersten großen Anlagen (Climeworks, Island).",
    notes="""Sprechertext: Wie holt man CO₂ wieder aus der Luft? Zwei Wege stehen in diesem Vortrag. Der Baum: Er nimmt CO₂ mit Sonnenlicht auf und baut daraus Holz. Er braucht dafür Fläche und Jahrzehnte, und der Kohlenstoff bleibt nur so lange gespeichert, wie der Wald steht. Die Maschine: Direct Air Capture, kurz DAC. Gebläse saugen Luft durch einen Filter, an dem das CO₂ hängen bleibt. Erhitzt man den Filter, löst sich das CO₂ wieder; es wird verdichtet und tief im Gestein gespeichert. Die Maschine braucht kaum Fläche, aber viel Energie. Beide stecken in der Entnahme, die die Szenarien annehmen. Wie die Maschine genau funktioniert und wie wir sie rechnen, kommt im Kapitel Vergleich.

Falls Fragen kommen
Erste Anlagen im industriellen Maßstab laufen in Island (Climeworks Orca seit 2021, Mammoth seit 2024); das CO₂ wird dort im Basalt mineralisiert. In den CMIP7-Szenarien zählt DAC zur neuartigen Entnahme, zusammen mit BECCS, Gesteinsverwitterung und Ozean.""",
)

PROCESS = dict(
    title="Wie eine Maschine CO₂ aus der Luft holt",
    key="s_dac_prozess",
    takeaway=("Der Prozess braucht vor allem Energie. Mit einer Wärmepumpe wird daraus nur Strom: rund 1,5 MWh "
              "je Tonne CO₂. Wie sauber DAC entnimmt, hängt damit am Strom; wie viel davon nötig ist, am Wetter."),
    source=("Prozess: Sorbens-DAC mit dampfunterstützter Temperatur-Vakuum-Wechseladsorption (Sendi et al. 2022). "
            "Energie: premise-Datensatz Sorbens-DAC 100 kt/a (ecoinvent 3.12, Modellergebnis); Wärmepumpe und "
            "Wetterabhängigkeit nach Sendi et al. 2022."),
    notes="""Sprechertext: Bäume reichen nicht, also brauchen wir die Maschine. Wie funktioniert sie? Erstens: Gebläse drücken Luft durch ein Sorbens, ein Material mit Aminen, an dem das CO₂ haften bleibt. Zweitens: Ist es voll, wird die Kammer geschlossen; Vakuum und Dampf um 100 °C lösen das CO₂ wieder ab. Drittens: Das CO₂ wird verdichtet und in tiefen Gesteinsschichten eingelagert. Das kostet vor allem Energie, rechts je Tonne: anderthalb Megawattstunden Wärme und eine halbe Strom. Mit einer Wärmepumpe wird aus der Wärme Strom — dann hängt alles am Strom. Und wie viel Strom, hängt am Wetter.

Falls Fragen kommen
Energie aus dem premise-Datensatz (Sorbens-DAC, 100 kt/a, ecoinvent 3.12): 0,5 MWh Strom und 5,4 GJ Wärme je t. Wärmepumpe nach Sendi et al. 2022: 50 % des Carnot-Werts, Senke 120 °C, COP 1,5–2,0. Climeworks meldet für Hinwil 3,3 MWh Wärme und 0,7 MWh Strom je t, etwa doppelt so viel Wärme — das ist eine Sensitivität (Backup). Flüssig-DAC (Kalilauge, Hochtemperatur) ist nicht enthalten.""",
)

METHOD = dict(
    title="Wie wir DAC rechnen: je Ort und je Jahr",
    key="s_dac_rechnung",
    takeaway=("Das Wetter am Ort bestimmt, wie viel Strom eine Tonne braucht. Die Ökobilanz rechnet daraus mit dem "
              "Strommix des Jahres, wie viel CO₂ dabei entsteht. Am Ende steht dieselbe Frage wie beim Baum: Welcher "
              "Anteil der entnommenen Tonne bleibt netto übrig?"),
    source=("Klima: Messdaten CRU TS 4.09 (Harris et al. 2020). Prozess: Sendi et al. 2022. Strommix: Modellergebnis "
            "REMIND-EU, SSP2-NDC, über premise (Sacchi et al. 2022) mit ecoinvent 3.12. GWP100 nach IPCC 2021."),
    notes="""Sprechertext: So rechnen wir DAC — für jede halbe Gradzelle und jedes Jahr bis 2100. Oben der Ort: Aus Temperatur und Feuchte am Ort folgt mit dem Prozessmodell, wie viel Wärme der Prozess braucht und wie gut die Wärmepumpe arbeitet, also wie viel Strom eine Tonne kostet. Unten das Jahr: Welcher Strommix dann in der Region läuft, kommt aus dem Energiesystemmodell REMIND; die Ökobilanz rechnet daraus die Emissionen je Kilowattstunde, dazu Anlage, Sorbens und Speicherung. Zusammen: wie viel CO₂ je entnommener Tonne entsteht. Daraus der Netto-Wirkungsgrad — dieselbe Größe wie beim Baum: Dort frisst die Albedo einen Teil der Tonne, hier die Emissionen.

Falls Fragen kommen
Klima: CRU TS 4.09, Monatsmittel 2011–2020, Jahresmittel von Temperatur und Feuchte. Wärmebedarf: +12,6 % je 10 Prozentpunkte Feuchte, +9,4 % je 10 K, an Sendis vier Klimaklassen angepasst (Fehler ≤ 0,012 MWh/t). Strom: premise mit REMIND-EU SSP2-NDC, je Land der Markt seiner REMIND-Region, zwischen den Stützjahren interpoliert; GWP100 nach IPCC 2021; gerechnet in Brightway. Methode: docs/methods/dac-modell.md.""",
)

FEASIBLE = dict(
    title="Wer wo entnehmen kann",
    key="hex_d0",
    takeaway=("DAC kann auf rund vier Fünfteln des Landes stehen, nur nicht im hohen Norden. Der Baum kühlt nur auf "
              "0,39 Gha. Verglichen wird, wo Bäume Platz haben: Auf 39 % dieser Fläche geht beides, auf 8 % nur der "
              "Baum, auf 22 % nur DAC, auf 32 % keins von beiden."),
    source=("Eigene Rechnung. Baum: empfohlene Waldart je Zelle, gepflanzt 2025, kühlt bis 2150 (Fläche: Walker et al. "
            "2022). DAC: kältester Monat nicht unter −15 °C (nach Sendi et al. 2022; Klima: CRU TS 4.09). Je 2°-Block "
            "die Gruppe mit der größten Fläche."),
    notes="""Sprechertext: Wo kann was überhaupt hin? DAC kann fast überall stehen — nur nicht im hohen Norden: Wo der kälteste Monat unter minus 15 Grad liegt, ist das Verfahren nicht vorgesehen. Das ist rund ein Fünftel des Landes. Der Baum dagegen kühlt nur dort, wo Platz ist und die Albedo ihn nicht auffrisst. Verglichen wird auf der Fläche, auf der Bäume Platz haben: Dunkelblau geht beides, grün nur der Baum, weil es für DAC zu kalt ist, türkis nur DAC, weil der Baum dort wärmt. Braun: keins von beiden. Blass türkis ist das übrige Land, auf das nur DAC kann.

Falls Fragen kommen
Anteile an der wiederbewaldbaren Fläche (0,83 Gha): beides 39 %, nur Baum 8 %, nur DAC 22 %, keins 32 %. Baum = empfohlene Waldart der Zelle, gepflanzt 2025, kühlt 2150. Grenze für DAC nach Sendi et al. (2022): dort mehr als 30 Tage unter −15 °C, hier mit Monatsmitteln der kälteste Monat unter −15 °C (Sendi: rund ein Viertel des Landes). Je 2°-Block zeigt die Karte die Gruppe mit der größten wiederbewaldbaren Fläche.""",
)

D1_TAKEAWAY = ("Mit Wärmepumpe braucht eine Tonne CO₂ 1,1 bis 1,9 MWh Strom: am wenigsten im warmen, trockenen Klima, "
               "am meisten im feuchten oder kalten. Wo der kälteste Monat unter −15 °C liegt (20 % des Landes), ist "
               "Sorbens-DAC nicht vorgesehen.")


def picture(slide, key: str, frame) -> None:
    """SVG picture (PNG fallback) from docs/slides/figures/<key>.svg/.png."""
    B.svg_picture(slide, key.removeprefix("hex_").removeprefix("s_"), frame, stem=key)


def fit_box(shape, text: str) -> None:
    """Kurz-gesagt box: height from the text length, bottom edge kept (autofit is not rendered)."""
    bottom = shape.top + shape.height
    lines = math.ceil(len(text) / (shape.width / 914400 * 11.3)) + 1
    shape.height = Inches(0.16 + lines * 0.215)
    shape.top = bottom - shape.height


def fill(slide, spec: dict, frame) -> None:
    picture(slide, spec["key"], frame)
    box = next(sh for sh in slide.shapes if sh.name == "Kurz gesagt")
    B.set_box(box, "Kurz gesagt", spec["takeaway"])
    fit_box(box, spec["takeaway"])
    B.set_box(next(sh for sh in slide.shapes if sh.name == "Quelle"), None, spec["source"])
    slide.notes_slide.notes_text_frame.text = spec["notes"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", type=Path, default=B.DECK)
    deck = ap.parse_args().deck
    if any(p.name.startswith("~$") for p in deck.parent.iterdir()):
        sys.exit("Deck ist in PowerPoint geöffnet (~$-Datei) — erst schließen.")
    prs = Presentation(str(deck))
    titles = [s.shapes.title.text for s in prs.slides if s.shapes.title is not None]
    if INTRO["title"] in titles:
        sys.exit("Schon angewendet: die DAC-Folien sind bereits drin.")
    if deck == B.DECK:
        B.WORKSPACE.mkdir(exist_ok=True)
        snap = B.WORKSPACE / f"dissvortrag_v2_vor_dac_folien_{datetime.now():%Y%m%d_%H%M%S}.pptx"
        shutil.copy2(deck, snap)
        print("Snapshot:", snap.name)

    cmip = B.by_title(prs, "… und kommen nur mit CO₂-Entnahme in die Nähe")
    fill(B.new_slide_after(prs, cmip, INTRO["title"]), INTRO, SCHEMA_FRAME)

    need = B.by_title(prs, "Bäume reichen nicht")
    s_proc = B.new_slide_after(prs, need, PROCESS["title"])
    fill(s_proc, PROCESS, SCHEMA_FRAME)
    fill(B.new_slide_after(prs, s_proc, METHOD["title"]), METHOD, SCHEMA_FRAME)

    d1 = B.by_title(prs, "Was eine Maschine braucht")
    box = next(sh for sh in d1.shapes if sh.name == "Kurz gesagt")
    B.set_box(box, "Kurz gesagt", D1_TAKEAWAY)
    fill(B.new_slide_after(prs, d1, FEASIBLE["title"]), FEASIBLE, B.FRAME)

    d4 = B.by_title(prs, "Die Maschine wird zur Messlatte")
    B.remove_pictures(d4)
    B.svg_picture(d4, "d4")

    prs.save(str(deck))
    print("gespeichert:", deck)


if __name__ == "__main__":
    main()
