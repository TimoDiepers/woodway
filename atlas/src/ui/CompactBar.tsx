import { useEffect, useState } from "react";
import { Globe, Map as MapIcon, Moon, Search, Sun, X } from "lucide-react";
import { PlaceSearch, type Place } from "@/ui/PlaceSearch";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { useMediaQuery } from "@/lib/useMediaQuery";

/** The phone's top bar: the name and four round 44 px controls, nothing that wraps. Search opens a field below the bar. */
export function CompactBar({ onPlace }: { onPlace(p: Place): void }) {
  const t = useT();
  const { lang, setLang, theme, setTheme, projection, setProjection } = useAtlas();
  const prefersDark = useMediaQuery("(prefers-color-scheme: dark)");
  const dark = theme === "dark" || (theme === "system" && prefersDark);
  const [searching, setSearching] = useState(false);
  useEffect(() => {
    if (!searching) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setSearching(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [searching]);
  const btn = "grid h-11 w-11 place-items-center rounded-full text-ink active:bg-ink/10";
  return (
    <header className="pointer-events-none absolute inset-x-0 top-0 z-20 flex items-center justify-between px-3"
      style={{ paddingTop: "max(0.5rem, env(safe-area-inset-top))" }}>
      <h1 className="pointer-events-auto font-serif text-[1.6rem] font-semibold leading-none drop-shadow-[0_1px_0_rgb(var(--color-paper))]">{t("app.title")}</h1>
      <div className="panel pointer-events-auto flex items-center rounded-full p-0.5">
        <button aria-label={t("search.label")} aria-expanded={searching} onClick={() => setSearching((s) => !s)} className={btn}>
          <Search size={18} aria-hidden />
        </button>
        <button aria-label={t("lang.switch")} onClick={() => setLang(lang === "en" ? "de" : "en")} className={`${btn} text-sm font-medium tracking-wide`}>
          {t("lang.short")}
        </button>
        <button aria-label={t(projection === "globe" ? "projection.flat" : "projection.globe")} onClick={() => setProjection(projection === "globe" ? "mercator" : "globe")} className={btn}>
          {projection === "globe" ? <MapIcon size={18} aria-hidden /> : <Globe size={18} aria-hidden />}
        </button>
        <button aria-label={t("theme.label")} onClick={() => setTheme(dark ? "light" : "dark")} className={btn}>
          {dark ? <Sun size={18} aria-hidden /> : <Moon size={18} aria-hidden />}
        </button>
      </div>
      {searching && (
        <div className="panel pointer-events-auto absolute inset-x-3 top-full mt-2 flex items-start gap-1 p-2">
          <div className="min-w-0 flex-1"><PlaceSearch autoFocus onPick={(p) => { setSearching(false); onPlace(p); }} /></div>
          <button aria-label={t("panel.close")} onClick={() => setSearching(false)} className="grid h-10 w-10 shrink-0 place-items-center rounded-full active:bg-ink/10"><X size={18} aria-hidden /></button>
        </div>
      )}
    </header>
  );
}
