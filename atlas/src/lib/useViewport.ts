import { useEffect, useState } from "react";
import { useMediaQuery } from "./useMediaQuery";

/** Phones (either orientation) and tablets: the map takes the whole screen, controls live in a sheet. */
export const COMPACT_QUERY = "(max-width: 1023px), (max-height: 559px)";
/** A phone held sideways: too short for a bottom sheet, so the sheet's content sits in a side column. */
export const SIDEWAYS_QUERY = "(max-height: 559px) and (min-width: 600px)";

export function useLayoutMode(): "desktop" | "sheet" | "side" {
  const compact = useMediaQuery(COMPACT_QUERY);
  const side = useMediaQuery(SIDEWAYS_QUERY);
  return !compact ? "desktop" : side ? "side" : "sheet";
}

/** The visible viewport height in px (follows the mobile browser bar). */
export function useViewportHeight(): number {
  const read = () => (typeof window === "undefined" ? 800 : window.visualViewport?.height ?? window.innerHeight);
  const [h, setH] = useState(read);
  useEffect(() => {
    const on = () => setH(read());
    window.addEventListener("resize", on);
    window.visualViewport?.addEventListener("resize", on);
    return () => { window.removeEventListener("resize", on); window.visualViewport?.removeEventListener("resize", on); };
  }, []);
  return h;
}
