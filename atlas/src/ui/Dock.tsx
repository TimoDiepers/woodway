import type { Layer, LayerId } from "@/model/layers";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { LayerPicker } from "@/ui/LayerPicker";
import { TimeSlider } from "@/ui/TimeSlider";

/**
 * What the map shows, in one card: the layer and, when the layer has one, the year.
 * `row`: both on one line (wide enough screens); otherwise the year sits under the layer.
 */
export function Dock({ layer, onLayer, bare = false, row = false }: { layer: Layer; onLayer(id: LayerId): void; bare?: boolean; row?: boolean }) {
  const t = useT();
  const { year, setYear, playing, setPlaying } = useAtlas();
  return (
    <div role="group" aria-label={t("dock.label")} data-ch={layer.group === "dac" ? "dac" : "baeume"}
      className={(bare ? "" : "panel pointer-events-auto rounded-xl ") + (row ? "flex items-center gap-3 p-1.5" : "flex flex-col gap-1 p-1.5")}>
      <div className={row ? "w-[min(19rem,48%)] shrink-0" : ""}><LayerPicker value={layer.id} onChange={onLayer} /></div>
      {layer.timed && (
        <div className={row ? "min-w-0 flex-1 border-l border-[var(--paper-line)] pl-3 pr-1" : "px-1.5"}>
          <TimeSlider year={year} onYear={setYear} playing={playing} onPlaying={setPlaying} />
        </div>
      )}
    </div>
  );
}
