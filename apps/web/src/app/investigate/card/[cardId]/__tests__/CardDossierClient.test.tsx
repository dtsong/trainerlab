import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import { CardDossierClient } from "../CardDossierClient";

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
const mockUseCurrentUser = vi.fn();
const mockUseCard = vi.fn();

vi.mock("@/hooks", () => ({
  useAuth: () => mockUseAuth(),
  useCurrentUser: (...args: unknown[]) => mockUseCurrentUser(...args),
  useCard: (...args: unknown[]) => mockUseCard(...args),
}));

vi.mock("@/components/cards", () => ({
  CardDetail: ({ card }: { card: { name: string } }) => (
    <div>CardDetail: {card.name}</div>
  ),
}));

describe("CardDossierClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows sign-in teaser when logged out", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signOut: vi.fn(),
    });
    mockUseCurrentUser.mockReturnValue({ data: null, isLoading: false });
    mockUseCard.mockReturnValue({
      data: { name: "Pikachu" },
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<CardDossierClient cardId="sv1-1" />);
    expect(screen.getByText("Sign in to view the dossier")).toBeInTheDocument();
  });

  it("renders card detail when user has full access", () => {
    mockUseAuth.mockReturnValue({
      user: { id: "u1", email: "x@y.com", displayName: null, photoURL: null },
      loading: false,
      signOut: vi.fn(),
    });
    mockUseCurrentUser.mockReturnValue({
      data: {
        is_beta_tester: true,
        is_subscriber: false,
        is_creator: false,
        is_admin: false,
      },
      isLoading: false,
    });
    mockUseCard.mockReturnValue({
      data: { name: "Charizard ex" },
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<CardDossierClient cardId="sv4-54" />);
    expect(screen.getByText("CardDetail: Charizard ex")).toBeInTheDocument();
  });
});
