import type { AtlasSlideId, Item } from "./sequence";

export interface DeckState { i: number; step: number; ni: number; ns: number }
export interface Pos { k: number; step: number }
export type Cmd = { send: "next" | "prev" } | { send: "goto"; n: number; step: number | "end" } | null;
type Steps = (id: AtlasSlideId) => number;
type Result = { pos: Pos; cmd: Cmd };

export function next(seq: Item[], pos: Pos, deck: DeckState | null, atlasSteps: Steps): Result {
  const cur = seq[pos.k];
  const nxt = seq[pos.k + 1];
  const stay: Result = { pos, cmd: null };
  if (!cur) return stay;
  if (cur.kind === "deck") {
    if (!deck) return stay;
    if (deck.ni === deck.i) return { pos, cmd: { send: "next" } };
    if (!nxt) return stay;
    if (nxt.kind === "deck") return nxt.i === deck.i + 1 ? { pos, cmd: { send: "next" } } : stay;
    return { pos: { k: pos.k + 1, step: 0 }, cmd: null };
  }
  if (pos.step < atlasSteps(cur.id)) return { pos: { k: pos.k, step: pos.step + 1 }, cmd: null };
  if (!nxt) return stay;
  if (nxt.kind === "deck") return { pos: { k: pos.k + 1, step: 0 }, cmd: { send: "goto", n: nxt.i, step: 0 } };
  return { pos: { k: pos.k + 1, step: 0 }, cmd: null };
}

export function prev(seq: Item[], pos: Pos, deck: DeckState | null, atlasSteps: Steps): Result {
  const cur = seq[pos.k];
  const before = seq[pos.k - 1];
  const stay: Result = { pos, cmd: null };
  if (!cur) return stay;
  if (cur.kind === "deck") {
    if (!deck) return stay;
    if (deck.step > 0) return { pos, cmd: { send: "prev" } };
    if (!before) return stay;
    if (before.kind === "deck") return { pos, cmd: { send: "prev" } };
    return { pos: { k: pos.k - 1, step: atlasSteps(before.id) }, cmd: null };
  }
  if (pos.step > 0) return { pos: { k: pos.k, step: pos.step - 1 }, cmd: null };
  if (!before) return stay;
  if (before.kind === "deck") return { pos: { k: pos.k - 1, step: 0 }, cmd: { send: "goto", n: before.i, step: "end" } };
  return { pos: { k: pos.k - 1, step: atlasSteps(before.id) }, cmd: null };
}

/** Keep k in step with the deck after it moved by itself. */
export function follow(seq: Item[], pos: Pos, deck: DeckState): Pos {
  const k = seq.findIndex((s) => s.kind === "deck" && s.i === deck.i);
  if (k < 0 || k === pos.k) return pos;
  return { k, step: 0 };
}
