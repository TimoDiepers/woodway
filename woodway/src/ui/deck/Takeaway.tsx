import type { ReactNode } from "react";

export type Chapter = "baeume" | "klima" | "vergleich" | "dac";

export function Takeaway({
  children,
  ch,
  size = "app",
}: {
  children: ReactNode;
  ch?: Chapter;
  size?: "app" | "slide";
}) {
  return (
    <div className={size === "slide" ? "takeaway slide" : "takeaway"} data-ch={ch}>
      {children}
    </div>
  );
}
