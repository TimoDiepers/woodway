import { cellColors } from "@/map/paint";
import type { Atlas } from "@/data/types";
import { layerById, type Layer } from "@/model/layers";
import { hexToRgba } from "@/color/scale";

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
