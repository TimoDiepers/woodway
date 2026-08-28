# Bild-Prompts für „Retten Bäume das Klima?"

Prompts zum selbst Generieren (Nano Banana Pro, Midjourney, DALL·E, Imagen …).
Ergebnis-Diagramme (Wachstumskurven, Strahlungsantrieb, Äquivalenzverhältnis) kommen
weiterhin aus `generate_figures.py` — hier stehen nur die **bildhaften** Folienelemente.

---

## 0. Wie du damit arbeitest

1. **Einen Stil wählen** (Abschnitt 1) und für *alle* Bilder durchziehen. Ein gemischter
   Stil zerstört den Eindruck einer Serie schneller als ein mittelmäßiges Einzelbild.
2. Prompt kopieren, **Stil-Suffix anhängen**, generieren, 3–4 Varianten ziehen.
3. Dateiname aus der Kopfzeile verwenden und nach `docs/slides/figures/` legen —
   `generate.js` bindet sie dann unter genau diesem Namen ein.
4. **Keine Schrift ins Bild generieren lassen.** Bildmodelle setzen Text unzuverlässig,
   deutsche Umlaute fast nie. Beschriftungen kommen als PowerPoint-Textfelder darüber.

**Seitenverhältnisse:** Vollbild-Folie `16:9` · Halbe Folie / Spaltenbild `4:3` oder `1:1`
· Vollbild-Stimmungsbild `16:9`.

---

## 1. Stil — eine Variante wählen

### Variante A — Editorial-Fotografie (Empfehlung)
Ruhig, glaubwürdig, passt zu einem Fachvortrag; die Diagramme bleiben die lauteste
Bildsprache der Präsentation.

> **Stil-Suffix A:**
> `editorial science photography, natural diffused daylight, muted desaturated palette of
> deep forest green, warm sand and slate grey, shallow depth of field, medium format look,
> fine grain, no text, no watermark, no people looking at camera`

### Variante B — Papercut-Isometrie
Illustrativ, gut wenn du für ein breiteres Publikum ohne Vorwissen etwas Verspieltes willst.
Skaliert schön über die Systemgrenzen-Reise (jede Ebene ein Diorama).

> **Stil-Suffix B:**
> `layered paper-cut diorama, isometric view, matte cardboard textures, deep forest green,
> cream and ochre palette, soft studio light, subtle drop shadows, clean neutral background,
> no text, no watermark`

**Negativ-Prompt (immer anhängen):**
`text, letters, numbers, labels, captions, watermark, logo, oversaturated colors, HDR,
neon, lens flare, distorted anatomy, extra limbs, cartoonish faces, stock-photo smiling people`

---

## 2. Wo Bilder in den Vortrag passen

Die Systemgrenzen-Zeichnungen (`kv_1`–`kv_6`) und die Gleichungen (`gl_1`–`gl_6`) erzeugt
`generate_diagrams.py` — die sind gesetzt und brauchen keine Bildgenerierung. Die Prompts hier
sind **optionale Stimmungsbilder**: Sie ersetzen keine Aussage, sie geben den sechs
Systemgrenzen ein Gesicht. Aktuell bindet `generate.js` keines davon ein; sobald eine Datei
unter dem angegebenen Namen in `figures/` liegt, kann sie auf der genannten Folie ergänzt
werden.

| Datei | passt zu | Rolle |
|---|---|---|
| `bild_20_blatt_makro.png` | Folie 4 — Systemgrenze Blatt | Maßstab: worüber reden wir |
| `bild_30_holz.png` | Folie 8 — Systemgrenze Baum | wo der Kohlenstoff landet |
| `bild_31_wurzeln.png` | Folie 10 — Speicher | die unsichtbare Hälfte |
| `bild_40_bestand.png` | Folie 12 — Systemgrenze Bestand | Fläche statt Objekt |
| `bild_50_grenzschicht.png` | Folie 16 — Systemgrenze Atmosphäre | die Luftsäule darüber |
| `bild_51_erde.png` | Folie 21 — Systemgrenze Erde | Maßstabssprung |
| `bild_60_wachstum.png` | Folie 24 — Wachstum | Zeit wird sichtbar |
| `bild_70_pflanzung.png` | Folie 30 — Antwort | Schlussbild |

---

## 3. Systemgrenze Blatt

