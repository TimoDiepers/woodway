---
name: Aufforstung als Klima-Technologie
description: Dissertationsvortrag als HTML-Deck – Papier, Tinte und eine Farbe je Kapitel entlang einer wachsenden Systemgrenze
colors:
  paper: "#f2ede2"
  paper-deep: "#e7e0d0"
  paper-line: "#d6ccb6"
  ink: "#1b2420"
  ink-2: "#3f4a44"
  muted: "#5d665f"
  moss: "#3d552d"
  moss-soft: "#a9bc8f"
  clay: "#6e3d3a"
  clay-soft: "#d2a597"
  fjord: "#1e536d"
  fjord-soft: "#9dbfcf"
  dac-amber: "#9a6516"
  dac-amber-soft: "#e8cb92"
  night: "#14181a"
  co2: "#2e7d4f"
  alb: "#c8602a"
  ray: "#d9822b"
  sun: "#e8b84f"
  sun-ray: "#d9a441"
  amber: "#e0a83e"
  photosynthesis: "#2f7a45"
  respiration: "#7e4a74"
  decomposition: "#3d6698"
  disturbance: "#c0392b"
typography:
  chapter:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "104px"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.02em"
    fontVariation: "\"opsz\" 72"
  headline:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "50px"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.015em"
    fontVariation: "\"opsz\" 72"
  lead:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "32px"
    fontWeight: 400
    lineHeight: 1.38
  body:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "27px"
    fontWeight: 400
    lineHeight: 1.42
  takeaway:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "22px"
    fontWeight: 500
    lineHeight: 1.38
  takeaway-wide:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "24px"
    fontWeight: 500
    lineHeight: 1.38
  takeaway-panel:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "20px"
    fontWeight: 500
    lineHeight: 1.38
  label:
    fontFamily: "IBM Plex Sans, Helvetica Neue, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.3
  annotation:
    fontFamily: "IBM Plex Sans, Helvetica Neue, sans-serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.35
  source:
    fontFamily: "IBM Plex Sans, Helvetica Neue, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.35
rounded:
  box: "8px"
  term: "10px"
  card: "12px"
  pill: "22px"
spacing:
  slide-x: "88px"
  slide-top: "64px"
  slide-bottom: "72px"
  header-gap: "36px"
  column-gap: "56px"
components:
  takeaway:
    backgroundColor: "{colors.moss}"
    textColor: "{colors.paper}"
    typography: "{typography.takeaway}"
    rounded: "{rounded.box}"
    padding: "16px 26px 17px 64px"
  takeaway-light:
    backgroundColor: "{colors.paper-deep}"
    textColor: "{colors.ink}"
    rounded: "{rounded.box}"
  chapter-pill-on:
    backgroundColor: "{colors.moss}"
    textColor: "{colors.paper}"
    rounded: "{rounded.pill}"
    height: "44px"
  schema-node:
    backgroundColor: "{colors.paper-deep}"
    textColor: "{colors.ink}"
    rounded: "{rounded.box}"
---

# Design System: Aufforstung als Klima-Technologie

## Overview

**Creative North Star: "Das Feldbuch an der Wandtafel"**

Ein Vortrag, der wie ein sorgfältig geführtes Feldbuch aussieht und in einem großen Hörsaal funktionieren muss. Warmes Papier, dunkle Tinte, flache Zeichnungen in wenigen Naturfarben; jede Zahl ist eine eigene Rechnung und steht mit Quelle da. Die Gestaltung erzählt die Storyline mit: Die Systemgrenze wächst vom einzelnen Baum über das Klima zum globalen Potenzial und schließlich zu DAC, und jedes Kapitel hat genau eine Farbe, die Titel, Takeaway, Bodenlinie und Kapitelmarker trägt.

Die Folien sind auf einer festen Leinwand von 1600×900 gesetzt und werden als Ganzes skaliert; nichts scrollt, nichts bricht um. Bewegung ist Erzählung, kein Schmuck: Ein Klick bringt genau ein neues Element, Elemente der Vorfolie stehen pixelgenau an derselben Stelle und animieren nicht erneut. Das DAC-Kapitel wechselt auf dunkle Nachtfolien, damit der Bruch in der Geschichte („Ich hab die Lösung: Direct Air Capture!“) auch visuell einer ist.

