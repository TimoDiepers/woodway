"""JS/CSS for maps with one frame per year (player under the map); applied by new_vergleich.py."""


def patch(s: str) -> str:
    def rep(old, new):
        nonlocal s
        assert old in s, old[:60]
        s = s.replace(old, new)

    rep("""      const look = new Map(L.cells.map(cell => [cell[0] * g.nx + cell[1], cell]));""",
        """      const look = new Map(L.cells.map((cell, j) => [cell[0] * g.nx + cell[1], j]));""")
    rep("""        const r = Math.floor((g.lat0 - lat) / d), c = Math.floor((lon - g.lon0) / d), cell = look.get(r * g.nx + c);
        if (!cell) continue;""",
        """        const r = Math.floor((g.lat0 - lat) / d), c = Math.floor((lon - g.lon0) / d), j = look.get(r * g.nx + c);
        if (j === undefined) continue;
        const cell = L.cells[j];""")
    rep("""          const sc = M.scales[L.scale]; col = mapScale(sc, cell[2]); tip = mapFmt(cell[2], sc);""",
        """          const sc = M.scales[L.scale], v = L.frames ? this.frameValue(L, j) : cell[2];
          col = mapScale(sc, v); tip = mapFmt(v, sc) + (L.frames ? ` (${Math.round(this.year ?? L.years[0])})` : '');""")
    rep("""    this.k = null;
    this.final(this.nSteps);
    new ResizeObserver(() => { if (this.size()) { this.chart.resize(); this.final(this.k ?? this.nSteps); } }).observe(host);
  }""", """    this.k = null;
    this.timeLayer = this.mapSpec && this.mapSpec.panels[0].layers.find(L => L.frames);
    if (this.timeLayer) { this.year = this.timeLayer.years[0]; if (host.dataset.renderer !== 'svg') this.player(); }
    this.final(this.nSteps);
    new ResizeObserver(() => { if (this.size()) { this.chart.resize(); this.final(this.k ?? this.nSteps); } }).observe(host);
  }

  /* Maps with one frame per year (nbs.map_fields: "years" + "frames"): values glide between the years.
     A play button and a timeline under the map, as in woodway's TimeSlider: a full sweep takes 10 s,
     advanced per animation frame by elapsed time, so it moves continuously instead of in yearly jumps. */
  frameValue(L, j) {
    const y0 = L.years[0], n = L.years.length - 1, t = Math.max(0, Math.min(n, (this.year ?? y0) - y0));
    const k = Math.min(n - 1, Math.floor(t)), f = t - k;
    return L.frames[k][j] * (1 - f) + L.frames[k + 1][j] * f;
  }
  player() {
    const L = this.timeLayer, y0 = L.years[0], y1 = L.years[L.years.length - 1], perSec = (y1 - y0) / 10;
    const bar = document.createElement('div');
    bar.className = 'player';
    bar.innerHTML = `<button type="button" aria-label="Abspielen"><svg viewBox="0 0 24 24"><path class="i-play" d="M7 4.5v15l12-7.5z"/><g class="i-pause"><rect x="6" y="4.5" width="4" height="15" rx="1"/><rect x="14" y="4.5" width="4" height="15" rx="1"/></g></svg></button>
      <div class="track"><input type="range" min="${y0}" max="${y1}" step="1" value="${y0}" aria-label="Jahr"><div class="ticks">${[y0, 2050, 2075, 2100].map(y => `<span style="left:calc(7px + (100% - 14px) * ${(y - y0) / (y1 - y0)})">${y}</span>`).join('')}</div></div>
      <span class="yr">${y0}</span>`;
    this.host.after(bar);
    const btn = bar.querySelector('button'), range = bar.querySelector('input'), label = bar.querySelector('.yr');
    let raf = null, last = null;
    const show = y => { this.setYear(y); range.value = Math.round(y); label.textContent = Math.round(y); };
    const stop = () => { if (raf) cancelAnimationFrame(raf); raf = null; last = null; bar.classList.remove('playing'); btn.setAttribute('aria-label', 'Abspielen'); };
    const tick = ts => {
      if (last === null) last = ts;
      const next = this.year + perSec * (ts - last) / 1000; last = ts;
      if (next >= y1) { show(y1); stop(); return; }
      show(next); raf = requestAnimationFrame(tick);
    };
    btn.addEventListener('click', () => {
      btn.blur();
      if (raf) { stop(); return; }
      if (this.year >= y1) show(y0);   // a finished sweep starts again
      bar.classList.add('playing'); btn.setAttribute('aria-label', 'Pause');
      raf = requestAnimationFrame(tick);
    });
    range.addEventListener('input', () => { stop(); show(+range.value); });
    range.addEventListener('change', () => range.blur());
    // leaving the slide: stop and go back to the first year
    const slide = this.host.closest('.slide');
    if (slide) new MutationObserver(() => { if (!slide.classList.contains('active')) { stop(); if (this.year !== y0) show(y0); } })
      .observe(slide, { attributes: true, attributeFilter: ['class'] });
  }
  setYear(y) {
    this.year = y;
    if (!this.chart || this.k === null) return;
    const i = this.mapAxes[0], out = [];
    this.hexSeries(out, n => `a${i}_${n}`, i, this.mapSpec.panels[0], 0, this.s);
    out.forEach(x => { x.animation = false; });
    this.chart.setOption({ series: out });
  }""")
    rep(""".chart { flex: 1; min-height: 0; position: relative; }""",
        """.chart { flex: 1; min-height: 0; position: relative; }
/* timeline under a map with one frame per year (MplChart.player) */
.player { display: flex; align-items: center; gap: 16px; width: 640px; margin: 2px auto 0; font-family: var(--sans); }
.player button { flex: none; width: 44px; height: 44px; border-radius: 50%; border: 1.5px solid var(--paper-line); background: var(--paper-deep);
                 display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--ch); }
.player button:hover { background: color-mix(in srgb, var(--paper-deep) 80%, var(--ch)); }
.player button svg { width: 18px; height: 18px; fill: currentColor; }
.player .i-pause, .player.playing .i-play { display: none; }
.player.playing .i-pause { display: inline; }
.player .track { position: relative; flex: 1; padding-bottom: 18px; }
.player input[type=range] { width: 100%; margin: 0; accent-color: var(--ch); cursor: pointer; }
.player .ticks span { position: absolute; top: 24px; transform: translateX(-50%); font-size: 14px; color: var(--muted); }
.player .yr { flex: none; width: 64px; font: 600 26px/1 var(--sans); color: var(--ch); font-variant-numeric: tabular-nums; }""")
    return s
