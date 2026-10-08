import dataclasses

import numpy as np
import pytest

from nbs.config import ModelConfig
from nbs.pipeline import SiteResult
from nbs.variants import run_ladder, run_variants, summarise_variants


@pytest.mark.slow
def test_run_variants_returns_base_plus_one_flip_per_switch():
    results = run_variants("enf_boreal", 60.0)
    assert isinstance(results, dict)
    # base + one flip each for co2_forcing, albedo, disturbance, carbon_sink
    assert len(results) == 5
    for name, r in results.items():
        assert isinstance(r, SiteResult)
        assert isinstance(name, str) and name


@pytest.mark.slow
def test_run_variants_base_result_uses_the_base_config():
    base = ModelConfig(co2_forcing="linear")
    results = run_variants("enf_boreal", 60.0, base=base)
    assert results["Basis"].config == base


@pytest.mark.slow
def test_run_variants_each_non_base_result_differs_in_exactly_one_field():
    base = ModelConfig()
    results = run_variants("enf_boreal", 60.0, base=base)
    for name, r in results.items():
        if name == "Basis":
            continue
        diffs = [
            f.name
            for f in dataclasses.fields(base)
            if getattr(r.config, f.name) != getattr(base, f.name)
        ]
        assert len(diffs) == 1, f"{name}: expected exactly one switch to differ, got {diffs}"


@pytest.mark.slow
def test_run_variants_keys_are_short_german_strings():
    results = run_variants("enf_boreal", 60.0)
    for name in results:
        assert isinstance(name, str)
        assert len(name) < 60


@pytest.mark.slow
def test_run_ladder_default_has_five_rungs_in_narrative_order():
    ladder = run_ladder("enf_boreal", 60.0)
    assert isinstance(ladder, list)
    assert len(ladder) == 5
    names = [name for name, _ in ladder]
    assert names == [
        "naive Kohlenstoffrechnung",
        "+ Albedo",
        "+ Störung",
        "+ Senkensättigung",
        "+ Hintergrundkonzentration",
    ]
    for name, r in ladder:
        assert isinstance(r, SiteResult)


@pytest.mark.slow
def test_run_ladder_first_rung_is_naive():
    ladder = run_ladder("enf_boreal", 60.0)
    _, first = ladder[0]
    assert first.config.co2_forcing == "linear"
    assert first.config.carbon_sink == "preindustrial"
    assert first.config.albedo is False
    assert first.config.disturbance == "off"


@pytest.mark.slow
def test_run_ladder_last_rung_is_the_full_default_model():
    ladder = run_ladder("enf_boreal", 60.0)
    _, last = ladder[-1]
    assert last.config == ModelConfig()


@pytest.mark.slow
def test_run_ladder_accepts_a_custom_ladder():
    custom = [
        ("A", ModelConfig(albedo=False)),
        ("B", ModelConfig(albedo=True)),
    ]
    ladder = run_ladder("enf_boreal", 60.0, ladder=custom)
    assert [name for name, _ in ladder] == ["A", "B"]


@pytest.mark.slow
def test_summarise_variants_from_ladder_has_expected_columns():
    ladder = run_ladder("enf_boreal", 60.0)
    rows = summarise_variants(ladder)
    assert len(rows) == len(ladder)
    for row in rows:
        assert "name" in row
        assert "t_star" in row
        assert "delta_t_2150" in row
        assert "diff_from_base" in row
    # the first rung is its own base: dt_2150 - dt_2150 is an exact 0.0 in
    # IEEE754 for any finite value, so abs=0 (not the default abs=1e-12,
    # which would dominate a diff_from_base of order 1e-13/1e-14 anyway) is
    # the correct tolerance here, not a loose one.
    assert rows[0]["diff_from_base"] == pytest.approx(0.0, abs=0)


@pytest.mark.slow
def test_summarise_variants_from_dict_uses_first_entry_as_base():
    results = run_variants("enf_boreal", 60.0)
    rows = summarise_variants(results)
    assert len(rows) == len(results)
    assert rows[0]["name"] == "Basis"
    assert rows[0]["diff_from_base"] == pytest.approx(0.0, abs=0)


@pytest.mark.slow
def test_summarise_variants_diff_matches_manual_computation():
    # delta_t_2150 and diff_from_base are both of order 1e-13 to 1e-14 here;
    # pytest.approx's default abs=1e-12 would dominate that and let a wrong
    # value through, so both comparisons need an explicit abs=0 and rely on
    # rel alone.
    ladder = run_ladder("enf_boreal", 60.0)
    rows = summarise_variants(ladder)
    base_dt_2150 = ladder[0][1].delta_t[-1]
    for row, (_, result) in zip(rows, ladder):
        expected_diff = result.delta_t[-1] - base_dt_2150
        assert row["diff_from_base"] == pytest.approx(expected_diff, rel=1e-9, abs=0)
        assert row["delta_t_2150"] == pytest.approx(result.delta_t[-1], rel=1e-9, abs=0)
