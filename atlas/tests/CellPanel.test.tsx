import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import { CellPanel } from "@/ui/CellPanel";
import { coolsFrom, coolsUntil, deltaT } from "@/model/model";

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
});
