# React Deck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A second, optional version of the talk (`atlas/talk.html`) that plays the existing HTML deck slide by slide in an iframe and inserts five live atlas slides built from the atlas's React components.

**Architecture:** A React shell owns keys, progress and notes. A sequence (derived from slide titles in `deck/src/slides/*.html`) lists every deck slide in order plus the atlas slides at their places. Deck slides run inside an iframe of the built HTML deck in a new `?host` mode, steered over the deck's existing postMessage protocol; atlas slides are React components in the deck's 1600×900 frame.

**Tech Stack:** as the atlas (Vite 5, React 18, TS 5, Tailwind 3, MapLibre 5, Vitest 2); vanilla JS in `deck/src/js/deck.js`.

**Spec:** `docs/superpowers/specs/2026-10-10-react-deck-design.md`

## Global Constraints

- The HTML deck stays the default and keeps working unchanged without `?host` (no visual or behavioural change for existing URLs).
- Every number on an atlas slide is computed in the browser from the atlas export; no typed numbers.
- Atlas slides are German, in the deck's look: 1600×900 frame, Literata headline in the chapter colour, `Takeaway` and `SourceLine` from `atlas/src/ui/deck` (atlas Task 5b), ground line in the chapter colour; chapter `data-ch` "vergleich" for slides 1–2, "dac" for 3–4, none for 5.
- Atlas components are reused, not copied: import from `@/map/AtlasMap`, `@/ui/Legend`, `@/ui/CellPanel`, `@/ui/GlobalStrip`, `@/model/*`, `@/data/load`.
- Commits without Co-Authored-By and without "Generated with Claude Code".
- Deck URL: production `../index.html?host`, development `/deck/index.html?host`.

## Review Focus

1. Pressing ← on the first step of an atlas slide must land on the previous deck slide's **last** step, not its first. → Task 3 `navigation.test.ts` "back into a deck slide lands on its end".
2. Fast key repeat while the iframe has not yet answered must not skip or double-step. → Task 3 "ignores keys until the deck answered".
3. A deck slide added, removed or renamed later must not silently shift atlas slides to wrong places. → Task 2 `sequence.test.ts` "anchors exist".
4. The iframe failing to load (deck not built) must show a message, not a blank stage. → Task 3 "deck missing".
5. The default HTML deck must behave exactly as before without `?host`. → Task 1 headless check.

---

### Task 1: HTML deck: host mode, goto with step, atlas link slide

**Files:**
- Modify: `deck/src/js/deck.js` (Deck constructor, `onMessage`)
- Modify: `deck/src/css/deck.css` (host rules)
- Modify: `deck/src/slides/07_backup.html` (append one slide)
- Verify: headless script in the scratchpad (not committed)

**Interfaces:**
- Produces: deck query `?host`; message `{src:"dv", cmd:"goto", n, step?: number | "end"}`.

- [ ] **Step 1: Write the headless check (fails first)**

