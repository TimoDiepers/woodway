/* Chart data and ECharts load in the background. Parsing ~3 MB of chart data blocks the main thread for about a
   second, and the deck's SVG entrances (the title slide's trees) run on that thread — so the load starts only once
   the opening slide has played its entrance (~2.1 s), or at once when the deck opens on a later slide, runs as a
   preview, or the speaker moves on (Deck calls window.__deckDataNow). */
(function () {
  let begin;
  const started = new Promise(ok => { begin = ok; });
  let asked = false;
  window.__deckDataNow = () => { if (!asked) { asked = true; begin(); } };
  window.DECK_DATA = started.then(() => Promise.all(["data/cmip7.js", "data/ec_charts.js", "data/maps.js", "vendor/echarts/echarts.min.js"].map(src => new Promise(ok => {
    const s = document.createElement('script'); s.src = src; s.async = true; s.dataset.dyn = 1;
    s.onload = s.onerror = ok; document.head.appendChild(s);
  })))).then(() => { /* the deck draws four of the seven CMIP7 markers */
    const keep = ["H", "M", "ML", "VL"], D = window.CMIP7; if (!D) return;
    D.markers = D.markers.filter(m => keep.includes(m.k));
    const deckCol = { VL: "#2e7d4f", ML: "#b08326", M: "#c8602a", H: "#8e2433" };   /* deck palette: --co2, ochre, --alb, clay red */
    D.markers.forEach(m => { m.color = deckCol[m.k] || m.color; }); D.cum = D.cum.filter(c => keep.includes(c.k)); });
  // overview thumbnails (?embed&lite): layout only, no chart data
  if (/[?&]lite\b/.test(location.search)) return;
  const h = parseInt(location.hash.slice(1), 10);
  if (/[?&](embed|presenter)/.test(location.search) || window.__EMBED || (Number.isFinite(h) && h > 1)) window.__deckDataNow();
  else setTimeout(window.__deckDataNow, 2100);
})();
