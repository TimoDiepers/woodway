import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import type { Atlas } from "@/data/types";

const seen = vi.hoisted(() => ({ year: 0 }));
vi.mock("@/map/AtlasMap", () => ({ default: (p: { year: number }) => { seen.year = p.year; return <div data-testid="map" />; } }));
import AtlasSlide from "@/talk/AtlasSlide";
import { SLIDES, atlasSteps, talkLayer } from "@/talk/slides";
import { scaleOf } from "@/model/layers";
import { hexToRgba, scaleColor } from "@/color/scale";
import { buildP95 } from "@/talk/stats";

const DIR = path.resolve(__dirname, "../../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;
let at: Atlas;
beforeAll(async () => { at = await loadAtlas("data/", diskFetch); });

describe("AtlasSlide", () => {
  it("shows title, a percentage takeaway and the source line", () => {
    const { container } = render(<AtlasSlide def={SLIDES.jedeZelle} atlas={at} step={0} />);
    expect(screen.getByRole("heading", { name: "Temperaturwirkung eines Baums je Zelle, 2030–2100" })).toBeTruthy();
    expect(container.querySelector(".takeaway")!.textContent).toMatch(/^2030: Ein Baum kühlt auf \d+ % der wiederbewaldbaren Fläche\. Die Albedo wirkt erst mit dem Kronenschluss\.$/);
    expect(container.querySelector(".src")).toBeTruthy();
    expect(screen.getByTestId("map")).toBeTruthy();
  });
  it("names the year of the step and drops the canopy remark from 2050 on", () => {
    const { container } = render(<AtlasSlide def={SLIDES.jedeZelle} atlas={at} step={2} />);
    expect(container.querySelector(".takeaway")!.textContent).toMatch(/^2100: Ein Baum kühlt auf \d+ % der wiederbewaldbaren Fläche\.$/);
  });
  it("titles describe the content", () => {
    expect(SLIDES.albedo.title).toBe("Netto-Anteil nach Albedo je Zelle, 2100");
    expect(SLIDES.dacStrom.title).toBe("Netto-Anteil von DAC je Zelle, 2026–2070");
    expect(SLIDES.dacAusbau.title).toBe("DACCS-Ausbau je Zelle, 2026–2100");
    expect(SLIDES.atlas.title).toBe("Atlas");
  });
  it("albedo slide states only the areas, as the deck does", () => {
    const { container } = render(<AtlasSlide def={SLIDES.albedo} atlas={at} step={0} />);
    expect(container.querySelector(".takeaway")!.textContent).toBe("Bäume kühlen 2100 auf 0,47 von 0,83 Gha wiederbewaldbarer Fläche; auf dem Rest überwiegt die Albedo.");
  });
  it("DAC slides name the median over the land area and the capacity", () => {
    const a = render(<AtlasSlide def={SLIDES.dacStrom} atlas={at} step={1} />);
    expect(a.container.querySelector(".takeaway")!.textContent).toBe("2040: Im Median über die Landfläche bleiben 91 % jeder entnommenen Tonne netto.");
    a.unmount();
    const b = render(<AtlasSlide def={SLIDES.dacAusbau} atlas={at} step={1} />);
    expect(b.container.querySelector(".takeaway")!.textContent).toMatch(/^[\d,.]+ Gt CO₂ pro Jahr um 2081, kostenoptimal bei höchstens 20 % Ausbau im Jahr, um ab 2084 bei 1,5 °C zu sein; die Kapazität je Land ist auf Zellen nahe Sedimentbecken mit dem höchsten Netto-Anteil verteilt\.$/);
  });
  it("sources name the storage and the forest-type paper", () => {
    expect(SLIDES.dacAusbau.source).toContain("Speicher Gidden et al. 2025");
    expect(SLIDES.jedeZelle.source).toContain("Waldtyp: Hasler et al. 2024");
  });
  it("DAC build-out map uses a scale fitted to the built cells, with the greys kept apart", () => {
    const layer = talkLayer(SLIDES.dacAusbau, at);
    const sc = scaleOf(at, layer)!;
    expect(sc.domain[1]).toBe(buildP95(at, 2030));
    const lum = ([r, g, b]: number[]) => 0.3 * r + 0.59 * g + 0.11 * b;
    const low = lum(scaleColor(sc, 0.01 * sc.domain[1]));
    expect(lum(hexToRgba(at.meta.colors.tooCold)) - low).toBeGreaterThan(40);   // even the smallest capacity stands out from land and "too cold"
    expect(at.meta.colors.tooCold).not.toBe(at.meta.colors.land);
    expect(layer.greys).toContain("reason.tooCold");
    expect(talkLayer(SLIDES.dacAusbau, at)).toBe(layer);   // stable, so the map does not repaint
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
