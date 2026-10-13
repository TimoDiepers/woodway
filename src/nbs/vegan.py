"""The vegan world: everyone eats vegan from T_START on (an upper bound, stated as such).

Two parts, as on the slides:

- gases: methane and nitrous oxide of livestock disappear. Taken as the livestock share of the CMIP7 Very Low
  emissions, so that what Very Low already cuts in agriculture is not counted twice: livestock's share of farm
  emissions (FAOSTAT 2022) applied to Very Low's farm path (data/vegan/vl_agrar.json, from the marker's
  sectoral data). Without that file the share of Very Low's total is used, held constant -- cautious, since
  Very Low cuts energy methane faster than farm methane. N2O of cropland
  (synthetic fertiliser, crop residues) falls by the net cropland a vegan diet frees (Poore & Nemecek 2018: -19 %).
- land: grazing land and the freed cropland grow forest (see dt_flaeche), the larger and more uncertain part.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from nbs.constants import YEARS

ROOT = Path(__file__).resolve().parents[2]
FAO = ROOT / "data/vegan/faostat_tierhaltung.json"
CMIP7_EM = ROOT / "data/cmip7/fair-inputs/emissions_1750-2500.csv"
VL_AGRAR = ROOT / "data/vegan/vl_agrar.json"   # Very Low's farm emissions by year, if found (QUELLE.md)
SCENARIO = "cmip7-VL"
ACKER_NETTO_FREI = 0.19   # Poore & Nemecek 2018: arable land -19 % in a vegan world, net of the replacement crops


@lru_cache(maxsize=None)
def _vl(specie: str) -> pd.Series:
    em = pd.read_csv(CMIP7_EM)
    return em[(em.scenario == "VL") & (em.variable == specie)].iloc[0]


def quelle_bezug() -> str:
    """"agrar": the shares refer to Very Low's farm path; "gesamt": to its total (fallback, cautious)."""
    return "agrar" if VL_AGRAR.exists() else "gesamt"


def _bezug_pfad(specie: str) -> NDArray:
    """What the livestock share is taken of, per year of YEARS: Very Low's farm path, else its total."""
    if quelle_bezug() == "agrar":
        a = json.loads(VL_AGRAR.read_text())
        return np.interp(YEARS, a["jahre"], a["ch4_mt" if specie == "CH4" else "n2o_kt"])
    return np.array([float(_vl(specie)[f"{y}.5"]) for y in YEARS])


@lru_cache(maxsize=1)
def livestock_shares() -> dict[str, float]:
    """Livestock share in FAOSTAT's year: of farm CH4/N2O (FAOSTAT's own farm total) when Very Low's farm path is
    known, else of Very Low's total CH4/N2O. Held constant over time."""
    fao = json.loads(FAO.read_text())
    n2o_tier = fao["n2o_tier_kt"] + ACKER_NETTO_FREI * fao["n2o_acker_kt"]
    if quelle_bezug() == "agrar":
        return {"CH4": fao["ch4_kt"] / fao["ch4_agrar_kt"], "N2O": n2o_tier / fao["n2o_agrar_kt"]}
    y = f"{fao['jahr']}.5"
    return {"CH4": fao["ch4_kt"] / 1e3 / float(_vl("CH4")[y]), "N2O": n2o_tier / float(_vl("N2O")[y])}


def emission_delta() -> dict[str, NDArray]:
    """Change of emissions per year of YEARS (negative): CH4 [Mt/a], N2O [kt/a]."""
    s = livestock_shares()
    return {sp: -s[sp] * _bezug_pfad(sp) for sp in ("CH4", "N2O")}


@lru_cache(maxsize=1)
def dt_gase() -> NDArray:
    """Temperature change [K] on YEARS from the gases alone, FaIR on Very Low."""
    from nbs.fair_module import _END_IDX, _START_IDX, run_fair_baseline, run_fair_emission_delta

    n = _END_IDX - _START_IDX
    fair_unit = {"CH4": 1.0, "N2O": 1e-3}   # FaIR holds N2O in Mt, emission_delta gives kt
    d = {sp: np.pad(v * fair_unit[sp], (0, max(0, n - len(v))))[:n] for sp, v in emission_delta().items()}
    base = run_fair_baseline(SCENARIO)
    out = run_fair_emission_delta(d, SCENARIO) - base
    out = np.append(out, out[-1])[: len(YEARS)]
    out.setflags(write=False)
    return out


FREI = ROOT / "data/vegan/frei_0p5.npz"   # scripts/prepare_forest_data.py --only-freed


@lru_cache(maxsize=1)
def _frei() -> dict[str, NDArray]:
    with np.load(FREI) as f:
        return {k: f[k].astype(float) for k in f.files}


def freed_area_m2() -> NDArray:
    """(360, 720) area a vegan world frees and that could carry forest [m^2] (Walker's grazing land in full,
    cropland at ACKER_NETTO_FREI, only where Walker's reforestation rule holds)."""
    return _frei()["freed_area_m2"].copy()


def freed_carbon_mgc_ha() -> NDArray:
    """(360, 720) unrealised AGB+BGB carbon on that area [Mg C/ha] (Walker, unconstrained)."""
    return _frei()["freed_carbon_mgc_ha"].copy()


@lru_cache(maxsize=1)
def _flaeche_forcing():
    from nbs.tree_paths import forcing_cells

    return forcing_cells(freed_area_m2(), freed_carbon_mgc_ha())


@lru_cache(maxsize=1)
def dt_flaeche() -> NDArray:
    """Temperature change [K] on YEARS of forest on the freed land, one FaIR run (SSP2-4.5 background, as the
    trees of chapter 2-3)."""
    from nbs.fair_module import run_fair_baseline, run_fair_perturbed

    nee, rf, _ = _flaeche_forcing()
    base = run_fair_baseline("ssp245")
    d = run_fair_perturbed(nee[: len(base)], rf[: len(base)], "ssp245") - base
    out = np.append(d, d[-1])[: len(YEARS)]
    out.setflags(write=False)
    return out


def flaeche_info() -> dict:
    """Freed forest-capable land and the part of it that cools [Gha]."""
    return {"frei_gha": float(freed_area_m2().sum() / 1e13), "kuehlt_gha": float(_flaeche_forcing()[2])}
