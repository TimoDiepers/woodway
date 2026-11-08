import type { Atlas, Scale } from "@/data/types";
import type { Key } from "@/i18n/useT";
import { bestandUptake, cellTotal, closure, dacBuildMt, dacNet, deltaT, felling, netShare, typeKey, veganLand } from "./model";

export type LayerId = "forestType" | "area" | "sun" | "darker" | "cloud" | "light" | "deltaT" | "netShare" | "cellTotal"
  | "bestandUp" | "felling" | "veganLand" | "elec" | "dacNet" | "dacBuild";

/** The sections of the layer list, in the order of the talk: one tree, all reforestable land, today's forest, a
 *  vegan world, DAC. `ch` is the chapter colour of the section. */
export const GROUPS = [
  { g: "tree", ch: "baeume", label: "group.tree" },
  { g: "land", ch: "vergleich", label: "group.land" },
  { g: "today", ch: "baeume", label: "group.today" },
  { g: "vegan", ch: "dac", label: "group.vegan" },
  { g: "dac", ch: "dac", label: "group.dac" },
] as const;
export type GroupId = (typeof GROUPS)[number]["g"];
export const groupCh = (g: GroupId) => GROUPS.find((x) => x.g === g)!.ch;

export interface Layer {
  id: LayerId; group: GroupId; label: Key; source: Key; timed: boolean;
  /** follows the chosen planting year */
  planted?: boolean;
  kind: "num" | "cat"; scale?: string; unit?: Key | string;
  /** A scale computed from the data, instead of the named one (the talk fits the build-out scale to the built cells). */
  scaleFn?: (at: Atlas) => Scale;
  value(at: Atlas, cell: number, year: number): number;
  reason(at: Atlas, cell: number): Key | null;
  /** The reasons this layer can give for a grey cell, in legend order. */
  greys: Key[];
}

/** The grey a reason is drawn in: the deck's colours from meta.json. */
/** The greys on a dark page: land a step above the dark sea (#20282b), "not measured" and "too cold" a step above that. */
export const DARK_GREYS = { land: "#2e373a", unmeasured: "#3a4447", tooCold: "#46504f" } as const;

export function reasonColor(at: Atlas, reason: Key | null, dark = false): string {
  const c = dark ? DARK_GREYS : at.meta.colors;
  if (reason === "reason.tooCold") return c.tooCold;
  // a second grey where the layer has two reasons on land: not measured, no clouds, or today's forest that cools
  if (reason === "reason.unmeasured" || reason === "reason.noCloud" || reason === "reason.forestCools") return c.unmeasured;
  return c.land;
}

export const BUILD_SCALE: Scale = { stops: ["#d6ecea", "#7cc2bc", "#2f9c98", "#0d4f57"], domain: [0, 60], unit: "Mt/a" };
/** Whole cells [10⁻⁶ K per 10 000 km²]: planted land cools (green) or warms (orange), as the deck's "lohnt" scale,
 *  over the range single cells reach; today's forest and felling only cool, on one green ramp. */
export const AREA_SCALE: Scale = { stops: ["#14532d", "#3f8a55", "#a9cf9a", "#ece7d8", "#efb98a", "#d0632a", "#7d2e10"], domain: [-20, 20], mid: 0, unit: "10⁻⁶ K" };
export const COOL_SCALE: Scale = { stops: ["#0f3d22", "#2f7a45", "#7fb98a", "#cfe4c6", "#ece7d8"], domain: [-120, 0], unit: "10⁻⁶ K" };

// nbs.constants.A_EARTH_M2, as in nbs.grid.cell_area_m2
const R2 = 5.1006e14 / (4 * Math.PI);
export const ROW_AREA = Array.from({ length: 360 }, (_, i) => {
  const a = ((90 - 0.5 * i) * Math.PI) / 180, b = ((90 - 0.5 * (i + 1)) * Math.PI) / 180;
  return (2 * Math.PI * R2 * Math.abs(Math.sin(a) - Math.sin(b))) / 720;
});

