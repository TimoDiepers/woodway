import type { Atlas } from "@/data/types";
import { ROW_AREA } from "@/model/layers";
import { dacNet, deltaT, typeKey, yearIndex } from "@/model/model";

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

/** The talk's area-level net share: Σ(area·ΔT) / Σ(area·ΔT_CO₂) over forest cells (only those that cool in that year if asked). */
export function netShareArea(at: Atlas, year: number, onlyCooling: boolean): number {
  let net = 0, co2 = 0;
  const k = yearIndex(at, year);
  for (let c = 0; c < N(at); c++) {
    const key = typeKey(at, c);
    if (!key) continue;
    const d = deltaT(at, c, year);
    if (!Number.isFinite(d) || (onlyCooling && !(d < 0))) continue;
    const a = at.f.area[c];
    net += a * d;
    co2 += a * at.f.a[c] * at.meta.curves[key].dtCo2[k];
  }
  return co2 ? net / co2 : NaN;
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
