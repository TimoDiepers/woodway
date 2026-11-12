"""Forest-type registry (nbs.species), built from data in nbs.forest_data."""

import dataclasses

import pytest

from nbs.forest_data import F30_CAP, TYPES, growth_by_key, key_grid
from nbs.species import (
    PARAMETER_FIELDS,
    REFERENCE_SITES,
    SPECIES,
    ParamSource,
    get_species,
    reference_site,
)

IGBP = {"enf": "evergreen_needleleaf", "ebf": "evergreen_broadleaf", "dnf": "deciduous_needleleaf",
        "dbf": "deciduous_broadleaf", "mf": "mixed"}


def test_one_entry_per_type_and_zone_with_data():
    assert set(SPECIES) == set(growth_by_key())
    assert {k.split("_")[0] for k in SPECIES} == set(TYPES)


def test_every_typical_forest_is_registered():
    assert {k for k in key_grid().ravel() if k is not None} <= set(SPECIES)


def test_species_are_immutable():
    sp = get_species("mf_gemaessigt")
    with pytest.raises(dataclasses.FrozenInstanceError):
        sp.k = 0.5  # type: ignore[misc]


@pytest.mark.parametrize("key", sorted(SPECIES))
def test_parameters_are_physically_plausible(key):
    import numpy as np

    sp = get_species(key)
    assert 4.0 < sp.m_max_kgC < 700.0  # 2-300 t C/ha at 450 trees/ha
    assert 0.0 < sp.k <= -np.log(1.0 - F30_CAP**0.5) / 30.0 + 1e-12
    assert sp.p == 2.0
    assert sp.stand_area_m2 == pytest.approx(1e4 / 450.0)
    assert 0.0 < sp.p_disturb < 0.05
    assert 0.0 <= sp.eps_immediate <= 1.0
    assert sp.igbp_class == IGBP[key.split("_")[0]]
    assert sp.valid_gez == (key.split("_", 1)[1],)


def test_tropical_forest_holds_more_carbon_than_boreal():
    """Walker et al. 2022: the unrealized biomass gain is largest in the tropics."""
    assert get_species("ebf_tropisch").m_max_kgC > get_species("enf_boreal").m_max_kgC


@pytest.mark.parametrize("key", sorted(SPECIES))
def test_every_parameter_documents_its_provenance(key):
    sp = get_species(key)
    assert set(PARAMETER_FIELDS) <= set(sp.sources)
    for name, src in sp.sources.items():
        assert isinstance(src, ParamSource)
        if src.stufe == "annahme":
            assert src.notiz.strip(), f"{key}.{name}: Annahme ohne Erlaeuterung"


def test_every_entry_has_a_reference_site_inside_its_cells():
    assert set(REFERENCE_SITES) == set(SPECIES)
    for key in SPECIES:
        assert 0.0 <= reference_site(key) <= 75.0


def test_unknown_species_raises_with_helpful_message():
    with pytest.raises(KeyError, match="known species"):
        get_species("picea_abies")
