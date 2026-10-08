"""Build docs/slides/html/dissvortrag_v2.html, the HTML deck.

Starts from the frozen export in scripts/deck/base/dissvortrag_v2.html (made by
scripts/export_html_v2.py) and applies the patch modules in this folder in
order. Idempotent: every run starts again from the base file.

    uv run python scripts/deck/build_deck.py
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HTML = REPO / "docs/slides/html/dissvortrag_v2.html"
SNAP = Path(__file__).parent / "base" / "dissvortrag_v2.html"
page = SNAP.read_text(encoding="utf-8")

A = '<!-- =====================================================\n     KAPITEL: VERGLEICH'
B = '<section class="slide title" data-title="Danke">'
head, rest = page.split(A, 1)
chapter, tail = rest.split(B, 1)
chapter = A + chapter
tail = B + tail


def section(title: str) -> str:
    m = re.search(r'<section class="slide[^"]*" data-ch="vergleich" data-title="' + re.escape(title) + r'">.*?</section>\n',
                  chapter, flags=re.S)
    assert m, title
    return m.group(0)


def renumber(sec: str, n: int) -> str:
    return re.sub(r'<aside class="notes" data-n="\d+">', f'<aside class="notes" data-n="{n}">', sec)


def unnumber(sec: str) -> str:
    return re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', sec)


# ---------------------------------------------------------------- 29 chapter
s29 = section("Vergleich")
s29 = s29.replace('data-title="Vergleich"', 'data-title="Baum und Maschine"')
s29 = s29.replace('<h1 class="rise">Vergleich</h1><p class="rise" style="--d:300">Ingenieure auf dem Holzweg?</p>',
                  '<h1 class="rise">Baum und Maschine</h1><p class="rise" style="--d:300">Was alle Bäume zusammen bewirken — und wozu die Maschine</p>')
s29 = re.sub(r'<aside class="notes" data-n="\d+">.*?</aside>', '''<aside class="notes" data-n="29">
    <p>Bisher ein Baum an drei Orten und dann an jedem Ort. Jetzt alle Bäume zusammen, mit derselben Rechnung. Erst die Ergebnisse für den Wald: Wo ist Platz, wie wirkt er über die Zeit, wann muss man pflanzen, und reicht das? Dann die Frage vom Anfang: Braucht es die Maschine — und wo und ab wann lohnt sie sich?</p>
  </aside>''', s29, flags=re.S)

# ---------------------------------------------------------------- 30 area
s30 = renumber(section("Wo Bäume hinkönnen"), 30)
s30 = s30.replace("Von den 0,83 Gha bleiben 0,42 Gha, auf denen ein 2025 gepflanzter Baum bis 2100 kühlt. Mit dieser Fläche rechnen wir weiter.",
                  "Bei 2000 Bäumen je Hektar ist das Platz für rund 1,7 Billionen Bäume — die naive Rechnung vom Anfang brauchte 2 Billionen. Und nur die Hälfte davon kühlt: Von den 0,83 Gha bleiben 0,42 Gha, auf denen ein 2025 gepflanzter Baum bis 2100 kühlt, rund 0,8 Billionen Bäume. Das sind die grünen Flächen der Karte davor; die orangen wärmen.")
s30 = re.sub(r'<p class="takeaway" data-step="1" style="--d:0">.*?</p>',
             '<p class="takeaway" data-step="1" style="--d:0; font-size:22px">Wiederbewaldbar sind 0,83 Gha, rund 6 % der eisfreien Landfläche: Platz für rund 1,7 Billionen Bäume — die naive Rechnung brauchte 2 Billionen. Kühlen tut der Baum, 2025 gepflanzt, davon nur auf 0,42 Gha (0,8 Billionen Bäume); auf der anderen Hälfte, im Norden und im Trockenen, wärmt er.</p>',
             s30, flags=re.S)

# ---------------------------------------------------------------- 31 planting choice (new)
s31 = '''<section class="slide" data-ch="vergleich" data-title="Kühlung nach bepflanzter Fläche">
  <header class="sh"><h2>Kühlung 2100 nach bepflanzter Fläche, die stärksten Flächen zuerst</h2></header>
  <div class="body">
    <div class="chart" data-chart="w1" data-label="Kühlung im Jahr 2100 gegen die bepflanzte Fläche, Flächen nach ihrer Kühlung je Hektar sortiert: steigt bis 0,42 Gha, fällt danach"></div>
    <div class="foot"><div></div><p class="takeaway" data-step="1" style="--d:1800; font-size:22px">Nach ihrer Kühlung je Hektar sortiert, liefern die besten 0,1 Gha schon 58 % der größtmöglichen Kühlung, die besten 0,2 Gha 84 %. Das Maximum, 19 mK im Jahr 2100, liegt bei 0,42 Gha. Jede weitere Fläche wärmt: Alle 0,83 Gha zusammen kühlen nur noch um 8 mK.</p></div>
  </div>
  <p class="src">Eigene Rechnung: typischer Wald je Zelle (Hasler et al. 2024), gepflanzt 2025, Kohlenstoff Walker et al. 2022, Albedo Duveiller et al. 2018; Temperatur je Baum mit dem Klima-Emulator FaIR (Leach et al. 2021; Smith et al. 2024), SSP2-4,5, über die Bäume jeder Zelle summiert.</p>
  <aside class="notes" data-n="31">
    <p>Wo soll man pflanzen? Wir sortieren alle wiederbewaldbaren Flächen danach, wie stark ein Hektar Wald dort bis 2100 kühlt, die besten zuerst, und pflanzen in dieser Reihenfolge. Nach rechts die bepflanzte Fläche, nach oben die Kühlung im Jahr 2100. Am Anfang geht es steil nach oben: Die besten 0,1 Gigahektar — vor allem Tropen mit viel Sonne und ohne Schnee, hier Marabá — bringen schon mehr als die Hälfte. Dann flacht es ab; Aachen liegt weit vorn, Joensuu kühlt je Hektar schwächer, aber noch deutlich. Bei 0,42 Gigahektar ist Schluss: Ab hier wärmt jeder weitere Hektar, weil die Albedo mehr kostet, als der Kohlenstoff bringt — im schneereichen Norden und im Trockenen. Wer alle 0,83 Gigahektar bepflanzt, verschenkt mehr als die Hälfte der Kühlung. Das ist die Rangfolge für Bäume: zuerst dort, wo sie am stärksten kühlen; nie dort, wo sie wärmen.</p>
    <p class="q">Falls Fragen kommen — Rechenweg: je Zelle die Temperaturwirkung eines Baums 2100 (volles Modell, Karte „Was ein Baum wo bewirkt“) mal Zahl der Bäume (Fläche / Standfläche des Waldtyps), sortiert nach Wirkung je Hektar, aufsummiert. Diese Summe ist linear. Ein FaIR-Lauf mit der ganzen Fläche auf einmal ergibt 20 mK (nur kühlende Flächen) und 9 mK (alle Flächen) statt 19 und 8 mK — dieselbe Aussage. In CO₂: brutto 106 Gt auf den kühlenden Flächen, 155 Gt auf allen; netto nach Albedo 62 gegen 29 Gt (nächste Folie). „Kühlend“ heißt: Der Baum des typischen Waldes, 2025 gepflanzt, kühlt in dieser Zelle bis 2100 netto.</p>
  </aside>
</section>
'''


# ---------------------------------------------------------------- tree results: all trees over time, planting year
w2 = """<section class="slide" data-ch="vergleich" data-title="Alle Bäume, Jahr für Jahr">
  <header class="sh"><h2>Alle Bäume zusammen, Jahr für Jahr</h2></header>
  <div class="body">
    <div class="chart" data-chart="w2" data-label="Kühlung der Erde 2025 bis 2100 durch alle Bäume: nur kühlende Flächen mit und ohne Albedo, alle Flächen"></div>
    <div class="foot"><div></div><p class="takeaway" data-step="1" style="--d:1800; font-size:21px">Dieselbe Rechnung wie je Baum, über alle Bäume summiert. Auf den kühlenden 0,42 Gha kühlen sie 2050 um 15 mK, 2100 um 20 mK. Die Albedo holt mit dem Kronenschluss auf: Der Netto-Anteil fällt von 85 % (2050) auf 59 % (2100). Auf allen 0,83 Gha kühlen die Bäume anfangs sogar stärker, ab 2061 schwächer, 2100 nur noch um 9 mK. Welche Fläche richtig ist, hängt davon ab, wann man fragt.</p></div>
  </div>
  <p class="src">Eigene Rechnung: typischer Wald je Zelle (Hasler et al. 2024), gepflanzt 2025, Kohlenstoff Walker et al. 2022, Albedo Duveiller et al. 2018; je Fläche ein Lauf des Klima-Emulators FaIR (Leach et al. 2021; Smith et al. 2024) mit der ganzen Entnahme als negativer Emission und der Albedo als Antrieb, SSP2-4,5; gestrichelt derselbe Lauf ohne Albedo.</p>
  <aside class="notes" data-n="0">
    <p>Jetzt nicht mehr ein Baum, sondern alle. Grün: alle Bäume auf den 0,42 Gigahektar, auf denen der Baum bis 2100 kühlt, rund 800 Milliarden Bäume. Je Baum sind es ein paar 10⁻¹⁴ Grad; mal 800 Milliarden ergibt das Tausendstel Grad, Millikelvin. Gestrichelt dieselben Bäume ohne Albedo — wie je Baum im Kapitel Klima. Der Abstand wächst mit der Zeit: Der Kohlenstoff wirkt früh, die Albedo kommt mit dem Kronenschluss. 2050 bleiben 85 % der Kühlung, 2100 nur noch 59 %. Orange: alle 0,83 Gigahektar. Bis um 2060 kühlen sie sogar stärker, weil im Norden der Wald zuerst Kohlenstoff bindet. Dann holt die Albedo auf, und 2100 bleibt weniger als die Hälfte. Wer nur auf 2050 schaut, würde überall pflanzen; wer auf 2100 schaut, nur auf der Hälfte. Das kann man nur sehen, wenn man Jahr für Jahr rechnet — eine statische Bilanz liefert eine einzige Zahl.</p>
    <p class="q">Falls Fragen kommen — Vier FaIR-Läufe (kühlende Flächen und alle Flächen, je mit und ohne Albedo), dieselben wie für die 62 Gt auf der nächsten Folie. Kühlend = der Baum des typischen Waldes kühlt in dieser Zelle bis 2100 netto. Werte: kühlende Flächen 2035 −4,0, 2050 −14,9, 2075 −21,0, 2100 −20,0 mK; ohne Albedo −4,2 / −17,5 / −30,8 / −34,2 mK; alle Flächen −5,5 / −17,4 / −16,0 / −9,2 mK. Nach 2100 rechnen wir nicht; der Vortrag bewertet 2100.</p>
  </aside>
