import { GROUPS, LAYERS, groupCh, type LayerId } from "@/model/layers";
import { useT } from "@/i18n/useT";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/ui/primitives/select";

/** One dropdown instead of a long list: the current layer, and every layer in sections in the order of the talk
 *  (one tree, all land, today's forest, a vegan world, DAC). */
export function LayerPicker({ value, onChange }: { value: LayerId; onChange(id: LayerId): void }) {
  const t = useT();
  const cur = LAYERS.find((l) => l.id === value)!;
  const ch = groupCh(cur.group);
  return (
    <Select value={value} onValueChange={(v) => onChange(v as LayerId)}>
      <SelectTrigger aria-label={t("layer.label")} data-ch={ch}
        className="h-9 gap-2 border-[var(--paper-line)] bg-paper/70 px-2.5 [@media(pointer:coarse)]:h-10 text-left text-sm font-medium text-ink focus-visible:ring-[color-mix(in_srgb,var(--ch)_40%,transparent)]">
        {/* a div: the primitive clamps direct <span> children to one line, which collapses the dot */}
        <div className="flex min-w-0 items-center gap-2">
          <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-[var(--ch)]" aria-hidden />
          <div className="truncate"><SelectValue /></div>
        </div>
      </SelectTrigger>
      <SelectContent position="popper" sideOffset={4}
        className="max-h-[min(70dvh,var(--radix-select-content-available-height))] w-[var(--radix-select-trigger-width)] min-w-[15rem] border-[var(--paper-line)] bg-panel">
        {GROUPS.map(({ g, ch: c, label }) => (
          <SelectGroup key={g} data-ch={c}>
            <SelectLabel className="mt-1 px-2.5 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--ch)]">{t(label)}</SelectLabel>
            {LAYERS.filter((l) => l.group === g).map((l) => (
              <SelectItem key={l.id} value={l.id}
                className="py-2 pl-8 text-sm leading-snug focus:bg-[color-mix(in_srgb,var(--ch-soft)_40%,transparent)] focus:text-ink [@media(pointer:coarse)]:min-h-11">
                {t(l.label)}
              </SelectItem>
            ))}
          </SelectGroup>
        ))}
      </SelectContent>
    </Select>
  );
}
