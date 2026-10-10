import type { Layer, LayerId } from "@/model/layers";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { LayerPicker } from "@/ui/LayerPicker";
import { TimeSlider } from "@/ui/TimeSlider";

/** What the map shows, in one card: the layer, and below it the year when the layer has one. */
export function Dock({ layer, onLayer, bare = false }: { layer: Layer; onLayer(id: LayerId): void; bare?: boolean }) {
  const t = useT();
  const { year, setYear, playing, setPlaying } = useAtlas();
  return (
    <div role="group" aria-label={t("dock.label")} data-ch={layer.group === "dac" ? "dac" : "baeume"}
      className={(bare ? "" : "panel pointer-events-auto rounded-xl ") + "flex flex-col gap-2 p-2"}>
      <LayerPicker value={layer.id} onChange={onLayer} />
      {layer.timed && (
        <div className="border-t border-[var(--paper-line)] px-1 pt-2">
          <TimeSlider year={year} onYear={setYear} playing={playing} onPlaying={setPlaying} />
        </div>
      )}
    </div>
  );
}
