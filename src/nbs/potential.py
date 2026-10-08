"""The Bastin correction cascade (Akt 6) and the reverse 1.5-degree calculation.

``cascade()`` walks Bastin et al. (2019)'s headline claim down through the
corrections the talk's critique makes, one term at a time, exactly the
table in ``docs/superpowers/specs/2026-09-09-baum-klima-geo-potenzial-design.md``
Section 8:

1. Bastin's raw claim (literature, unverified by this model).
2. Realistic carbon densities and soil carbon (a **literature correction,
   not computed here** -- Section 4 of the spec never gives this chain a
   soil-carbon term, so there is nothing in ``src/nbs`` this step could be
   derived from; it is carried in from the published comments and marked
   as such in ``note``).
3. Non-forest biomes excluded: the first step where **this model's own**
   numbers appear -- ``nbs.landscape.plantable_area_m2()``, which by
   construction already only assigns area to land (``land_mask()``, the
   2026-09-10 fix) outside existing forest, savanna/grassland/desert,
   cropland and the kryosphere.
4. The albedo filter: cells whose break-even year never arrives within the
   study horizon (``nbs.map_plots._breakeven_year_field`` returning
   ``inf``, i.e. net delta-T is still positive at ``nbs.constants.T_END``)
   are area that counts against the intervention, not for it.
5. A disturbance buffer, sized from the Monte-Carlo ensemble
   (``nbs.pipeline.run_single_tree_ensemble``): the gap between the
   ensemble mean and the deterministic run at the same year is exactly
   ``nbs.metrics.risk_premium`` -- the amount by which ignoring disturbance
   risk flatters the deterministic result.
6. The usable potential: step 5's numbers restated as the cascade's answer,
   with the ensemble's 5-95% band spelled out in ``note``.

From step 3 onward carbon is this model's own (since 2026-10-05): the
Walker et al. (2022) unrealized above- plus belowground carbon of each
reforestable cell, summed over the cells a step keeps. Soil carbon is not
in it, which is why step 3 lies below step 2's literature correction; every
later step is a genuine reduction by this model's own filters.

``reverse_1p5()`` answers the talk's closing question: scaling up *the
same* corrected species/area mix that ``nbs.landscape`` and
``nbs.aggregate`` already describe (not a new, hypothetical mix), how many
multiples of it would be needed for the resulting global delta-T to bring
the ssp245 baseline back under 1.5 K by 2050 and keep it there through
``nbs.constants.T_END``? Reported for two model variants -- full physics
(CO2, albedo, deterministic disturbance) and carbon-only (albedo off,
disturbance off) -- so the difference between them is exactly the size of
the correction the rest of this module argues for.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.typing import NDArray

from nbs.aggregate import aggregate_by_species, co2_factor_grid, global_delta_t, unit_curves
from nbs.albedo_grid import alpha_q_product
from nbs.config import ModelConfig
from nbs.constants import T_END, YEARS
from nbs.fair_module import run_fair_baseline, run_fair_perturbed
from nbs.grid import grid_lats, grid_lons
from nbs.landscape import assign_species, plantable_area_m2, tree_count
from nbs.map_plots import _breakeven_year_field
from nbs.metrics import quantile_band
from nbs.pipeline import run_single_tree_ensemble
from nbs.species import SPECIES

GHA_TO_M2 = 1e13
"""1 Gha = 1e9 ha = 1e13 m^2."""

BASTIN_2019_CITATION = (
    "Bastin, J.-F. et al. (2019), \"The global tree restoration potential\", "
    "Science 365(6448), 76-79, doi:10.1126/science.aax0848"
)
BASTIN_RAW_AREA_GHA = 0.9
"""Bastin et al. 2019's own headline canopy-cover-addition claim: 0.9 billion
ha (517 billion trees). Checked 2026-09-10 against the published abstract
and multiple independent secondary sources quoting the same figure; not
independently re-derivable from this model (it is the paper's own number,
predating any of the corrections below). Kept for context in step 1's
``note`` only -- ``area_gha`` for steps 1-2 is left ``None`` (see the module
docstring: this model has no area figure of its own until step 3, and using
Bastin's literal 0.9 Gha there would make step 3's independently-measured
area look like an *increase*, which it structurally is not)."""
BASTIN_RAW_CARBON_GTC = 205.0
"""Bastin et al. 2019's headline carbon storage potential at maturity.
Checked 2026-09-10 against the published abstract and multiple independent
secondary sources quoting the same figure."""

ICE_FREE_LAND_GHA = 13.0
"""Earth's ice-free land area, a rounded literature approximation -- not
computed by this model (the same figure and rounding used in
``notebooks/03_potenzial_global.ipynb``'s ``ICE_FREE_LAND_GHA`` constant,
duplicated here so ``reverse_1p5``'s own ``hinweis`` text can be checked by
a test instead of only asserted in prose). ``reverse_1p5``'s required area
(both variants) is *below* this constant, not above it -- see the module's
own ``test_potential.py`` for the pinned relationship."""

REALISTIC_CARBON_GTC = 81.0
"""Literature correction for realistic carbon densities and soil carbon --
**not computed by this model** (Section 4 of the design spec gives this
physics chain no soil-carbon term at all, so there is nothing in
``src/nbs`` this number could be derived from; it is carried in from
outside, unchanged).

