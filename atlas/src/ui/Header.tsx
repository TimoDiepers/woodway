import { Moon, Sun } from "lucide-react";
import { useAtlas } from "@/store";
import { useT } from "@/i18n/useT";
import { useMediaQuery } from "@/lib/useMediaQuery";

export function Header() {
  const t = useT();
  const { lang, setLang, theme, setTheme } = useAtlas();
  const prefersDark = useMediaQuery("(prefers-color-scheme: dark)");
  const dark = theme === "dark" || (theme === "system" && prefersDark);
  return (
    <header className="pointer-events-auto flex items-start justify-between gap-4">
      <div>
        <h1 className="text-3xl font-semibold leading-tight">{t("app.title")}</h1>
        <p className="text-sm text-inkMuted">{t("app.subtitle")}</p>
      </div>
      <div className="panel flex items-center gap-1 p-1">
        <button onClick={() => setLang(lang === "en" ? "de" : "en")} className="rounded px-2 py-1 text-sm hover:bg-ink/5">{t("lang.switch")}</button>
        <button aria-label={t("theme.label")} onClick={() => setTheme(dark ? "light" : "dark")} className="grid h-8 w-8 place-items-center rounded hover:bg-ink/5">
          {dark ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  );
}
