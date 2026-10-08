# Abgleich gegen Hasler et al. (2024) nach Umstellung auf Waldtypen (2026-10-05)

Hasler, N. et al. (2024): Accounting for albedo change to identify
climate-positive tree cover restoration. Nat. Commun. 15, 2275.
Methoden geprüft im Volltext (PMC10965905).

## Ausgangsbefund

Nach der Umstellung auf Datengrundlagen (Walker-Fläche und -Kohlenstoff,
Hasler-Waldtyp, Cook-Patton-Tempo; `nbs.forest_data`) kühlt bis 2150 unter
SSP2-4.5 nur 0,28 der 0,83 Gha wiederbewaldbarer Fläche. Median-Offset 146 %,
Hasler global 52 %. Vorher (fünf gesetzte Arten) lag das Modell bei 39 %.

## Was Hasler rechnet (Methoden, wörtlich geprüft)

* Albedo: voller Übergang Offenland → Waldklasse, **keine** Skalierung mit
  dem Bedeckungszuwachs (wie hier).
* Antrieb über Strahlungskerne; CO₂e mit 5,35·ln, **400 ppm** Bezug, geteilt
  durch den mittleren Restanteil eines CO₂-Pulses über **100 Jahre**.
* Kohlenstoff: maximale ober- + unterirdische Biomasse, **ohne Boden** (wie
  hier). Ergebnis „maximum CO₂e“, ausdrücklich ohne Zeitverlauf.

## Zerlegung

| Schritt | Median-Offset | > 50 % Offset | > 100 % |
|---|---|---|---|
| Hasler, global (Bastin-Fläche) | 52 % | 48 % | 29 % |
| Hasler, **Walker-Fläche** (889 Mha) | – | **65 %** | – |
| Haslers statische Formel, unsere Δα·q̇ und Walker-Kohlenstoff, 828 Mha | **92 %** | **73 %** | 47 % |
| unser Modell, ΔT 2150, SSP2-4.5 | 146 % | 84 % | 66 % |

1. **Fläche.** Unsere Fläche ist jetzt Walkers Wiederbewaldungsfläche —
   genau die Karte, für die Hasler selbst 65 % mit erheblichem Offset
   findet (boreal- und trockengebietslastig). Der Vergleichswert ist also
   nicht 52 %, sondern 65 %.
2. **Statisch stimmen wir mit Hasler überein.** Mit Haslers eigener Formel
   auf unseren Zellen: 73 % statt 65 %. Albedo-CO₂e im Median 146 t/ha
   (Hasler global 120 t/ha); die Differenz liegt im Rahmen von τ = 0,8
   gegenüber Kernen (±15 %) und Gao- gegenüber Duveiller-Albedo.
3. **Der Rest ist der Zeitverlauf, nicht die Impulsantwort.** Den Rückfluss
   von CO₂ aus Ozean und Land haben beide Rechnungen: Hasler teilt das
   Albedo-CO₂e durch den mittleren Restanteil eines Pulses über 100 Jahre
   (Joos-Impulsantwort), Gl. 5–7. Der Unterschied liegt woanders. Hasler
   vergleicht Endzustände: maximalen Kohlenstoff mit maximaler Albedo, bei
   festen 400 ppm. Wir rechnen die Erwärmung im Jahr 2150 unter SSP2-4.5.
   Dann ist der Baum gesättigt, der größte Teil seiner Entnahme liegt
   Jahrzehnte zurück, und bei rund 600 ppm wirkt jedes kg schwächer. Die
   Albedo wirkt dagegen ab Kronenschluss voll. Störung ändert wenig (150 %
   ohne, 146 % mit). Hasler nennt den Zeitverlauf selbst als offene Lücke.
   Arnold (Masterarbeit, GWP100 bzw. dynamische Ökobilanz) hat die Albedo
   gar nicht, nur als Grenze genannt.
4. **Der alte Gleichstand war Zufall.** Die gesetzten Arten trugen 114 tC/ha
   (Hasler 63) und eine etwa doppelt so hohe Albedo-Strafe; Zähler und
   Nenner waren gemeinsam zu groß (Abgleich 2026-09-10, Abschnitt 4).

> Nachtrag 2026-10-05: Die Zahlen oben stammen aus dem Lauf vor der
> Anpassung an Williams et al. 2026 (Albedo-Tempo) und Grünig et al. 2026
> (Störung). Aktuelle Werte: `fakten.json`, Abschnitt `literatur`.

## Bekannte Richtung der Fehler

