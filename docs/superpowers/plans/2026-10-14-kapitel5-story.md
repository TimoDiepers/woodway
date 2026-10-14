# Kapitel 5 auf einer Temperaturkurve – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kapitel 5 erzählt mit einem Anker in °C (Very Low, 1,5-°C-Linie, eine Kurve je Maßnahme) die Botschaft „Für die Spitze zählt, was vor 2050 wirkt“; Kapitel 4 endet mit demselben Anker.

**Architecture:** Das Build-Skript schreibt die ungeschnittene Very-Low-Temperatur und die Wirkung jeder Maßnahme als eigene Reihe; eine neue Anker-Funktion in `deck.js` zeichnet daraus Kurven in °C, mit Phasen je Folie und ohne Neu-Einlauf übernommener Linien; die Folien 27–31 und der letzte Schritt der Zeitgrafik in Kapitel 4 werden umgebaut.

**Tech Stack:** Python (uv, numpy, FaIR, Gurobi über `nbs.dac_optim._lp`), HTML/CSS/JS-Deck mit ECharts 6 (`deck/build.py`), Chrome headless + CDP-Skripte zur Prüfung.

**Spec:** `docs/superpowers/specs/2026-10-14-kapitel5-story-design.md`

## Global Constraints

- Botschaft wörtlich: „Für die Spitze zählt, was vor 2050 wirkt.“
- Kurven im Anker: `vl_c + wirkung.baeume + wirkung.<maßnahme>` in °C, nie bei 1,5 °C oder 0 abgeschnitten.
- DAC-Pfade: `solve_min_peak(gap, danach="frueh")` mit Wachstum 1,2 / 1,5 / 2,0 / unbegrenzt (`growth=1e6, limit_start=False`).
- Im Vortrag heißt der DAC-Pfad „so schnell wie erlaubt, bis 1,5 °C erreicht ist“; das dreistufige Ziel nur in Backup und Methodendoku.
- Übernommene Linien und Markierungen: `animation: false`; neue: `animation` nicht setzen (folgt dem Deck). Wiederholter Anker ohne `data-step` am Host. Chart-`steps` = genau die genutzten Klicks.
- Deck-Regeln: Schrift ≥ 18 px in Charts, ≥ 20 px Fließtext; Takeaway höchstens zwei Zeilen und endet mit der Überleitungsfrage; keine Claude-Attribution in Commits; nicht pushen ohne Timos OK.
- pytest nur über `uv run --extra dev pytest … -k "not Sobol"`.

## Review Focus

1. Very Low liegt Ende des Jahrhunderts unter 1,5 °C: Dort muss die Kurve unter der Linie weiterlaufen (nicht bei 1,5 °C kleben); Test in Task 1.
2. DAC kühlt nur, solange die Lücke > 0 ist: Die DAC-Kurve darf nach dem Rückkehrjahr nicht über 1,5 °C steigen; Test in Task 2.
3. Wechsel 27 → 28 → 30 mit dazwischenliegender Folie 29 (ohne Anker): Anker auf 30 darf nicht neu einlaufen; Prüfung in Task 8 (CDP).
4. Rückwärts blättern (30 → 28): keine leeren Klicks, Kurven korrekt; Prüfung in Task 8.
5. 100 %/a liegt zwischen 50 %/a und unbegrenzt (Spitze, Rückkehrjahr); Test in Task 2.

---

### Task 1: Very Low ungeschnitten

**Files:**
- Modify: `src/nbs/vergleich_figures.py:307-315`
- Test: `tests/test_vergleich_vl.py`

**Interfaces:**
- Produces: `vl_series() -> dict` mit `{"jahre": list[int], "median_c": list[float]}` (Very Low, Median, 7-Jahres-Mittel, °C, 2026–2100); `overshoot_series()` unverändert in der Ausgabe, berechnet aber aus `vl_series()`.

- [ ] **Step 1: Write the failing test**

```python
"""Very Low as a temperature in deg C, not clipped at 1.5 deg C."""
import numpy as np


def test_vl_series_unclipped_and_consistent_with_overshoot():
    from nbs.vergleich_figures import overshoot_series, vl_series
    v, o = vl_series(), overshoot_series()
    assert v["jahre"] == o["jahre"]
    t = np.array(v["median_c"])
    assert np.allclose(np.maximum(0.0, t - 1.5), o["noetig_k"])
    assert 1.7 < t.max() < 1.95          # the peak of Very Low around 2050
    assert t[-1] < 1.5                   # back below 1.5 deg C by 2100, and kept as such
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --extra dev pytest tests/test_vergleich_vl.py -q`
Expected: FAIL with `ImportError: cannot import name 'vl_series'`

- [ ] **Step 3: Write minimal implementation** (replace `overshoot_series` body)

