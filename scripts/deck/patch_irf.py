"""Klima chapter: a slide on how ocean and land answer a pulse, in front of 'Was der Luft wirklich fehlt'."""


def _row(y0, step, label, sign, verb, rev):
    d = lambda x1, y1, x2, y2: f'<path d="M{x1} {y1} L{x2} {y2}" stroke="var(--co2)" stroke-width="4" fill="none" marker-end="url(#ah-oz)"/>'
    a1 = d(372, y0 + 62, 212, y0 + 76) if rev else d(212, y0 + 76, 372, y0 + 62)
    a2 = d(372, y0 + 126, 212, y0 + 108) if rev else d(212, y0 + 108, 372, y0 + 126)
    st = f' data-step="{step}"' if step else ' style="--d:100"'
    return f'''        <g class="pop"{st}>
          <text x="0" y="{y0 + 14}" font-size="16" letter-spacing="1.5" fill="var(--muted)">{label}</text>
          <rect x="0" y="{y0 + 30}" width="204" height="124" rx="10" fill="#dfe9ef" stroke="var(--paper-line)" stroke-width="2"/>
          <text x="20" y="{y0 + 66}" font-size="24" font-weight="600" fill="var(--ink)">Atmosphäre</text>
          <text x="20" y="{y0 + 112}" font-size="30" font-weight="600" fill="{'#8c6d5a' if sign == '+' else 'var(--co2)'}">{'+' if sign == '+' else '−'}1 t CO₂</text>
          <rect x="380" y="{y0 + 30}" width="230" height="56" rx="10" fill="#cfe0ea" stroke="var(--paper-line)" stroke-width="2"/>
          <text x="398" y="{y0 + 66}" font-size="22" font-weight="600" fill="var(--ink)">Ozean</text>
          <rect x="380" y="{y0 + 98}" width="230" height="56" rx="10" fill="#dde3cc" stroke="var(--paper-line)" stroke-width="2"/>
          <text x="398" y="{y0 + 134}" font-size="22" font-weight="600" fill="var(--ink)">Land</text>
          <text x="398" y="{y0 + 134}" dx="64" font-size="17" fill="var(--muted)">Pflanzen, Böden</text>
          {a1}
          {a2}
          <text x="292" y="{y0 + 168}" text-anchor="middle" font-size="19" font-weight="600" fill="var(--co2)">{verb}</text>
        </g>'''


SEC = f'''<section class="slide" data-ch="klima" data-title="Ozean und Land antworten">
  <header class="sh"><h2>Ozean und Land antworten: bei Emission wie bei Entnahme</h2></header>
  <div class="body">
    <div style="display:grid; grid-template-columns:640px 1fr; gap:28px; flex:1; min-height:0; align-items:center">
      <svg class="schema" data-export="s_ozean_land" viewBox="0 0 620 400" style="width:100%; height:auto" aria-label="Emission: Ozean und Land nehmen einen Teil auf; Entnahme: Ozean und Land geben einen Teil ab">
        <defs><marker id="ah-oz" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="var(--co2)"/></marker></defs>
        <g font-family="IBM Plex Sans">
{_row(0, 0, "EMISSION", "+", "nehmen einen Teil auf", False)}
{_row(210, 1, "ENTNAHME", "-", "geben einen Teil ab", True)}
        </g>
      </svg>
      <div class="chart" data-chart="k3" style="height:100%" data-label="Impulsantwort: was von einer emittierten Tonne in der Luft bleibt und was von einer entnommenen Tonne der Luft fehlt, 75 Jahre"></div>
    </div>
    <div class="foot">
      <div class="rise" style="--d:900">
        <div class="eq tex">$$g_C(t) = a_0 + \\sum_{{i=1}}^{{3}} a_i\\, e^{{-t/\\tau_i}}$$</div>
        <p style="font:400 16px/1.4 var(--sans); color:var(--muted); margin-top:4px">a₀ ≈ 22 % bleibt auf Dauer; τ ≈ 4, 37 und 394 Jahre</p>
      </div>
      <p class="takeaway" data-step="2" style="--d:0; font-size:21px">Kommt eine Tonne CO₂ in die Luft, nehmen Ozean und Land über Jahrzehnte einen Teil auf: Nach 20 Jahren sind noch 60 % in der Luft, nach 50 Jahren 49 %. Bei einer Entnahme läuft es umgekehrt: Ozean und Land geben einen Teil ab. Was der Luft fehlt, folgt derselben Kurve g<sub>C</sub>.</p>
    </div>
  </div>
  <p class="src">Impulsantwort: Modellergebnis, Mittel mehrerer Erdsystem- und Kohlenstoffkreislaufmodelle (Joos et al. 2013), Puls vor heutigem Hintergrund. Für Entnahmen gleicher Größe annähernd spiegelbildlich (Zickfeld et al. 2015).</p>
  <aside class="notes" data-n="0">
    <p>Bevor wir zum Baum zurückgehen, ein Schritt zurück. Die Luft ist kein abgeschlossener Behälter: Sie tauscht ständig CO₂ mit dem Ozean und mit dem Land aus, also mit Pflanzen und Böden. Oben eine Emission: Eine Tonne CO₂ kommt in die Luft. Ozean und Land nehmen über die Jahre einen Teil davon auf — nach 20 Jahren sind noch 60 % in der Luft, nach 50 Jahren knapp die Hälfte, und gut ein Fünftel bleibt praktisch auf Dauer. Diese Kurve heißt Impulsantwort, g_C, und unten steht ihre Form: ein Rest, der bleibt, plus drei Anteile, die mit eigenen Zeitkonstanten abklingen — Jahre, Jahrzehnte, Jahrhunderte.</p>
    <p>Unten der Fall, um den es uns geht: Eine Tonne wird der Atmosphäre entnommen. Dann läuft der Austausch umgekehrt: Ozean und Land enthalten jetzt relativ zur Atmosphäre zu viel CO₂ und geben einen Teil ab. Die atmosphärische Änderung klingt mit derselben Impulsantwort ab. Das ist der erste Schritt über den Baum hinaus: Was der Baum aufnimmt, ist nicht in voller Höhe und nicht dauerhaft eine CO₂-Änderung der Atmosphäre. Wie stark das fehlende CO₂ dann wirkt, ist die zweite Frage — die kommt zwei Folien weiter.</p>
    <p class="q">Falls Fragen kommen — Joos et al. (2013), Mittel aus Erdsystem- und Boxmodellen für einen Puls vor heutigem Hintergrund: a₀ = 0,217; a = 0,224 / 0,282 / 0,276; τ = 394 / 36,5 / 4,3 Jahre. Physikalisch: schnelle Durchmischung mit der Deckschicht des Ozeans, langsamer Austausch mit der Tiefsee, ganz langsam Karbonatchemie und Verwitterung; dazu das Land über Photosynthese und Böden. Entnahme spiegelbildlich: Für kleine Pulse gilt das gut (Zickfeld et al. 2015 finden für große Entnahmen eine leichte Asymmetrie). Ab der übernächsten Folie rechnet das Modell mit der Antwort von FaIR vor dem steigenden Hintergrund von SSP2-4,5 (2100: 42 % statt 44 % eines Pulses von 2025 noch in der Luft).</p>
  </aside>
</section>

'''


