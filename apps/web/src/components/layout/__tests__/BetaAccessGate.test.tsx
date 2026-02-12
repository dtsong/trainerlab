import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import { BetaAccessGate } from "../BetaAccessGate";

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/"),
}));

vi.mock("@/hooks", () => ({
  useAuth: vi.fn(() => ({
    user: null,
    loading: false,
    signOut: vi.fn(),
  })),
  useCurrentUser: vi.fn(() => ({
    data: null,
    isLoading: false,
    isFetching: false,
    refetch: vi.fn(),
  })),
}));

const mockUsePathname = vi.mocked(
  (await import("next/navigation")).usePathname
);
const mockUseAuth = vi.mocked((await import("@/hooks")).useAuth);
const mockUseCurrentUser = vi.mocked((await import("@/hooks")).useCurrentUser);

function createMockAuthUser(overrides = {}) {
  return {
    id: "user-1",
    email: "ash@pokemon.com",
    displayName: "Ash Ketchum",
    photoURL: null,
    ...overrides,
  };
}

describe("BetaAccessGate", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePathname.mockReturnValue("/");
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signOut: vi.fn(),
    });
    mockUseCurrentUser.mockReturnValue({
      data: null,
      isLoading: false,
      isFetching: false,
      refetch: vi.fn(),
    } as any);
  });

  it("renders children on public routes when logged out", () => {
    mockUsePathname.mockReturnValue("/");
    render(
      <BetaAccessGate>
        <div>public child</div>
      </BetaAccessGate>
    );
    expect(screen.getByText("public child")).toBeInTheDocument();
  });

  it("blocks non-public routes when logged out", () => {
    mockUsePathname.mockReturnValue("/cards");
    render(
      <BetaAccessGate>
        <div>protected child</div>
      </BetaAccessGate>
    );
    expect(screen.queryByText("protected child")).not.toBeInTheDocument();
    expect(screen.getByText(/Sign in required/i)).toBeInTheDocument();
    expect(screen.getByText("Sign in").closest("a")).toHaveAttribute(
      "href",
      expect.stringContaining("/auth/login")
    );
  });

  it("renders children on non-beta protected routes when logged in", () => {
    mockUsePathname.mockReturnValue("/settings");
    mockUseAuth.mockReturnValue({
      user: createMockAuthUser(),
      loading: false,
      signOut: vi.fn(),
    });
    render(
      <BetaAccessGate>
        <div>settings child</div>
      </BetaAccessGate>
    );
    expect(screen.getByText("settings child")).toBeInTheDocument();
  });

  it("shows beta gate when logged in but lacks beta access", () => {
    mockUsePathname.mockReturnValue("/meta");
    mockUseAuth.mockReturnValue({
      user: createMockAuthUser(),
      loading: false,
      signOut: vi.fn(),
    });
    mockUseCurrentUser.mockReturnValue({
      data: {
        is_beta_tester: false,
        is_subscriber: false,
        is_creator: false,
        is_admin: false,
      },
      isLoading: false,
      isFetching: false,
      refetch: vi.fn(),
    } as any);

    render(
      <BetaAccessGate>
        <div>meta child</div>
      </BetaAccessGate>
    );

    expect(screen.queryByText("meta child")).not.toBeInTheDocument();
    expect(
      screen.getByText(/Closed Beta Access Required/i)
    ).toBeInTheDocument();
  });
});
