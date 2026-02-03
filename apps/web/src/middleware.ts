export { auth as middleware } from "@/lib/auth";

export const config = {
  matcher: ["/decks/:path*", "/settings/:path*"],
};
