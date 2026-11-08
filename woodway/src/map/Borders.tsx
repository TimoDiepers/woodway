import { useEffect, useState } from "react";
import { Layer, Source } from "react-map-gl/maplibre";
import type { FeatureCollection } from "geojson";

const load = (url: string, set: (d: FeatureCollection | null) => void) =>
  fetch(url).then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.json(); }).then(set).catch(() => set(null));

/** Over the hexagons: the sea in the map's sea colour (Natural Earth 1:50m), so coastal cells end at the coast
 *  instead of reaching into it (every cell keeps its value, only its overhang goes); then the country borders and
 *  coastlines (1:50m), a paper-coloured casing under a dark line, so a line reads on deep green and on pale cells
 *  alike, both a little wider as the map zooms in. */
// they load after the map's own layers: beforeId keeps them under the hover and selection outlines
export default function Borders({ dark }: { dark: boolean }) {
  const [lines, setLines] = useState<FeatureCollection | null>(null);
  const [sea, setSea] = useState<FeatureCollection | null>(null);
  useEffect(() => { load("borders.geojson", setLines); load("ocean.geojson", setSea); }, []);
  const w = (a: number, b: number) => ["interpolate", ["linear"], ["zoom"], 1, a, 6, b] as unknown as number;
  return (
    <>
      {sea && (
        <Source id="ocean" type="geojson" data={sea}>
          {/* the sea colour of the base style (lib/mapStyle.ts) */}
          <Layer beforeId="hex-hover-casing" id="ocean-fill" type="fill" paint={{ "fill-color": dark ? "#20282b" : "#efe9dc", "fill-antialias": true }} />
        </Source>
      )}
      {lines && (
        <Source id="borders" type="geojson" data={lines}>
          <Layer beforeId="hex-hover-casing" id="borders-casing" type="line" layout={{ "line-join": "round", "line-cap": "round" }}
            paint={{ "line-color": dark ? "#14181a" : "#f6f1e6", "line-width": w(1.8, 3.2), "line-opacity": dark ? 0.45 : 0.55 }} />
          <Layer beforeId="hex-hover-casing" id="borders-line" type="line" layout={{ "line-join": "round", "line-cap": "round" }}
            paint={{ "line-color": dark ? "#d6dbd6" : "#2b332e", "line-width": w(0.6, 1.2), "line-opacity": 0.6 }} />
        </Source>
      )}
    </>
  );
}
