import { render } from "@testing-library/react";
import { forwardRef, type ReactNode } from "react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import { layerById } from "@/model/layers";
import { cellAt } from "@/map/lookup";

// maplibre needs WebGL; the test drives the map's event props directly.
const props: { current: Record<string, (e?: unknown) => void> } = { current: {} };
vi.mock("react-map-gl/maplibre", () => ({
  default: forwardRef((p: Record<string, unknown> & { children?: ReactNode }, _ref) => {
    props.current = p as never;
    return <div data-testid="map">{p.children}</div>;
  }),
  Marker: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Source: ({ children }: { children: ReactNode }) => <>{children}</>,
  Layer: () => null,
}));
vi.mock("@/map/Borders", () => ({ default: () => null }));

import AtlasMap from "@/map/AtlasMap";

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, path.basename(u))))) as unknown as typeof fetch;
const AACHEN = { lng: 6.08, lat: 50.78 };

describe("AtlasMap", () => {
  it("clears the hover readout when the map starts to move (a site jump)", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const onHover = vi.fn();
    render(<AtlasMap atlas={at} layer={layerById("deltaT")} year={2100} cell={null} onCell={() => {}} onHover={onHover} />);
    props.current.onMouseMove({ lngLat: { ...AACHEN, wrap: () => AACHEN }, point: { x: 10, y: 20 } });
    expect(onHover).toHaveBeenLastCalledWith(cellAt(AACHEN.lng, AACHEN.lat), 10, 20);
    props.current.onMoveStart?.();
    expect(onHover).toHaveBeenLastCalledWith(null, 0, 0);
  });
  it("wraps longitudes from a globe spun past the date line", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const onCell = vi.fn();
    render(<AtlasMap atlas={at} layer={layerById("deltaT")} year={2100} cell={null} onCell={onCell} />);
    props.current.onClick({ lngLat: { lng: AACHEN.lng + 360, lat: AACHEN.lat, wrap: () => AACHEN } });
    expect(onCell).toHaveBeenLastCalledWith(cellAt(AACHEN.lng, AACHEN.lat));
  });
  it("site markers are ringed in theme colours, not fixed white", async () => {
    const at = await loadAtlas("data/", diskFetch);
    const { container } = render(<AtlasMap atlas={at} layer={layerById("deltaT")} year={2100} cell={null} onCell={() => {}} sites={at.meta.sites} />);
    const dots = container.querySelectorAll("span[title]");
    expect(dots.length).toBe(3);
    for (const d of dots) {
      expect(d.className).not.toMatch(/border-white/);
      expect(d.className).toMatch(/border-paper/);
    }
  });
});
