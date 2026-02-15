import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ArchetypePanel, type ArchetypePanelData } from "../ArchetypePanel";

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

// Mock UI components
vi.mock("@/components/ui/panel-overlay", () => ({
  PanelOverlay: ({
    isOpen,
    onClose,
    children,
  }: {
    isOpen: boolean;
    onClose: () => void;
    children: React.ReactNode;
  }) =>
    isOpen ? (
      <div data-testid="panel-overlay">
        <button onClick={onClose} data-testid="overlay-backdrop">
          backdrop
        </button>
        {children}
      </div>
    ) : null,
}));

vi.mock("@/components/ui/tier-badge", () => ({
  TierBadge: ({ tier }: { tier: string }) => (
    <span data-testid="tier-badge">{tier}</span>
  ),
}));

vi.mock("@/components/ui/trend-arrow", () => ({
  TrendArrow: ({ direction }: { direction: string }) => (
    <span data-testid="trend-arrow">{direction}</span>
  ),
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({
    children,
    asChild,
    ...props
  }: {
    children: React.ReactNode;
    asChild?: boolean;
    className?: string;
    variant?: string;
  }) => <div {...props}>{children}</div>,
}));

vi.mock("../MatchupSpread", () => ({
  MatchupSpread: ({ matchups }: { matchups: unknown[] }) => (
    <div data-testid="matchup-spread">{matchups.length} matchups</div>
  ),
}));

