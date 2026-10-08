"""Representative tree species, one per biome.

Stock parameters are per tree at the stated stand density, not per hectare:
the presentation reasons about a single tree throughout, and the albedo term
needs the tree's own footprint.
"""

from __future__ import annotations

import numpy as np

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class Species:
    """Parameter set for one representative species."""

    key: str
    name_de: str
    name_lat: str

    m_max_kgC: float
    """Saturation carbon stock per tree [kgC]."""
    k: float
    """Chapman-Richards growth rate [1/a]."""
    p: float
    """Chapman-Richards shape parameter [-]."""
    beta_closure: float
    """Exponent linking canopy closure to relative stock [-]."""

    stand_area_m2: float
    """Ground area occupied by one tree [m^2]."""
    alpha_canopy: float
    """Albedo of the closed canopy [-]."""
    igbp_class: str
    """IGBP land cover class, used to look up transition albedo deltas."""

    p_disturb: float
    """Annual disturbance probability at zero background warming [1/a]."""
    severity_beta: tuple[float, float]
    """Beta(a, b) shape of the lost stock fraction given a disturbance."""
    gamma_warming: float
    """Sensitivity of disturbance probability to background warming [1/K]."""
    eps_immediate: float
    """Fraction of disturbed carbon released at once (combustion) [-]."""
    tau_decay_yr: float
    """Decay time of the remaining debris pool [a]."""

    valid_gez: tuple[str, ...]
    """FAO Global Ecological Zones the species may be planted in."""

    sources: dict[str, "ParamSource"] = field(default_factory=dict)
    """Provenance of every parameter above -- see ``ParamSource`` and
    ``PARAMETER_FIELDS``. Complete by test: no field may be missing."""


Herkunft = Literal["literatur", "abgeleitet", "annahme"]


@dataclass(frozen=True)
class ParamSource:
    """Where one parameter value came from, stated honestly.

    ``stufe``:

    ``"literatur"``  the value is read from the named publication.
    ``"abgeleitet"`` computed here from a published value; ``notiz`` says how.
    ``"annahme"``    chosen for plausibility. ``referenz`` then names what the
                     order of magnitude was oriented on -- which is *not* the
                     same as the value being taken from there, and must never
                     be quoted as if it were.

    The distinction exists because an earlier version of this module carried a
    bare citation string per parameter. That reads as "this number is from the
    IPCC" for values that were in fact picked to be plausible, and it covered
    only five of the twelve parameters, leaving the other seven with no
    statement at all.
    """

    stufe: Herkunft
    referenz: str
    notiz: str = ""


PARAMETER_FIELDS: tuple[str, ...] = (
    "m_max_kgC",
    "k",
    "p",
    "beta_closure",
    "stand_area_m2",
    "alpha_canopy",
    "igbp_class",
    "p_disturb",
    "severity_beta",
    "gamma_warming",
    "eps_immediate",
    "tau_decay_yr",
    "valid_gez",
)
"""Every parameter that must carry a ParamSource. Enforced by test_species.py."""

_IPCC = "IPCC 2019 Refinement, Vol. 4 Ch. 4"
_SEIDL = "Seidl et al. 2017, Nat. Clim. Change 7, 395-402"
_BONAN = "Bonan 2008, Science 320, 1444-1449"
_DUVEILLER = "Duveiller, Hooker, Cescatti 2018, Sci. Data 5, 180014"
_FAO_GEZ = "FAO Global Ecological Zones (FRA 2010/2020 Klassifikation)"
_SPEC = (
    "docs/superpowers/specs/2026-09-09-baum-klima-geo-potenzial-design.md, "
    "Abschnitt 5 und Validierungsliste"
)

_OFFEN = (
    "Der Abgleich gegen Ertragstafeln und das IPCC-2019-Refinement steht laut "
    "Spezifikation noch aus; der Wert ist bislang eine plausible Setzung, kein "
    "belegter Literaturwert."
)

