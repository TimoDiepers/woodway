import { DECK_TITLES, deckIndex } from "@/talk/deckSlides";
import { ANCHORS, SEQUENCE } from "@/talk/sequence";

describe("sequence", () => {
  it("reads the deck's slide titles in order", () => {
    expect(DECK_TITLES[0]).toBe("Titel");
    expect(DECK_TITLES).toContain("Danke");
    expect(DECK_TITLES.at(-1)).toBe("Atlas: alle Ergebnisse interaktiv");
  });
  it("anchors exist", () => {
    for (const a of ANCHORS) expect(() => deckIndex(a.after)).not.toThrow();
  });
  it("covers every deck slide exactly once, in order", () => {
    const deck = SEQUENCE.filter((s) => s.kind === "deck").map((s) => (s as { i: number }).i);
    expect(deck).toEqual(DECK_TITLES.map((_, i) => i));
  });
  it("places each atlas slide right after its anchor", () => {
    for (const a of ANCHORS) {
      const k = SEQUENCE.findIndex((s) => s.kind === "atlas" && s.id === a.id);
      const prevDeck = SEQUENCE.slice(0, k).reverse().find((s) => s.kind === "deck");
      expect(prevDeck).toEqual({ kind: "deck", i: deckIndex(a.after) });
    }
  });
});
