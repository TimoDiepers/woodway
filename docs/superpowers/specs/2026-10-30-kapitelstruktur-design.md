# Kapitelstruktur: drei Kapitel, je zwei Teile, ein Bild pro Begriff

Stand 2026-10-30, abgestimmt mit Timo im Gespräch (visueller Begleiter, Prototypen `prototype-flow-v4.html`, `parts-v4.html` in `.superpowers/brainstorm/26071-1793346972/content/`).

## Ziel und Warum

- Zuhörer wissen jederzeit, **in welchem Kapitel und welchem Teil** sie sind, und was danach kommt. Vorschau leicht: keine Inhalte vorwegnehmen, nur Namen und ein Satz.
- **Ein Begriff = ein Bild = eine Farbe**, überall im Vortrag. Nichts taucht auf einer Kapitelfolie auf, das vorher nicht gefallen ist.
- Wirkung wie von einem Designer für eine Firma: ruhig, absichtsvoll, gedämpfte Farben. Bewegung ja, aber jede Bewegung hat einen Grund.

## Nicht-Ziele

- Keine Änderung an Inhalten der Folien (Rechnungen, Grafiken, Texte), außer Struktur, Anzeige und Farben.
- Keine neuen Zeichnungen außer den sechs Teil-Icons.
- Kein Umbau des Holzweg-/DAC-Teils, Schluss, Backup.

## Anti-Ziele (wäre ein Fehlschlag, auch wenn es funktioniert)

- Comichaft, Elemente fliegen kreuz und quer, mehrere Dinge bewegen sich gleichzeitig in verschiedene Richtungen.
- Teilfarben lauter als die Kapitelfarben.
- Verschiedene Bilder für denselben Begriff; Icons, deren Wichtigstes klein nicht zu erkennen ist.
- Nummerierung (1/2, ①/②) als Ersatz für Bedeutung; viel Text auf Kapitelfolien.

## Struktur

| Kapitel | Teil 1 | Teil 2 |
|---|---|---|
| Bäume | Kohlenstoff-Aufnahme | Reflexionsänderung |
| Klima | Strahlungsantrieb | Temperaturkurve |
| Potenzial | Kühlung eines Baums | Kühlung der Welt |

Logik als Kette: Bäume liefert Aufnahme und Reflexionsänderung eines Baums, Klima macht daraus (über die Strahlungsantrieb) seine Temperaturkurve, Potenzial macht aus der Temperaturkurve die Kühlung eines Baums an jedem Ort und dann die der Welt.

Zuordnung der bestehenden Folien (`data-title`):

- **Bäume / Kohlenstoff-Aufnahme:** Kohlenstoff-Aufnahme, Modellierung der Kohlenstoff-Aufnahme, Wachstumskurven im globalen Vergleich, (die Zwischenstand-Folie entfällt).
- **Bäume / Reflexionsänderung:** Reflexion, direkt: dunkles Laub; Reflexion, indirekt: Wolkenbildung; Netto-Energieänderung ΔQ̇ durch Albedo.
- **Klima / Strahlungsantrieb:** Gemeinsame Währung, Kohlenstoffkreislauf, Strahlungsantrieb von CO₂, Strahlungsantrieb der Albedo.
- **Klima / Temperaturkurve:** Vom Strahlungsantrieb zur Temperatur (einschließlich „Temperaturwirkung je Baum“).
- **Potenzial / Kühlung eines Baums:** Ein Baum an drei Orten, Ein Baum an jedem Ort.
- **Potenzial / Kühlung der Welt:** Wiederbewaldbare Fläche, Wo Aufforstung sich lohnt, Kühlende Wirkung globaler Aufforstung, Überschlagsrechnung noch einmal, Fazit *(meine Entscheidung: Fazit gehört zu Teil 2)*.

Technisch: `data-part="1|2"` auf jeder Inhaltsfolie (gibt es teils schon), Kapitel über `data-ch`.

## Übergang aus der Einleitung (F3 → F4)

