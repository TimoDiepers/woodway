"""Slide 31 (animated build-out: map, counters, net removal and cooling over time) and slide 32 (target year,
electricity mix) for patch_dac_optim."""

from __future__ import annotations

import numpy as np

from dacopt_assets import assets
from dacopt_v1 import _de, _xy

AMBER, TREE, NEED = "#9a6516", "#2f7a45", "#8e0d16"
MAP_W, MAP_H = 760, 300
LABEL_SIDE = {"DZA": "left", "LBY": "top", "EGY": "right", "USA": "top", "AUS": "top"}
SW, SH, SL, SR, ST, SB = 1420, 128, 76, 236, 12, 30   # one strip: width, height, margins

CSS31 = """
.play { display: grid; grid-template-columns: 980px 1fr; grid-template-rows: 300px auto; gap: 4px 34px; flex: 1; min-height: 0; }
.play .wmap { position: relative; width: 760px; height: 300px; }
.play .wmap img, .play .wmap svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.play .wmap img { image-rendering: pixelated; opacity: .85; }
.play .side { display: flex; flex-direction: column; gap: 10px; padding-top: 0; }
.play .yr { font: 600 64px/1 var(--sans); color: var(--ink); font-variant-numeric: tabular-nums; }
.play .ctr .n { font: 600 42px/1.05 var(--sans); color: #9a6516; font-variant-numeric: tabular-nums; }
.play .ctr .n small { font-size: 22px; font-weight: 500; }
.play .ctr .l { font: 400 18px/1.3 var(--sans); color: var(--muted); }
.play .side .takeaway { padding: 10px 14px 11px 46px; font-size: 19px; margin-top: 4px; }
.play .side .takeaway::before { left: 16px; top: 14px; width: 22px; height: 22px; }
.play .strips { grid-column: 1 / -1; display: flex; flex-direction: column; gap: 12px; }
.play .strips svg { width: 100%; height: auto; overflow: visible; display: block; }
.mix2 { display: grid; grid-template-columns: 1fr 470px; gap: 56px; flex: 1; min-height: 0; align-items: start; }
.mix2 h5 { font: 600 22px/1.25 var(--sans); color: var(--ink); margin: 0 0 8px; }
.mix2 h5 small { font-weight: 400; color: var(--muted); font-size: 18px; }
.mix2 svg { width: 100%; overflow: visible; }
.mix2 .box { border-left: 4px solid #9a6516; padding: 6px 0 6px 20px; }
.mix2 .box p { font: 400 21px/1.4 var(--sans); color: var(--ink-2); margin: 10px 0 0; }
"""


def play_data(res: dict, gap: dict) -> dict:
    h = res["haupt"]
    x, eta = np.array(h["x"]), np.array(h["eta"])
    countries = []
    for i, c in enumerate(h["laender"]):
        if x[i].max() <= 0.004:
            continue
        cx, cy = _xy(*assets()["cent"][c], MAP_W, MAP_H)
        countries.append({"c": c, "x": round(cx, 1), "y": round(cy, 1), "side": LABEL_SIDE.get(c, "top"),
                          "cap": [round(float(v), 4) for v in x[i]]})
    net = (x * eta).sum(axis=0)
    return {"y": h["jahre"], "c": countries, "tot": [round(float(v), 4) for v in x.sum(axis=0)],
            "cumnet": [round(float(v), 2) for v in np.cumsum(net)], "goal": round(h["co2_ziel_gt"], 1)}


def _axes(s, X, Y, ticks, unit, top_label):
    for v in ticks:
        s.append(f'<line x1="{SL}" x2="{SW - SR}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#e4dccb"/>'
                 f'<text x="{SL - 10}" y="{Y(v) + 6:.1f}" text-anchor="end" font-size="18" fill="#5d665f">{_de(v)}</text>')
    s.append(f'<text x="{SL}" y="{ST - 1}" font-size="18" font-weight="600" fill="#1b2420">{top_label} <tspan font-weight="400" fill="#5d665f">[{unit}]</tspan></text>')


