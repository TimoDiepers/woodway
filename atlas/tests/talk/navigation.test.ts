import { next, prev, follow, type DeckState } from "@/talk/navigation";
import type { Item } from "@/talk/sequence";

const seq: Item[] = [{ kind: "deck", i: 0 }, { kind: "deck", i: 1 }, { kind: "atlas", id: "jedeZelle" }, { kind: "deck", i: 2 }];
const steps = () => 2;
const st = (i: number, step: number, last: number): DeckState => ({ i, step, ni: step < last ? i : i + 1, ns: step < last ? step + 1 : 0 });

describe("navigation", () => {
  it("forwards next while the deck has clicks", () => {
    expect(next(seq, { k: 0, step: 0 }, st(0, 0, 1), steps)).toEqual({ pos: { k: 0, step: 0 }, cmd: { send: "next" } });
  });
  it("follows the deck onto its next slide", () => {
    expect(follow(seq, { k: 0, step: 0 }, st(1, 0, 3))).toEqual({ k: 1, step: 0 });
  });
  it("leaves the deck for an atlas slide after the last click", () => {
    expect(next(seq, { k: 1, step: 0 }, st(1, 3, 3), steps)).toEqual({ pos: { k: 2, step: 0 }, cmd: null });
  });
  it("steps through the atlas slide, then back into the deck", () => {
    expect(next(seq, { k: 2, step: 1 }, st(1, 3, 3), steps).pos).toEqual({ k: 2, step: 2 });
    expect(next(seq, { k: 2, step: 2 }, st(1, 3, 3), steps)).toEqual({ pos: { k: 3, step: 0 }, cmd: { send: "goto", n: 2, step: 0 } });
  });
  it("back into a deck slide lands on its end", () => {
    expect(prev(seq, { k: 2, step: 0 }, st(1, 3, 3), steps)).toEqual({ pos: { k: 1, step: 0 }, cmd: { send: "goto", n: 1, step: "end" } });
  });
  it("ignores keys until the deck answered", () => {
    expect(next(seq, { k: 0, step: 0 }, null, steps)).toEqual({ pos: { k: 0, step: 0 }, cmd: null });
  });
  it("stays put at the ends", () => {
    expect(prev(seq, { k: 0, step: 0 }, st(0, 0, 1), steps).cmd).toEqual(null);
    expect(next(seq, { k: 3, step: 0 }, st(2, 0, 0), steps).cmd).toEqual(null);
  });
  it("goes back from a deck slide onto the atlas slide's last step", () => {
    expect(prev(seq, { k: 3, step: 0 }, st(2, 0, 0), steps)).toEqual({ pos: { k: 2, step: 2 }, cmd: null });
  });
});
