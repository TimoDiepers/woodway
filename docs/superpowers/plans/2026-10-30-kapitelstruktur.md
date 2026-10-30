# Kapitelstruktur Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Three chapters with two parts each, shown by one ring-and-disc system (overview, chapter slide, corner indicator), six part icons, and a muted part palette carried through formulas and charts.

**Architecture:** One chapter table in `deck.js` (`CHAPTERS`) drives the ring markup, the corner indicator and the chapter-slide parts. Rings are SVG built by one function (`ringSvg`). The overview → chapter slide motion is a FLIP of the disc (`Deck.enterChapter`, replacing `zoomInto`); chapter slide → first content slide reuses the existing `planFlight`/`flyHome` disc flight. Colours live as CSS custom properties; charts take the same hex values from `src/nbs/plots.py` constants and are re-exported.

**Tech Stack:** Static HTML deck (`deck/src`, built by `deck/build.py`), vanilla JS, CSS, KaTeX, ECharts data exported from matplotlib (`deck/export_charts.py`), Playwright (Python, via `uv run --with playwright`) for checks.

**Spec:** `docs/superpowers/specs/2026-10-30-kapitelstruktur-design.md`

## Global Constraints

- Chapter colours: Bäume `#304620`, Klima `#612f2d`, Potenzial `#04455f`.
- Part colours (fill / text): Kohlenstoff `#437d61`/`#105b3e`, Reflexion `#9d945f`/`#787136`, Strahlungsbilanz `#ba8d66`/`#96683e`, Temperatur `#985248`/`#762c26`, Baum `#4690a1`/`#006e81`, Welt `#316491`/`#004474`.
- Part names exactly: Kohlenstoff-Aufnahme, Reflexionsänderung, Strahlungsbilanz, Temperaturkurve, Kühlung eines Baums, Kühlung der Welt.
- Motion: disc glide 900 ms `cubic-bezier(.16,1,.3,1)`; ring arcs start at 700 ms and 1500 ms; part rows wipe (`clip-path`, 700 ms) at 800 ms and 1600 ms; arc colour change 600 ms. Backwards navigation and `prefers-reduced-motion`: final state, no motion.
- No numbering, no part icons in slide titles, sun/incoming light stays `--sun`/`--sun-ray`.
- Build: `uv run python deck/build.py`; preview via the running `deck/serve.py` on http://localhost:8765. The in-page editor must still edit chapter-slide texts.
- Commit only when Timo asks; no attribution lines.

## Review Focus

- Jumping straight to a slide (URL `#n`, menu, chapter button) mid-chapter: indicator must show the right chapter/part with no animation leftovers.
- Stepping backwards from the first content slide to the chapter slide: rings fully drawn, rows visible, no replayed motion.
- Presenter view and PDF export (`deck/export_pdf.py`, `still` mode): every slide renders its final state.
- Holzweg/DAC, Schluss, Backup slides: no indicator, no errors.
- Narrow / phone viewport: the indicator text stack must not overlap the slide title.

Each is checked by `structure_check.py` (Task 2) or the screenshot pass in Task 7.

---

### Task 1: Palette and part icons

**Files:**
- Modify: `deck/src/css/deck.css` (`:root` colour block, lines ~30–60)
- Modify: `deck/src/index.html` (sprite: drop `i-co2`, `i-refl`, `i-bal`, `i-temp`; add six part symbols)
- Modify: slides that `<use href="#i-…">`: `02_baeume.html` (ovf card), `04_potenzial.html` (ue-modell, ue-ziel), `index.html` template `tpl-trees` badges
- Source: `.superpowers/brainstorm/26071-1793346972/content/parts-v4.html` (symbols `k-*`)

**Interfaces:**
- Produces: CSS vars `--moss --clay --fjord` (new values), `--p-co2 --p-refl --p-bal --p-temp --p-one --p-world` (fill), `--t-co2 --t-refl --t-bal --t-temp --t-one --t-world` (text). Symbols `#p-co2 #p-refl #p-bal #p-temp #p-one #p-world` (viewBox `0 0 100 100`, fills via `var(--p-…)`, paper via `var(--paper)`).

- [ ] Copy the six `k-*` symbols from parts-v4 into the sprite, renamed `p-*`; replace `var(--kco2)`→`var(--p-co2)` etc.
- [ ] Set the CSS vars; `--co2` → `var(--p-co2)`, `--alb` → `var(--p-refl)`, `--ray` → `var(--p-refl)`.
- [ ] Replace every `#i-co2/#i-refl/#i-bal/#i-temp` use with the matching `#p-*`; `tpl-trees` badges likewise.
- [ ] Verify: `grep -rn '#i-\(co2\|refl\|bal\|temp\)' deck/src` → no hits; build; screenshot the Bäume closing card (`shot.py "Netto-Energieänderung ΔQ̇ durch Albedo:end"`) shows the new icons.

### Task 2: Ring, corner indicator, part assignment

