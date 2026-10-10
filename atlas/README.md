# Atlas

The talk's model, cell by cell: forest type, albedo, the temperature effect of one tree, DAC electricity, net share and build-out, 2026–2100, in English and German.

Place search asks OpenStreetMap's Nominatim, and only when Enter is pressed; nothing else leaves the page.

    uv run python atlas/export_atlas.py   # model → public/data (run after a model change)
    cd atlas && npm install
    npm run dev                           # http://localhost:5173
    npm test
    npm run build                         # → dist/, deployed under /atlas/ with the deck

Data: `public/data/meta.json` (grid, type curves, palettes, global paths) and `fields.bin` (360×720 fields; the browser loads `fields.bin.gz`, written alongside with gzip -9 and mtime 0, and falls back to `fields.bin` where `DecompressionStream` is missing). The browser computes each year exactly: ΔT = a·ΔT_CO₂,type(t) + b·ΔT_albedo,type(t), DAC net share linear between the LCA base years.

## Talk

`talk.html` is the React talk: the HTML deck in an iframe, with five live atlas slides inserted at their places. Live at https://timodiepers.github.io/dissvortrag/atlas/talk.html.

    uv run python deck/build.py   # the deck must be built first (dev serves it under /deck/)
    cd atlas && node scripts/thumbs.mjs   # stills of every slide for the overview (M), needs Chrome
    npm run dev                   # http://localhost:5173/talk.html

The order of deck slides and atlas slides is in `src/talk/sequence.ts`, the atlas slides themselves in `src/talk/slides.ts`. Keys: → / Space / PageDown / Enter next, ← / PageUp / Backspace back, Home first, B jump to the backup, M slide overview, N notes, F fullscreen. In production the deck is loaded from `../index.html?host`, in development from `/deck/index.html?host`.
