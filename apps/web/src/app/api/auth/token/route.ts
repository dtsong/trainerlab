import { NextRequest, NextResponse } from "next/server";

/**
 * Returns the raw JWT string for the frontend API client
 * to include in Authorization: Bearer headers.
 */
export async function GET(req: NextRequest) {
  // Auth.js (NextAuth v5) stores the session token in cookies that can be
  // prefixed with __Secure- or __Host- depending on environment.
  // We read the raw cookie value directly so the frontend can forward it as
  // `Authorization: Bearer <token>` to the FastAPI backend.
  const cookieNames = [
    "__Secure-authjs.session-token",
    "__Host-authjs.session-token",
    "authjs.session-token",
    // Backward-compatible (local/dev or older setups)
    "__Secure-next-auth.session-token",
    "next-auth.session-token",
  ];

  const token =
    cookieNames
      .map((name) => req.cookies.get(name)?.value)
      .find((v) => typeof v === "string" && v.length > 0) ?? null;

  const headers = {
    "Cache-Control": "no-store, max-age=0",
  };

  if (!token) {
    return NextResponse.json(
      { error: "Not authenticated" },
      { status: 401, headers }
    );
  }

  return NextResponse.json({ token }, { headers });
}
