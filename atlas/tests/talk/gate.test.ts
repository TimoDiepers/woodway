import { CmdGate } from "@/talk/gate";

const st = (i: number) => ({ i, step: 0, ni: i, ns: 1 });

describe("CmdGate", () => {
  it("lets one command through until the deck answered", () => {
    let t = 0;
    const g = new CmdGate(() => t);
    expect(g.busy()).toBe(false);
    g.begin({ send: "next" });
    t = 10;
    expect(g.busy()).toBe(true);
    expect(g.accept(st(1))).toBe(true);
    expect(g.busy()).toBe(false);
  });
  it("frees itself when a reply is lost", () => {
    let t = 0;
    const g = new CmdGate(() => t, 300);
    g.begin({ send: "next" });
    t = 301;
    expect(g.busy()).toBe(false);
  });
  it("ignores a late reply to an older command after a goto", () => {
    const g = new CmdGate(() => 0);
    g.begin({ send: "goto", n: 5, step: 0 });
    expect(g.accept(st(2))).toBe(false);
    expect(g.busy()).toBe(true);
    expect(g.accept(st(5))).toBe(true);
    expect(g.busy()).toBe(false);
  });
});
