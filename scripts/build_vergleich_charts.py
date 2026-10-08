"""Put the deck's maps and the Vergleich chapter's charts into dissvortrag_v2.pptx as SVG from the HTML
deck (scripts/export_deck_svgs.mjs -> docs/slides/figures/hex_<key>.svg/.png), replacing the
old pictures in the same place. Rerunnable; snapshot to docs/slides/workspace/ first.

    uv run python scripts/build_vergleich_charts.py
"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

from pptx import Presentation

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_map_slides as B  # noqa: E402

CHARTS = {  # title -> key
    "Welcher Wald wo wächst": "b5",
    "Zwei Zutaten: Sonne und Schnee": "b8a",
    "Zusätzlich absorbiertes Licht: je nach Ort": "b8",
    "Was ein Baum wo bewirkt": "k15",
    "Wo Bäume hinkönnen": "v0",
    "Was eine Maschine braucht": "d1",
    "Bäume reichen nicht": "v2",
    "Wer wo entnehmen kann": "d0",
    "Heute: der Holzweg": "v3",
    "DAC fährt mit der Energiewende mit": "v4",
    "Die Maschine wird zur Messlatte": "d4",
    "Wo Bäume kühlen — und wo nicht": "v1",
}
EMU = 914400


def main() -> None:
    if any(p.name.startswith("~$") for p in B.DECK.parent.iterdir()):
        sys.exit("Deck ist in PowerPoint geöffnet (~$-Datei) — erst schließen.")
    B.WORKSPACE.mkdir(exist_ok=True)
    shutil.copy2(B.DECK, B.WORKSPACE / f"dissvortrag_v2_vor_diagramme_{datetime.now():%Y%m%d_%H%M%S}.pptx")
    prs = Presentation(str(B.DECK))
    for title, key in CHARTS.items():
        slide = B.by_title(prs, title)
        pics = [s for s in slide.shapes if s.shape_type == 13]
        if pics:  # keep the place of the old picture
            p = pics[0]
            frame = (p.left / EMU, p.top / EMU, max(p.width / EMU, 11.0), p.height / EMU)
            frame = (min(frame[0], 13.333 - 0.42 - frame[2]), frame[1], frame[2], frame[3])
        else:
            frame = B.FRAME
        B.remove_pictures(slide)
        B.svg_picture(slide, key, frame)
        pic = slide.shapes[-1]
        tree = slide.shapes._spTree
        tree.remove(pic._element)
        tree.insert(2, pic._element)
        print(f"{title}: hex_{key}")
    prs.save(str(B.DECK))


if __name__ == "__main__":
    main()