Checked 2026-09-10: the published Technical Comments on Bastin et al. (2019)
in Science 366 (2019) -- Veldman et al. (doi:10.1126/science.aay7976) and
Friedlingstein et al. (doi:10.1126/science.aay8060) -- both argue the 205 GtC
figure is roughly five-fold too high once realistic carbon densities, soil
carbon and existing land-cover carbon are accounted for; secondary sources
summarising this literature repeatedly quote 81 GtC (about 39% of the raw
205 GtC) as the resulting corrected figure, and an independently published,
open-access estimate along the same lines (bioRxiv 10.1101/730325,
"Rethinking global carbon storage potential of trees") gives a closely
adjacent 71.7-75.7 GtC. **The 81 GtC figure's exact primary source could not
be confirmed by reading the original comment's full text** (paywalled); it
is used here because the task-7 brief specifies it and because it sits
squarely inside the independently corroborated 71.7-75.7 GtC range, but it
is reported as unverified-in-full-text rather than silently treated as
fully sourced. See ``task-7-report.md`` for the detail."""

_REALISTIC_CARBON_SOURCE_NOTE = (
    "Literaturkorrektur, NICHT vom Modell gerechnet (die Kette hat keinen "
    "Bodenkohlenstoff-Term, Design-Spec Abschnitt 4/14). Quelle: Science-"
    "Kommentare zu Bastin et al. 2019 (Veldman et al., doi:10.1126/"
    "science.aay7976; Friedlingstein et al., doi:10.1126/science.aay8060) "
    "argumentieren, 205 GtC seien rund fünffach zu hoch; 81 GtC (rund "
    "39 %) wird in der Sekundärliteratur wiederholt als Korrekturwert "
    "genannt und liegt neben einer unabhängigen frei zugänglichen "
    "Schätzung von 71,7-75,7 GtC (bioRxiv 10.1101/730325). Die genaue "
    "Primärquelle der Zahl 81 GtC selbst konnte wegen Paywall nicht im "
    "Volltext geprüft werden -- als unbelegt im Volltext gekennzeichnet, "
    "nicht stillschweigend übernommen."
)

_ENSEMBLE_MEMBERS = 300
"""Ensemble size for the disturbance-buffer ratio. Not the spec's 1000
(Section 7) -- this only needs to size a per-species *ratio* precisely
enough to see the ensemble mean's departure from the deterministic run, not
to resolve tail risk itself (nbs.tree's own tests already do that at 1000
members), and keeping it at 300 x 5 species keeps ``cascade()`` in the
"seconds" budget the task requires."""


def _carbon_gtc(mask: NDArray) -> float:
    """Walker et al. (2022) unrealized AGB+BGB carbon summed over *mask*'s
    plantable area [GtC] (Mg C/ha x ha / 1e9)."""
    from nbs.forest_data import carbon_gain_mgc_ha

    return float((carbon_gain_mgc_ha() * plantable_area_m2() / 1e4)[mask].sum() / 1e9)


def _gtc_per_gha(area_gha: float, carbon_gtc: float) -> float:
    if area_gha <= 0.0:
        raise ValueError("Fläche muss positiv sein, um eine Dichte abzuleiten")
    return carbon_gtc / area_gha


def _masked_aggregate_by_species(
    retain_mask: NDArray, config: ModelConfig | None = None
) -> dict[str, tuple[float, float]]:
    """Same shape as ``nbs.aggregate.aggregate_by_species``, restricted to
    cells where *retain_mask* is True. Mirrors that function's logic exactly
    (same N_c, same P_c, same per-species sums) so the two can never drift
    apart in method, only in which cells are summed."""
    species_grid = assign_species()
    n_grid = tree_count()
    out: dict[str, tuple[float, float]] = {}
    for key in SPECIES:
        mask = (species_grid == key) & retain_mask
        n_sum = float((n_grid[mask] * co2_factor_grid(key, config)[mask]).sum())
        if mask.any():
            p = alpha_q_product(key)
            np_sum = float(np.sum(n_grid[mask] * p[mask]))
        else:
            np_sum = 0.0
        out[key] = (n_sum, np_sum)
    return out


def _convolved_global_delta_t(
    retain_mask: NDArray, scenario: str, config: ModelConfig | None = None
) -> NDArray:
    """Global delta-T(t) [K] over *retain_mask* by convolution with FaIR's
    marginal response to a small 2025 pulse (nbs.aggregate.unit_curves) --
    linear in the trees, exact for small signals. Kept for the didactic
    variants FaIR cannot run directly (Joos response, constant effect per kg)."""
    total = np.zeros(len(YEARS), dtype=float)
    for key, (n_sum, np_sum) in _masked_aggregate_by_species(retain_mask, config).items():
        if n_sum == 0.0 and np_sum == 0.0:
            continue
        co2, albedo_unit = unit_curves(key, scenario, config)
        total += n_sum * co2 + np_sum * albedo_unit
    return total


def _forcing_series(
    retain_mask: NDArray, scenario: str, config: ModelConfig
) -> tuple[NDArray, NDArray]:
    """(net CO2 exchange [GtCO2/yr], albedo forcing [W/m^2]) of all trees in
    *retain_mask*, on YEARS: the same trees, carbon levels and albedo products
    as the convolution, summed before the climate model instead of after."""
    from nbs.constants import A_EARTH_M2, M_CO2_PER_C, TAU_ATM
    from nbs.pipeline import run_single_tree
    from nbs.species import get_species, reference_site

    nee = np.zeros(len(YEARS))
    rf = np.zeros(len(YEARS))
    for key, (n_sum, np_sum) in _masked_aggregate_by_species(retain_mask, config).items():
        if n_sum == 0.0 and np_sum == 0.0:
            continue
        res = run_single_tree(key, reference_site(key), scenario, config=config)
        nee -= M_CO2_PER_C * np.asarray(res.trajectory.net_uptake_kgC_yr) * n_sum / 1e12
        if config.albedo:
            closure = np.asarray(res.trajectory.closure, dtype=float)
            rf += -TAU_ATM * closure * get_species(key).stand_area_m2 / A_EARTH_M2 * np_sum
    return nee, rf


@lru_cache(maxsize=256)
def _fair_cached(mask_hash: str, scenario: str, config: ModelConfig, scale: float) -> NDArray:
    mask = _MASKS[mask_hash]
    nee, rf = _forcing_series(mask, scenario, config)
    base = run_fair_baseline(scenario)
    pert = run_fair_perturbed(scale * nee[: len(base)], scale * rf[: len(base)], scenario)
    dt = np.append(pert - base, (pert - base)[-1])  # pad to len(YEARS), as nbs.pipeline does
    dt.setflags(write=False)
    return dt


_MASKS: dict[str, NDArray] = {}


def fair_global_delta_t(
    retain_mask: NDArray, scenario: str = "ssp245", config: ModelConfig | None = None, scale: float = 1.0
) -> NDArray:
    """Global delta-T(t) [K] of all trees in *retain_mask* (times *scale*)
    from one full FaIR run: removals as negative CO2 emissions, albedo as an
    added forcing. FaIR then computes everything state-dependent -- sinks
    that weaken as they fill, a forcing per kg that falls as CO2 rises.
    Used for every area-wide number (since 2026-10-05); a single tree stays
    with the convolution, its 1e-15 K are below FaIR's numerical precision."""
    import hashlib

    config = config or ModelConfig()
    mask = np.asarray(retain_mask, dtype=bool)
    h = hashlib.sha1(mask.tobytes()).hexdigest()
    _MASKS[h] = mask
    return _fair_cached(h, scenario, config, float(scale)).copy()


