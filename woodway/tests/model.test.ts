import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import type { Atlas } from "@/data/types";
import { deltaT, netShare, dacNet, dacBuildMt, coolsFrom, coolsUntil, cellSeries, yearIndex, setPlantYear, cellTotal, veganLand, bestandUptake, felling } from "@/model/model";

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (url: string) => new Response(readFileSync(path.join(DIR, url.replace(/^.*data\//, ""))))) as unknown as typeof fetch;

let at: Atlas;
beforeAll(async () => { at = await loadAtlas("data/", diskFetch); });

describe("model", () => {
  it("reproduces the exporter's reference cells", () => {
    for (const r of at.meta.reference) {
      const c = r.i * 720 + r.j;
      expect(deltaT(at, c, 2050) / r.dt2050).toBeCloseTo(1, 5);   // relative: float32 fields
      expect(deltaT(at, c, 2100) / r.dt2100).toBeCloseTo(1, 5);
      expect(netShare(at, c, 2100) / r.net2100).toBeCloseTo(1, 5);
      for (const [y, v] of [[2026, r.dac2026], [2045, r.dac2045]] as const) {
        if (v === null) expect(dacNet(at, c, y)).toBeNaN();   // no DAC in this cell
        else expect(dacNet(at, c, y)).toBeCloseTo(v, 5);
      }
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

// whole cells [10⁻⁶ K per 10 000 km²] back to K: the cell's area, as the model divides by it
const R2 = 5.1006e14 / (4 * Math.PI);
const cellM2 = (c: number) => { const i = Math.floor(c / 720), a = ((90 - 0.5 * i) * Math.PI) / 180, b = ((90 - 0.5 * (i + 1)) * Math.PI) / 180;
  return (2 * Math.PI * R2 * Math.abs(Math.sin(a) - Math.sin(b))) / 720; };
const worldMK = (f: (at: Atlas, c: number, y: number) => number, year: number) => {
  let s = 0;
  for (let c = 0; c < 360 * 720; c++) { const v = f(at, c, year); if (Number.isFinite(v)) s += (v * cellM2(c)) / 1e16; }
  return 1000 * s;
};

describe("whole cells, today's forest and the planting year", () => {
  it("felling and further growth add up to the exporter's world totals", () => {
    const k = yearIndex(at, 2100), b = at.meta.bestand;
    expect(worldMK(felling, 2100) / b.fellMK[k]).toBeCloseTo(1, 3);
    expect(worldMK(bestandUptake, 2100) / b.uptakeMK[k]).toBeCloseTo(1, 3);
    expect(b.fellMK[k]).toBeLessThan(0);      // felling where forest warms cools
    expect(b.uptakeMK[k]).toBeLessThan(0);    // further growth cools
  });
  it("felling only where forest warms; vegan land only where land is freed", () => {
    let fell = 0, free = 0;
    for (let c = 0; c < 360 * 720; c++) {
      if (Number.isFinite(felling(at, c, 2100))) { fell++; expect(at.f.bFell[c]).toBe(1); }
      if (Number.isFinite(veganLand(at, c, 2100))) { free++; expect(at.f.freeType[c]).toBeGreaterThan(0); }
    }
    expect(fell).toBeGreaterThan(1000);
    expect(free).toBeGreaterThan(1000);
  });
  it("the whole cell is the tree's effect times its trees", () => {
    const r = at.meta.reference[0], c = r.i * 720 + r.j;
    expect(cellTotal(at, c, 2100)).toBeCloseTo((deltaT(at, c, 2100) * (at.f.area[c] / (1e4 / 450)) / cellM2(c)) * 1e16, 6);
  });
  it("a later planting year shifts the tree: nothing before it, less by 2050, back to the reference with 2026", () => {
    const r = at.meta.reference[0], c = r.i * 720 + r.j;
    expect(at.meta.plantYears).toEqual([2026, 2031, 2036, 2041, 2046, 2051, 2056, 2061]);
    setPlantYear(2046);
    expect(deltaT(at, c, 2040)).toBe(0);
    expect(Math.abs(deltaT(at, c, 2050))).toBeLessThan(Math.abs(r.dt2050));
    setPlantYear(2026);
    expect(deltaT(at, c, 2050)).toBeCloseTo(r.dt2050, 20);
  });
});
