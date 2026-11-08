export interface Meta {
  version: 1;
  grid: {nlat: number; nlon: number; d: number; lat0: number; lon0: number};
  years: number[];
  fields: Record<string, {offset: number; dtype: "f4" | "u1"; length: number}>;
  types: string[];
  typeGroup: Record<string, string>;
  curves: Record<string, {m: number[]; closure: number[]; phiCo2: number[]; phiAlbUnit: number[]; dtCo2: number[]; dtAlbUnit: number[]}>;
  /** the planting years on offer, and the curves of a tree planted in each later one (meta.curves is the first) */
  plantYears: number[];
  curvesLater: Record<string, Record<string, {m: number[]; closure: number[]; dtCo2: number[]; dtAlbUnit: number[]}>>;
  /** today's forest (Walker et al. 2022, woody land): per type the ΔT of one tree's further uptake per age bin (site
   *  factor 1) and of its canopy's albedo held from 2026 (per unit light product); world totals [mK, Gt CO2/a] */
  bestand: {curves: Record<string, {dtUp: number[][]; dtCanopy: number[]; stockRef: number[]}>; ageBin: number;
            areaGha: number; fellGha: number; uptakeMK: number[]; fellMK: number[]; uptakeGt: number[]};
  dacYears: number[];
  build: {years: number[]; countries: string[]; cells: [number, number][]; owner: number[]; capacityGt: number[][]};
  global: {years: number[]; need: number[]; afterTrees: number[]; afterDac: number[]; dacCapacityGt: number[];
           paths: Record<"alle" | "kuehlt" | "forst", number[]>; areasGha: Record<"alle" | "kuehlt", number>;
           /** Very Low without its own removal [°C] and what each measure does to it [mK, < 0 = cooler] (deck chapter 5) */
           vlC: number[]; effect: Record<"trees" | "vegan" | "dac20" | "dac50" | "dac100" | "veganDac", number[]>;
           /** DACCS plans per build-out limit [%/a], and the vegan world's at 20 %/a: world capacity [Gt/a], cost
            *  [trillion € per year, median with the optimistic-pessimistic range], sum to 2100, €/t, year back at 1.5 °C */
           dac: Record<"20" | "50" | "100" | "vegan", {capGt: number[]; costMed: number[]; costLo: number[]; costHi: number[];
                                                     sumMed: number; eurT: number; back: number}>;
           vegan: {freeGha: number; coolsGha: number};
           plantYear: number; dacGrowthPct: number};
  sites: {name: string; lat: number; lon: number; color: string}[];
  scales: Record<string, Scale>;
  categories: {waldtyp: {key: string; label: string; color: string}[]};
  colors: {land: string; tooCold: string; unmeasured: string};
  reference: {i: number; j: number; dt2050: number; dt2100: number; net2100: number; dac2026: number | null; dac2045: number | null}[];
}

export interface Scale {
  stops: string[];
  domain: [number, number];
  mid?: number;
  gamma?: number;
  unit: string;
}

export interface Atlas {
  meta: Meta;
  f: Record<string, Float32Array | Uint8Array>;
  buildByCell: Map<number, number>;  // flat cell index → index into meta.build.cells
  cellsPerOwner: number[];           // cells per meta.build.owner id, counted once
}
