import { describe, it, expect, vi } from "vitest";

// Mock next-auth and jose before importing auth module
vi.mock("next-auth", () => {
  const mockHandlers = { GET: vi.fn(), POST: vi.fn() };
  const mockAuth = vi.fn();
  const mockSignIn = vi.fn();
  const mockSignOut = vi.fn();

  return {
    default: vi.fn(() => ({
      handlers: mockHandlers,
      auth: mockAuth,
      signIn: mockSignIn,
      signOut: mockSignOut,
    })),
    __esModule: true,
  };
});

vi.mock("next-auth/providers/google", () => ({
  default: { id: "google", name: "Google", type: "oidc" },
  __esModule: true,
}));

vi.mock("jose", () => ({
  SignJWT: vi.fn().mockImplementation(() => ({
    setProtectedHeader: vi.fn().mockReturnThis(),
    setIssuedAt: vi.fn().mockReturnThis(),
    setExpirationTime: vi.fn().mockReturnThis(),
    sign: vi.fn().mockResolvedValue("mock-jwt-token"),
  })),
  jwtVerify: vi.fn().mockResolvedValue({
    payload: { sub: "user-123", email: "test@example.com" },
  }),
}));

describe("auth module", () => {
  it("should export handlers, auth, signIn, and signOut", async () => {
    const authModule = await import("../auth");

    expect(authModule).toHaveProperty("handlers");
    expect(authModule).toHaveProperty("auth");
    expect(authModule).toHaveProperty("signIn");
    expect(authModule).toHaveProperty("signOut");
  });

  it("should configure NextAuth with expected structure", async () => {
    const NextAuth = (await import("next-auth")).default;

    expect(NextAuth).toHaveBeenCalledWith(
      expect.objectContaining({
        trustHost: true,
        providers: expect.any(Array),
        session: expect.objectContaining({
          strategy: "jwt",
        }),
        pages: expect.objectContaining({
          signIn: "/auth/login",
        }),
        jwt: expect.objectContaining({
          encode: expect.any(Function),
          decode: expect.any(Function),
        }),
        callbacks: expect.objectContaining({
          jwt: expect.any(Function),
          session: expect.any(Function),
        }),
      })
    );
  });

  it("should use Google as the auth provider", async () => {
    const NextAuth = (await import("next-auth")).default;
    const callArgs = vi.mocked(NextAuth).mock.calls[0][0];

    expect(callArgs).toHaveProperty("providers");
    expect(callArgs.providers).toBeDefined();
    // Google provider should be included
    expect(callArgs.providers.length).toBeGreaterThan(0);
  });

  it("should set sign-in page to /auth/login", async () => {
    const NextAuth = (await import("next-auth")).default;
    const callArgs = vi.mocked(NextAuth).mock.calls[0][0];

    expect(callArgs.pages?.signIn).toBe("/auth/login");
  });

  it("should use JWT session strategy", async () => {
    const NextAuth = (await import("next-auth")).default;
    const callArgs = vi.mocked(NextAuth).mock.calls[0][0];

    expect(callArgs.session?.strategy).toBe("jwt");
  });

  describe("JWT encode/decode", () => {
    it("should have encode function that handles empty token", async () => {
      const NextAuth = (await import("next-auth")).default;
      const callArgs = vi.mocked(NextAuth).mock.calls[0][0];
      const encode = callArgs.jwt?.encode;

      if (encode) {
        const result = await encode({
          token: null,
          salt: "",
          secret: "test-secret",
        });
        expect(result).toBe("");
      }
    });

    it("should have decode function that handles empty token", async () => {
      const NextAuth = (await import("next-auth")).default;
      const callArgs = vi.mocked(NextAuth).mock.calls[0][0];
      const decode = callArgs.jwt?.decode;

      if (decode) {
        const result = await decode({
          token: "",
          salt: "",
          secret: "test-secret",
        });
        expect(result).toBeNull();
      }
    });

    it("should encode a valid token using jose SignJWT", async () => {
      const NextAuth = (await import("next-auth")).default;
      const jose = await import("jose");
      const callArgs = vi.mocked(NextAuth).mock.calls[0][0];
      const encode = callArgs.jwt?.encode;

      if (encode) {
        const result = await encode({
          token: { sub: "user-123", email: "test@example.com" },
          salt: "",
          secret: "test-secret",
        });
        expect(result).toBe("mock-jwt-token");
        expect(jose.SignJWT).toHaveBeenCalled();
      }
    });

    it("should decode a valid token using jose jwtVerify", async () => {
      const NextAuth = (await import("next-auth")).default;
      const jose = await import("jose");
      const callArgs = vi.mocked(NextAuth).mock.calls[0][0];
      const decode = callArgs.jwt?.decode;

      if (decode) {
        const result = await decode({
          token: "valid-jwt-token",
          salt: "",
          secret: "test-secret",
        });
        expect(result).toEqual({
          sub: "user-123",
          email: "test@example.com",
        });
        expect(jose.jwtVerify).toHaveBeenCalled();
      }
    });

    it("should return null when decode encounters an error", async () => {
      const NextAuth = (await import("next-auth")).default;
      const jose = await import("jose");
      const callArgs = vi.mocked(NextAuth).mock.calls[0][0];
      const decode = callArgs.jwt?.decode;

      // Make jwtVerify throw an error
      vi.mocked(jose.jwtVerify).mockRejectedValueOnce(
        new Error("Invalid token")
      );

      if (decode) {
        const result = await decode({
          token: "invalid-jwt-token",
          salt: "",
          secret: "test-secret",
        });
        expect(result).toBeNull();
      }
    });
  });

  describe("callbacks", () => {
    it("should have jwt callback that sets user info on first sign-in", async () => {
      const NextAuth = (await import("next-auth")).default;
      const callArgs = vi.mocked(NextAuth).mock.calls[0][0];
      const jwtCallback = callArgs.callbacks?.jwt;

      if (jwtCallback) {
        const token = { sub: "old-sub" };
        const account = { providerAccountId: "google-123", provider: "google" };
        const profile = {
          email: "test@example.com",
          name: "Test User",
          picture: "https://example.com/avatar.jpg",
        };

        const result = await (jwtCallback as Function)({
          token,
          account,
          profile,
        });

        expect(result.sub).toBe("google-123");
        expect(result.email).toBe("test@example.com");
        expect(result.name).toBe("Test User");
        expect(result.picture).toBe("https://example.com/avatar.jpg");
      }
    });

    it("should have jwt callback that preserves token on subsequent calls", async () => {
      const NextAuth = (await import("next-auth")).default;
      const callArgs = vi.mocked(NextAuth).mock.calls[0][0];
      const jwtCallback = callArgs.callbacks?.jwt;

      if (jwtCallback) {
        const token = {
          sub: "google-123",
          email: "test@example.com",
          name: "Test User",
        };

        // No account or profile on subsequent calls
        const result = await (jwtCallback as Function)({
          token,
          account: undefined,
          profile: undefined,
        });

        expect(result.sub).toBe("google-123");
        expect(result.email).toBe("test@example.com");
      }
    });

    it("should have session callback that populates user fields", async () => {
      const NextAuth = (await import("next-auth")).default;
      const callArgs = vi.mocked(NextAuth).mock.calls[0][0];
      const sessionCallback = callArgs.callbacks?.session;

      if (sessionCallback) {
        const session = {
          user: { id: "", email: "", name: "", image: undefined },
          expires: "",
        };
        const token = {
          sub: "google-123",
          email: "test@example.com",
          name: "Test User",
          picture: "https://example.com/avatar.jpg",
        };

        const result = await (sessionCallback as Function)({ session, token });

        expect(result.user.id).toBe("google-123");
        expect(result.user.email).toBe("test@example.com");
        expect(result.user.name).toBe("Test User");
        expect(result.user.image).toBe("https://example.com/avatar.jpg");
      }
    });
  });
});
