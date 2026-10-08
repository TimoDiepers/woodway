"""The model against Hasler et al. (2024), Nat. Commun. 15, 2275.

The closest external check available: same question, same data family,
global, and with its own evaluation of the Bastin area this talk's cascade
builds on. The full write-up is
docs/superpowers/specs/2026-09-10-abgleich-hasler-2024.md; these tests pin
the parts that would silently rot -- both the agreements that support the
model and the divergences that must stay disclosed.

Hasler's published figures, quoted here so a reader need not open the paper:

    Bastin-comparable area          916 Mha
    median albedo offset (global)    52 %
    >50 % offset (Bastin area)       48 %
    net climate-negative (Bastin)    29 %
    tropical moist broadleaf >50 %    6 %
    boreal >50 %                     72 %
    temperate grassland, negative    72 %
    carbon density (Bastin area)   63.3 tC/ha  (58 GtC / 916 Mha)
    albedo CO2e median            -120 Mg CO2e/ha (90 % CI 28 to -469)
"""

import numpy as np
import pytest

from nbs.constants import A_CO2_LOG_W_M2_PER_PPM, KG_CO2_PER_PPM
from nbs.landscape import plantable_area_m2
from nbs.species import SPECIES

HASLER_AREA_MHA = 916.0
HASLER_CARBON_DENSITY_TC_HA = 58.0 / 0.916  # 63.3


# --------------------------------------------------------------------------
# Übereinstimmende Bausteine
# --------------------------------------------------------------------------


def test_log_forcing_coefficient_matches_hasler():
    """Hasler Eq. 4 uses RF = 5.35 ln(C/C0), the Myhre et al. (1998)
    coefficient this model also uses. Same law, same constant."""
    assert A_CO2_LOG_W_M2_PER_PPM == 5.35


def test_carbon_mass_per_ppm_matches_hasler():
    """Hasler: 2.13 PgC per ppm. This model stores the CO2 mass instead;
    converted, the two must agree to better than a percent, or the CO2e
    comparison in the findings document is not like-for-like."""
    gtc_per_ppm = KG_CO2_PER_PPM * (12.0 / 44.0) / 1e12
    assert gtc_per_ppm == pytest.approx(2.13, rel=0.01, abs=0)


def test_plantable_area_is_close_to_haslers_bastin_subset():
    """Two independent constructions of "where could tree cover be added":
    Hasler's 916 Mha subset of Bastin and this model's land mask plus biome
    exclusions. Agreement to a few percent is a real check; a factor-two gap
    would mean one of them is measuring something else."""
    area_mha = float(plantable_area_m2().sum() / 1e10)
    assert area_mha == pytest.approx(HASLER_AREA_MHA, rel=0.10, abs=0)


# --------------------------------------------------------------------------
# Der Albedo-Offset, die eigentliche Gegenprobe
# --------------------------------------------------------------------------


HASLER_WALKER_OVER_50 = 0.65
"""Hasler et al. 2024: share of the Walker reforestation map with an albedo
offset above 50 % (889 Mha). Since 2026-10-05 this model's area *is* that map."""


def _static_offset():
    """Hasler's own static formula (400 ppm, mean 100-year airborne fraction
    0.52) on this model's cells: Delta-alpha*q of the typical forest against
    Walker's carbon. Returns (offset %, area weights) on typed cells."""
    from nbs import albedo_grid
    from nbs.animations import _by_type
    from nbs.constants import A_EARTH_M2, TAU_ATM
    from nbs.forest_data import carbon_gain_mgc_ha, typical_type

    prod = _by_type(albedo_grid.alpha_q_product)
    a = plantable_area_m2()
    m = (a > 0) & (typical_type() != None) & np.isfinite(prod)  # noqa: E711
    per_tco2 = 5.35 / 400.0 / (2.13e9 * 44.0 / 12.0)
    co2e = -prod * TAU_ATM * 1e4 / A_EARTH_M2 / per_tco2 / 0.52
    off = co2e / (carbon_gain_mgc_ha() * 44.0 / 12.0) * 100.0
    return off[m], a[m]


@pytest.mark.slow
def test_static_offset_matches_hasler_on_the_same_map():
    """With Hasler's static formula on our cells, the share above 50 % offset
    lands near Hasler's 65 % for the Walker map (measured: 73 %). Agreement here
    is the check that Delta-alpha*q and carbon are right; the rest of the gap
    to the dynamic result is the time course (docs/methods/abgleich-hasler-waldtypen.md)."""
    off, w = _static_offset()
    share = float(w[off > 50.0].sum() / w.sum())
    assert abs(share - HASLER_WALKER_OVER_50) < 0.15


