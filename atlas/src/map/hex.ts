import { cellAt, LAT_MAX } from "./lookup";

/** Hexagon radius (centre to corner) in degrees: hexagons 0.5° across, one per 0.5° data cell. */
export const HEX_R_DEG = 0.5 / Math.sqrt(3);
/** Rows of the lattice are 1.5·R apart in latitude. */
export const HEX_ROW_DEG = 1.5 * HEX_R_DEG;

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
 * with the 0.5° cell under each centre. Rows sit at (j + ½)·1.5·R, so no centre falls on a cell edge; even rows
 * start 0.125° east of a cell edge, odd rows 0.25° further.
 */
export function hexCentres(bounds: Bounds, pad = 0): { lon: Float32Array; lat: Float32Array; cell: Int32Array } {
  const b = clampBounds(bounds);
  const latMin = Math.max(-LAT_MAX, b.south - pad), latMax = Math.min(LAT_MAX, b.north + pad);
  const lonMin = b.west - pad, lonMax = b.east + pad;
  const j0 = Math.ceil(latMin / HEX_ROW_DEG - 0.5), j1 = Math.floor(latMax / HEX_ROW_DEG - 0.5);
  const nRows = Math.max(0, j1 - j0 + 1), nCols = Math.floor((lonMax - lonMin) / 0.5) + 2;
  const lon = new Float32Array(nRows * nCols), lat = new Float32Array(nRows * nCols), cell = new Int32Array(nRows * nCols);
  let n = 0;
  for (let j = j0; j <= j1; j++) {
    const y = (j + 0.5) * HEX_ROW_DEG;
    const x0 = -180 + 0.125 + (j & 1 ? 0.25 : 0);
    for (let k = Math.ceil((lonMin - x0) / 0.5), x = x0 + 0.5 * k; x <= lonMax; k++, x = x0 + 0.5 * k) {
      const c = cellAt(wrapLon(x), y);
      if (c === null) continue;
      lon[n] = x; lat[n] = y; cell[n] = c; n++;
    }
  }
  return { lon: lon.subarray(0, n), lat: lat.subarray(0, n), cell: cell.subarray(0, n) };
}
