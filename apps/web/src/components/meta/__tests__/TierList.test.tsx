import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TierList, type ArchetypeData } from "../TierList";

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
vi.mock("@/components/ui/tier-badge", () => ({
  TierBadge: ({ tier }: { tier: string }) => (
    <span data-testid={`tier-badge-${tier}`}>{tier}</span>
  ),
}));

vi.mock("@/components/ui/trend-arrow", () => ({
  TrendArrow: ({ direction }: { direction: string }) => (
    <span data-testid="trend-arrow">{direction}</span>
  ),
}));

vi.mock("@/components/ui/jp-signal-badge", () => ({
  JPSignalBadge: () => <span data-testid="jp-signal-badge">JP Signal</span>,
}));

describe("TierList", () => {
  const mockArchetypes: ArchetypeData[] = [
    {
      id: "charizard",
      name: "Charizard ex",
      tier: "S",
      share: 15.3,
      trend: "up",
      trendValue: 2.1,
    },
    {
      id: "lugia",
      name: "Lugia VSTAR",
      tier: "A",
      share: 10.5,
      trend: "stable",
    },
    {
      id: "gardevoir",
      name: "Gardevoir ex",
      tier: "A",
      share: 9.8,
      trend: "down",
      trendValue: -1.5,
    },
    {
      id: "miraidon",
      name: "Miraidon ex",
      tier: "B",
      share: 5.2,
      trend: "up",
      trendValue: 0.8,
    },
    {
      id: "rogue",
      name: "Rogue Deck",
      tier: "Rogue",
      share: 1.2,
      trend: "stable",
    },
  ];

  const defaultProps = {
    archetypes: mockArchetypes,
    onArchetypeSelect: vi.fn(),
  };

  it("should render the tier list with listbox role", () => {
    render(<TierList {...defaultProps} />);

    expect(screen.getByRole("listbox")).toBeInTheDocument();
    expect(screen.getByRole("listbox")).toHaveAttribute(
      "aria-label",
      "Meta tier list"
    );
  });

  it("should render archetype names", () => {
    render(<TierList {...defaultProps} />);

    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    expect(screen.getByText("Lugia VSTAR")).toBeInTheDocument();
    expect(screen.getByText("Gardevoir ex")).toBeInTheDocument();
    expect(screen.getByText("Miraidon ex")).toBeInTheDocument();
    expect(screen.getByText("Rogue Deck")).toBeInTheDocument();
  });

  it("should render share percentages", () => {
    render(<TierList {...defaultProps} />);

    expect(screen.getByText("15.3%")).toBeInTheDocument();
    expect(screen.getByText("10.5%")).toBeInTheDocument();
    expect(screen.getByText("9.8%")).toBeInTheDocument();
    expect(screen.getByText("5.2%")).toBeInTheDocument();
    expect(screen.getByText("1.2%")).toBeInTheDocument();
  });

  it("should render tier badges for populated tiers", () => {
    render(<TierList {...defaultProps} />);

    expect(screen.getByTestId("tier-badge-S")).toBeInTheDocument();
    expect(screen.getByTestId("tier-badge-A")).toBeInTheDocument();
    expect(screen.getByTestId("tier-badge-B")).toBeInTheDocument();
    expect(screen.getByTestId("tier-badge-Rogue")).toBeInTheDocument();
  });

  it("should show deck count per tier", () => {
    render(<TierList {...defaultProps} />);

    // S tier, B tier, and Rogue each have 1 deck
    const singleDeckLabels = screen.getAllByText("1 deck");
    expect(singleDeckLabels.length).toBe(3);
    // A tier has 2 decks
    expect(screen.getByText("2 decks")).toBeInTheDocument();
  });

  it("should call onArchetypeSelect when an archetype is clicked", async () => {
    const onArchetypeSelect = vi.fn();
    const user = userEvent.setup();
    render(
      <TierList {...defaultProps} onArchetypeSelect={onArchetypeSelect} />
    );

    await user.click(screen.getByText("Charizard ex"));

    expect(onArchetypeSelect).toHaveBeenCalledWith(mockArchetypes[0]);
  });

  it("should highlight the selected archetype", () => {
    render(<TierList {...defaultProps} selectedArchetypeId="charizard" />);

    const charizardButton = screen.getByText("Charizard ex").closest("button");
    expect(charizardButton).toHaveAttribute("aria-pressed", "true");
  });

  it("should not highlight unselected archetypes", () => {
    render(<TierList {...defaultProps} selectedArchetypeId="charizard" />);

    const lugiaButton = screen.getByText("Lugia VSTAR").closest("button");
    expect(lugiaButton).toHaveAttribute("aria-pressed", "false");
  });

  it("should not render empty tier sections", () => {
    const archetypesWithoutC: ArchetypeData[] = [
      {
        id: "charizard",
        name: "Charizard ex",
        tier: "S",
        share: 15.3,
        trend: "up",
      },
    ];
    render(
      <TierList archetypes={archetypesWithoutC} onArchetypeSelect={vi.fn()} />
    );

    // C tier badge should not be rendered since there are no C tier decks
    expect(screen.queryByTestId("tier-badge-C")).not.toBeInTheDocument();
  });

  it("should show JP signal badge when JP share diverges significantly", () => {
    const archetypesWithJP: ArchetypeData[] = [
      {
        id: "test",
        name: "JP Divergent Deck",
        tier: "S",
        share: 10,
        trend: "up",
        jpShare: 25, // 15% difference > 5% threshold
      },
    ];
    render(
      <TierList archetypes={archetypesWithJP} onArchetypeSelect={vi.fn()} />
    );

    expect(screen.getByTestId("jp-signal-badge")).toBeInTheDocument();
  });

  it("should not show JP signal badge when JP share is close", () => {
    const archetypesWithCloseJP: ArchetypeData[] = [
      {
        id: "test",
        name: "Close JP Deck",
        tier: "S",
        share: 10,
        trend: "up",
        jpShare: 12, // 2% difference < 5% threshold
      },
    ];
    render(
      <TierList
        archetypes={archetypesWithCloseJP}
        onArchetypeSelect={vi.fn()}
      />
    );

    expect(screen.queryByTestId("jp-signal-badge")).not.toBeInTheDocument();
  });

  it("should apply custom className", () => {
    render(<TierList {...defaultProps} className="custom-class" />);

    expect(screen.getByRole("listbox")).toHaveClass("custom-class");
  });
});
