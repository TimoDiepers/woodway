import { act, render, screen } from "@testing-library/react";
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

/** The layer dropdown: open it, pick an option by its name. */
async function pickLayer(name: string) {
  await userEvent.click(screen.getByRole("combobox", { name: "Layer" }));
  await userEvent.click(await screen.findByRole("option", { name }));
}
import { useAtlas } from "@/store";
import { cellAt } from "@/map/lookup";

describe("App", () => {
  it("shows the map, the layer list and the legend", async () => {
    render(<App />);
    expect(await screen.findByTestId("map")).toBeInTheDocument();
    expect(screen.getAllByText("Temperature effect of one tree").length).toBeGreaterThan(0);
    expect(screen.getByText(/FaIR/)).toBeInTheDocument();
  });
  it("language switch relabels the legend", async () => {
    render(<App />);
    await screen.findByTestId("map");
    await userEvent.click(screen.getByRole("button", { name: "More" }));
    await userEvent.click(screen.getByRole("button", { name: "Deutsch" }));
    expect(screen.getAllByText("Temperaturwirkung eines Baums").length).toBeGreaterThan(0);
    await userEvent.click(screen.getByRole("button", { name: "English" }));
  });
  it("layers that do not change over time have no year slider; timed ones do", async () => {
    render(<App />);
    await screen.findByTestId("map");
    expect(screen.getByRole("slider")).toBeInTheDocument();             // ΔT per tree: timed
    act(() => useAtlas.getState().setPlaying(true));
    await pickLayer("Solar radiation at the ground");
    expect(screen.queryByRole("slider")).toBeNull();
    expect(useAtlas.getState().playing).toBe(false);                     // nothing left to play
    await pickLayer("DAC net share");
    expect(screen.getByRole("slider")).toBeInTheDocument();
    await pickLayer("Temperature effect of one tree");
  });
  it("legend names every grey: unmeasured albedo, and both reasons of the build-out", async () => {
    render(<App />);
    await screen.findByTestId("map");
    await pickLayer("Solar radiation at the ground");
    expect(screen.getByText("reforestable, not measured locally")).toBeInTheDocument();
    expect(screen.getByText("no room for trees")).toBeInTheDocument();
    await pickLayer("DACCS build-out");
    expect(screen.getByText("no DACCS built here")).toBeInTheDocument();
    expect(screen.getByText("too cold for sorbent DAC")).toBeInTheDocument();
    await pickLayer("Temperature effect of one tree");
  });
});

describe("desktop layout", () => {
  it("the same pieces as on a phone: legend plate, tool row, one dock; details only after a click", async () => {
    render(<App />);
    await screen.findByTestId("map");
    expect(screen.getByRole("toolbar", { name: "Map tools" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Map settings" })).toBeInTheDocument();
    expect(screen.getByText("Click a cell to read its century.")).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Cell details" })).toBeNull();
    act(() => (map.props.onCell as (c: number) => void)(cellAt(6.08, 50.78)!));
    expect(screen.getByRole("region", { name: "Cell details" })).toBeInTheDocument();
    expect(map.props.cell).toBe(cellAt(6.08, 50.78));
    act(() => useAtlas.getState().setCell(null));
  });
  it("a condition row in the details switches the map's layer", async () => {
    render(<App />);
    await screen.findByTestId("map");
    act(() => (map.props.onCell as (c: number) => void)(cellAt(6.08, 50.78)!));
    await userEvent.click(screen.getByRole("button", { name: /^Solar radiation at the ground:/ }));
    expect(useAtlas.getState().layer).toBe("sun");
    expect(screen.queryByRole("slider")).toBeNull();          // a static layer: the dock is the dropdown alone
    act(() => { useAtlas.getState().setLayer("deltaT"); useAtlas.getState().setCell(null); });
  });
});

describe("projection", () => {
  it("picks globe or flat map in More, passes it to the map and remembers it, passes it to the map and remembers it", async () => {
    render(<App />);
    await screen.findByTestId("map");
    expect(map.props.projection).toBe("globe");
    await userEvent.click(screen.getByRole("button", { name: "More" }));
    expect(screen.getByRole("button", { name: "Globe" })).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(screen.getByRole("button", { name: "Flat map" }));
    expect(map.props.projection).toBe("mercator");
    expect(localStorage.getItem("atlas-projection")).toBe("mercator");
    await userEvent.click(screen.getByRole("button", { name: "Globe" }));
    expect(map.props.projection).toBe("globe");
    expect(localStorage.getItem("atlas-projection")).toBe("globe");
    act(() => useAtlas.getState().setLang("de"));
    expect(screen.getByRole("button", { name: "Karte" })).toBeInTheDocument();
    act(() => useAtlas.getState().setLang("en"));
  });
});

describe("place search", () => {
  it("picking a result selects its cell and flies there", async () => {
    render(<App />);
    await screen.findByTestId("map");
    await userEvent.click(screen.getByRole("button", { name: "Search a place" }));
    await userEvent.type(await screen.findByRole("searchbox", { name: "Search a place" }), "Berlin{Enter}");
    await userEvent.click(await screen.findByRole("button", { name: "Berlin, Deutschland" }));
    expect(useAtlas.getState().cell).toBe(cellAt(13.3888599, 52.5170365));
    expect(map.props.flyTo).toEqual({ lon: 13.3888599, lat: 52.5170365, zoom: 4 });
    act(() => useAtlas.getState().setCell(null));
  });
});

describe("layer dropdown", () => {
  it("shows the current layer and offers every layer in two sections, trees and DAC", async () => {
    render(<App />);
    await screen.findByTestId("map");
    const box = screen.getByRole("combobox", { name: "Layer" });
    expect(box).toHaveTextContent("Temperature effect of one tree");
    expect(screen.queryByRole("radio")).toBeNull();          // no long list any more
    await userEvent.click(box);
    expect(await screen.findByText("Trees")).toBeInTheDocument();
    expect(screen.getByText("Direct air capture")).toBeInTheDocument();
    expect(screen.getAllByRole("option")).toHaveLength(10);
    await userEvent.click(screen.getByRole("option", { name: "DAC net share" }));
    expect(useAtlas.getState().layer).toBe("dacNet");
    expect(screen.getByRole("combobox", { name: "Layer" })).toHaveTextContent("DAC net share");
    await pickLayer("Temperature effect of one tree");
  });
  it("works with the keyboard", async () => {
    render(<App />);
    await screen.findByTestId("map");
    screen.getByRole("combobox", { name: "Layer" }).focus();
    await userEvent.keyboard("{Enter}");
    await screen.findAllByRole("option");
    await userEvent.keyboard("{ArrowDown}{Enter}");
    expect(useAtlas.getState().layer).toBe("netShare");
    act(() => useAtlas.getState().setLayer("deltaT"));
  });
});
