"""Slide "Strahlungsantrieb" rebuilt (2026-10-07): right only phi = phi_alpha + phi_CO2, the term being
explained highlighted with its expansion below; the picture on the left carries the explanation and
keeps one base drawing in all steps:
  step 0  energy balance: sunlight (short waves), reflection, heat radiation (long waves)
  step 1  albedo: the tree's area projected onto the top of the atmosphere (/ A_Erde), a cloud on the way
          up (tau_atm: part of the reflection change that arrives)
  step 2  CO2: albedo marks fade; a CO2 molecule lets the short waves through, another absorbs the long
          waves and emits them again in all directions, also back down
  step 3  takeaway
Applied after patch_merge."""
import math
import re

TITLE = "Strahlungsantrieb: Energiebilanz am Oberrand"

CSS = """
/* forcing slide: the term being explained is framed, the albedo marks fade when CO2 comes */
.fterm { display: inline-block; padding: 2px 10px 6px; border-radius: 10px; border: 2.5px solid transparent;
  transition: border-color .4s, background .4s, opacity .4s; }
.slide:has(.f-alb.shown) .fterm.alb { border-color: #d95f02; background: rgba(217, 95, 2, .07); }
.slide:has(.f-co2.shown) .fterm.alb { border-color: transparent; background: none; opacity: .45; }
.slide:has(.f-co2.shown) .fterm.co2 { border-color: #1b7837; background: rgba(27, 120, 55, .07); }
.slide:has(.f-co2.shown) .fexp.alb { opacity: .4; }
.fexp { transition: opacity .4s; }
svg:has(.f-co2.shown) .albmark { opacity: .18; transition: opacity .5s; }
/* last click: the two factors of the CO2 term framed, they come next */
.fstack { display: grid; }
.fstack > * { grid-area: 1 / 1; transition: opacity .5s; }
.f-box { opacity: 0; }
.f-box.shown { opacity: 1; }
.fstack:has(.f-box.shown) .fplain { opacity: 0; }
.fcheck { font: 700 30px/1 var(--sans); color: #d95f02; margin-left: 4px; opacity: 0; transition: opacity .4s; }
.slide:has(.f-co2.shown) .fcheck { opacity: 1; }
/* slide 18: the greenhouse drawing gives way to the charts */
.ghwrap { position: relative; width: 860px; height: 547px; align-self: start; }
.ghwrap > .chart { position: absolute; inset: 0; background: var(--paper); opacity: 0; transition: opacity .6s var(--ease); }
.ghwrap > .chart.shown { opacity: 1; }
.ghwrap > svg { transition: opacity .6s var(--ease); }
.ghwrap:has(> .chart.shown) > svg { opacity: 0; }
.f-box .fbox { border-color: #1b7837; border-width: 2.5px; border-radius: 6px; }
"""


def wave(x0, y0, x1, y1, lam, amp, tail=18):
    """Sine along the segment; straight for the last *tail* px so the arrowhead sits clean."""
    dx, dy = x1 - x0, y1 - y0
    n_len = math.hypot(dx, dy)
    ux, uy = dx / n_len, dy / n_len
    nx, ny = -uy, ux
    pts = []
    steps = max(2, int(n_len / 2.5))
    for i in range(steps + 1):
        s = n_len * i / steps
        a = amp * math.sin(2 * math.pi * s / lam) * min(1.0, max(0.0, (n_len - tail - s) / 10))
        pts.append(f"{x0 + ux * s + nx * a:.1f} {y0 + uy * s + ny * a:.1f}")
    return "M" + " L".join(pts)


def _anim(out, key):
    """Gentle motion for the forcing drawings (slides 17-19): radiation flows along its path, carbon
    arrows and cycles flow too, molecules jiggle, the sun turns."""
    def flow(m):
        tag = m.group(0)
        if tag.count(" L") > 20:
            topic = "t-sw" if ('#d9a441' in tag or '#d9822b' in tag) else "t-lw"
            return tag.replace("<path ", f'<path class="flow {topic}" ', 1)
        if ' A' in tag or ('#2e7d4f' in tag and ' C' in tag):
            return tag.replace("<path ", '<path class="flowc" ', 1)
        return tag
    out = re.sub(r'<path d="M[^"]*"[^>]*>', flow, out)
    k = iter(range(1000))
    out = re.sub(r'<g><line x1="([\d.]+)" y1="([\d.]+)"', lambda m: f'<g class="mol" style="--ph:-{(next(k) * 0.37) % 3:.2f}s"><line x1="{m.group(1)}" y1="{m.group(2)}"', out)
    out = out.replace('<g stroke="#d9a441" stroke-width="4" stroke-linecap="round"><line x1="46"', '<g class="rays" stroke="#d9a441" stroke-width="4" stroke-linecap="round"><line x1="46"', 1)
    return out.replace('<svg class="schema', f'<svg class="schema anim {key}', 1)


def co2r(x, y, s, angle):
    """A molecule turned by *angle* degrees around its centre."""
    return f'<g transform="rotate({angle} {x} {y})">' + co2(x, y, s) + '</g>'


def co2(x, y, s=1.0):
    r1, r2, d = 11 * s, 8 * s, 22 * s
    return (f'<g><line x1="{x - d + r2:.1f}" y1="{y}" x2="{x - r1:.1f}" y2="{y}" stroke="var(--ink)" stroke-width="3"/>'
            f'<line x1="{x + r1:.1f}" y1="{y}" x2="{x + d - r2:.1f}" y2="{y}" stroke="var(--ink)" stroke-width="3"/>'
            f'<circle cx="{x - d:.1f}" cy="{y}" r="{r2:.1f}" fill="var(--paper)" stroke="var(--ink)" stroke-width="3"/>'
            f'<circle cx="{x}" cy="{y}" r="{r1:.1f}" fill="#555"/>'
            f'<circle cx="{x + d:.1f}" cy="{y}" r="{r2:.1f}" fill="var(--paper)" stroke="var(--ink)" stroke-width="3"/></g>')


SW, LW = 16, 54  # wavelengths in the drawing: sunlight short, heat radiation long
Y_TOA, Y_GND = 74, 476

