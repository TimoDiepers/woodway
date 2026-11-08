import { useEffect, useState } from "react";
import { Layer, Source } from "react-map-gl/maplibre";
import type { FeatureCollection } from "geojson";

/** Place names over the map (Natural Earth, woodway/scripts/labels.py), fetched only once they are switched on:
 *  countries from their own zoom (MIN_LABEL), towns from theirs (MIN_ZOOM); MapLibre places them by rank and
 *  leaves out what would collide. Glyphs: Noto Sans, served from public/glyphs. */
export default function Labels({ lang, dark }: { lang: "de" | "en"; dark: boolean }) {
  const [data, setData] = useState<FeatureCollection | null>(null);
  useEffect(() => { fetch("labels.geojson").then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.json(); }).then(setData).catch(() => setData(null)); }, []);
  if (!data) return null;
  const ink = dark ? "#e6e2d6" : "#1b2420", halo = dark ? "rgba(20, 24, 26, .85)" : "rgba(246, 241, 230, .9)";
  const z = (a: number, b: number, c: number) => ["interpolate", ["linear"], ["zoom"], 1.5, a, 4, b, 7, c] as unknown as number;
  return (
    <Source id="labels" type="geojson" data={data}>
      <Layer id="labels-dot" type="circle" filter={["all", ["==", ["get", "k"], "p"], [">=", ["zoom"], ["get", "z"]]]}
        paint={{ "circle-radius": ["case", ["==", ["get", "cap"], 1], 3, 2.2], "circle-color": ink, "circle-stroke-color": halo, "circle-stroke-width": 1.2 }} />
      <Layer id="labels-place" type="symbol" filter={["all", ["==", ["get", "k"], "p"], [">=", ["zoom"], ["get", "z"]]]}
        layout={{ "text-field": ["get", lang], "text-font": ["Noto Sans Regular"], "text-size": z(11, 12.5, 14), "text-anchor": "top",
                  "text-offset": [0, 0.45], "text-max-width": 8, "symbol-sort-key": ["get", "r"], "text-padding": 4 }}
        paint={{ "text-color": ink, "text-halo-color": halo, "text-halo-width": 1.4, "text-halo-blur": 0.4 }} />
      <Layer id="labels-country" type="symbol" filter={["all", ["==", ["get", "k"], "c"], [">=", ["zoom"], ["-", ["get", "z"], 0.6]]]}
        layout={{ "text-field": ["get", lang], "text-font": ["Noto Sans Medium"], "text-size": z(10.5, 13, 16), "text-transform": "uppercase",
                  "text-letter-spacing": 0.12, "text-max-width": 7, "symbol-sort-key": ["get", "r"], "text-padding": 6 }}
        paint={{ "text-color": ink, "text-opacity": 0.62, "text-halo-color": halo, "text-halo-width": 1.6, "text-halo-blur": 0.4 }} />
    </Source>
  );
}