</section>
"""

w3 = """<section class="slide" data-ch="vergleich" data-title="Wann pflanzen?">
  <header class="sh"><h2>Wann pflanzen? Warten kostet vor allem bis zur Jahrhundertmitte</h2></header>
  <div class="body">
    <div class="chart" data-chart="w3" data-label="Kühlung 2050 und 2100 nach Pflanzjahr, gemessen an der Pflanzung 2025, kühlende Flächen"></div>
    <div class="foot"><div></div><p class="takeaway" data-step="1" style="--d:1800; font-size:22px">Für die Kühlung im Jahr 2100 ist es fast gleich, ob 2025 oder 2045 gepflanzt wird. Für die Spitze der Erwärmung um 2050 nicht: Fünf Jahre Warten kosten dort ein Fünftel der Kühlung, zehn Jahre fast die Hälfte, zwanzig Jahre fast alles. Bäume müssen also jetzt gepflanzt werden.</p></div>
  </div>
  <p class="src">Eigene Rechnung, volles Modell: typischer Wald je Zelle auf den 0,42 Gha, in jedem Pflanzjahr dieselbe Fläche; Störung steigt mit der Erwärmung (Grünig et al. 2026); FaIR (Leach et al. 2021), SSP2-4,5; je Baum gerechnet und über die Bäume summiert. Höhepunkt der Erwärmung im niedrigsten Szenario: 2049 (Folie 2).</p>
  <aside class="notes" data-n="0">
    <p>Im Kapitel Klima haben wir gesehen: Ein später gepflanzter Baum kühlt bis 2100 weniger, weil ihm Zeit fehlt und die Welt, in die er wächst, wärmer ist. Hier dasselbe für alle Bäume auf der kühlenden Fläche. Hellgrün die Kühlung im Jahr 2100: Ob 2025 oder 2045 gepflanzt — fast gleich; der jüngere Wald bindet bis dahin noch kräftig, und seine Albedo ist noch nicht voll da. Dunkelgrün die Kühlung um 2050, wenn die Erwärmung im niedrigsten Szenario ihren Höhepunkt hat. Da zählt nur, was bis dahin gewachsen ist: fünf Jahre Warten kosten ein Fünftel, zehn Jahre die Hälfte. Wer die Spitze der Erwärmung drücken will, muss jetzt pflanzen.</p>
    <p class="q">Falls Fragen kommen — Kühlung 2050 relativ zur Pflanzung 2025: 2030 78 %, 2035 54 %, 2040 29 %, 2045 9 %. Kühlung 2100: 101 % bis 101 % (der jüngere Wald hat 2100 weniger Albedo-Strafe und wächst noch). Je Baum gerechnet und aufsummiert (linear); absolut kühlt die Pflanzung 2025 so 2050 um 15,5 mK, fast wie im FaIR-Lauf mit der ganzen Fläche (14,9 mK). Die Störung steigt mit der Erwärmung, ein später gepflanzter Wald lebt in einer wärmeren Welt. Spätere Pflanzjahre als 2045 im Kapitel Klima je Baum.</p>
  </aside>
</section>
"""


w4 = """<section class="slide" data-ch="vergleich" data-title="Bäume unter drei Szenarien">
  <header class="sh"><h2>Bäume in einer kühleren und einer wärmeren Welt</h2></header>
  <div class="body">
    <table style="margin-top:2px">
      <thead><tr><th style="width:34%"></th><th style="width:22%">sehr optimistisch</th><th style="width:22%">Mitte (bisher)</th><th style="width:22%">sehr pessimistisch</th></tr></thead>
      <tbody>
        <tr class="rise"><td style="color:var(--muted)">Hintergrund in FaIR</td><td>SSP1-1.9</td><td>SSP2-4.5</td><td>SSP3-7.0</td></tr>
        <tr class="rise"><td style="color:var(--muted)">Erwärmung 2100 ohne die Bäume</td><td>1,5 °C</td><td>2,7 °C</td><td>3,5 °C</td></tr>
        <tr class="rise" data-step="1"><td style="font-weight:600; color:var(--fjord)">Netto-Anteil je Baum: Aachen (DE) · Joensuu (FI) · Marabá (BR)</td><td>71 · 43 · 86 %</td><td>65 · 32 · 83 %</td><td>58 · 19 · 79 %</td></tr>
        <tr class="rise" data-step="1"><td style="font-weight:600; color:var(--fjord)">Kühlung 2100, kühlende Flächen</td><td>24 mK</td><td>20 mK</td><td>17 mK</td></tr>
        <tr class="rise" data-step="1"><td style="font-weight:600; color:var(--fjord)">netto bis 2100: kühlende Flächen · alle Flächen</td><td>66 · 41 Gt</td><td>62 · 29 Gt</td><td>58 · 19 Gt</td></tr>
        <tr class="rise" data-step="2"><td style="font-weight:600; color:var(--fjord)">Entnahme-Bedarf bis 2100 (CMIP7)</td><td>Very Low: 335 Gt</td><td>Very Low: 335 Gt</td><td>Low-to-Negative: 820 Gt</td></tr>
        <tr class="rise" data-step="2"><td style="font-weight:600; color:var(--fjord)">davon decken die Bäume</td><td style="font-weight:600">20 %</td><td style="font-weight:600">18 %</td><td style="font-weight:600">7 %</td></tr>
      </tbody>
    </table>
    <div style="flex:1"></div>
    <p class="takeaway" data-step="3" style="--d:0; font-size:22px">In einer wärmeren Welt kühlen Bäume weniger: Störungen nehmen zu, und jedes Kilogramm CO₂ wirkt in vollerer Luft schwächer, die Albedo aber gleich. Im hohen Norden trifft das am stärksten. Am Befund ändert das nichts: Je nach Szenario decken die Bäume 7 bis 20 % des Bedarfs.</p>
  </div>
  <p class="src">Eigene Rechnung, gleiche Bäume und Flächen (0,42 bzw. 0,83 Gha, typischer Wald, gepflanzt 2025); nur der Hintergrund in FaIR (Leach et al. 2021; Smith et al. 2024) wechselt, Emissionen aus RCMIP. Bedarf: CMIP7-Markerszenarien (van Vuuren et al. 2026), Summe 2024–2100.</p>
  <aside class="notes" data-n="0">
    <p>Wie belastbar ist das? Bisher lief alles im mittleren Szenario SSP2-4,5. Hier dieselben Bäume auf denselben Flächen in einer sehr optimistischen und einer sehr pessimistischen Welt. Optimistisch: SSP1-1,9, die Erwärmung bleibt um 1,5 Grad. Pessimistisch: SSP3-7,0, 3,5 Grad im Jahr 2100. In der wärmeren Welt kühlen die Bäume weniger: Feuer, Sturm und Käfer werden häufiger, und jedes Kilogramm CO₂ wirkt in einer volleren Atmosphäre schwächer. Die Albedo dagegen bleibt, wie sie ist. Am stärksten trifft das den Norden — Joensuu fällt von 43 auf 19 Prozent netto. Der Bedarf ändert sich mit: Wer spät mindert, braucht mehr Entnahme; dafür steht das CMIP7-Szenario Low-to-Negative mit 820 Gigatonnen. Die Bäume decken dann nur noch 7 Prozent.</p>
    <p class="q">Falls Fragen kommen — Netto = Kohlenstoff der Kaskade (106 bzw. 155 Gt CO₂, unabhängig vom Szenario) × Netto-Anteil des Szenarios aus je zwei FaIR-Läufen (mit und ohne Albedo). Fläche bewusst festgehalten (die kühlende Fläche der Mitte), damit nur der Hintergrund wechselt. Erwärmung des gewählten FaIR-Mitglieds ohne Bäume, gegenüber 1850–1900. Warum Low-to-Negative für pessimistisch: Es erreicht niedrige Erwärmung erst nach starkem Überschießen mit viel Entnahme — das ist die Welt der späten Minderung; die CMIP7-Szenarien ohne Ziel (Medium, High) planen keine Entnahme. Kühlung 2050: 16 / 15 / 14 mK. Daten: docs/slides/chart_data/szenarien_baeume.json.</p>
  </aside>