def _svg(variant: str) -> str:
    """The forcing drawing; the base is the same on both slides and sits at the same place.
    "frage" (slide 17): albedo marks, then CO2 only as a question (greenhouse effect);
    "treibhaus" (slide 18): the greenhouse effect in detail, no albedo marks."""
    base = f'''<svg class="schema" data-export="s_antrieb_v3" viewBox="0 0 880 560" style="width:860px; height:547px; overflow:visible; align-self:start" aria-label="Energiebilanz am Oberrand: Sonnenlicht kurzwellig, Wärmeabstrahlung langwellig; Albedo: Baumfläche auf den Oberrand projiziert, Wolke auf dem Weg nach oben; CO2 lässt kurzwelliges Licht durch, absorbiert langwellige Wärmestrahlung und strahlt sie in alle Richtungen wieder ab">
  <defs>
    <marker id="fx-y" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#d9a441"/></marker>
    <marker id="fx-o" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#d9822b"/></marker>
    <marker id="fx-r" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#b2182b"/></marker>
    <marker id="fx-m" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#8a7f6c"/></marker>
  </defs>
  <g font-family="IBM Plex Sans">
    <!-- base: the same in every step -->
    <g>
      <rect x="0" y="{Y_TOA}" width="880" height="{Y_GND - Y_TOA}" fill="#e3edf2"/>
      <line x1="0" y1="{Y_TOA}" x2="880" y2="{Y_TOA}" stroke="var(--muted)" stroke-width="2" stroke-dasharray="8 6"/>
      <text x="880" y="{Y_TOA - 12}" text-anchor="end" font-size="22" fill="var(--muted)">Oberrand der Atmosphäre</text>
      <rect x="0" y="{Y_GND}" width="880" height="34" fill="#d9cfb9"/>
      <line x1="0" y1="{Y_GND}" x2="880" y2="{Y_GND}" stroke="#8c7a58" stroke-width="3"/>
      <rect x="212" y="370" width="16" height="{Y_GND - 370}" fill="#3b3024"/>
      <circle cx="220" cy="328" r="58" fill="#6f8f55"/><circle cx="184" cy="372" r="40" fill="#7f9c64"/><circle cx="258" cy="374" r="38" fill="#5f7f48"/>
      <g stroke="#d9a441" stroke-width="4" stroke-linecap="round"><line x1="46" y1="6" x2="46" y2="14"/><line x1="46" y1="54" x2="46" y2="62"/><line x1="18" y1="34" x2="26" y2="34"/><line x1="66" y1="34" x2="74" y2="34"/><line x1="27" y1="15" x2="32" y2="20"/><line x1="60" y1="48" x2="65" y2="53"/><line x1="27" y1="53" x2="32" y2="48"/><line x1="60" y1="20" x2="65" y2="15"/></g>
      <circle cx="46" cy="34" r="17" fill="#e8b84f"/>
      <path d="{wave(70, 58, 196, 280, SW, 6)}" stroke="#d9a441" stroke-width="3.5" fill="none" marker-end="url(#fx-y)"/>
      <text x="14" y="236" font-size="22" fill="var(--ink-2)">Sonnenlicht</text>
      <text x="14" y="262" font-size="18" fill="var(--muted)">kurzwellig</text>
      <path d="{wave(236, 272, 352, Y_TOA + 4, SW, 6)}" stroke="#d9822b" stroke-width="3.5" stroke-dasharray="7 5" fill="none" marker-end="url(#fx-o)"/>
      <text x="352" y="128" font-size="22" fill="var(--ink-2)">Reflexion</text>
      <path d="{wave(770, Y_GND - 4, 770, Y_TOA + 4, LW, 13)}" stroke="#b2182b" stroke-width="3.5" fill="none" marker-end="url(#fx-r)"/>
      <text x="744" y="410" text-anchor="end" font-size="22" fill="var(--ink-2)">Wärme-</text>
      <text x="744" y="436" text-anchor="end" font-size="22" fill="var(--ink-2)">abstrahlung</text>
      <text x="744" y="460" text-anchor="end" font-size="18" fill="var(--muted)">langwellig</text>
    </g>
'''
    alb = f'''    <!-- step 1: albedo -->
    <g class="albmark"><g class="pop f-alb" data-step="1">
      <polygon points="144,{Y_TOA} 296,{Y_TOA} 296,330 144,330" fill="#d95f02" opacity=".10"/>
      <line x1="144" y1="{Y_TOA}" x2="144" y2="372" stroke="#d95f02" stroke-width="2" stroke-dasharray="5 5"/>
      <line x1="296" y1="{Y_TOA}" x2="296" y2="372" stroke="#d95f02" stroke-width="2" stroke-dasharray="5 5"/>
      <line x1="144" y1="{Y_TOA}" x2="296" y2="{Y_TOA}" stroke="#d95f02" stroke-width="6" stroke-linecap="round"/>
      <text x="220" y="{Y_TOA - 12}" text-anchor="middle" font-size="22" font-weight="600" fill="#b04a00">÷ A<tspan font-size="15" dy="5">Erde</tspan></text>
      <text x="220" y="{Y_TOA + 26}" text-anchor="middle" font-size="18" fill="#b04a00">W je m² Erde</text>
      <text x="306" y="{Y_GND - 52}" font-size="21" font-weight="600" fill="#7a5b2e">ΔQ̇<tspan font-size="15" dy="5">Baum</tspan></text>
      <text x="306" y="{Y_GND - 28}" font-size="18" fill="var(--muted)">mehr absorbiert [W]</text>
      <g transform="translate(316 196)">
        <circle cx="0" cy="0" r="20" fill="#fff"/><circle cx="24" cy="-8" r="24" fill="#fff"/><circle cx="50" cy="2" r="18" fill="#fff"/>
        <rect x="-4" y="0" width="58" height="18" fill="#fff"/>
      </g>
      <path d="M352 214 l38 18" stroke="#d9822b" stroke-width="2.5" stroke-dasharray="3 5" fill="none" marker-end="url(#fx-o)"/>
      <text x="398" y="246" font-size="21" font-weight="600" fill="#7a5b2e">τ<tspan font-size="15" dy="5">atm</tspan><tspan dy="-5"> = 0,854</tspan></text>
      <text x="398" y="270" font-size="18" fill="var(--muted)">kommt oben an</text>
    </g></g>
'''
    frage = f'''    <!-- step 2: CO2 as a question -->
    <g class="pop f-co2" data-step="2">
      <ellipse cx="610" cy="235" rx="140" ry="74" fill="#b2182b" fill-opacity=".06" stroke="#b2182b" stroke-width="2" stroke-dasharray="6 6"/>
      {co2(530, 220)}{co2(626, 190)}{co2(590, 270)}{co2(684, 252)}
      <text x="704" y="214" font-size="52" font-weight="600" fill="#b2182b">?</text>
      <text x="470" y="128" font-size="25" font-weight="600" fill="#b2182b">Treibhauseffekt</text>
      <text x="470" y="154" font-size="19" fill="var(--ink-2)">CO₂ hält Wärme in der Atmosphäre</text>
    </g>
'''
    treibhaus = f'''    <!-- step 2: CO2 -->
    <g class="pop" style="--d:300">
      {co2(104, 118)}
      <text x="142" y="124" font-size="18" fill="var(--ink-2)">lässt durch</text>
      {co2(770, 250, 1.15)}
      <path d="{wave(750, 236, 690, 180, LW / 2.2, 6, 14)}" stroke="#b2182b" stroke-width="3" fill="none" marker-end="url(#fx-r)"/>
      <path d="{wave(792, 236, 852, 180, LW / 2.2, 6, 14)}" stroke="#b2182b" stroke-width="3" fill="none" marker-end="url(#fx-r)"/>
      <path d="{wave(750, 266, 690, 324, LW / 2.2, 6, 14)}" stroke="#b2182b" stroke-width="3" fill="none" marker-end="url(#fx-r)"/>
      <path d="{wave(792, 266, 852, 324, LW / 2.2, 6, 14)}" stroke="#b2182b" stroke-width="3" fill="none" marker-end="url(#fx-r)"/>
      <text x="436" y="166" font-size="21" font-weight="600" fill="#1b5e33">CO₂ absorbiert</text>
      <text x="436" y="192" font-size="21" font-weight="600" fill="#1b5e33">langwellige Strahlung</text>
      <text x="436" y="218" font-size="21" font-weight="600" fill="#1b5e33">und strahlt sie in alle</text>
      <text x="436" y="244" font-size="21" font-weight="600" fill="#1b5e33">Richtungen wieder ab</text>
      <text x="676" y="356" text-anchor="end" font-size="18" fill="var(--ink-2)">auch zurück zur Erde</text>
      <text x="436" y="300" font-size="21" font-weight="600" fill="#b2182b">Mehr CO₂: mehr Wärme</text>
      <text x="436" y="326" font-size="21" font-weight="600" fill="#b2182b">bleibt in der Atmosphäre</text>
    </g>
'''
    body = base + (alb + frage if variant == "frage" else treibhaus)
    return body + "  </g>\n</svg>"


RIGHT = r'''<div style="display:flex; flex-direction:column; gap:10px; align-self:start">
      <div class="eq tex" style="font-size:36px; text-align:left; white-space:nowrap">$\varphi(t) =$ <span class="fterm alb">$\aq{\varphi_\alpha}(t)$<span class="fcheck">✓</span></span> $+$ <span class="fterm co2">$\cq{\varphi_{\mathrm{CO_2}}}(t)$</span></div>
      <p style="font:400 19px/1.4 var(--sans); color:var(--ink-2); margin:-6px 0 6px">Strahlungsantrieb: Änderung der Energiebilanz am Oberrand in W je m² Erde; positiv wärmt, negativ kühlt.</p>
      <div class="fexp alb"><div class="rise f-alb" data-step="1" style="--d:500"><div class="eq tex" style="font-size:24px; text-align:left">$$\aq{\varphi_\alpha}(t) = \pc{\tau_{\mathrm{atm}}}\,\bq{\Delta\dot Q_{\mathrm{Baum}}}(t)\,/\,\pc{A_{\mathrm{Erde}}}$$</div><dl class="legend sm tex"><dt>$\pc{\tau_{\mathrm{atm}}}$</dt><dd>Anteil der Reflexionsänderung, der am Oberrand ankommt — 0,854</dd><dt>$\bq{\Delta\dot Q_{\mathrm{Baum}}}$</dt><dd>zusätzlich absorbierte Strahlung des Baums [W] — Kapitel Bäume</dd><dt>$\pc{A_{\mathrm{Erde}}}$</dt><dd>Erdoberfläche — 5,1 · 10¹⁴ m²</dd></dl></div></div>
    </div>'''

NOTES = '''
    <p>Im Kapitel Bäume hatten wir zwei Wirkungen in zwei Einheiten: Kilogramm CO₂ und Watt Strahlung. Für das Klima zählen beide über dieselbe Größe: die Energiebilanz der Erde am Oberrand der Atmosphäre. Herein kommt Sonnenlicht, kurzwellig; hinaus gehen das reflektierte Licht und die Wärmestrahlung der Erde, langwellig. Die Änderung dieser Bilanz in Watt je Quadratmeter Erde heißt Strahlungsantrieb, rechts φ. Er hat zwei Teile: Albedo und CO₂.</p>
    <p>Klick: zuerst die Albedo, der einfache Teil. Unter dem Baum wird mehr Sonnenlicht absorbiert: ΔQ̇_Baum, in Watt, aus dem Kapitel Bäume. Am Oberrand zählt das je Quadratmeter Erde, also teilen wir durch die Erdoberfläche. Und auf dem Weg nach oben nehmen Wolken, Wasserdampf und Aerosole einen Teil der Reflexionsänderung weg: Oben kommen 85 Prozent an, τ_atm.</p>
    <p>Klick: jetzt das CO₂. Hier stellen wir erst die Frage. CO₂ macht etwas in der Atmosphäre, das mehr Energie in ihr hält: der Treibhauseffekt. Nimmt der Baum CO₂ heraus, wird weniger gehalten, es kühlt. Wie das genau funktioniert und wie viel es ausmacht, zeigen die nächsten Folien.</p>
    <p class="q">Falls Fragen kommen — τ_atm = 0,854: ΔQ̇_Baum gilt an der Oberfläche, der Weg nach unten (Wolken) steckt schon in der gemessenen Einstrahlung. Auf dem Weg nach oben absorbieren oder streuen Wolken, Wasserdampf und Aerosole einen Teil: Reflektiert die Oberfläche 10 W weniger, verlassen am Oberrand nur etwa 8,5 W weniger die Erde. Globaler Mittelwert nach Lenton &amp; Vaughan (2009), auch bei Cherubini et al. (2012): Wurzel der zweiseitigen Transmission 0,730 bei klarem Himmel (Lacis &amp; Hansen 1974). Genauer wären Strahlungs-Kernels je Ort und Monat (Bright &amp; O'Halloran 2019). Die Verdunstung ist an dieser Grenze ein interner Fluss und kein Antrieb (Backup „Und die Verdunstung?“). Kurz- und langwellig: Sonnenlicht hat sein Maximum bei etwa 0,5 µm, die Wärmestrahlung der Erde bei etwa 10 µm; CO₂ absorbiert vor allem um 15 µm.</p>
  '''


