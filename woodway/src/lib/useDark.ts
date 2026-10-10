import { useAtlas } from "@/store";
import { useMediaQuery } from "./useMediaQuery";

/** The theme actually shown: the stored choice, or the system's when it is "system". */
export function useDark(): boolean {
  const theme = useAtlas((s) => s.theme);
  const prefersDark = useMediaQuery("(prefers-color-scheme: dark)");
  return theme === "dark" || (theme === "system" && prefersDark);
}