def strips_svg(res: dict, gap: dict) -> str:
    h = res["haupt"]
    y = np.array(h["jahre"], dtype=float)
    x, eta = np.array(h["x"]), np.array(h["eta"])
    net = (x * eta).sum(axis=0)
    lim = np.minimum(np.array(res["wachstumsgrenze_gt"]), 9.5)
    tree, dac = np.array(gap["k"]), 1000 * np.array(h["kuehlung_k"])
    X = lambda v: SL + (v - 2026) / 74 * (SW - SL - SR)
    out = []
    # strip 1: cumulative net removal, with what is needed (target 2100) and what the growth limit allows at most
    cum = np.cumsum(net)
    goal = h["co2_ziel_gt"]
    lim_cum = np.cumsum(np.array(res["wachstumsgrenze_gt"])) * float(net.sum() / x.sum())  # at the path's net share
    T1, H1 = 300.0, SH + 22
    Y1 = lambda v: ST + 14 + (1 - v / T1) * (H1 - ST - 14 - 6)
    pts = lambda ys, Y: " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(y, ys))
    s = [f'<svg viewBox="0 0 {SW} {H1}" font-family="IBM Plex Sans" aria-label="Kumulierte Netto-CO2-Entnahme durch DAC, Ziel 2100 und Wachstumsgrenze">',
         '<defs><clipPath id="clipA"><rect class="dacclip" x="0" y="-20" width="0" height="400"/></clipPath></defs>']
    _axes(s, X, Y1, (0, 150, 300), "Gt CO₂", "1 · Netto entnommen, aufsummiert")
    ok = lim_cum <= T1
    j = int(np.flatnonzero(ok)[-1])
    s.append(f'<polyline points="{pts(lim_cum[: j + 1], Y1)}" fill="none" stroke="#5d665f" stroke-width="2" stroke-dasharray="6 5"/>')
    k = int(np.argmax(lim_cum >= 120))
    s.append(f'<text x="{X(y[k]) - 10:.1f}" y="{Y1(lim_cum[k]) + 6:.1f}" text-anchor="end" font-size="17" fill="#5d665f">höchstens möglich (+20 %/a)</text>')
    s.append(f'<line x1="{SL}" x2="{X(2100):.1f}" y1="{Y1(goal):.1f}" y2="{Y1(goal):.1f}" stroke="{NEED}" stroke-width="1.5" stroke-dasharray="3 5" opacity=".55"/>')
    s.append(f'<g clip-path="url(#clipA)"><polygon points="{X(2026):.1f},{Y1(0):.1f} {pts(cum, Y1)} {X(2100):.1f},{Y1(0):.1f}" fill="{AMBER}" fill-opacity=".9"/></g>')
    s.append(f'<circle cx="{X(2100):.1f}" cy="{Y1(goal):.1f}" r="7" fill="{NEED}" stroke="#fff" stroke-width="2"/>')
    s.append(f'<text x="{SW - SR + 12}" y="{Y1(goal) + 6:.1f}" font-size="19" font-weight="600" fill="{NEED}">nötig: {_de(goal)} Gt</text>')
    s.append(f'<line class="cursor" x1="{X(2026):.1f}" x2="{X(2026):.1f}" y1="{ST + 6}" y2="{H1 - 6}" stroke="#1b2420" stroke-width="2"/></svg>')
    out.append("".join(s))
    # strip 2: warming above 1.5 deg C over time -- Very Low, with the trees, with trees and DAC (the overshoot)
    T2, H2 = 350.0, SH + SB + 40
    Y2 = lambda v: ST + 14 + (1 - v / T2) * (H2 - SB - ST - 14)
    need = np.array(gap["need"])
    over = np.maximum(0.0, need - tree - dac)
    s = [f'<svg viewBox="0 0 {SW} {H2}" font-family="IBM Plex Sans" aria-label="Erwärmung über 1,5 °C 2026 bis 2100: Very Low, mit Bäumen, mit Bäumen und DAC">',
         '<defs><clipPath id="clipB"><rect class="dacclip" x="0" y="-20" width="0" height="600"/></clipPath></defs>']
    _axes(s, X, Y2, (0, 100, 200, 300), "mK", "2 · Erwärmung über 1,5 °C")
    for v in (2026, 2050, 2075, 2100):
        s.append(f'<text x="{X(v):.1f}" y="{H2 - 4}" text-anchor="middle" font-size="18" fill="#5d665f">{v}</text>')
    s.append(f'<polyline points="{pts(need, Y2)}" fill="none" stroke="{NEED}" stroke-width="2.5" stroke-dasharray="9 6"/>')
    s.append(f'<polyline points="{pts(need - tree, Y2)}" fill="none" stroke="{TREE}" stroke-width="2.5"/>')
    s.append(f'<g clip-path="url(#clipB)"><polygon points="{X(2026):.1f},{Y2(0):.1f} {pts(over, Y2)} {X(2100):.1f},{Y2(0):.1f}" fill="#c4121f" fill-opacity=".55"/>'
             f'<polyline points="{pts(over, Y2)}" fill="none" stroke="#8e0d16" stroke-width="3"/></g>')
    ip = int(np.argmax(need))
    s.append(f'<text x="{X(y[ip]) + 12:.1f}" y="{Y2(need[ip]) - 6:.1f}" font-size="18" font-weight="600" fill="{NEED}">Very Low</text>')
    xe = SW - SR + 12
    s.append(f'<text x="{xe}" y="{Y2(need[-1]) - 14:.1f}" font-size="18" font-weight="600" fill="{NEED}">Very Low {_de(need[-1])}</text>')
    s.append(f'<text x="{xe}" y="{Y2(need[-1] - tree[-1]) + 8:.1f}" font-size="18" font-weight="600" fill="{TREE}">+ Bäume {_de(need[-1] - tree[-1])}</text>')
    s.append(f'<text x="{xe}" y="{Y2(0) + 2:.1f}" font-size="18" font-weight="600" fill="#8e0d16">+ DAC: 1,5 °C</text>')
    s.append(f'<line class="cursor" x1="{X(2026):.1f}" x2="{X(2026):.1f}" y1="{ST + 6}" y2="{H2 - SB}" stroke="#1b2420" stroke-width="2"/></svg>')
    out.append("".join(s))
    return "".join(out)


