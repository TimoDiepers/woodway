import { useEffect } from "react";
import { Layer, Source } from "react-map-gl/maplibre";
import { FADE, useReady } from "./useReady";

/** Place names over the map (Natural Earth, woodway/scripts/labels.py), fetched only once they are switched on:
 *  countries from their own zoom (MIN_LABEL), towns from theirs (MIN_ZOOM); MapLibre places them by rank and
 *  leaves out what would collide. Glyphs: Noto Sans, served from public/glyphs. MapLibre fetches and parses the file
 *  in its worker; the names fade in once they and their glyphs are drawn, never letter set by letter set. */
export default function Labels({ lang, dark, onReady }: { lang: "de" | "en"; dark: boolean; onReady?: () => void }) {
  const on = useReady("labels"), o = (v: number) => (on ? v : 0);
  useEffect(() => { if (on) onReady?.(); }, [on, onReady]);
  // sharp text from MapLibre's distance-field glyphs: no halo blur, solid colours (a transparent name reads soft);
  // the countries in a lighter ink of their own, not the town ink at reduced opacity
  const ink = dark ? "#e6e2d6" : "#1b2420", inkCountry = dark ? "#b4b8b0" : "#5d665f", halo = dark ? "#14181a" : "#f6f1e6";
  // upright and facing the viewer, also towards the globe's edge
  const flat = { "text-pitch-alignment": "viewport", "text-rotation-alignment": "viewport" } as const;
  const z = (a: number, b: number, c: number) => ["interpolate", ["linear"], ["zoom"], 1.5, a, 4, b, 7, c] as unknown as number;
  return (
    <Source id="labels" type="geojson" data="labels.geojson">
      <Layer id="labels-dot" type="circle" filter={["all", ["==", ["get", "k"], "p"], [">=", ["zoom"], ["get", "z"]]]}
        paint={{ "circle-radius": ["case", ["==", ["get", "cap"], 1], 3, 2.2], "circle-color": ink, "circle-stroke-color": halo, "circle-stroke-width": 1.2,
                 "circle-opacity": o(1), "circle-stroke-opacity": o(1), "circle-opacity-transition": FADE, "circle-stroke-opacity-transition": FADE }} />
      <Layer id="labels-place" type="symbol" filter={["all", ["==", ["get", "k"], "p"], [">=", ["zoom"], ["get", "z"]]]}
        layout={{ "text-field": ["get", lang], "text-font": ["Noto Sans Regular"], "text-size": z(11.5, 12.5, 14), "text-anchor": "top", ...flat,
                  "text-offset": [0, 0.45], "text-max-width": 8, "symbol-sort-key": ["get", "r"], "text-padding": 4 }}
        paint={{ "text-color": ink, "text-halo-color": halo, "text-halo-width": 1.5, "text-halo-blur": 0, "text-opacity": o(1), "text-opacity-transition": FADE }} />
      <Layer id="labels-country" type="symbol" filter={["all", ["==", ["get", "k"], "c"], [">=", ["zoom"], ["-", ["get", "z"], 0.6]]]}
        layout={{ "text-field": ["get", lang], "text-font": ["Noto Sans Medium"], "text-size": z(11.5, 13, 16), "text-transform": "uppercase", ...flat,
                  "text-letter-spacing": 0.12, "text-max-width": 7, "symbol-sort-key": ["get", "r"], "text-padding": 6 }}
        paint={{ "text-color": inkCountry, "text-opacity": o(1), "text-opacity-transition": FADE, "text-halo-color": halo, "text-halo-width": 1.5, "text-halo-blur": 0 }} />
    </Source>
  );
}