</section>
"""

# ---------------------------------------------------------------- 32 need
s32 = renumber(section("Bäume reichen nicht"), 32)
s32 = s32.replace('data-label="CO₂-Entnahme 2024–2100 je Szenario gegen das Potenzial aller nutzbaren Flächen"',
                  'data-label="CO₂-Entnahme 2024–2100 je Szenario gegen Bäume nur auf kühlenden Flächen und auf allen Flächen"')
s32 = re.sub(r'<p class="takeaway" data-step="1" style="--d:0">.*?</p>',
             '<p class="takeaway" data-step="1" style="--d:0; font-size:21px">Auf den kühlenden Flächen binden die Bäume bis 2100 106 Gt CO₂ (schraffiert). Nach Albedo bleibt davon netto 59 % übrig, 62 Gt — derselbe Netto-Anteil wie je Baum, nur über alle Flächen. Das sind 18 % der 335 Gt, die das niedrigste Szenario braucht. Auf allen Flächen sind es nur 29 Gt, weil die andere Hälfte wärmt. Die Natur allein reicht also nicht: Es braucht auch Maschinen.</p>',
             s32, flags=re.S)
s32 = re.sub(r'<p class="src">.*?</p>',
             '<p class="src">Bedarf: Modellergebnis CMIP7-Szenarien (van Vuuren et al. 2026), dieselben Daten wie Folie 3. Bäume: eigene Rechnung, typischer Wald, gepflanzt 2025; netto = nach Albedo, aus Läufen des Klima-Emulators FaIR (Leach et al. 2021).</p>',
             s32, flags=re.S)
s32 = re.sub(r'<aside class="notes" data-n="32">.*?</aside>', '''<aside class="notes" data-n="32">
    <p>Jetzt die Frage vom Anfang: Braucht es die Maschine überhaupt? Oben, was die Szenarien bis 2100 an Entnahme brauchen: hellgrün die Landnutzung, türkis die neuartigen Verfahren. Unten unsere Bäume, alle 2025 gepflanzt. Schraffiert, was sie bis 2100 im Holz binden. Ausgefüllt, was davon netto wirkt — wie je Baum: Die Albedo frisst einen Teil der Kühlung, über alle kühlenden Flächen 41 %. Netto heißt hier: so viel CO₂, wie man entnehmen müsste, um 2100 dieselbe Kühlung zu bekommen wie mit dem Wald samt Albedo. Klug gepflanzt, nur wo sie kühlen, bleiben netto 62 Gt — 18 % des niedrigsten Szenarios. Überall gepflanzt sind es weniger, 29 Gt: Die Bäume auf der wärmenden Hälfte heben mehr als die Hälfte der Wirkung wieder auf. Mit Fläche lässt sich das also nicht ausgleichen. Die naive Rechnung vom Anfang hätte den ganzen Bedarf mit zwei Billionen Bäumen gedeckt; mit der vollen Systemgrenze deckt der Wald knapp ein Fünftel. Die Antwort auf die Frage ist also: Ja, es braucht auch Maschinen.</p>
    <p class="q">Falls Fragen kommen — Bäume brutto 106 Gt CO₂ = Kaskade (28,8 GtC × 44/12). Netto: um das Verhältnis der Kühlung mit und ohne Albedo auf den behaltenen Flächen verringert (FaIR-Läufe mit der ganzen Fläche). Gegen den Landanteil des VL-Szenarios (226 Gt) sind es 27 %. Bedarf aus den CMIP7-Daten wie auf Folie 3 (Very Low 335 Gt bis 2100, davon 109 neuartig). Bastin et al. 2019 (Folie 6): 205 GtC, also rund 750 Gt CO₂. Andere Studien kommen mit mehr Kohlenstoff je Hektar auf einen höheren Netto-Anteil (Backup „Einordnung: andere Studien“); auch mit Fahrenbachs doppelter Kohlenstoffmenge bliebe es bei einem Bruchteil des Bedarfs. Reihenfolge innerhalb der kühlenden Fläche: Die am stärksten kühlenden 0,1 Gha (vor allem Tropen) bringen schon 58 % der Kühlung, 0,2 Gha 84 % (Backup „Kühlung nach bepflanzter Fläche“). Die Umkehrrechnung (1,5 °C unter SSP2-4,5) liegt im Backup.</p>
  </aside>''', s32, flags=re.S)


# 32 becomes the need in three worlds (replaces the single-scenario bars and the table)
s32 = s32.replace('<header class="sh"><h2>Bäume reichen nicht</h2></header>',
                  '<header class="sh"><h2>Entnahme-Bedarf der Szenarien und was die Bäume liefern</h2></header>')
s32 = s32.replace('data-chart="v2" data-label="CO₂-Entnahme 2024–2100 je Szenario gegen Bäume nur auf kühlenden Flächen und auf allen Flächen"',
                  'data-chart="v2s" data-label="Sieben CMIP7-Szenarien: ihre Entnahme bis 2100 (Land und neuartig) neben dem, was unsere Bäume in derselben Welt netto liefern"')
s32 = re.sub(r'<p class="takeaway" data-step="1" style="--d:0; font-size:21px">.*?</p>',
             '<p class="takeaway" data-step="1" style="--d:1800; font-size:21px">Wer die Erwärmung niedrig halten will, setzt auf Entnahme: 230 bis 820 Gt bis 2100, oft zur Hälfte an Land. Unsere Bäume liefern in derselben Welt netto 60 bis 66 Gt, in wärmeren Welten etwas weniger — 8 bis 27 % dessen, was diese Szenarien voraussetzen. Szenarien ohne Entnahme erwärmen die Erde um 3 °C. Es braucht also auch Maschinen.</p>',
             s32, flags=re.S)
s32 = re.sub(r'<p class="src">.*?</p>',
             '<p class="src">Entnahme und Emissionen: CMIP7-Markerszenarien (van Vuuren et al. 2026), Summe 2024–2100, wie Folie 3. Bäume: eigene Rechnung, typischer Wald, gepflanzt 2025, gleiche Flächen in allen Szenarien; netto = brutto × Netto-Anteil aus FaIR (Leach et al. 2021; Smith et al. 2024), angetrieben mit den Emissionen desselben Szenarios.</p>',
             s32, flags=re.S)
s32 = re.sub(r'<aside class="notes" data-n="\d+">.*?</aside>', """<aside class="notes" data-n="0">
    <p>Jetzt die Frage vom Anfang: Braucht es die Maschine überhaupt? Hier die sieben Szenarien von Folie 3, sortiert danach, wie warm es 2100 wird — links optimistisch, rechts pessimistisch. Jede Welt ist in sich stimmig: Dieselben Emissionen treiben FaIR an, und die Entnahme ist die, mit der genau dieses Szenario rechnet. Links in jeder Gruppe die Entnahme des Szenarios: hellgrün an Land, also mehr Wald und weniger Abholzung, türkis neuartig, also BECCS und Maschinen. Rechts daneben unsere Bäume in derselben Welt: schraffiert, was im Holz steckt, ausgefüllt, was nach Albedo netto wirkt, orange überall gepflanzt. In wärmeren Welten wirkt jede Tonne etwas schwächer und Störungen nehmen zu: 66 Gigatonnen in Very Low, 60 in High. Die Szenarien, die niedrig bleiben, setzen ein Vielfaches davon voraus — oft schon allein an Land. Die Szenarien ohne Entnahme landen bei 3 Grad. Bäume reichen also nicht; es braucht auch Maschinen.</p>
    <p class="q">Falls Fragen kommen — Netto = brutto (Kaskade, 106 Gt auf den kühlenden, 155 Gt auf allen Flächen) × Netto-Anteil aus zwei FaIR-Läufen je Szenario (mit und ohne Albedo), unser FaIR-Mitglied mit den CMIP7-Emissionen aus dem Archiv des ScenarioMIP-Papiers. Die Szenarien enthalten Landnutzung und Entnahme schon als Annahme; wir rechnen nur zurück, was unsere Bäume in dieser Welt leisten. Der Landanteil umfasst mehr als Aufforstung (weniger Abholzung, Böden). Unser Mitglied: Very Low 1,7 °C, High 3,3 °C im Jahr 2100 (Ensemble-Median des Papiers 1,6 und 3,45 °C). Die übrigen Folien rechnen mit SSP2-4,5 als mittlerem Hintergrund; dort netto 62 Gt. Bastin et al. 2019 (Folie 6): 205 GtC, also rund 750 Gt CO₂.</p>
  </aside>""", s32, flags=re.S)

# ---------------------------------------------------------------- 33, 34 DAC schemata
s33 = renumber(section("Wie eine Maschine CO₂ aus der Luft holt"), 33)
s34 = renumber(section("Wie wir DAC rechnen"), 34)
s34 = s34.replace('<text x="1138" y="272" font-size="23" font-weight="600" fill="var(--paper)">Netto-Wirkungsgrad</text>',
                  '<text x="1138" y="272" font-size="23" font-weight="600" fill="var(--paper)">Netto-Anteil</text>')
s34 = s34.replace("Daraus der Netto-Wirkungsgrad — dieselbe Größe wie beim Baum", "Daraus der Netto-Anteil — dieselbe Größe wie beim Baum")
s34 = s34.replace('aria-label="Rechenweg: Wetter und Prozessmodell ergeben den Strom je Tonne; mit dem Strommix rechnet die Ökobilanz daraus die Emissionen; daraus der Netto-Wirkungsgrad"',
                  'aria-label="Rechenweg: Wetter und Prozessmodell ergeben den Strom je Tonne; mit dem Strommix rechnet die Ökobilanz daraus die Emissionen; daraus der Netto-Anteil"')
s34 = s34.replace('<text x="1138" y="134" font-size="20" fill="var(--moss)">η = 1 − Albedo-Offset</text>',
                  '<text x="1138" y="134" font-size="20" fill="var(--moss)">Netto-Anteil nach Albedo</text>')
s34 = s34.replace('<text x="808" y="142" font-size="17" fill="var(--muted)">Karte auf der nächsten Folie</text>',
                  '<text x="808" y="142" font-size="17" fill="var(--muted)">je nach Klima am Ort</text>')
s34 = s34.replace("Daraus der Netto-Wirkungsgrad — dieselbe Größe wie beim Baum: Dort frisst die Albedo einen Teil der Tonne, hier die Emissionen.</p>",
                  "Daraus der Netto-Wirkungsgrad — dieselbe Größe wie beim Baum: Dort frisst die Albedo einen Teil der Tonne, hier die Emissionen. Deshalb rechnen wir DAC so und nicht mit einem Literaturwert: Strom und Strommix ändern sich mit Ort und Jahr, und nur so lassen sich Baum und Maschine am selben Ort im selben Jahr vergleichen.</p>")
s34 = s34.replace("Methode: docs/methods/dac-modell.md.</p>",
                  "Nicht im Modell: Kosten; Flächenbedarf der Anlage (klein gegen den Wald); Zusatzstrom (gerechnet wird mit dem Netzmittel der Region); Flüssig-DAC; Undichtigkeit des Speichers (geologische Speicherung gilt als dauerhaft). Die Emissionen der Anlage gehen mit GWP100 ein — eine Vereinfachung gegenüber dem Baum, der durch FaIR läuft; bei wenigen Prozent Emissionen je Tonne ändert das wenig. Methode: docs/methods/dac-modell.md.</p>")

# ---------------------------------------------------------------- 35 DAC map (new)
s35 = '''<section class="slide" data-ch="vergleich" data-title="Netto-Entnahme von DAC">
  <header class="sh"><h2>Netto-Entnahme von DAC, 2025 bis 2100</h2></header>
  <div class="body">
    <div class="chart" data-chart="d5" data-label="Weltkarte: Anteil einer entnommenen Tonne, der nach den Emissionen von Strom und Anlage netto bleibt, Jahr für Jahr von 2025 bis 2100"></div>
    <div class="foot"><div></div><p class="takeaway" data-step="1" style="--d:0; font-size:21px">Mit dem Strom von 2025 bleiben im Median 41 % der entnommenen Tonne netto; auf 3 % des Landes, vor allem in Indien, emittiert DAC mehr, als es entnimmt. Mit der Energiewende steigt der Median auf 65 % (2030), 79 % (2035) und 91 % (2040). Zum Vergleich: Bäume auf den kühlenden Flächen kommen auf 59 %. Im hohen Norden (20 % des Landes) ist es für Sorbens-DAC zu kalt.</p></div>
  </div>
  <p class="src">Eigene Rechnung, Sorbens-DAC mit Wärmepumpe (Sendi et al. 2022; Klima CRU TS 4.09). Strommix je Region und Jahr: Modellergebnis REMIND-EU SSP2-NDC (heutige Zusagen) über premise, ecoinvent 3.12; GWP100. Mittel je 2°-Block; Median über das Land, auf dem DAC möglich ist.</p>
  <aside class="notes" data-n="35">
    <p>Lohnt sich die Maschine? Die Karte zeigt, welcher Anteil einer entnommenen Tonne netto übrig bleibt, wenn man die Emissionen des Stroms und der Anlage abzieht. Türkis heißt: viel bleibt. Mit dem Strom von heute im Median gut 40 %. In Joensuu mit finnischem Strom schon 84 %, in Aachen gut die Hälfte, bei Marabá knapp zwei Drittel. Mit Kohlestrom bleibt fast nichts: Krakau 5 %, Kinshasa 16 %, Peking 18 %; wo es orange wird, vor allem in Indien, emittiert die Maschine mehr, als sie entnimmt. Grau: Im hohen Norden ist es für dieses Verfahren zu kalt. Zum Vergleich mit dem Baum, derselbe Netto-Anteil: Aachen 65 %, Joensuu 32 %, Marabá 83 %, über alle kühlenden Flächen 59 %. Heute ist der Baum also im Mittel die sauberere Tonne, ab etwa 2030 die Maschine.</p>
    <p>Jetzt lasse ich die Jahre laufen [Play]. Mit dem Strom wird die Maschine besser, ohne dass sie selbst sich ändert: Aachen erreicht um 2030 gut 80 %, Krakau um 2035, Peking und Kinshasa um 2040. Ab etwa 2040 bleiben fast überall über 90 %. Das ist die Reihenfolge für die Maschine: zuerst dort, wo der Strom sauber ist; nicht mit fossilem Strom; nicht im hohen Norden.</p>
    <p class="q">Falls Fragen kommen — Annahme mit Gewicht: REMIND-EU SSP2-NDC dekarbonisiert schnell (Deutschland 0,42 → 0,09 kg CO₂e/kWh von 2020 bis 2030); mit langsamerer Energiewende verschieben sich die Jahre nach hinten. Gerechnet wird mit dem Netzmittel der Region, nicht mit zusätzlichem Ökostrom. Strom je Tonne 1,1–1,9 MWh; eine Gigatonne im Jahr bräuchte rund 1 500 TWh, etwa 5 % der heutigen Weltstromerzeugung. Mit den Climeworks-Energiewerten (doppelt so viel Wärme) wird es später (Methodendoku). Werte zwischen den Stützjahren der Ökobilanz (2020, 2030, 2040, 2050, 2075, 2100) linear interpoliert; die Karte gleitet zwischen den Jahren. Median 2050: 94 %. Ein Block zeigt das flächengewichtete Mittel seiner Zellen; die Anteile im Text sind aus den Zellen gerechnet.</p>
  </aside>
</section>
'''


d6sec = """<section class="slide" data-ch="vergleich" data-title="DAC in drei Strompfaden">
  <header class="sh"><h2>Netto-Entnahme von DAC in drei Strompfaden</h2></header>
  <div class="body">
    <div class="chart" data-chart="d6" data-label="Median des netto verbleibenden Anteils einer Tonne bei DAC, 2025 bis 2100, in drei REMIND-EU-Pfaden, mit dem Netto-Anteil der Bäume als Band"></div>
    <div class="foot"><div></div><p class="takeaway" data-step="1" style="--d:1800; font-size:22px">Wie schnell der Strom sauber wird, verschiebt DAC um einige Jahre, nicht das Bild: Mit dem Strom von 2025 bleiben im Median 36 bis 41 % der Tonne, 2040 schon 80 bis 93 %. Spätestens ab etwa 2035 bleibt bei DAC je Tonne netto mehr übrig als bei einem Baum auf kühlender Fläche.</p></div>
  </div>
  <p class="src">Eigene Rechnung wie „Netto-Entnahme von DAC“; Strommix und Hintergrund je Pfad: Modellergebnis REMIND-EU über premise 2.4.9 (Sacchi et al. 2022), ecoinvent 3.12: SSP2-PkBudg650 (Budget 650 Gt, etwa 1,5 °C), SSP2-NDC (heutige Zusagen, bisher), SSP2-NPi (nur umgesetzte Politik). Median über das Land, auf dem Sorbens-DAC möglich ist. Bäume: Netto-Anteil 2100 der kühlenden Flächen in den sieben CMIP7-Welten.</p>
  <aside class="notes" data-n="0">
    <p>Die Karte eben hing an einer Annahme: wie schnell der Strom sauber wird. Hier dieselbe Rechnung mit drei Pfaden des Energiesystemmodells REMIND. Dunkel: ein Pfad, der zu 1,5 Grad passt. Mittel: heutige Zusagen, unser bisheriger Fall. Hell: nur die Politik, die schon umgesetzt ist. Jede Linie ist der Median über das Land, auf dem die Maschine laufen kann. Heute liegen alle drei bei knapp 40 %. Mit sauberem Strom steigen alle — im pessimistischen Pfad nur einige Jahre später: 2040 80 statt gut 90 %. Das grüne Band ist der Netto-Anteil der Bäume auf den kühlenden Flächen, in allen sieben Welten von eben. Spätestens um 2035 liegt die Maschine je Tonne darüber, in jedem Pfad.</p>
    <p class="q">Falls Fragen kommen — Median Netto-Anteil 2025 / 2030 / 2040 / 2050: PkBudg650 39 / 62 / 93 / 96 %, NDC 41 / 65 / 91 / 94 %, NPi 36 / 55 / 80 / 89 %. Netto emittierend mit dem Strom von 2025: 3 / 4 / 5 % des Landes. Dass der 1,5-°C-Pfad 2025 knapp unter dem mittleren liegt, kommt aus dem Stützjahr 2030 (in einigen Regionen mischt REMIND-EU dort etwas anders); 2020 ist für alle Pfade dieselbe Datenbank. Auch NPi macht den Strom in Europa bis 2050 weitgehend sauber; der Unterschied liegt vor allem in Asien in den 2030er und 2040er Jahren (Indien 2040: 0,26 gegen 0,02 kg CO₂e/kWh). Zuordnung zu den CMIP7-Welten nur grob: PkBudg650 ≈ Very Low, NDC ≈ Medium-Low, NPi ≈ Medium. Neue Datenbanken: scripts/build_premise_scenarios.py, Ökobilanz: scripts/dac_lca_precompute.py --pathway.</p>
  </aside>
