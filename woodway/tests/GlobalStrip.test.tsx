import { act, fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import { GlobalStrip } from "@/ui/GlobalStrip";
import { useAtlas } from "@/store";

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;

describe("GlobalStrip", () => {
  it("names the curves of the deck's anchor and DACCS capacity and cost of the year", async () => {
    const at = await loadAtlas("data/", diskFetch);
    render(<GlobalStrip atlas={at} year={2080} />);
    for (const name of ["Best case scenario (Very Low, without its own removal)", "+ trees", "+ vegan world", "+ DACCS", "+ vegan world + DACCS"])
      expect(screen.getByText(name)).toBeInTheDocument();
    const d = at.meta.global.dac["20"], k = at.meta.global.years.indexOf(2080);
    expect(screen.getByText(`DACCS ${d.capGt[k].toFixed(1)} Gt/a · ${d.costMed[k].toFixed(1)} tn €/a`)).toBeInTheDocument();
  });
  it("shows two decimals below 1 Gt/a instead of 0.0", async () => {
    const at = await loadAtlas("data/", diskFetch);
    render(<GlobalStrip atlas={at} year={2050} />);
    const d = at.meta.global.dac["20"], v = d.capGt[24];
    expect(v).toBeLessThan(1);
    expect(screen.getByText(new RegExp(`^DACCS ${v.toFixed(2)} Gt/a`))).toBeInTheDocument();
  });
  it("switches the DACCS build-out limit; the vegan world with DACCS only at 20 %/a", async () => {
    const at = await loadAtlas("data/", diskFetch);
    render(<GlobalStrip atlas={at} year={2050} />);
    fireEvent.click(screen.getByRole("button", { name: "50 %/a" }));
    expect(screen.getByRole("button", { name: "50 %/a" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByText("+ vegan world + DACCS")).not.toBeInTheDocument();
    const d = at.meta.global.dac["50"];
    expect(screen.getByText(new RegExp(`^DACCS ${d.capGt[24].toFixed(1)} Gt/a`))).toBeInTheDocument();
    expect(screen.getByText(new RegExp(`build-out at most 50 %/a, back to 1.5 °C as early as possible \\(${d.back}\\)`))).toBeInTheDocument();
  });
  it("names the rules behind the curves, with the model's numbers", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const g = at.meta.global;
    render(<GlobalStrip atlas={at} year={2080} />);
    const area = g.areasGha.kuehlt.toFixed(2), year = g.plantYear;
    expect(area).toBe("0.47");
    expect(screen.getByText(new RegExp(`^Trees: forest on the ${area} Gha that cool, all planted in ${year}, not harvested. Vegan world from ${year}: .* forest on ${g.vegan.freeGha.toFixed(2)} Gha`))).toBeInTheDocument();
    act(() => useAtlas.getState().setLang("de"));
    expect(screen.getByText(/^Bäume: Wald auf den 0,47 Gha, die kühlen, alle 2026 gepflanzt, ohne Nutzung\. .*zurück auf 1,5 °C \(2083\)/)).toBeInTheDocument();
    act(() => useAtlas.getState().setLang("en"));
  });
});
