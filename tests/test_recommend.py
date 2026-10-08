import numpy as np
import pytest

from nbs.landscape import plantable_area_m2
from nbs.recommend import (
    M2_PER_GHA,
    admissible_mask,
    improvement,
    recommend,
    score_field,
    summary,
    total_delta_t,
)
from nbs.species import SPECIES, get_species

def test_every_plantable_latitude_has_at_least_one_candidate():
    """No plantable cell may be left without an admissible species -- that
    would silently drop area from the recommendation that the cascade still
    counts as available."""
    plantable = plantable_area_m2() > 0.0
    any_admissible = np.zeros_like(plantable)
    for key in SPECIES:
        any_admissible |= admissible_mask(key)
    assert not np.any(plantable & ~any_admissible)


def test_typical_forest_is_always_admissible():
    """The typical forest of a cell (Hasler et al. 2024) must be among its
    admissible types -- otherwise the comparison could drop the default."""
    species = recommend.__globals__["assign_species"]()
    for key in SPECIES:
        assert np.all(admissible_mask(key)[species == key])


def test_recommended_species_is_none_exactly_where_nothing_is_plantable():
    rec = recommend()
    plantable = plantable_area_m2() > 0.0
    has_species = rec.species != None  # noqa: E711
    assert np.array_equal(has_species, plantable)


@pytest.mark.slow
def test_recommendation_is_admissible_everywhere_it_is_made():
    rec = recommend()
    for key in SPECIES:
        chosen = rec.species == key
        if not chosen.any():
            continue
        assert np.all(admissible_mask(key)[chosen])


@pytest.mark.slow
def test_recommended_score_is_the_minimum_over_admissible_species():
    """The argmin has to hold cell by cell, not only on average: a species
    with a better score anywhere it is admissible means the wrong tree gets
    planted there."""
    rec = recommend()
    fields = {key: score_field(key) for key in SPECIES}
    chosen = rec.species != None  # noqa: E711
    for key, field in fields.items():
        both = chosen & np.isfinite(field)
        # No admissible alternative may beat the recommendation. atol=0: the
        # scores are ~1e-10 K/ha, so any non-zero absolute tolerance would
        # pass a completely different species.
        assert np.all(rec.score[both] <= field[both] + 0.0)


@pytest.mark.slow
def test_margin_is_non_negative_and_finite_where_two_species_compete():
    rec = recommend()
    n_admissible = sum(admissible_mask(key).astype(int) for key in SPECIES)
    competitive = n_admissible >= 2
    assert np.all(rec.margin[competitive] >= 0.0)
    assert np.all(np.isfinite(rec.margin[competitive]))
    lonely = (rec.species != None) & (n_admissible == 1)  # noqa: E711
    assert np.all(np.isnan(rec.margin[lonely]))


@pytest.mark.slow
def test_recommendation_cools_at_least_as_much_as_the_latitude_band_default():
    rec = recommend()
    dt_rec = total_delta_t(rec.species)
    dt_band = total_delta_t(rec.assigned)
    assert dt_rec <= dt_band
    gain = improvement()
    assert gain["gewinn_k"] >= 0.0
    assert gain["delta_t_empfohlen_k"] == pytest.approx(dt_rec, rel=1e-12, abs=0)


@pytest.mark.slow
def test_summary_areas_account_for_the_whole_plantable_area():
    stats = summary()
    total_gha = float(plantable_area_m2().sum() / M2_PER_GHA)
    assert sum(v["flaeche_gha"] for v in stats.values()) == pytest.approx(
        total_gha, rel=1e-10, abs=0
    )
    assert sum(v["flaeche_zugewiesen_gha"] for v in stats.values()) == pytest.approx(
        total_gha, rel=1e-10, abs=0
    )
