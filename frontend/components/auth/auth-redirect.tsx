"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { LoadingScreen } from "@/components/ui/loading-screen";
import { useAuth } from "@/components/providers/auth-provider";

export function AuthRedirect({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (status === "authenticated") {
      router.replace("/dashboard");
    }
  }, [router, status]);

  if (status === "loading") {
    return <LoadingScreen />;
  }

  if (status === "authenticated") {
    return null;
  }

  return <>{children}</>;
}
