# Abgleich gegen Hasler et al. (2024)

**Quelle.** Hasler, N., Williams, C. A., Carrasco Denney, V., Ellis, P. W.,
Shrestha, S., Terasaki Hart, D. E., Wolff, N. H., Yeo, S., Crowther, T. W.,
Werden, L. K., Cook-Patton, S. C. (2024): *Accounting for albedo change to
identify climate-positive tree cover restoration.* Nature Communications 15,
2275. doi:10.1038/s41467-024-46577-1.

Das ist die direkteste externe Prüfmöglichkeit für dieses Modell: dieselbe
Frage (Albedo gegen Kohlenstoff bei Aufforstung), dieselbe Datenfamilie,
global aufgelöst, und mit einer eigenen Auswertung genau der Bastin-Fläche,
auf der die Kaskade dieses Vortrags aufsetzt.

## 1. Methodisch identisch

Fünf Bausteine stimmen bis auf die Schreibweise überein. Das ist kein
Zufall — es sind beides Standardwege — aber es heißt, dass die Zahlen
vergleichbar sind und ein Unterschied etwas bedeutet.

| Baustein | Hasler et al. | dieses Modell |
|---|---|---|
| Albedo → globaler Antrieb | `RF_α · A_Zelle / A_Erde` (Gl. 3) | `φ_α = −Δα·q̇·τ·f·A_Baum/A_Erde` (`nbs.forcing`) |
| CO₂-Strahlungsantrieb | `5,35 · ln(C/C₀)` (Gl. 4, Myhre 1998) | `A_CO2_LOG_W_M2_PER_PPM = 5.35` (`nbs.constants`) |
| Masse je ppm | 2,13 PgC/ppm | `KG_CO2_PER_PPM = 7,82e12` kg CO₂/ppm = 2,133 GtC/ppm |
| Verbleib in der Atmosphäre | Impulsantwort, Joos-Mehrmodellmittel | `green_carbon` (FaIR) bzw. `green_carbon_preindustrial` (Joos 2013) |
| Wachstumsform | Chapman-Richards-S-Kurve (Zeitszenarien, Fig. S7) | `biomass_closed` (`nbs.tree`) |

Auch die Albedo-Rohdaten stammen aus derselben Familie: Hasler nutzt den
Gao-Albedo-Atlas mit MODIS-Schneebedeckung, dieses Modell die
Duveiller-Übergangsraster — Duveiller et al. 2018 ist in Hasler Referenz 5.

**τ_atm = 0,8 ist damit erstmals extern eingeordnet.** Hasler ersetzt diesen
Faktor durch sechs räumlich und monatlich aufgelöste Strahlungskerne
(CAM3, CAM5, ECHAM6, HadGEM2, HadGEM3, CACKv1.0) und rechnet
`RF_α = K_α · Δα`. Der Kern leistet genau das, was τ hier pauschal leistet:
die Umrechnung einer Oberflächen-Albedoänderung in einen Antrieb an der
Atmosphärenobergrenze. Ein Pauschalwert um 0,8 liegt in der üblichen
Spanne solcher Kerne; die Streuung zwischen den sechs Kernen beziffert
Hasler auf ±15 % des Medians (mehr in hohen Breiten). **τ = 0,8 ist also
eine vertretbare Näherung mit einer bekannten Unsicherheit von rund
±15 %, keine freie Setzung mehr.**

## 2. Ergebnisse: die Größenordnung stimmt

Hasler rechnet für die Bastin-Fläche eine vergleichbare Teilmenge aus:
916 Mha mit unter 25 % Baumbedeckung, die über 25 % tragen könnten. Die
bepflanzbare Fläche dieses Modells (`nbs.landscape.plantable_area_m2`)
beträgt **948,8 Mha** — 3,6 % mehr, bei zwei unabhängigen Verfahren.

Der zentrale vergleichbare Wert ist der **Albedo-Offset**: der Anteil der
Kohlenstoff-Kühlung, den die Albedo-Erwärmung auffrisst. Gemessen am
Horizontende 2150, je Zelle, über die bepflanzbare Fläche dieses Modells:

| Größe | Hasler et al. | dieses Modell |
|---|---|---|
| Median-Offset | 52 % (global) | **39 %** (flächengewichtet), 58 % ungewichtet |
| Fläche mit über 50 % Offset | 48 % (Bastin-Fläche) | **39 %** |
| netto klimanegativ (über 100 %) | 29 % (Bastin-Fläche) | **1,8 %** |
| Tropen: Fläche mit über 50 % Offset | 6 % | **8,6 %** |
| Boreal: Fläche mit über 50 % Offset | 72 % | **96 %** |

Die Tropen stimmen fast exakt. Boreal fällt dieses Modell strenger aus,
die Gesamtfläche milder. Beides hat denselben, benennbaren Grund — siehe 3
und 4.