# The provenance story is identical for all five species: the same spec fixed
# them in the same way, in one pass, against the same intended sources. Rather
# than repeat five identical dictionaries, they share this one -- and if a
# single species' parameter ever does get a real source, it overrides here.
_COMMON_SOURCES: dict[str, ParamSource] = {
    "m_max_kgC": ParamSource("annahme", _IPCC, _OFFEN),
    "k": ParamSource("annahme", _IPCC, _OFFEN),
    "p": ParamSource("annahme", _IPCC, _OFFEN),
    "beta_closure": ParamSource(
        "annahme",
        _SPEC,
        "Exponent der Bedeckungsgrad-Kennlinie f = (m/m_max)^beta. Frei "
        "gesetzt; beta = 0,5 heisst 'halber Vorrat, rund 70 % Bedeckung'.",
    ),
    "stand_area_m2": ParamSource(
        "annahme",
        _SPEC,
        "Standflaeche eines Baumes, entspricht 1600-2500 Baeumen je Hektar. "
        "Geht linear in den Albedo-Kanal und in jede Flaechenhochrechnung ein.",
    ),
    "alpha_canopy": ParamSource(
        "annahme",
        _BONAN,
        "Groessenordnung an Bonans Kronenalbedo-Werten orientiert. Wird von "
        "der Rasterschicht nicht benutzt: dort kommt Delta_alpha aus dem "
        f"Duveiller-Raster ({_DUVEILLER}).",
    ),
    "igbp_class": ParamSource(
        "abgeleitet",
        _DUVEILLER,
        "Waehlt den Landbedeckungsuebergang im Duveiller-Raster. Die Zuordnung "
        "Art -> IGBP-Klasse ist eindeutig; die Legende der 45 Uebergangscodes "
        "wurde aus PMC5819485 rekonstruiert, sie steht nicht in der Datei.",
    ),
    "p_disturb": ParamSource(
        "annahme",
        _SEIDL,
        "Groessenordnung an Seidls europaeischen Stoerungsraten orientiert; "
        "der artspezifische Wert ist gesetzt, nicht aus der Arbeit entnommen.",
    ),
    "severity_beta": ParamSource(
        "annahme",
        _SPEC,
        "Beta-Verteilung des verlorenen Vorratsanteils. Form frei gesetzt; "
        "der Erwartungswert a/(a+b) ist die einzige Groesse, die der "
        "deterministische Lauf benutzt.",
    ),
    "gamma_warming": ParamSource(
        "annahme",
        _SEIDL,
        "Sensitivitaet der Stoerungsrate gegenueber der Hintergrunderwaermung, "
        "p = p0 exp(gamma T). Fuer alle fuenf Arten gleich gesetzt (0,20 1/K) "
        "-- eine bewusste Vereinfachung, kein artspezifischer Befund. Traegt "
        "die gesamte Aussage der Pflanzjahr-Folie.",
    ),
    "eps_immediate": ParamSource(
        "annahme",
        _SEIDL,
        "Sofort verbrannter Anteil des gestoerten Kohlenstoffs. Die "
        "Spezifikation nennt eps ~ 0,3 fuer Feuer und deutlich kleiner fuer "
        "Sturm; die artspezifische Aufteilung darauf ist gesetzt.",
    ),
    "tau_decay_yr": ParamSource(
        "annahme",
        _SPEC,
        "Zerfallszeit des Totholzpools. Frei gesetzt, waermere Standorte "
        "kuerzer.",
    ),
    "valid_gez": ParamSource(
        "literatur",
        _FAO_GEZ,
        "Zonennamen sind FAO-Klassen. Welche Zonen einer Art zugeordnet sind, "
        "ist eine Setzung nach Standortanspruechen, kein FAO-Datensatz.",
    ),
}


def _sources(**overrides: ParamSource) -> dict[str, ParamSource]:
    """The common provenance table, with per-species exceptions applied."""
    table = dict(_COMMON_SOURCES)
    table.update(overrides)
    return table

