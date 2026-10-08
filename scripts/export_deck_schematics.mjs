// Export the deck's schematic drawings (inline <svg data-export="key"> in the HTML deck) as
// SVG (+ PNG fallback) for the pptx, docs/slides/figures/:
//
//   <key>.svg/.png       the finished drawing (every build step shown)
//   <key>@<n>.svg/.png   build layer n alone (0 = what is there before the first click),
//                        same size, so the layers stack exactly
//
// The drawings use the deck's CSS tokens (fill="var(--moss)") and web fonts; this script
// opens the deck in headless Chrome with every build step shown, writes the computed colours
// into plain attributes and swaps the fonts for ones PowerPoint has (IBM Plex Sans -> Arial,
// Literata -> Georgia). Effects that step back on a slide (.dimmable on data-tree="dim")
// keep their reduced opacity. scripts/build_schema_slides.py puts them into the pptx.
//
//   cd docs/slides/html && python3 -m http.server 8765 &
//   NODE_PATH=<dir with puppeteer-core> node scripts/export_deck_schematics.mjs [keys...]
import { createRequire } from 'module';
import { writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
const puppeteer = require('puppeteer-core');
const here = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(here, '../docs/slides/figures');
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = process.env.DECK_URL || 'http://127.0.0.1:8765/dissvortrag_v2.html';
const SCALE = 2;

const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 1000, deviceScaleFactor: SCALE });
page.on('pageerror', e => console.error('PAGEERROR', e.message));
await page.goto(URL + '?all', { waitUntil: 'networkidle0', timeout: 120000 });
const all = await page.evaluate(() => [...document.querySelectorAll('svg[data-export]')].map(s => s.dataset.export));
const keys = process.argv.slice(2).length ? process.argv.slice(2) : all;

for (const key of keys) {
  const out = await page.evaluate(k => {
    const src = document.querySelector(`svg[data-export="${k}"]`);
    const fonts = { 'IBM Plex Sans': 'Arial', 'Literata': 'Georgia' };
    const dim = !!src.closest('[data-tree="dim"]');
    const base = src.cloneNode(true);
    // colours as plain rgb: computed color-mix() comes back as color(srgb …), which LibreOffice
    // and PowerPoint do not read; one pixel through a canvas gives the sRGB value
    const cv = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
    const rgb = c => {
      if (!c || c === 'none' || c.startsWith('url(')) return c;
      cv.clearRect(0, 0, 1, 1); cv.fillStyle = '#000'; cv.fillStyle = c; cv.fillRect(0, 0, 1, 1);
      const [r, g, bl, al] = cv.getImageData(0, 0, 1, 1).data;
      return al === 255 ? `rgb(${r},${g},${bl})` : `rgba(${r},${g},${bl},${(al / 255).toFixed(3)})`;
    };
    const a = [src, ...src.querySelectorAll('*')], b = [base, ...base.querySelectorAll('*')];
    a.forEach((el, i) => {
      const cs = getComputedStyle(el), o = b[i];
      for (const p of ['fill', 'stroke']) {
        const v = el.getAttribute(p);
        if (v && (v.includes('var(') || v.includes('color-mix('))) o.setAttribute(p, rgb(cs[p]));
      }
      const ff = el.getAttribute('font-family');
      if (ff) o.setAttribute('font-family', fonts[ff] || ff);
      const w = el.getAttribute('font-weight');
      if (w && +w >= 600) o.setAttribute('font-weight', 'bold');
      if (dim && el.classList.contains('dimmable')) o.setAttribute('opacity', '0.22');
      o.removeAttribute('class'); o.removeAttribute('style');
    });
    const vb = src.viewBox.baseVal;
    base.removeAttribute('data-export');
    base.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    base.setAttribute('width', vb.width); base.setAttribute('height', vb.height);

    // build layers: an element belongs to the step of its nearest data-step (0 without one)
    const step = el => { const s = el.closest('[data-step]'); return s ? +s.dataset.step : 0; };
    const steps = [...new Set([0, ...[...base.querySelectorAll('[data-step]')].map(e => +e.dataset.step)])].sort((x, y) => x - y);
    const ser = svg => new XMLSerializer().serializeToString(svg);
    const strip = svg => { for (const e of svg.querySelectorAll('[data-step]')) e.removeAttribute('data-step'); return svg; };
    const layers = steps.length > 1 ? steps.map(n => {
      const c = base.cloneNode(true);
      // deepest first, so a group is judged after its children are gone
      for (const e of [...c.querySelectorAll('*')].reverse()) {
        if (e.closest('defs')) continue;
        const keep = step(e) === n || [...e.querySelectorAll('*')].some(d => step(d) === n);
        if (!keep) e.remove();
      }
      return { n, svg: ser(strip(c)) };
    }) : [];
    return { full: ser(strip(base)), w: vb.width, h: vb.height, layers };
  }, key);

  const files = [{ name: key, svg: out.full }, ...out.layers.map(l => ({ name: `${key}@${l.n}`, svg: l.svg }))];
  for (const f of files) {
    writeFileSync(`${OUT}/${f.name}.svg`, f.svg);
    // PNG fallback: the exported SVG itself, drawn as an image (what PowerPoint would show)
    const png = await page.evaluate(async (svg, w, h, s) => {
      const img = new Image();
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
      await img.decode();
      const c = document.createElement('canvas');
      c.width = w * s; c.height = h * s;
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      return c.toDataURL('image/png').split(',')[1];
    }, f.svg, out.w, out.h, SCALE);
    writeFileSync(`${OUT}/${f.name}.png`, Buffer.from(png, 'base64'));
  }
  console.log(`${key}: ${out.layers.length ? out.layers.length + ' Ebenen' : 'ohne Aufbau'}`);
}
await browser.close();
