import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { loadAtlas, LoadError } from "@/data/load";
import type { Atlas } from "@/data/types";
import { layerById, type LayerId } from "@/model/layers";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { useMediaQuery } from "@/lib/useMediaQuery";
import { useLayoutMode, useViewportHeight } from "@/lib/useViewport";
import AtlasMap from "@/map/AtlasMap";
import { CompactSheet } from "@/ui/CompactSheet";
import { HoverReadout } from "@/ui/HoverReadout";
import { CellPanel } from "@/ui/CellPanel";
import { GlobalStrip } from "@/ui/GlobalStrip";
import { TitlePlate } from "@/ui/TitlePlate";
import { ToolColumn } from "@/ui/ToolColumn";
import { Dock } from "@/ui/Dock";
import { type Place } from "@/ui/PlaceSearch";
import { cellAt, cellCenter } from "@/map/lookup";

type Jump = { lon: number; lat: number; zoom?: number };

const WORLD = { lon: 10, lat: 25 };
const TOOLS_W = 64;      // the phone's tool column and its margin, in px
const DOCK_H = 120;      // until the dock has measured itself

/** The height of an element, followed as it changes (the dock grows a slider, the plate loses its hint). */
function useHeight<T extends HTMLElement>(fallback: number) {
  const ref = useRef<T>(null);
  const [h, setH] = useState(fallback);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const read = () => { if (el.offsetHeight > 0) setH(el.offsetHeight); };
    const ro = new ResizeObserver(read);
    ro.observe(el); read();
    return () => ro.disconnect();
  });
  return [ref, h] as const;
}

