"""Build the premise databases for the scenario sensitivity of the DAC model.

The main case uses REMIND-EU SSP2-NDC (databases ``ei312_REMIND-EU_SSP2_NDC_<year>`` in the
Brightway project ``ei312_REMIND_EU``). For the sensitivity this script adds, with the same source
(ecoinvent 3.12 cut-off) and premise's default sector updates:

* ``ei312_REMIND-EU_SSP2_PkBudg650_<year>``  -- very optimistic: carbon budget 650 Gt (about 1.5 degC)
* ``ei312_REMIND-EU_SSP2_NPi_<year>``        -- very pessimistic: national policies implemented, no more

for 2030, 2040, 2050, 2075 and 2100. 2020 is shared with SSP2-NDC (the REMIND pathways do not
differ yet). One scenario-year at a time, so the memory stays within a laptop; databases that exist
already are skipped, so the script can be rerun after an interruption.

Runs in an environment with premise 2.4.9 and the project's Brightway versions (bw2data 4.7,
bw2calc 2.5, bw_temporalis 1.2); needs the premise key in ``PREMISE_KEY``:

    <venv>/bin/python scripts/build_premise_scenarios.py
"""

from __future__ import annotations

import os
import time

import bw2data as bd
from premise import NewDatabase

PROJECT = "ei312_REMIND_EU"
SOURCE = "ecoinvent-3.12-cutoff"
PATHWAYS = ("SSP2-PkBudg650", "SSP2-NPi")
YEARS = (2030, 2040, 2050, 2075, 2100)


def name(pathway: str, year: int) -> str:
    return f"ei312_REMIND-EU_{pathway.replace('-', '_')}_{year}"


def main() -> None:
    bd.projects.set_current(PROJECT)
    for pathway in PATHWAYS:
        for year in YEARS:
            db = name(pathway, year)
            if db in bd.databases:
                print(f"{db}: vorhanden, übersprungen", flush=True)
                continue
            t0 = time.time()
            print(f"{db}: start", flush=True)
            ndb = NewDatabase(
                scenarios=[{"model": "remind-eu", "pathway": pathway, "year": year}],
                source_db=SOURCE,
                source_version="3.12",
                key=os.environ["PREMISE_KEY"],
                biosphere_name="ecoinvent-3.12-biosphere",
            )
            ndb.update()
            ndb.write_db_to_brightway(name=[db])
            meta = bd.databases[db]
            meta["representative_time"] = f"{year}-01-01T00:00:00"
            bd.databases[db] = meta
            bd.databases.flush()
            print(f"{db}: fertig in {(time.time() - t0) / 60:.0f} min", flush=True)
            del ndb


if __name__ == "__main__":
    main()
