"""Klima formulas explained like slides 10-12 (2026-10-07): a colour per role, a symbol legend under
every formula, one notation for the chapter.

colours: tree quantities brown, response functions teal, CO2 path green, albedo orange, temperature red,
parameters gold (as in the tree chapter).
notation: concentration c (C is the heat capacity), time constants theta_i (tau is tau_atm),
m_CO2-dot = -44/12 m-dot is the flux into the atmosphere, so Delta m_CO2 < 0 and phi_CO2 < 0 for a tree.
"""
import re

MACROS = r'''  "\\bq":  "\\textcolor{6b4a2b}{\\boldsymbol{#1}}",   // from the tree chapter
  "\\rq":  "\\textcolor{1f7a8c}{\\boldsymbol{#1}}",   // response functions g_C, g_T
  "\\cq":  "\\textcolor{1b7837}{\\boldsymbol{#1}}",   // CO2 path
  "\\aq":  "\\textcolor{d95f02}{\\boldsymbol{#1}}",   // albedo
  "\\tq":  "\\textcolor{b2182b}{\\boldsymbol{#1}}",   // temperature
'''

CSS = """
/* compact symbol legend under a formula in the foot (Klima) */
.legend.sm { gap: 2px 14px; margin-top: 10px; }
.legend.sm dt { font-size: 20px; }
.legend.sm dd { font-size: 15.5px; line-height: 1.3; }
"""


def _legend(rows, d=1200):
    items = "".join(f"<dt>${sym}$</dt><dd>{text}</dd>" for sym, text in rows)
    return f'<dl class="legend sm tex rise" style="--d:{d}">{items}</dl>'


def _foot_left(eq, rows, size=24, d=900):
    return (f'<div class="rise" style="--d:{d}"><div class="eq tex" style="font-size:{size}px">$${eq}$$</div>'
            + _legend(rows, d + 300) + "</div>")


PHI_A = (r"\begin{aligned}\varphi(t) &= \underbrace{\cq{\varphi_{\mathrm{CO_2}}}(t)}_{\text{CO₂-Aufnahme}} + \underbrace{\aq{\varphi_\alpha}(t)}_{\text{Albedo}}\\[22pt] "
         r"\aq{\varphi_\alpha}(t) &= \pc{\tau_{\mathrm{atm}}}\,\bq{\Delta\dot Q_{\mathrm{Baum}}}(t)\,/\,\pc{A_{\mathrm{Erde}}}\\[4pt] "
         r"\cq{\varphi_{\mathrm{CO_2}}}(t) &= \underbrace{\cq{A_{\mathrm{CO_2}}}(t)}_{\text{je kg CO₂}}\;\underbrace{\cq{\Delta m_{\mathrm{CO_2}}}(t)}_{\text{CO₂-Änderung}}\end{aligned}",
         [(r"\aq{\varphi_\alpha}", "Albedo-Antrieb [W/m²], > 0: wärmt"),
          (r"\bq{\Delta\dot Q_{\mathrm{Baum}}}", "zusätzlich absorbierte Strahlung des Baums [W] (Kapitel Bäume)"),
          (r"\pc{\tau_{\mathrm{atm}}}", "Anteil der Mehrreflexion, der den Oberrand erreicht — ≈ 0,8"),
          (r"\pc{A_{\mathrm{Erde}}}", "Erdoberfläche — 5,1 · 10¹⁴ m²")])

G_C = (r"\rq{g_C}(t) = \pc{a_0} + \sum_{i=1}^{3} \pc{a_i}\, e^{-t/\pc{\theta_i}}",
       [(r"\rq{g_C}", "Anteil, der t Jahre nach Emission oder Entnahme in der Atmosphäre bleibt"),
        (r"\pc{a_0}", "dauerhaft verbleibender Anteil — 0,22"),
        (r"\pc{a_i},\ \pc{\theta_i}", "abklingende Anteile 0,22 · 0,28 · 0,28; Zeitkonstanten 394 · 37 · 4 Jahre")])

