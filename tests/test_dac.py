"""Tests for the DAC model (nbs.dac, nbs.dac_climate, nbs.dac_compare)."""

import numpy as np
import pytest

from nbs.dac import (
    SENDI_CLASSES,
    cop,
    dac_possible,
    efficiency_grid,
    electricity_gwp_grid,
    energy_grid,
    fit_heat_demand,
    lca_vintages,
)
from nbs.dac_climate import climate_grid, country_for_land, saturation_vapour_pressure_hpa
from nbs.grid import grid_lats, grid_lons


def _at(field, lat, lon):
    return float(field[np.argmin(abs(grid_lats() - lat)), np.argmin(abs(grid_lons() - lon))])


def test_magnus_formula_matches_tabulated_values():
    # WMO tables: 6.11 hPa at 0 deg C, 23.4 hPa at 20 deg C
    assert saturation_vapour_pressure_hpa(np.array(0.0)) == pytest.approx(6.112, abs=0.01)
    assert saturation_vapour_pressure_hpa(np.array(20.0)) == pytest.approx(23.37, abs=0.1)


def test_climate_is_plausible_at_known_places():
    c = climate_grid()
    assert 9 < _at(c["t_mean_c"], 50.78, 6.08) < 12  # Aachen
    assert 24 < _at(c["t_mean_c"], 24.7, 46.7) < 29  # Riyadh
    assert _at(c["rh_mean_pct"], 24.7, 46.7) < 40  # dry
    assert _at(c["rh_mean_pct"], -6.2, 106.8) > 70  # Jakarta, humid


def test_country_codes_where_expected():
    codes = country_for_land()
    assert codes[np.argmin(abs(grid_lats() - 50.78)), np.argmin(abs(grid_lons() - 6.08))] == "DE"
    assert codes[np.argmin(abs(grid_lats() - 60.0)), np.argmin(abs(grid_lons() - 10.0))] == "NO"


def test_cop_follows_sendi_and_rises_with_temperature():
    """Sendi et al. Eq. 29-31: 50 % of Carnot between ambient - 10 K and 120 deg C."""
    assert cop(np.array(20.0)) == pytest.approx(0.5 * 393.15 / (393.15 - 283.15), rel=1e-9)
    assert cop(np.array(30.0)) > cop(np.array(10.0))
    assert cop(np.array(-20.0)) == cop(np.array(1.0)), "held at 1 deg C below that"


def test_heat_demand_fit_reproduces_sendi_table_1():
    fit = fit_heat_demand()
    assert fit.max_abs_error_mwh < 0.05
    assert fit.a_rh > 0, "humid air costs more heat (water co-adsorption)"
    for key, value in SENDI_CLASSES.items():
        assert fit.class_model[key] == pytest.approx(value, abs=0.05)


def test_energy_is_in_a_plausible_range_and_higher_where_humid():
    e = energy_grid()["strom"]
    assert 1.0 < np.nanmin(e) and np.nanmax(e) < 2.2
    assert _at(e, -6.2, 106.8) > _at(e, 24.7, 46.7), "Jakarta (humid) above Riyadh (dry)"


def test_very_cold_cells_are_excluded():
    ok = dac_possible()
    c = climate_grid()
    assert not ok[c["t_coldest_month_c"] < -15.0].any()
    assert np.isnan(energy_grid()["strom"][~ok]).all()


def test_lca_file_covers_all_vintages_and_countries():
    data = lca_vintages()["jahre"]
    assert sorted(data) == ["2020", "2030", "2040", "2050", "2075", "2100"]
    land = np.isfinite(climate_grid()["t_mean_c"])
    codes = set(country_for_land()[land]) - {""}  # e.g. Antarctica has a code but no CRU climate
    for d in data.values():
        assert codes <= set(d["strom_kg_pro_kwh"])
        assert all(d["remind_region"][c] != "World" for c in d["ohne_eigenen_markt"]), "fallback to REMIND region"


def test_electricity_gets_cleaner_and_dac_efficiency_rises():
    g25, g50 = electricity_gwp_grid(2025), electricity_gwp_grid(2050)
    assert np.nanmedian(g50) < np.nanmedian(g25)
    e25, e50 = efficiency_grid(2025), efficiency_grid(2050)
    assert np.nanmedian(e50) > np.nanmedian(e25)
    assert np.nanmax(e50) < 1.0, "never more than the tonne removed"


def test_best_option_codes_are_consistent():
    from nbs.dac_compare import OPTIONS, best_option_grid, tree_efficiency_grid

    code = best_option_grid(2040)
    dac = efficiency_grid(2040)
    tree = tree_efficiency_grid(2040)
    dac_cells = code == OPTIONS.index("dac") + 1
    assert (dac[dac_cells] > 0).all()
    both = dac_cells & np.isfinite(tree)
    assert (dac[both] >= tree[both]).all()
    tree_cells = code >= 2
    assert (tree[tree_cells] > 0).all()


def test_vergleich_numbers_are_consistent():
    from nbs.vergleich_figures import CMIP7_REMOVAL, PLACES, crossover_year, place_cell, tree_potential_gtco2

    gross, net = tree_potential_gtco2()
    assert 0 < net < gross, "albedo only takes away"
    eng, land = CMIP7_REMOVAL["Very Low"]
    assert eng + land == pytest.approx(335.2, abs=0.5), "CMIP7 Very Low, summed 2024-2100 (slide 3)"
    for p in PLACES:
        place_cell(p)  # raises if no cell with trees and DAC nearby
    years = [crossover_year(p) for p in PLACES]
    # DAC overtakes the tree at most places by 2070; since tau_atm = 0.854 also in Manaus (2048), so no
    # place is required to stay with the tree any more
    assert all(y is None or 2020 <= y <= 2070 for y in years)
    assert sum(y is not None for y in years) >= 4
