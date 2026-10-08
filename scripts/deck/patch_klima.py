"""Klima chapter in a clean order (2026-10-07), applied after patch_story:

end of Bäume: kg CO2 and W of light side by side (b9) -- the open question; energy only in Klima
Klima: impulse response (concept) -> applied to the tree -> radiative forcing of CO2 (new, formulas)
       -> forcing of CO2 and albedo -> temperature response (energy balance) -> FaIR does all of it
       -> what a tree does where.
The disturbance feedback slide goes to the live backup (small effect; planting year is shown globally later).
Titles and takeaways in a scientific register.
"""
import re


def _take(page: str, title: str) -> tuple[str, str]:
    m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(title) + r'"[^>]*>.*?</section>\n\n?',
                  page, flags=re.S)
    assert m, title
    return page[: m.start()] + page[m.end():], m.group(0)



FRAME = """<section class="slide" data-ch="klima" data-title="Strahlungsantrieb: Energiebilanz am Oberrand">
  <header class="sh"><h2>Strahlungsantrieb: die Energiebilanz am Oberrand der Atmosphäre</h2></header>
  <div class="body">
    <div style="display:grid; grid-template-columns:600px 1fr; gap:44px; flex:1; min-height:0; align-items:center">
    <svg class="schema" data-export="s_antrieb" viewBox="0 0 570 440" style="width:100%; height:100%" aria-label="Energiebilanz am Oberrand der Atmosphäre: Einstrahlung, Reflexion und Wärmeabstrahlung; die Albedo des Baums wird direkt zum Antrieb, das CO2 über zwei Schritte">
      <defs>
        <marker id="ah-an-y" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#d9a441"/></marker>
        <marker id="ah-an-o" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#d9822b"/></marker>
        <marker id="ah-an-r" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#b2182b"/></marker>
      </defs>
      <g font-family="IBM Plex Sans">
        <g class="pop" style="--d:100">
          <rect x="0" y="70" width="560" height="330" fill="#e3edf2"/>
          <line x1="0" y1="70" x2="560" y2="70" stroke="var(--muted)" stroke-width="2" stroke-dasharray="8 6"/>
          <text x="112" y="58" font-size="16" letter-spacing="1.5" fill="var(--muted)">OBERRAND DER ATMOSPHÄRE</text>
          <rect x="0" y="400" width="560" height="34" fill="#d9cfb9"/>
          <line x1="0" y1="400" x2="560" y2="400" stroke="#8c7a58" stroke-width="3"/>
          <rect x="292" y="300" width="16" height="100" fill="#3b3024"/>
          <circle cx="300" cy="262" r="58" fill="#6f8f55"/><circle cx="262" cy="306" r="40" fill="#7f9c64"/><circle cx="340" cy="308" r="38" fill="#5f7f48"/>
          <circle cx="70" cy="30" r="20" fill="#e8b84f"/>
          <path d="M92 48 L262 238" stroke="#d9a441" stroke-width="4" fill="none" marker-end="url(#ah-an-y)"/>
          <text x="24" y="200" font-size="17" fill="var(--ink-2)">Einstrahlung</text>
          <path d="M282 232 L392 30" stroke="#d9822b" stroke-width="4" stroke-dasharray="3 9" stroke-linecap="round" fill="none" marker-end="url(#ah-an-o)"/>
          <text x="352" y="150" font-size="17" fill="var(--ink-2)">Reflexion</text>
          <path d="M480 396 q12 -18 0 -36 q-12 -18 0 -36 q12 -18 0 -36 q-12 -18 0 -36 q12 -18 0 -36 q-12 -18 0 -36 q12 -18 0 -36 q-12 -18 0 -36 L480 34" stroke="#b2182b" stroke-width="3.5" fill="none" marker-end="url(#ah-an-r)"/>
          <text x="466" y="356" text-anchor="end" font-size="17" fill="var(--ink-2)">Wärme-</text>
          <text x="466" y="378" text-anchor="end" font-size="17" fill="var(--ink-2)">abstrahlung</text>
        </g>
      </g>
    </svg>
    <div><p class="rise" style="--d:500; font:400 19px/1.45 var(--sans); color:var(--ink-2); margin-bottom:14px">Die Energiebilanz am Oberrand: Einstrahlung − Reflexion − Wärmeabstrahlung. Ihre Änderung in W je m² Erde ist der Strahlungsantrieb φ; positiv wärmt, negativ kühlt.</p>
    <div class="eq tex rise" style="--d:900; font-size:26px">$$\\varphi_\\alpha(t) = \\tau_{\\mathrm{atm}}\\,\\Delta\\dot Q_{\\mathrm{Baum}}(t)\\,/\\,A_{\\mathrm{Erde}}$$</div></div>
    </div>
    <div class="foot"><div></div>
      <p class="takeaway" data-step="1" style="--d:0; font-size:21px">Beide Wirkungen des Baums ändern die Energiebilanz der Erde und werden als Strahlungsantrieb in W/m² vergleichbar. Für die Albedo ist das ein Schritt: die absorbierte Strahlung auf die Erdoberfläche verteilen, mit dem Anteil τ_atm ≈ 0,8, der die Atmosphäre verlassen hätte. Für das CO₂ folgen zwei Schritte.</p>
    </div>
  </div>
  <p class="src">Schema. Albedo-Antrieb: zusätzlich absorbierte Strahlung je Baum (Kapitel Bäume; Duveiller et al. 2018) mal τ_atm ≈ 0,8, geteilt durch A_Erde = 5,1 · 10¹⁴ m².</p>
  <aside class="notes" data-n="0">
    <p>Im Kapitel Bäume hatten wir zwei Wirkungen in zwei Einheiten: Kilogramm CO₂ und Watt Strahlung. Für das Klima zählt beides über dieselbe Größe: die Energiebilanz der Erde am Oberrand der Atmosphäre. Herein kommt Sonnenlicht, hinaus gehen das reflektierte Licht und die Wärmestrahlung der Erde. Ändert sich diese Bilanz, ändert sich die Temperatur. Die Änderung in Watt je Quadratmeter Erde heißt Strahlungsantrieb.</p>
    <p>Erstens die Albedo: Das dunkle Kronendach reflektiert weniger. Die zusätzlich absorbierte Strahlung haben wir in Watt je Baum schon berechnet — das ist bereits Energie. Wir verteilen sie auf die Erdoberfläche und berücksichtigen mit τ_atm, welcher Teil der Mehrreflexion die Atmosphäre tatsächlich verlassen hätte. Ein Schritt. Zweitens das CO₂: Weniger CO₂ in der Atmosphäre heißt mehr Wärmeabstrahlung. Dafür brauchen wir zwei Schritte — wie viel CO₂ der Atmosphäre fehlt, und wie stark jedes Kilogramm wirkt. Die kommen jetzt.</p>
    <p class="q">Falls Fragen kommen — τ_atm ≈ 0,8: Anteil der an der Oberfläche zusätzlich reflektierten Kurzwellenstrahlung, der den Oberrand erreicht. Die Verdunstung ist an dieser Grenze ein interner Fluss und kein Antrieb (Backup „Und die Verdunstung?“). Herleitung der Energiebilanz aus dem ersten Hauptsatz: Backup.</p>
  </aside>
</section>

"""