DM = (r"\begin{aligned}\bq{\dot m_{\mathrm{CO_2}}}(t') &= -\tfrac{44}{12}\,\bq{\dot m}(t')\\ "
      r"\cq{\Delta m_{\mathrm{CO_2}}}(t) &= \sum_{t' \le t} \rq{g_C}(t-t')\, \bq{\dot m_{\mathrm{CO_2}}}(t')\end{aligned}",
      [(r"\bq{\dot m}", "Netto-Kohlenstoffaufnahme des Baums im Jahr t′ [kg C/a]"),
       (r"\bq{\dot m_{\mathrm{CO_2}}}", "CO₂-Fluss in die Atmosphäre [kg CO₂/a]; Aufnahme negativ"),
       (r"\rq{g_C}", "Impulsantwort der Vorfolie"),
       (r"\cq{\Delta m_{\mathrm{CO_2}}}", "CO₂-Änderung der Atmosphäre [kg] (Linien: −Δm)")])

PHI_CO2 = (r"\begin{aligned}\varphi(c) &= \pc{5{,}35}\,\tfrac{\mathrm{W}}{\mathrm{m^2}}\,\ln\frac{c}{\pc{c_0}}\\ "
           r"\cq{A_{\mathrm{CO_2}}}(t) &= \frac{\partial\varphi}{\partial m} = \frac{\pc{5{,}35}\,\mathrm{W/m^2}}{\pc{k}\,c(t)}\\ "
           r"\cq{\varphi_{\mathrm{CO_2}}}(t) &= \cq{A_{\mathrm{CO_2}}}(t)\,\cq{\Delta m_{\mathrm{CO_2}}}(t)\end{aligned}",
           [(r"\varphi(c)", "Antrieb des gesamten CO₂ gegenüber vorindustriell [W/m²]"),
            (r"c,\ \pc{c_0}", "CO₂-Konzentration im Szenario [ppm]; vorindustriell 278 ppm"),
            (r"m,\ \pc{k}", "CO₂-Masse der Atmosphäre, m = k · c; k = 7,82 · 10¹² kg je ppm"),
            (r"\cq{A_{\mathrm{CO_2}}}", "Antrieb je kg CO₂ [W/m²/kg] — 1,65 → 1,31 · 10⁻¹⁵ (2025 → 2100)"),
            (r"\cq{\Delta m_{\mathrm{CO_2}}}", "CO₂-Änderung der Atmosphäre durch den Baum (Vorfolie)"),
            (r"\cq{\varphi_{\mathrm{CO_2}}}", "CO₂-Antrieb des Baums [W/m²], < 0: kühlt")])

PHI = (r"\varphi(t) = \cq{\varphi_{\mathrm{CO_2}}}(t) + \aq{\varphi_\alpha}(t)",
       [(r"\varphi", "gesamter Strahlungsantrieb des Baums [W/m²] (schwarz)"),
        (r"\cq{\varphi_{\mathrm{CO_2}}}", "CO₂-Antrieb, < 0, kühlt (grün; Folie „Strahlungsantrieb von CO₂“)"),
        (r"\aq{\varphi_\alpha}", "Albedo-Antrieb, > 0, wärmt (orange; Folie „Strahlungsantrieb“)")])

DT = (r"\begin{aligned}\pc{C}\,\frac{\mathrm{d}\tq{T}}{\mathrm{d}t} &= \varphi(t) - \pc{\Lambda}\,\tq{T}(t)\\ "
      r"\tq{\Delta T}(t) &= \sum_{t' \le t} \rq{g_T}(t-t')\,\varphi(t')\end{aligned}",
      [(r"\tq{T}", "Temperaturänderung der Erdoberfläche [K]"),
       (r"\varphi", "Strahlungsantrieb [W/m²]; für den Baum: Vorfolie"),
       (r"\pc{C}", "Wärmekapazität von Oberfläche und Ozean [J/(m² K)]"),
       (r"\pc{\Lambda}", "Rückkopplungsparameter: Mehrabstrahlung je K [W/(m² K)]"),
       (r"\rq{g_T}", "Temperatur-Impulsantwort auf ein Jahr mit 1 W/m² [K]; aus FaIR"),
       (r"\tq{\Delta T}", "Temperaturwirkung des Baums [K]")])