**Key Characteristics:**
- Papier `paper` als Grund, Tinte `ink` als Text, eine Kapitelfarbe als einzige Akzentfläche je Folie
- Literata für Aussagen, IBM Plex Sans für alles, was beschriftet, misst oder zitiert
- Flache Schemata: Sonne, Baum aus drei Kronenkreisen, Boden als Linie mit Erdschichten
- Kanalfarben mit fester Bedeutung über Schema und Chart hinweg (CO₂ grün, Albedo orange)
- Lesbar aus der letzten Reihe; nur Quellen dürfen klein sein

## Colors

Gedeckte Naturfarben auf warmem Papier; Sättigung ist für Bedeutung reserviert.

### Primary
- **Moos** (moss): Kapitel Bäume. Titel, Takeaway-Fläche, Bodenlinie, aktiver Kapitelmarker.
- **Ton** (clay): Kapitel Klima, gleiche Rollen.
- **Fjord** (fjord): Kapitel Potenzial, gleiche Rollen.
- **DAC-Bernstein** (dac-amber): Kapitel DAC, gleiche Rollen; auf den Nachtfolien hell als `dac-amber-soft`.

Jede Kapitelfarbe hat eine `-soft`-Variante für Blatt-Icon im Takeaway, Ränder und Marker auf dunklem Grund. Im CSS laufen sie über `--ch` und `--ch-soft`, gesetzt per `data-ch` auf der Folie.

### Secondary (Kanäle und Prozesse)
- **CO₂-Grün** (co2): alles, was Kohlenstoffaufnahme meint, in Schema und Chart.
- **Albedo-Orange** (alb): Albedo-Effekt und die Linie „alle Flächen“; derselbe Wert wie `EC.alb` in den Charts.
- **Lichtstrahl** (ray): reflektiertes Sonnenlicht in den Schemata, heller als `alb`, weil es Licht ist und kein Effekt.
- **Sonne / Sonnenstrahl / Bernstein** (sun, sun-ray, amber): Sonnenscheibe, Strahlen, Akzente auf dunklen Folien.
- **Prozessfarben** (photosynthesis, respiration, decomposition, disturbance): die vier Kohlenstoffflüsse am Baum, identisch in Formel, Schema und Chart.

### Neutral
- **Papier** (paper): Folienhintergrund und Seitenhintergrund.
- **Tiefes Papier** (paper-deep): Kästen, Knoten, Panels.
- **Papierlinie** (paper-line): Rahmen und Trennlinien.
- **Tinte / Tinte 2 / Gedämpft** (ink, ink-2, muted): Text in drei Stufen; `muted` hält 5,1:1 auf Papier.
- **Nacht** (night): Grund der dunklen DAC-Folien; dort werden ink/ink-2/muted per Token umdefiniert, nicht überschrieben.

### Named Rules
**Die Eine-Kapitelfarbe-Regel.** Pro Folie trägt nur die Kapitelfarbe Fläche (Takeaway, aktiver Marker). Alle anderen Farben erscheinen als Linie, Punkt oder Beschriftung.

**Die Kanalfarben-Regel.** Eine Farbe heißt überall dasselbe. CO₂ ist grün und Albedo orange, in Formel, Schema, Chart und Takeaway. Neue Farben kommen als Token in `:root`, nie als Hex in einer Folie.

### Symbolfarben (Formeln)
Jedes Formelsymbol hat eine eigene Farbe (`--s-<rolle>`, Klasse `.c-<rolle>`). Der Farbton zeigt den Kanal, die Abstufung das Symbol:
- **CO₂ (Grün bis Türkis):** φ_CO₂ `phic`, ε_CO₂ `eps`, Δm_CO₂ `dm`, ṁ_CO₂ `mdc`, g_C `gc`; Konzentration c, c₀ in Blau (`conc`, `conco`).
- **Albedo und Energie (Orange bis Braun):** φ_α `phia`, α `alb`, α_B/α_W, Δα_Baum `dal`, Δα_Wolke `daw`, α_Wolke, Δf_Wolke, q̇_ein `qin` (Sonnengold), ΔQ̇_Albedo `dq`; Flächen A_Baum, A_Erde und τ_atm gedeckt.
- **Strahlungsantrieb gesamt:** φ in Violett (`phi`, `phio`), weil er beide Kanäle summiert.
- **Temperatur (Karmin bis Wein):** ΔT, T `dt`, R `rf`, S `sk`, f `ft`.
- **Baum:** m_Baum `mb`, die vier Prozessfarben, Wachstumsparameter in Ocker (`mmax`, `kw`, `pw`), Störung in Rost (`sz`, `gam`, `pd`).

