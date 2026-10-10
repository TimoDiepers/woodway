import { cellColors, mercatorImage, IMG_W, IMG_H } from "@/map/paint";
import type { Atlas } from "@/data/types";
import { layerById, type Layer } from "@/model/layers";
import { hexToRgba } from "@/color/scale";

describe("mercatorImage", () => {
  it("equator row samples the equator cells, top row samples 85° N", () => {
    const colors = new Uint32Array(360 * 720);
    for (let i = 0; i < 360; i++) colors.fill(i + 1, i * 720, (i + 1) * 720);   // colour = row + 1
    const img = mercatorImage(colors);
    expect(img.length).toBe(IMG_W * IMG_H);
    expect(img[(IMG_H / 2) * IMG_W]).toBe(180 + 1);         // just south of the equator: row 180
    expect(img[0]).toBe(Math.floor((90 - 85) / 0.5) + 1);   // row 10
    expect(img[(IMG_H - 1) * IMG_W]).toBe(Math.floor((90 + 85) / 0.5) - 1 + 1);
  });
  it("columns sample their own longitude", () => {
    const colors = new Uint32Array(360 * 720);
    for (let j = 0; j < 720; j++) colors[180 * 720 + j] = j + 1;
    const img = mercatorImage(colors);
    const r = IMG_H / 2;
    for (const x of [0, 1, 2, 719, 1439]) expect(img[r * IMG_W + x]).toBe(Math.floor((x * 720) / IMG_W) + 1);
  });
});

describe("cellColors", () => {
  it("a category index outside the palette paints plain land, never a hole", () => {
    const n = 360 * 720;
    const at = {
      f: { land: new Uint8Array(n).fill(1), type: new Uint8Array(n) },
      meta: { colors: { land: "#cccccc", tooCold: "#aaaaaa", unmeasured: "#d3ccbc" }, categories: { waldtyp: [{ key: "x", label: "x", color: "#ff0000" }] }, scales: {} },
    } as unknown as Atlas;
    const base = layerById("forestType");
    const layer: Layer = { ...base, value: (_a, c) => (c === 0 ? 0 : c === 1 ? 5 : -1) };
    const out = cellColors(at, layer, 2100);
    const [r, g, b, a] = hexToRgba("#cccccc");
    const land = ((a << 24) | (b << 16) | (g << 8) | r) >>> 0;
    expect(out[0]).not.toBe(land);
    expect(out[1]).toBe(land);
    expect(out[2]).toBe(land);
  });
});
