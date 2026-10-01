"""Grid-resolved albedo forcing input, built from the Duveiller (2018) rasters.

Two physically separate quantities feed phi_albedo: the albedo change of the
land surface (Delta_albedo, dimensionless) and the shortwave insolation that
change acts on (q_sw, W/m^2). The author decided (see
docs/superpowers/specs/2026-09-09-albedoquelle-entscheidung.md, "Nachtrag des
Controllers") to keep them as two separate modelled fields rather than
pre-combining them into a single delivered product -- Delta_albedo stays a
free knob for sensitivity analysis, and the covariance the data provider
already measured between the two is recovered, not assumed, by dividing the
provider's own Delta_SWreflected by its own Delta_albedo.

Source data: JRC open data repository, Duveiller, Hooker & Cescatti (2018),
Sci. Data 5, 180014, v2.0 (registered as duveiller_albedo / duveiller_swr in
nbs.datasources.SOURCES). Two files:

- data/raw/alb_det.nc: Delta_albedo, Delta_albedo_ext, SD_, N_
- data/raw/swr_det.nc: Delta_SWreflected, Delta_SWreflected_ext, SD_, N_

Both on a 1 degree grid (iTr=45, mon=12, lat=180, lon=360). iTr concatenates
an origin and a destination IGBP class from the paper's ten-class legend
(PMC5819485): 1 EBF (tropical), 2 DBF, 3 ENF (boreal), 4 DNF, 5 MF,
6 Savannas, 7 Shrublands, 8 Grasslands, 9 Cropland, 10 Wetlands. The dataset
documents land cover *loss* (forest -> open); afforestation is the reverse
transition, so every value read from these files is sign-flipped before it
is called "afforestation" anywhere in this module.

Sign convention throughout this module: delta_alpha < 0 means the forest is
darker than the open land it replaces, which is a positive (warming) forcing
once it reaches phi_albedo_from_product. This is the *opposite* sign of the
dataset's own Delta_albedo, which is positive for the deforestation direction
it actually documents (forest -> open makes the surface brighter).
"""

from __future__ import annotations

import warnings
from functools import lru_cache

import numpy as np
import xarray as xr
from numpy.typing import NDArray

from nbs.datasources import resolve
from nbs.forcing import fallback_delta_alpha, fallback_q_sw
from nbs.grid import N_LAT, N_LON, grid_lats
from nbs.species import get_species

# Species igbp_class -> Duveiller transition code, afforestation direction
# (i.e. the paper's forest -> open code; the sign is flipped where the value
# is read). From the controller's addendum to the decision spec: Code 38 is
# ENF -> Grassland (boreal conifers), 28 is DBF -> Grassland, 18 is
# EBF -> Grassland (tropical broadleaf evergreen). Cropland variants (39, 29,
# 19) are provided for completeness but not exercised beyond this mapping.
_TRANSITION_CODES: dict[tuple[str, str], int] = {
    ("evergreen_needleleaf", "grassland"): 38,
    ("evergreen_needleleaf", "cropland"): 39,
    ("deciduous_broadleaf", "grassland"): 28,
    ("deciduous_broadleaf", "cropland"): 29,
    ("evergreen_broadleaf", "grassland"): 18,
    ("evergreen_broadleaf", "cropland"): 19,
}

DELTA_ALPHA_MIN_ABS = 0.03
"""Guard threshold for the Delta_SWreflected / Delta_albedo division [-].

The quotient is the dataset's own implied insolation, but it blows up as
Delta_albedo approaches zero: measured against the code-38 (ENF ->
Grassland) transition, the raw quotient ranges from -1.8e4 to +5.2e5 W/m^2
before any guard is applied, which is not physically possible surface
shortwave. Restricting to cells with |Delta_albedo| >= 0.03 (a 3-percentage-
point albedo change -- above the ~1-3% measurement noise floor documented in
the decision spec's data coverage discussion) brings the quotient into a
physically plausible band (roughly -50 to +500 W/m^2 for that transition,
still noisy at the tails but no longer dominated by division artefacts).
Masked cells are filled from the zonal climatology instead of discarded; see
_quotient_with_zonal_fill.
"""

ZONAL_BIN_WIDTH_DEG = 10.0
"""Width of the latitude bins used to build the robust insolation climatology.

Chosen empirically: for the code-38 transition, 10-degree bins in the 40-70N
band that actually carries data have several hundred to several thousand
qualifying cell-months per bin per month, which is enough for a median to be
robust against single-cell noise, while narrower bins (e.g. 5 degrees) leave
some months with only a handful of qualifying cells at the band edges.
"""

_RAW_DIR_KEYS = {"albedo": "duveiller_albedo", "swr": "duveiller_swr"}


def _transition_code(species_key: str, baseline: str) -> int:
    sp = get_species(species_key)
    try:
        return _TRANSITION_CODES[(sp.igbp_class, baseline)]
    except KeyError:
        known = ", ".join(sorted(f"{k[0]}/{k[1]}" for k in _TRANSITION_CODES))
        raise KeyError(
            f"keine Duveiller-Transition fuer igbp_class={sp.igbp_class!r}, "
            f"baseline={baseline!r} registriert; bekannt sind: {known}"
        ) from None


