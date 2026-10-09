"""Chapters 3 and 4 along time (data: docs/slides/chart_data/zeitpfade.json, scripts/build_zeitpfade_data.py).

- Area slide: the overlay chart shows the trees planted at the Bonn Challenge pace -- every reforestable cell,
  the cooling cells, the cooling cells as managed forest (timber bound; released dashed) -- and then, with the
  axis growing, how far Very Low lies above 1.5 deg C year by year.
- Optimisation slide: the same chart (dark) on the left, the question and the constraints on the right, the
  target now on temperature, not on a CO2 amount.
- New slide after the film: what waiting costs -- the year from which the world stays at 1.5 deg C against the
  DAC cap, for trees and DAC from today and each ten years later.
- The conclusion takes the new numbers.
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _de(v, nd=0):
    return f"{v:,.{nd}f}".replace(",", " ").replace(".", ",")


def _sec(page, title):
    m = re.search(r'<section class="slide[^"]*"(?: data-ch="[^"]*")? data-title="' + re.escape(title) + r'">.*?</section>\n', page, flags=re.S)
    assert m, title
    return m


def _rep(s, old, new):
    assert s.count(old) == 1, old[:90]
    return s.replace(old, new)


JS = r"""
/* chapter 3: trees planted at the Bonn pace, three ways; then the warming of Very Low above 1.5 deg C */
const EC_ZEIT = {
  steps: 2,
  option(k) {
    const D = window.ZEIT, P = ys => D.jahre.map((y, i) => [y, ys[i]]), n = D.jahre.length - 1;
    const end = (text, color) => ({ show: true, formatter: text, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 10 });
    const line = (id, ys, color, text, extra) => Object.assign({ id, type: 'line', showSymbol: false, data: P(ys), z: 5,
      lineStyle: { color, width: 3.4 }, itemStyle: { color }, endLabel: end(text, color), labelLayout: { moveOverlap: 'shiftY' },
      animationDuration: 1800 }, extra || {});
    const p = D.pfade, f = v => ecNum(v, 0);
    const series = [
      line('al', p.alle, '#c8602a', `alle Flächen: ${f(p.alle[n])} mK`),
      line('k', p.kuehlt, '#2f7a45', `kühlende Flächen: ${f(p.kuehlt[n])} mK`, { animationDelay: 200 })];
    if (k >= 1) {
      series.push(line('fo', p.forst, '#14532d', `+ Forst, Holz gebunden: ${f(p.forst[n])} mK`, { lineStyle: { color: '#14532d', width: 3.8 }, animationDelay: 300 }));
      series.push(line('ff', p.forst_frei, '#14532d', `Holz freigesetzt: ${f(p.forst_frei[n])} mK`,
                       { lineStyle: { color: '#14532d', width: 2.4, type: [8, 6] }, animationDelay: 600 }));
    }
    if (k >= 2) {
      for (const s of series) s.endLabel = Object.assign({}, s.endLabel, { show: s.id === 'fo', formatter: `Bäume: ${f(p.forst_frei[n])}–${f(p.forst[n])} mK` });
      const ip = D.noetig.indexOf(Math.max(...D.noetig));
      series.push({ id: 'need', type: 'line', showSymbol: false, data: P(D.noetig), z: 3, lineStyle: { color: '#8e0d16', width: 3 },
        areaStyle: { color: 'rgba(196,18,31,.16)' }, itemStyle: { color: '#8e0d16' }, animationDuration: 1800, animationDelay: 500,
        endLabel: end('Very Low über 1,5 °C', '#8e0d16'),
        markPoint: { silent: true, symbol: 'circle', symbolSize: 12, itemStyle: { color: '#8e0d16', borderColor: '#fff', borderWidth: 2 },
          label: { show: true, position: 'top', distance: 10, color: '#8e0d16', fontFamily: EC.font, fontSize: 19, fontWeight: 600,
                   formatter: `um ${D.jahre[ip]}: ${ecNum(D.noetig[ip] / 1000, 2)} K zu warm` },
          data: [{ coord: [D.jahre[ip], D.noetig[ip]] }] } });
    }
    return {
      animationDurationUpdate: 1100, animationEasingUpdate: 'cubicInOut',
      title: { text: 'Kühlung Jahr für Jahr, gepflanzt im Bonn-Tempo (17,5 Mha/a)', left: 74, top: 0,
               textStyle: { color: EC.ink, fontFamily: EC.font, fontSize: 21, fontWeight: 600 } },
      grid: { left: 74, right: 330, top: 50, bottom: 46 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisTick: { show: true, customValues: [2026, 2050, 2075, 2100] },
                      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: k >= 2 ? 350 : 30, interval: k >= 2 ? 50 : 5, name: k >= 2 ? 'Kühlung bzw. Erwärmung [mK]' : 'Kühlung der Erde [mK]', nameLocation: 'middle', nameGap: 52,
                      axisLabel: { color: EC.muted, fontFamily: EC.font, fontSize: 19 }, splitLine: { show: true, lineStyle: { color: EC.grid } } }),
      series
    };
  }
};

