import { useEffect, useState } from "react";
import { useMap } from "react-map-gl/maplibre";

/** True once the map has loaded source *id* and drawn it (the next "idle": glyphs of labels included), so a layer
 *  can fade in then instead of popping in piece by piece over a slow connection. */
export function useReady(id: string): boolean {
  const { current } = useMap();
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const map = current?.getMap();
    if (!map || ready) return;
    let done = false;
    const check = () => {
      if (done || !map.getSource(id) || !map.isSourceLoaded(id)) return;
      done = true;
      map.once("idle", () => setReady(true));
    };
    map.on("sourcedata", check);
    check();
    return () => { done = true; map.off("sourcedata", check); };
  }, [current, id, ready]);
  return ready;
}

/** A paint property that eases from 0 to *to* once ready (MapLibre transitions paint changes). */
export const FADE = { duration: 700, delay: 0 };