@lru_cache(maxsize=None)
def _open(key: str) -> xr.Dataset | None:
    path = resolve(key)
    if path is None:
        return None
    return xr.open_dataset(path)


def _rasters_available() -> bool:
    return _open(_RAW_DIR_KEYS["albedo"]) is not None and _open(_RAW_DIR_KEYS["swr"]) is not None


def product_provenance() -> str:
    """'raster' if both Duveiller files resolve, else 'fallback'.

    Meant for a figure's footer: it reports where the numbers on that figure
    came from, not whether a particular species/baseline/cell happens to have
    data within the raster (that is a separate, expected kind of emptiness --
    e.g. a tropical transition has no valid cells at 60N because there is no
    tropical forest there, which is correct geography, not a fallback).
    """
    return "raster" if _rasters_available() else "fallback"


def _verify_lat_alignment(dataset_lat: NDArray) -> None:
    """Confirm the native 1-degree grid replicates exactly onto the target rows.

    nbs.grid.grid_lats() runs north to south, cell centres 89.75 down to
    -89.75 on a 0.5-degree grid; the Duveiller dataset's lat runs north to
    south too, cell centres 89.5 down to -89.5 on a 1-degree grid. The two
    only agree cell-edge for cell-edge, not centre for centre (they are
    different resolutions), so the check compares edges: each native 1-degree
    cell must span exactly the same latitude range as the pair of 0.5-degree
    target cells it expands into under 2x replication. This is checked, not
    assumed, every time a raster is opened.
    """
    n = len(dataset_lat)
    native_edges = np.linspace(90.0, -90.0, n + 1)
    native_centres = 0.5 * (native_edges[:-1] + native_edges[1:])
    if not np.allclose(dataset_lat, native_centres, rtol=0.0, atol=1e-9):
        raise ValueError(
            "Duveiller-Datensatz: lat-Koordinaten sind keine gleichmaessigen "
            "1-Grad-Zellmittelpunkte wie angenommen."
        )
    target_edges = np.linspace(90.0, -90.0, 2 * n + 1)
    if not np.allclose(target_edges[::2], native_edges, rtol=0.0, atol=1e-9):
        raise ValueError(
            "Duveiller-Gitter (1 Grad) passt nicht per 2x-Verdopplung auf "
            "nbs.grid.grid_lats() (0.5 Grad); Regridding-Annahme ungueltig."
        )


def _verify_lon_alignment(dataset_lon: NDArray) -> None:
    """Same check as _verify_lat_alignment, for longitude."""
    n = len(dataset_lon)
    native_edges = np.linspace(-180.0, 180.0, n + 1)
    native_centres = 0.5 * (native_edges[:-1] + native_edges[1:])
    if not np.allclose(dataset_lon, native_centres, rtol=0.0, atol=1e-9):
        raise ValueError(
            "Duveiller-Datensatz: lon-Koordinaten sind keine gleichmaessigen "
            "1-Grad-Zellmittelpunkte wie angenommen."
        )
    target_edges = np.linspace(-180.0, 180.0, 2 * n + 1)
    if not np.allclose(target_edges[::2], native_edges, rtol=0.0, atol=1e-9):
        raise ValueError(
            "Duveiller-Gitter (1 Grad) passt nicht per 2x-Verdopplung auf "
            "nbs.grid.grid_lons() (0.5 Grad); Regridding-Annahme ungueltig."
        )


def _regrid(native_180x360: NDArray) -> NDArray:
    """Exact 1-degree -> 0.5-degree regrid by 2x replication on both axes.

    Every 1-degree cell maps onto exactly four 0.5-degree cells with no
    overlap and no gap, so plain replication is exact and needs no
    interpolation library.
    """
    out = np.repeat(np.repeat(native_180x360, 2, axis=0), 2, axis=1)
    assert out.shape == (N_LAT, N_LON)
    return out


def _load_monthly(kind: str, species_key: str, baseline: str, extended: bool) -> NDArray | None:
    """(12, 180, 360) monthly field straight out of the dataset, dataset sign.

    kind is 'albedo' or 'swr'. Returns None if the raster is unavailable.

    The species/baseline pair is validated before checking data availability,
    so an unknown baseline raises the same way whether or not the raster
    happens to be present -- callers should not see different error behaviour
    on a fresh checkout than in an environment with the data downloaded.
    """
    code = _transition_code(species_key, baseline)
    ds = _open(_RAW_DIR_KEYS[kind])
    if ds is None:
        return None
    var_root = "Delta_albedo" if kind == "albedo" else "Delta_SWreflected"
    var = var_root + ("_ext" if extended else "")
    da = ds[var].sel(iTr=code)
    _verify_lat_alignment(da["lat"].values)
    _verify_lon_alignment(da["lon"].values)
    return np.asarray(da.values, dtype=float)