Die Farbe hängt am KaTeX-Makro (`\phic`, `\eps`, `\dm`, `\dT` … in `deck.js`), nie an einem Hex in der Folie. Chip, Markierung und Badge eines Symbols tragen dieselbe Klasse. Auf Nachtfolien werden die Symbole automatisch aufgehellt, auf gefüllten Flächen (Takeaway, `.card.solid`) nehmen sie die Schriftfarbe der Fläche an.

**Die Ein-Symbol-eine-Farbe-Regel.** Ein Symbol hat in jeder Formel, jedem Chip, jeder Zeichnung und jedem Chart dieselbe Farbe; zwei Symbole in derselben Formel haben nie dieselbe.

**Die Eine-Markierung-Regel.** Hervorgehoben wird ein Term immer gleich: eine 12-%-Tönung seiner Farbe ohne Rand, 10px Ecken (`.hl`, `.chip`, Chart-Symbole). Kein Rahmen, keine andere Form.

## Typography

**Display Font:** Literata (mit Georgia)
**Body Font:** Literata (mit Georgia)
**Label Font:** IBM Plex Sans (mit Helvetica Neue)

**Character:** Literata gibt den Aussagen die Stimme eines gedruckten Buches, mit optischer Größe für die großen Titel. Plex Sans ist das Messinstrument: Achsen, Legenden, Schema-Beschriftungen, Tabellen, Quellen.

### Hierarchy
- **Chapter** (600, 104px, 1): nur auf Kapitelfolien, hell auf Kapitelfarbe.
- **Headline** (600, 50px, 1,08): Folientitel in Kapitelfarbe, sachlich-beschreibend, höchstens zwei Zeilen.
- **Lead** (400, 32px, 1,38): einleitende Aussage, max. 1180px breit.
- **Body** (400, 27px, 1,42): Fließtext und Listen; Minimum für Inhaltstext 20px.
- **Takeaway** (500, 1,38): der „Kurz gesagt“-Satz, höchstens zwei Zeilen. Größe nach Platz, nie je Folie: 24px über die ganze Breite, 22px in einer Spalte, 20px in einem schmalen Panel.
- **Label** (Plex 600, 18px): Kapitälchen-Überschriften in Spalten und Kästen, gesperrt.
- **Annotation** (Plex 400, 19px): Legenden, Achsenticks, Schema-Text; Untergrenze 18px.
- **Source** (Plex 400, 13px): Quellenzeile unten; die einzige Schrift, die klein sein darf.

### Rollen (Klassen)
Text im Folienkörper nimmt eine Rolle, kein eigenes `font:`. Größe per `.sm`/`.lg`, Farbe per `.c-<rolle>`:
- `.t-kicker` Plex 600 17px, normale Schreibung, ink-2 (`.lg` 21px): Überschrift über einer Gruppe. Keine Versalien, keine Sperrung.
- `.t-head` Plex 600 21px, Tinte (`.sm` 18, `.lg` 24): Überschrift eines Panels, einer Karte, einer Zeile.
- `.t-text` Plex 400 20px/1,4, Tinte 2 (`.sm` 18, `.lg` 23): Text in Panels und Listen.
- `.t-note` Plex 400 18px, gedämpft: Legende, Hinweis, Unterzeile.
- `.t-stat` Plex 600 44px, Akzentfarbe (`.sm` 32, `.lg` 52, `.xl` 92); `small` = Einheit.
- `.t-say` Literata 600 28px, Kapitelfarbe: eine Aussage im Buchton.

### Named Rules
**Die Letzte-Reihe-Regel.** Gemessen auf der 1600×900-Leinwand: Ticks, Legenden und Schema-Text ≥ 18px, Fließtext ≥ 20px, Versal-Labels ≥ 16px. Bei matplotlib-Figuren die figsize an den Folienplatz anpassen (Skalierung ≥ 0,65), nicht die Schrift aufblasen.

