import type { Atlas } from "@/data/types";
import type { Layer } from "@/model/layers";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { Legend } from "@/ui/Legend";

/**
 * Top left, as in woodway: the app's name, a first-visit line saying what to do, and the key to the colours,
 * read top to bottom as one plate, so what the map shows and what its colours mean sit together.
 */
export function TitlePlate({ atlas, layer, compact }: { atlas: Atlas | null; layer: Layer; compact: boolean }) {
  const t = useT();
  const hintSeen = useAtlas((s) => s.hintSeen);
  return (
    <header className={"panel pointer-events-auto min-w-0 " + (compact ? "w-[min(19rem,calc(100vw-5rem))] px-3 py-2" : "w-80 px-4 py-3")}>
      {/* on a phone the hint shares the title's line: one row less over the map */}
      <div className={compact ? "flex items-baseline gap-2" : ""}>
        <h1 className={compact ? "shrink-0 font-serif text-base font-semibold leading-tight" : "font-serif text-2xl font-semibold leading-tight"}>{t("app.title")}</h1>
        {!compact && <p className="text-xs text-inkMuted">{t("app.subtitle")}</p>}
        {!hintSeen && (
          <p className={"font-serif text-xs italic leading-snug text-inkMuted " + (compact ? "min-w-0" : "mt-1.5 border-t border-[var(--paper-line)] pt-1.5")}>
            {t(compact ? "hint.tap" : "hint.click")}
          </p>
        )}
      </div>
      <div className={"border-t border-[var(--paper-line)] " + (compact ? "mt-1.5 pt-1.5" : "mt-2 pt-2")}>
        {atlas ? <div className="fade-in"><Legend atlas={atlas} layer={layer} compact={compact} /></div> : <LegendSkeleton compact={compact} />}
      </div>
    </header>
  );
}

/** The legend's shape while the data loads: its title, the colour ramp and its ticks as soft bars, so the plate has
 *  its size from the start and the real legend takes its place without a jump. */
function LegendSkeleton({ compact }: { compact: boolean }) {
  const t = useT();
  return (
    <div aria-busy="true" aria-label={t("app.loading")} className="flex flex-col gap-1.5">
      <div className="skel h-4 w-44" />
      <div className="skel h-2.5 w-full max-w-[14rem]" />
      <div className="flex max-w-[14rem] justify-between"><div className="skel h-2.5 w-6" /><div className="skel h-2.5 w-4" /><div className="skel h-2.5 w-6" /></div>
      {!compact && <><div className="skel mt-1 h-2.5 w-28" /><div className="skel h-2.5 w-full" /><div className="skel h-2.5 w-4/5" /></>}
    </div>
  );
}