```python
def vl_series() -> dict:
    """CMIP7 Very Low (median, 7-year mean) in deg C above pre-industrial, 2026-2100, not clipped."""
    from nbs.cmip7_figures import temperature

    t = temperature()
    v = t[(t.szenario == "VL") & (t.jahr >= T_START) & (t.jahr <= 2100)].sort_values("jahr")
    med = v["median"].rolling(7, center=True, min_periods=1).mean()  # the median still carries the ensemble's year-to-year noise
    return {"jahre": [int(y) for y in v.jahr], "median_c": [float(x) for x in med]}


def overshoot_series() -> dict:
    """The limit, read off the scenario data: how far CMIP7 Very Low (median) lies above 1.5 deg C, year by
    year -- the cooling that would be needed on top of Very Low to stay at 1.5 deg C."""
    v = vl_series()
    return {"jahre": v["jahre"], "noetig_k": [max(0.0, x - 1.5) for x in v["median_c"]]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --extra dev pytest tests/test_vergleich_vl.py -q`
Expected: PASS (If `t[-1] < 1.5` fails, report the value to Timo; do not change the assertion.)

- [ ] **Step 5: Commit**

```bash
git add src/nbs/vergleich_figures.py tests/test_vergleich_vl.py
git commit -m "feat(figures): Very Low in deg C, not clipped at 1.5 deg C"
```

---

### Task 2: Wirkung je Maßnahme und 100 %/a in den Deck-Daten

**Files:**
- Modify: `scripts/build_zeitpfade_data.py` (in `main()`: DAC-Läufe einmal rechnen, `opt_100`, `vl_c`, `wirkung` in `out`)
- Test: `tests/test_zeitpfade_data.py`
- Generated: `deck/chart_data/zeitpfade.json`, `deck/chart_data/dacfilm.json`

**Interfaces:**
- Consumes: `vl_series()` (Task 1); `solve_min_peak`, `delta_t`, `vegan.dt_gase`, `vegan.dt_flaeche`.
- Produces in `zeitpfade.json`: `vl_c: list[float]` (°C, 3 Nachkommastellen, Länge = `jahre`); `wirkung: {"baeume","dac_20","dac_50","dac_100","dac_frei","vegan"}` je `list[float]` in mK (< 0 = kühler, 2 Nachkommastellen); `dac.opt_100` wie die anderen `opt_*` (`kap`, `ab`, `spitze`, `w`, `temp`, …).

- [ ] **Step 1: Write the failing test** (reads the built JSON)

```python
"""The deck data for the chapter-5 anchor: Very Low in deg C and the effect of each measure, unclipped."""
import json
from pathlib import Path

import numpy as np

Z = json.loads(Path("deck/chart_data/zeitpfade.json").read_text())


def _c(key):
    return np.array(Z["vl_c"]) + (np.array(Z["wirkung"]["baeume"]) + np.array(Z["wirkung"][key])) / 1000


def test_anchor_series_exist_and_have_the_years():
    n = len(Z["jahre"])
    assert len(Z["vl_c"]) == n
    assert set(Z["wirkung"]) == {"baeume", "dac_20", "dac_50", "dac_100", "dac_frei", "vegan"}
    assert all(len(v) == n for v in Z["wirkung"].values())


def test_dac_stays_at_or_below_1p5_after_its_return_year():
    for key, case in (("dac_20", "opt_20"), ("dac_50", "opt_50"), ("dac_100", "opt_100"), ("dac_frei", "opt_frei")):
        t = _c(key); i = Z["jahre"].index(Z["dac"][case]["ab"])
        assert np.all(t[i:] <= 1.5 + 1e-3), key


def test_faster_growth_is_ordered():
    d = Z["dac"]
    assert d["opt_frei"]["spitze"] <= d["opt_100"]["spitze"] <= d["opt_50"]["spitze"] <= d["opt_20"]["spitze"] + 0.1
    assert d["opt_frei"]["ab"] <= d["opt_100"]["ab"] <= d["opt_50"]["ab"] <= d["opt_20"]["ab"]


def test_vegan_goes_below_1p5_and_is_not_clipped():
    t = _c("vegan")
    assert t.min() < 1.45
    assert abs(t.max() - (1.5 + max(Z["vegan"]["gap"]) / 1000)) < 0.005
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --extra dev pytest tests/test_zeitpfade_data.py -q`
Expected: FAIL with `KeyError: 'vl_c'`

- [ ] **Step 3: Implement in `scripts/build_zeitpfade_data.py`**

Import: `from nbs.vergleich_figures import overshoot_series, vl_series` (extend the existing import). Replace the block that builds `dac = {...}` by solving each path once and keeping the results:

