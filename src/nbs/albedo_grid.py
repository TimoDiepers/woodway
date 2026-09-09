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


@lru_cache(maxsize=None)
def _annual_mean_of_monthly_product_cached(
    species_key: str, baseline: str, extended: bool
) -> NDArray:
    a = _load_monthly("albedo", species_key, baseline, extended)
    s = _load_monthly("swr", species_key, baseline, extended)
    if a is None or s is None:
        da, qsw = _fallback_row_values()
        return _broadcast_rows(da * qsw)
    ds_alb = _open(_RAW_DIR_KEYS["albedo"])
    code = _transition_code(species_key, baseline)
    lat = ds_alb["Delta_albedo"].sel(iTr=code)["lat"].values
    q = _quotient_with_zonal_fill(a, s, lat)
    afforestation = -a
    monthly_product = afforestation * q  # (12, 180, 360)
    annual = _nanmean_over_months(monthly_product)
    return _regrid(annual)


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

    This is what alpha_q_product returns. The Plan 1 findings document
    (section 4) argues that averaging Delta_albedo and insolation to two
    annual numbers first and multiplying them (_product_of_annual_means)
    should understate the boreal effect, because spring snow masking needs
    both fields high at once. Measured against the actual code-38 raster this
    module loads, the opposite direction turned up instead: at 45N and 60N
    the monthly path is *smaller* in magnitude than the naive one, because
    Delta_albedo (snow-masking contrast) peaks in winter while the implied
    insolation peaks in summer -- the two are mostly out of phase across the
    year, with only a brief spring overlap that is not enough to dominate the
    annual mean. See task-3-report.md, section 5, for the full numbers. This
    function's own correctness (that it multiplies monthly, not annually,
    which is what actually preserves the within-year covariance) is
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
    numbers: the naive product here actually comes out *larger* in magnitude
    than the correct monthly path for the boreal conifer transition, not
    smaller as the original hypothesis expected -- Delta_albedo and
    insolation are mostly out of phase across the year for that transition,
    not in phase.
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
    _annual_mean_of_monthly_product's docstring. Falls back to
    nbs.forcing.fallback_delta_alpha * nbs.forcing.fallback_q_sw, per
    latitude row, when the raster is unavailable; product_provenance()
    reports which case applied.
    """
    return _annual_mean_of_monthly_product(species_key, baseline=baseline, extended=extended)


__all__ = [
    "DELTA_ALPHA_MIN_ABS",
    "ZONAL_BIN_WIDTH_DEG",
    "alpha_q_product",
    "delta_alpha_grid",
    "insolation_grid",
    "product_provenance",
]
