import dataclasses
import pytest

from nbs.species import (
    PARAMETER_FIELDS,
    REFERENCE_SITES,
    SPECIES,
    ParamSource,
    Species,
    get_species,
    reference_site,
)

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
def test_every_parameter_documents_its_provenance(key):
    """Not a subset of the parameters -- all of them. The previous version of
    this test listed five field names, which is exactly why the other seven
    went undocumented for so long without anything failing."""
    sp = get_species(key)
    assert set(sp.sources) == set(PARAMETER_FIELDS), (
        f"{key}: Quellenangaben decken nicht alle Parameter ab, "
        f"fehlend={set(PARAMETER_FIELDS) - set(sp.sources)}, "
        f"unerwartet={set(sp.sources) - set(PARAMETER_FIELDS)}"
    )


@pytest.mark.parametrize("key", sorted(EXPECTED_KEYS))
def test_provenance_entries_are_structured_and_non_empty(key):
    sp = get_species(key)
    for name, src in sp.sources.items():
        assert isinstance(src, ParamSource), f"{key}.{name} ist keine ParamSource"
        assert src.stufe in ("literatur", "abgeleitet", "annahme")
        assert src.referenz.strip(), f"{key}.{name}: leere Referenz"


@pytest.mark.parametrize("key", sorted(EXPECTED_KEYS))
def test_a_declared_assumption_never_carries_a_bare_citation(key):
    """An "annahme" must say what its reference actually is -- a citation with
    no note reads as if the value came from the paper, which is the exact
    misreading this level exists to prevent."""
    sp = get_species(key)
    for name, src in sp.sources.items():
        if src.stufe == "annahme":
            assert src.notiz.strip(), f"{key}.{name}: Annahme ohne Erlaeuterung"


def test_every_species_has_a_reference_site():
    """The talk's E-figures are all evaluated at one latitude per species and
    slide 25 names them. If they live only on the slide, a regenerated figure
    can silently disagree with the deck."""
    assert set(REFERENCE_SITES) == EXPECTED_KEYS
    assert reference_site("picea_abies") == 60.0
    for key in EXPECTED_KEYS:
        assert -90.0 <= reference_site(key) <= 90.0


def test_reference_sites_are_not_the_cascade_band_centres():
    """Two different latitude sets exist for two different purposes; mixing
    them up would change published numbers without any test noticing."""
    from nbs.potential import _REP_LAT_DEG

    assert REFERENCE_SITES != _REP_LAT_DEG


def test_unknown_species_raises_with_helpful_message():
    with pytest.raises(KeyError, match="quercus_robur"):
        get_species("quercus_robur")
