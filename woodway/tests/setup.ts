import "@testing-library/jest-dom/vitest";

// jsdom doesn't implement ResizeObserver; Radix's Slider (used in
// MorePopover) reads element size on mount via @radix-ui/react-use-size.
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

// jsdom has no PointerEvent at all. Vaul (the Drawer's drag/swipe-to-dismiss
// implementation) reads pointerId and setPointerCapture off pointer events
// during its own event wiring — without this, mounting a Drawer throws.
if (typeof globalThis.PointerEvent === "undefined") {
  class PointerEventPolyfill extends MouseEvent {
    pointerId: number;
    constructor(type: string, params: PointerEventInit = {}) {
      super(type, params);
      this.pointerId = params.pointerId ?? 0;
    }
  }
  globalThis.PointerEvent = PointerEventPolyfill as unknown as typeof PointerEvent;
}

// jsdom has no matchMedia at all. Used by useMediaQuery (OverlayPanel's
// desktop-sidebar-vs-mobile-drawer switch) — a real min/max-width parser
// against window.innerWidth (jsdom defaults to 1024) rather than a stub
// that always returns the same value, so tests can exercise both branches
// by setting innerWidth before rendering.
if (typeof window !== "undefined" && typeof window.matchMedia === "undefined") {
  window.matchMedia = (query: string) => {
    const min = query.match(/min-width:\s*(\d+(?:\.\d+)?)px/);
    const max = query.match(/max-width:\s*(\d+(?:\.\d+)?)px/);
    // Anything that isn't a width query (prefers-reduced-motion, prefers-
    // color-scheme) is reported as NOT matching, which is what a default
    // browser profile reports too. Without this, "no min and no max" fell
    // through to vacuously true and every such query matched — which would
    // silently put the whole suite on the reduced-motion path.
    const evaluate = () =>
      Boolean(min || max) &&
      (!min || window.innerWidth >= parseFloat(min[1])) &&
      (!max || window.innerWidth <= parseFloat(max[1]));
    const listeners = new Set<() => void>();
    return {
      get matches() {
        return evaluate();
      },
      media: query,
      onchange: null,
      addEventListener: (_: string, cb: () => void) => listeners.add(cb),
      removeEventListener: (_: string, cb: () => void) => listeners.delete(cb),
      addListener: (cb: () => void) => listeners.add(cb),
      removeListener: (cb: () => void) => listeners.delete(cb),
      dispatchEvent: () => true,
    } as unknown as MediaQueryList;
  };
}

// jsdom implements neither Element.hasPointerCapture/setPointerCapture/
// releasePointerCapture nor scrollIntoView. Radix's Select (used in
// MorePopover for the extrusion shape dropdown) calls hasPointerCapture
// during its own pointer-event handling and scrollIntoView when an item is
// selected — without these, opening/using the dropdown throws.
if (typeof Element !== "undefined") {
  if (!Element.prototype.hasPointerCapture) {
    Element.prototype.hasPointerCapture = () => false;
  }
  if (!Element.prototype.setPointerCapture) {
    Element.prototype.setPointerCapture = () => {};
  }
  if (!Element.prototype.releasePointerCapture) {
    Element.prototype.releasePointerCapture = () => {};
  }
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = () => {};
  }
}

// jsdom has no requestAnimationFrame at all. TimeSlider's play/pause loop
// calls it directly on mount whenever isPlaying is true — without this,
// clicking play in a test throws immediately. A setTimeout-based shim is
// enough for tests that just need the callback to eventually fire; nothing
// here asserts frame-accurate timing.
if (typeof globalThis.requestAnimationFrame === "undefined") {
  globalThis.requestAnimationFrame = ((cb: FrameRequestCallback) =>
    setTimeout(() => cb(performance.now()), 16) as unknown as number) as typeof requestAnimationFrame;
  globalThis.cancelAnimationFrame = ((id: number) => clearTimeout(id)) as typeof cancelAnimationFrame;
}
