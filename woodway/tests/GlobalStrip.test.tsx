import { act, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import { GlobalStrip } from "@/ui/GlobalStrip";
import { useAtlas } from "@/store";

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;

describe("GlobalStrip", () => {
  it("names the three curves and the DAC capacity of the year", async () => {
    const at = await loadAtlas("data/", diskFetch);
    render(<GlobalStrip atlas={at} year={2035} />);
    expect(screen.getByText("Very Low scenario")).toBeInTheDocument();
    expect(screen.getByText("with the trees")).toBeInTheDocument();
    expect(screen.getByText("with trees and DACCS")).toBeInTheDocument();
    const k = at.meta.global.years.indexOf(2035);
    const v = at.meta.global.dacCapacityGt[k];
    const gt = v.toFixed(v < 1 ? 2 : 1);
    expect(screen.getByText(`DACCS capacity ${gt} Gt/a`)).toBeInTheDocument();
  });
  it("shows two decimals below 1 Gt/a instead of 0.0", async () => {
    const at = await loadAtlas("data/", diskFetch);
    render(<GlobalStrip atlas={at} year={2050} />);
    const v = at.meta.global.dacCapacityGt[24];
    expect(v).toBeLessThan(1);
    expect(screen.getByText(`DACCS capacity ${v.toFixed(2)} Gt/a`)).toBeInTheDocument();
  });
  it("names the rules behind the curves, with the model's numbers", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const g = at.meta.global;
    render(<GlobalStrip atlas={at} year={2080} />);
    const area = g.areasGha.kuehlt.toFixed(2), year = g.plantYear;
    expect(area).toBe("0.39");
    expect(screen.getByText(`With the trees: managed forest on the ${area} Gha that cool, all planted in ${year}, timber kept; DACCS: cost-optimal, build-out at most 20 %/a, back to 1.5 °C as early as possible.`)).toBeInTheDocument();
    act(() => useAtlas.getState().setLang("de"));
    expect(screen.getByText(/^Mit den Bäumen: bewirtschafteter Wald auf den 0,39 Gha, die kühlen, alle 2026 gepflanzt, .*zurück auf 1,5 °C\.$/)).toBeInTheDocument();
    act(() => useAtlas.getState().setLang("en"));
  });
});
