"""Data for woodway (woodway/public/data): every per-place result of the model on the 0.5 deg grid.

Writes meta.json (grid, curves, palettes, global paths, reference values) and fields.bin (360x720
fields, float32 or uint8, offsets in meta.json), plus fields.bin.gz (gzip -9, mtime 0, so the same data
gives the same bytes), which the browser fetches and inflates; fields.bin stays as the fallback. The browser evaluates years exactly:
  tree:  dT(t) = a * dtCo2_type(t) + b * dtAlbUnit_type(t)   (nbs.aggregate: site factor and albedo
         product scale the two unit curves linearly)
  DAC:   net share interpolated linearly between the LCA base years (nbs.dac._interp does the same).

    uv run python woodway/export_woodway.py
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np

from nbs.aggregate import _product_no_nan, co2_factor_grid
from nbs.animations import _STAND_AREA_M2, SITES, _by_type, cloud_brightening_grid, typical_light_product, typical_measured_mask
from nbs.constants import A_EARTH_M2, T_START, TAU_ATM, YEARS, SZENARIO
from nbs.dac import dac_possible, efficiency_grid, energy_grid, lca_vintages
from nbs.dac_climate import climate_grid
from nbs.dac_optim import GROWTH
from nbs.forest_data import reforestable_area_m2
from nbs.landscape import assign_species
from nbs.map_fields import CATEGORIES, LAND, SCALES, TOO_COLD, UNMEASURED
from nbs.pipeline import run_single_tree
from nbs import albedo_grid
from nbs.response import convolve_response, green_temperature
from nbs.species import SPECIES, get_species, reference_site

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "woodway" / "public" / "data"
CHART_DATA = ROOT / "deck" / "chart_data"


def _r(a, nd=6):
    return [float(f"{v:.{nd}g}") for v in np.asarray(a, dtype=float)]


def type_curves() -> dict:
    """Per forest type, the curves of one tree at its reference site, planted in T_START."""
    g_t = green_temperature(SZENARIO)
    out = {}
    for key in SPECIES:
        res = run_single_tree(key, lat_deg=reference_site(key), plant_year=T_START)
        sp = get_species(key)
        unit_alb = -TAU_ATM * np.asarray(res.trajectory.closure, dtype=float) * sp.stand_area_m2 / A_EARTH_M2
        out[key] = {
            "m": _r(res.trajectory.stock_kgC),
            "phiCo2": _r(res.phi_co2),
            "closure": _r(res.trajectory.closure),
            "phiAlbUnit": _r(unit_alb),
            "dtCo2": _r(convolve_response(g_t, res.phi_co2)),
            "dtAlbUnit": _r(convolve_response(g_t, unit_alb)),
        }
    return out


class _Fields:
    def __init__(self):
        self.parts: list[bytes] = []
        self.meta: dict = {}
        self.offset = 0

    def add(self, name: str, arr: np.ndarray, dtype: str) -> None:
        assert arr.shape == (360, 720), (name, arr.shape)
        a = np.ascontiguousarray(arr, dtype=np.float32 if dtype == "f4" else np.uint8)
        b = a.tobytes()
        pad = (-self.offset) % 4  # keep every float32 field 4-byte aligned for Float32Array views
        if pad:
            self.parts.append(b"\0" * pad)
            self.offset += pad
        self.meta[name] = {"offset": self.offset, "dtype": dtype, "length": a.size}
        self.parts.append(b)
        self.offset += len(b)


def build_table() -> dict:
    """DAC capacity per cell over time: the optimisation behind the deck's DAC film."""
    film = json.loads((CHART_DATA / "dacfilm.json").read_text(encoding="utf-8"))
    cells = [[int(round((90.0 - lat) / 0.5 - 0.5)), int(round((lon + 180.0) / 0.5 - 0.5))] for lon, lat in film["cells"]]
    return {"years": film["years"], "countries": film["countries"], "cells": cells, "owner": film["owner"],
            "capacityGt": film["paths"]["opt"]["cc"]}


def _dac_case(c: dict) -> dict:
    """One DACCS plan of the deck (zeitpfade.json): world capacity and its cost per year (trillion EUR, the
    optimistic plan priced with the median, the optimistic and the pessimistic costs)."""
    k = c["kosten"]
    return {"capGt": c["w"], "costMed": k["median"]["je_jahr_bio"], "costLo": k["optimistisch"]["je_jahr_bio"],
            "costHi": k["pessimistisch"]["je_jahr_bio"], "sumMed": k["median"]["summe_bio"], "eurT": k["median"]["eur_t"],
            "back": c["ab"]}


