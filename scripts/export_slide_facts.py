"""Compute every model number the slide texts quote.

Writes ``deck/chart_data/fakten.json``. The slide texts in deck/src are typed
by hand; compare them against this file after a model change (FaIR
calibration, site factor, albedo source), and tests/test_slide_numbers.py
checks the headline numbers.

    .venv/bin/python scripts/export_slide_facts.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from nbs.aggregate import albedo_offset_summary, albedo_offset_field
from nbs.animations import SITES, site_cell
from nbs.constants import A_CO2_LOG_W_M2_PER_PPM, KG_CO2_PER_PPM, T_START, YEARS
from nbs.fair_module import CENTRAL_MEMBER, run_fair_baseline
from nbs.grid import grid_lats
from nbs.landscape import assign_species, plantable_area_m2
from nbs.map_plots import _breakeven_year_field
from nbs.metrics import t_star
from nbs.pipeline import _background_temperature, run_single_tree
from nbs.potential import cascade, reverse_1p5
from nbs.recommend import improvement, summary
from nbs.response import background_co2_ppm
from nbs.species import REFERENCE_SITES, get_species
from nbs.storyline_figures import ladder_delta_t, ladder_t_star, run_site
from nbs.tree import disturbance_probability

OUT = Path(__file__).resolve().parent.parent / "deck" / "chart_data" / "fakten.json"
ICE_FREE_LAND_GHA = 13.0  # rounded literature value, as on the slide


def _year(t: float) -> int | None:
    return int(t) if np.isfinite(t) else None


def sites() -> dict:
    out = {}
    for s in SITES:
        full = run_site(s)
        late = run_site(s, plant_year=2085)
        out[s.name] = {
            "t_star": _year(t_star(full.delta_t, YEARS)),
            "phi_negativ_ab": _year(t_star(full.phi_total, YEARS)),
            "delta_t_2150_K": float(full.delta_t[-1]),
            "anteil_pflanzjahr_2085": float(late.delta_t[-1] / full.delta_t[-1]),
            "leiter": [_year(t) for t in ladder_t_star(s)],
            "leiter_dt_2150_K": ladder_delta_t(s),
        }
    return out


def trees() -> dict:
    """Bäume chapter: the typical forest at both sites and the forest types."""
    from nbs.animations import site_key, site_uptake_kg_co2
    from nbs.forest_data import TREES_PER_HA, carbon_gain_mgc_ha, growth_by_key, reforestable_area_m2, typical_type
    from nbs.map_plots import TYPE_NAMES
    from nbs.storyline_figures import _site_species, site_annual_watts

    out = {"orte": {}}
    for s in SITES:
        sp = _site_species(s)
        i, j = site_cell(s)
        out["orte"][s.name] = {
            "art": site_key(s),
            "name": sp.name_de,
            "zuwachs_mgc_ha": float(carbon_gain_mgc_ha()[i, j]),
            "saettigung_kgc": float(sp.m_max_kgC),
            "saettigung_kg_co2": float(sp.m_max_kgC * 44.0 / 12.0),
            "aufnahme_2150_kg_co2": float(site_uptake_kg_co2(s)[-1]),
            "k": float(sp.k),
            "licht_w": site_annual_watts(s),
        }
    typ, a = typical_type(), reforestable_area_m2()
    out["typen_gha"] = {TYPE_NAMES[t]: float(a[typ == t].sum() / 1e13) for t in TYPE_NAMES}
    out["flaeche_wiederbewaldbar_gha"] = float(a.sum() / 1e13)
    out["flaeche_mit_typ_gha"] = float(a[typ != None].sum() / 1e13)  # noqa: E711
    out["baeume_je_ha"] = TREES_PER_HA
    out["k_je_art"] = {k: g["k"] for k, g in growth_by_key().items()}
    return out


def literature() -> dict:
    """Albedo comparison with the literature (nbs.storyline_figures.LITERATURE_REMAINING)."""
    from nbs.storyline_figures import LITERATURE_REMAINING, own_remaining

    return {"dieses_modell": own_remaining(),
            "studien": {lab: v for lab, _d, v, _lb in LITERATURE_REMAINING}}


def tree_energy() -> dict:
    """B10: last year in which the light (albedo) outweighs the naively
    converted CO2 at the tree, per site; None if CO2 leads from year one."""
    from nbs.storyline_figures import _shell_one_trajectory, naive_co2_watts, site_annual_watts

    out = {}
    for s in SITES:
        co2 = naive_co2_watts(s)
        alb = _shell_one_trajectory(s).closure * site_annual_watts(s)
        ahead = np.nonzero(alb[1:] >= co2[1:])[0]
        out[s.name] = int(YEARS[ahead[-1] + 1]) if ahead.size else None
    return out


def a_co2() -> dict:
    from nbs.response import green_carbon, green_carbon_preindustrial

    a = A_CO2_LOG_W_M2_PER_PPM / (background_co2_ppm("ssp245") * KG_CO2_PER_PPM) * 1e15
    return {
        "start": float(a[0]),
        "ende": float(a[-1]),
        # airborne fraction of a 2025 pulse in 2100: FaIR (scenario) vs Joos (shell 2)
        "g_c_fair_2100": float(green_carbon("ssp245")[2100 - T_START]),
        "g_c_joos_2100": float(green_carbon_preindustrial()[2100 - T_START]),
    }


def climate() -> dict:
    import pandas as pd

    from nbs.fair_module import _PARAMS_CSV

    base = run_fair_baseline("ssp245")
    return {
        "fair_mitglied": CENTRAL_MEMBER,
        "lambda_w_m2_k": float(pd.read_csv(_PARAMS_CSV, index_col=0).loc[CENTRAL_MEMBER, "ocean_heat_transfer[0]"]),
        "erwaermung_2025_K": float(base[0]),
        "erwaermung_2081_2100_K": float(base[56:76].mean()),
        "erwaermung_2150_K": float(base[-1]),
    }


def cascade_facts() -> dict:
    steps = cascade("ssp245")
    land, albedo, disturbance = steps[2], steps[3], steps[4]
    band = [float(v) for v in disturbance["band_gtc"]] if "band_gtc" in disturbance else None
    return {
        "flaeche_land_gha": land["area_gha"],
        "kohlenstoff_land_gtc": land["carbon_gtc"],
        "flaeche_nutzbar_gha": albedo["area_gha"],
        "kohlenstoff_nach_albedo_gtc": albedo["carbon_gtc"],
        "kohlenstoff_gtc": disturbance["carbon_gtc"],
        "band_gtc": band,
        "delta_t_2150_K": disturbance["delta_t_2150"],
        "anteil_bastin": disturbance["carbon_gtc"] / steps[0]["carbon_gtc"],
        "albedo_filter_anteil_flaeche": 1.0 - albedo["area_gha"] / land["area_gha"],
    }


def reverse() -> dict:
    r = reverse_1p5("ssp245")["mit_albedo_und_stoerung"]
    return {
        "vielfaches": r["vielfaches_der_modellierten_flaeche"],
        "flaeche_gha": r["area_gha"],
        "anteil_eisfrei": r["area_gha"] / ICE_FREE_LAND_GHA,
        "kritisches_jahr": r["kritisches_jahr"],
    }


def maps() -> dict:
    field = _breakeven_year_field("ssp245")
    plantable = assign_species() != None  # noqa: E711
    lats = np.abs(grid_lats())[:, None] * np.ones((1, field.shape[1]))
    boreal = plantable & (lats >= 50) & (lats < 70)
    rest = plantable & (lats < 50) & np.isfinite(field)
    gain = improvement(2100, "ssp245")
    rec = summary(2100, "ssp245")
    return {
        "boreal_nie_anteil": float(np.isinf(field[boreal]).mean()),
        "median_t_star_ausserhalb_boreal": float(np.median(field[rest])),
        "artenwahl_gewinn": gain["gewinn_anteil"],
        "empfohlen_gha": {k: v["flaeche_gha"] for k, v in rec.items()},
    }


def hasler() -> dict:
    s = albedo_offset_summary()
    field = albedo_offset_field()
    lats = np.abs(grid_lats())[:, None] * np.ones((1, field.shape[1]))
    finite = np.isfinite(field)

    def above_50(lo, hi):
        band = finite & (lats >= lo) & (lats < hi)
        return float(np.mean(field[band] > 50.0))

    # Dryland (temperate grassland/savanna) share that is net warming at the
    # horizon -- Hasler: 72 %. Same construction as
    # tests/test_hasler_comparison.py::test_model_cannot_reproduce_haslers_dryland_finding.
    from nbs.aggregate import _product_no_nan, co2_factor_grid, unit_curves
    from nbs.forest_data import key_grid
    from nbs.landscape import exclusion_mask
    from nbs.species import SPECIES

    dryland = exclusion_mask()["savanne_grasland"]
    keys_all = key_grid(all_cells=True)
    offset = np.full(dryland.shape, np.nan)
    for key in SPECIES:
        band = dryland & (keys_all == key)
        if not band.any():
            continue
        co2, albedo_unit = unit_curves(key)
        f = co2_factor_grid(key)
        offset[band] = _product_no_nan(key)[band] * float(albedo_unit[-1]) / (-(f[band] * float(co2[-1]))) * 100.0
    dry = offset[np.isfinite(offset)]

    return {
        "trockengebiet_netto_negativ": float(np.mean(dry > 100.0)),
        "median_offset_pct": float(s["median"]),
        "ueber_50": float(s["ueber_50"]),
        "ueber_100": float(s["ueber_100"]),
        "tropen_ueber_50": above_50(0, 35),
        "boreal_ueber_50": above_50(60, 70),
    }


def boreal_reference() -> dict:
    """Typical forest at the northern site (Fairbanks, conifer forest) for the DAC slide."""
    from nbs.animations import site_key
    from nbs.storyline_figures import run_site

    jo = SITES[1]
    res = run_site(jo)
    p = disturbance_probability(get_species(site_key(jo)), _background_temperature("ssp245"))[:50]
    return {
        "art": site_key(jo),
        "breite": jo.lat,
        "t_star": _year(t_star(res.delta_t, YEARS)),
        "stoerung_50_jahre": float(1.0 - np.prod(1.0 - p)),
    }


def dac_facts() -> dict:
    """Numbers for the DAC slides (nbs.dac, nbs.dac_compare, nbs.dac_figures)."""
    from nbs.dac import (PREMISE_ELECTRICITY_MWH, PREMISE_HEAT_MWH, dac_possible, efficiency_grid, energy_grid,
                         fit_heat_demand, lca_vintages)
    from nbs.dac_climate import climate_grid, country_for_land
    from nbs.dac_figures import area_shares, switch_year_grid
    from nbs.dac_compare import tree_efficiency_grid
    from nbs.grid import cell_area_m2
    from nbs.landscape import plantable_area_m2

    area = cell_area_m2()
    land = np.isfinite(climate_grid()["t_mean_c"])
    e = energy_grid()["strom"]
    fit = fit_heat_demand()
    shares = area_shares()
    sw = switch_year_grid()
    w = plantable_area_m2()
    codes = country_for_land()

    def median_switch(iso):
        m = (w > 0) & (codes == iso)
        fin = m & np.isfinite(sw)
        if not m.any():
            return None
        return {"median_jahr": int(np.median(sw[fin])) if fin.any() else None,
                "nie_anteil": float(w[m & ~np.isfinite(sw)].sum() / w[m].sum())}

    years = {T_START: 0, 2030: 2030 - T_START, 2040: 2040 - T_START, 2050: 2050 - T_START, 2070: 2070 - T_START}  # decision years up to LAST_PLANT_YEAR
    el = lca_vintages()["jahre"]
    return {
        "premise_strom_mwh": PREMISE_ELECTRICITY_MWH,
        "premise_waerme_mwh": PREMISE_HEAT_MWH,
        "strom_mwh": {"min": float(np.nanmin(e)), "median": float(np.nanmedian(e)), "max": float(np.nanmax(e))},
        "zu_kalt_anteil_land": float(1 - area[dac_possible()].sum() / area[land].sum()),
        "fit": {"a_t_pro_10k": fit.a_t, "a_rh_pro_10pp": fit.a_rh, "max_fehler_mwh": fit.max_abs_error_mwh},
        "strom_kg_pro_kwh_2020_2030_2050": {iso: [el[y]["strom_kg_pro_kwh"][iso] for y in ("2020", "2030", "2050")]
                                             for iso in ("DE", "FR", "NO", "PL", "US", "CN", "IN", "BR")},
        "wirkungsgrad_median": {y: float(np.nanmedian(efficiency_grid(y))) for y in years},
        "wirkungsgrad_median_dampf": {y: float(np.nanmedian(efficiency_grid(y, "dampf"))) for y in (T_START, 2050)},
        "wirkungsgrad_median_climeworks": {y: float(np.nanmedian(efficiency_grid(y, "climeworks"))) for y in (T_START, 2050)},
        "baum_wirkungsgrad_median_2025": float(np.nanmedian(tree_efficiency_grid(T_START))),  # key: start year
        "dac_besser_anteil": {y: float(shares["dac"][i]) for y, i in years.items()},
        "keins_kuehlt_anteil": {y: float(shares["nichts kühlt"][i]) for y, i in years.items()},
        "zu_kalt_anteil_bepflanzbar": float(w[(w > 0) & ~dac_possible()].sum() / w[w > 0].sum()),
        "umstieg": {iso: median_switch(iso) for iso in ("NO", "SE", "FI", "FR", "ES", "DE", "PL", "US", "BR", "CN",
                                                        "IN", "ID", "CD", "RU", "CA")},
    }


def vergleich_facts() -> dict:
    """Numbers for the restructured Vergleich chapter (nbs.vergleich_figures)."""
    from nbs.dac import dac_possible, electricity_gwp_grid, energy_grid, rest_gwp
    from nbs.dac_compare import tree_efficiency_grid
    from nbs.landscape import plantable_area_m2
    from nbs.vergleich_figures import (CMIP7_REMOVAL, PLACES, crossover_year, dac_eta_at, place_species,
                                       tree_eta_at, tree_potential_gtco2)

    gross, net = tree_potential_gtco2()
    vl_eng, vl_land = CMIP7_REMOVAL["Very Low"]
    w = plantable_area_m2()
    m = w > 0
    eff = tree_efficiency_grid(T_START)
    e = energy_grid()["strom"]
    eta20 = 1 - (e * electricity_gwp_grid(2020) + rest_gwp(2020))
    better20 = m & np.isfinite(eta20) & (eta20 > np.where(np.isfinite(eff), eff, -np.inf)) & (eta20 > 0)
    landok = np.isfinite(eta20)
    return {
        "baeume_brutto_gtco2": gross,
        "baeume_netto_gtco2": net,
        "vl_gesamt_gtco2": vl_eng + vl_land,
        "vl_land_gtco2": vl_land,
        "vl_technisch_gtco2": vl_eng,
        "anteil_netto_an_vl": net / (vl_eng + vl_land),
        "bepflanzbar_kuehlt_gha": float(w[m & (eff > 0)].sum() / 1e13),
        "bepflanzbar_waermt_gha": float(w[m & ~(eff > 0)].sum() / 1e13),
        "dac_2020_besser_anteil": float(w[better20].sum() / w[m].sum()),
        "dac_2020_netto_emittierend_land": float(np.mean(eta20[landok] < 0)),
        "orte": {p.name: {"art": place_species(p), "baum_2025": tree_eta_at(p, T_START),  # key: start year
                          "dac_2020": dac_eta_at(p, T_START, 2020), "umstieg": crossover_year(p)} for p in PLACES},
        "gt_pro_jahr_baeume_gha": float(cascade()[-1]["area_gha"] / (gross / 125.0)),
    }


def clouds() -> dict:
    """Cloud brightening against the albedo per full-grown tree [W] at the sites, and the
    area-weighted global share (nbs.cloud_grid; Duveiller et al. 2021, Cerasoli et al. 2021)."""
    import numpy as np

    from nbs.animations import SITES, _STAND_AREA_M2, site_cell, typical_alpha_q_product, typical_cloud_product
    from nbs.landscape import plantable_area_m2

    alb, cld = typical_alpha_q_product(), typical_cloud_product()
    out = {"orte": {}}
    for s in SITES:
        c = site_cell(s)
        a, w = -alb[c] * _STAND_AREA_M2, -cld[c] * _STAND_AREA_M2
        out["orte"][s.name] = {"albedo_w": round(float(a), 1), "wolken_w": round(float(w), 1),
                               "netto_w": round(float(a + w), 1), "anteil": round(float(-w / a), 3)}
    area = plantable_area_m2()
    ok = np.isfinite(alb) & (area > 0)
    out["anteil_global"] = round(float(np.average(cld[ok], weights=area[ok]) / -np.average(alb[ok], weights=area[ok])), 3)
    return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    facts = {
        "klima": climate(),
        "orte": sites(),
        "licht_ueberwiegt_bis": tree_energy(),
        "a_co2": a_co2(),
        "kaskade": cascade_facts(),
        "umkehr": reverse(),
        "karten": maps(),
        "hasler": hasler(),
        "boreal_referenz": boreal_reference(),
        "baeume": trees(),
        "literatur": literature(),
        "dac": dac_facts(),
        "vergleich": vergleich_facts(),
        "wolken": clouds(),
    }
    args.out.write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(facts, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
