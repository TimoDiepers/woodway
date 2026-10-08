"""Direct air capture (sorbent, 100 kt/a) per grid cell and year: energy demand
from the ambient climate, life-cycle emissions from premise databases.

Levels come from premise (dataset "carbon dioxide, captured and stored, with a
sorbent-based direct air capture system, 100ktCO2", REMIND-EU SSP2-NDC):
0.5 MWh electricity and 5.4 GJ = 1.5 MWh heat per t CO2. How that demand
moves with the climate comes from Sendi et al. (2022, One Earth 5, 1153,
doi:10.1016/j.oneear.2022.09.003), who simulate the same kind of process
(amine sorbent, Lewatit VP OC 1065, steam-assisted TVSA) with hourly weather
everywhere on land:

* Heat at ~110 deg C from an air-source heat pump, their Eq. 29-31:
  COP = eta * T_H / (T_H - T_C), eta = 0.5, T_H = 110 + 10 deg C,
  T_C = T_ambient - 10 deg C. Colder air -> lower COP -> more electricity.
* The heat demand itself rises with humidity (water co-adsorbs on the amine
  and has to be desorbed too) and with cold (longer bed heating). Sendi et al.
  give that only as means of four climate classes (Table 1, total electricity
  incl. heat pumps): cold-dry 1.76, cold-humid 2.15, hot-dry 1.64, hot-humid
  2.11 MWh/t. ``fit_heat_demand`` fits a linear heat-demand factor in
  temperature and humidity to exactly those four numbers (with their COP and
  their 0.32 MWh/t for vacuum pumps, compressors and fans), and the model
  applies the *relative* factor to premise's 1.5 MWh heat.
* Cells whose coldest month averages below -15 deg C are excluded, after
  Sendi et al.'s exclusion of regions below -15 deg C on more than 30 days a
  year (only monthly means are used here). Below 1 deg C the performance is
  held at 1 deg C, as in their maps.

Emissions per t captured = electricity [MWh/t] x GWP of the country's
electricity in that year (premise links each country to its REMIND region)
+ everything else of the premise dataset (sorbent, plant, compression,
transport, storage) from ``scripts/dac_lca_precompute.py``. Yearly values
between the premise vintages are interpolated linearly.

Net efficiency, the comparison metric with afforestation:

    eta_DAC = 1 - emissions per t CO2 removed / 1 t

the share of the removed CO2 that is a net removal.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from nbs.dac_climate import climate_grid, country_for_land
from nbs.grid import cell_area_m2

ROOT = Path(__file__).resolve().parents[2]
LCA_FILE = ROOT / "data" / "dac" / "lca_vintages.json"

# premise, sorbent DAC 100 kt/a (per t CO2)
PREMISE_ELECTRICITY_MWH = 0.5
PREMISE_HEAT_MWH = 5.4 / 3.6
# Climeworks Hinwil as reported in Sendi et al. (2022), SI table (sensitivity)
CLIMEWORKS_ELECTRICITY_MWH = 0.70
CLIMEWORKS_HEAT_MWH = 3.31

# Sendi et al. (2022)
SENDI_CLASSES = {  # (cold?, dry?) -> mean total electricity incl. heat pumps [MWh/t], Table 1
    (True, True): 1.76,
    (True, False): 2.15,
    (False, True): 1.64,
    (False, False): 2.11,
}
SENDI_AUX_MWH = 0.26 + 0.06  # vacuum pumps/compressors + fans, SI table
T_CLASS_SPLIT_C, RH_CLASS_SPLIT_PCT = 18.0, 65.0
T_HEATING_C, DT_MIN_K, ETA_2ND = 110.0, 10.0, 0.5
T_FLOOR_C = 1.0
T_COLDEST_MONTH_MIN_C = -15.0
REFERENCE = (20.0, 50.0)  # (deg C, % RH): Sendi et al.'s fixed-condition reference


def cop(t_c: NDArray) -> NDArray:
    """Heat-pump COP at ambient temperature, Sendi et al. Eq. 29-31."""
    t = np.maximum(t_c, T_FLOOR_C)
    t_hot = T_HEATING_C + DT_MIN_K + 273.15
    t_cold = t - DT_MIN_K + 273.15
    return ETA_2ND * t_hot / (t_hot - t_cold)


def dac_possible() -> NDArray:
    """Land cells warm enough for DAC (coldest month >= -15 deg C)."""
    c = climate_grid()
    return np.isfinite(c["t_mean_c"]) & (c["t_coldest_month_c"] >= T_COLDEST_MONTH_MIN_C)


def _climate_classes() -> dict[tuple[bool, bool], NDArray]:
    c = climate_grid()
    ok = dac_possible()
    cold = c["t_mean_c"] < T_CLASS_SPLIT_C
    dry = c["rh_mean_pct"] < RH_CLASS_SPLIT_PCT
    return {(k_cold, k_dry): ok & (cold == k_cold) & (dry == k_dry) for k_cold, k_dry in SENDI_CLASSES}


def _heat_factor(t_c: NDArray, rh: NDArray, a_t: float, a_rh: float) -> NDArray:
    """Heat demand relative to the reference climate (20 deg C, 50 % RH)."""
    t = np.maximum(t_c, T_FLOOR_C)
    return 1.0 + a_t * (t - REFERENCE[0]) / 10.0 + a_rh * (rh - REFERENCE[1]) / 10.0


@dataclass(frozen=True)
class HeatFit:
    q_ref_mwh: float  # Sendi's heat demand at the reference climate [MWh_th/t]
    a_t: float  # per 10 K
    a_rh: float  # per 10 % RH
    class_model: dict  # class -> modelled mean total electricity [MWh/t]
    max_abs_error_mwh: float


@lru_cache(maxsize=1)
def fit_heat_demand() -> HeatFit:
    """Fit Sendi et al.'s four class means (area-weighted over our cells)."""
    from scipy.optimize import least_squares

    c = climate_grid()
    area = cell_area_m2()
    classes = _climate_classes()

    def model(p):
        q, a_t, a_rh = p
        e = q * _heat_factor(c["t_mean_c"], c["rh_mean_pct"], a_t, a_rh) / cop(c["t_mean_c"]) + SENDI_AUX_MWH
        return {k: float(np.average(e[m], weights=area[m])) for k, m in classes.items()}

    def residual(p):
        m = model(p)
        return np.array([m[k] - SENDI_CLASSES[k] for k in SENDI_CLASSES])

    sol = least_squares(residual, x0=[3.0, 0.0, 0.05])
    fitted = model(sol.x)
    return HeatFit(
        q_ref_mwh=float(sol.x[0]),
        a_t=float(sol.x[1]),
        a_rh=float(sol.x[2]),
        class_model=fitted,
        max_abs_error_mwh=float(np.max(np.abs(residual(sol.x)))),
    )