def patch(page: str) -> str:
    head, sep, tail = page.partition("</style>")
    page = head + CSS + sep + tail
    m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(TITLE) + r'"[^>]*>.*?</section>', page, flags=re.S)
    assert m
    sec = m.group(0)
    body = re.search(r'<div class="body">.*?\n  </div>\n  <p class="src">', sec, flags=re.S)
    assert body
    new_body = ('<div class="body">\n    ' + ROAD_HIDDEN + '\n    <div style="display:grid; grid-template-columns:860px 1fr; gap:34px; flex:1; min-height:0; align-items:center">\n    '
                + _anim(_svg("frage"), "s17") + '\n    ' + RIGHT + '\n    </div>\n  </div>\n  <p class="src">')
    sec = sec[: body.start()] + new_body + sec[body.end():]
    # one-line title, so the drawing sits exactly where it sits on the next slide
    sec = sec.replace('<h2>Strahlungsantrieb: die Energiebilanz am Oberrand der Atmosphäre</h2>', '<h2>Strahlungsantrieb: Energiebilanz am Oberrand</h2>', 1)
    sec = re.sub(r'(<aside class="notes" data-n="\d+">).*?(</aside>)', lambda n: n.group(1) + NOTES + n.group(2), sec, flags=re.S)
    page = page[: m.start()] + sec + page[m.end():]
    return _co2_slides(page)


def _sec(page, title):
    m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(title) + r'"[^>]*>.*?</section>\n\n?', page, flags=re.S)
    assert m, title
    return m


def _edit(page, title, pairs):
    m = _sec(page, title)
    sec = m.group(0)
    for a, b in pairs:
        assert a in sec, (title, a[:60])
        sec = sec.replace(a, b, 1)
    return page[: m.start()] + sec + page[m.end():]


EPS = r"\cq{\varepsilon_{\mathrm{CO_2}}}(t)"
DM = r"\cq{\Delta m_{\mathrm{CO_2}}}(t)"
GREY_EPS = r"\textcolor{b5ada0}{\varepsilon_{\mathrm{CO_2}}(t)}"
GREY_DM = r"\textcolor{b5ada0}{\Delta m_{\mathrm{CO_2}}(t)}"
PHI = r"\cq{\varphi_{\mathrm{CO_2}}}(t) = "
def _word(word, sym, cur, swap):
    """One factor of the word formula: the word, replaced by its symbol once the slide introduces it (.fswap)."""
    cls = "fw" + (" cur" if cur else "") + (" swaps" if swap else "")
    if sym is None:
        return '<span class="' + cls + '"><span class="w">' + word + '</span></span>'
    return ('<span class="' + cls + '"><span class="w">' + word + '</span><span class="s tex">$' + sym + '$</span></span>')


EPS_SYM = r"\cq{\varepsilon_{\mathrm{CO_2}}}(t)"
DM_SYM = r"\cq{\Delta m_{\mathrm{CO_2}}}(t)"
PHI_TEX = '<span class="tex">$' + r"\cq{\varphi_{\mathrm{CO_2}}}(t) =" + '$</span>'
EPS_ROAD = ('<span class="froad late">' + PHI_TEX + _word("Stärke des Antriebs", EPS_SYM, True, True) + '<span class="fx">×</span>'
            + _word("verbleibende CO₂-Menge", None, False, False) + '</span>')
# slide 17 carries the same signpost invisibly, so the drawing starts at the same height as on slide 18
ROAD_HIDDEN = '<div class="road" style="visibility:hidden" aria-hidden="true">' + EPS_ROAD + '</div>'



def _co2_slides(page):
    """After slide 17 the CO2 term is the base: first epsilon (where it comes from), then delta m."""
    irf_old_road = ('<span>CO₂-Term, Schritt 1: die CO₂-Änderung der Atmosphäre</span><span class="tex">$\\textcolor{b5ada0}{\\varphi(t) = '
                    '\\varepsilon_{\\mathrm{CO_2}}(t)}\\,\\boxed{\\cq{\\Delta m_{\\mathrm{CO_2}}}(t)} \\textcolor{b5ada0}{{}+ \\varphi_\\alpha(t)}$</span>')
    irf_new_road = ('<span class="froad">' + PHI_TEX + '<span class="fw done"><span class="tex">$' + EPS_SYM + '$</span></span><span class="fx">×</span>'
                    + _word("verbleibende CO₂-Menge", DM_SYM, True, True) + '</span>')
    page = _edit(page, "Impulsantwort des Kohlenstoffkreislaufs", [
        ('<div class="road rise" style="--d:200">', '<div class="road">'),
        (irf_old_road, irf_new_road),
        ("<p>Oben die Gleichung von eben: Wir arbeiten jetzt am CO₂-Term und beginnen mit dem zweiten Faktor, der CO₂-Änderung der Atmosphäre Δm_CO₂ — umrahmt.</p>",
         "<p>Oben der CO₂-Term: Den Antrieb je Kilogramm ε_CO₂ haben wir. Jetzt der zweite Faktor, die CO₂-Änderung der Atmosphäre Δm_CO₂ — umrahmt.</p>"),
    ])
    page = _edit(page, "Impulsantwort auf die CO₂-Aufnahme eines Baums", [(irf_old_road, irf_new_road)])
    eps_old_road = ('<div class="road"><span>CO₂-Term, Schritt 2: der Antrieb je kg CO₂</span><span class="tex">$\\textcolor{b5ada0}{\\varphi(t) =}\\ '
                    '\\boxed{\\cq{\\varepsilon_{\\mathrm{CO_2}}}(t)}\\,\\cq{\\Delta m_{\\mathrm{CO_2}}}(t) \\textcolor{b5ada0}{{}+ \\varphi_\\alpha(t)}$</span>')
    eps_new_road = '<div class="road rise" style="--d:200">' + EPS_ROAD
    page = _edit(page, "Strahlungsantrieb von CO₂", [
        (eps_old_road, eps_new_road),
        ("<dd>CO₂-Änderung der Atmosphäre durch den Baum (Vorfolie)</dd>", "<dd>CO₂-Änderung der Atmosphäre durch den Baum (nächste Folien)</dd>"),
        ("<p>Oben wieder die Gleichung: Δm_CO₂ haben wir jetzt. Es fehlt der erste Faktor des CO₂-Terms, der Antrieb je Kilogramm ε_CO₂ — umrahmt.</p>",
         "<p>Oben der CO₂-Term von eben, unsere Basis für die nächsten Folien. Zuerst der erste Faktor, der Antrieb je Kilogramm ε_CO₂ — umrahmt.</p>"),
        ("<p>Die zweite Frage: Wie stark", "<p>Die erste Frage: Wie stark"),
        ("und mal der CO₂-Änderung des Baums aus der Impulsantwort", "und mal der CO₂-Änderung des Baums, die wir als Nächstes bestimmen"),
    ])
    # epsilon before the two impulse-response slides
    eps = _sec(page, "Strahlungsantrieb von CO₂")
    sec = eps.group(0)
    page = page[: eps.start()] + page[eps.end():]
    anchor = _sec(page, "Impulsantwort des Kohlenstoffkreislaufs")
    page = page[: anchor.start()] + sec + page[anchor.start():]
    # total forcing: albedo first, as on slide 17
    page = _edit(page, "Gesamter Strahlungsantrieb je Baum", [
        ("Eigene Rechnung: CO₂-Antrieb wie auf der Vorfolie;", "Eigene Rechnung: CO₂-Antrieb wie auf den Folien „Strahlungsantrieb von CO₂“ und „Impulsantwort“;"),
        (r"$\boxed{\varphi(t) = \cq{\varepsilon_{\mathrm{CO_2}}}(t)\,\cq{\Delta m_{\mathrm{CO_2}}}(t) + \aq{\varphi_\alpha}(t)}$",
         r"$\boxed{\varphi(t) = \aq{\varphi_\alpha}(t) + \cq{\varepsilon_{\mathrm{CO_2}}}(t)\,\cq{\Delta m_{\mathrm{CO_2}}}(t)}$"),
        (r"$$\varphi(t) = \cq{\varphi_{\mathrm{CO_2}}}(t) + \aq{\varphi_\alpha}(t)$$", r"$$\varphi(t) = \aq{\varphi_\alpha}(t) + \cq{\varphi_{\mathrm{CO_2}}}(t)$$"),
        ("<dt>$\\cq{\\varphi_{\\mathrm{CO_2}}}$</dt><dd>CO₂-Antrieb, < 0, kühlt (grün; Folie „Strahlungsantrieb von CO₂“)</dd><dt>$\\aq{\\varphi_\\alpha}$</dt><dd>Albedo-Antrieb, > 0, wärmt (orange; Folie „Strahlungsantrieb“)</dd>",
         "<dt>$\\aq{\\varphi_\\alpha}$</dt><dd>Albedo-Antrieb, > 0, wärmt (orange; Folie „Strahlungsantrieb“)</dd><dt>$\\cq{\\varphi_{\\mathrm{CO_2}}}$</dt><dd>CO₂-Antrieb, < 0, kühlt (grün; Folie „Strahlungsantrieb von CO₂“)</dd>"),
    ])
    page = _greenhouse(page)
    main, sep, backup = page.partition("<!-- BACKUP:BEGIN -->")
    n = iter(range(1, 1000))
    main = re.sub(r'<aside class="notes" data-n="\d+">', lambda m: f'<aside class="notes" data-n="{next(n)}">', main)
    return main + sep + backup


