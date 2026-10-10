"""Regenerate woodway/public/borders.geojson from the deck's Natural Earth land boundary lines.

Any segment with |dlon| > 180 (antimeridian jump) is split so no line spans the map.
Run: uv run python woodway/scripts/borders.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/borders/ne_110m_admin_0_boundary_lines_land.geojson"
OUT = ROOT / "woodway/public/borders.geojson"


def split(line):
    parts, cur = [], [line[0]]
    for a, b in zip(line, line[1:]):
        if abs(b[0] - a[0]) > 180:
            parts.append(cur)
            cur = []
        cur.append(b)
    parts.append(cur)
    return [p for p in parts if len(p) > 1]


def main():
    d = json.loads(SRC.read_text())
    lines = []
    for f in d["features"]:
        g = f["geometry"]
        for ln in [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]:
            lines += split([[round(x, 3), round(y, 3)] for x, y, *_ in ln])
    feat = {"type": "Feature", "properties": {}, "geometry": {"type": "MultiLineString", "coordinates": lines}}
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": [feat]}, separators=(",", ":")))
    print(f"{len(lines)} lines -> {OUT}")


if __name__ == "__main__":
    main()