VARIANTS = ("waermepumpe", "dampf", "climeworks")


@lru_cache(maxsize=None)
def energy_grid(variant: str = "waermepumpe") -> dict[str, NDArray]:
    """Per cell [MWh/t CO2]: ``strom`` (electricity incl. heat pump) and
    ``waerme_dampf`` (heat from industrial steam, only for variant "dampf").
    NaN where DAC is not possible.

    * "waermepumpe": premise levels, heat via heat pump (main case);
    * "dampf": premise levels, heat from the industrial heat market (natural
      gas-dominated), no heat pump -- sensitivity;
    * "climeworks": measured Climeworks levels (Sendi et al. SI), heat pump.
    """
    fit = fit_heat_demand()
    c = climate_grid()
    ok = dac_possible()
    factor = _heat_factor(c["t_mean_c"], c["rh_mean_pct"], fit.a_t, fit.a_rh)
    if variant == "climeworks":
        el, heat = CLIMEWORKS_ELECTRICITY_MWH, CLIMEWORKS_HEAT_MWH
    else:
        el, heat = PREMISE_ELECTRICITY_MWH, PREMISE_HEAT_MWH
    heat_cell = heat * factor
    if variant == "dampf":
        strom, steam = np.full(ok.shape, el), heat_cell
    else:
        strom, steam = el + heat_cell / cop(c["t_mean_c"]), np.zeros(ok.shape)
    return {
        "strom": np.where(ok, strom, np.nan),
        "waerme_dampf": np.where(ok, steam, np.nan),
    }


