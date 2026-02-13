import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TournamentRow } from "../TournamentRow";

import type { ApiTournamentSummary } from "@trainerlab/shared-types";

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

describe("TournamentRow", () => {
  const baseTournament: ApiTournamentSummary = {
    id: "t-1",
    name: "Charlotte Regional",
    date: "2026-02-03",
    region: "NA",
    country: "US",
    format: "standard",
    best_of: 3,
    tier: "major",
    participant_count: 512,
    major_format_key: "svi-asc",
    major_format_label: "Scarlet & Violet to Ascended Heroes",
    top_placements: [
      { placement: 1, archetype: "Charizard ex", player_name: "Alice" },
      { placement: 2, archetype: "Lugia VSTAR", player_name: "Bob" },
      { placement: 3, archetype: "Gardevoir ex", player_name: "Charlie" },
      { placement: 4, archetype: "Miraidon ex", player_name: "Diana" },
      { placement: 5, archetype: "Raging Bolt ex", player_name: "Eve" },
      { placement: 6, archetype: "Dragapult ex", player_name: "Frank" },
      { placement: 7, archetype: "Gholdengo ex", player_name: "Grace" },
      { placement: 8, archetype: "Arceus VSTAR", player_name: "Hank" },
    ],
  };

  const defaultProps = {
    tournament: baseTournament,
    expanded: false,
    onToggle: vi.fn(),
  };

  it("should render tournament name", () => {
    render(<TournamentRow {...defaultProps} />);

    expect(screen.getByText("Charlotte Regional")).toBeInTheDocument();
  });

  it("should render current-year date without year", () => {
    render(<TournamentRow {...defaultProps} />);

    expect(screen.getAllByText("Feb 3").length).toBeGreaterThan(0);
  });

  it("should render past-year date with year", () => {
    const pastTournament = {
      ...baseTournament,
      date: "2024-06-15",
    };
    render(<TournamentRow {...defaultProps} tournament={pastTournament} />);

    expect(screen.getAllByText("Jun 15, 2024").length).toBeGreaterThan(0);
  });

  it("should show top 8 placements when participant_count >= 64", () => {
    render(<TournamentRow {...defaultProps} expanded={true} />);

    // 8th placement visible
    expect(screen.getByText("Hank")).toBeInTheDocument();
    expect(screen.getByText("Arceus VSTAR")).toBeInTheDocument();
  });

  it("should show top 4 placements when participant_count < 64", () => {
    const smallTournament = {
      ...baseTournament,
      participant_count: 32,
    };
    render(
      <TournamentRow
        {...defaultProps}
        tournament={smallTournament}
        expanded={true}
      />
    );

    // 4th placement visible, 5th not
    expect(screen.getByText("Diana")).toBeInTheDocument();
    expect(screen.queryByText("Eve")).not.toBeInTheDocument();
  });

  it("should show top 4 when participant_count is null", () => {
    const nullCountTournament = {
      ...baseTournament,
      participant_count: null,
    };
    render(
      <TournamentRow
        {...defaultProps}
        tournament={nullCountTournament}
        expanded={true}
      />
    );

    expect(screen.getByText("Diana")).toBeInTheDocument();
    expect(screen.queryByText("Eve")).not.toBeInTheDocument();
  });

  it("should not show placements when collapsed", () => {
    render(<TournamentRow {...defaultProps} expanded={false} />);

    expect(screen.queryByText("Alice")).not.toBeInTheDocument();
    expect(screen.queryByText("View Full Results")).not.toBeInTheDocument();
  });

  it("should show placements and detail link when expanded", () => {
    render(<TournamentRow {...defaultProps} expanded={true} />);

    expect(screen.getByText("Alice")).toBeInTheDocument();
    const link = screen.getByText(/View Full Results/);
    expect(link.closest("a")).toHaveAttribute("href", "/tournaments/t-1");
  });

  it("should call onToggle when row button is clicked", () => {
    const onToggle = vi.fn();
    render(<TournamentRow {...defaultProps} onToggle={onToggle} />);

    fireEvent.click(screen.getByRole("button"));

    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("should show region when showRegion is true", () => {
    render(<TournamentRow {...defaultProps} showRegion={true} />);

    expect(screen.getAllByText("NA").length).toBeGreaterThan(0);
  });

  it("should hide region when showRegion is false", () => {
    render(<TournamentRow {...defaultProps} showRegion={false} />);

    expect(screen.queryByText("NA")).not.toBeInTheDocument();
  });

  it("should render 'Anonymous' when player_name is null", () => {
    const anonTournament = {
      ...baseTournament,
      top_placements: [
        { placement: 1, archetype: "Charizard ex", player_name: null },
      ],
    };
    render(
      <TournamentRow
        {...defaultProps}
        tournament={anonTournament}
        expanded={true}
      />
    );

    expect(screen.getByText("Anonymous")).toBeInTheDocument();
  });

  it("should show winner badge when placements exist", () => {
    render(<TournamentRow {...defaultProps} />);

    // Winner badge shows in collapsed row
    const badges = screen.getAllByText("Charizard ex");
    expect(badges.length).toBeGreaterThan(0);
  });

  it("should not show winner badge when no placements", () => {
    const emptyTournament = {
      ...baseTournament,
      top_placements: [],
    };
    render(<TournamentRow {...defaultProps} tournament={emptyTournament} />);

    expect(screen.queryByText("Charizard ex")).not.toBeInTheDocument();
  });

  it("should set aria-expanded on the toggle button", () => {
    const { rerender } = render(
      <TournamentRow {...defaultProps} expanded={false} />
    );

    expect(screen.getByRole("button")).toHaveAttribute(
      "aria-expanded",
      "false"
    );

    rerender(<TournamentRow {...defaultProps} expanded={true} />);

    expect(screen.getByRole("button")).toHaveAttribute("aria-expanded", "true");
  });

  it("shows major format badge for official majors when enabled", () => {
    render(
      <TournamentRow
        {...defaultProps}
        showMajorFormatBadge={true}
        expanded={false}
      />
    );

    expect(screen.getAllByText("SVI-ASC").length).toBeGreaterThan(0);
  });

  it("does not show major format badge for grassroots tournaments", () => {
    render(
      <TournamentRow
        {...defaultProps}
        showMajorFormatBadge={true}
        tournament={{ ...baseTournament, tier: "grassroots" }}
      />
    );

    expect(screen.queryByText("SVI-ASC")).not.toBeInTheDocument();
  });
});
