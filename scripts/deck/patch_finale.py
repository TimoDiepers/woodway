"""End of the talk: the DAC chapter stays dark like its break slide ("Sind wir auf dem Holzweg?"), the conclusion
answers it in daylight -- the same forest and the same engineer, now in the sun -- and the thanks stay bright.

- Slides "DAC-Modell" and "Optimierung von DAC" get the dark look of the result film (class "dark"), the ECharts
  gap chart on the optimisation slide gets light text.
- The conclusion is rewritten: three answers in the order of the talk, the outlook in one line, one takeaway.
"""

import re

DARK_CSS = """
/* DAC chapter: dark like its break slide */
.slide.dark { --ink: #f2ede2; --ink-2: #d6dbd6; --muted: #9aa39d; --paper-deep: #20282b; --paper-line: #3a4447; --fjord-soft: #9cc3d6; }
.slide.dark .inp h4, .slide.dark .bridge b { color: #e0a83e; }
.slide.dark .inp .q { color: #8d958f; }
.slide.dark .inp { border-top-color: #e0a83e; }
/* the conclusion in daylight */
.slide.finale { --ch: #4f7a3a; --ch-soft: #b5cf98; background: linear-gradient(180deg, #fbf1d3 0%, #f4eedd 46%, #f2ede2 100%); }
.slide.finale > .sh, .slide.finale > .body { position: relative; z-index: 1; }
.slide.finale .cols3 .col p { font-size: 22px; line-height: 1.42; }
.slide.finale .outlook { margin-top: 26px; background: rgba(255, 255, 255, .45); border-radius: 0 10px 10px 0; }
.slide.finale .outlook p { font-size: 20px; }
/* the happy end: the sun comes up when the slide opens; on the last click a young tree grows, the engineer speaks, birds pass */
/* from the dark DAC chapter into the day: the slide opens at night, the sun comes up, the night and the dark forest
   fade, then the text */
.slide.finale .sunrays { transform-box: fill-box; transform-origin: center; animation: sunspin 40s linear infinite; }
@keyframes sunspin { to { transform: rotate(360deg); } }
.slide.finale .sunrise { transform: translateY(300px); transition: transform 3.6s cubic-bezier(.25, .6, .25, 1) .2s; }
.slide.finale .night { opacity: 1; transition: opacity 3.2s ease-in-out 1s; }
.slide.finale .dawn { opacity: 0; }
.slide.finale.active .dawn { animation: dawn 5s ease-in-out .4s both; }
@keyframes dawn { 0% { opacity: 0; } 45% { opacity: .85; } 100% { opacity: 0; } }
.slide.finale > .sh, .slide.finale > .body { opacity: 0; transition: opacity 1.1s ease 3.4s; }
.slide.finale.active .sunrise, .embed .slide.finale .sunrise, .all .slide.finale .sunrise { transform: none; }
.slide.finale.active .night, .embed .slide.finale .night, .all .slide.finale .night { opacity: 0; }
.slide.finale.active > .sh, .slide.finale.active > .body, .embed .slide.finale > .sh, .embed .slide.finale > .body,
.all .slide.finale > .sh, .all .slide.finale > .body { opacity: 1; }
.slide.finale .sapling { transform-box: fill-box; transform-origin: 50% 100%; }
.slide.active.finale .sapling.shown { animation: sprout 1.8s cubic-bezier(.3, 1.4, .5, 1) both; }
@keyframes sprout { from { transform: scale(.05); } to { transform: scale(1); } }
.slide.finale .say { transform-box: fill-box; transform-origin: 40% 100%; }
.slide.active.finale .say.shown { animation: pop .5s cubic-bezier(.3, 1.5, .5, 1) 1.1s both; }
.slide.finale .birds { opacity: 0; }
.slide.active.finale .birds.shown { opacity: 1; animation: fly 9s linear .4s both; }
@keyframes fly { from { transform: translate(-380px, 30px); } to { transform: translate(560px, -60px); } }
.slide.finale .birds path { animation: flap .5s ease-in-out infinite alternate; transform-box: fill-box; transform-origin: 50% 50%; }
@keyframes flap { from { transform: scaleY(1); } to { transform: scaleY(.45); } }
"""

DARK_EC = r"""
/* the gap chart on a dark slide: light text and lines, the colours of the curves stay */
function ecDark(o) {
  const map = { [EC.ink]: '#f2ede2', [EC.ink2]: '#d6dbd6', [EC.muted]: '#9aa39d', [EC.grid]: '#2c3437', [EC.line]: '#3a4447', '#8a918c': '#6d756f', '#8e0d16': '#ff7a6e', '#c4121f': '#ff5a4f', '#2f7a45': '#6cc28a', '#c8602a': '#ef8a52' };
  const walk = v => { if (Array.isArray(v)) return v.map(walk); if (v && typeof v === 'object' && v.constructor === Object) { for (const k in v) v[k] = walk(v[k]); return v; }
                      return typeof v === 'string' && map[v] ? map[v] : v; };
  return walk(o);
}
"""

