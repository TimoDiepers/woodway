// Renders every slide of the built deck (../deck/dist) once, in its end state, to a small WebP:
// deck/dist/thumbs/01.webp … The talk's slide overview shows these instead of one live deck per card,
// which ran phones out of memory ("a problem repeatedly occurred").
// Usage: node scripts/thumbs.mjs   (CHROME=/path/to/chrome to override the browser)
import { createServer } from "node:http";
import { existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const DIST = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../deck/dist");
const OUT = path.join(DIST, "thumbs");
const W = 480;   // card width at 2× on a two-column phone grid, ~30 KB each
const CHROMES = [process.env.CHROME, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"];
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".png": "image/png",
  ".jpg": "image/jpeg", ".webp": "image/webp", ".woff2": "font/woff2", ".json": "application/json" };

const server = createServer((req, res) => {
  const rel = decodeURIComponent(new URL(req.url, "http://x").pathname);
  const p = path.join(DIST, rel === "/" ? "index.html" : rel);
  if (!p.startsWith(DIST) || !existsSync(p) || statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": TYPES[path.extname(p)] ?? "application/octet-stream" });
  res.end(readFileSync(p));
}).listen(0);
const port = server.address().port;

const browser = await puppeteer.launch({ executablePath: CHROMES.find((c) => c && existsSync(c)), headless: true,
  args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox", "--hide-scrollbars"] });
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 900, deviceScaleFactor: W / 1600 });
  await page.goto(`http://localhost:${port}/index.html?embed#1`, { waitUntil: "load" });
  await page.evaluate(() => window.DECK_DATA);
  await page.evaluate(() => document.fonts.ready);
  const n = await page.evaluate(() => document.querySelectorAll("section.slide").length);
  if (!n) throw new Error("no slides found in deck/dist/index.html");
  mkdirSync(OUT, { recursive: true });
  for (let i = 0; i < n; i++) {
    await page.evaluate((i) => window.postMessage({ src: "dv", goto: i, step: "end" }, "*"), i);
    // charts and maps animate in even in still mode; a slide without one only needs the message and a layout
    const charts = await page.evaluate((i) => document.querySelectorAll("section.slide")[i].querySelectorAll(".chart").length, i);
    await new Promise((r) => setTimeout(r, charts ? 2600 : 400));
    await page.screenshot({ path: path.join(OUT, `${String(i + 1).padStart(2, "0")}.webp`), type: "webp", quality: 72 });
  }
  console.log(`${n} thumbnails → ${path.relative(process.cwd(), OUT)}`);
} finally {
  await browser.close();
  server.close();
}
