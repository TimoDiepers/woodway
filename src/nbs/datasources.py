"""Registry of external raster datasets, with provenance and integrity checks.

Every dataset that contributes a number to a slide is registered here with its
DOI, licence and citation, so a figure can always be traced back to what it
came from. Files live under data/raw/, which is git-ignored: nothing large is
committed, and a fresh checkout falls back to the parametrised stand-ins in
nbs.forcing until scripts/fetch_data.py has run.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


@dataclass(frozen=True)
class Source:
    key: str
    title: str
    doi: str
    url: str
    sha256: str
    """Empty string means the checksum has not been pinned yet."""
    license: str
    size_mb: float
    citation: str
    filename: str


SOURCES: dict[str, Source] = {
    "duveiller_bph": Source(
        key="duveiller_bph",
        title="Biophysical effects of vegetation cover change from satellite and models",
        doi="10.5281/zenodo.1182145",
        url="https://zenodo.org/api/records/1182145/files/LULCC-bph_LSM-vs-RS.nc/content",
        sha256="",
        license="CC-BY-4.0",
        size_mb=699.8,
        citation="Duveiller, G., Hooker, J., Cescatti, A. (2018), Sci. Data 5, 180014",
        filename="LULCC-bph_LSM-vs-RS.nc",
    ),
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve(key: str) -> Path | None:
    """Local path of a downloaded dataset, or None if it is not usable.

    Returns None both when the file is absent and when its checksum does not
    match a pinned one, so a caller can fall back without distinguishing the
    two. Use status() when the difference matters.
    """
    try:
        src = SOURCES[key]
    except KeyError:
        known = ", ".join(sorted(SOURCES))
        raise KeyError(f"Quelle {key!r} unbekannt; bekannt sind: {known}") from None

    path = RAW_DIR / src.filename
    if not path.exists():
        return None
    if src.sha256 and _sha256(path) != src.sha256:
        return None
    return path


def status() -> dict[str, str]:
    """Per source: 'vorhanden', 'fehlt' or 'prüfsumme_falsch'."""
    out: dict[str, str] = {}
    for key, src in SOURCES.items():
        path = RAW_DIR / src.filename
        if not path.exists():
            out[key] = "fehlt"
        elif src.sha256 and _sha256(path) != src.sha256:
            out[key] = "prüfsumme_falsch"
        else:
            out[key] = "vorhanden"
    return out
