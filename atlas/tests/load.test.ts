import { loadAtlas, LoadError } from "@/data/load";

function fakeData() {
  const n = 360 * 720;
  const land = new Uint8Array(n).fill(1);
  const a = new Float32Array(n).fill(2);
  const buf = new Uint8Array(n + 4 * n);   // land at 0 (u1), a at n (n is a multiple of 4)
  buf.set(land, 0);
  buf.set(new Uint8Array(a.buffer), n);
  const meta = {
    version: 1, grid: { nlat: 360, nlon: 720, d: 0.5, lat0: 90, lon0: -180 }, years: [2026],
    fields: { land: { offset: 0, dtype: "u1", length: n }, a: { offset: n, dtype: "f4", length: n } },
    types: [], typeGroup: {}, curves: {}, dacYears: [],
    build: { years: [2026], countries: ["X"], cells: [[10, 20]], owner: [0], capacityGt: [[1]] },
    global: {}, sites: [], scales: {}, categories: { waldtyp: [] }, colors: { land: "#000", tooCold: "#000" }, reference: [],
  };
  return { meta, buf };
}

function fetcher(fail?: string): typeof fetch {
  const { meta, buf } = fakeData();
  return (async (url: string) => {
    if (fail && url.endsWith(fail)) return new Response("", { status: 404 });
    if (url.endsWith("meta.json")) return new Response(JSON.stringify(meta));
    return new Response(buf);
  }) as unknown as typeof fetch;
}

describe("loadAtlas", () => {
  it("decodes fields into typed arrays", async () => {
    const at = await loadAtlas("data/", fetcher());
    expect(at.f.land).toBeInstanceOf(Uint8Array);
    expect(at.f.a).toBeInstanceOf(Float32Array);
    expect(at.f.a[123]).toBe(2);
    expect(at.buildByCell.get(10 * 720 + 20)).toBe(0);
  });
  it("fetch failure names the file", async () => {
    await expect(loadAtlas("data/", fetcher("fields.bin"))).rejects.toMatchObject({ file: "fields.bin" });
    await expect(loadAtlas("data/", fetcher("fields.bin"))).rejects.toBeInstanceOf(LoadError);
  });
});
