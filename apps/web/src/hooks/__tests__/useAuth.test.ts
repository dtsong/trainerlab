import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";

vi.mock("next-auth/react", () => ({
  useSession: vi.fn(),
  signOut: vi.fn(),
}));

import { useSession, signOut as nextAuthSignOut } from "next-auth/react";
import { useAuth } from "../useAuth";

describe("useAuth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return null user when not authenticated", () => {
    vi.mocked(useSession).mockReturnValue({
      data: null,
      status: "unauthenticated",
      update: vi.fn(),
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it("should return user data when authenticated", () => {
    vi.mocked(useSession).mockReturnValue({
      data: {
        user: {
          id: "user-123",
          email: "test@example.com",
          name: "Test User",
          image: "https://example.com/avatar.jpg",
        },
        expires: "2024-12-31",
      },
      status: "authenticated",
      update: vi.fn(),
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.user).toEqual({
      id: "user-123",
      email: "test@example.com",
      displayName: "Test User",
      photoURL: "https://example.com/avatar.jpg",
    });
    expect(result.current.loading).toBe(false);
  });

  it("should show loading state when session is loading", () => {
    vi.mocked(useSession).mockReturnValue({
      data: null,
      status: "loading",
      update: vi.fn(),
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.loading).toBe(true);
    expect(result.current.user).toBeNull();
  });

  it("should handle null email gracefully", () => {
    vi.mocked(useSession).mockReturnValue({
      data: {
        user: {
          id: "user-123",
          email: null,
          name: "Test User",
          image: null,
        },
        expires: "2024-12-31",
      },
      status: "authenticated",
      update: vi.fn(),
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.user?.email).toBeNull();
    expect(result.current.user?.photoURL).toBeNull();
  });

  it("should call nextAuthSignOut when signOut is called", async () => {
    vi.mocked(useSession).mockReturnValue({
      data: {
        user: {
          id: "user-123",
          email: "test@example.com",
          name: "Test User",
          image: null,
        },
        expires: "2024-12-31",
      },
      status: "authenticated",
      update: vi.fn(),
    });
    vi.mocked(nextAuthSignOut).mockResolvedValue({ url: "/" });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.signOut();
    });

    expect(nextAuthSignOut).toHaveBeenCalledWith({ redirectTo: "/" });
  });

  it("should return stable signOut function reference", () => {
    vi.mocked(useSession).mockReturnValue({
      data: null,
      status: "unauthenticated",
      update: vi.fn(),
    });

    const { result, rerender } = renderHook(() => useAuth());
    const firstSignOut = result.current.signOut;

    rerender();
    const secondSignOut = result.current.signOut;

    expect(firstSignOut).toBe(secondSignOut);
  });

  it("should handle missing name in session", () => {
    vi.mocked(useSession).mockReturnValue({
      data: {
        user: {
          id: "user-123",
          email: "test@example.com",
          name: undefined,
          image: undefined,
        },
        expires: "2024-12-31",
      },
      status: "authenticated",
      update: vi.fn(),
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.user?.displayName).toBeNull();
  });
});