</section>
"""

# ---------------------------------------------------------------- 36 time
s36 = renumber(section("Zeit zählt"), 36)
STRIP = '''    <svg class="schema" data-export="s_mitnahme" data-step="1" viewBox="0 0 1424 104" style="width:100%; flex:none; margin-top:6px" aria-label="Was der Wald vor Ort zusätzlich bringt: Verdunstung, Windschutz, Lebensraum, Schatten">
      <g font-family="IBM Plex Sans" class="pop" data-step="1" style="--d:600">
        <line x1="0" y1="2" x2="1424" y2="2" stroke="var(--paper-line)" stroke-width="2"/>
        <text x="0" y="36" font-size="16" letter-spacing="1.5" fill="var(--muted)">WAS DER WALD VOR ORT ZUSÄTZLICH BRINGT</text>
        <text x="0" y="62" font-size="16" letter-spacing="1.5" fill="var(--muted)">IN DER BILANZ NICHT BEWERTET</text>
        <g transform="translate(440 22)">
          <path d="M18 6 c-11 16-16 27-16 34a16 16 0 0 0 32 0c0-7-5-18-16-34z" fill="none" stroke="var(--zs)" stroke-width="3"/>
          <text x="48" y="22" font-size="22" font-weight="600" fill="var(--ink)">Verdunstung</text>
          <text x="48" y="50" font-size="18" fill="var(--ink-2)">kühlt die Luft am Ort</text>
        </g>
        <g transform="translate(670 22)">
          <g transform="translate(-2 6) scale(1.7)" fill="none" stroke="#7f7f7f" stroke-width="1.6" stroke-linecap="round"><path d="M12.8 19.6A2 2 0 1 0 14 16H2"/><path d="M17.5 8a2.5 2.5 0 1 1 2 4H2"/><path d="M9.8 4.4A2 2 0 1 1 11 8H2"/></g>
          <text x="48" y="22" font-size="22" font-weight="600" fill="var(--ink)">Windschutz</text>
          <text x="48" y="50" font-size="18" fill="var(--ink-2)">bremst den Wind</text>
        </g>
        <g transform="translate(890 22)">
          <g transform="translate(-2 6) scale(1.6)" fill="none" stroke="#654320" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M16 7h.01"/><path d="M3.4 18H12a8 8 0 0 0 8-8V7a4 4 0 0 0-7.28-2.3L2 20"/><path d="m20 7 2 .5-2 .5"/><path d="M10 18v3"/><path d="M14 17.75V21"/><path d="M7 18a6 6 0 0 0 3.84-10.61"/></g>
          <text x="48" y="22" font-size="22" font-weight="600" fill="var(--ink)">Lebensraum</text>
          <text x="48" y="50" font-size="18" fill="var(--ink-2)">für Vögel, Insekten, Pilze</text>
        </g>
        <g transform="translate(1200 22)">
          <path d="M2 38 H36" stroke="#7a7466" stroke-width="9" stroke-linecap="round" opacity=".5"/>
          <text x="48" y="22" font-size="22" font-weight="600" fill="var(--ink)">Schatten</text>
          <text x="48" y="50" font-size="18" fill="var(--ink-2)">kühlt den Boden</text>
        </g>
      </g>
    </svg>
'''
s36 = s36.replace('<div class="chart" data-chart="z1"', STRIP.rstrip("\n") + '\n    <div class="chart" data-chart="z1"', 1)
# strip after the chart, not before
s36 = s36.replace(STRIP.rstrip("\n") + '\n    <div class="chart" data-chart="z1" data-label="Anteil der Entnahme bis 2100, den ein 2025 gepflanzter Baum schon geschafft hat, gegen DAC"></div>',
                  '<div class="chart" data-chart="z1" data-label="Anteil der Entnahme bis 2100, den ein 2025 gepflanzter Baum schon geschafft hat, gegen DAC"></div>\n' + STRIP.rstrip("\n"))
s36 = re.sub(r'<p class="takeaway" data-step="1" style="--d:0">.*?</p>',
             '<p class="takeaway" data-step="2" style="--d:0; font-size:22px">Ein 2025 gepflanzter Baum hat bis 2035 16 % und bis 2050 49 % dessen entnommen, was er bis 2100 schafft; DAC entnimmt ab dem ersten Betriebsjahr. Wer bis 2100 kühlen will, muss Bäume deshalb früh pflanzen, auf den Flächen, auf denen sie kühlen. Die lokalen Wirkungen des Waldes kommen hinzu; die Bilanz bewertet sie nicht.</p>',
             s36, flags=re.S)
s36 = s36.replace("Deshalb heißt die Reihenfolge: Bäume jetzt pflanzen — gerade weil sie langsam sind.</p>",
                  "Deshalb heißt die Reihenfolge: Bäume jetzt pflanzen — gerade weil sie langsam sind. Und unten: Was der Wald vor Ort sonst noch tut, haben wir ganz am Anfang gesehen — Verdunstung, Windschutz, Lebensraum, Schatten. Für das globale Klima zählen diese Wirkungen kaum, deshalb stehen sie nicht in der Bilanz. Für die Menschen vor Ort zählen sie, und keine Maschine liefert sie.</p>")

# ---------------------------------------------------------------- 37 ranking (new schema)
def cell(x, y, col, title, lines, pill, pill_w, step):
    t = "\n".join(f'          <text x="{x + 28}" y="{y + 84 + 28 * k}" font-size="19" fill="var(--ink-2)">{ln}</text>' for k, ln in enumerate(lines))
    return f'''        <g class="pop" data-step="{step}">
          <rect x="{x}" y="{y}" width="600" height="206" rx="10" fill="var(--paper-deep)" stroke="var(--paper-line)" stroke-width="2"/>
          <rect x="{x}" y="{y}" width="8" height="206" rx="4" fill="{col}"/>
          <text x="{x + 28}" y="{y + 44}" font-size="25" font-weight="600" fill="var(--ink)">{title}</text>
{t}
          <rect x="{x + 28}" y="{y + 154}" width="{pill_w}" height="36" rx="18" fill="#efcfae"/><text x="{x + 28 + pill_w / 2}" y="{y + 179}" text-anchor="middle" font-size="18" fill="var(--ink)">{pill}</text>
        </g>'''


s37 = f'''<section class="slide" data-ch="vergleich" data-title="Rangfolge für Baum und Maschine">
  <header class="sh"><h2>Rangfolge für Baum und Maschine: wo zuerst, wo nicht</h2></header>
  <div class="body">
    <svg class="schema" data-export="s_rangfolge" viewBox="0 0 1424 548" style="width:100%; flex:1; min-height:0" aria-label="Zwei mal zwei: Baum und Maschine, jeweils wo zuerst und wo nicht">
      <g font-family="IBM Plex Sans">
        <g class="pop" style="--d:100">
          <text x="200" y="28" font-size="16" letter-spacing="1.5" fill="var(--moss)" font-weight="600">BAUM</text>
          <text x="820" y="28" font-size="16" letter-spacing="1.5" fill="var(--fjord)" font-weight="600">MASCHINE (DAC)</text>
          <text x="0" y="154" font-size="16" letter-spacing="1.5" fill="var(--muted)">ZUERST</text>
          <text x="0" y="374" font-size="16" letter-spacing="1.5" fill="var(--muted)">NICHT</text>
        </g>
{cell(200, 46, "var(--moss)", "Wo er am stärksten kühlt, und früh", ["Tropen, wenig Schnee: netto bleiben bei Marabá (BR)", "83 %, in Aachen (DE) 65 %, in Joensuu (FI) 32 %.", "Früh: 5 Jahre Warten kosten 2050 ein Fünftel."], "0,42 Gha · netto 62 Gt CO₂", 250, 1)}
{cell(200, 266, "var(--alb)", "Wo die Albedo überwiegt", ["Schneereicher Norden und Trockengebiete: Dort", "wärmt der Baum bis 2100. Auf allen Flächen", "sinkt die Wirkung von 62 auf 29 Gt CO₂."], "0,41 Gha wärmen bis 2100", 236, 1)}
{cell(820, 46, "var(--fjord)", "Wo der Strom sauber ist", ["Heute z. B. Joensuu (FI): 84 % der Tonne netto.", "Mit der Energiewende fast überall: 2040 bleiben", "im Median 91 % der Tonne."], "Median 2025: 41 % · 2040: 91 %", 290, 2)}
{cell(820, 266, "#c4612c", "Mit fossilem Strom, im hohen Norden", ["Mit dem Strom von 2025: Krakau (PL) 5 %,", "Kinshasa (CD) 16 %, Peking (CN) 18 % netto.", "Im Norden ist es für Sorbens-DAC zu kalt."], "20 % des Landes zu kalt", 228, 2)}
        <text class="pop" data-step="3" x="200" y="508" font-size="20" fill="var(--ink-2)">Dazu bringt der Wald vor Ort, was keine Maschine liefert: Schatten, Verdunstung, Windschutz, Lebensraum.</text>
        <text class="pop" data-step="3" x="200" y="540" font-size="20" fill="var(--ink)">Keines von beiden ersetzt die Minderung der Emissionen: Die Szenarien setzen sie voraus.</text>
      </g>
    </svg>
    <div class="foot"><div></div><p class="takeaway" data-step="4" style="--d:0; font-size:22px">Beide Rangfolgen folgen aus derselben Größe: dem Anteil einer entnommenen Tonne, der je Ort und Jahr netto bleibt. Beim Baum begrenzt die Albedo, bei der Maschine der Strom.</p></div>
  </div>
  <p class="src">Eigene Rechnung; Zahlen von den Folien „Was ein Baum wo bewirkt“, „Entnahme-Bedarf der Szenarien“ und „Netto-Entnahme von DAC“; Zeitverlauf: Wachstumskurve je Ort (Walker et al. 2022; Cook-Patton et al. 2020). Baum: typischer Wald, gepflanzt 2025, Horizont 2100. DAC: Strommix REMIND-EU SSP2-NDC.</p>
  <aside class="notes" data-n="36">
    <p>Was heißt das konkret? Links der Baum, rechts die Maschine; oben, wo zuerst, unten, wo nicht. Der Baum zuerst dort, wo er am stärksten kühlt — in den Tropen. Und früh: Fünf Jahre Warten kosten um 2050 ein Fünftel der Kühlung; DAC dagegen entnimmt ab dem ersten Betriebsjahr. Nicht dort, wo die Albedo überwiegt: im schneereichen Norden und in Trockengebieten. Die Maschine zuerst dort, wo der Strom sauber ist — heute etwa in Finnland, mit der Energiewende fast überall. Nicht mit Kohlestrom, dann emittiert sie fast so viel, wie sie entnimmt, und nicht im hohen Norden, da ist es für das Verfahren zu kalt. Unten: Der Wald bringt vor Ort mehr als Kohlenstoff — Schatten, Verdunstung, Windschutz, Lebensraum. Für das globale Klima zählt das kaum, deshalb steht es nicht in der Bilanz; für die Menschen vor Ort zählt es. Und keines von beiden ersetzt es, die Emissionen zu senken.</p>
    <p class="q">Falls Fragen kommen — Und wo beides geht: Wer entnimmt je Tonne sauberer? Mit dem Strom von 2020 die Maschine nur auf 21 % der bepflanzbaren Fläche; wo beides geht, überholt sie den Baum mit der Energiewende im Mittel 2031. Das steht im Backup („Die Maschine wird zur Messlatte“, „DAC fährt mit der Energiewende mit“). Es ist aber nicht die entscheidende Frage: Die Maschine braucht kaum Fläche, man kann am selben Ort beides tun, und gebraucht wird beides. Die Grenze ist für den Baum die kühlende Fläche, für die Maschine sauberer Strom und Geld: rund 1 500 TWh je Gt CO₂ im Jahr, etwa 5 % der heutigen Weltstromerzeugung. Kosten rechnet das Modell nicht. Die Zahlen 62 und 29 Gt sind netto nach Albedo bis 2100; 0,41 Gha = wiederbewaldbare Fläche, auf der der Baum bis 2100 wärmt.</p>
  </aside>
</section>
'''

# ---------------------------------------------------------------- 38 answer (replaces "Die Antwort hängt an der Grenze")
s38 = '''<section class="slide" data-ch="vergleich" data-title="Auf dem Holzweg? Nein.">
  <header class="sh"><h2>Auf dem Holzweg? Nein.</h2></header>
  <div class="body">
    <div class="cols3" style="margin-top:24px">
      <div class="col rise"><h4><span class="big-n">1</span>Bäume reichen nicht</h4><p>Netto 60 bis 66 Gt CO₂ bis 2100, je nach Szenario 8 bis 27 % der Entnahme, mit der es rechnet — und das nur, wenn ausschließlich dort gepflanzt wird, wo der Baum kühlt.</p></div>
      <div class="col rise" data-step="1"><h4><span class="big-n">2</span>Maschinen werden gebraucht, aber nicht überall</h4><p>Mit dem Strom von 2025 bleiben im Median 41 % der Tonne. Zuerst dort, wo der Strom sauber ist; nicht mit fossilem Strom und nicht im hohen Norden.</p></div>
      <div class="col rise" data-step="2"><h4><span class="big-n">3</span>Bäume früh, Maschinen mit der Energiewende</h4><p>Fünf Jahre später gepflanzt, fehlt um 2050 ein Fünftel der Kühlung; dazu bringt der Wald vor Ort Schatten und Lebensraum. DAC wirkt ab Betrieb und wird mit sauberem Strom besser.</p></div>
    </div>
    <div style="flex:1"></div>
    <p class="takeaway" data-step="3" style="--d:0; font-size:25px">Die Ingenieure sind nicht auf dem Holzweg: Ohne Maschinen lässt sich der Bedarf der Szenarien nicht decken. Für Baum und Maschine hängt die Wirkung je Tonne am Ort und am Zeitpunkt. Die naive Rechnung zog die Grenze um den Baum; mit der vollen Systemgrenze heißt die Antwort: beides, jeweils am richtigen Ort.</p>
  </div>
  <aside class="notes" data-n="37">
    <p>Zurück zur Frage im Titel: Sind die Ingenieure auf dem Holzweg? Nein. Erstens reichen die Bäume nicht — selbst klug gepflanzt binden sie knapp ein Fünftel dessen, was das niedrigste Szenario braucht. Zweitens werden Maschinen deshalb gebraucht, aber nicht überall: Mit heutigem Strom bleibt im Mittel weniger als die Hälfte der Tonne, mit Kohlestrom fast nichts, im hohen Norden geht das Verfahren nicht. Drittens die Zeit: Bäume jetzt, weil sie langsam sind; Maschinen in dem Maß, wie der Strom sauber wird. Die naive Rechnung vom Anfang hat die Grenze um den Baum gezogen und kam auf zwei Billionen Bäume für den ganzen Bedarf. Mit der vollen Grenze ist die Antwort: beides, jeweils am richtigen Ort und zur richtigen Zeit.</p>
  </aside>
</section>
'''

# ---------------------------------------------------------------- 39 method (replaces "Was diese Arbeit neu zeigt")
s39 = '''<section class="slide" data-ch="vergleich" data-title="Was für diese Antworten nötig war">
  <header class="sh"><h2>Was für diese Antworten nötig war</h2></header>
  <div class="body">
    <table style="margin-top:4px">
      <thead><tr><th style="width:22%">Gebraucht</th><th style="width:28%">Baum</th><th style="width:26%">Maschine (DAC)</th><th style="width:24%">Erst damit sichtbar</th></tr></thead>
      <tbody style="vertical-align:top">
        <tr class="rise"><td style="font-weight:600; color:var(--fjord)">Systemgrenze bis zur Temperatur</td><td style="font-size:18px">Wachstum, Albedo, Rückgabe an Ozean und Land, vollere Atmosphäre, Störung</td><td style="font-size:18px">Strom, Anlage, Sorbens, Speicherung (Ökobilanz)</td><td style="font-size:18px">Netto-Anteil je Ort (Aachen (DE) 65 %, Joensuu (FI) 32 %); auf der Hälfte der Fläche wärmt der Baum</td></tr>
        <tr class="rise" data-step="1"><td style="font-weight:600; color:var(--fjord)">Je Ort und je Jahr</td><td style="font-size:18px">0,5°-Zellen: Waldtyp, Kohlenstoff, gemessene Albedo mit Zeitverlauf</td><td style="font-size:18px">Wetter am Ort; Strommix je Region und Jahr (REMIND-EU über premise)</td><td style="font-size:18px">Rangfolgen statt eines Mittelwerts</td></tr>
        <tr class="rise" data-step="2"><td style="font-weight:600; color:var(--fjord)">Ein kalibrierter Klima-Emulator, ein Horizont</td><td style="font-size:18px">FaIR (Leach et al. 2021; Smith et al. 2024): Entnahme als negative Emission, Albedo als Antrieb, im Szenario SSP2-4,5; bewertet 2100</td><td style="font-size:18px">Entnahme je Jahr, netto nach den eigenen Emissionen (diese mit GWP100)</td><td style="font-size:18px">Zeitverlauf: bis 2061 kühlt „überall pflanzen“ stärker, danach schwächer; Warten kostet vor allem um 2050. Statische Bilanzen und GWP100 liefern eine Zahl</td></tr>
      </tbody>
    </table>
    <p class="rise" data-step="3" style="margin-top:22px; font:400 18px/1.45 var(--sans); color:var(--ink-2)"><b style="color:var(--muted); letter-spacing:.08em; font-weight:600">NICHT IM MODELL</b> &nbsp; Kosten · Verdunstung und Wolken als eigene Klimawirkung · dynamische Schneedecke · Flüssig-DAC · Zusatzstrom statt Netzmittel · ein Klimamitglied statt Ensemble</p>
    <div style="flex:1"></div>
    <p class="takeaway" data-step="4" style="--d:0; font-size:22px">Die einzelnen Bausteine gibt es in der Literatur. Neu ist ihre Kombination: dieselbe zeitaufgelöste Rechnung je Ort für Baum und Maschine, mit einem kalibrierten Klima-Emulator statt fester Umrechnungsfaktoren.</p>
  </div>
  <aside class="notes" data-n="38">
    <p>Was hat es gebraucht, um diese Fragen zu beantworten? Drei Dinge. Erstens die Systemgrenze bis zur Temperatur: Erst mit Ozean, Land, vollerer Atmosphäre und Störung sieht man, wie viel die Albedo vom Nutzen des Kohlenstoffs frisst — in Aachen ein Drittel, in Joensuu zwei Drittel — und dass der Baum auf der Hälfte der Fläche wärmt. Am Baum allein gerechnet, wie in der naiven Rechnung, käme Aachen auf −158 statt −35 · 10⁻¹⁵ K (Backup „Was jede Erweiterung der Systemgrenze kostet“). Zweitens je Ort und je Jahr rechnen: Nur so entstehen Rangfolgen — wo zuerst, wo nicht — statt eines globalen Mittelwerts. Drittens ein echtes Klimamodell statt fester Faktoren: Wir lassen den Klima-Emulator FaIR laufen, der auf Messungen und auf die großen Klimamodelle kalibriert ist. Er rechnet selbst, dass sich die Senken füllen, dass jedes Kilogramm bei mehr CO₂ schwächer wirkt und wie träge die Erde reagiert. Erst damit lassen sich Tempo und Wirkung von Baum und Maschine im selben Horizont vergleichen; GWP100 und statische Bilanzen sehen nur Endzustände.</p>
    <p class="q">Falls Fragen kommen — Einordnung, ehrlich: Zeitaufgelöst rechnen auch andere — Kirschbaum et al. 2011 (ein Standort), Arora &amp; Montenegro 2011, Weber et al. 2024 und Liang et al. 2025 (Erdsystem- bzw. dynamische Modelle, ganze Szenarien). Statisch und je Ort rechnen Hasler et al. 2024 und Rohatyn et al. 2022. Das Tempo der Albedo stammt aus Williams et al. 2026. Unseres Wissens neu ist die Kombination: je Ort und Jahr, vom Baum bis zur Temperatur, mit Szenario-Hintergrund und Störung, und derselbe Rahmen für DAC. FaIR: Version 2.2, Parametersatz fair-calibrate 1.4.1, ein Mitglied nahe dem Ensemble-Median (ECS 2,9 K), nach einer vorab festgelegten Regel gewählt (docs/methods/klimamodell-fair.md). Grenzen: keine Kosten; Strom als Netzmittel der Region; Schneedecke statisch (boreal eher zu streng); Klimanormal 2011–2020 für DAC; DAC-Emissionen mit GWP100 statt durch FaIR. Vergleich mit anderen Studien: Backup „Einordnung: andere Studien“.</p>
  </aside>
</section>
'''

# ---------------------------------------------------------------- moved to the backup (live)
moved_titles = ["Einordnung: andere Studien", "Was eine Maschine braucht", "Wer wo entnehmen kann", "Heute: der Holzweg",
                "DAC fährt mit der Energiewende mit", "Die Maschine wird zur Messlatte",
                "Beides — in der richtigen Reihenfolge", "Die Antwort hängt an der Grenze", "Was diese Arbeit neu zeigt"]
moved = unnumber(s31) + "\n" + unnumber(s36) + "\n" + "".join(unnumber(section(t)) + "\n" for t in moved_titles)
moved = ('<!-- VERGLEICH-ALT: bis 2026-10-06 im Hauptteil (Storyline v2); live, bis die pptx nachgezogen ist.\n'
         '     Steht hinter dem Backup-Block, damit export_html_v2.py --backup ihn nicht überschreibt. -->\n' + moved)

def nbsp(sec: str) -> str:
    return re.sub(r"(\d) (%|Gt|Gha|mK|K\b|MWh|TWh)", "\\1\u00a0\\2", sec)


s31, s32, s35, s36, s37, s38, s39, w2, w3, w4, d6sec = map(nbsp, (s31, s32, s35, s36, s37, s38, s39, w2, w3, w4, d6sec))
new_chapter = (chapter[:chapter.index('<section class="slide chapter"')]
               + "\n".join([s29, s30, w2, w3, s32, s33, s34, s35, d6sec, s37, s38, s39]) + "\n")
tail = tail.replace('<aside class="notes" data-n="44">', '<aside class="notes" data-n="39">', 1)
tail = tail.replace("<!-- BACKUP:END -->\n", "<!-- BACKUP:END -->\n\n" + moved, 1)

# chapter name in the chips of the three chapter title slides and on the overview
page = head + new_chapter + tail
page = page.replace('<rect x="398" y="110" width="175" height="44"', '<rect x="398" y="110" width="252" height="44"')
page = re.sub(r'(<text x="442" y="139" font-size="20" font-weight="\d+" fill="[^"]*">)Vergleich(</text>)', r'\1Baum und Maschine\2', page)
page = page.replace('<text y="390" fill="var(--fjord)">Vergleich</text>', '<text y="390" fill="var(--fjord)" font-size="44">Baum und Maschine</text>')
page = page.replace('<text y="436" fill="var(--muted)" font-family="IBM Plex Sans" font-weight="400" font-size="21">Ingenieure auf dem Holzweg?</text>',
                    '<text y="436" fill="var(--muted)" font-family="IBM Plex Sans" font-weight="400" font-size="21">Was alle Bäume bewirken —</text>')
page = page.replace('<text y="464" fill="var(--muted)" font-family="IBM Plex Sans" font-weight="400" font-size="21">Bäume und Maschinen</text>',
                    '<text y="464" fill="var(--muted)" font-family="IBM Plex Sans" font-weight="400" font-size="21">und wozu die Maschine?</text>')
page = page.replace('aria-label="Drei Kapitel: Bäume, Klima, Vergleich — eine wachsende Systemgrenze"',
                    'aria-label="Drei Kapitel: Bäume, Klima, Baum und Maschine — eine wachsende Systemgrenze"')
page = page.replace("Vergleich = alle Flächen, alle Wege.</p>", "Baum und Maschine = alle Flächen, beide Entnahmewege.</p>")

# FaIR named and cited on the slides that use it
page = page.replace('<p class="src">Links Modellergebnis: FaIR, ein Klima-Emulator, kalibriert auf Messungen und CMIP6-Modelle (fair-calibrate 1.4.1, Mitglied 787474). Rechts eigene Rechnung: typischer Wald je Ort, gepflanzt 2025, SSP2-4,5.</p>',
                    '<p class="src">Links Modellergebnis des Klima-Emulators FaIR 2.2 (Leach et al. 2021), kalibriert auf Messungen und Klimamodelle (fair-calibrate 1.4.1, Smith et al. 2024; Mitglied 787474, ECS 2,9 K). Rechts eigene Rechnung mit FaIR: typischer Wald je Ort, gepflanzt 2025, SSP2-4,5.</p>')
page = page.replace('<p class="src">Eigene Rechnung; Wirkung je kg: Formel 5,35·ln(C/C₀) (Myhre et al. 1998, aus Strahlungstransfer-Modellen); CO₂-Pfad SSP2-4,5: Modellergebnis FaIR.</p>',
                    '<p class="src">Eigene Rechnung; Wirkung je kg: Formel 5,35·ln(C/C₀) (Myhre et al. 1998, aus Strahlungstransfer-Modellen); CO₂-Pfad SSP2-4,5: Modellergebnis des Klima-Emulators FaIR (Leach et al. 2021; Smith et al. 2024).</p>')
page = page.replace('<p class="src">Eigene Rechnung, volles Modell, SSP2-4,5; jede Stufe schaltet einen Prozess dazu.</p>',
                    '<p class="src">Eigene Rechnung, volles Modell mit dem Klima-Emulator FaIR (Leach et al. 2021; Smith et al. 2024), SSP2-4,5; jede Stufe schaltet einen Prozess dazu.</p>')
page = page.replace('<p class="src">Eigene Rechnung, volles Modell, SSP2-4,5; typischer Wald je Ort (Hasler et al. 2024), Kohlenstoff der Zelle (Walker et al. 2022), Albedo lokal gemessen oder Breitenband (Duveiller et al. 2018); Mittel je 2°-Block, gewichtet mit der wiederbewaldbaren Fläche.</p>',
                    '<p class="src">Eigene Rechnung, volles Modell mit FaIR (Leach et al. 2021), SSP2-4,5; typischer Wald je Ort (Hasler et al. 2024), Kohlenstoff der Zelle (Walker et al. 2022), Albedo lokal gemessen oder Breitenband (Duveiller et al. 2018); Mittel je 2°-Block, gewichtet mit der wiederbewaldbaren Fläche.</p>')
page = page.replace('<p class="src">Eigene Rechnung, volles Modell, SSP2-4,5; Anstieg der Störung mit der Erwärmung aus Modellprojektionen für Europa (Grünig et al. 2026).</p>',
                    '<p class="src">Eigene Rechnung, volles Modell mit FaIR (Leach et al. 2021), SSP2-4,5; Anstieg der Störung mit der Erwärmung aus Modellprojektionen für Europa (Grünig et al. 2026).</p>')
assert page.count("Leach et al. 2021") >= 7, page.count("Leach et al. 2021")

import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_player import patch
page = patch(page)
import patch_irf
page = patch_irf.patch(page)
import patch_fair
page = patch_fair.patch(page)
import patch_story
page = patch_story.patch(page)
import patch_klima
page = patch_klima.patch(page)
import patch_formeln
page = patch_formeln.patch(page)
import patch_tau
page = patch_tau.patch(page)
import patch_start
page = patch_start.patch(page)
import patch_stil
page = patch_stil.patch(page)
import patch_naiv
page = patch_naiv.patch(page)
import patch_luecke
page = patch_luecke.patch(page)
import patch_kommentare
page = patch_kommentare.patch(page)
import patch_takeaway
page = patch_takeaway.patch(page)
import patch_lesbar
page = patch_lesbar.patch(page)
import patch_merge
page = patch_merge.patch(page)
import patch_forcing
page = patch_forcing.patch(page)
import patch_pfeile
page = patch_pfeile.patch(page)
import patch_motion
page = patch_motion.patch(page)
import patch_story3
page = patch_story3.patch(page)
import patch_story4
page = patch_story4.patch(page)
import patch_dac_optim
page = patch_dac_optim.patch(page)
import patch_comments5
page = patch_comments5.patch(page)
import patch_menu
page = patch_menu.patch(page)
import patch_fastload
page = patch_fastload.patch(page)
HTML.write_text(page, encoding="utf-8")
print("ok", page.count('<aside class="notes" data-n='))
