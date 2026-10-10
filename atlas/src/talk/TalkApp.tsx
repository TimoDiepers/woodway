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

/** Fields the keys belong to; a focused button or slider (left behind by a click) must not block ← →. */
function isTextField(el: HTMLElement): boolean {
  if (el.tagName === "TEXTAREA" || el.tagName === "SELECT") return true;
  return el.tagName === "INPUT" && /^(text|search|number|email|url|tel|password|)$/.test((el as HTMLInputElement).type || "");
}

function fitScale() { return Math.min(window.innerWidth / 1600, window.innerHeight / 900); }

export default function TalkApp() {
  const [pos, setPos] = useState<Pos>({ k: 0, step: 0 });
  const [notesOpen, setNotesOpen] = useState(false);
  const [missing, setMissing] = useState(false);
  const [scale, setScale] = useState(fitScale);
  const [atlas, setAtlas] = useState<Atlas | null>(null);
  const [atlasFailed, setAtlasFailed] = useState(false);
  // Key handlers read the latest deck state and position from refs: a reply and the next key can arrive before React re-renders.
  const posRef = useRef(pos);
  const deckRef = useRef<DeckState | null>(null);
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

  const movePos = useCallback((p: Pos) => { posRef.current = p; setPos(p); }, []);
  const onState = useCallback((s: DeckState) => {
    if (!gate.current.accept(s)) return; // late reply to a superseded command
    setMissing(false);
    deckRef.current = s;
    const p = posRef.current;
    if (SEQUENCE[p.k].kind === "deck") movePos(follow(SEQUENCE, p, s));
  }, [movePos]);
  const onMissing = useCallback(() => setMissing(true), []);

  const apply = useCallback((r: { pos: Pos; cmd: Cmd }) => {
    movePos(r.pos);
    if (r.cmd) { gate.current.begin(r.cmd); frame.current?.send(r.cmd); }
  }, [movePos]);
  const go = useCallback((k: number) => {
    const it = SEQUENCE[k];
    if (!it || gate.current.busy()) return;
    movePos({ k, step: 0 });
    if (it.kind === "deck") {
      const cmd = { send: "goto", n: it.i, step: 0 } as const;
      gate.current.begin(cmd);
      frame.current?.send(cmd);
    }
  }, [movePos]);
  const forward = useCallback(() => { if (!gate.current.busy()) apply(next(SEQUENCE, posRef.current, deckRef.current, atlasSteps)); }, [apply]);
  const back = useCallback(() => { if (!gate.current.busy()) apply(prev(SEQUENCE, posRef.current, deckRef.current, atlasSteps)); }, [apply]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const el = e.target as HTMLElement | null;   // typing in the atlas search must not turn pages
      if (el && (el.isContentEditable || isTextField(el))) return;
      if (el?.tagName === "BUTTON" && (e.key === " " || e.key === "Enter")) return;   // those press the button
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
      <div className="talk-progress" style={{ transform: `scaleX(${Math.min(1, pos.k / (MAIN_END - 1))})` }} />
      <div className={"talk-drawer" + (notesOpen ? " open" : "")} aria-live="polite" onClick={(e) => e.stopPropagation()}>
        <h5>Sprechernotizen</h5>
        {notes ? notes.map((n, i) => <p key={i}>{n}</p>) : <p className="q">{item.kind === "atlas" ? "Keine Notizen." : "Notizen dieser Folie stehen im HTML-Deck."}</p>}
      </div>
    </div>
  );
}
