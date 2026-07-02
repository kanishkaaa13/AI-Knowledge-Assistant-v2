"use client";

import * as React from "react";
import { usePathname, useRouter } from "next/navigation";

import { LoadingScreen } from "@/components/ui/loading-screen";
import { useAuth } from "@/components/providers/auth-provider";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  React.useEffect(() => {
    if (status === "unauthenticated") {
      router.replace(`/login?redirect=${encodeURIComponent(pathname || "/dashboard")}`);
    }
  }, [pathname, router, status]);

  if (status === "loading") {
    return <LoadingScreen />;
  }

  if (status === "unauthenticated") {
    return null;
  }

  return <>{children}</>;
}
