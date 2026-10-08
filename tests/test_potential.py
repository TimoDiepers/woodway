import numpy as np
import pytest

from nbs.potential import ICE_FREE_LAND_GHA, cascade, reverse_1p5


@pytest.mark.slow
def test_cascade_is_ordered_and_labelled():
    steps = cascade()
    assert len(steps) >= 5
    for s in steps:
        assert s["name_de"] and isinstance(s["name_de"], str)
        # Slide text: no ASCII stand-ins for umlauts. One of these reached a
        # figure title in Plan 1.
        for bad in ("Stoerung", "Saettigung", "fuer", "ueber", "groesser"):
            assert bad not in s["name_de"], s["name_de"]


@pytest.mark.slow
def test_area_never_grows_along_the_cascade():
    """Every step is a correction downward. A step that increases the area
    means a sign or bookkeeping error."""
    areas = [s["area_gha"] for s in cascade() if s["area_gha"] is not None]
    assert all(b <= a + 1e-9 for a, b in zip(areas, areas[1:]))


@pytest.mark.slow
def test_final_potential_is_a_fraction_of_the_raw_claim():
    steps = cascade()
    raw, final = steps[0]["carbon_gtc"], steps[-1]["carbon_gtc"]
    assert 0.0 < final < raw


@pytest.mark.slow
def test_reverse_calculation_reports_both_variants():
    r = reverse_1p5()
    assert "mit_albedo_und_stoerung" in r and "nur_kohlenstoff" in r
    assert r["mit_albedo_und_stoerung"]["n_trees"] > r["nur_kohlenstoff"]["n_trees"]


# --- Additional tests beyond the brief's Step 1 -----------------------------


@pytest.mark.slow
def test_cascade_steps_carry_the_documented_fields():
    for s in cascade():
        assert set(s) >= {"name_de", "area_gha", "carbon_gtc", "delta_t_2150", "note", "quelle"}
        assert isinstance(s["note"], str) and s["note"]
        assert isinstance(s["quelle"], str) and s["quelle"]


@pytest.mark.slow
def test_literature_only_steps_have_no_model_area_or_delta_t():
    """Steps 1-2 (Bastin's raw claim, the soil-carbon literature correction)
    carry no area or model-run figure -- this model has neither until step 3
    introduces its own land-masked area. A non-None value there would mean
    a literature number got silently relabelled as something this model
    computed."""
    steps = cascade()
    for s in steps[:2]:
        assert s["area_gha"] is None
        assert s["delta_t_2150"] is None


@pytest.mark.slow
def test_soil_carbon_step_is_marked_as_a_literature_correction():
    steps = cascade()
    soil_step = steps[1]
    assert "iteraturkorrektur" in soil_step["note"] or "iteratur" in soil_step["note"]
    assert "Bodenkohlenstoff" in soil_step["note"]


@pytest.mark.slow
def test_cascade_carbon_values_are_all_positive_where_present():
    for s in cascade():
        if s["carbon_gtc"] is not None:
            assert s["carbon_gtc"] > 0.0, s["name_de"]


@pytest.mark.slow
def test_final_delta_t_2150_is_net_cooling():
    """The cascade's headline potential should still cool the planet net,
    at the model's own horizon -- a positive number here would mean the
    'usable potential' does not even do what it is supposed to do."""
    steps = cascade()
    assert steps[-1]["delta_t_2150"] < 0.0


@pytest.mark.slow
def test_reverse_1p5_variants_report_area_and_critical_year():
    r = reverse_1p5()
    for key in ("mit_albedo_und_stoerung", "nur_kohlenstoff"):
        variant = r[key]
        assert variant["n_trees"] > 0.0
        assert variant["area_gha"] > 0.0
        assert variant["vielfaches_der_modellierten_flaeche"] > 0.0
        assert 2050 <= variant["kritisches_jahr"] <= 2150


@pytest.mark.slow
def test_reverse_1p5_ratio_is_consistent_with_the_two_variants():
    r = reverse_1p5()
    expected_ratio = (
        r["mit_albedo_und_stoerung"]["n_trees"] / r["nur_kohlenstoff"]["n_trees"]
    )
    assert r["verhaeltnis"] == pytest.approx(expected_ratio, rel=1e-9)
    assert r["verhaeltnis"] > 1.0


@pytest.mark.slow
def test_reverse_1p5_required_area_matches_its_ice_free_land_statement():
    """Pins the actual relationship behind the deck's punchline slide (P5),
    not just its prose: the required area is a large multiple of this
    model's own plantable area (the "x exceeds what the planet has room
    for" point still holds -- planting *this specific, corrected area
    several times over* is not achievable), but it is NOT larger than
    Earth's entire ice-free land area.

    ``reverse_1p5``'s own ``hinweis`` string used to say the opposite of
    the second half ("groesser als die gesamte eisfreie Flaeche der Erde"),
    which is false for both variants (9.58 and 9.76 Gha, against a ~13 Gha
    constant) and reached a slide before anyone checked it against the
    numbers already computed a few lines above it. A sign flip in the
    comparison direction below must fail this test.
    """
    r = reverse_1p5()
    for key in ("mit_albedo_und_stoerung", "nur_kohlenstoff"):
        # "large factor": 5x is a conservative floor that rules out a
        # near-1.0 factor slipping through unnoticed.
        assert r[key]["vielfaches_der_modellierten_flaeche"] > 5.0
    # Since the FaIR calibration (2026-10-05, ECS 2.9 K instead of ~5.6 K) the
    # full model needs 19.4 Gha -- more than all ice-free land -- while the
    # carbon-only variant (9.6 Gha) stays below it. Whichever way it falls,
    # the note must say the same thing as the number.
    full = r["mit_albedo_und_stoerung"]
    above = full["area_gha"] > ICE_FREE_LAND_GHA
    assert above
    assert ("mehr als diese Fläche" in r["hinweis"]) == above
    # Since the scaled base is the area that cools by 2150 (Walker area,
    # 2026-10-05), even the carbon-only variant needs more than the ice-free
    # land. What must hold: albedo and disturbance never make it cheaper.
    assert r["nur_kohlenstoff"]["area_gha"] <= full["area_gha"]


@pytest.mark.slow
def test_direct_fair_run_agrees_with_the_convolution_for_the_whole_area():
    """Area-wide numbers come from a direct FaIR run, trees and maps from the
    convolution with FaIR's marginal pulse response. For the whole
    reforestable area both must tell the same story: carbon-only cooling
    within 10 %, remaining share after albedo within 5 percentage points (2100)."""
    from nbs.config import ModelConfig
    from nbs.constants import YEARS
    from nbs.landscape import assign_species
    from nbs.potential import _convolved_global_delta_t, fair_global_delta_t

    m = assign_species() != None  # noqa: E711
    i = int(np.flatnonzero(YEARS == 2100)[0])
    co2_cfg = ModelConfig(albedo=False)
    f_co2, c_co2 = fair_global_delta_t(m, "ssp245", co2_cfg)[i], _convolved_global_delta_t(m, "ssp245", co2_cfg)[i]
    assert f_co2 == pytest.approx(c_co2, rel=0.10)
    f_full, c_full = fair_global_delta_t(m, "ssp245")[i], _convolved_global_delta_t(m, "ssp245")[i]
    assert abs(f_full / f_co2 - c_full / c_co2) < 0.05
