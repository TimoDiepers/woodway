// Export the deck's maps from the HTML deck as SVG (+ PNG fallback) for the pptx.
//
// The maps are drawn by the HTML deck (ECharts, nbs.map_fields); this script opens the
// deck in headless Chrome, renders each map with ECharts' SVG renderer in its finished
// state and writes docs/slides/figures/hex_<key>.svg and .png. scripts/build_map_slides.py
// puts them into dissvortrag_v2.pptx.
//
//   cd docs/slides/html && python3 -m http.server 8765 &
//   NODE_PATH=<dir with puppeteer-core> node scripts/export_deck_svgs.mjs [keys...]
import { createRequire } from 'module';
import { writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
const puppeteer = require('puppeteer-core');
const here = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(here, '../docs/slides/figures');
const KEYS = process.argv.slice(2).length ? process.argv.slice(2) : ['b5', 'b8a', 'b8', 'k15', 'v0', 'v1', 'd1', 'd4'];
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = process.env.DECK_URL || 'http://127.0.0.1:8765/dissvortrag_v2.html';

// PowerPoint and LibreOffice read neither the CSS `font:` shorthand nor font lists in SVG text,
// and not always `dominant-baseline`: write every text as plain SVG attributes instead.
function plainText(svg) {
  return svg.replace(/<text([^>]*)>/g, (m, attrs) => {
    let size = null, weight = null, style = null;
    const st = attrs.match(/style="([^"]*)"/);
    if (st) {
      const css = st[1];
      const sh = css.match(/font:\s*(normal|italic)?\s*(\d{3}|bold|normal)?\s*([\d.]+)px/);
      if (sh) { style = sh[1]; weight = sh[2]; size = sh[3]; }
      const fs = css.match(/font-size:\s*([\d.]+)px/); if (fs) size = fs[1];
      const fw = css.match(/font-weight:\s*(\w+)/); if (fw) weight = fw[1];
      const fst = css.match(/font-style:\s*(\w+)/); if (fst) style = fst[1];
      attrs = attrs.replace(/\s*style="[^"]*"/, '');
    }
    let dy = '';
    if (/dominant-baseline="(central|middle)"/.test(attrs)) { attrs = attrs.replace(/\s*dominant-baseline="[^"]*"/, ''); dy = ' dy="0.35em"'; }
    const w = weight && weight !== 'normal' && +weight !== 400 ? ` font-weight="${+weight >= 600 || weight === 'bold' ? 'bold' : weight}"` : '';
    const it = style === 'italic' ? ' font-style="italic"' : '';
    return `<text${attrs} font-family="Arial"${size ? ` font-size="${(+size).toFixed(2)}"` : ''}${w}${it}${dy}>`;
  });
}

// Text with a halo (ECharts: stroke under the fill via paint-order) comes out pale in
// LibreOffice and PowerPoint, which ignore paint-order and draw the stroke on top: write the
// halo as its own text (stroke only) under a copy without stroke.
function splitHalo(svg) {
  return svg.replace(/<text([^>]*?)\s+paint-order="stroke"([^>]*)>([^<]*)<\/text>/g, (m, a, b, body) => {
    const attrs = a + b;
    const halo = attrs.replace(/\s+fill="[^"]*"/, '').replace(/\s+fill-opacity="[^"]*"/, '') + ' fill="none"';
    const text = attrs.replace(/\s+stroke(-[a-z]+)?="[^"]*"/g, '');
    return `<text${halo}>${body}</text><text${text}>${body}</text>`;
  });
}

const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 1000, deviceScaleFactor: 2 });
page.on('pageerror', e => console.error('PAGEERROR', e.message));
await page.goto(URL + '?all', { waitUntil: 'networkidle0', timeout: 120000 });
for (const key of KEYS) {
  const svg = await page.evaluate(k => { const r = MplChart.svg(k, 1600); window.__last = r.host; return r.svg; }, key);
  writeFileSync(`${OUT}/hex_${key}.svg`, splitHalo(plainText(svg)));
  const el = await page.$('.svg-export:last-of-type');
  await el.screenshot({ path: `${OUT}/hex_${key}.png` });
  await page.evaluate(() => { window.__last.remove(); });
  console.log(`hex_${key}.svg  ${(svg.length / 1e6).toFixed(2)} MB`);
}
await browser.close();
