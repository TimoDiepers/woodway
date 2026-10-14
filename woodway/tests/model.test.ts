import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import type { Atlas } from "@/data/types";
import { deltaT, netShare, dacNet, dacBuildMt, coolsFrom, coolsUntil, cellSeries, yearIndex } from "@/model/model";

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (url: string) => new Response(readFileSync(path.join(DIR, path.basename(url))))) as unknown as typeof fetch;

let at: Atlas;
beforeAll(async () => { at = await loadAtlas("data/", diskFetch); });

describe("model", () => {
  it("reproduces the exporter's reference cells", () => {
    for (const r of at.meta.reference) {
      const c = r.i * 720 + r.j;
      expect(deltaT(at, c, 2050)).toBeCloseTo(r.dt2050, 20);
      expect(deltaT(at, c, 2100) / r.dt2100).toBeCloseTo(1, 5);
      expect(netShare(at, c, 2100) / r.net2100).toBeCloseTo(1, 5);
      expect(dacNet(at, c, 2026)).toBeCloseTo(r.dac2026, 5);
      expect(dacNet(at, c, 2045)).toBeCloseTo(r.dac2045, 5);
    }
  });
  it("ocean cell gives NaN and no series", () => {
    const ocean = 180 * 720 + 300;   // 0.25° S, 29.75° W: mid-Atlantic
    expect(at.f.land[ocean]).toBe(0);
    expect(Number.isNaN(deltaT(at, ocean, 2100))).toBe(true);
    expect(Number.isNaN(dacNet(at, ocean, 2050))).toBe(true);
    expect(cellSeries(at, ocean)).toBeNull();
    expect(dacBuildMt(at, ocean, 2080)).toBe(0);
  });
  it("clamps years", () => {
    expect(yearIndex(at, 1990)).toBe(0);
    expect(yearIndex(at, 2300)).toBe(at.meta.years.length - 1);
    const r = at.meta.reference[0];
    const c = r.i * 720 + r.j;
    expect(deltaT(at, c, 2300)).toBe(deltaT(at, c, 2100));
    expect(dacNet(at, c, 1990)).toBe(dacNet(at, c, 2026));
  });
  it("series and cooling year are consistent", () => {
    const r = at.meta.reference[0];
    const c = r.i * 720 + r.j;
    const s = cellSeries(at, c)!;
    expect(s.dt.at(-1)).toBeCloseTo(deltaT(at, c, 2100), 25);
    const y = coolsFrom(at, c);
    if (y !== null) expect(deltaT(at, c, y)).toBeLessThan(0);
  });
  it("a tree cools only if it still cools in 2100; cool-then-warm cells report the last cool year", () => {
    let cool = -1, flip = -1;
    for (let c = 0; c < at.f.type.length && (cool < 0 || flip < 0); c++) {
      if (!at.f.type[c]) continue;
      if (cool < 0 && deltaT(at, c, 2100) < 0) cool = c;
      if (flip < 0 && deltaT(at, c, 2100) >= 0 && at.meta.years.some((y) => deltaT(at, c, y) < 0)) flip = c;
    }
    expect(cool).toBeGreaterThanOrEqual(0);
    expect(flip).toBeGreaterThanOrEqual(0);
    expect(coolsFrom(at, cool)).not.toBeNull();
    expect(coolsUntil(at, cool)).toBeNull();
    expect(coolsFrom(at, flip)).toBeNull();
    const u = coolsUntil(at, flip)!;
    expect(deltaT(at, flip, u)).toBeLessThan(0);
    expect(deltaT(at, flip, u + 1)).toBeGreaterThanOrEqual(0);
  });
  it("DAC build-out appears where the optimisation puts it", () => {
    const [i, j] = at.meta.build.cells[0];
    const total = at.meta.build.years.map((y) => dacBuildMt(at, i * 720 + j, y));
    expect(Math.max(...total)).toBeGreaterThan(0);
  });
  it("an owner's cells add up to its capacity", () => {
    const b = at.meta.build, t = b.years.indexOf(2035), owner = b.capacityGt.findIndex((row) => row[t] > 0);
    let sum = 0;
    b.cells.forEach(([i, j], k) => { if (b.owner[k] === owner) sum += dacBuildMt(at, i * 720 + j, 2035); });
    expect(sum).toBeCloseTo(1000 * b.capacityGt[owner][t], 6);
    expect(sum).toBeGreaterThan(0);
  });
});
