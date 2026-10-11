import type { Atlas } from "@/data/types";
import type { Layer } from "@/model/layers";
import { reasonColor, scaleOf } from "@/model/layers";
import { hexToRgba, scaleColor, themedScale, type RGBA } from "@/color/scale";
import { LAT_MAX } from "./lookup";
import { clampBounds, hexCentres, mercY, HEX_R_DEG, HEX_R_M, HEX_ROW_M, type Bounds } from "./hex";

/** The whole map (to ±85°): where the canvas source sits before the first painting. */
export const IMAGE_COORDS: [[number, number], [number, number], [number, number], [number, number]] =
  [[-180, LAT_MAX], [180, LAT_MAX], [180, -LAT_MAX], [-180, -LAT_MAX]];

const pack = ([r, g, b, a]: RGBA) => ((a << 24) | (b << 16) | (g << 8) | r) >>> 0;

export function cellColors(at: Atlas, layer: Layer, year: number, out: Uint32Array = new Uint32Array(360 * 720), dark = false): Uint32Array {
  const base = scaleOf(at, layer), sc = base && themedScale(base, dark);
  const land = pack(hexToRgba(reasonColor(at, null, dark)));
  const grey = new Map(layer.greys.map((r) => [r, pack(hexToRgba(reasonColor(at, r, dark)))]));
  const cats = at.meta.categories.waldtyp.map((c) => pack(hexToRgba(c.color)));
  for (let c = 0; c < out.length; c++) {
    if (!at.f.land[c]) { out[c] = 0; continue; }
    const v = layer.value(at, c, year);
    if (layer.kind === "cat") out[c] = v >= 0 && v < cats.length ? cats[v] : land;
    else if (Number.isFinite(v) && sc) out[c] = pack(scaleColor(sc, v));
    else { const r = layer.reason(at, c); out[c] = (r && grey.get(r)) ?? land; }
  }
  return out;
}

/**
 * Paints the 0.5° hexagons of the view into a canvas of w×h px that covers `bounds` in Web Mercator, as the
 * talk's maps do: a regular lattice, each hexagon in the colour of the cell under its centre. The hexagons are
 * rasterised here, row by row of pixels (a pixel belongs to the hexagon its centre lies in, so neighbours tile
 * without seams or overlap), and put into the canvas at once: filling a path per hexagon is far too slow for
 * the ~100 000 hexagons of a world view. `colors` (from cellColors) can be passed in to reuse them across views.
 */
export function paintHexView(ctx: CanvasRenderingContext2D, w: number, h: number, bounds: Bounds, at: Atlas, layer: Layer,
  year: number, colors: Uint32Array = cellColors(at, layer, year)): void {
  const b = clampBounds(bounds);
  const hx = hexCentres(b, HEX_R_DEG);
  const kx = w / (b.east - b.west), yN = mercY(b.north), ky = h / (yN - mercY(b.south));
  const px = new Uint8ClampedArray(w * h * 4), img = new Uint32Array(px.buffer);
  const dx = 0.25 * kx;   // half the width of a hexagon: 0.25° in px
  let lat = NaN, yT = 0, yU = 0, yD = 0, yB = 0;
  for (let i = 0; i < hx.lon.length; i++) {
    if (hx.lat[i] !== lat) {   // rows share their latitude, and so the y of their corners
      lat = hx.lat[i];
      // the row's Mercator y, snapped to the lattice (the centres' latitudes are only float32)
      const m = (Math.round(mercY(lat) / HEX_ROW_M - 0.5) + 0.5) * HEX_ROW_M;
      yT = (yN - m - HEX_R_M) * ky; yU = (yN - m - HEX_R_M / 2) * ky;
      yD = (yN - m + HEX_R_M / 2) * ky; yB = (yN - m + HEX_R_M) * ky;
    }
    const c = colors[hx.cell[i]];
    if (!c) continue;   // ocean stays transparent
    const cx = (hx.lon[i] - b.west) * kx;
    if (cx + dx < 0 || cx - dx > w) continue;
    const r0 = Math.max(0, Math.ceil(yT - 0.5)), r1 = Math.min(h, Math.ceil(yB - 0.5));
    for (let r = r0; r < r1; r++) {
      const y = r + 0.5;
      const half = y < yU ? (dx * (y - yT)) / (yU - yT) : y > yD ? (dx * (yB - y)) / (yB - yD) : dx;
      const x0 = Math.max(0, Math.ceil(cx - half - 0.5)), x1 = Math.min(w, Math.ceil(cx + half - 0.5));
      if (x1 > x0) img.fill(c, r * w + x0, r * w + x1);
    }
  }
  ctx.putImageData(new ImageData(px, w, h), 0, 0);
}
