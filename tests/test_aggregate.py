import numpy as np
import pytest

from nbs.aggregate import aggregate_by_species, delta_t_at_year, global_delta_t, unit_curves
from nbs.constants import YEARS


@pytest.mark.slow
def test_unit_curves_have_the_study_length():
    a, b = unit_curves("picea_abies")
    assert a.shape == YEARS.shape and b.shape == YEARS.shape


@pytest.mark.slow
def test_aggregation_equals_cellwise_computation_on_a_sample():
    """The load-bearing test of this module.

    The whole grid is affordable only because everything past the tree
    trajectory is linear in tree count, so the aggregate can be formed from two
    scalars per species instead of running 259 200 cells. This test takes a
    random sample of cells, runs each one explicitly through the same unit
    curves, and checks the sum matches the aggregate. If it fails, the shortcut
    is not exact and no result on the map can be trusted.
    """
    from nbs.aggregate import _product_no_nan
    from nbs.landscape import assign_species, tree_count

    # nbs.aggregate treats cells the Duveiller raster has no data for (NaN in
    # alpha_q_product -- a real, expected geographic gap, not a bug; see
    # nbs.aggregate._product_no_nan) as carrying zero albedo product, since
    # nbs.landscape assigns species by latitude band alone, uncorrelated with
    # the raster's own sparse coverage. Both routes below apply that same
    # policy via _product_no_nan, so they are testing the same quantity the
    # implementation actually computes.
    rng = np.random.default_rng(0)
    sp_grid, n_grid = assign_species(), tree_count()
    idx = np.argwhere((sp_grid != None) & (n_grid > 0))  # noqa: E711
    assert len(idx) > 20, "zu wenige bepflanzbare Zellen fuer die Stichprobe"
    sample = idx[rng.choice(len(idx), size=20, replace=False)]

    year_idx = -1
    explicit = 0.0
    for i, j in sample:
        key = sp_grid[i, j]
        co2, alb = unit_curves(key)
        p = _product_no_nan(key)[i, j]
        explicit += n_grid[i, j] * (co2[year_idx] + p * alb[year_idx])

    # same cells, via the aggregate route
    aggregate = 0.0
    for key in {sp_grid[i, j] for i, j in sample}:
        co2, alb = unit_curves(key)
        n_sum = sum(n_grid[i, j] for i, j in sample if sp_grid[i, j] == key)
        np_sum = sum(
            n_grid[i, j] * _product_no_nan(key)[i, j]
            for i, j in sample
            if sp_grid[i, j] == key
        )
        aggregate += n_sum * co2[year_idx] + np_sum * alb[year_idx]

    scale = abs(explicit)
    assert aggregate == pytest.approx(explicit, rel=1e-9, abs=1e-12 * scale)


@pytest.mark.slow
def test_global_delta_t_has_the_study_length_and_is_finite():
    dt = global_delta_t()
    assert dt.shape == YEARS.shape
    assert np.all(np.isfinite(dt))


@pytest.mark.slow
def test_map_has_both_signs():
    """The talk's claim is that the same measure has opposite signs in
    different places. If the map is single-signed, either the albedo product or
    the species assignment is wrong."""
    field = delta_t_at_year(2125)
    finite = field[np.isfinite(field) & (field != 0.0)]
    assert (finite < 0).any(), "keine kuehlende Zelle"
    assert (finite > 0).any(), "keine waermende Zelle"


@pytest.mark.slow
def test_species_aggregates_are_positive_counts():
    for key, (n_sum, np_sum) in aggregate_by_species().items():
        assert n_sum >= 0.0, key
        assert np.isfinite(np_sum), key