PLAY_JS = r"""
/* slide 31: DAC build-out 2026 -> 2100 as an animation, started by the first click */
(function () {
  const D = window.DAC_PLAY, sec = document.querySelector('section[data-title="DAC-Ausbau nach Ort und Zeit"]');
  if (!D || !sec) return;
  const svg = sec.querySelector('.wmap svg'), NS = 'http://www.w3.org/2000/svg';
  const trig = sec.querySelector('.playtrig'), yr = sec.querySelector('.yr'), nCap = sec.querySelector('.n-cap'), nCum = sec.querySelector('.n-cum');
  const clips = sec.querySelectorAll('.dacclip'), curs = sec.querySelectorAll('.cursor');
  const X0 = %X0%, X1 = %X1%, DUR = 14000, Y0 = D.y[0], Y1 = D.y[D.y.length - 1];
  const lerp = (arr, t) => { const i = Math.min(arr.length - 2, Math.floor(t)), f = t - i; return arr[i] + f * (arr[i + 1] - arr[i]); };
  const nodes = D.c.map(c => {
    const g = document.createElementNS(NS, 'g'), ci = document.createElementNS(NS, 'circle'), tx = document.createElementNS(NS, 'text');
    ci.setAttribute('cx', c.x); ci.setAttribute('cy', c.y); ci.setAttribute('fill', '#9a6516'); ci.setAttribute('fill-opacity', '.82');
    ci.setAttribute('stroke', '#fff'); ci.setAttribute('stroke-width', '1.5');
    for (const [k, v] of [['font-family', 'IBM Plex Sans'], ['font-size', '19'], ['font-weight', '600'], ['fill', '#1b2420'],
                          ['paint-order', 'stroke'], ['stroke', '#f2ede2'], ['stroke-width', '4']]) tx.setAttribute(k, v);
    g.append(ci, tx); svg.append(g); return { c, ci, tx };
  });
  const fmt = (v, d) => v.toLocaleString('de-DE', { minimumFractionDigits: d, maximumFractionDigits: d });
  function draw(year) {
    const t = Math.max(0, Math.min(D.y.length - 1, year - Y0));
    for (const n of nodes) {
      const cap = lerp(n.c.cap, t), r = cap > 0.002 ? Math.max(4, 18 * Math.sqrt(cap)) : 0, sd = n.c.side;
      n.ci.setAttribute('r', r.toFixed(1));
      n.tx.setAttribute('text-anchor', sd === 'left' ? 'end' : sd === 'right' ? 'start' : 'middle');
      n.tx.setAttribute('x', (sd === 'left' ? n.c.x - r - 6 : sd === 'right' ? n.c.x + r + 6 : n.c.x).toFixed(1));
      n.tx.setAttribute('y', (sd === 'top' ? n.c.y - r - 8 : sd === 'bottom' ? n.c.y + r + 21 : n.c.y + 7).toFixed(1));
      n.tx.textContent = cap >= 0.2 ? `${n.c.c} ${fmt(cap, 1)}` : '';
    }
    yr.textContent = Math.floor(year);
    const cap = lerp(D.tot, t);
    nCap.firstChild.nodeValue = fmt(cap, cap < 1 ? 2 : 1) + ' ';
    nCum.firstChild.nodeValue = fmt(lerp(D.cumnet, t), 0) + ' ';
    const xc = (X0 + (year - Y0) / (Y1 - Y0) * (X1 - X0)).toFixed(1);
    clips.forEach(c => c.setAttribute('width', xc)); curs.forEach(c => { c.setAttribute('x1', xc); c.setAttribute('x2', xc); });
  }
  let t0 = null, wasShown = false;
  function tick(now) {
    const shown = trig.classList.contains('shown') && sec.classList.contains('active');
    if (shown && !wasShown) t0 = now;
    if (!trig.classList.contains('shown')) { draw(Y0); t0 = null; }
    else if (!sec.classList.contains('active')) draw(Y1);
    else { const f = Math.min(1, (now - t0) / DUR), e = f < .5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2; draw(Y0 + e * (Y1 - Y0)); }
    wasShown = shown; requestAnimationFrame(tick);
  }
  draw(Y0); requestAnimationFrame(tick);
})();
""".replace("%X0%", str(SL)).replace("%X1%", str(SW - SR))


