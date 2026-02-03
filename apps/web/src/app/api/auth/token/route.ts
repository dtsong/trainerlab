import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";

/**
 * Returns the raw JWT string for the frontend API client
 * to include in Authorization: Bearer headers.
 */
export async function GET(req: NextRequest) {
  const token = await getToken({ req, raw: true });

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  return NextResponse.json({ token });
}
