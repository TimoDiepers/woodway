"""Representative tree species, one per biome.

Stock parameters are per tree at the stated stand density, not per hectare:
the presentation reasons about a single tree throughout, and the albedo term
needs the tree's own footprint.
"""

from __future__ import annotations

from dataclasses import dataclass, field


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

    sources: dict[str, str] = field(default_factory=dict)


_IPCC = "IPCC 2019 Refinement, Vol. 4 Ch. 4"
_SEIDL = "Seidl et al. 2017, Nat. Clim. Change"
_BONAN = "Bonan 2008, Science"

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
        sources={"m_max_kgC": _IPCC, "k": _IPCC, "p": _IPCC,
                 "p_disturb": _SEIDL, "alpha_canopy": _BONAN},
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
        sources={"m_max_kgC": _IPCC, "k": _IPCC, "p": _IPCC,
                 "p_disturb": _SEIDL, "alpha_canopy": _BONAN},
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
        sources={"m_max_kgC": _IPCC, "k": _IPCC, "p": _IPCC,
                 "p_disturb": _SEIDL, "alpha_canopy": _BONAN},
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
        sources={"m_max_kgC": _IPCC, "k": _IPCC, "p": _IPCC,
                 "p_disturb": _SEIDL, "alpha_canopy": _BONAN},
    ),
    "tropical_mixed": Species(
        key="tropical_mixed",
        name_de="Tropischer Mischbestand",
        name_lat="gemischt, immergruen",
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
        sources={"m_max_kgC": _IPCC, "k": _IPCC, "p": _IPCC,
                 "p_disturb": _SEIDL, "alpha_canopy": _BONAN},
    ),
}


def get_species(key: str) -> Species:
    """Return the species registered under *key*."""
    try:
        return SPECIES[key]
    except KeyError:
        known = ", ".join(sorted(SPECIES))
        raise KeyError(f"unknown species {key!r}; known species: {known}") from None