**Die Einordnung zwischen den Potenzialkarten passt.** Hasler prüft drei:
Griscom (828 Mha, schließt boreale Ökoregionen *und* Grasbiome aus): 18 %
mit erheblichem Offset. Bastin (916 Mha, schließt nichts aus): 48 %.
Walker (889 Mha, Schwerpunkt Tundra/Savanne/boreal): 65 %. Dieses Modell
schließt Grasland und Savanne aus, behält aber die Boreale — und landet
mit 39 % genau zwischen Griscom und Bastin. Das ist die Position, die es
strukturell einnehmen muss.

## 3. Die Kaskade unterschätzt den Albedo-Abzug — konstruktionsbedingt

Die Albedo-Stufe der Kaskade (`nbs.potential.cascade`, Stufe 4) nimmt
81 → 79,5 GtC weg, also **1,8 %**. Hasler halbiert die Bastin-Fläche:
214 → 101 Pg CO₂e, also **53 %**.

Das ist kein Widerspruch, sondern eine andere Frage:

* Die Kaskade **filtert**: sie entfernt Zellen, die bis 2150 *nie* einen
  Ausgleich erreichen (t\* = ∞). Das sind 1,8 % der Fläche.
* Hasler **rabattiert**: jede Zelle verliert den Anteil ihres
  Kohlenstoffnutzens, den die Albedo auffrisst — auch dort, wo am Ende
  noch ein Nutzen übrig bleibt.

Eine Zelle mit 60 % Offset ist in der Kaskade voll drin und bei Hasler zu
60 % weg. Beide Aussagen sind richtig, sie messen Verschiedenes: die
Kaskade misst, **ob** Aufforstung irgendwann kühlt, Hasler misst,
**wie viel** vom Nutzen übrig bleibt.

**Konsequenz für den Vortrag:** die 78,2 GtC der Kaskade sind kein
albedo-bereinigter Kohlenstoffwert. Nach Haslers Rechenweise wären es auf
derselben Fläche rund 60 % davon. Der Vortrag darf 78,2 GtC nicht als
„nach Albedo" verkaufen — er nennt sie als das, was sie ist: die Fläche,
die den Vorzeichentest besteht, bewertet mit der Literatur-Kohlenstoffdichte.

## 4. Zwei Annahmen, die der Abgleich als zu hoch ausweist

**Kohlenstoffdichte.** Die Sättigungsdichten dieses Modells (`m_max_kgC` je
`stand_area_m2`) liegen bei 100–200 tC/ha:

| Art | m_max [kgC] | Standfläche [m²] | Bäume/ha | tC/ha bei Sättigung |
|---|---|---|---|---|
| Gemeine Fichte | 50 | 5,0 | 2000 | 100 |
| Waldkiefer | 60 | 5,0 | 2000 | 120 |
| Rotbuche | 75 | 6,0 | 1667 | 125 |
| Rosen-Eukalyptus | 50 | 4,0 | 2500 | 125 |
| Tropischer Mischbestand | 100 | 5,0 | 2000 | 200 |

Der bis 2150 tatsächlich erreichte Bestand über die ganze bepflanzbare
Fläche sind **114 tC/ha**. Hasler rechnet auf der Bastin-Fläche mit
58 GtC auf 916 Mha, also **63,3 tC/ha** (ober- und unterirdische Biomasse,
Boden bewusst nicht) aus der Walker-Karte. **Dieses Modell liegt rund 80 %
darüber.** Für die boreale Fichte sind 100 tC/ha am oberen Rand dessen,
was borealer Wald an Biomasse trägt.

Die Parameter sind in `nbs.species` bereits als *Setzung* ausgewiesen
(Backup-Folie 41). Hasler liefert jetzt eine externe Zahl, gegen die sie
zu prüfen sind.

**Albedo-Strafe je Hektar.** Nach Haslers eigener Umrechnung (Gl. 4–7,
Rest­anteil nach 100 Jahren) ergeben die Δα·q̇-Produkte dieses Modells auf
der bepflanzbaren Fläche einen Median von rund **−255 Mg CO₂e/ha**;
Hasler nennt global **−120 Mg CO₂e/ha** (90 %-Bereich 28 bis −469).
Der Wert dieses Modells liegt **innerhalb** von Haslers Spanne, aber
oberhalb seines Medians — teils, weil die bepflanzbare Fläche hier
boreal-lastig ist (51 % der Zellen), teils aus derselben Richtung wie die
Kohlenstoffdichte.

**Dass beide Größen etwa doppelt so hoch liegen, ist der Grund, warum das
Verhältnis — der Offset — trotzdem passt.** Zähler und Nenner sind
gemeinsam zu groß. Für den Offset und damit für t\* ist das
weitgehend folgenlos; für jede absolute GtC-Angabe ist es das nicht.

