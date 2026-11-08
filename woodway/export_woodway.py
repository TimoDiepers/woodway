"""Data for woodway (woodway/public/data): every per-place result of the model on the 0.5 deg grid.

Writes meta.json (grid, curves, palettes, global paths, reference values) and fields.bin (360x720
fields, float32 or uint8, offsets in meta.json), plus each field alone as fields/<name>.bin.gz (gzip -9,
mtime 0, so the same data gives the same bytes): the browser fetches the fields of the layer on screen first
and the others after them, and inflates them; fields.bin stays as the fallback. The browser evaluates years exactly:
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


PLANT_YEARS = list(range(T_START, 2062, 5))   # the planting years woodway offers (2026-2061, as the deck's backup)
AGE_BIN = 3                                    # years per age bin of today's forest (keeps the curve table small)


def type_curves(plant_year: int = T_START) -> dict:
    """Per forest type, the curves of one tree at its reference site, planted in *plant_year*."""
    g_t = green_temperature(SZENARIO)
    out = {}
    for key in SPECIES:
        res = run_single_tree(key, lat_deg=reference_site(key), plant_year=plant_year)
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


def _dt_uptake(uptake_kgC: np.ndarray) -> np.ndarray:
    """Temperature change [K] of one tree's net carbon uptake series on YEARS (the CO2 chain of nbs.pipeline)."""
    from nbs.config import ModelConfig
    from nbs.forcing import co2_flux_kg_per_yr, phi_co2, phi_co2_background
    from nbs.pipeline import _green_carbon_for
    from nbs.response import background_co2_ppm
    cfg = ModelConfig()
    flux = co2_flux_kg_per_yr(uptake_kgC)
    g_c = _green_carbon_for(cfg, SZENARIO)
    f = phi_co2(flux, g_c) if cfg.co2_forcing == "linear" else phi_co2_background(flux, g_c, background_co2_ppm(SZENARIO))
    return convolve_response(green_temperature(SZENARIO), f)


