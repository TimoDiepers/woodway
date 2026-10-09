import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync } from "node:fs";
import path from "node:path";

vi.mock("@/map/AtlasMap", () => ({ default: () => <div data-testid="map" /> }));
const DIR = path.resolve(__dirname, "../public/data/");
globalThis.fetch = (async (url: string) => new Response(readFileSync(path.join(DIR, path.basename(String(url)))))) as unknown as typeof fetch;

import App from "@/App";

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
