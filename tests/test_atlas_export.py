"""The atlas export reproduces the model it was cut from."""
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "atlas" / "public" / "data"


def _load():
    meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
    raw = (DATA / "fields.bin").read_bytes()
    out = {}
    for name, f in meta["fields"].items():
        dt = np.float32 if f["dtype"] == "f4" else np.uint8
        out[name] = np.frombuffer(raw, dtype=dt, count=f["length"], offset=f["offset"]).reshape(360, 720)
    return meta, out


def _dt(meta, fields, year):
    k = meta["years"].index(year)
    dt = np.full((360, 720), np.nan)
    for n, key in enumerate(meta["types"], start=1):
        m = fields["type"] == n
        c = meta["curves"][key]
        dt[m] = fields["a"][m] * c["dtCo2"][k] + fields["b"][m] * c["dtAlbUnit"][k]
    return dt


def test_files_exist_and_are_small():
    meta, fields = _load()
    assert meta["version"] == 1
    assert len(meta["types"]) == 18
    assert meta["years"][0] == 2026 and meta["years"][-1] == 2100
    size = (DATA / "fields.bin").stat().st_size + (DATA / "meta.json").stat().st_size
    assert size < 40e6  # raw; gzipped well under 6 MB (checked in Task 11)


def test_cooling_area_is_the_talks_039_gha():
    meta, fields = _load()
    dt = _dt(meta, fields, 2100)
    cool = fields["area"][(fields["type"] > 0) & (dt < 0)].sum() / 1e13
    assert cool == pytest.approx(meta["global"]["areasGha"]["kuehlt"], abs=0.005)
    assert cool == pytest.approx(0.393, abs=0.005)


def test_dac_median_2026_is_46_percent():
    meta, fields = _load()
    y0, y1 = 2020, 2030
    w = (2026 - y0) / (y1 - y0)
    eta = (1 - w) * fields["dacNet2020"] + w * fields["dacNet2030"]
    assert float(np.nanmedian(eta)) == pytest.approx(0.4647, abs=0.002)


def test_reference_cells_are_consistent():
    meta, fields = _load()
    dt50, dt100 = _dt(meta, fields, 2050), _dt(meta, fields, 2100)
    for r in meta["reference"]:
        assert dt50[r["i"], r["j"]] == pytest.approx(r["dt2050"], rel=1e-5)
        assert dt100[r["i"], r["j"]] == pytest.approx(r["dt2100"], rel=1e-5)


@pytest.mark.slow
def test_dt_2100_equals_the_model_everywhere():
    from nbs.dac_compare import tree_efficiency_grid
    from nbs.map_fields import _tree_dt_grid
    from nbs.constants import T_START

    meta, fields = _load()
    dt = _dt(meta, fields, 2100)
    ref = _tree_dt_grid()
    ok = np.isfinite(ref)
    # float32 factors: where CO2 and albedo almost cancel, the relative error grows; compare against the
    # field's scale (display resolution is 1e-16 K, this tolerance is 1e-19 K)
    np.testing.assert_allclose(dt[ok], ref[ok], rtol=1e-5, atol=1e-5 * np.abs(ref[ok]).max())
    eff = tree_efficiency_grid(T_START)
    k = meta["years"].index(2100)
    carbon = np.zeros_like(dt)
    for n, key in enumerate(meta["types"], start=1):
        m = fields["type"] == n
        carbon[m] = fields["a"][m] * meta["curves"][key]["dtCo2"][k]
    np.testing.assert_allclose((dt / carbon)[ok], eff[ok], rtol=1e-4, atol=1e-5)


@pytest.mark.slow
def test_dac_net_equals_the_model_between_base_years():
    from nbs.dac import efficiency_grid

    meta, fields = _load()
    for year, (y0, y1) in [(2026, (2020, 2030)), (2045, (2040, 2050)), (2060, (2050, 2075)), (2090, (2075, 2100))]:
        w = (year - y0) / (y1 - y0)
        eta = (1 - w) * fields[f"dacNet{y0}"].astype(float) + w * fields[f"dacNet{y1}"].astype(float)
        ref = efficiency_grid(year)
        ok = np.isfinite(ref)
        np.testing.assert_allclose(eta[ok], ref[ok], rtol=1e-5, atol=1e-6)


def _same(got, ref, scale_ref=None, rtol=1e-5):
    """float32 storage: relative 1e-5 plus an atol of 1e-5 of the field's scale; NaN pattern must match."""
    got = np.asarray(got, dtype=float)
    ref = np.asarray(ref, dtype=float)
    assert np.array_equal(np.isfinite(got), np.isfinite(ref))
    ok = np.isfinite(ref)
    scale = np.abs(ref[ok]).max() if scale_ref is None else scale_ref
    np.testing.assert_allclose(got[ok], ref[ok], rtol=rtol, atol=1e-5 * scale)


