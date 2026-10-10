import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import { layerById, scaleOf } from "@/model/layers";
import { scaleColor } from "@/color/scale";
import { cellAt, LAT_MAX } from "@/map/lookup";
import { hexCentres, HEX_R_DEG } from "@/map/hex";
import { paintHexView } from "@/map/paint";

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;
const wrap = (lon: number) => ((((lon + 180) % 360) + 360) % 360) - 180;
const rows = (lat: Float32Array) => [...new Set(lat)].sort((a, b) => a - b);

describe("hexCentres", () => {
  it("a 2°×2° box at the equator: one hexagon per cell, each centre in its own cell, a hex lattice", () => {
    const h = hexCentres({ west: 0, south: 0, east: 2, north: 2 });
    // √3·R = 0.5° across, 1.5·R = 0.433° between rows: 4 / (0.5 · 0.433) ≈ 18.5 hexagons
    expect(Math.abs(h.lon.length - 4 / (0.5 * 1.5 * HEX_R_DEG))).toBeLessThanOrEqual(2);
    for (let i = 0; i < h.lon.length; i++) {
      expect(h.lon[i]).toBeGreaterThanOrEqual(0); expect(h.lon[i]).toBeLessThanOrEqual(2);
      expect(h.lat[i]).toBeGreaterThanOrEqual(0); expect(h.lat[i]).toBeLessThanOrEqual(2);
      expect(h.cell[i]).toBe(cellAt(h.lon[i], h.lat[i]));
    }
    const ys = rows(h.lat);
    for (let k = 1; k < ys.length; k++) expect(ys[k] - ys[k - 1]).toBeCloseTo(1.5 * HEX_R_DEG, 4);
    // neighbouring rows are offset by a quarter degree, every row is spaced 0.5° across
    for (let k = 1; k < ys.length; k++) {
      const a = Math.min(...[...h.lon].filter((_, i) => h.lat[i] === ys[k - 1]));
      const b = Math.min(...[...h.lon].filter((_, i) => h.lat[i] === ys[k]));
      expect(Math.abs(a - b)).toBeCloseTo(0.25, 4);
    }
    const row0 = [...h.lon].filter((_, i) => h.lat[i] === ys[0]).sort((a, b) => a - b);
    for (let k = 1; k < row0.length; k++) expect(row0[k] - row0[k - 1]).toBeCloseTo(0.5, 4);
  });

  it("no centres beyond ±85°", () => {
    const h = hexCentres({ west: -180, south: -90, east: 180, north: 90 });
    expect(h.lon.length).toBeGreaterThan(200_000);
    let far = 0;
    for (let i = 0; i < h.lat.length; i++) far = Math.max(far, Math.abs(h.lat[i]));
    expect(far).toBeLessThanOrEqual(LAT_MAX);
  });

  it("bounds across ±180: centres past the date line take the cells of the other side", () => {
    const h = hexCentres({ west: 179, south: 0, east: 181, north: 1 });
    expect(h.lon.length).toBeGreaterThan(4);
    expect([...h.lon].some((x) => Math.abs(x) > 180)).toBe(true);   // unwrapped: one piece across the line
    for (let i = 0; i < h.lon.length; i++) expect(h.cell[i]).toBe(cellAt(wrap(h.lon[i]), h.lat[i]));
    // a view wider than the world is clamped to one world width
    const w = hexCentres({ west: -400, south: 0, east: 400, north: 1 });
    expect(Math.min(...w.lon)).toBeGreaterThanOrEqual(-180);
    expect(Math.max(...w.lon)).toBeLessThanOrEqual(180);
    expect(new Set(w.cell).size).toBe(w.cell.length);
  });
});

describe("paintHexView", () => {
  it("the hexagon centred in Aachen's cell is filled with that cell's ΔT colour, ocean stays clear", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const layer = layerById("deltaT");
    globalThis.ImageData ??= class { constructor(public data: Uint8ClampedArray, public width: number, public height: number) {} } as never;
    let put: ImageData | null = null;
    const ctx = { putImageData: (d: ImageData) => { put = d; } } as unknown as CanvasRenderingContext2D;
    const b = { west: 2.5, south: 49.5, east: 7.5, north: 53 }, w = 1000, h = 1100;
    paintHexView(ctx, w, h, b, at, layer, 2100);
    expect(put!.width).toBe(w); expect(put!.height).toBe(h);
    const img = new Uint32Array(put!.data.buffer);

    const Y = (lat: number) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
    const pixel = (lon: number, lat: number) =>
      img[Math.floor(((Y(b.north) - Y(lat)) / (Y(b.north) - Y(b.south))) * h) * w + Math.floor(((lon - b.west) / (b.east - b.west)) * w)];
    const aachen = cellAt(6.08, 50.78)!;
    const [r, g, bl, a] = scaleColor(scaleOf(at, layer)!, layer.value(at, aachen, 2100));
    const want = ((a << 24) | (bl << 16) | (g << 8) | r) >>> 0;
    const hx = hexCentres(b);
    const mine = [...hx.cell.keys()].filter((i) => hx.cell[i] === aachen);
    expect(mine.length).toBeGreaterThan(0);
    for (const i of mine) {
      // the centre, and points well inside the hexagon (not in the cell): the whole hexagon has the colour
      expect(pixel(hx.lon[i], hx.lat[i])).toBe(want);
      expect(pixel(hx.lon[i] + 0.2, hx.lat[i])).toBe(want);
      expect(pixel(hx.lon[i], hx.lat[i] + 0.8 * HEX_R_DEG)).toBe(want);
    }
    // hexagons over the sea (the North Sea in the north-west corner) are not painted
    const sea = [...hx.cell.keys()].filter((i) => !at.f.land[hx.cell[i]]);
    expect(sea.length).toBeGreaterThan(0);
    for (const i of sea) expect(pixel(hx.lon[i], hx.lat[i])).toBe(0);
  });
});
