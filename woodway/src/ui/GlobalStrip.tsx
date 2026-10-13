import { Area, ComposedChart, Line, ReferenceLine, ResponsiveContainer, XAxis, YAxis } from "recharts";
import type { Atlas } from "@/data/types";
import { useNum, useT } from "@/i18n/useT";
import { SourceLine } from "@/ui/deck/SourceLine";

const TICK = { fontSize: 11, fill: "var(--muted)", fontFamily: "var(--sans)" };
const CURVES = [
  { key: "strip.need", color: "#b2182b" },
  { key: "strip.afterTrees", color: "var(--co2)" },
  { key: "strip.afterDac", color: "var(--dac)" },
] as const;

export function GlobalStrip({ atlas, year }: { atlas: Atlas; year: number }) {
  const t = useT(), num = useNum();
  const g = atlas.meta.global;
  const data = g.years.map((y, k) => ({ year: y, need: g.need[k], trees: g.afterTrees[k], dac: g.afterDac[k] }));
  const k = Math.max(0, Math.min(g.years.length - 1, Math.round(year) - g.years[0]));
  return (
    <section className="text-xs" aria-label={t("strip.title")} data-ch="vergleich">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="ch-text font-serif text-sm font-semibold leading-tight">{t("strip.title")}</h2>
        <span className="shrink-0 tabular-nums text-inkMuted">{t("strip.capacity", { gt: num(g.dacCapacityGt[k], g.dacCapacityGt[k] < 1 ? 2 : 1) })}</span>
      </div>
      <div className="mt-1 h-24">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <XAxis dataKey="year" type="number" domain={[g.years[0], g.years.at(-1)!]} ticks={[2026, 2050, 2075, 2100]} tick={TICK} stroke="var(--paper-line)" />
            <YAxis tick={TICK} width={58} unit={` ${t("strip.unit")}`} stroke="var(--paper-line)" />
            <Area dataKey="need" stroke="#b2182b" fill="#b2182b" fillOpacity={0.12} strokeDasharray="4 3" dot={false} isAnimationActive={false} />
            <Line dataKey="trees" stroke="var(--co2)" dot={false} strokeWidth={2} isAnimationActive={false} />
            <Line dataKey="dac" stroke="var(--dac)" dot={false} strokeWidth={2} isAnimationActive={false} />
            <ReferenceLine x={Math.round(year)} stroke="var(--ink)" strokeDasharray="3 3" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-1 flex flex-wrap gap-x-3 text-inkMuted">
        {CURVES.map((c) => (
          <li key={c.key}><span className="mr-1 inline-block h-0.5 w-3 align-middle" style={{ background: c.color }} />{t(c.key)}</li>
        ))}
      </ul>
      <div className="mt-1"><SourceLine>{t("strip.source", { area: num(g.areasGha.kuehlt, 2), year: g.plantYear, growth: num(g.dacGrowthPct) })}</SourceLine></div>
    </section>
  );
}
