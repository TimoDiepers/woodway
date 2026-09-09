"""Tests for scripts/fetch_data.py's download(), notably its failure path.

fetch_data.py lives outside the nbs package (it is a CLI entry point), but
pytest can import it directly because pyproject.toml adds scripts/ to
pythonpath. No network access happens here: urllib.request.urlretrieve is
monkeypatched to simulate a dropped connection.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

import fetch_data


def test_failed_download_leaves_no_file_at_the_target(tmp_path, monkeypatch):
    """A connection that drops mid-transfer must not hand resolve() a
    truncated file it would mistake for good data."""
    monkeypatch.setattr(fetch_data, "RAW_DIR", tmp_path)

    def fake_urlretrieve(url, filename):
        # urlretrieve writes incrementally; simulate a partial write before
        # the connection drops.
        Path(filename).write_bytes(b"partial-data")
        raise ConnectionError("connection dropped mid-transfer")

    monkeypatch.setattr(fetch_data.urllib.request, "urlretrieve", fake_urlretrieve)

    key = next(iter(fetch_data.SOURCES))
    target = tmp_path / fetch_data.SOURCES[key].filename

    with pytest.raises(ConnectionError):
        fetch_data.download(key)

    assert not target.exists()
    assert list(tmp_path.iterdir()) == [], "no temporary .part file may remain either"


def test_successful_download_is_verified_and_renamed(tmp_path, monkeypatch):
    """A completed download lands at the final filename, with its size and
    checksum reported for pinning."""
    monkeypatch.setattr(fetch_data, "RAW_DIR", tmp_path)
    payload = b"stand-in file contents"

    def fake_urlretrieve(url, filename):
        Path(filename).write_bytes(payload)

    monkeypatch.setattr(fetch_data.urllib.request, "urlretrieve", fake_urlretrieve)

    key = next(iter(fetch_data.SOURCES))
    fetch_data.download(key)

    target = tmp_path / fetch_data.SOURCES[key].filename
    assert target.exists()
    assert target.read_bytes() == payload
    assert list(tmp_path.glob("*.part")) == [], "no temporary file left behind"


def test_pinned_checksum_mismatch_deletes_the_file_and_raises(tmp_path, monkeypatch):
    """A pinned checksum that does not match the download must not be left
    on disk as if it were good data."""
    monkeypatch.setattr(fetch_data, "RAW_DIR", tmp_path)
    key = next(iter(fetch_data.SOURCES))
    # Source is a frozen dataclass, so swap the whole registry entry (via
    # monkeypatch.setitem, which restores it after the test) rather than
    # mutating the instance in place.
    src = dataclasses.replace(
        fetch_data.SOURCES[key],
        sha256="0" * 64,  # deliberately wrong for whatever payload is written below
    )
    monkeypatch.setitem(fetch_data.SOURCES, key, src)

    def fake_urlretrieve(url, filename):
        Path(filename).write_bytes(b"some bytes that will not match")

    monkeypatch.setattr(fetch_data.urllib.request, "urlretrieve", fake_urlretrieve)

    target = tmp_path / src.filename

    with pytest.raises(ValueError, match="Prüfsumme"):
        fetch_data.download(key)

    assert not target.exists()
    assert list(tmp_path.iterdir()) == []
