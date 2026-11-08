import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import type { Atlas } from "@/data/types";
import { LAYERS, layerById, reasonColor } from "@/model/layers";
import { cellColors } from "@/map/paint";
import { hexToRgba } from "@/color/scale";
import { en } from "@/i18n/en";
import { de } from "@/i18n/de";

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (url: string) => new Response(readFileSync(path.join(DIR, url.replace(/^.*data\//, ""))))) as unknown as typeof fetch;

let at: Atlas;
beforeAll(async () => { at = await loadAtlas("data/", diskFetch); });

const pack = (hex: string) => { const [r, g, b, a] = hexToRgba(hex); return ((a << 24) | (b << 16) | (g << 8) | r) >>> 0; };

describe("layers", () => {
  it("every land cell without a value has a named reason, in every layer and year", () => {
    for (const l of LAYERS) {
      for (const y of l.timed ? [2026, 2063, 2100] : [2100]) {
        let missing = 0;
        for (let c = 0; c < 360 * 720; c++) {
          if (!at.f.land[c]) continue;
          const v = l.value(at, c, y);
          const bad = l.kind === "cat" ? v < 0 : !Number.isFinite(v);
          if (bad && l.reason(at, c) === null) missing++;
        }
        expect(missing, `${l.id} ${y}`).toBe(0);
      }
    }
  });
  it("albedo layers show only locally measured cells and name the others", () => {
    let c = 0;
    while (!(at.f.type[c] && !at.f.measured[c])) c++;
    for (const id of ["sun", "darker", "light"] as const) {
      const l = layerById(id);
      expect(Number.isNaN(l.value(at, c, 2100)), id).toBe(true);
      expect(l.reason(at, c), id).toBe("reason.unmeasured");
      expect(l.greys).toContain("reason.unmeasured");
      expect(cellColors(at, l, 2100)[c]).toBe(pack(at.meta.colors.unmeasured));
    }
    expect(reasonColor(at, "reason.unmeasured")).toBe("#d3ccbc");
    expect(en["reason.unmeasured"]).toBe("reforestable, not measured locally");
    expect(de["reason.unmeasured"]).toBe("wiederbewaldbar, nicht lokal gemessen");
  });
  it("the cloud layer shows the local cloud retrieval in %-points, both signs, and greys the rest as not measured", () => {
    const l = layerById("cloud");
    let c = 0;
    while (!(at.f.type[c] && !Number.isFinite(at.f.cloud[c]))) c++;
    expect(l.reason(at, c)).toBe("reason.noCloud");
    expect(cellColors(at, l, 2100)[c]).toBe(pack(at.meta.colors.unmeasured));
    let pos = 0, neg = 0;
    for (let k = 0; k < 360 * 720; k++) { const v = l.value(at, k, 2100); if (v > 0) pos++; else if (v < 0) neg++; }
    expect(pos).toBeGreaterThan(neg);
    expect(neg).toBeGreaterThan(0);   // in places forest has fewer clouds than open land
    expect(at.meta.scales.wolken.mid).toBe(0);
  });
  it("extra absorbed light grows with canopy closure: none at planting, mature value times f(t) later", () => {
    let c = 0;
    while (!(at.f.type[c] && at.f.measured[c])) c++;
    const l = layerById("light"), f = at.meta.curves[at.meta.types[at.f.type[c] - 1]].closure;
    expect(l.timed).toBe(true);
    expect(l.value(at, c, 2026)).toBe(0);
    expect(l.value(at, c, 2100)).toBeCloseTo(at.f.light[c] * f.at(-1)!, 6);
    expect(Math.abs(l.value(at, c, 2100))).toBeLessThan(Math.abs(at.f.light[c]));
  });
  it("the build-out names both grey reasons", () => {
    expect(layerById("dacBuild").greys).toEqual(["reason.noDac", "reason.tooCold"]);
  });
});
