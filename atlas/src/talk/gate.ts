import type { Cmd, DeckState } from "./navigation";

/** One command in flight at a time: the deck's reply carries the state the next key must start from. */
export class CmdGate {
  private since: number | null = null;
  private expect: number | null = null;
  constructor(private now: () => number = () => Date.now(), private ttl = 300) {}

  busy(): boolean {
    if (this.since === null) return false;
    if (this.now() - this.since > this.ttl) { this.since = null; return false; } // lost reply: keys flow again, a late goto reply stays stale
    return true;
  }
  begin(cmd: NonNullable<Cmd>) {
    this.since = this.now();
    this.expect = cmd.send === "goto" ? cmd.n : null;
  }
  /** true when the reply answers the last goto (or no goto is waiting for its answer). */
  accept(s: DeckState): boolean {
    if (this.expect !== null && s.i !== this.expect) return false;
    this.since = null;
    this.expect = null;
    return true;
  }
}