EPS_NOTES_HEAD = (
    "    <p>Auf der letzten Folie haben wir gesagt: CO₂ hält Wärme in der Atmosphäre, der Treibhauseffekt. Jetzt genauer, "
    "dasselbe Bild. Das Sonnenlicht ist kurzwellig, CO₂ lässt es durch. Die Erde strahlt Wärme ab, langwellig; diese Strahlung "
    "absorbiert CO₂ und strahlt sie in alle Richtungen wieder ab, auch zurück zur Erde. Mehr CO₂ heißt: mehr Wärme bleibt in "
    "der Atmosphäre, die Bilanz am Oberrand verschiebt sich. Wie stark, rechnen Strahlungstransfer-Modelle aus.</p>\n"
    "    <p>Klick: genau das zeigt die Kurve links.</p>\n")

def loop(cx, cy, rx, ry, color, marker):
    """A round double arrow (cycle): two arcs, each with its own arrowhead."""
    def p(deg):
        t = math.radians(deg)
        return f"{cx + rx * math.cos(t):.1f} {cy + ry * math.sin(t):.1f}"
    arc = lambda a0, a1: f'<path d="M{p(a0)} A{rx} {ry} 0 0 1 {p(a1)}" stroke="{color}" stroke-width="4" fill="none" marker-end="url(#{marker})"/>'
    return arc(196, 334) + arc(16, 154)


def _cc_svg() -> str:
    """Slide 19: the drawing of slides 17/18 (same base, same place), radiation faded; ocean and land take up
    part of an extra tonne of CO2."""
    base = _svg("treibhaus")
    base = base[: base.index("    <!-- step 2: CO2 -->")]
    base = base.replace('class="schema" data-export="s_antrieb_v3"', 'class="schema cc" data-export="s_kreislauf"', 1)
    G = Y_GND
    extra = f'''    <g>
      <rect x="0" y="{G + 2}" width="500" height="58" fill="#d9cfb9"/>
      <rect x="0" y="{G + 60}" width="500" height="80" fill="#a39684"/>
      <path d="M0 {G + 60} H500" stroke="#8c7f6c" stroke-width="2"/>
      <rect x="500" y="{G - 2}" width="380" height="14" fill="#e3edf2"/>
      <path d="M500 {G} q15 8 30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t20 0 L880 {G + 140} L500 {G + 140} Z" fill="#7fb0cc"/>
      <rect x="500" y="{G + 60}" width="380" height="80" fill="#5f93b3"/>
      <path d="M500 {G} q15 8 30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t20 0" stroke="#4f86a6" stroke-width="2.5" fill="none"/>
      <text x="868" y="{G + 24}" text-anchor="end" font-size="22" font-weight="600" fill="#fff">Ozean</text>
      <text x="40" y="{G + 24}" font-size="22" font-weight="600" fill="#5b4a2e">Land</text>
    </g>
    <g class="pop" style="--d:200">
      <ellipse cx="470" cy="200" rx="96" ry="54" fill="#8c6d5a" fill-opacity=".10" stroke="#8c6d5a" stroke-width="2" stroke-dasharray="6 6"/>
      {co2(432, 186)}{co2(510, 176)}{co2(470, 226)}
      <text x="470" y="128" text-anchor="middle" font-size="25" font-weight="600" fill="#8c6d5a">+1 t CO₂</text>
    </g>
    <g class="pop" data-step="1">
      {loop(410, 408, 50, 50, "#5f7f48", "fx-k")}
      {loop(660, G + 64, 72, 48, "#ffffff", "fx-w")}
      <text x="660" y="{G + 132}" text-anchor="middle" font-size="18" font-weight="600" fill="#fff">Kreislauf mit der Tiefsee</text>
      <path d="M470 262 C 462 300 446 330 430 352" stroke="#2e7d4f" stroke-width="4.5" fill="none" marker-end="url(#fx-g)"/>
      <path d="M520 248 C 580 310 640 380 670 {G - 16}" stroke="#2e7d4f" stroke-width="4.5" fill="none" marker-end="url(#fx-g)"/>
      <text x="470" y="400" font-size="20" font-weight="600" fill="#1b5e33">Land</text>
      <text x="470" y="426" font-size="20" font-weight="600" fill="#1b5e33">nimmt auf</text>
      <text x="712" y="410" font-size="20" font-weight="600" fill="#1b5e33">Ozean</text>
      <text x="712" y="436" font-size="20" font-weight="600" fill="#1b5e33">nimmt auf</text>
    </g>
'''
    defs = ('<marker id="fx-k" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#5f7f48"/></marker>'
            '<marker id="fx-w" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#ffffff"/></marker>'
            '<marker id="fx-g" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#2e7d4f"/></marker>'
            '<marker id="fx-b" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#7fb0cc"/></marker>'
            '<marker id="fx-l" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#a9bc8f"/></marker>')
    base = base.replace("</defs>", defs + "</defs>", 1)
    # marker ids must be unique per slide copy of the drawing
    base = re.sub(r'id="fx-(\w)"', r'id="cc-\1"', base).replace("url(#fx-", "url(#cc-")
    extra = extra.replace("url(#fx-", "url(#cc-")
    return _anim(base + extra + "  </g>\n</svg>", "s19")


CC_CSS = """
/* slide 19: the radiation of the base drawing steps back, the carbon cycle is in front */
svg.cc > g > g:first-of-type > path[marker-end] { opacity: .2; }
svg.cc > g > g:first-of-type > text:not(:nth-of-type(1)) { opacity: 0; }
"""


def _cycle(page):
    head, sep, tail = page.partition("</style>")
    page = head + CC_CSS + sep + tail
    m = _sec(page, "Impulsantwort des Kohlenstoffkreislaufs")
    sec = m.group(0)
    road = re.search(r'<div class="road[^"]*"[^>]*>.*?</div>', sec).group(0).replace('<div class="road rise" style="--d:200">', '<div class="road">')
    chart = re.search(r'<div class="chart"[^>]*data-chart="k3"[^>]*></div>', sec).group(0)
    chart = re.sub(r'data-slot-steps="[^"]*"', 'data-slot-steps="0,1"', chart).replace(' style="height:100%"', '').replace('data-chart="k3"', 'data-chart="k3s"')
    chart = chart.replace('<div class="chart"', '<div class="chart" style="height:270px; margin-top:4px"', 1)
    eq = re.search(r'<div class="eq tex"[^>]*>\$\$\\rq\{g_C\}.*?</div>', sec).group(0).replace('font-size:23px', 'font-size:22px')
    dl = re.search(r'<dl class="legend sm tex[^"]*"[^>]*>.*?</dl>', sec).group(0)
    dl = re.sub(r'<dl class="legend sm tex[^"]*"[^>]*>', '<dl class="legend sm tex" style="margin-left:44px">', dl)
    eq = eq.replace('<div class="eq tex"', '<div class="eq tex" style="margin:4px 0 0 44px; text-align:left"', 1) if 'style=' not in eq[:30] else re.sub(r'style="[^"]*"', 'style="font-size:22px; margin:4px 0 0 44px; text-align:left"', eq, count=1)
    right = ('<div style="display:flex; flex-direction:column; gap:14px; align-self:start">'
             '<div class="rise" style="--d:300"><p class="ghs"><b>1</b>Zusatzemission: 1 t CO₂ kommt in die Atmosphäre.</p></div>'
             '<div class="rise" data-step="1" style="--d:200"><p class="ghs"><b>2</b>Natürliche Kreisläufe (runde Pfeile) tauschen ständig CO₂ aus. Kommt eine Tonne dazu, '
             'nehmen Land und Ozean über die Jahre einen Teil davon auf.</p></div>'
             '<div class="rise" data-step="2" style="--d:200"><p class="ghs"><b>3</b>Wie schnell? Nach 20 Jahren sind noch 60 % in der Atmosphäre, '
             'nach 100 Jahren 41 %.</p>'
             '<div class="rise" data-step="2" style="--d:0">' + chart.replace('<div class="chart"', '<div class="chart" data-step="2"', 1) + '</div></div>'
             '<div class="rise" data-step="3" style="--d:200"><p class="ghs"><b>4</b>Entnahme genauso, spiegelbildlich: Ozean und Land geben CO₂ ab.</p></div>'
             '<div class="rise epsdef fswap" data-step="4" style="--d:200"><p>Verbleibende CO₂-Menge = <span class="tex">$\\cq{\\Delta m_{\\mathrm{CO_2}}}$</span> [kg]</p></div>'
             '</div>')
    body = ('<div class="body">\n    ' + road + '\n    <div style="display:grid; grid-template-columns:860px 1fr; gap:34px; flex:1; min-height:0; align-items:center">'
            '<div class="ghwrap">' + _cc_svg() + '</div>' + right + '</div>\n  </div>\n  <p class="src">')
    b = re.search(r'<div class="body">.*?\n  </div>\n  <p class="src">', sec, flags=re.S)
    sec = sec[: b.start()] + body + sec[b.end():]
    sec = sec.replace('<h2>Impulsantwort des Kohlenstoffkreislaufs: Zusatzemission und Entnahme</h2>', '<h2>Kohlenstoffkreislauf: Ozean und Land</h2>', 1)
    n = re.search(r'<aside class="notes" data-n="\d+">\n?', sec)
    sec = sec[: n.end()] + IRF_NOTES_HEAD + sec[n.end():]
    sec = sec.replace("</aside>", IRF_NOTES_TAIL + "  </aside>", 1)
    return page[: m.start()] + sec + page[m.end():]