def slide31(res: dict, gap: dict) -> str:
    h = res["haupt"]
    x, eta = np.array(h["x"]), np.array(h["eta"])
    tot = x.sum(axis=0)
    y = h["jahre"]
    cap = _de(tot.max(), 1)
    cap_year = int(y[int(np.argmax(tot > 0.999 * tot.max()))])
    i50, i60 = y.index(2050), y.index(2060)
    cum = np.cumsum((x * eta).sum(axis=0))
    top = sorted(((x[i, -1], c) for i, c in enumerate(h["laender"])), reverse=True)[:5]
    top_txt = ", ".join(f"{c} {_de(v, 1)}" for v, c in top)
    goal = _de(h["co2_ziel_gt"])
    need = gap["need"][-1]
    return f'''<section class="slide" data-ch="dac" data-title="DAC-Ausbau nach Ort und Zeit">
  <header class="sh"><h2>Wann und wo DAC gebaut wird</h2></header>
  <div class="body">
    <div class="play">
      <div class="wmap"><img src="{assets()["land_png"]}" alt=""><svg viewBox="0 0 {MAP_W} {MAP_H}" aria-label="Weltkarte: installierte DAC-Kapazität je Land, Jahr für Jahr; Kreisfläche nach Gt CO2 pro Jahr"></svg></div>
      <div class="side">
        <div class="yr">2026</div>
        <div class="ctr"><div class="n n-cap">0 <small>Gt CO₂/a</small></div><div class="l">installierte Kapazität weltweit<br>(Kreise: je Land)</div></div>
        <div class="ctr"><div class="n n-cum">0 <small>von {goal} Gt</small></div><div class="l">netto entnommen</div></div>
        <span class="playtrig" data-step="1" style="display:none"></span>
        <p class="takeaway" data-step="2" style="--d:0">1,5 °C erst 2100, davor ein langer Overshoot.</p>
      </div>
      <div class="strips">{strips_svg(res, gap)}</div>
    </div>
  </div>
  <p class="src">Lineares Programm (Folie 30), Strompfad heutige Zusagen (REMIND-EU SSP2-NDC). Speicher: Gidden et al. 2025; Wachstum: Zurbriggen et al. 2026; Kühlung: FaIR-Klimaantwort. Bäume: kühlende Flächen, gepflanzt 2026 (Folie 25).</p>
  <aside class="notes" data-n="0">
    <p>Das Ergebnis als Film. Links die Welt, rechts die Zähler. Unten zwei Zeitreihen: oben, wie viel CO₂ DAC bis dahin netto entnommen hat, mit dem Nötigen für 2100 als Punkt und gestrichelt dem, was die Wachstumsgrenze höchstens erlaubt; darunter die Erwärmung über 1,5 °C: gestrichelt Very Low, grün mit den Bäumen, rot mit Bäumen und DAC.</p>
    <p>Klick: Jetzt läuft die Zeit. Lange passiert wenig: Frankreich baut früh, weil der Strom sauber ist. In den 2040ern kommen Algerien, Libyen und Ägypten: viel Speicher, Strom wird sauber. 2050 laufen weltweit erst {_de(tot[i50], 2)} Gigatonnen im Jahr, insgesamt sind {_de(cum[i50], 0)} Gigatonnen entnommen. Die Wachstumsgrenze bremst: Die Entnahme läuft lange genau an der gestrichelten Linie entlang, schneller geht es nicht. 2060 sind es {_de(tot[i60], 1)}, dann kommen die USA und Australien mit ihrem großen Speicher; ab {cap_year} laufen {cap} Gigatonnen im Jahr: {top_txt}.</p>
    <p>Und unten sieht man den Overshoot: Um 2050 liegt die Welt auch mit Bäumen und DAC noch rund 0,3 Grad über 1,5 °C, denn DAC ist noch klein, und die Wirkung kommt später als die Entnahme: Ozean und Land geben einen Teil zurück, die Erde reagiert träge. Erst zum Ende des Jahrhunderts drückt DAC die Kurve herunter, 2100 auf 1,5 °C.</p>
    <p>Klick: Erst Nordafrika, dann USA und Australien, {cap} Gigatonnen im Jahr; und die Kühlung kommt spät.</p>
    <p class="q">Falls Fragen kommen — Warum nicht Nordeuropa? Sauberer Strom, aber kaum sicherer Speicher (Norwegen 6,9 Gt, Deutschland 1,3 Gt). Warum nicht Russland? Viel Speicher, aber kälter und schmutzigerer Strom. Die Reihenfolge je Land ist nicht ganz eindeutig: Bei gleicher Kapazität wären auch etwas andere Aufteilungen optimal; eindeutig sind die Menge und die großen Standorte. Der Netto-Anteil der genutzten Anlagen liegt bei 96–97 %.</p>
  </aside>
</section>

'''


