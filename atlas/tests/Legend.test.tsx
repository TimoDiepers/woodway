import { render } from "@testing-library/react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import type { Atlas } from "@/data/types";
import { layerById } from "@/model/layers";
import { Legend } from "@/ui/Legend";

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;
let at: Atlas;
beforeAll(async () => { at = await loadAtlas("data/", diskFetch); });

describe("Legend", () => {
  it("writes negative ticks with the true minus sign", () => {
    const { container } = render(<Legend atlas={at} layer={layerById("deltaT")} />);
    const ticks = [...container.querySelectorAll(".tabular-nums span")].map((s) => s.textContent);
    expect(ticks[0]).toBe("−90");
    expect(ticks.join(" ")).not.toMatch(/-/);
  });
  it("puts a short unit on the line of the ticks", () => {
    const { container } = render(<Legend atlas={at} layer={layerById("dacNet")} />);
    const row = container.querySelector(".tabular-nums")!;
    expect(row.textContent).toContain("%");
  });
});
