"""Render the Bäume-chapter figures: static PNGs for the deck, looping clips as optional material.

    .venv/bin/python scripts/build_animations.py

Writes to docs/slides/figures/: b6_kohlenstoff_kurve.png and
b8_albedo_jahreskarte.png for the deck, plus the optional clips as MP4 (H.264)
with a poster PNG each. For a clip in PowerPoint: Wiedergabe -> Automatisch starten, Wiedergabe bis zum Stoppen
wiederholen; set the poster PNG as the video's poster frame so the PDF export
shows a self-explanatory still.
"""

from __future__ import annotations

from pathlib import Path

from nbs.animations import (
    albedo_annual_map_figure,
    albedo_map_animation,
    carbon_curve_figure,
    carbon_map_animation,
)

OUT = Path(__file__).resolve().parents[1] / "docs" / "slides" / "figures"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(carbon_curve_figure(str(OUT / "b6_kohlenstoff_kurve.png")))
    print(albedo_annual_map_figure(str(OUT / "b8_albedo_jahreskarte.png")))
    # optional material, not in the main deck
    print(carbon_map_animation(str(OUT / "b6_kohlenstoff_karte.mp4"),
                               poster_path=str(OUT / "b6_kohlenstoff_karte_poster.png")))
    print(albedo_map_animation(str(OUT / "b8_albedo_karte.mp4"),
                               poster_path=str(OUT / "b8_albedo_karte_poster.png")))


if __name__ == "__main__":
    main()