def global_paths() -> dict:
    z = json.loads((CHART_DATA / "zeitpfade.json").read_text(encoding="utf-8"))
    film = json.loads((CHART_DATA / "dacfilm.json").read_text(encoding="utf-8"))
    w, veg = z["wirkung"], z["vegan"]
    return {"years": z["jahre"], "need": z["noetig"], "afterTrees": z["baeume_rest"],
            "afterDac": film["paths"]["opt"]["dac"], "dacCapacityGt": film["paths"]["opt"]["tot"],
            "paths": {k: z["pfade"][k] for k in ("alle", "kuehlt", "forst")},
            "areasGha": {k: z["flaechen_gha"][k] for k in ("alle", "kuehlt")},
            # the deck's anchor (chapter 5): Very Low in deg C and what each measure does to it [mK, < 0 = cooler]
            "vlC": z["vl_c"],
            "effect": {"trees": w["baeume"], "vegan": w["vegan"], "dac20": w["dac_20"], "dac50": w["dac_50"],
                       "dac100": w["dac_100"], "veganDac": w["dac_vegan"]},
            "dac": {**{g: _dac_case(z["dac"][f"g{g}"]) for g in ("20", "50", "100")}, "vegan": _dac_case({**veg["g20"], "kosten": veg["kosten"]})},
            "vegan": {"freeGha": veg["frei_gha"], "coolsGha": veg["kuehlt_gha"]},
            # the rules behind the two curves, for the strip's source line
            "plantYear": int(T_START), "dacGrowthPct": round((GROWTH - 1) * 100, 3)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    keys = list(SPECIES)
    species = assign_species()
    code = np.zeros((360, 720), dtype=np.uint8)
    a = np.full((360, 720), np.nan)
    b = np.full((360, 720), np.nan)
    for n, key in enumerate(keys, start=1):
        m = species == key
        code[m] = n
        a[m] = co2_factor_grid(key)[m]
        b[m] = _product_no_nan(key)[m]

    area = np.where(code > 0, reforestable_area_m2(), 0.0)
    land = np.isfinite(climate_grid()["t_mean_c"]) | (area > 0)
    ok = dac_possible()
    base_years = sorted(int(y) for y in lca_vintages()["jahre"])

    f = _Fields()
    f.add("land", land.astype(np.uint8), "u1")
    f.add("type", code, "u1")
    f.add("area", area, "f4")
    f.add("trees", area / _STAND_AREA_M2, "f4")
    f.add("sun", _by_type(albedo_grid.insolation_grid), "f4")
    f.add("darker", -100.0 * _by_type(albedo_grid.delta_alpha_grid), "f4")
    f.add("light", -typical_light_product() * _STAND_AREA_M2, "f4")
    # albedo of the cell's typical forest measured locally; elsewhere sun/darker are NaN and light is
    # gap-filled -- the deck (b8/b8a) shows measured cells only, so does woodway
    f.add("measured", typical_measured_mask().astype(np.uint8), "u1")
    # extra reflection of the extra clouds over the typical forest [%-points], where Duveiller et al. 2021 retrieve
    # it locally (deck b8i, third panel); NaN elsewhere
    cloud, cloud_ok = cloud_brightening_grid()
    f.add("cloud", np.where(cloud_ok & (code > 0), cloud, np.nan), "f4")
    f.add("a", a, "f4")
    f.add("b", b, "f4")
    f.add("elec", np.where(ok, energy_grid("waermepumpe")["strom"], np.nan), "f4")
    f.add("dacOk", ok.astype(np.uint8), "u1")
    for y in base_years:
        f.add(f"dacNet{y}", efficiency_grid(y), "f4")

    curves = type_curves()
    years = [int(y) for y in YEARS]

    def dt_at(i, j, year):
        k = years.index(year)
        c = curves[keys[code[i, j] - 1]]
        return float(np.float32(a[i, j]) * c["dtCo2"][k] + np.float32(b[i, j]) * c["dtAlbUnit"][k])

    reference = []
    for s in SITES:
        i, j = int((90.0 - s.lat) // 0.5), int((s.lon + 180.0) // 0.5)
        if code[i, j] == 0:
            continue
        k = years.index(2100)
        carbon = np.float32(a[i, j]) * curves[keys[code[i, j] - 1]]["dtCo2"][k]
        reference.append({"i": i, "j": j, "dt2050": dt_at(i, j, 2050), "dt2100": dt_at(i, j, 2100),
                          "net2100": float(dt_at(i, j, 2100) / carbon),
                          # no DAC in the cell (e.g. Fairbanks): null, the browser gives NaN there
                          **{f"dac{y}": (None if np.isnan(v := float(efficiency_grid(y)[i, j])) else v) for y in (2026, 2045)}})

    assert len(reference) == 3, f"expected the three example sites, got {len(reference)}"

    meta = {
        "version": 1,
        "grid": {"nlat": 360, "nlon": 720, "d": 0.5, "lat0": 90.0, "lon0": -180.0},
        "years": years,
        "fields": f.meta,
        "types": keys,
        "typeGroup": {k: k.split("_")[0] for k in keys},
        "curves": curves,
        "dacYears": base_years,
        "build": build_table(),
        "global": global_paths(),
        "sites": [{"name": s.label, "lat": s.lat, "lon": s.lon, "color": s.color} for s in SITES],
        "scales": SCALES,
        "categories": {"waldtyp": CATEGORIES["waldtyp"]},
        "colors": {"land": LAND, "tooCold": TOO_COLD, "unmeasured": UNMEASURED},
        "reference": reference,
    }
    raw = b"".join(f.parts)
    (OUT / "fields.bin").write_bytes(raw)
    (OUT / "fields.bin.gz").write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
                                   encoding="utf-8")
    print(f"wrote {OUT}: {f.offset / 1e6:.1f} MB fields, {len(reference)} reference cells")


if __name__ == "__main__":
    main()