@pytest.mark.slow
def test_per_cell_fields_equal_their_model_source():
    from nbs.animations import _STAND_AREA_M2, _by_type, typical_alpha_q_product
    from nbs.dac import dac_possible, energy_grid
    from nbs.dac_climate import climate_grid
    from nbs.forest_data import reforestable_area_m2
    from nbs import albedo_grid

    meta, fields = _load()
    typ = fields["type"] > 0
    ok = dac_possible()
    area = np.where(typ, reforestable_area_m2(), 0.0)
    _same(fields["light"], -typical_alpha_q_product() * _STAND_AREA_M2)
    _same(fields["sun"], _by_type(albedo_grid.insolation_grid))
    _same(fields["darker"], -100.0 * _by_type(albedo_grid.delta_alpha_grid))
    _same(fields["area"], area)
    _same(fields["trees"], area / _STAND_AREA_M2)
    _same(fields["elec"], np.where(ok, energy_grid("waermepumpe")["strom"], np.nan))
    np.testing.assert_array_equal(fields["dacOk"], ok.astype(np.uint8))
    land = np.isfinite(climate_grid()["t_mean_c"]) | (area > 0)
    np.testing.assert_array_equal(fields["land"], land.astype(np.uint8))
    assert fields["land"][typ].all()


@pytest.mark.slow
def test_type_codes_and_factors_equal_the_model():
    from nbs.aggregate import _product_no_nan, co2_factor_grid
    from nbs.landscape import assign_species

    meta, fields = _load()
    species = assign_species()
    for n, key in enumerate(meta["types"], start=1):
        m = species == key
        assert (fields["type"] == n).sum() == m.sum()
        assert (fields["type"][m] == n).all()
        _same(fields["a"][m], co2_factor_grid(key)[m])
        _same(fields["b"][m], _product_no_nan(key)[m])
    assert (fields["type"][~np.isin(species, meta["types"])] == 0).all()


@pytest.mark.slow
def test_curves_equal_a_fresh_single_tree_run():
    from nbs.constants import A_EARTH_M2, T_START, TAU_ATM
    from nbs.pipeline import run_single_tree
    from nbs.response import convolve_response, green_temperature
    from nbs.species import get_species, reference_site

    meta, _ = _load()
    g_t = green_temperature("ssp245")
    for key in (meta["types"][0], meta["types"][-1]):
        res = run_single_tree(key, lat_deg=reference_site(key), plant_year=T_START)
        unit = -TAU_ATM * np.asarray(res.trajectory.closure, dtype=float) * get_species(key).stand_area_m2 / A_EARTH_M2
        c = meta["curves"][key]
        for name, ref in [("m", res.trajectory.stock_kgC), ("phiCo2", res.phi_co2), ("phiAlbUnit", unit),
                          ("dtCo2", convolve_response(g_t, res.phi_co2)), ("dtAlbUnit", convolve_response(g_t, unit))]:
            ref = np.asarray(ref, dtype=float)
            assert len(c[name]) == len(ref) == len(meta["years"])
            np.testing.assert_allclose(c[name], ref, rtol=1e-5, atol=1e-5 * np.abs(ref).max())


def test_build_table_and_global_paths_equal_the_deck_data():
    meta, fields = _load()
    film = json.loads((ROOT / "deck" / "chart_data" / "dacfilm.json").read_text(encoding="utf-8"))
    z = json.loads((ROOT / "deck" / "chart_data" / "zeitpfade.json").read_text(encoding="utf-8"))
    b, g = meta["build"], meta["global"]
    assert b["years"] == film["years"] and b["countries"] == film["countries"] and b["owner"] == film["owner"]
    assert b["capacityGt"] == film["paths"]["opt"]["cc"]
    for (i, j), (lon, lat) in zip(b["cells"], film["cells"]):
        assert 90.0 - (i + 0.5) * 0.5 == pytest.approx(lat, abs=0.25 + 1e-9)
        assert -180.0 + (j + 0.5) * 0.5 == pytest.approx(lon, abs=0.25 + 1e-9)
    assert len(b["cells"]) == len(film["cells"])
    assert g["years"] == z["jahre"] and g["need"] == z["noetig"] and g["afterTrees"] == z["baeume_rest"]
    assert g["afterDac"] == film["paths"]["opt"]["dac"] and g["dacCapacityGt"] == film["paths"]["opt"]["tot"]
    for k in ("alle", "kuehlt", "forst"):
        assert g["paths"][k] == z["pfade"][k]
    for k in ("alle", "kuehlt"):
        assert g["areasGha"][k] == z["flaechen_gha"][k]
