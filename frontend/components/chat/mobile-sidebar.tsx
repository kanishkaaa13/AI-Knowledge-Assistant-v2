"use client";

import type { ReactNode } from "react";

import { Dialog, DialogContent } from "@/components/ui/dialog";

export function MobileSidebar({
  children,
  onOpenChange,
  open
}: {
  children: ReactNode;
  onOpenChange: (open: boolean) => void;
  open: boolean;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="left-0 top-0 h-screen max-w-[340px] translate-x-0 translate-y-0 rounded-none border-r p-0 xl:hidden">
        {children}
      </DialogContent>
    </Dialog>
  );
}
