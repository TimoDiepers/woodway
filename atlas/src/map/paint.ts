import type { Atlas } from "@/data/types";
import type { Layer } from "@/model/layers";
import { scaleOf } from "@/model/layers";
import { hexToRgba, scaleColor, type RGBA } from "@/color/scale";
import { LAT_MAX } from "./lookup";

export const IMG_W = 1440, IMG_H = 1440;
export const IMAGE_COORDS: [[number, number], [number, number], [number, number], [number, number]] =
  [[-180, LAT_MAX], [180, LAT_MAX], [180, -LAT_MAX], [-180, -LAT_MAX]];

const pack = ([r, g, b, a]: RGBA) => ((a << 24) | (b << 16) | (g << 8) | r) >>> 0;

export function cellColors(at: Atlas, layer: Layer, year: number, out = new Uint32Array(360 * 720)): Uint32Array {
  const sc = scaleOf(at, layer);
  const land = pack(hexToRgba(at.meta.colors.land));
  const cold = pack(hexToRgba(at.meta.colors.tooCold));
  const cats = at.meta.categories.waldtyp.map((c) => pack(hexToRgba(c.color)));
  for (let c = 0; c < out.length; c++) {
    if (!at.f.land[c]) { out[c] = 0; continue; }
    const v = layer.value(at, c, year);
    if (layer.kind === "cat") out[c] = v >= 0 ? cats[v] : land;
    else if (Number.isFinite(v) && sc) out[c] = pack(scaleColor(sc, v));
    else out[c] = layer.reason(at, c) === "reason.tooCold" ? cold : land;
  }
  return out;
}

const ROW_OF: Int32Array = (() => {
  const rows = new Int32Array(IMG_H);
  const yMax = Math.log(Math.tan(Math.PI / 4 + (LAT_MAX * Math.PI) / 360));
  for (let r = 0; r < IMG_H; r++) {
    const y = yMax - ((r + 0.5) / IMG_H) * 2 * yMax;
    const lat = (Math.atan(Math.sinh(y)) * 180) / Math.PI;
    rows[r] = Math.min(359, Math.floor((90 - lat) / 0.5));
  }
  return rows;
})();

export function mercatorImage(colors: Uint32Array, out = new Uint32Array(IMG_W * IMG_H)): Uint32Array {
  for (let r = 0; r < IMG_H; r++) {
    const src = ROW_OF[r] * 720, dst = r * IMG_W;
    for (let x = 0; x < IMG_W; x++) out[dst + x] = colors[src + ((x * 720) / IMG_W) | 0];
  }
  return out;
}
