import { useEffect } from "react";
import { Layer, Source } from "react-map-gl/maplibre";
import { FADE, useReady } from "./useReady";

/**
 * The world's shape, the first thing the map shows, then what lies over the hexagons:
 *  1. the land: a land-coloured ground under everything, and the sea (Natural Earth 1:50m) over it in the sea
 *     colour. The sea arrives invisible (sea on sea) and the ground fades in under it: the continents appear.
 *     Over the hexagons the same sea trims coastal cells at the coast (every cell keeps its value).
 *  2. country borders and coastlines (1:50m), a paper-coloured casing under a dark line, fading in once loaded.
 * `onLand` reports when the land stands, so the hexagons fade in after it, never before. MapLibre fetches and
 * parses the files in its worker. They load after the map's own layers: beforeId keeps them in their place.
 */
export default function Borders({ dark, onLand, onBase }: { dark: boolean; onLand?: () => void; onBase?: () => void }) {
  const land = useReady("ocean"), lines = useReady("borders");
  useEffect(() => { if (land) onLand?.(); }, [land, onLand]);
  useEffect(() => { if (land && lines) onBase?.(); }, [land, lines, onBase]);
  const w = (a: number, b: number) => ["interpolate", ["linear"], ["zoom"], 1, a, 6, b] as unknown as number;
  const seaColour = dark ? "#20282b" : "#efe9dc", landColour = dark ? "#2e373a" : "#ddd6c7";   // lib/mapStyle.ts, meta.colors.land
  return (
    <>
      <Layer beforeId="atlas-layer" id="land-ground" type="background"
        paint={{ "background-color": landColour, "background-opacity": land ? 1 : 0, "background-opacity-transition": FADE }} />
      <Source id="ocean" type="geojson" data="ocean.geojson">
        <Layer beforeId="hex-hover-casing" id="ocean-fill" type="fill" paint={{ "fill-color": seaColour, "fill-antialias": true }} />
      </Source>
      <Source id="borders" type="geojson" data="borders.geojson">
        <Layer beforeId="hex-hover-casing" id="borders-casing" type="line" layout={{ "line-join": "round", "line-cap": "round" }}
          paint={{ "line-color": dark ? "#14181a" : "#f6f1e6", "line-width": w(1.8, 3.2), "line-opacity": lines ? (dark ? 0.45 : 0.55) : 0, "line-opacity-transition": FADE }} />
        <Layer beforeId="hex-hover-casing" id="borders-line" type="line" layout={{ "line-join": "round", "line-cap": "round" }}
          paint={{ "line-color": dark ? "#d6dbd6" : "#2b332e", "line-width": w(0.6, 1.2), "line-opacity": lines ? 0.6 : 0, "line-opacity-transition": FADE }} />
      </Source>
    </>
  );
}