```python
    frueh = dict(danach="frueh")
    runs = {"opt_20": solve_min_peak(gap, **frueh), "opt_30": solve_min_peak(gap, growth=1.3, **frueh),
            "opt_50": solve_min_peak(gap, growth=1.5, **frueh), "opt_100": solve_min_peak(gap, growth=2.0, **frueh),
            "opt_frei": solve_min_peak(gap, growth=1e6, limit_start=False, **frueh)}
    dac = {k: _case(r) for k, r in runs.items()}
    dac.update(opt_2035=_case(solve(gap_k=gap, start_jahr=2035)), opt_2040=_case(solve(gap_k=gap, start_jahr=2040)))
```

After `veg = {...}` is built (it holds `dg`, `df`), add:

```python
    # chapter 5 anchor: Very Low in deg C and what each measure does to it, unclipped (mK, < 0 = cooler)
    wirkung = {"baeume": _mk(delta_t("forst")), "vegan": _mk(dg + df),
               **{f"dac_{k}": _mk(-np.array(runs[f"opt_{k}"]["kuehlung_k"])) for k in ("20", "50", "100", "frei")}}
    vl_c = [round(v, 3) for v in vl_series()["median_c"]]
```

and add `"vl_c": vl_c, "wirkung": wirkung,` to the `out = {...}` dict. Everything else in `main()` that used `dac["opt_20"]`, `dac["opt_frei"]` stays as is.

- [ ] **Step 4: Run the build and the test**

Run (≈ 7 min): `uv run python scripts/build_zeitpfade_data.py > /tmp/zp.log 2>&1 && uv run python scripts/build_dacfilm_data.py > /tmp/df.log 2>&1; tail -2 /tmp/zp.log`
Then: `uv run --extra dev pytest tests/test_zeitpfade_data.py tests/test_vergleich_vl.py -q`
Expected: build writes `zeitpfade.json`; tests PASS. Print and note for the slides: `opt_50`, `opt_100`, `opt_frei` → `spitze`, `ab`, `kap`; max of `vl_c` and its year; min/max of all anchor curves (for the y axis).

- [ ] **Step 5: Commit**

```bash
git add scripts/build_zeitpfade_data.py tests/test_zeitpfade_data.py deck/chart_data/zeitpfade.json deck/chart_data/dacfilm.json
git commit -m "feat(zeitpfade): Very Low in deg C and the effect of each measure; DAC at 100 %/a"
```

---

### Task 3: Anker in °C und Abbau-Grafik in `deck.js`

**Files:**
- Modify: `deck/src/js/deck.js` (replace `ecAnker`, `TEMPO_COL`, `EC_ANKER0..3`, `EC_TEMPOKAP`; add `EC_ABBAU`; register in `EC_CHARTS`)

**Interfaces:**
- Consumes: `window.ZEIT.vl_c`, `ZEIT.wirkung.*`, `ZEIT.dac.opt_*.ab`, `ZEIT.vegan.ohne_dac.ab` (Task 2).
- Produces: chart keys `anker4` (Kap. 4, hell), `anker0` (Folie 27), `anker1` (28), `anker2` (30), `abbau` (29).

- [ ] **Step 1: Replace the anchor code** (everything from the comment `/* chapter 5 anchor:` up to `const EC_VEGAN_ALL` is replaced; `EC_TEMPOKAP` and `TEMPO_COL` go):

