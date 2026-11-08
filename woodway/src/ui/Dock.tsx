import { groupCh, type Layer, type LayerId } from "@/model/layers";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { LayerPicker } from "@/ui/LayerPicker";
import { TimeSlider } from "@/ui/TimeSlider";
import { PlantYearPicker } from "@/ui/PlantYearPicker";

/**
 * What the map shows, in one card: the layer (and the planting year of planted trees) and, when the layer has one, the year.
 * `row`: both on one line (wide enough screens); otherwise the year sits under the layer.
 */
export function Dock({ layer, onLayer, bare = false, row = false }: { layer: Layer; onLayer(id: LayerId): void; bare?: boolean; row?: boolean }) {
  const t = useT();
  const { year, setYear, playing, setPlaying, plantYear, setPlantYear, plantYears } = useAtlas();
  // planted trees: the timeline starts in their planting year (before it nothing grows)
  const from = layer.planted ? plantYear : 2026;
  return (
    <div role="group" aria-label={t("dock.label")} data-ch={groupCh(layer.group)}
      // sized to what it holds: a layer without years is the dropdown alone, not an empty bar
      className={(bare ? "" : "panel pointer-events-auto rounded-xl ") + (row
        ? "flex items-center gap-3 p-1.5 " + (bare ? "w-full" : layer.planted ? "w-[min(48rem,100%)]" : layer.timed ? "w-[min(42rem,100%)]" : "w-[min(20rem,100%)]")
        : "flex w-full flex-col gap-1 p-1.5 " + (bare ? "" : "max-w-md"))}>
      {/* the layer and, for planted trees, the planting year right of it: two dropdowns of one kind */}
      <div className={"flex gap-1.5 " + (row ? (layer.planted ? "w-[min(25rem,56%)] shrink-0" : layer.timed ? "w-[min(19rem,48%)] shrink-0" : "w-full") : "")}>
        <div className="min-w-0 flex-1"><LayerPicker value={layer.id} onChange={onLayer} /></div>
        {layer.planted && <PlantYearPicker value={plantYear} years={plantYears} onChange={setPlantYear} />}
      </div>
      {layer.timed && (
        <div className={row ? "min-w-0 flex-1 border-l border-[var(--paper-line)] pl-3 pr-1" : "px-1.5"}>
          <TimeSlider year={Math.max(year, from)} onYear={setYear} playing={playing} onPlaying={setPlaying} min={from} />
        </div>
      )}
    </div>
  );
}

