# Kapitel 5 einfacher erzählen: eine Temperaturkurve, eine Botschaft

Stand 2026-10-14, im Gespräch mit Timo entworfen (Brainstorming). Ersetzt die Erzählung über „die Lücke“ in Kapitel 5 und den letzten Schritt der Zeitgrafik in Kapitel 4.

## Ziel

**Botschaft:** Für die Spitze zählt, was vor 2050 wirkt.

Das Publikum soll ohne Umweg verstehen, was gezeigt wird. Heute gibt es drei Schichten „zusätzlich“: Lücke über Very Low, nach den Bäumen, dann DAC oder vegan. Dazu kommt eine Optimierung mit drei Zielstufen. Das fällt weg.

## Bezugsgröße: die echte Temperaturkurve

- **Ein Anker-Chart:** Erwärmung gegenüber vorindustriell in °C mit einer Linie bei 1,5 °C, die Fläche darüber leicht rot.
- **Ausgangskurve:** CMIP7 Very Low (Median, 7-Jahres-Mittel), wie in der Einleitung. Spitze etwa 1,82 °C um 2050.
- **Maßnahmen:** Jede Maßnahme ist eine eigene Kurve: Very Low plus die Temperaturwirkung der Maßnahme, **nicht** bei 1,5 °C oder null abgeschnitten. Fällt eine Kurve unter 1,5 °C, sieht man das.
- **Gleicher Ort:** Der Chart steht in Kapitel 5 auf allen Folien an derselben Stelle. Übernommene Linien laufen nicht neu ein, nur neue Linien animieren. Die bestehenden Regeln aus `animation-nur-neues` bleiben.

## Folienfolge

| Folie | Inhalt | Anker |
|---|---|---|
| Ende Kap. 4 („Wiederbewaldbare Fläche“, Schritt „Und reicht das?“) | Statt der roten Lücke in mK der Anker in hell. | Very Low, + Bäume (Forst, Holz gebunden), rund −0,03 K |
| 26 Holzweg? | wie jetzt: Männchen, DACCS-Kiste | – |
| 27 DAC-Modell | Flussdiagramm **bis η_C**, ohne Optimierung. Takeaway: Heute bleibt knapp die Hälfte netto, 2040 91 %; DAC hängt an der Zeit. | Very Low + Bäume |
| 28 DAC so schnell wie erlaubt | Satz: DAC wächst so schnell, wie einst die Windkraft wuchs, 20 %/a, gebaut, wo es am meisten bringt, bis 1,5 °C erreicht ist. Klick: 50 %/a, 100 %/a, unbegrenzt. Klick: Kosten (13,8 Bio. € im teuersten Jahr = 76 % EU-BIP; bis 2100 223 Bio. €). Takeaway: Schneller geht technisch nicht, früher zurück ist teuer, wir brauchen etwas anderes. | + DAC 20 %/a, dann 50, 100 %/a, unbegrenzt |
| 29 Warum Ernährung? | Motivation in drei Klicks, dann der Grenzfall „vegane Welt“ (siehe unten). Takeaway als Frage: Wie viel bringt das, und wann? | – (eigene kleine Grafik Methan gegen CO₂) |
| 30 Was sofort wirkt | Anker + vegane Welt (ohne DAC); rechts der Beitrags-Plot nach Ursache. Takeaway: Für die Spitze zählt, was vor 2050 wirkt. | + vegan; DAC-Linien gedimmt |
| 31 Finale | Spalte 3 auf die Botschaft angepasst | – |

## Folie 29 „Warum Ernährung?“

1. **Schnelle Kühlung:** Methan wirkt stark, ist aber nach rund 12 Jahren abgebaut; vom CO₂ bleibt ein Teil Jahrhunderte. Kleine Grafik: Anteil einer Emission, der in der Luft bleibt, Methan gegen CO₂ über 100 Jahre. Quelle: IPCC AR6 WG I, Kap. 7. Die Lebensdauer 11,8 Jahre ist beim Bau an der Tabelle zu prüfen.
2. **Keine technische Hürde:** Nichts muss erfunden oder gebaut werden. Pflanzliche Ernährung ist die größte Nachfrage-Option; die Hürden sind kulturell und politisch und brauchen politische Unterstützung. Quelle: IPCC AR6 WG III, Kap. 5 (Creutzig et al. 2022).
3. **Eher günstiger:** In Ländern mit hohem Einkommen ist vegane Ernährung 21–34 % billiger. Quelle: Springmann et al. 2021, Lancet Planetary Health, doi:10.1016/S2542-5196(21)00251-5. In den Notizen: gilt für wenig verarbeitete Lebensmittel; in Ländern mit niedrigem Einkommen ist gesunde, nachhaltige Ernährung teurer als die übliche.

Dann der Grenzfall in vier Punkten: alle ab 2026 vegan; Tierhaltung fällt weg (Methan, Lachgas, CO₂ aus Futter und Rodung); Ersatzprodukte brauchen etwa die Hälfte des Futterackers; Wald auf frei werdenden Flächen, wo er kühlt.

## Rechnung

Die Modelle bleiben, nur Ausgabe und Darstellung ändern sich.

- `scripts/build_zeitpfade_data.py` schreibt zusätzlich nach `zeitpfade.json`:
  - `vl_c`: Very Low in °C, Median, geglättet, **nicht** bei 1,5 °C abgeschnitten (aus `overshoot_series` vor dem Abschneiden).
  - `wirkung`: Temperaturwirkung je Maßnahme in mK, < 0 = kühler, ungeschnitten: `baeume` (`delta_t("forst")`), `dac_20`, `dac_50`, `dac_100`, `dac_frei` (je `-kuehlung_k` des Pfads), `vegan` (`dt_gase + dt_flaeche`).
- **DAC-Pfade:** `solve_min_peak(…, danach="frueh")` wie bisher, Wachstum 1,2 / 1,5 / **2,0 (neu)** / unbegrenzt. Im Vortrag heißt das „so schnell wie erlaubt, bis 1,5 °C erreicht ist“. Das dreistufige Ziel steht in Backup und Methodendoku. Die DAC-Wirkung wird auf der Lücke nach den Bäumen optimiert und zur Kurve „Very Low + Bäume“ addiert.
- **Kurven im Chart:** `vl_c + wirkung.baeume + wirkung.<maßnahme>` in °C.
- Die Kosten bleiben `path_cost` auf dem 20-%-Pfad.

## Was bleibt, was geht

- **Hauptteil, entfällt:** die Lücke als eigene Größe in mK; die Optimierung mit Zielstufen und Grenzen auf Folie 27; die Karte auf Folie 28; die Folie „Ausbautempo und Kosten“ (geht in 28 auf).
- **Backup, bleibt oder kommt hinzu:** Optimierung (Schema, Karte, Länder), Tempo-Charts mit 30 %/a, Kostenverlauf, Beiträge über die Zeit, Varianten.
- Notizen und Quellenzeilen der geänderten Folien werden neu geschrieben, Takeaways enden mit der Überleitungsfrage.

## Prüfung

- Das Deck baut. Die Klickzahl je Folie passt (keine leeren Klicks).
- Der Anker steht auf 27–30 pixelgleich und animiert nur neue Linien; gemessen mit dem CDP-Skript wie bisher.
- Die Zahlen auf Folien und in Notizen stimmen mit `zeitpfade.json` überein (Spitzen, Jahre, Kapazitäten, Kosten).
- Die Tests laufen ohne Sobol grün.
