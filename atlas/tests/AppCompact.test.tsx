import { act, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import path from "node:path";

const map = vi.hoisted(() => ({ props: {} as Record<string, unknown> }));
vi.mock("@/map/AtlasMap", () => ({ default: (p: Record<string, unknown>) => { map.props = p; return <div data-testid="map" />; } }));
const DIR = path.resolve(__dirname, "../public/data/");
globalThis.fetch = (async (url: string) => new Response(readFileSync(path.join(DIR, path.basename(String(url)))))) as unknown as typeof fetch;

import App from "@/App";
import { useAtlas } from "@/store";
import { cellAt } from "@/map/lookup";

const insets = () => map.props.insets as { top: number; bottom: number; right?: number };

describe("App on a phone", () => {
  beforeAll(() => { window.innerWidth = 390; window.innerHeight = 844; });
  afterAll(() => { window.innerWidth = 1024; window.innerHeight = 768; });
  afterEach(() => act(() => useAtlas.getState().setCell(null)));

  it("has a compact bar with round controls and keeps legend and year in the sheet's peek", async () => {
    render(<App />);
    await screen.findByTestId("map");
    expect(screen.getByRole("button", { name: "Deutsch" })).toHaveTextContent("DE");
    expect(screen.queryByText("The talk's model, cell by cell · 2026–2100")).toBeNull();   // no subtitle on a phone
    expect(screen.getByRole("slider")).toBeInTheDocument();
    expect(screen.getAllByText("Temperature effect of one tree").length).toBeGreaterThan(0);
    // the camera centres in the free part of the screen: below the bar, above the peek
    expect(insets().top).toBeGreaterThan(0);
    expect(insets().bottom).toBeGreaterThanOrEqual(120);
  });

  it("a tapped cell opens its panel, lifts the sheet and brings the cell into view without zooming", async () => {
    render(<App />);
    await screen.findByTestId("map");
    const before = insets().bottom;
    const aachen = cellAt(6.08, 50.78)!;
    act(() => (map.props.onCell as (c: number) => void)(aachen));
    expect(await screen.findByText(/Cools the climate|Does not cool|Cools the climate until/)).toBeInTheDocument();
    expect(insets().bottom).toBeGreaterThan(before);
    const jump = map.props.flyTo as { lon: number; lat: number; zoom?: number };
    expect(jump.zoom).toBeUndefined();
    expect(Math.abs(jump.lat - 50.78)).toBeLessThan(0.5);
  });

  it("closing the cell drops the sheet back to its peek", async () => {
    render(<App />);
    await screen.findByTestId("map");
    const peek = insets().bottom;
    act(() => (map.props.onCell as (c: number) => void)(cellAt(6.08, 50.78)!));
    act(() => (map.props.onCell as (c: number | null) => void)(null));
    expect(insets().bottom).toBe(peek);
  });
});
