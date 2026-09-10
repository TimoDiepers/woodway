import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

from nbs.map_plots import (  # noqa: E402
    plot_breakeven_map,
    plot_horizon_field,
    plot_sign_map,
)


@pytest.mark.slow
def test_sign_map_is_written(tmp_path):
    plot_sign_map(2125, str(tmp_path / "p1.png"))
    assert (tmp_path / "p1.png").stat().st_size > 10_000


@pytest.mark.slow
def test_horizon_field_is_written(tmp_path):
    plot_horizon_field(str(tmp_path / "e6.png"), species_key="picea_abies")
    assert (tmp_path / "e6.png").stat().st_size > 10_000


@pytest.mark.slow
def test_breakeven_map_is_written(tmp_path):
    plot_breakeven_map(str(tmp_path / "p0.png"))
    assert (tmp_path / "p0.png").stat().st_size > 10_000


@pytest.mark.slow
def test_sign_map_default_year_is_2050(tmp_path):
    """The task-6 revision: default to 2050, where the measured warming
    fraction (48.2%) is closest to an even split, not the horizon end where
    the map would read almost single-signed."""
    p_default = plot_sign_map(out_path=str(tmp_path / "default.png"))
    p_2050 = plot_sign_map(2050, str(tmp_path / "explicit_2050.png"))
    assert (tmp_path / "default.png").stat().st_size > 10_000
    assert (tmp_path / "explicit_2050.png").stat().st_size > 10_000
    assert p_default and p_2050


@pytest.mark.slow
def test_breakeven_field_has_both_finite_years_and_never_cells():
    """The talk's claim is transient, not permanent: some cells break even
    early, some late, and some (boreal, strong albedo penalty) never within
    the 2025-2150 horizon. A map with only one of these three outcomes would
    misrepresent the underlying t_star distribution."""
    from nbs.map_plots import _breakeven_year_field

    field = _breakeven_year_field()
    finite = field[np.isfinite(field)]
    infinite = field[np.isinf(field)]
    assert finite.size > 0, "keine Zelle mit endlichem t*"
    assert infinite.size > 0, "keine Zelle ohne Ausgleich im Horizont"
    assert np.all(finite >= 2025) and np.all(finite <= 2150)


def test_footer_names_both_data_provenances():
    """A figure built on fallback tables must say so, or a reader will take a
    calibrated stand-in for a measurement.

    Checked on the composed footer string rather than on the rendered figure:
    the plotting helpers close their figure when they save it, so there is no
    live artist to interrogate afterwards.
    """
    from nbs.albedo_grid import product_provenance
    from nbs.landscape import provenance as landscape_provenance
    from nbs.map_plots import footer_text

    footer = footer_text()
    assert product_provenance() in footer
    assert landscape_provenance() in footer


def test_footer_states_the_three_tier_fractions_for_picea_abies():
    """Plan 2's instruction: the footer must state the three-tier
    fractions, not just the coarse raster/fallback provenance flag.

    After the ``nbs.landscape.land_mask()`` fix (the 71.3%-over-ocean
    plantable-area defect) the numbers for Picea abies changed from 8.9%
    local / 41.1% zonal / 50.0% table to 29.3% / 70.7% / 0.0%: the species'
    absolute-latitude band is 60-70 degrees on *both* sides of the equator,
    and before the fix roughly half its fabricated "plantable" cells landed
    in the 60-70S band -- almost pure Southern Ocean, where the ENF<->
    grassland transition has no local retrieval and not even a same-
    hemisphere zonal one, hence the 50% table fallback. The land mask now
    correctly excludes that band entirely, so every plantable Picea abies
    cell is real Northern Hemisphere boreal forest, where the transition has
    either a local or a zonal retrieval -- table drops to exactly 0.0%."""
    from nbs.map_plots import footer_text

    footer = footer_text()
    assert "29,3 %" in footer
    assert "70,7 %" in footer
    assert "0,0 %" in footer


def test_footer_is_composable_for_another_species():
    from nbs.map_plots import footer_text

    footer = footer_text("fagus_sylvatica")
    assert "Rotbuche" in footer