/* how fast DAC must grow: warming above 1.5 deg C after trees and DAC, for growth limits and without limit */
const EC_TEMPO = {
  steps: 3,
  option(k) {
    const D = window.ZEIT, T = D.tempo, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const L = (id, ys, color, name, extra) => Object.assign({ id, name, type: 'line', showSymbol: false, data: P(ys), z: 5,
      lineStyle: { color, width: 3.2 }, itemStyle: { color }, animationDuration: 1600 }, extra || {});
    const kap = c => `${ecNum(c.kap, 1)} Gt/a`;
    const series = [
      L('base', D.baeume_rest, '#e0645a', 'nur Bäume', { lineStyle: { color: '#e0645a', width: 2.4, type: [8, 6] } }),
      L('g20', T.g20.rest, '#f0b04a', `+20 %/a: ${kap(T.g20)}`)];
    if (k >= 1) {
      series.push(L('g30', T.g30.rest, '#ffd27a', `+30 %/a: ${kap(T.g30)}`, { lineStyle: { color: '#ffd27a', width: 2.6 } }));
      series.push(L('g10', T.g10.rest, '#c8602a', '+10 %/a: reicht nicht', { lineStyle: { color: '#c8602a', width: 2.6 } }));
    }
    if (k >= 2) series.push(L('frei', T.frei.rest, '#3fd0b0', `ohne Grenze: ${kap(T.frei)} ab 2026`, { lineStyle: { color: '#3fd0b0', width: 3.4 } }));
    if (k >= 3) series.push(L('voll', T.vollgas.rest, '#ff6a3d', `Vollgas +20 %/a: ${kap(T.vollgas)}`, { lineStyle: { color: '#ff6a3d', width: 2.8, type: [8, 5] } }));
    return {
      animationDurationUpdate: 900,
      title: { text: 'Erwärmung über 1,5 °C nach Bäumen und DAC [mK]', left: 70, top: 0, textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
      grid: { left: 70, right: 300, top: 46, bottom: 40 },
      legend: { orient: 'vertical', right: 0, top: 90, itemGap: 14, itemWidth: 28, icon: 'path://M0,4 H28 V7 H0 Z',
                textStyle: { color: '#d6dbd6', fontFamily: EC.font, fontSize: 18 }, data: series.map(s => s.name) },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: 0, max: 350, interval: 100, axisLine: { lineStyle: { color: '#4a524d' } },
                      axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 19 }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
      series
    };
  }
};
"""

CSS = """
.warten { display: grid; grid-template-columns: 1fr 500px; gap: 36px; flex: 1; min-height: 0; }
.warten > .chart { height: 100%; min-height: 0; }
.warten .side { display: flex; flex-direction: column; gap: 18px; align-self: center; }
.warten .side p { font: 400 21px/1.4 var(--sans); color: var(--ink-2); margin: 0; }
.warten .side p b { color: #f0b04a; font-weight: 600; }
.warten .side .ort { border-left: 4px solid #3fd0b0; padding: 6px 0 6px 16px; }
.warten .side .ort b { color: #6fe3c8; }
/* chapter 3: the managed forest in two lines, beside its curve */
.forstpos { position: absolute; left: 112px; top: 74px; width: 330px; pointer-events: none; }
.forstbox { position: relative; display: grid; grid-template-columns: 92px 1fr; gap: 14px;
            align-items: center; padding: 12px 16px; border-radius: 10px; background: rgba(255,255,255,.75); border: 1.5px solid #c9d8bf;
            transition: opacity .5s; }
.forstbox p { font: 400 17px/1.35 var(--sans); color: var(--ink-2); margin: 0; }
.forstbox p b { color: #14532d; }
.slide:has(.zs4.shown) .forstpos { opacity: 0; transition: opacity .5s; }
/* search space of the optimisation */
.such { display: grid; grid-template-columns: 860px 1fr; grid-template-rows: auto 1fr; gap: 18px 36px; flex: 1; min-height: 0; }
.such .map { position: relative; width: 860px; height: 339px; border-radius: 10px; overflow: hidden; }
.such .map img { position: absolute; inset: 0; width: 100%; height: 100%; image-rendering: pixelated; }
.such .leg { display: flex; align-items: center; gap: 10px; font: 400 17px/1 var(--sans); color: #9aa39d; margin-top: 8px; }
.such .leg i { display: inline-block; width: 180px; height: 12px; border-radius: 3px; background: linear-gradient(90deg, #c8602a, #e9dcae 50%, #1f7a74); }
.such .size { display: grid; grid-template-columns: repeat(3, auto); gap: 4px 26px; justify-content: start; margin-top: 18px; }
.such .size b { font: 600 40px/1 var(--sans); color: #f2ede2; }
.such .size span { font: 400 17px/1.2 var(--sans); color: #9aa39d; }
.such .inputs { grid-column: 1 / -1; grid-template-columns: repeat(4, 1fr); }
.such .inp .v { font-size: 36px; }
"""


def _forstbox() -> str:
    """Two lines and a saw-tooth: what 'managed forest' means here."""
    pts = " ".join(f"{x},{y}" for x, y in ((0, 52), (24, 14), (24, 52), (48, 14), (48, 52), (72, 14), (72, 52)))
    svg = (f'<svg viewBox="-4 0 84 60" width="92" height="64" aria-hidden="true"><polyline points="{pts}" fill="none" stroke="#14532d" stroke-width="3" stroke-linejoin="round"/>'
           '<path d="M0 58 H76" stroke="#8a7f6c" stroke-width="1.5"/>'
           '<rect x="4" y="40" width="12" height="18" fill="#b98a3e"/><rect x="28" y="34" width="12" height="24" fill="#b98a3e"/><rect x="52" y="28" width="12" height="30" fill="#b98a3e"/></svg>')
    return (f'<div class="forstpos"><div class="forstbox rise" data-step="3" style="--d:300">{svg}<p><b>Forst:</b> Kahlschlag alle 20–80 Jahre, neu pflanzen; 70 % bleiben als Bauholz gebunden.</p></div></div><span class="zs4" data-step="4" style="display:none"></span>')


def patch(page: str) -> str:
    from dacopt_assets import assets

    d = json.loads((REPO / "docs/slides/chart_data/zeitpfade.json").read_text())
    n = len(d["jahre"]) - 1
    pf = d["pfade"]
    i50 = d["jahre"].index(2050)
    peak = max(d["noetig"])
    yr_peak = d["jahre"][d["noetig"].index(peak)]
    T, ort = d["tempo"], d["ort"]
    kap = lambda k: _de(T[k]["kap"], 1)
    spar = 100 * (1 - ort["optimiert"] / ort["nach_speicher"])

    head, sep, tail = page.partition("</style>")
    page = head + CSS + sep + tail
    m = re.search(r"const EC_CHARTS = \{([^}]*)\};", page)
    page = (page[: m.start()] + "window.ZEIT = " + json.dumps(d, separators=(",", ":")) + ";\n"
            + JS + "const EC_CHARTS = {" + m.group(1).rstrip() + ", zeit: EC_ZEIT, tempo: EC_TEMPO };" + page[m.end():])

    # ---- area slide: the new chart in the overlay, the forest box on its click, then the takeaway
    m = _sec(page, "Wiederbewaldbare Fläche")
    s = m.group(0)
    s = _rep(s, '<div class="chart" data-ec="luecke" data-step="2" data-label="Kühlung der Erde 2026 bis 2100 durch alle Bäume; dann die Kühlung, die nötig wäre, um im Szenario Very Low unter 1,5 °C zu bleiben"></div>',
             '<div class="chart" data-ec="zeit" data-step="2" data-label="Kühlung der Erde 2026 bis 2100, Bäume im Bonn-Tempo gepflanzt: alle Flächen, kühlende Flächen, kühlende Flächen als Forst; dann die Erwärmung von Very Low über 1,5 °C"></div>'
             + _forstbox())
    s = _rep(s, '<p class="takeaway" data-step="4" style="--d:0">Für 1,5 °C in 2100 bräuchte es das 5,5-Fache der Bäume: zusätzlich rund 262 Gt CO₂ Entnahme.</p>',
             f'<p class="takeaway" data-step="5" style="--d:0">Auch als Forst bringen die Bäume bis 2100 nur {_de(pf["forst"][n])} mK; um {yr_peak} ist es {_de(peak / 1000, 1)} K zu warm.</p>')
    notes = (f"      <p>Klick: Was bringt das über die Zeit — wenn wir realistisch pflanzen, im Tempo der Bonn Challenge, 17,5 Millionen Hektar im Jahr? Orange alle Flächen, grün nur die kühlenden: 2050 erst {_de(pf['kuehlt'][i50], 1)} Millikelvin, 2100 rund {_de(pf['kuehlt'][n])}. Wer überall pflanzt, verliert im Norden an die Albedo.</p>\n"
             f"    <p>Klick: Und wenn wir den Wald nutzen, als Forst? Kahlschlag alle 20 Jahre in den Tropen bis 80 im Norden, dann neu pflanzen; 70 Prozent gehen als Bauholz raus und bleiben gebunden, der Rest zerfällt. Dann sind es 2100 {_de(pf['forst'][n])} Millikelvin, mehr als ohne Nutzung — der junge Wald nimmt wieder schnell auf. Geht das Holz zurück in die Luft, gestrichelt, nur {_de(pf['forst_frei'][n])}.</p>\n"
             f"    <p>Klick: Und reicht das? Die Achse wächst mit. Rot: so weit liegt Very Low über 1,5 °C, Jahr für Jahr — um {yr_peak} rund {_de(peak / 1000, 2)} Grad. Die Bäume sind dagegen ein Strich am Boden.</p>\n"
             f"    <p>Klick: Auch als Forst bringen die Bäume bis 2100 nur {_de(pf['forst'][n])} Millikelvin; die Lücke um {yr_peak} ist mehr als zehnmal so groß.</p>\n"
             "    <p class=\"q\">Falls Fragen kommen — Forst: Umtrieb nach Klimazone 80/60/30/20 Jahre (boreal/gemäßigt/subtropisch/tropisch; Spannen aus der Literatur 50–150 Jahre Naturwald, 7–25 Jahre tropische Plantagen), Stammholz 70 % des Bestandskohlenstoffs (60–80 % je nach Holzart), Reste beim Fällen als Emission. Bauholz hält real Jahrzehnte (IPCC-Halbwertszeit Schnittholz 35 Jahre), dauerhaft gebunden ist also die optimistische Grenze. Boreale und gemäßigte Bestände werden bis 2100 kaum geerntet; der Gewinn kommt aus den Tropen und Subtropen.</p>\n")
    a = s.index("      <p>Klick: Was bringt das über die Zeit?")
    b = s.index("    <p>Die Lücke ist groß.")
    s = s[:a] + notes + s[b:]
    page = page[: m.start()] + s + page[m.end():]

    # ---- optimisation slide: the search space
    m = _sec(page, "Optimierung von DAC")
    s = m.group(0)
    items = re.findall(r'<div class="inp rise".*?</span></div>', s, flags=re.S)
    assert len(items) == 4
    cards = '<div class="inputs">' + "".join(items) + '</div>'
    body = (f'<div class="body">\n    <div class="such">'
            f'<div><div class="map"><img src="{assets()["eta_png"]}" alt="Weltkarte: Netto-Anteil von DAC je Zelle 2030"></div>'
            '<div class="leg">Netto-Anteil η 2030 <span>0</span><i></i><span>100 %</span> · grau: zu kalt</div></div>'
            '<div><p class="bridge rise" data-step="1">Gesucht: <b>wo und wann</b> DAC gebaut wird, damit die höchste Erwärmung über 1,5 °C so niedrig wie möglich bleibt — und es 2100 bei 1,5 °C ist, mit so wenig Anlagen wie möglich.</p>'
            '<div class="size rise" data-step="1" style="--d:300"><b>148</b><b>75</b><b>45 183</b><span>Länder mit Speicher</span><span>Jahre</span><span>Zellen mit η je Jahr</span></div></div>'
            + cards + '</div>\n  </div>\n  <p class="src">')
    b = re.search(r'<div class="body">.*?\n  </div>\n  <p class="src">', s, flags=re.S)
    s = s[: b.start()] + body + s[b.end():]
    s = _rep(s, "<h2>Die Lücke schließen: wo und wann DAC?</h2>", "<h2>Wo und wann DAC? Der Suchraum</h2>")
    s = re.sub(r'<p class="src">.*?</p>',
               '<p class="src">Lineares Programm, eigene Rechnung, in zwei Stufen: niedrigste Spitze der Erwärmung über 1,5 °C nach den Bäumen (Forst im Bonn-Tempo) und DAC; bei dieser Spitze 1,5 °C ab 2100 mit kleinster Gesamtmenge. '
               'Variablen: Kapazität je Land und Jahr. Netto-Anteil je Land: beste 10 % der Zellen mit Sedimentbecken in höchstens 100 km. Klimaantwort: FaIR, wie bei den Bäumen.</p>', s, count=1, flags=re.S)
    a = s.index(">", s.index('<aside class="notes" data-n="')) + 1
    b = s.index("</aside>")
    s = s[:a] + (
        "\n    <p>Was die Optimierung durchsucht. Links der Netto-Anteil je Zelle für 2030: grün, wo DAC sauber entnimmt, orange, wo der Strom noch so schmutzig ist, dass wenig übrig bleibt. Das ändert sich jedes Jahr mit dem Strommix.</p>\n"
        "    <p>Klick: Gesucht ist, wo und wann DAC gebaut wird, damit die höchste Erwärmung über 1,5 °C so niedrig wie möglich bleibt; und dann, bei dieser Spitze, 1,5 °C bis 2100 mit so wenig Anlagen wie möglich. Der Suchraum: 148 Länder mit Speicher, 75 Jahre, dahinter rund 45 000 Zellen mit eigenem Netto-Anteil je Jahr.</p>\n"
        "    <p>Klick: Die Rahmenbedingungen. Der Netto-Anteil aus dem Modell; wie viel CO₂ jedes Land sicher speichern kann, nach Gidden et al. weltweit 1 460 Gigatonnen, Deutschland nur 1,3; der Hochlauf, höchstens 20 Prozent im Jahr wie einst die Windkraft, ab den 8,8 Megatonnen, die für 2030 geplant sind; und gebaute Anlagen laufen weiter.</p>\n"
        "    <p class=\"q\">Falls Fragen kommen — Ein lineares Programm: Kapazität je Land und Jahr als Variablen, die Klimaantwort aus FaIR linear je Tonne. Kein Transport über Landesgrenzen; Basalt-Mineralisierung (Island) ist bei Gidden nicht enthalten.</p>\n  ") + s[b:]
    page = page[: m.start()] + s + page[m.end():]

    # ---- after the film: how fast DAC must grow, and why the place hardly matters
    html = f"""<section class="slide dark" data-ch="dac" data-title="Wie schnell DAC wachsen muss">
  <header class="sh"><h2>Wie schnell muss DAC wachsen?</h2></header>
  <div class="body">
    <div class="warten">
      <div class="chart" data-ec="tempo" data-label="Erwärmung über 1,5 °C 2026 bis 2100 nach Bäumen und DAC, für Hochlaufgrenzen von 10, 20 und 30 Prozent im Jahr und ohne Grenze"></div>
      <div class="side">
        <p class="rise">Optimiert auf die niedrigste Spitze: mit +20 %/a senkt DAC sie nur von {_de(T['ohne']['spitze'])} auf <b>{_de(T['g20']['spitze'])} mK</b>. Danach {kap('g20')} Gt/a für 1,5 °C bis 2100.</p>
        <p class="rise" data-step="1">+30 %/a: Spitze {_de(T['g30']['spitze'])} mK, {kap('g30')} Gt/a. +10 %/a: 1,5 °C bis 2100 nicht erreichbar.</p>
        <p class="rise" data-step="2">Ohne Hochlaufgrenze: <b>{kap('frei')} Gt/a ab 2026</b> drücken die Spitze auf <b>{_de(T['frei']['spitze'])} mK</b>. Das Tempo begrenzt DAC.</p>
        <p class="rise" data-step="3">„So schnell wie möglich“ runter: <b>1,5 °C ab {T['vollgas']['ab']}</b>, aber {kap('vollgas')} Gt/a, fast alle Speicher voll, 2100 weit unter 1,5 °C.</p>
        <p class="rise ort" data-step="4">Wo genau, ist fast egal: optimiert {_de(ort['optimiert'], 1)}, nach Speicher verteilt {_de(ort['nach_speicher'], 1)} Gt/a. Ist DAC groß, ist der Strom fast überall erneuerbar. <b>Perfekt muss es nicht sein — Hauptsache, wir fangen an.</b></p>
        <p class="takeaway" data-step="5" style="--d:0">Früh anfangen, damit DAC reift und wachsen kann. Den Gipfel um 2050 senkt es kaum.</p>
      </div>
    </div>
  </div>
  <p class="src">Lineares Programm wie vorige Folien, Bäume als Forst im Bonn-Tempo (Holz gebunden). Ziel: niedrigste Spitze der Erwärmung über 1,5 °C, dann bei dieser Spitze 1,5 °C ab 2100 mit möglichst wenig DAC („Vollgas“: dann so schnell wie möglich auf 1,5 °C); Speicher nach Gidden et al. 2025. Nach Speicher verteilt: Weltkapazität im Verhältnis der Speicher, jedes Jahr gleich.</p>
  <aside class="notes" data-n="0">
    <p>Optimiert ist jetzt auf das, was zählt: die höchste Erwärmung über 1,5 °C so niedrig wie möglich. Gestrichelt nur die Bäume, Spitze {_de(T['ohne']['spitze'])} Millikelvin um 2048. Gelb mit DAC bei 20 Prozent Hochlauf: Die Spitze sinkt nur auf {_de(T['g20']['spitze'])} — bis 2048 ist DAC schlicht noch zu klein. Danach bringt es die Welt mit {kap('g20')} Gigatonnen im Jahr bis 2100 auf 1,5 °C.</p>
    <p>Klick: Mit 30 Prozent Hochlauf sinkt die Spitze auf {_de(T['g30']['spitze'])}, und es reichen {kap('g30')} Gigatonnen im Jahr. Mit 10 Prozent, wie viele Technologien in der Praxis, ist 1,5 °C bis 2100 gar nicht erreichbar.</p>
    <p>Klick: Und ohne jede Grenze, wenn wir ab heute bauen könnten, so viel wir wollen? Dann drücken {kap('frei')} Gigatonnen im Jahr ab 2026 die Spitze auf {_de(T['frei']['spitze'])} Millikelvin — ein Drittel weniger. Das Tempo des Hochlaufs begrenzt DAC, nicht seine Endgröße.</p>
    <p>Klick: Und wenn wir nach der Spitze so schnell wie möglich wieder auf 1,5 °C wollen? Dann heißt es Vollgas an der Hochlaufgrenze: 1,5 °C ab {T['vollgas']['ab']}, aber {kap('vollgas')} Gigatonnen im Jahr, fast alle sicheren Speicher voll — und weil gebaute Anlagen weiterlaufen, 2100 weit unter 1,5 °C. Deshalb rechnen wir den Hauptpfad mit einem Zieljahr: 1,5 °C bis 2100 mit möglichst wenig Anlagen.</p>
    <p>Klick: Und das Wo? Fast egal. Die Optimierung braucht {_de(ort['optimiert'], 1)} Gigatonnen im Jahr, eine einfache Verteilung nach Speicher {_de(ort['nach_speicher'], 1)}, rund {_de(spar)} Prozent mehr. Wenn DAC groß ist, ist der Strom fast überall erneuerbar; in den frühen Jahren ist DAC so klein, dass der Ort global kaum zählt. Die Optimierung zeigt also: Perfekt muss es nicht sein, Hauptsache wir fangen an — denn nur wer heute baut, bringt die Technik zur Reife.</p>
    <p>Klick: Früh anfangen, damit DAC reift und wachsen kann. Den Gipfel um 2050 senkt es kaum — den muss die Emissionsminderung leisten.</p>
  </aside>
</section>
"""
    m = _sec(page, "DAC-Ausbau")
    page = page[: m.end()] + html + page[m.end():]

    # ---- conclusion: the new numbers
    m = _sec(page, "Auf dem Holzweg? Nein.")
    s = m.group(0)
    s = re.sub(r'<h4><span class="big-n">2</span>.*?</p>',
               f'<h4><span class="big-n">2</span>Bäume allein reichen nicht</h4><p>im Bonn-Tempo, als Forst: {_de(pf["forst"][n])} mK bis 2100<br>→ um {yr_peak} fehlen über 0,3 K</p>', s, count=1, flags=re.S)
    s = re.sub(r'<h4><span class="big-n">3</span>.*?</p>',
               f'<h4><span class="big-n">3</span>DAC schließt die Lücke, aber spät</h4><p>{kap("g20")} Gt/a für 1,5 °C bis 2100, wo, ist fast egal<br>→ früh anfangen; den Overshoot um {yr_peak} verhindert es nicht</p>', s, count=1, flags=re.S)
    s = re.sub(r'<p>Klick: Zweitens:.*?</p>',
               f'<p>Klick: Zweitens: Bäume allein reichen nicht. Realistisch gepflanzt und als Forst genutzt bringen sie bis 2100 rund {_de(pf["forst"][n])} Millikelvin; um {yr_peak} liegt Very Low über 0,3 Grad über 1,5 °C.</p>', s, count=1, flags=re.S)
    s = re.sub(r'<p>Klick: Drittens:.*?</p>',
               f'<p>Klick: Drittens: DAC kann die Lücke schließen, aber spät: {kap("g20")} Gigatonnen im Jahr für 1,5 °C bis 2100. Wo genau, ist fast egal; entscheidend ist, früh anzufangen, damit es wachsen kann. Den Overshoot um {yr_peak} verhindert es nicht. Bis dahin zählen Emissionsminderung und die Bäume, die jetzt gepflanzt werden.</p>', s, count=1, flags=re.S)
    page = page[: m.start()] + s + page[m.end():]

    k = iter(range(1, 1000))
    page = re.sub(r'<aside class="notes" data-n="\d+">', lambda _: f'<aside class="notes" data-n="{next(k)}">', page)
    return page
