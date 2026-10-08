"""Takeaways stand out and are short (2026-10-07): a dark box in the chapter colour with the leaf in the
light accent; at most two lines per takeaway. The former long text goes into the speaker notes
("Ausführlich: ...") so no number is lost. Applied last."""
import html
import re

CSS_OLD = """.takeaway {
  position: relative; padding-left: 50px;
  border-top: 1px solid var(--paper-line); padding-top: 18px; margin-top: 24px;
  font-style: italic; font-size: 24px; line-height: 1.42; color: var(--ink);
  font-variation-settings: "opsz" 24; text-wrap: pretty;
}
.takeaway::before {
  content: ""; position: absolute; left: 2px; top: 23px; width: 26px; height: 26px; background: var(--ch);"""
CSS_NEW = """.takeaway {
  position: relative; padding: 16px 26px 17px 64px; margin-top: 24px;
  background: var(--ch); color: var(--paper); border-radius: 8px;
  font-style: normal; font-weight: 500; font-size: 24px; line-height: 1.38;
  font-variation-settings: "opsz" 24; text-wrap: pretty;
  box-shadow: 0 10px 24px -16px rgba(30, 26, 18, .55);
}
.takeaway::before {
  content: ""; position: absolute; left: 24px; top: 19px; width: 26px; height: 26px; background: var(--ch-soft);"""

SHORT = {
    "CMIP7: Erwärmung": "Selbst Very Low: Höchstwert 1,8 °C (2049), unter 1,5 °C erst nach 2120.",
    "CMIP7: CO₂-Entnahme": "Weniger Erwärmung → mehr Entnahme: Very Low setzt 335 Gt CO₂ bis 2100 voraus.",
    "Überschlagsrechnung": "Umstritten → Bilanzgrenze schrittweise bis zum Klimasystem erweitern.",
    "C-Aufnahme über die Zeit": "Annahme: Für das Klima zählt nur der Jahresmittelwert.",
    "C-Aufnahme im Modell": "Volle Speicherwirkung erst nach Jahrzehnten; Störung trifft den ganzen Vorrat.",
    "Typischer Waldtyp je Ort": "Gepflanzt wird der typische Wald des Ortes; der Kohlenstoff hängt am Ort, nicht am Typ.",
    "CO₂-Aufnahme je Baum": "Maximum um 2041. Bis 2100 je Baum: Aachen 163, Joensuu 111, Marabá 232 kg CO₂.",
    "Einstrahlung und Albedo-Kontrast": "Absorbierte Strahlung = Einstrahlung × Albedo-Kontrast; Schnee → größerer Kontrast.",
    "Zusätzlich absorbierte Strahlung": "Je Baum: Aachen 34 W, Joensuu 45 W, Marabá 21 W. Zwei Wirkungen, zwei Einheiten.",
    "Strahlungsantrieb: Energiebilanz am Oberrand": "Gemeinsame Größe: Strahlungsantrieb in W/m².",
    "Impulsantwort des Kohlenstoffkreislaufs": "Nach 20 Jahren noch 60 % in der Atmosphäre; Entnahme klingt spiegelbildlich ab.",
    "Impulsantwort auf die CO₂-Aufnahme eines Baums": "2100 fehlt der Atmosphäre nur gut die Hälfte der Aufnahme: Aachen 84 von 163 kg.",
    "Strahlungsantrieb von CO₂": "Mehr CO₂ in der Atmosphäre, weniger Antrieb je kg: 1,64 → 1,31 · 10⁻¹⁵ W/m².",
    "Gesamter Strahlungsantrieb je Baum": "Mit φ wissen wir, wie groß der Antrieb ist → noch nicht, wie stark sich die Temperatur ändert.",
    "Temperaturantwort auf den Strahlungsantrieb": "Problem: C und Λ sind nicht konstant, die CO₂-Senken hängen von T ab.",
    "Das Erdsystem rechnen: FaIR": "Kalibrierter Emulator für die ganze Kette → Bäume als kleine Störung des Szenarios.",
    "Temperaturwirkung eines Baums je Ort": "Tropen: stärkste Kühlung. Hohe Breiten, Trockengebiete: netto erwärmend.",
    "Wiederbewaldbare Fläche": "0,83 Gha wiederbewaldbar, nur 0,39 Gha davon kühlend.",
    "Globale Temperaturwirkung über die Zeit": "2100: 19 mK auf kühlenden Flächen, nur 6,8 mK auf allen.",
    "Beitrag der Aufforstung zum Entnahmebedarf": "Bis 2050: 43 von 53 Gt. Bis 2100: 59 von 335 Gt. Lücke: 276 Gt.",
    "Sorbens-DAC: Prozess und Energiebedarf": "Kandidat für die Lücke: DAC, rund 1,5 MWh Strom je Tonne CO₂.",
    "DAC-Modell": "Klima am Ort → Strombedarf; Strommix des Jahres → Emissionen; daraus der Netto-Anteil.",
    "Netto-Entnahme von DAC": "Netto-Anteil im Median: 46 % (2026), 91 % (2040). Bäume: 58 %.",
    "DAC in drei Strompfaden": "Strompfad verschiebt nur um Jahre → ab etwa 2035 DAC je Tonne vor dem Baum.",
    "Priorisierung von Aufforstung und DAC": "Baum: begrenzt durch Albedo. DAC: begrenzt durch den Strom.",
    "Auf dem Holzweg? Nein.": "Beides gebraucht, jeweils am geeigneten Ort und zur richtigen Zeit.",
    "Methodischer Beitrag": "Neu: eine zeitaufgelöste Rechnung je Ort für Baum und DAC, mit kalibriertem Klima-Emulator.",
}


def _nb(text: str) -> str:
    """No-break spaces before units and the degree sign, as in the rest of the deck."""
    return re.sub(r" (?=(%|°C|Gt|Gha|kg|W\b|mK|MWh|K\b))", " ", text)


def patch(page: str) -> str:
    assert CSS_OLD in page
    page = page.replace(CSS_OLD, CSS_NEW)
    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)
    done = set()
    for title, short in SHORT.items():
        m = re.search(r'<section class="slide[^"]*"[^>]*data-title="' + re.escape(title) + r'"[^>]*>.*?</section>', main, flags=re.S)
        assert m, title
        sec = m.group(0)
        t = re.search(r'(<p class="takeaway"[^>]*>)(.*?)(</p>)', sec, flags=re.S)
        assert t, title
        old = html.unescape(re.sub(r"<[^>]+>", "", t.group(2))).replace(" ", " ").strip()
        sec = sec[: t.start()] + t.group(1) + _nb(short) + t.group(3) + sec[t.end():]
        n = re.search(r'<aside class="notes"[^>]*>\n?', sec)
        if n and old != short:
            sec = sec[: n.end()] + f'    <p class="q">Ausführlich: {html.escape(old, quote=False)}</p>\n' + sec[n.end():]
        main = main[: m.start()] + sec + main[m.end():]
        done.add(title)
    # every takeaway of the main part is covered
    left = [re.search(r'data-title="([^"]*)', s).group(1) for s in re.findall(r'<section class="slide[^"]*".*?</section>', main, flags=re.S)
            if 'class="takeaway"' in s and re.search(r'data-title="([^"]*)', s).group(1) not in done]
    assert not left, left
    return main + "<!-- BACKUP:BEGIN -->" + backup
