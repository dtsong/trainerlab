import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextResponse } from "next/server";

// Mock next-auth's auth wrapper — it just calls the callback
vi.mock("@/lib/auth", () => ({
  auth: (cb: Function) => cb,
}));

vi.mock("next/server", () => {
  const redirect = vi.fn(() => ({ type: "redirect" }));
  const next = vi.fn(() => ({ type: "next" }));
  return {
    NextResponse: { redirect, next },
  };
});

// Import after mocks are set up
const { default: middleware } = await import("@/middleware");

function makeReq(pathname: string, authenticated: boolean) {
  return {
    nextUrl: { pathname },
    url: "http://localhost:3000" + pathname,
    auth: authenticated ? { user: { email: "test@example.com" } } : null,
  } as unknown as Parameters<typeof middleware>[0];
}

const mockCtx = { params: Promise.resolve({}) };

describe("middleware", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("allows unauthenticated access to /", () => {
    middleware(makeReq("/", false), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("allows unauthenticated access to /auth/login", () => {
    middleware(makeReq("/auth/login", false), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("allows unauthenticated access to /api/waitlist", () => {
    middleware(makeReq("/api/waitlist", false), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("allows unauthenticated access to /meta", () => {
    middleware(makeReq("/meta", false), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("allows unauthenticated access to /meta/japan", () => {
    middleware(makeReq("/meta/japan", false), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("allows unauthenticated access to /tournaments", () => {
    middleware(makeReq("/tournaments", false), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("allows unauthenticated access to /tournaments/123", () => {
    middleware(makeReq("/tournaments/123", false), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("allows unauthenticated access to /evolution", () => {
    middleware(makeReq("/evolution", false), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("allows unauthenticated access to /evolution/some-article", () => {
    middleware(makeReq("/evolution/some-article", false), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("redirects unauthenticated access to /decks", () => {
    middleware(makeReq("/decks", false), mockCtx);
    expect(NextResponse.redirect).toHaveBeenCalled();
    const url = (NextResponse.redirect as ReturnType<typeof vi.fn>).mock
      .calls[0][0] as URL;
    expect(url.searchParams.get("callbackUrl")).toBe("/decks");
  });

  it("redirects unauthenticated access to /cards", () => {
    middleware(makeReq("/cards", false), mockCtx);
    expect(NextResponse.redirect).toHaveBeenCalled();
  });

  it("allows authenticated access to /meta", () => {
    middleware(makeReq("/meta", true), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("allows authenticated access to /decks", () => {
    middleware(makeReq("/decks", true), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("allows unauthenticated access to /feed.xml", () => {
    middleware(makeReq("/feed.xml", false), mockCtx);
    expect(NextResponse.next).toHaveBeenCalled();
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });
});