## 5. Der Befund, der der Erzählung widerspricht

Hasler: *„Contrary to previous work that suggests the greatest albedo
concerns are in the boreal, we find that drylands have a greater proportion
of net climate-negative areas."* Konkret: temperiertes Grasland, Savanne
und Buschland sind zu **72 %** netto klimanegativ und zu 83 % erheblich
offset-belastet; die Boreale nur zu **34 %** netto klimanegativ (aber 72 %
erheblich offset-belastet).

Der Vortrag erzählt die Albedo-Falle als boreale Geschichte. Das ist nach
Hasler unvollständig.

**Dieses Modell kann den Befund nicht reproduzieren.** Auf den von der
Kaskade ausgeschlossenen Savannen-/Grasland-/Wüstenzellen (4,55 Gha)
kommt es auf einen Median-Offset von 26 %, mit 0,7 % netto klimanegativ —
weit entfernt von Haslers 72 %. Zwei Gründe, beide benennbar:

1. **Kein Trockenheitssignal im Kohlenstoff.** Haslers Mechanismus ist,
   dass die größten Offsets dort auftreten, wo die Kohlenstoffdichte am
   *niedrigsten* ist. Dieses Modell gibt einer Trockengebietszelle
   dieselben Artparameter wie einer feuchten Zelle im selben Breitenband —
   der Nenner des Offsets bricht nicht ein. Das ist die Hauptursache.
2. **Kein Bodenhelligkeitssignal im Δα.** Die Drei-Stufen-Füllung setzt in
   einer Trockengebietszelle den zonalen Median desselben Übergangs ein,
   nicht einen trockengebietsspezifischen Wert. Helle, trockene Böden mit
   entsprechend großem Δα sieht sie nicht.

**Konsequenz für den Vortrag:** der Ausschluss von Savanne und Grasland
aus der bepflanzbaren Fläche war bisher mit der Bastin-Kritik begründet
(Landnutzungsumwandlung statt Wiederherstellung, Biodiversität). Er ist
zusätzlich eine **Modellgrenze**: dieses Modell dürfte auf diesen Flächen
gar nicht rechnen, weil es dort weder Kohlenstoff noch Albedo richtig
abbildet. Beides gehört auf die Folie — die zweite Begründung ist die
ehrlichere.

## 6. Wo dieses Modell etwas kann, was Hasler nicht kann

Hasler rechnet mit **maximum CO₂e**: dem Endzustand, wenn Kohlenstoff und
Albedo beide gesättigt sind. Die Arbeit sagt das selbst und nennt es als
offene Lücke:

> *„we compared maximum potential carbon storage with maximum albedo
> change, which ignores the time frame over which both unfold … in other
> areas, particularly where the albedo offset is intermediate, it is
> possible for the net climate impact to range from positive to negative
> depending on the time horizon … additional work is urgently needed to
> determine the net climate impact over the coming decades."*

Genau das rechnet dieses Modell: t\*(Zelle), das Horizontfeld, die Leiter,
die Pflanzjahr-Kohorten. Die zwölf hypothetischen Zeitszenarien in Haslers
Fig. S7 sind der Platzhalter für das, was hier explizit gerechnet wird.

Zweitens: **Störungen.** Hasler schließt sie ausdrücklich aus
(*„Additional consideration of the durability of tree cover is also
warranted … While we did not account for these factors"*). Der
Störungspuffer und die Pflanzjahr-Folie dieses Vortrags liegen in genau
dieser Lücke.

Drittens, gegen dieses Modell: Hasler weist darauf hin, dass der
Rückgang der Schneebedeckung die boreale Albedo-Strafe über die Zeit
*verkleinert*, während sie in Trockengebieten bleibt oder wächst. Das
Δα·q̇-Produkt dieses Modells ist **statisch** — es kennt keine abnehmende
Schneedecke. Die boreale Strafe der späten Jahrzehnte ist hier daher eher
zu hoch angesetzt; t\* für boreale Zellen ist tendenziell zu spät.

## 7. Was daraus folgt

Belegt: der Rechenweg (Abschnitt 1), die Größenordnung des Offsets, die
Einordnung der Fläche zwischen Griscom und Bastin, τ_atm ≈ 0,8 mit ±15 %.

Zu korrigieren im Vortrag:

1. 78,2 GtC nicht als albedo-bereinigten Wert darstellen (Abschnitt 3).
2. Den Savannen-/Graslandausschluss auch als Modellgrenze begründen,
   nicht nur als Bastin-Kritik (Abschnitt 5).
3. Die boreale Erzählung um Haslers Trockengebietsbefund ergänzen.
4. Das statische Δα als Annahme ausweisen (Abschnitt 6).

Offen und der Prüfung wert: die Kohlenstoffdichten (Abschnitt 4), die
80 % über dem externen Wert liegen.
