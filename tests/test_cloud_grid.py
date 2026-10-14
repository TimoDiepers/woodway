"""Cloud brightening over forest (Duveiller et al. 2021, converted after Cerasoli et al. 2021)."""

import numpy as np
import pytest

from nbs import cloud_grid as cg
from nbs.albedo_grid import monthly_insolation_native
from nbs.animations import SITES, site_cell
from nbs.constants import D_AFTERNOON, R_CLOUD

AACHEN, JOENSUU, MARABA = SITES


def test_shapes_and_finite():
    mp = cg.monthly_cloud_product("mf_gemaessigt")
    assert mp.shape == (12, 360, 720) and np.isfinite(mp).all()
    np.testing.assert_allclose(cg.cloud_q_product("mf_gemaessigt"), mp.mean(axis=0), atol=1e-12)


def test_insolation_is_finite_on_land_bands():
    q = monthly_insolation_native("enf_boreal")
    assert q.shape == (12, 180, 360)
    assert np.isfinite(q[:, 30:60, :]).all()          # 30-60 N band has measurements every month


def test_formula_at_a_local_cell():
    df = cg.delta_cloud_native("enf_boreal")
    q = monthly_insolation_native("enf_boreal")
    full = np.isfinite(df).all(axis=0) & np.isfinite(q).all(axis=0)
    i, j = np.argwhere(full)[0]
    native = cg._monthly_native_tiered("enf_boreal")[0]
    np.testing.assert_allclose(native[:, i, j], df[:, i, j] * R_CLOUD * D_AFTERNOON * q[:, i, j])


def test_mixed_uses_whichever_type_exists():
    d = np.load(cg.DATA)
    mixed = cg.delta_cloud_native("mf_gemaessigt")
    only_efo = np.isfinite(d["EFO"]) & ~np.isfinite(d["DFO"])
    np.testing.assert_allclose(mixed[only_efo], d["EFO"][only_efo])
    both = np.isfinite(d["EFO"]) & np.isfinite(d["DFO"])
    np.testing.assert_allclose(mixed[both], 0.5 * (d["EFO"][both] + d["DFO"][both]), rtol=1e-6)


def test_aachen_summer_brightens():
    assert cg.monthly_cloud_product("mf_gemaessigt")[6][site_cell(AACHEN)] > 0


def test_joensuu_snow_season_stays_negative():
    assert cg.monthly_cloud_product("mf_boreal")[2][site_cell(JOENSUU)] < 0


def test_band_without_any_retrieval_is_zero_tier_two():
    tier = cg.cloud_provenance_grid("enf_boreal")
    mp = cg.monthly_cloud_product("enf_boreal")
    south = np.arange(360) > 300            # south of about -60 deg
    assert (tier[south] == 2).all() and (mp[:, south] == 0).all()


def test_cloud_effect_smaller_than_albedo_at_aachen():
    from nbs.albedo_grid import alpha_q_product
    c = cg.cloud_q_product("mf_gemaessigt")[site_cell(AACHEN)]
    a = alpha_q_product("mf_gemaessigt")[site_cell(AACHEN)]
    assert 0 < c < -a