def _quotient_with_zonal_fill(a: NDArray, s: NDArray, lat: NDArray) -> NDArray:
    """Monthly implied insolation s/a [W/m^2], guarded and gap-filled.

    a, s: (mon, lat, lon) dataset-sign Delta_albedo / Delta_SWreflected.
    lat: (lat,) native cell-centre latitudes, same order as a's lat axis.

    Cells with |a| below DELTA_ALPHA_MIN_ABS are masked (the quotient there
    is dominated by division noise, not signal) and filled from the median
    quotient of the other cells in the same month and the same
    ZONAL_BIN_WIDTH_DEG latitude band that do pass the threshold. A cell
    stays NaN only if it has no data at all, or if its whole zonal band has
    no qualifying cell in that month -- both of which mean "this transition
    has no signal here", which is a real geographic absence, not something to
    paper over.
    """
    valid_data = np.isfinite(a) & np.isfinite(s)
    passes = valid_data & (np.abs(a) >= DELTA_ALPHA_MIN_ABS)

    q = np.full(a.shape, np.nan, dtype=float)
    q[passes] = s[passes] / a[passes]

    bin_edges = np.arange(-90.0, 90.0 + ZONAL_BIN_WIDTH_DEG, ZONAL_BIN_WIDTH_DEG)
    bin_idx = np.clip(np.digitize(lat, bin_edges) - 1, 0, len(bin_edges) - 2)

    n_mon = a.shape[0]
    for m in range(n_mon):
        for bi in range(len(bin_edges) - 1):
            rows = np.where(bin_idx == bi)[0]
            if rows.size == 0:
                continue
            block_pass = passes[m][rows, :]
            if not block_pass.any():
                continue
            clim = float(np.median(q[m][rows, :][block_pass]))
            need_fill = valid_data[m][rows, :] & ~block_pass
            if need_fill.any():
                block = q[m][rows, :]
                block[need_fill] = clim
                q[m][rows, :] = block
    return q


@lru_cache(maxsize=None)
def _fallback_row_values() -> tuple[NDArray, NDArray]:
    lat = grid_lats()
    da = np.array([fallback_delta_alpha(x) for x in lat])
    qsw = np.array([fallback_q_sw(x) for x in lat])
    return da, qsw


def _broadcast_rows(row_values: NDArray) -> NDArray:
    return np.repeat(row_values[:, None], N_LON, axis=1)


