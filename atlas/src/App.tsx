import { useEffect, useState } from "react";
import { loadAtlas, LoadError } from "@/data/load";
import type { Atlas } from "@/data/types";
import { LAYERS, layerById, type LayerId } from "@/model/layers";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { useMediaQuery } from "@/lib/useMediaQuery";
import AtlasMap from "@/map/AtlasMap";
import { Header } from "@/ui/Header";
import { LayerPicker } from "@/ui/LayerPicker";
import { Legend } from "@/ui/Legend";
import { TimeSlider } from "@/ui/TimeSlider";
import { HoverReadout } from "@/ui/HoverReadout";

export default function App() {
  const t = useT();
  const s = useAtlas();
  const [atlas, setAtlas] = useState<Atlas | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hover, setHover] = useState<{ cell: number | null; x: number; y: number }>({ cell: null, x: 0, y: 0 });
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
  const ch = layer.group === "dac" ? "dac" : "baeume";
  return (
    <div className="relative h-full w-full overflow-hidden">
      <AtlasMap atlas={atlas} layer={layer} year={s.year} cell={s.cell} onCell={s.setCell}
        onHover={wide ? (cell, x, y) => setHover({ cell, x, y }) : undefined} dark={dark} initialView={{ longitude: 10, latitude: 25, zoom: wide ? 2.1 : 1.6 }} sites={atlas.meta.sites} />
      {wide && <HoverReadout atlas={atlas} layer={layer} year={s.year} {...hover} />}
      <div className="pointer-events-none absolute inset-x-0 top-0 p-4" style={{ paddingTop: "max(1rem, env(safe-area-inset-top))" }}>
        <Header />
      </div>
      <aside className="panel absolute left-4 top-24 max-h-[calc(100%-12rem)] w-60 overflow-auto p-3 max-md:hidden">
        <LayerPicker value={s.layer} onChange={s.setLayer} />
      </aside>
      <div className="absolute bottom-4 left-4 right-4 flex flex-col gap-3 md:right-auto md:w-[28rem]" style={{ paddingBottom: "env(safe-area-inset-bottom)" }}>
        <select aria-label="Layer" value={s.layer} onChange={(e) => s.setLayer(e.target.value as LayerId)}
          className="panel w-full px-3 py-2 text-sm text-ink md:hidden">
          {LAYERS.map((l) => <option key={l.id} value={l.id}>{t(l.label)}</option>)}
        </select>
        <div className="panel p-3"><Legend atlas={atlas} layer={layer} /></div>
        {layer.timed && (
          <div className="panel p-3" data-ch={ch}>
            <TimeSlider year={s.year} onYear={s.setYear} playing={s.playing} onPlaying={s.setPlaying} />
          </div>
        )}
      </div>
    </div>
  );
}
