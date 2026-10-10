import type { Atlas } from "@/data/types";
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
