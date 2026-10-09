"""Slide 19 shows a removal instead of an emission: the tree takes 1 kg CO2 out of the air, land and ocean
give part of it back because the exchange with the air shifts (less CO2 in the air: the ocean outgasses,
plants take up less -- compared with the case without the removal)."""

import re

S19 = "Impulsantwort des Kohlenstoffkreislaufs"
BACK = "#8c6d5a"   # CO2 going back into the air (the deck's emission brown)
GREEN = "#2e7d4f"  # removal

NOTES = (
    "    <p>Jetzt der zweite Faktor. Wie viel das CO₂ des Baums fürs Klima ausmacht, hängt davon ab, wie viel davon der Atmosphäre wirklich fehlt. "
    "Dasselbe Bild wie eben, die Strahlung tritt zurück, dazu Meer und Land. Der Baum nimmt ein Kilogramm CO₂ aus der Luft auf — oben die Lücke, der Pfeil geht in den Baum.</p>\n"
    "    <p>Klick: Die runden Pfeile sind die natürlichen Kohlenstoffkreisläufe: Die Atmosphäre tauscht ständig CO₂ mit Land und Ozean aus, der Ozean mit der Tiefsee. "
    "Fehlt der Luft ein Kilogramm, verschiebt sich dieser Austausch: Im Ozean ist jetzt relativ zur Luft zu viel CO₂ gelöst, er gast etwas aus; die Böden nehmen etwas weniger auf. "
    "Land und Ozean geben also einen Teil zurück. Genau genommen bleiben beide heute Senken, sie nehmen nur weniger auf als ohne die Entnahme — für die Atmosphäre wirkt das wie eine Rückgabe.</p>\n"
    "    <p>Klick: rechts die Kurve dazu, die Impulsantwort — nach 20 Jahren fehlen der Luft noch 60 % des Kilogramms, nach 100 Jahren 41 %, ein gutes Fünftel fehlt dauerhaft. "
    "Braun der Teil, den Land und Ozean zurückgegeben haben.</p>\n"
    "    <p>Klick: Was der Atmosphäre am Ende fehlt, ist die verbleibende CO₂-Menge Δm_CO₂ — der zweite Faktor oben.</p>\n"
    "    <p>Klick: Damit haben wir beide Teile des Antriebs, Albedo und CO₂. Bleibt die Frage, wie aus dem Antrieb eine Temperatur wird — nächste Folie.</p>\n"
    "    <p class=\"q\">Falls Fragen kommen — Joos et al. (2013), Mittel aus Erdsystem- und Boxmodellen für einen Puls vor heutigem Hintergrund: a₀ = 0,217; a = 0,224 / 0,282 / 0,276; "
    "τ = 394 / 36,5 / 4,3 Jahre. Physikalisch: schnelle Durchmischung mit der Deckschicht des Ozeans, langsamer Austausch mit der Tiefsee, ganz langsam Karbonatchemie und Verwitterung; "
    "dazu das Land über Photosynthese und Böden. Für eine Emission gilt dieselbe Kurve mit umgekehrtem Vorzeichen; Zickfeld et al. (2015) finden für große Entnahmen eine leichte Asymmetrie. "
    "Im Modell rechnet das FaIR (Folie „Das Erdsystem rechnen“), vor dem steigenden Hintergrund von SSP2-4,5 (2100: 42 % statt 44 % eines Pulses von 2026).</p>\n"
    "    <p>Für den Baum heißt das: Jede Jahresaufnahme ist so eine kleine Entnahme, die nach dieser Kurve abklingt; aufsummiert fehlt der Atmosphäre 2100 gut die Hälfte dessen, "
    "was der Baum aufgenommen hat, in Aachen 84 von 163 kg CO₂ (Backup „Impulsantwort auf die CO₂-Aufnahme eines Baums“).</p>\n")


def _rep(s, old, new):
    assert s.count(old) == 1, old[:90]
    return s.replace(old, new)


