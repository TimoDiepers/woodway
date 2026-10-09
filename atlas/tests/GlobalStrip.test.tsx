import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import { GlobalStrip } from "@/ui/GlobalStrip";

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;

describe("GlobalStrip", () => {
  it("names the three curves and the DAC capacity of the year", async () => {
    const at = await loadAtlas("data/", diskFetch);
    render(<GlobalStrip atlas={at} year={2080} />);
    expect(screen.getByText("Very Low scenario")).toBeInTheDocument();
    expect(screen.getByText("with the trees")).toBeInTheDocument();
    expect(screen.getByText("with trees and DAC")).toBeInTheDocument();
    const k = at.meta.global.years.indexOf(2080);
    const gt = at.meta.global.dacCapacityGt[k].toFixed(1);
    expect(screen.getByText(`DAC capacity ${gt} Gt/a`)).toBeInTheDocument();
  });
});
