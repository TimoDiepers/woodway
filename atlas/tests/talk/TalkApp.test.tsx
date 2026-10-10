import { act, fireEvent, render, screen } from "@testing-library/react";
import TalkApp from "@/talk/TalkApp";

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
});
