// The HTML deck's slides, read at build time so the React deck follows every edit of deck/src/slides.
const files = import.meta.glob("../../../deck/src/slides/*.html", { query: "?raw", import: "default", eager: true }) as Record<string, string>;

const SECTIONS = Object.keys(files).sort().flatMap((f) =>
  [...files[f].matchAll(/<section class="slide([^"]*)"[^>]*data-title="([^"]*)"/g)].map((m) => ({ cls: m[1], title: m[2] })));

export const DECK_TITLES: string[] = SECTIONS.map((s) => s.title);
/** Chapter openers ("slide chapter …"): the overview's headings. */
export const DECK_CHAPTER: boolean[] = SECTIONS.map((s) => /\bchapter\b/.test(s.cls));

export function deckIndex(title: string): number {
  const i = DECK_TITLES.indexOf(title);
  if (i < 0) throw new Error(`no deck slide titled "${title}"`);
  return i;
}
