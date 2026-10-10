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

import { focusColors } from "@/map/paint";

describe("focusColors", () => {
  it("fades every cell but the selected one, keeps holes holes, and changes nothing without a selection", () => {
    const opaque = 0xff336699 >>> 0;
    const colors = new Uint32Array([opaque, opaque, 0]);
    expect(focusColors(colors, null)).toBe(colors);
    const out = focusColors(colors, 1);
    expect(out[1]).toBe(opaque);
    expect(out[0] >>> 24).toBeLessThan(0x80);          // faded
    expect(out[0] & 0xffffff).toBe(opaque & 0xffffff); // same colour, only see-through
    expect(out[2]).toBe(0);
    expect(colors[0]).toBe(opaque);                    // the cached colours stay untouched
  });
});
