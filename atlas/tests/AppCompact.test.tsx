import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync } from "node:fs";
import path from "node:path";

const map = vi.hoisted(() => ({ props: {} as Record<string, unknown> }));
vi.mock("@/map/AtlasMap", () => ({ default: (p: Record<string, unknown>) => { map.props = p; return <div data-testid="map" />; } }));
const DIR = path.resolve(__dirname, "../public/data/");
const BERLIN = [{ display_name: "Berlin, Deutschland", lat: "52.5170365", lon: "13.3888599" }];
globalThis.fetch = (async (url: string) =>
  String(url).startsWith("https://nominatim.openstreetmap.org/")
    ? new Response(JSON.stringify(BERLIN))
    : new Response(readFileSync(path.join(DIR, path.basename(String(url)))))) as unknown as typeof fetch;

import App from "@/App";
import { useAtlas } from "@/store";
import { cellAt } from "@/map/lookup";

const insets = () => map.props.insets as { top: number; bottom: number; right?: number };
const tap = (c: number | null) => act(() => (map.props.onCell as (c: number | null) => void)(c));
const AACHEN = () => cellAt(6.08, 50.78)!;

describe("App on a phone", () => {
  beforeAll(() => { window.innerWidth = 390; window.innerHeight = 844; });
  afterAll(() => { window.innerWidth = 1024; window.innerHeight = 768; });
  beforeEach(() => { localStorage.clear(); act(() => useAtlas.getState().resetHints()); });
  afterEach(() => act(() => useAtlas.getState().setCell(null)));

  it("floats one dock at the bottom with the layer dropdown and the year, the legend top left, the tools on the right", async () => {
    render(<App />);
    await screen.findByTestId("map");
    const dock = screen.getByRole("group", { name: "Map settings" });
    expect(within(dock).getByRole("combobox", { name: "Layer" })).toBeInTheDocument();
    expect(within(dock).getByRole("slider")).toBeInTheDocument();
    const plate = screen.getByRole("banner");
    expect(within(plate).getByRole("figure", { name: "Temperature effect of one tree" })).toBeInTheDocument();
    const tools = screen.getByRole("toolbar", { name: "Map tools" });
    for (const name of ["Search a place", "Back to the whole world", "Overview", "How to read this map", "Deutsch", "Flat map"])
      expect(within(tools).getByRole("button", { name })).toBeInTheDocument();
    expect(insets().right).toBeGreaterThan(0);          // the globe centres left of the tool column
    expect(insets().bottom).toBeGreaterThan(0);         // … and above the dock
  });

  it("no detail panel until a cell is tapped; then it opens, keeps the year at hand, and closes again", async () => {
    render(<App />);
    await screen.findByTestId("map");
    expect(screen.queryByRole("region", { name: "Cell details" })).toBeNull();
    const before = insets().bottom;
    tap(AACHEN());
    const sheet = screen.getByRole("region", { name: "Cell details" });
    expect(within(sheet).getByText(/Cools the climate|Does not cool|Cools the climate until/)).toBeInTheDocument();
    expect(screen.getByRole("slider")).toBeInTheDocument();
    expect(insets().bottom).toBeGreaterThan(before);
    const jump = map.props.flyTo as { lon: number; lat: number; zoom?: number };
    expect(jump.zoom).toBeUndefined();
    expect(map.props.cell).toBe(AACHEN());               // the map fades the other cells
    await userEvent.click(within(sheet).getByRole("button", { name: "Close" }));
    expect(screen.queryByRole("region", { name: "Cell details" })).toBeNull();
    expect(map.props.cell).toBeNull();
  });

  it("a tap on the ocean closes the detail panel", async () => {
    render(<App />);
    await screen.findByTestId("map");
    tap(AACHEN());
    tap(null);
    expect(screen.queryByRole("region", { name: "Cell details" })).toBeNull();
  });

  it("search opens from the tool column and jumps to the place", async () => {
    render(<App />);
    await screen.findByTestId("map");
    expect(screen.queryByRole("searchbox")).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: "Search a place" }));
    const box = await screen.findByRole("searchbox", { name: "Search a place" });
    expect(box).toHaveFocus();
    await userEvent.type(box, "Berlin{Enter}");
    await userEvent.click(await screen.findByRole("button", { name: "Berlin, Deutschland" }));
    expect(useAtlas.getState().cell).toBe(cellAt(13.3888599, 52.5170365));
    expect(map.props.flyTo).toEqual({ lon: 13.3888599, lat: 52.5170365, zoom: 4 });
    expect(screen.queryByRole("searchbox")).toBeNull();
  });

  it("recenter flies back to the whole world and closes the cell", async () => {
    render(<App />);
    await screen.findByTestId("map");
    tap(AACHEN());
    await userEvent.click(screen.getByRole("button", { name: "Back to the whole world" }));
    expect(map.props.flyTo).toMatchObject({ lon: 10, lat: 25 });
    expect(useAtlas.getState().cell).toBeNull();
  });

  it("the overview holds the worldwide result and the example places", async () => {
    render(<App />);
    await screen.findByTestId("map");
    expect(screen.queryByText("Warming above 1.5 °C, worldwide")).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: "Overview" }));
    const panel = await screen.findByRole("dialog", { name: "Overview" });
    expect(within(panel).getByText("Warming above 1.5 °C, worldwide")).toBeInTheDocument();
    await userEvent.click(within(panel).getByRole("button", { name: /Aachen/ }));
    expect(screen.queryByRole("dialog", { name: "Overview" })).toBeNull();
    expect(screen.getByRole("region", { name: "Cell details" })).toBeInTheDocument();
  });

  it("a first-visit hint says what to do, retires after the first cell and comes back from the help panel", async () => {
    render(<App />);
    await screen.findByTestId("map");
    expect(screen.getByText("Tap a cell to read its century.")).toBeInTheDocument();
    tap(AACHEN());
    tap(null);
    expect(screen.queryByText("Tap a cell to read its century.")).toBeNull();
    expect(localStorage.getItem("atlas-hints")).toBe("seen");
    await userEvent.click(screen.getByRole("button", { name: "How to read this map" }));
    const help = await screen.findByRole("dialog", { name: "How to read this map" });
    expect(within(help).getByText("The colours")).toBeInTheDocument();
    expect(within(help).getByText("Grey cells")).toBeInTheDocument();
    await userEvent.click(within(help).getByRole("button", { name: "Show the first-visit hint again" }));
    expect(screen.getByText("Tap a cell to read its century.")).toBeInTheDocument();
  });

  it("a static layer's dock has no slider", async () => {
    render(<App />);
    await screen.findByTestId("map");
    act(() => useAtlas.getState().setLayer("sun"));
    expect(screen.queryByRole("slider")).toBeNull();
    act(() => useAtlas.getState().setLayer("deltaT"));
    expect(screen.getByRole("slider")).toBeInTheDocument();
  });
});
