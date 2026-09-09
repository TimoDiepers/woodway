"""Resolve and download the registered raster datasets into data/raw/.

Run with no arguments to see what is present and what is missing:

    uv run python scripts/fetch_data.py

Pass keys to download them:

    uv run python scripts/fetch_data.py duveiller_bph

Nothing here is required to run the model: every consumer falls back to the
parametrised stand-ins when a source is missing, and says so on the figure.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

from nbs.datasources import RAW_DIR, SOURCES, status


def report() -> None:
    st = status()
    width = max(len(k) for k in SOURCES)
    for key, src in SOURCES.items():
        print(f"{key:<{width}}  {st[key]:<18}  {src.size_mb:7.1f} MB  {src.license}")
        print(f"{'':<{width}}  {src.citation}")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(key: str) -> None:
    """Download one registered source into RAW_DIR.

    Writes to a temporary sibling path first and only renames onto the final
    filename once the transfer has completed, so a dropped connection never
    leaves a truncated file that resolve() would later accept as good data.
    On any failure the temporary file is removed and the exception re-raised;
    nothing partial is ever left at the target path.

    If the source's checksum is already pinned, the download is verified
    against it and deleted (with an exception raised) on mismatch. If it is
    not yet pinned, the checksum is computed and printed so it can be pasted
    into the Source entry to pin future downloads.
    """
    src = SOURCES[key]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    target = RAW_DIR / src.filename
    tmp = target.with_suffix(target.suffix + ".part")
    print(f"lade {key} ({src.size_mb:.1f} MB) -> {target}")
    try:
        urllib.request.urlretrieve(src.url, tmp)  # noqa: S310
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    size_bytes = tmp.stat().st_size
    print(f"{size_bytes} Bytes empfangen")
    digest = _sha256(tmp)

    if src.sha256:
        if digest != src.sha256:
            tmp.unlink(missing_ok=True)
            raise ValueError(
                f"{key}: Prüfsumme stimmt nicht (erwartet {src.sha256}, "
                f"erhalten {digest}); Datei verworfen"
            )
        tmp.replace(target)
        print("fertig, Prüfsumme bestätigt")
    else:
        tmp.replace(target)
        print(f"fertig, sha256={digest}")
        print(
            f"Um künftige Downloads zu prüfen, sha256 in den Source-Eintrag "
            f"für {key!r} eintragen."
        )


if __name__ == "__main__":
    if len(sys.argv) == 1:
        report()
    else:
        for key in sys.argv[1:]:
            download(key)
