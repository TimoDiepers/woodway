import type { Atlas } from "@/data/types";
import { ROW_AREA } from "@/model/layers";
import { dacBuildMt, dacNet, deltaT } from "@/model/model";

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

/** Median of the DAC net share over the land area where DAC is possible: each cell counts with its area. */
export function medianDacNet(at: Atlas, year: number): number {
  const v: { s: number; w: number }[] = [];
  let total = 0;
  for (let c = 0; c < N(at); c++) {
    if (!at.f.dacOk[c]) continue;
    const s = dacNet(at, c, year);
    if (!Number.isFinite(s)) continue;
    const w = ROW_AREA[Math.floor(c / 720)];
    v.push({ s, w });
    total += w;
  }
  v.sort((a, b) => a.s - b.s);
  let acc = 0;
  for (const x of v) { acc += x.w; if (acc >= total / 2) return x.s; }
  return NaN;
}

export function dacCapacityGt(at: Atlas, year: number): number {
  const g = at.meta.global;
  const k = g.years.indexOf(year);
  return g.dacCapacityGt[k >= 0 ? k : Math.max(0, Math.min(g.years.length - 1, Math.round(year) - g.years[0]))];
}

/** 95th percentile of the capacity (Mt/a) of the cells that are built in that year: the top of the talk's build-out scale. */
export function buildP95(at: Atlas, year: number): number {
  const v: number[] = [];
  for (const c of at.buildByCell.keys()) { const m = dacBuildMt(at, c, year); if (m > 0) v.push(m); }
  v.sort((a, b) => a - b);
  return v.length ? v[Math.min(v.length - 1, Math.floor(0.95 * v.length))] : NaN;
}
