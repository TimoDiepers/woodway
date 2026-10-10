// The HTML deck's slides, read at build time so the React deck follows every edit of deck/src/slides.
const files = import.meta.glob("../../../deck/src/slides/*.html", { query: "?raw", import: "default", eager: true }) as Record<string, string>;

export const DECK_TITLES: string[] = Object.keys(files).sort().flatMap((f) =>
  [...files[f].matchAll(/<section class="slide[^"]*"[^>]*data-title="([^"]*)"/g)].map((m) => m[1]));

export function deckIndex(title: string): number {
  const i = DECK_TITLES.indexOf(title);
  if (i < 0) throw new Error(`no deck slide titled "${title}"`);
  return i;
}
