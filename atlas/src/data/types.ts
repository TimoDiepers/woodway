export interface Meta {
  version: 1;
  grid: {nlat: number; nlon: number; d: number; lat0: number; lon0: number};
  years: number[];
  fields: Record<string, {offset: number; dtype: "f4" | "u1"; length: number}>;
  types: string[];
  typeGroup: Record<string, string>;
  curves: Record<string, {m: number[]; phiCo2: number[]; phiAlbUnit: number[]; dtCo2: number[]; dtAlbUnit: number[]}>;
  dacYears: number[];
  build: {years: number[]; countries: string[]; cells: [number, number][]; owner: number[]; capacityGt: number[][]};
  global: {years: number[]; need: number[]; afterTrees: number[]; afterDac: number[]; dacCapacityGt: number[];
           paths: Record<"alle" | "kuehlt" | "forst", number[]>; areasGha: Record<"alle" | "kuehlt", number>};
  sites: {name: string; lat: number; lon: number; color: string}[];
  scales: Record<string, Scale>;
  categories: {waldtyp: {key: string; label: string; color: string}[]};
  colors: {land: string; tooCold: string};
  reference: {i: number; j: number; dt2050: number; dt2100: number; net2100: number; dac2026: number; dac2045: number}[];
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
