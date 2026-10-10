import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef } from "react";
import type { Cmd, DeckState } from "./navigation";

export const DECK_URL = import.meta.env.DEV ? "/deck/index.html?host" : "../index.html?host";

export interface DeckFrameHandle { send: (cmd: NonNullable<Cmd>) => void }
interface Props { onState: (s: DeckState) => void; onMissing: () => void }

const ANSWER_TIMEOUT_MS = 4000;
// The deck listens as soon as its script has run; its iframe `load` event waits for every data file
// (seconds), so greet it from the start until it answers.
const HELLO_EVERY_MS = 250;

const DeckFrame = forwardRef<DeckFrameHandle, Props>(function DeckFrame({ onState, onMissing }, ref) {
  const frame = useRef<HTMLIFrameElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>();
  const answered = useRef(false);
  const greet = useRef<ReturnType<typeof setInterval>>();

  const post = useCallback((msg: Record<string, unknown>) => {
    frame.current?.contentWindow?.postMessage({ src: "dv", ...msg }, "*");
  }, []);

  useImperativeHandle(ref, () => ({
    send: (cmd) => post(cmd.send === "goto" ? { cmd: "goto", n: cmd.n, step: cmd.step } : { cmd: cmd.send }),
  }), [post]);

  useEffect(() => {
    const onMessage = (e: MessageEvent) => {
      if (e.source !== frame.current?.contentWindow) return;
      const d = e.data;
      if (!d || d.src !== "dv" || !d.state) return;
      answered.current = true;
      clearTimeout(timer.current);
      clearInterval(greet.current);
      onState(d.state as DeckState);
    };
    window.addEventListener("message", onMessage);
    return () => { window.removeEventListener("message", onMessage); clearTimeout(timer.current); };
  }, [onState]);

  useEffect(() => {
    greet.current = setInterval(() => { if (!answered.current) post({ cmd: "hello" }); else clearInterval(greet.current); }, HELLO_EVERY_MS);
    return () => clearInterval(greet.current);
  }, [post]);

  const onLoad = () => {
    post({ cmd: "hello" });
    clearTimeout(timer.current);
    if (!answered.current) timer.current = setTimeout(() => { if (!answered.current) onMissing(); }, ANSWER_TIMEOUT_MS);
  };

  return <iframe ref={frame} src={DECK_URL} title="Vortrag" tabIndex={-1} onLoad={onLoad} onError={onMissing} style={{ pointerEvents: "none" }} />;
});

export default DeckFrame;
