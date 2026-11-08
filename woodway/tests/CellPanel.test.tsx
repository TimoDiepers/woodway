import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { cloneElement, type ReactElement } from "react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import { CellPanel } from "@/ui/CellPanel";
import { coolsFrom, coolsUntil, dacBuildMt, deltaT, netShare, typeKey } from "@/model/model";
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
    expect(screen.getByRole("button", { name: /^Electricity.*MWh\/t/ })).toBeInTheDocument();
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
    expect(screen.getByText(`Cools the climate until ${coolsUntil(at, cell)}, then warms: albedo and clouds outweigh the CO₂`)).toBeInTheDocument();
  });
  it("keeps every curve after a language switch", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const r = at.meta.reference[0];
    const { container } = render(<CellPanel atlas={at} cell={r.i * 720 + r.j} year={2050} onClose={() => {}} />);
    expect(drawn(container)).toBe(6);   // ΔT here (Aachen) and at the two other places; CO₂ and albedo forcing; carbon
    act(() => useAtlas.getState().setLang("de"));
    expect(screen.getByText("Kohlenstoff in einem Baum [kg C]")).toBeInTheDocument();
    expect(drawn(container)).toBe(6);
    act(() => useAtlas.getState().setLang("en"));
    expect(drawn(container)).toBe(6);
  });
  it("states the DAC build-out as the country's capacity spread over its best cells", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const k = at.meta.build.cells.findIndex(([i, j]) => dacBuildMt(at, i * 720 + j, 2035) > 0);
    const [i, j] = at.meta.build.cells[k];
    const cell = i * 720 + j;
    const mt = dacBuildMt(at, cell, 2035);
    expect(mt).toBeGreaterThan(0);
    render(<CellPanel atlas={at} cell={cell} year={2035} onClose={() => {}} />);
    expect(screen.getByText(`${mt.toFixed(1)} Mt CO₂/a capacity here in 2035 (the country's capacity spread over its best cells)`)).toBeInTheDocument();
  });

  it("weighs CO₂ against albedo for the year: how much of the CO₂ effect the albedo takes back", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const r = at.meta.reference[0];
    const cell = r.i * 720 + r.j;
    render(<CellPanel atlas={at} cell={cell} year={2100} onClose={() => {}} />);
    const tug = screen.getByRole("figure", { name: "CO₂ against albedo and clouds, 2100" });
    const pct = Math.round((1 - netShare(at, cell, 2100)) * 100);
    expect(within(tug).getByText(`Albedo and clouds take back ${pct} % of the CO₂ effect.`)).toBeInTheDocument();
  });
  it("ranks the cell among all reforestable cells of the world", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const r = at.meta.reference[2];
    const cell = r.i * 720 + r.j;
    const here = deltaT(at, cell, 2050);
    let n = 0, weaker = 0;
    for (let c = 0; c < at.f.type.length; c++) if (typeKey(at, c)) { n++; if (deltaT(at, c, 2050) > here) weaker++; }
    render(<CellPanel atlas={at} cell={cell} year={2050} onClose={() => {}} />);
    const rank = screen.getByRole("figure", { name: "Among the world's reforestable cells, 2050" });
    expect(within(rank).getByText(`Cools more than ${Math.floor((100 * weaker) / n)} % of them`)).toBeInTheDocument();
  });
  it("lists the conditions here; a row shows its layer on the map", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const r = at.meta.reference[0];
    const onLayer = vi.fn();
    render(<CellPanel atlas={at} cell={r.i * 720 + r.j} year={2050} onClose={() => {}} layer="sun" onLayer={onLayer} />);
    const list = screen.getByRole("list", { name: "Conditions here" });
    const sun = within(list).getByRole("button", { name: /^Sunlight.*W\/m²/ });
    expect(sun).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(within(list).getByRole("button", { name: /^Albedo change/ }));
    expect(onLayer).toHaveBeenCalledWith("darker");
  });
});
