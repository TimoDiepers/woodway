import * as React from "react";
import * as PopoverPrimitive from "@radix-ui/react-popover";
import { cn } from "@/lib/utils";

const Popover = PopoverPrimitive.Root;
const PopoverTrigger = PopoverPrimitive.Trigger;

const PopoverContent = React.forwardRef<
  React.ElementRef<typeof PopoverPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content>
>(({ className, align = "end", sideOffset = 8, collisionPadding = 12, ...props }, ref) => (
  <PopoverPrimitive.Portal>
    <PopoverPrimitive.Content
      ref={ref}
      align={align}
      sideOffset={sideOffset}
      // Radix flips a popover to whichever side has more room, but it will
      // not shrink one: a panel taller than the space (the styling and more
      // menus, opened from the mobile tool column at mid-screen) flipped up
      // and then ran off the top of the viewport, ~110px of it unreachable.
      // collisionPadding keeps a margin against every edge, and capping the
      // height at Radix's own measured available height makes the content
      // scroll inside the panel instead of escaping it.
      collisionPadding={collisionPadding}
      className={cn(
        "z-30 flex max-h-[var(--radix-popover-content-available-height)] w-64 flex-col overflow-y-auto rounded-md border border-panelBorder bg-panel/95 p-3 text-ink shadow-xl shadow-black/10 dark:shadow-black/40 backdrop-blur outline-none",
        "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
        // Enters from the edge it is anchored to, so a panel hinged on the
        // mobile tool column reads as pulled out of that column rather than
        // materializing beside it.
        "data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 data-[side=bottom]:slide-in-from-top-2",
        className,
      )}
      {...props}
    />
  </PopoverPrimitive.Portal>
));
PopoverContent.displayName = PopoverPrimitive.Content.displayName;

export { Popover, PopoverTrigger, PopoverContent };
