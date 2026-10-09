import { useEffect, useRef } from "react";
import { Pause, Play } from "lucide-react";
import { useT } from "@/i18n/useT";

const YEARS_PER_SECOND = 6;

export function TimeSlider({ year, onYear, playing, onPlaying, min = 2026, max = 2100 }:
  { year: number; onYear(y: number): void; playing: boolean; onPlaying(p: boolean): void; min?: number; max?: number }) {
  const t = useT();
  const yearRef = useRef(year);
  yearRef.current = year;
  useEffect(() => {
    if (!playing) return;
    let last = performance.now(), acc = yearRef.current >= max ? min : yearRef.current, raf = 0;
    const tick = (now: number) => {
      acc += ((now - last) / 1000) * YEARS_PER_SECOND; last = now;
      if (acc >= max) { onYear(max); onPlaying(false); return; }
      onYear(acc); raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, min, max, onYear, onPlaying]);
  return (
    <div className="flex items-center gap-3">
      <button aria-label={t(playing ? "slider.pause" : "slider.play")} onClick={() => onPlaying(!playing)}
        className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[var(--ch)] text-[var(--paper)]">
        {playing ? <Pause size={16} /> : <Play size={16} />}
      </button>
      <input type="range" role="slider" aria-label={t("slider.year")} min={min} max={max} step={1} value={Math.round(year)}
        onChange={(e) => { onPlaying(false); onYear(+e.target.value); }}
        className="w-full" style={{ accentColor: "var(--ch)" }} />
      <output className="ch-text w-12 text-right font-serif text-lg font-semibold tabular-nums">{Math.round(year)}</output>
    </div>
  );
}