def patch(page: str) -> str:
    anchor = '<section class="slide" data-ch="klima" data-title="Was der Luft wirklich fehlt">'
    assert anchor in page
    page = page.replace(anchor, SEC + anchor, 1)

    def rep(old, new):
        nonlocal page
        assert old in page, old[:70]
        page = page.replace(old, new, 1)

    rep('<div class="foot"><div></div><p class="takeaway" data-step="1" style="--d:1800">Balken: was der Baum geholt hat, wie im Kapitel Bäume. Linien: was der Luft davon wirklich fehlt, wenn Ozean und Land antworten. Von einem Jahr fehlt nach 20 Jahren noch 60 %, nach 50 Jahren 49 % — über alle Jahre bis 2100 gut die Hälfte.</p></div>',
        '<div class="foot"><div class="eq tex rise" style="--d:1800">$$\\Delta m_{\\mathrm{CO_2}}(t) = \\sum_{t\' \\le t} g_C(t-t\')\\, \\dot m_{\\mathrm{CO_2}}(t\')$$</div><p class="takeaway" data-step="1" style="--d:1800; font-size:22px">Jetzt der Baum: Jedes Jahr ist eine kleine Entnahme, die nach g<sub>C</sub> abklingt. Balken: was der Baum bisher geholt hat; Linie: was davon der Luft fehlt. Aufsummiert über alle Jahre fehlt der Luft bis 2100 gut die Hälfte dessen, was der Baum geholt hat — in Aachen (DE) 84 von 164 kg.</p></div>')
    rep('<p>Frage 1: Wie lange fehlt das CO₂ der Luft? Sprechertext: Links ein einziges Jahr Zuwachs, 2050. Am Baum bilanziert wäre es für immer weg, gestrichelt. Aber Luft, Ozean und Landbiosphäre stehen im Austausch: Fehlt oben CO₂, nehmen Ozean und Land weniger auf und geben zurück. Was übrig bleibt, die durchgezogene Linie, heißt g_C. Rechts dasselbe für jedes Jahr, aufsummiert.</p>',
        '<p>Dieselbe Antwort, jetzt für den Baum. Der Baum entnimmt jedes Jahr ein bisschen; jede dieser kleinen Entnahmen klingt für sich nach der Kurve von eben ab. Die Balken zeigen, was der Baum bis dahin insgesamt geholt hat, die Linien, was davon der Luft noch fehlt — das ist die Formel unten: jede Jahresentnahme mal dem Anteil, der bis heute noch fehlt. Bis 2100 fehlt der Luft gut die Hälfte dessen, was der Baum geholt hat.</p>')
    rep('<div class="chart" data-slot-steps="0,1" data-chart="k5" data-label="Links ein Jahr Entnahme 2050 und was davon der Luft fehlt; rechts alle Jahre"></div>',
        '<div class="chart" data-chart="k5" data-label="Je Baum: bisher geholtes CO₂ (Balken) und was davon der Luft fehlt (Linien), Aachen (DE), Joensuu (FI), Marabá (BR)"></div>')
    return page
