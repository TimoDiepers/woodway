# Ingenieure auf dem Holzweg?

**Woodway** (every result of the model, cell by cell): https://woodway.tidi.dev/

**Slides:** https://woodway.tidi.dev/slides/ (woodway is also live on the talk's last slide)

Until the domain is set up, the same site is at https://timodiepers.github.io/dissvortrag/ and https://timodiepers.github.io/dissvortrag/slides/.

Model and slides for a PhD defence talk: how much afforestation cools the climate once you follow the carbon past the tree, and how much direct air capture (DAC) has to do on top.

The talk widens the system boundary step by step. It starts with one tree, which takes up carbon and absorbs extra sunlight because its canopy is darker than the land it replaces. Next comes the carbon cycle, where ocean and land hand back part of the removed CO₂. Then the Earth's energy balance turns forcing into temperature. Finally the view grows to every reforestable 0.5° cell, and then to DAC as the second removal route. Everything is computed year by year, so the result is a temperature path to 2100 rather than one number.

## The chain

One tree, two channels, one convolution:

    m(t)  →  ṁ_CO₂ = −(44/12)·ṁ  →  Δm_CO₂ = g_C ∗ ṁ_CO₂  →  φ_CO₂ = ε_CO₂·Δm_CO₂
          →  f(t)                                          →  φ_α = τ_atm·ΔQ̇_Baum / A_Erde
                                                           →  ΔT = g_T ∗ (φ_CO₂ + φ_α)

FaIR (calibrated with fair-calibrate 1.4.1) supplies the impulse responses g_C and g_T. Area-wide numbers come from a direct FaIR run instead, with the removal as a negative emission and the albedo as a forcing, so filling sinks and the weaker effect per kg at higher CO₂ are part of the result. Evapotranspiration is not a term in φ: it does not cross the top of the atmosphere.

```python
from nbs.pipeline import run_single_tree
from nbs.metrics import t_star

r = run_single_tree("mf_gemaessigt", lat_deg=50.8, scenario="ssp245")   # temperate mixed forest, Aachen
print(t_star(r.delta_t, r.years))
```

## Layout

```
src/nbs/            the model
  tree.py, species.py, site_factor.py, forest_data.py   growth and forest type per cell
  forcing.py, response.py, fair_module.py              forcing, impulse responses, FaIR
  pipeline.py, metrics.py                              one tree at one place
  grid.py, albedo_grid.py, landscape.py, aggregate.py  the 0.5° grid
  potential.py, tree_paths.py, planting_time.py        area, planting paths over time
  dac*.py                                              DAC energy, life cycle, storage, optimisation
  *_figures.py, map_fields.py                          figures and map data for the deck
  legacy/                                              the earlier level 0–6 framework, kept with its tests
scripts/            fetch and prepare data, compute the deck's numbers and data
deck/               the HTML talk (see below)
atlas/              the interactive map of all results (see atlas/README.md)
data/               inputs (data/raw is not in git)
docs/methods/       method notes: forest types, FaIR, DAC model, literature
notebooks/          01 one tree, 03 the global layer
tests/
```

## Setup

Python 3.11+ and [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run python scripts/fetch_data.py duveiller_bph   # albedo rasters (Duveiller et al. 2018, CC-BY-4.0)
```

The other raw inputs (Walker, Hasler, Cook-Patton, CRU, Gidden, CMIP7) go to `data/raw/`. `scripts/prepare_*.py`, `scripts/fetch_*.py` and the method notes say where each comes from. Without the rasters, the affected functions fall back to latitude tables visibly and say so through `provenance()`.

The DAC life-cycle inputs (`data/dac/lca_vintages*.json`) come from premise databases in a separate Brightway environment (`scripts/build_premise_scenarios.py`, `scripts/dac_lca_precompute.py`). They are committed, so the model runs without Brightway.

## The deck

The talk is one HTML page, live at https://woodway.tidi.dev/slides/. Its sources are in `deck/src`, and one build puts it together:

```bash
uv run python deck/build.py      # -> deck/dist/index.html (plus data/ and vendor/)
cd deck/dist && python3 -m http.server 8765
```

```
deck/
  build.py            inlines src/ into one page, injects chart_data, copies assets, drops unused charts
  src/index.html      page shell: head, icons, script order
  src/css/deck.css    design tokens, layout, animation
  src/js/deck.js      navigation, charts (ECharts), presenter view, slide menu
  src/js/loader.js    loads chart data and ECharts in the background
  src/js/dacfilm.js   the animated DAC map
  src/slides/         one file per chapter, 07_backup.html after "Danke"
  chart_data/         JSON the build injects (tempsum, zeitpfade, dacfilm) or the model caches
  assets/data/        figure data: ec_charts.js, maps.js, cmip7.js
  assets/vendor/      ECharts, KaTeX, fonts (everything runs offline)
  export_charts.py    model figures -> assets/data (via mpl_to_echarts.py)
```

To change slide text or layout, edit `deck/src` and rebuild. If the model changes, refresh the data first and then rebuild:

| Data | Command |
|---|---|
| figures, maps, CMIP7 series | `uv run python deck/export_charts.py` (or `--only k6,b8`) |
| numbers quoted on slides | `uv run python scripts/export_slide_facts.py` → `deck/chart_data/fakten.json` |
| temperature per tree | `uv run python scripts/build_tempsum_data.py` |
| planting and DAC paths | `uv run python scripts/build_zeitpfade_data.py` |
| DAC optimisation, DAC film | `scripts/dac_optim_export.py`, then `scripts/build_dacfilm_data.py` |

Slide texts are typed in `deck/src/slides`, so check them against `fakten.json` after a model change. `tests/test_slide_numbers.py` recomputes the headline numbers.

Keys in the deck: ← → to move, P for the presenter view, N for notes, R to replay the animation, M for the slide menu, B for the backup, F for fullscreen, and a number followed by Enter to jump to that slide. Pushes to `main` that touch `deck/` build and deploy it to GitHub Pages (`.github/workflows/pages.yml`).

## Tests

```bash
uv run pytest -m "not slow"     # fast
uv run pytest                   # everything, including FaIR-backed runs
```
