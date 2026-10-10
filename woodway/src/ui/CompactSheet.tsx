import { useEffect, useRef, useState, type ReactNode, type PointerEvent as RPointerEvent, type KeyboardEvent } from "react";
import { useT } from "@/i18n/useT";

/**
 * The phone's bottom sheet: a plain region, not a dialog — the map and the top bar stay usable and readable
 * by screen readers while it is open (a Radix/Vaul drawer is always modal and hides everything else).
 * Three resting heights: the peek (legend and year, in reach of the thumb), half (a tapped cell), almost full.
 * Drag the handle or the peek; tap the handle or use the arrow keys on it to step.
 */
export function CompactSheet({ title, peek, children, snaps, snap, onSnap, vh, onTopHeight, inertAtPeek = true, onDismiss }:
  { title: string; peek: ReactNode; children: ReactNode; snaps: number[]; snap: number; onSnap(i: number): void; vh: number; onTopHeight?(px: number): void;
    /** false when the lowest step already shows content worth reading (a cell's details at half height) */
    inertAtPeek?: boolean;
    /** given: the sheet can be dragged down past its lowest height to close it */
    onDismiss?(): void }) {
  const t = useT();
  const [drag, setDrag] = useState<number | null>(null);   // live height in px while dragging
  const start = useRef<{ y: number; h: number; moved: boolean; handle: boolean } | null>(null);
  const rest = snaps[snap] * vh;
  const height = drag ?? rest;
  // the top part (handle + peek) keeps its own height; the scroll column takes what remains of the step
  const top = useRef<HTMLDivElement>(null);
  const [topH, setTopH] = useState(0);
  useEffect(() => {
    const el = top.current;
    if (!el) return;
    const report = () => { const h = el.offsetHeight; if (h > 0) { setTopH(h); onTopHeight?.(h); } };
    const ro = new ResizeObserver(report);
    ro.observe(el); report();
    return () => ro.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const full = snaps[snaps.length - 1] * vh;

  const down = (e: RPointerEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement).closest("input, button:not([data-sheet-handle]), a, select, textarea")) return;
    // pointer capture retargets the release to this element, so remember now whether the handle was pressed
    start.current = { y: e.clientY, h: rest, moved: false, handle: !!(e.target as HTMLElement).closest("[data-sheet-handle]") };
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const move = (e: RPointerEvent<HTMLDivElement>) => {
    const s = start.current;
    if (!s) return;
    const dy = s.y - e.clientY;
    if (!s.moved && Math.abs(dy) < 6) return;
    s.moved = true;
    setDrag(Math.max(onDismiss ? 0 : snaps[0] * vh, Math.min(snaps[snaps.length - 1] * vh, s.h + dy)));
  };
  const up = () => {
    const s = start.current;
    start.current = null;
    if (!s) return;
    if (!s.moved) {
      // a tap on the handle steps up, from the top back down to the peek
      if (s.handle) step();
      return;
    }
    const h = drag ?? s.h, v = h - s.h;
    // pulled well below the lowest height (a third of it, or 120 px): let go of it
    if (onDismiss && h < snaps[0] * vh - Math.min(120, (snaps[0] * vh) / 3)) { setDrag(null); onDismiss(); return; }
    // nearest resting height, with a nudge in the direction of a decisive flick
    let best = 0;
    snaps.forEach((f, i) => { if (Math.abs(f * vh - h) < Math.abs(snaps[best] * vh - h)) best = i; });
    if (Math.abs(v) > 40 && best === snap) best = Math.max(0, Math.min(snaps.length - 1, snap + Math.sign(v)));
    setDrag(null);
    onSnap(best);
  };
  const step = () => onSnap(snap < snaps.length - 1 ? snap + 1 : 0);
  const key = (e: KeyboardEvent) => {
    if (e.key === "ArrowUp") { e.preventDefault(); onSnap(Math.min(snaps.length - 1, snap + 1)); }
    if (e.key === "ArrowDown") { e.preventDefault(); onSnap(Math.max(0, snap - 1)); }
  };

  return (
    <section aria-label={title} data-snap={snap}
      className="fixed inset-x-0 bottom-0 z-30 flex flex-col rounded-t-xl border-t border-[var(--paper-line)] bg-panel shadow-[0_-10px_28px_-18px_rgba(30,26,18,.5)] will-change-transform"
      // always as tall as the highest step and slid down (a transform, so moving it never re-lays out the page);
      // the content column below gets the visible height so it scrolls exactly within what is shown
      style={{ height: full, transform: `translateY(${full - height}px)`, transition: drag === null ? "transform 320ms cubic-bezier(0.16, 1, 0.3, 1)" : "none" }}>
      <div ref={top} className="shrink-0 touch-none select-none" onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up}>
        <button type="button" data-sheet-handle aria-label={t(snap === snaps.length - 1 ? "sheet.collapse" : "sheet.expand")}
          aria-expanded={snap > 0} onKeyDown={key}
          // Enter/Space (a click without a pointer, detail 0); pointer taps are handled on release above
          onClick={(e) => { if (e.detail === 0) step(); }}
          className={"group mx-auto flex w-full items-center justify-center focus-visible:outline-none " + (onDismiss ? "h-9" : "h-7")}>
          <span className="h-1.5 w-10 rounded-full bg-[var(--paper-line)] group-focus-visible:w-14 group-focus-visible:bg-[var(--ch)]" aria-hidden />
        </button>
        <div className="px-4 pb-2.5">{peek}</div>
      </div>
      <div className="min-h-0 overflow-y-auto overscroll-contain border-t border-[var(--paper-line)] px-4 pt-4"
        style={{ flex: `0 0 ${Math.max(0, rest - topH)}px`, paddingBottom: "max(1.5rem, env(safe-area-inset-bottom))" }}
        // below the fold at the peek: out of the tab order and the reading order (React 18 sets `inert` only as a string)
        {...(inertAtPeek && snap === 0 && drag === null ? { inert: "" } : {})}>
        {children}
      </div>
    </section>
  );
}
