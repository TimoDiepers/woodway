import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

from nbs.constants import YEARS  # noqa: E402
from nbs.plots import (  # noqa: E402
    plot_decomposition,
    plot_disturbance_fan,
    plot_tree_inputs,
)


@pytest.fixture(scope="module")
def result():
    from nbs.pipeline import run_single_tree

    return run_single_tree("picea_abies", lat_deg=60.0)


@pytest.mark.slow
def test_channel_decomposition_sums_to_the_total(result):
    from nbs.response import convolve_response, green_temperature

    g = green_temperature(result.scenario)
    dt_c = convolve_response(g, result.phi_co2)
    dt_a = convolve_response(g, result.phi_albedo)
    # delta_t here is of order 1e-13 K; np.allclose's default atol=1e-8 would
    # swamp that entirely and let a wrong decomposition (e.g. a dropped or
    # sign-flipped channel) pass. Scale the tolerance to the signal instead.
    scale = np.abs(result.delta_t).max()
    assert np.allclose(dt_c + dt_a, result.delta_t, rtol=0.0, atol=1e-9 * scale)


@pytest.mark.slow
def test_input_figure_is_written(tmp_path, result):
    p = plot_tree_inputs(result, str(tmp_path / "sub" / "e2.png"))
    assert p.endswith("e2.png")
    assert (tmp_path / "sub" / "e2.png").stat().st_size > 10_000


@pytest.mark.slow
def test_decomposition_figure_is_written(tmp_path, result):
    p = plot_decomposition(result, str(tmp_path / "e3.png"))
    assert (tmp_path / "e3.png").stat().st_size > 10_000


@pytest.mark.slow
def test_fan_figure_is_written(tmp_path, result):
    # The scale of the synthetic noise is deliberately tied to the signal's
    # own magnitude rather than a fixed constant: delta_t here is of order
    # 1e-13 K, and a fixed scale=1e-4 (as in the original brief) would be
    # nine orders of magnitude larger than the signal, drowning it entirely.
    # That still exercises plot_disturbance_fan as a smoke test, but the
    # resulting "ensemble" would describe nothing about how disturbance risk
    # actually spreads delta_t. Scaling the noise to a fraction of
    # abs(delta_t).max() keeps the synthetic spread on the same order as the
    # real trajectory, so the fan in the figure looks like a plausible
    # perturbation of the deterministic curve instead of pure noise.
    rng = np.random.default_rng(0)
    spread = 0.15 * np.abs(result.delta_t).max()
    ensemble = result.delta_t[None, :] + rng.normal(scale=spread, size=(30, len(YEARS)))
    p = plot_disturbance_fan(result, ensemble, str(tmp_path / "e4.png"))
    assert (tmp_path / "e4.png").stat().st_size > 10_000


@pytest.mark.slow
def test_planting_time_figure_is_written(tmp_path):
    from nbs.plots import plot_planting_time

    plot_planting_time(str(tmp_path / "pz.png"))
    assert (tmp_path / "pz.png").stat().st_size > 10_000


@pytest.mark.slow
def test_growth_curves_figure_is_written(tmp_path):
    from nbs.plots import plot_growth_curves

    plot_growth_curves(str(tmp_path / "e1.png"))
    assert (tmp_path / "e1.png").stat().st_size > 10_000


def test_growth_curve_legend_carries_the_parameters_not_the_annotations():
    """Two species share m_max = 50 kgC, so annotations placed at the
    saturation level sat on top of each other. The parameters belong in the
    legend label; this pins that they are still stated somewhere."""
    import inspect

    from nbs.plots import plot_growth_curves

    source = inspect.getsource(plot_growth_curves)
    assert "label=" in source and "m$_{max}$" in source
    assert "ax.annotate" not in source
