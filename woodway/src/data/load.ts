import type { Atlas, Meta } from "./types";

export class LoadError extends Error {
  constructor(public file: string, detail: string) {
    super(`${file}: ${detail}`);
  }
}

/** Fetch one file and decode it; any failure (network, HTTP status, parse, decode) names the file. */
async function get<T>(fetcher: typeof fetch, base: string, file: string, decode: (res: Response) => Promise<T>): Promise<T> {
  let res: Response;
  try {
    res = await fetcher(base + file);
  } catch (e) {
    throw new LoadError(file, String(e));
  }
  if (!res.ok) throw new LoadError(file, `HTTP ${res.status}`);
  try {
    return await decode(res);
  } catch (e) {
    throw new LoadError(file, String(e));
  }
}

/** A gzipped file inflated in the browser. A server that already sent it with Content-Encoding: gzip hands over
 *  the plain bytes, which never start with the gzip magic (a field's first cell is ocean, 0). */
async function inflate(res: Response): Promise<ArrayBuffer> {
  const buf = await res.arrayBuffer();
  const b = new Uint8Array(buf, 0, Math.min(2, buf.byteLength));
  if (b[0] !== 0x1f || b[1] !== 0x8b) return buf;
  return new Response(new Response(buf).body!.pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
}

function view(name: string, d: Meta["fields"][string], buf: ArrayBuffer, offset = 0): Float32Array | Uint8Array {
  const a = d.dtype === "f4" ? new Float32Array(buf, offset, d.length) : new Uint8Array(buf, offset, d.length);
  if (a.length !== d.length) throw new Error(`${name}: ${a.length} of ${d.length} cells`);
  return a;
}

/**
 * meta.json, then the fields. Each field is its own small file (data/fields/<name>.bin.gz): with `first`, the
 * promise resolves once those have arrived (the layer on screen) and the others follow in the background, each
 * set reported by `onMore` with the atlas as a new object (the same arrays, more of them); without `first` it waits
 * for all. Without DecompressionStream all fields come at once from fields.bin.
 */
export async function loadAtlas(base = "data/", fetcher: typeof fetch = fetch,
  opts: { first?: string[]; onMore?: (at: Atlas) => void; after?: Promise<unknown>; firstAfter?: Promise<unknown> } = {}): Promise<Atlas> {
  const meta = await get(fetcher, base, "meta.json", (r) => r.json() as Promise<Meta>);
  const f: Atlas["f"] = {};
  const buildByCell = new Map<number, number>();
  meta.build.cells.forEach(([i, j], k) => buildByCell.set(i * meta.grid.nlon + j, k));
  const cellsPerOwner: number[] = [];
  for (const o of meta.build.owner) cellsPerOwner[o] = (cellsPerOwner[o] ?? 0) + 1;
  const atlas: Atlas = { meta, f, buildByCell, cellsPerOwner };

  if (typeof globalThis.DecompressionStream !== "function") {
    const buf = await get(fetcher, base, "fields.bin", (r) => r.arrayBuffer());
    try {
      for (const [name, d] of Object.entries(meta.fields)) f[name] = view(name, d, buf, d.offset);
    } catch (e) {
      throw new LoadError("fields.bin", String(e));
    }
    return atlas;
  }
  const one = (name: string) => {
    const file = `fields/${name}.bin.gz`;
    return get(fetcher, base, file, inflate).then((buf) => {
      try { f[name] = view(name, meta.fields[name], buf); } catch (e) { throw new LoadError(file, String(e)); }
    });
  };
  // the curves of later planting years and of today's forest: not needed for the first picture
  const extras = () => Promise.all([
    get(fetcher, base, "curves_later.json", (r) => r.json()).then((v) => { meta.curvesLater = v; }),
    get(fetcher, base, "bestand_curves.json", (r) => r.json()).then((v) => { meta.bestand.curves = v; }),
  ]);
  const all = Object.keys(meta.fields);
  if (!opts.first) {
    await Promise.all([...all.map(one), extras()]);
    return atlas;
  }
  const first = opts.first.filter((n) => n in meta.fields);
  await opts.firstAfter;   // the world's shape before the data, on a slow connection
  await Promise.all(first.map(one));
  // the rest after it, a few at a time, so they share the line with nothing the screen waits for
  const rest = all.filter((n) => !first.includes(n));
  (async () => {
    await opts.after;   // what the screen shows first (land, lines, names) gets the line before the rest
    await extras().catch(() => {});
    opts.onMore?.({ ...atlas });
    for (let k = 0; k < rest.length; k += 4) {
      await Promise.all(rest.slice(k, k + 4).map(one)).catch(() => {});
      opts.onMore?.({ ...atlas });
    }
  })();
  return atlas;
}
