"""Write the data behind every chart in the main part of dissvortrag.pptx.

One CSV per chart, in ``docs/slides/chart_data/``. The file name starts with
the slide number the chart sits on, so ``33b_vorrat_kohorten.csv`` is the
second chart on slide 33. ``scripts/build_native_charts.py`` reads these
files and puts them into the deck as native PowerPoint charts.

Where the numbers come from:

* Slides 12, 31-35, 38, 40 and 42 are computed here with ``nbs``, under the
  same conditions as ``docs/slides/generate_result_figures.py`` and the
  notebooks that drew the old PNGs (SSP2-4.5, ``ModelConfig()``, 2025-2150).
* Slides 15/16 use ``nbs.albedo_grid.seasonal_profile`` as notebook 03 does.
* Slide 29 (``g_T``) and slide 11 (the three time scales) never had a data
  source -- the old PNGs were drawn from hand-picked shapes. They are
  rebuilt here as the same analytical curves, fitted to the old figures, and
  are marked ``illustrativ`` in their file names. Their numbers are shapes,
  not results.

Run:

    uv run python scripts/export_chart_data.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from nbs.config import ModelConfig
from nbs.constants import YEARS
from nbs.forcing import co2_flux_kg_per_yr
from nbs.metrics import t_star
from nbs.pipeline import run_single_tree
from nbs.response import convolve_response, green_temperature
from nbs.species import REFERENCE_SITES, SPECIES, get_species

OUT = Path(__file__).resolve().parent.parent / "docs" / "slides" / "chart_data"
SCENARIO = "ssp245"
CONFIG = ModelConfig()
UNDISTURBED = ModelConfig(**{**CONFIG.__dict__, "disturbance": "off"})
BOREAL = "enf_boreal"
MONTHS_DE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def write(name: str, df: pd.DataFrame) -> None:
    path = OUT / f"{name}.csv"
    df.to_csv(path, index=False, float_format="%.6g")
    print(f"  {path.relative_to(OUT.parent.parent.parent)}  ({len(df)} Zeilen)")


# -- slide 11: three time scales of carbon uptake (illustrative) -------------


def slide_11() -> None:
    hours = np.linspace(0.0, 24.0, 97)
    day = (hours >= 6.0) & (hours <= 20.0)
    flux = np.full_like(hours, 4.4)
    flux[day] = 4.4 - 23.0 * np.sin(np.pi * (hours[day] - 6.0) / 14.0)
    write("11a_tagesgang_co2_fluss_illustrativ", pd.DataFrame(
        {"stunde": hours, "netto_co2_fluss_umol_m2_s": flux}))

    months = np.arange(12)
    monthly = -15.5 + 65.5 * np.cos(2.0 * np.pi * (months - 0.3) / 12.0)
    write("11b_jahresgang_co2_bilanz_illustrativ", pd.DataFrame(
        {"monat": MONTHS_DE, "netto_co2_kg_je_baum_und_monat": monthly}))

    age = np.arange(0, 101)
    m_max, k, p = 2475.0, np.log(3.0) / 22.0, 3.0
    stock = m_max * (1.0 - np.exp(-k * age)) ** p
    rate = m_max * p * k * np.exp(-k * age) * (1.0 - np.exp(-k * age)) ** (p - 1.0)
    reversal = np.where(age >= 70, 1680.0 - (1680.0 - 870.0) * (age - 70) / 30.0, np.nan)
    write("11c_bestandesalter_speicher_illustrativ", pd.DataFrame({
        "alter_a": age,
        "gespeichert_kg_co2_je_baum": stock,
        "stoerung_kg_co2_je_baum": reversal,
        "jaehrliche_aufnahme_kg_co2_je_baum_a": rate,
    }))


# -- slide 12: what the loss term takes from the stock -----------------------


def slide_12() -> None:
    from nbs.tree import biomass_closed, simulate_deterministic

    from nbs.animations import SITES
    from nbs.storyline_figures import _site_species

    sp = _site_species(SITES[0])  # the running example: mixed forest at Aachen
    t_age = YEARS - YEARS[0]
    t_warm = 1.0 * t_age / 100.0
    write("12_vorrat_fichte_verlustterm", pd.DataFrame({
        "jahr": YEARS,
        "nur_wachstum_kgC": biomass_closed(t_age, sp),
        "mit_stoerung_dTw_0_kgC": simulate_deterministic(sp, np.zeros_like(t_warm), dt=1 / 12).stock_kgC,
        "mit_stoerung_dTw_1K_linear_kgC": simulate_deterministic(sp, t_warm, dt=1 / 12).stock_kgC,
    }))


# -- slides 15/16: the albedo effect is a spring event -----------------------


def slides_15_16() -> None:
    from nbs.albedo_grid import seasonal_profile

    prof = {lat: seasonal_profile(BOREAL, lat) for lat in (45.0, 60.0)}
    panels = [
        ("a_delta_albedo", "delta_alpha_monthly", "delta_alpha"),
        ("b_einstrahlung", "q_sw_monthly", "q_kurz_W_m2"),
        ("c_albedo_antrieb", "product_monthly", "delta_alpha_mal_q_W_m2"),
    ]
    for slide in (15, 16):
        for suffix, key, col in panels:
            df = pd.DataFrame({"monat": MONTHS_DE})
            for lat in (45.0, 60.0):
                df[f"{col}_{lat:.0f}N"] = np.asarray(prof[lat][key], dtype=float)
            if key == "product_monthly":
                for lat in (45.0, 60.0):
                    df[f"jahresmittel_{lat:.0f}N"] = float(np.mean(prof[lat][key]))
            write(f"{slide}{suffix}_fichte_saison", df)


# -- slide 29: temperature response to an energy pulse (illustrative) --------


def slide_29() -> None:
    t = np.arange(0, 301)
    fast = 0.58 * np.exp(-t / 4.0)
    slow = 0.42 * np.exp(-t / 252.0)
    write("29_temperaturantwort_gT_illustrativ", pd.DataFrame({
        "jahre_nach_stoss": t,
        "schnell_deckschicht": fast,
        "langsam_tiefsee": slow,
        "gT_summe": fast + slow,
    }))


# -- slides 31/32: one tree at one place -------------------------------------


def slides_31_32() -> None:
    r = run_single_tree(BOREAL, REFERENCE_SITES[BOREAL], SCENARIO, config=CONFIG)
    y = r.years
    write("31a_vorrat_fichte", pd.DataFrame({"jahr": y, "vorrat_kgC_je_baum": r.trajectory.stock_kgC}))
    write("31b_co2_fluss_fichte", pd.DataFrame(
        {"jahr": y, "co2_fluss_kg_je_a": co2_flux_kg_per_yr(r.trajectory.net_uptake_kgC_yr)}))
    write("31c_bedeckungsgrad_fichte", pd.DataFrame({"jahr": y, "bedeckungsgrad": r.trajectory.closure}))

    g = green_temperature(SCENARIO)
    write("32a_antrieb_fichte", pd.DataFrame({
        "jahr": y,
        "phi_co2_1e-15_W_m2": r.phi_co2 * 1e15,
        "phi_albedo_1e-15_W_m2": r.phi_albedo * 1e15,
        "phi_netto_1e-15_W_m2": r.phi_total * 1e15,
    }))
    write("32b_temperatur_fichte", pd.DataFrame({
        "jahr": y,
        "dT_co2_1e-15_K": convolve_response(g, r.phi_co2) * 1e15,
        "dT_albedo_1e-15_K": convolve_response(g, r.phi_albedo) * 1e15,
        "dT_netto_1e-15_K": r.delta_t * 1e15,
    }))
    print(f"    t*_phi = {t_star(r.phi_total, y):.0f}, t*_dT = {t_star(r.delta_t, y):.0f}")


# -- slide 33: planting year and disturbance risk ----------------------------


def slide_33() -> None:
    from nbs.planting_time import DEFAULT_AGE_YR, PLANT_YEARS, cohort, cohort_table, hazard_curve

    lat = REFERENCE_SITES[BOREAL]
    hazard = hazard_curve(BOREAL, SCENARIO) * 100.0
    table = cohort_table(BOREAL, lat, SCENARIO, PLANT_YEARS, DEFAULT_AGE_YR, CONFIG)

    df = pd.DataFrame({"jahr": YEARS, "stoerungswahrscheinlichkeit_pct_a": hazard})
    for py in PLANT_YEARS:
        sel = (YEARS >= py) & (YEARS <= py + DEFAULT_AGE_YR)
        df[f"fenster_{py}_pct_a"] = np.where(sel, hazard, np.nan)
    write("33a_stoerungsrisiko_pflanzjahr", df)

    df = pd.DataFrame({"jahr": YEARS})
    for py in PLANT_YEARS:
        df[f"mit_stoerung_{py}_kgC"] = cohort(BOREAL, py, lat, SCENARIO, CONFIG).trajectory.stock_kgC
    for py in PLANT_YEARS:
        df[f"ohne_stoerung_{py}_kgC"] = cohort(BOREAL, py, lat, SCENARIO, UNDISTURBED).trajectory.stock_kgC
    write("33b_vorrat_kohorten", df)

    write("33c_risiko_und_ausgleichsjahr", pd.DataFrame({
        "pflanzjahr": list(PLANT_YEARS),
        f"p_stoerung_in_{DEFAULT_AGE_YR}a_pct": [table[py]["p_stoerung"] * 100.0 for py in PLANT_YEARS],
        "vorratsverlust_pct": [table[py]["verlust_anteil"] * 100.0 for py in PLANT_YEARS],
        "risikofaktor": [table[py]["risikofaktor"] for py in PLANT_YEARS],
        "ausgleichsjahr_t_star": [table[py]["t_star"] for py in PLANT_YEARS],
    }))


# -- slides 34/35: five species ----------------------------------------------


def slides_34_35() -> None:
    df34 = pd.DataFrame({"jahr": YEARS})
    df35 = pd.DataFrame({"jahr": YEARS})
    for key, lat in REFERENCE_SITES.items():
        with_dist = run_single_tree(key, lat, SCENARIO, config=CONFIG)
        without = run_single_tree(key, lat, SCENARIO, config=UNDISTURBED)
        df34[f"{key}_mit_stoerung_kgC"] = with_dist.trajectory.stock_kgC
        df34[f"{key}_ohne_stoerung_kgC"] = without.trajectory.stock_kgC
        df34[f"{key}_m_max_kgC"] = get_species(key).m_max_kgC
        df35[f"{key}_dT_1e-15_K"] = with_dist.delta_t * 1e15
    write("34_wachstumskurven_arten", df34)
    write("35_temperatur_arten", df35)


# -- slide 38: the correction cascade ----------------------------------------


def slide_38() -> None:
    from nbs.potential import cascade

    steps = cascade(SCENARIO)
    write("38_kaskade_potenzial", pd.DataFrame({
        "stufe": [s["name_de"] for s in steps],
        "kohlenstoff_GtC": [s["carbon_gtc"] for s in steps],
        "flaeche_Gha": [s["area_gha"] for s in steps],
        "art": ["Literatur" if s["area_gha"] is None else "Modell" for s in steps],
    }))


# -- slide 40: area per recommended species ----------------------------------


def slide_40() -> None:
    from nbs.recommend import summary

    from nbs.map_plots import TYPE_NAMES

    stats = summary(2100, SCENARIO)
    rows = []
    for t, name in TYPE_NAMES.items():
        ks = [k for k in SPECIES if k.startswith(t + "_")]
        rows.append({"art": name, "art_key": t,
                     "empfohlen_Gha": sum(stats[k]["flaeche_gha"] for k in ks),
                     "breitenband_Gha": sum(stats[k]["flaeche_zugewiesen_gha"] for k in ks)})
    write("40_flaeche_je_art", pd.DataFrame(rows).sort_values("empfohlen_Gha", ascending=False))


# -- slide 42: the reverse calculation ---------------------------------------


def slide_42() -> None:
    from nbs.landscape import plantable_area_m2
    from nbs.potential import reverse_1p5

    r = reverse_1p5(SCENARIO)
    write("42_umkehrrechnung_flaeche", pd.DataFrame({
        "groesse": ["bepflanzbare Fläche (Modell)", "nötig, nur Kohlenstoff", "nötig, volles Modell"],
        "flaeche_Gha": [
            float(plantable_area_m2().sum()) / 1e13,
            r["nur_kohlenstoff"]["area_gha"],
            r["mit_albedo_und_stoerung"]["area_gha"],
        ],
        "eisfreie_landflaeche_Gha": 13.0,
    }))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for fn in (slide_11, slide_12, slides_15_16, slide_29, slides_31_32, slide_33,
               slides_34_35, slide_38, slide_40, slide_42):
        print(fn.__name__)
        fn()


if __name__ == "__main__":
    main()