A puppeteer-core script (Chrome at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`; puppeteer-core lives in `/private/tmp/claude-501/-Users-timodiepers-Documents-Coding-dissvortrag/e3673260-30d4-4c41-a070-652c40137a03/scratchpad/node_modules` — symlink it into your scratch dir) that serves `deck/dist` (`python3 -m http.server 8770` in `deck/dist`) and checks:
- `index.html`: `#menu-fab` visible, `html` lacks class `host`;
- `index.html?host`: `#menu-fab` and `#hint` not displayed, `html.host` present;
- in `?host`, posting `{src:"dv", cmd:"goto", n: 20, step: "end"}` from `window` itself (deck listens to `message` from any source) → `deck.i === 20` and `deck.step === deck.steps(deck.slides[20])`;
- the last slide's `data-title` is `"Atlas: alle Ergebnisse interaktiv"`.

Run `python3 deck/build.py` then the script. Expected: FAIL on the `host` checks.

- [ ] **Step 2: Implement**

In `deck.js`, in the Deck constructor next to `this.embed = …`:

```js
    this.host = location.search.includes('host');      // inside the React deck: it supplies the chrome
    if (this.host) document.documentElement.classList.add('host');
```

In `onMessage`, replace the `goto` branch:

```js
    else if (d.cmd === 'goto' && Number.isInteger(d.n)) {
      const n = Math.max(0, Math.min(this.slides.length - 1, d.n));
      this.go(n, d.step === 'end' ? this.steps(this.slides[n]) : Number.isInteger(d.step) ? d.step : 0);
    }
```

and after every navigation in host mode the parent must hear the new state: at the end of `go(…)` (where the deck already calls `this.sync()`, check; if not, add `this.sync();` as its last line — `sync` is a no-op without a peer).

In `deck.css` (end of file):

```css
/* inside the React deck (?host): the shell draws menu, hint and progress */
.host #menu-fab, .host .hint, .host .progress { display: none !important; }
```

Append to `deck/src/slides/07_backup.html`:

```html
<!-- Atlas -->
<section class="slide backup" data-title="Atlas: alle Ergebnisse interaktiv">
  <header class="sh"><h2>Atlas: alle Ergebnisse interaktiv</h2></header>
  <div class="body" style="justify-content:center; gap:28px">
    <p class="lead rise">Jede Zelle, jedes Jahr: Waldtyp, Albedo, Temperaturwirkung eines Baums, DAC-Strom, Netto-Anteil und Ausbau, 2026 bis 2100.</p>
    <p class="rise" style="--d:200; font: 500 34px/1.3 var(--sans)"><a href="atlas/" style="color: var(--ch)">timodiepers.github.io/dissvortrag/atlas</a></p>
  </div>
  <p class="src">Dieselben Daten wie auf den Folien (atlas/export_atlas.py).</p>
  <aside class="notes"><p>Für Fragen zu einzelnen Orten: der Atlas zeigt jede 0,5°-Zelle mit ihrer ganzen Kette.</p></aside>
</section>
```

- [ ] **Step 3: Rebuild and re-run the check**

Run: `python3 deck/build.py && <your check script>`
Expected: all checks pass; `index.html` without `?host` unchanged (menu button visible). Also run `uv run pytest -q tests/test_slide_numbers.py` (it reads deck facts) — expected pass.

- [ ] **Step 4: Commit**

```bash
git add deck/src
git commit -m "feat(deck): host mode for the React deck, goto with step, atlas link slide"
```

---

### Task 2: Talk entry, slide frame, sequence

**Files:**
- Create: `atlas/talk.html`, `atlas/src/talk/main.tsx`, `atlas/src/talk/frame.css`, `atlas/src/talk/deckSlides.ts`, `atlas/src/talk/sequence.ts`
- Modify: `atlas/vite.config.ts` (second entry + dev middleware for `/deck/`)
- Test: `atlas/tests/talk/sequence.test.ts`

**Interfaces:**
- Produces:

```ts
// deckSlides.ts — titles of the HTML deck's slides in order, read from deck/src/slides/*.html at build time
export const DECK_TITLES: string[]
export function deckIndex(title: string): number            // throws if the title is not a deck slide
// sequence.ts
export type AtlasSlideId = "jedeZelle" | "albedo" | "dacStrom" | "dacAusbau" | "atlas";
export type Item = { kind: "deck"; i: number } | { kind: "atlas"; id: AtlasSlideId };
export const ANCHORS: { id: AtlasSlideId; after: string }[]
export const SEQUENCE: Item[]
export const MAIN_END: number   // index in SEQUENCE of the first backup item
```

- [ ] **Step 1: Write the failing test**

`atlas/tests/talk/sequence.test.ts`:

```ts
import { DECK_TITLES, deckIndex } from "@/talk/deckSlides";
import { ANCHORS, SEQUENCE } from "@/talk/sequence";

describe("sequence", () => {
  it("reads the deck's slide titles in order", () => {
    expect(DECK_TITLES[0]).toBe("Titel");
    expect(DECK_TITLES).toContain("Danke");
    expect(DECK_TITLES.at(-1)).toBe("Atlas: alle Ergebnisse interaktiv");
  });
  it("anchors exist", () => {
    for (const a of ANCHORS) expect(() => deckIndex(a.after)).not.toThrow();
  });
  it("covers every deck slide exactly once, in order", () => {
    const deck = SEQUENCE.filter((s) => s.kind === "deck").map((s) => (s as { i: number }).i);
    expect(deck).toEqual(DECK_TITLES.map((_, i) => i));
  });
  it("places each atlas slide right after its anchor", () => {
    for (const a of ANCHORS) {
      const k = SEQUENCE.findIndex((s) => s.kind === "atlas" && s.id === a.id);
      expect(SEQUENCE[k - 1]).toEqual({ kind: "deck", i: deckIndex(a.after) });
    }
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd atlas && npx vitest run tests/talk/sequence.test.ts` — Expected: FAIL, modules missing.

- [ ] **Step 3: Implement**

`atlas/src/talk/deckSlides.ts`:

```ts
// The HTML deck's slides, read at build time so the React deck follows every edit of deck/src/slides.
const files = import.meta.glob("../../../deck/src/slides/*.html", { query: "?raw", import: "default", eager: true }) as Record<string, string>;

export const DECK_TITLES: string[] = Object.keys(files).sort().flatMap((f) =>
  [...files[f].matchAll(/<section class="slide[^"]*"[^>]*data-title="([^"]*)"/g)].map((m) => m[1]));

export function deckIndex(title: string): number {
  const i = DECK_TITLES.indexOf(title);
  if (i < 0) throw new Error(`no deck slide titled "${title}"`);
  return i;
}
```

`atlas/src/talk/sequence.ts`:

```ts
import { DECK_TITLES, deckIndex } from "./deckSlides";

export type AtlasSlideId = "jedeZelle" | "albedo" | "dacStrom" | "dacAusbau" | "atlas";
export type Item = { kind: "deck"; i: number } | { kind: "atlas"; id: AtlasSlideId };

export const ANCHORS: { id: AtlasSlideId; after: string }[] = [
  { id: "jedeZelle", after: "Temperaturwirkung eines Baums je Ort" },
  { id: "albedo", after: "Temperaturwirkung eines Baums je Ort" },
  { id: "dacStrom", after: "DAC-Modell" },
  { id: "dacAusbau", after: "DAC-Ausbau" },
  { id: "atlas", after: "Atlas: alle Ergebnisse interaktiv" },
];

export const SEQUENCE: Item[] = DECK_TITLES.flatMap((title, i) => [
  { kind: "deck", i } as Item,
  ...ANCHORS.filter((a) => a.after === title).map((a) => ({ kind: "atlas", id: a.id }) as Item),
]);

export const MAIN_END = SEQUENCE.findIndex((s) => s.kind === "deck" && s.i === deckIndex("Danke") + 1);
```

Note on the test "places each atlas slide right after its anchor": two slides share the anchor "Temperaturwirkung eines Baums je Ort", so the second one follows the first atlas slide, not the deck slide. Adjust the test's loop to compare against the last deck item before it: `const prevDeck = SEQUENCE.slice(0, k).reverse().find((s) => s.kind === "deck")` and expect it to equal `{kind: "deck", i: deckIndex(a.after)}`.

`atlas/talk.html`: copy `atlas/index.html`, change `<title>` to `Vortrag · Auf dem Holzweg? (React)`, `lang="de"`, and the script to `/src/talk/main.tsx`.

`atlas/src/talk/main.tsx`: like `src/main.tsx` but renders `TalkApp` from `./TalkApp` (Task 3; for now a placeholder component exporting `<p>Talk</p>` so the build works) and imports `./frame.css`.

`atlas/src/talk/frame.css` — the deck's slide frame for React slides:

```css
.talk-stage { position: fixed; inset: 0; overflow: hidden; background: var(--stage, var(--paper)); }
.talk-deck { position: absolute; left: 50%; top: 50%; width: 1600px; height: 900px; transform-origin: center; }
.talk-deck iframe { position: absolute; inset: 0; width: 1600px; height: 900px; border: 0; background: transparent; }
.rslide { position: absolute; inset: 0; padding: 64px 88px 56px; display: flex; flex-direction: column; background: var(--paper); color: var(--ink); }
.rslide .sh { display: flex; justify-content: space-between; gap: 48px; margin-bottom: 28px; }
.rslide .sh h2 { font: 600 50px/1.08 var(--serif); letter-spacing: -0.015em; font-variation-settings: "opsz" 72; color: var(--ch); max-width: 1180px; }
.rslide .num { position: absolute; left: 88px; bottom: 20px; font: 500 14px/1 var(--sans); color: var(--muted); }
.talk-ground { position: fixed; left: 0; right: 0; bottom: 0; height: 6px; background: var(--ch, transparent); }
```

`atlas/vite.config.ts`: add `build.rollupOptions.input = { main: path.resolve(__dirname, "index.html"), talk: path.resolve(__dirname, "talk.html") }`, `server.fs.allow: [".."]` (the glob reads `../deck/src/slides`), and a dev-only plugin that serves `../deck/dist` under `/deck/`:

```ts
import fs from "node:fs";
const deckDist = path.resolve(__dirname, "../deck/dist");
const serveDeck = {
  name: "serve-deck",
  configureServer(server: import("vite").ViteDevServer) {
    server.middlewares.use("/deck", (req, res, next) => {
      const p = path.join(deckDist, decodeURIComponent((req.url ?? "/").split("?")[0]).replace(/^\/$/, "/index.html"));
      if (!p.startsWith(deckDist) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) return next();
      res.setHeader("Content-Type", p.endsWith(".html") ? "text/html" : p.endsWith(".js") ? "text/javascript" : p.endsWith(".css") ? "text/css" : "application/octet-stream");
      fs.createReadStream(p).pipe(res);
    });
  },
};
```

and add `serveDeck` to `plugins`.

- [ ] **Step 4: Run tests and build**

Run: `cd atlas && npx vitest run && npx tsc -b && npm run build`
Expected: all PASS; `dist/talk.html` exists.

- [ ] **Step 5: Commit**

```bash
git add atlas
git commit -m "feat(talk): second entry, slide frame and the talk sequence from the deck's titles"
```

---

### Task 3: Shell and deck frame navigation

**Files:**
- Create: `atlas/src/talk/navigation.ts`, `atlas/src/talk/DeckFrame.tsx`, `atlas/src/talk/TalkApp.tsx`
- Test: `atlas/tests/talk/navigation.test.ts`

**Interfaces:**
- Consumes: `SEQUENCE`, `Item` (Task 2).
- Produces:

```ts
// navigation.ts — pure state machine, no DOM
export interface DeckState { i: number; step: number; ni: number; ns: number }   // as the deck reports it
export interface Pos { k: number; step: number }   // k = index in SEQUENCE; step only used on atlas items
export type Cmd = { send: "next" | "prev" } | { send: "goto"; n: number; step: number | "end" } | null;
export function next(seq: Item[], pos: Pos, deck: DeckState | null, atlasSteps: (id: AtlasSlideId) => number): { pos: Pos; cmd: Cmd }
export function prev(seq: Item[], pos: Pos, deck: DeckState | null, atlasSteps: (id: AtlasSlideId) => number): { pos: Pos; cmd: Cmd }
export function follow(seq: Item[], pos: Pos, deck: DeckState): Pos   // keep k in step with the deck after it moved by itself
```

Rules:
- On a deck item with `deck` known: `next` → if `deck.ni === deck.i` (more clicks here) or `seq[k+1]` is deck item `deck.i + 1` → `{send: "next"}`, `k` advances only when the deck reports the new slide (`follow`). Else (`seq[k+1]` is atlas) → `pos = {k: k+1, step: 0}`, no command.
- On an atlas item: `next` → `step < atlasSteps(id)` → `step+1`; else if `seq[k+1]` is deck item j → `pos = {k+1, 0}`, `{send:"goto", n: j, step: 0}`; else next atlas item.
- `prev` mirrors it; from an atlas item at step 0 to a deck item j → `{send: "goto", n: j, step: "end"}`.
- With `deck === null` (iframe not answered yet) on a deck item: return the same pos and `cmd: null` (keys ignored).
- At the ends: unchanged.

- [ ] **Step 1: Write the failing tests**

`atlas/tests/talk/navigation.test.ts`:

```ts
import { next, prev, follow, type DeckState } from "@/talk/navigation";
import type { Item } from "@/talk/sequence";

const seq: Item[] = [{ kind: "deck", i: 0 }, { kind: "deck", i: 1 }, { kind: "atlas", id: "jedeZelle" }, { kind: "deck", i: 2 }];
const steps = () => 2;
const st = (i: number, step: number, last: number): DeckState => ({ i, step, ni: step < last ? i : i + 1, ns: step < last ? step + 1 : 0 });

describe("navigation", () => {
  it("forwards next while the deck has clicks", () => {
    expect(next(seq, { k: 0, step: 0 }, st(0, 0, 1), steps)).toEqual({ pos: { k: 0, step: 0 }, cmd: { send: "next" } });
  });
  it("follows the deck onto its next slide", () => {
    expect(follow(seq, { k: 0, step: 0 }, st(1, 0, 3))).toEqual({ k: 1, step: 0 });
  });
  it("leaves the deck for an atlas slide after the last click", () => {
    expect(next(seq, { k: 1, step: 0 }, st(1, 3, 3), steps)).toEqual({ pos: { k: 2, step: 0 }, cmd: null });
  });
  it("steps through the atlas slide, then back into the deck", () => {
    expect(next(seq, { k: 2, step: 1 }, st(1, 3, 3), steps).pos).toEqual({ k: 2, step: 2 });
    expect(next(seq, { k: 2, step: 2 }, st(1, 3, 3), steps)).toEqual({ pos: { k: 3, step: 0 }, cmd: { send: "goto", n: 2, step: 0 } });
  });
  it("back into a deck slide lands on its end", () => {
    expect(prev(seq, { k: 2, step: 0 }, st(1, 3, 3), steps)).toEqual({ pos: { k: 1, step: 0 }, cmd: { send: "goto", n: 1, step: "end" } });
  });
  it("ignores keys until the deck answered", () => {
    expect(next(seq, { k: 0, step: 0 }, null, steps)).toEqual({ pos: { k: 0, step: 0 }, cmd: null });
  });
  it("stays put at the ends", () => {
    expect(prev(seq, { k: 0, step: 0 }, st(0, 0, 1), steps).cmd).toEqual(null);
    expect(next(seq, { k: 3, step: 0 }, st(2, 0, 0), steps).cmd).toEqual(null);
  });
});
```

Note: at the very first deck slide with `step === 0`, `prev` returns `cmd: null`; at the last deck slide with `ni > i` and nothing after it, `next` returns `cmd: null`.

- [ ] **Step 2: Run to verify failure**

Run: `cd atlas && npx vitest run tests/talk/navigation.test.ts` — Expected: FAIL, module missing.

- [ ] **Step 3: Implement `navigation.ts` per the rules above, then the components**

`DeckFrame.tsx`: renders `<iframe src={DECK_URL} title="Vortrag">` where `DECK_URL = import.meta.env.DEV ? "/deck/index.html?host" : "../index.html?host"`; on `load` posts `{src:"dv", cmd:"hello"}`; listens to `message` events with `data.src === "dv" && data.state` and calls `onState(state)`; exposes `send(cmd)` through a ref (`useImperativeHandle`). If no state arrives within 4 s of `load`, or the iframe errors, calls `onMissing()`.

`TalkApp.tsx`:
- loads the atlas once (`loadAtlas("data/")`), sets the store's `lang` to `"de"`;
- keeps `pos`, `deck: DeckState | null`, `notesOpen`;
- keydown (window): → / Space / PageDown / Enter → `next`; ← / PageUp / Backspace → `prev`; `Home` → first item (`goto 0`); `b` → `MAIN_END`; `n` → toggle notes; `f` → fullscreen. Apply the returned `cmd` via the frame ref.
- On every deck state: `setDeck(s); setPos(p => seq[p.k].kind === "deck" ? follow(SEQUENCE, p, s) : p)`.
- Renders `.talk-stage` > `.talk-deck` scaled with `scale(min(innerWidth/1600, innerHeight/900))`; the iframe always mounted (hidden with `visibility:hidden` while an atlas item is shown, so its state survives); the current atlas slide (Task 4; until then a placeholder `<section className="rslide"><h2>{id}</h2></section>`); a progress bar (`k / (SEQUENCE.length - 1)`), the notes drawer showing the atlas slide's notes; when `onMissing` fired: `<p role="alert">Das HTML-Deck fehlt: erst python deck/build.py ausführen.</p>`.
- Forward keys pressed while the iframe has focus: the deck in `?host` mode still binds its own keys — add to Task 1's host mode? No: instead the shell keeps focus by setting `tabIndex={-1}` and `pointer-events: none` on the iframe in host mode; clicks on the stage advance like →.

- [ ] **Step 4: Run tests, try it**

Run: `cd atlas && npx vitest run && npx tsc -b`; then `python3 ../deck/build.py` (from repo root: `uv run python deck/build.py`) and `npm run dev`, open `/talk.html`.
Expected: tests PASS; the deck's title slide shows; → steps through the deck with its animations; after "Temperaturwirkung eines Baums je Ort" the placeholder atlas slide appears; ← returns to that deck slide's last step.

- [ ] **Step 5: Commit**

```bash
git add atlas
git commit -m "feat(talk): shell that plays the HTML deck and switches to atlas slides"
```

---

### Task 4: The five atlas slides

**Files:**
- Create: `atlas/src/talk/stats.ts`, `atlas/src/talk/AtlasSlide.tsx`, `atlas/src/talk/slides.ts`
- Modify: `atlas/src/talk/TalkApp.tsx` (render real slides; `atlasSteps` from `slides.ts`)
- Test: `atlas/tests/talk/stats.test.ts`, `atlas/tests/talk/AtlasSlide.test.tsx`

**Interfaces:**
- Consumes: `Atlas`, `deltaT`, `netShare`, `dacNet`, `layerById`, `AtlasMap`, `Legend`, `GlobalStrip`, `CellPanel`, `LayerPicker`, `TimeSlider` (atlas), `Takeaway`, `SourceLine` (atlas Task 5b).
- Produces:

```ts
// stats.ts
export function coolingShare(at: Atlas, year: number): number          // reforestable area where a tree cools / all reforestable area
export function medianNetShare(at: Atlas, year: number): number        // area-weighted median of netShare over forest cells
export function medianDacNet(at: Atlas, year: number): number          // median of dacNet over cells where DAC is possible
export function dacCapacityGt(at: Atlas, year: number): number         // meta.global.dacCapacityGt at that year
// slides.ts
export interface AtlasSlideDef { id: AtlasSlideId; title: string; ch?: "vergleich" | "dac"; layer: LayerId;
  years: number[];                       // year per step; the map animates between them
  sitesFrom?: number;                    // step from which the three example sites are marked
  takeaway(at: Atlas, step: number): string; source: string; notes: string[]; free?: boolean }
export const SLIDES: Record<AtlasSlideId, AtlasSlideDef>
export const atlasSteps: (id: AtlasSlideId) => number   // SLIDES[id].years.length - 1 (+1 if sitesFrom)
```

- [ ] **Step 1: Write the failing tests**

`atlas/tests/talk/stats.test.ts` (reads the real export like `tests/model.test.ts`):

```ts
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import type { Atlas } from "@/data/types";
import { coolingShare, medianDacNet, dacCapacityGt } from "@/talk/stats";

const DIR = path.resolve(__dirname, "../../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;
let at: Atlas;
beforeAll(async () => { at = await loadAtlas("data/", diskFetch); });

describe("talk stats", () => {
  it("cooling share in 2100 is the talk's 0.39 of 0.83 Gha", () => {
    const g = at.meta.global.areasGha;
    expect(coolingShare(at, 2100)).toBeCloseTo(g.kuehlt / g.alle, 2);
  });
  it("DAC median net share 2026 is 46 %", () => {
    expect(medianDacNet(at, 2026)).toBeCloseTo(0.4647, 3);
  });
  it("DAC capacity follows the global path", () => {
    const k = at.meta.global.years.indexOf(2100);
    expect(dacCapacityGt(at, 2100)).toBe(at.meta.global.dacCapacityGt[k]);
  });
});
```

`atlas/tests/talk/AtlasSlide.test.tsx` (map mocked like `tests/App.test.tsx`): render `<AtlasSlide def={SLIDES.jedeZelle} atlas={at} step={0} />` → heading "Jede Zelle, jedes Jahr", a `.takeaway` whose text contains a percentage, a `.src` line; `step={2}` → takeaway text contains "2100".

- [ ] **Step 2: Run to verify failure**

Run: `cd atlas && npx vitest run tests/talk` — Expected: FAIL, modules missing.

- [ ] **Step 3: Implement**

`stats.ts`: loops over the 259 200 cells once per call (fast enough: < 10 ms); area weights from `at.f.area`; medians via sorting the finite values (weighted median: sort by value, walk cumulative area to half).

`slides.ts` (German texts; numbers only through `takeaway()` with `toLocaleString("de-DE")`):
- `jedeZelle`: title "Jede Zelle, jedes Jahr", ch "vergleich", layer "deltaT", years [2030, 2050, 2100], sitesFrom 3 (one extra click marks the sites), takeaway: `${pct(coolingShare(at, year))} der wiederbewaldbaren Fläche: dort kühlt ein Baum im Jahr ${year}.`, source "Eigenes Modell: typischer Wald der Zelle, gepflanzt 2026, FaIR (Leach et al. 2021), SSP2-4,5; Fläche Walker et al. 2022.", notes: two short paragraphs ("Dieselbe Rechnung wie für Aachen, jetzt für jede Zelle …", "Klick: das Jahr läuft …").
- `albedo`: title "Wo die Albedo den Kohlenstoff auffrisst", ch "vergleich", layer "netShare", years [2100], takeaway `Im Mittel bleiben ${pct(medianNetShare(at, 2100))} der CO₂-Wirkung nach Abzug der Albedo.`, source as above + "Albedo: Duveiller et al. 2018".
- `dacStrom`: title "DAC wird mit dem Strom sauber", ch "dac", layer "dacNet", years [2026, 2040, 2070], takeaway `${year}: Im Median bleiben ${pct(medianDacNet(at, year))} jeder entnommenen Tonne.`, source "Eigenes Modell: Sorbens-DAC mit Wärmepumpe (Sendi et al. 2022), Strommix REMIND-EU SSP2-NDC über premise."
- `dacAusbau`: title "Wo DAC gebaut wird", ch "dac", layer "dacBuild", years [2026, 2100] (the step animates through all years), takeaway `${dacCapacityGt(at, 2100).toLocaleString("de-DE", {maximumFractionDigits: 1})} Gt CO₂ pro Jahr im Jahr 2100, an den Speichern mit dem höchsten Netto-Anteil.`, source "Eigene Optimierung (Gidden et al. 2025 Speicher, Hochlauf +20 %/a)."
- `atlas`: title "Atlas", free: true, layer "deltaT", years [2100], takeaway "Jede Zelle anklicken: Waldtyp, Wachstum, Antrieb, Temperatur und DAC an diesem Ort.", source "Alle Daten: atlas/export_atlas.py."

`AtlasSlide.tsx`: `<section className="rslide" data-ch={def.ch}>` with header `<h2>`, a map area (`flex:1; position:relative`) holding `AtlasMap` (no hover, `projection="mercator"`, `initialView={{longitude: 10, latitude: 20, zoom: 1.15}}`, sites from `sitesFrom`), the `Legend` bottom-left over the map, the `Takeaway` (size "slide") under the map, `SourceLine` at the foot, and the slide number. The year animates between `years[step-1]` and `years[step]` over 1.2 s with `requestAnimationFrame` (instant when the user prefers reduced motion). `free` slides render the full atlas UI instead (`LayerPicker`, `TimeSlider`, `CellPanel`, `GlobalStrip`) wired to the store.

In `TalkApp.tsx`, replace the placeholder with `<AtlasSlide def={SLIDES[item.id]} atlas={atlas} step={pos.step} />` and pass `atlasSteps` to `next`/`prev`; set `--ch` on the stage for the ground line.

- [ ] **Step 4: Run tests, look at it**

Run: `cd atlas && npx vitest run && npx tsc -b && npm run dev` → `/talk.html`.
Expected: tests PASS; each atlas slide reads like a deck slide (paper, Literata headline in the chapter colour, takeaway box with leaf), the year animates on each click, the numbers match the tests.

- [ ] **Step 5: Commit**

```bash
git add atlas
git commit -m "feat(talk): five live atlas slides with numbers computed from the export"
```

---

### Task 5: Deploy, docs, run-through

**Files:**
- Modify: `.github/workflows/pages.yml` (deck/dist must be built before the atlas copies in; the talk lives at `/atlas/talk.html`), `README.md`, `atlas/README.md`

- [ ] **Step 1:** Make sure the Pages workflow runs `python deck/build.py` before `npm run build` in `atlas/` (the glob reads `deck/src/slides`, not dist — but the order keeps it obvious) and copies `atlas/dist` to `deck/dist/atlas`. The talk's production deck URL `../index.html?host` then resolves to the deck at the site root.
- [ ] **Step 2:** README: add "**Vortrag (React, mit Live-Karten):** https://timodiepers.github.io/dissvortrag/atlas/talk.html"; `atlas/README.md`: a "Talk" section (`npm run dev` → `/talk.html`, needs `uv run python deck/build.py` first; sequence in `src/talk/sequence.ts`, slides in `src/talk/slides.ts`).
- [ ] **Step 3: Run-through** — build both (`uv run python deck/build.py && cd atlas && npm run build`), assemble like Pages (`cp -R atlas/dist deck/dist/atlas`), serve `deck/dist` and open `/atlas/talk.html` headless at 1600×900: press → through the whole talk (deck slides plus the five atlas slides) and ← back across each boundary; screenshot each atlas slide; no console errors. Fix everything found in one batch.
- [ ] **Step 4: Commit and push**

```bash
git add .github/workflows/pages.yml README.md atlas/README.md
git commit -m "feat(talk): deploy the React deck with the atlas, docs"
git push origin HEAD:main
```
