import { en } from "./en";
import { de } from "./de";
import { useAtlas } from "@/store";

export type Key = keyof typeof en;
export type Lang = "en" | "de";
const DICT: Record<Lang, Record<Key, string>> = { en, de };

export function translate(lang: Lang, key: Key, vars?: Record<string, string | number>): string {
  let s = DICT[lang][key] ?? en[key];
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, String(v));
  return s;
}

export function useT() {
  const lang = useAtlas((s) => s.lang);
  return (key: Key, vars?: Record<string, string | number>) => translate(lang, key, vars);
}

/** Numbers in the language's style: 1,234.5 / 1.234,5. */
export function useNum() {
  const lang = useAtlas((s) => s.lang);
  return (v: number, digits = 0) =>
    v.toLocaleString(lang === "de" ? "de-DE" : "en-GB", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}