def patch(page: str) -> str:
    m = re.search(r'<section class="slide[^"]*" data-ch="klima" data-title="' + re.escape(S19) + r'">.*?</section>', page, flags=re.S)
    assert m
    sec = m.group(0)

    # drawing, start: the CO2 is missing (faded molecules in a green dashed gap), an arrow into the tree
    sec = _rep(sec, '<ellipse cx="470" cy="200" rx="96" ry="54" fill="#8c6d5a" fill-opacity=".10" stroke="#8c6d5a" stroke-width="2" stroke-dasharray="6 6"/>',
               f'<ellipse cx="470" cy="200" rx="96" ry="54" fill="{GREEN}" fill-opacity=".06" stroke="{GREEN}" stroke-width="2" stroke-dasharray="6 6"/><g opacity=".3">')
    sec = _rep(sec, f'      <text x="470" y="128" text-anchor="middle" font-size="25" font-weight="600" fill="#8c6d5a">+1 t CO₂</text>\n',
               '</g>\n'
               f'      <text x="470" y="128" text-anchor="middle" font-size="25" font-weight="600" fill="{GREEN}">−1 kg CO₂</text>\n'
               f'      <path class="flowc" d="M382 226 C 352 246 326 262 306 286" stroke="{GREEN}" stroke-width="4.5" fill="none" marker-end="url(#cc-g)"/>\n'
               f'      <text x="320" y="318" font-size="20" font-weight="600" fill="#1b5e33">in den</text>\n'
               f'      <text x="320" y="342" font-size="20" font-weight="600" fill="#1b5e33">Baum</text>\n')
    # click 1: land and ocean give part of it back: arrows from them into the gap, brown
    sec = _rep(sec, '<path class="flowc" d="M470 262 C 462 300 446 330 430 352" stroke="#2e7d4f" stroke-width="4.5" fill="none" marker-end="url(#cc-g)"/>',
               f'<path class="flowc" d="M436 352 C 450 330 462 300 468 266" stroke="{BACK}" stroke-width="4.5" fill="none" marker-end="url(#cc-e)"/>')
    sec = _rep(sec, '<path class="flowc" d="M520 248 C 580 310 640 380 670 460" stroke="#2e7d4f" stroke-width="4.5" fill="none" marker-end="url(#cc-g)"/>',
               f'<path class="flowc" d="M670 460 C 640 380 580 310 524 252" stroke="{BACK}" stroke-width="4.5" fill="none" marker-end="url(#cc-e)"/>')
    sec = _rep(sec, '<text x="470" y="426" font-size="20" font-weight="600" fill="#1b5e33">nimmt auf</text>',
               f'<text x="470" y="426" font-size="20" font-weight="600" fill="#6b4f3f">geben ab</text>')
    sec = _rep(sec, '<text x="712" y="436" font-size="20" font-weight="600" fill="#1b5e33">nimmt auf</text>',
               f'<text x="712" y="436" font-size="20" font-weight="600" fill="#6b4f3f">gast aus</text>')
    sec = _rep(sec, '<text x="470" y="400" font-size="20" font-weight="600" fill="#1b5e33">Land</text>',
               '<text x="470" y="400" font-size="20" font-weight="600" fill="#6b4f3f">Böden</text>')
    sec = _rep(sec, '<text x="712" y="410" font-size="20" font-weight="600" fill="#1b5e33">Ozean</text>',
               '<text x="712" y="410" font-size="20" font-weight="600" fill="#6b4f3f">Ozean</text>')
    sec = _rep(sec, '<marker id="cc-g" ',
               f'<marker id="cc-e" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="{BACK}"/></marker><marker id="cc-g" ')

    # right column
    sec = _rep(sec, '<b style="background:#8c6d5a">1</b>Zusatzemission: 1 t CO₂ kommt in die Atmosphäre.',
               f'<b style="background:{GREEN}">1</b>Entnahme: Baum nimmt 1 kg CO₂ aus der Luft')
    sec = _rep(sec, '<b style="background:#2e7d4f">2</b>Natürliche Kreisläufe (runde Pfeile)<br>→ Land und Ozean nehmen einen Teil auf',
               f'<b style="background:{BACK}">2</b>Weniger CO₂ in der Luft → Ozean gast aus,<br>Böden nehmen weniger auf: ein Teil kommt zurück')
    sec = _rep(sec, 'Tempo: 60 % nach 20, 41 % nach 100 Jahren', 'Es fehlen noch 60 % nach 20, 41 % nach 100 J.')
    sec = _rep(sec, 'data-slot-steps="0,1" data-chart="k3s" data-label="Impulsantwort: atmosphärischer Anteil einer emittierten und einer entnommenen Tonne CO₂ über 150 Jahre"',
               'data-slot-steps="0" data-chart="k3s" data-label="Impulsantwort: wie viel von 1 kg entnommenem CO₂ der Atmosphäre über 150 Jahre noch fehlt; der Rest kommt aus Land und Ozean zurück"')
    # the old point 4 (removal mirrors emission) is gone: the removal is the example now; later clicks move up
    p4 = re.search(r'<div class="rise" data-step="3" style="--d:200"><p class="ghs"><b style="background:#5e8f3a">4</b>Entnahme: genauso, spiegelbildlich</p></div>', sec)
    assert p4
    sec = sec[: p4.start()] + sec[p4.end():]
    sec = _rep(sec, '<div class="rise epsdef fswap" data-step="4"', '<div class="rise epsdef fswap" data-step="3"')
    sec = _rep(sec, '<p class="takeaway" data-step="5"', '<p class="takeaway" data-step="4"')
    sec = _rep(sec, 'Puls vor heutigem Hintergrund. Für Entnahmen gleicher Größe annähernd spiegelbildlich (Zickfeld et al. 2015).',
               'Puls vor heutigem Hintergrund, für eine Entnahme mit umgekehrtem Vorzeichen (Zickfeld et al. 2015).')

    n = re.search(r'(<aside class="notes" data-n="\d+">\n)(.*?)(  </aside>)', sec, flags=re.S)
    assert n
    sec = sec[: n.start(2)] + NOTES + sec[n.start(3):]
    page = page[: m.start()] + sec + page[m.end():]
    return _signed(page)


