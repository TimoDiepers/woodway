import { useMemo } from "react";
import { X } from "lucide-react";
import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Atlas } from "@/data/types";
import { cellSeries, coolsFrom, coolsUntil, dacBuildMt, deltaT, netShare, typeKey, yearIndex } from "@/model/model";
import { treeRank } from "@/model/rank";
import { LAYERS, scaleOf, type LayerId } from "@/model/layers";
import { scaleColor, themedScale } from "@/color/scale";
import { cellCenter } from "@/map/lookup";
import { useNum, useT, type Key } from "@/i18n/useT";
import { useDark } from "@/lib/useDark";

const TICK = { fontSize: 10, fill: "var(--muted)", fontFamily: "var(--sans)" };
const TREE_ROWS: LayerId[] = ["area", "sun", "darker", "light"];
const DAC_ROWS: LayerId[] = ["elec", "dacNet", "dacBuild"];

type Series = { label: string; color: string; values: number[]; width?: number; faint?: boolean };

/** Lines use fixed data keys (v0, v1, …); the translated label is only the line's name, so a language switch
 *  never orphans a line from its data. */
function Chart({ title, years, series, year, tall = false }: { title: string; years: number[]; series: Series[]; year: number; tall?: boolean }) {
  const cols = series.map((s) => s.values);
  const data = useMemo(
    () => years.map((y, k) => Object.fromEntries([["year", y], ...cols.map((v, i) => [`v${i}`, v[k]])])),
    // the values arrays are memoised per cell upstream
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [years, ...cols],
  );
  return (
    <section className="mt-3">
      <h3 className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 text-[11px] leading-tight text-inkMuted">
        <span className="font-medium text-ink">{title}</span>
        {series.length > 1 && series.map((s, i) => (
          <span key={i} className="whitespace-nowrap">
            <span className="mr-1 inline-block w-3 align-middle" style={{ height: s.faint ? 1 : 2, background: s.color }} />{s.label}
          </span>
        ))}
      </h3>
      <div className={tall ? "h-[96px]" : "h-[76px]"}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 6, bottom: 0, left: 0 }}>
            <XAxis dataKey="year" type="number" domain={[years[0], years.at(-1)!]} ticks={[2026, 2050, 2075, 2100]} tick={TICK} stroke="var(--paper-line)" height={18} />
            <YAxis tick={TICK} width={32} tickCount={3} stroke="var(--paper-line)" />
            <ReferenceLine y={0} stroke="var(--muted)" strokeOpacity={0.4} />
            <ReferenceLine x={year} stroke="var(--ink)" strokeDasharray="3 3" />
            <Tooltip formatter={(v: number) => v.toFixed(1).replace(/^-/, "\u2212")} labelFormatter={(y) => String(y)}
              contentStyle={{ background: "rgb(var(--color-panel))", color: "rgb(var(--color-ink))", border: "1px solid var(--paper-line)", borderRadius: 6, fontSize: 12, fontFamily: "var(--sans)" }} />
            {series.map((s, i) => (
              <Line key={i} dataKey={`v${i}`} name={s.label} stroke={s.color} dot={false} isAnimationActive={false}
                strokeWidth={s.width ?? 1.75} strokeOpacity={s.faint ? 0.75 : 1} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

/** The talk's core in one bar: the CO₂ uptake cools, the darker canopy warms; the tick is what is left. */
function Tug({ co2, alb, share, year }: { co2: number; alb: number; share: number; year: number }) {
  const t = useT(), num = useNum();
  const span = Math.max(Math.abs(co2), Math.abs(alb), 1e-9), net = co2 + alb;
  const at = (v: number) => 50 + (v / span) * 48;
  const seg = (v: number, color: string) => (
    <span className="absolute inset-y-0" style={{ [v < 0 ? "right" : "left"]: "50%", width: `${(Math.abs(v) / span) * 48}%`, background: color }} />
  );
  const fmt = (v: number) => (v > 0 ? "+" : "") + num(v, 1).replace(/^-/, "−");
  const pct = Math.round((1 - share) * 100);
  const title = t("panel.tug", { year });
  return (
    <figure aria-label={title} className="mt-3">
      <figcaption className="text-[11px] font-medium leading-tight text-ink">{title}</figcaption>
      <div className="relative mt-1.5 h-2.5 overflow-hidden rounded-sm bg-ink/[0.05]" aria-hidden>
        {seg(co2, "var(--co2)")}
        {seg(alb, "var(--alb)")}
        <span className="absolute inset-y-0 left-1/2 w-px bg-ink/30" />
        <span className="absolute -inset-y-0.5 w-0.5 -translate-x-1/2 rounded bg-ink" style={{ left: `${at(net)}%` }} />
      </div>
      <div className="mt-1 flex justify-between text-[11px] tabular-nums">
        <span style={{ color: "var(--co2)" }}>{t("panel.tugCo2")} {fmt(co2)}</span>
        <span style={{ color: "var(--alb)" }}>{t("panel.tugAlb")} {fmt(alb)}</span>
      </div>
      {Number.isFinite(share) && (
        <p className="mt-0.5 text-xs text-inkMuted">{pct >= 0 ? t("panel.albedoTakes", { pct: num(pct) }) : t("panel.albedoAdds", { pct: num(-pct) })}</p>
      )}
    </figure>
  );
}

/** Where this cell stands: every reforestable cell of the world as a histogram in the map's colours, this one marked. */
function RankStrip({ atlas, cell, year }: { atlas: Atlas; cell: number; year: number }) {
  const t = useT(), num = useNum(), dark = useDark();
  const base = atlas.meta.scales.baumwirkung, sc = themedScale(base, dark);
  const r = useMemo(() => treeRank(atlas, cell, year, base.domain as [number, number]), [atlas, cell, year, base]);
  if (!r) return null;
  const max = Math.max(...r.bins), n = r.bins.length, [lo, hi] = r.domain, w = (hi - lo) / n;
  const pos = Math.max(0, Math.min(100, ((r.here - lo) / (hi - lo)) * 100));
  const title = t("panel.rank", { year });
  return (
    <figure aria-label={title} className="mt-3">
      <figcaption className="flex items-baseline justify-between gap-2 text-[11px] leading-tight">
        <span className="font-medium text-ink">{title}</span>
      </figcaption>
      <div className="relative mt-1.5 flex h-7 items-end gap-px" aria-hidden>
        {r.bins.map((b, i) => {
          const [R, G, B] = scaleColor(sc, lo + (i + 0.5) * w);
          return <span key={i} className="flex-1 rounded-t-[1px]" style={{ height: `${Math.max(4, Math.sqrt(b / max) * 100)}%`, background: `rgb(${R},${G},${B})` }} />;
        })}
        <span className="absolute -bottom-1 -top-1 w-0.5 -translate-x-1/2 rounded bg-ink" style={{ left: `${pos}%` }} />
      </div>
      <p className="mt-1 text-xs text-inkMuted">{t(r.cools ? "panel.rankCools" : "panel.rankWarms", { pct: num(r.pct) })}</p>
    </figure>
  );
}

/** One input of the model at this cell, on its own ramp; pressing it paints that layer on the map. */
function ConditionRow({ atlas, cell, year, id, active, onLayer }: { atlas: Atlas; cell: number; year: number; id: LayerId; active: boolean; onLayer?(id: LayerId): void }) {
  const t = useT(), num = useNum(), dark = useDark();
  const l = LAYERS.find((x) => x.id === id)!;
  const base = scaleOf(atlas, l), sc = base && themedScale(base, dark);
  const v = l.value(atlas, cell, year);
  const ok = Number.isFinite(v);
  const unit = sc?.unit ?? "";
  const digits = id === "elec" ? 2 : Math.abs(v) < 10 ? 1 : 0;
  const shown = ok ? `${num(v, digits)} ${unit}`.trim() : t(l.reason(atlas, cell) ?? "reason.noTrees");
  const pos = ok && sc ? Math.max(0, Math.min(100, ((v - sc.domain[0]) / (sc.domain[1] - sc.domain[0])) * 100)) : null;
  return (
    <li>
      <button type="button" aria-pressed={active} aria-label={`${t(l.label)}: ${shown}`} onClick={() => onLayer?.(id)}
        className="group grid w-full grid-cols-[minmax(0,1fr)_3rem_6rem] items-center gap-2 rounded px-1.5 py-1 text-left text-xs hover:bg-ink/5 aria-pressed:bg-[color-mix(in_srgb,var(--ch-soft)_35%,transparent)]">
        <span className="truncate text-ink">{t(l.label)}</span>
        <span className="relative h-1.5 rounded-sm" style={{ background: sc ? `linear-gradient(to right, ${sc.stops.join(",")})` : undefined, opacity: ok ? 1 : 0.25 }} aria-hidden>
          {pos !== null && <span className="absolute -inset-y-1 w-0.5 -translate-x-1/2 rounded bg-ink" style={{ left: `${pos}%` }} />}
        </span>
        <span className={"truncate text-right tabular-nums " + (ok ? "text-ink" : "text-[10.5px] italic text-inkMuted")}>{shown}</span>
      </button>
    </li>
  );
}

/**
 * A cell, in the order the questions arrive: does a tree here cool (and from when), why (CO₂ against albedo),
 * compared to what (the world's cells, the talk's places), and what the model's inputs are here.
 * `dense`: the phone sheet, with flatter charts.
 */
export function CellPanel({ atlas, cell, year, onClose, dense = false, layer, onLayer }:
  { atlas: Atlas; cell: number; year: number; onClose(): void; dense?: boolean; layer?: LayerId; onLayer?(id: LayerId): void }) {
  const t = useT(), num = useNum(), dark = useDark();
  const { lat, lon } = cellCenter(cell);
  const key = typeKey(atlas, cell);
  const s = useMemo(() => {
    const r = cellSeries(atlas, cell);
    return r && { ...r, phiCo2: r.phiCo2.map((v) => v * 1e15), phiAlb: r.phiAlb.map((v) => v * 1e15), dt: r.dt.map((v) => v * 1e15) };
  }, [atlas, cell]);
  // the talk's three places, as thin lines behind this cell's own (the cell itself is not drawn twice)
  const sites = useMemo(() => atlas.meta.sites.flatMap((site, i) => {
    const ref = atlas.meta.reference[i];
    const c = ref && ref.i * 720 + ref.j;
    const r = c !== undefined && c !== cell ? cellSeries(atlas, c) : null;
    return r ? [{ label: site.name.replace(/\s*\(.*\)$/, ""), color: site.color, values: r.dt.map((v) => v * 1e15), width: 1, faint: true }] : [];
  }), [atlas, cell]);
  const cool = key ? coolsFrom(atlas, cell) : null;
  const until = key ? coolsUntil(atlas, cell) : null;
  const build = dacBuildMt(atlas, cell, year);
  const [group, zone] = key ? key.split("_") : ["", ""];
  const y = Math.round(year), k = yearIndex(atlas, year);
  const status = cool ? t("panel.coolsFrom", { year: cool }) : until ? t("panel.coolsUntil", { year: until }) : t("panel.neverCools");
  const fmt = (v: number, d = 0) => (Number.isFinite(v) ? num(v, d).replace(/^-/, "−") : "–");
  const share = key ? netShare(atlas, cell, year) : NaN;
  const facts = key && s ? [
    { label: t("panel.factDt", { year: y }), value: fmt(deltaT(atlas, cell, year) * 1e15, 1), unit: "10⁻¹⁵ K" },
    { label: t("panel.factNet", { year: y }), value: fmt(share * 100), unit: "%" },
    { label: t("panel.factStock", { year: y }), value: fmt(s.m[k], 1), unit: "kg C" },
  ] : [];
  const curve = key && atlas.meta.curves[key];
  const heading = (id: Key) => <h3 className="mb-0.5 mt-4 text-[11px] font-semibold uppercase tracking-[0.08em] text-inkMuted">{t(id)}</h3>;

  return (
    <article className="relative text-[13px] leading-snug" data-ch="baeume">
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <h2 className="ch-text font-serif text-base font-semibold leading-tight">
            {key ? t("panel.forest", { type: t(`type.${group}` as Key), zone: t(`zone.${zone}` as Key) }) : t("panel.noForest")}
          </h2>
          <p className="mt-0.5 text-xs text-inkMuted">
            {key && <>{t("panel.areaShort", { area: num(atlas.f.area[cell] / 1e6), trees: num(atlas.f.trees[cell] / 1e6, 1) })} · </>}
            {num(lat, 2)}, {num(lon, 2)}
          </p>
        </div>
        <button aria-label={t("panel.close")} onClick={onClose} className="-mr-2 -mt-1.5 grid h-10 w-10 shrink-0 place-items-center rounded-full text-inkMuted hover:bg-ink/5 hover:text-ink active:bg-ink/10"><X size={18} /></button>
      </div>
      {key && s && curve && (
        <>
          <dl className="mt-2 grid grid-cols-3 divide-x divide-[var(--paper-line)] rounded-md border border-[var(--paper-line)] bg-paper/60">
            {facts.map((f) => (
              <div key={f.label} className="px-2 py-1.5">
                <dt className="truncate text-[10.5px] text-inkMuted">{f.label}</dt>
                <dd className="font-serif text-[15px] font-semibold tabular-nums leading-tight text-ink">{f.value}<span className="ml-0.5 font-sans text-[10.5px] font-normal text-inkMuted">{f.unit}</span></dd>
              </div>
            ))}
          </dl>
          <p className={"mt-2 flex items-center gap-2 text-xs font-medium " + (until || !cool ? "" : "ch-text")} style={until || !cool ? { color: "var(--alb)" } : undefined}>
            <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: "currentColor" }} />{status}
          </p>
          <Tug co2={atlas.f.a[cell] * curve.dtCo2[k] * 1e15} alb={atlas.f.b[cell] * curve.dtAlbUnit[k] * 1e15} share={share} year={y} />
          <RankStrip atlas={atlas} cell={cell} year={year} />
          <Chart tall={!dense} title={t("panel.compare")} years={s.years} year={year}
            series={[...sites, { label: t("panel.here"), color: dark ? "var(--ch-soft)" : "var(--ch)", values: s.dt, width: 2.25 }]} />
          <Chart title={t("panel.forcing")} years={s.years} year={year} series={[
            { label: t("panel.forcingCo2"), color: "var(--co2)", values: s.phiCo2 },
            { label: t("panel.forcingAlb"), color: "var(--alb)", values: s.phiAlb }]} />
          <Chart title={t("panel.stock")} years={s.years} year={year} series={[{ label: t("panel.stockSeries"), color: "var(--co2)", values: s.m }]} />
        </>
      )}
      {heading("panel.conditions")}
      <p className="mb-1 text-[11px] italic text-inkMuted">{t("panel.conditionsHint")}</p>
      <ul aria-label={t("panel.conditions")} className="-mx-1.5">
        {TREE_ROWS.map((id) => <ConditionRow key={id} atlas={atlas} cell={cell} year={year} id={id} active={layer === id} onLayer={onLayer} />)}
      </ul>
      <div data-ch="dac">
        {heading("panel.dac")}
        {atlas.f.dacOk[cell] ? (
          <>
            <ul aria-label={t("panel.dac")} className="-mx-1.5">
              {DAC_ROWS.map((id) => <ConditionRow key={id} atlas={atlas} cell={cell} year={year} id={id} active={layer === id} onLayer={onLayer} />)}
            </ul>
            {build > 0 && <p className="mt-1 text-[11px] leading-snug text-inkMuted">{t("panel.dacBuild", { mt: num(build, 1), year: y })}</p>}
          </>
        ) : (
          <p className="text-xs text-inkMuted">{t("panel.dacTooCold")}</p>
        )}
      </div>
    </article>
  );
}
