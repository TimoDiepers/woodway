import { scaleColor, scaleT, hexToRgba } from "@/color/scale";
import type { Scale } from "@/data/types";
import { LAYERS } from "@/model/layers";
import { en } from "@/i18n/en";

const div: Scale = { stops: ["#000000", "#808080", "#ffffff"], domain: [-90, 45], mid: 0, unit: "K" };

describe("scales", () => {
  it("domain ends and the middle hit the stops", () => {
    expect(scaleColor(div, -90)).toEqual(hexToRgba("#000000"));
    expect(scaleColor(div, 0)).toEqual(hexToRgba("#808080"));
    expect(scaleColor(div, 45)).toEqual(hexToRgba("#ffffff"));
  });
  it("clamps outside the domain", () => {
    expect(scaleT(div, -500)).toBe(0);
    expect(scaleT(div, 500)).toBe(1);
  });
  it("gamma bends the ramp", () => {
    const g: Scale = { stops: ["#000000", "#ffffff"], domain: [0, 100], gamma: 0.5, unit: "%" };
    expect(scaleT(g, 25)).toBeCloseTo(0.5, 6);
  });
  it("every layer has labels in the dictionary", () => {
    for (const l of LAYERS) {
      expect(en[l.label]).toBeTruthy();
      expect(en[l.source]).toBeTruthy();
    }
  });
});
