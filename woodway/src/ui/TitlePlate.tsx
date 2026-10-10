import type { Atlas } from "@/data/types";
import type { Layer } from "@/model/layers";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { Legend } from "@/ui/Legend";

/**
 * Top left, as in woodway: the app's name, a first-visit line saying what to do, and the key to the colours,
 * read top to bottom as one plate, so what the map shows and what its colours mean sit together.
 */
export function TitlePlate({ atlas, layer, compact }: { atlas: Atlas; layer: Layer; compact: boolean }) {
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
        <Legend atlas={atlas} layer={layer} compact={compact} />
      </div>
    </header>
  );
}