* Statisches Δα·q̇: keine abnehmende Schneedecke. Boreal eher zu hohe
  Albedo-Strafe in späten Jahrzehnten (Hasler, Diskussion).
* Tempo am Deckel: In 73 % der Zellen liegt Cook-Patton × 30 Jahre über
  Poorters 55 % des Walker-Potenzials; dort gilt der Deckel. Das Tempo
  unterscheidet die Waldtypen daher kaum.

## Zerlegung je Studie (2026-10-05, nach Williams-Tempo und Grünig-γ)

Gemeinsame Größe: Anteil des reinen Kohlenstoffnutzens, der nach der Albedo
bleibt. Ganze wiederbewaldbare Fläche (0,83 Gha), SSP2-4.5.

**Schritt für Schritt** (Komponenten einzeln dazugeschaltet):

| Rechenweise | bleibt 2100 | bleibt 2150 |
|---|---|---|
| Haslers statische Formel (400 ppm, Restanteil über 100 Jahre) | 20 % | 20 % |
| A: Zeitverlauf, Wirkung je kg konstant, Rückfluss Joos | 32 % | 11 % |
| B: + Wirkung je kg sinkt mit steigendem CO₂ | 9 % | −18 % |
| C: + Senken im Szenario (FaIR) | −4 % | −25 % |
| D: + Störung (volles Modell) | 17 % | 5 % |

**Gegenprobe gegen FaIR direkt:** Die gesamte Entnahme (148 Gt CO₂ bis
2150) und die Albedo als Zeitreihe in einen vollen FaIR-Lauf gegeben:
reiner Kohlenstoff −0,0486 K (unsere Faltung −0,0476 K) in 2100; bleibt
18 % (unsere 17 %) in 2100 und 4 % (5 %) in 2150. Die Faltung mit der
2025er Impulsantwort ist also keine Quelle der Strenge.

**Woher die Abweichung je Studie kommt:**

* **Hasler 2024 (47 %, Bastin-Fläche, statisch):** vor allem die Fläche.
  Auf der Walker-Fläche rechnet Hasler selbst mit mehr Offset (65 % der
  Fläche über 50 %; wir mit seiner Formel 73 %). Mit seiner Formel bleiben
  hier 20 %. Der Rest ist der Horizont: bis 2100 ähnlich (17 %), bis 2150
  weniger (5 %), weil der Rückfluss weiterläuft und die Albedo nicht.
* **Fahrenbach 2026 (59 %, CESM2, Bastin, 2100):** vor allem die
  Kohlenstoffmenge. CESM2 lässt auf 926 Mha bis 2100 350 Gt CO₂ wachsen
  (≈ 100 t C/ha, Vegetation und Totholz), Walker misst 51 t C/ha
  zusätzlich. Mit 2,4-mal so viel Kohlenstoff blieben bei uns rechnerisch
  1 − 0,83/2,4 ≈ 65 %. Dazu kühlt bei Fahrenbach die Verdunstung in den
  Tropen mit, die hier fehlt.
* **Liang 2025 (30 %, Feuer + Albedo, 2100, SSP1-2.6):** nahe bei uns
  (17 % bis 2100), obwohl mit niedrigerem CO₂-Hintergrund gerechnet;
  Liang zieht zusätzlich Feuerverluste ab.
* **Rohatyn 2022 (30 %, Trockengebiete):** andere Fläche; unser Modell
  bildet Trockengebiete nicht gut ab (Abschnitt 5 des Abgleichs 2026-09-10).
* **Riley 2025 (82 %):** bestehende Projekte, die überwiegend dort liegen,
  wo Albedo wenig kostet (Auswahl, nicht Potenzial).
* **Weber 2024 (≥ 67 %):** Erdsystemmodell, Albedo und Luftchemie, andere
  Fläche und 4-°C-Welt.

**Was unser Ergebnis stützt:** Kohlenstoff aus Messdaten hochgerechnet
(Walker), Albedo gemessen (Duveiller), Tempo der Albedo gemessen
(Williams), Klimakette identisch mit vollem FaIR. **Wo wir eher zu streng
sind:** keine Verdunstungskühlung (Tropen), statische Schneedecke
(boreal). **Wo eine Annahme viel trägt:** Schritt D. Eine Störung lichtet
den Wald, und der Kronenschluss folgt dem Vorrat überproportional
(β ≈ 1,8 aus Williams). Das bringt 2100 rund 20 Prozentpunkte zurück. Die
Richtung ist belegt: Nach Störungen steigt die Albedo, boreal kühlen Brände
über Jahrzehnte (Randerson et al. 2006). Die Stärke ist eine Annahme.
