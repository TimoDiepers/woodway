import { useCallback, useEffect, useRef, useState } from "react";
import { loadAtlas } from "@/data/load";
import { useAtlas } from "@/store";
import DeckFrame, { type DeckFrameHandle } from "./DeckFrame";
import { CmdGate } from "./gate";
import { follow, next, prev, type Cmd, type DeckState, type Pos } from "./navigation";
import { MAIN_END, SEQUENCE, type AtlasSlideId } from "./sequence";

// Filled in with the atlas slides (Task 4): clicks per slide and the speaker notes.
const atlasSteps = (_id: AtlasSlideId): number => 0;
const ATLAS_NOTES: Partial<Record<AtlasSlideId, string>> = {};

const NEXT_KEYS = new Set(["ArrowRight", " ", "PageDown", "Enter"]);
const PREV_KEYS = new Set(["ArrowLeft", "PageUp", "Backspace"]);

function fitScale() { return Math.min(window.innerWidth / 1600, window.innerHeight / 900); }

export default function TalkApp() {
  const [pos, setPos] = useState<Pos>({ k: 0, step: 0 });
  const [deck, setDeck] = useState<DeckState | null>(null);
  const [notesOpen, setNotesOpen] = useState(false);
  const [missing, setMissing] = useState(false);
  const [scale, setScale] = useState(fitScale);
  const frame = useRef<DeckFrameHandle>(null);
  const gate = useRef(new CmdGate());

  useEffect(() => {
    useAtlas.getState().setLang("de");
    loadAtlas("data/").catch(() => { /* atlas slides report their own missing data */ });
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
  const notes = item.kind === "atlas" ? ATLAS_NOTES[item.id] : undefined;

  return (
    <div className="talk-stage" onClick={forward}>
      <div className="talk-deck" style={{ transform: `translate(-50%, -50%) scale(${scale})` }} data-k={pos.k} data-step={pos.step}>
        <div style={{ visibility: atlasShown ? "hidden" : "visible" }}>
          <DeckFrame ref={frame} onState={onState} onMissing={onMissing} />
        </div>
        {item.kind === "atlas" && (
          <section className="rslide" data-atlas={item.id} data-step={pos.step}><h2>{item.id}</h2></section>
        )}
      </div>
      {missing && <p role="alert" className="talk-missing">Das HTML-Deck fehlt: erst python deck/build.py ausführen.</p>}
      <div className="talk-progress" style={{ transform: `scaleX(${pos.k / (SEQUENCE.length - 1)})` }} />
      <div className={"talk-drawer" + (notesOpen ? " open" : "")} aria-live="polite" onClick={(e) => e.stopPropagation()}>
        <h5>Sprechernotizen</h5>
        {notes ? <p>{notes}</p> : <p className="q">{item.kind === "atlas" ? "Keine Notizen." : "Notizen dieser Folie stehen im HTML-Deck."}</p>}
      </div>
    </div>
  );
}
