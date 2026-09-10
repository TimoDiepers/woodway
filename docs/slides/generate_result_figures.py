"""Rebuild the result (E) and potential (P) figures of dissvortrag.pptx.

Every figure in the results and potential sections was produced by a
throwaway script that no longer exists, so the conditions each one was
evaluated under -- species, latitude, scenario, model configuration, horizon
-- lived only in the slide text. This script is that record, executable.

Run it to regenerate:

    uv run python docs/slides/generate_result_figures.py            # alle
    uv run python docs/slides/generate_result_figures.py --out /tmp/x  # Probelauf

**Conditions.** Unless a figure says otherwise, everything here is:
scenario SSP2-4.5, ``ModelConfig()`` (logarithmic CO2 forcing against the
rising background, albedo channel on, disturbance as an expected-value
drain, scenario-conditioned carbon sink), horizon 2025-2150, one tree as the
reference unit, and each species at its own ``nbs.species.REFERENCE_SITES``
latitude. These are the conditions slides 25-38 state; if this script and the
deck ever disagree, ``tests/test_slide_numbers.py`` is what catches it.

**Not covered here.** Four figures on the deck have no plotting function in
``nbs`` and are therefore not rebuilt by this script:
``e5_arten.png``, ``e7_leiter_wasserfall.png``, ``p2_kaskade_wasserfall.png``
and ``p4_umkehrrechnung.png``. Their *numbers* are pinned by
``tests/test_slide_numbers.py`` (the ladder rungs, the cascade endpoint, the
reverse calculation), so a stale figure cannot go unnoticed indefinitely --
but the drawing itself would have to be redone by hand. This is a known gap,
stated here rather than left to be discovered.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from nbs.config import ModelConfig
from nbs.map_plots import (
    plot_breakeven_map,
    plot_horizon_field,
    plot_planting_map,
    plot_sign_map,
)
from nbs.pipeline import run_single_tree, run_single_tree_ensemble
from nbs.plots import (
    plot_decomposition,
    plot_disturbance_fan,
    plot_planting_time,
    plot_tree_inputs,
)
from nbs.species import REFERENCE_SITES

DEFAULT_OUT = Path(__file__).resolve().parent / "figures"
SCENARIO = "ssp245"
CONFIG = ModelConfig()
ENSEMBLE_MEMBERS = 1000
SIGN_MAP_YEAR = 2050
PLANTING_MAP_YEAR = 2100

BOREAL = "picea_abies"
TROPICAL = "tropical_mixed"


def generate(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def done(path: str) -> None:
        written.append(Path(path))
        print(f"  {path}")

    print(f"Bedingungen: {SCENARIO.upper()}, {CONFIG.describe_de()}")

    print("E2/E3: Einzelbaum, boreal und tropisch")
    boreal = run_single_tree(BOREAL, REFERENCE_SITES[BOREAL], SCENARIO, config=CONFIG)
    tropical = run_single_tree(
        TROPICAL, REFERENCE_SITES[TROPICAL], SCENARIO, config=CONFIG
    )
    done(plot_tree_inputs(boreal, str(out_dir / "e2_eingangsgroessen_boreal.png")))
    done(plot_decomposition(boreal, str(out_dir / "e3_zerlegung_boreal.png")))
    done(plot_decomposition(tropical, str(out_dir / "e3_zerlegung_tropisch.png")))

    print(f"E4: Störungsfächer, {ENSEMBLE_MEMBERS} Realisationen")
    det, ensemble = run_single_tree_ensemble(
        BOREAL,
        REFERENCE_SITES[BOREAL],
        SCENARIO,
        n_members=ENSEMBLE_MEMBERS,
        config=CONFIG,
    )
    done(
        plot_disturbance_fan(
            det, ensemble, str(out_dir / "e4_stoerungsfaecher_boreal.png")
        )
    )

    print("E6: Horizontfeld (Gedankenexperiment über alle Breiten)")
    done(
        plot_horizon_field(
            str(out_dir / "e6_horizontfeld.png"), species_key=BOREAL, scenario=SCENARIO
        )
    )

    print("E8: Pflanzjahr und Störungsrisiko")
    done(
        plot_planting_time(
            str(out_dir / "e8_pflanzjahr_risiko.png"),
            species_key=BOREAL,
            lat_deg=REFERENCE_SITES[BOREAL],
            scenario=SCENARIO,
            config=CONFIG,
        )
    )

    print("P0/P1: Ausgleichsjahr und Vorzeichen im Raster")
    done(plot_breakeven_map(str(out_dir / "p0_ausgleichsjahr_karte.png"), scenario=SCENARIO))
    done(
        plot_sign_map(
            SIGN_MAP_YEAR,
            str(out_dir / f"p1_vorzeichenkarte_{SIGN_MAP_YEAR}.png"),
            scenario=SCENARIO,
        )
    )

    print("P5: verfügbare Fläche und Artenwahl")
    done(
        plot_planting_map(
            str(out_dir / "p5_flaeche_und_artenwahl.png"),
            year=PLANTING_MAP_YEAR,
            scenario=SCENARIO,
        )
    )

    print(
        "\nOhne Generator (von Hand zu erneuern): e5_arten, e7_leiter_wasserfall, "
        "p2_kaskade_wasserfall, p4_umkehrrechnung"
    )
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="Zielverzeichnis für die PNGs"
    )
    args = parser.parse_args()
    written = generate(args.out)
    print(f"\n{len(written)} Abbildungen geschrieben nach {args.out}")


if __name__ == "__main__":
    main()
