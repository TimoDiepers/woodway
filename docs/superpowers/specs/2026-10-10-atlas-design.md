# Atlas: the model's results as an interactive map

Date: 2026-10-10 · Status: approved in conversation, awaiting spec review

## Purpose

A web map that shows all of the talk's per-place data and results in one place, for the same two audiences as the deck: the public (link after the talk) and the examiners (nothing a peer would call wrong). It replaces the placeholder content of the woodway app (`~/Documents/Coding/woodway`) with this repository's model output.

Decisions made in conversation:

- **Atlas, not versus.** Layers a visitor picks, plus a time slider; no "tree or DAC wins here" comparison. Trees and DAC do not compete for land in the storyline, and the forest type of a cell is given by the data (Hasler et al. 2024), not chosen.
- **Lives in this repo** as `atlas/`, next to `deck/`. The woodway repo stays as it is; code is copied, not moved.
- **English and German**, English by default, switchable.
- **Native 0.5° grid**, the model's own resolution. No H3 resampling.
- **Stack as woodway:** Vite, React 18, TypeScript, Tailwind, MapLibre GL v5 (react-map-gl), Zustand, Radix primitives, Recharts, Vitest.

This spec covers sub-project 1, the atlas. Sub-project 2, an optional React version of the deck that uses the atlas components as slides, gets its own spec after the atlas ships; this spec only requires that the atlas components can be embedded.

## Content

### Layers

One layer at a time, picked from a grouped list. Each layer has a legend with unit, a source line and, where it has one, a time axis.

| Group | Layer | Values | Time |
|---|---|---|---|
| Trees | Typical forest type | Hasler et al. 2024 categories | — |
| | Reforestable area | share of the cell's land [%], Walker et al. 2022 | — |
| | Sunlight at the ground | W/m², Duveiller et al. 2018 | — |
| | Albedo contrast forest vs. open land | percentage points | — |
| | Extra absorbed light per tree | W | — |
| | Temperature effect of one tree | ΔT [10⁻¹⁵ K], cooling and warming on one diverging scale | year 2026–2150 |
| | Net share | ΔT with albedo ÷ ΔT from CO₂ alone [%] | year |
| DAC | Electricity per t CO₂ | MWh/t, heat pump; "too cold for sorbent DAC" as its own grey | — |
| | DAC net share | share of a removed tonne left after the plant's own emissions [%] | year 2026–2100 |
| | DAC build-out | capacity per cell from the optimisation [Mt/a] | year 2026–2100 |

Palettes and units are the deck's (`nbs.map_fields.SCALES`, `CATEGORIES`), so a map in the atlas and on a slide read the same. Cells without the quantity are drawn as grey land with a labelled reason ("no room for trees", "too cold for sorbent DAC"), never as a low value.

All trees follow the talk's one rule: typical forest of the cell, planted in `T_START` (2026), SSP2-4.5.

### Cell panel

Click or tap a cell (or pick one of the three example sites, Aachen (DE), Joensuu (FI), Marabá (BR), or search a place):

- forest type, reforestable area, number of trees;
- curves over time for one tree: carbon store m(t), forcing φ_CO₂ and φ_α, temperature effect ΔT(t), with the slider year marked;
- the year from which the tree cools, if it does by 2150;
- DAC at that place: electricity per tonne, net share over time, build-out if the optimisation puts capacity there.

### Global strip

Below the map, tied to the same slider year: the planting paths at the Bonn Challenge pace, the remaining warming above 1.5 °C (Very Low), and the worldwide DAC capacity, from the data behind the deck's chapter 3 and 4 charts (`deck/chart_data/zeitpfade.json`, `dacfilm.json`).

### Not included

The versus view, a species picker, H3 hexagons, 3D extrusion, and any value that does not come from the model. The "illustrative data" marker goes, replaced by source lines.

## Architecture

