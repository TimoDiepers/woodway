import type { Cmd, DeckState } from "./navigation";

/** One command in flight at a time: the deck's reply carries the state the next key must start from. */
export class CmdGate {
  private since: number | null = null;
  private expect: number | null = null;
  constructor(private now: () => number = () => Date.now(), private ttl = 300) {}

  busy(): boolean {
    if (this.since === null) return false;
    if (this.now() - this.since > this.ttl) { this.since = null; this.expect = null; return false; } // lost reply
    return true;
  }
  begin(cmd: NonNullable<Cmd>) {
    this.since = this.now();
    this.expect = cmd.send === "goto" ? cmd.n : null;
  }
  /** true when the reply answers the command in flight (or nothing is in flight). */
  accept(s: DeckState): boolean {
    if (this.busy() && this.expect !== null && s.i !== this.expect) return false;
    this.since = null;
    this.expect = null;
    return true;
  }
}
