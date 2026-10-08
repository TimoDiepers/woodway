"""Pick the 'central' FaIR configuration from the fair-calibrate 1.4.1 ensemble.

Runs all 841 constrained members (RCMIP emissions, as nbs.fair_module does)
under SSP1-2.6, SSP2-4.5, SSP3-7.0 and SSP5-8.5 and picks the member closest
to the ensemble median at once in
  * historical warming 2011-2020 and 2015-2024 relative to 1850-1900, and
  * end-of-century warming 2081-2100 in each scenario,
each measured in units of the ensemble's own 5-95 % spread. The chosen id
goes into nbs.fair_module.CENTRAL_MEMBER.

    .venv/bin/python scripts/select_fair_member.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from fair import FAIR
from fair.interface import fill, initialise
from fair.io import read_properties

CAL = Path(__file__).resolve().parents[1] / "data" / "fair_calibrate_1.4.1"
PARAMS = CAL / "calibrated_constrained_parameters_calibration1.4.1.csv"
SPECIES = CAL / "species_configs_properties_calibration1.4.1.csv"
SCENARIOS = ["ssp126", "ssp245", "ssp370", "ssp585"]
# IPCC AR6 WG1 SPM Table SPM.1, 2081-2100 vs 1850-1900, best estimate.
AR6 = {"ssp126": 1.8, "ssp245": 2.7, "ssp370": 3.6, "ssp585": 4.4}


def main() -> None:
    df = pd.read_csv(PARAMS, index_col=0)
    f = FAIR(ch4_method="Thornhill2021")
    f.define_time(1750, 2150, 1)
    f.define_scenarios(SCENARIOS)
    f.define_configs(df.index)
    species, properties = read_properties(filename=str(SPECIES))
    f.define_species(species, properties)
    f.allocate()
    f.fill_from_rcmip()
    f.fill_species_configs(str(SPECIES))
    f.override_defaults(str(PARAMS))
    fill(f.climate_configs["stochastic_run"], False)  # forced response only, as in nbs.fair_module
    initialise(f.concentration, f.species_configs["baseline_concentration"])
    initialise(f.forcing, 0)
    initialise(f.temperature, 0)
    initialise(f.cumulative_emissions, 0)
    initialise(f.airborne_emissions, 0)
    initialise(f.ocean_heat_content_change, 0)
    f.run(progress=False)

    tb = np.arange(1750, 2151)  # timebounds 1750..2150

    def window(t, a, b):
        return t[(tb >= a) & (tb <= b)].mean(axis=0)

    metrics = {}
    for sc in SCENARIOS:
        t = f.temperature.sel(scenario=sc, layer=0).values  # (timebounds, configs)
        t = t - window(t, 1850, 1900)
        metrics[sc] = window(t, 2081, 2100)
        if sc == "ssp245":
            metrics["hist"] = window(t, 2011, 2020)
            metrics["recent"] = window(t, 2015, 2024)
            co2 = f.concentration.sel(scenario=sc, specie="CO2").values
            metrics["co2_2020"] = co2[tb == 2020][0]
            metrics["co2_2100"] = co2[tb == 2100][0]
            metrics["2025"] = t[tb == 2025][0]

    score = np.zeros(len(df))
    for key in ["hist", "recent"] + SCENARIOS:
        v = metrics[key]
        score += ((v - np.median(v)) / (np.percentile(v, 95) - np.percentile(v, 5))) ** 2
    best = int(np.argmin(score))

    print(f"central member: {df.index[best]}")
    print(f"{'':8s} {'member':>7s} {'median':>7s} {'5-95 %':>12s} {'AR6':>5s}")
    for key in ["hist", "recent", "2025", "co2_2020", "co2_2100"] + SCENARIOS:
        v = metrics[key]
        print(f"{key:8s} {v[best]:7.2f} {np.median(v):7.2f} {np.percentile(v, 5):5.2f}-{np.percentile(v, 95):5.2f}"
              f" {AR6.get(key, {'hist': 1.09, 'recent': 1.24, 'co2_2020': 412.0, 'co2_2100': 603.5}.get(key, float('nan'))):5.2f}")
    row = df.iloc[best]
    ecs = row["forcing_4co2"] / (2 * row["ocean_heat_transfer[0]"])
    all_ecs = df["forcing_4co2"] / (2 * df["ocean_heat_transfer[0]"])
    print(f"ECS {ecs:.2f} K (ensemble median {all_ecs.median():.2f}; AR6 3.0, likely 2.5-4.0)")


if __name__ == "__main__":
    main()
