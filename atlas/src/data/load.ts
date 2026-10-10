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

/** fields.bin.gz inflated in the browser. A server that already sent it with Content-Encoding: gzip hands
 *  over the plain bytes, which never start with the gzip magic (the first cell is ocean, 0). */
async function inflate(res: Response): Promise<ArrayBuffer> {
  const buf = await res.arrayBuffer();
  const b = new Uint8Array(buf, 0, Math.min(2, buf.byteLength));
  if (b[0] !== 0x1f || b[1] !== 0x8b) return buf;
  return new Response(new Response(buf).body!.pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
}

function views(meta: Meta, buf: ArrayBuffer): Atlas["f"] {
  const f: Atlas["f"] = {};
  for (const [name, d] of Object.entries(meta.fields)) {
    f[name] = d.dtype === "f4" ? new Float32Array(buf, d.offset, d.length) : new Uint8Array(buf, d.offset, d.length);
  }
  return f;
}

export async function loadAtlas(base = "data/", fetcher: typeof fetch = fetch): Promise<Atlas> {
  const gz = typeof globalThis.DecompressionStream === "function";
  const bin = gz ? "fields.bin.gz" : "fields.bin";
  const [meta, buf] = await Promise.all([
    get(fetcher, base, "meta.json", (r) => r.json() as Promise<Meta>),
    get(fetcher, base, bin, (r) => (gz ? inflate(r) : r.arrayBuffer())),
  ]);
  let f: Atlas["f"];
  try {
    f = views(meta, buf);
  } catch (e) {
    throw new LoadError(bin, String(e));
  }
  const buildByCell = new Map<number, number>();
  meta.build.cells.forEach(([i, j], k) => buildByCell.set(i * meta.grid.nlon + j, k));
  const cellsPerOwner: number[] = [];
  for (const o of meta.build.owner) cellsPerOwner[o] = (cellsPerOwner[o] ?? 0) + 1;
  return { meta, f, buildByCell, cellsPerOwner };
}
