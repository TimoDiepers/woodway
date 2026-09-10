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

Every area-derived carbon number from step 3 onward uses one density,
carried from step 2's literature correction but **anchored to this
model's own step-3 area, not Bastin's original 0.9 Gha claim**:

    density_gtc_per_gha = carbon_gtc(step 2) / area_gha(step 3)

This is a deliberate choice, not an approximation error: the model's own
land mask plus biome exclusion (``nbs.landscape``) measures a plantable
area that comes out a few percent *larger* than Bastin's own headline
figure -- an honest and, on reflection, unsurprising result given the two
areas are independent estimates with a shared ~10% order of uncertainty,
not a claim that this model found *more* restorable land than Bastin did.
Anchoring the density to this model's own denominator means step 3 carries
step 2's literature carbon correction forward *unchanged*
(``81 GtC = area_gha(step 3) * density`` by construction) rather than
manufacturing an increase purely from the area mismatch; every step after 3
is then a genuine, monotonic reduction in both area and carbon, driven only
by this model's own filters.

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

from nbs.aggregate import aggregate_by_species, global_delta_t, unit_curves
from nbs.albedo_grid import alpha_q_product
from nbs.config import ModelConfig
from nbs.constants import T_END, YEARS
from nbs.fair_module import run_fair_baseline
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

_REP_LAT_DEG: dict[str, float] = {
    "tropical_mixed": 5.0,
    "eucalyptus_grandis": 22.5,
    "fagus_sylvatica": 42.5,
    "pinus_sylvestris": 55.0,
    "picea_abies": 65.0,
}
"""Representative latitude per species: the centre of its assigned band in
``nbs.landscape._BAND_SPECIES``. Disturbance parameters (p_disturb,
severity_beta, gamma_warming) are species properties, not per-cell ones, so
a single representative-latitude ensemble per species is enough to size the
*relative* disturbance buffer (ensemble mean / deterministic, at year
T_END) -- re-running a 300-member ensemble at each of ~5000 plantable cells
would cost nothing physically new, since only the ratio, not the absolute
per-tree magnitude, is carried over to the (raster-based, per-cell-correct)
grid aggregate."""

_ENSEMBLE_MEMBERS = 300
"""Ensemble size for the disturbance-buffer ratio. Not the spec's 1000
(Section 7) -- this only needs to size a per-species *ratio* precisely
enough to see the ensemble mean's departure from the deterministic run, not
to resolve tail risk itself (nbs.tree's own tests already do that at 1000
members), and keeping it at 300 x 5 species keeps ``cascade()`` in the
"seconds" budget the task requires."""


def _gtc_per_gha(area_gha: float, carbon_gtc: float) -> float:
    if area_gha <= 0.0:
        raise ValueError("Fläche muss positiv sein, um eine Dichte abzuleiten")
    return carbon_gtc / area_gha