def bestand_curves() -> dict:
    """Per forest type, what one tree of today's forest does from T_START on if it stays (nbs.tree_paths.felling_*):
    its further uptake from the age that holds its stock (per age bin, at site factor 1), and its canopy's albedo at
    full closure, held from T_START (per unit of the light product, as dtAlbUnit). Felling is the opposite of both."""
    from nbs.tree_paths import _trajectory
    g_t = green_temperature(SZENARIO)
    n = len(YEARS)
    out = {}
    for key in SPECIES:
        up, _, st = _trajectory(key, int(YEARS[0]))
        sp = get_species(key)
        canopy = -TAU_ATM * np.ones(n) * sp.stand_area_m2 / A_EARTH_M2
        bins = []
        for b in range(0, n // AGE_BIN + 2):
            a0 = min(b * AGE_BIN + AGE_BIN // 2, n - 1)
            u = np.maximum(up[np.minimum(a0 + np.arange(n), n - 1)], 0.0)
            bins.append(_r(_dt_uptake(u)))
        out[key] = {"dtUp": bins, "dtCanopy": _r(convolve_response(g_t, canopy)),
                    "stockRef": _r(np.maximum.accumulate(st))}
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
            # installed capacity per country and year [Gt CO2/a] (not the removal running that year)
            "capacityGt": film["paths"]["opt"]["kap"]}


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
    # the land a vegan world frees and that could carry forest (deck chapter 5, nbs.vegan): its area, the typical
    # forest there (key_grid over all cells) and that forest's site factor on the freed land's carbon, as
    # nbs.tree_paths.forcing_cells; the browser evaluates it like the reforestable cells (a, b with the type curves)
    from nbs.forest_data import key_grid
    from nbs.tree_paths import _site_factor
    from nbs.vegan import freed_area_m2, freed_carbon_mgc_ha
    fkeys = key_grid(all_cells=True)
    fsite = _site_factor(fkeys, freed_carbon_mgc_ha())
    farea = freed_area_m2()
    fcode = np.zeros((360, 720), dtype=np.uint8)
    fa = np.full((360, 720), np.nan)
    fb = np.full((360, 720), np.nan)
    for n, key in enumerate(keys, start=1):
        m = (fkeys == key) & (farea > 0) & (fsite > 0)
        fcode[m] = n
        fa[m] = fsite[m]
        fb[m] = _product_no_nan(key)[m]
    f.add("freeArea", np.where(fcode > 0, farea, 0.0), "f4")
    f.add("freeType", fcode, "u1")
    f.add("freeA", fa, "f4")
    f.add("freeB", fb, "f4")
    # today's forest (Walker et al. 2022, woody land: nbs.tree_paths._bestand): its type, area, site factor on the
    # potential carbon, the age bin that holds today's stock, the light product, and where forest warms (felling)
    from nbs.tree_paths import _bestand, felling_cells, _trajectory
    barea, bcur, bpot = _bestand()
    bsite = _site_factor(fkeys, bpot)
    bcode = np.zeros((360, 720), dtype=np.uint8)
    bage = np.zeros((360, 720), dtype=np.uint8)
    bb = np.full((360, 720), np.nan)
    for n_, key in enumerate(keys, start=1):
        m = (fkeys == key) & (barea > 0) & (bsite > 0)
        if not m.any():
            continue
        bcode[m] = n_
        bb[m] = _product_no_nan(key)[m]
        _, _, st = _trajectory(key, int(YEARS[0]))
        s_ref = np.maximum.accumulate(st)
        c_tree = bcur[m] * 1000.0 * get_species(key).stand_area_m2 / 1e4
        a0 = np.searchsorted(s_ref, c_tree / bsite[m])
        bage[m] = np.minimum(a0 // AGE_BIN, len(YEARS) // AGE_BIN + 1)
    fell = felling_cells() & (bcode > 0)
    f.add("bArea", np.where(bcode > 0, barea, 0.0), "f4")
    f.add("bType", bcode, "u1")
    f.add("bA", np.where(bcode > 0, bsite, np.nan), "f4")
    f.add("bAge", bage, "u1")
    f.add("bB", bb, "f4")
    f.add("bFell", fell.astype(np.uint8), "u1")
    f.add("elec", np.where(ok, energy_grid("waermepumpe")["strom"], np.nan), "f4")
    f.add("dacOk", ok.astype(np.uint8), "u1")
    for y in base_years:
        f.add(f"dacNet{y}", efficiency_grid(y), "f4")

    curves = type_curves()
    years = [int(y) for y in YEARS]
    # the same tree planted later: the curves that change with the planting year (the 2026 ones stay in curves)
    later = {str(y): {k: {c: v[c] for c in ("m", "closure", "dtCo2", "dtAlbUnit")} for k, v in type_curves(y).items()}
             for y in PLANT_YEARS[1:]}
    bcurves = bestand_curves()

    # today's forest worldwide, the sum of its cells (each one linear, as the map): ΔT [mK] if it stays, of its
    # uptake alone, and of felling where it warms; and its uptake [Gt CO2/a]
    from nbs.constants import M_CO2_PER_C
    from nbs.tree_paths import _trajectory as _traj
    tot = {"keep": np.zeros(len(years)), "uptake": np.zeros(len(years)), "fell": np.zeros(len(years)), "gt": np.zeros(len(years))}
    for n_, key in enumerate(keys, start=1):
        m = bcode == n_
        if not m.any():
            continue
        trees = barea[m] / get_species(key).stand_area_m2
        bc = bcurves[key]
        up, _, _ = _traj(key, int(YEARS[0]))
        for ab in np.unique(bage[m]):
            mm = bage[m] == ab
            w_up = float((bsite[m][mm] * trees[mm]).sum())
            w_alb = float((bb[m][mm] * trees[mm]).sum())
            d_up = w_up * np.asarray(bc["dtUp"][ab]); d_alb = w_alb * np.asarray(bc["dtCanopy"])
            tot["keep"] += d_up + d_alb; tot["uptake"] += d_up
            fm = fell[m][mm]
            if fm.any():
                tot["fell"] -= float((bsite[m][mm][fm] * trees[mm][fm]).sum()) * np.asarray(bc["dtUp"][ab]) \
                    + float((bb[m][mm][fm] * trees[mm][fm]).sum()) * np.asarray(bc["dtCanopy"])
            a0 = min(int(ab) * AGE_BIN + AGE_BIN // 2, len(years) - 1)
            u = np.maximum(up[np.minimum(a0 + np.arange(len(years)), len(years) - 1)], 0.0)
            tot["gt"] += w_up * M_CO2_PER_C * u / 1e12

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
        "plantYears": PLANT_YEARS,
        "curvesLater": later,
        "bestand": {"curves": bcurves, "ageBin": AGE_BIN,
                    "areaGha": round(float(barea[bcode > 0].sum() / 1e13), 3), "fellGha": round(float(barea[fell].sum() / 1e13), 3),
                    # the canopy's albedo of today's forest is in today's climate already: only what changes counts,
                    # its further uptake (cools) and, where it is cut, the brighter land minus the lost uptake
                    "uptakeMK": _r(1000 * tot["uptake"], 4), "fellMK": _r(1000 * tot["fell"], 4),
                    "uptakeGt": _r(tot["gt"], 4)},
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
    (OUT / "fields.bin").write_bytes(raw)   # all fields in one, for browsers without DecompressionStream
    # each field on its own, gzip -9 with mtime 0 (the same data gives the same bytes): the browser fetches the
    # fields of the layer on screen first and the rest after it
    fdir = OUT / "fields"
    fdir.mkdir(exist_ok=True)
    for old in fdir.glob("*.bin.gz"):
        old.unlink()
    for name, d in f.meta.items():
        n = d["length"] * (4 if d["dtype"] == "f4" else 1)
        (fdir / f"{name}.bin.gz").write_bytes(gzip.compress(raw[d["offset"]: d["offset"] + n], compresslevel=9, mtime=0))
    (OUT / "fields.bin.gz").unlink(missing_ok=True)
    (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
                                   encoding="utf-8")
    print(f"wrote {OUT}: {f.offset / 1e6:.1f} MB fields, {len(reference)} reference cells")


if __name__ == "__main__":
    main()
