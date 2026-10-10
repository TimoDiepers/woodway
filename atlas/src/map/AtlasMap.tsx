import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Map, { Layer as MLayer, Marker, Source, type MapRef, type MapLayerMouseEvent, type SourceProps } from "react-map-gl/maplibre";
import type { CanvasSource, CanvasSourceSpecification, Map as MaplibreMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Atlas } from "@/data/types";
import type { Layer } from "@/model/layers";
import { paperBasemap, paperBasemapDark } from "@/lib/mapStyle";
import { cellColors, paintHexView, IMAGE_COORDS } from "./paint";
import { clampBounds } from "./hex";
import { cellAt, cellCenter } from "./lookup";
import Borders from "./Borders";

export interface AtlasMapProps {
  atlas: Atlas; layer: Layer; year: number; cell: number | null;
  onCell(cell: number | null): void;
  onHover?(cell: number | null, x: number, y: number): void;
  projection?: "globe" | "mercator"; dark?: boolean;
  sites?: { name: string; lat: number; lon: number; color: string }[];
  flyTo?: { lon: number; lat: number } | null;
  initialView?: { longitude: number; latitude: number; zoom: number };
}

type Coords = typeof IMAGE_COORDS;

// The painted image reaches this far beyond the view (share of its span per side), so a short pan or zoom
// out stays covered until the repaint at its end.
const MARGIN = 0.15;
// A painting larger than this is drawn at a lower resolution (texture size, memory, paint time).
const MAX_SIDE = 4096, MAX_PX = 10e6;
const mercY = (lat: number) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));

/** The image for the current view: bounds clamped to the paintable world, canvas size at device pixels. */
function viewImage(map: MaplibreMap) {
  const v = map.getBounds();
  const [w0, s0, e0, n0] = [v.getWest(), v.getSouth(), v.getEast(), v.getNorth()];
  const mx = MARGIN * (e0 - w0), my = MARGIN * (n0 - s0);
  const b = clampBounds({ west: w0 - mx, south: s0 - my, east: e0 + mx, north: n0 + my });
  const world = 512 * 2 ** map.getZoom() * (window.devicePixelRatio || 1);   // the world's width in device px
  let w = (world * (b.east - b.west)) / 360, h = (world * (mercY(b.north) - mercY(b.south))) / (2 * Math.PI);
  const k = Math.min(1, MAX_SIDE / w, MAX_SIDE / h, Math.sqrt(MAX_PX / (w * h)));
  w = Math.max(1, Math.round(w * k)); h = Math.max(1, Math.round(h * k));
  const coords: Coords = [[b.west, b.north], [b.east, b.north], [b.east, b.south], [b.west, b.south]];
  return { b, w, h, coords };
}

export default function AtlasMap({ atlas, layer, year, cell, onCell, onHover, projection = "globe", dark = false,
  sites = [], flyTo = null, initialView = { longitude: 10, latitude: 25, zoom: 1.6 } }: AtlasMapProps) {
  const mapRef = useRef<MapRef | null>(null);
  // The painting goes straight from this canvas to the GPU (a maplibre canvas source, not an encoded image).
  const canvas = useMemo(() => document.createElement("canvas"), []);
  const [loaded, setLoaded] = useState(false);
  // where the canvas sits; a theme switch re-adds the source from these props and the canvas as it is
  const [coords, setCoords] = useState<Coords>(IMAGE_COORDS);
  const pending = useRef(0);
  const latest = useRef({ atlas, layer, year });
  latest.current = { atlas, layer, year };
  const colours = useRef<{ atlas: Atlas; layer: Layer; year: number; colors: Uint32Array } | null>(null);

  useEffect(() => () => { pending.current++; }, []);

  useEffect(() => {
    if (flyTo) mapRef.current?.flyTo({ center: [flyTo.lon, flyTo.lat], zoom: 4, duration: 1200 });
  }, [flyTo]);

  // Paint the view: one paint per animation frame, the latest request wins. The cells' colours are kept
  // until layer or year change; a moved view only redraws the hexagons.
  const repaint = useCallback(() => {
    const ticket = ++pending.current;
    requestAnimationFrame(() => {
      const map = mapRef.current?.getMap();
      if (ticket !== pending.current || !map) return;
      const t0 = performance.now();
      const { atlas, layer, year } = latest.current;
      let cc = colours.current;
      if (!cc || cc.atlas !== atlas || cc.layer !== layer || cc.year !== year)
        cc = colours.current = { atlas, layer, year, colors: cellColors(atlas, layer, year, cc?.colors) };
      const v = viewImage(map);
      canvas.width = v.w; canvas.height = v.h;
      paintHexView(canvas.getContext("2d", { willReadFrequently: true })!, v.w, v.h, v.b, atlas, layer, year, cc.colors);
      performance.measure?.("atlas:paint", { start: t0 });   // read by the headless check
      const src = map.getSource("atlas") as CanvasSource | undefined;
      if (src?.play) {
        src.setCoordinates(v.coords);
        src.play(); src.pause();   // uploads the canvas once (an animate: false source keeps its texture otherwise)
      }
      setCoords(v.coords);
      performance.measure?.("atlas:upload", { start: t0 });
    });
  }, [canvas]);

  useEffect(() => { if (loaded) repaint(); }, [atlas, layer, year, projection, loaded, repaint]);

  const pick = (e: MapLayerMouseEvent) => {
    const { lng, lat } = e.lngLat.wrap();   // a spun globe reports longitudes beyond ±180
    const c = cellAt(lng, lat);
    return c !== null && atlas.f.land[c] ? c : null;
  };

  const sel = cell !== null ? cellCenter(cell) : null;
  return (
    <Map
      ref={mapRef}
      initialViewState={initialView}
      mapStyle={dark ? paperBasemapDark : paperBasemap}
      projection={projection}
      onLoad={() => setLoaded(true)}
      onMoveEnd={() => repaint()}
      onResize={() => repaint()}
      onClick={(e) => onCell(pick(e))}
      onMouseMove={onHover ? (e) => onHover(pick(e), e.point.x, e.point.y) : undefined}
      onMouseLeave={onHover ? () => onHover(null, 0, 0) : undefined}
      // the cell under a still pointer changes once the map moves (a site jump, a search): drop the readout
      onMoveStart={onHover ? () => onHover(null, 0, 0) : undefined}
      style={{ position: "absolute", inset: 0, background: "rgb(var(--color-paper))" }}
      attributionControl={{ compact: true }}
    >
      {/* react-map-gl types <Source> without canvas sources; it passes them on to maplibre like any other */}
      <Source {...({ id: "atlas", type: "canvas", canvas, coordinates: coords, animate: false } as CanvasSourceSpecification as unknown as SourceProps)}>
        <MLayer id="atlas-layer" type="raster" paint={{ "raster-resampling": "nearest", "raster-opacity": 0.95, "raster-fade-duration": 0 }} />
      </Source>
      <Borders dark={dark} />
      {sites.map((s) => (
        <Marker key={s.name} longitude={s.lon} latitude={s.lat} anchor="center">
          <span className="block h-3 w-3 rounded-full border-2 border-paper shadow-[0_0_0_1px_rgb(var(--color-ink)/0.55)]" style={{ background: s.color }} title={s.name} />
        </Marker>
      ))}
      {sel && (
        <Marker longitude={sel.lon} latitude={sel.lat} anchor="center">
          <span className="block h-4 w-4 rounded-sm border-2 border-ink" aria-hidden />
        </Marker>
      )}
    </Map>
  );
}
