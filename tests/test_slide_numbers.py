"""Every headline number the deck states, recomputed from the code.

The deck is the product; these tests are what keep it honest. A reconciliation
pass found five wrong figures on slides that had passed review, all of the same
kind: a number that was right for one quantity, printed as another. So this
file does not assert prose -- it asserts the *relationships* the prose claims,
at the tolerance a slide rounds to.

Marked slow where a FaIR-backed run is needed. Read the failure message before
touching a number here: if one of these fails, either the model changed or a
slide is now wrong, and which one it is decides what gets edited.
"""

import numpy as np
import pytest

from nbs.albedo_grid import local_coverage, provenance_fractions
from nbs.constants import YEARS
from nbs.landscape import land_mask_fractions, plantable_area_m2
from nbs.metrics import t_star
from nbs.potential import ICE_FREE_LAND_GHA
from nbs.species import REFERENCE_SITES, SPECIES

GHA = 1e13


def _pct(x: float) -> float:
    return round(x * 100.0, 1)


# --------------------------------------------------------------------------
# Folie 33 / 36: die Landmaske
# --------------------------------------------------------------------------


def test_slide_36_land_mask_is_quoted_as_an_area_share():
    """Slide 36: "12,0 Gha bzw. 23,6 % der Erdoberfläche ... 20,3 % der
    Rasterzellen". Both numbers, both labelled. The earlier version printed the
    cell share as the area share."""
    fr = land_mask_fractions()
    assert round(fr["gha"], 1) == 12.0
    assert _pct(fr["flaeche"]) == 23.6
    assert _pct(fr["zellen"]) == 20.3


def test_slide_33_plantable_area_as_a_share_of_ice_free_land():
    """Slide 33: "0,9488 Gha, das sind 7,3 % der eisfreien Landfläche"."""
    area_gha = float(plantable_area_m2().sum() / GHA)
    assert round(area_gha, 4) == 0.9488
    assert _pct(area_gha / ICE_FREE_LAND_GHA) == 7.3


def test_slide_36_local_retrieval_coverage_has_its_denominator_named():
    """Slide 36: "rund 20 % der Landmaske ... knapp 4 % der Erdoberfläche".
    The two differ by a factor five; the earlier slide quoted the globe share
    as a land share."""
    cov = local_coverage("picea_abies")
    assert 0.18 < cov["landmaske"] < 0.22
    assert 0.035 < cov["globus"] < 0.045
    assert cov["landmaske"] > 4.0 * cov["globus"]


def test_slide_36_provenance_mix_per_species():
    """Slide 36: 29,3 % lokal / 70,7 % zonal für die Fichte, und bei vier von
    fünf Arten ist die zonale Extrapolation in der Mehrheit."""
    fr = provenance_fractions("picea_abies")
    assert _pct(fr["lokal"]) == 29.3
    assert _pct(fr["zonal"]) == 70.7
    zonal_majority = [k for k in SPECIES if provenance_fractions(k)["zonal"] > 0.5]
    assert len(zonal_majority) == 4
    assert "tropical_mixed" not in zonal_majority


# --------------------------------------------------------------------------
# Folie 29 / 30: das Erwärmungsfenster
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_slide_29_warming_window_is_a_gradient_not_a_binary():
    """Slide 29 claimed only the spruce warms and "the other four cool from
    year one". Pine and beech warm too, for 11 and 14 years. The corrected
    slide states all five; this pins the ordering and the two endpoints."""
    from nbs.pipeline import run_single_tree

    years_warm, stars = {}, {}
    for key, lat in REFERENCE_SITES.items():
        res = run_single_tree(key, lat)
        years_warm[key] = int((res.delta_t > 0).sum())
        stars[key] = t_star(res.delta_t, YEARS)

    assert years_warm["picea_abies"] == 45
    assert years_warm["fagus_sylvatica"] == 14
    assert years_warm["pinus_sylvestris"] == 11
    assert years_warm["eucalyptus_grandis"] == 0
    assert years_warm["tropical_mixed"] == 0
    assert stars["picea_abies"] == 2071
    # The tropical stand must stay the strongest cooler at the horizon.
    coolest = min(
        REFERENCE_SITES, key=lambda k: run_single_tree(k, REFERENCE_SITES[k]).delta_t[-1]
    )
    assert coolest == "tropical_mixed"


