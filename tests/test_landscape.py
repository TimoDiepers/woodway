import numpy as np
import pytest

from nbs.grid import cell_area_m2
from nbs.landscape import (
    assign_species, exclusion_mask, plantable_area_m2, provenance, tree_count,
)
from nbs.species import SPECIES


def test_shapes_match_the_grid():
    assert plantable_area_m2().shape == (360, 720)
    assert tree_count().shape == (360, 720)


def test_plantable_area_never_exceeds_the_cell():
    """An area-weighted sum that oversubscribes cells inflates every downstream
    number, and nothing later would catch it."""
    assert np.all(plantable_area_m2() <= cell_area_m2() + 1.0)


def test_plantable_area_is_non_negative():
    assert np.all(plantable_area_m2() >= 0.0)


def test_assigned_species_are_registered_ones():
    # np.unique on an object array cannot sort a mix of None and str (Python
    # 3's None has no total order, and this holds for any Python/numpy
    # version -- sorted([None, None, "a"]) itself raises TypeError). Filter
    # the None entries out before calling unique; this checks the identical
    # thing the original one-liner intended, just without tripping over that.
    grid = assign_species()
    assigned = set(np.unique(grid[grid != None]).tolist())  # noqa: E711
    assert assigned <= set(SPECIES)


def test_no_trees_where_no_species_is_assigned():
    sp = assign_species()
    assert np.all(tree_count()[sp == None] == 0)  # noqa: E711


def test_tree_count_follows_area_and_stand_area():
    from nbs.species import get_species
    sp, area, n = assign_species(), plantable_area_m2(), tree_count()
    idx = np.argwhere(sp != None)  # noqa: E711
    assert len(idx), "keine Zelle bepflanzbar"
    i, j = idx[0]
    expected = area[i, j] / get_species(sp[i, j]).stand_area_m2
    assert n[i, j] == pytest.approx(expected, rel=1e-9, abs=0)


def test_every_exclusion_reason_is_a_boolean_grid():
    for reason, mask in exclusion_mask().items():
        assert mask.dtype == bool, reason
        assert mask.shape == (360, 720), reason


def test_excluded_cells_have_no_plantable_area():
    area = plantable_area_m2()
    for reason, mask in exclusion_mask().items():
        assert np.all(area[mask] == 0.0), f"{reason}: ausgeschlossen, aber bepflanzbar"


def test_global_plantable_area_is_plausible():
    """Bastin's headline is about 0.9 Gha before corrections. Anything far
    outside a few Gha means the mask or the units are wrong."""
    gha = plantable_area_m2().sum() / 1e4 / 1e9
    assert 0.05 < gha < 5.0, f"{gha:.2f} Gha ist ausserhalb jeder Plausibilitaet"


def test_provenance_is_reported():
    assert provenance() in {"raster", "fallback"}
