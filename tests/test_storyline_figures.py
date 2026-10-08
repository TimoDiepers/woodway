"""Tests for nbs.storyline_figures: numbers behind the storyline-v2 figures."""

from nbs.animations import SITES
from nbs.constants import YEARS
from nbs.metrics import t_star
from nbs.storyline_figures import LADDER_STEPS, ladder_t_star, run_site


def test_last_ladder_step_is_the_full_model():
    """The ladder rebuilds the chain shell by shell; its last rung must be
    exactly what the full model gives at the site."""
    for site in SITES:
        steps = ladder_t_star(site)
        assert len(steps) == len(LADDER_STEPS)
        assert steps[-1] == t_star(run_site(site).delta_t, YEARS)


def test_shell_one_alone_cools_from_the_start():
    """With the boundary around the tree, the naive calculation holds: the
    tree cools from year one everywhere."""
    for site in SITES:
        assert ladder_t_star(site)[0] == YEARS[0]
