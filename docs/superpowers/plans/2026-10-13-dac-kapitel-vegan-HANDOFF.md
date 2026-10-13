# Übergabe: DAC-Kapitel mit Kosten und veganer Welt

Für die Session, die den Plan umsetzt. Stand 2026-10-13. Lies dieses Dokument ganz, dann Spec, dann Plan.

## Was zu tun ist

Den Plan `docs/superpowers/plans/2026-10-13-dac-kapitel-vegan.md` Task für Task umsetzen (Skill `superpowers:executing-plans`, Checkboxen abhaken). Die Spec dazu: `docs/superpowers/specs/2026-10-13-dac-kapitel-vegan-design.md`. Beide sind mit Timo abgestimmt; Entscheidungen nicht neu verhandeln (Liste unten).

## Wo gearbeitet wird

- **Worktree:** `/Users/timodiepers/Documents/Coding/dissvortrag-main`, Branch `main`. Alle Pfade im Plan sind relativ dazu.
- **Nicht** im Hauptordner `/Users/timodiepers/Documents/Coding/dissvortrag` arbeiten – dort ist Branch `holzweg` (anderes Thema) ausgecheckt.
- **Uncommitteter WIP** in 11 Dateien auf main (20 a Lebensdauer, `solve_min_peak`, Kostenfunktionen) gehört zu dieser Arbeit; Task 1 committet ihn, nachdem die Tests grün sind.
- main ist 3 Commits vor `origin/main` (Spec und Plan). **Nicht pushen ohne Timos Zustimmung** – ein Push auf main startet `.github/workflows/pages.yml` und veröffentlicht das Deck.
- Rohdaten (gitignored) liegen nur im Hauptordner: `/Users/timodiepers/Documents/Coding/dissvortrag/data/raw`. Task 5 legt im Worktree einen Symlink `data/raw` an.
- Python: `uv run …` im Worktree (eigene `.venv`, wird beim ersten Aufruf gebaut). Kein `.venv/bin/python` direkt.

## Memory der Vorgänger-Session

Die automatische Memory liegt unter `/Users/timodiepers/.claude/projects/-Users-timodiepers-Documents-Coding-dissvortrag/memory/` und lädt **nur**, wenn die Session im Hauptordner `dissvortrag` startet. Startest du in `dissvortrag-main`, lies diese Dateien von Hand (Pflicht):

- `MEMORY.md` (Index)
- `dac-optimierung.md`, `storyline-zeit-kapitel34.md`, `dissvortrag-eine-regel.md`, `dac-modell-setup.md`
- `wissenschaftlich-ehrlich-bleiben.md`, `folientitel-beschreibend.md`, `animation-nur-neues.md`, `lesbarkeit-grosser-saal.md`, `design-erst-zeigen-dann-committen.md`, `takeaway-darf-frage-sein.md`, `keine-claude-attribution.md`, `dissvortrag-artifact.md`

Neue Erkenntnisse in diesen Memory-Ordner schreiben (Task 12, Step 6).

## Abgestimmte Entscheidungen (nicht neu verhandeln)