def _fair_runnable(config: ModelConfig) -> bool:
    return config.carbon_sink == "scenario" and config.co2_forcing == "logarithmic"


def _masked_global_delta_t(
    retain_mask: NDArray, scenario: str, config: ModelConfig | None = None
) -> NDArray:
    """Length-126 global delta-T(t) [K], restricted to *retain_mask*: a direct
    FaIR run where the configuration is FaIR's own physics, else the
    convolution (didactic variants)."""
    config = config or ModelConfig()
    if _fair_runnable(config):
        return fair_global_delta_t(retain_mask, scenario, config)
    return _convolved_global_delta_t(retain_mask, scenario, config)


def _representative_tree(key: str, retain_mask: NDArray) -> tuple[float, float, float] | None:
    """(latitude, longitude, albedo product) of the representative tree of
    forest type *key* inside *retain_mask*, or None if the key keeps no area.

    The disturbance ensemble runs one tree per key and carries only the
    ratio ensemble/deterministic over to the grid. That tree must stand
    where the key actually stays after the filters (a cell the albedo filter
    removed warms, and dividing by a positive Delta-T flips the meaning of
    the quantiles). Since 2026-10-05 the carbon level varies per cell
    (nbs.site_factor), so the tree is a real retained cell: the one closest
    to the area-weighted mean of albedo product and carbon factor."""
    from nbs.site_factor import site_factor_grid

    cells = (assign_species() == key) & retain_mask
    if not cells.any():
        return None
    w = plantable_area_m2()[cells]
    product = alpha_q_product(key)[cells]
    factor = site_factor_grid(key)[cells]
    d = ((product - np.average(product, weights=w)) / (np.std(product) + 1e-12)) ** 2 + (
        (factor - np.average(factor, weights=w)) / (np.std(factor) + 1e-12)
    ) ** 2
    k = int(np.argmin(d))
    rows, cols = np.nonzero(cells)
    return float(grid_lats()[rows[k]]), float(grid_lons()[cols[k]]), float(product[k])