### `bild_20_blatt_makro.png` — Blatt als Energiewandler
**Format:** 1:1 oder 4:3
> Macro photograph of a single leaf surface at dawn, tiny water droplets condensing on the
> waxy cuticle, sunlight refracting through the droplets, visible leaf venation, extremely
> shallow depth of field, dew evaporating as faint mist above the surface

### `bild_21_stoma.png` — Spaltöffnung (optional)
**Format:** 1:1
> Stylised scientific illustration of a plant stoma on a leaf epidermis, two guard cells
> forming an open pore, cross-section view, muted green and cream palette, clean background,
> textbook illustration style without any labels

---

## 4. Systemgrenze Baum

### `bild_30_holz.png` — Wo der Kohlenstoff landet
**Format:** 4:3
> Close-up of a freshly cut tree trunk cross-section showing dense annual growth rings,
> pale sapwood and darker heartwood, sawdust on the surface, natural daylight, top-down view

### `bild_31_wurzeln.png` — Die unsichtbare Hälfte
**Format:** 16:9
> Cross-section view of forest soil in an excavated pit, tree roots and fine root hairs
> spreading through dark humus layers, mycelium threads visible, earthy brown and ochre
> tones, scientific field documentation look

---

## 5. Systemgrenze Bestand

### `bild_40_bestand.png` — Fläche statt Einzelbaum
**Format:** 16:9
> Drone view straight down over a dense mixed forest canopy, individual tree crowns visible
> as a mosaic of green textures, thin morning mist between the crowns, soft even light

### `bild_41_stoerung.png` — Störung (optional, zu Q₁₀ und Störungsraten)
**Format:** 4:3
> Aerial view of a forest section with clearly visible bark beetle damage, patches of dead
> rust-coloured spruce standing among healthy green trees, overcast diffuse light,
> documentary tone, no people

---

## 6. Systemgrenze Atmosphäre & Erde

### `bild_50_grenzschicht.png` — Die Luftsäule über dem Wald (Folie 10)
**Format:** 4:3
> Landscape photograph from a hillside looking across a forested valley at sunrise, a
> distinct layer of mist and water vapour hovering directly above the canopy, cumulus clouds
> forming above it, cool blue shadows and warm light on the horizon

### `bild_51_erde.png` — Systemgrenze Erde (Folie 15)
**Format:** 16:9
> Full disc of Earth seen from deep space, Atlantic and African continents visible, swirling
> cloud systems, thin atmosphere rim lit by the sun, deep black background, realistic
> satellite imagery look

---

## 7. Zeit

### `bild_60_wachstum.png` — Dieselbe Fläche, vier Zeitpunkte (Folie 17)
**Zweck:** Kernbild für die instationäre Bilanz — die Fläche ist gepflanzt, aber sie *ist*
noch kein Wald.
**Format:** 16:9

> Four-panel sequence of the exact same landscape viewpoint showing forest growth stages
> side by side: bare planted field with seedlings, young saplings, mid-height dense young
> forest, mature tall forest, identical camera angle and framing in every panel, consistent
> overcast light, documentary time-lapse style

**Tipp:** Vier Panels bekommen Modelle selten konsistent hin. Alternative: vier Einzelbilder
mit identischem Prompt plus `seedlings` / `young saplings` / `dense young forest` /
`mature forest` generieren und in PowerPoint nebeneinanderlegen.

### `bild_61_uhr.png` — Warmzeit vor der Gutschrift (optional)
**Format:** 1:1
> Young tree sapling planted in open ground, long shadow cast by low sun, dry cracked soil
> around it, wide empty sky, sense of waiting and passing time

---

## 8. Abschluss

### `bild_70_pflanzung.png` — Antwort auf die Titelfrage (Folie 24–26)
**Format:** 16:9
> Hands of a forestry worker in worn gloves placing a small tree seedling into prepared soil,
> close-up, blurred reforestation site with rows of young plantings in the background,
> soft overcast light, hopeful but sober mood

---

## 9. Was **nicht** generiert wird

| Element | Warum | Woher stattdessen |
|---|---|---|
| Kontrollvolumen `kv_1`–`kv_6` | Pfeile, Symbole und Zahlen müssen exakt zur Gleichung passen | `generate_diagrams.py` |
| Gleichungen `gl_1`–`gl_6` | Formelsatz und farbliche Hervorhebung neuer Terme | `generate_diagrams.py` |
| Systemgrenzen-Leiste (6 Kästen) | wiederholt sich identisch, exakte Beschriftung | `generate.js` (HTML) |
| Alle Ergebniskurven | Modellergebnisse, keine Illustrationen | `generate_figures.py` |
