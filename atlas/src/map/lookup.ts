export const LAT_MAX = 85;

export function cellAt(lon: number, lat: number): number | null {
  if (!Number.isFinite(lon) || !Number.isFinite(lat) || Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
  const i = Math.min(359, Math.floor((90 - lat) / 0.5));
  const j = Math.min(719, Math.floor((lon + 180) / 0.5));
  return i * 720 + j;
}

export function cellCenter(cell: number): { lon: number; lat: number } {
  const i = Math.floor(cell / 720), j = cell % 720;
  return { lon: -180 + 0.5 * j + 0.25, lat: 90 - 0.5 * i - 0.25 };
}
