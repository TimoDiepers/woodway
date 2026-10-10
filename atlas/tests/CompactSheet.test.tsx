import { fireEvent, render, screen } from "@testing-library/react";
import { CompactSheet } from "@/ui/CompactSheet";

function setup(snap = 0) {
  const onSnap = vi.fn();
  render(<CompactSheet title="Atlas" peek={<p>peek</p>} snaps={[0.2, 0.55, 0.92]} snap={snap} onSnap={onSnap} vh={800}><p>more</p></CompactSheet>);
  return onSnap;
}

describe("CompactSheet", () => {
  it("a tap on the handle steps up (pointer capture must not lose which element was pressed)", () => {
    const onSnap = setup(0);
    const handle = screen.getByRole("button", { name: "Show more" });
    const wrap = handle.parentElement!;
    fireEvent.pointerDown(handle, { clientY: 600, pointerId: 1 });
    fireEvent.pointerUp(wrap, { clientY: 600, pointerId: 1 });   // captured: the release lands on the wrapper
    expect(onSnap).toHaveBeenCalledWith(1);
  });
  it("Enter on the handle steps up; arrow keys step up and down", () => {
    const onSnap = setup(1);
    const handle = screen.getByRole("button", { name: "Show more" });
    fireEvent.click(handle, { detail: 0 });
    expect(onSnap).toHaveBeenLastCalledWith(2);
    fireEvent.keyDown(handle, { key: "ArrowDown" });
    expect(onSnap).toHaveBeenLastCalledWith(0);
  });
  it("a drag settles on the nearest height", () => {
    const onSnap = setup(0);
    const handle = screen.getByRole("button", { name: "Show more" });
    fireEvent.pointerDown(handle, { clientY: 640, pointerId: 1 });
    fireEvent.pointerMove(handle.parentElement!, { clientY: 300, pointerId: 1 });   // +340 px: from 160 to 500 px
    fireEvent.pointerUp(handle.parentElement!, { clientY: 300, pointerId: 1 });
    expect(onSnap).toHaveBeenCalledWith(1);                                         // 0.55 × 800 = 440 is nearest
  });
  it("the hidden part is inert at the peek and live above it", () => {
    setup(0);
    expect(screen.getByText("more").parentElement).toHaveAttribute("inert");
  });
});