def _nanmean_over_months(monthly: NDArray) -> NDArray:
    """np.nanmean over axis 0, without the "Mean of empty slice" warning.

    A cell with no valid month at all is expected here: this transition has
    no signal outside the land-cover types it actually connects (e.g. a
    tropical transition has nothing to say at 60N), and NaN is the correct,
    intentional result for it, not a bug to be flagged.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return np.nanmean(monthly, axis=0)


def _interpolate_missing_months(monthly: NDArray) -> NDArray:
    """Bridge missing months of a (12, lat, lon) field within each cell.

    A cell with a local retrieval can still lack single months: Duveiller
    has no albedo under snow, in polar night or under persistent cloud
    (for transition 38, 47 % of the local cells miss at least one month,
    mostly November to February). Averaging only the months that exist
    weights the annual mean towards the months with data. Each gap is
    filled linearly from the same cell's neighbouring months, wrapping
    across the year boundary (December borders January). A cell with a
    single valid month is held at that value; a cell with none stays NaN
    for the zonal and table tiers.
    """
    out = monthly.copy()
    n_valid = np.isfinite(monthly).sum(axis=0)
    months = np.arange(12)
    for i, j in np.argwhere((n_valid > 0) & (n_valid < 12)):
        series = monthly[:, i, j]
        ok = np.isfinite(series)
        if ok.sum() == 1:
            out[:, i, j] = series[ok][0]
            continue
        xs = np.concatenate([months[ok] - 12, months[ok], months[ok] + 12])
        ys = np.tile(series[ok], 3)
        out[:, i, j] = np.interp(months, xs, ys)
    return out


@lru_cache(maxsize=None)
def _delta_alpha_grid_cached(species_key: str, baseline: str, extended: bool) -> NDArray:
    a = _load_monthly("albedo", species_key, baseline, extended)
    if a is None:
        da, _ = _fallback_row_values()
        return _broadcast_rows(da)
    afforestation = -a  # dataset documents forest -> open; afforestation reverses it
    annual = _nanmean_over_months(afforestation)  # (180, 360)
    return _regrid(annual)


@lru_cache(maxsize=None)
def _insolation_grid_cached(species_key: str, baseline: str, extended: bool) -> NDArray:
    a = _load_monthly("albedo", species_key, baseline, extended)
    s = _load_monthly("swr", species_key, baseline, extended)
    if a is None or s is None:
        _, qsw = _fallback_row_values()
        return _broadcast_rows(qsw)
    ds_alb = _open(_RAW_DIR_KEYS["albedo"])
    code = _transition_code(species_key, baseline)
    lat = ds_alb["Delta_albedo"].sel(iTr=code)["lat"].values
    q = _quotient_with_zonal_fill(a, s, lat)
    annual = _nanmean_over_months(q)  # (180, 360)
    return _regrid(annual)


def _native_lat_for(species_key: str, baseline: str) -> NDArray | None:
    """Native 1-degree lat coordinate for the given species/baseline, or None
    if the raster is unavailable. Validates species/baseline first, same as
    _load_monthly, so an unknown baseline raises regardless of data
    availability. lat is a dataset-level coordinate, the same for every iTr
    slice, so no transition code is actually needed to read it -- the
    validation call is for the error behaviour, not the value.
    """
    _transition_code(species_key, baseline)
    ds = _open(_RAW_DIR_KEYS["albedo"])
    if ds is None:
        return None
    return ds["lat"].values


@lru_cache(maxsize=None)
def _monthly_product_native_cached(
    species_key: str, baseline: str, extended: bool
) -> NDArray | None:
    """(12, 180, 360) native-grid monthly afforestation Delta_albedo * q_sw
    product, dataset sign already flipped to afforestation. None if the
    raster is unavailable -- callers apply their own fallback.
    """
    a = _load_monthly("albedo", species_key, baseline, extended)
    s = _load_monthly("swr", species_key, baseline, extended)
    if a is None or s is None:
        return None
    lat = _native_lat_for(species_key, baseline)
    q = _quotient_with_zonal_fill(a, s, lat)
    afforestation = -a
    return afforestation * q  # (12, 180, 360)


@lru_cache(maxsize=None)
def _annual_mean_of_monthly_product_cached(
    species_key: str, baseline: str, extended: bool
) -> NDArray:
    monthly = _monthly_product_native_cached(species_key, baseline, extended)
    if monthly is None:
        da, qsw = _fallback_row_values()
        return _broadcast_rows(da * qsw)
    annual = _nanmean_over_months(monthly)
    return _regrid(annual)


@lru_cache(maxsize=None)
def _monthly_product_grid_cached(species_key: str, baseline: str, extended: bool) -> NDArray:
    """(12, 360, 720) regridded monthly product.

    Fallback (no raster): the fallback tables carry no monthly information,
    so every month is set to the same annual fallback scalar, per latitude
    row -- the honest representation of "no seasonal cycle known", not an
    invented one.
    """
    monthly = _monthly_product_native_cached(species_key, baseline, extended)
    if monthly is None:
        da, qsw = _fallback_row_values()
        annual_row = _broadcast_rows(da * qsw)  # (360, 720)
        return np.repeat(annual_row[None, :, :], 12, axis=0)
    return np.stack([_regrid(monthly[m]) for m in range(12)], axis=0)


# --- Three-tier gap fill for the public alpha_q_product / monthly_product ---
#
# The Duveiller raster documents a land-cover *transition*: it only has a
# retrieval where both the pre- and post-transition cover co-occur close
# enough together (the "co-occurrence" cells Duveiller et al. 2018 -- Sci.
# Data 5, 180014 -- describe in their Materials and Methods). For transition
# 38 (ENF -> Grassland, the picea_abies/pinus_sylvestris case) that is only
# 2567 of 64800 native one-degree cells even in the spatially-extended
# variant used here. Because nbs.landscape assigns a species to a cell purely
# by latitude band, with no correlation to where this specific transition's
# co-occurrence cells happen to sit, a global map built only from "local"
# cells would be almost entirely empty for every species -- and worse, an
# earlier version of nbs.aggregate silently treated that emptiness as "zero
# albedo effect", which would have erased the talk's central claim (the same
# measure has opposite signs in different places) for ~91% of the affected
# cells rather than reporting it as missing.
#
# Three tiers, in this priority order, are filled into every cell so that
# alpha_q_product (and monthly_product, kept exactly consistent with it) are
# always fully finite:
#
#   0 "lokal"   -- a real retrieval: the raw monthly-then-averaged product is
#                  finite for that cell (nbs.albedo_grid's own
#                  DELTA_ALPHA_MIN_ABS guard and the quotient's zonal climat-
#                  ology already apply upstream of this tier -- both operate
#                  within a co-occurrence cell, not across cells with none).
#                  Months without a retrieval inside such a cell are bridged
#                  from its own neighbouring months first
#                  (_interpolate_missing_months), so the annual value is a
#                  true twelve-month mean.
#   1 "zonal"   -- no local retrieval, but the species' own transition has at
#                  least one local cell somewhere in the same
#                  ZONAL_BIN_WIDTH_DEG-wide latitude band (signed latitude,
#                  so the Northern and Southern hemispheres never mix): the
#                  median of those cells' product is used. Reusing the same
#                  10-degree bin width already chosen and justified for this
#                  dataset's insolation-quotient zonal fill
#                  (_quotient_with_zonal_fill's docstring) rather than
#                  picking a second, unrelated width: at this resolution a
#                  single bin is already comfortably stable where the
#                  species has any signal at all -- the 60-70N bin for
#                  transition 38 (picea_abies/pinus_sylvestris's own band,
#                  nbs.landscape) holds 623 finite native cells, and the
#                  bins covering the other four species' own latitude bands
#                  hold several hundred each. A bin with zero local cells at
#                  all (every Southern-hemisphere bin for the boreal
#                  transitions -- there is no boreal conifer forest there to
#                  retrieve a transition from) is left for the next tier.
#                  This is a deliberately much simpler stand-in for what
#                  Duveiller et al. (2018) do to extend retrievals beyond
#                  co-occurrence cells: they train a per-transition,
#                  per-month Random Forest on climate and vegetation-index
#                  predictors from the co-occurrence cells and predict onto
#                  the single-class area. A latitude-zone median captures the
#                  same first-order fact that model leans on most -- that
#                  Delta_albedo and q_sw are primarily controlled by
#                  latitude/climate -- without the predictor stack or a
#                  trained model; it approximates that extension, it does
#                  not reimplement it.
#   2 "tabelle" -- neither of the above: the Plan 1 latitude stand-in
#                  (nbs.forcing.fallback_delta_alpha * fallback_q_sw),
#                  evaluated at the cell's own latitude. This is what every
#                  cell already got, uniformly, before this module read any
#                  raster at all -- the same fallback, just now applied per
#                  cell instead of to the whole grid.
_TIER_LOCAL, _TIER_ZONAL, _TIER_TABLE = 0, 1, 2
TIER_NAMES: dict[int, str] = {
    _TIER_LOCAL: "lokal",
    _TIER_ZONAL: "zonal",
    _TIER_TABLE: "tabelle",
}


def _zonal_annual_fill(raw_annual_native: NDArray, lat_native: NDArray) -> tuple[NDArray, NDArray]:
    """Fill NaN cells of a native-grid annual product with the median of the
    same species' own finite cells in the same ZONAL_BIN_WIDTH_DEG latitude
    bin (signed latitude -- hemispheres never share a bin).

    Returns (filled, was_filled); a cell whose whole bin has no finite value
    at all is left NaN in filled (was_filled False there) for the caller's
    table tier to handle -- a real absence of signal in that latitude range,
    not something to paper over with a neighbouring hemisphere's number.
    """
    filled = raw_annual_native.copy()
    was_filled = np.zeros(raw_annual_native.shape, dtype=bool)
    valid = np.isfinite(raw_annual_native)

    bin_edges = np.arange(-90.0, 90.0 + ZONAL_BIN_WIDTH_DEG, ZONAL_BIN_WIDTH_DEG)
    bin_idx = np.clip(np.digitize(lat_native, bin_edges) - 1, 0, len(bin_edges) - 2)

    for bi in range(len(bin_edges) - 1):
        rows = np.where(bin_idx == bi)[0]
        if rows.size == 0:
            continue
        block_valid = valid[rows, :]
        if not block_valid.any():
            continue
        zonal_value = float(np.median(raw_annual_native[rows, :][block_valid]))
        need_fill = ~valid[rows, :]
        if need_fill.any():
            block = filled[rows, :]
            block[need_fill] = zonal_value
            filled[rows, :] = block
            wf = was_filled[rows, :]
            wf[need_fill] = True
            was_filled[rows, :] = wf

    return filled, was_filled


def _fill_tiers_native(
    raw_annual_native: NDArray, lat_native: NDArray
) -> tuple[NDArray, NDArray]:
    """(filled, tier), both native-shaped: filled is fully finite, tier is
    _TIER_LOCAL / _TIER_ZONAL / _TIER_TABLE per cell. See the module-level
    comment above for the three tiers' definitions and priority order.
    """
    local_valid = np.isfinite(raw_annual_native)
    filled = raw_annual_native.copy()
    tier = np.where(local_valid, _TIER_LOCAL, _TIER_TABLE).astype(np.int8)

    zonal_filled, was_zonal = _zonal_annual_fill(raw_annual_native, lat_native)
    use_zonal = (~local_valid) & was_zonal
    filled[use_zonal] = zonal_filled[use_zonal]
    tier[use_zonal] = _TIER_ZONAL

    remaining = ~np.isfinite(filled)
    if remaining.any():
        table_row = np.array(
            [fallback_delta_alpha(float(lat)) * fallback_q_sw(float(lat)) for lat in lat_native]
        )
        table_grid = np.repeat(table_row[:, None], raw_annual_native.shape[1], axis=1)
        filled[remaining] = table_grid[remaining]
        # tier is already _TIER_TABLE here by construction (never touched by
        # the local or zonal branches above).

    assert np.isfinite(filled).all(), "Drei-Stufen-Fuellung sollte nie NaN uebrig lassen"
    return filled, tier


@lru_cache(maxsize=None)
def _monthly_product_native_tiered_cached(
    species_key: str, baseline: str, extended: bool
) -> tuple[NDArray, NDArray] | None:
    """((12, native_lat, native_lon) fully-finite monthly product, (native_lat,
    native_lon) annual tier code), or None if the raster is unavailable at
    all (the caller then uses the whole-grid fallback, as every other
    function in this module already does in that case).

    Cells that needed the zonal or table tier get the *same* value repeated
    across all twelve months -- the same "no seasonal cycle known here"
    convention _monthly_product_grid_cached's fallback branch already uses
    when the whole raster is missing, just applied per cell instead of to
    every cell. This is what makes alpha_q_product exactly the mean of
    monthly_product for every cell, including the filled ones, not just the
    locally-retrieved ones (see monthly_product's and alpha_q_product's
    docstrings).
    """
    monthly_raw = _monthly_product_native_cached(species_key, baseline, extended)
    lat = _native_lat_for(species_key, baseline)
    if monthly_raw is None or lat is None:
        return None

    # Local cells first get their own missing months bridged, so that every
    # month counts with weight 1/12 in the annual mean below.
    monthly_raw = _interpolate_missing_months(monthly_raw)
    raw_annual = _nanmean_over_months(monthly_raw)
    filled_annual, tier = _fill_tiers_native(raw_annual, lat)

    monthly_filled = monthly_raw.copy()
    needs_replace = tier != _TIER_LOCAL
    if needs_replace.any():
        monthly_filled[:, needs_replace] = filled_annual[needs_replace][None, :]

    return monthly_filled, tier


@lru_cache(maxsize=None)
def _product_tiered_cached(
    species_key: str, baseline: str, extended: bool
) -> tuple[NDArray, NDArray]:
    """((12, 360, 720) fully-finite regridded monthly product, (360, 720)
    regridded annual tier code). The single source both alpha_q_product and
    monthly_product read from, so the two can never drift apart."""
    native = _monthly_product_native_tiered_cached(species_key, baseline, extended)
    if native is None:
        da, qsw = _fallback_row_values()
        annual_row = _broadcast_rows(da * qsw)  # (360, 720)
        monthly_grid = np.repeat(annual_row[None, :, :], 12, axis=0)
        tier_grid = np.full((N_LAT, N_LON), _TIER_TABLE, dtype=np.int8)
        return monthly_grid, tier_grid

    monthly_native, tier_native = native
    monthly_grid = np.stack([_regrid(monthly_native[m]) for m in range(12)], axis=0)
    tier_grid = _regrid(tier_native)
    return monthly_grid, tier_grid


def delta_alpha_grid(
    species_key: str, *, baseline: str = "grassland", extended: bool = True
) -> NDArray:
    """(360, 720) annual-mean afforestation Delta_albedo [-].

    The negative of the dataset's forest -> open (deforestation) value:
    negative where the forest is darker than the open land it replaces.
    Falls back to nbs.forcing.fallback_delta_alpha, broadcast across
    longitude, when the raster is unavailable.
    """
    return _delta_alpha_grid_cached(species_key, baseline, extended).copy()


def insolation_grid(
    species_key: str, *, baseline: str = "grassland", extended: bool = True
) -> NDArray:
    """(360, 720) annual-mean surface shortwave insolation [W/m^2].

    Derived monthly as Delta_SWreflected / Delta_albedo (both from the
    dataset's own deforestation-direction values, so the quotient's sign is
    the same regardless of which land-cover direction is read), then
    averaged over the year. Cells where |Delta_albedo| < DELTA_ALPHA_MIN_ABS
    are masked and filled from a zonal (ZONAL_BIN_WIDTH_DEG latitude band)
    monthly climatology built from cells that do pass the threshold. Falls
    back to nbs.forcing.fallback_q_sw, broadcast across longitude, when the
    raster is unavailable.
    """
    return _insolation_grid_cached(species_key, baseline, extended).copy()


def _annual_mean_of_monthly_product(
    species_key: str, baseline: str = "grassland", extended: bool = True
) -> NDArray:
    """(360, 720) W/m^2. The correct way: multiply Delta_albedo by insolation
    month by month, then average over the year.

    This is what alpha_q_product returns. The original Plan 1 hypothesis
    (section 4 of the findings document, before its 2026-09-09 correction)
    argued that averaging Delta_albedo and insolation to two annual numbers
    first and multiplying them (_product_of_annual_means) should understate
    the boreal effect, because spring snow masking needs both fields high at
    once. Measured against the actual code-38 raster this module loads, the
    opposite direction holds instead: at 45N-65N the monthly path is
    *smaller* in magnitude than the naive one, by roughly 15-25% depending on
    latitude (see task-3-report.md, section 5, for the full numbers, and
    seasonal_profile for the underlying monthly shape at any latitude). The
    mechanism: Delta_albedo (snow-masking contrast) peaks in deep winter
    (e.g. January at 60N) when the implied insolation is only ~10-20 W/m^2 --
    those winter months inflate the annual mean of Delta_albedo alone without
    contributing much to the product, which is exactly what
    _product_of_annual_means multiplies against the annual mean of
    insolation. The spring overlap (Delta_albedo still substantial while
    insolation has risen) is real and sharp -- a single spring month's
    product commonly runs 2-4x the annual mean of the monthly path -- but it
    is a brief spike, not enough to outweigh the winter months once averaged.
    This function's own correctness (that it multiplies monthly, not
    annually, which is what actually preserves the within-year covariance) is
    unaffected by that finding -- only the sign of the resulting difference
    from _product_of_annual_means is.
    """
    return _annual_mean_of_monthly_product_cached(species_key, baseline, extended).copy()


def _product_of_annual_means(
    species_key: str, baseline: str = "grassland", extended: bool = True
) -> NDArray:
    """(360, 720) W/m^2. The *wrong* way, kept only so tests can compare
    against it: annual-mean Delta_albedo times annual-mean insolation.

    Do not use this for anything that reaches a slide. Multiplying two
    already-averaged fields discards the within-year covariance between
    albedo contrast and insolation by construction -- that is a
    methodological error regardless of which way the resulting difference
    from _annual_mean_of_monthly_product happens to point. See that
    function's docstring and task-3-report.md, section 5, for the measured
    numbers: for the boreal conifer transition this naive product comes out
    *larger* in magnitude than the correct monthly path, not smaller as the
    original hypothesis expected, because deep-winter months with strong
    Delta_albedo but almost no insolation inflate mean(Delta_albedo) without
    contributing to the true product.
    """
    return delta_alpha_grid(species_key, baseline=baseline, extended=extended) * insolation_grid(
        species_key, baseline=baseline, extended=extended
    )


def alpha_q_product(
    species_key: str, *, baseline: str = "grassland", extended: bool = True
) -> NDArray:
    """(360, 720) W/m^2. Annual mean of the monthly Delta_albedo * q_sw product.

    Negative where the forest is darker than the open land it replaces (the
    resulting forcing from phi_albedo_from_product is then positive/warming
    there). Built month by month, not from two annual means -- see
    _annual_mean_of_monthly_product's docstring for why that matters.

    **Always fully finite.** Every cell is filled from one of three tiers, in
    priority order: a real local retrieval, a zonal (latitude-band) median of
    the same species' other local retrievals, or the Plan 1 latitude
    stand-in -- see the "Three-tier gap fill" comment above
    _zonal_annual_fill for the full reasoning and the per-tier cell counts.
    Use product_provenance_grid / provenance_fractions to find out which
    tier backs any given cell or region; product_provenance() only answers
    the coarser raster-vs-fallback question at the whole-module level.
    Exactly np.mean(monthly_product(species_key, ...), axis=0) -- monthly_product
    is filled by the identical tiers, so the two can never drift apart.
    """
    monthly_grid, _tier = _product_tiered_cached(species_key, baseline, extended)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return np.nanmean(monthly_grid, axis=0)


def monthly_product(
    species_key: str, *, baseline: str = "grassland", extended: bool = True
) -> NDArray:
    """(12, 360, 720) W/m^2. The monthly Delta_albedo * q_sw product, before
    the annual averaging alpha_q_product does.

    Same sign convention as alpha_q_product (negative where the forest is
    darker); alpha_q_product is exactly np.mean(monthly_product(...), axis=0)
    -- both are now always fully finite (see alpha_q_product's docstring for
    the three-tier fill), so that mean needs no NaN-skipping to hold exactly.
    A cell that needed the zonal or table tier gets that single value
    repeated across all twelve months -- the honest representation of "no
    seasonal cycle known here", the same convention already used when the
    whole raster is missing. A locally-retrieved cell is untouched: its real
    monthly shape (e.g. the boreal spring spike -- see seasonal_profile for a
    latitude-band summary of that shape) is exactly what the raster gives.
    """
    monthly_grid, _tier = _product_tiered_cached(species_key, baseline, extended)
    return monthly_grid.copy()


def product_provenance_grid(
    species_key: str, *, baseline: str = "grassland", extended: bool = True
) -> NDArray:
    """(360, 720) int8 array: which tier filled alpha_q_product at each cell.

    0 = "lokal" (a real Duveiller retrieval), 1 = "zonal" (latitude-band
    median of the same species' other retrievals), 2 = "tabelle" (Plan 1
    latitude stand-in). See TIER_NAMES for the code -> German-label mapping,
    and the "Three-tier gap fill" comment above _zonal_annual_fill for the
    full derivation. When the raster is unavailable at all, every cell is 2.
    """
    _monthly_grid, tier_grid = _product_tiered_cached(species_key, baseline, extended)
    return tier_grid.copy()


def provenance_fractions(
    species_key: str, *, baseline: str = "grassland", extended: bool = True
) -> dict[str, float]:
    """Share of *this species' plantable cells* (nbs.landscape.assign_species()
    == species_key) in each provenance tier: {"lokal": ..., "zonal": ...,
    "tabelle": ...}, fractions summing to 1.0 (0.0/0.0/0.0 if the species has
    no plantable cells at all).

    This is the number any figure built on alpha_q_product must be able to
    state alongside it -- a map that is mostly "zonal" or "tabelle" rather
    than "lokal" is still a legitimate product, but only if it says so.
    Restricted to the species' own plantable cells (not the whole grid):
    those are the only cells nbs.aggregate ever actually reads a product
    from, and the whole-grid share would be dominated by irrelevant ocean
    and other-species cells that never influence any result.
    """
    from nbs.landscape import assign_species

    tier_grid = product_provenance_grid(species_key, baseline=baseline, extended=extended)
    mask = assign_species() == species_key
    total = int(mask.sum())
    if total == 0:
        return {name: 0.0 for name in TIER_NAMES.values()}
    sub = tier_grid[mask]
    return {
        TIER_NAMES[code]: float(np.sum(sub == code)) / total for code in TIER_NAMES
    }


def local_coverage(
    species_key: str, *, baseline: str = "grassland", extended: bool = True
) -> dict[str, float]:
    """How far Duveiller's *local* retrievals reach for one species' transition.

    ``provenance_fractions`` answers a different question -- the tier mix over
    the cells this species is actually planted on. This one answers "how much
    of the world does the raster cover at all for this transition", which is
    the number a data-basis slide wants, and returns it against **both**
    denominators, because they differ by a factor of five and quoting one as
    the other is the mistake this function exists to prevent:

    ``globus``    -- local-retrieval cells / all 259 200 grid cells [-]
    ``landmaske`` -- local-retrieval cells / cells in nbs.landscape.land_mask [-]
    ``zellen``    -- the local-retrieval cell count itself

    Measured for picea_abies: 10 268 cells, 4.0% of the globe, 19.5% of the
    land mask. "About 4% of the land area" is therefore wrong by a factor of
    five in one direction, and "about 20% of the Earth" by a factor of five in
    the other.
    """
    from nbs.landscape import land_mask

    tier = product_provenance_grid(species_key, baseline=baseline, extended=extended)
    local = tier == 0
    n_local = int(local.sum())
    return {
        "zellen": float(n_local),
        "globus": n_local / float(local.size),
        "landmaske": n_local / float(land_mask().sum()),
    }


def seasonal_profile(
    species_key: str,
    lat_deg: float,
    *,
    half_width_deg: float = 2.5,
    baseline: str = "grassland",
    extended: bool = True,
) -> dict:
    """Monthly Delta_albedo, insolation and their product, zonally averaged
    over [lat_deg - half_width_deg, lat_deg + half_width_deg] on the native
    1-degree grid, plus the peak month and its ratio to the annual mean.

    Returns a dict:
      - 'delta_alpha_monthly': (12,) afforestation Delta_albedo [-]
      - 'q_sw_monthly': (12,) insolation [W/m^2]
      - 'product_monthly': (12,) Delta_albedo * q_sw [W/m^2], afforestation
        sign (negative where the forest is darker)
      - 'peak_month': int, 1-12, the month of the largest |product_monthly|
      - 'peak_to_annual_ratio': float,
        abs(product_monthly[peak_month]) / abs(mean(product_monthly))

    This is the seasonal shape that _annual_mean_of_monthly_product's
    docstring and task-3-report.md describe in aggregate: Delta_albedo peaks
    in winter (snow-masking contrast), insolation peaks in summer, and the
    product's own peak falls in the spring overlap between the two, well
    above the annual mean -- see the measured peak_to_annual_ratio, which
    grows with latitude in the boreal band.

    Falls back to nbs.forcing.fallback_delta_alpha/fallback_q_sw when the
    raster is unavailable. Those tables carry no monthly information, so
    every month comes out identical: peak_month is arbitrarily 1 and
    peak_to_annual_ratio is exactly 1.0, which is the honest answer to "what
    is the seasonal shape" when none is known, not a real seasonal claim.
    """
    a = _load_monthly("albedo", species_key, baseline, extended)
    s = _load_monthly("swr", species_key, baseline, extended)
    lat = _native_lat_for(species_key, baseline)

    if a is None or s is None or lat is None:
        da, qsw = _fallback_row_values()
        row = int(np.argmin(np.abs(grid_lats() - lat_deg)))
        product_val = float(da[row] * qsw[row])
        return {
            "delta_alpha_monthly": np.full(12, da[row]),
            "q_sw_monthly": np.full(12, qsw[row]),
            "product_monthly": np.full(12, product_val),
            "peak_month": 1,
            "peak_to_annual_ratio": 1.0,
        }

    band = (lat >= lat_deg - half_width_deg) & (lat <= lat_deg + half_width_deg)
    if not band.any():
        raise ValueError(
            f"kein Gitterpunkt in [{lat_deg - half_width_deg}, "
            f"{lat_deg + half_width_deg}] Grad; half_width_deg vergroessern"
        )

    q = _quotient_with_zonal_fill(a, s, lat)
    afforestation = -a
    monthly_prod_native = afforestation * q

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        delta_alpha_monthly = np.nanmean(afforestation[:, band, :], axis=(1, 2))
        q_sw_monthly = np.nanmean(q[:, band, :], axis=(1, 2))
        product_monthly = np.nanmean(monthly_prod_native[:, band, :], axis=(1, 2))

    abs_product = np.abs(product_monthly)
    if not np.isfinite(abs_product).any():
        peak_month = 1
        peak_to_annual_ratio = float("nan")
    else:
        peak_idx = int(np.nanargmax(abs_product))
        annual_mean_abs = abs(float(np.nanmean(product_monthly)))
        peak_month = peak_idx + 1
        peak_to_annual_ratio = (
            float(abs_product[peak_idx] / annual_mean_abs) if annual_mean_abs > 0.0 else float("nan")
        )

    return {
        "delta_alpha_monthly": delta_alpha_monthly,
        "q_sw_monthly": q_sw_monthly,
        "product_monthly": product_monthly,
        "peak_month": peak_month,
        "peak_to_annual_ratio": peak_to_annual_ratio,
    }


__all__ = [
    "DELTA_ALPHA_MIN_ABS",
    "TIER_NAMES",
    "ZONAL_BIN_WIDTH_DEG",
    "alpha_q_product",
    "delta_alpha_grid",
    "insolation_grid",
    "local_coverage",
    "monthly_product",
    "product_provenance_grid",
    "provenance_fractions",
    "seasonal_profile",
    "product_provenance",
]