**Files:**
- Modify: `deck/src/js/deck.js` (`decorate`, ~2976–3010; `flyHome` landing, ~3190–3230)
- Modify: `deck/src/css/deck.css` (`.path` rules ~145–165; remove `.h-part`, `.ico`)
- Modify: slides `02`–`04`: `data-part` on every content slide per the spec table (Zwischenstand = 1, Fazit = 2)
- Create: `$CLAUDE_JOB_DIR/tmp/structure_check.py`

**Interfaces:**
- Produces in `deck.js`:
  - `const CHAPTERS = { baeume: { name: 'Bäume', disc: 'e-baeume', parts: [['co2', 'Kohlenstoff-Aufnahme'], ['refl', 'Reflexionsänderung']] }, klima: { name: 'Klima', disc: 'e-klima', parts: [['bal', 'Strahlungsbilanz'], ['temp', 'Temperaturkurve']] }, vergleich: { name: 'Potenzial', disc: 'e-potenzial', parts: [['one', 'Kühlung eines Baums'], ['world', 'Kühlung der Welt']] } }`
  - `ringSvg(ch: string, arcs: [state, state]) -> string` — `<svg class="ring" viewBox="-14 -14 128 128">` with the disc `<use>` and two `<circle r="57">` arcs (dasharray `C*172/360`, rotations −86° and 94°); `state ∈ 'off'|'track'|'on'|'done'` set as class; colours from CSS: `.on` → `var(--p-<part>)`, `.done` → `var(--ch)`, `.track` → `var(--paper-line)`, `.off` → dashoffset = arc length.
- Indicator markup (in `.sh`, replacing the old pill content): `<nav class="path">` → one `.pc` button per chapter containing `ringSvg(...)`; current one `.on` (58 px), others 28 px; before them `<p class="where"><i>{chapter}</i><b>{part}</b></p>`. Chapter click → its opener (unchanged behaviour).
- Slides with `data-ch="dac"`, `.backup`, `.brk`, `06_schluss`: no `.path`.

- [ ] Write `structure_check.py`: loads http://localhost:8765, for every slide index n with `deck.still = true; deck.go(n,'end')` asserts: content slide in baeume/klima/vergleich has exactly one `.path .pc.on`, its `.where i` = chapter name and `.where b` = part name from the spec table (by `data-title`); `.pc.on .ring circle` classes are `[done|on, on|track]` matching the part; dac/backup slides have no `.path`; no page errors.
- [ ] Run it → fails (old pill, no `.where`).
- [ ] Implement `CHAPTERS`, `ringSvg`, new `path()` in `decorate`; drop the `h-part` breadcrumb; add `data-part` where missing.
- [ ] Indicator CSS: right-aligned text stack (`i` 500 14px chapter colour, `b` 600 17px ink), discs in a row with 12 px gaps; arc stroke transition 600 ms; scale both px values ×(1600/1200) for the deck's 1600×900 stage.
- [ ] `flyHome`: land on `.pc svg.ring`; replace the pill-grow step with `.where` fading in (300 ms) after landing.
- [ ] Ring on the `.ovtrail` discs of the closing cards: done chapter `['done','done']`, next/later `['track','track']`.
- [ ] Run `structure_check.py` → passes; screenshot one slide per part.

### Task 3: Overview slide

**Files:**
- Modify: `deck/src/slides/01_einleitung.html` (Überblick, lines ~88–115)