CO2_FORCING = '''<section class="slide" data-ch="klima" data-title="Strahlungsantrieb von CO₂">
  <header class="sh"><h2>Strahlungsantrieb von CO₂</h2></header>
  <div class="body">
    <div class="chart" data-slot-steps="0,1" data-chart="k6" data-label="Links Strahlungsantrieb des gesamten CO₂ über der Konzentration mit Tangenten 2025 und 2100; rechts Antrieb je kg CO₂ 2025 bis 2100"></div>
    <div class="foot">
      <div class="eq tex rise" style="--d:900; font-size:24px">$$\\begin{aligned}\\varphi(C) &= 5{,}35\\,\\tfrac{\\mathrm{W}}{\\mathrm{m^2}}\\,\\ln\\frac{C}{C_0}\\\\ A_{\\mathrm{CO_2}}(t) &= \\frac{\\partial\\varphi}{\\partial m} = \\frac{5{,}35\\,\\mathrm{W/m^2}}{k\\,C(t)}\\\\ \\varphi_{\\mathrm{CO_2}}(t) &= A_{\\mathrm{CO_2}}(t)\\,\\Delta m_{\\mathrm{CO_2}}(t)\\end{aligned}$$</div>
      <p class="takeaway" data-step="1" style="--d:1800; font-size:21px">CO₂ verringert die langwellige Abstrahlung der Erde; dieser Strahlungsantrieb wächst logarithmisch mit der Konzentration. Je mehr CO₂ bereits in der Atmosphäre ist, desto kleiner ist der Antrieb je zusätzlichem Kilogramm: im Szenario SSP2-4.5 1,65 · 10⁻¹⁵ W/m² im Jahr 2025, 1,31 · 10⁻¹⁵ W/m² im Jahr 2100. Mit der CO₂-Änderung aus der Impulsantwort ergibt das den Antrieb des Baums.</p>
    </div>
  </div>
  <p class="src">Antrieb: Myhre et al. 1998 (aus Strahlungstransfer-Modellen), C₀ = 278 ppm; k = 7,82 · 10¹² kg CO₂ je ppm; CO₂-Konzentration im Szenario SSP2-4.5: Modellergebnis FaIR (Leach et al. 2021; Smith et al. 2024).</p>
  <aside class="notes" data-n="0">
    <p>Die zweite Frage: Wie stark wärmt das CO₂, das in der Atmosphäre fehlt oder dazukommt? CO₂ absorbiert die Wärmestrahlung der Erde in bestimmten Wellenlängen. Mehr CO₂ heißt: Die Wärme wird aus größerer, kälterer Höhe abgestrahlt, also weniger davon — die Energiebilanz der Erde verschiebt sich. Diese Verschiebung in Watt je Quadratmeter Erdoberfläche heißt Strahlungsantrieb. Links: Für das gesamte CO₂ in der Luft wächst er logarithmisch mit der Konzentration — die Kurve wird flacher. Die Steigung ist der Antrieb je zusätzlichem Kilogramm; 2025 ist sie steiler als 2100, weil bis dahin mehr CO₂ in der Luft ist. Rechts diese Steigung über die Zeit: 1,65 heute, 1,31 im Jahr 2100, in 10⁻¹⁵ Watt je Quadratmeter und Kilogramm. Unten die drei Zeilen: Antrieb des gesamten CO₂, seine Ableitung je Kilogramm, und mal der CO₂-Änderung des Baums aus der Impulsantwort — das ist der Antrieb, den der Baum über seinen Kohlenstoff erzeugt.</p>
    <p class="q">Falls Fragen kommen — Myhre et al. (1998): ΔF = 5,35 · ln(C/C₀) W/m², aus Strahlungstransfer-Rechnungen; für kleine Änderungen linearisiert, A_CO₂ = 5,35 / (k · C). FaIR selbst nutzt eine genauere, zustandsabhängige Formel (Meinshausen et al. 2020); entlang SSP2-4.5 weicht der Koeffizient um höchstens 2,5 % ab. Der Lehrbuchwert 1,76 · 10⁻¹⁵ W/m² je kg (IPCC AR6) entspricht etwa 389 ppm. Spektrum und Höhe der Abstrahlung: Backup „Warum CO₂ wärmt“.</p>
  </aside>
</section>

'''