def _disturbance_factor(
    retain_mask: NDArray, scenario: str
) -> tuple[float, float, float]:
    """Area-weighted (mean, low, high) disturbance factor at T_END: ensemble
    Delta-T over deterministic Delta-T of each species' representative tree
    (``_representative_tree``), weighted by its share of *retain_mask*'s
    plantable area.

    Every retained cell cools at T_END by construction (its t* is finite),
    so every ratio is positive; low/high are each species' 5 % / 95 %
    ensemble quantiles mapped to "less cooling" / "more cooling" before
    weighting, so the band always encloses the mean. Summing quantiles over
    species treats all trees as hit together (one stand, fully correlated
    disturbances) -- an upper bound on the spread; independent disturbances
    across millions of trees would average out to the mean."""
    species_grid = assign_species()
    area = plantable_area_m2()
    area_by_species = {
        key: float(area[(species_grid == key) & retain_mask].sum()) for key in SPECIES
    }
    total_area = sum(area_by_species.values())
    if total_area <= 0.0:
        raise ValueError("keine bepflanzbare Fläche nach dem Albedo-Filter übrig")

    w_mean = 0.0
    w_lo = 0.0
    w_hi = 0.0
    for key in SPECIES:
        site = _representative_tree(key, retain_mask)
        if site is None:
            continue
        lat, lon, product = site
        weight = area_by_species[key] / total_area
        det, ens = run_single_tree_ensemble(
            key, lat_deg=lat, scenario=scenario, n_members=_ENSEMBLE_MEMBERS, seed=0,
            delta_alpha=product, q_sw=1.0, lon_deg=lon,
        )
        det_end = float(det.delta_t[-1])
        if det_end >= 0.0:
            raise ValueError(
                f"repräsentativer Baum {key} bei {lat:.1f}° kühlt {T_END} nicht -- "
                "Verhältnis Ensemble/deterministisch nicht definiert"
            )
        lo, _med, hi = quantile_band(ens)
        r_lo, r_hi = sorted((float(lo[-1]) / det_end, float(hi[-1]) / det_end))
        w_mean += weight * (float(np.mean(ens[:, -1])) / det_end)
        w_lo += weight * r_lo
        w_hi += weight * r_hi
    return w_mean, w_lo, w_hi


