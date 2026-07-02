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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [status, setStatus] = React.useState<AuthStatus>("loading");
  const router = useRouter();
  const pathname = usePathname();

  const refreshUser = React.useCallback(async () => {
    // Skip refresh on public routes (login/register)
    const isPublicRoute = pathname === "/login" || pathname === "/register";
    if (isPublicRoute) {
      setStatus("unauthenticated");
      setUser(null);
      setClientAuthCookie(false);
      return;
    }

    setStatus("loading");

    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setUser(null);
        setStatus("unauthenticated");
        setClientAuthCookie(false);
        router.replace("/login");
        return;
      }
    }

    try {
      // First try to get the current user directly (works if access_token is valid)
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setStatus("authenticated");
      setClientAuthCookie(true);
    } catch (firstError: any) {
      const statusCode = firstError?.response?.status;
      const is401 = statusCode === 401;
      const isNetworkOrServer = !statusCode || statusCode >= 500;

      if (is401) {
        // Token may be expired — try refreshing
        try {
          const refreshData = await refreshSession();
          if (typeof window !== "undefined" && refreshData.access_token) {
            localStorage.setItem("access_token", refreshData.access_token);
          }
          const currentUser = await getCurrentUser();
          setUser(currentUser);
          setStatus("authenticated");
          setClientAuthCookie(true);
        } catch {
          // Both failed — clear auth state and redirect
          setUser(null);
          setStatus("unauthenticated");
          setClientAuthCookie(false);
          if (typeof window !== "undefined") {
            localStorage.removeItem("access_token");
          }
          if (pathname !== "/login" && pathname !== "/register") {
            router.replace("/login");
          }
        }
      } else if (isNetworkOrServer) {
        // Network error or 5xx — backend may be down (cold start).
        // Treat as unauthenticated and redirect to login.
        setUser(null);
        setStatus("unauthenticated");
        setClientAuthCookie(false);
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
        }
        if (pathname !== "/login" && pathname !== "/register") {
          router.replace("/login");
        }
      } else {
        // Other non-auth error — mark as unauthenticated
        setUser(null);
        setStatus("unauthenticated");
        setClientAuthCookie(false);
        if (pathname !== "/login" && pathname !== "/register") {
          router.replace("/login");
        }
      }
    }
  }, [pathname, router]);

  React.useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  React.useEffect(() => {
    const handleExpired = async () => {
      setUser(null);
      setStatus("unauthenticated");
      setClientAuthCookie(false);
      if (typeof window !== "undefined") {
        localStorage.clear();
        document.cookie.split(";").forEach((c) => {
          document.cookie = c
            .replace(/^ +/, "")
            .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        });
      }
      toast.error("Your session expired. Please log in again.");

      if (pathname !== "/login" && pathname !== "/register") {
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
