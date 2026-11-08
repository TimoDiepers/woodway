"""Regenerate woodway/public/borders.geojson: Natural Earth 1:50m land boundaries and coastlines, as one line set.

Any segment with |dlon| > 180 (antimeridian jump) is split so no line spans the map.
Run: uv run python woodway/scripts/borders.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = [ROOT / "data/borders/ne_50m_admin_0_boundary_lines_land.geojson",   # 1:50m: holds up when zoomed in
       ROOT / "data/borders/ne_50m_coastline.geojson"]
OUT = ROOT / "woodway/public/borders.geojson"
OCEAN = ROOT / "data/borders/ne_50m_ocean.geojson"
OCEAN_OUT = ROOT / "woodway/public/ocean.geojson"   # the sea, laid over the hexagons: cells end at the coast


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
    lines = []
    for f in (f for src in SRC for f in json.loads(src.read_text())["features"]):
        g = f["geometry"]
        for ln in [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]:
            # 0.01 deg (~1 km): finer than the 0.5 deg cells, and points that round together are dropped
            pts = [[round(x, 2), round(y, 2)] for x, y, *_ in ln]
            pts = [q for k, q in enumerate(pts) if k == 0 or q != pts[k - 1]]
            if len(pts) > 1:
                lines += split(pts)
    feat = {"type": "Feature", "properties": {}, "geometry": {"type": "MultiLineString", "coordinates": lines}}
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": [feat]}, separators=(",", ":")))
    print(f"{len(lines)} lines -> {OUT}")
    # the ocean at the same precision: rings rounded to 0.01 deg, repeated points dropped, tiny rings left out
    polys = []
    for f in json.loads(OCEAN.read_text())["features"]:
        g = f["geometry"]
        for poly in [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]:
            rings = []
            for ring in poly:
                pts = [[round(x, 2), round(y, 2)] for x, y, *_ in ring]
                pts = [q for k, q in enumerate(pts) if k == 0 or q != pts[k - 1]]
                if len(pts) >= 4:
                    rings.append(pts)
            if rings:
                polys.append(rings)
    feat = {"type": "Feature", "properties": {}, "geometry": {"type": "MultiPolygon", "coordinates": polys}}
    OCEAN_OUT.write_text(json.dumps({"type": "FeatureCollection", "features": [feat]}, separators=(",", ":")))
    print(f"{len(polys)} ocean polygons -> {OCEAN_OUT}")


if __name__ == "__main__":
    main()
