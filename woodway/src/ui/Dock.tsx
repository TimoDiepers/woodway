import { groupCh, type Layer, type LayerId } from "@/model/layers";
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
  const { year, setYear, playing, setPlaying, plantYear, setPlantYear } = useAtlas();
  return (
    <div role="group" aria-label={t("dock.label")} data-ch={groupCh(layer.group)}
      // sized to what it holds: a layer without years is the dropdown alone, not an empty bar
      className={(bare ? "" : "panel pointer-events-auto rounded-xl ") + (row
        ? "flex items-center gap-3 p-1.5 " + (bare ? "w-full" : layer.timed ? "w-[min(42rem,100%)]" : "w-[min(20rem,100%)]")
        : "flex w-full flex-col gap-1 p-1.5 " + (bare ? "" : "max-w-md"))}>
      <div className={row ? (layer.timed ? "w-[min(19rem,48%)] shrink-0" : "w-full") : ""}><LayerPicker value={layer.id} onChange={onLayer} /></div>
      {layer.timed && (
        <div className={row ? "min-w-0 flex-1 border-l border-[var(--paper-line)] pl-3 pr-1" : "px-1.5"}>
          <TimeSlider year={year} onYear={setYear} playing={playing} onPlaying={setPlaying} />
        </div>
      )}
      {layer.planted && <PlantYear value={plantYear} onChange={setPlantYear} row={row} />}
    </div>
  );
}

/** The year the trees of this layer are planted in: 2026 as in the talk, or later (the deck's backup "Einfluss des
 *  Pflanzjahres"). A native select: small, keyboard- and touch-friendly, and it says what it is. */
function PlantYear({ value, onChange, row }: { value: number; onChange(y: number): void; row: boolean }) {
  const t = useT();
  const years = useAtlas((s) => s.plantYears);
  return (
    <label className={(row ? "shrink-0 border-l border-[var(--paper-line)] pl-3 " : "px-1.5 ") + "flex items-center gap-1.5 text-xs text-inkMuted"}>
      <span className="whitespace-nowrap">{t("dock.planted")}</span>
      <select value={value} onChange={(e) => onChange(+e.target.value)} aria-label={t("dock.plantedLong")}
        className="h-8 rounded-md border border-[var(--paper-line)] bg-paper/70 px-1.5 font-serif text-[14px] font-semibold tabular-nums text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ch)]/40 [@media(pointer:coarse)]:h-10">
        {years.map((y) => <option key={y} value={y}>{y}</option>)}
      </select>
    </label>
  );
}