@lru_cache(maxsize=None)
def _cascade_cached(scenario: str) -> tuple[dict, ...]:
    """The cached computation behind ``cascade()``. Every one of the five
    species' 300-member disturbance ensembles (``_disturbance_factor``) is
    the expensive part of this function; caching by *scenario* means a test
    suite (or a figure script) calling ``cascade()`` repeatedly for the same
    scenario pays that cost once per process, not once per call -- the same
    pattern ``nbs.landscape._compute`` and ``nbs.aggregate``'s unit-curve
    cache already use."""
    plantable_mask = assign_species() != None  # noqa: E711
    area3_gha = float(plantable_area_m2().sum()) / GHA_TO_M2
    carbon3_gtc = _carbon_gtc(plantable_mask)

    delta_t3 = _masked_global_delta_t(plantable_mask, scenario)

    t_star_field = _breakeven_year_field(scenario)
    never_breaks_even = np.isinf(t_star_field)
    retain4 = plantable_mask & ~never_breaks_even
    excluded4_gha = (
        float(plantable_area_m2()[plantable_mask & never_breaks_even].sum()) / GHA_TO_M2
    )
    area4_gha = float(plantable_area_m2()[retain4].sum()) / GHA_TO_M2
    carbon4_gtc = _carbon_gtc(retain4)
    delta_t4 = _masked_global_delta_t(retain4, scenario)

    # Supplementary, stricter check for the brief's "or only after a stated
    # year" reading: how much area only breaks even after 2100. Reported in
    # the note, not used for the primary area/carbon figures above, which
    # follow the design spec's literal "am Horizont" (at T_END) wording.
    stated_year = 2100
    late_or_never = plantable_mask & (
        never_breaks_even | (~np.isnan(t_star_field) & (t_star_field > stated_year))
    )
    late_or_never_gha = float(plantable_area_m2()[late_or_never].sum()) / GHA_TO_M2

    w_mean, lo_factor, hi_factor = _disturbance_factor(retain4, scenario)
    carbon5_gtc = carbon4_gtc * w_mean
    carbon5_lo, carbon5_hi = carbon4_gtc * lo_factor, carbon4_gtc * hi_factor
    delta_t5 = float(delta_t4[-1]) * w_mean
    delta_t5_lo = float(delta_t4[-1]) * lo_factor
    delta_t5_hi = float(delta_t4[-1]) * hi_factor

    steps = [
        {
            "name_de": "Bastin, Rohwert",
            "area_gha": None,
            "carbon_gtc": BASTIN_RAW_CARBON_GTC,
            "delta_t_2150": None,
            "note": (
                f"Unkorrigierte Angabe aus Bastin et al. 2019: "
                f"{BASTIN_RAW_AREA_GHA:.1f} Gha zusätzliche "
                "Kronenbedeckung (517 Mrd. Bäume), 205 GtC "
                "Kohlenstoffspeicherpotenzial bei voller Reife. Geprüft "
                "am 2026-09-10 gegen die Veröffentlichung und mehrere "
                "unabhängige Sekundärquellen -- Titel und beide "
                "Zahlen bestätigt."
            ),
            "quelle": BASTIN_2019_CITATION,
        },
        {
            "name_de": "Realistische Kohlenstoffdichten und Bodenkohlenstoff",
            "area_gha": None,
            "carbon_gtc": REALISTIC_CARBON_GTC,
            "delta_t_2150": None,
            "note": _REALISTIC_CARBON_SOURCE_NOTE,
            "quelle": "Veldman et al. 2019 (doi:10.1126/science.aay7976); "
            "Friedlingstein et al. 2019 (doi:10.1126/science.aay8060); "
            "Zahlenwert unbelegt im Volltext geprüft, siehe note.",
        },
        {
            "name_de": "Nicht-Wald-Biome ausgeschlossen",
            "area_gha": area3_gha,
            "carbon_gtc": carbon3_gtc,
            "delta_t_2150": float(delta_t3[-1]),
            "note": (
                f"Erster Schritt mit eigenen Modellzahlen: {area3_gha:.4f} Gha "
                "wiederbewaldbare Fläche (Walker et al. 2022, R/L + R/H, ohne "
                "Flächen für Ernährung und Siedlung) mit bekanntem Waldtyp "
                "(Hasler et al. 2024). Kohlenstoff = nicht realisiertes "
                "Potenzial ober- und unterirdisch je Zelle (Walker), "
                f"summiert: {carbon3_gtc:.1f} GtC -- ohne Bodenkohlenstoff, "
                "daher unter der Literaturkorrektur von Stufe 2."
            ),
            "quelle": "nbs.landscape.plantable_area_m2 (dieses Modell)",
        },
        {
            "name_de": "Albedo-Filter: kein Ausgleich bis zum Horizont",
            "area_gha": area4_gha,
            "carbon_gtc": carbon4_gtc,
            "delta_t_2150": float(delta_t4[-1]),
            "note": (
                f"{excluded4_gha:.4f} Gha ausgeschlossen: Zellen, deren "
                f"Ausgleichsjahr t* nie vor {T_END} erreicht wird (netto "
                "positiv am Horizont, "
                "nbs.map_plots._breakeven_year_field). Das ist Fläche, "
                "die gegen die Massnahme zählt, nicht für sie -- "
                "ihr Herausnehmen macht die globale Delta-T-Summe "
                f"{T_END} STÄRKER kühlend "
                f"({float(delta_t3[-1]):.4e} K -> {float(delta_t4[-1]):.4e} "
                "K), obwohl die Fläche sinkt: teils negativer Beitrag "
                "im Sinne der Kaskadentabelle. Strengere Lesart (Ausgleich "
                f"erst nach {stated_year} zählt ebenfalls dagegen): "
                f"{late_or_never_gha:.4f} Gha ausgeschlossen."
            ),
            "quelle": "nbs.map_plots._breakeven_year_field (dieses Modell)",
        },
        {
            "name_de": "Störungspuffer aus dem Ensemble",
            "area_gha": area4_gha,
            "carbon_gtc": carbon5_gtc,
            "delta_t_2150": delta_t5,
            "band_gtc": (carbon5_lo, carbon5_hi),
            "note": (
                f"Flächenweiter Mittel-Faktor Ensemble/deterministisch "
                f"bei {T_END}: {w_mean:.4f} (5-95%-Band: {lo_factor:.4f} "
                f"bis {hi_factor:.4f}), aus {_ENSEMBLE_MEMBERS}-Mitglieder-"
                "Ensembles je Art am mittleren Baum ihrer verbliebenen Zellen "
                "(nbs.pipeline.run_single_tree_ensemble), flächen-"
                "gewichtet über die nach Stufe 4 verbleibenden Arten "
                f"kombiniert. Band Kohlenstoff: {min(carbon5_lo, carbon5_hi):.2f} "
                f"bis {max(carbon5_lo, carbon5_hi):.2f} GtC. Band "
                f"Delta-T({T_END}): {min(delta_t5_lo, delta_t5_hi):.4e} bis "
                f"{max(delta_t5_lo, delta_t5_hi):.4e} K."
            ),
            "quelle": "nbs.pipeline.run_single_tree_ensemble (dieses Modell)",
        },
    ]

    steps.append(
        {
            "name_de": "Nutzbares Potenzial",
            "area_gha": area4_gha,
            "carbon_gtc": carbon5_gtc,
            "delta_t_2150": delta_t5,
            "note": (
                f"Endergebnis der Kaskade: {area4_gha:.3f} Gha, "
                f"{carbon5_gtc:.1f} GtC (Band "
                f"{min(carbon5_lo, carbon5_hi):.1f}-"
                f"{max(carbon5_lo, carbon5_hi):.1f} GtC), "
                f"{abs(delta_t5):.4f} K globale Abkühlung bei {T_END} "
                f"unter ssp245 -- {100.0 * carbon5_gtc / BASTIN_RAW_CARBON_GTC:.1f} "
                "% von Bastins unkorrigiertem Rohwert."
            ),
            "quelle": "Kaskadenergebnis dieses Moduls",
        }
    )
    return tuple(steps)


