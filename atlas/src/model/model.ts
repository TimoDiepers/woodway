import type { Atlas } from "@/data/types";

export const NLON = 720;

export const cellIJ = (cell: number): [number, number] => [Math.floor(cell / NLON), cell % NLON];

export function typeKey(at: Atlas, cell: number): string | null {
  const n = at.f.type[cell];
  return n ? at.meta.types[n - 1] : null;
}

export function yearIndex(at: Atlas, year: number): number {
  const y = at.meta.years;
  return Math.max(0, Math.min(y.length - 1, Math.round(year) - y[0]));
}

export function deltaT(at: Atlas, cell: number, year: number): number {
  const key = typeKey(at, cell);
  if (!key) return NaN;
  const c = at.meta.curves[key], k = yearIndex(at, year);
  return at.f.a[cell] * c.dtCo2[k] + at.f.b[cell] * c.dtAlbUnit[k];
}

export function netShare(at: Atlas, cell: number, year: number): number {
  const key = typeKey(at, cell);
  if (!key) return NaN;
  const c = at.meta.curves[key], k = yearIndex(at, year);
  const carbon = at.f.a[cell] * c.dtCo2[k];
  return carbon === 0 ? NaN : (carbon + at.f.b[cell] * c.dtAlbUnit[k]) / carbon;
}

/** Linear between the LCA base years, as nbs.dac._interp; the slider never leaves 2026–2100. */
export function dacNet(at: Atlas, cell: number, year: number): number {
  if (!at.f.dacOk[cell]) return NaN;
  const ys = at.meta.dacYears;
  const y = Math.max(at.meta.years[0], Math.min(at.meta.years.at(-1)!, year));
  let k = 0;
  while (k < ys.length - 2 && y > ys[k + 1]) k++;
  const w = (y - ys[k]) / (ys[k + 1] - ys[k]);
  return (1 - w) * at.f[`dacNet${ys[k]}`][cell] + w * at.f[`dacNet${ys[k + 1]}`][cell];
}

export function dacBuildMt(at: Atlas, cell: number, year: number): number {
  const k = at.buildByCell.get(cell);
  if (k === undefined) return 0;
  const b = at.meta.build, owner = b.owner[k];
  const t = Math.max(0, Math.min(b.years.length - 1, Math.round(year) - b.years[0]));
  return (1000 * b.capacityGt[owner][t]) / at.cellsPerOwner[owner];
}

/** First year from which the tree cools for good (ΔT < 0 through 2100); null if it does not cool in 2100. */
export function coolsFrom(at: Atlas, cell: number): number | null {
  const ys = at.meta.years;
  if (!(deltaT(at, cell, ys.at(-1)!) < 0)) return null;
  let from = ys.at(-1)!;
  for (let k = ys.length - 1; k >= 0 && deltaT(at, cell, ys[k]) < 0; k--) from = ys[k];
  return from;
}

/** For a tree that cools at some point but warms again by 2100: the last year with ΔT < 0. */
export function coolsUntil(at: Atlas, cell: number): number | null {
  const ys = at.meta.years;
  if (!typeKey(at, cell) || deltaT(at, cell, ys.at(-1)!) < 0) return null;
  for (let k = ys.length - 1; k >= 0; k--) if (deltaT(at, cell, ys[k]) < 0) return ys[k];
  return null;
}

export interface CellSeries { years: number[]; m: number[]; phiCo2: number[]; phiAlb: number[]; dt: number[] }

export function cellSeries(at: Atlas, cell: number): CellSeries | null {
  const key = typeKey(at, cell);
  if (!key) return null;
  const c = at.meta.curves[key], a = at.f.a[cell], b = at.f.b[cell];
  return {
    years: at.meta.years,
    m: c.m.map((v) => a * v),
    phiCo2: c.phiCo2.map((v) => a * v),
    phiAlb: c.phiAlbUnit.map((v) => b * v),
    dt: c.dtCo2.map((v, k) => a * v + b * c.dtAlbUnit[k]),
  };
}
