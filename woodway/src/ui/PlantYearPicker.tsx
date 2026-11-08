import { Sprout } from "lucide-react";
import { useT } from "@/i18n/useT";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger } from "@/ui/primitives/select";

/** The planting year, right of the layer dropdown and built like it: a sapling and the year, opening a list in the
 *  same style. It names itself to screen readers. */
export function PlantYearPicker({ value, years, onChange }: { value: number; years: number[]; onChange(y: number): void }) {
  const t = useT();
  return (
    <Select value={String(value)} onValueChange={(v) => onChange(+v)}>
      <SelectTrigger aria-label={t("dock.plantedLong")} title={t("dock.plantedLong")}
        className="h-9 w-auto shrink-0 gap-2 border-[var(--paper-line)] bg-paper/70 px-2.5 [@media(pointer:coarse)]:h-10 text-left text-sm font-medium text-ink focus-visible:ring-[color-mix(in_srgb,var(--ch)_40%,transparent)]">
        <div className="flex items-center gap-1.5">
          <Sprout size={15} strokeWidth={2} className="shrink-0 text-[var(--ch)]" aria-hidden />
          <span className="tabular-nums">{value}</span>
        </div>
      </SelectTrigger>
      <SelectContent position="popper" sideOffset={6} align="end"
        className="min-w-[9.5rem] border-[var(--paper-line)] bg-panel">
        <SelectGroup>
          <SelectLabel className="px-2.5 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--ch)]">{t("dock.plantedLong")}</SelectLabel>
          {years.map((y) => (
            <SelectItem key={y} value={String(y)}
              className="py-2 pl-8 text-sm tabular-nums leading-snug focus:bg-[color-mix(in_srgb,var(--ch-soft)_40%,transparent)] focus:text-ink [@media(pointer:coarse)]:min-h-11">
              {y}{y === years[0] && <span className="ml-2 font-sans text-xs text-inkMuted">{t("dock.plantedTalk")}</span>}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  );
}
