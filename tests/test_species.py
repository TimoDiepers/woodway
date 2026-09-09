import dataclasses
import pytest

from nbs.species import SPECIES, Species, get_species

EXPECTED_KEYS = {
    "picea_abies",
    "pinus_sylvestris",
    "fagus_sylvatica",
    "eucalyptus_grandis",
    "tropical_mixed",
}


def test_five_species_one_per_biome():
    assert set(SPECIES) == EXPECTED_KEYS


def test_species_are_immutable():
    sp = get_species("picea_abies")
    assert dataclasses.is_dataclass(sp)
    with pytest.raises(dataclasses.FrozenInstanceError):
        sp.k = 0.5  # type: ignore[misc]


@pytest.mark.parametrize("key", sorted(EXPECTED_KEYS))
def test_parameters_are_physically_plausible(key):
    sp = get_species(key)
    assert 10.0 < sp.m_max_kgC < 500.0
    assert 0.01 < sp.k < 0.25
    assert 1.0 <= sp.p <= 4.0
    assert 0.1 <= sp.beta_closure <= 1.0
    assert 1.0 < sp.stand_area_m2 < 50.0
    assert 0.05 < sp.alpha_canopy < 0.25
    assert 0.0 < sp.p_disturb < 0.05
    assert 0.0 <= sp.eps_immediate <= 1.0
    assert 1.0 < sp.tau_decay_yr < 100.0
    assert sp.valid_gez


def test_boreal_grows_slower_than_tropical():
    assert get_species("picea_abies").k < get_species("tropical_mixed").k


def test_plantation_grows_fastest():
    ks = {k: sp.k for k, sp in SPECIES.items()}
    assert max(ks, key=ks.get) == "eucalyptus_grandis"


@pytest.mark.parametrize("key", sorted(EXPECTED_KEYS))
def test_every_species_documents_its_sources(key):
    sp = get_species(key)
    for field in ("m_max_kgC", "k", "p", "p_disturb", "alpha_canopy"):
        assert field in sp.sources, f"{key}: keine Quelle fuer {field}"


def test_unknown_species_raises_with_helpful_message():
    with pytest.raises(KeyError, match="quercus_robur"):
        get_species("quercus_robur")