describe("ArchetypePanel", () => {
  const mockArchetype: ArchetypePanelData = {
    id: "charizard",
    name: "Charizard ex",
    tier: "S",
    share: 15.3,
    trend: "up",
    trendValue: 2.1,
    keyCards: [
      { name: "Charizard ex", inclusionRate: 0.98, avgCopies: 2.5 },
      { name: "Rare Candy", inclusionRate: 0.95, avgCopies: 4.0 },
      { name: "Arven", inclusionRate: 0.92, avgCopies: 3.1 },
    ],
    buildVariants: [
      {
        name: "Pidgeot Build",
        description: "Uses Pidgeot for consistency",
        share: 65,
      },
      {
        name: "Bibarel Build",
        description: "Uses Bibarel for draw support",
        share: 35,
      },
    ],
    matchups: [
      {
        opponent: "Lugia VSTAR",
        winRate: 0.6,
        sampleSize: 120,
        confidence: "high" as const,
      },
      {
        opponent: "Gardevoir ex",
        winRate: 0.45,
        sampleSize: 80,
        confidence: "high" as const,
      },
    ],
    recentResults: [
      {
        tournament: "Regional Charlotte",
        placement: "1st",
        date: "2024-01-15",
      },
      {
        tournament: "League Cup Austin",
        placement: "Top 4",
        date: "2024-01-10",
      },
    ],
  };

  const defaultProps = {
    archetype: mockArchetype,
    isOpen: true,
    onClose: vi.fn(),
  };

  it("should render nothing when archetype is null", () => {
    const { container } = render(
      <ArchetypePanel archetype={null} isOpen={true} onClose={vi.fn()} />
    );

    expect(container.innerHTML).toBe("");
  });

  it("should render nothing when panel is closed", () => {
    const { container } = render(
      <ArchetypePanel {...defaultProps} isOpen={false} />
    );

    // PanelOverlay mock returns null when not open
    expect(container.innerHTML).toBe("");
  });

  it("should render the archetype name", () => {
    render(<ArchetypePanel {...defaultProps} />);

    // "Charizard ex" appears both as the archetype header name and as a key card
    const elements = screen.getAllByText("Charizard ex");
    expect(elements.length).toBeGreaterThanOrEqual(1);
    // The header should contain it in an h2
    const heading = elements.find((el) => el.tagName === "H2");
    expect(heading).toBeDefined();
  });

  it("should render the tier badge", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByTestId("tier-badge")).toHaveTextContent("S");
  });

  it("should render the share percentage", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByText("15.3%")).toBeInTheDocument();
  });

  it("should render the trend arrow", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByTestId("trend-arrow")).toHaveTextContent("up");
  });

  it("should render the close button", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(
      screen.getByRole("button", { name: /close panel/i })
    ).toBeInTheDocument();
  });

  it("should call onClose when close button is clicked", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<ArchetypePanel {...defaultProps} onClose={onClose} />);

    await user.click(screen.getByRole("button", { name: /close panel/i }));

    expect(onClose).toHaveBeenCalled();
  });

  it("should render the Decklist section", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByText("Decklist")).toBeInTheDocument();
  });

  it("should render key card names", () => {
    render(<ArchetypePanel {...defaultProps} />);

    // The first key card name is also the archetype name, so check the others
    expect(screen.getByText("Rare Candy")).toBeInTheDocument();
    expect(screen.getByText("Arven")).toBeInTheDocument();
  });

  it("should render key card inclusion rates", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByText("98%")).toBeInTheDocument();
    expect(screen.getByText("95%")).toBeInTheDocument();
    expect(screen.getByText("92%")).toBeInTheDocument();
  });

  it("should render key card average copies", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByText("2.5x")).toBeInTheDocument();
    expect(screen.getByText("4.0x")).toBeInTheDocument();
    expect(screen.getByText("3.1x")).toBeInTheDocument();
  });

  it("should render the Build Variants section", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByText("Build Variants")).toBeInTheDocument();
  });

  it("should render build variant names and descriptions", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByText("Pidgeot Build")).toBeInTheDocument();
    expect(
      screen.getByText("Uses Pidgeot for consistency")
    ).toBeInTheDocument();
    expect(screen.getByText("Bibarel Build")).toBeInTheDocument();
    expect(
      screen.getByText("Uses Bibarel for draw support")
    ).toBeInTheDocument();
  });

  it("should render build variant share percentages", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByText("65%")).toBeInTheDocument();
    expect(screen.getByText("35%")).toBeInTheDocument();
  });

  it("should render the Matchup Spread section", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByText("Matchup Spread")).toBeInTheDocument();
    expect(screen.getByTestId("matchup-spread")).toBeInTheDocument();
  });

  it("should render the Recent Results section", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByText("Recent Results")).toBeInTheDocument();
  });

  it("should render recent result tournament names and placements", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByText("Regional Charlotte")).toBeInTheDocument();
    expect(screen.getByText("1st")).toBeInTheDocument();
    expect(screen.getByText("League Cup Austin")).toBeInTheDocument();
    expect(screen.getByText("Top 4")).toBeInTheDocument();
  });

  it("should render recent result dates", () => {
    render(<ArchetypePanel {...defaultProps} />);

    expect(screen.getByText("2024-01-15")).toBeInTheDocument();
    expect(screen.getByText("2024-01-10")).toBeInTheDocument();
  });

  it("should render the Build This Deck CTA link", () => {
    render(<ArchetypePanel {...defaultProps} />);

    const buildLink = screen.getByText("Build This Deck").closest("a");
    expect(buildLink).toHaveAttribute(
      "href",
      "/decks/new?archetype=Charizard%20ex"
    );
  });

  it("should limit key cards to 8", () => {
    const manyKeyCards = Array.from({ length: 12 }, (_, i) => ({
      name: `Card ${i + 1}`,
      inclusionRate: 0.9 - i * 0.05,
      avgCopies: 3.0,
    }));

    render(
      <ArchetypePanel
        {...defaultProps}
        archetype={{ ...mockArchetype, keyCards: manyKeyCards }}
      />
    );

    // Should show only first 8
    expect(screen.getByText("Card 8")).toBeInTheDocument();
    expect(screen.queryByText("Card 9")).not.toBeInTheDocument();
  });

  it("should limit recent results to 5", () => {
    const manyResults = Array.from({ length: 8 }, (_, i) => ({
      tournament: `Tournament ${i + 1}`,
      placement: `${i + 1}th`,
      date: `2024-01-${String(i + 1).padStart(2, "0")}`,
    }));

    render(
      <ArchetypePanel
        {...defaultProps}
        archetype={{ ...mockArchetype, recentResults: manyResults }}
      />
    );

    expect(screen.getByText("Tournament 5")).toBeInTheDocument();
    expect(screen.queryByText("Tournament 6")).not.toBeInTheDocument();
  });
});
