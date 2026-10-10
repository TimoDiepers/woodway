import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import type { Atlas } from "@/data/types";

const seen = vi.hoisted(() => ({ year: 0 }));
vi.mock("@/map/AtlasMap", () => ({ default: (p: { year: number }) => { seen.year = p.year; return <div data-testid="map" />; } }));
import AtlasSlide from "@/talk/AtlasSlide";
import { SLIDES, atlasSteps } from "@/talk/slides";

const DIR = path.resolve(__dirname, "../../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;
let at: Atlas;
beforeAll(async () => { at = await loadAtlas("data/", diskFetch); });

describe("AtlasSlide", () => {
  it("shows title, a percentage takeaway and the source line", () => {
    const { container } = render(<AtlasSlide def={SLIDES.jedeZelle} atlas={at} step={0} />);
    expect(screen.getByRole("heading", { name: "Jede Zelle, jedes Jahr" })).toBeTruthy();
    expect(container.querySelector(".takeaway")!.textContent).toMatch(/\d+\s?%/);
    expect(container.querySelector(".src")).toBeTruthy();
    expect(screen.getByTestId("map")).toBeTruthy();
  });
  it("names the year of the step", () => {
    const { container } = render(<AtlasSlide def={SLIDES.jedeZelle} atlas={at} step={2} />);
    expect(container.querySelector(".takeaway")!.textContent).toContain("2100");
  });
  it("albedo slide gives both area-level shares", () => {
    const { container } = render(<AtlasSlide def={SLIDES.albedo} atlas={at} step={0} />);
    expect(container.querySelector(".takeaway")!.textContent).toMatch(/Wo Bäume kühlen \(0,39 Gha\), bleiben 57 % ihrer CO₂-Wirkung; über alle 0,83 Gha wiederbewaldbarer Fläche nur 12 %\./);
  });
  it("a new slide starts at its own first year, without running there", () => {
    const { rerender, container } = render(<AtlasSlide def={SLIDES.albedo} atlas={at} step={0} />);
    expect(seen.year).toBe(2100);
    rerender(<AtlasSlide def={SLIDES.dacStrom} atlas={at} step={0} />);
    expect(seen.year).toBe(2026);
    expect(container.querySelector(".ryear")!.textContent).toBe("2026");
  });
  it("shows no slide number and no place search on the free slide", () => {
    const { container } = render(<AtlasSlide def={SLIDES.atlas} atlas={at} step={0} />);
    expect(container.querySelector(".num")).toBeNull();
    expect(container.querySelector("input[type=search], input[type=text]")).toBeNull();
  });
  it("counts clicks: years plus the sites click", () => {
    expect(atlasSteps("jedeZelle")).toBe(3);
    expect(atlasSteps("albedo")).toBe(0);
    expect(atlasSteps("dacStrom")).toBe(2);
    expect(atlasSteps("dacAusbau")).toBe(1);
    expect(atlasSteps("atlas")).toBe(0);
  });
});
