import * as React from "react"
import * as SliderPrimitive from "@radix-ui/react-slider"

import { cn } from "@/lib/utils"

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
  // The label belongs on the thumb, not on the root: the thumb is the
  // element that carries role="slider", so an aria-label left on the root
  // names a wrapper nobody announces and every slider in the app reaches
  // assistive tech as an unnamed control.
>(({ className, "aria-label": ariaLabel, "aria-labelledby": ariaLabelledBy, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn(
      // Vertical padding so the whole band around the track answers a tap,
      // not just the 6px of the track itself. It costs no layout: the row
      // this sits in is sized by its play button, which is taller than the
      // padded slider at both breakpoints.
      "relative flex w-full touch-none select-none items-center py-2.5 sm:py-2",
      className
    )}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-panelBorder/50">
      <SliderPrimitive.Range className="absolute h-full bg-accent" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledBy}
      // The mark stays 14px — it is a bead on a track, and a bigger one would
      // sit on the year rather than point at it. The target does not: an
      // invisible pseudo-element carries it out to 44px on a phone and 32px
      // on a pointer, the same pair as every other control here. Events on a
      // pseudo-element are events on the element that owns it, so Radix's own
      // drag handling picks them up untouched.
      //
      // Wider vertically than horizontally on purpose: the horizontal reach
      // has to stay inside the 12px gaps to either side, or grabbing the
      // thumb at 2020 would swallow taps meant for the play button.
      className="relative block h-3.5 w-3.5 rounded-full border-2 border-accent bg-panel shadow-sm transition-colors after:absolute after:-inset-x-2.5 after:-inset-y-[15px] after:content-[''] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 disabled:pointer-events-none disabled:opacity-50 sm:after:-inset-x-[9px] sm:after:-inset-y-[9px]" />
  </SliderPrimitive.Root>
))
Slider.displayName = SliderPrimitive.Root.displayName

export { Slider }