```js
/* the anchor of chapters 4 and 5: Very Low in deg C with the 1.5 deg C line, and a curve per measure (Very Low plus
   the trees plus the measure), never clipped. Phases: 'k4' chapter 4 (light, Very Low and trees), 0 the DAC model,
   1 DAC as fast as allowed (click 1 adds 50 and 100 %/a and no limit), 2 the vegan world (click 1; DAC lines step
   back). What stood on the slide before stands again without an entrance; only new lines are drawn in. */
const ANKER_COL = { vl: '#9aa39d', b: '#7fbf8c', d20: '#ff5a4f', d50: '#f5894a', d100: '#f2b04b', frei: '#ff9a8f', v: '#7fd0e0' };
function ecAnker(phase) {
  const light = phase === 'k4';
  return { steps: { k4: 0, 0: 0, 1: 1, 2: 1 }[phase], option(k) {
    const D = window.ZEIT, W = D.wirkung, P = ys => D.jahre.map((y, i) => [y, ys[i]]);
    const vl = D.vl_c, b = vl.map((v, i) => v + W.baeume[i] / 1000), on = key => b.map((v, i) => v + W[key][i] / 1000);
    const order = ['k4', 0, 1, 2], rank = order.indexOf(phase);
    const born = { vl: 'k4', b: 'k4', d20: 1, d50: 1, d100: 1, frei: 1, v: 2 };
    const later = { d50: 1, d100: 1, frei: 1, v: 1 };                          // the click within its phase
    const has = id => order.indexOf(born[id]) < rank || (born[id] === phase && k >= (later[id] || 0));
    const isNew = id => born[id] === phase, dim = id => phase === 2 && id.startsWith('d') || phase === 2 && id === 'frei';
    const ink = light ? EC.ink : '#f2ede2', mut = light ? EC.muted : '#9aa39d', grid = light ? EC.grid : '#2c3437';
    const dot = (color, data, id) => ({ silent: true, symbol: 'circle', symbolSize: 11, animation: isNew(id) ? undefined : false,
      itemStyle: { color, borderColor: light ? '#f2ede2' : '#14181a', borderWidth: 2, opacity: dim(id) ? .35 : 1 },
      label: { show: true, color, fontFamily: EC.font, fontSize: 18, fontWeight: 600, distance: 9, opacity: dim(id) ? .45 : 1 }, data });
    const L = (id, ys, name, o = {}) => Object.assign({ id, name, type: 'line', data: P(ys), showSymbol: false, z: 5,
      animation: isNew(id) ? undefined : false, animationDuration: 1600,
      lineStyle: Object.assign({ color: ANKER_COL[id], width: 3, opacity: dim(id) ? .35 : 1 }, o.line || {}), itemStyle: { color: ANKER_COL[id] },
      markPoint: o.mark ? dot(ANKER_COL[id], o.mark, id) : undefined }, o.extra || {});
    const peak = ys => { const i = ys.indexOf(Math.max(...ys)); return [D.jahre[i], ys[i]]; };
    const series = [];
    const [pv, tv] = peak(vl);
    series.push(L('vl', vl, 'Very Low', { line: { width: 2.4, type: [8, 6] },
      mark: [{ coord: [pv, tv], label: { position: 'top', formatter: `Spitze ${pv}: ${ecNum(tv, 2)} °C` } }],
      extra: { markLine: { silent: true, symbol: 'none', animation: false, lineStyle: { color: ink, width: 1.6, type: 'solid', opacity: .7 },
        label: { show: true, position: 'insideEndTop', color: ink, fontFamily: EC.font, fontSize: 18, formatter: '1,5 °C' }, data: [{ yAxis: 1.5 }] },
        markArea: { silent: true, animation: false, itemStyle: { color: 'rgba(196,18,31,.10)' }, data: [[{ yAxis: 1.5 }, { yAxis: 2.5 }]] } } }));
    series.push(L('b', b, '+ Bäume'));
    if (has('d20')) series.push(L('d20', on('dac_20'), 'DAC 20 %/a', { mark: [{ coord: [D.dac.opt_20.ab, 1.5], label: { position: 'right', offset: [4, -18], formatter: `1,5 °C ab ${D.dac.opt_20.ab}` } }] }));
    if (has('d50')) series.push(L('d50', on('dac_50'), '50 %/a'), L('d100', on('dac_100'), '100 %/a'));
    if (has('frei')) { const f = on('dac_frei'), [pf, tf] = peak(f);
      series.push(L('frei', f, 'unbegrenzt', { line: { width: 2.6, type: [4, 5] }, mark: [{ coord: [pf, tf], label: { position: 'right', offset: [2, -16], formatter: `${ecNum(tf, 2)} °C` } }] })); }
    if (has('v')) { const v = on('vegan'), [pw, tw] = peak(v);
      series.push(L('v', v, 'vegan', { line: { width: 3.4 }, mark: [{ coord: [pw, tw], label: { position: 'top', offset: [34, 0], formatter: `vegan: ${ecNum(tw, 2)} °C` } }] })); }
    const all = series.flatMap(s => s.data.map(p => p[1])), lo = Math.floor(Math.min(...all) * 10) / 10, hi = Math.ceil(Math.max(...all) * 10 + .5) / 10;
    return {
      animationDurationUpdate: 800,
      title: { text: 'Erwärmung gegenüber vorindustriell [°C]', left: 70, top: 0, textStyle: { color: ink, fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
      legend: { left: 66, top: 34, itemGap: 12, itemWidth: 22, icon: 'path://M0,4 H28 V7 H0 Z', textStyle: { color: light ? EC.ink : '#d6dbd6', fontFamily: EC.font, fontSize: 18 },
                data: series.map(x => x.name) },
      grid: { left: 70, right: 24, top: 92, bottom: 40 },
      xAxis: ecAxis({ type: 'value', min: 2026, max: 2100, axisLine: { lineStyle: { color: light ? EC.muted : '#4a524d' } },
                      axisLabel: { color: mut, fontFamily: EC.font, fontSize: 19, customValues: [2026, 2050, 2075, 2100], formatter: v => String(v) } }),
      yAxis: ecAxis({ type: 'value', min: lo, max: hi, interval: .1, axisLine: { lineStyle: { color: light ? EC.muted : '#4a524d' } },
                      axisLabel: { color: mut, fontFamily: EC.font, fontSize: 19, formatter: v => ecNum(v, 1) }, splitLine: { show: true, lineStyle: { color: grid } } }),
      series
    };
  } };
}
const EC_ANKER4 = ecAnker('k4'), EC_ANKER0 = ecAnker(0), EC_ANKER1 = ecAnker(1), EC_ANKER2 = ecAnker(2);
/* why food: what stays in the air of one emission, methane (lifetime 11.8 years, IPCC AR6 WG I) against CO2 (impulse
   response of Joos et al. 2013, multi-model mean), over 100 years */
const EC_ABBAU = { steps: 0, option() {
  const t = Array.from({ length: 101 }, (_, i) => i);
  const co2 = t.map(y => 100 * (0.2173 + 0.2240 * Math.exp(-y / 394.4) + 0.2824 * Math.exp(-y / 36.54) + 0.2763 * Math.exp(-y / 4.304)));
  const ch4 = t.map(y => 100 * Math.exp(-y / 11.8));
  const L = (id, ys, color, name) => ({ id, name, type: 'line', data: t.map((y, i) => [y, ys[i]]), showSymbol: false, lineStyle: { color, width: 3.2 }, itemStyle: { color },
    endLabel: { show: true, formatter: name, color, fontFamily: EC.font, fontSize: 19, fontWeight: 600, distance: 8 } });
  return {
    title: { text: 'Was von einer Emission in der Luft bleibt [%]', left: 60, top: 0, textStyle: { color: '#f2ede2', fontFamily: EC.font, fontSize: 19, fontWeight: 600 } },
    grid: { left: 60, right: 90, top: 46, bottom: 40 },
    xAxis: ecAxis({ type: 'value', min: 0, max: 100, interval: 25, name: 'Jahre', nameLocation: 'middle', nameGap: 28, nameTextStyle: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18 },
                    axisLine: { lineStyle: { color: '#4a524d' } }, axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18 } }),
    yAxis: ecAxis({ type: 'value', min: 0, max: 100, interval: 25, axisLine: { lineStyle: { color: '#4a524d' } },
                    axisLabel: { color: '#9aa39d', fontFamily: EC.font, fontSize: 18 }, splitLine: { show: true, lineStyle: { color: '#2c3437' } } }),
    series: [L('co2', co2, '#5fae76', 'CO₂'), L('ch4', ch4, '#4f9fc7', 'Methan')]
  };
} };
```