- Kapitelnamen: **Baum-Modell**, **Klima-Modell**, **Potenziale** (Titel der Kapitelfolien, Anzeige, Abschlusskarten).
- F3 Überschlagsrechnung endet mit der Kritik (Science-Kommentare, kippende Schlagzeilen): die Rechnung war zu einfach.
- F4 Überblick, aufgebaut Klick für Klick, Titel zuerst „Was lief falsch?“, ohne Quellenzeile, Scheiben ohne Ring:
  - Start: nur Baum-Modell, mittig. Klick: seine zwei Kritikpunkte, ohne Teil-Icons und Teilnamen (die kommen erst mit den Kapitelfolien), je eine neutrale Karte (fette Aussage, eine gedämpfte Zeile): „Nur der Vorrat am Ende / wann der Baum bindet, zählt nicht“ (Bastin et al. nennen selbst „several decades“, rechnen aber ohne Zeitlimit), „Reflexion fehlte / dunkles Laub schluckt Sonnenlicht“.
  - Klick: Klima-Modell rechts dazu, das Paar gleitet in die Mitte. Klick: sein Punkt: „Gigatonnen statt Grad / Reflexion lässt sich nicht in CO₂ zählen“. (Keine Rückgabe durch Ozean und Land: die 320 Gt der UN sind schon mit dem Kohlenstoffkreislauf gerechnet; der Einwand von Lewis/Friedlingstein galt Bastins Vergleich mit den Emissionen.)
  - Klick: die Kritik-Karten blenden aus, das Paar rückt nach links und die Reihe setzt sich in die Mitte, nach einem Pfeil kommt Potenziale (ohne Text); der Titel blendet über zu „Wie viel können Bäume *wirklich* kühlen?“, „wirklich“ hell auf Grün.
  - Klick: vor jedem Kapitelnamen wächst eine Nummer (1, 2, 3; runder Badge in Kapitelfarbe) herein: jetzt ist es die Agenda.
- Übergänge der Scheiben (F4 → Kapitelfolie, Kapitelfolie → Anzeige) messen den sichtbaren Kreis, nicht die Zeichnung; F4 → Kapitelfolie gleitet 1 s gleichmäßig (ease-in-out).
- Von F4 gleitet die Scheibe des Baum-Modells in dessen Kapitelfolie. Die eigene Überblicksfolie entfällt.
- Die Zwischenstand-Folie im Kapitel Bäume entfällt; „direkt und indirekt“ führt die erste Reflexionsfolie ein.

## Kapitelfolie (Einstieg in ein Kapitel)

Ablauf wie `prototype-flow-v4.html`, Schritt `in0/in1/in2`:

1. Die Scheibe des Kapitels gleitet von ihrer Position (Überblick bzw. Eckanzeige) nach links und wächst auf ca. 330 px; die anderen Scheiben blenden aus. Gleichzeitig wird der Kapitelname zum großen Titel rechts daneben (Literata 600, ~80 px, Kapitelfarbe). Eine Bewegung, ein Element: 900 ms, `cubic-bezier(.16,1,.3,1)`.
2. Unter dem Titel ein Satz zum Ziel des Kapitels (IBM Plex Sans 21 px, ink2):
   - Bäume: „Was ein einzelner Baum tut, über die Zeit.“
   - Klima: „Was das für die Temperatur der Erde heißt.“
   - Potenzial: „Was alle Bäume zusammen schaffen.“
3. Der Ring zeichnet sich Bogen für Bogen (ab 700 ms und 1500 ms), jeder Bogen in seiner Teilfarbe. Mit jedem Bogen öffnet sich daneben eine Teilzeile per Wischblende von links (`clip-path`, 700 ms): Teil-Icon 56 px, Teilname (600, 22 px), eine Zeile darunter (16 px, muted):
   - Kohlenstoff-Aufnahme: „Wann bindet er wie viel CO₂?“
   - Reflexionsänderung: „Wie ändert er die Reflexion, über Laub und Wolken?“
   - Strahlungsantrieb: „Wie viel Wärme bleibt dadurch auf der Erde?“
   - Temperaturkurve: „Wie reagiert die Temperatur, Jahr für Jahr?“
   - Kühlung eines Baums: „Wie viel kühlt ein Baum, an jedem Ort?“
   - Kühlung der Welt: „Wie viel kühlen alle Bäume zusammen?“

   Im Editor anpassbar.