FOREST = {"#0f1412": "#4a3a2a", "#1d2823": "#6f8f55", "#18221d": "#7f9c64", "#212d27": "#5f7f48",
          "#26342d": "#8ea477", "#212e28": "#a9bc8f", "#2b3a32": "#7f9c64", "#101513": "#cbd6b4"}

NOTES = """    <p>Zurück zur Frage vom Anfang des Kapitels: Sind wir mit den Bäumen auf dem Holzweg? Nein — aber sie sind nicht die ganze Antwort.</p>
    <p>Erstens: Bäume kühlen, aber nicht überall. Von 0,83 Milliarden Hektar wiederbewaldbarer Fläche kühlen nur 0,39 netto; im Norden hält die Albedo dagegen. Also pflanzen, wo sie kühlen.</p>
    <p>Klick: Zweitens: Bäume allein reichen nicht. Auf allen kühlenden Flächen bringen sie 2100 rund 19 Millikelvin; für 1,5 °C fehlen dann noch rund 262 Gigatonnen CO₂.</p>
    <p>Klick: Drittens: DAC kann die Lücke schließen, aber spät: 6,9 Gigatonnen im Jahr ab Ende der 2060er, dort, wo Speicher ist — Nordafrika, USA, Australien. Den Overshoot um 2050 verhindert es nicht, dafür wächst es zu langsam. Bis dahin zählen Emissionsminderung und die Bäume, die jetzt gepflanzt werden.</p>
    <p>Klick: Was noch nicht drin ist: was mit dem Holz passiert — Bauholz statt Beton und Stahl hilft den Bäumen wahrscheinlich noch mehr —, Lebensraum und Artenvielfalt, die lokale Kühlung durch Schatten und Verdunstung, Wasser und Boden.</p>
    <p>Klick: Also: Jetzt Bäume pflanzen, dort, wo sie kühlen — und DAC früh hochfahren.</p>
    <p>Klick: Und das Gute: Wir kriegen das hin, wenn wir wollen.</p>
"""


def _sec(page, title):
    m = re.search(r'<section class="slide[^"]*"(?: data-ch="[^"]*")? data-title="' + re.escape(title) + r'">.*?</section>\n', page, flags=re.S)
    assert m, title
    return m


def _rep(s, old, new):
    assert s.count(old) == 1, old[:90]
    return s.replace(old, new)


def _daylight(page) -> str:
    """The forest and the engineer of the break slide, recoloured for daylight, smaller, along the foot of the slide."""
    s = _sec(page, "Sind wir auf dem Holzweg?").group(0)
    svg = re.search(r'<svg class="deco mo" data-export="s_holzweg"[^>]*>(.*?)</svg>', s, flags=re.S).group(1)
    eng = svg[svg.index('<g class="eng" data-step="1">'):]
    forest = svg[: svg.index('<g class="eng" data-step="1">')]
    night_forest = forest
    for a, b in FOREST.items():
        forest = forest.replace(a, b)
    eng = re.sub(r'<g class="bubble">.*?</g>(?=</g>$)', '', eng, flags=re.S).replace('<g class="eng" data-step="1">', '<g>', 1)
    eng = eng.replace('fill="#14181a"', 'fill="#f2ede2"')
    import math
    cx, cy = 1120, 668   # up over the trees, clear of the text and the speech bubble
    sun = ('<g class="sunrays" stroke="#eab64e" stroke-width="6" stroke-linecap="round">'
           + "".join(f'<line x1="{cx + 76 * math.cos(a):.1f}" y1="{cy + 76 * math.sin(a):.1f}" x2="{cx + 98 * math.cos(a):.1f}" y2="{cy + 98 * math.sin(a):.1f}"/>'
                     for a in (k * math.pi / 6 for k in range(12)))
           + f'</g><circle cx="{cx}" cy="{cy}" r="60" fill="#f0c25a"/>')
    return (f'<svg class="deco mo" data-export="s_finale" viewBox="0 0 1600 900" aria-hidden="true" style="z-index:0">'
            '<defs><linearGradient id="fin-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#14181a"/>'
            '<stop offset=".62" stop-color="#1c1f22"/><stop offset=".86" stop-color="#3a2c22"/><stop offset="1" stop-color="#4a3424"/></linearGradient>'
            '<radialGradient id="fin-glow" cx="1120" cy="700" r="760" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ffb35c" stop-opacity=".95"/>'
            '<stop offset=".35" stop-color="#f08a5d" stop-opacity=".55"/><stop offset="1" stop-color="#c76b7a" stop-opacity="0"/></radialGradient></defs>'
            '<g class="night"><rect width="1600" height="900" fill="url(#fin-sky)"/></g><g class="dawn"><rect width="1600" height="900" fill="url(#fin-glow)"/></g>'
            f'<g class="sunrise"><g opacity=".9">{sun}</g></g>'
            f'<g transform="translate(0 372) scale(.6)">{forest}</g><g transform="translate(960 372) scale(.6)">{forest}</g>'
            f'<g class="night"><g transform="translate(0 372) scale(.6)">{night_forest}</g><g transform="translate(960 372) scale(.6)">{night_forest}</g></g>'
            f'<g transform="translate(560 372) scale(.6)">{eng}</g>{_ending()}</svg>')


