import type { Atlas } from "@/data/types";
import { reasonColor, scaleOf, type Layer } from "@/model/layers";
import { useNum, useT, type Key } from "@/i18n/useT";
import { useAtlas } from "@/store";
import { useDark } from "@/lib/useDark";
import { themedScale } from "@/color/scale";
import { SourceLine } from "@/ui/deck/SourceLine";

/** `caption={false}`: the layer's name is shown elsewhere (the phone's dropdown right above). */
export function Legend({ atlas, layer, compact = false, caption = true }: { atlas: Atlas; layer: Layer; compact?: boolean; caption?: boolean }) {
  const t = useT(), num = useNum();
  const lang = useAtlas((s) => s.lang);
  const dark = useDark();
  const base = scaleOf(atlas, layer), sc = base && themedScale(base, dark);
  const fmt = (v: number) => num(v, Number.isInteger(v) ? 0 : 1).replace(/^-/, "\u2212");
  const unit = layer.unit ? (layer.unit.includes(".") ? t(layer.unit as Key) : layer.unit) : sc?.unit ?? "";
  const inlineUnit = unit.length > 0 && unit.length <= 4;   // a short unit ("%") sits with the ticks
  const greys = (
    <ul className={compact ? "flex flex-wrap gap-x-2.5 gap-y-0.5 text-[11px] text-inkMuted" : "flex flex-col gap-0.5 text-inkMuted"}>
      {layer.greys.map((r) => (
        <li key={r} className={compact ? "flex items-center gap-1" : "flex items-center gap-2"}>
          <span className={compact ? "h-2.5 w-2.5 shrink-0 rounded-sm border border-[var(--paper-line)]" : "h-3 w-3 shrink-0 rounded-sm border border-[var(--paper-line)]"} style={{ background: reasonColor(atlas, r, dark) }} />{t(r)}
        </li>
      ))}
    </ul>
  );
  const cats = layer.kind === "cat" && (
    <ul className={compact ? "flex flex-wrap gap-x-2.5 gap-y-0.5 text-[11px]" : "flex flex-col gap-0.5"}>
      {atlas.meta.categories.waldtyp.map((c) => (
        <li key={c.key} className="flex items-center gap-1.5">
          <span className={compact ? "h-2.5 w-2.5 rounded-sm" : "h-3 w-3 rounded-sm"} style={{ background: c.color }} />
          {t(`type.${c.key}` as Key)}
        </li>
      ))}
    </ul>
  );
  if (compact) {
    // the phone's plate: the layer's name in full, the ramp with its ticks and unit, then what the greys mean
    return (
      <figure className="flex flex-col gap-1 text-xs" aria-label={t(layer.label)} data-ch={layer.group === "dac" ? "dac" : "baeume"}>
        {caption && <figcaption className="ch-text line-clamp-2 font-serif text-[13px] font-semibold leading-tight">{t(layer.label)}</figcaption>}
        {cats}
        {layer.kind !== "cat" && sc && (
          <div>
            <div className="h-2 w-full rounded-sm" style={{ background: `linear-gradient(to right, ${sc.stops.join(",")})` }} />
            <div className="mt-0.5 flex items-baseline gap-2 text-[11px] tabular-nums text-inkMuted">
              <div className="flex flex-1 justify-between">
                <span>{fmt(sc.domain[0])}</span>
                {sc.mid !== undefined && <span>{fmt(sc.mid)}</span>}
                <span>{fmt(sc.domain[1])}</span>
              </div>
              {unit && <span className="shrink-0">{unit}</span>}
            </div>
          </div>
        )}
        {layer.greys.length > 0 && greys}
      </figure>
    );
  }
  return (
    <figure className="flex flex-col gap-1.5 text-xs" aria-label={t(layer.label)} data-ch={layer.group === "dac" ? "dac" : "baeume"}>
      <figcaption className="ch-text font-serif text-base font-semibold leading-tight">{t(layer.label)}</figcaption>
      {cats}
      {layer.kind !== "cat" && sc && (
        <div>
          <div className="h-2.5 w-56 max-w-full rounded-sm" style={{ background: `linear-gradient(to right, ${sc.stops.join(",")})` }} />
          <div className="mt-0.5 flex w-56 max-w-full justify-between tabular-nums text-inkMuted">
            <span>{fmt(sc.domain[0])}</span>
            {sc.mid !== undefined && <span>{fmt(sc.mid)}</span>}
            <span>{fmt(sc.domain[1])}</span>
            {inlineUnit && <span className="ml-2">{unit}</span>}
          </div>
          {!inlineUnit && <p className="text-inkMuted">{unit}{layer.id === "deltaT" && ` · ${t("legend.cools")} ← → ${t("legend.warms")}`}</p>}
        </div>
      )}
      {greys}
      <div lang={lang} className="max-w-xs"><SourceLine>{t(layer.source)}</SourceLine></div>
    </figure>
  );
}
