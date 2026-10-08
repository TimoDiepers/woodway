"""Klima chapter: how the Earth system is computed -- FaIR, calibrated on Earth system models, run with
and without the trees (after 'Ozean und Land antworten')."""

SVG = '''<svg class="schema" data-export="s_fair" viewBox="0 0 1424 470" style="width:100%; flex:1; min-height:0" aria-label="Eingaben CO2-Fluss und Albedo-Antrieb gehen in FaIR; FaIR rechnet Kohlenstoffkreislauf, Antrieb und Temperatur; das Szenario einmal wie es ist und einmal mit unseren Bäumen zusätzlich; die Differenz ist ihr Beitrag">
  <defs><marker id="ah-fa" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="var(--muted)"/></marker></defs>
  <g font-family="IBM Plex Sans">
    <g class="pop" style="--d:100">
      <text x="0" y="30" font-size="16" letter-spacing="1.5" fill="var(--muted)">EINGABE, JAHR FÜR JAHR</text>
      <rect x="0" y="50" width="330" height="150" rx="10" fill="var(--paper-deep)" stroke="var(--co2)" stroke-width="3"/>
      <circle cx="30" cy="84" r="16" fill="var(--co2)"/><text x="30" y="91" text-anchor="middle" font-size="18" font-weight="600" fill="var(--paper)">1</text>
      <text x="56" y="92" font-size="23" font-weight="600" fill="var(--ink)">CO₂-Fluss der Bäume</text>
      <text x="20" y="130" font-size="19" fill="var(--ink-2)">geht als negative Emission</text>
      <text x="20" y="158" font-size="19" fill="var(--ink-2)">zu allen anderen Emissionen</text>
      <text x="20" y="186" font-size="17" fill="var(--muted)">Gt CO₂ je Jahr</text>
      <rect x="0" y="230" width="330" height="150" rx="10" fill="var(--paper-deep)" stroke="var(--alb)" stroke-width="3"/>
      <circle cx="30" cy="264" r="16" fill="var(--alb)"/><text x="30" y="271" text-anchor="middle" font-size="18" font-weight="600" fill="var(--paper)">2</text>
      <text x="56" y="272" font-size="23" font-weight="600" fill="var(--ink)">Albedo der Bäume</text>
      <text x="20" y="310" font-size="19" fill="var(--ink-2)">geht getrennt als zusätzlicher</text>
      <text x="20" y="338" font-size="19" fill="var(--ink-2)">Strahlungsantrieb ein</text>
      <text x="20" y="366" font-size="17" fill="var(--muted)">W je m² Erde</text>
      <path d="M336 125 H402" stroke="var(--muted)" stroke-width="3" fill="none" marker-end="url(#ah-fa)"/>
      <path d="M336 305 H402" stroke="var(--muted)" stroke-width="3" fill="none" marker-end="url(#ah-fa)"/>
    </g>
    <g class="pop" data-step="1">
      <rect x="410" y="20" width="560" height="400" rx="12" fill="var(--clay)"/>
      <text x="436" y="62" font-size="26" font-weight="600" fill="var(--paper)">FaIR, ein Klima-Emulator</text>
      <text x="436" y="92" font-size="17" fill="#ead7d2">kalibriert auf Erdsystemmodelle und Messungen</text>
      <text x="436" y="114" font-size="17" fill="#ead7d2">Hintergrund: Szenario SSP2-4,5</text>
      <rect x="436" y="138" width="508" height="76" rx="8" fill="#8b5450"/>
      <text x="456" y="170" font-size="21" font-weight="600" fill="var(--paper)">Kohlenstoffkreislauf</text>
      <text x="456" y="198" font-size="17" fill="#f1e3df">Ozean und Land antworten; Senken füllen sich</text>
      <rect x="436" y="226" width="508" height="76" rx="8" fill="#8b5450"/>
      <text x="456" y="258" font-size="21" font-weight="600" fill="var(--paper)">Antrieb</text>
      <text x="456" y="286" font-size="17" fill="#f1e3df">CO₂ wirkt je kg schwächer, je voller die Luft</text>
      <rect x="436" y="314" width="508" height="76" rx="8" fill="#8b5450"/>
      <text x="456" y="346" font-size="21" font-weight="600" fill="var(--paper)">Temperatur</text>
      <text x="456" y="374" font-size="17" fill="#f1e3df">Oberfläche in Jahren, tiefer Ozean über Jahrhunderte</text>
    </g>
    <g class="pop" data-step="2">
      <path d="M976 220 H1042" stroke="var(--muted)" stroke-width="3" fill="none" marker-end="url(#ah-fa)"/>
      <text x="1050" y="30" font-size="16" letter-spacing="1.5" fill="var(--muted)">ZWEI LÄUFE, GLEICHES SZENARIO</text>
      <rect x="1050" y="44" width="374" height="84" rx="10" fill="var(--paper-deep)" stroke="var(--paper-line)" stroke-width="2"/>
      <text x="1070" y="80" font-size="21" fill="var(--ink)">das Szenario, wie es ist</text>
      <text x="1070" y="108" font-size="16" fill="var(--muted)">mit seiner Landnutzung und Entnahme</text>
      <rect x="1050" y="140" width="374" height="84" rx="10" fill="var(--paper-deep)" stroke="var(--paper-line)" stroke-width="2"/>
      <text x="1070" y="176" font-size="21" fill="var(--ink)">dasselbe + unsere Bäume</text>
      <text x="1070" y="204" font-size="16" fill="var(--muted)">eine kleine zusätzliche Störung</text>
      <rect x="1050" y="268" width="374" height="130" rx="10" fill="var(--clay)"/>
      <text x="1070" y="310" font-size="23" font-weight="600" fill="var(--paper)">Beitrag der Bäume</text>
      <text x="1070" y="348" font-size="21" fill="var(--paper)">ΔT(t) = Differenz</text>
      <text x="1070" y="380" font-size="17" fill="#ead7d2">Jahr für Jahr, in K</text>
      <path d="M1237 228 V262" stroke="var(--muted)" stroke-width="3" fill="none" marker-end="url(#ah-fa)"/>
    </g>
  </g>
</svg>'''