const noTrees = (at: Atlas, c: number): Key | null => (at.f.land[c] && !at.f.type[c] ? "reason.noTrees" : null);
const tooCold = (at: Atlas, c: number): Key | null => (at.f.land[c] && !at.f.dacOk[c] ? "reason.tooCold" : null);
// Albedo fields only where the typical forest's albedo was measured locally (deck b8/b8a): elsewhere sun and
// darker are missing and light is gap-filled, so all three show the cell as reforestable but not measured.
const measured = (name: string) => (at: Atlas, c: number) => (at.f.type[c] && at.f.measured[c] ? at.f[name][c] : NaN);
const unmeasured = (at: Atlas, c: number): Key | null => noTrees(at, c) ?? (at.f.type[c] && !at.f.measured[c] ? "reason.unmeasured" : null);
// Cloud brightening only where Duveiller et al. 2021 retrieve the cloud change locally (deck b8i)
const cloudless = (at: Atlas, c: number): Key | null => noTrees(at, c) ?? (at.f.type[c] && !Number.isFinite(at.f.cloud[c]) ? "reason.noCloud" : null);
const notFreed = (at: Atlas, c: number): Key | null => (at.f.land[c] && !at.f.freeType[c] ? "reason.notFreed" : null);
const noForest = (at: Atlas, c: number): Key | null => (at.f.land[c] && !at.f.bType[c] ? "reason.noForestToday" : null);
const forestCools = (at: Atlas, c: number): Key | null => noForest(at, c) ?? (at.f.land[c] && !at.f.bFell[c] ? "reason.forestCools" : null);
const TREES: Key[] = ["reason.noTrees"], ALBEDO: Key[] = ["reason.noTrees", "reason.unmeasured"], COLD: Key[] = ["reason.tooCold"];

export const LAYERS: Layer[] = [
  { id: "forestType", group: "tree", label: "layer.forestType", source: "src.forestType", timed: false, kind: "cat",
    value: (at, c) => { const k = typeKey(at, c); return k ? at.meta.categories.waldtyp.findIndex((x) => x.key === at.meta.typeGroup[k]) : -1; },
    reason: noTrees, greys: TREES },
  { id: "area", group: "land", label: "layer.area", source: "src.forestType", timed: false, kind: "num", scale: "flaeche", unit: "unit.area",
    value: (at, c) => (at.f.type[c] ? (100 * at.f.area[c]) / ROW_AREA[Math.floor(c / 720)] : NaN), reason: noTrees, greys: TREES },
  { id: "sun", group: "tree", label: "layer.sun", source: "src.albedo", timed: false, kind: "num", scale: "sonne", value: measured("sun"), reason: unmeasured, greys: ALBEDO },
  { id: "darker", group: "tree", label: "layer.darker", source: "src.albedo", timed: false, kind: "num", scale: "abdunkeln", value: measured("darker"), reason: unmeasured, greys: ALBEDO },
  { id: "cloud", group: "tree", label: "layer.cloud", source: "src.cloud", timed: false, kind: "num", scale: "wolken",
    value: (at, c) => (at.f.type[c] ? at.f.cloud[c] : NaN), reason: cloudless, greys: ["reason.noTrees", "reason.noCloud"] },
  { id: "light", group: "tree", planted: true, label: "layer.light", source: "src.light", timed: true, kind: "num", scale: "licht",
    value: (at, c, y) => measured("light")(at, c) * closure(at, c, y), reason: unmeasured, greys: ALBEDO },
  { id: "deltaT", group: "tree", planted: true, label: "layer.deltaT", source: "src.deltaT", timed: true, kind: "num", scale: "baumwirkung", unit: "unit.deltaT",
    value: (at, c, y) => deltaT(at, c, y) * 1e15, reason: noTrees, greys: TREES },
  { id: "netShare", group: "tree", planted: true, label: "layer.netShare", source: "src.deltaT", timed: true, kind: "num", scale: "dac_netto", unit: "unit.netShare",
    value: (at, c, y) => netShare(at, c, y) * 100, reason: noTrees, greys: TREES },
  { id: "cellTotal", group: "land", planted: true, label: "layer.cellTotal", source: "src.cellTotal", timed: true, kind: "num", scaleFn: () => AREA_SCALE, unit: "unit.perArea",
    value: cellTotal, reason: noTrees, greys: TREES },
  { id: "bestandUp", group: "today", label: "layer.bestandUp", source: "src.bestand", timed: true, kind: "num", scaleFn: () => COOL_SCALE, unit: "unit.perArea",
    value: bestandUptake, reason: noForest, greys: ["reason.noForestToday"] },
  { id: "felling", group: "today", label: "layer.felling", source: "src.felling", timed: true, kind: "num", scaleFn: () => COOL_SCALE, unit: "unit.perArea",
    value: felling, reason: forestCools, greys: ["reason.forestCools", "reason.noForestToday"] },
  { id: "veganLand", group: "vegan", planted: true, label: "layer.veganLand", source: "src.veganLand", timed: true, kind: "num", scaleFn: () => AREA_SCALE, unit: "unit.perArea",
    value: veganLand, reason: notFreed, greys: ["reason.notFreed"] },
  { id: "elec", group: "dac", label: "layer.elec", source: "src.dac", timed: false, kind: "num", scale: "strom",
    value: (at, c) => (at.f.dacOk[c] ? at.f.elec[c] : NaN), reason: tooCold, greys: COLD },
  { id: "dacNet", group: "dac", label: "layer.dacNet", source: "src.dac", timed: true, kind: "num", scale: "dac_netto",
    value: (at, c, y) => dacNet(at, c, y) * 100, reason: tooCold, greys: COLD },
  { id: "dacBuild", group: "dac", label: "layer.dacBuild", source: "src.build", timed: true, kind: "num", scale: "__build", unit: "unit.dacBuild",
    value: (at, c, y) => { const v = dacBuildMt(at, c, y); return v > 0 ? v : NaN; },
    reason: (at, c) => tooCold(at, c) ?? (at.f.land[c] ? "reason.noDac" : null), greys: ["reason.noDac", "reason.tooCold"] },
];

