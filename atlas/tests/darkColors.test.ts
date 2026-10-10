import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import type { Atlas } from "@/data/types";
import { layerById, reasonColor, scaleOf, DARK_GREYS } from "@/model/layers";
import { cellColors } from "@/map/paint";
import { hexToRgba, themedScale } from "@/color/scale";
import { cellAt } from "@/map/lookup";

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;
let at: Atlas;
beforeAll(async () => { at = await loadAtlas("data/", diskFetch); });
const pack = ([r, g, b, a]: number[]) => ((a << 24) | (b << 16) | (g << 8) | r) >>> 0;

describe("dark mode colours", () => {
  it("land without a value is drawn in the dark grey, not the paper grey", () => {
    const sahara = cellAt(10, 23)!;                    // land, no reforestable forest
    const light = cellColors(at, layerById("deltaT"), 2100, undefined, false);
    const dark = cellColors(at, layerById("deltaT"), 2100, undefined, true);
    expect(light[sahara]).toBe(pack(hexToRgba(at.meta.colors.land)));
    expect(dark[sahara]).toBe(pack(hexToRgba(DARK_GREYS.land)));
  });
  it("every reason has its own dark grey", () => {
    for (const r of ["reason.noTrees", "reason.tooCold", "reason.unmeasured"] as const)
      expect(reasonColor(at, r, true)).not.toBe(reasonColor(at, r, false));
  });
  it("the light middle of a diverging scale turns dark; its ends stay", () => {
    const sc = scaleOf(at, layerById("deltaT"))!;
    const d = themedScale(sc, true);
    const mid = Math.floor(sc.stops.length / 2);
    expect(d.stops[mid]).not.toBe(sc.stops[mid]);
    expect(d.stops[0]).toBe(sc.stops[0]);
    expect(d.stops.at(-1)).toBe(sc.stops.at(-1));
    expect(themedScale(sc, false)).toBe(sc);
  });
});