IRF_NOTES_HEAD = (
    "    <p>Jetzt der zweite Faktor. Wie viel Wärme das CO₂ des Baums insgesamt ausmacht, hängt davon ab, wie viel davon in der "
    "Atmosphäre bleibt. Dasselbe Bild wie eben, die Strahlung tritt zurück, dazu Meer und Land. Eine Tonne CO₂ kommt in die Atmosphäre.</p>\n"
    "    <p>Klick: Die runden Pfeile sind die natürlichen Kohlenstoffkreisläufe: Die Atmosphäre tauscht ständig CO₂ mit Land und Ozean aus, der Ozean mit der Tiefsee. Kommt eine "
    "Tonne dazu, nehmen Ozean und Land über die Jahre einen Teil davon auf.</p>\n"
    "    <p>Klick: rechts die Kurve dazu, die Impulsantwort g_C — nach 20 Jahren sind noch 60 % in der Luft, nach 100 Jahren gut 40 %, ein Fünftel bleibt sehr lange.</p>\n"
    "    <p>Klick: Für eine Entnahme gilt dasselbe, spiegelbildlich. Ozean und Land geben dann CO₂ ab.</p>\n")

IRF_NOTES_TAIL = (
    "    <p>Für den Baum heißt das: Jede Jahresaufnahme ist so eine kleine Entnahme, die nach dieser Kurve abklingt; aufsummiert "
    "fehlt der Atmosphäre 2100 gut die Hälfte dessen, was der Baum aufgenommen hat, in Aachen 84 von 163 kg CO₂ "
    "(Backup „Impulsantwort auf die CO₂-Aufnahme eines Baums“).</p>\n")


def _gh_svg() -> str:
    """Slide 18: the greenhouse effect step by step on the drawing of slide 17 (same base, same place)."""
    base = _svg("treibhaus")
    base = base[: base.index("    <!-- step 2: CO2 -->")]
    steps = f'''    <g class="pop" data-step="1">
      {co2(104, 118)}
      <text x="142" y="124" font-size="20" font-weight="600" fill="#a8740b">durchlässig</text>
    </g>
    <g class="gh2"><g class="pop" data-step="2">
      {co2(770, 250, 1.15)}
      <path d="{wave(750, 236, 690, 180, LW / 2.2, 6, 14)}" stroke="#b2182b" stroke-width="3" fill="none" marker-end="url(#fx-r)"/>
      <path d="{wave(792, 236, 852, 180, LW / 2.2, 6, 14)}" stroke="#b2182b" stroke-width="3" fill="none" marker-end="url(#fx-r)"/>
      <path d="{wave(750, 266, 690, 324, LW / 2.2, 6, 14)}" stroke="#b2182b" stroke-width="3" fill="none" marker-end="url(#fx-r)"/>
      <path d="{wave(792, 266, 852, 324, LW / 2.2, 6, 14)}" stroke="#b2182b" stroke-width="3" fill="none" marker-end="url(#fx-r)"/>
      <text x="470" y="300" font-size="20" font-weight="600" fill="#b2182b">absorbiert</text>
      <text x="470" y="326" font-size="20" font-weight="600" fill="#b2182b">→ emittiert in</text>
      <text x="470" y="352" font-size="20" font-weight="600" fill="#b2182b">alle Richtungen</text>
    </g></g>
    <g class="pop gh3" data-step="3">
      <defs><linearGradient id="gh-tg" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#d6604d"/><stop offset="1" stop-color="#4f86a6"/></linearGradient></defs>
      <rect x="392" y="150" width="10" height="316" rx="5" fill="url(#gh-tg)"/>
      <text x="382" y="166" text-anchor="end" font-size="18" font-weight="600" fill="#4f86a6">kalt</text>
      <text x="382" y="462" text-anchor="end" font-size="18" font-weight="600" fill="#d6604d">warm</text>
      {co2r(440, 410, .6, -25)}
      {co2r(440, 330, .6, 15)}{co2r(495, 330, .6, -35)}
      {co2r(440, 250, .6, 40)}{co2r(495, 250, .6, -10)}{co2r(550, 250, .6, 25)}
      {co2r(440, 170, .6, -20)}{co2r(495, 170, .6, 35)}{co2r(550, 170, .6, -40)}{co2r(605, 170, .6, 10)}
      <path d="{wave(440, 472, 440, 419, 22, 5, 0)}" stroke="#b2182b" stroke-width="3" fill="none"/>
      <path d="{wave(495, 472, 495, 339, 22, 5, 0)}" stroke="#b2182b" stroke-width="3" fill="none"/>
      <path d="{wave(550, 472, 550, 259, 22, 5, 0)}" stroke="#b2182b" stroke-width="3" fill="none"/>
      <path d="{wave(605, 472, 605, 179, 22, 5, 0)}" stroke="#b2182b" stroke-width="3" fill="none"/>
      <path d="{wave(605, 161, 605, 80, 22, 4, 12)}" stroke="#4f86a6" stroke-width="1.8" fill="none" marker-end="url(#fx-r)"/>
      <text x="628" y="112" font-size="18" font-weight="600" fill="#6a3d9a">nur von oben</text>
      <text x="628" y="134" font-size="18" font-weight="600" fill="#6a3d9a">ins All:</text>
      <text x="628" y="156" font-size="18" font-weight="600" fill="#6a3d9a">kalt, schwach</text>
    </g>
'''
    out = base + steps + "  </g>\n</svg>"
    out = _anim(out, "s18")
    # own marker ids: the same ids on slide 17 would win, and markers of a hidden slide do not render
    return re.sub(r'id="fx-(\w)"', r'id="gh-\1"', out).replace("url(#fx-", "url(#gh-")


GH_RIGHT = r'''<div class="ghsteps" style="display:flex; flex-direction:column; gap:12px; align-self:start; min-width:0">
      <div class="rise" data-step="1" style="--d:200"><p class="ghs"><b style="background:#a8740b">1</b>Sonnenlicht, kurzwellig (~0,5 µm)<br>→ CO₂ ist dafür durchlässig</p></div>
      <div class="rise" data-step="2" style="--d:200"><p class="ghs"><b style="background:#b2182b">2</b>Wärmestrahlung der Erde, langwellig (~10 µm)<br>→ CO₂ absorbiert (Bande um 15 µm)<br>→ emittiert in alle Richtungen, auch zur Erde</p></div>
      <div class="rise" data-step="3" style="--d:200"><p class="ghs"><b style="background:#6a3d9a">3</b>Mehr CO₂<br>→ Wärmestrahlung wird öfter wieder geschluckt<br>→ sie entkommt erst aus größerer Höhe ins All<br>→ dort ist es kälter: kältere Luft strahlt weniger ab</p></div>
      <div class="rise epsdef fswap" data-step="4" style="--d:200"><p>Stärke des Antriebs = <span class="tex">$\cq{\varepsilon_{\mathrm{CO_2}}}$</span>: Netto-Änderung der Energiebilanz am Oberrand je kg CO₂ [W/m² je kg]<br>→ ganzer Treibhauseffekt in einer Zahl</p></div>
      <div class="rise" data-step="5" style="--d:200"><p class="ghs"><b style="background:#1b7837">!</b>Aber: <span class="tex">$\cq{\varepsilon_{\mathrm{CO_2}}}$</span> ist kein fester Wert<br>→ sinkt mit dem Hintergrund-CO₂ c (Grafik)<br>→ Bande schon weitgehend gesättigt</p>
        <div class="eq tex" style="font-size:23px; text-align:left; margin:2px 0 0 44px">$$\cq{\varepsilon_{\mathrm{CO_2}}}(t) = \frac{\pc{5{,}35}\,\mathrm{W/m^2}}{\pc{k}\,c(t)}$$</div></div>
    </div>'''

GH_CHART = ('<div class="chart" data-step="5" data-chart="k6e" data-label="Antrieb je kg CO₂ 2026 bis 2100 im Szenario SSP2-4.5: '
            'er sinkt, weil die Hintergrundkonzentration steigt"></div>')

