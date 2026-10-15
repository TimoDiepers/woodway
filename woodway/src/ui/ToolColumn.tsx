import { Fragment, useState, type ReactNode } from "react";
import { ChartSpline, Compass, Ellipsis, ExternalLink, HelpCircle, Presentation, Search } from "lucide-react";
import type { Atlas } from "@/data/types";
import type { Layer } from "@/model/layers";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { useMediaQuery } from "@/lib/useMediaQuery";
import { ToolPanel } from "@/ui/ToolPanel";
import { HelpContent } from "@/ui/HelpContent";
import { PlaceSearch, type Place } from "@/ui/PlaceSearch";
import { GlobalStrip } from "@/ui/GlobalStrip";

type PanelId = "search" | "world" | "help" | "more";

/** The talk's slides: published next to woodway under slides/; in development the dev server serves the built deck. */
const SLIDES_URL = import.meta.env.DEV ? "/deck/index.html" : "slides/";
/** inside the deck's own last slide, a link back to the deck would only open it a second time */
const EMBEDDED = typeof window !== "undefined" && window.parent !== window;

/**
 * The map's tools in one card: a column against the right edge on a phone, a row top right on a desktop.
 * Only what is reached for while exploring sits there (find, go home, how to read the map); the slides and the
 * display settings wait one tap further in "More", each with its name written out.
 */
export function ToolColumn({ atlas, layer, compact, onPlace, onRecenter }: { atlas: Atlas; layer: Layer; compact: boolean; onPlace(p: Place): void; onRecenter(): void }) {
  const t = useT();
  const year = useAtlas((s) => s.year);
  const touch = useMediaQuery("(pointer: coarse)") || compact;
  const [open, show] = useState<PanelId | null>(null);
  const toggle = (p: PanelId) => (o: boolean) => show(o ? p : open === p ? null : open);

  const btn = compact
    ? "grid h-11 w-11 place-items-center text-ink hover:bg-ink/5 active:bg-ink/10 aria-expanded:bg-ink/10"
    : "grid h-9 w-9 place-items-center rounded-md text-ink hover:bg-ink/5 aria-expanded:bg-ink/10";
  const tool = (id: string, label: string, icon: ReactNode, onClick?: () => void, expanded?: boolean) => (
    <button type="button" data-tool={id} aria-label={label} title={compact ? undefined : label} onClick={onClick} className={btn}
      {...(expanded !== undefined ? { "aria-expanded": expanded, "aria-haspopup": "dialog" as const } : {})}>{icon}</button>
  );
  const panel = (id: PanelId, label: string, icon: ReactNode, head: { title: string; sub?: string },
    body: ReactNode, opts: { wide?: boolean; edge?: "top" | "bottom" } = {}) => (
    <ToolPanel compact={compact} open={open === id} onOpenChange={toggle(id)} {...head} {...opts}
      trigger={tool(id, label, icon, compact ? () => show(open === id ? null : id) : undefined, open === id)}>{body}</ToolPanel>
  );

  const items = [
    // on a phone the search drops from the top: rising from the bottom it would sit under the keyboard
    <Fragment key="search">{panel("search", t("search.label"), <Search size={18} aria-hidden />, { title: t("search.label") },
      <PlaceSearch autoFocus onPick={(p) => { show(null); onPlace(p); }} />, { edge: "top" })}</Fragment>,
    <Fragment key="recenter">{tool("recenter", t("tools.recenter"), <Compass size={18} aria-hidden />, () => { show(null); onRecenter(); })}</Fragment>,
    // the whole world in one chart, as the deck's anchor: Very Low, the trees, a vegan world, DACCS
    <Fragment key="world">{panel("world", t("tools.world"), <ChartSpline size={18} aria-hidden />, { title: t("tools.world") },
      <GlobalStrip atlas={atlas} year={year} />, { wide: true })}</Fragment>,
    <Fragment key="help">{panel("help", t("help.title"), <HelpCircle size={18} aria-hidden />, { title: t("help.title"), sub: t("help.sub") },
      <HelpContent touch={touch} source={t(layer.source)} />, { wide: true })}</Fragment>,
    ...(compact ? [] : [<span key="sep" className="mx-0.5 h-5 w-px bg-[var(--paper-line)]" aria-hidden />]),
    <Fragment key="more">{panel("more", t("tools.more"), <Ellipsis size={18} aria-hidden />, { title: t("tools.more") }, <MoreMenu />)}</Fragment>,
  ];

  return (
    <div role="toolbar" aria-label={t("tools.label")} aria-orientation={compact ? "vertical" : "horizontal"}
      className={"panel pointer-events-auto flex overflow-hidden " + (compact ? "flex-col divide-y divide-[var(--paper-line)] rounded-xl" : "items-center gap-0.5 p-1")}>
      {/* on a phone the column reads from the top corner down: More first, search last */}
      {compact ? items.reverse() : items}
    </div>
  );
}

/** The slides as a named row, then the three display settings as segmented choices. */
function MoreMenu() {
  const t = useT();
  const { lang, setLang, theme, setTheme, projection, setProjection } = useAtlas();
  const row = "flex min-h-11 w-full items-center gap-3 rounded-md px-2 text-left text-sm font-medium text-ink hover:bg-ink/5 active:bg-ink/10";
  return (
    <div className="flex flex-col">
      <nav className="-mx-2 flex flex-col">
        {!EMBEDDED && (
          <a href={SLIDES_URL} target="_blank" rel="noopener" className={row}>
            <Presentation size={18} className="shrink-0 text-inkMuted" aria-hidden />
            <span className="flex-1">{t("tools.slides")}</span>
            <ExternalLink size={14} className="shrink-0 text-inkMuted" aria-hidden />
          </a>
        )}
      </nav>
      <div className="mt-2 flex flex-col gap-2.5 border-t border-[var(--paper-line)] pt-3">
        <Choice label={t("projection.label")} value={projection} onChange={setProjection}
          options={[{ value: "globe", label: t("projection.globe") }, { value: "mercator", label: t("projection.flat") }]} />
        <Choice label={t("theme.label")} value={theme} onChange={setTheme}
          options={[{ value: "light", label: t("theme.light") }, { value: "dark", label: t("theme.dark") }, { value: "system", label: t("theme.system") }]} />
        {/* each language under its own name, so a visitor who reads only one still finds it */}
        <Choice label={t("lang.label")} value={lang} onChange={setLang}
          options={[{ value: "en", label: "English" }, { value: "de", label: "Deutsch" }]} />
      </div>
    </div>
  );
}

function Choice<T extends string>({ label, value, options, onChange }: {
  label: string; value: T; options: { value: T; label: string }[]; onChange(v: T): void;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-sm text-inkMuted">{label}</span>
      <div role="group" aria-label={label} className="flex rounded-lg border border-[var(--paper-line)] bg-paper/60 p-0.5">
        {options.map((o) => (
          <button key={o.value} type="button" aria-pressed={value === o.value} onClick={() => onChange(o.value)}
            className="h-8 rounded-md px-3 text-[13px] font-medium text-inkMuted transition-colors hover:text-ink [@media(pointer:coarse)]:h-10 aria-pressed:bg-panel aria-pressed:text-ink aria-pressed:shadow-[0_1px_2px_rgba(30,26,18,.18)]">
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}
