import { useEffect, useMemo, useRef, useState } from "react";
import Map, { Layer as MLayer, Marker, Source, type MapRef, type MapLayerMouseEvent } from "react-map-gl/maplibre";
import type { ImageSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Atlas } from "@/data/types";
import type { Layer } from "@/model/layers";
import { paperBasemap, paperBasemapDark } from "@/lib/mapStyle";
import { cellColors, mercatorImage, IMAGE_COORDS, IMG_W, IMG_H } from "./paint";
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

const EMPTY = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";

export default function AtlasMap({ atlas, layer, year, cell, onCell, onHover, projection = "globe", dark = false,
  sites = [], flyTo = null, initialView = { longitude: 10, latitude: 25, zoom: 1.6 } }: AtlasMapProps) {
  const mapRef = useRef<MapRef | null>(null);
  const canvas = useMemo(() => { const c = document.createElement("canvas"); c.width = IMG_W; c.height = IMG_H; return c; }, []);
  const buffers = useMemo(() => ({ colors: new Uint32Array(360 * 720), img: new Uint32Array(IMG_W * IMG_H) }), []);
  const [loaded, setLoaded] = useState(false);
  const urlRef = useRef<string | null>(null);
  const pending = useRef(0);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);

  useEffect(() => () => {
    pending.current++;
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
  }, []);

  useEffect(() => {
    if (flyTo) mapRef.current?.flyTo({ center: [flyTo.lon, flyTo.lat], zoom: 4, duration: 1200 });
  }, [flyTo]);

  // Repaint on layer/year change: one paint per animation frame, the latest request wins.
  useEffect(() => {
    if (!loaded) return;
    const ticket = ++pending.current;
    const raf = requestAnimationFrame(() => {
      if (ticket !== pending.current) return;
      cellColors(atlas, layer, year, buffers.colors);
      mercatorImage(buffers.colors, buffers.img);
      const ctx = (ctxRef.current ??= canvas.getContext("2d"))!;
      ctx.putImageData(new ImageData(new Uint8ClampedArray(buffers.img.buffer), IMG_W, IMG_H), 0, 0);
      canvas.toBlob((blob) => {
        if (!blob || ticket !== pending.current) return;
        const url = URL.createObjectURL(blob);
        const src = mapRef.current?.getMap().getSource("atlas") as ImageSource | undefined;
        src?.updateImage({ url, coordinates: IMAGE_COORDS });
        if (urlRef.current) URL.revokeObjectURL(urlRef.current);
        urlRef.current = url;
      });
    });
    return () => cancelAnimationFrame(raf);
  }, [atlas, layer, year, loaded, canvas, buffers]);

  const pick = (e: MapLayerMouseEvent) => {
    const c = cellAt(e.lngLat.lng, e.lngLat.lat);
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
      onClick={(e) => onCell(pick(e))}
      onMouseMove={onHover ? (e) => onHover(pick(e), e.point.x, e.point.y) : undefined}
      onMouseLeave={onHover ? () => onHover(null, 0, 0) : undefined}
      style={{ position: "absolute", inset: 0, background: "rgb(var(--color-paper))" }}
      attributionControl={{ compact: true }}
    >
      <Source id="atlas" type="image" url={EMPTY} coordinates={IMAGE_COORDS}>
        <MLayer id="atlas-layer" type="raster" paint={{ "raster-resampling": "nearest", "raster-opacity": 0.95, "raster-fade-duration": 0 }} />
      </Source>
      <Borders dark={dark} />
      {sites.map((s) => (
        <Marker key={s.name} longitude={s.lon} latitude={s.lat} anchor="center">
          <span className="block h-3 w-3 rounded-full border-2 border-white" style={{ background: s.color }} title={s.name} />
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
