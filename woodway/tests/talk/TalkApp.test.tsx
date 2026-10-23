import { act, fireEvent, render, screen } from "@testing-library/react";
import TalkApp from "@/talk/TalkApp";
import { deckIndex } from "@/talk/deckSlides";
import { SEQUENCE } from "@/talk/sequence";

vi.mock("@/data/load", () => ({ loadAtlas: () => new Promise(() => {}) }));

const state = { i: 0, step: 0, ni: 0, ns: 1, n: 46, main: 32 };
function reply(frame: HTMLIFrameElement, s = state) {
  act(() => { window.dispatchEvent(new MessageEvent("message", { data: { src: "dv", state: s }, source: frame.contentWindow })); });
}

describe("TalkApp", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("clears the missing-deck alert when the deck answers late", () => {
    const { container } = render(<TalkApp />);
    const frame = container.querySelector("iframe")!;
    fireEvent.load(frame);
    act(() => { vi.advanceTimersByTime(4100); });
    expect(screen.getByRole("alert")).toBeTruthy();
    reply(frame);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("sends one command per key until the deck answered", () => {
    const { container } = render(<TalkApp />);
    const frame = container.querySelector("iframe")!;
    fireEvent.load(frame);
    reply(frame);
    const post = vi.spyOn(frame.contentWindow!, "postMessage");
    for (let n = 0; n < 5; n++) fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(post.mock.calls.filter((c) => (c[0] as { cmd: string }).cmd === "next")).toHaveLength(1);
    reply(frame, { ...state, i: 0, step: 1, ni: 1, ns: 0 });
    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(post.mock.calls.filter((c) => (c[0] as { cmd: string }).cmd === "next")).toHaveLength(2);
  });

  it("a key right after the deck's reply starts from the reply's state, before React re-rendered", () => {
    const i = deckIndex("Ein Baum an jedem Ort");
    const { container } = render(<TalkApp />);
    const frame = container.querySelector("iframe")!;
    fireEvent.load(frame);
    reply(frame, { ...state, i, step: 1, ni: i, ns: 2 });
    const post = vi.spyOn(frame.contentWindow!, "postMessage");
    act(() => {
      window.dispatchEvent(new MessageEvent("message", { data: { src: "dv", state: { ...state, i, step: 2, ni: i + 1, ns: 0 } }, source: frame.contentWindow }));
      fireEvent.keyDown(window, { key: "ArrowRight" });
    });
    expect(post).not.toHaveBeenCalled();   // the last click is done: the key enters the atlas slide, no further "next"
    expect(container.querySelector(".talk-deck")!.getAttribute("data-k")).toBe(String(SEQUENCE.findIndex((x) => x.kind === "atlas")));
  });

  it("the progress bar is full on 'Danke'", () => {
    const { container } = render(<TalkApp />);
    const frame = container.querySelector("iframe")!;
    fireEvent.load(frame);
    reply(frame, { ...state, i: deckIndex("Danke"), ni: deckIndex("Danke") + 1, ns: 0 });
    expect((container.querySelector(".talk-progress") as HTMLElement).style.transform).toBe("scaleX(1)");
  });

  it("a focused button does not block the arrow keys", () => {
    const { container } = render(<TalkApp />);
    const frame = container.querySelector("iframe")!;
    fireEvent.load(frame);
    reply(frame, { ...state, i: 1, step: 0, ni: 1, ns: 1 });
    const post = vi.spyOn(frame.contentWindow!, "postMessage");
    const b = document.body.appendChild(document.createElement("button"));
    fireEvent.keyDown(b, { key: "ArrowLeft" });
    expect(post.mock.calls.some((c) => (c[0] as { cmd: string }).cmd === "prev")).toBe(true);
    b.remove();
  });

  it("typing in a text field does not turn pages", () => {
    const { container } = render(<TalkApp />);
    const frame = container.querySelector("iframe")!;
    fireEvent.load(frame);
    reply(frame);
    const post = vi.spyOn(frame.contentWindow!, "postMessage");
    const input = document.body.appendChild(document.createElement("input"));
    input.type = "search";
    fireEvent.keyDown(input, { key: "ArrowRight" });
    expect(post).not.toHaveBeenCalled();
    input.remove();
  });
});
