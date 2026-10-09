# React deck: the talk with live atlas slides

Date: 2026-10-10 · Status: decided by the controller under the user's standing instruction ("go all the way, write spec and plan yourself, I review the final result"). Follows `2026-10-10-atlas-design.md` (sub-project 1).

## Purpose

An optional second version of the talk that runs on the atlas's stack (Vite, React, TypeScript) and shows some results as live maps from the atlas, driven click by click like the rest of the deck. The HTML deck (`deck/`) stays the default and is not rewritten.

## Decision: reuse the HTML deck's slides, add React slides

Porting 45 animated slides (ECharts charts, SVG schematics, KaTeX, the DAC film) to React would duplicate the deck and split every later text edit across two codebases. Instead:

- The React deck shows the **existing HTML deck in an iframe** for all existing slides, with its own animations, steering it over the postMessage protocol the deck already speaks for its presenter view (`{src: "dv", cmd: "next" | "prev" | "goto"}` in, `{src: "dv", state: {i, step, ni, ns, n, main}}` out).
- **Atlas slides are React components** that render `AtlasMap`, `Legend`, `CellPanel` and the global strip from `atlas/src`, in the deck's 1600×900 slide frame and style (Task 5b of the atlas plan: tokens, `Takeaway`, `SourceLine`).
- One **sequence** lists, in order, ranges of deck slides and atlas slides. The React shell owns the keyboard, the step counter of atlas slides and the switch between iframe and React slide.

Two small, backwards-compatible additions to the HTML deck:

- `?host` query: the deck runs normally (animated) but hides its own chrome (menu button, key hint), because the React shell provides it.
- `goto` accepts an optional `step` (`"end"` = last step), so stepping back from an atlas slide lands on the previous deck slide's final state.

## Content: the atlas slides

All German (the talk is German); numbers on the slides are computed live from the atlas data, never typed in.

1. **"Jede Zelle, jedes Jahr"** — after "Temperaturwirkung eines Baums je Ort". Layer ΔT per tree; clicks: 2030 → 2050 → 2100 (the year runs, not jumps); last click marks Aachen (DE), Joensuu (FI), Marabá (BR). Takeaway: share of the reforestable area where a tree cools in 2100, computed from the fields.
2. **"Wo die Albedo den Kohlenstoff auffrisst"** — layer net share 2100; Takeaway: area-weighted median net share.
3. **"DAC wird mit dem Strom sauber"** — in the DAC chapter after "DAC-Modell". Layer DAC net share; clicks: 2026 → 2040 → 2070; Takeaway: median net share at each step.
4. **"Wo DAC gebaut wird"** — after "DAC-Ausbau". Layer DAC build-out; the year plays 2026 → 2100 on one click; Takeaway: capacity in 2100 from the global paths.
5. **"Atlas"** — last backup slide: the full atlas UI (layer picker, slider, cell panel) for questions.

The HTML deck gets one backup slide "Atlas: alle Ergebnisse interaktiv" with the link to `/atlas/`, so the default deck also points to it.

## Architecture

```
atlas/
  talk.html                 second Vite entry
  src/talk/
    sequence.ts             [{kind: "deck", from, to} | {kind: "atlas", id}] — the talk order
    TalkApp.tsx             shell: 1600×900 frame scaled to the window, keys, progress, notes drawer (N)
    DeckFrame.tsx           the iframe + protocol (send cmd, receive state)
    slides/*.tsx            the five atlas slides; each exports {title, notes, steps, render(step)}
    frame.css               the deck's slide frame (.slide, .sh h2, ground line) for React slides
```

- Deck URL: production `../index.html?host` (Pages: deck at the site root, atlas under `/atlas/`); development `/deck/index.html?host`, served by a tiny Vite dev middleware from `deck/dist` (built with `python deck/build.py`).
- Keys: → / Space / PageDown next; ← / PageUp previous; Home first; B backup; N notes; F fullscreen. On a deck range the shell forwards next/prev to the iframe and uses the reported state to decide when to leave the range.
- The atlas components already take their state as props (atlas spec); slides pass layer, year and selected cell per step, and a `still` map without hover.

## Testing

- `sequence.test.ts`: the sequence covers every deck slide exactly once in order; atlas slides sit after the named deck slides (titles looked up in `deck/src/slides/*.html`).
- `navigation.test.ts`: a fake deck (emitting state like the real one) — next through a range, into an atlas slide, back to the deck slide's last step, out the other side.
- Atlas slide tests: each slide's takeaway numbers equal the values computed directly from the exported fields.
- Browser: run the whole talk once at 1600×900 with the built deck in the iframe; no console errors; atlas slides animate their year; prev/next across the boundaries lands on the right step.
