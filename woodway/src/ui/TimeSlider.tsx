import { useEffect, useRef, type CSSProperties, type ReactNode } from "react";
import { Pause, Play } from "lucide-react";
import { useT } from "@/i18n/useT";

const YEARS_PER_SECOND = 6;

/** Play, a slim track that fills up to the year, and the year itself: one line, ~36 px tall. `min` is the first year
 *  shown (the planting year for planted trees: nothing happens before it); `after` sits at the end of the row. */
export function TimeSlider({ year, onYear, playing, onPlaying, min = 2026, max = 2100, after }:
  { year: number; onYear(y: number): void; playing: boolean; onPlaying(p: boolean): void; min?: number; max?: number;
    after?: ReactNode }) {
  const t = useT();
  const yearRef = useRef(year);
  yearRef.current = year;
  useEffect(() => {
    if (!playing) return;
    let last = performance.now(), acc = yearRef.current >= max ? min : yearRef.current, raf = 0;
    const tick = (now: number) => {
      acc += (Math.min(now - last, 100) / 1000) * YEARS_PER_SECOND; last = now;
      if (acc >= max) { onYear(max); onPlaying(false); return; }
      onYear(acc); raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, min, max, onYear, onPlaying]);
  const pct = ((Math.round(year) - min) / (max - min)) * 100;
  return (
    <div className="flex items-center gap-2.5">
      {/* the disc is 32 px; on touch the button around it reaches 40 px without growing the row's look */}
      <button aria-label={t(playing ? "slider.pause" : "slider.play")} onClick={() => onPlaying(!playing)}
        className="group -my-1 -ml-1 grid h-10 w-10 shrink-0 place-items-center rounded-full focus-visible:outline-none [@media(pointer:fine)]:h-8 [@media(pointer:fine)]:w-8 [@media(pointer:fine)]:m-0">
        <span className="grid h-8 w-8 place-items-center rounded-full bg-[var(--ch)] text-[var(--paper)] transition-transform group-active:scale-95 group-focus-visible:ring-2 group-focus-visible:ring-[var(--ch)]/40 group-focus-visible:ring-offset-2 group-focus-visible:ring-offset-panel">
          {playing ? <Pause size={14} fill="currentColor" strokeWidth={0} /> : <Play size={14} className="translate-x-px" fill="currentColor" strokeWidth={0} />}
        </span>
      </button>
      <input type="range" aria-label={t("slider.year")} min={min} max={max} step={1} value={Math.round(year)}
        onChange={(e) => { onPlaying(false); onYear(+e.target.value); }}
        className="year-range min-w-0 flex-1" style={{ "--pct": `${pct}%` } as CSSProperties} />
      <output className="ch-text w-11 text-right font-serif text-[15px] font-semibold tabular-nums leading-none">{Math.round(year)}</output>
      {after}
    </div>
  );
}
