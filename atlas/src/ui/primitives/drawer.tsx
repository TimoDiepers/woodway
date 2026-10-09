import * as React from "react"
import { Drawer as DrawerPrimitive } from "vaul"

import { cn } from "@/lib/utils"

// shouldScaleBackground defaults to false here — the app behind the drawer
// is a full-bleed WebGL globe, and Vaul's iOS-style "scale the background"
// effect is built for ordinary scrollable page content; applying it to a
// live WebGL canvas risks visual glitches for no real benefit here.
const Drawer = ({
  shouldScaleBackground = false,
  ...props
}: React.ComponentProps<typeof DrawerPrimitive.Root>) => (
  <DrawerPrimitive.Root
    shouldScaleBackground={shouldScaleBackground}
    {...props}
  />
)
Drawer.displayName = "Drawer"

const DrawerTrigger = DrawerPrimitive.Trigger

const DrawerPortal = DrawerPrimitive.Portal

const DrawerClose = DrawerPrimitive.Close

const DrawerContent = React.forwardRef<
  React.ElementRef<typeof DrawerPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DrawerPrimitive.Content> & {
    /**
     * The active snap point, as a fraction of the viewport, for a snapped
     * sheet. It is what lets content scroll at a low snap point instead of
     * only ever dragging the sheet up to the next one.
     *
     * This element is always a full 100dvh tall (see the note below), so a
     * `flex-1` scroll region inside it is also sized to the whole viewport
     * — even when only 45% of the sheet is above the fold. Content shorter
     * than the viewport then has nothing to scroll: the browser never
     * starts a native scroll, so every upward swipe falls through to
     * Vaul's drag and the sheet just jumps to its taller snap point, and
     * content that sits below the fold is unreachable without expanding.
     * Sizing the content column to the *visible* height instead makes the
     * overflow real, so the same swipe scrolls, exactly as it does for a
     * sheet whose content happens to be viewport-tall already.
     */
    snapFraction?: number | null
  }
>(({ className, children, snapFraction, ...props }, ref) => (
  <DrawerPortal>
    {/* No DrawerOverlay here — this is a non-modal sheet (see OverlayPanel's
        use of modal={false}), deliberately with nothing dimming or blocking
        clicks to the map/controls behind it while it's open.

        Full width, flush to the bottom edge (inset-x-0 bottom-0, no
        margin) — an earlier floating-card version with margin on every
        side made the drawer narrower than the screen for no real benefit
        and added real complexity (a margin-inset "virtual viewport" div
        Vaul had to portal into) for a look that wasn't wanted after all.

        h-[100dvh]: Vaul computes each snap point's reveal purely as
        containerHeight * fraction, assuming this element's own rendered
        height is always exactly the viewport height — then translates it
        down by containerHeight minus that, so its top edge lands exactly
        at the reveal line and its (now off-screen) bottom trails
        harmlessly past the fold. h-[100dvh] matches that assumption: this
        element is always exactly one viewport tall, so every snap fraction
        reveals precisely what it promises regardless of how much real
        content exists (a shorter, content-sized box would instead get
        dragged past the viewport edge by the shortfall — that was the
        earlier "cut off at bottom" bug). dvh (not vh) so that matches
        whichever browser-chrome state is actually visible right now.

        This does NOT reintroduce the earlier drag-breaking h-dvh
        regression: this component uses Vaul's snapPoints prop, and its
        dismiss/snap release logic (onReleaseSnapPoints, in vaul's own
        source) computes purely off window.innerHeight and the snap
        fractions themselves — it never reads this element's rendered
        height. That earlier breakage came from a since-deleted
        pixel-measurement/ResizeObserver system, not from a tall box on its
        own. */}
    <DrawerPrimitive.Content
      ref={ref}
      className={cn(
        "pointer-events-auto fixed inset-x-0 bottom-0 z-30 flex h-[100dvh] flex-col overflow-hidden rounded-t-md border-t border-panelBorder bg-panel/95 shadow-xl shadow-black/10 dark:shadow-black/40 backdrop-blur",
        className,
      )}
      {...props}
    >
      <div className="mx-auto mt-2 h-1.5 w-10 shrink-0 rounded-full bg-panelBorder" />
      {typeof snapFraction === "number" ? (
        // 0.875rem is the drag handle above (mt-2 + h-1.5), so the column
        // below it ends exactly at the fold rather than 14px past it.
        //
        // The height travels as a custom property rather than a plain
        // inline height so index.css can override it mid-drag: the active
        // snap point only updates on release, so a column pinned to the low
        // snap would show a growing band of empty panel under it for the
        // whole upward drag.
        <div
          data-drawer-snap-column
          className="flex min-h-0 flex-col h-[var(--drawer-snap-column-height)]"
          style={
            {
              "--drawer-snap-column-height": `calc(${snapFraction} * 100dvh - 0.875rem)`,
            } as React.CSSProperties
          }
        >
          {children}
        </div>
      ) : (
        children
      )}
    </DrawerPrimitive.Content>
  </DrawerPortal>
))
DrawerContent.displayName = "DrawerContent"

const DrawerHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("grid gap-1 p-4 text-left", className)} {...props} />
)
DrawerHeader.displayName = "DrawerHeader"

const DrawerFooter = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("mt-auto flex flex-col gap-2 p-4", className)} {...props} />
)
DrawerFooter.displayName = "DrawerFooter"

const DrawerTitle = React.forwardRef<
  React.ElementRef<typeof DrawerPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DrawerPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DrawerPrimitive.Title
    ref={ref}
    className={cn("font-mono text-sm text-ink", className)}
    {...props}
  />
))
DrawerTitle.displayName = DrawerPrimitive.Title.displayName

const DrawerDescription = React.forwardRef<
  React.ElementRef<typeof DrawerPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DrawerPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DrawerPrimitive.Description
    ref={ref}
    className={cn("font-serif text-xs uppercase tracking-wide text-inkMuted", className)}
    {...props}
  />
))
DrawerDescription.displayName = DrawerPrimitive.Description.displayName

export {
  Drawer,
  DrawerPortal,
  DrawerTrigger,
  DrawerClose,
  DrawerContent,
  DrawerHeader,
  DrawerFooter,
  DrawerTitle,
  DrawerDescription,
}