GH_CSS = """
/* slide 18: the drawing moves a little */
svg.anim .flow { stroke-dasharray: 44 5; animation: ghflow 1.6s linear infinite; }
svg.anim .flow[stroke-dasharray] { stroke-dasharray: 7 5; animation-duration: 1.1s; }
@keyframes ghflow { to { stroke-dashoffset: -49; } }
svg.anim .mol { transform-box: fill-box; transform-origin: center; animation: ghjig 2.6s ease-in-out infinite alternate; animation-delay: var(--ph); }
@keyframes ghjig { from { transform: translate(-1.5px, -1px) rotate(-5deg); } to { transform: translate(1.5px, 1px) rotate(5deg); } }
svg.anim .rays { transform-box: view-box; transform-origin: 46px 34px; animation: ghspin 24s linear infinite; }
@keyframes ghspin { to { transform: rotate(360deg); } }
svg.anim .flowc { stroke-dasharray: 16 6; animation: ghflowc 1.3s linear infinite; }
@keyframes ghflowc { to { stroke-dashoffset: -22; } }
/* step by step: only what the current step is about keeps moving */
.slide:has(.f-alb.shown) svg.s17 .t-lw { animation-play-state: paused; }
.slide:has(.f-co2.shown) svg.s17 :is(.t-sw, .rays) { animation-play-state: paused; }
.slide:has(.f-co2.shown) svg.s17 .t-lw { animation-play-state: running; }
.slide:has([data-step="1"].shown) svg.s18 :is(.flow, .mol, .rays) { animation-play-state: paused; }
.slide:has([data-step="1"].shown):not(:has([data-step="2"].shown)) svg.s18 :is(.t-sw, .rays, [data-step="1"] .mol) { animation-play-state: running; }
.slide:has([data-step="2"].shown):not(:has([data-step="3"].shown)) svg.s18 :is(.t-lw, .gh2 .flow, .gh2 .mol) { animation-play-state: running; }
.slide:has([data-step="3"].shown) svg.s18 :is(.gh3 .flow, .gh3 .mol) { animation-play-state: running; }
.slide:has([data-step="1"].shown) svg.s19 :is(.t-sw, .t-lw, .rays) { animation-play-state: paused; }
@media (prefers-reduced-motion: reduce) { svg.anim .flow, svg.anim .flowc, svg.anim .mol, svg.anim .rays { animation: none; } }
/* slide 18, step 3: the layered column in front, the single molecule of step 2 steps back */
svg:has(.gh3.shown) .gh2 { opacity: .1; transition: opacity .5s; }
svg:has(.gh3.shown) .gh2 text { opacity: 0; }
/* signpost of the CO2 slides: a word formula; a word gives way to its symbol once the slide introduces it */
.road:has(.froad) { height: 52px; margin-bottom: 12px; }
.froad { display: inline-flex; align-items: center; gap: 12px; font: 500 23px/1.2 var(--sans); color: var(--ink); letter-spacing: 0; }
.froad .tex { font-size: 26px; }
.froad .fx { color: var(--muted); }
.froad .fw { padding: 2px 10px 4px; border: 2.5px solid transparent; border-radius: 10px; color: #a49c8c; }
.froad .fw.cur { border-color: #1b7837; background: rgba(27, 120, 55, .07); color: var(--ink); }
.froad .fw.done { padding: 4px 0; }
.froad .fw .s { display: none; }
.froad .fw { transition: color .5s var(--ease), border-color .5s var(--ease); }
/* slide 18: both factors plain at first; the first click frames the one of this slide and fades the other */
.froad.late .fw, .froad.late .fw.cur { color: var(--ink); border-color: transparent; background: none; }
.slide:has(.ghsteps > [data-step="1"].shown) .froad.late .fw.cur { border-color: #1b7837; background: rgba(27, 120, 55, .07); }
.slide:has(.ghsteps > [data-step="1"].shown) .froad.late .fw:not(.cur) { color: #a49c8c; }
.slide:has(.fswap.shown) .froad .fw.swaps .w { display: none; }
.slide:has(.fswap.shown) .froad .fw.swaps .s { display: inline; animation: fadein .6s var(--ease) both; }
.epsdef { border-left: 5px solid #1b7837; background: rgba(27, 120, 55, .07); border-radius: 6px; padding: 10px 14px; }
.epsdef p { font: 400 20px/1.4 var(--sans); color: var(--ink); }
/* slide 18: the steps of the greenhouse effect, numbered like the drawing */
.ghs { position: relative; padding-left: 44px; font: 400 21px/1.4 var(--sans); color: var(--ink); }
.ghs b { position: absolute; left: 0; top: 1px; width: 30px; height: 30px; border-radius: 50%; background: #b2182b; color: var(--paper);
  font: 600 17px/30px var(--sans); text-align: center; }
"""

EPS_NOTES = (
    "\n    <p>Zuerst die Struktur, oben: Der CO₂-Antrieb hat zwei Komponenten. ε_CO₂ sagt, wie viel Antrieb jedes Kilogramm CO₂ in der Atmosphäre bewirkt — das ist diese Folie. Δm_CO₂ sagt, wie viel CO₂ zu einem Zeitpunkt noch in der Atmosphäre ist — das ist die nächste Folie.</p>\n"
    "    <p>Klick: Auf der letzten Folie stand die Frage: Was macht CO₂ in der Atmosphäre? Jetzt am selben Bild, Schritt für Schritt.</p>\n"
    "    <p>Klick: Das Sonnenlicht ist kurzwellig. CO₂ lässt es durch, es erreicht den Boden.</p>\n"
    "    <p>Klick: Die Erde strahlt die Energie als Wärme wieder ab, langwellig. Diese Strahlung absorbiert CO₂ und strahlt sie in alle Richtungen wieder ab — ein Teil geht zurück zur Erde.</p>\n"
    "    <p>Klick: Kommt mehr CO₂ dazu, wird die Wärmestrahlung in dieser Bande öfter wieder geschluckt. Ins All entkommt sie erst aus größerer Höhe, wo es kälter ist — und ein kälterer Strahler gibt weniger ab. Also verlässt weniger Wärme die Erde: Die Bilanz am Oberrand wird positiv, das ist der Strahlungsantrieb. Die Erde erwärmt sich, bis die Bilanz wieder ausgeglichen ist. Nimmt der Baum CO₂ heraus, ist es umgekehrt: negativ, es kühlt.</p>\n"
    "    <p>Klick: ε_CO₂ fasst das zusammen: die Netto-Änderung der Energiebilanz am Oberrand je Kilogramm zusätzlichem CO₂, in Watt je Quadratmeter. Was in der Atmosphäre im Einzelnen passiert, steckt darin; uns interessiert nur, was an der Systemgrenze herauskommt.</p>\n"
    "    <p>Klick: Aber ε ist kein fester Wert. Wie stark wirkt jedes Kilogramm? Das hängt davon ab, wie viel CO₂ schon da ist: Im Zentrum der Absorptionsbande ist die Atmosphäre schon undurchlässig; zusätzliches CO₂ wirkt nur noch an den Rändern der Bande, deshalb wächst der Antrieb logarithmisch und jedes weitere Kilogramm bewirkt weniger. Deshalb steht die Konzentration c im Nenner. Links die Kurve dazu, einfach zum Merken: heute 1,64, im Jahr 2100 im Szenario SSP2-4.5 noch 1,31 · 10⁻¹⁵ Watt je Quadratmeter und Kilogramm.</p>\n"
    "    <p class=\"q\">Falls Fragen kommen — Antrieb des gesamten CO₂: 5,35 · ln(c/c₀) W/m² (Myhre et al. 1998, aus Strahlungstransfer-Modellen); die Ableitung je kg ist ε_CO₂ = 5,35/(k · c). FaIR nutzt eine genauere, zustandsabhängige Formel (Meinshausen et al. 2020); entlang SSP2-4.5 weicht der Koeffizient um höchstens 2,5 % ab. Kurven dazu: Backup „Strahlungsantrieb von CO₂: Kurven“. Emissionshöhe: Pierrehumbert (2011, Physics Today); Benestad (2016, Theor. Appl. Climatol.); bei weiterer CO₂-Zunahme stammt rund 90 % des zusätzlichen Effekts aus der höheren Emissionshöhe (J. Climate 33(9), 2020). Spektrum und Höhe der Abstrahlung: Backup „Warum CO₂ wärmt“.</p>\n  ")


