import type { Scale } from "@/data/types";

export type RGBA = [number, number, number, number];

export function hexToRgba(hex: string, alpha = 255): RGBA {
  return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16), alpha];
}

export function scaleT(sc: Scale, v: number): number {
  const [lo, hi] = sc.domain;
  let t: number;
  if (sc.mid !== undefined) {
    t = v < sc.mid ? (0.5 * (v - lo)) / (sc.mid - lo) : 0.5 + (0.5 * (v - sc.mid)) / (hi - sc.mid);
  } else {
    t = (v - lo) / (hi - lo);
  }
  t = Math.max(0, Math.min(1, t));
  return sc.gamma ? Math.pow(t, sc.gamma) : t;
}

const cache = new WeakMap<Scale, RGBA[]>();

export function scaleColor(sc: Scale, v: number): RGBA {
  let stops = cache.get(sc);
  if (!stops) { stops = sc.stops.map((s) => hexToRgba(s)); cache.set(sc, stops); }
  const x = scaleT(sc, v) * (stops.length - 1);
  const k = Math.min(stops.length - 2, Math.floor(x)), f = x - k;
  const p = stops[k], q = stops[k + 1];
  return [0, 1, 2].map((c) => Math.round(p[c] + (q[c] - p[c]) * f)).concat(255) as RGBA;
}
