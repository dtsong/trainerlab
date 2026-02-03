import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("next-auth/react", () => ({
  signIn: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useSearchParams: vi.fn(() => new URLSearchParams()),
}));

const mockUseSearchParams = vi.mocked(
  (await import("next/navigation")).useSearchParams
);

import LoginPage from "../page";

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseSearchParams.mockReturnValue(new URLSearchParams() as any);
  });

  it("renders closed beta messaging", () => {
    render(<LoginPage />);
    expect(screen.getByText("Closed Beta")).toBeInTheDocument();
    expect(
      screen.getByText(/Access is currently limited to invited testers/)
    ).toBeInTheDocument();
  });

  it("shows waitlist link pointing to /#waitlist", () => {
    render(<LoginPage />);
    const link = screen.getByText("Sign up for the waitlist");
    expect(link).toBeInTheDocument();
    expect(link.closest("a")).toHaveAttribute("href", "/#waitlist");
  });

  it("shows Google sign-in button", () => {
    render(<LoginPage />);
    expect(
      screen.getByRole("button", { name: /Continue with Google/i })
    ).toBeInTheDocument();
  });

  it("shows beta access hint on OAuthCallback error", () => {
    mockUseSearchParams.mockReturnValue(
      new URLSearchParams("error=OAuthCallback") as any
    );
    render(<LoginPage />);
    expect(screen.getByText(/may not have beta access/)).toBeInTheDocument();
  });
});