4. Ersetzt komplett: Eckszene (`x-*`, `.cscene`), `.cgoal`-Karten, `fx`/`fxk`-Overlays, `.dic`/`.drow`, `Deck.zoomInto`/`zoomDisc`.

## Anzeige auf Inhaltsfolien (oben rechts)

- Die drei Kapitelscheiben in Reihenfolge. Das aktuelle Kapitel als Pille (leicht in Kapitelfarbe getönt, so breit wie ihr Text): links im Ring (54 px) das Icon des aktuellen Teils (nicht die Kapitelscheibe; die fliegt von der Kapitelfolie herein und blendet bei der Landung ins Teil-Icon über), rechts daneben zwei Zeilen, Kapitelname (500, 14 px, Kapitelfarbe) über dem Teilnamen (600, 17 px, ink). Alle anderen Kapitel, auch erledigte, als kleine Scheiben (30 px), stark abgeblendet (32 % Deckkraft).
- Ring des aktuellen Kapitels: erledigter Teil in Kapitelfarbe, aktueller Teil in Teilfarbe, kommender Teil blasse Spur.
- Übergang Kapitelfolie → erste Inhaltsfolie: die große Scheibe gleitet in die Pille, die sich dann samt Text aus der Scheibe heraus entfaltet. Teilwechsel im selben Kapitel: die Pille nimmt ihre neue Breite an (alte und neue Folie gemeinsam, kein Doppelbild), der neue Teilname steigt ein, der neue Bogen zeichnet sich. Sonst steht die Anzeige still.
- Ersetzt: Kapitel-Pille der Navigation auf Inhaltsfolien und die `h-part`-Brotkrumen mit `i-*`-Icons.
- Holzweg/DAC, Fazit, Schluss, Backup: keine Anzeige.

## Teil-Icons

Sechs runde Icons im Stil der Kapitelscheiben: Kreis in Teilfarbe, Zeichnung in Papierfarbe, Sonne in Sonnengelb. Das Wichtige ist groß, damit es bei 28 px erkennbar bleibt (geprüft in `parts-v4.html`):

- Kohlenstoff-Aufnahme: großes O=C=O, Pfeil hinab in eine Krone.
- Reflexionsänderung: Sonne und großer V-Strahl über einer Fläche.
- Strahlungsantrieb: gestrichelte Bilanzgrenze, Sonnenstrahl hinein, Wärmewelle hinaus.
- Temperaturkurve: Thermometer links, daneben große ΔT-Kurve unter die gestrichelte Nulllinie.
- Kühlung eines Baums: Baum mit Thermometer und Pfeil nach unten.
- Kühlung der Welt: Erdausschnitt voller Bäume.

Quelle: die `<symbol>`-Definitionen in `.superpowers/brainstorm/26071-1793346972/content/parts-v4.html` (Symbole `k-co2`, `k-refl`, `k-bal`, `k-temp`, `k-one`, `k-world`); kommen als `<symbol>` in `deck/src/index.html` und ersetzen `i-co2`, `i-refl`, `i-bal`, `i-temp`. Dort stehen noch `var(--kco2)` usw.; im Deck auf die Variablen aus der Farbtabelle umstellen. Generator-Skripte liegen in `.superpowers/brainstorm/…/gen/`.

Verwendung (immer dasselbe Icon für denselben Teil): Teilzeilen der Kapitelfolie; Abschluss- und Zusammenfassungskarten (z. B. `ovf`-Karte Bäume, „Überschlagsrechnung, noch einmal“); neben den Merkformeln/Ergebnissen eines Teils. Nicht in Folientiteln.

## Farben

