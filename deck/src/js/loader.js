/* chart data and ECharts load in the background; the first slide does not wait for them */
window.DECK_DATA = Promise.all(["data/cmip7.js", "data/ec_charts.js", "data/maps.js", "vendor/echarts/echarts.min.js"].map(src => new Promise(ok => {
  const s = document.createElement('script'); s.src = src; s.async = true; s.dataset.dyn = 1;
  s.onload = s.onerror = ok; document.head.appendChild(s);
}))).then(() => { /* the deck draws four of the seven CMIP7 markers */
  const keep = ["H", "M", "ML", "VL"], D = window.CMIP7; if (!D) return;
  D.markers = D.markers.filter(m => keep.includes(m.k)); D.cum = D.cum.filter(c => keep.includes(c.k)); });