PATHWAYS = {  # REMIND-EU pathway in premise -> label; the main case is SSP2-NDC
    "SSP2-NDC": "Mitte: heutige Zusagen",
    "SSP2-PkBudg650": "sehr optimistisch: 1,5 °C-Budget",
    "SSP2-NPi": "sehr pessimistisch: nur heutige Politik",
}


@lru_cache(maxsize=None)
def lca_vintages(pathway: str = "SSP2-NDC") -> dict:
    f = LCA_FILE if pathway == "SSP2-NDC" else LCA_FILE.with_name(f"lca_vintages_{pathway}.json")
    return json.loads(f.read_text())


def _interp(year: int, values: dict[int, float]) -> float:
    xs = sorted(values)
    return float(np.interp(year, xs, [values[x] for x in xs]))


@lru_cache(maxsize=None)
def electricity_gwp_grid(year: int, pathway: str = "SSP2-NDC") -> NDArray:
    """GWP100 of 1 kWh in each cell's country [kg CO2e/kWh], interpolated in time."""
    data = lca_vintages(pathway)["jahre"]
    codes = country_for_land()
    out = np.full(codes.shape, np.nan)
    per_country = {}
    for iso in set(codes.ravel()) - {""}:
        per_country[iso] = _interp(year, {int(y): d["strom_kg_pro_kwh"].get(iso, d["strom_kg_pro_kwh"]["World"])
                                          for y, d in data.items()})
    world = _interp(year, {int(y): d["strom_kg_pro_kwh"]["World"] for y, d in data.items()})
    land = np.isfinite(climate_grid()["t_mean_c"])
    for iso, val in per_country.items():
        out[codes == iso] = val
    out[land & (codes == "")] = world
    return out


def rest_gwp(year: int, pathway: str = "SSP2-NDC") -> float:
    """Everything but energy, per kg CO2 captured and stored [kg CO2e/kg]."""
    return _interp(year, {int(y): d["rest_kg_pro_kg"] for y, d in lca_vintages(pathway)["jahre"].items()})


def steam_heat_gwp(year: int, pathway: str = "SSP2-NDC") -> float:
    """[kg CO2e/MJ] of the industrial heat market (sensitivity "dampf")."""
    return _interp(year, {int(y): d["waerme_dampf_kg_pro_mj"] for y, d in lca_vintages(pathway)["jahre"].items()})


@lru_cache(maxsize=None)
def emissions_grid(year: int, variant: str = "waermepumpe", pathway: str = "SSP2-NDC") -> NDArray:
    """Life-cycle GWP100 per t CO2 removed [t CO2e/t], per cell, NaN where
    DAC is not possible; electricity mix and background of the REMIND-EU *pathway*."""
    e = energy_grid(variant)
    # MWh/t * kg/kWh = t/t ; MWh_th/t * 3600 MJ/MWh * kg/MJ / 1000 = t/t
    return (e["strom"] * electricity_gwp_grid(year, pathway)
            + e["waerme_dampf"] * 3600.0 * steam_heat_gwp(year, pathway) / 1000.0 + rest_gwp(year, pathway))


def efficiency_grid(year: int, variant: str = "waermepumpe", pathway: str = "SSP2-NDC") -> NDArray:
    """eta_DAC = 1 - emissions per t removed."""
    return 1.0 - emissions_grid(year, variant, pathway)
