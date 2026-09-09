"""Summary numbers for a temperature trajectory."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def t_star(delta_t: NDArray, years: NDArray) -> float:
    """Year from which the intervention stays net cooling.

    Not the first year with delta_t <= 0 — early on neither channel has acted
    yet, so that year would always be the first. This is the year after the
    last sign change: from here on the net effect never turns positive again.
    """
    dt = np.asarray(delta_t, dtype=float)
    warming = np.flatnonzero(dt > 0.0)
    if warming.size == 0:
        return float(years[0])
    last_warming = int(warming[-1])
    if last_warming >= len(dt) - 1:
        return float(np.inf)
    return float(years[last_warming + 1])


def _year_index(years: NDArray, year: int) -> int:
    idx = np.flatnonzero(np.asarray(years) == year)
    if idx.size == 0:
        raise ValueError(f"year {year} is outside {years[0]}..{years[-1]}")
    return int(idx[0])


def prob_warming(ensemble_delta_t: NDArray, years: NDArray, year: int) -> float:
    """Fraction of ensemble members that are still warming in *year*."""
    col = np.asarray(ensemble_delta_t)[:, _year_index(years, year)]
    return float(np.mean(col > 0.0))


def risk_premium(
    ensemble_delta_t: NDArray, deterministic_delta_t: NDArray, years: NDArray, year: int
) -> float:
    """Ensemble mean minus deterministic run [K] in *year*.

    Positive means the deterministic run overstates the cooling — the amount by
    which ignoring disturbance risk flatters the result.
    """
    i = _year_index(years, year)
    return float(np.mean(np.asarray(ensemble_delta_t)[:, i]) - np.asarray(deterministic_delta_t)[i])


def quantile_band(
    ensemble_delta_t: NDArray, lo: float = 0.05, hi: float = 0.95
) -> tuple[NDArray, NDArray, NDArray]:
    """Lower band, median and upper band across ensemble members."""
    ens = np.asarray(ensemble_delta_t, dtype=float)
    return (
        np.quantile(ens, lo, axis=0),
        np.quantile(ens, 0.5, axis=0),
        np.quantile(ens, hi, axis=0),
    )
