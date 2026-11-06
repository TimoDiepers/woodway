"""Existing forest per 0.5-degree cell, for the felling case (data/forest/bestand_0p5.npz).

Walker et al. (2022), doi:10.7910/DVN/DSDDQK: woody land today is NCS opportunity categories MM/L, M/L, MM/H, M/H
(3, 4, 6, 7; 1 non-woody and 2, 5 reforestation are left out). Per cell the area [m^2] of these pixels and, over
exactly them, the area-weighted mean current AGB+BGB carbon (potential minus unconstrained unrealised) and the
potential [Mg C/ha].

    uv run python scripts/prepare_bestand.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_forest_data import ROOT, _mean, _strip_sum  # noqa: E402

OUT = ROOT / "data" / "forest" / "bestand_0p5.npz"
WOODY_CATEGORIES = (3, 4, 6, 7)


def existing_forest() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    def weigh(read):
        sel = np.isin(read(0), WOODY_CATEGORIES)
        if not sel.any():
            return None
        pot = np.maximum(read(1).astype(float), 0)
        unr = np.maximum(read(2).astype(float), 0)
        return sel.astype(float), [np.maximum(pot - unr, 0), pot]

    area, (cur_sum, pot_sum) = _strip_sum(
        ("NCS_Opportunity_Categories_500m.tif", "Base_Pot_AGB_BGB_MgCha_500m.tif",
         "Base_Unr_AGB_BGB_MgCha_500m.tif"), weigh)
    return area, _mean(cur_sum, area), _mean(pot_sum, area)


def main() -> None:
    area, cur, pot = existing_forest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT, area_m2=area.astype(np.float32), current_mgc_ha=cur.astype(np.float32),
                        potential_mgc_ha=pot.astype(np.float32))
    a = area.sum()
    print("bestand:", round(a / 1e13, 3), "Gha,", round(float((area * cur).sum()) / 1e4 / 1e9, 1), "Gt C current,",
          round(float((area * pot).sum()) / 1e4 / 1e9, 1), "Gt C potential")


if __name__ == "__main__":
    main()