- [ ] Wrap each overview disc with its ring (`ringSvg(ch, ['track','track'])` inserted by `decorate` into a `.ovring` placeholder, or the two circles inline at the disc's scale: r = 118·57/50, stroke ×(118/50)).
- [ ] Remove the two muted subtitle lines under each name *(my call: the goal sentence now lives on the chapter slide)*. Keep the connecting line and the step reveals.
- [ ] Notes: drop "mit jedem wird die Systemgrenze größer" wording only if it no longer fits; otherwise unchanged.
- [ ] Screenshot `Überblick:end`.

### Task 4: Chapter slides and the enter motion

**Files:**
- Modify: `02_baeume.html`, `03_klima.html`, `04_potenzial.html` (opener sections)
- Modify: `deck/src/js/deck.js` (`onward`, `zoomDisc`, `zoomInto` → `enterChapter`)
- Modify: `deck/src/css/deck.css` (`.slide.chapter` block ~433–440; delete `.cscene`, `.cgoal`, `.cnode`, `.ci`, `.crow`, `.carr`, `.fx`, `.dic`, `.drow`, `derive`, `.zoomer`)
- Modify: `deck/src/index.html` (delete `x-baeume`, `x-klima`, `x-potenzial`)

**Interfaces:**
- Opener markup:
  ```html
  <section class="slide chapter" data-ch="baeume" data-title="Bäume">
    <div class="cdisc" data-fly="baeume"></div>            <!-- ringSvg filled in by decorate, arcs 'on','on' -->
    <div class="ctext">
      <h1>Bäume</h1>
      <p class="cgoal">Ein Modell für das, was ein einzelner Baum fürs Klima tut.</p>
      <div class="cpart"><svg viewBox="0 0 100 100"><use href="#p-co2"/></svg><div><b>Kohlenstoff-Aufnahme</b><span>Wie viel CO₂ er bindet, Jahr für Jahr</span></div></div>
      <div class="cpart">…</div>
    </div>
    <aside class="notes">…</aside>
  </section>
  ```
  Goal and row texts exactly as in the spec.
- `Deck.enterChapter(e: Element, s: HTMLElement) -> void`: clone of the source disc flies from its box to `s .cdisc` box (one transform, 900 ms, spec easing); prev slide fades (340 ms); at the end `go(i+1, 0)` with `s.classList.add('arrive')`, clone removed. `onward` calls it where it called `zoomInto`.
- Entrance CSS on `.slide.chapter.active` (and only when not `still`): ring arc 1/2 dashoffset → 0 at 700/1500 ms; `.cpart` 1/2 clip-path wipe at 800/1600 ms; `h1`, `.cgoal` fade in 300 ms. With `html.still`/reduced motion: final state.

- [ ] Rewrite the three openers; carry their notes over, edit the Bäume note ("Die zwei Zeichen begleiten uns … oben links" → "oben rechts sehen wir immer, wo wir sind").
- [ ] `.slide.chapter`: paper background, `color: var(--ink)`, h1 in `var(--ch)`; disc ~440 px (330·1600/1200) centred at (400, 470); text block from x 750.
- [ ] Implement `enterChapter`; delete `zoomInto` and its CSS/symbols.
- [ ] Check: click from Überblick into Bäume, from Bäume closing card into Klima, from Klima closing card into Potenzial (Playwright video or frames at 0/450/900/1800 ms); backwards from first content slide → opener in final state; `structure_check.py` still passes; editor edits `h1`/`.cgoal`/`.cpart b` and the change lands in the slide source.

### Task 5: Symbol and drawing colours in the deck

**Files:**
- Modify: `deck/src/css/deck.css` (`--s-*` block, lines ~50–58)
- Modify: `deck/src/js/deck.js` (`alb: '#c8602a'` ~280, `'#2e7d4f'` ~428, `'#6a3d9a'`, `'#b2182b'` uses)
- Modify: `deck/src/js/loader.js:16` (`deckCol.VL` stays scenario colour; only change if it equals `--co2` semantics → `--p-co2` fill)
- Modify: inline hex in `03_klima.html`, `07_backup.html` (`#2e7d4f`, `#d95f02`, `#6a3d9a`, `#b2182b`)

Mapping (text tone for symbols/labels, fill tone for areas/arcs):
- Kohlenstoff: `--s-phic`, `--s-dm`, `--s-eps`, `--s-mdc` → `--t-co2`
- Reflexion: `--s-phia`, `--s-alb`, `--s-albb`, `--s-albw`, `--s-dal`, `--s-dq`, `--s-alw` → `--t-refl`; `--s-daw` → `--p-refl`
- Strahlungsbilanz: `--s-phi`, `--s-phio`, `--s-rf` → `--t-bal`
- Temperatur: `--s-dt`, `--s-ft` → `--t-temp`
- Others unchanged unless they clash visibly with a part colour.

- [ ] Apply the mapping; replace the inline hex values with `var(...)`.
- [ ] Screenshots: Netto-Energieänderung (end), Strahlungsantrieb von CO₂ (end), Strahlungsantrieb der Albedo (end), Vom Strahlungsantrieb zur Temperatur (end), Überschlagsrechnung noch einmal; symbols readable on paper (text tones ≥ 4.5:1).

### Task 6: Chart colours

**Files:**
- Modify: `src/nbs/plots.py:28-29,374` (`C_CARBON`, `C_ALBEDO`, `C_GROWTH`), `src/nbs/storyline_figures.py:48-49` and the temperature `#b2182b` / CO₂ `#2e7d4f` / `#1b7837` literals, `src/nbs/vergleich_figures.py:37`, `src/nbs/animations.py:678,753,794,796,848`, `src/nbs/dac_figures.py` (temperature reds only where they mean ΔT)
- Modify: `deck/src/js/deck.js:280` (`EC.alb`)
- Regenerate: `deck/assets/data/ec_charts.js`

Chart lines use the **text** tone (contrast on paper ≥ 3:1), filled areas the fill tone *(refinement of the spec, which said fill tone for curves: `#9d945f` on paper is ~2.6:1)*.

- [ ] Add `C_TEMP = "#762c26"` beside `C_CARBON = "#105b3e"`, `C_ALBEDO = "#787136"` in `plots.py`; import them in the figure modules instead of literals.
- [ ] `uv run pytest tests -q` → still passes.
- [ ] `uv run python deck/export_charts.py`; build; screenshot every chart slide in chapters 2–4 and compare series colours with the formula symbols next to them.

### Task 7: Clean-up and full pass

- [ ] Remove dead CSS/JS left from openers and breadcrumb (`grep -n 'cscene\|zoomInto\|h-part\|\.dic\|\.drow\|x-baeume\|i-co2' deck/src` → none).
- [ ] `check.py` (page errors, source-line overlaps) → no errors; `structure_check.py` → pass.
- [ ] Screenshot pass: every slide of chapters 1–4 at 1600×900 and at 390×844; `export_pdf.py` runs.
- [ ] Report to Timo with screenshots; commit only on request.