def cascade(scenario: str = "ssp245") -> list[dict]:
    """The Bastin correction cascade, six ordered steps. See the module
    docstring for the derivation of each step and the density-anchoring
    choice that keeps area and carbon monotonically non-increasing from
    step 3 onward.

    Each step is ``{"name_de": str, "area_gha": float | None,
    "carbon_gtc": float | None, "delta_t_2150": float | None, "note": str,
    "quelle": str}``. ``area_gha``/``delta_t_2150`` are ``None`` for the two
    pure-literature steps (1-2), which have no area or model-run figure of
    their own yet. A fresh shallow copy of each step dict is returned every
    call (see ``_cascade_cached``) so a caller can never mutate the cached
    computation out from under a later call.
    """
    return [dict(step) for step in _cascade_cached(scenario)]


def reverse_1p5(scenario: str = "ssp245") -> dict:
    """How many multiples of this model's own corrected species/area mix
    (``nbs.landscape`` / ``nbs.aggregate``, unfiltered by the albedo or
    disturbance steps above -- the broadest honest base to scale) would be
    needed to bring the *scenario* baseline back under 1.5 K by 2050 and
    keep it there through ``nbs.constants.T_END``, for two model variants.

    Returns ``{"mit_albedo_und_stoerung": {...}, "nur_kohlenstoff": {...},
    "verhaeltnis": float, "hinweis": str}``; each variant dict carries
    ``n_trees``, ``area_gha``, ``vielfaches_der_modellierten_flaeche`` (the
    scale factor itself -- >1 already means "more than every plantable
    cell this model identifies, planted several times over") and
    ``kritisches_jahr`` (the year inside the window that sets the
    requirement, i.e. where the ssp245-minus-1.5K gap is hardest to close
    relative to that variant's own cooling per tree).

    Full physics uses ``ModelConfig()`` (CO2 + albedo + deterministic
    disturbance, today's default); carbon-only uses
    ``ModelConfig(albedo=False, disturbance="off")``. Both read the exact
    same tree/area mix from ``nbs.aggregate.aggregate_by_species`` and
    ``nbs.landscape.plantable_area_m2`` -- only the response-function
    physics differs, so the ratio between the two variants isolates exactly
    what ignoring albedo and disturbance would have hidden.
    """
    baseline = run_fair_baseline(scenario)
    baseline = np.append(baseline, baseline[-1])  # pad to len(YEARS), see nbs.pipeline
    if len(baseline) != len(YEARS):
        raise ValueError(f"Basislauf hat Länge {len(baseline)}, erwartet {len(YEARS)}")

    window_start_year = 2050
    start_idx = int(window_start_year) - int(YEARS[0])
    if not (0 <= start_idx < len(YEARS)):
        raise ValueError(f"Startjahr {window_start_year} liegt außerhalb des Studienzeitraums")
    gap = baseline[start_idx:] - 1.5
    years_window = YEARS[start_idx:]

    # Base: the cells that cool by T_END (the cascade's usable area). Since the
    # switch to Walker's area and carbon (2026-10-05) the full reforestable
    # mix warms on net at T_END, and multiples of a warming mix answer nothing.
    from nbs.map_plots import _breakeven_year_field

    base = (assign_species() != None) & np.isfinite(_breakeven_year_field(scenario))  # noqa: E711
    area_gha = float(plantable_area_m2()[base].sum()) / GHA_TO_M2
    n_trees_base = float(tree_count()[base].sum())

    def _variant(config: ModelConfig) -> dict:
        """Smallest multiple k of the cooling area that keeps the scenario at
        or below 1.5 K over the whole window -- searched with full FaIR runs
        (bisection), not by scaling one run: at tens of times the area the
        response is no longer linear (sinks fill, each kg works less)."""
        def excess(k: float) -> NDArray:
            dt = fair_global_delta_t(base, scenario, config, scale=k)[start_idx:]
            return gap + dt  # > 0: still above 1.5 K

        # linear first guess from the convolution, then bracket and bisect
        dt1 = _convolved_global_delta_t(base, scenario, config)[start_idx:]
        if np.any(dt1 >= 0.0):
            raise ValueError(
                "Modellvariante kühlt im Fenster 2050.."
                f"{T_END} nicht durchgehend -- Umkehrrechnung nicht definiert"
            )
        with np.errstate(divide="ignore", invalid="ignore"):
            k_lin = float(np.max(gap / (-dt1)))
        lo, hi = 0.0, max(k_lin, 1.0)
        while np.any(excess(hi) > 0.0):
            lo, hi = hi, 2.0 * hi
            if hi > 1e4:
                raise ValueError("Umkehrrechnung: kein Vielfaches bis 10 000 erreicht 1,5 K")
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            if np.any(excess(mid) > 0.0):
                lo = mid
            else:
                hi = mid
            if hi - lo < 1e-3 * hi:
                break
        k = hi
        i_crit = int(np.argmax(excess(k)))
        return {
            "n_trees": k * n_trees_base,
            "area_gha": k * area_gha,
            "vielfaches_der_modellierten_flaeche": k,
            "kritisches_jahr": int(years_window[i_crit]),
            "vielfaches_linear": k_lin,
        }

    full = _variant(ModelConfig())
    carbon_only = _variant(ModelConfig(albedo=False, disturbance="off"))

    return {
        "mit_albedo_und_stoerung": full,
        "nur_kohlenstoff": carbon_only,
        "verhaeltnis": full["n_trees"] / carbon_only["n_trees"],
        "hinweis": (
            "Beide Varianten liegen beim Vielfachen der Fläche, die in diesem "
            f"Modell bis {T_END} kühlt ({area_gha:.3f} Gha) -- {full['vielfaches_der_modellierten_flaeche']:.1f}-fach "
            "mit Albedo und Störung, "
            f"{carbon_only['vielfaches_der_modellierten_flaeche']:.1f}-fach "
            "bei reiner Kohlenstoffrechnung. Das volle Modell braucht damit "
            f"rund {100.0 * full['area_gha'] / ICE_FREE_LAND_GHA:.0f} % der "
            f"gesamten eisfreien Landfläche der Erde (~{ICE_FREE_LAND_GHA:.0f} "
            "Gha, Näherung) -- "
            + (
                "mehr als diese Fläche überhaupt hergibt"
                if full["area_gha"] > ICE_FREE_LAND_GHA
                else "weniger als diese Fläche, aber ein großer Teil davon"
            )
            + ": Baumpflanzung allein hält ssp245 nicht unter 1,5 Grad."
        ),
    }


__all__ = [
    "BASTIN_RAW_AREA_GHA",
    "BASTIN_RAW_CARBON_GTC",
    "ICE_FREE_LAND_GHA",
    "REALISTIC_CARBON_GTC",
    "cascade",
    "reverse_1p5",
]
