"""The deck data for the chapter-5 anchor: Very Low in deg C and the effect of each measure, unclipped."""
import json
from pathlib import Path

import numpy as np

Z = json.loads(Path("deck/chart_data/zeitpfade.json").read_text())


def _c(key):
    return np.array(Z["vl_c"]) + (np.array(Z["wirkung"]["baeume"]) + np.array(Z["wirkung"][key])) / 1000


def test_anchor_series_exist_and_have_the_years():
    n = len(Z["jahre"])
    assert len(Z["vl_c"]) == n
    assert set(Z["wirkung"]) == {"baeume", "dac_20", "dac_50", "dac_100", "dac_frei", "vegan"}
    assert all(len(v) == n for v in Z["wirkung"].values())


def test_dac_stays_at_or_below_1p5_after_its_return_year():
    for key, case in (("dac_20", "opt_20"), ("dac_50", "opt_50"), ("dac_100", "opt_100"), ("dac_frei", "opt_frei")):
        t = _c(key); i = Z["jahre"].index(Z["dac"][case]["ab"])
        assert np.all(t[i:] <= 1.5 + 1e-3), key


def test_faster_growth_is_ordered():
    d = Z["dac"]
    assert d["opt_frei"]["spitze"] <= d["opt_100"]["spitze"] <= d["opt_50"]["spitze"] <= d["opt_20"]["spitze"] + 0.1
    assert d["opt_frei"]["ab"] <= d["opt_100"]["ab"] <= d["opt_50"]["ab"] <= d["opt_20"]["ab"]


def test_vegan_goes_below_1p5_and_is_not_clipped():
    t = _c("vegan")
    assert t.min() < 1.5                 # back below 1.5 deg C before 2100 (Very Low without its removal: 1.46 in 2100)
    assert abs(t.max() - (1.5 + max(Z["vegan"]["gap"]) / 1000)) < 0.005
