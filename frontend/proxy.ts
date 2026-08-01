import { NextRequest, NextResponse } from "next/server";

const protectedRoutes = ["/dashboard"];
const authRoutes = ["/login", "/register"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Only check auth_hint cookie (client-settable) for basic routing
  const hasAuthHint = request.cookies.get("auth_hint")?.value === "1";

  const isProtectedRoute = protectedRoutes.some((route) => pathname.startsWith(route));
  const isAuthRoute = authRoutes.some((route) => pathname.startsWith(route));

  // Allow access to protected routes - let API calls handle auth validation
  // This prevents redirect loops when httponly cookies can't be checked server-side
  
  if (isAuthRoute && hasAuthHint) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/login", "/register"]
};
