import type { Atlas } from "@/data/types";

export const NLON = 720;

export const cellIJ = (cell: number): [number, number] => [Math.floor(cell / NLON), cell % NLON];

export function typeKey(at: Atlas, cell: number): string | null {
  const n = at.f.type[cell];
  return n ? at.meta.types[n - 1] : null;
}

/** The planting year every planted tree follows (2026 or a later one of meta.plantYears); set from the store. */
let plantYear = 2026;
export const setPlantYear = (y: number) => { plantYear = y; };
export const getPlantYear = () => plantYear;

/** The curves of one tree of forest type *key*, planted in the chosen year (meta.curves holds 2026). */
export function curvesOf(at: Atlas, key: string) {
  const later = plantYear !== at.meta.years[0] ? at.meta.curvesLater?.[String(plantYear)]?.[key] : undefined;
  return later ? { ...at.meta.curves[key], ...later } : at.meta.curves[key];
}

export function yearIndex(at: Atlas, year: number): number {
  const y = at.meta.years;
  return Math.max(0, Math.min(y.length - 1, Math.round(year) - y[0]));
}

export function deltaT(at: Atlas, cell: number, year: number): number {
  const key = typeKey(at, cell);
  if (!key) return NaN;
  const c = curvesOf(at, key), k = yearIndex(at, year);
  return at.f.a[cell] * c.dtCo2[k] + at.f.b[cell] * c.dtAlbUnit[k];
}

/** Canopy closure f(t) of the cell's forest type, 0 to 1: the share of the mature tree's extra absorbed light. */
export function closure(at: Atlas, cell: number, year: number): number {
  const key = typeKey(at, cell);
  return key ? curvesOf(at, key).closure[yearIndex(at, year)] : NaN;
}

export function netShare(at: Atlas, cell: number, year: number): number {
  const key = typeKey(at, cell);
  if (!key) return NaN;
  const c = curvesOf(at, key), k = yearIndex(at, year);
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
  const c = curvesOf(at, key), a = at.f.a[cell], b = at.f.b[cell];
  return {
    years: at.meta.years,
    m: c.m.map((v) => a * v),
    phiCo2: c.phiCo2.map((v) => a * v),
    phiAlb: c.phiAlbUnit.map((v) => b * v),
    dt: c.dtCo2.map((v, k) => a * v + b * c.dtAlbUnit[k]),
  };
}

// --- per land area: what a whole cell's forest does [10⁻⁶ K per 10 000 km² of the cell], as the deck's map
// "Wo lohnt sich Aufforstung?" (nbs.map_fields.total_effect): ΔT per tree x trees / cell area -------------------
const STAND_M2 = 5;   // 2000 trees per ha (nbs.forest_data.TREES_PER_HA)
const R2 = 5.1006e14 / (4 * Math.PI);
const CELL_M2 = Array.from({ length: 360 }, (_, i) => {
  const a = ((90 - 0.5 * i) * Math.PI) / 180, b = ((90 - 0.5 * (i + 1)) * Math.PI) / 180;
  return (2 * Math.PI * R2 * Math.abs(Math.sin(a) - Math.sin(b))) / 720;
});
const perArea = (cell: number, dtTree: number, areaM2: number) =>
  (dtTree * (areaM2 / STAND_M2) / CELL_M2[Math.floor(cell / NLON)]) * 1e16;

/** All reforestable area of the cell forested, planted in the chosen year. */
export function cellTotal(at: Atlas, cell: number, year: number): number {
  return typeKey(at, cell) ? perArea(cell, deltaT(at, cell, year), at.f.area[cell]) : NaN;
}

/** Forest on the land a vegan world frees (nbs.vegan), planted in the chosen year. */
export function veganLand(at: Atlas, cell: number, year: number): number {
  const n = at.f.freeType?.[cell];
  if (!n) return NaN;
  const c = curvesOf(at, at.meta.types[n - 1]), k = yearIndex(at, year);
  return perArea(cell, at.f.freeA[cell] * c.dtCo2[k] + at.f.freeB[cell] * c.dtAlbUnit[k], at.f.freeArea[cell]);
}

/** Today's forest (Walker et al. 2022): what its further uptake from 2026 on does, if it grows on undisturbed. */
function bestand(at: Atlas, cell: number, year: number): { up: number; canopy: number } | null {
  const n = at.f.bType?.[cell];
  if (!n) return null;
  const b = at.meta.bestand.curves[at.meta.types[n - 1]], k = yearIndex(at, year);
  return { up: at.f.bA[cell] * b.dtUp[at.f.bAge[cell]][k], canopy: at.f.bB[cell] * b.dtCanopy[k] };
}
export function bestandUptake(at: Atlas, cell: number, year: number): number {
  const v = bestand(at, cell, year);
  return v ? perArea(cell, v.up, at.f.bArea[cell]) : NaN;
}

/** Today's forest where forest warms (nbs.tree_paths.felling_cells), cut in 2026, the wood buried, the land kept
 *  open: the brighter land, minus the uptake it would still have had. */
export function felling(at: Atlas, cell: number, year: number): number {
  if (!at.f.bFell?.[cell]) return NaN;
  const v = bestand(at, cell, year)!;
  return perArea(cell, -(v.up + v.canopy), at.f.bArea[cell]);
}