| Thema | Entscheidung |
|---|---|
| DAC-Ziel | erst niedrigste Spitze über 1,5 °C, dann so früh wie möglich zurück (`solve_min_peak(..., danach="frueh")`). Timo hatte das früher verworfen (54 Gt/a ohne Grenze); jetzt bewusst gewählt. |
| Tempo | 20/30/50 %/a und ohne Grenze; Botschaft: nur Tempo senkt die Spitze; Spitze zählt wegen Kipppunkten/Extremen. |
| Kosten | im Nachgang auf den optimierten Pfad (`path_cost`), Okosun 2026, Median + Spanne, reale EUR 2024, unverzinst; Spitze je Jahr und Summe 2026–2100. |
| Vergleich | BIP EU-27 2024 (Eurostat) und explizite fossile Subventionen (IEA) auf der Folie; IMF inkl. impliziter Kosten (~7 Bio. USD) nur in den Notizen. |
| Bäume | Bonn-Challenge-Tempo **überall raus**: alles 2026 pflanzen, „einfache Annahme“ (Timo). Gilt Kapitel 4, Lücke, vegane Welt. |
| Vegan Umfang | Gase (CH₄, N₂O) **und** Wald auf frei werdenden Flächen; der Flächenteil ist ausdrücklich als größerer, unsicherer Teil zu nennen. |
| Vegan Tempo | sofort und vollständig 2026 (Grenzfall). |
| Vegan Flächen | explizit modelliert: Walkers `Societal_Constraints` (Weide ganz, Acker zu 19 % nach Poore & Nemecek), nur NCS R/L+R/H, dieselbe Baumkette, nur kühlende Zellen. |
| Vegan Gase | FAOSTAT + Poore & Nemecek; Delta bezogen auf den **Agrar-Pfad von Very Low** (Sektordaten des Markers REMIND-MAgPIE 3.5-4.11 suchen, Plan Task 5 Step 1b); Rückfall: konstanter Anteil an der Gesamtemission (vorsichtig, so benennen). |
| Ergebnis | Schließen vegan + Bäume die Lücke fast ganz, wird genau das gezeigt. |

## Haltepunkte bei Timo (dort anhalten und warten)

1. **Task 1 Step 1:** wenn die WIP-Tests scheitern.
2. **Task 9 Step 4:** Zahlentabelle des Volllaufs vorlegen, Annahmen nennen; erst nach OK Daten committen und weiter.
3. **Task 10 Step 4** und **Task 11 Step 6:** Screenshots der Folien zeigen; erst nach OK committen.
4. Immer, wenn ein Ergebnis unplausibel ist: nicht glätten, sondern zeigen ([[wissenschaftlich-ehrlich-bleiben]]).

## Arbeitsweise mit Timo

- Antworten auf Deutsch, knapp. Folientexte Deutsch, sachlich, keine Slogans.
- Commits: Conventional-Commit-Stil auf Englisch, **ohne** `Co-Authored-By` und ohne „Generated with Claude Code“.
- Gestaltung erst als Screenshot zeigen, dann committen.
- Neue Zahlen auf Folien nur aus `deck/chart_data/zeitpfade.json` bzw. den Build-Skripten, nie von Hand.

## Bekannte Stolpersteine

- `scripts/build_zeitpfade_data.py` läuft ~1 h (viele LPs); im Hintergrund starten und Log mitschreiben.
- Headless-Screenshots von Chart-Folien per `#N` sind flaky (echarts lädt nicht immer rechtzeitig): mehrfach versuchen.
- Deck bauen: `uv run python deck/build.py` → `deck/dist/index.html` (dist ist gitignored).
- FaIR: `nbs.fair_module` rechnet mit dem zentralen Mitglied; CMIP7-Szenarien heißen `"cmip7-VL"` usw.; Bäume laufen auf `"ssp245"`-Hintergrund (bestehende Konvention, beibehalten).
- Walker-README: Klassen in `Societal_Constraints_500m.tif`: 1 Acker, 2 Wanderfeldbau, 3 Weide, 4 Siedlung. Download über Harvard Dataverse doi:10.7910/DVN/DSDDQK.
- Die CMIP7-Zenodo-Daten (record 20713982) enthalten **keine** Sektoraufteilung – schon geprüft; für Step 1b andere Quellen nutzen.

## Vorschlag für den ersten Prompt der neuen Session

> Setze den Plan `docs/superpowers/plans/2026-10-13-dac-kapitel-vegan.md` um. Lies zuerst `docs/superpowers/plans/2026-10-13-dac-kapitel-vegan-HANDOFF.md` und die dort genannten Memory-Dateien, dann Spec und Plan. Arbeite im Worktree `/Users/timodiepers/Documents/Coding/dissvortrag-main` mit superpowers:executing-plans und halte an den Haltepunkten an.
