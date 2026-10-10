import { useEffect, useMemo, useRef, useState } from "react";
import type { Atlas } from "@/data/types";
import { layerById } from "@/model/layers";
import AtlasMap from "@/map/AtlasMap";
import { useAtlas } from "@/store";
import { CellPanel } from "@/ui/CellPanel";
import { GlobalStrip } from "@/ui/GlobalStrip";
import { LayerPicker } from "@/ui/LayerPicker";
import { Legend } from "@/ui/Legend";
import { TimeSlider } from "@/ui/TimeSlider";
import { SourceLine } from "@/ui/deck/SourceLine";
import { Takeaway } from "@/ui/deck/Takeaway";
import { talkLayer, type AtlasSlideDef } from "./slides";

const ANIM_MS = 1200;
const VIEW = { longitude: 10, latitude: 20, zoom: 1.15 };

/** The year shown follows the step's target: it runs there over 1.2 s (at once with reduced motion). */
function useAnimatedYear(target: number): number {
  const [year, setYear] = useState(target);
  const cur = useRef(target);
  useEffect(() => {
    const from = cur.current;
    if (from === target) return;
    const reduce = typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) { cur.current = target; setYear(target); return; }
    let raf = 0;
    const t0 = performance.now();
    const tick = (now: number) => {
      const k = Math.min(1, (now - t0) / ANIM_MS);
      const e = k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2;   // ease in-out
      cur.current = from + (target - from) * e;
      setYear(Math.round(cur.current));
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target]);
  return year;
}

/** Keyed by slide: each slide starts at its own first year instead of running there from the previous one. */
export default function AtlasSlide(p: { def: AtlasSlideDef; atlas: Atlas; step: number }) {
  return <SlideBody key={p.def.id} {...p} />;
}

function SlideBody({ def, atlas, step }: { def: AtlasSlideDef; atlas: Atlas; step: number }) {
  const store = useAtlas();
  const target = def.years[Math.max(0, Math.min(def.years.length - 1, step))];
  const animated = useAnimatedYear(target);
  const free = !!def.free;
  const layer = free ? layerById(store.layer) : talkLayer(def, atlas);
  const year = free ? store.year : animated;
  const sites = useMemo(() => (def.sitesFrom !== undefined && step >= def.sitesFrom ? atlas.meta.sites : []), [def.sitesFrom, step, atlas]);
  const stop = (e: { stopPropagation(): void }) => e.stopPropagation();

  return (
    <section className="rslide" data-ch={def.ch} data-atlas={def.id} data-step={step}>
      <header className="sh"><h2>{def.title}</h2></header>
      <div className="rmap" onClick={free ? stop : undefined}>
        <AtlasMap atlas={atlas} layer={layer} year={year} cell={free ? store.cell : null}
          onCell={free ? store.setCell : () => {}} projection="mercator" dark={false}
          sites={sites} initialView={VIEW} />
        {free ? (
          <>
            <aside className="panel rpanel left">
              <LayerPicker value={store.layer} onChange={store.setLayer} />
            </aside>
            {store.cell !== null
              ? <aside className="panel rpanel right"><CellPanel atlas={atlas} cell={store.cell} year={store.year} onClose={() => store.setCell(null)} /></aside>
              : <div className="panel rpanel right small"><GlobalStrip atlas={atlas} year={store.year} /></div>}
            <div className="panel rlegend free"><Legend atlas={atlas} layer={layer} compact /></div>
            <div className="panel rpanel slider"><TimeSlider year={store.year} onYear={store.setYear} playing={store.playing} onPlaying={store.setPlaying} /></div>
          </>
        ) : (
          <>
            <div className="panel rlegend"><Legend atlas={atlas} layer={layer} /></div>
            <div className="ryear">{Math.round(year)}</div>
          </>
        )}
      </div>
      <Takeaway ch={def.ch} size="slide">{def.takeaway(atlas, step)}</Takeaway>
      <SourceLine>{def.source}</SourceLine>
    </section>
  );
}
