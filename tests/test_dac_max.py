"""DACCS at the fastest build-out: linear to 8.8 Mt/a in 2030, then +20 %/a, every plant running, placed where
eta_C is highest within each country's storage (nbs.dac_optim.max_buildout). No optimisation, no target."""
import numpy as np
import pytest

from nbs.constants import YEARS


@pytest.fixture(scope="module")
def r():
    from nbs.dac_optim import max_buildout
    return max_buildout()


def test_follows_the_growth_limit(r):
    from nbs.dac_optim import growth_limit
    assert np.allclose(np.array(r["w"]), growth_limit(), rtol=1e-9, atol=1e-12)


def test_cooling_is_tiny_at_the_peak(r):
    k = np.array(r["kuehlung_k"])
    i = list(YEARS).index(2050)
    assert 0 < k[i] < 0.01                       # a few mK against a gap of 0.32 K
    assert np.all(np.diff(k[: i + 1]) >= -1e-12)  # the effect only grows while the build-out grows


def test_storage_holds_and_cost_up_to_the_peak(r):
    from nbs.dac_storage import storage_by_country
    x = np.array(r["x"])
    st = storage_by_country("prudent")
    assert np.all(x.sum(axis=1) <= np.array([st[c] for c in r["laender"]]) + 1e-6)
    assert 0 < r["kosten_bis_2050"]["summe_bio"] < 5


def test_net_removal_is_the_capacity_times_eta(r):
    w, net = np.array(r["w"]), np.array(r["netto"])
    i = list(YEARS).index(2050)
    assert np.all(net[: i + 1] <= w[: i + 1] + 1e-12) and net[i] > 0.5 * w[i]


def test_storage_fills_and_removal_stops(r):
    w, run = np.array(r["w"]), np.array(r["entnahme"])
    y = r["speicher_voll"]
    assert y is not None and 2050 < y <= 2100
    i = list(YEARS).index(y)
    assert np.allclose(run[:i], w[:i]) and run[i] < w[i]      # until then all of the build-out runs
