import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import type { Atlas } from "@/data/types";
import { coolingShare, medianDacNet, dacCapacityGt } from "@/talk/stats";

const DIR = path.resolve(__dirname, "../../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;
let at: Atlas;
beforeAll(async () => { at = await loadAtlas("data/", diskFetch); });

describe("talk stats", () => {
  it("cooling share in 2100 is the talk's 0.39 of 0.83 Gha", () => {
    const g = at.meta.global.areasGha;
    expect(coolingShare(at, 2100)).toBeCloseTo(g.kuehlt / g.alle, 2);
  });
  it("DAC median net share 2026 is 46 %", () => {
    expect(medianDacNet(at, 2026)).toBeCloseTo(0.4647, 3);
  });
  it("DAC capacity follows the global path", () => {
    const k = at.meta.global.years.indexOf(2100);
    expect(dacCapacityGt(at, 2100)).toBe(at.meta.global.dacCapacityGt[k]);
  });
});
