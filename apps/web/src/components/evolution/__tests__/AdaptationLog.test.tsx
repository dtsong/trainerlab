import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AdaptationLog } from "../AdaptationLog";
import type { ApiAdaptation } from "@trainerlab/shared-types";

vi.mock("../DecklistDiff", () => ({
  DecklistDiff: ({
    cardsAdded,
    cardsRemoved,
  }: {
    cardsAdded: unknown;
    cardsRemoved: unknown;
  }) => (
    <div data-testid="decklist-diff">
      {cardsAdded ? "Added" : ""}
      {cardsRemoved ? "Removed" : ""}
    </div>
  ),
}));

const mockAdaptations: ApiAdaptation[] = [
  {
    id: "adapt-1",
    type: "tech",
    description: "Added Dusknoir for spread damage support",
    cards_added: [{ name: "Dusknoir", count: 2 }],
    cards_removed: [{ name: "Spiritomb", count: 1 }],
    target_archetype: "Charizard ex",
    confidence: 0.85,
  },
  {
    id: "adapt-2",
    type: "consistency",
    description: "Increased supporter count for reliability",
    cards_added: null,
    cards_removed: null,
    target_archetype: null,
    confidence: null,
  },
  {
    id: "adapt-3",
    type: "engine",
    description: "Switched to Pidgeot engine",
    cards_added: [{ name: "Pidgeot ex", count: 2 }],
    cards_removed: null,
    target_archetype: null,
    confidence: 0.92,
  },
];

describe("AdaptationLog", () => {
  it("should render empty state when no adaptations", () => {
    render(<AdaptationLog adaptations={[]} />);

    expect(screen.getByText("No adaptations detected")).toBeInTheDocument();
  });

  it("should render adaptation type badges", () => {
    render(<AdaptationLog adaptations={mockAdaptations} />);

    expect(screen.getByText("tech")).toBeInTheDocument();
    expect(screen.getByText("consistency")).toBeInTheDocument();
    expect(screen.getByText("engine")).toBeInTheDocument();
  });

  it("should render adaptation descriptions", () => {
    render(<AdaptationLog adaptations={mockAdaptations} />);

    expect(
      screen.getByText("Added Dusknoir for spread damage support")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Increased supporter count for reliability")
    ).toBeInTheDocument();
    expect(screen.getByText("Switched to Pidgeot engine")).toBeInTheDocument();
  });

  it("should display target archetype", () => {
    render(<AdaptationLog adaptations={mockAdaptations} />);

    expect(screen.getByText("vs Charizard ex")).toBeInTheDocument();
  });

  it("should display confidence percentage", () => {
    render(<AdaptationLog adaptations={mockAdaptations} />);

    expect(screen.getByText("85% confidence")).toBeInTheDocument();
    expect(screen.getByText("92% confidence")).toBeInTheDocument();
  });

  it("should not display target archetype when null", () => {
    render(<AdaptationLog adaptations={[mockAdaptations[1]]} />);

    expect(screen.queryByText(/^vs /)).not.toBeInTheDocument();
  });

  it("should not display confidence when null", () => {
    render(<AdaptationLog adaptations={[mockAdaptations[1]]} />);

    expect(screen.queryByText(/confidence/)).not.toBeInTheDocument();
  });

  it("should show expand button for adaptations with card diffs", () => {
    render(<AdaptationLog adaptations={[mockAdaptations[0]]} />);

    // The expand chevron should be visible for adaptations with cards_added/removed
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("should expand to show DecklistDiff on click", async () => {
    const user = userEvent.setup();

    render(<AdaptationLog adaptations={[mockAdaptations[0]]} />);

    expect(screen.queryByTestId("decklist-diff")).not.toBeInTheDocument();

    const button = screen.getByRole("button");
    await user.click(button);

    expect(screen.getByTestId("decklist-diff")).toBeInTheDocument();
  });

  it("should collapse DecklistDiff on second click", async () => {
    const user = userEvent.setup();

    render(<AdaptationLog adaptations={[mockAdaptations[0]]} />);

    const button = screen.getByRole("button");
    await user.click(button);
    expect(screen.getByTestId("decklist-diff")).toBeInTheDocument();

    await user.click(button);
    expect(screen.queryByTestId("decklist-diff")).not.toBeInTheDocument();
  });

  it("should not show DecklistDiff for adaptations without card changes", () => {
    render(<AdaptationLog adaptations={[mockAdaptations[1]]} />);

    // The consistency adaptation has no cards_added/removed
    expect(screen.queryByTestId("decklist-diff")).not.toBeInTheDocument();
  });

  it("should handle adaptation with only cards_added", async () => {
    const user = userEvent.setup();

    render(<AdaptationLog adaptations={[mockAdaptations[2]]} />);

    const button = screen.getByRole("button");
    await user.click(button);

    expect(screen.getByTestId("decklist-diff")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    const { container } = render(
      <AdaptationLog adaptations={mockAdaptations} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("should apply custom className to empty state", () => {
    const { container } = render(
      <AdaptationLog adaptations={[]} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("should handle unknown adaptation type gracefully", () => {
    const unknownType: ApiAdaptation[] = [
      {
        id: "adapt-unknown",
        type: "unknown-type",
        description: "Some unknown adaptation",
        cards_added: null,
        cards_removed: null,
        target_archetype: null,
        confidence: null,
      },
    ];

    render(<AdaptationLog adaptations={unknownType} />);

    expect(screen.getByText("unknown-type")).toBeInTheDocument();
    expect(screen.getByText("Some unknown adaptation")).toBeInTheDocument();
  });

  it("should handle adaptation without description", () => {
    const noDescription: ApiAdaptation[] = [
      {
        id: "adapt-no-desc",
        type: "removal",
        description: null,
        cards_added: null,
        cards_removed: null,
        target_archetype: null,
        confidence: null,
      },
    ];

    render(<AdaptationLog adaptations={noDescription} />);

    expect(screen.getByText("removal")).toBeInTheDocument();
  });

  it("should allow multiple adaptations to be expanded independently", async () => {
    const user = userEvent.setup();

    // Both adapt-1 and adapt-3 have card changes
    render(
      <AdaptationLog adaptations={[mockAdaptations[0], mockAdaptations[2]]} />
    );

    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(2);

    // Expand first
    await user.click(buttons[0]);
    expect(screen.getAllByTestId("decklist-diff")).toHaveLength(1);

    // Expand second
    await user.click(buttons[1]);
    expect(screen.getAllByTestId("decklist-diff")).toHaveLength(2);

    // Collapse first
    await user.click(buttons[0]);
    expect(screen.getAllByTestId("decklist-diff")).toHaveLength(1);
  });
});
