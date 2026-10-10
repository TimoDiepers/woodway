import type { Atlas } from "@/data/types";
import { cellAt } from "@/map/lookup";
import { useT } from "@/i18n/useT";

/** `bare`: no label (the sheet's own heading names the row) and full-size touch targets. */
export function SiteButtons({ atlas, onPick, bare = false }: { atlas: Atlas; onPick(cell: number, site: { lon: number; lat: number }): void; bare?: boolean }) {
  const t = useT();
  return (
    <div className={bare ? "flex flex-wrap items-center gap-2 text-sm" : "flex flex-wrap items-center gap-1.5 text-xs"}>
      {!bare && <span className="text-inkMuted">{t("sites.label")}</span>}
      {atlas.meta.sites.flatMap((s) => { const cell = cellAt(s.lon, s.lat); return cell === null ? [] : [{ s, cell }]; }).map(({ s, cell }) => (
        <button key={s.name} onClick={() => onPick(cell, s)}
          className={bare ? "min-h-11 rounded-full border border-panelBorder bg-paper px-3.5 active:bg-ink/10" : "rounded-full border border-panelBorder bg-paper/80 px-2 py-0.5 hover:bg-ink/5"}>
          <span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: s.color }} />{s.name}
        </button>
      ))}
    </div>
  );
}