export default function App() {
  const t = useT();
  const s = useAtlas();
  const [atlas, setAtlas] = useState<Atlas | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hover, setHover] = useState<{ cell: number | null; x: number; y: number }>({ cell: null, x: 0, y: 0 });
  const [flyTo, setFlyTo] = useState<Jump | null>(null);
  const [snap, setSnap] = useState(0);
  const [dockRef, dockH] = useHeight<HTMLDivElement>(DOCK_H);
  const [plateRef, plateH] = useHeight<HTMLDivElement>(140);
  const prefersDark = useMediaQuery("(prefers-color-scheme: dark)");
  const dark = s.theme === "dark" || (s.theme === "system" && prefersDark);
  const mode = useLayoutMode();
  const vh = useViewportHeight();
  const wide = mode === "desktop";
  useEffect(() => { document.documentElement.classList.toggle("dark", dark); }, [dark]);
  useEffect(() => { document.documentElement.lang = s.lang; }, [s.lang]);
  useEffect(() => {
    loadAtlas().then(setAtlas).catch((e) => setError(e instanceof LoadError ? e.file : String(e)));
  }, []);
  // the first opened cell retires the first-visit hint
  useEffect(() => { if (s.cell !== null && !s.hintSeen) s.markHintSeen(); }, [s.cell, s.hintSeen]);

  // a layer that does not change over time has no year to play
  useEffect(() => { if (atlas && !layerById(s.layer).timed && s.playing) s.setPlaying(false); }, [atlas, s.layer, s.playing]);
  if (error) return <p role="alert" className="p-8">{t("app.loadError", { file: error })}</p>;
  if (!atlas) return <p className="p-8 text-inkMuted">{t("app.loading")}</p>;
  const layer = layerById(s.layer);
  const open = s.cell !== null;

  // the detail sheet's resting heights on a phone: half (map above it), almost full
  const snaps = [mode === "side" ? 0.82 : 0.55, 0.94];
  const bottom = !wide && open ? Math.round(snaps[snap] * vh) : dockH + 16;
  // upright, the plate takes the top of the screen: the globe centres below it (sideways it sits beside it)
  const insets = wide ? undefined : { top: mode === "sheet" ? plateH : 0, bottom: Math.min(bottom, Math.round(vh * 0.6)), right: TOOLS_W };

  // the globe fills the free part of a phone or tablet screen: ~1.0 at 360 px, ~2.1 on a 768 px tablet
  const freeSide = Math.min(window.innerWidth - TOOLS_W, vh - DOCK_H - (mode === "sheet" ? 140 : 0));
  const compactZoom = Math.max(0.8, Math.min(2.4, 1.0 + Math.log2(Math.max(200, freeSide) / 360)));
  const worldZoom = wide ? 2.1 : compactZoom;

  const openCell = (c: number, jump: Jump) => {
    s.setCell(c);
    if (!wide) setSnap(0);
    setFlyTo(jump);
  };
  const select = (c: number | null) => {
    if (c === null) { s.setCell(null); return; }
    if (wide) { s.setCell(c); return; }
    openCell(c, cellCenter(c));            // keep the zoom: bring the tapped cell above the sheet
  };
  const goTo = (p: Place) => {
    const c = cellAt(p.lon, p.lat);
    const land = c !== null && atlas.f.land[c];
    s.setCell(land ? c : null);
    if (!wide) setSnap(0);
    setFlyTo({ lon: p.lon, lat: p.lat, zoom: 4 });
  };
  const pickSite = (c: number, site: { lon: number; lat: number }) => openCell(c, { lon: site.lon, lat: site.lat, zoom: 4 });
  const recenter = () => { s.setCell(null); setFlyTo({ ...WORLD, zoom: worldZoom }); };
  const pickLayer = (id: LayerId) => s.setLayer(id);
  const closeCell = () => s.setCell(null);

  const map = (
    <AtlasMap atlas={atlas} layer={layer} year={s.year} cell={s.cell} onCell={select}
      onHover={wide ? (cell, x, y) => setHover({ cell, x, y }) : undefined} dark={dark} projection={s.projection}
      initialView={{ longitude: WORLD.lon, latitude: WORLD.lat, zoom: worldZoom }}
      sites={atlas.meta.sites} flyTo={flyTo} insets={insets} />
  );
  const tools = (
    <ToolColumn atlas={atlas} layer={layer} year={s.year} compact={!wide}
      onPlace={goTo} onRecenter={recenter} onSite={pickSite} />
  );
  const safeTop = { paddingTop: "max(0.75rem, env(safe-area-inset-top))" };

  if (!wide) {
    return (
      <div className="relative h-full w-full overflow-hidden">
        {map}
        <div ref={plateRef} className="pointer-events-none absolute left-0 top-0 z-10 p-3" style={{ ...safeTop, paddingLeft: "max(0.75rem, env(safe-area-inset-left))" }}>
          <TitlePlate atlas={atlas} layer={layer} compact />
        </div>
        {/* top right, beside the plate: clear of the detail sheet at every height it rests at */}
        <div className="pointer-events-none absolute right-0 top-0 z-10 p-3" style={{ ...safeTop, paddingRight: "max(0.75rem, env(safe-area-inset-right))" }}>
          {tools}
        </div>
        {open ? (
          // the details carry the dock on top, so the year stays in reach while reading a cell
          <CompactSheet title={t("panel.details")} snaps={snaps} snap={snap} onSnap={setSnap} vh={vh} inertAtPeek={false}
            peek={<Dock layer={layer} onLayer={pickLayer} bare />}>
            <CellPanel atlas={atlas} cell={s.cell!} year={s.year} onClose={closeCell} dense />
          </CompactSheet>
        ) : (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 flex justify-center px-3"
            style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))", paddingRight: mode === "side" ? TOOLS_W + 12 : undefined }}>
            <div ref={dockRef} className="w-full max-w-md"><Dock layer={layer} onLayer={pickLayer} /></div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="relative h-full w-full overflow-hidden">
      {map}
      <HoverReadout atlas={atlas} layer={layer} year={s.year} {...hover} />
      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex items-start justify-between gap-4 p-4" style={safeTop}>
        <TitlePlate atlas={atlas} layer={layer} compact={false} />
        {tools}
      </div>
      {open && (
        <section aria-label={t("panel.details")} className="panel absolute bottom-4 right-4 top-[4.75rem] z-10 w-96 overflow-auto p-4">
          <CellPanel atlas={atlas} cell={s.cell!} year={s.year} onClose={closeCell} />
        </section>
      )}
      {!open && (
        <div className="panel absolute bottom-4 right-4 z-10 w-[26rem] p-3"><GlobalStrip atlas={atlas} year={s.year} /></div>
      )}
      <div className="pointer-events-none absolute bottom-4 left-4 z-10 w-[24rem]" style={{ paddingBottom: "env(safe-area-inset-bottom)" }}>
        <Dock layer={layer} onLayer={pickLayer} />
      </div>
    </div>
  );
}
