# Woodway

The model of the PhD defence talk "Aufforstung als Klima-Technologie" (see the [main README](../README.md)), cell by cell, 2026–2100, in English and German. The layers follow the talk: one tree (forest type, sunlight, albedo change, clouds, absorbed radiation, temperature effect, net share; planted in 2026 or any fifth year up to 2061), all reforestable land (area, the effect of the whole cell), today's forest (cooling by further growth, an upper bound; felling where forest warms, the talk's thought experiment), a vegan world (forest on the freed land) and DAC (electricity, removal efficiency, build-out). The world strip adds it up and states what today's forests still take up. Live at https://woodway.tidi.dev/, with the talk's slides under https://woodway.tidi.dev/slides/ (linked from the app's tool column).

Place search asks OpenStreetMap's Nominatim, and only when Enter is pressed; nothing else leaves the page.

Country borders (Natural Earth 1:50m) sit over the hexagons with a light casing; place names (Natural Earth countries and populated places, German and English, each from its own zoom level) can be switched on under More. They come from `woodway/scripts/borders.py` and `woodway/scripts/labels.py` (the 19 MB places file is fetched to `data/raw/` on first run); their glyphs (Noto Sans, OFL) are served from `public/glyphs`.

    uv run python woodway/export_woodway.py   # model → public/data (run after a model change)
    cd woodway && npm install
    npm run dev                               # http://localhost:5173
    npm test
    npm run build                             # → dist/, published at the site root, the deck under slides/

Data: `public/data/meta.json` (grid, type curves, palettes, global paths) and the 360×720 fields, each as `fields/<name>.bin.gz` (gzip -9, mtime 0), with `fields.bin` holding all of them as the fallback where `DecompressionStream` is missing. The browser loads in this order: the world's shape (sea and lines, asked for at start), the fields of the layer on screen, the place names, then the other fields in the background; each part fades in once it stands (land, then the hexagons, then the names), and the legend, the world chart and the cell details show skeletons until their data is there. The browser computes each year exactly: ΔT = a·ΔT_CO₂,type(t) + b·ΔT_albedo,type(t), DAC net share linear between the LCA base years.

In the deck's last slide woodway runs in an iframe (`../?embed&lang=de&theme=light`): `?lang` and `?theme` set language and theme for that visit, and `?embed` hands the deck's paging keys back to it.

## The React talk (not published)

`talk.html` is an earlier React version of the talk: the HTML deck in an iframe with live map slides. It is no longer built for Pages; it still runs in development:

    uv run python deck/build.py   # the deck must be built first (dev serves it under /deck/)
    cd woodway && npm run dev     # http://localhost:5173/talk.html

The order of deck slides and map slides is in `src/talk/sequence.ts`, the map slides themselves in `src/talk/slides.ts`.