def _col(head, color, eq, rows):
    return (f'<div><p style="font:600 15px/1.2 var(--sans); letter-spacing:.08em; color:{color}; text-align:center; margin-bottom:4px">{head}</p>'
            f'<div class="eq tex" style="font-size:22px; text-align:center">$${eq}$$</div>' + _legend(rows, 0).replace(' rise" style="--d:0"', '"') + "</div>")


# slide 20: the overall equation, an arrow from each term to its own column (formula + legend)
SPLIT = ('<div class="rise" style="--d:900">'
         r'<div class="eq tex" style="font-size:30px; text-align:center">$$\varphi(t) = \underset{\textcolor{1b7837}{\LARGE\swarrow}}{\cq{\varphi_{\mathrm{CO_2}}}(t)}\qquad+\qquad\underset{\textcolor{d95f02}{\LARGE\searrow}}{\aq{\varphi_\alpha}(t)}$$</div>'
         '<div style="display:grid; grid-template-columns:1fr 1fr; gap:28px">'
         + _col("CO₂-AUFNAHME", "#1b7837",
                r"\cq{\varphi_{\mathrm{CO_2}}}(t) = \cq{\varepsilon_{\mathrm{CO_2}}}(t)\,\cq{\Delta m_{\mathrm{CO_2}}}(t)",
                [(r"\cq{\varphi_{\mathrm{CO_2}}}", "CO₂-Antrieb [W/m²], < 0: kühlt"),
                 (r"\cq{\Delta m_{\mathrm{CO_2}}}", "CO₂-Änderung der Atmosphäre durch den Baum [kg] — Folien 21–22"),
                 (r"\cq{\varepsilon_{\mathrm{CO_2}}}", "Strahlungseffizienz: Antrieb je kg CO₂ [W/m² je kg] — Folie 23")])
         + _col("ALBEDO", "#d95f02",
                r"\aq{\varphi_\alpha}(t) = \pc{\tau_{\mathrm{atm}}}\,\bq{\Delta\dot Q_{\mathrm{Baum}}}(t)\,/\,\pc{A_{\mathrm{Erde}}}",
                [(r"\aq{\varphi_\alpha}", "Albedo-Antrieb [W/m²], > 0: wärmt"),
                 (r"\bq{\Delta\dot Q_{\mathrm{Baum}}}", "zusätzlich absorbierte Strahlung des Baums [W] — Kapitel Bäume"),
                 (r"\pc{\tau_{\mathrm{atm}}}", "Anteil der Mehrreflexion, der den Oberrand erreicht — ≈ 0,8"),
                 (r"\pc{A_{\mathrm{Erde}}}", "Erdoberfläche — 5,1 · 10¹⁴ m²")])
         + "</div></div>")


