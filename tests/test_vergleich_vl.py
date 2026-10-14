"""Very Low as a temperature in deg C, not clipped at 1.5 deg C."""
import numpy as np


def test_vl_series_unclipped_and_consistent_with_overshoot():
    from nbs.vergleich_figures import overshoot_series, vl_series
    v, o = vl_series(), overshoot_series()
    assert v["jahre"] == o["jahre"]
    t = np.array(v["median_c"])
    assert np.allclose(np.maximum(0.0, t - 1.5), o["noetig_k"])
    assert 1.7 < t.max() < 1.95          # the peak of Very Low around 2050
    assert t[0] < 1.5                    # 2026 still just below 1.5 deg C: the series is not clipped there
    assert 1.5 < t[-1] < 1.7             # 2100 Very Low (median) is still above 1.5 deg C
