import { act, render, screen } from "@testing-library/react";
import { cloneElement, type ReactElement } from "react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import { CellPanel } from "@/ui/CellPanel";
import { coolsFrom, coolsUntil, dacBuildMt, deltaT } from "@/model/model";
import { useAtlas } from "@/store";

// jsdom has no layout: give the charts a fixed size so recharts draws its lines.
vi.mock("recharts", async (orig) => {
  const m = await orig<typeof import("recharts")>();
  return { ...m, ResponsiveContainer: ({ children }: { children: ReactElement }) => cloneElement(children, { width: 360, height: 112 }) };
});

const drawn = (root: HTMLElement) =>
  [...root.querySelectorAll(".recharts-line-curve")].filter((p) => (p.getAttribute("d") ?? "").length > 10).length;

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;

describe("CellPanel", () => {
  it("shows forest type, cooling year and DAC for Aachen", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const r = at.meta.reference[0];
    const cell = r.i * 720 + r.j;
    render(<CellPanel atlas={at} cell={cell} year={2050} onClose={() => {}} />);
    expect(screen.getByText(/Mixed forest|Deciduous|Evergreen|Larch/)).toBeInTheDocument();
    const y = coolsFrom(at, cell);
    expect(screen.getByText(y ? `Cools the climate from ${y} on` : "Does not cool the climate by 2100")).toBeInTheDocument();
    expect(screen.getByText(/MWh electricity per tonne|Too cold for sorbent DAC/)).toBeInTheDocument();
  });
  it("cell without forest says so instead of drawing curves", async () => {
    const at = await loadAtlas("data/", diskFetch);
    let cell = 0;
    while (!(at.f.land[cell] && !at.f.type[cell])) cell++;
    render(<CellPanel atlas={at} cell={cell} year={2050} onClose={() => {}} />);
    expect(screen.getByText("No reforestable land in this cell")).toBeInTheDocument();
  });
  it("a tree that cools and then warms says until when", async () => {
    const at = await loadAtlas("data/", diskFetch);
    let cell = 0;
    while (!(at.f.type[cell] && deltaT(at, cell, 2100) >= 0 && coolsUntil(at, cell) !== null)) cell++;
    render(<CellPanel atlas={at} cell={cell} year={2050} onClose={() => {}} />);
    expect(screen.getByText(`Cools the climate until ${coolsUntil(at, cell)}, then warms: the albedo outweighs the CO₂`)).toBeInTheDocument();
  });
  it("keeps every curve after a language switch", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const r = at.meta.reference[0];
    const { container } = render(<CellPanel atlas={at} cell={r.i * 720 + r.j} year={2050} onClose={() => {}} />);
    expect(drawn(container)).toBe(4);   // carbon; CO₂ and albedo forcing; ΔT
    act(() => useAtlas.getState().setLang("de"));
    expect(screen.getByText("Kohlenstoff in einem Baum [kg C]")).toBeInTheDocument();
    expect(drawn(container)).toBe(4);
    act(() => useAtlas.getState().setLang("en"));
    expect(drawn(container)).toBe(4);
  });
  it("states the DAC build-out as the country's capacity spread over its best cells", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const [i, j] = at.meta.build.cells[0];
    const cell = i * 720 + j;
    const mt = dacBuildMt(at, cell, 2080);
    expect(mt).toBeGreaterThan(0);
    render(<CellPanel atlas={at} cell={cell} year={2080} onClose={() => {}} />);
    expect(screen.getByText(`${mt.toFixed(1)} Mt CO₂/a capacity here in 2080 (the country's capacity spread over its best cells)`)).toBeInTheDocument();
  });
});