# ---- Forest types per climate zone (2026-10-05) -------------------------
# Replaces the five hand-parameterised species. One entry per forest type
# (Hasler et al. 2024, IGBP classes) and climate zone (Walker et al. 2022,
# from FAO GEZ); growth and carbon from published global data, see
# nbs.forest_data. Disturbance per type carries over the earlier species
# values (evergreen needleleaf <- spruce, deciduous needleleaf <- pine,
# deciduous broadleaf <- beech, evergreen broadleaf <- tropical mixed stand,
# mixed forest <- mean of spruce and beech).

_WALKER = "Walker et al. 2022, PNAS 119, e2111312119"
_COOK_PATTON = "Cook-Patton et al. 2020, Nature 585, 545-550"
_POORTER = "Poorter et al. 2016, Nature 530, 211-214"
_HASLER = "Hasler et al. 2024, Nat. Commun. 15, 2275"
_WILLIAMS = "Williams et al. 2026, J. Geophys. Res. Biogeosci. 131, doi:10.1029/2025JG009284"

ALBEDO_HALF_YEARS = 40.0
"""Williams et al. (2026), from satellite chronosequences worldwide: about half
of the albedo decline after reforestation occurs within 40 years, 80 % takes
50-120 years. The canopy closure f = (m/m_max)^beta drives the albedo channel,
so beta is set per entry such that f(40 a) = 0.5. One global rule; Williams
also report slower declines in extratropical and broadleaf forests and faster
ones in the tropics and in needleleaf/mixed forests -- not resolved here."""


_GRUENIG = "Grünig et al. 2026, Science, doi:10.1126/science.adx6329"
_AR6 = "IPCC AR6 WG1 SPM, Tab. SPM.1"

GAMMA_WARMING = 0.26
"""Rise of the disturbance rate with background warming, p = p0 exp(gamma T).
Grünig et al. (2026) project stand-replacing disturbance in Europe by
2081-2100 at +31 / +61 / +122 % (RCP2.6 / 4.5 / 8.5) relative to 1986-2020;
with the global warming of the matching SSPs relative to 1995-2014 (IPCC
AR6: about 0.9 / 1.8 / 3.5 K), gamma = ln(1 + increase) / Delta T gives
0.30 / 0.26 / 0.23 per K; the mean is used. European forests only -- the
one continental projection available; applied to all forest types."""


def _beta_for_half_at(k: float, p: float, years: float = ALBEDO_HALF_YEARS) -> float:
    """beta with ((1 - e^{-k t})^p)^beta = 0.5 at t = *years*."""
    return float(np.log(0.5) / (p * np.log(1.0 - np.exp(-k * years))))

_TYPE_META: dict[str, dict] = {
    "enf": dict(name="Immergrüner Nadelwald", igbp="evergreen_needleleaf", alpha=0.09,
                p_disturb=0.012, severity=(2.0, 2.0), eps=0.30, tau=30.0),
    "dnf": dict(name="Lärchenwald", igbp="deciduous_needleleaf", alpha=0.10,
                p_disturb=0.008, severity=(2.0, 2.5), eps=0.35, tau=25.0),
    "dbf": dict(name="Sommergrüner Laubwald", igbp="deciduous_broadleaf", alpha=0.15,
                p_disturb=0.005, severity=(2.0, 3.0), eps=0.15, tau=20.0),
    "ebf": dict(name="Immergrüner Laubwald", igbp="evergreen_broadleaf", alpha=0.12,
                p_disturb=0.005, severity=(2.0, 4.0), eps=0.25, tau=10.0),
    "mf": dict(name="Mischwald", igbp="mixed", alpha=0.12,
               p_disturb=0.0085, severity=(2.0, 2.5), eps=0.225, tau=25.0),
}
_ZONE_DE = {"tropisch": "tropisch", "subtropisch": "subtropisch", "gemaessigt": "gemäßigt", "boreal": "boreal"}


