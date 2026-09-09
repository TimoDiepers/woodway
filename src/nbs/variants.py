"""Comparison forms over ModelConfig: attribution and a cumulative waterfall.

Two ways of showing the effect of the four model-complexity switches on the
results slides:

- ``run_variants``: one-at-a-time. A base configuration, then one result per
  switch flipped away from it, so each effect is attributed on its own.
- ``run_ladder``: cumulative, in narrative order, for a waterfall figure.
  Each rung adds one more piece of physical realism onto the previous one,
  ending at the full default model.

``summarise_variants`` turns either shape of result into a small table (t*,
Delta-T(2150), difference from the base) that a notebook or figure can
render without recomputing anything.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Iterable

from nbs.config import ModelConfig
from nbs.metrics import t_star
from nbs.pipeline import SiteResult, run_single_tree


def run_variants(
    species_key: str,
    lat_deg: float,
    *,
    base: ModelConfig = ModelConfig(),
    scenario: str = "ssp245",
    **kw: Any,
) -> dict[str, SiteResult]:
    """One-at-a-time sensitivity: *base*, plus one result per switch flipped
    away from it, keyed by a short German name.

    Each key names exactly which switch was flipped and to what, so the
    resulting dict can be plotted directly as an attribution figure (each
    non-base bar shows the effect of that one switch, isolated from the
    other three).
    """
    alt_co2 = "linear" if base.co2_forcing == "logarithmic" else "logarithmic"
    alt_disturbance = "off" if base.disturbance != "off" else "deterministic"
    alt_sink = "preindustrial" if base.carbon_sink == "scenario" else "scenario"

    co2_label = (
        "linearer CO2-Antrieb" if alt_co2 == "linear" else "logarithmischer CO2-Antrieb"
    )
    albedo_label = "ohne Albedo" if base.albedo else "mit Albedo"
    dist_label = "ohne Störung" if alt_disturbance == "off" else "mit Störung"
    sink_label = (
        "vorindustrielle Senke" if alt_sink == "preindustrial" else "Senkensättigung"
    )

    configs: dict[str, ModelConfig] = {
        "Basis": base,
        co2_label: dataclasses.replace(base, co2_forcing=alt_co2),
        albedo_label: dataclasses.replace(base, albedo=not base.albedo),
        dist_label: dataclasses.replace(base, disturbance=alt_disturbance),
        sink_label: dataclasses.replace(base, carbon_sink=alt_sink),
    }

    return {
        name: run_single_tree(species_key, lat_deg, scenario=scenario, config=cfg, **kw)
        for name, cfg in configs.items()
    }


_DEFAULT_LADDER: list[tuple[str, ModelConfig]] = [
    (
        "naive Kohlenstoffrechnung",
        ModelConfig(
            co2_forcing="linear",
            carbon_sink="preindustrial",
            albedo=False,
            disturbance="off",
        ),
    ),
    (
        "+ Albedo",
        ModelConfig(
            co2_forcing="linear",
            carbon_sink="preindustrial",
            albedo=True,
            disturbance="off",
        ),
    ),
    (
        "+ Störung",
        ModelConfig(
            co2_forcing="linear",
            carbon_sink="preindustrial",
            albedo=True,
            disturbance="deterministic",
        ),
    ),
    (
        "+ Senkensättigung",
        ModelConfig(
            co2_forcing="linear",
            carbon_sink="scenario",
            albedo=True,
            disturbance="deterministic",
        ),
    ),
    (
        "+ Hintergrundkonzentration",
        ModelConfig(
            co2_forcing="logarithmic",
            carbon_sink="scenario",
            albedo=True,
            disturbance="deterministic",
        ),
    ),
]
"""The talk's narrative order, plus the two carbon-cycle honesties this task
adds: sink saturation (scenario-conditioned g_C) and the background
concentration (logarithmic CO2 forcing). The last rung equals
``ModelConfig()``, the full default model.
"""


def run_ladder(
    species_key: str,
    lat_deg: float,
    *,
    ladder: list[tuple[str, ModelConfig]] | None = None,
    scenario: str = "ssp245",
    **kw: Any,
) -> list[tuple[str, SiteResult]]:
    """Cumulative ladder of configurations, for a waterfall figure.

    Returns ordered pairs, not a dict, since the order *is* the point: each
    rung is meant to be read as "the previous rung, plus one more effect".
    Pass ``ladder`` to run a caller-supplied sequence instead of the
    talk's default narrative order.
    """
    if ladder is None:
        ladder = _DEFAULT_LADDER
    return [
        (name, run_single_tree(species_key, lat_deg, scenario=scenario, config=cfg, **kw))
        for name, cfg in ladder
    ]


def summarise_variants(
    results: dict[str, SiteResult] | Iterable[tuple[str, SiteResult]],
) -> list[dict[str, Any]]:
    """Small table for a notebook or figure: per variant, t*, Delta-T(2150)
    and the difference from the base.

    Accepts either shape of result -- the dict from ``run_variants`` or the
    ordered list of pairs from ``run_ladder``. In both cases the *first*
    entry (dict-insertion order, or list order) is taken as "the base";
    for ``run_variants`` that is always its "Basis" entry, for ``run_ladder``
    it is the first rung.
    """
    items = list(results.items()) if isinstance(results, dict) else list(results)
    if not items:
        return []

    base_delta_t_2150 = float(items[0][1].delta_t[-1])

    rows = []
    for name, result in items:
        dt_2150 = float(result.delta_t[-1])
        rows.append(
            {
                "name": name,
                "t_star": t_star(result.delta_t, result.years),
                "delta_t_2150": dt_2150,
                "diff_from_base": dt_2150 - base_delta_t_2150,
            }
        )
    return rows
