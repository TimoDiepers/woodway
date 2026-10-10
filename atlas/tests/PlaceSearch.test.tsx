import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PlaceSearch } from "@/ui/PlaceSearch";

const BERLIN = [
  { display_name: "Berlin, Deutschland", lat: "52.5170365", lon: "13.3888599" },
  { display_name: "Berlin, Coös County, New Hampshire, United States", lat: "44.4686", lon: "-71.1851" },
];
const ok = (body: unknown) => vi.fn(async () => new Response(JSON.stringify(body))) as unknown as typeof fetch & ReturnType<typeof vi.fn>;

describe("PlaceSearch", () => {
  it("asks Nominatim only on Enter, lists the results and flies to the one picked", async () => {
    const fetcher = ok(BERLIN);
    const onPick = vi.fn();
    render(<PlaceSearch onPick={onPick} fetcher={fetcher} />);
    const box = screen.getByRole("searchbox", { name: "Search a place" });
    await userEvent.type(box, "Berlin");
    expect(fetcher).not.toHaveBeenCalled();
    await userEvent.type(box, "{Enter}");
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher.mock.calls[0][0]).toBe("https://nominatim.openstreetmap.org/search?format=json&limit=5&q=Berlin");
    await userEvent.click(await screen.findByRole("button", { name: "Berlin, Deutschland" }));
    expect(onPick).toHaveBeenCalledWith({ name: "Berlin, Deutschland", lon: 13.3888599, lat: 52.5170365 });
    expect(screen.queryByRole("button", { name: "Berlin, Deutschland" })).toBeNull();
  });
  it("says when nothing matches", async () => {
    render(<PlaceSearch onPick={() => {}} fetcher={ok([])} />);
    await userEvent.type(screen.getByRole("searchbox"), "xqzv{Enter}");
    expect(await screen.findByText("No matches.")).toBeInTheDocument();
  });
  it("says when the search is unavailable", async () => {
    const down = vi.fn(async () => new Response("", { status: 503 })) as unknown as typeof fetch;
    render(<PlaceSearch onPick={() => {}} fetcher={down} />);
    await userEvent.type(screen.getByRole("searchbox"), "Berlin{Enter}");
    expect(await screen.findByText("Search unavailable.")).toBeInTheDocument();
  });
  it("an empty query asks nothing", async () => {
    const fetcher = ok(BERLIN);
    render(<PlaceSearch onPick={() => {}} fetcher={fetcher} />);
    await userEvent.type(screen.getByRole("searchbox"), "   {Enter}");
    expect(fetcher).not.toHaveBeenCalled();
  });
});
