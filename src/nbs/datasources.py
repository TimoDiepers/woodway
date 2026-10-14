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
    "duveiller_albedo": Source(
        key="duveiller_albedo",
        title="Land cover change albedo effect, IGBPdet transitions (Delta_albedo)",
        doi="10.2905/F97E4216-E81C-4DFB-B42D-D0C19070D029",
        url="https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/ECOCLIM/Biophysical-effects-vgt-change/v2.0/",
        sha256="119e16490fad04e361bfd6a0e38c53c7a1f5aa758446f3be7274efc7e239b872",
        license="CC-BY-4.0, (c) European Union",
        size_mb=14.4,
        citation="Duveiller, G., Hooker, J., Cescatti, A. (2018), Sci. Data 5, 180014, "
        "v2.0 (JRC open data repository)",
        filename="alb_det.nc",
    ),
    "duveiller_swr": Source(
        key="duveiller_swr",
        title="Land cover change albedo effect, IGBPdet transitions "
        "(Delta_SWreflected)",
        doi="10.2905/F97E4216-E81C-4DFB-B42D-D0C19070D029",
        url="https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/ECOCLIM/Biophysical-effects-vgt-change/v2.0/",
        sha256="6049b6b0ac1b433ec5743c78ed2060325179982d2a81c84452fb9241fa2beb8a",
        license="CC-BY-4.0, (c) European Union",
        size_mb=14.8,
        citation="Duveiller, G., Hooker, J., Cescatti, A. (2018), Sci. Data 5, 180014, "
        "v2.0 (JRC open data repository)",
        filename="swr_det.nc",
    ),
    "duveiller_clouds": Source(
        key="duveiller_clouds",
        title="lulcc-bph-clouds: forest effect on low cloud cover (data_for_figures)",
        doi="10.5281/zenodo.4727774",
        url="https://zenodo.org/records/4727774/files/data_for_figures.zip?download=1",
        sha256="26b23dd230cec1d91f154a917dcec4157d1b474d0e054e9e45cf27f0138cef83",
        license="CC-BY-4.0",
        size_mb=20.1,
        citation="Duveiller, G. et al. (2021), Nat. Commun. 12, 4337",
        filename="duveiller2021_data_for_figures.zip",
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
