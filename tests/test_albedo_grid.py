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
    _annual_mean_of_monthly_product,
    _load_monthly,
    _product_of_annual_means,
    _regrid,
    alpha_q_product,
    delta_alpha_grid,
    insolation_grid,
    product_provenance,
)
from nbs.datasources import resolve
from nbs.forcing import fallback_delta_alpha, fallback_q_sw, phi_albedo, phi_albedo_from_product
from nbs.grid import grid_lats
from nbs.species import get_species

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
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Measured against the real code-38 (ENF -> Grassland) raster, the "
        "monthly-then-averaged product is *smaller* in magnitude than the "
        "naive product of two annual means at 60N, not larger as Plan 1's "
        "latitude-table argument predicted. Verified two ways: (1) across "
        "grid rows 45-71N the monthly path is smaller everywhere, and (2) "
        "restricted to the 138 cells in the 55-65N band that pass the "
        "Delta_albedo guard in all 12 months (so the comparison involves no "
        "zonal-climatology fill at all), mean|monthly|=13.05 W/m^2 vs "
        "mean|naive|=16.57 W/m^2, with only 8/138 cells (5.8%) showing the "
        "opposite ordering. The physical reason: Delta_albedo (snow-masking "
        "contrast) peaks in winter (Jan-Mar, up to 0.28) while the implied "
        "insolation peaks in summer (May-Jul, up to ~224 W/m^2) -- the two "
        "cycles are mostly *anti*-correlated across the year, with only a "
        "narrow spring window (the single largest monthly product, April, "
        "at -36.5 W/m^2) where they briefly overlap. That spike is real but "
        "does not dominate the annual mean. This is not an implementation "
        "bug (the first assertion below, that the two paths differ at all, "
        "does pass) -- see task-3-report.md for the full numbers and the "
        "per-latitude table. Left unmodified per instruction: report the "
        "numbers, do not loosen the tolerance."
    ),
)
def test_monthly_product_differs_from_product_of_annual_means():
    """The load-bearing property this module was built to test for.

    Spring snow masking needs albedo change and insolation to be multiplied
    month by month, because they peak together. Multiplying two annual means
    loses exactly that covariance. If these two agree, the monthly path is not
    being taken and the boreal effect is understated.
    """
    monthly = _annual_mean_of_monthly_product("picea_abies")
    annual = _product_of_annual_means("picea_abies")
    boreal_row = np.argmin(np.abs(grid_lats() - 60.0))
    a, b = monthly[boreal_row, :], annual[boreal_row, :]
    finite = np.isfinite(a) & np.isfinite(b)
    assert finite.any(), "keine gueltigen borealen Zellen"
    assert not np.allclose(a[finite], b[finite], rtol=1e-3)
    assert np.nanmean(np.abs(a[finite])) > np.nanmean(np.abs(b[finite]))


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
