import { useEffect, useRef } from "react";
import { ArrowRight, Presentation } from "lucide-react";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { SLIDES_URL } from "@/ui/ToolColumn";

/**
 * The first visit's front page: what this site is (the model behind Timo Diepers' PhD defence), what was computed,
 * and two ways in. The map loads behind the blurred backdrop meanwhile. Shown once; never inside the deck's iframe.
 */
export function Welcome() {
  const t = useT();
  const { lang, setLang, markWelcomeSeen } = useAtlas();
  const primary = useRef<HTMLButtonElement>(null);
  useEffect(() => { primary.current?.focus(); }, []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") { e.preventDefault(); markWelcomeSeen(); } };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [markWelcomeSeen]);

  return (
    <div className="fade-in fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-paper/45 p-4 backdrop-blur-md"
      style={{ paddingTop: "max(1rem, env(safe-area-inset-top))", paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}>
      <div role="dialog" aria-modal="true" aria-labelledby="welcome-title" aria-describedby="welcome-body"
        className="panel relative w-full max-w-[34rem] px-5 py-5 sm:px-7 sm:py-6">
        <div role="group" aria-label={t("lang.label")} className="absolute right-3 top-3 flex text-xs font-medium">
          {(["en", "de"] as const).map((l) => (
            <button key={l} type="button" aria-pressed={lang === l} onClick={() => setLang(l)}
              className="rounded px-1.5 py-1 uppercase text-inkMuted hover:text-ink aria-pressed:text-ink aria-pressed:underline aria-pressed:underline-offset-4">
              {l}
            </button>
          ))}
        </div>
        <h2 id="welcome-title" className="pr-16 font-serif text-[1.75rem] font-semibold leading-tight sm:text-3xl">{t("welcome.title")}</h2>
        <p id="welcome-body" className="mt-3 text-[15px] leading-relaxed text-ink">{t("welcome.intro")}</p>
        <div className="mt-5 flex flex-col gap-2 sm:flex-row sm:items-center">
          <button ref={primary} type="button" onClick={markWelcomeSeen}
            className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-accent px-5 font-serif text-[15px] font-semibold text-panel transition-colors hover:bg-accent/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:ring-offset-2 focus-visible:ring-offset-panel">
            {t("welcome.explore")}<ArrowRight size={16} aria-hidden />
          </button>
          <a href={SLIDES_URL} target="_blank" rel="noopener" onClick={markWelcomeSeen}
            className="inline-flex h-11 items-center justify-center gap-2 rounded-md border border-panelBorder px-4 font-serif text-[15px] font-medium text-ink transition-colors hover:bg-ink/[0.06] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50">
            <Presentation size={16} className="text-inkMuted" aria-hidden />{t("welcome.slides")}
          </a>
        </div>
        <p className="mt-2.5 text-xs text-inkMuted">{t("welcome.slidesNote")}</p>
      </div>
    </div>
  );
}
