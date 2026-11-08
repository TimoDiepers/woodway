import { render } from "@testing-library/react";
import { forwardRef, type ReactNode } from "react";
import { readFileSync } from "node:fs";
import path from "node:path";
import { loadAtlas } from "@/data/load";
import { layerById } from "@/model/layers";
import { cellAt } from "@/map/lookup";

// maplibre needs WebGL; the test drives the map's event props directly.
const props: { current: Record<string, (e?: unknown) => void> } = { current: {} };
// a stand-in for maplibre's image source: a new one after every style change
const fake = vi.hoisted(() => ({
  source: null as null | { setCoordinates: ReturnType<typeof vi.fn>; play: ReturnType<typeof vi.fn>; pause: ReturnType<typeof vi.fn> },
  sourceProps: {} as Record<string, unknown>,
}));
vi.mock("react-map-gl/maplibre", async () => {
  const { useImperativeHandle } = await import("react");
  return {
  default: forwardRef((p: Record<string, unknown> & { children?: ReactNode }, ref) => {
    props.current = p as never;
    useImperativeHandle(ref, () => ({ getMap: () => ({
      getSource: (id: string) => (id === "atlas" ? fake.source : undefined),
      getBounds: () => ({ getWest: () => -20, getSouth: () => 30, getEast: () => 40, getNorth: () => 70 }), getZoom: () => 3,
    }), flyTo: () => {} }));
    return <div data-testid="map">{p.children}</div>;
  }),
  Marker: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  // the hexagons' canvas source; the outline sources (hover, selection) are GeoJSON and not what this checks
  Source: ({ children, ...p }: { children: ReactNode; id?: string }) => { if (p.id === "atlas") fake.sourceProps = p; return <>{children}</>; },
  Layer: () => null,
  };
});
vi.mock("@/map/Borders", () => ({ default: () => null }));

import AtlasMap from "@/map/AtlasMap";
import { act, waitFor } from "@testing-library/react";

const DIR = path.resolve(__dirname, "../public/data/");
const diskFetch = (async (u: string) => new Response(readFileSync(path.join(DIR, u.replace(/^.*data\//, ""))))) as unknown as typeof fetch;
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
  it("paints the view into the canvas source and keeps it across a theme switch that rebuilds the map style", async () => {
    const at = await loadAtlas("data/", diskFetch);
    // jsdom has no canvas: a 2d context that takes the pixels
    const put = vi.fn();
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({ putImageData: put } as never);
    globalThis.ImageData ??= class { constructor(public data: Uint8ClampedArray, public width: number, public height: number) {} } as never;

    fake.source = { setCoordinates: vi.fn(), play: vi.fn(), pause: vi.fn() };
    const { rerender } = render(<AtlasMap atlas={at} layer={layerById("deltaT")} year={2100} cell={null} onCell={() => {}} />);
    act(() => props.current.onLoad());
    await waitFor(() => expect(fake.source!.pause).toHaveBeenCalledTimes(1));
    expect(put).toHaveBeenCalledTimes(1);
    // the view (-20..40 °E, 30..70 °N) and a margin around it
    const coords = fake.source!.setCoordinates.mock.calls[0][0] as number[][];
    expect(coords[0][0]).toBeLessThan(-20); expect(coords[1][0]).toBeGreaterThan(40);
    expect(coords[0][1]).toBeGreaterThan(70); expect(coords[2][1]).toBeLessThan(30);
    await waitFor(() => expect(fake.sourceProps.coordinates).toEqual(coords));
    const canvas = fake.sourceProps.canvas as HTMLCanvasElement;
    expect(fake.sourceProps.type).toBe("canvas");
    expect(canvas.width).toBe(put.mock.calls[0][0].width);

    // dark: the style is replaced and react-map-gl adds the source again from its props: the same painted
    // canvas at the same place, no repaint needed
    rerender(<AtlasMap atlas={at} layer={layerById("deltaT")} year={2100} cell={null} onCell={() => {}} dark />);
    expect(fake.sourceProps.canvas).toBe(canvas);
    expect(fake.sourceProps.coordinates).toEqual(coords);
    // a moved map paints again
    act(() => props.current.onMoveEnd?.());
    await waitFor(() => expect(put).toHaveBeenCalledTimes(2));
  });
});
