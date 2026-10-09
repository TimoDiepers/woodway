import type { Atlas, Scale } from "@/data/types";
import type { Key } from "@/i18n/useT";
import { dacBuildMt, dacNet, deltaT, netShare, typeKey } from "./model";

export type LayerId = "forestType" | "area" | "sun" | "darker" | "light" | "deltaT" | "netShare" | "elec" | "dacNet" | "dacBuild";

export interface Layer {
  id: LayerId; group: "trees" | "dac"; label: Key; source: Key; timed: boolean;
  kind: "num" | "cat"; scale?: string; unit?: Key | string;
  value(at: Atlas, cell: number, year: number): number;
  reason(at: Atlas, cell: number): Key | null;
}

export const BUILD_SCALE: Scale = { stops: ["#d6ecea", "#7cc2bc", "#2f9c98", "#0d4f57"], domain: [0, 60], unit: "Mt/a" };

// nbs.constants.A_EARTH_M2, as in nbs.grid.cell_area_m2
const R2 = 5.1006e14 / (4 * Math.PI);
const ROW_AREA = Array.from({ length: 360 }, (_, i) => {
  const a = ((90 - 0.5 * i) * Math.PI) / 180, b = ((90 - 0.5 * (i + 1)) * Math.PI) / 180;
  return (2 * Math.PI * R2 * Math.abs(Math.sin(a) - Math.sin(b))) / 720;
});

const noTrees = (at: Atlas, c: number): Key | null => (at.f.land[c] && !at.f.type[c] ? "reason.noTrees" : null);
const tooCold = (at: Atlas, c: number): Key | null => (at.f.land[c] && !at.f.dacOk[c] ? "reason.tooCold" : null);
const field = (name: string, k = 1) => (at: Atlas, c: number) => (at.f.type[c] ? at.f[name][c] * k : NaN);

export const LAYERS: Layer[] = [
  { id: "forestType", group: "trees", label: "layer.forestType", source: "src.forestType", timed: false, kind: "cat",
    value: (at, c) => { const k = typeKey(at, c); return k ? at.meta.categories.waldtyp.findIndex((x) => x.key === at.meta.typeGroup[k]) : -1; },
    reason: noTrees },
  { id: "area", group: "trees", label: "layer.area", source: "src.forestType", timed: false, kind: "num", scale: "flaeche", unit: "unit.area",
    value: (at, c) => (at.f.type[c] ? (100 * at.f.area[c]) / ROW_AREA[Math.floor(c / 720)] : NaN), reason: noTrees },
  { id: "sun", group: "trees", label: "layer.sun", source: "src.albedo", timed: false, kind: "num", scale: "sonne", value: field("sun"), reason: noTrees },
  { id: "darker", group: "trees", label: "layer.darker", source: "src.albedo", timed: false, kind: "num", scale: "abdunkeln", value: field("darker"), reason: noTrees },
  { id: "light", group: "trees", label: "layer.light", source: "src.albedo", timed: false, kind: "num", scale: "licht", value: field("light"), reason: noTrees },
  { id: "deltaT", group: "trees", label: "layer.deltaT", source: "src.deltaT", timed: true, kind: "num", scale: "baumwirkung", unit: "unit.deltaT",
    value: (at, c, y) => deltaT(at, c, y) * 1e15, reason: noTrees },
  { id: "netShare", group: "trees", label: "layer.netShare", source: "src.deltaT", timed: true, kind: "num", scale: "dac_netto", unit: "unit.netShare",
    value: (at, c, y) => netShare(at, c, y) * 100, reason: noTrees },
  { id: "elec", group: "dac", label: "layer.elec", source: "src.dac", timed: false, kind: "num", scale: "strom",
    value: (at, c) => (at.f.dacOk[c] ? at.f.elec[c] : NaN), reason: tooCold },
  { id: "dacNet", group: "dac", label: "layer.dacNet", source: "src.dac", timed: true, kind: "num", scale: "dac_netto",
    value: (at, c, y) => dacNet(at, c, y) * 100, reason: tooCold },
  { id: "dacBuild", group: "dac", label: "layer.dacBuild", source: "src.build", timed: true, kind: "num", scale: "__build", unit: "unit.dacBuild",
    value: (at, c, y) => { const v = dacBuildMt(at, c, y); return v > 0 ? v : NaN; },
    reason: (at, c) => tooCold(at, c) ?? (at.f.land[c] ? "reason.noDac" : null) },
];

export const layerById = (id: LayerId): Layer => LAYERS.find((l) => l.id === id)!;
export const scaleOf = (at: Atlas, l: Layer): Scale | undefined => (l.scale === "__build" ? BUILD_SCALE : l.scale ? at.meta.scales[l.scale] : undefined);
