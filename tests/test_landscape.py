import numpy as np
import pytest

from nbs.grid import cell_area_m2, grid_lats
from nbs.landscape import (
    assign_species, exclusion_mask, land_mask, land_mask_provenance,
    plantable_area_m2, provenance, tree_count,
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


# --- Land mask: regression tests for the 71.3%-over-ocean defect ----------
#
# Measured before the fix: of 5740 cells marked plantable, 4092 (71.3%) were
# over ocean, because plantable_area_m2() had no land mask at all -- a
# latitude row's "plantable" columns were a random permutation of the whole
# row, oceans included. None of the tests above caught it: an area-weighted
# sum and a 0.05-5 Gha plausibility bound are both satisfiable by nonsense
# that happens to be the right order of magnitude. These four are written to
# fail on that defect specifically.


def test_land_mask_provenance_is_reported():
    assert land_mask_provenance() in {"raster", "fallback_alles_land"}


def test_no_plantable_area_outside_the_land_mask():
    """The defect this fix targets, directly: a plantable cell wherever
    land_mask() is False is exactly the 71.3%-over-ocean bug."""
    area = plantable_area_m2()
    land = land_mask()
    assert np.all(area[~land] == 0.0), "bepflanzbare Flaeche ausserhalb der Landmaske"


def test_no_species_assigned_outside_the_land_mask():
    sp = assign_species()
    land = land_mask()
    assert np.all(sp[~land] == None)  # noqa: E711


def test_land_mask_covers_a_plausible_fraction_of_the_globe():
    """Land is ~29% of Earth's surface **by area**; this mask is vegetated land
    only (wherever the Duveiller raster has no land-cover-transition retrieval
    at all -- desert, ice, bare rock, and any land cover the dataset's ten IGBP
    classes do not reach), so it must come out noticeably below 29%, not at or
    above it, and nowhere near 0% or 100%.

    The comparison must be made against the *area* fraction. Half-degree cells
    shrink towards the poles, so the cell-count fraction is a different number
    (20.3% vs 23.6% here) and checking it against the 29% area figure compares
    two different quantities -- which is how "20.3% of the Earth's surface"
    reached a slide."""
    from nbs.landscape import land_mask_fractions

    fr = land_mask_fractions()
    assert 0.10 < fr["flaeche"] < 0.29, (
        f"{fr['flaeche']:.3f} liegt ausserhalb der plausiblen Landspanne"
    )
    assert 0.10 < fr["zellen"] < 0.30


def test_cell_and_area_fractions_of_the_land_mask_are_not_interchangeable():
    """Pins the gap that caused the slide error: this mask sits at low and mid
    latitudes, where cells are large, so its area share is materially *above*
    its cell share. Anything that quotes one as the other is wrong by this
    margin, and the two must not be allowed to silently converge."""
    from nbs.landscape import land_mask_fractions

    fr = land_mask_fractions()
    assert fr["flaeche"] > fr["zellen"] + 0.02
    # Gha and area fraction must describe the same mask.
    assert fr["gha"] == pytest.approx(fr["flaeche"] * 51.006, rel=1e-3, abs=0)


def test_no_plantable_cell_in_the_mostly_ocean_55_to_70_south_band():
    """55-70S is almost entirely Southern Ocean -- the only vegetated land
    there is a sliver of southern Patagonia/Tierra del Fuego and a handful
    of sub-Antarctic islands, none of which this half-degree grid should
    resolve into a plantable cell once masked. This is the literal
    60S-over-ocean failure the controller's visual check found on the
    un-masked map."""
    lats = grid_lats()
    band = (lats <= -55.0) & (lats >= -70.0)
    sp = assign_species()
    assert np.all(sp[band] == None), "bepflanzbare Zelle im Band 55-70 Sued"  # noqa: E711


def test_land_mask_is_spatially_coherent_not_confetti():
    """The known second problem: species assignment (and hence the
    forest/savanna/agriculture/plantable split within land) comes from
    latitude bands, not real land cover, so it stays speckled even after
    masking -- expected and accepted (see the module docstring). What must
    NOT be speckled is the land mask itself, since it comes from real
    geography: real coastlines are contiguous, so almost every land cell
    should have at least one land neighbour. A mask assembled the way the
    old plantable-area split was (a per-row random permutation) would fail
    this hard, since an isolated land pixel surrounded by ocean on all four
    sides is exactly what "confetti" means."""
    land = land_mask()
    up = np.zeros_like(land)
    up[1:, :] = land[:-1, :]
    down = np.zeros_like(land)
    down[:-1, :] = land[1:, :]
    left = np.roll(land, 1, axis=1)
    right = np.roll(land, -1, axis=1)
    has_land_neighbour = up | down | left | right
    frac_coherent = float(has_land_neighbour[land].mean())
    assert frac_coherent > 0.95, (
        f"nur {frac_coherent:.3f} der Landzellen haben eine Landnachbarzelle "
        "-- das ist Konfetti, keine Geografie"
    )
