import { useAtlas } from "@/store";

describe("store", () => {
  it("setYear clamps to 2026–2100 and ignores non-finite input", () => {
    const { setYear } = useAtlas.getState();
    setYear(2050.4);
    expect(useAtlas.getState().year).toBe(2050);
    setYear(NaN);
    expect(useAtlas.getState().year).toBe(2050);
    setYear(Infinity);
    expect(useAtlas.getState().year).toBe(2050);
    setYear(3000);
    expect(useAtlas.getState().year).toBe(2100);
  });
});
