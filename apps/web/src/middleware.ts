import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";

const PUBLIC_PATHS = new Set(["/", "/auth/login"]);
const PUBLIC_PREFIXES = ["/api/", "/auth/"];

export default auth((req) => {
  const { pathname } = req.nextUrl;

  if (PUBLIC_PATHS.has(pathname)) return NextResponse.next();
  if (PUBLIC_PREFIXES.some((p) => pathname.startsWith(p)))
    return NextResponse.next();
  if (pathname === "/feed.xml") return NextResponse.next();

  if (!req.auth) {
    const url = new URL("/auth/login", req.url);
    url.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon\\.ico|sitemap\\.xml|robots\\.txt).*)",
  ],
};
