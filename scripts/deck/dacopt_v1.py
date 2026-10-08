"""DAC chapter: the optimisation (where, when, how much) -- slide 30 (problem) and slide 31 (result).

Data: data/dac/optim.json (scripts/dac_optim_export.py), data/dac/speicher_gidden.json, luecke.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from dacopt_assets import LAT_N, LAT_S, assets
from patch_story4 import _rep, _sec

HERE = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
AMBER = "#9a6516"
RED = "#c4121f"

CSS = """
/* ---------- DAC optimisation (slides 30/31) ---------- */
.opt { display: grid; grid-template-columns: 470px 1fr; gap: 46px; flex: 1; min-height: 0; align-items: start; }
.opt .cards { display: flex; flex-direction: column; gap: 14px; }
.opt .card { position: relative; border: 2.5px solid transparent; border-radius: 12px; padding: 8px 10px 6px; background: rgba(154,101,22,0);
             transition: border-color .35s, background .35s; }
.opt .card h5 { font: 600 19px/1.2 var(--sans); color: var(--ink-2); margin: 0 0 6px; }
.opt .card h5 small { font-weight: 400; color: var(--muted); font-size: 16px; }
.opt .card .map { position: relative; width: 446px; height: 176px; }
.opt .card .map img, .opt .card .map svg { position: absolute; inset: 0; width: 100%; height: 100%; image-rendering: pixelated; }
.opt .lines { display: flex; flex-direction: column; gap: 22px; padding-top: 6px; }
.opt .ol { font: 400 29px/1.3 var(--sans); color: var(--ink); }
.opt .ol .k { display: inline-block; width: 168px; color: var(--muted); font-size: 24px; }
.opt .ol .sub { display: block; margin: 4px 0 0 168px; font-size: 20px; color: var(--muted); }
.opt .ol b { font-weight: 600; color: #6b4410; }
.slide:not(:has(.os2.shown)) .ol1 .hl::before,
.slide:has(.os2.shown):not(:has(.os3.shown)) .ol2 .hl::before,
.slide:has(.os3.shown):not(:has(.os4.shown)) .ol3 .hl::before,
.slide:has(.os4.shown):not(:has(.os5.shown)) .ol4 .hl::before,
.slide:has(.os5.shown):not(:has(.os6.shown)) .ol5 .hl::before { border-color: #9a6516; background: rgba(154, 101, 22, .08); }
.slide:has(.os3.shown):not(:has(.os4.shown)) .card:is(.c-eta, .c-gap),
.slide:has(.os4.shown):not(:has(.os5.shown)) .card.c-store { border-color: #9a6516; background: rgba(154, 101, 22, .06); }
"""


def _xy(lon, lat, w, h):
    return (lon + 180) / 360 * w, (LAT_N - lat) / (LAT_N - LAT_S) * h


def _de(v, nd=0):
    return f"{v:,.{nd}f}".replace(",", " ").replace(".", ",")


def _store_svg(a) -> str:
    store = json.loads((REPO / "data/dac/speicher_gidden.json").read_text())
    W, H = 446, 176
    out = [f'<svg viewBox="0 0 {W} {H}" aria-hidden="true">']
    big = sorted(((v["prudent"], k) for k, v in store.items() if v["prudent"] > 3 and k in a["cent"]), reverse=True)
    for gt, k in big:
        x, y = _xy(*a["cent"][k], W, H)
        r = 2.2 * np.sqrt(gt)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{AMBER}" fill-opacity=".55" stroke="#fff" stroke-width="1"/>')
    labels = {"RUS": (8, -2), "USA": (-14, -18), "AUS": (-20, -22), "BRA": (14, 6), "DEU": (-30, -12)}
    for k, (dx, dy) in labels.items():
        x, y = _xy(*a["cent"][k], W, H)
        gt = store[k]["prudent"]
        if k == "DEU":
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="#1b2420"/>')
        out.append(f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" font-family="IBM Plex Sans" font-size="15" font-weight="600" '
                   f'fill="#1b2420" paint-order="stroke" stroke="#fff" stroke-width="3">{k} {_de(gt, 1 if gt < 10 else 0)}</text>')
    out.append("</svg>")
    return "".join(out)


def _gap_svg() -> str:
    d = json.loads((REPO / "docs/slides/chart_data/luecke.json").read_text())
    y, need, k = np.array(d["y"]), np.array(d["need"]), np.array(d["k"])
    gap = np.maximum(0, need - k)
    W, H, L, B, T = 446, 176, 46, 28, 10
    X = lambda v: L + (v - 2026) / 74 * (W - L - 28)
    Y = lambda v: T + (1 - v / 350) * (H - T - B)
    pts = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(y, gap))
    s = [f'<svg viewBox="0 0 {W} {H}" aria-hidden="true" font-family="IBM Plex Sans">']
    for v in (0, 100, 200, 300):
        s.append(f'<line x1="{L}" x2="{W - 28}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#e4ddcf" stroke-width="1"/>'
                 f'<text x="{L - 6}" y="{Y(v) + 5:.1f}" text-anchor="end" font-size="17" fill="#7a7466">{v}</text>')
    for v in (2026, 2050, 2075, 2100):
        s.append(f'<text x="{X(v):.1f}" y="{H - 6}" text-anchor="middle" font-size="17" fill="#7a7466">{v}</text>')
    s.append(f'<polygon points="{X(2026):.1f},{Y(0):.1f} {pts} {X(2100):.1f},{Y(0):.1f}" fill="{RED}" fill-opacity=".55"/>')
    s.append(f'<polyline points="{pts}" fill="none" stroke="#8e0d16" stroke-width="2.5" stroke-dasharray="7 4"/>')
    i = int(np.argmax(gap))
    s.append(f'<text x="{X(y[i]) + 16:.1f}" y="{Y(gap[i]) + 2:.1f}" font-size="16" font-weight="600" fill="#8e0d16">{_de(gap[i])} mK</text>')
    s.append("</svg>")
    return "".join(s)


def _slide30(res: dict) -> str:
    a = assets()
    h = res["haupt"]
    x = np.array(h["x"])
    nord = sum(x[h["laender"].index(c)].sum() for c in ("NOR", "SWE", "FIN", "FRA", "DEU", "GBR") if c in h["laender"])
    share = nord / x.sum()
    assert share < 0.10, f"takeaway needs Nordic share < 10 %, got {share:.1%}"
    store = json.loads((REPO / "data/dac/speicher_gidden.json").read_text())
    world = sum(v["prudent"] for v in store.values())
    return f'''<section class="slide" data-ch="dac" data-title="Optimierung von DAC">
  <header class="sh"><h2>Optimierung: wo, wann und wie viel DAC?</h2></header>
  <div class="body">
    <div class="opt">
      <div class="cards">
        <div class="card c-eta"><h5>Netto-Anteil je Ort <small>(2030, Folie 29)</small></h5><div class="map"><img src="{a["eta_png"]}" alt=""></div></div>
        <div class="card c-store"><h5>Speicher je Land <small>(Gt CO₂, Gidden et al. 2025)</small></h5><div class="map"><img src="{a["store_png"]}" alt="">{_store_svg(a)}</div></div>
        <div class="card c-gap"><h5>Lücke zu 1,5 °C <small>(mK, Folie 25)</small></h5><div class="map">{_gap_svg()}</div></div>
      </div>
      <div class="lines">
        <div class="ol ol1"><span class="k">Gesucht</span><span class="hl">DAC-Entnahme <b>x</b> je Land und Jahr</span><span class="sub">2026 bis 2100, in Gt CO₂ pro Jahr</span></div>
        <div class="ol ol2 rise os2" data-step="1"><span class="k">Minimiere</span><span class="hl">nötige Anlagen: größte Jahresentnahme</span><span class="sub">bei gleicher Kapazität: kleinste Gesamtmenge Σ <b>x</b></span></div>
        <div class="ol ol3 rise os3" data-step="2"><span class="k">so dass</span><span class="hl">Kühlung ≥ Lücke ab 2100</span><span class="sub">Kühlung aus Netto-Anteil × <b>x</b> und Klimaantwort (FaIR)</span></div>
        <div class="ol ol4 rise os4" data-step="3"><span class="k"></span><span class="hl">Σ Einlagerung ≤ Speicher je Land</span><span class="sub">weltweit {_de(world)} Gt; Deutschland 1,3 Gt</span></div>
        <div class="ol ol5 rise os5" data-step="4"><span class="k"></span><span class="hl">Wachstum ≤ 20 % pro Jahr</span><span class="sub">so schnell wie einst die Windkraft; Start 2030: 8,8 Mt/a geplant</span></div>
      </div>
    </div>
    <div class="foot"><div></div><p class="takeaway os6" data-step="5" style="--d:0">Speicher gibt es weltweit genug, aber kaum dort, wo der Strom am saubersten ist.</p></div>
  </div>
  <p class="src">Lineares Programm, eigene Rechnung. Netto-Anteil: Median der besten 10 % der Zellen je Land mit Sedimentbecken in höchstens 100 km. Speicher: „prudent planetary limit“ je Land (Gidden et al. 2025, Nature 645, 124). Wachstum: Wind-Analogie, Kapazität 2030 (Zurbriggen et al. 2026, Nat. Commun. 17, 6184). Klimaantwort: FaIR, wie bei den Bäumen.</p>
  <aside class="notes" data-n="0">
    <p>Die Lücke von eben wollen wir mit DAC schließen. Die Frage ist jetzt nicht mehr „Baum oder Maschine je Tonne“, sondern: Wo, wann und wie viel müsste man bauen? Das rechne ich als Optimierungsproblem. Links die drei Eingänge: wie viel einer entnommenen Tonne je Ort netto bleibt, wie viel CO₂ jedes Land sicher speichern kann, und die Lücke zu 1,5 °C.</p>
    <p>Gesucht ist die Entnahme je Land und Jahr. Klick: Wir wollen so wenige Anlagen wie möglich bauen, also die größte Jahresentnahme klein halten; bei gleicher Anlagenzahl so wenig wie möglich entnehmen. Klick: Die Kühlung muss die Lücke spätestens 2100 decken; den Overshoot davor lassen wir zu. Die Kühlung rechne ich aus dem Netto-Anteil und derselben Klimaantwort wie beim Baum. Klick: Kein Land darf mehr einlagern als seinen Speicher. Das sind die Zahlen von Gidden et al., die alles abziehen, was nicht sicher ist: Schutzgebiete, Siedlungen, zu flach, zu tief. Weltweit 1 460 Gigatonnen; Deutschland 1,3, Norwegen 6,9, Russland 244, USA 141. Klick: Und die Technik kann nicht beliebig schnell wachsen: höchstens 20 Prozent im Jahr, so schnell wie einst die Windkraft, ausgehend von den 8,8 Megatonnen, die für 2030 geplant sind.</p>
    <p>Klick: Speicher ist weltweit genug, aber nicht dort, wo der Strom am saubersten ist. Nordeuropa hat sauberen Strom, aber fast keinen sicheren Speicher.</p>
    <p class="q">Falls Fragen kommen — DAC kommt zusätzlich zu den 335 Gt Entnahme, die in Very Low schon stecken. Speicher heißt hier: Sedimentbecken innerhalb von 100 km um die Anlage, kein Transport über Landesgrenzen; Basalt-Mineralisierung (Island) ist bei Gidden nicht enthalten. Die Klimaantwort ist je Tonne linear gerechnet; mit vollem FaIR nachgerechnet kühlt der Pfad 2099 um {_de(100 * res["fair_abweichung_2100_rel"], 1)} % stärker, die Rechnung ist also leicht konservativ.</p>
  </aside>
</section>

'''


def patch(page: str) -> str:
    res = json.loads((REPO / "data/dac/optim.json").read_text())
    page = page.replace("</style>", CSS + "</style>", 1)
    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)
    m = _sec(main, "Netto-Entnahme von DAC")
    sec29 = _rep(m.group(0), "<p>Diese Karte setzt einen Strompfad voraus. Wie robust ist das? Die nächste Folie rechnet drei Pfade.</p>",
                 "<p>Wo und wann sollte man also bauen, damit es für 1,5 °C reicht? Das rechnen wir jetzt. Andere Strompfade: Backup „DAC in drei Strompfaden“.</p>")
    main = main[: m.start()] + sec29 + _slide30(res) + main[m.end():]
    main = patch_result(main + "<!-- BACKUP:BEGIN -->" + backup, res)
    main, backup = main.split("<!-- BACKUP:BEGIN -->", 1)
    from patch_story3 import BACKUP_MARK
    moved = []
    for title in ("DAC in drei Strompfaden", "Priorisierung von Aufforstung und DAC"):
        m = _sec(main, title)
        moved.append(re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', m.group(0)))
        main = main[: m.start()] + main[m.end():]
    assert BACKUP_MARK in backup
    backup = backup.replace(BACKUP_MARK, "".join(moved) + BACKUP_MARK, 1)
    main = patch_closing(main, res)
    n = iter(range(1, 1000))
    main = re.sub(r'<aside class="notes" data-n="\d+">', lambda mm: f'<aside class="notes" data-n="{next(n)}">', main)
    return main + "<!-- BACKUP:BEGIN -->" + backup


# ---------------------------------------------------------------- slide 31: result
REGIONS = {  # Gidden's IPCC R5 names -> label, colour
    "R5OECD90+EU": ("OECD & EU", AMBER),
    "R5MAF": ("Naher Osten & Afrika", "#4f7a8c"),
    "R5ASIA": ("Asien", "#6f8f55"),
    "R5LAM": ("Lateinamerika", "#8e6aa8"),
    "R5REF": ("Reformländer", "#7a7466"),
}

CSS31 = """
.res { display: grid; grid-template-columns: 640px 1fr; gap: 40px; flex: 1; min-height: 0; }
.res .left { display: flex; flex-direction: column; gap: 10px; }
.res .right { display: grid; grid-template-rows: 1fr 250px; gap: 4px; min-height: 0; }
.res .right .chart { min-height: 0; }
.res h5 { font: 600 20px/1.2 var(--sans); color: var(--ink-2); margin: 0 0 4px; }
.res h5 small { font-weight: 400; color: var(--muted); font-size: 17px; }
.res .wmap { position: relative; width: 640px; height: 252px; }
.res .wmap img, .res .wmap svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.res .wmap img { image-rendering: pixelated; opacity: .9; }
"""

EC_DAC = r"""
/* slide 31: temperature gap and DAC cooling; DAC removal per region */
const EC_DAC_TEMP = {
  steps: 1,
  option(k) {
    const D = window.DAC_OPT, P = (ys) => D.y.map((y, i) => [y, ys[i]]);
    const base = k >= 1 ? D.cool : D.cool.map(() => 0);
    const end = (text, color) => ({ show: true, formatter: text, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 10 });
    const series = [
      { id: 'base', type: 'line', stack: 'g', showSymbol: false, silent: true, data: P(base), lineStyle: { width: 0 }, z: 2, tooltip: { show: false } },
      { id: 'fill', type: 'line', stack: 'g', showSymbol: false, silent: true, data: P(D.gap.map((v, i) => Math.max(0, v - base[i]))), lineStyle: { width: 0 }, z: 2,
        tooltip: { show: false }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(196,18,31,.62)' }, { offset: 1, color: 'rgba(196,18,31,.22)' }]) },
        animationDuration: 1400 },
      { id: 'need', type: 'line', showSymbol: false, data: P(D.gap), lineStyle: { color: '#8e0d16', width: 3.2, type: [10, 6] }, itemStyle: { color: '#8e0d16' }, z: 6,
        endLabel: k >= 1 ? { show: false } : end('nötig für 1,5 °C', '#8e0d16'), animationDuration: 1200,
        markPoint: { symbol: 'circle', symbolSize: 11, itemStyle: { color: '#8e0d16', borderColor: '#fff', borderWidth: 2 },
                     label: { show: true, position: 'right', distance: 8, offset: [4, -16], formatter: `nötig für 1,5 °C: ${ecNum(Math.max(...D.gap), 0)} mK`,
                              color: '#8e0d16', fontFamily: EC.font, fontSize: 19, fontWeight: 600 },
                     data: [{ coord: [D.y[D.gap.indexOf(Math.max(...D.gap))], Math.max(...D.gap)] }] } }
    ];
    if (k >= 1) series.push({ id: 'cool', type: 'line', showSymbol: false, data: P(D.cool), lineStyle: { color: '#9a6516', width: 3.6 }, itemStyle: { color: '#9a6516' }, z: 7,
      endLabel: end('DAC kühlt:\n2100 Lücke zu', '#9a6516'), animationDuration: 1800 });
    return {
      animationDurationUpdate: 900, animationEasingUpdate: 'cubicInOut',
      title: { text: 'Lücke zu 1,5 °C und Kühlung durch DAC [mK]', left: 74, top: 0, textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 21, fontWeight: 600 } },
      grid: { left: 74, right: 190, top: 46, bottom: 40 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisTick: { show: true, customValues: [2026, 2050, 2075, 2100] }, axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: 350, interval: 100,
                      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19 }, splitLine: { show: true, lineStyle: { color: EC.grid } } }),
      tooltip: ecTooltip({ trigger: 'axis', formatter: ps => `<b>${ps[0].value[0]}</b><br>` + ps.filter(p => ['need', 'cool'].includes(p.seriesId))
                    .map(p => `${ecDot(p.color)}${ecNum(p.value[1], 0)} mK`).join('<br>') }),
      series
    };
  }
};
const EC_DAC_RAMP = {
  steps: 0,
  option() {
    const D = window.DAC_OPT;
    const series = D.ramp.map((r, j) => ({ id: r.name, name: r.name, type: 'line', stack: 'r', showSymbol: false, data: D.y.map((y, i) => [y, r.data[i]]),
      lineStyle: { width: 0 }, itemStyle: { color: r.color }, areaStyle: { color: r.color, opacity: .85 }, z: 3, animationDuration: 1800 }));
    series.push({ id: 'cap', type: 'line', showSymbol: false, silent: true, data: [[D.capYear, D.cap], [2100, D.cap]], lineStyle: { color: EC.ink, width: 1.5, type: [6, 5] }, z: 4,
      tooltip: { show: false }, endLabel: { show: true, formatter: `${ecNum(D.cap, 1)} Gt/a`, color: EC.ink, fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 10 }, animationDelay: 1500 });
    return {
      title: { text: 'DAC-Entnahme weltweit [Gt/a]', left: 74, top: 0, textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 21, fontWeight: 600 } },
      grid: { left: 74, right: 190, top: 46, bottom: 40 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisTick: { show: true, customValues: [2026, 2050, 2075, 2100] }, axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: 8, interval: 2,
                      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19 }, splitLine: { show: true, lineStyle: { color: EC.grid } } }),
      tooltip: ecTooltip({ trigger: 'axis', formatter: ps => `<b>${ps[0].value[0]}</b><br>` + ps.filter(p => p.seriesId !== 'cap')
                    .map(p => `${ecDot(p.color)}${ecNum(p.value[1], 2)} Gt/a`).join('<br>') }),
      series
    };
  }
};
"""


def _result_data(res: dict) -> dict:
    h = res["haupt"]
    x = np.array(h["x"])
    y = h["jahre"]
    tot = x.sum(axis=0)
    # world total only: the split between countries year by year is not unique (any order that fills the
    # same storages at the same capacity is optimal), the map shows the unique part, the totals per country
    ramp = [{"name": "weltweit", "color": AMBER, "data": [round(float(v), 4) for v in tot]}]
    cap = float(tot.max())
    return {"y": y, "gap": [round(1000 * v, 2) for v in h["luecke_k"]], "cool": [round(1000 * v, 2) for v in h["kuehlung_k"]],
            "ramp": ramp, "cap": round(cap, 2), "capYear": int(y[int(np.argmax(tot > 0.999 * cap))])}


def _bubble_svg(res: dict, a: dict) -> str:
    h = res["haupt"]
    x = np.array(h["x"]).sum(axis=1)
    W, H = 640, 252
    order = np.argsort(-x)
    s = [f'<svg viewBox="0 0 {W} {H}" aria-label="Weltkarte: DAC-Entnahme 2026 bis 2100 je Land, Kreisfläche nach Gigatonnen">']
    for j, i in enumerate(order):
        c = h["laender"][i]
        if x[i] < 1 or c not in a["cent"]:
            continue
        cx, cy = _xy(*a["cent"][c], W, H)
        col = REGIONS.get(h["region"][i], ("", "#7a7466"))[1]
        s.append(f'<circle class="pop" data-step="2" style="--d:{120 * j}" cx="{cx:.1f}" cy="{cy:.1f}" r="{3.2 * np.sqrt(x[i]):.1f}" '
                 f'fill="{col}" fill-opacity=".78" stroke="#fff" stroke-width="1.5"/>')
    off = {"USA": (0, -44), "DZA": (-52, 4), "LBY": (30, -26), "EGY": (34, 26), "NOR": (-4, -16)}
    for j, i in enumerate(order[:5]):
        c = h["laender"][i]
        cx, cy = _xy(*a["cent"][c], W, H)
        dx, dy = off.get(c, (0, -20))
        s.append(f'<text class="rise" data-step="2" style="--d:{120 * j + 400}" x="{cx + dx:.1f}" y="{cy + dy:.1f}" text-anchor="middle" '
                 f'font-family="IBM Plex Sans" font-size="18" font-weight="600" fill="#1b2420" paint-order="stroke" stroke="#f2ede2" stroke-width="4">'
                 f'{c} {_de(x[i])}</text>')
    s.append("</svg>")
    return "".join(s)


def _target_svg(res: dict) -> str:
    rows = res["ziel_kurve"]
    W, H, B, T = 640, 178, 34, 30
    bw, gap = 96, 46
    x0 = (W - len(rows) * bw - (len(rows) - 1) * gap) / 2
    top = max(r["kapazitaet_gt"] for r in rows)
    s = [f'<svg viewBox="0 0 {W} {H}" font-family="IBM Plex Sans" aria-label="Nötige DAC-Kapazität je Zieljahr">']
    s.append(f'<line x1="20" x2="{W - 20}" y1="{H - B}" y2="{H - B}" stroke="#8a918c" stroke-width="1"/>')
    for j, r in enumerate(rows):
        v = r["kapazitaet_gt"]
        hgt = (H - B - T) * v / top
        x = x0 + j * (bw + gap)
        y = H - B - hgt
        col = AMBER if r["ziel_jahr"] == 2100 else "#d9b97a"
        rr = min(10, hgt / 2)
        s.append(f'<path class="grow" data-step="3" style="--d:{150 * j}" d="M{x:.1f} {H - B} V{y + rr:.1f} a{rr} {rr} 0 0 1 {rr} {-rr} H{x + bw - rr:.1f} '
                 f'a{rr} {rr} 0 0 1 {rr} {rr} V{H - B} Z" fill="{col}"/>')
        s.append(f'<text class="rise" data-step="3" style="--d:{150 * j + 300}" x="{x + bw / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-size="19" '
                 f'font-weight="600" fill="#1b2420">{_de(v, 1 if v < 10 else 0)}</text>')
        s.append(f'<text x="{x + bw / 2:.1f}" y="{H - 8}" text-anchor="middle" font-size="19" fill="#5d665f">ab {r["ziel_jahr"]}</text>')
    s.append("</svg>")
    return "".join(s)


def _slide31(res: dict) -> str:
    a = assets()
    h = res["haupt"]
    d = _result_data(res)
    assert h["status"] == "geschlossen" and h["ziel_jahr"] == 2100
    cap = _de(d["cap"], 1)
    sens = res["sens"]
    g, c11 = np.array(h["luecke_k"]), np.array(sens["wachstum_11"]["kuehlung_k"])
    rest11 = _de(1000 * (g[-1] - c11[-1]))
    i50 = h["jahre"].index(2050)
    cool50, gap50 = _de(1000 * h["kuehlung_k"][i50], 1), _de(1000 * h["luecke_k"][i50])
    x = np.array(h["x"])
    tot50 = _de(x.sum(axis=0)[i50], 2)
    top = sorted(((x[i].sum(), c) for i, c in enumerate(h["laender"])), reverse=True)[:5]
    top_txt = ", ".join(f"{c} {_de(v)}" for v, c in top)
    zk = "; ".join(f"ab {r['ziel_jahr']}: {_de(r['kapazitaet_gt'], 1)} Gt/a" for r in res["ziel_kurve"])
    html = f'''<section class="slide" data-ch="dac" data-title="DAC-Ausbau nach Ort und Zeit">
  <header class="sh"><h2>DAC-Ausbau nach Ort und Zeit</h2></header>
  <div class="body">
    <div class="res">
      <div class="left">
        <div><h5>Wo: Entnahme 2026–2100 je Land <small>(Gt CO₂; <span style="color:#9a6516">●</span> OECD &amp; EU <span style="color:#4f7a8c">●</span> Naher Osten &amp; Afrika)</small></h5><div class="wmap"><img src="{a["land_png"]}" alt="">{_bubble_svg(res, a)}</div></div>
        <div class="rise" data-step="3"><h5>Früher 1,5 °C → mehr Anlagen <small>(nötige Kapazität, Gt/a)</small></h5>{_target_svg(res)}</div>
      </div>
      <div class="right">
        <div class="chart" data-ec="dactemp" data-label="Lücke zu 1,5 °C 2026 bis 2100 und Kühlung durch den optimierten DAC-Ausbau"></div>
        <div class="rise" data-step="1" style="display:flex; min-height:0"><div class="chart" data-ec="dacramp" style="flex:1" data-label="DAC-Entnahme je Region in Gt pro Jahr, 2026 bis 2100"></div></div>
      </div>
    </div>
    <div class="foot"><div></div><p class="takeaway" data-step="4" style="--d:0">1,5 °C bis 2100 braucht {cap} Gt/a DAC, so viel wie die kühnsten Szenarien. Bis 2050 wirkt es kaum.</p></div>
  </div>
  <p class="src">Lineares Programm, eigene Rechnung (Folie 30): kleinste Kapazität, mit der die Lücke ab dem Zieljahr geschlossen ist. Speicher: Gidden et al. 2025; Wachstum ≤ 20 %/a ab 8,8 Mt/a 2030: Zurbriggen et al. 2026; Klimaantwort FaIR. Regionen: IPCC R5.</p>
  <aside class="notes" data-n="0">
    <p>Das Ergebnis. Rechts oben noch einmal die Lücke zu 1,5 °C. Klick: Das kühlt der optimierte DAC-Ausbau. Lange passiert fast nichts: Weil die Technik höchstens 20 Prozent im Jahr wachsen kann, entnimmt sie 2050 erst {tot50} Gigatonnen im Jahr und kühlt um {cool50} Millikelvin, bei {gap50} Millikelvin Lücke. Erst ab den 2060ern wird es viel; ab {d["capYear"]} laufen {cap} Gigatonnen im Jahr, und 2100 ist die Lücke zu. Bis dahin bleibt der Overshoot.</p>
    <p>Klick: Wo? Vor allem in den USA und in Nordafrika: {top_txt} Gigatonnen. Dort gibt es viel sicheren Speicher und, ab den 2040ern, sauberen Strom. In welchem Jahr welches Land entnimmt, legt die Rechnung nicht eindeutig fest, nur wie viel insgesamt; deshalb zeige ich rechts die Welt als Ganzes. Nordeuropa hat sauberen Strom, aber kaum Speicher; Russland hat Speicher, aber Strom und Klima sind schlechter.</p>
    <p>Klick: Und wenn wir 1,5 °C früher wollen? Dann braucht es viel mehr Anlagen: {zk}. Jedes frühere Jahr kostet überproportional.</p>
    <p>Klick: {cap} Gigatonnen im Jahr sind so viel, wie die kühnsten Szenarien für DAC annehmen; vorsichtige Schätzungen liegen bei 3 bis 4. Mit rund 1,5 MWh je Tonne wären das etwa {_de(d["cap"] * 1.5 * 1000, 0)} TWh Strom, ein Drittel der heutigen Weltstromerzeugung.</p>
    <p class="q">Falls Fragen kommen — Mit 11 % Wachstum im Jahr (wie Ammoniak) ist 2100 nicht erreichbar: Es fehlen dann noch {rest11} mK. Mit dem technischen Speicherpotenzial statt der vorsichtigen Grenze oder mit dem Landesmedian statt der besten Standorte ändert sich die nötige Kapazität nicht ({_de(sens["technisch"]["kapazitaet_gt"], 1)} bzw. {_de(sens["median"]["kapazitaet_gt"], 1)} Gt/a); sie hängt am Klima und am Wachstum, nicht an der Ortswahl. Gegenprobe mit vollem FaIR: {_de(100 * res["fair_abweichung_2100_rel"], 1)} % mehr Kühlung 2099. Nicht enthalten: Kosten, Strom- und Wasserverfügbarkeit, Injektionsraten je Becken.</p>
  </aside>
</section>

'''
    return html


def patch_result(page: str, res: dict) -> str:
    d = _result_data(res)
    page = page.replace("</style>", CSS31 + "</style>", 1)
    m = re.search(r"const EC_CHARTS = \{([^}]*)\};", page)
    assert m and "luecke: EC_GAP" in m.group(1)
    page = page[: m.start()] + "window.DAC_OPT = " + json.dumps(d) + ";\n" + EC_DAC + \
        "const EC_CHARTS = {" + m.group(1).rstrip() + ", dactemp: EC_DAC_TEMP, dacramp: EC_DAC_RAMP };" + page[m.end():]
    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)
    m = _sec(main, "Optimierung von DAC")
    main = main[: m.end()] + _slide31(res) + main[m.end():]
    return main + "<!-- BACKUP:BEGIN -->" + backup


def patch_closing(main: str, res: dict) -> str:
    """Texts of 'Auf dem Holzweg? Nein.' and 'Methodischer Beitrag' after the optimisation."""
    h = res["haupt"]
    cap = _de(h["kapazitaet_gt"], 1)
    x = np.array(h["x"])
    tot = x.sum(axis=0)
    y = h["jahre"]
    cap_year = int(y[int(np.argmax(tot > 0.999 * tot.max()))])
    t50 = _de(tot[y.index(2050)], 2)
    k2090 = _de(next(r["kapazitaet_gt"] for r in res["ziel_kurve"] if r["ziel_jahr"] == 2090))
    m = _sec(main, "Auf dem Holzweg? Nein.")
    sec = m.group(0)
    sec = re.sub(r'<div class="col rise" data-step="1">.*?</div>',
                 f'<div class="col rise" data-step="1"><h4><span class="big-n">2</span>DAC schließt die Lücke, aber spät und nur in großem Maßstab</h4>'
                 f'<p>1,5 °C bis 2100: {cap} Gt/a ab {cap_year}<br>→ so viel wie die kühnsten Szenarien<br>→ bis 2050: {t50} Gt/a, kaum Wirkung<br>'
                 f'→ dort, wo Speicher ist (USA, Nordafrika), nicht dort, wo der Strom am saubersten ist</p></div>', sec, count=1, flags=re.S)
    sec = re.sub(r'<div class="col rise" data-step="2">.*?</div>',
                 '<div class="col rise" data-step="2"><h4><span class="big-n">3</span>Aufforstung früh, DAC so früh wie möglich hochfahren</h4>'
                 '<p>Baum: 5 Jahre später gepflanzt → 2050 fehlt knapp ein Viertel der Kühlung<br>→ dazu lokale Wirkungen: Schatten, Lebensraum<br>'
                 f'DAC: wächst höchstens 20 %/a<br>→ jedes frühere Zieljahr braucht viel mehr Anlagen (2090: {k2090} Gt/a)</p></div>', sec, count=1, flags=re.S)
    sec = _rep(sec, "Beides gebraucht, jeweils am geeigneten Ort und zur richtigen Zeit.",
               "Beides gebraucht: Bäume jetzt am geeigneten Ort, DAC jetzt hochfahren, denn es wirkt erst spät.")
    sec = re.sub(r'(<aside class="notes"[^>]*>).*?(</aside>)', lambda mm: mm.group(1) + f'''
    <p class="q">Ausführlich: Die Ingenieure sind nicht auf dem Holzweg: Ohne technische Entnahme lässt sich die Lücke zu 1,5 °C nicht schließen. Aber DAC wirkt spät: Selbst mit Wachstum wie bei der Windkraft braucht es {cap} Gt/a, um 2100 bei 1,5 °C zu sein, und bis 2050 kühlt es kaum. Bäume dort, wo sie kühlen, und zwar jetzt.</p>
    <p>Zurück zur Frage im Titel: Sind die Ingenieure auf dem Holzweg? Nein. Erstens reichen die Bäume nicht, selbst klug gepflanzt binden sie knapp ein Fünftel dessen, was das niedrigste Szenario braucht. Zweitens schließt DAC die Lücke, aber spät und nur in großem Maßstab: {cap} Gigatonnen im Jahr ab {cap_year}, so viel wie die kühnsten Szenarien annehmen, und vor allem dort, wo Speicher ist. Drittens die Zeit: Bäume jetzt, weil sie langsam wachsen; DAC so früh wie möglich hochfahren, weil es nur begrenzt schnell wachsen kann. Wer 1,5 °C früher will, braucht viel mehr Anlagen, für 2090 schon {k2090} Gigatonnen im Jahr. Die naive Rechnung vom Anfang zog die Grenze um den Baum. Mit der vollen Grenze ist die Antwort: beides, und beides jetzt.</p>
  ''' + mm.group(2), sec, count=1, flags=re.S)
    main = main[: m.start()] + sec + main[m.end():]

    m = _sec(main, "Methodischer Beitrag")
    sec = m.group(0)
    row = ('<tr class="rise" data-step="3"><td style="font-weight:600; color:var(--fjord)">Ausbau optimieren</td><td style="font-size:20px">—</td>'
           '<td style="font-size:20px">Lineares Programm: Speicher je Land (Gidden 2025), Wachstum ≤ 20 %/a</td>'
           '<td style="font-size:20px">nötige Kapazität je Zieljahr<br>→ Ort nach Speicher statt nach Strom</td></tr>\n      </tbody>')
    sec = _rep(sec, "</tbody>", row)
    sec = _rep(sec, '<p class="rise" data-step="3" style="margin-top:22px;', '<p class="rise" data-step="4" style="margin-top:22px;')
    sec = _rep(sec, "Zusatzstrom statt Netzmittel · ein Klimamitglied statt Ensemble",
               "Zusatzstrom statt Netzmittel · Injektionsraten je Becken · ein Klimamitglied statt Ensemble")
    sec = _rep(sec, '<p class="takeaway" data-step="4" style="--d:0; font-size:22px">Neu: eine zeitaufgelöste Rechnung je Ort für Baum und DAC, mit kalibriertem Klima-Emulator.',
               '<p class="takeaway" data-step="5" style="--d:0; font-size:22px">Neu: eine zeitaufgelöste Rechnung je Ort für Baum und DAC, mit kalibriertem Klima-Emulator und Ausbau-Optimierung.')
    sec = _rep(sec, "GWP100 und statische Bilanzen sehen nur Endzustände.</p>",
               "GWP100 und statische Bilanzen sehen nur Endzustände. Viertens die Optimierung: Erst mit Speicher- und Wachstumsgrenzen sieht man, "
               "wie viel DAC wann nötig ist und dass der Speicher, nicht der Strom, die Orte bestimmt.</p>")
    return main[: m.start()] + sec + main[m.end():]