def patch(page: str) -> str:
    def rep(old, new):
        nonlocal page
        assert old in page, old[:90]
        page = page.replace(old, new, 1)

    rep('  "\\\\st":', MACROS + '  "\\\\st":')
    rep("/* symbol legends */", CSS + "\n/* symbol legends */")

    rep(r'<div class="eq tex rise" style="--d:900; font-size:26px">$$\varphi_\alpha(t) = \tau_{\mathrm{atm}}\,\Delta\dot Q_{\mathrm{Baum}}(t)\,/\,A_{\mathrm{Erde}}$$</div>',
        SPLIT)
    rep('''<div class="rise" style="--d:900">
        <div class="eq tex">$$g_C(t) = a_0 + \\sum_{i=1}^{3} a_i\\, e^{-t/\\tau_i}$$</div>
        <p style="font:400 16px/1.4 var(--sans); color:var(--muted); margin-top:4px">a₀ ≈ 22 % bleibt auf Dauer; τ ≈ 4, 37 und 394 Jahre</p>
      </div>''', _foot_left(*G_C, size=26))
    rep(r'''<div class="eq tex rise" style="--d:1800">$$\Delta m_{\mathrm{CO_2}}(t) = \sum_{t' \le t} g_C(t-t')\, \dot m_{\mathrm{CO_2}}(t')$$</div>''',
        _foot_left(*DM, size=22, d=1500))
    rep(r'''<div class="eq tex rise" style="--d:900; font-size:24px">$$\begin{aligned}\varphi(C) &= 5{,}35\,\tfrac{\mathrm{W}}{\mathrm{m^2}}\,\ln\frac{C}{C_0}\\ A_{\mathrm{CO_2}}(t) &= \frac{\partial\varphi}{\partial m} = \frac{5{,}35\,\mathrm{W/m^2}}{k\,C(t)}\\ \varphi_{\mathrm{CO_2}}(t) &= A_{\mathrm{CO_2}}(t)\,\Delta m_{\mathrm{CO_2}}(t)\end{aligned}$$</div>''',
        _foot_left(*PHI_CO2, size=21))
    rep(r'''<div class="eq tex rise" style="--d:900; font-size:28px">$$\varphi(t) = \varphi_{\mathrm{CO_2}}(t) + \varphi_\alpha(t)$$</div>''',
        _foot_left(*PHI, size=28))
    rep(r'''<div class="eq tex rise" style="--d:900; font-size:24px">$$\begin{aligned}C\,\frac{\mathrm{d}T}{\mathrm{d}t} &= \varphi(t) - \Lambda\,T(t)\\ \Delta T(t) &= \sum_{t' \le t} g_T(t-t')\,\varphi(t')\end{aligned}$$</div>''',
        _foot_left(*DT, size=22))

    # 23 and 25: formula and legend beside the chart (the two-panel charts keep their height)
    for key in ("k6", "k12b"):
        m = re.search(r'(<div class="chart" data-slot-steps="0,1" data-chart="' + key + r'"[^>]*></div>)\s*<div class="foot">\s*'
                      r'(<div class="rise" style="--d:900">.*?</dl></div>)\s*(<p class="takeaway".*?</p>)\s*</div>', page, flags=re.S)
        assert m, key
        chart = m.group(1).replace('></div>', ' style="height:100%"></div>', 1)
        page = page[:m.start()] + (
            '<div style="display:grid; grid-template-columns:minmax(0,1fr) 610px; gap:28px; flex:1; min-height:0; align-items:center">'
            + chart + m.group(2) + '</div>\n    <div class="foot"><div></div>' + m.group(3) + '</div>') + page[m.end():]

    # a signpost on every following slide: the overall equation, the term in work boxed, the rest grey
    G = r"\textcolor{b5ada0}"
    road = {
        "Impulsantwort des Kohlenstoffkreislaufs": ("CO₂-Term, Schritt 1: die CO₂-Änderung der Atmosphäre",
            G + r"{\varphi(t) = A_{\mathrm{CO_2}}(t)}\,\boxed{\cq{\Delta m_{\mathrm{CO_2}}}(t)} " + G + r"{{}+ \varphi_\alpha(t)}"),
        "Impulsantwort auf die CO₂-Aufnahme eines Baums": ("CO₂-Term, Schritt 1: die CO₂-Änderung der Atmosphäre",
            G + r"{\varphi(t) = A_{\mathrm{CO_2}}(t)}\,\boxed{\cq{\Delta m_{\mathrm{CO_2}}}(t)} " + G + r"{{}+ \varphi_\alpha(t)}"),
        "Strahlungsantrieb von CO₂": ("CO₂-Term, Schritt 2: der Antrieb je kg CO₂",
            G + r"{\varphi(t) =}\ \boxed{\cq{A_{\mathrm{CO_2}}}(t)}\,\cq{\Delta m_{\mathrm{CO_2}}}(t) " + G + r"{{}+ \varphi_\alpha(t)}"),
        "Gesamter Strahlungsantrieb je Baum": ("Beide Terme zusammen",
            r"\boxed{\varphi(t) = \cq{A_{\mathrm{CO_2}}}(t)\,\cq{\Delta m_{\mathrm{CO_2}}}(t) + \aq{\varphi_\alpha}(t)}"),
        "Temperaturantwort auf den Strahlungsantrieb": ("Vom Antrieb zur Temperatur",
            G + r"{\varphi(t)}\ \longrightarrow\ \boxed{\tq{\Delta T}(t)}"),
    }
    for title, (label, tex) in road.items():
        m = re.search(r'<section class="slide" data-ch="klima" data-title="' + re.escape(title) + r'">.*?<div class="body">', page, flags=re.S)
        assert m, title
        page = page[:m.end()] + f'\n    <div class="road rise" style="--d:200"><span>{label}</span><span class="tex">${tex}$</span></div>' + page[m.end():]
    rep("/* symbol legends */", """/* signpost: the overall equation with the term in work boxed (Klima) */
.road { display: flex; gap: 16px; align-items: center; margin: 0 0 12px; font: 500 16px/1.2 var(--sans); color: var(--muted); letter-spacing: .02em; }
.road .tex { font-size: 22px; color: var(--ink); }

/* symbol legends */""")

    # notes refer to the terms of the overall equation
    rep("Dafür brauchen wir zwei Schritte — wie viel CO₂ der Atmosphäre fehlt, und wie stark jedes Kilogramm wirkt. Die kommen jetzt.</p>",
        "Dafür brauchen wir zwei Schritte — wie viel CO₂ der Atmosphäre fehlt, und wie stark jedes Kilogramm wirkt. Rechts steht das als Gleichung: Der gesamte Antrieb ist CO₂-Term plus Albedo-Term. Den Albedo-Term können wir sofort hinschreiben. Den CO₂-Term zerlegen wir in Antrieb je Kilogramm mal CO₂-Änderung; diese beiden Faktoren bauen die nächsten Folien auf. Die Zeile oben auf jeder Folie zeigt, an welchem Term wir gerade sind.</p>")
    for title, text in (("Impulsantwort des Kohlenstoffkreislaufs",
                         "Oben die Gleichung von eben: Wir arbeiten jetzt am CO₂-Term und beginnen mit dem zweiten Faktor, der CO₂-Änderung der Atmosphäre Δm_CO₂ — umrahmt."),
                        ("Strahlungsantrieb von CO₂",
                         "Oben wieder die Gleichung: Δm_CO₂ haben wir jetzt. Es fehlt der erste Faktor des CO₂-Terms, der Antrieb je Kilogramm A_CO₂ — umrahmt."),
                        ("Gesamter Strahlungsantrieb je Baum",
                         "Oben: Beide Faktoren des CO₂-Terms sind bekannt, der Albedo-Term seit Beginn des Kapitels. Jetzt setzen wir die Gleichung zusammen.")):
        m = re.search(r'data-title="' + re.escape(title) + r'">.*?<aside class="notes" data-n="\d+">\n', page, flags=re.S)
        assert m, title
        page = page[:m.end()] + f"    <p>{text}</p>\n" + page[m.end():]

    rep('<div style="display:grid; grid-template-columns:600px 1fr; gap:44px; flex:1; min-height:0; align-items:center">',
        '<div style="display:grid; grid-template-columns:440px 1fr; gap:36px; flex:1; min-height:0; align-items:center">')

    # sources and notes in the same notation
    rep("Antrieb: Myhre et al. 1998 (aus Strahlungstransfer-Modellen), C₀ = 278 ppm;",
        "Antrieb: Myhre et al. 1998 (aus Strahlungstransfer-Modellen), c₀ = 278 ppm;")
    page = page.replace("ΔF = 5,35 · ln(C/C₀) W/m², aus Strahlungstransfer-Rechnungen; für kleine Änderungen linearisiert, A_CO₂ = 5,35 / (k · C).",
                        "ΔF = 5,35 · ln(c/c₀) W/m², aus Strahlungstransfer-Rechnungen; für kleine Änderungen linearisiert, A_CO₂ = 5,35 / (k · c).")
    rep("Die Balken zeigen, was der Baum bis dahin insgesamt geholt hat, die Linien, was davon der Luft noch fehlt — das ist die Formel unten: jede Jahresentnahme mal dem Anteil, der bis heute noch fehlt. Bis 2100 fehlt der Luft gut die Hälfte dessen, was der Baum geholt hat.</p>",
        "Die Balken zeigen, was der Baum bis dahin insgesamt aufgenommen hat, die Linien, um wie viel das CO₂ in der Atmosphäre dadurch abgenommen hat. Das ist die Formel unten: Aus dem Kohlenstoffzuwachs des Baums wird mit 44/12 ein CO₂-Fluss, negativ, weil er die Atmosphäre verlässt; jede Jahresaufnahme wird mit der Impulsantwort gewichtet, die bis heute vergangen ist, und alles summiert. 2100 ist das gut die Hälfte dessen, was der Baum aufgenommen hat. Ich zeige hier bewusst bis 2200, über unseren Bewertungshorizont hinaus: Um 2090 erreicht die Abnahme ihr Maximum. Danach wächst der Wald kaum noch, die Aufnahme geht gegen null, aber Ozean und Land geben weiter CO₂ zurück — die Linie sinkt, Richtung des dauerhaften Anteils von gut einem Fünftel.</p>")
    # radiative efficiency: epsilon_CO2 (A is an area: A_Baum, A_Erde); epsilon was only the immediate release share
    rep("vom verlorenen Vorrat entweichen ε ≈ 0,23 sofort,", "vom verlorenen Vorrat entweichen rund 23 % sofort,")
    page = (page.replace(r"A_{\mathrm{CO_2}}", r"\varepsilon_{\mathrm{CO_2}}").replace("A_CO₂", "ε_CO₂")
            .replace("Antrieb je kg CO₂ [W/m²/kg]", "Strahlungseffizienz [W/m² je kg]"))
    # tau_atm: what it is and where the 0.8 comes from (2026-10-07)
    TAU_TXT = "Anteil einer Reflexionsänderung an der Oberfläche, der am Oberrand ankommt — ≈ 0,8"
    page = page.replace("Anteil der Mehrreflexion, der den Oberrand erreicht — ≈ 0,8", TAU_TXT)
    rep("mit dem Anteil τ_atm ≈ 0,8, der die Atmosphäre verlassen hätte.",
        "mit dem Anteil τ_atm ≈ 0,8 der Reflexionsänderung, der am Oberrand der Atmosphäre ankommt.")
    rep("Duveiller et al. 2018) mal τ_atm ≈ 0,8, geteilt durch A_Erde = 5,1 · 10¹⁴ m².",
        "Duveiller et al. 2018) mal τ_atm, geteilt durch A_Erde = 5,1 · 10¹⁴ m². τ_atm ≈ 0,8: Durchlässigkeit der Atmosphäre für Kurzwellenstrahlung von der Oberfläche nach oben, ein globaler Mittelwert (Annahme; Literatur 0,85: Lenton & Vaughan 2009, Cherubini et al. 2012).")
    page = page.replace("berücksichtigen mit τ_atm, welcher Teil der Mehrreflexion die Atmosphäre tatsächlich verlassen hätte.",
                        "berücksichtigen mit τ_atm, welcher Teil dieser Reflexionsänderung am Oberrand der Atmosphäre tatsächlich ankommt.")
    rep("Falls Fragen kommen — τ_atm ≈ 0,8: Anteil der an der Oberfläche zusätzlich reflektierten Kurzwellenstrahlung, der den Oberrand erreicht.",
        "Falls Fragen kommen — τ_atm ≈ 0,8: ΔQ̇_Baum gilt an der Oberfläche, und der Weg nach unten (Wolken) steckt schon in der gemessenen Einstrahlung. Auf dem Weg nach oben absorbieren oder streuen Wolken, Wasserdampf und Aerosole einen Teil: Reflektiert die Oberfläche 10 W weniger, verlassen am Oberrand nur etwa 8 W weniger die Erde. Wir nehmen einen globalen Mittelwert (Literatur 0,85: Lenton & Vaughan 2009; Cherubini et al. 2012). Genauer wären Strahlungs-Kernels je Ort und Monat (Bright & O'Halloran 2019): unter dichter Bewölkung, etwa in den Tropen, liegt der Wert niedriger, in klaren, trockenen Regionen höher.")
    rep("τ_atm ≈ 0,8; typischer Wald je Ort, gepflanzt 2025, SSP2-4.5.</p>",
        "τ_atm ≈ 0,8 (globaler Mittelwert, Annahme; Literatur 0,85: Lenton & Vaughan 2009); typischer Wald je Ort, gepflanzt 2025, SSP2-4.5.</p>")
    rep("Falls Fragen kommen — τ_atm ≈ 0,8: Anteil der an der Oberfläche zusätzlich reflektierten Strahlung, der den Oberrand der Atmosphäre erreicht",
        "Falls Fragen kommen — τ_atm ≈ 0,8: Anteil einer Reflexionsänderung an der Oberfläche, der am Oberrand der Atmosphäre ankommt")
    assert "Mehrreflexion" not in page
    return page