def patch(page: str) -> str:
    def rep(old, new, count=1):
        nonlocal page
        assert old in page, old[:80]
        page = page.replace(old, new, count)

    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)

    # --- end of the Bäume chapter: b9 back in, b10 (energy, naive) to the live backup
    backup, b9 = _take(backup, "Was der Baum mit seiner Umgebung tauscht")
    b9_backup = b9
    main, b10 = _take(main, "Gemeinsame Währung: Energie")
    b9 = b9.replace('data-title="Was der Baum mit seiner Umgebung tauscht"', 'data-title="CO₂-Aufnahme und absorbierte Strahlung"')
    b9 = b9.replace("<h2>Was der Baum mit seiner Umgebung tauscht</h2>", "<h2>CO₂-Aufnahme und zusätzlich absorbierte Strahlung je Baum</h2>")
    b9 = re.sub(r'<p class="takeaway" data-step="1" style="--d:1800">.*?</p>',
                '<p class="takeaway" data-step="1" style="--d:1800">CO₂-Aufnahme in Kilogramm und zusätzlich absorbierte Sonnenstrahlung in Watt sind nicht direkt vergleichbar. Dafür braucht es das Klimasystem: Wie entwickelt sich die CO₂-Änderung in der Atmosphäre, welchen Strahlungsantrieb erzeugt sie, und welche Temperaturänderung folgt?</p>',
                b9, flags=re.S)
    b9 = b9.replace('<aside class="notes">', '<aside class="notes" data-n="0">', 1)
    b9 = b9.replace("Durchgehende Linien kommen erst im Kapitel Klima, wenn das Klimasystem antwortet.</p>",
                    "Durchgehende Linien kommen erst im Kapitel Klima, wenn das Klimasystem antwortet. Die Frage, wie man Kilogramm und Watt vergleicht, beantwortet das nächste Kapitel: Beide werden zu einem Strahlungsantrieb und dann zu einer Temperatur.</p>")
    anchor = "<!-- =====================================================\n     KAPITEL: KLIMA"
    assert anchor in main
    _ = b9  # 2026-10-07: the kg-or-W question is the closing sentence of the last albedo slide instead

    old_b8 = "Beim Licht ist es umgekehrt: Wo Schnee liegt und die Sonne kräftig ist, schluckt der Baum am meisten — Aachen (DE) 34 W, Joensuu (FI) 45 W und Marabá (BR) 21 W im Jahresmittel."
    assert old_b8 in main
    main = main.replace(old_b8, "Die zusätzlich absorbierte Strahlung ist dort am größten, wo Schnee liegt und die Einstrahlung hoch ist: im Jahresmittel Aachen (DE) 34 W, Joensuu (FI) 45 W, Marabá (BR) 21 W je ausgewachsenem Baum. Damit liegen beide Wirkungen vor, in zwei Einheiten: CO₂-Aufnahme in kg, absorbierte Strahlung in W. Wie sie auf das Klima wirken, zeigt das nächste Kapitel.")

    # --- Klima: take the sections out and put them back in order
    secs = {}
    for t in ("Ozean und Land antworten", "Das Erdsystem rechnen: FaIR", "Was der Luft wirklich fehlt",
              "Kohlenstoff und Licht in einer Währung", "Die Erde erwärmt sich träge",
              "Die Erwärmung wirkt auf den Baum zurück", "Was ein Baum wo bewirkt"):
        main, secs[t] = _take(main, t)

    oz = secs["Ozean und Land antworten"]
    oz = oz.replace('data-title="Ozean und Land antworten"', 'data-title="Impulsantwort des Kohlenstoffkreislaufs"')
    oz = oz.replace("<h2>Ozean und Land antworten: bei Emission wie bei Entnahme</h2>",
                    "<h2>Impulsantwort des Kohlenstoffkreislaufs: Zusatzemission und Entnahme</h2>")
    oz = re.sub(r'<p class="takeaway" data-step="2" style="--d:0; font-size:21px">.*?</p>',
                '<p class="takeaway" data-step="2" style="--d:0; font-size:21px">Nach einer Zusatzemission nehmen Ozean und Landbiosphäre einen Teil des CO₂ auf: Nach 20 Jahren verbleiben 60 % in der Atmosphäre, nach 50 Jahren 49 %. Für eine Entnahme gilt dieselbe Impulsantwort mit umgekehrtem Vorzeichen: Ozean und Land geben CO₂ ab, die atmosphärische Änderung klingt ebenso ab.</p>',
                oz, flags=re.S)
    oz = oz.replace("Wie stark das fehlende CO₂ dann wirkt, ist die zweite Frage — die kommt zwei Folien weiter.",
                    "Wie stark diese CO₂-Änderung wärmt oder kühlt, ist die zweite Frage — der Strahlungsantrieb, gleich nach dem Beispiel des Baums.")
    oz = oz.replace("Im Modell rechnet das FaIR (nächste Folie), vor dem steigenden Hintergrund von SSP2-4,5",
                    "Im Modell rechnet das FaIR (Folie „Das Erdsystem rechnen“), vor dem steigenden Hintergrund von SSP2-4,5")

    lf = secs["Was der Luft wirklich fehlt"]
    lf = lf.replace('data-title="Was der Luft wirklich fehlt"', 'data-title="Impulsantwort auf die CO₂-Aufnahme eines Baums"')
    lf = lf.replace("<h2>Was der Luft wirklich fehlt</h2>", "<h2>Impulsantwort auf die CO₂-Aufnahme eines Baums</h2>")
    lf = re.sub(r'<p class="takeaway" data-step="1" style="--d:1800; font-size:22px">.*?</p>',
                '<p class="takeaway" data-step="1" style="--d:1800; font-size:22px">Jede jährliche Aufnahme des Baums ist eine kleine Entnahme, die mit g<sub>C</sub> abklingt. Summiert über alle Jahre (Faltung) ist die Abnahme des atmosphärischen CO₂ 2100 gut halb so groß wie die aufgenommene Menge, in Aachen (DE) 84 von 164 kg. Um 2090 erreicht sie ihr Maximum: Danach nimmt der ausgewachsene Wald kaum noch auf, Ozean und Land geben weiter CO₂ ab — 2200 noch 68 von 177 kg.</p>',
                lf, flags=re.S)

    k10 = secs["Kohlenstoff und Licht in einer Währung"]
    k10 = k10.replace('data-title="Kohlenstoff und Licht in einer Währung"', 'data-title="Gesamter Strahlungsantrieb je Baum"')
    k10 = k10.replace("<h2>Kohlenstoff und Licht in einer Währung</h2>", "<h2>Gesamter Strahlungsantrieb je Baum</h2>")
    k10 = k10.replace("$$\\begin{aligned}\\varphi_{\\mathrm{CO_2}}(t) &= A_{\\mathrm{CO_2}}(t)\\,\\Delta m_{\\mathrm{CO_2}}(t)\\\\ \\varphi_\\alpha(t) &= \\tau_{\\mathrm{atm}}\\,\\Delta\\dot Q(t)\\,/\\,A_{\\mathrm{Erde}}\\end{aligned}$$",
                      "$$\\varphi(t) = \\varphi_{\\mathrm{CO_2}}(t) + \\varphi_\\alpha(t)$$")
    k10 = re.sub(r'<p class="takeaway" data-step="1" style="--d:1800; font-size:21px">.*?</p>',
                 '<p class="takeaway" data-step="1" style="--d:1800; font-size:21px">Beide Antriebe in derselben Einheit, addiert: An allen drei Orten überwiegt der kühlende CO₂-Antrieb; in Joensuu (FI) gleicht der Albedo-Antrieb einen großen Teil aus, bei Marabá (BR) nur wenig. Der Albedo-Antrieb wächst mit dem Kronenschluss, der CO₂-Antrieb mit dem Vorrat, abgeschwächt durch Impulsantwort und vollere Atmosphäre.</p>',
                 k10, flags=re.S)
    k10 = re.sub(r'<p class="src">.*?</p>',
                 '<p class="src">Eigene Rechnung: CO₂-Antrieb wie auf der Vorfolie; Albedo-Antrieb aus der gemessenen Albedo-Änderung (Duveiller et al. 2018) und dem Kronenschluss (Williams et al. 2026), τ_atm ≈ 0,8; typischer Wald je Ort, gepflanzt 2025, SSP2-4.5.</p>',
                 k10, flags=re.S)
    k10 = re.sub(r'<aside class="notes" data-n="\d+">.*?</aside>', '''<aside class="notes" data-n="0">
    <p>Jetzt laufen beide Wege zusammen: der Albedo-Antrieb vom Anfang des Kapitels und der CO₂-Antrieb, den wir eben in zwei Schritten gebaut haben. Beide in Watt je Quadratmeter Erde, also lassen sie sich addieren. Grün kühlt der Kohlenstoff, orange wärmt die Albedo, schwarz die Summe. An allen drei Orten bleibt die Summe kühlend; in Joensuu holt die Albedo einen großen Teil auf.</p>
    <p class="q">Falls Fragen kommen — τ_atm ≈ 0,8: Anteil der an der Oberfläche zusätzlich reflektierten Strahlung, der den Oberrand der Atmosphäre erreicht (Wolken und Gase absorbieren einen Teil). A_Erde = 5,1 · 10¹⁴ m². Herleitung der Energiebilanz und der Verdunstung, die an dieser Grenze nicht als Antrieb zählt: Backup.</p>
  </aside>''', k10, flags=re.S)

    tr = secs["Die Erde erwärmt sich träge"]
    tr = tr.replace('data-title="Die Erde erwärmt sich träge"', 'data-title="Temperaturantwort auf den Strahlungsantrieb"')
    tr = tr.replace("<h2>Die Erde erwärmt sich träge</h2>", "<h2>Temperaturantwort auf den Strahlungsantrieb</h2>")
    tr = re.sub(r'<div class="foot"><div></div><p class="takeaway" data-step="1" style="--d:1800; font-size:22px">.*?</p></div>',
                lambda m: '<div class="foot"><div class="eq tex rise" style="--d:900; font-size:24px">$$\\begin{aligned}C\\,\\frac{\\mathrm{d}T}{\\mathrm{d}t} &= \\varphi(t) - \\Lambda\\,T(t)\\\\ \\Delta T(t) &= \\sum_{t\' \\le t} g_T(t-t\')\\,\\varphi(t\')\\end{aligned}$$</div><p class="takeaway" data-step="1" style="--d:1800; font-size:21px">Die Temperatur folgt dem Antrieb verzögert: Die Oberfläche reagiert in Jahren, der tiefe Ozean über Jahrhunderte (links, Sprungantwort). Gefaltet mit dem Antrieb des Baums ergibt sich seine Temperaturwirkung (rechts). Gestrichelt nur der CO₂-Anteil: Nach Albedo bleiben 2100 in Aachen (DE) 65 %, in Joensuu (FI) 32 %, bei Marabá (BR) 83 % — der Netto-Anteil.</p></div>',
                tr, flags=re.S)
    tr = tr.replace("<p>Links: So reagiert die Erde auf ein dauerhaft zusätzliches Watt je Quadratmeter",
                    "<p>Oben die Energiebilanz der Erde in ihrer einfachsten Form: Die Wärmekapazität C mal die Erwärmungsrate ist der Antrieb minus das, was die wärmere Erde zusätzlich abstrahlt, Λ mal T. Ihre Lösung ist wieder eine Impulsantwort, diesmal für die Temperatur: g_T. Links: So reagiert die Erde auf ein dauerhaft zusätzliches Watt je Quadratmeter")

    fa = secs["Das Erdsystem rechnen: FaIR"]
    fa = fa.replace("Ozean, Land, Atmosphäre und Temperatur hängen eng zusammen; im Detail rechnen das Erdsystemmodelle auf Großrechnern.",
                    "Impulsantwort, Strahlungsantrieb und Temperaturantwort sind im Erdsystem gekoppelt und hängen vom Zustand der Erde ab; im Detail rechnen das Erdsystemmodelle auf Großrechnern.")
    fa = fa.replace("<p>Was wir eben für eine Tonne gesehen haben, ist nur ein Teil eines eng gekoppelten Systems:",
                    "<p>Die drei Schritte haben wir eben einzeln aufgebaut. In der Wirklichkeit sind sie eng gekoppelt:")
    fa = fa.replace("In der Mitte rechnet FaIR selbst die drei Schritte, die die nächsten Folien für unseren Baum zeigen: Kohlenstoffkreislauf, Antrieb, Temperatur.",
                    "In der Mitte rechnet FaIR selbst die drei Schritte, die wir eben für den Baum aufgebaut haben: Kohlenstoffkreislauf, Antrieb, Temperatur. Die Erwärmung des Szenarios wirkt außerdem auf den Baum zurück: Die Störungsrate steigt mit der Temperatur (p = p₀ e^γT, Kapitel Bäume); bis 2100 ändert das die Wirkung je Baum kaum, in Aachen von −34 auf −35 · 10⁻¹⁵ K.")

    order = [FRAME, oz, lf, CO2_FORCING, k10, tr, fa, secs["Was ein Baum wo bewirkt"]]
    anchor = "<!-- =====================================================\n     KAPITEL: VERGLEICH"
    assert anchor in main
    klima_chapter_end = main.index(anchor)
    # the chapter slide stays where it is; the content slides follow it
    chap = re.search(r'<section class="slide chapter" data-ch="klima".*?</section>\n\n?', main, flags=re.S)
    insert_at = chap.end()
    main = main[:insert_at] + "".join(order) + main[insert_at:]
    _ = klima_chapter_end

    # chapter subtitle and overview
    main = main.replace('<p class="rise" style="--d:300">Wie lange fehlt das CO₂ — und wie stark wirkt es?</p>',
                        '<p class="rise" style="--d:300">Strahlungsantrieb, Impulsantwort und Temperatur</p>')
    main = main.replace('font-size="21">Wie lange fehlt das CO₂ —</text>', 'font-size="21">Strahlungsantrieb, Impuls-</text>')
    main = main.replace('font-size="21">und wie stark wirkt es?</text>', 'font-size="21">antwort, Temperatur</text>')

    # the model slide of the Bäume chapter: the feedback stays in the model, as a side note
    main = main.replace("in PowerPoint ausgrauen, eingelöst auf „Die Erwärmung wirkt auf den Baum zurück“.",
                        "in PowerPoint ausgrauen. Im Modell ist die Rückkopplung enthalten (Hintergrund-Erwärmung aus FaIR); bis 2100 ändert sie die Wirkung je Baum kaum (Aachen −34 → −35 · 10⁻¹⁵ K), deshalb keine eigene Folie (Backup „Die Erwärmung wirkt auf den Baum zurück“).")

    moved = b9_backup + b10 + re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', secs["Die Erwärmung wirkt auf den Baum zurück"])
    moved = re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', moved)
    backup = backup.replace("<!-- KAPITEL 1-2, aus dem Hauptteil genommen (2026-10-06): live im Backup. -->\n",
                            "<!-- KAPITEL 1-2, aus dem Hauptteil genommen (2026-10-06/07): live im Backup. -->\n" + moved, 1)

    # titles in a scientific register (h2, data-title and quoted references in texts and notes)
    for old, new in (("Was der Baum der Luft entnimmt", "CO₂-Aufnahme je Baum"),
                     ("Zwei Zutaten: Sonne und Schnee", "Einstrahlung und Albedo-Kontrast"),
                     ("Zusätzlich absorbiertes Licht: je nach Ort", "Zusätzlich absorbierte Strahlung je Baum"),
                     ("Welcher Wald wo wächst", "Typischer Waldtyp je Ort"),
                     ("Was ein Baum wo bewirkt", "Temperaturwirkung eines Baums je Ort"),
                     ("Wo Bäume hinkönnen", "Wiederbewaldbare Fläche"),
                     ("Alle Bäume zusammen, Jahr für Jahr", "Globale Temperaturwirkung aller Bäume über die Zeit"),
                     ("Wann pflanzen? Warten kostet vor allem bis zur Jahrhundertmitte", "Einfluss des Pflanzjahres"),
                     ("Wie eine Maschine CO₂ aus der Luft holt", "Sorbens-DAC: Prozess und Energiebedarf"),
                     ("Wie wir DAC rechnen: je Ort und je Jahr", "DAC-Modell: je Ort und je Jahr"),
                     ("Was für diese Antworten nötig war", "Methodischer Beitrag")):
        main = main.replace(f"<h2>{old}</h2>", f"<h2>{new}</h2>").replace(f"„{old}“", f"„{new}“")
        backup = backup.replace(f"„{old}“", f"„{new}“")
    for old, new in (('data-title="Was der Baum der Luft entnimmt"', 'data-title="CO₂-Aufnahme je Baum"'),
                     ('data-title="Zwei Zutaten: Sonne und Schnee"', 'data-title="Einstrahlung und Albedo-Kontrast"'),
                     ('data-title="Zusätzlich absorbiertes Licht"', 'data-title="Zusätzlich absorbierte Strahlung"'),
                     ('data-title="Welcher Wald wo wächst"', 'data-title="Typischer Waldtyp je Ort"'),
                     ('data-title="Was ein Baum wo bewirkt"', 'data-title="Temperaturwirkung eines Baums je Ort"'),
                     ('data-title="Wo Bäume hinkönnen"', 'data-title="Wiederbewaldbare Fläche"'),
                     ('data-title="Alle Bäume, Jahr für Jahr"', 'data-title="Globale Temperaturwirkung über die Zeit"'),
                     ('data-title="Wann pflanzen?"', 'data-title="Einfluss des Pflanzjahres"'),
                     ('data-title="Wie eine Maschine CO₂ aus der Luft holt"', 'data-title="Sorbens-DAC: Prozess und Energiebedarf"'),
                     ('data-title="Wie wir DAC rechnen"', 'data-title="DAC-Modell"'),
                     ('data-title="Was für diese Antworten nötig war"', 'data-title="Methodischer Beitrag"')):
        main = main.replace(old, new)
    main = main.replace("<h2>Impulsantwort auf die CO₂-Aufnahme eines Baums</h2>", "<h2>Impulsantwort auf die CO₂&#8209;Aufnahme eines Baums</h2>")

    n = iter(range(1, 1000))
    main = re.sub(r'<aside class="notes" data-n="\d+">', lambda m: f'<aside class="notes" data-n="{next(n)}">', main)
    return main + "<!-- BACKUP:BEGIN -->" + backup