@pytest.mark.slow
def test_slide_30_horizon_field_averages_land_only_and_leaves_ocean_rows_blank():
    """Slide 30's figure once ran its zonal mean over whole rows, ~80% ocean,
    which drew a zero contour through the Southern Ocean. Rows without land
    must now be blank, and the marked band must be the northern one only."""
    from nbs.aggregate import unit_curves
    from nbs.albedo_grid import alpha_q_product
    from nbs.grid import grid_lats
    from nbs.landscape import land_mask
    from nbs.map_plots import _assignment_band

    land = land_mask()
    n_land = land.sum(axis=1)
    assert int((n_land == 0).sum()) == 90, "Zeilen ohne Land"

    product = alpha_q_product("picea_abies")
    zonal = np.where(
        n_land > 0, (product * land).sum(axis=1) / np.maximum(n_land, 1), np.nan
    )
    assert np.all(np.isnan(zonal[n_land == 0]))
    assert np.all(np.isfinite(zonal[n_land > 0]))

    lo, hi = _assignment_band("picea_abies")
    assert lo > 0 and hi > lo, "die Fichte darf kein Südhalbkugel-Band markiert bekommen"
    assert 60.0 <= lo <= 61.0 and 69.0 <= hi <= 70.0

    co2, alb = unit_curves("picea_abies")
    lats = grid_lats()
    eq = int(np.argmin(np.abs(lats - 0.25)))
    field_eq = co2 + zonal[eq] * alb
    # Slide 30: "am Äquator acht Jahre" -- there is no latitude that cools
    # from year one, which is what the old caption claimed.
    assert int((field_eq > 0).sum()) == 8


# --------------------------------------------------------------------------
# Folie 32: Pflanzjahr
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_slide_32_planting_year_numbers():
    """Slide 32: Risikofaktor 1,52; Verlust 20,9 % statt 16,5 %; t* 2071 -> 2146."""
    from nbs.planting_time import cohort_table

    table = cohort_table("picea_abies")
    assert round(table[2085]["risikofaktor"], 2) == 1.52
    assert _pct(table[2025]["verlust_anteil"]) == 16.5
    assert _pct(table[2085]["verlust_anteil"]) == 20.9
    assert table[2025]["t_star"] == 2071
    assert table[2085]["t_star"] == 2146


# --------------------------------------------------------------------------
# Folie 35 / 37 / 38: Kaskade, Artenwahl, Umkehrrechnung
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_slide_35_cascade_endpoint():
    """Slide 35: 78,2 GtC (Band 69,8-84,7), 0,9313 Gha, 0,2393 K, 38,2 %."""
    from nbs.potential import BASTIN_RAW_CARBON_GTC, cascade

    final = cascade()[-1]
    assert round(final["carbon_gtc"], 1) == 78.2
    assert round(final["area_gha"], 4) == 0.9313
    assert round(final["delta_t_2150"], 4) == -0.2393
    assert _pct(final["carbon_gtc"] / BASTIN_RAW_CARBON_GTC) == 38.2


@pytest.mark.slow
def test_slide_37_area_is_cascade_step_three_not_the_cascade_result():
    """Slide 37 said "0,95 Gha bleiben nach der Kaskade übrig". The planting
    map is built on nbs.landscape's plantable area, which is cascade *step 3*
    -- before the albedo filter and the disturbance buffer take it to 0,9313."""
    from nbs.potential import cascade

    steps = cascade()
    step3 = next(s for s in steps if s["area_gha"] is not None)
    assert round(step3["area_gha"], 4) == 0.9488
    assert round(float(plantable_area_m2().sum() / GHA), 4) == round(step3["area_gha"], 4)
    assert steps[-1]["area_gha"] < step3["area_gha"]


@pytest.mark.slow
def test_slide_37_species_choice_gain():
    """Slide 37: 25,4 % mehr Kühlung, und weder Fichte noch Eukalyptus wird
    irgendwo empfohlen."""
    from nbs.recommend import improvement, summary

    assert _pct(improvement()["gewinn_anteil"]) == 25.4
    stats = summary()
    assert stats["picea_abies"]["flaeche_gha"] == 0.0
    assert stats["eucalyptus_grandis"]["flaeche_gha"] == 0.0
    assert stats["picea_abies"]["flaeche_zugewiesen_gha"] > 0.3


@pytest.mark.slow
def test_slide_38_reverse_calculation():
    """Slide 38: 10,3-fach, 9,76 / 9,58 Gha, rund 75 % der eisfreien Landfläche."""
    from nbs.potential import reverse_1p5

    r = reverse_1p5()
    full = r["mit_albedo_und_stoerung"]
    carbon_only = r["nur_kohlenstoff"]
    assert round(full["vielfaches_der_modellierten_flaeche"], 1) == 10.3
    assert round(full["area_gha"], 2) == 9.76
    assert round(carbon_only["area_gha"], 2) == 9.58
    assert _pct(full["area_gha"] / ICE_FREE_LAND_GHA) == 75.0
    assert full["area_gha"] < ICE_FREE_LAND_GHA, "die Fläche darf das Land nicht übersteigen"


# --------------------------------------------------------------------------
# Folie 31: die Leiter
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_slide_31_ladder_rungs():
    """Slide 31: t* 2025 -> 2048 -> 2048 -> 2049 -> 2071, also "Albedo kostet
    23 Jahre, die Hintergrundkonzentration nochmal 22"."""
    from nbs.variants import run_ladder

    stars = [t_star(res.delta_t, YEARS) for _name, res in run_ladder("picea_abies", 60.0)]
    assert stars == [2025, 2048, 2048, 2049, 2071]
    assert stars[1] - stars[0] == 23
    assert stars[4] - stars[3] == 22
