import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const publicPaths = new Set(["/", "/login", "/signup"]);
const apiBase = process.env.NEXT_PUBLIC_API_URL || "https://realty-api.indicationsmedia.com";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths and static assets
  if (publicPaths.has(pathname) || pathname.startsWith("/_next") || pathname.startsWith("/api")) {
    return NextResponse.next();
  }

  // For dashboard routes, the client checks localStorage — middleware can't read it.
  // We set a cookie from the client on login to enable server-side protection.
  const token = request.cookies.get("athena_token")?.value;

  // If no cookie but trying to access protected route, still allow — client-side guard handles it
  // This is a soft middleware that adds security headers but doesn't block on missing cookie
  const response = NextResponse.next();

  // Security headers
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
