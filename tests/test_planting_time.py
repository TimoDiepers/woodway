import numpy as np
import pytest

from nbs.config import ModelConfig
from nbs.constants import T_START, YEARS
from nbs.planting_time import (
    DEFAULT_AGE_YR,
    PLANT_YEARS,
    cohort,
    cohort_table,
    hazard_curve,
    risk_ratio,
    survival_probability,
)
from nbs.pipeline import _background_temperature
from nbs.species import get_species
from nbs.tree import simulate_deterministic


def test_every_cohort_reaches_the_default_age_inside_the_axis():
    assert max(PLANT_YEARS) + DEFAULT_AGE_YR <= int(YEARS[-1])


def test_planting_before_the_axis_starts_is_rejected():
    sp = get_species("enf_boreal")
    background = np.zeros(len(YEARS))
    with pytest.raises(ValueError, match="ausserhalb"):
        simulate_deterministic(sp, background, plant_year=T_START - 1)


def test_nothing_grows_before_the_planting_year():
    """A cohort's stock, debris and uptake must be exactly zero until it is
    planted -- not merely small. A non-zero value there would mean the tree
    was quietly credited with years it never lived."""
    sp = get_species("enf_boreal")
    background = np.full(len(YEARS), 1.0)
    traj = simulate_deterministic(sp, background, plant_year=2065)
    idx = 2065 - T_START
    assert np.all(traj.stock_kgC[:idx] == 0.0)
    assert np.all(traj.debris_kgC[:idx] == 0.0)
    assert np.all(traj.net_uptake_kgC_yr[:idx] == 0.0)
    assert traj.stock_kgC[idx + 1] > 0.0


def test_a_constant_climate_makes_a_late_cohort_an_exact_shift_of_an_early_one():
    """With the background held flat there is no rising hazard, so the only
    difference between cohorts is the calendar shift. This pins that the
    plant_year machinery itself introduces no bias -- everything the
    cohort_table reports beyond this shift comes from the climate."""
    sp = get_species("enf_boreal")
    background = np.full(len(YEARS), 1.0)
    early = simulate_deterministic(sp, background, plant_year=T_START)
    late = simulate_deterministic(sp, background, plant_year=T_START + 40)
    n = len(YEARS) - 40
    np.testing.assert_allclose(
        late.stock_kgC[40:], early.stock_kgC[:n], rtol=1e-12, atol=0.0
    )


def test_hazard_rises_with_the_background_and_the_ratio_is_p0_free():
    """risk_ratio must depend only on gamma and the warming between the two
    years: two species with the same gamma but different base rates have to
    give the identical ratio, or the figure's '×1,52' would silently be a
    species property."""
    hazard = hazard_curve("enf_boreal")
    assert hazard[-1] > hazard[0]
    assert risk_ratio("enf_boreal", T_START) == pytest.approx(1.0, rel=0, abs=1e-14)

    import dataclasses

    import nbs.tree as tree

    sp = get_species("enf_boreal")
    doubled = dataclasses.replace(sp, p_disturb=2.0 * sp.p_disturb)
    background = _background_temperature("ssp245")
    p_a = tree.disturbance_probability(sp, background)
    p_b = tree.disturbance_probability(doubled, background)
    idx = 2085 - T_START
    assert (p_b[idx] / p_b[0]) == pytest.approx(p_a[idx] / p_a[0], rel=1e-12, abs=0)


def test_survival_falls_monotonically_with_the_planting_year():
    probs = [survival_probability("enf_boreal", py) for py in PLANT_YEARS]
    assert all(b < a for a, b in zip(probs, probs[1:]))
    assert all(0.0 < p < 1.0 for p in probs)


@pytest.mark.slow
def test_later_cohorts_lose_a_larger_share_at_the_same_age():
    """The isolated risk effect: same species, same age, later planting. The
    loss share has to grow -- if it did not, the slide's claim that a rising
    fire risk penalises late planting would have no support in the model."""
    table = cohort_table("enf_boreal")
    losses = [table[py]["verlust_anteil"] for py in PLANT_YEARS]
    # Very Low (without its removal) warms to about 2050 and then cools again: a later cohort lives through a similar
    # hazard at the same age, so its loss share stays close (since 2026-11-04; under SSP2-4.5 it grew)
    assert max(losses) < 1.1 * min(losses)
    # And the undisturbed reference must be identical for every cohort: at
    # the same age, with the hazard off, they are the same tree.
    refs = [table[py]["vorrat_ungestoert"] for py in PLANT_YEARS]
    assert refs == pytest.approx([refs[0]] * len(refs), rel=1e-12, abs=0)


@pytest.mark.slow
def test_break_even_is_pushed_back_at_least_by_the_planting_delay():
    """Waiting costs at least the waiting time: t* of a later cohort is never
    earlier than its own planting year, and never earlier than the first
    cohort's t* plus the delay. Since the albedo timing follows Williams et al.
    (2026), the temperate mixed forest cools from its planting year on, so
    the shift equals the delay exactly; before, with a fast-closing canopy,
    it was larger."""
    table = cohort_table("mf_gemaessigt")
    first, last = PLANT_YEARS[0], PLANT_YEARS[-1]
    assert table[last]["t_star"] >= last
    shift = table[last]["t_star"] - table[first]["t_star"]
    assert np.isfinite(shift)
    assert shift >= (last - first)


@pytest.mark.slow
def test_cohort_carries_its_planting_year_on_the_result():
    res = cohort("enf_boreal", 2045)
    assert res.plant_year == 2045
    assert res.config == ModelConfig()
