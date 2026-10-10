import type { Atlas } from "@/data/types";
import { dacNet, deltaT, netShare } from "@/model/model";

const N = (at: Atlas) => at.f.type.length;

/** Reforestable area where a tree cools in that year / all reforestable area. */
export function coolingShare(at: Atlas, year: number): number {
  let cool = 0, all = 0;
  for (let c = 0; c < N(at); c++) {
    if (!at.f.type[c]) continue;
    const a = at.f.area[c];
    all += a;
    if (deltaT(at, c, year) < 0) cool += a;
  }
  return all ? cool / all : NaN;
}

/** Median of the values, each weighted (cumulative weight reaches half the total). */
function weightedMedian(vals: number[], w: number[]): number {
  const idx = vals.map((_, i) => i).sort((i, j) => vals[i] - vals[j]);
  const half = w.reduce((s, x) => s + x, 0) / 2;
  let acc = 0;
  for (const i of idx) { acc += w[i]; if (acc >= half) return vals[i]; }
  return NaN;
}

/** Area-weighted median of the net share (CO₂ effect after the albedo) over forest cells. */
export function medianNetShare(at: Atlas, year: number): number {
  const v: number[] = [], w: number[] = [];
  for (let c = 0; c < N(at); c++) {
    if (!at.f.type[c]) continue;
    const s = netShare(at, c, year);
    if (Number.isFinite(s)) { v.push(s); w.push(at.f.area[c]); }
  }
  return weightedMedian(v, w);
}

/** Median of the DAC net share over the cells where DAC is possible. */
export function medianDacNet(at: Atlas, year: number): number {
  const v: number[] = [];
  for (let c = 0; c < N(at); c++) {
    if (!at.f.dacOk[c]) continue;
    const s = dacNet(at, c, year);
    if (Number.isFinite(s)) v.push(s);
  }
  v.sort((a, b) => a - b);
  const m = v.length >> 1;
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}

export function dacCapacityGt(at: Atlas, year: number): number {
  const g = at.meta.global;
  const k = g.years.indexOf(year);
  return g.dacCapacityGt[k >= 0 ? k : Math.max(0, Math.min(g.years.length - 1, Math.round(year) - g.years[0]))];
}
