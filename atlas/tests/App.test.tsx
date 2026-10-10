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
    await userEvent.click(screen.getByRole("button", { name: "Deutsch" }));
    expect(screen.getAllByText("Temperaturwirkung eines Baums").length).toBeGreaterThan(0);
    await userEvent.click(screen.getByRole("button", { name: "English" }));
  });
  it("static layers keep the slider for the global strip", async () => {
    render(<App />);
    await screen.findByTestId("map");
    await pickLayer("Solar radiation at the ground");
    expect(screen.getByRole("slider")).toBeInTheDocument();
    expect(screen.getByText("Warming above 1.5 °C, worldwide")).toBeInTheDocument();
    await pickLayer("Temperature effect of one tree");
  });
  it("legend names every grey: unmeasured albedo, and both reasons of the build-out", async () => {
    render(<App />);
    await screen.findByTestId("map");
    await pickLayer("Solar radiation at the ground");
    expect(screen.getByText("reforestable, not measured locally")).toBeInTheDocument();
    expect(screen.getByText("no room for trees")).toBeInTheDocument();
    await pickLayer("DAC build-out");
    expect(screen.getByText("no DAC built here")).toBeInTheDocument();
    expect(screen.getByText("too cold for sorbent DAC")).toBeInTheDocument();
    await pickLayer("Temperature effect of one tree");
  });
});

describe("projection", () => {
  it("toggles between globe and flat map, passes it to the map and remembers it", async () => {
    render(<App />);
    await screen.findByTestId("map");
    expect(map.props.projection).toBe("globe");
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
    await userEvent.type(screen.getByRole("searchbox", { name: "Search a place" }), "Berlin{Enter}");
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
