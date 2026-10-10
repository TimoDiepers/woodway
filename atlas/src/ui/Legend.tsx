import type { Atlas } from "@/data/types";
import { reasonColor, scaleOf, type Layer } from "@/model/layers";
import { useNum, useT, type Key } from "@/i18n/useT";
import { useAtlas } from "@/store";
import { SourceLine } from "@/ui/deck/SourceLine";

export function Legend({ atlas, layer, compact = false }: { atlas: Atlas; layer: Layer; compact?: boolean }) {
  const t = useT(), num = useNum();
  const lang = useAtlas((s) => s.lang);
  const sc = scaleOf(atlas, layer);
  const fmt = (v: number) => num(v, Number.isInteger(v) ? 0 : 1).replace(/^-/, "\u2212");
  const unit = layer.unit ? (layer.unit.includes(".") ? t(layer.unit as Key) : layer.unit) : sc?.unit ?? "";
  const inlineUnit = !compact && unit.length > 0 && unit.length <= 4;   // a short unit ("%") sits with the ticks
  return (
    <figure className={compact ? "flex flex-col gap-1 text-[11px]" : "flex flex-col gap-1.5 text-xs"} aria-label={t(layer.label)} data-ch={layer.group === "dac" ? "dac" : "baeume"}>
      <figcaption className={compact ? "ch-text font-serif text-sm font-semibold leading-tight" : "ch-text font-serif text-base font-semibold leading-tight"}>{t(layer.label)}</figcaption>
      {layer.kind === "cat" ? (
        <ul className={compact ? "flex flex-wrap gap-x-3 gap-y-0.5" : "flex flex-col gap-0.5"}>
          {atlas.meta.categories.waldtyp.map((c) => (
            <li key={c.key} className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm" style={{ background: c.color }} />
              {t(`type.${c.key}` as Key)}
            </li>
          ))}
        </ul>
      ) : sc ? (
        <div className={compact ? "flex items-center gap-3" : undefined}>
          <div className={compact ? "min-w-0 flex-1" : undefined}>
          <div className="h-2.5 w-56 max-w-full rounded-sm" style={{ background: `linear-gradient(to right, ${sc.stops.join(",")})` }} />
          <div className="mt-0.5 flex w-56 max-w-full justify-between tabular-nums text-inkMuted">
            <span>{fmt(sc.domain[0])}</span>
            {sc.mid !== undefined && <span>{fmt(sc.mid)}</span>}
            <span>{fmt(sc.domain[1])}</span>
            {inlineUnit && <span className="ml-2">{unit}</span>}
          </div>
          {!compact && !inlineUnit && <p className="text-inkMuted">{unit}{layer.id === "deltaT" && ` · ${t("legend.cools")} ← → ${t("legend.warms")}`}</p>}
          </div>
          {compact && <p className="shrink-0 text-inkMuted">{unit}</p>}
        </div>
      ) : null}
      <ul className={compact ? "flex flex-wrap gap-x-3 gap-y-0.5 text-inkMuted" : "flex flex-col gap-0.5 text-inkMuted"}>
        {layer.greys.map((r) => (
          <li key={r} className={compact ? "flex items-center gap-1.5" : "flex items-center gap-2"}>
            <span className="h-3 w-3 shrink-0 rounded-sm border border-[var(--paper-line)]" style={{ background: reasonColor(atlas, r) }} />{t(r)}
          </li>
        ))}
      </ul>
      {!compact && <div lang={lang} className="max-w-xs"><SourceLine>{t(layer.source)}</SourceLine></div>}
    </figure>
  );
}
