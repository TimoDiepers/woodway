import pytest

from nbs.datasources import SOURCES, Source, resolve, status


def test_every_source_carries_provenance():
    """A number that reaches a slide must be traceable to a citable source."""
    assert SOURCES, "das Register ist leer"
    for key, src in SOURCES.items():
        assert isinstance(src, Source)
        assert src.doi or src.url, f"{key}: weder DOI noch URL"
        assert src.license, f"{key}: keine Lizenz"
        assert src.citation, f"{key}: keine Zitierangabe"


def test_status_reports_every_registered_source():
    st = status()
    assert set(st) == set(SOURCES)
    assert all(v in {"vorhanden", "fehlt", "pruefsumme_falsch"} for v in st.values())


def test_resolve_returns_none_for_a_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr("nbs.datasources.RAW_DIR", tmp_path)
    assert resolve(next(iter(SOURCES))) is None


def test_unknown_source_raises_with_the_known_keys_listed():
    with pytest.raises(KeyError, match="unbekannt"):
        resolve("gibt_es_nicht")