@pytest.mark.slow
def test_dynamic_offset_is_stricter_than_the_static_one():
    """Delta-T in 2150 under SSP2-4.5 counts the time course: a growing tree,
    CO2 flowing back for decades, a fuller atmosphere. That makes the dynamic
    offset larger than Hasler's static one on the same cells -- disclosed on
    the literature slide, pinned here so it cannot flip silently."""
    from nbs.aggregate import albedo_offset_summary

    off, w = _static_offset()
    o = np.argsort(off)
    static_median = float(off[o][np.searchsorted(np.cumsum(w[o]), 0.5 * w.sum())])
    assert albedo_offset_summary()["median"] > static_median


@pytest.mark.slow
def test_offset_ranks_the_biomes_the_way_hasler_does():
    """Tropics least, boreal most offset -- Hasler's ordering, which the
    talk's argument needs. (Hasler: 6 % of tropical moist broadleaf, 72 % of
    the boreal above 50 %; this model is stricter in both, see above.)"""
    from nbs.aggregate import albedo_offset_field
    from nbs.forest_data import zone_name

    field = albedo_offset_field()
    zone = zone_name()
    finite = np.isfinite(field)

    def share_above_50(z):
        band = finite & (zone == z)
        return float(np.mean(field[band] > 50.0))

    tropical, boreal = share_above_50("tropisch"), share_above_50("boreal")
    assert boreal > 0.70, "boreale Zellen müssen erheblich offset-belastet sein"
    assert boreal > 2.0 * tropical


@pytest.mark.slow
def test_the_cascade_albedo_step_is_a_filter_not_a_discount():
    """The cascade's albedo step removes whole cells that are still warming
    at the horizon; the offset discounts every cell. Both stay distinct."""
    from nbs.aggregate import albedo_offset_summary
    from nbs.potential import cascade

    steps = cascade()
    before = next(s for s in steps if s["area_gha"] is not None)
    after = steps[3]
    filtered = 1.0 - after["carbon_gtc"] / before["carbon_gtc"]
    assert 0.0 < filtered < 1.0
    discount = albedo_offset_summary()["median"] / 100.0
    assert discount > filtered, "Filter und Rabatt sind zusammengelaufen"


# --------------------------------------------------------------------------
# Die offengelegten Abweichungen
# --------------------------------------------------------------------------


def test_carbon_density_is_close_to_hasler():
    """Walker's unrealized biomass carbon over the reforestable area (51 tC/ha)
    against Hasler's 63.3 tC/ha over the Bastin area: same data family,
    different area. Before 2026-10-05 the set species ran at about twice
    Hasler's density -- that overshoot is gone; this keeps it gone."""
    from nbs.forest_data import carbon_gain_mgc_ha

    a = plantable_area_m2()
    density = float((carbon_gain_mgc_ha() * a)[a > 0].sum() / a[a > 0].sum())
    assert 0.6 < density / HASLER_CARBON_DENSITY_TC_HA < 1.1


@pytest.mark.slow
def test_model_cannot_reproduce_haslers_dryland_finding():
    """Hasler: temperate grassland/savanna/shrubland is 72 % net climate-
    negative, worse than average. Here drylands (not reforestable, typical
    forest of the neighbourhood) stay better than the plantable average --
    no dryland signal in Delta-alpha (zonal fill). Pinned as a limitation."""
    from nbs.aggregate import _product_no_nan, albedo_offset_summary, co2_factor_grid, unit_curves
    from nbs.forest_data import key_grid
    from nbs.landscape import exclusion_mask

    dryland = exclusion_mask()["savanne_grasland"]
    keys = key_grid(all_cells=True)
    offset = np.full(dryland.shape, np.nan)
    for key in SPECIES:
        band = dryland & (keys == key)
        if not band.any():
            continue
        co2, albedo_unit = unit_curves(key)
        f = co2_factor_grid(key)
        offset[band] = _product_no_nan(key)[band] * float(albedo_unit[-1]) / (-(f[band] * float(co2[-1]))) * 100.0
    values = offset[np.isfinite(offset)]
    net_negative = float(np.mean(values > 100.0))
    assert net_negative < albedo_offset_summary()["ueber_100"], "Trockengebiete schlechter als der Durchschnitt"
    assert net_negative < 0.72, "erreicht Haslers 72 % -- dann die Modellgrenze im Befunddokument neu prüfen"
