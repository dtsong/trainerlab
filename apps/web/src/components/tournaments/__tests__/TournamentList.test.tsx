import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TournamentList } from "../TournamentList";

import type { ApiTournamentListResponse } from "@trainerlab/shared-types";

const mockUseTournaments = vi.fn();

vi.mock("@/hooks/useTournaments", () => ({
  useTournaments: (...args: unknown[]) => mockUseTournaments(...args),
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

const mockData: ApiTournamentListResponse = {
  items: [
    {
      id: "t-1",
      name: "Charlotte Regional",
      date: "2026-02-03",
      region: "NA",
      country: "US",
      format: "standard",
      best_of: 3,
      tier: "major",
      participant_count: 512,
      top_placements: [
        {
          placement: 1,
          archetype: "Charizard ex",
          player_name: "Alice",
        },
      ],
    },
    {
      id: "t-2",
      name: "Stuttgart Regional",
      date: "2026-01-20",
      region: "EU",
      country: "DE",
      format: "standard",
      best_of: 3,
      tier: "major",
      participant_count: 384,
      top_placements: [
        {
          placement: 1,
          archetype: "Gardevoir ex",
          player_name: "Bob",
        },
      ],
    },
  ],
  total: 2,
  page: 1,
  limit: 20,
  has_next: false,
  has_prev: false,
};

describe("TournamentList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render skeleton loading state", () => {
    mockUseTournaments.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    });

    const { container } = render(
      <TournamentList apiParams={{ tier: "major" }} />
    );

    const pulseElements = container.querySelectorAll(".animate-pulse");
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it("should show error message on API failure", () => {
    mockUseTournaments.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    });

    render(<TournamentList apiParams={{ tier: "major" }} />);

    expect(screen.getByText("Failed to load tournaments")).toBeInTheDocument();
  });

  it("should call refetch when Try Again is clicked", () => {
    const refetch = vi.fn();
    mockUseTournaments.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch,
    });

    render(<TournamentList apiParams={{ tier: "major" }} />);

    fireEvent.click(screen.getByText("Try Again"));

    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("should show empty state when no tournaments", () => {
    mockUseTournaments.mockReturnValue({
      data: { ...mockData, items: [], total: 0 },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<TournamentList apiParams={{ tier: "major" }} />);

    expect(
      screen.getByText("No tournaments found matching your filters.")
    ).toBeInTheDocument();
  });

  it("should render tournament rows when data is present", () => {
    mockUseTournaments.mockReturnValue({
      data: mockData,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<TournamentList apiParams={{ tier: "major" }} />);

    expect(screen.getByText("Charlotte Regional")).toBeInTheDocument();
    expect(screen.getByText("Stuttgart Regional")).toBeInTheDocument();
  });

  it("should hide pagination when single page", () => {
    mockUseTournaments.mockReturnValue({
      data: mockData,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<TournamentList apiParams={{ tier: "major" }} />);

    expect(screen.queryByText("Previous")).not.toBeInTheDocument();
    expect(screen.queryByText("Next")).not.toBeInTheDocument();
  });

  it("should show pagination and disable Previous on first page", () => {
    mockUseTournaments.mockReturnValue({
      data: { ...mockData, has_next: true, total: 40 },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<TournamentList apiParams={{ tier: "major" }} />);

    expect(screen.getByText("Previous")).toBeDisabled();
    expect(screen.getByText("Next")).not.toBeDisabled();
    expect(screen.getByText("Page 1 of 2")).toBeInTheDocument();
  });

  it("should disable Next on last page", () => {
    mockUseTournaments.mockReturnValue({
      data: {
        ...mockData,
        page: 2,
        has_prev: true,
        has_next: false,
        total: 40,
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<TournamentList apiParams={{ tier: "major" }} />);

    expect(screen.getByText("Previous")).not.toBeDisabled();
    expect(screen.getByText("Next")).toBeDisabled();
  });

  it("should pass apiParams to useTournaments", () => {
    mockUseTournaments.mockReturnValue({
      data: mockData,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(
      <TournamentList apiParams={{ tier: "major", format: "standard" }} />
    );

    expect(mockUseTournaments).toHaveBeenCalledWith(
      expect.objectContaining({
        tier: "major",
        format: "standard",
        page: 1,
        limit: 20,
        sort_by: "date",
        order: "desc",
      })
    );
  });

  it("should pass showRegion prop to TournamentRow", () => {
    mockUseTournaments.mockReturnValue({
      data: {
        ...mockData,
        items: [mockData.items[0]],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    const { rerender } = render(
      <TournamentList apiParams={{ tier: "major" }} showRegion={true} />
    );

    expect(screen.getAllByText("NA").length).toBeGreaterThan(0);

    rerender(
      <TournamentList apiParams={{ tier: "major" }} showRegion={false} />
    );

    expect(screen.queryByText("NA")).not.toBeInTheDocument();
  });
});