SEC = f'''<section class="slide" data-ch="klima" data-title="Das Erdsystem rechnen: FaIR">
  <header class="sh"><h2>Das Erdsystem rechnen: ein kalibrierter Klima-Emulator</h2></header>
  <div class="body">
    {SVG}
    <div class="foot"><div></div><p class="takeaway" data-step="3" style="--d:0; font-size:21px">Ozean, Land, Atmosphäre und Temperatur hängen eng zusammen; im Detail rechnen das Erdsystemmodelle auf Großrechnern. FaIR bildet ihr Verhalten nach, kalibriert auf diese Modelle und auf Messungen, und rechnet ein Szenario in Sekunden. Die Szenarien enthalten schon Landnutzung und Entnahme. Wir stören sie nur: Unsere Bäume kommen als kleiner zusätzlicher CO₂-Fluss und Albedo-Antrieb hinzu. Die Differenz zeigt, was diese Bäume in einer solchen Welt leisten.</p></div>
  </div>
  <p class="src">FaIR 2.2 (Leach et al. 2021), Parametersatz fair-calibrate 1.4.1 (Smith et al. 2024): beschränkt durch beobachtete Erwärmung, Ozeanwärme und CO₂ sowie die IPCC-Bewertung, abgeglichen mit CMIP6-Modellen; ein Mitglied nahe dem Median (ECS 2,9 K). Emissionen SSP2-4,5 aus RCMIP (Nicholls et al. 2020).</p>
  <aside class="notes" data-n="0">
    <p>Was wir eben für eine Tonne gesehen haben, ist nur ein Teil eines eng gekoppelten Systems: Wie viel CO₂ Ozean und Land aufnehmen, hängt davon ab, wie voll sie schon sind und wie warm es ist; wie stark ein Kilogramm wärmt, hängt davon ab, wie viel CO₂ schon in der Luft ist; und die Erde erwärmt sich träge. Im Detail rechnen das Erdsystemmodelle — große Programme, die auf Großrechnern Wochen für ein Szenario brauchen. Für unsere Frage brauchen wir viele Läufe; deshalb nutzen wir FaIR, einen Klima-Emulator. FaIR ist ein kleines Modell aus wenigen Gleichungen, dessen Parameter so eingestellt sind, dass es die großen Modelle und die Messungen nachbildet. Ein Szenario dauert Sekunden.</p>
    <p>So setzen wir es ein. Wichtig: Ein Szenario wie SSP2-4,5 ist keine Welt ohne Bäume — es enthält schon Landnutzung, Abholzung und Aufforstung, die CMIP7-Szenarien dazu viel Entnahme. Wir rechnen das Szenario deshalb zweimal: einmal so, wie es ist, und einmal mit unseren Bäumen als kleine zusätzliche Störung obendrauf. Die Differenz ist ihr Beitrag. Weil die Störung klein ist, reagiert das System linear; wir rechnen also aus dem Szenario zurück, was eine Tonne aus unseren Bäumen in dieser Welt bewirkt — egal, ob ein Teil davon im Szenario schon eingeplant ist. Links die Eingaben: Erstens der CO₂-Fluss der Bäume, Jahr für Jahr — er geht als negative Emission zu allen anderen Emissionen dazu. Zweitens die Albedo, getrennt, als zusätzlicher Strahlungsantrieb in Watt je Quadratmeter. In der Mitte rechnet FaIR selbst die drei Schritte, die die nächsten Folien für unseren Baum zeigen: Kohlenstoffkreislauf, Antrieb, Temperatur. Rechts: Die Differenz der beiden Läufe ist der Beitrag der Bäume zur Temperatur, Jahr für Jahr.</p>
    <p class="q">Falls Fragen kommen — Technisch: Der Netto-CO₂-Fluss der Bäume wird zu den fossilen CO₂-Emissionen des Szenarios addiert, der Albedo-Antrieb zum vorgegebenen Antrieb (wie die Sonne, er wird nicht aus Emissionen berechnet). Ein einzelner Baum ändert die Temperatur um 10⁻¹⁵ K — das liegt unter der Rechengenauigkeit eines einzelnen Laufs. Für einen Baum nutzen wir deshalb FaIRs eigene Antworten auf einen kleinen Puls (eine Gigatonne CO₂ bzw. ein Antriebspuls) und summieren Jahr für Jahr auf; für die ganze Fläche rechnen wir direkt den gestörten Lauf. Beide Wege liefern dasselbe (17 % gegen 18 % bis 2100). Das Mitglied 787474 wurde nach einer vorab festgelegten Regel gewählt (am nächsten am Median in historischer Erwärmung und in vier Szenarien); docs/methods/klimamodell-fair.md. Verdunstung und Wolken als eigener Antrieb sind nicht enthalten.</p>
  </aside>
</section>

'''


def patch(page: str) -> str:
    anchor = '<section class="slide" data-ch="klima" data-title="Was der Luft wirklich fehlt">'
    assert anchor in page
    page = page.replace(anchor, SEC + anchor, 1)
    old = "Ab der übernächsten Folie rechnet das Modell mit der Antwort von FaIR vor dem steigenden Hintergrund von SSP2-4,5"
    assert old in page
    page = page.replace(old, "Im Modell rechnet das FaIR (nächste Folie), vor dem steigenden Hintergrund von SSP2-4,5", 1)
    return page
