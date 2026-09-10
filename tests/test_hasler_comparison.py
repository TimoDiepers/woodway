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


@pytest.mark.slow
def test_albedo_offset_is_the_same_order_as_haslers():
    """Hasler: median 52 %, 48 % of the Bastin area above 50 %. This model
    lands at 39 % and 39 %. Lower, for reasons the findings document names
    (grassy biomes already excluded here), but the same quantity in the same
    range -- not half of it and not double."""
    from nbs.aggregate import albedo_offset_summary

    s = albedo_offset_summary()
    assert 30.0 < s["median"] < 50.0, "Median-Offset außerhalb der Hasler-Größenordnung"
    assert 0.30 < s["ueber_50"] < 0.50
    assert s["p5"] > 0.0, "kein bepflanzbarer Ort ohne jede Albedo-Strafe"
    assert s["p95"] < 100.0


@pytest.mark.slow
def test_offset_ranks_the_biomes_the_way_hasler_does():
    """Tropics almost untouched, boreal severely offset. Hasler: 6 % of
    tropical moist broadleaf above a 50 % offset, 72 % of the boreal. The
    ordering is the part of the talk's argument that must hold."""
    from nbs.aggregate import albedo_offset_field
    from nbs.grid import grid_lats

    field = albedo_offset_field()
    lats = grid_lats()[:, None] * np.ones((1, 720))
    finite = np.isfinite(field)

    def share_above_50(lo, hi):
        band = finite & (np.abs(lats) >= lo) & (np.abs(lats) < hi)
        return float(np.mean(field[band] > 50.0))

    tropical, boreal = share_above_50(0, 35), share_above_50(60, 70)
    assert tropical < 0.15, "Tropen dürfen nicht erheblich offset-belastet sein"
    assert boreal > 0.70, "boreale Zellen müssen es sein"
    assert boreal > 5.0 * tropical


@pytest.mark.slow
def test_the_cascade_albedo_step_is_a_filter_not_a_discount():
    """The most misreadable number in the talk. The cascade's albedo step
    removes ~2 % of the carbon; Hasler's discount removes 53 % of the same
    area's benefit. Both are right because they answer different questions,
    and the gap between them must stay large enough that nobody can present
    the cascade's 78.2 GtC as an albedo-adjusted figure."""
    from nbs.aggregate import albedo_offset_summary
    from nbs.potential import cascade

    steps = cascade()
    before = next(s for s in steps if s["area_gha"] is not None)
    after = steps[3]
    filtered = 1.0 - after["carbon_gtc"] / before["carbon_gtc"]
    assert filtered < 0.05, "die Kaskadenstufe ist ein Filter, kein Rabatt"

    discount = albedo_offset_summary()["median"] / 100.0
    assert discount > 5.0 * filtered, (
        "Filter und Rabatt sind zusammengelaufen -- dann stimmt eine der beiden "
        "Rechnungen nicht mehr"
    )


# --------------------------------------------------------------------------
# Die offengelegten Abweichungen
# --------------------------------------------------------------------------


def test_carbon_density_is_declared_high_against_hasler():
    """This model's saturation densities run 100-200 tC/ha against Hasler's
    63.3 tC/ha over the Bastin area. That is a known, documented overshoot
    (findings document section 4); this test exists so it cannot grow
    further unnoticed, and so that fixing it is visible as a test change."""
    densities = {
        key: sp.m_max_kgC * (1e4 / sp.stand_area_m2) / 1000.0
        for key, sp in SPECIES.items()
    }
    assert min(densities.values()) >= 90.0
    assert max(densities.values()) <= 210.0
    mean_density = sum(densities.values()) / len(densities)
    ratio = mean_density / HASLER_CARBON_DENSITY_TC_HA
    assert 1.5 < ratio < 2.5, (
        f"Verhältnis zur externen Dichte ist {ratio:.2f} -- der Befundtext nennt "
        "rund das Doppelte; bei einer Korrektur beide zusammen anpassen"
    )


@pytest.mark.slow
def test_model_cannot_reproduce_haslers_dryland_finding():
    """Hasler's headline correction to the boreal-centric story: temperate
    grassland/savanna/shrubland is 72 % net climate-negative, worse than the
    boreal. This model gets nowhere near that on the same kind of land,
    because it gives a dryland cell the same species carbon as a mesic one.

    Pinned as a *limitation*, not a target. If a later version does grow a
    dryland signal, this test fails and the exclusion argument on the slide
    has to be revisited -- which is exactly when it should be."""
    from nbs.aggregate import unit_curves, _product_no_nan
    from nbs.grid import grid_lats
    from nbs.landscape import _BAND_SPECIES, exclusion_mask

    dryland = exclusion_mask()["savanne_grasland"]
    lats = grid_lats()[:, None] * np.ones((1, 720))
    offset = np.full(dryland.shape, np.nan)
    for lo, hi, key in _BAND_SPECIES:
        band = dryland & (np.abs(lats) >= lo) & (np.abs(lats) < hi)
        if not band.any():
            continue
        co2, albedo_unit = unit_curves(key)
        product = _product_no_nan(key)
        offset[band] = product[band] * float(albedo_unit[-1]) / (-float(co2[-1])) * 100.0

    values = offset[np.isfinite(offset)]
    net_negative = float(np.mean(values > 100.0))
    assert net_negative < 0.10, "unerwartet: das Modell sieht plötzlich ein Trockengebietssignal"
    assert net_negative < 0.72 / 3.0, (
        "immer noch weit unter Haslers 72 % -- die Modellgrenze aus Abschnitt 5 "
        "des Befunddokuments besteht fort"
    )
