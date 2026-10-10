import type { ReactNode } from "react";
import { useAtlas } from "@/store";
import { useT, type Key } from "@/i18n/useT";

const ENTRIES = ["question", "map", "layers", "colours", "grey", "year", "data"] as const;

/** Everything the screen does not explain by itself, in one place: what the atlas asks, and how to read it. */
export function HelpContent({ touch }: { touch: boolean }) {
  const t = useT();
  const { hintSeen, resetHints, lang } = useAtlas();
  const verb = lang === "de" ? (touch ? "Tippe" : "Klicke") : touch ? "Tap" : "Click";
  return (
    <div>
      {ENTRIES.map((e) => (
        <Entry key={e} title={t(`help.${e}.t` as Key)}>{t(`help.${e}` as Key, { verb })}</Entry>
      ))}
      <div className="mt-4 border-t border-[var(--paper-line)] pt-3">
        <button onClick={resetHints} disabled={!hintSeen}
          className="h-10 w-full rounded-md border border-[var(--paper-line)] bg-paper/60 text-sm font-medium text-ink hover:bg-ink/5 disabled:opacity-50">
          {t("help.reset")}
        </button>
        <p className="mt-1.5 text-[11px] italic leading-snug text-inkMuted">{t("help.resetNote")}</p>
      </div>
    </div>
  );
}

function Entry({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mb-3.5 last:mb-0">
      <h3 className="mb-0.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-inkMuted">{title}</h3>
      <p className="font-serif text-sm leading-normal text-ink">{children}</p>
    </section>
  );
}
