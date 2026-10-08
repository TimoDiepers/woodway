"""DAC chapter: the optimisation -- slide 30 (goal and inputs), 31 (where and when, animated map), 32 (electricity
mix and target year). Data: data/dac/optim.json (scripts/dac_optim_export.py), luecke.json (trees, need)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from dacopt_assets import assets
from dacopt_v1 import _de, _xy, patch_closing
from patch_story4 import _rep, _sec

HERE = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
AMBER, TREE, NEED = "#9a6516", "#2f7a45", "#8e0d16"
PATHS = {"SSP2-NPi": ("heutige Politik", "#b0603a"), "SSP2-NDC": ("heutige Zusagen", AMBER),
         "SSP2-PkBudg650": ("1,5-°C-kompatibel", "#1f7a74")}

CSS = """
/* ---------- DAC optimisation (slides 30-32) ---------- */
.goal { display: grid; grid-template-columns: auto 1fr; gap: 30px; align-items: center; padding: 18px 28px; border-radius: 14px;
        background: rgba(154, 101, 22, .09); border: 2px solid rgba(154, 101, 22, .35); }
.goal .big { font: 600 78px/1 var(--sans); color: #9a6516; letter-spacing: -.01em; }
.goal p { font: 400 27px/1.35 var(--sans); color: var(--ink); margin: 0; }
.goal p small { display: block; font-size: 19px; color: var(--muted); margin-top: 4px; }
.ask { font: 400 29px/1.3 var(--sans); color: var(--ink); margin: 44px 0 22px; }
.ask b { color: #6b4410; font-weight: 600; }
.inputs { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }
.inp { border-top: 3px solid #9a6516; padding: 12px 4px 0; }
.inp .v { font: 600 48px/1.05 var(--sans); color: var(--ink); }
.inp .v small { font-size: 24px; font-weight: 500; }
.inp h4 { font: 600 24px/1.25 var(--sans); color: #6b4410; margin: 10px 0 8px; }
.inp p { font: 400 21px/1.4 var(--sans); color: var(--ink-2); margin: 0; }
.inp .q { display: block; margin-top: 10px; font-size: 17px; color: var(--muted); }

.play { display: grid; grid-template-columns: 1090px 1fr; grid-template-rows: auto 196px; gap: 6px 30px; flex: 1; min-height: 0; }
.play .wmap { position: relative; width: 1090px; height: 430px; }
.play .wmap img, .play .wmap svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.play .wmap img { image-rendering: pixelated; opacity: .85; }
.play .side { display: flex; flex-direction: column; gap: 16px; padding-top: 4px; }
.play .side .takeaway { padding: 12px 16px 13px 50px; }
.play .side .takeaway::before { left: 16px; top: 14px; width: 22px; height: 22px; }
.play .yr { font: 600 84px/1 var(--sans); color: var(--ink); font-variant-numeric: tabular-nums; }
.play .ctr .n { font: 600 44px/1.05 var(--sans); color: #9a6516; font-variant-numeric: tabular-nums; }
.play .ctr .n small { font-size: 24px; font-weight: 500; }
.play .ctr .l { font: 400 18px/1.3 var(--sans); color: var(--muted); }
.play .legend-eta { font: 400 17px/1.3 var(--sans); color: var(--muted); }
.play .legend-eta i { display: inline-block; width: 120px; height: 12px; border-radius: 6px; vertical-align: middle; margin: 0 6px;
                      background: linear-gradient(90deg, #c8602a, #e9dcae, #1f7a74); }
.play .strip { grid-column: 1 / -1; position: relative; }
.play .strip svg { width: 100%; height: 100%; overflow: visible; }

.mix { display: grid; grid-template-columns: 1fr 560px; gap: 46px; flex: 1; min-height: 0; }
.mix h5 { font: 600 21px/1.2 var(--sans); color: var(--ink); margin: 0 0 6px; }
.mix h5 small { font-weight: 400; color: var(--muted); font-size: 17px; }
.mix svg { width: 100%; overflow: visible; }
"""


def _load():
    res = json.loads((REPO / "data/dac/optim.json").read_text())
    gap = json.loads((REPO / "docs/slides/chart_data/luecke.json").read_text())
    return res, gap


# ---------------------------------------------------------------- slide 30
def _slide30(res: dict, gap: dict) -> str:
    h = res["haupt"]
    need = 1000 * h["luecke_k"][-1]
    trees = gap["k"][-1]
    store = json.loads((REPO / "data/dac/speicher_gidden.json").read_text())
    world = sum(v["prudent"] for v in store.values())
    em = {p["strompfad"]: p["eta_median"] for p in res["strompfade"]}["SSP2-NDC"]
    y = h["jahre"]
    e26, e40 = _de(100 * em[0]), _de(100 * em[y.index(2040)])
    return f'''<section class="slide" data-ch="dac" data-title="Optimierung von DAC">
  <header class="sh"><h2>DAC optimal einsetzen</h2></header>
  <div class="body">
    <div class="goal"><div class="big">{_de(h["co2_ziel_gt"])} Gt CO₂</div><p>muss DAC bis 2100 netto entnehmen, damit Very Low bei 1,5 °C endet
      <small>so viel kühlt 2100 die {_de(need)} mK, die nach den Bäumen fehlen (Folie 25; Klimaantwort wie bei den Bäumen)</small></p></div>
    <p class="ask rise" data-step="1">Gesucht: <b>wo und wann</b> DAC gebaut wird, mit möglichst wenig Anlagen. Eingaben und Grenzen:</p>
    <div class="inputs">
      <div class="inp rise" data-step="1" style="--d:200"><div class="v">{e26} → {e40} <small>%</small></div><h4>Netto-Anteil je Ort und Jahr</h4>
        <p>steigt mit sauberem Strom (Median 2026 → 2040)</p><span class="q">Strommix REMIND-EU über premise; Klima Sendi et al. 2022 (Folie 29)</span></div>
      <div class="inp rise" data-step="1" style="--d:450"><div class="v">{_de(world)} <small>Gt</small></div><h4>Speicher je Land</h4>
        <p>sicher nutzbar weltweit; Deutschland 1,3 Gt</p><span class="q">Gidden et al. 2025, Nature</span></div>
      <div class="inp rise" data-step="1" style="--d:700"><div class="v">≤ 20 <small>% pro Jahr</small></div><h4>Wachstum</h4>
        <p>ab 8,8 Mt/a (2030), so schnell wie einst die Windkraft</p><span class="q">Zurbriggen et al. 2026, Nat. Commun.</span></div>
      <div class="inp rise" data-step="1" style="--d:950"><div class="v">bis 2100</div><h4>Anlagen laufen weiter</h4>
        <p>einmal gebaut, bleibt eine Anlage in Betrieb</p><span class="q">Annahme</span></div>
    </div>
  </div>
  <p class="src">Lineares Programm, eigene Rechnung: Netto-Entnahme bis 2100 ≥ Vorgabe; kleinste Kapazität (größte Jahresentnahme), dann kleinste Gesamtmenge. Netto-Anteil: beste 10 % der Zellen je Land mit Sedimentbecken in höchstens 100 km. Klimaantwort: FaIR, wie bei den Bäumen.</p>
  <aside class="notes" data-n="0">
    <p>Jetzt drehen wir die Frage um: Nicht „Baum oder Maschine je Tonne“, sondern: Was müsste DAC leisten, damit wir 2100 bei 1,5 °C ankommen? Nach den Bäumen fehlen 2100 noch {_de(need)} Millikelvin. In CO₂ umgerechnet, mit derselben Klimaantwort wie beim Baum, heißt das: DAC muss bis 2100 netto {_de(h["co2_ziel_gt"])} Gigatonnen entnehmen. Das ist unsere Vorgabe.</p>
    <p>Klick: Gesucht ist, wo, wann und wie viel, mit möglichst wenig Anlagen. Die Rechnung kennt vier Dinge: wie viel einer entnommenen Tonne je Ort und Jahr netto bleibt, das steigt mit dem Strommix; wie viel CO₂ jedes Land sicher speichern kann, nach Gidden et al. weltweit {_de(world)} Gigatonnen, Deutschland nur 1,3; wie schnell DAC wachsen kann, höchstens 20 Prozent im Jahr wie einst die Windkraft, ausgehend von den 8,8 Megatonnen, die für 2030 geplant sind; und dass gebaute Anlagen weiterlaufen.</p>
    <p class="q">Falls Fragen kommen — Das ist ein lineares Programm: Entnahme je Land und Jahr als Variablen, Netto-Entnahme bis 2100 als Vorgabe. Die Umrechnung von Millikelvin in Gigatonnen nutzt die Klimaantwort aus FaIR, linear je Tonne; mit vollem FaIR nachgerechnet kühlt der Pfad um {_de(100 * res["fair_abweichung_2100_rel"], 1)} % stärker, die Rechnung ist also konservativ. DAC kommt zusätzlich zu den 335 Gt Entnahme, die in Very Low schon stecken. Kein Transport über Landesgrenzen; Basalt-Mineralisierung (Island) ist bei Gidden nicht enthalten.</p>
  </aside>
</section>

'''


from dacopt_s31 import CSS31, PLAY_JS, play_data, slide31, slide32


def _slide25(main: str, res: dict, gap: dict) -> str:
    """Slide 25: the limit as the 2100 value only, as on slide 30."""
    need, trees = gap["need"][-1], gap["k"][-1]
    m = _sec(main, "Wiederbewaldbare Fläche")
    sec = _rep(m.group(0), "Grenzwert 1,5 °C: 2050 fehlen 323 mK, die Bäume bringen 14 mK.",
               f"Für 1,5 °C in 2100 bräuchte es das {_de(need / trees, 1)}-Fache der Bäume: zusätzlich rund {_de(res['haupt']['co2_ziel_gt'], 0)} Gt CO₂ Entnahme.")
    sec, k = re.subn(r"<p>Klick: Und reicht das\?.*?</p>",
                     f"<p>Klick: Und reicht das? Die Achse wächst mit. Rot der Grenzwert: Very Low liegt 2100 noch {_de(need)} Millikelvin über 1,5 °C; "
                     f"so viel Kühlung wäre zusätzlich nötig, um 2100 bei 1,5 °C zu sein. Die Bäume auf den kühlenden Flächen bringen {_de(trees)}; "
                     f"es fehlen {_de(need - trees)}, also das {_de(need / trees, 1)}-Fache der Bäume. In CO₂ umgerechnet, mit derselben Klimaantwort, sind das rund {_de(res['haupt']['co2_ziel_gt'], 0)} Gigatonnen zusätzliche Netto-Entnahme bis 2100. Zwischendurch liegt Very Low noch höher, um 2050 gut 0,3 Grad über 1,5 °C.</p>", sec, count=1, flags=re.S)
    assert k == 1
    sec = sec.replace("Grenzwert: Erwärmung von Very Low über 1,5 °C (Median, van Vuuren et al. 2026).",
                      "Grenzwert: Erwärmung von Very Low 2100 über 1,5 °C (Median, 7-Jahres-Mittel; van Vuuren et al. 2026).")
    return main[: m.start()] + sec + main[m.end():]


def patch(page: str) -> str:
    res, gap = _load()
    page = page.replace("</style>", CSS + CSS31 + "</style>", 1)
    page = _rep(page, "window.LUECKE = {", 'window.LUECKE = {"co2": ' + f'{res["haupt"]["co2_ziel_gt"]:.1f}, ')
    main, backup = page.split("<!-- BACKUP:BEGIN -->", 1)
    main = _slide25(main, res, gap)
    m = _sec(main, "Netto-Entnahme von DAC")
    sec29 = _rep(m.group(0), "<p>Diese Karte setzt einen Strompfad voraus. Wie robust ist das? Die nächste Folie rechnet drei Pfade.</p>",
                 "<p>Wo und wann sollte man also bauen, damit es für 1,5 °C reicht? Das rechnen wir jetzt.</p>")
    main = main[: m.start()] + sec29 + _slide30(res, gap) + slide31(res, gap) + slide32(res) + main[m.end():]
    from patch_story3 import BACKUP_MARK
    moved = []
    for title in ("DAC in drei Strompfaden", "Priorisierung von Aufforstung und DAC"):
        m = _sec(main, title)
        moved.append(re.sub(r'<aside class="notes" data-n="\d+">', '<aside class="notes">', m.group(0)))
        main = main[: m.start()] + main[m.end():]
    backup = backup.replace(BACKUP_MARK, "".join(moved) + BACKUP_MARK, 1)
    main = patch_closing(main, res)
    n = iter(range(1, 1000))
    main = re.sub(r'<aside class="notes" data-n="\d+">', lambda mm: f'<aside class="notes" data-n="{next(n)}">', main)
    page = main + "<!-- BACKUP:BEGIN -->" + backup
    js = "window.DAC_PLAY = " + json.dumps(play_data(res, gap)) + ";\n" + PLAY_JS
    i = page.rindex("</body>")
    return page[:i] + "<script>\n" + js + "</script>\n" + page[i:]
