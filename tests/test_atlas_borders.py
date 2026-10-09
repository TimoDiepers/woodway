import json
from pathlib import Path

BORDERS = Path(__file__).resolve().parents[1] / "atlas/public/borders.geojson"


def test_no_antimeridian_jumps():
    d = json.loads(BORDERS.read_text())
    bad = 0
    for f in d["features"]:
        g = f["geometry"]
        lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for ln in lines:
            bad += sum(abs(b[0] - a[0]) > 180 for a, b in zip(ln, ln[1:]))
    assert bad == 0
