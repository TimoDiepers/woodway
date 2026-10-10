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
const fake = vi.hoisted(() => ({ source: null as null | { updateImage: ReturnType<typeof vi.fn> } }));
vi.mock("react-map-gl/maplibre", async () => {
  const { useImperativeHandle } = await import("react");
  return {
  default: forwardRef((p: Record<string, unknown> & { children?: ReactNode }, ref) => {
    props.current = p as never;
    useImperativeHandle(ref, () => ({ getMap: () => ({ getSource: (id: string) => (id === "atlas" ? fake.source : undefined) }), flyTo: () => {} }));
    return <div data-testid="map">{p.children}</div>;
  }),
  Marker: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Source: ({ children }: { children: ReactNode }) => <>{children}</>,
  Layer: () => null,
  };
});
vi.mock("@/map/Borders", () => ({ default: () => null }));

import AtlasMap from "@/map/AtlasMap";
import { act, waitFor } from "@testing-library/react";

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
  it("puts the painted layer back when a theme switch rebuilds the map style", async () => {
    const at = await loadAtlas("data/", diskFetch);
    // jsdom has no canvas: a 2d context that takes the pixels, a blob, an object URL
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({ putImageData: () => {} } as never);
    HTMLCanvasElement.prototype.toBlob = function (cb: BlobCallback) { cb(new Blob(["x"])); };
    let n = 0;
    URL.createObjectURL = () => `blob:paint-${++n}`;
    URL.revokeObjectURL = () => {};
    globalThis.ImageData ??= class { constructor(public data: Uint8ClampedArray, public width: number, public height: number) {} } as never;

    fake.source = { updateImage: vi.fn() };
    const { rerender } = render(<AtlasMap atlas={at} layer={layerById("deltaT")} year={2100} cell={null} onCell={() => {}} />);
    act(() => props.current.onLoad());
    await waitFor(() => expect(fake.source!.updateImage).toHaveBeenCalledTimes(1));
    const painted = fake.source!.updateImage.mock.calls[0][0].url;
    expect(painted).toMatch(/^blob:paint-/);

    // dark: the style is replaced, react-map-gl adds a fresh, empty image source and maplibre reports it
    fake.source = { updateImage: vi.fn() };
    rerender(<AtlasMap atlas={at} layer={layerById("deltaT")} year={2100} cell={null} onCell={() => {}} dark />);
    act(() => props.current.onSourceData?.({ sourceId: "atlas" }));
    expect(fake.source.updateImage).toHaveBeenCalledWith(expect.objectContaining({ url: painted }));
    // and only once: its own load event does not re-apply the same image
    act(() => props.current.onSourceData?.({ sourceId: "atlas" }));
    expect(fake.source.updateImage).toHaveBeenCalledTimes(1);
  });
});
