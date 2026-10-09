import { useEffect, useState } from "react";
import { Layer, Source } from "react-map-gl/maplibre";
import type { FeatureCollection } from "geojson";

export default function Borders({ dark }: { dark: boolean }) {
  const [data, setData] = useState<FeatureCollection | null>(null);
  useEffect(() => { fetch("borders.geojson").then((r) => r.json()).then(setData).catch(() => setData(null)); }, []);
  if (!data) return null;
  return (
    <Source id="borders" type="geojson" data={data}>
      <Layer id="borders-line" type="line" paint={{ "line-color": dark ? "#9aa39d" : "#5d665f", "line-width": 0.6, "line-opacity": 0.6 }} />
    </Source>
  );
}