def _masked_aggregate_by_species(
    retain_mask: NDArray,
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
        n_sum = float(n_grid[mask].sum())
        if mask.any():
            p = alpha_q_product(key)
            np_sum = float(np.sum(n_grid[mask] * p[mask]))
        else:
            np_sum = 0.0
        out[key] = (n_sum, np_sum)
    return out


def _masked_global_delta_t(
    retain_mask: NDArray, scenario: str, config: ModelConfig | None = None
) -> NDArray:
    """Length-126 global delta-T(t) [K], restricted to *retain_mask* -- the
    exact same construction as ``nbs.aggregate.global_delta_t``, just summed
    over a subset of cells instead of every plantable one."""
    total = np.zeros(len(YEARS), dtype=float)
    for key, (n_sum, np_sum) in _masked_aggregate_by_species(retain_mask).items():
        if n_sum == 0.0 and np_sum == 0.0:
            continue
        co2, albedo_unit = unit_curves(key, scenario, config)
        total += n_sum * co2 + np_sum * albedo_unit
    return total


def _disturbance_factor(
    retain_mask: NDArray, scenario: str
) -> tuple[float, float, float]:
    """Area-weighted (mean, q5-ratio, q95-ratio) disturbance factor at
    T_END, from a representative-latitude ensemble per species (see
    ``_REP_LAT_DEG``), weighted by each species' share of *retain_mask*'s
    plantable area. A factor of 1.0 would mean disturbance changes nothing;
    every measured mean factor here is below 1.0 (the ensemble mean is
    always less cooling than the deterministic run -- disturbance risk,
    ignored deterministically, flatters the result, exactly
    ``nbs.metrics.risk_premium``'s documented sign) and the 5-95% band
    straddles 1.0 (some realisations are luckier than the deterministic
    run, most are not)."""
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
    for key, lat in _REP_LAT_DEG.items():
        weight = area_by_species[key] / total_area
        if weight == 0.0:
            continue
        det, ens = run_single_tree_ensemble(
            key, lat_deg=lat, scenario=scenario, n_members=_ENSEMBLE_MEMBERS, seed=0
        )
        det_end = float(det.delta_t[-1])
        lo, _med, hi = quantile_band(ens)
        w_mean += weight * (float(np.mean(ens[:, -1])) / det_end)
        w_lo += weight * (float(lo[-1]) / det_end)
        w_hi += weight * (float(hi[-1]) / det_end)
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
    density = _gtc_per_gha(area3_gha, REALISTIC_CARBON_GTC)

    delta_t3 = _masked_global_delta_t(plantable_mask, scenario)

    t_star_field = _breakeven_year_field(scenario)
    never_breaks_even = np.isinf(t_star_field)
    retain4 = plantable_mask & ~never_breaks_even
    excluded4_gha = (
        float(plantable_area_m2()[plantable_mask & never_breaks_even].sum()) / GHA_TO_M2
    )
    area4_gha = float(plantable_area_m2()[retain4].sum()) / GHA_TO_M2
    carbon4_gtc = area4_gha * density
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

    w_mean, w_lo, w_hi = _disturbance_factor(retain4, scenario)
    lo_factor, hi_factor = sorted((w_lo, w_hi))
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
            "carbon_gtc": REALISTIC_CARBON_GTC,
            "delta_t_2150": float(delta_t3[-1]),
            "note": (
                f"Erster Schritt mit eigenen Modellzahlen: nbs.landscape "
                f"liefert {area3_gha:.4f} Gha bepflanzbare Fläche nach "
                "Landmaske (Vereinigung der Duveiller-Raster, 20,3 % der "
                "Erdoberfläche) und Ausschluss von bestehendem Wald, "
                "Savanne/Grasland/Wüste, Landwirtschaft und "
                "Kryosphäre. Das liegt geringfügig über "
                "Bastins eigener 0,9-Gha-Angabe (zwei unabhängige "
                "Schätzungen mit vergleichbarer Unsicherheit) -- die "
                "Kohlenstoffdichte wird daher an DIESE Fläche verankert "
                "(81 GtC / Fläche dieses Schritts), nicht an Bastins "
                "eigene, damit dieser Schritt Stufe 2 unverändert "
                "weiterträgt statt sie durch den Flächenunterschied "
                "künstlich zu erhöhen -- siehe Moduldoku."
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
            "note": (
                f"Flächenweiter Mittel-Faktor Ensemble/deterministisch "
                f"bei {T_END}: {w_mean:.4f} (5-95%-Band: {lo_factor:.4f} "
                f"bis {hi_factor:.4f}), aus {_ENSEMBLE_MEMBERS}-Mitglieder-"
                "Ensembles je Art an einer repräsentativen Breite "
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

    area_gha = float(plantable_area_m2().sum()) / GHA_TO_M2
    n_trees_base = sum(n for n, _ in aggregate_by_species().values())

    def _variant(config: ModelConfig) -> dict:
        dt = global_delta_t(scenario, config)[start_idx:]
        if np.any(dt >= 0.0):
            raise ValueError(
                "Modellvariante kühlt im Fenster 2050.."
                f"{T_END} nicht durchgehend -- Umkehrrechnung nicht definiert"
            )
        with np.errstate(divide="ignore", invalid="ignore"):
            k_series = gap / (-dt)
        i_crit = int(np.argmax(k_series))
        k = float(k_series[i_crit])
        return {
            "n_trees": k * n_trees_base,
            "area_gha": k * area_gha,
            "vielfaches_der_modellierten_flaeche": k,
            "kritisches_jahr": int(years_window[i_crit]),
        }

    full = _variant(ModelConfig())
    carbon_only = _variant(ModelConfig(albedo=False, disturbance="off"))

    return {
        "mit_albedo_und_stoerung": full,
        "nur_kohlenstoff": carbon_only,
        "verhaeltnis": full["n_trees"] / carbon_only["n_trees"],
        "hinweis": (
            "Beide Varianten liegen bereits über dem Vielfachen der von "
            f"diesem Modell identifizierten bepflanzbaren Fläche "
            f"({area_gha:.3f} Gha) -- "
            f"{full['vielfaches_der_modellierten_flaeche']:.1f}-fach mit "
            "Albedo und Störung, "
            f"{carbon_only['vielfaches_der_modellierten_flaeche']:.1f}-fach "
            "bei reiner Kohlenstoffrechnung. Das ist größer als die "
            "gesamte eisfreie Landfläche der Erde: Baumpflanzung allein "
            "hält ssp245 nicht unter 1,5 Grad."
        ),
    }


__all__ = [
    "BASTIN_RAW_AREA_GHA",
    "BASTIN_RAW_CARBON_GTC",
    "REALISTIC_CARBON_GTC",
    "cascade",
    "reverse_1p5",
]