In `EC_CHARTS` replace `anker0: …, anker1: …, anker2: …, anker3: EC_ANKER3, tempokap: EC_TEMPOKAP,` by `anker4: EC_ANKER4, anker0: EC_ANKER0, anker1: EC_ANKER1, anker2: EC_ANKER2, abbau: EC_ABBAU,`.

Note on `L('co2', co2, '#5fae76', 'CO₂')`: the helper's signature in `EC_ABBAU` is `(id, ys, color, name)`; keep it as written there.

- [ ] **Step 2: Build**

Run: `uv run python deck/build.py | tail -1`
Expected: `deck/dist/index.html … slides` (slides still reference `anker3`/`tempokap` until Task 6; a missing chart shows „Diagramm fehlt“ only on that slide).

- [ ] **Step 3: Commit**

```bash
git add deck/src/js/deck.js
git commit -m "feat(deck): anchor in deg C with Very Low, the 1.5 deg C line and a curve per measure; decay chart"
```

---

### Task 4: Kapitel 4 endet mit dem Anker

**Files:**
- Modify: `deck/src/slides/04_potenzial.html` (Folie „Wiederbewaldbare Fläche“: overlay), `deck/src/js/deck.js` (`EC_ZEIT`: `steps: 1`, the `k >= 2` branch with `D.noetig` removed, axis max fixed at 35), `deck/src/css/deck.css` (anchor card in the overlay)

**Interfaces:**
- Consumes: `anker4` (Task 3).

- [ ] **Step 1: In the overlay**, after the `data-ec="zeit"` chart, add the light anchor that covers the zeit chart from click 4:

```html
<div class="chart ankerk4" data-step="4" data-ec="anker4" data-label="Erwärmung gegenüber vorindustriell 2026 bis 2100: Very Low mit der Linie bei 1,5 °C, und mit den Bäumen als Forst"></div>
```

CSS (deck.css, next to the overlay rules):

```css
/* chapter 4, last click: the chapter-5 anchor in light, over the cooling chart of the same card */
.overlay .chart.ankerk4 { position: absolute; inset: 0; background: var(--paper); }
```

