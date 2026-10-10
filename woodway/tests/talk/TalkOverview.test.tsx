import { fireEvent, render, screen, within } from "@testing-library/react";
import { DECK_URL } from "@/talk/DeckFrame";
import TalkOverview from "@/talk/TalkOverview";
import { SEQUENCE, MAIN_END } from "@/talk/sequence";
import { DECK_TITLES, DECK_CHAPTER } from "@/talk/deckSlides";

describe("TalkOverview", () => {
  it("lists every item of the talk under chapter headings, atlas slides marked as live maps", () => {
    render(<TalkOverview open current={0} onJump={() => {}} onClose={() => {}} />);
    const cards = screen.getAllByRole("button", { name: /^\d+[a-z]?\s/ });
    expect(cards).toHaveLength(SEQUENCE.length);
    expect(screen.getByRole("heading", { name: "Vortrag" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Backup" })).toBeInTheDocument();
    const firstChapter = DECK_TITLES.find((_, i) => DECK_CHAPTER[i] && i > 0)!;
    expect(screen.getByRole("heading", { name: firstChapter })).toBeInTheDocument();
    expect(screen.getAllByText("Live-Karte").length).toBe(SEQUENCE.filter((s) => s.kind === "atlas").length);
    expect(MAIN_END).toBeGreaterThan(0);
  });

  it("jumps to the clicked item and marks the current one", () => {
    const onJump = vi.fn();
    render(<TalkOverview open current={3} onJump={onJump} onClose={() => {}} />);
    const cards = screen.getAllByRole("button", { name: /^\d+[a-z]?\s/ });
    expect(cards[3]).toHaveAttribute("aria-current", "true");
    fireEvent.click(cards[5]);
    expect(onJump).toHaveBeenCalledWith(5);
  });

  it("closes with Escape and its close button", () => {
    const onClose = vi.fn();
    render(<TalkOverview open current={0} onJump={() => {}} onClose={onClose} />);
    fireEvent.keyDown(window, { key: "Escape" });
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Schließen" }));
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it("shows pre-rendered thumbnails, never a live deck per card (a dozen decks run a phone out of memory)", () => {
    const { container } = render(<TalkOverview open current={0} onJump={() => {}} onClose={() => {}} />);
    expect(container.querySelector("iframe")).toBeNull();
    const imgs = container.querySelectorAll<HTMLImageElement>("img.ov-thumb");
    expect(imgs.length).toBe(SEQUENCE.filter((s) => s.kind === "deck").length);
    expect(imgs[0].getAttribute("loading")).toBe("lazy");
    expect(imgs[0].getAttribute("src")).toBe(DECK_URL.replace(/index\.html\?host$/, "thumbs/01.webp"));
  });

  it("a thumbnail that fails to load leaves the card with its number", () => {
    const { container } = render(<TalkOverview open current={0} onJump={() => {}} onClose={() => {}} />);
    const img = container.querySelector<HTMLImageElement>("img.ov-thumb")!;
    fireEvent.error(img);
    expect(img.isConnected).toBe(false);
    const first = screen.getAllByRole("button", { name: /^\d+[a-z]?\s/ })[0];
    expect(first.querySelector(".ov-num")).toHaveTextContent("1");
  });
});
