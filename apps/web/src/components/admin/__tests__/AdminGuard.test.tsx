import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AdminGuard } from "../AdminGuard";

const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({
    replace: mockReplace,
  })),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(() => ({
    user: null,
    loading: true,
    signOut: vi.fn(),
  })),
}));

const mockUseAuth = vi.mocked((await import("@/contexts/AuthContext")).useAuth);

describe("AdminGuard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: null,
      loading: true,
      authError: null,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signInWithGoogle: vi.fn(),
      signOut: vi.fn(),
      getIdToken: vi.fn(),
      clearAuthError: vi.fn(),
    });
  });

  it("should show loading state while auth is loading", () => {
    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.queryByText("Admin Content")).not.toBeInTheDocument();
  });

  it("should redirect to login when user is not authenticated", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      authError: null,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signInWithGoogle: vi.fn(),
      signOut: vi.fn(),
      getIdToken: vi.fn(),
      clearAuthError: vi.fn(),
    });

    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(mockReplace).toHaveBeenCalledWith("/auth/login");
    expect(screen.queryByText("Admin Content")).not.toBeInTheDocument();
  });

  it("should show access denied for non-admin users", () => {
    mockUseAuth.mockReturnValue({
      user: {
        uid: "123",
        email: "notadmin@example.com",
        displayName: "Not Admin",
        photoURL: null,
      },
      loading: false,
      authError: null,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signInWithGoogle: vi.fn(),
      signOut: vi.fn(),
      getIdToken: vi.fn(),
      clearAuthError: vi.fn(),
    });

    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("Access Denied")).toBeInTheDocument();
    expect(
      screen.getByText(
        "notadmin@example.com is not authorized to view this page."
      )
    ).toBeInTheDocument();
    expect(screen.queryByText("Admin Content")).not.toBeInTheDocument();
  });

  it("should render children for admin users", () => {
    mockUseAuth.mockReturnValue({
      user: {
        uid: "456",
        email: "daniel@appraisehq.ai",
        displayName: "Daniel",
        photoURL: null,
      },
      loading: false,
      authError: null,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signInWithGoogle: vi.fn(),
      signOut: vi.fn(),
      getIdToken: vi.fn(),
      clearAuthError: vi.fn(),
    });

    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("Admin Content")).toBeInTheDocument();
    expect(screen.queryByText("Access Denied")).not.toBeInTheDocument();
    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });
});