`EC_ZEIT`: `steps: 2` → `steps: 1`; delete the `if (k >= 2) { … }` block; yAxis `max: k >= 2 ? 350 : 35` → `max: 35`, `interval: 5`, name `'Kühlung der Erde [mK]'`.

- [ ] **Step 2: Notes** of that slide: replace the two paragraphs starting „Klick: Und reicht das?“ and „Klick: Auch als Forst …“ by one:

```html
<p>Klick: Und reicht das? Hier die Kurve vom Anfang: Very Low, das beste Szenario, in Grad. Es liegt rund 30 Jahre über 1,5 °C, Spitze um 2050. Grün darunter mit den Bäumen als Forst: kaum ein Unterschied, ein paar Hundertstel Grad. Die Bäume senken die Spitze nicht.</p>
```

- [ ] **Step 3: Build, screenshot click 4** (`$SP/shot.sh 25 4 …`), check: light chart fills the card, 1,5-°C line, Very Low dashed, trees green, no overlap with the forest box.

- [ ] **Step 4: Commit**

```bash
git add deck/src/slides/04_potenzial.html deck/src/js/deck.js deck/src/css/deck.css
git commit -m "feat(deck): chapter 4 ends on the temperature anchor instead of the gap"
```

---

### Task 5: Folie 27 – DAC-Modell bis η_C

**Files:**
- Modify: `deck/src/slides/05_dac.html` (section `data-title="DAC-Modell"`)

- [ ] **Step 1:** In the flowchart SVG delete the `<g data-step="3">…</g>` group (Einschränkungen, Optimierung). Change the η_C group to full width under both rows (`rect x="0" width="690"`, texts at `x="16"`) and keep `data-step="2"`.
- [ ] **Step 2:** Add before `</div>\n  <p class="src">` of that slide:

```html
    <p class="takeaway" data-step="3" style="--d:0">Heute bleibt von einer Tonne netto knapp die Hälfte, 2040 schon 91&nbsp;%: DAC hängt an der Zeit. <span class="tq">Wie schnell lässt es sich bauen?</span></p>
```

- [ ] **Step 3:** Notes: delete the paragraph „Klick: Weil das je Ort und Jahr anders ist, entscheidet eine Optimierung …“ and add: `<p>Klick: Mit heutigem Strom bleibt also knapp die Hälfte; je sauberer der Strom, desto mehr. DAC hängt damit an der Zeit, wie die Bäume. Wie schnell lässt es sich bauen?</p>`. `lq` stays: „Kann DAC die Lücke nach den Bäumen schließen? Erst: Was bringt eine Tonne?“ → change to „Kann DAC die Kurve unter 1,5 °C drücken? Erst: Was bringt eine Tonne?“. Chart host `data-ec="anker0"` keeps `data-step="0"` (first appearance in chapter 5).
- [ ] **Step 4:** Build, screenshot clicks 2 and 3, check: η_C box full width, takeaway two lines max, anchor in °C.
- [ ] **Step 5: Commit** `git commit -am "feat(deck): DAC model slide ends at the CO2 removal efficiency"`

---

### Task 6: Folie 28 – DAC so schnell wie erlaubt; alte Tempo-Folie entfällt

**Files:**
- Modify: `deck/src/slides/05_dac.html` (section `Was DAC leisten kann`; delete section `Ausbautempo und Kosten`)

- [ ] **Step 1:** Replace the body of „Was DAC leisten kann“ (`lq`, `.anker`, takeaway) with — numbers `X50/Y50`, `X100/Y100`, `XF/YF` are `spitze` (as °C above 1,5 → write peak °C = 1,5 + spitze/1000, two decimals) and `ab` of `opt_50`, `opt_100`, `opt_frei` from Task 2:

```html
    <p class="lq">Wie schnell lässt sich DAC bauen, und was bringt das?</p>
    <div class="anker">
      <div class="chart" data-ec="anker1" data-label="Erwärmung gegenüber vorindustriell 2026 bis 2100: Very Low und Bäume, mit DAC bei 20 Prozent Wachstum im Jahr, dann bei 50 und 100 Prozent und ohne Grenze"></div>
      <div class="flow">
        <div class="fb" data-step="0"><p class="pk">So schnell wie erlaubt</p><div><p>DAC wächst um höchstens 20&nbsp;% im Jahr, so schnell wie einst die Windkraft, gebaut, wo η<sub>C</sub> am höchsten ist, bis 1,5&nbsp;°C erreicht ist.</p><p><b class="big">49&nbsp;Gt/a</b>, 1,5&nbsp;°C ab 2083; die Spitze bleibt.</p></div></div>
        <div class="fb" data-step="1"><p class="pk">Schneller?</p><div><p>50&nbsp;%/a: Spitze X50&nbsp;°C, ab Y50 · 100&nbsp;%/a: X100&nbsp;°C, ab Y100.</p><p>Nur <b>ohne jede Grenze</b> sinkt die Spitze: XF&nbsp;°C, mit 72&nbsp;Gt/a ab sofort. So schnell ist noch keine Technik gewachsen.</p></div></div>
        <div class="fb" data-step="2"><p class="pk">Kosten</p><div><p>bei 20&nbsp;%/a im teuersten Jahr (2077): <b class="big">13,8&nbsp;Bio.&nbsp;€</b></p><p><b>76&nbsp;% des EU-BIP</b> · bis 2100 zusammen 223&nbsp;Bio.&nbsp;€</p></div></div>
      </div>
    </div>
    <p class="takeaway" data-step="3" style="--d:0">Schneller geht technisch nicht, und früh zurück ist teuer. <span class="tq">Gibt es etwas, das sofort wirkt?</span></p>
```

