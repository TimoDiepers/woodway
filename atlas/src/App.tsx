import { useEffect, useState, type ReactNode } from "react";
import { loadAtlas, LoadError } from "@/data/load";
import type { Atlas } from "@/data/types";
import { layerById, type LayerId } from "@/model/layers";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { useMediaQuery } from "@/lib/useMediaQuery";
import { useLayoutMode, useViewportHeight } from "@/lib/useViewport";
import AtlasMap from "@/map/AtlasMap";
import { Header } from "@/ui/Header";
import { CompactBar } from "@/ui/CompactBar";
import { CompactSheet } from "@/ui/CompactSheet";
import { LayerPicker } from "@/ui/LayerPicker";
import { SourceLine } from "@/ui/deck/SourceLine";
import { Legend } from "@/ui/Legend";
import { TimeSlider } from "@/ui/TimeSlider";
import { HoverReadout } from "@/ui/HoverReadout";
import { CellPanel } from "@/ui/CellPanel";
import { SiteButtons } from "@/ui/SiteButtons";
import { GlobalStrip } from "@/ui/GlobalStrip";
import { PlaceSearch, type Place } from "@/ui/PlaceSearch";
import { cellAt, cellCenter } from "@/map/lookup";

type Jump = { lon: number; lat: number; zoom?: number };

// phone layout: the top bar's height and the sheet's peek (legend + year), in px
const TOP_BAR = 60;
const PEEK = 150;   // until the sheet has measured its real peek
const SIDE_W = 320;

