import type { StyleSpecification } from "maplibre-gl";

// Base style: background/sky/light only. The actual basemap imagery (OSM
// standard vs. satellite) is added as ordinary React-managed <Source>/<Layer>
// pairs in BasemapLayers instead of being baked in here — toggling between
// them is then just a layout.visibility flip on existing layers (instant, no
// map.setStyle() reload/flicker), the same declarative pattern HexLayer
// already uses rather than a second, imperative code path.
export const paperBasemap: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    {
      id: "bg",
      type: "background",
      paint: { "background-color": "#f2ede2" },
    },
  ],
  // Soft warm atmosphere instead of the globe cutting straight into the page
  // — a golden haze at the limb (dawn/dusk terminator, not sci-fi blue), and
  // the sky itself is the exact paper color so it blends outward seamlessly.
  sky: {
    "sky-color": "#f2ede2",
    "horizon-color": "#d6ccb6",
    "fog-color": "#d6ccb6",
    "sky-horizon-blend": 0.6,
    // Kept low on purpose: at our working pitch (55°) and zoom (~3.4), most
    // of the visible terrain reads as "near horizon" to the fog model, so
    // anything but a thin blend washes the whole scene into a haze instead
    // of staying a rim effect at the true silhouette.
    "horizon-fog-blend": 0.12,
    "fog-ground-blend": 0.1,
    "atmosphere-blend": [
      "interpolate",
      ["linear"],
      ["zoom"],
      0, 0.2,
      2, 0.1,
      4, 0.05,
      7, 0,
    ],
  },
  light: {
    anchor: "viewport",
    color: "#f2ede2",
    intensity: 0.15,
    position: [1.15, 210, 30],
  },
};

// Dark-mode counterpart — same structure, an inky ground instead of paper,
// a dim cool-ember horizon instead of a golden dawn haze so the globe's rim
// doesn't glow like daylight against a night sky, and a lower-intensity
// light so extruded hexes don't blow out white the way they would under the
// paper theme's brighter fixture.
export const paperBasemapDark: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    {
      id: "bg",
      type: "background",
      paint: { "background-color": "#14181a" },
    },
  ],
  sky: {
    "sky-color": "#14181a",
    "horizon-color": "#3a4447",
    "fog-color": "#3a4447",
    "sky-horizon-blend": 0.6,
    "horizon-fog-blend": 0.12,
    "fog-ground-blend": 0.1,
    "atmosphere-blend": [
      "interpolate",
      ["linear"],
      ["zoom"],
      0, 0.2,
      2, 0.1,
      4, 0.05,
      7, 0,
    ],
  },
  light: {
    anchor: "viewport",
    color: "#e7e0d0",
    intensity: 0.1,
    position: [1.15, 210, 30],
  },
};

// tile.openstreetmap.org's standard raster tiles, retuned toward the paper
// palette — see BasemapLayers for why this is a plain raster-paint tint
// (deliberate, richer slate-teal, same cool family as the UI accent) rather
// than the tile's native colors.
export const OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
export const OSM_ATTRIBUTION = "© OpenStreetMap contributors";
export const OSM_ATTRIBUTION_URL = "https://www.openstreetmap.org/copyright";

// Esri's World Imagery — free, no API key, the standard no-signup satellite
// basemap (also what Leaflet-providers lists as Esri.WorldImagery). Native
// colors kept as-is (no paper retint): satellite photography read as a tint
// job looks wrong in a way a stylized street map doesn't.
export const SATELLITE_TILE_URL =
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
export const SATELLITE_ATTRIBUTION = "© Esri, Maxar, Earthstar Geographics, and the GIS User Community";
export const SATELLITE_ATTRIBUTION_URL =
  "https://www.esri.com/en-us/legal/terms/full-master-agreement";

// Esri's companion reference layer — transparent tiles carrying just labels,
// place names, roads and boundaries, meant to be stacked on top of World
// Imagery (this is exactly the pairing Esri's own "Imagery Hybrid" basemap
// uses). Satellite photography alone has no city/place labels of its own;
// this is what gives it the same "you can read what you're looking at"
// experience the standard basemap already has.
export const SATELLITE_LABELS_TILE_URL =
  "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}";
