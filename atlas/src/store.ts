import { create } from "zustand";
import type { LayerId } from "@/model/layers";

export type { LayerId } from "@/model/layers";
export type Theme = "light" | "dark" | "system";
export type Projection = "globe" | "mercator";

function stored<T extends string>(key: string, allowed: readonly T[], fallback: T): T {
  try {
    const v = localStorage.getItem(key) as T | null;
    return v && allowed.includes(v) ? v : fallback;
  } catch {
    return fallback;
  }
}
function save(key: string, v: string) {
  try { localStorage.setItem(key, v); } catch { /* private mode: keep it for this visit only */ }
}

interface AtlasState {
  lang: "en" | "de";
  setLang: (l: "en" | "de") => void;
  theme: Theme;
  setTheme: (t: Theme) => void;
  projection: Projection;
  setProjection: (p: Projection) => void;
  layer: LayerId;
  setLayer: (l: LayerId) => void;
  year: number;
  setYear: (y: number) => void;
  cell: number | null;
  setCell: (c: number | null) => void;
  playing: boolean;
  setPlaying: (p: boolean) => void;
  /** the first-visit line under the title; retired once a cell has been opened, back via the help panel */
  hintSeen: boolean;
  markHintSeen: () => void;
  resetHints: () => void;
}

export const useAtlas = create<AtlasState>((set) => ({
  lang: stored("atlas-lang", ["en", "de"] as const, "en"),
  setLang: (lang) => { save("atlas-lang", lang); document.documentElement.lang = lang; set({ lang }); },
  theme: stored("atlas-theme", ["light", "dark", "system"] as const, "system"),
  setTheme: (theme) => { save("atlas-theme", theme); set({ theme }); },
  projection: stored("atlas-projection", ["globe", "mercator"] as const, "globe"),
  setProjection: (projection) => { save("atlas-projection", projection); set({ projection }); },
  layer: "deltaT",
  setLayer: (layer) => set({ layer }),
  year: 2100,
  setYear: (year) => { if (Number.isFinite(year)) set({ year: Math.max(2026, Math.min(2100, Math.round(year))) }); },
  cell: null,
  setCell: (cell) => set({ cell }),
  playing: false,
  setPlaying: (playing) => set({ playing }),
  hintSeen: stored("atlas-hints", ["seen", "new"] as const, "new") === "seen",
  markHintSeen: () => { save("atlas-hints", "seen"); set({ hintSeen: true }); },
  resetHints: () => { save("atlas-hints", "new"); set({ hintSeen: false }); },
}));