**Die Tabellenziffern-Regel.** Zahlen in Tabellen, Zählern und Foliennummern laufen mit `tabular-nums`.

## Layout

Feste Leinwand von 1600×900, als Ganzes auf den Viewport skaliert; die Seitenfarbe übernimmt die Farbe der aktuellen Folie, damit die Folie bis an den Bildschirmrand läuft. Innenabstand 64/88/72px (oben/seitlich/unten); die unteren 72px sind das Quellenband, Inhalt und Takeaway enden darüber. Kopfzeile mit Titel links und Kapitelmarker rechts, 36px Abstand zum Körper. Inhaltsfolien nutzen ein festes Raster: `.split` (Abbildung + Seitenspalte 470px, 40px Abstand; `.narrow` 400px, `.wide` 620px), `.split.even` (zwei Hälften) oder `.split.draw` (Zeichnung 860px + Rest); die Abbildung füllt den Rest der Höhe. Dazu `.stack` (Spalte mit Abstand), `.fill`, `.center`, `.cols`/`.cols3` für linierte Textspalten. Quellenzeile absolut unten (14px Abstand) ab x=150, höchstens zwei Zeilen, Foliennummer bei x=88.

Auf Handys im Hochformat bleibt die Leinwand erhalten; ein Hinweis bittet ums Drehen. Die Übersicht (M) ist ein Raster aus Miniaturen, auf schmalen Bildschirmen mit kleineren Kacheln.

### Named Rules
**Die Selber-Ort-Regel.** Was auf der Vorfolie schon stand, steht auf der nächsten pixelgenau an derselben Stelle und animiert nicht erneut.

**Die Ein-Klick-ein-Element-Regel.** `data-step` bringt je Klick genau ein neues Element. Panels, die per Klick über eine Karte fahren, dürfen sie samt Legende überdecken; vorher war alles sichtbar.

## Elevation & Depth

Weitgehend flach. Tiefe entsteht über Tonstufen (paper → paper-deep) und dünne Papierlinien. Schatten gibt es nur an Elementen, die über etwas liegen: das Takeaway (ein weicher Schatten nach unten) und Seitenpanels, die über eine Karte fahren.

### Shadow Vocabulary
- **Takeaway-Auflage** (`box-shadow: 0 10px 24px -16px rgba(30, 26, 18, .55)`): hebt den Kurz-gesagt-Kasten leicht ab.

### Named Rules
**Die Flach-wie-Papier-Regel.** Kästen liegen flach auf dem Papier. Ein Schatten bedeutet „liegt über etwas anderem“ und nichts sonst.

## Shapes

Sanft gerundete Kästen (8px), volle Pillen (22px Radius) für Kapitelmarker und Ergebnis-Pillen, Kreise für nummerierte Badges. Rahmen sind ringsum gleich dünn (1,5px Papierlinie oder Kanalfarbe); keine dicken Seitenstreifen. Zeichnungen sind geometrisch: Kreise für Kronen, Rechtecke für Stämme, Linien mit Pfeilspitzen für Flüsse.

## Components

### Kurz gesagt (Takeaway)
- **Form:** Kasten mit 8px Radius in der Kapitelfarbe, helle Schrift, Blatt-Icon links in `--ch-soft`.
- **Inhalt:** höchstens zwei Zeilen, gern Stichpunkte statt ganzer Sätze; die lange Fassung steht als „Ausführlich: …“ in den Notizen.
- **Varianten:** `light` (tiefes Papier mit Rand in `--ch-soft`) für ruhige Folien; `wide` einzeilig über die volle Breite, linksbündig wie alle anderen.
- **Keine Inline-Größen:** Schriftgröße, Innenabstand und Zeilenhöhe kommen nur aus dem CSS.

### Kapitelmarker
- **Form:** je Kapitel eine Scheibe (44px) mit Lucide-Icon in der Kapitelfarbe; das aktuelle Kapitel als gefüllte Pille mit Namen.
- **Ort:** oben rechts auf Inhaltsfolien, oben links auf Kapitelfolien (invertiert auf Kapitelfarbe).

