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
    for year, (y0, y1) in [(2045, (2040, 2050)), (2060, (2050, 2075))]:
        w = (year - y0) / (y1 - y0)
        eta = (1 - w) * fields[f"dacNet{y0}"].astype(float) + w * fields[f"dacNet{y1}"].astype(float)
        ref = efficiency_grid(year)
        ok = np.isfinite(ref)
        np.testing.assert_allclose(eta[ok], ref[ok], rtol=1e-5, atol=1e-6)
