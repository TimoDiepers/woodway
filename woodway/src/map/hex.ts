import { cellAt, LAT_MAX } from "./lookup";

/** Hexagon radius (centre to corner) in degrees of longitude: hexagons 0.5° across, as wide as a data cell. */
export const HEX_R_DEG = 0.5 / Math.sqrt(3);
/** The same radius in Web-Mercator units (radians of x and y): the lattice is regular on the map. */
export const HEX_R_M = (HEX_R_DEG * Math.PI) / 180;
/** Rows of the lattice are 1.5·R apart in Mercator y. */
export const HEX_ROW_M = 1.5 * HEX_R_M;

export const mercY = (lat: number) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
export const latOfMercY = (y: number) => (Math.atan(Math.sinh(y)) * 180) / Math.PI;

export interface Bounds { west: number; south: number; east: number; north: number }

/**
 * The part of the world an image can cover: latitudes within ±85°, at most one world width, and its middle
 * longitude within [-180, 180) (an image source centred past the date line has no tile). A view across the
 * date line keeps its unwrapped longitudes, e.g. 170..190.
 */
export function clampBounds(b: Bounds): Bounds {
  const south = Math.max(-LAT_MAX, Math.min(b.south, b.north)), north = Math.min(LAT_MAX, Math.max(b.south, b.north));
  if (b.east - b.west >= 360) return { west: -180, south, east: 180, north };
  const shift = 360 * Math.floor(((b.west + b.east) / 2 + 180) / 360);
  return { west: b.west - shift, south, east: b.east - shift, north };
}

const wrapLon = (lon: number) => lon - 360 * Math.floor((lon + 180) / 360);

/**
 * Centres of the hexagon lattice inside the bounds (widened by `pad` degrees), row by row from south to north,
 * with the 0.5° cell under each centre. The lattice is regular in Web Mercator, as the talk's maps are on
 * screen: 0.5° of longitude across, rows at Mercator y = (j + ½)·1.5·R. Towards the poles rows come closer in
 * latitude, and several hexagons share a cell, as on the deck's Europe maps. Even rows start 0.125° east of a
 * cell edge, odd rows 0.25° further.
 */
export function hexCentres(bounds: Bounds, pad = 0): { lon: Float32Array; lat: Float32Array; cell: Int32Array } {
  const b = clampBounds(bounds);
  const latMin = Math.max(-LAT_MAX, b.south - pad), latMax = Math.min(LAT_MAX, b.north + pad);
  const lonMin = b.west - pad, lonMax = b.east + pad;
  const j0 = Math.ceil(mercY(latMin) / HEX_ROW_M - 0.5), j1 = Math.floor(mercY(latMax) / HEX_ROW_M - 0.5);
  const nRows = Math.max(0, j1 - j0 + 1), nCols = Math.floor((lonMax - lonMin) / 0.5) + 2;
  const lon = new Float32Array(nRows * nCols), lat = new Float32Array(nRows * nCols), cell = new Int32Array(nRows * nCols);
  let n = 0;
  for (let j = j0; j <= j1; j++) {
    const y = latOfMercY((j + 0.5) * HEX_ROW_M);
    const x0 = -180 + 0.125 + (j & 1 ? 0.25 : 0);
    for (let k = Math.ceil((lonMin - x0) / 0.5), x = x0 + 0.5 * k; x <= lonMax; k++, x = x0 + 0.5 * k) {
      const c = cellAt(wrapLon(x), y);
      if (c === null) continue;
      lon[n] = x; lat[n] = y; cell[n] = c; n++;
    }
  }
  return { lon: lon.subarray(0, n), lat: lat.subarray(0, n), cell: cell.subarray(0, n) };
}

/** The hexagon of the lattice under a point (as drawn by hexCentres): its centre, the nearest of the candidates in
 *  the two closest rows, measured in Web Mercator where the lattice is regular. Null off the lattice. */
export function hexAt(lon: number, lat: number): { lon: number; lat: number } | null {
  if (!Number.isFinite(lon) || !Number.isFinite(lat) || Math.abs(lat) > LAT_MAX) return null;
  const y = mercY(lat), x = (lon * Math.PI) / 180;
  const j0 = Math.floor(y / HEX_ROW_M - 0.5);
  let best: { lon: number; lat: number } | null = null, d = Infinity;
  for (const j of [j0, j0 + 1]) {
    const yc = (j + 0.5) * HEX_ROW_M, x0 = -180 + 0.125 + (j & 1 ? 0.25 : 0);
    const xc = x0 + 0.5 * Math.round((lon - x0) / 0.5), dx = (xc * Math.PI) / 180 - x, dy = yc - y;
    if (dx * dx + dy * dy < d) { d = dx * dx + dy * dy; best = { lon: xc, lat: latOfMercY(yc) }; }
  }
  return best && Math.abs(best.lat) <= LAT_MAX ? best : null;
}

/** The six corners of the hexagon around a lattice centre, closed, as [lon, lat]: pointy on top and bottom,
 *  0.25° to either side, as paint.ts draws them. */
export function hexRing(c: { lon: number; lat: number }): [number, number][] {
  const y = mercY(c.lat), r = HEX_R_M, lat = (dy: number) => latOfMercY(y + dy);
  const ring: [number, number][] = [[c.lon, lat(r)], [c.lon + 0.25, lat(r / 2)], [c.lon + 0.25, lat(-r / 2)],
    [c.lon, lat(-r)], [c.lon - 0.25, lat(-r / 2)], [c.lon - 0.25, lat(r / 2)]];
  return [...ring, ring[0]];
}
