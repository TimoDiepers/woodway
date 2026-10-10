import { useEffect, useRef, useState, type ReactNode } from "react";
import { X } from "lucide-react";
import { DECK_CHAPTER, DECK_TITLES } from "./deckSlides";
import { MAIN_END, SEQUENCE } from "./sequence";
import { SLIDES } from "./slides";
import { DECK_URL } from "./DeckFrame";

/** A still of each deck slide, rendered at build time (scripts/thumbs.mjs). One live deck per card ran phones
 *  out of memory; an image costs ~10 KB and nothing once it is decoded. */
const thumbUrl = (i: number) => DECK_URL.replace(/index\.html\?host$/, `thumbs/${String(i + 1).padStart(2, "0")}.webp`);

/** Card labels: a deck slide keeps the deck's own number; an atlas slide borrows its predecessor's with a letter. */
function labels(): string[] {
  let last = 0, sub = 0;
  return SEQUENCE.map((it) => {
    if (it.kind === "deck") { last = it.i + 1; sub = 0; return String(last); }
    return `${last}${String.fromCharCode(97 + sub++)}`;
  });
}

export default function TalkOverview({ open, current, onJump, onClose }:
  { open: boolean; current: number; onJump(k: number): void; onClose(): void }) {
  const body = useRef<HTMLDivElement>(null);
  const names = labels();
  const [broken, setBroken] = useState<ReadonlySet<number>>(() => new Set());

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); onClose(); } };
    window.addEventListener("keydown", onKey, true);
    // the current slide in view and focused, so arrows/Tab start there
    const cur = body.current?.querySelector<HTMLButtonElement>('[aria-current="true"]');
    cur?.scrollIntoView({ block: "center" });
    cur?.focus({ preventScroll: true });
    return () => window.removeEventListener("keydown", onKey, true);
  }, [open, onClose]);

  if (!open) return null;
  const groups: { title: string; cards: ReactNode[] }[] = [];
  SEQUENCE.forEach((it, k) => {
    const deckI = it.kind === "deck" ? it.i : -1;
    if (k === 0) groups.push({ title: "Vortrag", cards: [] });
    else if (k === MAIN_END) groups.push({ title: "Backup", cards: [] });
    else if (deckI > 0 && k < MAIN_END && DECK_CHAPTER[deckI]) groups.push({ title: DECK_TITLES[deckI], cards: [] });
    const title = it.kind === "deck" ? DECK_TITLES[it.i] : SLIDES[it.id].title;
    groups[groups.length - 1].cards.push(
      <button key={k} type="button" className="ov-card" aria-current={k === current ? "true" : undefined} onClick={() => onJump(k)}>
        <span className="ov-pv">
          {it.kind === "deck"
            ? broken.has(it.i)
              ? <span className="ov-num" aria-hidden>{names[k]}</span>
              : <img className="ov-thumb" src={thumbUrl(it.i)} loading="lazy" decoding="async" alt="" draggable={false}
                  onError={() => setBroken((b) => new Set(b).add(it.i))} />
            : <span className="ov-atlas" data-ch={SLIDES[it.id].ch ?? "baeume"}><span className="ov-hex" aria-hidden /></span>}
        </span>
        <span className="ov-cap"><i>{names[k]}</i> <span>{title}</span>{it.kind === "atlas" && <em>Live-Karte</em>}</span>
      </button>,
    );
  });

  return (
    <div className="ov" role="dialog" aria-modal="true" aria-label="Folienübersicht" onClick={(e) => e.stopPropagation()}>
      <div className="ov-head">
        <h2>Folien</h2>
        <span><kbd>M</kbd> oder <kbd>Esc</kbd> schließen · Karte wählen zum Springen</span>
        <button type="button" className="ov-close" aria-label="Schließen" onClick={onClose}><X size={22} /></button>
      </div>
      <div className="ov-body" ref={body}>
        {groups.map((g) => (
          <section key={g.title + g.cards.length}>
            <h3>{g.title}</h3>
            <div className="ov-grid">{g.cards}</div>
          </section>
        ))}
      </div>
    </div>
  );
}
