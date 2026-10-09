import type { ReactNode } from "react";

export function Kicker({ children }: { children: ReactNode }) {
  return <div className="kicker">{children}</div>;
}