def _ending() -> str:
    """Last click: a young tree beside the engineer, his line, three birds."""
    tree = ('<g class="sapling" data-step="5"><rect x="1424" y="772" width="10" height="98" fill="#4a3a2a"/>'
            '<circle cx="1429" cy="752" r="40" fill="#8fbf5f"/><circle cx="1404" cy="780" r="26" fill="#a3cc74"/><circle cx="1456" cy="782" r="24" fill="#7aa94c"/></g>')
    say = ('<g class="say" data-step="5"><path d="M1252 592 h242 a18 18 0 0 1 18 18 v62 a18 18 0 0 1 -18 18 h-136 l-26 30 l-4 -30 h-76 '
           'a18 18 0 0 1 -18 -18 v-62 a18 18 0 0 1 18 -18 Z" fill="#fffaf0" stroke="#e0c98f" stroke-width="2"/>'
           '<text x="1373" y="632" text-anchor="middle" font-family="Literata" font-size="25" font-weight="600" fill="#4f7a3a">Wir kriegen das hin,</text>'
           '<text x="1373" y="667" text-anchor="middle" font-family="Literata" font-size="25" font-weight="600" fill="#4f7a3a">wenn wir wollen.</text></g>')
    bird = lambda x, y, s: (f'<path d="M{x} {y} q{7 * s} {-7 * s} {14 * s} 0 q{7 * s} {-7 * s} {14 * s} 0" fill="none" stroke="#5b5346" '
                            f'stroke-width="3" stroke-linecap="round"/>')
    birds = f'<g class="birds" data-step="5">{bird(1080, 560, 1.2)}{bird(1124, 540, 1)}{bird(1046, 532, .9)}</g>'
    return tree + birds + say


def finale(page) -> str:
    cols = [("1", "Bäume kühlen, aber nicht überall", "0,39 von 0,83 Gha wiederbewaldbarer Fläche kühlen netto<br>→ pflanzen, wo die Albedo nicht dagegenhält"),
            ("2", "Bäume allein reichen nicht", "auf allen kühlenden Flächen 19 mK bis 2100<br>→ für 1,5 °C fehlen rund 262 Gt CO₂"),
            ("3", "DAC schließt die Lücke, aber spät", "6,9 Gt/a ab Ende der 2060er, dort, wo Speicher ist<br>→ den Overshoot um 2050 verhindert es nicht")]
    html = "".join(f'<div class="col rise"{"" if k == 0 else f" data-step={chr(34)}{k}{chr(34)}"}><h4><span class="big-n">{n}</span>{h}</h4><p>{p}</p></div>'
                   for k, (n, h, p) in enumerate(cols))
    return f'''<section class="slide finale" data-ch="dac" data-title="Auf dem Holzweg? Nein.">
  {_daylight(page)}
  <header class="sh"><h2>Auf dem Holzweg? Nein.</h2></header>
  <div class="body">
    <div class="cols3" style="margin-top:4px">{html}</div>
    <div class="outlook rise" data-step="3"><h4>Ausblick: was noch nicht drin ist</h4><p>Holznutzung (Bauholz statt Beton) · Lebensraum und Artenvielfalt · Kühlung durch Schatten und Verdunstung · Wasser und Boden</p></div>
    <p class="takeaway" data-step="4" style="--d:0; font-size:25px; margin-top:26px; align-self:flex-start">Also: Jetzt Bäume pflanzen, wo sie kühlen, und DAC früh hochfahren.</p>
  </div>
  <aside class="notes" data-n="0">
{NOTES}  </aside>
</section>
'''


def patch(page: str) -> str:
    head, sep, tail = page.partition("</style>")
    page = head + DARK_CSS + sep + tail
    page = _rep(page, "const EC_GAP_END = { steps: 0, option() { return EC_GAP.option(EC_GAP.steps); } };",
                DARK_EC + "const EC_GAP_END = { steps: 0, option() { return ecDark(EC_GAP.option(EC_GAP.steps)); } };")
    for t in ("DAC-Modell", "Optimierung von DAC"):
        page = _rep(page, f'<section class="slide" data-ch="dac" data-title="{t}">', f'<section class="slide dark" data-ch="dac" data-title="{t}">')
    m = _sec(page, "Auf dem Holzweg? Nein.")
    page = page[: m.start()] + finale(page) + page[m.end():]
    k = iter(range(1, 1000))
    page = re.sub(r'<aside class="notes" data-n="\d+">', lambda _: f'<aside class="notes" data-n="{next(k)}">', page)
    return page
