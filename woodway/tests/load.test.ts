import { gzipSync } from "node:zlib";
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
    global: {}, bestand: {}, sites: [], scales: {}, categories: { waldtyp: [] }, colors: { land: "#000", tooCold: "#000", unmeasured: "#000" }, reference: [],
  };
  return { meta, buf };
}

type Serve = Partial<Record<string, () => Response | Promise<Response>>>;

/** Serves meta.json, fields.bin and one fields/<name>.bin.gz per field; `over` replaces single files (by their path
 *  under data/); logs what was asked for. */
function fetcher(over: Serve = {}, log: string[] = []): typeof fetch {
  const { meta, buf } = fakeData();
  const n = 360 * 720;
  const files: Serve = {
    "meta.json": () => new Response(JSON.stringify(meta)),
    "fields.bin": () => new Response(buf),
    "fields/land.bin.gz": () => new Response(gzipSync(buf.slice(0, n))),
    "fields/a.bin.gz": () => new Response(gzipSync(buf.slice(n, 5 * n))),
    "curves_later.json": () => new Response("{}"),
    "bestand_curves.json": () => new Response("{}"),
    ...over,
  };
  return (async (url: string) => {
    const name = url.replace(/^data\//, "");
    log.push(name);
    return (files[name] ?? (() => new Response("", { status: 404 })))();
  }) as unknown as typeof fetch;
}
const status404 = () => new Response("", { status: 404 });

describe("loadAtlas", () => {
  it("decodes each gzipped field into a typed array", async () => {
    const log: string[] = [];
    const at = await loadAtlas("data/", fetcher({ "fields.bin": status404 }, log));
    expect(log.sort()).toEqual(["bestand_curves.json", "curves_later.json", "fields/a.bin.gz", "fields/land.bin.gz", "meta.json"]);
    expect(at.f.land).toBeInstanceOf(Uint8Array);
    expect(at.f.a).toBeInstanceOf(Float32Array);
    expect(at.f.a[123]).toBe(2);
    expect(at.buildByCell.get(10 * 720 + 20)).toBe(0);
  });
  it("with `first`, resolves once those fields are there and brings the others after", async () => {
    let more!: (a: unknown) => void;
    const arrived = new Promise((r) => { more = r; });
    const at = await loadAtlas("data/", fetcher(), { first: ["land"], onMore: (a) => { if ((a as typeof at).f.a) more(a); } });
    expect(at.f.land).toBeInstanceOf(Uint8Array);
    await arrived;
    expect(at.f.a).toBeInstanceOf(Float32Array);
  });
  it("takes the plain fields when the browser cannot inflate", async () => {
    const DS = globalThis.DecompressionStream;
    // @ts-expect-error -- an old browser
    delete globalThis.DecompressionStream;
    try {
      const log: string[] = [];
      const at = await loadAtlas("data/", fetcher({}, log));
      expect(log.sort()).toEqual(["fields.bin", "meta.json"]);
      expect(at.f.a[5]).toBe(2);
    } finally {
      globalThis.DecompressionStream = DS;
    }
  });
  it("accepts fields the server already inflated (Content-Encoding: gzip)", async () => {
    const { buf } = fakeData();
    const at = await loadAtlas("data/", fetcher({ "fields/a.bin.gz": () => new Response(buf.slice(360 * 720)) }));
    expect(at.f.a[7]).toBe(2);
  });
  it("fetch failure names the file", async () => {
    await expect(loadAtlas("data/", fetcher({ "fields/a.bin.gz": status404 }))).rejects.toMatchObject({ file: "fields/a.bin.gz" });
    await expect(loadAtlas("data/", fetcher({ "meta.json": status404 }))).rejects.toMatchObject({ file: "meta.json" });
    await expect(loadAtlas("data/", fetcher({ "meta.json": status404 }))).rejects.toBeInstanceOf(LoadError);
  });
  it("a network error names the file", async () => {
    const down = () => Promise.reject(new TypeError("Failed to fetch"));
    await expect(loadAtlas("data/", fetcher({ "meta.json": down }))).rejects.toMatchObject({ file: "meta.json" });
  });
  it("malformed JSON (a dev server's index.html) names meta.json", async () => {
    const html = () => new Response("<!doctype html><html></html>", { headers: { "content-type": "text/html" } });
    const err = await loadAtlas("data/", fetcher({ "meta.json": html })).catch((e) => e);
    expect(err).toBeInstanceOf(LoadError);
    expect(err.file).toBe("meta.json");
  });
  it("broken or short field data names the field file", async () => {
    const junk = () => new Response(new Uint8Array([0x1f, 0x8b, 1, 2, 3]));
    await expect(loadAtlas("data/", fetcher({ "fields/a.bin.gz": junk }))).rejects.toMatchObject({ file: "fields/a.bin.gz" });
    const short = () => new Response(gzipSync(new Uint8Array(100)));
    const err = await loadAtlas("data/", fetcher({ "fields/a.bin.gz": short })).catch((e) => e);
    expect(err).toBeInstanceOf(LoadError);
    expect(err.file).toBe("fields/a.bin.gz");
  });
});
