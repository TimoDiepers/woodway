"""Same tree, different planting year: what waiting costs.

Every other module in this package plants at ``T_START``. That hides a term
the talk needs: the disturbance hazard is not a species constant, it is

    p(t) = p0 * exp(gamma * T_background(t))                (nbs.tree)

read from the *calendar* year the tree is standing in, not from its age. A
seedling planted in 2085 therefore spends its whole life in a hotter world
than one planted in the start year spends in its. Two things follow, and this module
separates them because they are easy to confuse:

1. **The calendar cost.** A late cohort has fewer years before the 2100
   horizon, so less stock and less cooling on the table by then. Trivially
   true, nothing to do with fire.
2. **The risk cost.** At the *same age*, a late cohort has lost more stock,
   because the fire/windthrow hazard it lived through was higher every single
   year. ``cohort_table``'s ``age_yr`` column is the same-age comparison, and
   ``verlust_anteil`` is the isolated risk effect: the same tree, the same
   age, run once with ``disturbance="off"`` and once with the hazard on.

``risk_ratio`` states the mechanism in one number: the annual hazard in the
planting year relative to the start-year hazard. It depends only on gamma and the
background warming between the two years, not on the species' base rate.

The default age is 50 years, the largest round age every cohort in
``PLANT_YEARS`` still reaches inside the T_START-2100 axis (T_START + 20 + 50 < 2100).
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.typing import NDArray

from nbs.config import ModelConfig
from nbs.constants import T_START, YEARS
from nbs.fair_module import find_breakeven_year
from nbs.pipeline import SiteResult, _background_temperature, run_single_tree
from nbs.species import get_species
from nbs.tree import disturbance_probability

PLANT_YEARS: tuple[int, ...] = (T_START, T_START + 10, T_START + 20)
"""The cohorts the talk compares: 20-year steps from today."""

DEFAULT_AGE_YR = 50
"""Largest round age every cohort in PLANT_YEARS reaches before T_END."""


def _year_index(year: int) -> int:
    idx = int(year) - T_START
    if not 0 <= idx < len(YEARS):
        raise ValueError(f"Jahr {year} liegt ausserhalb der Studienachse")
    return idx


def hazard_curve(species_key: str, scenario: str = "ssp245") -> NDArray:
    """Annual disturbance probability p(t) over ``YEARS`` [1/a].

    The species' own p0 and gamma against the scenario's background warming
    -- the curve every cohort reads its hazard off, each over its own stretch
    of it.
    """
    sp = get_species(species_key)
    return disturbance_probability(sp, _background_temperature(scenario))


def risk_ratio(
    species_key: str, plant_year: int, scenario: str = "ssp245"
) -> float:
    """Annual hazard in *plant_year* divided by the hazard in ``T_START`` [-].

    Independent of p0: it is exp(gamma * (T_bg(plant_year) - T_bg(T_START))).
    """
    p = hazard_curve(species_key, scenario)
    return float(p[_year_index(plant_year)] / p[0])


def survival_probability(
    species_key: str,
    plant_year: int,
    age_yr: int = DEFAULT_AGE_YR,
    scenario: str = "ssp245",
) -> float:
    """Probability of *no* disturbance in the first ``age_yr`` years [-].

    ``prod(1 - p(t))`` over the cohort's own calendar window. One minus this
    is the chance the tree is hit at least once -- the number that rises with
    the planting year even though the species parameters never change.
    """
    p = hazard_curve(species_key, scenario)
    start = _year_index(plant_year)
    end = _year_index(plant_year + age_yr)
    return float(np.prod(1.0 - p[start:end]))


def cohort(
    species_key: str,
    plant_year: int,
    lat_deg: float | None = None,
    scenario: str = "ssp245",
    config: ModelConfig | None = None,
) -> SiteResult:
    """One cohort's full chain, on the common ``YEARS`` axis. Default site:
    the forest type's reference latitude (nbs.species.reference_site)."""
    from nbs.species import reference_site

    if lat_deg is None:
        lat_deg = reference_site(species_key)
    return run_single_tree(
        species_key, lat_deg, scenario, config=config, plant_year=plant_year,
    )



def cohort_table(
    species_key: str,
    lat_deg: float | None = None,
    scenario: str = "ssp245",
    plant_years: tuple[int, ...] = PLANT_YEARS,
    age_yr: int = DEFAULT_AGE_YR,
    config: ModelConfig | None = None,
) -> dict[int, dict[str, float]]:
    """Per planting year, the calendar cost and the risk cost side by side.

    Columns:

    ``risikofaktor``        annual hazard relative to a start-year planting [-]
    ``p_stoerung``          probability of at least one disturbance within
                            ``age_yr`` years of planting [-]
    ``vorrat_kgC``          stock at age ``age_yr``, hazard on [kgC]
    ``vorrat_ungestoert``   the same, hazard off [kgC]
    ``verlust_anteil``      1 - vorrat/vorrat_ungestoert [-] -- the isolated
                            risk effect, same species, same age
    ``delta_t_2150_k``      the cohort's own Delta_T at the horizon [K]
    ``t_star``              break-even year, or inf
    """
    base = config or ModelConfig()
    undisturbed = ModelConfig(**{**base.__dict__, "disturbance": "off"})

    out: dict[int, dict[str, float]] = {}
    for py in plant_years:
        idx_age = _year_index(py + age_yr)
        res = cohort(species_key, py, lat_deg, scenario, base)
        ref = cohort(species_key, py, lat_deg, scenario, undisturbed)

        stock = float(res.trajectory.stock_kgC[idx_age])
        stock_ref = float(ref.trajectory.stock_kgC[idx_age])
        out[py] = {
            "risikofaktor": risk_ratio(species_key, py, scenario),
            "p_stoerung": 1.0 - survival_probability(species_key, py, age_yr, scenario),
            "vorrat_kgC": stock,
            "vorrat_ungestoert": stock_ref,
            "verlust_anteil": (1.0 - stock / stock_ref) if stock_ref > 0.0 else float("nan"),
            "delta_t_2150_k": float(res.delta_t[-1]),
            # A cohort cannot break even before it exists: before planting
            # Delta-T is exactly 0, which t* would otherwise count as cooling.
            "t_star": max(find_breakeven_year(res.delta_t), float(py)),
        }
    return out


__all__ = [
    "DEFAULT_AGE_YR",
    "PLANT_YEARS",
    "cohort",
    "cohort_table",
    "hazard_curve",
    "risk_ratio",
    "survival_probability",
]
