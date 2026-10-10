import { deckKeyDir } from "@/lib/deckKeys";

describe("atlas inside the deck", () => {
  afterEach(() => { window.history.replaceState(null, "", "/"); vi.resetModules(); });

  it("?lang and ?theme set language and theme for this visit, without overwriting the visitor's own choice", async () => {
    localStorage.setItem("atlas-lang", "en");
    window.history.replaceState(null, "", "/?embed&lang=de&theme=light");
    vi.resetModules();
    const { useAtlas } = await import("@/store");
    expect(useAtlas.getState().lang).toBe("de");
    expect(useAtlas.getState().theme).toBe("light");
    expect(localStorage.getItem("atlas-lang")).toBe("en");
  });

  it("the deck's paging keys page the deck; keys a control needs stay with the control", () => {
    const key = (key: string, target: Element = document.body) => {
      const e = new KeyboardEvent("keydown", { key });
      Object.defineProperty(e, "target", { value: target });
      return deckKeyDir(e);
    };
    expect(key("PageDown")).toBe("next");
    expect(key("PageUp")).toBe("prev");
    expect(key("ArrowRight")).toBe("next");
    expect(key("ArrowLeft")).toBe("prev");
    const range = Object.assign(document.createElement("input"), { type: "range" });
    expect(key("ArrowRight", range)).toBeNull();                 // the year slider
    expect(key("ArrowLeft", document.createElement("input"))).toBeNull();   // the search field
    expect(key("PageDown", range)).toBe("next");                 // a clicker's page key always pages
    const combo = document.createElement("button"); combo.setAttribute("role", "combobox");
    expect(key("ArrowRight", combo)).toBeNull();
    expect(key("a")).toBeNull();
  });
});
