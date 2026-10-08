"""Marabá (BR) instead of Belém as the third running site, and every place name with its country
code on the slides (Aachen (DE), Joensuu (FI), Marabá (BR), ...) -- 2026-10-06.

Belém's cell has an unusually low carbon potential for the tropics (Walker et al. 2022: 80 Mg C/ha,
tropical median 113); Marabá in the south-eastern Amazon has 139 Mg C/ha, much reforestable land
and much sun. Texts and notes in dissvortrag_v2.pptx and the HTML deck; the charts come as SVG from
the HTML deck. Country codes go into the slide texts and charts, not into the speaker notes.

Run after scripts/export_slide_facts.py, scripts/export_html_v2.py --charts,
scripts/export_deck_svgs.mjs and scripts/build_consistent_numbers.py; then
scripts/export_html_v2.py --backup. Snapshot to docs/slides/workspace/ first.
"""

from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from pptx import Presentation

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_belem_site as BS  # noqa: E402
import build_horizon_2100 as H  # noqa: E402
import build_map_slides as B  # noqa: E402

PAIRS = [
    ("Aachen 49 kg C je Baum, Joensuu 33 kg C, Belém 40 kg C.", "Aachen 49 kg C je Baum, Joensuu 33 kg C, Marabá 69 kg C."),
    ("; Belém im immergrünen tropischen Laubwald.", "; Marabá im immergrünen tropischen Laubwald."),
    ("der Regenwald bei Belém liegt dazwischen.", "der Regenwald bei Marabá holt am meisten, 1,4-mal so viel wie Aachen."),
    ("bei Belém (östlicher Amazonas) rund 135 kg", "bei Marabá (südöstlicher Amazonas) rund 233 kg"),
    ("im Jahresmittel. Bei Belém ist der Wald sogar heller als Wiese oder Acker davor: −3 W.", "und Marabá 21 W im Jahresmittel."),
    ("Belém hat keinen Schnee, und das tropische Kronendach ist heller als das Weideland, das es ersetzt.",
     "Marabá hat keinen Schnee; dort zählt nur, dass das Kronendach etwas dunkler ist als das Weideland."),
    ("bei Belém kostet es nichts.", "bei Marabá nur wenig."),
    ("bei Belém um ein Drittel stärker.", "bei Marabá fast doppelt so stark."),
    ("−4,7·10⁻¹⁴ K bei Belém.", "−6,5·10⁻¹⁴ K bei Marabá."),
    ("bei Belém von 131 noch 47: Dort kostet die Albedo nichts.", "bei Marabá von 226 noch 65."),
    ("Belém: -131 → -133 → -72 → -48 → -47", "Marabá: -226 → -211 → -106 → -65 → -65"),
    ("Belém (−47) liegt im kühlenden Gürtel", "Marabá (−65) liegt im kühlenden Gürtel"),
    ("Aachen, Joensuu und Belém sind die drei Punkte", "Aachen, Joensuu und Marabá sind die drei Punkte"),
    ("in Joensuu und bei Belém gleich", "in Joensuu und bei Marabá gleich"),
    ("Joensuu und Belém", "Joensuu und Marabá"),
    ("Belém 135 kg CO₂", "Marabá 233 kg CO₂"),
    ("Aachen 34 W, Joensuu 45 W und Marabá", "Aachen 34 W, Joensuu 45 W und Marabá"),
]
CODES = {"Aachen": "DE", "Joensuu": "FI", "Marabá": "BR", "Krakau": "PL", "Peking": "CN", "Manaus": "BR",
         "Kinshasa": "CD"}
NAME = re.compile(r"\b(" + "|".join(CODES) + r")\b(?! \()")


def coded(text: str) -> str:
    return NAME.sub(lambda m: f"{m.group(1)} ({CODES[m.group(1)]})", text)


def pptx() -> None:
    prs = Presentation(str(B.DECK))
    for no, slide in enumerate(prs.slides, 1):
        if no > 44:
            break
        for sh in slide.shapes:
            if not sh.has_text_frame:
                continue
            H.replace_in_tf(sh.text_frame, PAIRS)
            for p in sh.text_frame.paragraphs:
                t = "".join(r.text for r in p.runs)
                n = coded(t)
                if n != t and p.runs:
                    p.runs[0].text = n
                    for r in p.runs[1:]:
                        r.text = ""
        if slide.has_notes_slide:
            t = slide.notes_slide.notes_text_frame.text
            n = t
            for old, new in PAIRS:
                n = n.replace(old, new)
            if n != t:
                slide.notes_slide.notes_text_frame.text = n
    for title, key in BS.CHARTS.items():
        slide = B.by_title(prs, title)
        old = H.chart_frame(slide)
        frame = (old.left / 914400, old.top / 914400, old.width / 914400, old.height / 914400)
        old._element.getparent().remove(old._element)
        B.svg_picture(slide, key, frame)
        pic = slide.shapes[-1]
        slide.shapes._spTree.remove(pic._element)
        slide.shapes._spTree.insert(2, pic._element)
    for title, key in {"Bäume reichen nicht": "v2", "Wer wo entnehmen kann": "d0", "Heute: der Holzweg": "v3",
                       "DAC fährt mit der Energiewende mit": "v4", "Die Maschine wird zur Messlatte": "d4"}.items():
        slide = B.by_title(prs, title)
        old = H.chart_frame(slide)
        frame = (old.left / 914400, old.top / 914400, old.width / 914400, old.height / 914400)
        old._element.getparent().remove(old._element)
        B.svg_picture(slide, key, frame)
        pic = slide.shapes[-1]
        slide.shapes._spTree.remove(pic._element)
        slide.shapes._spTree.insert(2, pic._element)
    prs.save(str(B.DECK))


def html_deck() -> None:
    s = H.HTML.read_text(encoding="utf-8")
    b = s.index("<!-- BACKUP:BEGIN -->")
    main = s[:b]
    for old, new in PAIRS:
        main = main.replace(old, new)
    # country codes in the visible text of the slides, not in the notes and not in the head
    a = main.index('<section class="slide')
    parts = re.split(r"(<aside class=\"notes\".*?</aside>)", main[a:], flags=re.S)
    main = main[:a] + "".join(p if p.startswith("<aside") else coded(p) for p in parts)
    H.HTML.write_text(main + s[b:], encoding="utf-8")


def main() -> None:
    if any(p.name.startswith("~$") for p in B.DECK.parent.iterdir()):
        sys.exit("Deck ist in PowerPoint geöffnet (~$-Datei) — erst schließen.")
    shutil.copy2(B.DECK, B.WORKSPACE / f"dissvortrag_v2_vor_maraba_{datetime.now():%Y%m%d_%H%M%S}.pptx")
    pptx()
    html_deck()


if __name__ == "__main__":
    main()
