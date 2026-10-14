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
    assert set(Z["wirkung"]) == {"baeume", "dac_20", "dac_50", "dac_100", "vegan", "dac_vegan"}
    assert all(len(v) == n for v in Z["wirkung"].values())


def test_daccs_holds_1p5_from_its_return_year_and_faster_is_earlier():
    ab = {}
    for g in (20, 50, 100):
        ab[g] = Z["dac"][f"g{g}"]["ab"]
        i = Z["jahre"].index(ab[g])
        assert _c(f"dac_{g}")[i:].max() <= 1.5 + 1e-3     # vl_c is rounded to 0.001 deg C in the file
    assert ab[100] <= ab[50] <= ab[20]


def test_daccs_runs_only_on_standing_plants_and_costs_hold():
    o = Z["dac"]["g20"]
    w, u = np.array(o["w"]), np.array(o["u"])
    assert np.all(u <= w + 1e-6)
    assert abs(w.max() - o["kap"]) < 0.01
    assert Z["kosten_pfad"]["median"]["summe_bio"] > Z["vegan"]["kosten"]["median"]["summe_bio"] > 0


def test_vegan_goes_below_1p5_and_is_not_clipped():
    t = _c("vegan")
    assert t.min() < 1.5                 # back below 1.5 deg C before 2100 (Very Low without its removal: 1.46 in 2100)
    assert abs(t.max() - (1.5 + max(Z["vegan"]["gap"]) / 1000)) < 0.005


def test_vegan_plus_daccs_holds_1p5_from_its_return_year():
    t = _c("vegan") + np.array(Z["wirkung"]["dac_vegan"]) / 1000
    i = Z["jahre"].index(Z["vegan"]["g20"]["ab"])
    assert t[i:].max() <= 1.5 + 1e-3
    assert Z["vegan"]["g20"]["ab"] < Z["dac"]["g20"]["ab"]
