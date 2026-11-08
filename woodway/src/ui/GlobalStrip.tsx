import { useState } from "react";
import { ComposedChart, Line, ReferenceLine, ResponsiveContainer, XAxis, YAxis } from "recharts";
import type { Atlas } from "@/data/types";
import { useNum, useT } from "@/i18n/useT";
import { SourceLine } from "@/ui/deck/SourceLine";

const TICK = { fontSize: 11, fill: "var(--muted)", fontFamily: "var(--sans)" };
const VEGAN = "#2f7fae";
const PACES = ["20", "50", "100"] as const;
type Pace = (typeof PACES)[number];
const CURVES = [
  { id: "vl", key: "strip.need", color: "var(--muted)", dash: "4 3" },
  { id: "trees", key: "strip.afterTrees", color: "var(--co2)" },
  { id: "vegan", key: "strip.vegan", color: VEGAN },
  { id: "dac", key: "strip.afterDac", color: "var(--dac)" },
  { id: "veganDac", key: "strip.veganDac", color: "var(--dac)", dash: "6 3" },
] as const;

/** The deck's anchor (chapter 5): Very Low in °C and a curve per measure on top of it -- the trees, a vegan world,
 *  DACCS at the chosen build-out limit, and the vegan world with DACCS (20 %/a, the only pace the deck pairs with it). */
export function GlobalStrip({ atlas, year }: { atlas: Atlas; year: number }) {
  const t = useT(), num = useNum();
  const [pace, setPace] = useState<Pace>("20");
  const g = { ...atlas.meta.global, bestand: atlas.meta.bestand }, e = g.effect;
  const dacE = e[`dac${pace}`];
  const data = g.years.map((y, k) => {
    const trees = g.vlC[k] + e.trees[k] / 1000, vegan = trees + e.vegan[k] / 1000;
    return { year: y, vl: g.vlC[k], trees, vegan, dac: trees + dacE[k] / 1000, veganDac: pace === "20" ? vegan + e.veganDac[k] / 1000 : null };
  });
  const k = Math.max(0, Math.min(g.years.length - 1, Math.round(year) - g.years[0]));
  const plan = g.dac[pace], cap = plan.capGt[k], eur = plan.costMed[k];
  // y in steps of 0.1 °C over every curve the chart can show, so 1.5 °C is a tick and the axis holds when the pace changes
  const all = data.flatMap((d) => [d.vl, d.trees, d.vegan, d.dac, d.veganDac ?? d.vl]);
  const lo = Math.floor(Math.min(1.5, ...all) * 10) / 10, hi = Math.ceil(Math.max(...all) * 10) / 10;
  const ticks = Array.from({ length: Math.round((hi - lo) * 10) + 1 }, (_, i) => Math.round((lo + i / 10) * 10) / 10);
  const curves = CURVES.filter((c) => c.id !== "veganDac" || pace === "20");
  return (
    <section className="text-xs" aria-label={t("strip.title")} data-ch="vergleich">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="ch-text font-serif text-sm font-semibold leading-tight">{t("strip.title")}</h2>
        <span className="shrink-0 tabular-nums text-inkMuted">
          {t("strip.capacity", { gt: num(cap, cap < 1 ? 2 : 1), eur: num(eur, eur < 1 ? 2 : 1) })}
        </span>
      </div>
      <div className="mt-1 flex items-center gap-1.5" role="group" aria-label={t("strip.pace")}>
        <span className="text-inkMuted">{t("strip.pace")}</span>
        {PACES.map((p) => (
          <button key={p} type="button" aria-pressed={pace === p} onClick={() => setPace(p)}
            className="rounded px-1.5 py-0.5 tabular-nums text-inkMuted hover:bg-ink/5 aria-pressed:bg-[color-mix(in_srgb,var(--dac-soft)_45%,transparent)] aria-pressed:text-ink">
            {t("strip.paceOpt", { pct: p })}
          </button>
        ))}
      </div>
      <div className="mt-1 h-40">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <XAxis dataKey="year" type="number" domain={[g.years[0], g.years.at(-1)!]} ticks={[2026, 2050, 2075, 2100]} tick={TICK} stroke="var(--paper-line)" />
            <YAxis tick={TICK} width={48} unit={` ${t("strip.unit")}`} stroke="var(--paper-line)" domain={[lo, hi]} ticks={ticks}
              tickFormatter={(v: number) => num(v, 1)} />
            <ReferenceLine y={1.5} stroke="var(--ink)" strokeOpacity={0.6} strokeWidth={1.25} />
            {curves.map((c) => (
              <Line key={c.id} dataKey={c.id} stroke={c.color} dot={false} strokeWidth={c.id === "vl" ? 1.5 : 2}
                strokeDasharray={"dash" in c ? c.dash : undefined} isAnimationActive={false} connectNulls={false} />
            ))}
            <ReferenceLine x={Math.round(year)} stroke="var(--ink)" strokeDasharray="3 3" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-1 flex flex-wrap gap-x-3 text-inkMuted">
        {curves.map((c) => (
          <li key={c.id}>
            <span className="mr-1 inline-block h-0.5 w-3 align-middle"
              style={"dash" in c ? { backgroundImage: `repeating-linear-gradient(to right, ${c.color} 0 3px, transparent 3px 5px)` } : { background: c.color }} />
            {t(c.key)}
          </li>
        ))}
      </ul>
      {/* today's forests: what they still take up and what felling the warming ones would do, in the year shown;
          not a curve -- their sink is part of the scenario already */}
      {g.bestand && (
        <p className="mt-1 text-inkMuted">{t("strip.today", {
          area: num(g.bestand.areaGha, 1), year: Math.round(year), gt: num(g.bestand.uptakeGt[k], 1),
          fell: num(g.bestand.fellGha, 2), dt: num(g.bestand.fellMK[k] / 1000, 3).replace("-", "−"),
        })}</p>
      )}
      <div className="mt-1"><SourceLine>{t("strip.source", {
        area: num(g.areasGha.kuehlt, 2), year: g.plantYear, free: num(g.vegan.freeGha, 2), growth: pace,
        back: plan.back, sum: num(plan.sumMed, 0), eurt: num(plan.eurT, 0),
      })}</SourceLine></div>
    </section>
  );
}
