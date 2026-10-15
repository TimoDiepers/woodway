import type { Atlas, Scale } from "@/data/types";
import type { Key } from "@/i18n/useT";
import { closure, dacBuildMt, dacNet, deltaT, netShare, typeKey } from "./model";

export type LayerId = "forestType" | "area" | "sun" | "darker" | "cloud" | "light" | "deltaT" | "netShare" | "elec" | "dacNet" | "dacBuild";

export interface Layer {
  id: LayerId; group: "trees" | "dac"; label: Key; source: Key; timed: boolean;
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
  if (reason === "reason.unmeasured" || reason === "reason.noCloud") return c.unmeasured;
  return c.land;
}

export const BUILD_SCALE: Scale = { stops: ["#d6ecea", "#7cc2bc", "#2f9c98", "#0d4f57"], domain: [0, 60], unit: "Mt/a" };

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
const TREES: Key[] = ["reason.noTrees"], ALBEDO: Key[] = ["reason.noTrees", "reason.unmeasured"], COLD: Key[] = ["reason.tooCold"];

export const LAYERS: Layer[] = [
  { id: "forestType", group: "trees", label: "layer.forestType", source: "src.forestType", timed: false, kind: "cat",
    value: (at, c) => { const k = typeKey(at, c); return k ? at.meta.categories.waldtyp.findIndex((x) => x.key === at.meta.typeGroup[k]) : -1; },
    reason: noTrees, greys: TREES },
  { id: "area", group: "trees", label: "layer.area", source: "src.forestType", timed: false, kind: "num", scale: "flaeche", unit: "unit.area",
    value: (at, c) => (at.f.type[c] ? (100 * at.f.area[c]) / ROW_AREA[Math.floor(c / 720)] : NaN), reason: noTrees, greys: TREES },
  { id: "sun", group: "trees", label: "layer.sun", source: "src.albedo", timed: false, kind: "num", scale: "sonne", value: measured("sun"), reason: unmeasured, greys: ALBEDO },
  { id: "darker", group: "trees", label: "layer.darker", source: "src.albedo", timed: false, kind: "num", scale: "abdunkeln", value: measured("darker"), reason: unmeasured, greys: ALBEDO },
  { id: "cloud", group: "trees", label: "layer.cloud", source: "src.cloud", timed: false, kind: "num", scale: "wolken",
    value: (at, c) => (at.f.type[c] ? at.f.cloud[c] : NaN), reason: cloudless, greys: ["reason.noTrees", "reason.noCloud"] },
  { id: "light", group: "trees", label: "layer.light", source: "src.light", timed: true, kind: "num", scale: "licht",
    value: (at, c, y) => measured("light")(at, c) * closure(at, c, y), reason: unmeasured, greys: ALBEDO },
  { id: "deltaT", group: "trees", label: "layer.deltaT", source: "src.deltaT", timed: true, kind: "num", scale: "baumwirkung", unit: "unit.deltaT",
    value: (at, c, y) => deltaT(at, c, y) * 1e15, reason: noTrees, greys: TREES },
  { id: "netShare", group: "trees", label: "layer.netShare", source: "src.deltaT", timed: true, kind: "num", scale: "dac_netto", unit: "unit.netShare",
    value: (at, c, y) => netShare(at, c, y) * 100, reason: noTrees, greys: TREES },
  { id: "elec", group: "dac", label: "layer.elec", source: "src.dac", timed: false, kind: "num", scale: "strom",
    value: (at, c) => (at.f.dacOk[c] ? at.f.elec[c] : NaN), reason: tooCold, greys: COLD },
  { id: "dacNet", group: "dac", label: "layer.dacNet", source: "src.dac", timed: true, kind: "num", scale: "dac_netto",
    value: (at, c, y) => dacNet(at, c, y) * 100, reason: tooCold, greys: COLD },
  { id: "dacBuild", group: "dac", label: "layer.dacBuild", source: "src.build", timed: true, kind: "num", scale: "__build", unit: "unit.dacBuild",
    value: (at, c, y) => { const v = dacBuildMt(at, c, y); return v > 0 ? v : NaN; },
    reason: (at, c) => tooCold(at, c) ?? (at.f.land[c] ? "reason.noDac" : null), greys: ["reason.noDac", "reason.tooCold"] },
];

export const layerById = (id: LayerId): Layer => LAYERS.find((l) => l.id === id)!;
export const scaleOf = (at: Atlas, l: Layer): Scale | undefined => (l.scaleFn ? l.scaleFn(at) : l.scale === "__build" ? BUILD_SCALE : l.scale ? at.meta.scales[l.scale] : undefined);
