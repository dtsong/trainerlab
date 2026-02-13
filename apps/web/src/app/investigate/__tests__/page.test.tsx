import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import InvestigatePage from "../page";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

const mockUseAuth = vi.fn();

vi.mock("@/hooks", () => ({
  useAuth: () => mockUseAuth(),
}));

describe("InvestigatePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("routes signed-out users to login with callbackUrl", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signOut: vi.fn(),
    });

    render(<InvestigatePage />);
    fireEvent.change(screen.getByPlaceholderText(/Try:/i), {
      target: { value: "Pikachu" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Sign in to search/i }));

    expect(mockPush).toHaveBeenCalledWith(
      "/auth/login?callbackUrl=%2Fcards%3Fq%3DPikachu"
    );
  });

  it("routes signed-in users directly to /cards with q param", () => {
    mockUseAuth.mockReturnValue({
      user: { id: "u1", email: "x@y.com", displayName: null, photoURL: null },
      loading: false,
      signOut: vi.fn(),
    });

    render(<InvestigatePage />);
    fireEvent.change(screen.getByPlaceholderText(/Try:/i), {
      target: { value: "Charizard ex" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^Search$/i }));

    expect(mockPush).toHaveBeenCalledWith("/cards?q=Charizard%20ex");
  });
});