def _bars(rows, colors, step, W=760, H=300, bw=130):
    B, T = 46, 40
    n = len(rows)
    gapw = (W - n * bw) / (n + 1)
    top = max(v for _, v in rows)
    s = [f'<svg viewBox="0 0 {W} {H}" font-family="IBM Plex Sans">', f'<line x1="0" x2="{W}" y1="{H - B}" y2="{H - B}" stroke="#8a918c"/>']
    for j, ((lab, v), colr) in enumerate(zip(rows, colors)):
        hgt = (H - B - T) * v / top
        x0 = gapw + j * (bw + gapw)
        yy = H - B - hgt
        rr = min(12, hgt / 2)
        s.append(f'<path class="grow" data-step="{step}" style="--d:{160 * j}" d="M{x0:.1f} {H - B} V{yy + rr:.1f} a{rr} {rr} 0 0 1 {rr} {-rr} '
                 f'H{x0 + bw - rr:.1f} a{rr} {rr} 0 0 1 {rr} {rr} V{H - B} Z" fill="{colr}"/>')
        s.append(f'<text class="rise" data-step="{step}" style="--d:{160 * j + 300}" x="{x0 + bw / 2:.1f}" y="{yy - 10:.1f}" text-anchor="middle" '
                 f'font-size="26" font-weight="600" fill="#1b2420">{_de(v, 1)}</text>')
        s.append(f'<text x="{x0 + bw / 2:.1f}" y="{H - 14}" text-anchor="middle" font-size="20" fill="#5d665f">{lab}</text>')
    s.append("</svg>")
    return "".join(s)


