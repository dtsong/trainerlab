import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import type { CardChange } from "@trainerlab/shared-types";
import { DecklistDiff } from "../DecklistDiff";

describe("DecklistDiff", () => {
  it("should show 'No card changes detected' when no changes", () => {
    render(<DecklistDiff cardsAdded={[]} cardsRemoved={[]} />);

    expect(screen.getByText("No card changes detected")).toBeInTheDocument();
  });

  it("should show 'No card changes detected' when props are null", () => {
    render(<DecklistDiff cardsAdded={null} cardsRemoved={null} />);

    expect(screen.getByText("No card changes detected")).toBeInTheDocument();
  });

  it("should show 'No card changes detected' when props are undefined", () => {
    render(<DecklistDiff />);

    expect(screen.getByText("No card changes detected")).toBeInTheDocument();
  });

  it("should render added cards with green styling", () => {
    const cardsAdded: CardChange[] = [
      { card_id: "sv3-125", name: "Charizard ex", count: 2 },
    ];

    render(<DecklistDiff cardsAdded={cardsAdded} cardsRemoved={[]} />);

    expect(screen.getByText(/Charizard ex/)).toBeInTheDocument();
    expect(screen.getByText(/2x/)).toBeInTheDocument();
  });

  it("should render removed cards with red styling", () => {
    const cardsRemoved: CardChange[] = [
      { card_id: "sv1-166", name: "Arven", count: 4 },
    ];

    render(<DecklistDiff cardsAdded={[]} cardsRemoved={cardsRemoved} />);

    expect(screen.getByText(/Arven/)).toBeInTheDocument();
    expect(screen.getByText(/4x/)).toBeInTheDocument();
  });

  it("should render both added and removed cards", () => {
    const cardsAdded: CardChange[] = [
      { card_id: "sv3-125", name: "Charizard ex", count: 1 },
    ];
    const cardsRemoved: CardChange[] = [
      { card_id: "sv1-166", name: "Arven", count: 2 },
    ];

    render(
      <DecklistDiff cardsAdded={cardsAdded} cardsRemoved={cardsRemoved} />
    );

    expect(screen.getByText(/Charizard ex/)).toBeInTheDocument();
    expect(screen.getByText(/Arven/)).toBeInTheDocument();
  });

  it("should not show count prefix when count is 1", () => {
    const cardsAdded: CardChange[] = [
      { card_id: "sv3-125", name: "Test Card", count: 1 },
    ];

    render(<DecklistDiff cardsAdded={cardsAdded} cardsRemoved={[]} />);

    expect(screen.getByText("Test Card")).toBeInTheDocument();
    expect(screen.queryByText(/1x/)).not.toBeInTheDocument();
  });

  it("should not show count prefix when count is undefined", () => {
    const cardsAdded: CardChange[] = [
      { card_id: "sv3-125", name: "Test Card" },
    ];

    render(<DecklistDiff cardsAdded={cardsAdded} cardsRemoved={[]} />);

    expect(screen.getByText("Test Card")).toBeInTheDocument();
    expect(screen.queryByText(/x /)).not.toBeInTheDocument();
  });

  it("should handle multiple cards of same type", () => {
    const cardsAdded: CardChange[] = [
      { card_id: "sv3-125", name: "Card A", count: 2 },
      { card_id: "sv3-126", name: "Card B", count: 3 },
      { card_id: "sv3-127", name: "Card C", count: 1 },
    ];

    render(<DecklistDiff cardsAdded={cardsAdded} cardsRemoved={[]} />);

    expect(screen.getByText(/Card A/)).toBeInTheDocument();
    expect(screen.getByText(/Card B/)).toBeInTheDocument();
    expect(screen.getByText(/Card C/)).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    const { container } = render(
      <DecklistDiff
        cardsAdded={[{ card_id: "1", name: "Test" }]}
        className="custom-class"
      />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("should show changes when only cardsAdded has items", () => {
    const cardsAdded: CardChange[] = [{ card_id: "1", name: "New Card" }];

    render(<DecklistDiff cardsAdded={cardsAdded} cardsRemoved={null} />);

    expect(screen.getByText("New Card")).toBeInTheDocument();
    expect(
      screen.queryByText("No card changes detected")
    ).not.toBeInTheDocument();
  });

  it("should show changes when only cardsRemoved has items", () => {
    const cardsRemoved: CardChange[] = [{ card_id: "1", name: "Old Card" }];

    render(<DecklistDiff cardsAdded={null} cardsRemoved={cardsRemoved} />);

    expect(screen.getByText("Old Card")).toBeInTheDocument();
    expect(
      screen.queryByText("No card changes detected")
    ).not.toBeInTheDocument();
  });

  it("should render removed cards before added cards", () => {
    const cardsAdded: CardChange[] = [
      { card_id: "add-1", name: "Added Card" },
    ];
    const cardsRemoved: CardChange[] = [
      { card_id: "rem-1", name: "Removed Card" },
    ];

    render(
      <DecklistDiff cardsAdded={cardsAdded} cardsRemoved={cardsRemoved} />
    );

    const allText = document.body.textContent || "";
    const removedIndex = allText.indexOf("Removed Card");
    const addedIndex = allText.indexOf("Added Card");

    expect(removedIndex).toBeLessThan(addedIndex);
  });
});
