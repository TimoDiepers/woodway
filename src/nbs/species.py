"""Representative tree species, one per biome.

Stock parameters are per tree at the stated stand density, not per hectare:
the presentation reasons about a single tree throughout, and the albedo term
needs the tree's own footprint.
"""

from __future__ import annotations

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

SPECIES: dict[str, Species] = {
    "picea_abies": Species(
        key="picea_abies",
        name_de="Gemeine Fichte",
        name_lat="Picea abies",
        m_max_kgC=50.0,
        k=0.030,
        p=2.0,
        beta_closure=0.5,
        stand_area_m2=5.0,
        alpha_canopy=0.09,
        igbp_class="evergreen_needleleaf",
        p_disturb=0.012,
        severity_beta=(2.0, 2.0),
        gamma_warming=0.20,
        eps_immediate=0.30,
        tau_decay_yr=30.0,
        valid_gez=("boreal_coniferous_forest", "boreal_tundra_woodland",
                   "temperate_continental_forest"),
        sources=_sources(),
    ),
    "pinus_sylvestris": Species(
        key="pinus_sylvestris",
        name_de="Waldkiefer",
        name_lat="Pinus sylvestris",
        m_max_kgC=60.0,
        k=0.045,
        p=2.0,
        beta_closure=0.5,
        stand_area_m2=5.0,
        alpha_canopy=0.10,
        igbp_class="evergreen_needleleaf",
        p_disturb=0.008,
        severity_beta=(2.0, 2.5),
        gamma_warming=0.20,
        eps_immediate=0.35,
        tau_decay_yr=25.0,
        valid_gez=("temperate_continental_forest", "temperate_oceanic_forest",
                   "boreal_coniferous_forest"),
        sources=_sources(),
    ),
    "fagus_sylvatica": Species(
        key="fagus_sylvatica",
        name_de="Rotbuche",
        name_lat="Fagus sylvatica",
        m_max_kgC=75.0,
        k=0.040,
        p=2.2,
        beta_closure=0.5,
        stand_area_m2=6.0,
        alpha_canopy=0.15,
        igbp_class="deciduous_broadleaf",
        p_disturb=0.005,
        severity_beta=(2.0, 3.0),
        gamma_warming=0.20,
        eps_immediate=0.15,
        tau_decay_yr=20.0,
        valid_gez=("temperate_oceanic_forest", "temperate_continental_forest",
                   "temperate_mountain_system"),
        sources=_sources(),
    ),
    "eucalyptus_grandis": Species(
        key="eucalyptus_grandis",
        name_de="Rosen-Eukalyptus (Plantage)",
        name_lat="Eucalyptus grandis",
        m_max_kgC=50.0,
        k=0.120,
        p=1.75,
        beta_closure=0.4,
        stand_area_m2=4.0,
        alpha_canopy=0.13,
        igbp_class="evergreen_broadleaf",
        p_disturb=0.010,
        severity_beta=(2.0, 2.0),
        gamma_warming=0.20,
        eps_immediate=0.45,
        tau_decay_yr=12.0,
        valid_gez=("subtropical_humid_forest", "tropical_moist_deciduous_forest"),
        sources=_sources(),
    ),
    "tropical_mixed": Species(
        key="tropical_mixed",
        name_de="Tropischer Mischbestand",
        name_lat="gemischt, immergrün",
        m_max_kgC=100.0,
        k=0.080,
        p=2.5,
        beta_closure=0.5,
        stand_area_m2=5.0,
        alpha_canopy=0.12,
        igbp_class="evergreen_broadleaf",
        p_disturb=0.005,
        severity_beta=(2.0, 4.0),
        gamma_warming=0.20,
        eps_immediate=0.25,
        tau_decay_yr=10.0,
        valid_gez=("tropical_rainforest", "tropical_moist_deciduous_forest"),
        sources=_sources(),
    ),
}


REFERENCE_SITES: dict[str, float] = {
    "picea_abies": 60.0,
    "pinus_sylvestris": 52.0,
    "fagus_sylvatica": 50.0,
    "eucalyptus_grandis": 25.0,
    "tropical_mixed": 0.0,
}
"""Reference latitude per species [deg N] for the talk's single-tree figures.

These are the sites slide 25 announces and every E-figure is evaluated at.
They lived only on the slide until this entry existed, so a regenerated
figure could silently have used a different latitude than the one the deck
claims. Chosen as typical planting latitudes for each species, not as band
centres -- ``nbs.potential._REP_LAT_DEG`` is a *different* set (the centres
of the assignment bands, 65/55/42.5/22.5/5), used only to size the
disturbance-buffer ratio. Do not substitute one for the other: the two answer
different questions and legitimately differ.
"""


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
