"""Tests for nbs.albedo_grid: the separate Delta_albedo / insolation fields
built from the Duveiller (2018) rasters, and their monthly-then-averaged
product.

Raster-dependent tests are marked with _RASTERS_PRESENT so a fresh checkout
(data/raw/ is git-ignored) skips them cleanly instead of failing on missing
files; the generic API tests below run either way, against the raster when
present and against nbs.forcing's fallback tables otherwise.
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from nbs.albedo_grid import (
    DELTA_ALPHA_MIN_ABS,
    TIER_NAMES,
    _annual_mean_of_monthly_product,
    _load_monthly,
    _product_of_annual_means,
    _regrid,
    alpha_q_product,
    delta_alpha_grid,
    insolation_grid,
    monthly_product,
    product_provenance,
    product_provenance_grid,
    provenance_fractions,
    seasonal_profile,
)
from nbs.datasources import resolve
from nbs.forcing import fallback_delta_alpha, fallback_q_sw, phi_albedo, phi_albedo_from_product
from nbs.grid import grid_lats
from nbs.species import SPECIES, get_species

_RASTERS_PRESENT = resolve("duveiller_albedo") is not None and resolve("duveiller_swr") is not None
_needs_rasters = pytest.mark.skipif(
    not _RASTERS_PRESENT,
    reason="data/raw/alb_det.nc und swr_det.nc fehlen (git-ignoriert); "
    "diese Pruefung braucht die echten Duveiller-Raster.",
)


def test_product_has_grid_shape():
    p = alpha_q_product("picea_abies")
    assert p.shape == (360, 720)


def test_product_is_negative_where_forest_is_darker():
    """Sign convention: a darker forest gives a negative delta_alpha, so the
    product is negative and the resulting forcing positive (warming)."""
    p = alpha_q_product("picea_abies")
    boreal = p[np.argmin(np.abs(grid_lats() - 60.0)), :]
    assert np.nanmean(boreal) < 0.0


@_needs_rasters
def test_monthly_product_differs_from_product_of_annual_means():
    """The load-bearing property this module was built to test for -- and the
    corrected version of it, after independent verification against the real
    code-38 (ENF -> Grassland) raster (see
    docs/superpowers/specs/2026-09-09-befunde-fuer-plan-2-und-3.md, section 4,
    as corrected on 2026-09-09, and task-3-report.md sections 5 and 9).

    The original Plan 1 hypothesis was that multiplying two annual means
    *understates* the boreal effect, because spring snow masking needs
    Delta_albedo and insolation high at once. The measured data shows the
    opposite: at the boreal latitudes checked here, the monthly-then-averaged
    product is *smaller* in magnitude than the naive product of two annual
    means, comfortably outside noise (the measured ratio is close to 0.8,
    i.e. the naive product overstates the boreal forcing by roughly 20-25%).

    Why: Delta_albedo (snow-masking contrast) peaks in deep winter -- January
    at 60N runs Delta_albedo ~ -0.25 in afforestation sign -- when the
    implied insolation is only ~10-20 W/m^2. Those winter months inflate
    mean(Delta_albedo) without contributing much to the true product, which
    is exactly what the naive path multiplies against mean(insolation). The
    spring overlap the original hypothesis was about is real and sharp (see
    seasonal_profile: a single spring month's product commonly runs 2-4x the
    annual mean at boreal latitudes), but it is a brief spike, not enough to
    outweigh the long winter stretch once averaged over the year.

    This direction, not a pinned ratio, is asserted below so the test
    survives a future data revision (a different provider version, an
    updated transition-code mapping) without needing hand-tuning, as long as
    the same winter-inflation mechanism holds.
    """
    monthly = _annual_mean_of_monthly_product("picea_abies")
    annual = _product_of_annual_means("picea_abies")
    boreal_row = np.argmin(np.abs(grid_lats() - 60.0))
    a, b = monthly[boreal_row, :], annual[boreal_row, :]
    finite = np.isfinite(a) & np.isfinite(b)
    assert finite.any(), "keine gueltigen borealen Zellen"
    assert not np.allclose(a[finite], b[finite], rtol=1e-3)

    mean_abs_monthly = np.nanmean(np.abs(a[finite]))
    mean_abs_annual = np.nanmean(np.abs(b[finite]))
    # Measured ratio is ~0.79 at this row; 0.90 leaves ample margin on both
    # sides while still ruling out "no real difference" or the reversed
    # (originally hypothesised) direction.
    assert mean_abs_monthly < 0.90 * mean_abs_annual, (
        f"monatlicher Weg ({mean_abs_monthly:.3f} W/m^2) sollte spuerbar "
        f"kleiner sein als das naive Jahresmittel-Produkt "
        f"({mean_abs_annual:.3f} W/m^2), nicht nur numerisch verschieden"
    )


def test_provenance_is_reported():
    assert product_provenance() in {"raster", "fallback"}


def test_forcing_from_product_matches_the_two_argument_form():
    """phi_albedo_from_product must be the same physics, differently fed."""
    sp = get_species("picea_abies")
    closure = np.linspace(0.0, 1.0, 126)
    d_alpha, q = fallback_delta_alpha(60.0), fallback_q_sw(60.0)
    a = phi_albedo(closure, d_alpha, q, sp)
    b = phi_albedo_from_product(closure, d_alpha * q, sp)
    scale = np.abs(a).max()
    assert np.allclose(a, b, rtol=0.0, atol=1e-9 * scale)


def test_fallback_product_reproduces_the_latitude_table():
    """With no raster present the product must equal the Plan 1 stand-ins, so
    the two plans cannot silently disagree about the same latitude.

    The row nearest 60N is evaluated at *that row's own* cell-centre latitude
    (grid_lats() has no row centred on exactly 60.0 -- on a 0.5-degree grid
    every centre sits at a .25/.75 fraction, so the nearest row here is at
    60.25N), not at the literal round number: alpha_q_product's fallback path
    evaluates fallback_delta_alpha/fallback_q_sw at each row's real latitude,
    and this checks that it does so exactly, not that 60.25N happens to equal
    the table's 60-degree breakpoint (it does not -- interpolating to 60.25
    shifts the product by about 0.15%, far more than this test's rel=1e-6).
    """
    if product_provenance() != "fallback":
        pytest.skip("Raster vorhanden, Fallback wird nicht geprueft")
    p = alpha_q_product("picea_abies")
    row = np.argmin(np.abs(grid_lats() - 60.0))
    lat_at_row = grid_lats()[row]
    expected = fallback_delta_alpha(lat_at_row) * fallback_q_sw(lat_at_row)
    assert np.nanmean(p[row, :]) == pytest.approx(expected, rel=1e-6, abs=0)


def test_delta_alpha_grid_and_insolation_grid_have_grid_shape():
    assert delta_alpha_grid("fagus_sylvatica").shape == (360, 720)
    assert insolation_grid("fagus_sylvatica").shape == (360, 720)


def test_monthly_product_has_twelve_grid_layers():
    assert monthly_product("picea_abies").shape == (12, 360, 720)


def test_monthly_product_averages_to_alpha_q_product():
    """alpha_q_product must be exactly the annual mean of monthly_product --
    same field, two granularities, not two independent computations that
    could silently drift apart."""
    mp = monthly_product("picea_abies")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        annual_from_monthly = np.nanmean(mp, axis=0)
    annual_direct = alpha_q_product("picea_abies")
    finite = np.isfinite(annual_from_monthly) & np.isfinite(annual_direct)
    assert finite.sum() > 0
    assert np.allclose(annual_from_monthly[finite], annual_direct[finite], rtol=0.0, atol=1e-9)


def test_seasonal_profile_returns_twelve_months_of_each_field():
    prof = seasonal_profile("picea_abies", 60.0)
    for key in ("delta_alpha_monthly", "q_sw_monthly", "product_monthly"):
        assert prof[key].shape == (12,)
    assert 1 <= prof["peak_month"] <= 12


def test_seasonal_profile_fallback_has_no_seasonal_cycle():
    """Without a raster, the fallback tables carry no monthly information, so
    every month must come out identical rather than an invented shape."""
    if product_provenance() != "fallback":
        pytest.skip("Raster vorhanden, Fallback wird nicht geprueft")
    prof = seasonal_profile("picea_abies", 60.0)
    assert np.allclose(prof["product_monthly"], prof["product_monthly"][0], rtol=0.0, atol=0.0)
    assert prof["peak_to_annual_ratio"] == 1.0


def test_alpha_q_product_returns_fresh_arrays_not_shared_cache_state():
    """Callers must not be able to corrupt the cached grid by mutating what
    they got back."""
    p1 = alpha_q_product("picea_abies")
    p1[np.isfinite(p1)] = 0.0
    p2 = alpha_q_product("picea_abies")
    assert not np.allclose(np.nan_to_num(p2), 0.0)


def test_unknown_baseline_raises_a_clear_error():
    with pytest.raises(KeyError, match="grassland|cropland"):
        delta_alpha_grid("picea_abies", baseline="ocean")


# --- Three-tier gap fill (local / zonal / table) ----------------------------
#
# Runs either way (with or without the raster present): the table tier alone
# already guarantees a fully finite grid when the raster is entirely absent
# (every cell 100% "tabelle"), so these do not need _needs_rasters.


def test_alpha_q_product_is_fully_finite_for_every_species():
    """The three-tier fill (local retrieval, zonal latitude-band median,
    Plan 1 table) must leave no cell unfilled -- a NaN here would propagate
    silently into nbs.aggregate's sums, which is exactly the failure mode
    the fill exists to prevent."""
    for key in SPECIES:
        p = alpha_q_product(key)
        assert np.all(np.isfinite(p)), f"{key}: nicht-endliche Zellen nach der Fuellung"


def test_provenance_fractions_sum_to_one_and_local_is_a_minority():
    """The Duveiller raster only has a retrieval where both land-cover types
    of a transition co-occur, which is inherently a small fraction of the
    globe for any one transition -- so "lokal" is a minority tier for four
    of the five species, whether or not the raster is present (without it,
    "lokal" is exactly 0).

    ``tropical_mixed`` is a documented exception, since
    ``nbs.landscape.land_mask()`` (the fix for the 71.3%-over-ocean
    plantable-area defect): its plantable cells are now confined to real
    vegetated land in the 0-10 degree band, which is exactly where the
    evergreen_broadleaf transition's co-occurrence retrievals cluster (real
    tropical rainforest) -- so restricting the local/zonal/table split to
    *this species' own plantable cells* (``provenance_fractions``' documented
    scope) now finds "lokal" in the majority there. Before the land-mask fix,
    many of tropical_mixed's "plantable" cells were fabricated cells over
    open ocean that the raster naturally has no local retrieval for, which
    diluted the local share below 50% for a reason that had nothing to do
    with geography. Pinned to the measured value so a further change is
    caught rather than silently re-passing this loosened assertion."""
    for key in SPECIES:
        frac = provenance_fractions(key)
        assert set(frac) == set(TIER_NAMES.values())
        total = sum(frac.values())
        # 0.0 only in the degenerate case of a species with no plantable
        # cells at all (provenance_fractions' own documented fallback);
        # every species nbs.landscape assigns has plantable cells, so this
        # should always be the sum-to-one branch in practice.
        assert total == pytest.approx(1.0, rel=0.0, abs=1e-9) or total == 0.0
        if key == "tropical_mixed":
            assert frac["lokal"] == pytest.approx(0.6316489361702128, abs=1e-9), (
                f"tropical_mixed: 'lokal' weicht vom gemessenen Wert nach der "
                f"Landmaskenkorrektur ab ({frac})"
            )
        else:
            assert frac["lokal"] < 0.5, f"{key}: 'lokal' ist keine Minderheit ({frac})"


@_needs_rasters
def test_zonal_tier_reproduces_local_tier_magnitude_in_boreal_band():
    """If the zonal (latitude-band median) tier gave wildly different values
    from the local retrievals it is built from, the extrapolation would be
    worthless. Checked in the 55-65N band for picea_abies (transition 38),
    which this repository's raster fills mostly from the local and zonal
    tiers (no table cells at all in this band): measured mean magnitude is
    -11.37 W/m^2 (n=3340 local cells) vs. -11.36 W/m^2 (n=11060 zonal cells)
    -- a 0.1% relative difference on the mean. 25% leaves ample margin while
    still catching a real failure (a sign flip, an order-of-magnitude miss,
    or a bin-alignment bug).
    """
    p = alpha_q_product("picea_abies")
    tier = product_provenance_grid("picea_abies")
    lat = grid_lats()
    band = (lat >= 55.0) & (lat <= 65.0)

    p_band = p[band, :]
    tier_band = tier[band, :]
    local_vals = p_band[tier_band == 0]
    zonal_vals = p_band[tier_band == 1]
    assert local_vals.size > 100 and zonal_vals.size > 100, (
        "zu wenige lokale/zonale Zellen im borealen Band fuer einen "
        "aussagekraeftigen Vergleich"
    )

    local_mean = float(local_vals.mean())
    zonal_mean = float(zonal_vals.mean())
    assert zonal_mean == pytest.approx(local_mean, rel=0.25, abs=0.0)


# --- Raster-only checks -----------------------------------------------------
#
# Everything below needs data/raw/alb_det.nc and data/raw/swr_det.nc, which
# are git-ignored and not present on a fresh checkout or in CI.


@_needs_rasters
@pytest.mark.parametrize(
    "species_key, lat_lo, lat_hi, expected_delta_albedo, expected_delta_swr",
    [
        # Values from the controller's addendum to the decision spec
        # (docs/superpowers/specs/2026-09-09-albedoquelle-entscheidung.md,
        # "Nachtrag des Controllers"), deforestation direction, computed from
        # the raw (non-extended, satellite-observed only) variable as a
        # per-cell annual mean (mean over months first) then averaged over
        # the band -- the method that reproduces the addendum's numbers
        # almost exactly (code 38 matches to four significant figures).
        ("picea_abies", 55.0, 65.0, 0.1159, 10.717),
        ("fagus_sylvatica", 55.0, 65.0, 0.0907, 6.961),
        ("eucalyptus_grandis", -10.0, 10.0, 0.0151, 3.469),
    ],
)
def test_measured_values_reproduce_the_controllers_addendum(
    species_key, lat_lo, lat_hi, expected_delta_albedo, expected_delta_swr
):
    """Reproduction check against the numbers the controller measured
    directly from the dataset (see the spec's addendum). A 10% relative
    tolerance accommodates the (undocumented in the addendum) exact latitude-
    band edges and rounding; the point is confirming the transition-code
    mapping and sign convention, not bit-exact reproduction.
    """
    sp = get_species(species_key)
    code = {"evergreen_needleleaf": 38, "deciduous_broadleaf": 28, "evergreen_broadleaf": 18}[
        sp.igbp_class
    ]
    a = _load_monthly("albedo", species_key, "grassland", extended=False)
    s = _load_monthly("swr", species_key, "grassland", extended=False)
    assert a is not None and s is not None

    from nbs.datasources import resolve as _resolve
    import xarray as xr

    ds = xr.open_dataset(_resolve("duveiller_albedo"))
    lat = ds["Delta_albedo"].sel(iTr=code)["lat"].values
    band = (lat >= lat_lo) & (lat <= lat_hi)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        cellwise_a = np.nanmean(a[:, band, :], axis=0)
        cellwise_s = np.nanmean(s[:, band, :], axis=0)
    measured_delta_albedo = float(np.nanmean(cellwise_a))
    measured_delta_swr = float(np.nanmean(cellwise_s))

    assert measured_delta_albedo == pytest.approx(expected_delta_albedo, rel=0.10, abs=0)
    assert measured_delta_swr == pytest.approx(expected_delta_swr, rel=0.10, abs=0)


@_needs_rasters
def test_code_38_valid_cell_counts_in_the_boreal_band_match_the_addendum():
    """The controller's addendum reports 2825 satellite-observed and 8637
    spatially-extended valid cell-months for code 38 in 55-65N -- an exact
    check, since these are plain counts with no averaging ambiguity."""
    a_raw = _load_monthly("albedo", "picea_abies", "grassland", extended=False)
    a_ext = _load_monthly("albedo", "picea_abies", "grassland", extended=True)

    from nbs.datasources import resolve as _resolve
    import xarray as xr

    ds = xr.open_dataset(_resolve("duveiller_albedo"))
    lat = ds["Delta_albedo"].sel(iTr=38)["lat"].values
    band = (lat >= 55.0) & (lat <= 65.0)

    assert int(np.isfinite(a_raw[:, band, :]).sum()) == 2825
    assert int(np.isfinite(a_ext[:, band, :]).sum()) == 8637


@_needs_rasters
def test_reconstructed_product_agrees_with_providers_own_swreflected():
    """alpha_q_product must reproduce the provider's own Delta_SWreflected
    annual mean closely, since both are formed from the same monthly fields:
    at any cell-month that passes the Delta_albedo guard, the product is
    exactly -Delta_SWreflected (a_m cancels: (-a_m)*(s_m/a_m) == -s_m). The
    two can only differ where a cell was masked and filled from the zonal
    climatology instead. Disagreement here would mean the delta_alpha/
    insolation separation lost the covariance the provider's own retrieval
    encodes -- exactly the risk the decision spec's addendum flags and asks
    to be checked.
    """
    species_key = "picea_abies"
    p = alpha_q_product(species_key)
    s = _load_monthly("swr", species_key, "grassland", extended=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        provider_afforestation = -_regrid(np.nanmean(s, axis=0))

    lat = grid_lats()
    band = (lat >= 55.0) & (lat <= 65.0)
    p_band = p[band, :]
    prov_band = provider_afforestation[band, :]
    finite = np.isfinite(p_band) & np.isfinite(prov_band)
    assert finite.sum() > 1000, "zu wenige ueberlappende Zellen fuer einen aussagekraeftigen Test"

    p_mean = float(np.nanmean(p_band[finite]))
    prov_mean = float(np.nanmean(prov_band[finite]))
    assert p_mean == pytest.approx(prov_mean, rel=0.10, abs=0)

    # Per-cell agreement should be tight for the large majority of cells --
    # only the zonally-filled ones should show any real spread.
    abs_diff = np.abs(p_band[finite] - prov_band[finite])
    assert np.median(abs_diff) < 0.5, "typische Zellabweichung sollte klein sein"


@_needs_rasters
def test_divide_guard_masks_a_documented_fraction_of_cells():
    """DELTA_ALPHA_MIN_ABS is chosen to remove the division blow-up without
    discarding most of the signal; this pins the fraction so a future change
    to the threshold is a visible, deliberate decision."""
    a = _load_monthly("albedo", "picea_abies", "grassland", extended=True)
    s = _load_monthly("swr", "picea_abies", "grassland", extended=True)
    valid = np.isfinite(a) & np.isfinite(s)
    passes = valid & (np.abs(a) >= DELTA_ALPHA_MIN_ABS)
    masked_fraction = 1.0 - passes.sum() / valid.sum()
    assert 0.15 < masked_fraction < 0.25


@_needs_rasters
def test_seasonal_profile_peaks_in_spring_at_60n():
    """The controller's corrected reading of Plan 1's snow-masking argument:
    the *seasonal peak* of the product is real and falls in spring, even
    though the *annual mean* of the monthly path is smaller than the naive
    annual-times-annual product (test_monthly_product_differs_from_...
    above). Measured peak month at 60N is March, peak-to-annual-mean ratio
    ~2.8; asserted loosely (March-May, ratio > 2) so the test survives a
    provider data revision without needing exact reproduction.
    """
    prof = seasonal_profile("picea_abies", 60.0)
    assert prof["peak_month"] in (3, 4, 5), f"peak_month={prof['peak_month']} nicht im Fruehjahr"
    assert prof["peak_to_annual_ratio"] > 2.0


@_needs_rasters
def test_seasonal_profile_peak_ratio_is_far_smaller_at_45n_than_60n():
    """The latitude dependence is the actual finding: the spring overlap
    between winter-peaking Delta_albedo and summer-peaking insolation gets
    sharper (a bigger peak-to-mean ratio) moving poleward, because the
    winter snow season lengthens and the overlap window narrows and
    intensifies. At 45N there is much less winter snow persistence, so the
    peak is far less pronounced relative to the annual mean.
    """
    ratio_45 = seasonal_profile("picea_abies", 45.0)["peak_to_annual_ratio"]
    ratio_60 = seasonal_profile("picea_abies", 60.0)["peak_to_annual_ratio"]
    assert ratio_45 < ratio_60
    assert ratio_45 < 2.0
