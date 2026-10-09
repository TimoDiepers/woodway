import { mercatorImage, IMG_W, IMG_H } from "@/map/paint";

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
});
