import json

import numpy as np
import pytest

from nbs import borders


def test_border_files_are_committed_not_only_downloadable():
    """A figure that loses its coastlines on a fresh checkout is a broken
    figure. These files are small and public domain; they belong in the
    repository, not in the git-ignored data/raw."""
    for name in borders._FILES.values():
        assert (borders.BORDER_DIR / name).exists()
    assert borders.borders_available()


def test_every_segment_is_a_lon_lat_polyline_inside_the_globe():
    for key, segments in borders._load().items():
        assert segments, key
        for seg in segments:
            assert seg.ndim == 2 and seg.shape[1] == 2
            assert seg.shape[0] >= 2
            assert np.all(np.abs(seg[:, 0]) <= 180.0)
            assert np.all(np.abs(seg[:, 1]) <= 90.0)


def test_no_segment_wraps_the_antimeridian():
    """One unsplit feature would draw a horizontal line straight across the
    map -- the classic failure of hand-rolled coastline plotting."""
    for segments in borders._load().values():
        for seg in segments:
            assert np.all(np.abs(np.diff(seg[:, 0])) <= 180.0)


def test_wrapping_input_is_split_rather_than_drawn_across_the_map(tmp_path):
    path = tmp_path / "wrap.geojson"
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[170, 0], [179, 1], [-179, 2], [-170, 3]],
                        },
                    }
                ],
            }
        )
    )
    segments = borders._segments(path)
    assert len(segments) == 2
    assert [len(s) for s in segments] == [2, 2]


def test_add_borders_draws_without_changing_the_axes_limits():
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    assert borders.add_borders(ax)
    assert ax.get_xlim() == (-180.0, 180.0)
    assert ax.get_ylim() == (-90.0, 90.0)
    plt.close(fig)
