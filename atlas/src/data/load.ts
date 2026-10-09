import type { Atlas, Meta } from "./types";

export class LoadError extends Error {
  constructor(public file: string, detail: string) {
    super(`${file}: ${detail}`);
  }
}

async function get(fetcher: typeof fetch, base: string, file: string): Promise<Response> {
  let res: Response;
  try {
    res = await fetcher(base + file);
  } catch (e) {
    throw new LoadError(file, String(e));
  }
  if (!res.ok) throw new LoadError(file, `HTTP ${res.status}`);
  return res;
}

export async function loadAtlas(base = "data/", fetcher: typeof fetch = fetch): Promise<Atlas> {
  const [metaRes, binRes] = await Promise.all([get(fetcher, base, "meta.json"), get(fetcher, base, "fields.bin")]);
  const meta = (await metaRes.json()) as Meta;
  const buf = await binRes.arrayBuffer();
  const f: Atlas["f"] = {};
  for (const [name, d] of Object.entries(meta.fields)) {
    f[name] = d.dtype === "f4" ? new Float32Array(buf, d.offset, d.length) : new Uint8Array(buf, d.offset, d.length);
  }
  const buildByCell = new Map<number, number>();
  meta.build.cells.forEach(([i, j], k) => buildByCell.set(i * meta.grid.nlon + j, k));
  return { meta, f, buildByCell };
}
