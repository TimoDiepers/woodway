"""Belém (eastern Amazon) as the third running site next to Aachen and Joensuu (2026-10-06):
slide texts and notes in dissvortrag_v2.pptx, the same texts and chart labels in the HTML deck,
and the site charts and light maps as SVG from the HTML deck.

Run after scripts/export_html_v2.py --charts and scripts/export_deck_svgs.mjs; then
scripts/export_html_v2.py --backup. Snapshot to docs/slides/workspace/ first.

    uv run python scripts/build_belem_site.py
"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

from pptx import Presentation

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_horizon_2100 as H  # noqa: E402
import build_map_slides as B  # noqa: E402

PAIRS = [
    ("Aachen 49 kg C je Baum, Joensuu 33 kg C.", "Aachen 49 kg C je Baum, Joensuu 33 kg C, Belém 40 kg C."),
    ("Aachen und Joensuu liegen beide im Mischwald — gemäßigt und boreal.",
     "Aachen und Joensuu liegen beide im Mischwald, gemäßigt und boreal; Belém im immergrünen tropischen Laubwald."),
    ("der Mischwald in Aachen holt 1,5-mal so viel wie der im finnischen Joensuu.",
     "der Mischwald in Aachen holt 1,5-mal so viel wie der im finnischen Joensuu; der Regenwald bei Belém liegt "
     "dazwischen."),
    ("in Joensuu (Ostfinnland) rund 111 kg", "bei Belém (östlicher Amazonas) rund 135 kg, in Joensuu (Ostfinnland) rund 111 kg"),
    ("— Aachen 34 W, Joensuu 45 W im Jahresmittel.",
     "— Aachen 34 W, Joensuu 45 W im Jahresmittel. Bei Belém ist der Wald sogar heller als Wiese oder Acker davor: −3 W."),
    ("Joensuu hat im April eine Spitze von rund 150 W: noch Schnee, Sonne schon hoch.",
     "Joensuu hat im April eine Spitze: noch Schnee, Sonne schon hoch. Belém hat keinen Schnee, und das tropische "
     "Kronendach ist heller als das Weideland, das es ersetzt."),
    ("So gerechnet überwiegt das CO₂ an beiden Orten vom ersten Jahr an; in Joensuu holt das Licht aber viel davon "
     "wieder auf.",
     "So gerechnet überwiegt das CO₂ an allen drei Orten vom ersten Jahr an; in Joensuu holt das Licht aber viel davon "
     "wieder auf, bei Belém kostet es nichts."),
    ("nach 75 Jahren 44 %", "nach 50 Jahren 49 %"),
    ("Mit dem Klimasystem kühlt der Wald an beiden Orten vom ersten Jahr an — in Joensuu aber 2100 nur mit 34 % der "
     "Kühlung von Aachen.",
     "Mit dem Klimasystem kühlt der Wald an allen drei Orten vom ersten Jahr an — in Joensuu aber 2100 nur mit 34 % "
     "der Kühlung von Aachen, bei Belém um ein Drittel stärker."),
    ("−1,2·10⁻¹⁴ K in Joensuu.", "−1,2·10⁻¹⁴ K in Joensuu, −4,7·10⁻¹⁴ K bei Belém."),
    ("In Joensuu bleiben von 108 nur 12.", "In Joensuu bleiben von 108 nur 12, bei Belém von 131 noch 47: Dort kostet "
     "die Albedo nichts."),
    ("Joensuu: -108 → -79 → -29 → -9 → -12 (·10⁻¹⁵ K).",
     "Joensuu: -108 → -79 → -29 → -9 → -12; Belém: -131 → -133 → -72 → -48 → -47 (·10⁻¹⁵ K)."),
    ("Aachen (−35) und Joensuu (−12 · 10⁻¹⁵ K) liegen dazwischen.",
     "Belém (−47) liegt im kühlenden Gürtel, Aachen (−35) und Joensuu (−12 · 10⁻¹⁵ K) dazwischen."),
    ("Bisher zwei Orte.", "Bisher drei Orte."),
    ("Aachen und Joensuu sind die beiden Punkte, die wir kennen.", "Aachen, Joensuu und Belém sind die drei Punkte, "
     "die wir kennen."),
    ("Das gilt in Aachen, in Joensuu und in den Tropen gleich", "Das gilt in Aachen, in Joensuu und bei Belém gleich"),
    # chart descriptions (HTML)
    ("Aachen und Joensuu, jedes zehnte Jahr", "Aachen, Joensuu und Belém, jedes zehnte Jahr"),
    ("rechts der Jahresgang in Aachen und Joensuu", "rechts der Jahresgang in Aachen, Joensuu und Belém"),
    ("in W, Aachen und Joensuu", "in W, Aachen, Joensuu und Belém"),
    ("Antrieb je Baum in Aachen und Joensuu:", "Antrieb je Baum in Aachen, Joensuu und Belém:"),
    ("Temperaturwirkung je Baum in Aachen und Joensuu", "Temperaturwirkung je Baum in Aachen, Joensuu und Belém"),
    ("nach Pflanzjahr, Aachen und Joensuu", "nach Pflanzjahr, Aachen, Joensuu und Belém"),
    ("Zwei Karten Europas:", "Zwei Weltkarten:"),
]

CHARTS = {  # title -> key: charts with the sites and the light maps (now world maps)
    "Welcher Wald wo wächst": "b5",
    "Was der Baum der Luft entnimmt": "b6",
    "Zwei Zutaten: Sonne und Schnee": "b8a",
    "Zusätzlich absorbiertes Licht: je nach Ort": "b8",
    "Was der Baum mit seiner Umgebung tauscht": "b9",
    "Gemeinsame Währung: Energie": "b10",
    "Was der Luft wirklich fehlt": "k5",
    "Kohlenstoff und Licht in einer Währung": "k10",
    "Die Erde erwärmt sich träge": "k12b",
    "Die Erwärmung wirkt auf den Baum zurück": "k13",
    "Was jede Erweiterung der Systemgrenze kostet": "k14",
    "Was ein Baum wo bewirkt": "k15",
    "Zeit zählt: DAC wirkt sofort, der Baum wächst erst": "z1",
}


def pptx() -> None:
    prs = Presentation(str(B.DECK))
    for no, slide in enumerate(prs.slides, 1):
        if no > 44:
            break
        for sh in slide.shapes:
            if sh.has_text_frame:
                H.replace_in_tf(sh.text_frame, PAIRS)
        if slide.has_notes_slide:
            t = slide.notes_slide.notes_text_frame.text
            n = t
            for old, new in PAIRS:
                n = n.replace(old, new)
            if n != t:
                slide.notes_slide.notes_text_frame.text = n
    for title, key in CHARTS.items():
        slide = B.by_title(prs, title)
        old = H.chart_frame(slide)
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
    prs.save(str(B.DECK))


def html_deck() -> None:
    s = H.HTML.read_text(encoding="utf-8")
    b = s.index("<!-- BACKUP:BEGIN -->")
    main = s[:b]
    for old, new in PAIRS:
        main = main.replace(old, new)
    H.HTML.write_text(main + s[b:], encoding="utf-8")


def main() -> None:
    if any(p.name.startswith("~$") for p in B.DECK.parent.iterdir()):
        sys.exit("Deck ist in PowerPoint geöffnet (~$-Datei) — erst schließen.")
    shutil.copy2(B.DECK, B.WORKSPACE / f"dissvortrag_v2_vor_belem_{datetime.now():%Y%m%d_%H%M%S}.pptx")
    pptx()
    html_deck()


if __name__ == "__main__":
    main()
