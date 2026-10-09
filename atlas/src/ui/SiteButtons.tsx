import type { Atlas } from "@/data/types";
import { cellAt } from "@/map/lookup";
import { useT } from "@/i18n/useT";

export function SiteButtons({ atlas, onPick }: { atlas: Atlas; onPick(cell: number, site: { lon: number; lat: number }): void }) {
  const t = useT();
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-xs">
      <span className="text-inkMuted">{t("sites.label")}</span>
      {atlas.meta.sites.map((s) => (
        <button key={s.name} onClick={() => onPick(cellAt(s.lon, s.lat)!, s)}
          className="rounded-full border border-panelBorder bg-paper/80 px-2 py-0.5 hover:bg-ink/5">
          <span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: s.color }} />{s.name}
        </button>
      ))}
    </div>
  );
}
