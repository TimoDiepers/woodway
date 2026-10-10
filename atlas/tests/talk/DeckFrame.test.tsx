import { act, render } from "@testing-library/react";
import DeckFrame from "@/talk/DeckFrame";

describe("DeckFrame", () => {
  afterEach(() => vi.useRealTimers());

  it("greets the deck from the start, not only after the iframe's load event (which waits for all data)", () => {
    vi.useFakeTimers();
    const { container } = render(<DeckFrame onState={() => {}} onMissing={() => {}} />);
    const win = (container.querySelector("iframe") as HTMLIFrameElement).contentWindow!;
    const post = vi.spyOn(win, "postMessage");
    act(() => { vi.advanceTimersByTime(700); });
    const hellos = post.mock.calls.filter(([m]) => (m as { cmd?: string }).cmd === "hello");
    expect(hellos.length).toBeGreaterThanOrEqual(2);
  });

  it("stops greeting once the deck has answered", () => {
    vi.useFakeTimers();
    const onState = vi.fn();
    const { container } = render(<DeckFrame onState={onState} onMissing={() => {}} />);
    const win = (container.querySelector("iframe") as HTMLIFrameElement).contentWindow!;
    const post = vi.spyOn(win, "postMessage");
    act(() => {
      window.dispatchEvent(new MessageEvent("message", { source: win, data: { src: "dv", state: { i: 0, step: 0, ni: 1, ns: 0 } } }));
    });
    expect(onState).toHaveBeenCalled();
    post.mockClear();
    act(() => { vi.advanceTimersByTime(1000); });
    expect(post.mock.calls.filter(([m]) => (m as { cmd?: string }).cmd === "hello")).toHaveLength(0);
  });
});
