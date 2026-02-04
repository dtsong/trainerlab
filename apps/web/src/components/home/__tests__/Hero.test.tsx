import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Hero } from "../Hero";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

// Mock ShufflingDeck to avoid timer side effects
vi.mock("../ShufflingDeck", () => ({
  ShufflingDeck: () => <div data-testid="shuffling-deck" />,
}));

// Mock hooks
const mockUseTournaments = vi.fn();
const mockUseHomeMetaData = vi.fn();

vi.mock("@/hooks/useTournaments", () => ({
  useTournaments: (...args: unknown[]) => mockUseTournaments(...args),
}));

vi.mock("@/hooks/useMeta", () => ({
  useHomeMetaData: () => mockUseHomeMetaData(),
}));

// Mock home-utils
vi.mock("@/lib/home-utils", () => ({
  computeHeroStats: vi.fn(
    (
      tournamentCount?: number,
      sampleSize?: number,
      upcomingCount?: number
    ) => ({
      tournamentCount:
        tournamentCount !== undefined ? String(tournamentCount) : "--",
      decklistCount: sampleSize !== undefined ? `${sampleSize}` : "--",
      upcomingEvents:
        upcomingCount !== undefined ? String(upcomingCount) : "--",
    })
  ),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
}

describe("Hero", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseTournaments.mockReturnValue({
      data: undefined,
      isLoading: false,
    });

    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      isLoading: false,
    });
  });

  it("should render the main heading", () => {
    render(<Hero />, { wrapper: createWrapper() });

    expect(screen.getByText("Data-Driven")).toBeInTheDocument();
    expect(screen.getByText("Deck Building")).toBeInTheDocument();
  });

  it("should render the subtitle text", () => {
    render(<Hero />, { wrapper: createWrapper() });

    expect(
      screen.getByText(/Your competitive research lab for Pokemon TCG/)
    ).toBeInTheDocument();
  });

  it("should render the 'Research Lab Active' label", () => {
    render(<Hero />, { wrapper: createWrapper() });

    expect(screen.getByText("Research Lab Active")).toBeInTheDocument();
  });

  it("should render 'Explore the Meta' link pointing to /meta", () => {
    render(<Hero />, { wrapper: createWrapper() });

    const link = screen.getByRole("link", { name: /Explore the Meta/i });
    expect(link).toHaveAttribute("href", "/meta");
  });

  it("should render 'Build a Deck' link pointing to /decks/new", () => {
    render(<Hero />, { wrapper: createWrapper() });

    const link = screen.getByRole("link", { name: /Build a Deck/i });
    expect(link).toHaveAttribute("href", "/decks/new");
  });

  it("should render stat items with placeholder values when loading", () => {
    mockUseTournaments.mockReturnValue({
      data: undefined,
      isLoading: true,
    });
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      isLoading: true,
    });

    render(<Hero />, { wrapper: createWrapper() });

    expect(screen.getByText("tournaments tracked")).toBeInTheDocument();
    expect(screen.getByText("decklists analyzed")).toBeInTheDocument();
    expect(screen.getByText("events upcoming")).toBeInTheDocument();
  });

  it("should render stat items with data when loaded", () => {
    mockUseTournaments
      .mockReturnValueOnce({
        data: { total: 42 },
        isLoading: false,
      })
      .mockReturnValueOnce({
        data: { total: 5 },
        isLoading: false,
      });

    mockUseHomeMetaData.mockReturnValue({
      globalMeta: { sample_size: 3000 },
      isLoading: false,
    });

    render(<Hero />, { wrapper: createWrapper() });

    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("3000")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("should render the Specimen Collection annotation text", () => {
    render(<Hero />, { wrapper: createWrapper() });

    expect(screen.getByText("Specimen Collection")).toBeInTheDocument();
    expect(screen.getByText("Updated Daily")).toBeInTheDocument();
  });
});
