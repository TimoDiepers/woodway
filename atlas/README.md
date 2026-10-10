# Atlas

The talk's model, cell by cell: forest type, albedo, the temperature effect of one tree, DAC electricity, net share and build-out, 2026–2100, in English and German.

    uv run python atlas/export_atlas.py   # model → public/data (run after a model change)
    cd atlas && npm install
    npm run dev                           # http://localhost:5173
    npm test
    npm run build                         # → dist/, deployed under /atlas/ with the deck

Data: `public/data/meta.json` (grid, type curves, palettes, global paths) and `fields.bin` (360×720 fields; the browser loads `fields.bin.gz`, written alongside with gzip -9 and mtime 0, and falls back to `fields.bin` where `DecompressionStream` is missing). The browser computes each year exactly: ΔT = a·ΔT_CO₂,type(t) + b·ΔT_albedo,type(t), DAC net share linear between the LCA base years.
