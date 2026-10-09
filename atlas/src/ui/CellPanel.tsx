import { useMemo } from "react";
import { X } from "lucide-react";
import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Atlas } from "@/data/types";
import { cellSeries, coolsFrom, coolsUntil, dacBuildMt, dacNet, typeKey } from "@/model/model";
import { cellCenter } from "@/map/lookup";
import { useNum, useT, type Key } from "@/i18n/useT";
import { Kicker } from "@/ui/deck/Kicker";
import { Takeaway } from "@/ui/deck/Takeaway";

const TICK = { fontSize: 11, fill: "var(--muted)", fontFamily: "var(--sans)" };

function Chart({ title, years, series, year }: { title: string; years: number[]; series: { key: string; color: string; values: number[] }[]; year: number }) {
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const data = useMemo(() => years.map((y, k) => Object.fromEntries([["year", y], ...series.map((s) => [s.key, s.values[k]])])), [years, series[0].values]);
  return (
    <section className="mt-3">
      <h3 className="text-xs font-medium text-inkMuted">{title}</h3>
      {series.length > 1 && (
        <p className="flex gap-3 text-[11px] text-inkMuted">
          {series.map((s) => <span key={s.key}><span className="mr-1 inline-block h-0.5 w-3 align-middle" style={{ background: s.color }} />{s.key}</span>)}
        </p>
      )}
      <div className="h-28">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 6, right: 8, bottom: 0, left: 0 }}>
            <XAxis dataKey="year" type="number" domain={[years[0], years.at(-1)!]} ticks={[2026, 2050, 2075, 2100]} tick={TICK} stroke="var(--paper-line)" />
            <YAxis tick={TICK} width={42} stroke="var(--paper-line)" />
            <ReferenceLine y={0} stroke="var(--muted)" strokeOpacity={0.4} />
            <ReferenceLine x={year} stroke="var(--ink)" strokeDasharray="3 3" />
            <Tooltip formatter={(v: number) => v.toFixed(1)} labelFormatter={(y) => String(y)}
              contentStyle={{ background: "var(--paper)", border: "1px solid var(--paper-line)", fontSize: 12, fontFamily: "var(--sans)" }} />
            {series.map((s) => <Line key={s.key} dataKey={s.key} name={s.key} stroke={s.color} dot={false} strokeWidth={2} isAnimationActive={false} />)}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export function CellPanel({ atlas, cell, year, onClose }: { atlas: Atlas; cell: number; year: number; onClose(): void }) {
  const t = useT(), num = useNum();
  const { lat, lon } = cellCenter(cell);
  const key = typeKey(atlas, cell);
  const s = useMemo(() => {
    const r = cellSeries(atlas, cell);
    return r && { ...r, phiCo2: r.phiCo2.map((v) => v * 1e15), phiAlb: r.phiAlb.map((v) => v * 1e15), dt: r.dt.map((v) => v * 1e15) };
  }, [atlas, cell]);
  const cool = key ? coolsFrom(atlas, cell) : null;
  const until = key ? coolsUntil(atlas, cell) : null;
  const eta = dacNet(atlas, cell, year);
  const build = dacBuildMt(atlas, cell, year);
  const [group, zone] = key ? key.split("_") : ["", ""];
  return (
    <article className="relative text-sm">
      <button aria-label={t("panel.close")} onClick={onClose} className="absolute right-0 top-0 grid h-8 w-8 place-items-center rounded hover:bg-ink/5"><X size={16} /></button>
      <p className="text-xs text-inkMuted">{t("panel.cell", { lat: num(lat, 2), lon: num(lon, 2) })}</p>
      <div data-ch="baeume">
        {key && s ? (
          <>
            <h2 className="mt-1 font-serif text-lg font-semibold text-[var(--ch)]">{t("panel.forest", { type: t(`type.${group}` as Key), zone: t(`zone.${zone}` as Key) })}</h2>
            <p className="text-inkMuted">{t("panel.area", { area: num(atlas.f.area[cell] / 1e6), trees: num(atlas.f.trees[cell] / 1e6, 1) })}</p>
            <div style={until ? ({ "--ch": "var(--alb)", "--ch-soft": "#ecc19a" } as React.CSSProperties) : undefined}>
              <Takeaway ch={until ? undefined : "baeume"}>{cool ? t("panel.coolsFrom", { year: cool }) : until ? t("panel.coolsUntil", { year: until }) : t("panel.neverCools")}</Takeaway>
            </div>
            <Chart title={t("panel.stock")} years={s.years} year={year} series={[{ key: t("panel.stockSeries"), color: "var(--co2)", values: s.m }]} />
            <Chart title={t("panel.forcing")} years={s.years} year={year} series={[
              { key: t("panel.forcingCo2"), color: "var(--co2)", values: s.phiCo2 },
              { key: t("panel.forcingAlb"), color: "var(--alb)", values: s.phiAlb }]} />
            <Chart title={t("panel.temperature")} years={s.years} year={year} series={[{ key: "ΔT", color: "#14532d", values: s.dt }]} />
          </>
        ) : (
          <p className="mt-2">{t("panel.noForest")}</p>
        )}
      </div>
      <div data-ch="dac" className="mt-5">
        <div className="mb-1.5 border-b border-[var(--paper-line)] pb-1"><Kicker>{t("panel.dac")}</Kicker></div>
        {atlas.f.dacOk[cell] ? (
          <ul className="text-inkMuted">
            <li>{t("panel.dacElec", { mwh: num(atlas.f.elec[cell], 2) })}</li>
            <li>{t("panel.dacNet", { pct: num(eta * 100), year: Math.round(year) })}</li>
            {build > 0 && <li>{t("panel.dacBuild", { mt: num(build, 1), year: Math.round(year) })}</li>}
          </ul>
        ) : (
          <p className="text-inkMuted">{t("panel.dacTooCold")}</p>
        )}
      </div>
    </article>
  );
}
