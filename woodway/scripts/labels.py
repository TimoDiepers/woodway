"""Write woodway/public/labels.geojson: the place names the map can show, from Natural Earth.

Countries (1:50m admin 0, at their label point, from their MIN_LABEL zoom) and populated places (1:10m, from their
MIN_ZOOM), each with its German and English name and a rank for the label collision (MapLibre symbol-sort-key: the
lower, the earlier placed). Places above MAX_ZOOM_PLACES are left out: the map does not zoom in that far.

    uv run python woodway/scripts/labels.py
"""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLACES = ROOT / "data/raw/naturalearth/ne_10m_populated_places.geojson"   # 19 MB, not in git: fetched on first run
PLACES_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_populated_places.geojson"
COUNTRIES = ROOT / "data/borders/ne_50m_admin_0_countries.geojson"
OUT = ROOT / "woodway/public/labels.geojson"
MAX_ZOOM_PLACES = 7.0


def _pt(lon, lat, props):
    return {"type": "Feature", "properties": props, "geometry": {"type": "Point", "coordinates": [round(lon, 3), round(lat, 3)]}}


def main():
    if not PLACES.exists():
        PLACES.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(PLACES_URL, PLACES)
    feats = []
    for f in json.loads(COUNTRIES.read_text())["features"]:
        p = f["properties"]
        if p.get("LABEL_X") is None:
            continue
        feats.append(_pt(p["LABEL_X"], p["LABEL_Y"], {"k": "c", "de": p.get("NAME_DE") or p["NAME"], "en": p.get("NAME_EN") or p["NAME"],
                                                       "z": float(p.get("MIN_LABEL") or 2), "r": int(p.get("LABELRANK") or 5)}))
    for f in json.loads(PLACES.read_text())["features"]:
        p = f["properties"]
        z = float(p.get("MIN_ZOOM") or 10)
        if z > MAX_ZOOM_PLACES:
            continue
        lon, lat = f["geometry"]["coordinates"][:2]
        feats.append(_pt(lon, lat, {"k": "p", "de": p.get("NAME_DE") or p["NAME"], "en": p.get("NAME_EN") or p["NAME"], "z": z,
                                    "r": int(p.get("SCALERANK") or 10), "cap": 1 if p.get("ADM0CAP") else 0}))
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":")))
    print(f"{sum(f['properties']['k'] == 'c' for f in feats)} countries, {sum(f['properties']['k'] == 'p' for f in feats)} places -> {OUT}")


if __name__ == "__main__":
    main()