def _type_sources() -> dict[str, ParamSource]:
    table = dict(_COMMON_SOURCES)
    table.update({
        "m_max_kgC": ParamSource(
            "abgeleitet", _WALKER,
            "Median des nicht realisierten Potenzials (oberirdisch + unterirdisch, ohne Boden) auf den "
            "wiederbewaldbaren Flächen dieses Typs und dieser Zone, je Baum bei 2000 Bäumen/ha. Je Zelle "
            "skaliert mit dem Wert der Zelle (nbs.site_factor)."),
        "k": ParamSource(
            "abgeleitet", f"{_COOK_PATTON}; {_POORTER}",
            "Flächengewichteter Median je Typ und Zone aus der Zuwachsrate der ersten 30 Jahre relativ zum "
            "Walker-Potenzial; begrenzt auf 55 % des Potenzials nach 30 Jahren (Poorter: 90 % nach 66 Jahren)."),
        "p": ParamSource("annahme", "Chapman-Richards", "Formparameter einheitlich 2."),
        "igbp_class": ParamSource("literatur", _HASLER, "Wahrscheinlichste Waldklasse (IGBP) je Zelle."),
        "gamma_warming": ParamSource(
            "abgeleitet", f"{_GRUENIG}; {_AR6}",
            "Mittel aus ln(1 + Zunahme) / Erwärmung über drei Szenarien (0,30 / 0,26 / 0,23 je K). Nur für Europa "
            "projiziert; für alle Waldtypen übernommen."),
        "beta_closure": ParamSource(
            "abgeleitet", _WILLIAMS,
            "So gewählt, dass der Kronenschluss und damit die Albedo-Wirkung nach 40 Jahren die Hälfte erreicht "
            "(Williams et al. 2026: rund die Hälfte des Albedo-Rückgangs in 40 Jahren). Globale Regel, nicht je Typ."),
        "valid_gez": ParamSource("abgeleitet", _WALKER,
                                 "Klimazone aus Walkers Bioklimazonen (aus FAO GEZ); Codes 1/5 vertauscht im README."),
    })
    return table


def _build_registry() -> tuple[dict[str, Species], dict[str, float]]:
    from nbs.forest_data import TREES_PER_HA, growth_by_key

    species, sites = {}, {}
    for key, g in growth_by_key().items():
        meta = _TYPE_META[g["type"]]
        species[key] = Species(
            key=key,
            name_de=f"{meta['name']} ({_ZONE_DE[g['zone']]})",
            name_lat=meta["igbp"],
            m_max_kgC=g["m_ref_mgc_ha"] * 1000.0 / TREES_PER_HA,
            k=g["k"],
            p=2.0,
            beta_closure=_beta_for_half_at(g["k"], 2.0),
            stand_area_m2=1e4 / TREES_PER_HA,
            alpha_canopy=meta["alpha"],
            igbp_class=meta["igbp"],
            p_disturb=meta["p_disturb"],
            severity_beta=meta["severity"],
            gamma_warming=GAMMA_WARMING,
            eps_immediate=meta["eps"],
            tau_decay_yr=meta["tau"],
            valid_gez=(g["zone"],),
            sources=_type_sources(),
        )
        sites[key] = g["lat_ref"]
    return species, sites


SPECIES, REFERENCE_SITES = _build_registry()
"""Forest type per climate zone -> parameters. REFERENCE_SITES: the
area-weighted mean |latitude| of the type's reforestable cells in that zone."""


def reference_site(key: str) -> float:
    """Reference latitude [deg N] of a species' single-tree figures."""
    try:
        return REFERENCE_SITES[key]
    except KeyError:
        known = ", ".join(sorted(REFERENCE_SITES))
        raise KeyError(f"unknown species {key!r}; known species: {known}") from None


def get_species(key: str) -> Species:
    """Return the species registered under *key*."""
    try:
        return SPECIES[key]
    except KeyError:
        known = ", ".join(sorted(SPECIES))
        raise KeyError(f"unknown species {key!r}; known species: {known}") from None
