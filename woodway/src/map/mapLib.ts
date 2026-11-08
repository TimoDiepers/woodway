/** MapLibre, requested as soon as this module is imported (at app start), so its chunk loads alongside the cell
 *  data instead of after it; react-map-gl takes the promise as its mapLib. */
export const mapLib = import("maplibre-gl");

/** The world's shape, asked for at app start with the app's own code: when MapLibre's worker asks for the same files
 *  a moment later, the browser has them (or has them coming). They are what the map shows first. */
if (typeof window !== "undefined" && typeof fetch === "function" && !import.meta.env?.VITEST)
  for (const u of ["ocean.geojson", "borders.geojson"]) fetch(u, { priority: "low" } as RequestInit).catch(() => {});   // after the map library and meta.json
