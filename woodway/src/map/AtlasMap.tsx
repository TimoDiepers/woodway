import type { FeatureCollection } from "geojson";
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
import { hexAt, hexRing } from "./hex";
import Borders from "./Borders";
import Labels from "./Labels";
import { mapLib } from "./mapLib";

export interface AtlasMapProps {
  /** null while the cells' data loads: the globe, its lines and names stand already, the hexagons fade in later */
  atlas: Atlas | null; layer: Layer; year: number; cell: number | null;
  /** land and lines stand, and then the place names (the app loads the other fields after them) */
  onBase?: () => void;
  onNames?: () => void;
  /** the layer's fields have arrived (the map draws its hexagons only then) */
  ready?: boolean;
  /** the planting year: a new one recolours the planted layers */
  plantYear?: number;
  /** place names over the map, in this language (off: none) */
  labels?: "de" | "en" | null;
  onCell(cell: number | null): void;
  onHover?(cell: number | null, x: number, y: number): void;
  projection?: "globe" | "mercator"; dark?: boolean;
  sites?: { name: string; lat: number; lon: number; color: string }[];
  /** zoom omitted: keep the current zoom and only bring the point into view (a tapped cell on a phone) */
  flyTo?: { lon: number; lat: number; zoom?: number } | null;
  initialView?: { longitude: number; latitude: number; zoom: number };
  /** screen area covered by UI (a phone's top bar and bottom sheet): the camera centres in what is left */
  insets?: { top: number; bottom: number; right?: number };
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

// the glyphs of the place names, served with the app (public/glyphs); MapLibre needs an absolute URL template
const GLYPHS = (typeof document !== "undefined" ? document.baseURI.replace(/[^/]*$/, "") : "/") + "glyphs/{fontstack}/{range}.pbf";
const styleLight = { ...paperBasemap, glyphs: GLYPHS };
const styleDark = { ...paperBasemapDark, glyphs: GLYPHS };

export default function AtlasMap({ atlas, ready = true, onBase, onNames, layer, year, plantYear = 2026, labels = null, cell, onCell, onHover, projection = "globe", dark = false,
  sites = [], flyTo = null, initialView = { longitude: 10, latitude: 25, zoom: 1.6 }, insets }: AtlasMapProps) {
  const mapRef = useRef<MapRef | null>(null);
  // The painting goes straight from this canvas to the GPU (a maplibre canvas source, not an encoded image).
  const canvas = useMemo(() => document.createElement("canvas"), []);
  const [loaded, setLoaded] = useState(false);
  // the first painted view of the cells: the hexagons fade in then, not before (a blank canvas until it)
  const [painted, setPainted] = useState(false);
  // the land first: the hexagons wait until the continents stand (or 10 s, if the sea file cannot be had)
  const [land, setLand] = useState(false);
  const showLand = useCallback(() => setLand(true), []);
  useEffect(() => { const t = setTimeout(() => setLand(true), 10000); return () => clearTimeout(t); }, []);
  const [hoverHex, setHoverHex] = useState<{ lon: number; lat: number } | null>(null);
  // where the canvas sits; a theme switch re-adds the source from these props and the canvas as it is
  const [coords, setCoords] = useState<Coords>(IMAGE_COORDS);
  const pending = useRef(0);
  const latest = useRef({ atlas, layer, year, dark, plantYear, ready });
  latest.current = { atlas, layer, year, dark, plantYear, ready };
  const colours = useRef<{ atlas: Atlas | null; layer: Layer; year: number; dark: boolean; plantYear: number; colors: Uint32Array } | null>(null);
  // the colours with the other cells faded around a selected one, kept while view and selection stay

  useEffect(() => () => { pending.current++; }, []);

  const padding = { top: insets?.top ?? 0, bottom: insets?.bottom ?? 0, left: 0, right: insets?.right ?? 0 };
  // a jump in this commit already carries the new padding; the inset easing must not cut it short
  const jumping = useRef(false);
  useEffect(() => {
    if (!flyTo) return;
    const map = mapRef.current;
    if (!map) return;
    jumping.current = true; queueMicrotask(() => { jumping.current = false; });
    if (flyTo.zoom === undefined) map.easeTo({ center: [flyTo.lon, flyTo.lat], padding, duration: 450 });
    else map.flyTo({ center: [flyTo.lon, flyTo.lat], zoom: flyTo.zoom, padding, duration: 1200 });
    // padding is read at the time of the jump on purpose
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flyTo]);
  // the sheet moving up or down shifts the free part of the screen: keep the view's centre in it
  useEffect(() => {
    if (!loaded || !insets || jumping.current) return;
    mapRef.current?.easeTo({ padding, duration: 300 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loaded, insets?.top, insets?.bottom, insets?.right]);

  // Paint the view: one paint per animation frame, the latest request wins. The cells' colours are kept
  // until layer or year change; a moved view only redraws the hexagons.
  const repaint = useCallback(() => {
    const ticket = ++pending.current;
    requestAnimationFrame(() => {
      const map = mapRef.current?.getMap();
      if (ticket !== pending.current || !map) return;
      const t0 = performance.now();
      const { atlas, layer, year, dark, plantYear, ready } = latest.current;
      if (!atlas || !ready) return;
      let cc = colours.current;
      if (!cc || cc.atlas !== atlas || cc.layer !== layer || cc.year !== year || cc.dark !== dark || cc.plantYear !== plantYear)
        cc = colours.current = { atlas, layer, year, dark, plantYear, colors: cellColors(atlas, layer, year, cc?.colors, dark) };
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
      setPainted(true);
      performance.measure?.("atlas:upload", { start: t0 });
    });
  }, [canvas]);

  useEffect(() => { if (loaded) repaint(); }, [atlas, ready, layer, year, plantYear, dark, projection, loaded, repaint]);

  const pick = (e: MapLayerMouseEvent) => {
    const { lng, lat } = e.lngLat.wrap();   // a spun globe reports longitudes beyond ±180
    const c = cellAt(lng, lat);
    if (c === null || !atlas || !atlas.f.land?.[c]) return null;
    // a coastal cell reaches into the sea, where the sea now covers it: a point in the sea picks nothing
    const map = mapRef.current?.getMap();
    if (map?.getLayer?.("ocean-fill") && map.queryRenderedFeatures(e.point, { layers: ["ocean-fill"] }).length) return null;
    return c;
  };

  const sel = cell !== null ? cellCenter(cell) : null;
  // the hexagon under the pointer and the selected one, as outlines on the map (the selected one stronger)
  const selHex = sel ? hexAt(sel.lon, sel.lat) : null;
  const ring = (h: { lon: number; lat: number } | null) =>
    ({ type: "FeatureCollection", features: h ? [{ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: hexRing(h) } }] : [] }) as FeatureCollection;
  return (
    <Map
      mapLib={mapLib}
      ref={mapRef}
      initialViewState={initialView}
      mapStyle={dark ? styleDark : styleLight}
      projection={projection}
      // ready once the style stands: "load" would wait for every first source (sea, lines) on a slow connection
      onLoad={() => setLoaded(true)}
      onRender={() => { if (!loaded && mapRef.current?.getMap().getSource("atlas")) setLoaded(true); }}
      onMoveEnd={() => repaint()}
      onResize={() => repaint()}
      onClick={(e) => onCell(pick(e))}
      onMouseMove={(e) => {
        const c = pick(e);
        onHover?.(c, e.point.x, e.point.y);
        const { lng, lat } = e.lngLat.wrap(), h = c !== null ? hexAt(lng, lat) : null;
        setHoverHex((o) => (o?.lon === h?.lon && o?.lat === h?.lat ? o : h));
      }}
      onMouseLeave={() => { onHover?.(null, 0, 0); setHoverHex(null); }}
      // the cell under a still pointer changes once the map moves (a site jump, a search): drop the readout
      onMoveStart={() => { onHover?.(null, 0, 0); setHoverHex(null); }}
      style={{ position: "absolute", inset: 0, background: "rgb(var(--color-paper))" }}
      attributionControl={{ compact: true }}
    >
      {/* react-map-gl types <Source> without canvas sources; it passes them on to maplibre like any other */}
      <Source {...({ id: "atlas", type: "canvas", canvas, coordinates: coords, animate: false } as CanvasSourceSpecification as unknown as SourceProps)}>
        <MLayer id="atlas-layer" type="raster" paint={{ "raster-resampling": "nearest", "raster-opacity": painted && ready && land ? 0.95 : 0, "raster-opacity-transition": { duration: 600, delay: 0 }, "raster-fade-duration": 0 }} />
      </Source>
      {/* the outlines first: sea and lines are inserted below them (beforeId), the names go on top */}
      <Source id="hex-hover" type="geojson" data={ring(hoverHex && (hoverHex.lon !== selHex?.lon || hoverHex.lat !== selHex?.lat) ? hoverHex : null)}>
        <MLayer id="hex-hover-casing" type="line" layout={{ "line-join": "round" }} paint={{ "line-color": dark ? "#14181a" : "#f6f1e6", "line-width": 3.5, "line-opacity": 0.85 }} />
        <MLayer id="hex-hover-line" type="line" layout={{ "line-join": "round" }} paint={{ "line-color": dark ? "#f2ede2" : "#1b2420", "line-width": 1.5 }} />
      </Source>
      <Source id="hex-sel" type="geojson" data={ring(selHex)}>
        <MLayer id="hex-sel-casing" type="line" layout={{ "line-join": "round" }} paint={{ "line-color": dark ? "#14181a" : "#f6f1e6", "line-width": 5 }} />
        <MLayer id="hex-sel-line" type="line" layout={{ "line-join": "round" }} paint={{ "line-color": dark ? "#f2ede2" : "#1b2420", "line-width": 2.5 }} />
      </Source>
      <Borders dark={dark} onLand={showLand} onBase={onBase} />
      {/* the names after the cells: they never hold up the data on a slow connection */}
      {labels && atlas && <Labels lang={labels} dark={dark} onReady={onNames} />}
      {sites.map((s) => (
        <Marker key={s.name} longitude={s.lon} latitude={s.lat} anchor="center">
          <span className="block h-3 w-3 rounded-full border-2 border-paper shadow-[0_0_0_1px_rgb(var(--color-ink)/0.55)]" style={{ background: s.color }} title={s.name} />
        </Marker>
      ))}
    </Map>
  );
}
