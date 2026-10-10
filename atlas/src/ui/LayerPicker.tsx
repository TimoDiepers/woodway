import type { KeyboardEvent } from "react";
import { LAYERS, type LayerId } from "@/model/layers";
import { useT } from "@/i18n/useT";
import { cn } from "@/lib/utils";
import { Kicker } from "@/ui/deck/Kicker";

export function LayerPicker({ value, onChange }: { value: LayerId; onChange(id: LayerId): void }) {
  const t = useT();
  // Roving tabindex: one Tab stop (the checked option); arrows/Home/End move and select across both groups.
  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const i = LAYERS.findIndex((l) => l.id === value);
    let n = i;
    if (e.key === "ArrowDown" || e.key === "ArrowRight") n = (i + 1) % LAYERS.length;
    else if (e.key === "ArrowUp" || e.key === "ArrowLeft") n = (i - 1 + LAYERS.length) % LAYERS.length;
    else if (e.key === "Home") n = 0;
    else if (e.key === "End") n = LAYERS.length - 1;
    else return;
    e.preventDefault();
    onChange(LAYERS[n].id);
    e.currentTarget.querySelector<HTMLElement>(`[data-layer="${LAYERS[n].id}"]`)?.focus();
  };
  return (
    <div role="radiogroup" aria-label={t("layer.label")} onKeyDown={onKey} className="flex flex-col gap-4">
      {(["trees", "dac"] as const).map((g) => (
        <div key={g} data-ch={g === "trees" ? "baeume" : "dac"}>
          <div className="mb-1.5 border-b border-[var(--paper-line)] pb-1">
            <Kicker>{t(g === "trees" ? "group.trees" : "group.dac")}</Kicker>
          </div>
          <ul className="flex flex-col gap-0.5">
            {LAYERS.filter((l) => l.group === g).map((l) => (
              <li key={l.id}>
                <button role="radio" data-layer={l.id} aria-checked={l.id === value} tabIndex={l.id === value ? 0 : -1} onClick={() => onChange(l.id)}
                  className={cn("w-full rounded-r border-l-[3px] py-1.5 pl-2.5 pr-2 text-left text-sm leading-snug transition-colors [@media(pointer:coarse)]:min-h-11 [@media(pointer:coarse)]:py-2.5 [@media(pointer:coarse)]:text-[15px]",
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
