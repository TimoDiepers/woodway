/**
 * Woodway embedded in the deck's last slide: once a click has put focus into it, the deck no longer hears
 * the keys. These are the ones it pages on. A clicker's page keys always page; arrows only where no control
 * needs them (the year slider, a text field, an open dropdown).
 */
export function deckKeyDir(e: KeyboardEvent): "next" | "prev" | null {
  if (e.metaKey || e.ctrlKey || e.altKey) return null;
  if (e.key === "PageDown") return "next";
  if (e.key === "PageUp") return "prev";
  if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return null;
  const el = e.target as HTMLElement | null;
  if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.closest?.('[role="combobox"], [role="listbox"], [role="slider"], [role="dialog"]'))) return null;
  return e.key === "ArrowRight" ? "next" : "prev";
}

/** In the deck's iframe (?embed): hand the paging keys to the deck. */
export function forwardDeckKeys(): () => void {
  if (window.parent === window || !new URLSearchParams(location.search).has("embed")) return () => {};
  const onKey = (e: KeyboardEvent) => {
    const dir = deckKeyDir(e);
    if (!dir) return;
    e.preventDefault();
    window.parent.postMessage({ src: "woodway-key", dir }, "*");
  };
  window.addEventListener("keydown", onKey);
  return () => window.removeEventListener("keydown", onKey);
}
