import { LAYERS, type LayerId } from "@/model/layers";
import { useT } from "@/i18n/useT";
import { cn } from "@/lib/utils";
import { Kicker } from "@/ui/deck/Kicker";

export function LayerPicker({ value, onChange }: { value: LayerId; onChange(id: LayerId): void }) {
  const t = useT();
  return (
    <div role="radiogroup" aria-label="Layer" className="flex flex-col gap-4">
      {(["trees", "dac"] as const).map((g) => (
        <div key={g} data-ch={g === "trees" ? "baeume" : "dac"}>
          <div className="mb-1.5 border-b border-[var(--paper-line)] pb-1">
            <Kicker>{t(g === "trees" ? "group.trees" : "group.dac")}</Kicker>
          </div>
          <ul className="flex flex-col gap-0.5">
            {LAYERS.filter((l) => l.group === g).map((l) => (
              <li key={l.id}>
                <button role="radio" aria-checked={l.id === value} onClick={() => onChange(l.id)}
                  className={cn("w-full rounded-r border-l-[3px] py-1.5 pl-2.5 pr-2 text-left text-sm leading-snug transition-colors",
                    l.id === value
                      ? "border-[var(--ch)] bg-[color-mix(in_srgb,var(--ch-soft)_45%,transparent)] font-medium text-ink"
                      : "border-transparent text-inkMuted hover:bg-ink/5 hover:text-ink")}>
                  {t(l.label)}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