def _signed(page: str) -> str:
    """Delta m_CO2 is a signed change of the air's CO2 (< 0 for a removal), not a 'remaining amount':
    the same words on the roads of slides 17-19, the box of slide 19, the definitions and the notes."""
    n = page.count('<span class="w">verbleibende CO₂-Menge</span>')
    assert n == 5, n
    page = page.replace('<span class="w">verbleibende CO₂-Menge</span>', '<span class="w">CO₂-Änderung der Atmosphäre</span>')
    page = _rep(page, '<p>Verbleibende CO₂-Menge = <span class="tex">$\\cq{\\Delta m_{\\mathrm{CO_2}}}$</span> [kg]</p>',
                '<p>CO₂-Änderung der Atmosphäre = <span class="tex">$\\cq{\\Delta m_{\\mathrm{CO_2}}}(t)$</span> [kg]<br>bei Entnahme negativ</p>')
    page = _rep(page, '<dd class="loc">verbleibende CO₂-Menge [kg] — Folie 19</dd>', '<dd class="loc">CO₂-Änderung der Atmosphäre [kg], &lt; 0 — Folie 19</dd>')
    page = _rep(page, 'ist die verbleibende CO₂-Menge Δm_CO₂ — der zweite Faktor oben.', 'ist die CO₂-Änderung der Atmosphäre Δm_CO₂(t), negativ — der zweite Faktor oben.')
    page = _rep(page, 'und die verbleibende CO₂-Menge — Albedo und Wachstum', 'und die CO₂-Änderung der Atmosphäre — Albedo und Wachstum')
    assert "erbleibende CO₂-Menge" not in page
    return page
