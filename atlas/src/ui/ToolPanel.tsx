import { useEffect, useId, type ReactNode } from "react";
import { X } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/ui/primitives/popover";
import { useT } from "@/i18n/useT";

/**
 * One panel, two shells (as in woodway): on a desktop a popover hinged to its button; on a phone or tablet
 * a card rising from the bottom edge, in reach of the thumb. Neither is modal: these panels change what
 * the map shows, and watching the change land is the point.
 */
export function ToolPanel({ compact, open, onOpenChange, trigger, title, sub, children, wide = false }: {
  compact: boolean; open: boolean; onOpenChange(o: boolean): void; trigger: ReactNode;
  title: string; sub?: string; children: ReactNode; wide?: boolean;
}) {
  const t = useT();
  const id = useId();
  useEffect(() => {
    if (!open || !compact) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onOpenChange(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, compact, onOpenChange]);

  const head = (
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <h2 id={id} className="font-serif text-[15px] font-semibold leading-tight text-ink">{title}</h2>
        {sub && <p className="text-[11px] italic leading-snug text-inkMuted">{sub}</p>}
      </div>
      <button aria-label={t("panel.close")} onClick={() => onOpenChange(false)}
        className="-mr-2 -mt-1.5 grid h-10 w-10 shrink-0 place-items-center rounded-full text-inkMuted hover:bg-ink/5 hover:text-ink active:bg-ink/10">
        <X size={18} aria-hidden />
      </button>
    </div>
  );

  if (!compact) {
    return (
      <Popover open={open} onOpenChange={onOpenChange}>
        <PopoverTrigger asChild>{trigger}</PopoverTrigger>
        <PopoverContent align="end" aria-labelledby={id} className={wide ? "w-96 p-4" : "w-80 p-4"}
          onOpenAutoFocus={(e) => { if (!(e.currentTarget as HTMLElement).querySelector("[autofocus], input")) e.preventDefault(); }}>
          {head}
          <div className="mt-3">{children}</div>
        </PopoverContent>
      </Popover>
    );
  }
  return (
    <>
      {trigger}
      {open && (
        <div role="dialog" aria-labelledby={id}
          className="panel fixed inset-x-2 bottom-2 z-40 flex max-h-[min(72dvh,36rem)] flex-col overflow-hidden rounded-xl shadow-xl animate-in fade-in-0 slide-in-from-bottom-4"
          style={{ marginBottom: "env(safe-area-inset-bottom)" }}>
          <div className="shrink-0 border-b border-[var(--paper-line)] px-4 pb-2 pt-3">{head}</div>
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 pb-5 pt-3">{children}</div>
        </div>
      )}
    </>
  );
}
