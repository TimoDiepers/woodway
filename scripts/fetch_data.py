"""Resolve and download the registered raster datasets into data/raw/.

Run with no arguments to see what is present and what is missing:

    uv run python scripts/fetch_data.py

Pass keys to download them:

    uv run python scripts/fetch_data.py duveiller_bph

Nothing here is required to run the model: every consumer falls back to the
parametrised stand-ins when a source is missing, and says so on the figure.
"""

from __future__ import annotations

import sys
import urllib.request

from nbs.datasources import RAW_DIR, SOURCES, status


def report() -> None:
    st = status()
    width = max(len(k) for k in SOURCES)
    for key, src in SOURCES.items():
        print(f"{key:<{width}}  {st[key]:<18}  {src.size_mb:7.1f} MB  {src.license}")
        print(f"{'':<{width}}  {src.citation}")


def download(key: str) -> None:
    src = SOURCES[key]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    target = RAW_DIR / src.filename
    print(f"lade {key} ({src.size_mb:.1f} MB) -> {target}")
    urllib.request.urlretrieve(src.url, target)  # noqa: S310
    print("fertig")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        report()
    else:
        for key in sys.argv[1:]:
            download(key)
