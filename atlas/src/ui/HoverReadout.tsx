import type { Atlas } from "@/data/types";
import type { Layer } from "@/model/layers";
import { scaleOf } from "@/model/layers";
import { useNum, useT, type Key } from "@/i18n/useT";

export function HoverReadout({ atlas, layer, year, cell, x, y }: { atlas: Atlas; layer: Layer; year: number; cell: number | null; x: number; y: number }) {
  const t = useT(), num = useNum();
  if (cell === null) return null;
  const v = layer.value(atlas, cell, year);
  let text: string;
  if (layer.kind === "cat") text = v >= 0 ? t(`type.${atlas.meta.categories.waldtyp[v].key}` as Key) : t("reason.noTrees");
  else if (Number.isFinite(v)) {
    const sc = scaleOf(atlas, layer);
    const unit = layer.unit ? (layer.unit.includes(".") ? t(layer.unit as Key) : layer.unit) : sc?.unit ?? "";
    text = t("hover.value", { value: num(v, Math.abs(v) < 10 ? 1 : 0), unit });
  } else text = t((layer.reason(atlas, cell) ?? "reason.noTrees") as Key);
  return (
    <div className="panel pointer-events-none absolute z-20 px-2 py-1 text-xs tabular-nums" style={{ left: x + 14, top: y - 10 }}>
      {text}
    </div>
  );
}