export const layerById = (id: LayerId): Layer => LAYERS.find((l) => l.id === id)!;

/** The fields a layer reads (value and grey reasons), so the browser can fetch them first and know when it can draw. */
const BASE = ["land", "type"];
const FIELDS: Record<LayerId, string[]> = {
  forestType: BASE, area: [...BASE, "area"],
  sun: [...BASE, "measured", "sun"], darker: [...BASE, "measured", "darker"], cloud: [...BASE, "cloud"], light: [...BASE, "measured", "light"],
  deltaT: [...BASE, "a", "b"], netShare: [...BASE, "a", "b"], cellTotal: [...BASE, "a", "b", "area"],
  bestandUp: ["land", "bType", "bA", "bAge", "bB", "bArea"], felling: ["land", "bType", "bA", "bAge", "bB", "bArea", "bFell"],
  veganLand: ["land", "freeType", "freeA", "freeB", "freeArea"],
  elec: ["land", "dacOk", "elec"],
  dacNet: ["land", "dacOk", "dacNet2020", "dacNet2030", "dacNet2040", "dacNet2050", "dacNet2075", "dacNet2100"],
  dacBuild: ["land", "dacOk"],
};
export const fieldsOf = (id: LayerId): string[] => FIELDS[id];
/** Every field of the layer has arrived. */
export const layerReady = (at: Atlas, id: LayerId, plantYear = at.meta.years[0]): boolean =>
  FIELDS[id].every((n) => !!at.f[n])
  && (id !== "bestandUp" && id !== "felling" || !!at.meta.bestand.curves)
  && (!layerById(id).planted || plantYear === at.meta.years[0] || !!at.meta.curvesLater);
/** Every field has arrived (the cell panel reads them all). */
export const allReady = (at: Atlas): boolean => Object.keys(at.meta.fields).every((n) => !!at.f[n]) && !!at.meta.curvesLater && !!at.meta.bestand.curves;
export const scaleOf = (at: Atlas, l: Layer): Scale | undefined => (l.scaleFn ? l.scaleFn(at) : l.scale === "__build" ? BUILD_SCALE : l.scale ? at.meta.scales[l.scale] : undefined);
