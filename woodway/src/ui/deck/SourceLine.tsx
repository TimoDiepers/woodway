import type { ReactNode } from "react";

export function SourceLine({ children }: { children: ReactNode }) {
  return <p className="src">{children}</p>;
}
