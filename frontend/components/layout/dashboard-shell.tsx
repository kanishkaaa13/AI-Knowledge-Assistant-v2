import * as React from "react";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  return <div className="flex h-screen overflow-hidden bg-[#080808]">{children}</div>;
}
