"""Very Low as a temperature in deg C, not clipped at 1.5 deg C; the reference of chapters 4-5 is Very Low
without the CO2 removal it assumes (novel and land), so trees and DAC are not counted twice."""
import numpy as np


def test_vl_series_unclipped_and_consistent_with_overshoot():
    from nbs.vergleich_figures import overshoot_series, vl_series
    v, o = vl_series(), overshoot_series()
    assert v["jahre"] == o["jahre"]
    t = np.array(v["median_c"])
    assert np.allclose(np.maximum(0.0, t - 1.5), o["noetig_k"])
    assert 1.7 < t.max() < 1.95          # the peak around 2050
    assert t[0] < 1.5                    # 2026 still just below 1.5 deg C: the series is not clipped there
    assert 1.5 < t[-1]                   # 2100 still above 1.5 deg C


def test_reference_is_very_low_without_its_removal():
    from nbs.vergleich_figures import vl_series
    ohne, mit = np.array(vl_series()["median_c"]), np.array(vl_series(mit_entnahme=True)["median_c"])
    d = ohne - mit
    assert abs(d[0]) < 0.005             # the removal starts small: no jump in 2026
    assert np.all(d >= -1e-6)            # without removal it is never cooler
    assert 0.07 < d[-1] < 0.13           # 2100: about 0.1 K warmer (335 Gt CO2 removal 2024-2100)
    assert 1.5 < mit[-1] < 1.7           # the published Very Low (median) in 2100
