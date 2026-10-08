"""Tighten the map story at the start of the Vergleich chapter in dissvortrag_v2.pptx.

* "Was ein Baum wo bewirkt" (k15, end of Klima) already shows where a tree cools;
  the categorical cooling map "Wo Bäume kühlen — und wo nicht" (v1) repeated it
  and moves to the backup, right after the backup divider.
* "Wo Bäume hinkönnen" (v0) keeps the area map and now also states how much of
  that area cools (0,39 Gha with the best-cooling forest type per cell, the rule
  of the whole Vergleich chapter).
* "Die Maschine wird zur Messlatte" (d4): the map gets the same three groups as
  the area shares next to it (DAC overtakes / tree stays better / neither cools),
  and the takeaway says where the tree stays ahead: mostly in the north, where
  it is too cold for DAC — not in the tropics.

It writes a snapshot to docs/slides/workspace/ first and refuses to run twice.

    uv run python scripts/build_story_vergleich.py
    uv run python scripts/build_story_vergleich.py --deck /tmp/copy.pptx   # Probelauf
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from pptx import Presentation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_map_slides import DECK, WORKSPACE, by_title, remove_pictures, set_box, svg_picture  # noqa: E402

V0_TAKEAWAY = ("Wiederbewaldbar sind 0,83 Gha, rund 6 % der eisfreien Landfläche, und dünn verteilt. "
               "Kühlen tut der Baum davon nur auf 0,39 Gha; der Rest liegt im Norden und im Trockenen, "
               "wo die Albedo mehr frisst, als der Baum an CO₂ bindet.")
V0_NOTES = """Sprechertext: Die Karte davor hat gezeigt, was ein Baum wo bewirkt. Jetzt die Frage für den Vergleich: Wie viel Platz gibt es überhaupt? Grün heißt: Dieser Anteil des Landes ist wiederbewaldbar — kein Wald, kein Acker, keine Stadt, keine offene Landschaft. Grau: Land ohne Platz. Kräftig grün wird es nur im hohen Norden und in einzelnen Regionen der Tropen — und gerade im Norden wärmt der Baum. Von den 0,83 Gha bleiben 0,39 Gha, auf denen er kühlt. Mit dieser Fläche rechnen wir weiter.

Falls Fragen kommen
Fläche nach Walker et al. (2022), nur Zellen mit einem typischen Waldtyp nach Hasler et al. (2024). Ab hier nimmt das Kapitel je Zelle den Waldtyp mit der stärksten Kühlung: 0,39 Gha kühlen (mit dem typischen Wald der Vorfolie 0,36 Gha). Die Karte „Wo Bäume kühlen — und wo nicht“ liegt im Backup. Gezeigt als Anteil an der Landfläche je 2°-Block; Blöcke mit weniger als 3 von 16 Landzellen sind ausgeblendet (Inselchen, einzelne Landzellen im Klimadatensatz), die Flächensummen enthalten sie."""

D4_TAKEAWAY = ("Weil wir DAC ohnehin brauchen, muss jede Baum-Tonne mindestens so gut sein wie die "
               "Maschinen-Tonne. Diese Messlatte steigt: 2030 liegt der Baum auf 25 % der bepflanzbaren "
               "Fläche darüber, ab 2050 nur noch auf 11 % — vor allem im Norden, wo es für DAC zu kalt ist, "
               "und in Teilen der Tropen.")
D4_NOTES = """Messlatte = DAC am selben Ort mit dem Strom seiner Region (wenn jedes Land seine eigene Entnahme leistet). Würde Entnahme weltweit gehandelt, wäre die Messlatte DAC am besten Standort (z. B. Norwegen, schon heute rund 90 %) — dann wäre der Baum fast überall sofort unterlegen.

Karte und Flächenanteile zeigen dieselben drei Gruppen. Blau bis ocker: ab diesem Jahr entnimmt DAC sauberer als der Baum (59 % der bepflanzbaren Fläche bis 2100). Grün: Der Baum bleibt bis 2100 besser (19 %), meist weil es dort für Sorbens-DAC zu kalt ist (17 %). Dunkelgrau: keins kühlt — der Baum wärmt, und für DAC ist es zu kalt (23 %). Zusammen sind 40 % der bepflanzbaren Fläche für Sorbens-DAC zu kalt. Was der Vergleich nicht enthält: Kosten, Flächenbedarf, Tempo, Dauerhaftigkeit der Speicherung, Mengen. Der Strom für eine Gigatonne entspricht rund 5 % der heutigen Weltstromerzeugung. Methode: docs/methods/dac-modell.md."""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", type=Path, default=DECK)
    deck = ap.parse_args().deck
    if any(p.name.startswith("~$") for p in deck.parent.iterdir()):
        sys.exit("Deck ist in PowerPoint geöffnet (~$-Datei) — erst schließen.")
    prs = Presentation(str(deck))
    slides = list(prs.slides)
    v1 = by_title(prs, "Wo Bäume kühlen — und wo nicht")
    backup = next(s for s in slides if any(sh.name == "BackupTitel" for sh in s.shapes))
    if slides.index(v1) > slides.index(backup):
        sys.exit("Schon angewendet: die Kühl-Karte liegt bereits im Backup.")
    if deck == DECK:
        WORKSPACE.mkdir(exist_ok=True)
        snap = WORKSPACE / f"dissvortrag_v2_vor_story_vergleich_{datetime.now():%Y%m%d_%H%M%S}.pptx"
        shutil.copy2(deck, snap)
        print("Snapshot:", snap.name)

    lst = prs.slides._sldIdLst
    el = lst[slides.index(v1)]
    lst.remove(el)
    lst.insert(list(prs.slides).index(backup) + 1, el)

    v0 = by_title(prs, "Wo Bäume hinkönnen")
    set_box(next(sh for sh in v0.shapes if sh.name == "Kurz gesagt"), "Kurz gesagt", V0_TAKEAWAY)
    v0.notes_slide.notes_text_frame.text = V0_NOTES

    d4 = by_title(prs, "Die Maschine wird zur Messlatte")
    remove_pictures(d4)
    svg_picture(d4, "d4")
    set_box(next(sh for sh in d4.shapes if sh.name == "Kurz gesagt"), "Kurz gesagt", D4_TAKEAWAY)
    d4.notes_slide.notes_text_frame.text = D4_NOTES

    prs.save(str(deck))
    print("gespeichert:", deck)


if __name__ == "__main__":
    main()