Kapitelfarbe = Struktur (Titel, Scheibe, Anzeige). Teilfarbe = die physikalische Größe dieses Teils, überall wo sie vorkommt. Teilfarben bewusst gedämpfter als die Kapitelfarben; Kapitel bleiben das Dunkelste.

| | Kapitel | Teil 1 (Fläche / Text) | Teil 2 (Fläche / Text) |
|---|---|---|---|
| Bäume | `#304620` | Kohlenstoff `#437d61` / `#105b3e` | Reflexion `#9d945f` / `#787136` |
| Klima | `#612f2d` | Strahlungsantrieb `#ba8d66` / `#96683e` | Temperatur `#985248` / `#762c26` |
| Potenzial | `#04455f` | Baum `#4690a1` / `#006e81` | Welt `#316491` / `#004474` |

Flächenton für Icons, Ringbögen, Kurven, Flächen in Diagrammen; Textton für Formelsymbole, Beschriftungen, dünne Linien. (Erzeugt in LCh; Kapitel L≈27, Teile L 41–62, Chroma 24–34.)

Durchziehen (CSS-Variablen in `deck/src/css/deck.css`, KaTeX-Makros, Python-Grafiken in `src/nbs/*_figures.py`, `deck/mpl_to_echarts.py`, `deck/assets/data/ec_charts.js` mit Neu-Export):

- `--moss`, `--clay`, `--fjord` → neue Kapitelfarben.
- Kohlenstoff: `--co2`, `--s-phic`, `--s-dm`, `--s-eps`, CO₂-Kurven und -Reihen → Kohlenstoff-Töne.
- Reflexion/Albedo: `--alb`, `--s-phia`, `--s-dq`, Albedo-Reihen (`EC.alb`) → Reflexion-Töne.
- Strahlungsantrieb: `--s-phi`, `--s-phio` → Strahlungsantrieb-Töne.
- Temperatur: `--s-dt` und ΔT-Kurven → Temperatur-Töne.
- Potenzial-Karten/Reihen je Baum bzw. global → Baum- bzw. Welt-Töne.
- Sonne und Sonnenstrahlen in Zeichnungen (`--sun`, `--sun-ray`) bleiben gelb: das ist Licht, keine Größe *(meine Entscheidung)*. Der reflektierte Strahl `--ray` wird Reflexion-Ton.
- Übrige Symbolfarben der Modellinterna (`--s-mb`, `--s-ps` …) bleiben, außer sie kollidieren sichtbar mit einer Teilfarbe; dann zur Bauzeit angleichen *(Entscheidung beim Bauen)*.

## Was vom aktuellen, nicht committeten Stand bleibt

Bleibt: Kritikfolie mit „Zu einfach gerechnet…“-Zeile und Notizen; Wegfall der alten F6; Reflexion als direkt/indirekt (Titel, Rückblick, Grafikbeschriftungen); der aufbauende Klima-Diagramm-Ablauf (`km-*`, starkes Abblenden nicht relevanter Teile); Überblick linear mit drei Scheiben.

Fliegt raus: alles unter „Ersetzt“ oben, plus `.ico`/`h-part`-CSS und die `i-*`-Symbole.

## Rahmenbedingungen

- Bau über `uv run python deck/build.py`; `serve.py`-Editor (Texte der Kapitelfolien, Teilzeilen) muss weiter funktionieren.
- Rückwärts blättern: Zustände ohne Animation setzen. `prefers-reduced-motion`: alle Übergänge sofort.
- Folien skalieren auf jede Größe (Stage 1200×675 bzw. Deck-Maß); Positionen in Stage-Koordinaten, nicht in Bildschirm-Pixeln.
- Commit nur auf Timos Wunsch, ohne Attributionszeilen.

## Dem Bauenden überlassen

Genaue Pixelpositionen und Abstände im echten Deck-Maß, die Umsetzung der Gleitbewegung (FLIP o. ä.), Zuordnung von Randfällen bei Symbolfarben, Feinabstimmung der Zeitpunkte, solange der Ablauf oben erhalten bleibt.