Source line: Gidden et al. 2025 (Speicher), Zurbriggen et al. 2026 (Wachstum), Okosun et al. 2026 (Kosten), Eurostat (BIP EU-27 2024), van Vuuren et al. 2026 (Very Low), Eigene Rechnung (DAC an der Wachstumsgrenze, verteilt nach η_C und Speicher je Land; Kosten im Nachgang). Notes: one paragraph per click in the wording above, plus the backup pointer (Karte, Länder, Optimierung im Backup).

- [ ] **Step 2:** Delete the whole section `data-title="Ausbautempo und Kosten"` from `05_dac.html` (its backup twin `Tempo und Kosten` stays in `07_backup.html`).
- [ ] **Step 3:** Build; screenshot clicks 0–3; check legend in one line (`Very Low · + Bäume · DAC 20 %/a · 50 %/a · 100 %/a · unbegrenzt`); if it wraps, shorten `'+ Bäume'` to `'Bäume'`.
- [ ] **Step 4: Commit** `git commit -am "feat(deck): DAC as fast as allowed on the anchor, faster limits and costs as clicks"`

---

### Task 7: Folie 29 „Warum Ernährung?“ (neu), Folie 30 und Finale

**Files:**
- Modify: `deck/src/slides/05_dac.html` (new section before `Was sofort wirkt`; that section; finale)

- [ ] **Step 1:** Insert before the section `Was sofort wirkt`:

```html
<section class="slide dark" data-ch="dac" data-title="Warum Ernährung?">
  <header class="sh"><h2>Warum Ernährung?</h2></header>
  <div class="body">
    <p class="lq">Gibt es etwas, das sofort wirkt?</p>
    <div class="anker">
      <div class="chart" data-ec="abbau" data-label="Anteil einer Emission, der in der Luft bleibt, über 100 Jahre: Methan nach rund 12 Jahren größtenteils abgebaut, vom CO₂ bleibt ein Fünftel"></div>
      <div class="flow">
        <div class="fb" data-step="0"><p class="pk">Schnell</p><div><p>Methan wirkt stark, ist aber nach rund 12&nbsp;Jahren abgebaut; vom CO₂ bleibt ein Teil Jahrhunderte. Fällt das Methan der Tierhaltung weg, kühlt es <b>innerhalb weniger Jahre</b>.</p></div></div>
        <div class="fb" data-step="1"><p class="pk">Keine Technik</p><div><p>Nichts muss erfunden oder gebaut werden. Die Hürden sind kulturell und politisch, nicht technisch.</p></div></div>
        <div class="fb" data-step="2"><p class="pk">Eher günstiger</p><div><p>In Ländern mit hohem Einkommen ist vegane Ernährung <b>21–34&nbsp;% billiger</b> als die übliche.</p></div></div>
        <div class="fb" data-step="3"><p class="pk">Grenzfall</p><div><p>Alle essen ab 2026 vegan: Tierhaltung fällt weg, Ersatzprodukte brauchen die Hälfte des Futterackers, auf frei werdender Fläche wächst Wald, wo er kühlt.</p></div></div>
      </div>
    </div>
    <p class="takeaway" data-step="4" style="--d:0">Schnell, ohne Technik, eher günstiger. <span class="tq">Wie viel bringt das, und wann?</span></p>
  </div>
  <p class="src"><span><a href="https://doi.org/10.1017/9781009157896.009" target="_blank" rel="noopener">IPCC AR6 WG I, Kap. 7</a> (Methan-Lebensdauer)</span><span><a href="https://doi.org/10.5194/acp-13-2793-2013" target="_blank" rel="noopener">Joos et al. 2013</a> (CO₂-Impulsantwort)</span><span><a href="https://www.ipcc.ch/report/ar6/wg3/downloads/report/IPCC_AR6_WGIII_Chapter05.pdf" target="_blank" rel="noopener">IPCC AR6 WG III, Kap. 5</a> (Ernährung als Nachfrage-Option, Hürden)</span><span><a href="https://doi.org/10.1016/S2542-5196(21)00251-5" target="_blank" rel="noopener">Springmann et al. 2021</a> (Kosten)</span></p>
  <aside class="notes" data-n="29">
    <p>DAC kommt für die Spitze zu spät. Gibt es etwas, das sofort wirkt? Links: Was von einer Emission in der Luft bleibt. Methan ist nach rund zwölf Jahren größtenteils abgebaut, vom CO₂ bleibt ein Fünftel über Jahrhunderte. Fällt das Methan der Tierhaltung weg, kühlt es also innerhalb weniger Jahre.</p>
    <p>Klick: Dafür muss nichts erfunden oder gebaut werden. Pflanzliche Ernährung ist laut IPCC die größte Option auf der Nachfrageseite; die Hürden sind kulturell und politisch, und es braucht Politik, die das erleichtert.</p>
    <p>Klick: Und es ist eher günstiger: In reichen Ländern ist vegane Ernährung ein Fünftel bis ein Drittel billiger als die übliche.</p>
    <p>Klick: Ich rechne den Grenzfall: Alle essen ab 2026 vegan. Die Tierhaltung fällt weg; Ersatzprodukte brauchen etwa die Hälfte des Ackers, der heute Futter trägt; auf frei werdenden Weiden und Äckern wächst Wald, wo er kühlt.</p>
    <p>Klick: Wie viel bringt das, und wann?</p>
    <p class="q">Falls Fragen kommen — Methan-Lebensdauer 11,8 Jahre (IPCC AR6 WG I). Kosten: gilt für wenig verarbeitete Lebensmittel; in Ländern mit niedrigem Einkommen ist eine gesunde, nachhaltige Ernährung teurer als die dort übliche (Springmann et al. 2021).</p>
  </aside>
</section>
```