def _greenhouse(page):
    """Slide 18: the greenhouse effect conceptually on the drawing, then what epsilon depends on; the curves
    go to the backup. Slide 19 builds up: principle, emission curve, removal; the per-tree slide goes to the backup."""
    head, sep, tail = page.partition("</style>")
    page = head + GH_CSS + sep + tail
    mark = "<!-- KAPITEL 1-2, aus dem Hauptteil genommen"
    m = _sec(page, "Strahlungsantrieb von CO₂")
    sec = m.group(0)
    # the slide with the curves, as it was: backup
    old = re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', sec)
    old = old.replace('data-title="Strahlungsantrieb von CO₂"', 'data-title="Strahlungsantrieb von CO₂: Kurven"', 1)
    old = old.replace('<div class="road rise" style="--d:200">', '<div class="road">', 1)
    road = re.search(r'<div class="road rise" style="--d:200">.*?</div>', sec).group(0)
    take = re.search(r'<p class="takeaway"[^>]*>.*?</p>', sec, flags=re.S).group(0)
    take = re.sub(r'data-step="\d+"', 'data-step="4"', take).replace("--d:1800", "--d:900")
    body = ('<div class="body">\n    ' + road + '\n    <div style="display:grid; grid-template-columns:860px 1fr; gap:34px; flex:1; min-height:0; align-items:center">'
            '<div class="ghwrap">' + _gh_svg() + GH_CHART + '</div>' + GH_RIGHT + '</div>\n  </div>\n  <p class="src">')
    b = re.search(r'<div class="body">.*?\n  </div>\n  <p class="src">', sec, flags=re.S)
    sec = sec[: b.start()] + body + sec[b.end():]
    sec = re.sub(r'(<aside class="notes" data-n="\d+">).*?(</aside>)', lambda n: n.group(1) + EPS_NOTES + n.group(2), sec, flags=re.S)
    page = page[: m.start()] + sec + page[m.end():]
    page = page.replace(mark, old + mark, 1)

    page = _cycle(page)
    page = _total(page)
    page = _temperature(page)

    # the per-tree impulse response: backup
    m = _sec(page, "Impulsantwort auf die CO₂-Aufnahme eines Baums")
    tree = re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', m.group(0))
    page = page[: m.start()] + page[m.end():]
    mark = "<!-- KAPITEL 1-2, aus dem Hauptteil genommen"
    assert mark in page
    page = page.replace(mark, tree + mark, 1)
    return page


_TOT = (r'\htmlClass{fd}{\varphi(t) = \pc{\tau_{\mathrm{atm}}}}\;\;\htmlClass{hl hl-q}{\bq{\Delta\dot Q_{\mathrm{Baum}}}(t)}\;\;'
        r'\htmlClass{fd}{/\,\pc{A_{\mathrm{Erde}}} + \cq{\varepsilon_{\mathrm{CO_2}}}(t)}\;\;\htmlClass{hl hl-m}{\cq{\Delta m_{\mathrm{CO_2}}}(t)}')
TOTAL_ROAD = ('<div class="road" style="margin-bottom:10px"><span>Beide Terme zusammen</span><span class="tex" style="font-size:27px">$' + _TOT + '$</span></div>')
TOTAL_DEFS = (r'<dl class="legend sm tex tdefs" style="grid-template-columns:auto 1fr auto 1fr; gap:4px 18px; margin:0 0 6px">'
              r'<dt>$\varphi$</dt><dd>Strahlungsantrieb des Baums [W/m²]</dd>'
              r'<dt>$\cq{\varepsilon_{\mathrm{CO_2}}}$</dt><dd>Antrieb je kg CO₂ — Folie 18</dd>'
              r'<dt>$\pc{\tau_{\mathrm{atm}}}$</dt><dd>Anteil am Oberrand — 0,854</dd>'
              r'<dt class="loc">$\cq{\Delta m_{\mathrm{CO_2}}}$</dt><dd class="loc">verbleibende CO₂-Menge [kg] — Folie 19</dd>'
              r'<dt class="loc">$\bq{\Delta\dot Q_{\mathrm{Baum}}}$</dt><dd class="loc">zusätzlich absorbierte Strahlung [W]</dd>'
              r'<dt>$\pc{A_{\mathrm{Erde}}}$</dt><dd>Erdoberfläche — 5,1 · 10¹⁴ m²</dd></dl>')
TOTAL_CSS = """
/* total forcing: the two place-dependent terms framed and marked on the first click */
.tdefs .loc { transition: color .4s, font-weight .4s; }
.slide:has(.locstep.shown) .tdefs dd.loc { color: var(--ink); font-weight: 600; }
.slide:has(.locstep.shown) .tdefs :is(dt, dd):not(.loc) { opacity: .28; }
.tdefs :is(dt, dd), .road .fd { transition: opacity .5s; }
.slide:has(.locstep.shown) .road .fd { opacity: .28; }
"""


def _total(page):
    """Total forcing: the full formula on top with all definitions, then 'the parameters depend on the place'
    and the three sites at once; no second equation below."""
    head, sep, tail = page.partition("</style>")
    page = head + TOTAL_CSS + sep + tail
    m = _sec(page, "Gesamter Strahlungsantrieb je Baum")
    sec = m.group(0)
    road = re.search(r'<div class="road">.*?</div>', sec).group(0)
    chart = re.search(r'<div class="chart"[^>]*data-chart="k10"[^>]*></div>', sec).group(0)
    foot = re.search(r'<div class="foot">.*?\n    </div>', sec, flags=re.S).group(0)
    take = re.search(r'<p class="takeaway".*?</p>', foot, flags=re.S).group(0)
    take = re.sub(r'data-step="\d+"', 'data-step="2"', take).replace("--d:1800", "--d:0")
    new_chart = re.sub(r'data-slot-steps="[^"]*"', 'data-slot-steps="0,0,0"', chart).replace('<div class="chart"', '<div class="chart" data-step="1"', 1)
    sec = sec.replace(road, TOTAL_ROAD + '\n    ' + TOTAL_DEFS + '\n    <p class="rise locstep" data-step="1" style="--d:0; font:500 22px/1.35 var(--sans); color:var(--ink); margin:22px 0 0">'
                      'Vom Ort abhängig: <span class="tex">$\\bq{\\Delta\\dot Q_{\\mathrm{Baum}}}$</span> und <span class="tex">$\\cq{\\Delta m_{\\mathrm{CO_2}}}$</span> (Albedo, Wachstum; Kapitel Bäume) '
                      '→ <b>Netto-Antrieb an drei Orten:</b></p>', 1)
    sec = sec.replace(chart, new_chart, 1)
    sec = sec.replace(foot, '<div class="foot"><div></div>' + take + '</div>', 1)
    n = re.search(r'<aside class="notes" data-n="\d+">\n?', sec)
    sec = sec[: n.end()] + ("    <p>Oben die ganze Gleichung: der Albedo-Term ausgeschrieben, dazu der CO₂-Term aus ε und Δm. Darunter alle Größen noch einmal.</p>\n"
                            "    <p>Klick: Vom Ort hängen zwei Größen ab, umrahmt: die zusätzlich absorbierte Strahlung und die verbleibende CO₂-Menge — Albedo und Wachstum aus dem Kapitel Bäume. Jetzt sehen wir, was an Netto-Antrieb herauskommt, an drei Orten zugleich.</p>\n") + sec[n.end():]
    return page[: m.start()] + sec + page[m.end():]



def _temp_svg() -> str:
    """Slide 21: the same drawing (same place), with land and ocean as on slide 19; the energy balance of the
    Earth step by step: forcing at the top, heat stored in surface and ocean, more heat radiation when warmer."""
    base = _svg("treibhaus")
    base = base[: base.index("    <!-- step 2: CO2 -->")]
    base = base.replace('class="schema" data-export="s_antrieb_v3"', 'class="schema" data-export="s_temperatur"', 1)
    G = Y_GND
    ground = f'''    <g>
      <rect x="0" y="{G + 2}" width="500" height="58" fill="#d9cfb9"/>
      <rect x="0" y="{G + 60}" width="500" height="80" fill="#a39684"/>
      <path d="M0 {G + 60} H500" stroke="#8c7f6c" stroke-width="2"/>
      <rect x="500" y="{G - 2}" width="380" height="14" fill="#e3edf2"/>
      <path d="M500 {G} q15 8 30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t20 0 L880 {G + 140} L500 {G + 140} Z" fill="#7fb0cc"/>
      <rect x="500" y="{G + 60}" width="380" height="80" fill="#5f93b3"/>
      <path d="M500 {G} q15 8 30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t20 0" stroke="#4f86a6" stroke-width="2.5" fill="none"/>
      <text x="868" y="{G + 24}" text-anchor="end" font-size="22" font-weight="600" fill="#fff">Ozean</text>
      <text x="40" y="{G + 24}" font-size="22" font-weight="600" fill="#5b4a2e">Land</text>
    </g>
    <!-- 1: the tree's forcing is negative: an energy sink at the top, more heat leaves -->
    <g class="pop" data-step="1">
      <path d="M480 {Y_TOA + 110} V{Y_TOA + 24}" stroke="#1b2420" stroke-width="5" fill="none" marker-end="url(#fx-k)"/>
      <rect x="370" y="{Y_TOA - 16}" width="220" height="32" rx="16" fill="#1b2420"/>
      <text x="480" y="{Y_TOA + 6}" text-anchor="middle" font-size="20" font-weight="600" fill="#fff">φ &lt; 0: Senke</text>
      <text x="480" y="{Y_TOA + 136}" text-anchor="middle" font-size="18" font-weight="600" fill="#1b2420">mehr Wärme geht hinaus</text>
    </g>
    <!-- 2: surface and ocean give off heat (C): the Earth cools, slowly -->
    <g class="pop" data-step="2">
      <rect x="0" y="{G + 2}" width="500" height="58" fill="#4f86a6" opacity=".22"/>
      <path d="M500 {G} q15 8 30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t30 0 t20 0 L880 {G + 140} L500 {G + 140} Z" fill="url(#tp-cool)"/>
      <text x="690" y="{G + 110}" text-anchor="middle" font-size="20" font-weight="600" fill="#fff">C: gibt Wärme ab</text>
      <text x="250" y="{G + 40}" text-anchor="middle" font-size="18" font-weight="600" fill="#2c5f7c">wird kühler</text>
    </g>
    <!-- 3: a cooler Earth radiates less (Lambda dT): brakes the cooling -->
    <g class="pop" data-step="3">
      <rect x="796" y="{Y_TOA + 6}" width="34" height="{G - Y_TOA - 12}" fill="#e3edf2" opacity=".72"/>
      <text x="700" y="{Y_TOA + 60}" text-anchor="end" font-size="20" font-weight="600" fill="#8a6a1e">Λ·ΔT: kühler →</text>
      <text x="700" y="{Y_TOA + 86}" text-anchor="end" font-size="20" font-weight="600" fill="#8a6a1e">strahlt weniger ab</text>
    </g>
'''
    defs = ('<linearGradient id="tp-cool" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2c5f7c" stop-opacity=".5"/>'
            '<stop offset=".45" stop-color="#2c5f7c" stop-opacity=".22"/><stop offset="1" stop-color="#2c5f7c" stop-opacity=".04"/></linearGradient>'
            '<marker id="fx-k" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#1b2420"/></marker>')
    base = base.replace("</defs>", defs + "</defs>", 1)
    out = base + ground + "  </g>\n</svg>"
    out = re.sub(r'id="fx-(\w)"', r'id="tp-\1"', out).replace("url(#fx-", "url(#tp-")
    return _anim(out, "s21")


