import { useEffect, useState } from "react";
import { loadAtlas, LoadError } from "@/data/load";
import type { Atlas } from "@/data/types";
import { layerById, type LayerId } from "@/model/layers";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { useMediaQuery } from "@/lib/useMediaQuery";
import AtlasMap from "@/map/AtlasMap";
import { Header } from "@/ui/Header";
import { LayerPicker } from "@/ui/LayerPicker";
import { SourceLine } from "@/ui/deck/SourceLine";
import { Legend } from "@/ui/Legend";
import { TimeSlider } from "@/ui/TimeSlider";
import { HoverReadout } from "@/ui/HoverReadout";
import { CellPanel } from "@/ui/CellPanel";
import { SiteButtons } from "@/ui/SiteButtons";
import { GlobalStrip } from "@/ui/GlobalStrip";
import { MobileSheet } from "@/ui/MobileSheet";

export default function App() {
  const t = useT();
  const s = useAtlas();
  const [atlas, setAtlas] = useState<Atlas | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hover, setHover] = useState<{ cell: number | null; x: number; y: number }>({ cell: null, x: 0, y: 0 });
  const [flyTo, setFlyTo] = useState<{ lon: number; lat: number } | null>(null);
  const prefersDark = useMediaQuery("(prefers-color-scheme: dark)");
  const dark = s.theme === "dark" || (s.theme === "system" && prefersDark);
  const wide = useMediaQuery("(min-width: 768px)");
  useEffect(() => { document.documentElement.classList.toggle("dark", dark); }, [dark]);
  useEffect(() => { document.documentElement.lang = s.lang; }, [s.lang]);
  useEffect(() => {
    loadAtlas().then(setAtlas).catch((e) => setError(e instanceof LoadError ? e.file : String(e)));
  }, []);

  if (error) return <p role="alert" className="p-8">{t("app.loadError", { file: error })}</p>;
  if (!atlas) return <p className="p-8 text-inkMuted">{t("app.loading")}</p>;
  const layer = layerById(s.layer);
  const pick = (id: LayerId) => s.setLayer(id);
  const ch = layer.group === "dac" ? "dac" : "baeume";
  return (
    <div className="relative h-full w-full overflow-hidden">
      <AtlasMap atlas={atlas} layer={layer} year={s.year} cell={s.cell} onCell={s.setCell}
        onHover={wide ? (cell, x, y) => setHover({ cell, x, y }) : undefined} dark={dark} initialView={{ longitude: 10, latitude: 25, zoom: wide ? 2.1 : 1.6 }} sites={atlas.meta.sites} flyTo={flyTo} />
      {wide && <HoverReadout atlas={atlas} layer={layer} year={s.year} {...hover} />}
      <div className="pointer-events-none absolute inset-x-0 top-0 p-4" style={{ paddingTop: "max(1rem, env(safe-area-inset-top))" }}>
        <Header />
        <div className="pointer-events-auto mt-2"><SiteButtons atlas={atlas} onPick={(c, site) => { s.setCell(c); setFlyTo({ lon: site.lon, lat: site.lat }); }} /></div>
      </div>
      <aside className="panel absolute left-4 top-32 max-h-[calc(100%-13.5rem)] w-60 overflow-auto p-3 max-md:hidden">
        <LayerPicker value={s.layer} onChange={pick} />
        <div className="mt-4 border-t border-[var(--paper-line)] pt-3"><Legend atlas={atlas} layer={layer} /></div>
      </aside>
      {wide && s.cell !== null && (
        <aside className="panel absolute right-4 top-32 bottom-4 w-96 overflow-auto p-4">
          <CellPanel atlas={atlas} cell={s.cell} year={s.year} onClose={() => s.setCell(null)} />
        </aside>
      )}
      {wide && s.cell === null && (
        <div className="panel absolute bottom-4 right-4 w-[26rem] p-3"><GlobalStrip atlas={atlas} year={s.year} /></div>
      )}
      <div className="absolute bottom-4 left-4 right-4 max-md:bottom-[calc(35dvh+0.5rem)] md:right-auto md:w-[22rem]" style={wide ? { paddingBottom: "env(safe-area-inset-bottom)" } : undefined}>
        {!wide && <div className="panel mb-3 p-3"><Legend atlas={atlas} layer={layer} compact /></div>}
        <div className="panel px-3 py-2" data-ch={ch}>
          <TimeSlider year={s.year} onYear={s.setYear} playing={s.playing} onPlaying={s.setPlaying} />
        </div>
      </div>
      {!wide && (
        <MobileSheet title={t("app.title")}>
          {s.cell !== null
            ? <CellPanel atlas={atlas} cell={s.cell} year={s.year} onClose={() => s.setCell(null)} />
            : <><LayerPicker value={s.layer} onChange={pick} /><div className="mt-4"><SourceLine>{t(layer.source)}</SourceLine></div><div className="mt-4 border-t border-[var(--paper-line)] pt-3"><GlobalStrip atlas={atlas} year={s.year} /></div></>}
        </MobileSheet>
      )}
    </div>
  );
}
