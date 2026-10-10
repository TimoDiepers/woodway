import { Component, type ReactNode } from "react";

/** One broken live slide (a lost WebGL context, a missing field) shows a note; the talk around it keeps running. */
export class SlideBoundary extends Component<{ title: string; children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(e: unknown) { console.error("[talk] slide failed:", e); }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <section className="rslide"><header className="sh"><h2>{this.props.title}</h2></header>
        <p role="alert">Diese Live-Folie ließ sich nicht zeichnen: „{this.props.title}“. Mit → geht es weiter.</p></section>
    );
  }
}