TEMP_RIGHT = r'''<div style="display:flex; flex-direction:column; gap:8px; align-self:start; min-width:0">
      <div class="eq tex" style="font-size:25px; text-align:left; margin:0">$$\htmlClass{hl hl-c}{\pc{C}}\;\;\;\frac{\mathrm{d}\,\tq{\Delta T}}{\mathrm{d}t} \;\;=\;\; \htmlClass{hl hl-p}{\varphi(t)} \;\;\;-\;\;\; \htmlClass{hl hl-l}{\pc{\Lambda}\;\tq{\Delta T}(t)}$$</div>
      <p style="font:400 18px/1.2 var(--sans); color:var(--muted); margin:-2px 0 -4px">gelöst nach <span class="tex">$\tq{\Delta T}$</span>:</p>
      <div class="eq tex" style="font-size:23px; text-align:left; margin:0 0 6px">$$\htmlClass{hl hl-r}{\tq{\Delta T}(t)} \;\;=\;\; \sum_{t' \le t} \frac{1}{\pc{C}}\, e^{-\frac{\pc{\Lambda}}{\pc{C}}\,(t-t')}\; \varphi(t')$$</div>
      <div class="rise ts1" data-step="1" style="--d:200"><p class="ghs"><b style="background:#1b2420">1</b><span class="tex">$\varphi < 0$</span>: Baum nimmt CO₂ auf<br>→ Energiesenke am Oberrand</p></div>
      <div class="rise ts2" data-step="2" style="--d:200"><p class="ghs"><b style="background:#8a6a1e">2</b><span class="tex">$\pc{C}$</span>: Oberfläche und Ozean geben Wärme ab<br>→ die Erde kühlt, aber langsam</p></div>
      <div class="rise ts3" data-step="3" style="--d:200"><p class="ghs"><b style="background:#6b5a1e">3</b><span class="tex">$\pc{\Lambda}\,\tq{\Delta T}$</span>: kühlere Erde strahlt weniger ab<br>→ bremst die Abkühlung</p></div>
      <div class="rise ts4" data-step="4" style="--d:200"><p class="ghs"><b style="background:#b2182b">4</b>Ergebnis je Baum: <span class="tex">$\tq{\Delta T} < 0$</span><br>→ nähert sich <span class="tex">$\varphi/\pc{\Lambda}$</span> (Grafik)</p></div>
    </div>'''


TEMP_CSS = """
/* slide 21: the term under discussion framed in the formula (same highlight as elsewhere) */
.slide:has(.ts1.shown):not(:has(.ts2.shown)) .hl-p::before { border-color: #1b2420; background: rgba(27, 36, 32, .06); }
.slide:has(.ts2.shown):not(:has(.ts3.shown)) .hl-c::before { border-color: #8a6a1e; background: rgba(138, 106, 30, .08); }
.slide:has(.ts3.shown):not(:has(.ts4.shown)) .hl-l::before { border-color: #6b5a1e; background: rgba(107, 90, 30, .08); }
.slide:has(.ts4.shown) .hl-r::before { border-color: #b2182b; background: rgba(178, 24, 43, .07); }
/* the radiation in this drawing stands still: here the topic is the energy balance, not the radiation */
svg.s21 :is(.flow, .rays) { animation-play-state: paused !important; }
"""


def _temperature(page):
    head, sep, tail = page.partition("</style>")
    page = head + TEMP_CSS + sep + tail
    m = _sec(page, "Temperaturantwort auf den Strahlungsantrieb")
    sec = m.group(0)
    road = re.search(r'<div class="road">.*?</div>', sec).group(0)
    chart = re.search(r'<div class="chart" data-slot-steps="0,1" data-chart="k12b"[^>]*></div>', sec).group(0)
    new_chart = ('<div class="chart" data-step="4" data-chart="k12t" data-label="Temperaturwirkung je Baum in Aachen (DE), Joensuu (FI) und Marabá (BR)"></div>')
    take = re.search(r'<p class="takeaway".*?</p>', sec, flags=re.S).group(0)
    take = re.sub(r'data-step="\d+"', 'data-step="5"', take).replace("--d:1800", "--d:0")
    body = ('<div class="body">\n    ' + road.replace('<div class="road">', '<div class="road" style="height:52px; margin-bottom:12px">', 1)
            + '\n    <div style="display:grid; grid-template-columns:860px 1fr; gap:34px; flex:1; min-height:0; align-items:center">'
            '<div class="ghwrap">' + _temp_svg() + new_chart + '</div>' + TEMP_RIGHT + '</div>\n    <div class="foot"><div></div>' + take + '</div>\n  </div>\n  <p class="src">')
    b = re.search(r'<div class="body">.*?\n  </div>\n  <p class="src">', sec, flags=re.S)
    sec = sec[: b.start()] + body + sec[b.end():]
    sec = re.sub(r'<p class="src">Links Modellergebnis.*?Rechts eigene Rechnung mit FaIR:', '<p class="src">Eigene Rechnung mit dem Klima-Emulator FaIR 2.2 (Leach et al. 2021; fair-calibrate 1.4.1, Smith et al. 2024; Mitglied 787474, ECS 2,9 K):', sec, count=1, flags=re.S)
    n = re.search(r'<aside class="notes" data-n="\d+">\n?', sec)
    sec = sec[: n.end()] + (
        "    <p>Dasselbe Bild, jetzt mit der Frage: Wie wird aus dem Antrieb eine Temperatur? Oben die Energiebilanz der Erde in ihrer einfachsten Form: Wärmekapazität C mal die Änderungsrate der Temperatur ist der Antrieb φ minus das, was die Erde wegen ihrer Temperaturänderung mehr oder weniger abstrahlt, Λ mal ΔT. Darunter dieselbe Gleichung, gelöst nach ΔT: Jeder Antrieb von früher wirkt bis heute nach, geteilt durch C und abklingend mit der Zeitkonstante C durch Λ; ΔT ist die Summe davon.</p>\n"
        "    <p>Klick: Was heißt das für den Baum? Sein Antrieb ist negativ, weil er CO₂ aufnimmt; die Albedo wärmt dagegen, aber netto überwiegt die Aufnahme. Am Oberrand ist der Baum also eine Energiesenke: Es geht mehr Wärme hinaus als ohne ihn.</p>\n"
        "    <p>Klick: C, die Wärmekapazität. Oberfläche und vor allem der Ozean geben Wärme ab; weil der Ozean so viel speichert, kühlt die Erde nur langsam.</p>\n"
        "    <p>Klick: Λ mal ΔT. Eine kühlere Erde strahlt weniger ab; das bremst die Abkühlung. Deshalb sinkt ΔT nicht immer weiter, sondern nähert sich φ durch Λ.</p>\n"
        "    <p>Klick: das Ergebnis, die Lösung unten in der Formel. Für den Baum setzen wir seinen Antrieb von der letzten Folie ein und bekommen seine Temperaturwirkung ΔT, links an den drei Orten. In Joensuu kühlt der Baum zuerst stärker; ab etwa 2060 wird die Kühlung schwächer. Der Grund ist der Antrieb: Ab etwa 2050 wächst der Baum langsamer, sein CO₂-Antrieb nimmt nur noch wenig zu (2055 bis 2100 von −52 auf −66), die Albedo aber wärmt mit dem Kronenschluss über dem Schnee weiter zu (von +20 auf +51, je 10⁻¹⁵ W/m²). Der Netto-Antrieb wird schwächer, die Temperatur folgt verzögert. In Aachen halten sich beide Zuwächse etwa die Waage, bei Marabá ist die Albedo klein — dort bleibt die Kühlung.</p>\n") + sec[n.end():]
    return page[: m.start()] + sec + page[m.end():]
