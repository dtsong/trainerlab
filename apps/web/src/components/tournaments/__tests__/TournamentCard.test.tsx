import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { TournamentCard } from "../TournamentCard";

import type { ApiTournamentSummary } from "@trainerlab/shared-types";

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

describe("TournamentCard", () => {
  const mockTournament: ApiTournamentSummary = {
    id: "t-1",
    name: "NAIC 2026",
    date: "2026-06-15T00:00:00Z",
    region: "NA",
    country: "US",
    format: "standard",
    best_of: 3,
    tier: "major",
    participant_count: 2048,
    top_placements: [
      { placement: 1, archetype: "Charizard ex", player_name: "Player A" },
      { placement: 2, archetype: "Lugia VSTAR", player_name: "Player B" },
      { placement: 3, archetype: "Gardevoir ex", player_name: "Player C" },
      { placement: 4, archetype: "Miraidon ex", player_name: "Player D" },
    ],
  };

  it("should render tournament name", () => {
    render(<TournamentCard tournament={mockTournament} />);

    expect(screen.getByText("NAIC 2026")).toBeInTheDocument();
  });

  it("should link to tournament detail page", () => {
    render(<TournamentCard tournament={mockTournament} />);

    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/tournaments/t-1");
  });

  it("should display the formatted date", () => {
    render(<TournamentCard tournament={mockTournament} />);

    const expectedDate = new Date(mockTournament.date).toLocaleDateString(
      "en-US",
      {
        month: "short",
        day: "numeric",
        year: "numeric",
      }
    );
    expect(screen.getByText(expectedDate)).toBeInTheDocument();
  });

  it("should display region and country", () => {
    render(<TournamentCard tournament={mockTournament} />);

    expect(screen.getByText("NA - US")).toBeInTheDocument();
  });

  it("should display only region when country is not provided", () => {
    const tournamentWithoutCountry: ApiTournamentSummary = {
      ...mockTournament,
      country: null,
    };

    render(<TournamentCard tournament={tournamentWithoutCountry} />);

    expect(screen.getByText("NA")).toBeInTheDocument();
    expect(screen.queryByText("NA -")).not.toBeInTheDocument();
  });

  it("should display participant count when available", () => {
    render(<TournamentCard tournament={mockTournament} />);

    expect(screen.getByText("2048")).toBeInTheDocument();
  });

  it("should not display participant count when not provided", () => {
    const tournamentWithoutParticipants: ApiTournamentSummary = {
      ...mockTournament,
      participant_count: null,
    };

    render(<TournamentCard tournament={tournamentWithoutParticipants} />);

    expect(screen.queryByText("2048")).not.toBeInTheDocument();
  });

  it("should display the tier badge for major tournaments", () => {
    render(<TournamentCard tournament={mockTournament} />);

    expect(screen.getByText("major")).toBeInTheDocument();
  });

  it("should display the tier badge for premier tournaments", () => {
    const premierTournament: ApiTournamentSummary = {
      ...mockTournament,
      tier: "premier",
    };

    render(<TournamentCard tournament={premierTournament} />);

    expect(screen.getByText("premier")).toBeInTheDocument();
  });

  it("should not display tier badge when tier is null", () => {
    const noTierTournament: ApiTournamentSummary = {
      ...mockTournament,
      tier: null,
    };

    render(<TournamentCard tournament={noTierTournament} />);

    expect(screen.queryByText("major")).not.toBeInTheDocument();
    expect(screen.queryByText("premier")).not.toBeInTheDocument();
    expect(screen.queryByText("league")).not.toBeInTheDocument();
  });

  it("should display top placements", () => {
    render(<TournamentCard tournament={mockTournament} />);

    expect(screen.getByText("Top Finishers")).toBeInTheDocument();
    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    expect(screen.getByText("Lugia VSTAR")).toBeInTheDocument();
    expect(screen.getByText("Gardevoir ex")).toBeInTheDocument();
    expect(screen.getByText("Miraidon ex")).toBeInTheDocument();
  });

  it("should display placement numbers", () => {
    render(<TournamentCard tournament={mockTournament} />);

    expect(screen.getByText("#1")).toBeInTheDocument();
    expect(screen.getByText("#2")).toBeInTheDocument();
    expect(screen.getByText("#3")).toBeInTheDocument();
    expect(screen.getByText("#4")).toBeInTheDocument();
  });

  it("should not show 'Top Finishers' when no placements exist", () => {
    const noPlacementsTournament: ApiTournamentSummary = {
      ...mockTournament,
      top_placements: [],
    };

    render(<TournamentCard tournament={noPlacementsTournament} />);

    expect(screen.queryByText("Top Finishers")).not.toBeInTheDocument();
  });

  it("should only show first 4 placements", () => {
    const manyPlacementsTournament: ApiTournamentSummary = {
      ...mockTournament,
      top_placements: [
        { placement: 1, archetype: "Deck 1" },
        { placement: 2, archetype: "Deck 2" },
        { placement: 3, archetype: "Deck 3" },
        { placement: 4, archetype: "Deck 4" },
        { placement: 5, archetype: "Deck 5" },
        { placement: 6, archetype: "Deck 6" },
      ],
    };

    render(<TournamentCard tournament={manyPlacementsTournament} />);

    expect(screen.getByText("Deck 1")).toBeInTheDocument();
    expect(screen.getByText("Deck 4")).toBeInTheDocument();
    expect(screen.queryByText("Deck 5")).not.toBeInTheDocument();
    expect(screen.queryByText("Deck 6")).not.toBeInTheDocument();
  });
});