```
nbs (Python)                         atlas/ (Vite + React + TS)
atlas/export_atlas.py  ── writes ──▶ atlas/public/data/
                                       meta.json    grid, category codes, scales, sources, sites, type curves,
                                                    LCA base years, global paths
                                       fields.bin   360×720 fields, Float32 or Uint8, offsets listed in meta.json
                                       dac.bin      DAC net share at the LCA base years, build-out per year
```

### Exporter

`atlas/export_atlas.py` calls existing `nbs` functions only and writes the files above. Fields are stored on the full 360×720 grid with NaN outside; gzip removes most of the cost of the empty cells (target: under 6 MB gzipped for all data).

Exactness, so the browser reproduces the model rather than approximating it:

- **Tree ΔT per year.** For the typical forest type k of a cell, ΔT(t) = a_cell · c_k(t) + b_cell · s_k(t), where a_cell = `co2_factor_grid(k)`, b_cell = `_product_no_nan(k)`, and c_k, s_k are the full time series that `nbs.dac_compare._unit_curves_planted` computes for `T_START` and today reduces to their last value. The exporter writes the 18 type curves and the two per-cell factors; the browser evaluates any year exactly. Carbon store and forcing curves come from the same `run_single_tree` call per type.
- **DAC net share per year.** `efficiency_grid(year)` is linear in the electricity GWP, which `nbs.dac._interp` interpolates linearly between the LCA base years. The exporter writes the grid at each base year; linear interpolation in the browser is then exact.
- **DAC build-out.** The capacity per country and year of the optimisation behind the DAC film, spread over the same cells as in `scripts/build_dacfilm_data.py`.

### Frontend

```
atlas/src/
  data/     load and decode meta.json + .bin into typed arrays
  model/    pure functions: deltaT(cell, year), netShare(cell, year), dacNet(cell, year), dacBuild(cell, year)
  map/      layer → 720×360 canvas → MapLibre image source; cell lookup from lon/lat; borders
  ui/       header, layer picker, legend, time slider with playback, cell panel (Recharts),
            global strip, search, example sites, EN/DE switch, theme, mobile drawer
  i18n/     en.ts, de.ts: one flat dictionary per language, same keys
```

Taken over from woodway and adapted: map view and projection toggle (globe/flat), basemap and borders, time slider, mobile drawer, theme, location search, panel layout. Dropped: versus bar, option picker, H3 data and paint logic, extrusion.

The map repaints the canvas when layer or year changes; while scrubbing it repaints once per animation frame. Hover shows the cell value; click opens the cell panel.

**Embeddable from the start:** the map, legend, slider and cell panel take their state as props (layer, year, selected cell) with the store as one possible owner, so the React deck can drive them per slide without the header and chrome.

### Build and deploy

`npm run build` in `atlas/` gives `atlas/dist`. The Pages workflow builds the deck and the atlas and publishes the atlas under `/atlas/` of the same site. The README links to it.

### Errors

If a data file fails to load, the app says so in place of the map, with the file name. No partial colouring.

## Testing

- **Python, `tests/test_atlas_export.py`:** the exported files reproduce the model.
  - ΔT 2100 and net share at Aachen, Joensuu and Marabá match `deck/chart_data/fakten.json`.
  - The cooling area summed from the exported fields is 0.39 Gha.
  - The DAC median net share in 2026 is 46 %.
  - For a sample of cells and years, a·c_k(t) + b·s_k(t) equals the direct model value.
- **Frontend, Vitest:**
  - `model/` functions against reference values the exporter writes for a few cells.
  - Colour scales map domain ends and midpoints to the deck's stops.
  - `en.ts` and `de.ts` have the same keys, none empty.
- **In the browser:** desktop and phone, every layer once, slider and playback, cell panel, language switch; no console errors; load time measured on a throttled connection.

## Open for the React deck spec (sub-project 2)

- How the React deck reuses atlas code (Vite alias or a shared package).
- Which slides become live atlas views.
- How the deck's existing slides are carried over.
