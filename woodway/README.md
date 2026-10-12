# Woodway

The model of the PhD defence talk "Aufforstung als Klima-Technologie" (see the [main README](../README.md)), cell by cell: forest type, albedo, the temperature effect of one tree, DAC electricity, net share and build-out, 2026–2100, in English and German. Live at https://woodway.tidi.dev/, with the talk's slides under https://woodway.tidi.dev/slides/ (linked from the app's tool column).

Place search asks OpenStreetMap's Nominatim, and only when Enter is pressed; nothing else leaves the page.

    uv run python woodway/export_woodway.py   # model → public/data (run after a model change)
    cd woodway && npm install
    npm run dev                               # http://localhost:5173
    npm test
    npm run build                             # → dist/, published at the site root, the deck under slides/

Data: `public/data/meta.json` (grid, type curves, palettes, global paths) and `fields.bin` (360×720 fields; the browser loads `fields.bin.gz`, written alongside with gzip -9 and mtime 0, and falls back to `fields.bin` where `DecompressionStream` is missing). The browser computes each year exactly: ΔT = a·ΔT_CO₂,type(t) + b·ΔT_albedo,type(t), DAC net share linear between the LCA base years.

In the deck's last slide woodway runs in an iframe (`../?embed&lang=de&theme=light`): `?lang` and `?theme` set language and theme for that visit, and `?embed` hands the deck's paging keys back to it.

## The React talk (not published)

`talk.html` is an earlier React version of the talk: the HTML deck in an iframe with live map slides. It is no longer built for Pages; it still runs in development:

    uv run python deck/build.py   # the deck must be built first (dev serves it under /deck/)
    cd woodway && npm run dev     # http://localhost:5173/talk.html

The order of deck slides and map slides is in `src/talk/sequence.ts`, the map slides themselves in `src/talk/slides.ts`.
