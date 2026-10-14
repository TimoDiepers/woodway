import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import type { Atlas } from "@/data/types";
import { coolingShare, medianDacNet, dacCapacityGt, buildP95 } from "@/talk/stats";

const DIR = path.resolve(__dirname, "../../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;
let at: Atlas;
beforeAll(async () => { at = await loadAtlas("data/", diskFetch); });

describe("talk stats", () => {
  it("cooling share in 2100 is the talk's 0.39 of 0.83 Gha", () => {
    const g = at.meta.global.areasGha;
    expect(coolingShare(at, 2100)).toBeCloseTo(g.kuehlt / g.alle, 2);
  });
  it("DAC median net share over the land area: 46 % in 2026, 91 % in 2040 (as the deck says)", () => {
    expect(Math.round(100 * medianDacNet(at, 2026))).toBe(46);
    expect(Math.round(100 * medianDacNet(at, 2040))).toBe(91);
  });
  it("DAC capacity follows the global path", () => {
    const k = at.meta.global.years.indexOf(2100);
    expect(dacCapacityGt(at, 2100)).toBe(at.meta.global.dacCapacityGt[k]);
  });
  it("95th percentile of the built cells' Mt/a in 2030 is a finite, positive scale top", () => {
    const p = buildP95(at, 2030);
    expect(p).toBeGreaterThan(0);
    expect(Number.isFinite(p)).toBe(true);
  });
});
