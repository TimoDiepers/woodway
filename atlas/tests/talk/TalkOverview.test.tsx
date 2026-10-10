import { fireEvent, render, screen, within } from "@testing-library/react";
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
});
