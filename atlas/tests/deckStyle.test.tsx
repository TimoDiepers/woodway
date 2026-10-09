import { render } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { Takeaway } from "@/ui/deck/Takeaway";
import { SourceLine } from "@/ui/deck/SourceLine";

describe("deck style", () => {
  it("renders the takeaway with its chapter", () => {
    const { container } = render(<Takeaway ch="dac">x</Takeaway>);
    const el = container.querySelector(".takeaway")!;
    expect(el).not.toBeNull();
    expect(el.getAttribute("data-ch")).toBe("dac");
    expect(el.textContent).toBe("x");
  });
  it("renders the source line", () => {
    const { container } = render(<SourceLine>y</SourceLine>);
    expect(container.querySelector(".src")?.textContent).toBe("y");
  });
  it("keeps the palette identical to the deck", () => {
    const css = readFileSync(resolve(__dirname, "../src/styles/tokens.css"), "utf8");
    for (const s of ["--paper: #f2ede2", "--moss: #3d552d", "--dac: #9a6516", "--co2: #2e7d4f", "--alb: #c8641a"]) {
      expect(css).toContain(s);
    }
  });
});
