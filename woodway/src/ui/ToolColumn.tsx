import { useState, type ReactNode } from "react";
import { BarChart2, Compass, Globe, HelpCircle, Map as MapIcon, Moon, Presentation, Search, Sun } from "lucide-react";
import type { Atlas } from "@/data/types";
import type { Layer } from "@/model/layers";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { useMediaQuery } from "@/lib/useMediaQuery";
import { ToolPanel } from "@/ui/ToolPanel";
import { HelpContent } from "@/ui/HelpContent";
import { PlaceSearch, type Place } from "@/ui/PlaceSearch";
import { SiteButtons } from "@/ui/SiteButtons";
import { GlobalStrip } from "@/ui/GlobalStrip";
import { SourceLine } from "@/ui/deck/SourceLine";

type PanelId = "search" | "overview" | "help";

/** The talk's slides: published next to woodway under slides/; in development the dev server serves the built deck. */
const SLIDES_URL = import.meta.env.DEV ? "/deck/index.html" : "slides/";
/** inside the deck's own last slide, a link back to the deck would only open it a second time */
const EMBEDDED = typeof window !== "undefined" && window.parent !== window;

/**
 * The map's tools in one card: a column against the right edge on a phone, a row top right on a desktop.
 * Utilities only (find, go home, restyle, look things up); what the map shows is decided in the dock.
 */
export function ToolColumn({ atlas, layer, year, compact, onPlace, onRecenter, onSite }: {
  atlas: Atlas; layer: Layer; year: number; compact: boolean;
  onPlace(p: Place): void; onRecenter(): void; onSite(cell: number, site: { lon: number; lat: number }): void;
}) {
  const t = useT();
  const { lang, setLang, theme, setTheme, projection, setProjection } = useAtlas();
  const prefersDark = useMediaQuery("(prefers-color-scheme: dark)");
  const touch = useMediaQuery("(pointer: coarse)") || compact;
  const dark = theme === "dark" || (theme === "system" && prefersDark);
  const [open, setOpen] = useState<PanelId | null>(null);
  const toggle = (p: PanelId) => (o: boolean) => setOpen(o ? p : open === p ? null : open);

  const btn = compact
    ? "grid h-10 w-10 place-items-center text-ink hover:bg-ink/5 active:bg-ink/10 aria-expanded:bg-ink/10"
    : "grid h-9 w-9 place-items-center rounded-md text-ink hover:bg-ink/5 aria-expanded:bg-ink/10";
  const tool = (label: string, icon: ReactNode, onClick?: () => void, expanded?: boolean) => (
    <button type="button" aria-label={label} title={compact ? undefined : label} onClick={onClick} className={btn}
      {...(expanded !== undefined ? { "aria-expanded": expanded, "aria-haspopup": "dialog" as const } : {})}>{icon}</button>
  );
  const panel = (id: PanelId, label: string, icon: ReactNode, sub: string | undefined, body: ReactNode, wide = false) => (
    <ToolPanel compact={compact} open={open === id} onOpenChange={toggle(id)} title={label} sub={sub} wide={wide}
      trigger={tool(label, icon, compact ? () => setOpen(open === id ? null : id) : undefined, open === id)}>{body}</ToolPanel>
  );

  return (
    <div role="toolbar" aria-label={t("tools.label")} aria-orientation={compact ? "vertical" : "horizontal"}
      className={"panel pointer-events-auto flex overflow-hidden " + (compact ? "flex-col divide-y divide-[var(--paper-line)] rounded-xl" : "items-center gap-0.5 p-1")}>
      {panel("search", t("search.label"), <Search size={18} aria-hidden />, undefined,
        <PlaceSearch autoFocus onPick={(p) => { setOpen(null); onPlace(p); }} />)}
      {tool(t("tools.recenter"), <Compass size={18} aria-hidden />, () => { setOpen(null); onRecenter(); })}
      {tool(t(projection === "globe" ? "projection.flat" : "projection.globe"),
        projection === "globe" ? <MapIcon size={18} aria-hidden /> : <Globe size={18} aria-hidden />,
        () => setProjection(projection === "globe" ? "mercator" : "globe"))}
      {tool(t("theme.label"), dark ? <Sun size={18} aria-hidden /> : <Moon size={18} aria-hidden />, () => setTheme(dark ? "light" : "dark"))}
      <button type="button" aria-label={t("lang.switch")} title={compact ? undefined : t("lang.switch")}
        onClick={() => setLang(lang === "en" ? "de" : "en")} className={`${btn} text-[13px] font-semibold tracking-wide`}>
        {t("lang.short")}
      </button>
      {panel("overview", t("tools.overview"), <BarChart2 size={18} aria-hidden />, t("tools.overviewSub"), (
        <div className="flex flex-col gap-4">
          <GlobalStrip atlas={atlas} year={year} />
          <section>
            <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-inkMuted">{t("sites.label")}</h3>
            <SiteButtons atlas={atlas} bare onPick={(c, s) => { setOpen(null); onSite(c, s); }} />
          </section>
          <SourceLine>{t(layer.source)}</SourceLine>
        </div>
      ), true)}
      {!EMBEDDED && (
        <a href={SLIDES_URL} target="_blank" rel="noopener" aria-label={t("tools.slides")} title={compact ? undefined : t("tools.slides")} className={btn}>
          <Presentation size={18} aria-hidden />
        </a>
      )}
      {panel("help", t("help.title"), <HelpCircle size={18} aria-hidden />, t("help.sub"), <HelpContent touch={touch} />, true)}
    </div>
  );
}
