"""Site factor per cell (nbs.site_factor) and forest data (nbs.forest_data)."""

import numpy as np

from nbs.forest_data import (
    F30_CAP,
    growth_by_key,
    key_grid,
    reforestable_area_m2,
    typical_type,
)
from nbs.site_factor import site_factor, site_factor_grid
from nbs.species import SPECIES

AACHEN = (50.78, 6.08)
JOENSUU = (62.60, 29.76)


def _key(lat, lon):
    from nbs.grid import grid_lats, grid_lons

    return key_grid()[int(np.argmin(abs(grid_lats() - lat))), int(np.argmin(abs(grid_lons() - lon)))]


def test_reforestable_area_is_walkers_opportunity():
    # Walker et al. 2022: R/L + R/H = 931 Mha
    assert abs(reforestable_area_m2().sum() / 1e13 - 0.931) < 0.005


def test_running_example_sites_are_mixed_forest():
    assert _key(*AACHEN) == "mf_gemaessigt"
    assert _key(*JOENSUU) == "mf_boreal"


def test_every_typical_key_is_registered():
    keys = {k for k in key_grid().ravel() if k is not None}
    assert keys <= set(SPECIES)


def test_typed_cells_are_reforestable():
    assert np.all(reforestable_area_m2()[typical_type() != None] > 0)  # noqa: E711


def test_growth_pace_respects_the_poorter_bound():
    k_cap = -np.log(1.0 - F30_CAP**0.5) / 30.0
    for g in growth_by_key().values():
        assert 0.0 < g["k"] <= k_cap + 1e-12


def test_factor_is_one_without_a_cell():
    assert site_factor("mf_gemaessigt", 50.78) == 1.0


def test_factor_is_cell_carbon_over_key_median():
    from nbs.forest_data import carbon_gain_mgc_ha
    from nbs.grid import grid_lats, grid_lons

    i = int(np.argmin(abs(grid_lats() - AACHEN[0])))
    j = int(np.argmin(abs(grid_lons() - AACHEN[1])))
    ref = growth_by_key()["mf_gemaessigt"]["m_ref_mgc_ha"]
    assert np.isclose(site_factor("mf_gemaessigt", *AACHEN), carbon_gain_mgc_ha()[i, j] / ref)
    assert np.isclose(site_factor_grid("mf_gemaessigt")[i, j], site_factor("mf_gemaessigt", *AACHEN))


def test_median_cell_of_a_key_has_factor_near_one():
    keys = key_grid()
    a = reforestable_area_m2()
    for key in ("mf_gemaessigt", "enf_boreal", "ebf_tropisch"):
        sel = keys == key
        f = site_factor_grid(key)[sel]
        o = np.argsort(f)
        cw = np.cumsum(a[sel][o])
        assert abs(f[o][np.searchsorted(cw, 0.5 * cw[-1])] - 1.0) < 1e-6
