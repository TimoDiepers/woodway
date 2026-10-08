"""Slides 5 and 6 become one (2026-10-07): the two numbers large, the division, today's trees for
comparison; beside it the Science reference on a general level (proposed so, quickly corrected
downwards for two reasons). The former slide 6 goes to the live backup. Applied after patch_stil."""
import re

SLIDE = '''<section class="slide" data-title="Überschlagsrechnung">
  <header class="sh"><h2>Überschlagsrechnung mit Bilanzgrenze um den Baum</h2></header>
  <div class="body">
    <div style="display:grid; grid-template-columns:minmax(0, 1fr) 560px; gap:56px; align-items:center; flex:1; min-height:0">
      <div style="display:grid; grid-template-columns:auto 1fr; gap:22px 32px; align-items:baseline">
        <span class="rise" style="font:600 64px/1 var(--sans); color:var(--moss); letter-spacing:-.02em; white-space:nowrap">163 kg CO₂</span>
        <span class="rise" style="--d:200; font:400 21px/1.35 var(--sans); color:var(--ink-2)">bindet ein durchschnittlicher Baum im Aachener Mischwald bis 2100</span>
        <span class="rise" data-step="1" style="font:600 64px/1 var(--sans); color:var(--clay); letter-spacing:-.02em; white-space:nowrap">335 Gt CO₂</span>
        <span class="rise" data-step="1" style="--d:200; font:400 21px/1.35 var(--sans); color:var(--ink-2)">Entnahme brauchen wir bis 2100 im Szenario Very Low (CMIP7)</span>
        <span class="rise" data-step="2" style="grid-column:1 / -1; margin-top:22px; font:600 46px/1.2 var(--serif); color:var(--moss); font-variant-numeric:lining-nums; white-space:nowrap">335 Gt ÷ 163 kg ≈ <span class="count" data-to="2.1" data-dec="1" data-delay="200">2,1</span> Billionen Bäume</span>
        <span class="rise" data-step="2" style="--d:700; grid-column:1 / -1; font:400 22px/1.35 var(--sans); color:var(--muted)">Vergleich: Bäume heute auf der Erde ≈ 3 Billionen</span>
      </div>
      <div class="rise" data-step="3" style="background:var(--paper-deep); border-left:6px solid var(--moss); padding:26px 30px; border-radius:6px">
        <p style="font:600 15px/1.2 var(--sans); letter-spacing:.08em; color:var(--moss); margin-bottom:12px">SO GERECHNET IN <i>SCIENCE</i> (BASTIN ET AL. 2019)</p>
        <p style="font:400 23px/1.4 var(--serif); color:var(--ink)">Fazit: Aufforstung sei die wirksamste Klimaschutzmaßnahme. Darauf beriefen sich Kampagnen wie <i>Trillion Trees</i>.</p>
        <div class="rise" data-step="4" style="margin-top:20px; padding-top:18px; border-top:2px solid var(--paper-line)">
          <p style="font:600 15px/1.2 var(--sans); letter-spacing:.08em; color:var(--clay); margin-bottom:10px">ABER</p>
          <p style="font:400 23px/1.4 var(--serif); color:var(--ink)">Die Arbeit wurde wissenschaftlich scharf kritisiert. Die Zahlen wurden rasch um rund 60&nbsp;% nach unten korrigiert, weil die Vereinfachung viele Fehler enthält.</p>
        </div>
      </div>
    </div>
    <p class="takeaway" data-step="5" style="--d:0">Offenbar gibt es Diskussionsbedarf. Deshalb sehen wir uns die Rechnung genauer an: Sie zieht die Bilanzgrenze um den Baum, und wir erweitern sie schrittweise bis zum Klimasystem.</p>
  </div>
  <p class="src">Baum: eigene Rechnung mit dem Modellbaum (Folie „C-Aufnahme im Modell“); Bedarf: CMIP7-Markerszenario Very Low, Summe 2024–2100 (Folie 3); Bäume heute: Crowther et al. 2015, Nature 525, 201; Bastin et al. 2019, Science 365, 76; Reaktionen u. a. Veldman et al. und Friedlingstein et al. 2019, Science 366.</p>
  <aside class="notes" data-n="0">
    <p>Die einfachste Rechnung: Ein durchschnittlicher Baum in einem Aachener Mischwald, heute gepflanzt, bindet bis 2100 rund 163 Kilogramm CO₂. Das niedrigste Szenario braucht bis 2100 rund 335 Gigatonnen Entnahme. Geteilt: etwa 2,1 Billionen Bäume. Zum Vergleich stehen heute rund 3 Billionen Bäume auf der Erde, wir bräuchten also zwei Drittel davon zusätzlich.</p>
    <p>Das klingt sehr vereinfacht, wurde aber genau so 2019 in Science gerechnet. Das Fazit des Papiers: Aufforstung sei die wirksamste Klimaschutzmaßnahme. Darauf beriefen sich Kampagnen wie Trillion Trees. Aber: Die Arbeit wurde wissenschaftlich scharf kritisiert, und die Zahlen wurden rasch um rund 60 Prozent nach unten korrigiert, weil die Vereinfachung viele Fehler enthält. Es gibt also Diskussionsbedarf. Deshalb sehen wir uns die Rechnung jetzt genauer an und erweitern ihre Bilanzgrenze Schritt für Schritt.</p>
    <p class="q">Falls Fragen kommen — Modellbaum: typischer Wald in Aachen (Mischwald, Hasler et al. 2024), Kohlenstoff je Hektar nach Walker et al. (2022), 2000 Bäume je Hektar, gepflanzt 2026; bis zur Sättigung wären es 180 kg. Bastin et al. (2019): 0,9 Gha zusätzliche Waldfläche, Platz für rund eine Billion Bäume, 205 GtC; nach den Kommentaren (Veldman et al., Friedlingstein et al. 2019) rund 81 GtC, also 60 % weniger. Hauptkritik: Die CO₂-Bilanz eines Baums ist komplexer als seine Aufnahme, und so viel zusätzliche Waldfläche steht nicht zur Verfügung (Backup „Die Rechnung in der Literatur“).</p>
  </aside>
</section>

'''


