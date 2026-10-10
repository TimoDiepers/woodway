import { cellAt, cellCenter } from "@/map/lookup";

describe("lookup", () => {
  it("finds Aachen's cell and back", () => {
    const c = cellAt(6.08, 50.78)!;
    expect(c).toBe(Math.floor((90 - 50.78) / 0.5) * 720 + Math.floor((6.08 + 180) / 0.5));
    const { lon, lat } = cellCenter(c);
    expect(Math.abs(lon - 6.08)).toBeLessThan(0.25);
    expect(Math.abs(lat - 50.78)).toBeLessThan(0.25);
  });
  it("edges", () => {
    expect(cellAt(180, 0)).toBe(180 * 720 + 719);
    expect(cellAt(-180, 0)).toBe(180 * 720 + 0);
    expect(cellAt(0, 90)).toBe(360);
    expect(cellAt(0, -90)).toBe(359 * 720 + 360);
  });
  it("outside grid", () => {
    expect(cellAt(0, 91)).toBeNull();
    expect(cellAt(200, 0)).toBeNull();
    expect(cellAt(NaN, 0)).toBeNull();
  });
});
