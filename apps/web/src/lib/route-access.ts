const PUBLIC_PATHS = new Set(["/", "/auth/login", "/feed.xml"]);

const PUBLIC_PREFIXES = [
  "/auth/",
  "/api/auth/",
  "/api/waitlist",
  "/api/og",
  "/embed",
  "/lab-notes",
];

const BETA_GATED_PREFIXES = [
  "/meta",
  "/cards",
  "/tournaments",
  "/events",
  "/evolution",
  "/rotation",
  "/decks",
  "/trips",
  "/creator",
  "/investigate",
  "/settings",
];

export function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.has(pathname)) {
    return true;
  }

  return PUBLIC_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

export function isBetaGatedPath(pathname: string): boolean {
  return BETA_GATED_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}