### Formelzeile, Chip und Markierung
- **Formelzeile** (`.fline`, unter dem Titel `.fline.head`): Chip, dann Formel oder Worte; `.part` gruppiert, `.part.next` liegt darüber und übernimmt per Klick.
- **Chip** (`.chip.c-<rolle>`): Name und Symbol einer Größe in der Tönung ihrer Farbe, ohne Rand.
- **Markierung** (`\hl{rolle on}{…}` in KaTeX, `.hl` in HTML): dieselbe Tönung hinter dem Term, nimmt keinen Platz ein; leuchtet mit `.on` oder dem Auslöser der Folie.
- **Legende** (`.legend`, `.sm`/`.lg`/`.two`): Symbol rechtsbündig, Bedeutung in Plex.
- **Schritte** (`.nstep` mit `.badge.c-<rolle>`): nummerierte Erklärung neben einer Zeichnung.

### Karte
- `.card` (tiefes Papier, 12px Ecken, 18/22px Innenabstand), `.card.solid` gefüllt in ihrer Farbe mit heller Schrift, `.card.line` nur Umriss. Die Folie setzt nur Größe und Ort.

### Schema-Knoten und Badges
- **Knoten:** tiefes Papier, Rand in Papierlinie oder Kanalfarbe, Titel Plex 600 19px, Unterzeile 15px gedämpft.
- **Badges:** nummerierte Kreise in Fluss- oder Kapitelfarbe, Ziffer hell.
- **Ergebnis-Pille:** warmer Pfirsichton, fette Zahl.

### Seitenpanel
- **Form:** 470px breit, voller Körperhöhe, über der Abbildung rechts; erscheint per Klick und darf die Abbildung überdecken.

### Charts
- **Quelle:** die eigenen matplotlib-Figuren, als ECharts nachgezeichnet; Beschriftungen und Achsen in Plex, wie alle anderen Diagramme.
- **Bildsprache:** Balken = was ein Baum in einem Jahr austauscht; Linien = erst mit Systemantwort. Orte in einem gemeinsamen Diagramm.
- **Bewegung:** Einlauf beim Erscheinen; bei reduzierter Bewegung sofort im Endzustand.

### Bedienelemente (öffentliche Fassung)
- **Übersicht (M):** modaler Dialog mit Miniaturen, Pfeiltasten wählen, Enter springt, Fokus bleibt im Dialog und kehrt beim Schließen zurück.
- **Hinweiszeile:** Tastenkürzel oben mittig, verblasst nach 5 s.
- **Referentenansicht (P):** dunkel, damit das Pult nicht leuchtet; aktuelle und nächste Folie, Notizen, Uhr.

## Do's and Don'ts

### Do:
- **Do** neue Farben als Token in `:root` anlegen und in SVG als `fill="var(--name)"` nutzen.
- **Do** Folientitel sachlich und beschreibend halten.
- **Do** jede Zahl mit Quelle in der Quellenzeile belegen.
- **Do** Schemata im flachen DAC-Stil zeichnen: Plex-Textblöcke, Kapitälchen-Labels (16px gesperrt), nummerierte Badges.
- **Do** `prefers-reduced-motion` mit dem Endzustand bedienen, nicht mit Abschalten.
- **Do** Folien aus dem festen Vokabular bauen (Kopf von `deck.css`): Rolle + Größe + Farbrolle, z. B. `class="t-stat lg c-moss"`.
- **Do** Symbole über ihr Makro schreiben (`\phic(t)`), Markierungen über `\hl{…}`.

### Don't:
- **Don't** Hex-Werte direkt in Folien-SVGs schreiben, wenn ein Token existiert.
- **Don't** `font:` oder Farbe inline oder in einer folienspezifischen Klasse setzen, wenn eine Rolle das schon tut.
- **Don't** Formelterme mit Rahmen hervorheben; Markierung ist immer die randlose Tönung.
- **Don't** ein Element, das auf der Vorfolie stand, erneut einblenden oder verschieben.
- **Don't** Inhaltstext unter 20px oder Chart-Beschriftungen unter 18px setzen.
- **Don't** Slogans oder Antithesen als Titel oder Takeaway formulieren.
- **Don't** dicke farbige Seitenstreifen an Kästen; Rahmen gehen ringsum.
- **Don't** kursive Literata-Beschriftungen an Zeichnungen; Beschriftung ist Plex.
