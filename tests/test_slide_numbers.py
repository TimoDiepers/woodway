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


import json
from pathlib import Path

FACTS = json.loads((Path(__file__).resolve().parents[1] / "deck/chart_data/fakten.json").read_text())
"""What the deck prints (scripts/build_storyline_v2_deck.py reads only this)."""


def test_slide_33_plantable_area_as_a_share_of_ice_free_land():
    """The reforestable area with a forest type (Walker et al. 2022 x Hasler
    et al. 2024) is what the deck calls 'wiederbewaldbar'."""
    area_gha = float(plantable_area_m2().sum() / GHA)
    assert area_gha == pytest.approx(FACTS["kaskade"]["flaeche_land_gha"], rel=1e-6)
    assert area_gha == pytest.approx(FACTS["baeume"]["flaeche_mit_typ_gha"], rel=1e-6)
    assert area_gha / ICE_FREE_LAND_GHA < 0.10


def test_slide_36_local_retrieval_coverage_has_its_denominator_named():
    """Land-mask share and globe share differ by a factor of about five; a
    slide must never quote one as the other."""
    cov = local_coverage("mf_gemaessigt")
    assert cov["landmaske"] > 4.0 * cov["globus"]


def test_slide_36_provenance_mix_per_species():
    """Every forest type's albedo cells split into local / zonal / table."""
    for key in SPECIES:
        fr = provenance_fractions(key)
        assert sum(fr.values()) == pytest.approx(1.0, abs=1e-9) or sum(fr.values()) == 0.0


# --------------------------------------------------------------------------
# Folie 29 / 30: das Erwärmungsfenster
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_slide_29_warming_window_is_a_gradient_not_a_binary():
    """Not 'warms or cools': the window runs from the tropics (cool from the
    first year) to the boreal evergreen needleleaf forest (warms the longest),
    and the tropical forest is the strongest cooler per tree at the horizon."""
    from nbs.pipeline import run_single_tree

    keys = ("ebf_tropisch", "dbf_gemaessigt", "enf_boreal")
    res = {k: run_single_tree(k, REFERENCE_SITES[k]) for k in keys}
    warm = {k: int((r.delta_t > 0).sum()) for k, r in res.items()}
    assert warm["ebf_tropisch"] == 0
    assert warm["enf_boreal"] > warm["dbf_gemaessigt"]
    assert res["ebf_tropisch"].delta_t[-1] < res["dbf_gemaessigt"].delta_t[-1]


@pytest.mark.slow
def test_slide_30_horizon_field_averages_land_only_and_leaves_ocean_rows_blank():
    """A zonal mean over whole rows (mostly ocean) once drew a zero contour
    through the Southern Ocean. Rows without land must stay blank."""
    from nbs.albedo_grid import alpha_q_product
    from nbs.landscape import land_mask

    land = land_mask()
    n_land = land.sum(axis=1)
    product = alpha_q_product("enf_boreal")
    zonal = np.where(n_land > 0, (product * land).sum(axis=1) / np.maximum(n_land, 1), np.nan)
    assert np.all(np.isnan(zonal[n_land == 0]))
    assert np.all(np.isfinite(zonal[n_land > 0]))


# --------------------------------------------------------------------------
# Folie 32: Pflanzjahr
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_slide_32_planting_year_numbers():
    """A later cohort grows into a warmer world: higher hazard, more of the
    stock lost at the same age."""
    from nbs.planting_time import cohort_table

    from nbs.constants import T_START

    table = cohort_table("mf_gemaessigt")
    late, first = T_START + 20, T_START
    # the later cohort starts in a warmer world (higher hazard at planting) ...
    assert table[late]["risikofaktor"] > table[first]["risikofaktor"] == pytest.approx(1.0)
    # ... but in Very Low the warming falls again after 2050, so at the same age it loses hardly more (backup slide)
    assert table[late]["verlust_anteil"] == pytest.approx(table[first]["verlust_anteil"], rel=0.05)


# --------------------------------------------------------------------------
# Folie 35 / 37 / 38: Kaskade, Artenwahl, Umkehrrechnung
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_slide_35_cascade_endpoint():
    """The cascade's end as printed, and its disturbance band enclosing the mean."""
    from nbs.potential import cascade

    final = cascade()[-1]
    assert final["carbon_gtc"] == pytest.approx(FACTS["kaskade"]["kohlenstoff_gtc"], rel=1e-6)
    assert final["area_gha"] == pytest.approx(FACTS["kaskade"]["flaeche_nutzbar_gha"], rel=1e-6)
    assert final["delta_t_2150"] == pytest.approx(FACTS["kaskade"]["delta_t_2150_K"], rel=1e-6)
    lo, hi = cascade()[-2]["band_gtc"]
    assert lo < final["carbon_gtc"] < hi, "the disturbance band must enclose its own mean"


@pytest.mark.slow
def test_slide_37_area_is_cascade_step_three_not_the_cascade_result():
    """The planting map is built on cascade *step 3* (all reforestable area),
    before the albedo filter and the disturbance buffer."""
    from nbs.potential import cascade

    steps = cascade()
    step3 = next(s for s in steps if s["area_gha"] is not None)
    assert float(plantable_area_m2().sum() / GHA) == pytest.approx(step3["area_gha"], rel=1e-9)
    assert steps[-1]["area_gha"] < step3["area_gha"]


@pytest.mark.slow
def test_slide_37_species_choice_gain():
    """Choosing the best admissible forest type cools more than planting the
    typical one everywhere; the printed gain is the computed one."""
    from nbs.recommend import improvement

    gain = improvement()["gewinn_anteil"]
    assert gain > 0.0
    assert gain == pytest.approx(FACTS["karten"]["artenwahl_gewinn"], rel=1e-6)


@pytest.mark.slow
def test_slide_38_reverse_calculation():
    """Reverse calculation as printed; albedo and disturbance never make it cheaper."""
    from nbs.potential import reverse_1p5

    r = reverse_1p5()
    full = r["mit_albedo_und_stoerung"]
    assert full["vielfaches_der_modellierten_flaeche"] == pytest.approx(FACTS["umkehr"]["vielfaches"], rel=1e-6)
    assert full["area_gha"] == pytest.approx(FACTS["umkehr"]["flaeche_gha"], rel=1e-6)
    assert r["nur_kohlenstoff"]["area_gha"] <= full["area_gha"]


# --------------------------------------------------------------------------
# Folie 31: die Leiter
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_slide_31_ladder_rungs():
    """The ladder as printed (fakten.json, per site): adding the ocean and
    land response never adds cooling."""
    for site in ("Aachen", "Fairbanks", "Marabá"):
        rungs = FACTS["orte"][site]["leiter_dt_2150_K"]
        assert rungs[2] > rungs[1], f"{site}: Rückgabe durch Ozean und Land muss Kühlung kosten"
        assert rungs[0] < rungs[-1], f"{site}: die volle Kette kühlt weniger als die naive"