export default function App() {
  const t = useT();
  const s = useAtlas();
  const [atlas, setAtlas] = useState<Atlas | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hover, setHover] = useState<{ cell: number | null; x: number; y: number }>({ cell: null, x: 0, y: 0 });
  const [flyTo, setFlyTo] = useState<Jump | null>(null);
  const [snap, setSnap] = useState(0);
  const [peekPx, setPeekPx] = useState(PEEK);
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

  if (error) return <p role="alert" className="p-8">{t("app.loadError", { file: error })}</p>;
  if (!atlas) return <p className="p-8 text-inkMuted">{t("app.loading")}</p>;
  const layer = layerById(s.layer);
  const ch = layer.group === "dac" ? "dac" : "baeume";

  // the sheet's resting heights as fractions of the screen; the half step never sits below the peek
  const peekF = Math.min(0.45, peekPx / vh);
  const snaps = [peekF, Math.max(0.55, peekF + 0.1), 0.92];
  const insets = mode === "sheet" ? { top: TOP_BAR, bottom: Math.round(snaps[Math.min(snap, 1)] * vh) }
    : mode === "side" ? { top: 0, bottom: 0, right: SIDE_W } : undefined;

  // the globe fills the free part of a phone or tablet screen: ~1.0 at 360 px, ~2.1 on a 768 px tablet
  const freeSide = mode === "side" ? Math.min(window.innerWidth - SIDE_W, vh) : Math.min(window.innerWidth, vh - TOP_BAR - peekPx);
  const compactZoom = Math.max(0.8, Math.min(2.4, 1.0 + Math.log2(Math.max(200, freeSide) / 360)));
  const select = (c: number | null) => {
    s.setCell(c);
    if (mode === "desktop") return;
    if (c === null) { setSnap(0); return; }
    if (mode === "sheet" && snap === 0) setSnap(1);
    const { lon, lat } = cellCenter(c);
    setFlyTo({ lon, lat });                    // keep the zoom: bring the tapped cell above the sheet
  };
  const goTo = (p: Place) => {
    const c = cellAt(p.lon, p.lat);
    s.setCell(c !== null && atlas.f.land[c] ? c : null);
    if (mode === "sheet") setSnap(c !== null && atlas.f.land[c] ? 1 : 0);
    setFlyTo({ lon: p.lon, lat: p.lat, zoom: 4 });
  };
  const pickSite = (c: number, site: { lon: number; lat: number }) => {
    s.setCell(c);
    if (mode === "sheet") setSnap(1);
    setFlyTo({ lon: site.lon, lat: site.lat, zoom: 4 });
  };
  const pickLayer = (id: LayerId) => {
    s.setLayer(id);
    if (mode === "sheet" && s.cell === null) setSnap(0);   // show the map with its new layer
  };
  const closeCell = () => { s.setCell(null); if (mode === "sheet") setSnap(0); };

  const map = (
    <AtlasMap atlas={atlas} layer={layer} year={s.year} cell={s.cell} onCell={select}
      onHover={wide ? (cell, x, y) => setHover({ cell, x, y }) : undefined} dark={dark} projection={s.projection}
      initialView={{ longitude: 10, latitude: 25, zoom: wide ? 2.1 : compactZoom }}
      sites={atlas.meta.sites} flyTo={flyTo} insets={insets} />
  );

  if (mode !== "desktop") {
    // legend and year: what the map needs to be read, always in view
    const dock = (
      <div className="flex flex-col gap-2" data-ch={ch}>
        <Legend atlas={atlas} layer={layer} compact />
        <TimeSlider year={s.year} onYear={s.setYear} playing={s.playing} onPlaying={s.setPlaying} />
      </div>
    );
    const section = (title: string, body: ReactNode) => (
      <section className="mb-5">
        <h2 className="mb-1.5 font-serif text-[15px] font-semibold text-ink">{title}</h2>
        {body}
      </section>
    );
    const rest = (
      <>
        {s.cell !== null && (
          <div className="mb-5 border-b border-[var(--paper-line)] pb-4">
            <CellPanel atlas={atlas} cell={s.cell} year={s.year} onClose={closeCell} dense />
          </div>
        )}
        {section(t("sheet.layers"), <LayerPicker value={s.layer} onChange={pickLayer} />)}
        {section(t("sites.label"), <SiteButtons atlas={atlas} onPick={pickSite} bare />)}
        <section className="mb-5"><PlaceSearch onPick={goTo} /></section>
        <section className="mb-5"><GlobalStrip atlas={atlas} year={s.year} /></section>
        <SourceLine>{t(layer.source)}</SourceLine>
      </>
    );
    return (
      <div className="relative h-full w-full overflow-hidden">
        {map}
        {mode === "sheet" ? (
          <>
            <CompactBar />
            <CompactSheet title={t("app.title")} peek={dock} snaps={snaps} snap={snap} onSnap={setSnap} vh={vh} onTopHeight={setPeekPx}>{rest}</CompactSheet>
          </>
        ) : (
          <>
            <div className="absolute inset-y-0 left-0" style={{ right: SIDE_W }}><CompactBar /></div>
            <aside className="absolute inset-y-0 right-0 flex flex-col border-l border-[var(--paper-line)] bg-panel"
              style={{ width: SIDE_W, paddingTop: "env(safe-area-inset-top)", paddingRight: "env(safe-area-inset-right)" }}>
              <div className="shrink-0 border-b border-[var(--paper-line)] p-3">{dock}</div>
              <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-3" style={{ paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}>{rest}</div>
            </aside>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="relative h-full w-full overflow-hidden">
      {map}
      <HoverReadout atlas={atlas} layer={layer} year={s.year} {...hover} />
      <div className="pointer-events-none absolute inset-x-0 top-0 p-4" style={{ paddingTop: "max(1rem, env(safe-area-inset-top))" }}>
        <Header />
        <div className="pointer-events-auto mt-2"><SiteButtons atlas={atlas} onPick={pickSite} /></div>
      </div>
      <aside className="panel absolute left-4 top-32 max-h-[calc(100%-13.5rem)] w-60 overflow-auto p-3">
        <div className="mb-3"><PlaceSearch onPick={goTo} /></div>
        <LayerPicker value={s.layer} onChange={pickLayer} />
        <div className="mt-4 border-t border-[var(--paper-line)] pt-3"><Legend atlas={atlas} layer={layer} /></div>
      </aside>
      {s.cell !== null && (
        <aside className="panel absolute right-4 top-32 bottom-4 w-96 overflow-auto p-4">
          <CellPanel atlas={atlas} cell={s.cell} year={s.year} onClose={closeCell} />
        </aside>
      )}
      {s.cell === null && (
        <div className="panel absolute bottom-4 right-4 w-[26rem] p-3"><GlobalStrip atlas={atlas} year={s.year} /></div>
      )}
      <div className="absolute bottom-4 left-4 w-[22rem]" style={{ paddingBottom: "env(safe-area-inset-bottom)" }}>
        <div className="panel px-3 py-2" data-ch={ch}>
          <TimeSlider year={s.year} onYear={s.setYear} playing={s.playing} onPlaying={s.setPlaying} />
        </div>
      </div>
    </div>
  );
}