def _take(page: str, title: str) -> tuple[str, str]:
    m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(title) + r'"[^>]*>.*?</section>\n\n?', page, flags=re.S)
    assert m, title
    return page[: m.start()] + page[m.end():], m.group(0)


def patch(page: str) -> str:
    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)
    main, old5 = _take(main, "Überschlagsrechnung")
    main, old6 = _take(main, "Die Rechnung in der Literatur")
    # the new slide where slide 5 was: before the next slide after it, i.e. where old6 was taken out
    anchor = re.search(r'<section class="slide[^"]*"[^>]*data-title="Wozu technische CO₂-Entnahme\?"[^>]*>.*?</section>\n\n?', main, flags=re.S)
    assert anchor
    main = main[: anchor.end()] + SLIDE + main[anchor.end():]
    old6 = re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', old6)
    backup = backup.replace("<!-- KAPITEL 1-2, aus dem Hauptteil genommen", old6 + "<!-- KAPITEL 1-2, aus dem Hauptteil genommen", 1)
    main, k = re.subn(r"2019 \(Folie 6\):", "2019 (Folie 5):", main)
    assert k == 1
    # one slide less before the Klima chapter: the legend references move by one
    for old, new in (("— Folien 21–22", "— Folien 20–21"), ("— Folie 23<", "— Folie 22<")):
        assert old in main, old
        main = main.replace(old, new)
    n = iter(range(1, 1000))
    main = re.sub(r'<aside class="notes" data-n="\d+">', lambda m: f'<aside class="notes" data-n="{next(n)}">', main)
    return main + "<!-- BACKUP:BEGIN -->" + backup
