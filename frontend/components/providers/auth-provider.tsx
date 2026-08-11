"use client";

import * as React from "react";
import { usePathname, useRouter } from "next/navigation";
import { toast } from "sonner";

import { getCurrentUser, login, logout, refreshSession, register } from "@/lib/api";
import { AuthFormValues, User } from "@/types/api";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  user: User | null;
  status: AuthStatus;
  loginUser: (values: AuthFormValues, redirectTo?: string) => Promise<void>;
  registerUser: (values: AuthFormValues, redirectTo?: string) => Promise<void>;
  logoutUser: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

function setClientAuthCookie(active: boolean) {
  if (typeof document === "undefined") {
    return;
  }

  document.cookie = `auth_hint=${active ? "1" : "0"}; Path=/; Max-Age=${active ? 604800 : 0}; SameSite=Lax`;
}

/** Drop any locally cached auth material (storage + cookies). */
function clearClientAuthStorage() {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.clear();
  document.cookie.split(";").forEach((cookie) => {
    document.cookie = cookie
      .replace(/^ +/, "")
      .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
  });
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [status, setStatus] = React.useState<AuthStatus>("loading");
  const router = useRouter();
  const pathname = usePathname();

  const refreshUser = React.useCallback(async () => {
    // Get current pathname dynamically to avoid dependency issues
    const currentPathname = typeof window !== "undefined" ? window.location.pathname : pathname;
    
    // Skip refresh on public routes (login/register) - just set unauthenticated without API calls
    const isPublicRoute = currentPathname === "/login" || currentPathname === "/register";
    if (isPublicRoute) {
      setStatus("unauthenticated");
      setUser(null);
      setClientAuthCookie(false);
      // Clear any stale auth data on public routes
      clearClientAuthStorage();
      return;
    }

    setStatus("loading");

    try {
      // First try to get the current user directly (works if access_token is valid)
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setStatus("authenticated");
      setClientAuthCookie(true);
    } catch (firstError: any) {
      // Any error - clear auth state and redirect to login
      setUser(null);
      setStatus("unauthenticated");
      setClientAuthCookie(false);
      clearClientAuthStorage();
      if (currentPathname !== "/login" && currentPathname !== "/register") {
        router.replace("/login");
      }
    }
  }, [router]);

  React.useEffect(() => {
    // Only refresh if not on login/register page to avoid infinite loops
    const isPublicRoute = pathname === "/login" || pathname === "/register";
    if (!isPublicRoute) {
      void refreshUser();
    } else {
      // On public routes, immediately set unauthenticated status without any delays
      setStatus("unauthenticated");
      setUser(null);
      setClientAuthCookie(false);
    }
  }, [pathname]);

  React.useEffect(() => {
    const handleExpired = async () => {
      setUser(null);
      setStatus("unauthenticated");
      setClientAuthCookie(false);
      clearClientAuthStorage();
      // Only show toast if not already on login page
      if (pathname !== "/login" && pathname !== "/register") {
        toast.error("Your session expired. Please log in again.");
        router.replace("/login");
      }
    };

    window.addEventListener("auth:expired", handleExpired);
    return () => window.removeEventListener("auth:expired", handleExpired);
  }, [pathname, router]);

  const loginUser = React.useCallback(
    async (values: AuthFormValues, redirectTo = "/dashboard") => {
      const response = await login(values);
      if (typeof window !== "undefined" && response.access_token) {
        localStorage.setItem("access_token", response.access_token);
      }
      setUser(response.user);
      setStatus("authenticated");
      setClientAuthCookie(true);
      toast.success(response.message);
      router.replace(redirectTo);
      // NOTE: Do NOT call router.refresh() here — it triggers SSR re-fetches
      // that race with the cookie being set, causing spurious errors.
    },
    [router]
  );

  const registerUser = React.useCallback(
    async (values: AuthFormValues, redirectTo = "/dashboard") => {
      const response = await register(values);
      if (typeof window !== "undefined" && response.access_token) {
        localStorage.setItem("access_token", response.access_token);
      }
      setUser(response.user);
      setStatus("authenticated");
      setClientAuthCookie(true);
      toast.success(response.message);
      router.replace(redirectTo);
      // NOTE: Do NOT call router.refresh() here — same race condition risk.
    },
    [router]
  );

  const logoutUser = React.useCallback(async () => {
    try {
      const response = await logout();
      toast.success(response.message);
    } finally {
      setUser(null);
      setStatus("unauthenticated");
      setClientAuthCookie(false);
      router.replace("/login");
    }
  }, [router]);

  const value = React.useMemo(
    () => ({
      user,
      status,
      loginUser,
      registerUser,
      logoutUser,
      refreshUser
    }),
    [user, status, loginUser, registerUser, logoutUser, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
