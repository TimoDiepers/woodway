import type { Atlas } from "@/data/types";
import { deltaT, typeKey, yearIndex } from "./model";

/** ΔT of one tree [10⁻¹⁵ K] for every cell with reforestable land, in one year. A few recent years are kept:
 *  the slider moves by one year at a time and a panel asks again on every render. */
const caches = new WeakMap<Atlas, Map<number, Float32Array>>();
function treeDts(at: Atlas, year: number): Float32Array {
  const key = yearIndex(at, year);
  let cache = caches.get(at);
  if (!cache) caches.set(at, (cache = new Map()));
  let v = cache.get(key);
  if (v) return v;
  const out: number[] = [];
  for (let c = 0; c < at.f.type.length; c++) if (typeKey(at, c)) out.push(deltaT(at, c, year) * 1e15);
  v = Float32Array.from(out);
  if (cache.size >= 4) cache.delete(cache.keys().next().value!);
  cache.set(key, v);
  return v;
}

export interface Rank {
  /** share of the world's reforestable cells this one beats: cools more than (or, warming, warms more than) */
  pct: number; cools: boolean;
  /** cell counts per bin over `domain`, values outside it fall into the end bins */
  bins: number[]; domain: [number, number]; here: number;
}

export function treeRank(at: Atlas, cell: number, year: number, domain: [number, number], nBins = 36): Rank | null {
  if (!typeKey(at, cell)) return null;
  const all = treeDts(at, year), here = deltaT(at, cell, year) * 1e15;
  const cools = here < 0;
  const bins = new Array<number>(nBins).fill(0);
  const [lo, hi] = domain, w = (hi - lo) / nBins;
  let beaten = 0;
  for (const v of all) {
    if (cools ? v > here : v < here) beaten++;
    bins[Math.max(0, Math.min(nBins - 1, Math.floor((v - lo) / w)))]++;
  }
  return { pct: Math.floor((100 * beaten) / all.length), cools, bins, domain, here };
}
