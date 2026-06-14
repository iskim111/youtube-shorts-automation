import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED = ["/overview", "/topics", "/calendar", "/rights", "/analytics", "/audit", "/settings", "/jobs"];

export function middleware(request: NextRequest) {
  if (process.env.NEXT_PUBLIC_AUTH_ENABLED !== "true") {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;
  if (pathname === "/login") {
    return NextResponse.next();
  }

  const isProtected = PROTECTED.some((p) => pathname === p || pathname.startsWith(`${p}/`));
  if (!isProtected) {
    return NextResponse.next();
  }

  if (!request.cookies.get("auth_token")?.value) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", pathname);
    return NextResponse.redirect(login);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