def slide32(res: dict) -> str:
    h = res["haupt"]
    zk = res["ziel_kurve"]
    goal = _de(h["co2_ziel_gt"])
    bars = _bars([(f'bis {r["ziel_jahr"]}', r["kapazitaet_gt"]) for r in zk[::-1]],
                 ["#d9b97a"] * (len(zk) - 1) + [AMBER][::-1] if False else [AMBER] + ["#d9b97a"] * (len(zk) - 1), 0)
    pw = {p["strompfad"]: p["kapazitaet_gt"] for p in res["strompfade"]}
    lo, hi = min(pw.values()), max(pw.values())
    z = {r["ziel_jahr"]: _de(r["kapazitaet_gt"], 1) for r in zk}
    return f'''<section class="slide" data-ch="dac" data-title="Strommix und Zieljahr">
  <header class="sh"><h2>Nötige DAC-Kapazität je Zieljahr</h2></header>
  <div class="body">
    <div class="mix2">
      <div><h5>Kapazität, um {goal} Gt CO₂ bis zum Zieljahr zu entnehmen <small>(Gt CO₂/a)</small></h5>{bars}</div>
      <div style="display:flex; flex-direction:column; gap:30px; padding-top:40px">
        <div class="box rise" data-step="1"><h5>Früher fertig → viel mehr Anlagen</h5><p>Bis 2100: {z[2100]} Gt/a. Bis 2085: {z[2085]} Gt/a, fast das Doppelte, weil DAC nicht schneller als 20&nbsp;%/a wachsen kann.</p></div>
        <div class="box rise" data-step="2"><h5>Strommix: kaum Einfluss</h5><p>Drei Strompfade, von heutiger Politik bis zum 1,5-°C-Pfad: {_de(lo, 1)} bis {_de(hi, 1)} Gt/a. DAC wird erst groß, wenn der Strom ohnehin sauber ist.</p></div>
      </div>
    </div>
    <div class="foot"><div></div><p class="takeaway" data-step="3" style="--d:0">Wie viel DAC nötig ist, entscheidet das Zieljahr, nicht der Strommix.</p></div>
  </div>
  <p class="src">Lineares Programm wie Folie 30, Vorgabe {goal} Gt netto bis zum Zieljahr. Strompfade: REMIND-EU SSP2 über premise: heutige Politik (NPi), heutige Zusagen (NDC), Budget 650 Gt (PkBudg650).</p>
  <aside class="notes" data-n="0">
    <p>Zwei Fragen an das Ergebnis. Links: Was, wenn wir die {goal} Gigatonnen früher entnehmen wollen? Bis 2100 reichen {z[2100]} Gigatonnen im Jahr, bis 2095 braucht es {z[2095]}, bis 2090 {z[2090]}, bis 2085 schon {z[2085]}.</p>
    <p>Klick: Früher fertig heißt viel mehr Anlagen, weil DAC nur begrenzt schnell wachsen kann: Wer früher fertig sein will, muss mit einer größeren Flotte arbeiten, die dann auch schneller wieder überflüssig wäre.</p>
    <p>Klick: Und der Strommix? Mit drei Strompfaden, von der heutigen Politik bis zu einem 1,5-°C-kompatiblen Pfad, ändert sich die nötige Kapazität kaum: {_de(lo, 2)} bis {_de(hi, 2)} Gigatonnen im Jahr. Denn DAC wird wegen der Wachstumsgrenze erst groß, wenn der Strom ohnehin sauber ist. Der Strommix entscheidet, wo DAC früh sinnvoll ist, nicht wie viel gebraucht wird.</p>
    <p>Klick: Wie viel DAC nötig ist, entscheidet das Zieljahr.</p>
    <p class="q">Falls Fragen kommen — Mit nur 11 % Wachstum im Jahr (wie Ammoniak) sind bis 2100 nur {_de(res["sens"]["wachstum_11"]["netto_gt"])} der {goal} Gt erreichbar. Mit dem technischen Speicherpotenzial oder mit dem Landesmedian statt der besten Standorte bleibt es bei {_de(res["sens"]["technisch"]["kapazitaet_gt"], 1)} bzw. {_de(res["sens"]["median"]["kapazitaet_gt"], 1)} Gt/a.</p>
  </aside>
</section>

'''
