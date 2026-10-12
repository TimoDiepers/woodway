"""Build the HTML deck: deck/src + deck/assets -> deck/dist.

    uv run python deck/build.py

The page is one file, deck/dist/index.html. It is assembled from
deck/src/index.html by replacing

  <!-- include path -->   with the file deck/src/path (CSS, JS, slides)
  @@NAME@@               with data from deck/chart_data (see DATA)

Chart data (ECharts specs, map rasters, CMIP7 series) and vendored libraries
live in deck/assets and are copied next to the page; the deck loads them in
the background. Charts nobody shows are left out of the copied data files.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

DECK = Path(__file__).resolve().parent
REPO = DECK.parent
SRC, ASSETS, DIST = DECK / "src", DECK / "assets", DECK / "dist"
CHART_DATA = DECK / "chart_data"


def _json(obj, ascii=True) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=ascii)


def _load(name: str) -> dict:
    return json.loads((CHART_DATA / name).read_text(encoding="utf-8"))


def data() -> dict[str, str]:
    """Values for the @@NAME@@ markers, read fresh from chart_data on every build. The DAC film's own data
    (scripts/build_dacfilm_data.py) go to data/dacfilm.js instead (dacfilm_js), loaded in the background."""
    film = _load("dacfilm.json")
    return {
        "TEMPSUM": _json(_load("tempsum.json"), ascii=False),  # scripts/build_tempsum_data.py
        "ZEIT": _json(_load("zeitpfade.json")),                # scripts/build_zeitpfade_data.py
        "DACFILM_LAND": "img/dac_land.png",       # written by dacfilm_js(): one file, not a copy in every DAC slide
        "DACFILM_BASINS": "img/dac_basins.png",
    }


def dacfilm_js() -> None:
    import base64

    film = _load("dacfilm.json")
    for k in ("land", "basins"):   # the map backgrounds as image files
        (DIST / "img" / f"dac_{k}.png").write_bytes(base64.b64decode(film.pop(k).split(",", 1)[1]))
    _write_js(DIST / "data" / "dacfilm.js", "DACFILM", film)


def assemble() -> str:
    page = (SRC / "index.html").read_text(encoding="utf-8")
    page = re.sub(r"<!-- include (\S+) -->\n?",
                  lambda m: (SRC / m.group(1)).read_text(encoding="utf-8"), page)
    values = data()
    page = re.sub(r"@@(\w+)@@", lambda m: values[m.group(1)], page)
    return page


def _read_js(path: Path) -> tuple[str, dict]:
    """window.NAME = {...}; -> (NAME, data)"""
    text = path.read_text(encoding="utf-8")
    head, body = text.split("=", 1)
    return head.replace("window.", "").strip(), json.loads(body.strip().rstrip(";"))


def _write_js(path: Path, name: str, obj: dict) -> None:
    path.write_text(f"window.{name} = " + _json(obj, ascii=False) + ";\n", encoding="utf-8")


def prune(page: str) -> None:
    """Keep only the figures the page shows. Map figures draw their cells from
    maps.js, so the copies of the cells inside ec_charts.js go too."""
    used = set(re.findall(r'data-chart="([^"]+)"', page))
    name, ec = _read_js(ASSETS / "data" / "ec_charts.js")
    mname, maps = _read_js(ASSETS / "data" / "maps.js")
    maps["maps"] = {k: v for k, v in maps["maps"].items() if k in used}
    ec = {k: v for k, v in ec.items() if k in used}
    for key in maps["maps"]:
        for ax in ec[key]["axes"]:
            ax["items"] = [it for it in ax.get("items", []) if it.get("t") != "cells"]
    missing = used - set(ec)
    assert not missing, f"figures without data: {sorted(missing)}"
    _write_js(DIST / "data" / "ec_charts.js", name, ec)
    _write_js(DIST / "data" / "maps.js", mname, maps)


def main() -> None:
    page = assemble()
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ASSETS, DIST)
    prune(page)
    dacfilm_js()
    (DIST / "index.html").write_text(page, encoding="utf-8")
    kb, n = len(page.encode()) // 1024, page.count('<section class="slide')
    print(f"deck/dist/index.html  {kb} KB, {n} slides")


if __name__ == "__main__":
    main()