Before committing, open the IPCC AR6 WG I chapter 7 (table of greenhouse-gas lifetimes) and confirm 11.8 years for methane; if the value differs, use the table's value in chart comment, slide and notes.

- [ ] **Step 2:** Section `Was sofort wirkt`: `lq` → „Wie viel bringt die vegane Welt, und wann?“; chart host stays `data-ec="anker2"` without `data-step`; in `.flow` delete the „Grenzfall“ block, keep the contribution chart block (`data-step="0"`, its chart `data-step="0"`), the `cue` (`data-step="1"`) and „DAC dazu?“ (`data-step="2"`); takeaway `data-step="3"`: „Für die Spitze zählt, was vor 2050 wirkt: weniger Methan senkt sie sofort, DAC kommt dafür zu spät.“ Notes: first paragraph from the contribution plot, second „Klick: im Anker die vegane Welt, ganz ohne DAC: Spitze … °C um 2044, ab 2065 unter 1,5 °C“ (values from `vl_c`/`wirkung`), then DAC dazu, then the takeaway.
- [ ] **Step 3:** Finale column 3: heading „Für die Spitze zählt, was vor 2050 wirkt“, text „DAC kommt zu spät und teuer; weniger Methan kühlt sofort<br>→ Bäume pflanzen, Methan senken, DAC schnell ausbauen“. Notes accordingly.
- [ ] **Step 4:** Renumber `data-n` in `05_dac.html`/`06_schluss.html` to slide positions (check with the slide list from the built `index.html`).
- [ ] **Step 5:** Build, screenshot 29 (clicks 0–4) and 30 (0–3); check text sizes, no overflow.
- [ ] **Step 6: Commit** `git commit -am "feat(deck): why food, the vegan world on the anchor, finale on the message"`

---

### Task 8: Prüfen

**Files:** none new (scratchpad scripts `animtest.mjs`, `fadetest*.mjs`, `persist2.py`)

- [ ] **Step 1:** `uv run --extra dev pytest -q -k "not Sobol"` → all green (report count).
- [ ] **Step 2:** Clicks per slide = max `data-step` and chart steps: list with the BeautifulSoup snippet from the last session; no slide ends with an empty click.
- [ ] **Step 3:** CDP: walk 25 (clicks) → 27 → 28 → 29 → 30 → 31 and back 30 → 28; per click report running anchor animations and the anchor's bounding rect on 27, 28, 30. Expected: animations only when a line is new (28 entry: DAC 20; 28 click 1: three lines; 30 click 1: vegan), rect identical on 27/28/30.
- [ ] **Step 4:** Numbers on slides and in notes against `zeitpfade.json` (Python snippet printing peaks/years/capacities used on 27–30).
- [ ] **Step 5:** Update memory `dac-optimierung.md` and `zuhoerer-fuehren.md` with the new chapter structure; commit any fixes.
