import { act, render, screen } from "@testing-library/react";
import { SlideBoundary } from "@/talk/SlideBoundary";
import { fireEvent } from "@testing-library/react";
import DeckFrame from "@/talk/DeckFrame";
import TalkApp from "@/talk/TalkApp";
import { MAIN_END, SEQUENCE } from "@/talk/sequence";

vi.mock("@/data/load", () => ({ loadAtlas: () => new Promise(() => {}) }));
const state = { i: 0, step: 0, ni: 0, ns: 1, n: 46, main: 32 };
const reply = (f: HTMLIFrameElement, s: object) =>
  act(() => { window.dispatchEvent(new MessageEvent("message", { data: { src: "dv", state: s }, source: f.contentWindow })); });

function Boom(): JSX.Element { throw new Error("broken slide"); }

describe("robustness", () => {
  it("an atlas slide that throws shows a message instead of blanking the talk", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(<SlideBoundary title="Netto-Anteil"><Boom /></SlideBoundary>);
    expect(screen.getByRole("alert")).toHaveTextContent("Netto-Anteil");
    spy.mockRestore();
  });

  it("after the deck's iframe reloads (e.g. after a crash) the shell greets it again", () => {
    vi.useFakeTimers();
    const { container } = render(<DeckFrame onState={() => {}} onMissing={() => {}} />);
    const frame = container.querySelector("iframe") as HTMLIFrameElement;
    const win = frame.contentWindow!;
    act(() => { window.dispatchEvent(new MessageEvent("message", { source: win, data: { src: "dv", state: { i: 3, step: 0, ni: 4, ns: 0 } } })); });
    const post = vi.spyOn(win, "postMessage");
    act(() => { frame.dispatchEvent(new Event("load")); vi.advanceTimersByTime(600); });
    expect(post.mock.calls.filter(([m]) => (m as { cmd?: string }).cmd === "hello").length).toBeGreaterThanOrEqual(2);
    vi.useRealTimers();
  });

  it("a jump from the overview is never dropped, even while the deck still owes a reply", () => {
    vi.useFakeTimers();
    const { container } = render(<TalkApp />);
    const frame = container.querySelector("iframe")!;
    reply(frame, state);
    fireEvent.keyDown(window, { key: "ArrowRight" });            // a command in flight, no reply yet
    fireEvent.click(screen.getByRole("button", { name: "Folienübersicht" }));
    const target = SEQUENCE.findIndex((s, k) => k > 5 && s.kind === "deck");
    fireEvent.click(screen.getAllByRole("button", { name: /^\d+[a-z]?\s/ })[target]);
    expect(container.querySelector(".talk-deck")!.getAttribute("data-k")).toBe(String(target));
    fireEvent.keyDown(window, { key: "b" });
    expect(container.querySelector(".talk-deck")!.getAttribute("data-k")).toBe(String(MAIN_END));
    vi.useRealTimers();
  });

  it("a reloaded deck is sent back to the slide the talk is on", () => {
    vi.useFakeTimers();
    const { container } = render(<TalkApp />);
    const frame = container.querySelector("iframe")!;
    reply(frame, state);
    fireEvent.keyDown(window, { key: "b" });
    const at = SEQUENCE[MAIN_END] as { kind: "deck"; i: number };
    reply(frame, { ...state, i: at.i });
    const post = vi.spyOn(frame.contentWindow!, "postMessage");
    act(() => { fireEvent.load(frame); });                         // the deck's page was reloaded (crash, memory)
    reply(frame, state);                                           // … and greets from slide 1
    expect(post.mock.calls.some(([m]) => (m as { cmd?: string; n?: number }).cmd === "goto" && (m as { n: number }).n === at.i)).toBe(true);
    expect(container.querySelector(".talk-deck")!.getAttribute("data-k")).toBe(String(MAIN_END));
    vi.useRealTimers();
  });
});
