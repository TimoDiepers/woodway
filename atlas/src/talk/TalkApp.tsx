import { useCallback, useEffect, useRef, useState } from "react";
import { loadAtlas } from "@/data/load";
import { useAtlas } from "@/store";
import DeckFrame, { type DeckFrameHandle } from "./DeckFrame";
import { CmdGate } from "./gate";
import { follow, next, prev, type Cmd, type DeckState, type Pos } from "./navigation";
import { MAIN_END, SEQUENCE } from "./sequence";
import { SLIDES, atlasSteps } from "./slides";
import AtlasSlide from "./AtlasSlide";
import type { Atlas } from "@/data/types";


const NEXT_KEYS = new Set(["ArrowRight", " ", "PageDown", "Enter"]);
const PREV_KEYS = new Set(["ArrowLeft", "PageUp", "Backspace"]);

function fitScale() { return Math.min(window.innerWidth / 1600, window.innerHeight / 900); }

export default function TalkApp() {
  const [pos, setPos] = useState<Pos>({ k: 0, step: 0 });
  const [deck, setDeck] = useState<DeckState | null>(null);
  const [notesOpen, setNotesOpen] = useState(false);
  const [missing, setMissing] = useState(false);
  const [scale, setScale] = useState(fitScale);
  const [atlas, setAtlas] = useState<Atlas | null>(null);
  const [atlasFailed, setAtlasFailed] = useState(false);
  const frame = useRef<DeckFrameHandle>(null);
  const gate = useRef(new CmdGate());

  useEffect(() => {
    useAtlas.getState().setLang("de");
    loadAtlas("data/").then(setAtlas).catch(() => setAtlasFailed(true));
  }, []);

  useEffect(() => {
    const onResize = () => setScale(fitScale());
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const onState = useCallback((s: DeckState) => {
    if (!gate.current.accept(s)) return; // late reply to a superseded command
    setMissing(false);
    setDeck(s);
    setPos((p) => (SEQUENCE[p.k].kind === "deck" ? follow(SEQUENCE, p, s) : p));
  }, []);
  const onMissing = useCallback(() => setMissing(true), []);

  const apply = useCallback((r: { pos: Pos; cmd: Cmd }) => {
    setPos(r.pos);
    if (r.cmd) { gate.current.begin(r.cmd); frame.current?.send(r.cmd); }
  }, []);
  const go = useCallback((k: number) => {
    const it = SEQUENCE[k];
    if (!it || gate.current.busy()) return;
    setPos({ k, step: 0 });
    if (it.kind === "deck") {
      const cmd = { send: "goto", n: it.i, step: 0 } as const;
      gate.current.begin(cmd);
      frame.current?.send(cmd);
    }
  }, []);
  const forward = useCallback(() => { if (!gate.current.busy()) apply(next(SEQUENCE, pos, deck, atlasSteps)); }, [apply, pos, deck]);
  const back = useCallback(() => { if (!gate.current.busy()) apply(prev(SEQUENCE, pos, deck, atlasSteps)); }, [apply, pos, deck]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const el = e.target as HTMLElement | null;   // typing in the atlas search must not turn pages
      if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT|BUTTON)$/.test(el.tagName))) return;
      if (NEXT_KEYS.has(e.key)) { e.preventDefault(); forward(); }
      else if (PREV_KEYS.has(e.key)) { e.preventDefault(); back(); }
      else if (e.key === "Home") { e.preventDefault(); go(0); }
      else if (e.key === "b" || e.key === "B") go(MAIN_END);
      else if (e.key === "n" || e.key === "N") setNotesOpen((o) => !o);
      else if (e.key === "f" || e.key === "F") {
        if (document.fullscreenElement) void document.exitFullscreen();
        else void document.documentElement.requestFullscreen?.();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [forward, back, go]);

  const item = SEQUENCE[pos.k];
  const atlasShown = item.kind === "atlas";
  const notes = item.kind === "atlas" ? SLIDES[item.id].notes : undefined;
  const def = item.kind === "atlas" ? SLIDES[item.id] : null;

  return (
    <div className="talk-stage" onClick={forward}>
      <div className="talk-deck" style={{ transform: `translate(-50%, -50%) scale(${scale})` }} data-k={pos.k} data-step={pos.step}>
        <div style={{ visibility: atlasShown ? "hidden" : "visible" }}>
          <DeckFrame ref={frame} onState={onState} onMissing={onMissing} />
        </div>
        {def && (atlas
          ? <AtlasSlide def={def} atlas={atlas} step={pos.step} />
          : <section className="rslide" data-ch={def.ch}><header className="sh"><h2>{def.title}</h2></header>
              <p role={atlasFailed ? "alert" : undefined}>{atlasFailed ? "Die Atlas-Daten fehlen: erst atlas/export_atlas.py ausführen." : "Atlas wird geladen …"}</p></section>)}
      </div>
      {missing && <p role="alert" className="talk-missing">Das HTML-Deck fehlt: erst python deck/build.py ausführen.</p>}
      {def && <div className="talk-ground" data-ch={def.ch ?? "baeume"} />}
      <div className="talk-progress" style={{ transform: `scaleX(${pos.k / (SEQUENCE.length - 1)})` }} />
      <div className={"talk-drawer" + (notesOpen ? " open" : "")} aria-live="polite" onClick={(e) => e.stopPropagation()}>
        <h5>Sprechernotizen</h5>
        {notes ? notes.map((n, i) => <p key={i}>{n}</p>) : <p className="q">{item.kind === "atlas" ? "Keine Notizen." : "Notizen dieser Folie stehen im HTML-Deck."}</p>}
      </div>
    </div>
  );
}
