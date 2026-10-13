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
ACKER_FUTTER = 0.38       # Poore & Nemecek 2018 (Table S10, via Our World in Data): 38 % of cropland grows feed;
                          # gross that is freed, the replacement crops take back ACKER_FUTTER - ACKER_NETTO_FREI
RIND_ENTWALDUNG = 0.41    # beef's share of agricultural deforestation 2001-2023 (Singh & Persson 2026, via OWID)


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


def _nenner() -> dict[str, float]:
    """What FAOSTAT's kt are a share of: its farm totals (Very Low's farm path known), else Very Low's total."""
    fao = json.loads(FAO.read_text())
    if quelle_bezug() == "agrar":
        return {"CH4": fao["ch4_agrar_kt"], "N2O": fao["n2o_agrar_kt"]}
    y = f"{fao['jahr']}.5"
    return {"CH4": float(_vl("CH4")[y]) * 1e3, "N2O": float(_vl("N2O")[y])}


@lru_cache(maxsize=1)
def livestock_shares() -> dict[str, float]:
    """Livestock share in FAOSTAT's year: of farm CH4/N2O (FAOSTAT's own farm total) when Very Low's farm path is
    known, else of Very Low's total CH4/N2O. Held constant over time. N2O net of the replacement crops."""
    fao, n = json.loads(FAO.read_text()), _nenner()
    return {"CH4": fao["ch4_kt"] / n["CH4"], "N2O": (fao["n2o_tier_kt"] + ACKER_NETTO_FREI * fao["n2o_acker_kt"]) / n["N2O"]}


def _co2_pfad(variable: str) -> NDArray:
    """Very Low's CO2 [Mt/a] on YEARS, only where it is emitted (no removals), relative to FAOSTAT's year."""
    v = np.array([max(0.0, float(_vl(variable)[f"{y}.5"])) for y in YEARS])
    return v / float(_vl(variable)[f"{json.loads(FAO.read_text())['jahr']}.5"])


def emission_parts() -> dict[str, dict[str, NDArray]]:
    """Change of emissions per year of YEARS by cause: CH4 [Mt/a], N2O [kt/a], CO2 FFI and CO2 AFOLU [Mt/a].

    - ch4_tier: livestock methane avoided.
    - n2o_vermieden: N2O of livestock and of the feed crops (ACKER_FUTTER of cropland N2O) avoided.
    - co2_hof: fossil CO2 up to the farm gate (farm energy, fertiliser and pesticide manufacture) of the feed crops
      avoided, ACKER_FUTTER of it; falls with Very Low's fossil CO2.
    - co2_entwaldung: deforestation for beef avoided, RIND_ENTWALDUNG of FAOSTAT's net forest conversion; falls with
      Very Low's land-use CO2 and ends where that turns into a sink (Very Low stops deforestation by itself).
    - ersatz: what the replacement crops add on ACKER_FUTTER - ACKER_NETTO_FREI of cropland, N2O and farm-gate CO2.
    Post-farm CO2 (processing, transport, retail) is taken as the same for the replacement foods."""
    fao, n = json.loads(FAO.read_text()), _nenner()
    ch4, n2o = _bezug_pfad("CH4"), _bezug_pfad("N2O")
    ffi, afolu = _co2_pfad("CO2 FFI") * fao["co2_hof_kt"] / 1e3, _co2_pfad("CO2 AFOLU") * fao["co2_entwaldung_kt"] / 1e3
    ersatz = ACKER_FUTTER - ACKER_NETTO_FREI
    return {"ch4_tier": {"CH4": -fao["ch4_kt"] / n["CH4"] * ch4},
            "n2o_vermieden": {"N2O": -(fao["n2o_tier_kt"] + ACKER_FUTTER * fao["n2o_acker_kt"]) / n["N2O"] * n2o},
            "co2_hof": {"CO2 FFI": -ACKER_FUTTER * ffi},
            "co2_entwaldung": {"CO2 AFOLU": -RIND_ENTWALDUNG * afolu},
            "ersatz": {"N2O": ersatz * fao["n2o_acker_kt"] / n["N2O"] * n2o, "CO2 FFI": ersatz * ffi}}


def emission_delta() -> dict[str, NDArray]:
    """Net change of emissions per year of YEARS (sum of emission_parts): CH4 [Mt/a], N2O [kt/a], CO2 [Mt/a]."""
    out: dict[str, NDArray] = {}
    for part in emission_parts().values():
        for sp, v in part.items():
            out[sp] = out.get(sp, 0) + v
    return out


def _dt_fair(delta: dict[str, NDArray]) -> NDArray:
    """Temperature change [K] on YEARS of an emission change (CH4 [Mt/a], N2O [kt/a] on YEARS), FaIR on Very Low."""
    from nbs.fair_module import _END_IDX, _START_IDX, run_fair_baseline, run_fair_emission_delta

    n = _END_IDX - _START_IDX
    fair_unit = {"CH4": 1.0, "N2O": 1e-3, "CO2 FFI": 1e-3, "CO2 AFOLU": 1e-3}   # FaIR: N2O in Mt, CO2 in Gt
    d = {sp: np.pad(v * fair_unit[sp], (0, max(0, n - len(v))))[:n] for sp, v in delta.items()}
    out = run_fair_emission_delta(d, SCENARIO) - run_fair_baseline(SCENARIO)
    out = np.append(out, out[-1])[: len(YEARS)]
    out.setflags(write=False)
    return out


@lru_cache(maxsize=1)
def dt_gase() -> NDArray:
    """Temperature change [K] on YEARS from the emissions alone (CH4, N2O, CO2), FaIR on Very Low."""
    return _dt_fair(emission_delta())


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


def _dt_wald(nee: NDArray, rf: NDArray) -> NDArray:
    from nbs.fair_module import run_fair_baseline, run_fair_perturbed

    base = run_fair_baseline("ssp245")
    d = run_fair_perturbed(nee[: len(base)], rf[: len(base)], "ssp245") - base
    out = np.append(d, d[-1])[: len(YEARS)]
    out.setflags(write=False)
    return out


@lru_cache(maxsize=1)
def dt_flaeche() -> NDArray:
    """Temperature change [K] on YEARS of forest on the freed land, one FaIR run (SSP2-4.5 background, as the
    trees of chapter 2-3)."""
    nee, rf, _ = _flaeche_forcing()
    return _dt_wald(nee, rf)


@lru_cache(maxsize=1)
def contributions() -> dict[str, NDArray]:
    """Temperature change [K] on YEARS by cause, each its own FaIR run, and netto = dt_gase + dt_flaeche (the
    parts add up to it only nearly, FaIR is not quite linear)."""
    nee, rf, _ = _flaeche_forcing()
    out = {k: _dt_fair(v) for k, v in emission_parts().items()}
    out["wald_co2"] = _dt_wald(nee, np.zeros_like(rf))
    out["wald_albedo"] = _dt_wald(np.zeros_like(nee), rf)
    out["netto"] = dt_gase() + dt_flaeche()
    return out


def flaeche_info() -> dict:
    """Freed forest-capable land and the part of it that cools [Gha]."""
    return {"frei_gha": float(freed_area_m2().sum() / 1e13), "kuehlt_gha": float(_flaeche_forcing()[2])}
