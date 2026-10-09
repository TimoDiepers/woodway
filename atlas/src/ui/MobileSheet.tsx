import type { ReactNode } from "react";
import { Drawer, DrawerContent, DrawerTitle } from "@/ui/primitives/drawer";

export function MobileSheet({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Drawer open modal={false} snapPoints={[0.35, 0.9]} dismissible={false}>
      <DrawerContent className="bg-panel">
        <DrawerTitle className="sr-only">{title}</DrawerTitle>
        <div className="overflow-auto px-4 pb-6">{children}</div>
      </DrawerContent>
    </Drawer>
  );
}
