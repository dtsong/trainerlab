import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";

/**
 * Returns the raw JWT string for the frontend API client
 * to include in Authorization: Bearer headers.
 */
export async function GET(req: NextRequest) {
  const token = await getToken({ req, raw: true });

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
