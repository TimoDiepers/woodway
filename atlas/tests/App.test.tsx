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
    await userEvent.click(screen.getByRole("radio", { name: "Sunlight at the ground" }));
    expect(screen.getByRole("slider")).toBeInTheDocument();
    expect(screen.getByText("Warming above 1.5 °C, worldwide")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("radio", { name: "Temperature effect of one tree" }));
  });
  it("legend names every grey: unmeasured albedo, and both reasons of the build-out", async () => {
    render(<App />);
    await screen.findByTestId("map");
    await userEvent.click(screen.getByRole("radio", { name: "Sunlight at the ground" }));
    expect(screen.getByText("reforestable, not measured locally")).toBeInTheDocument();
    expect(screen.getByText("no room for trees")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("radio", { name: "DAC build-out" }));
    expect(screen.getByText("no DAC built here")).toBeInTheDocument();
    expect(screen.getByText("too cold for sorbent DAC")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("radio", { name: "Temperature effect of one tree" }));
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
    expect(map.props.flyTo).toEqual({ lon: 13.3888599, lat: 52.5170365 });
    act(() => useAtlas.getState().setCell(null));
  });
});

describe("layer list keyboard", () => {
  it("arrow keys move the selection and focus, only the checked option is a tab stop", async () => {
    render(<App />);
    await screen.findByTestId("map");
    const cur = screen.getByRole("radio", { name: "Temperature effect of one tree" });
    expect(cur).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("radio", { name: "Sunlight at the ground" })).toHaveAttribute("tabindex", "-1");
    cur.focus();
    await userEvent.keyboard("{ArrowDown}");
    const next = screen.getByRole("radio", { name: "Net share after albedo" });
    expect(next).toHaveAttribute("aria-checked", "true");
    expect(next).toHaveFocus();
  });
});
