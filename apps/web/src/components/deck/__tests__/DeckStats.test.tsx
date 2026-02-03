import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { DeckStats } from "../DeckStats";
import { useDeckStore } from "@/stores/deckStore";
import type { ApiCardSummary } from "@trainerlab/shared-types";

function createMockCard(
  overrides: Partial<ApiCardSummary> = {}
): ApiCardSummary {
  return {
    id: "swsh1-1",
    name: "Test Card",
    supertype: "Pokemon",
    types: ["Lightning"],
    set_id: "swsh1",
    rarity: "Common",
    image_small: null,
    ...overrides,
  };
}

function createBasicEnergyCard(): ApiCardSummary {
  return {
    id: "swsh1-energy",
    name: "Lightning Energy",
    supertype: "Energy",
    types: ["Lightning"],
    set_id: "swsh1",
    rarity: null,
    image_small: null,
  };
}

describe("DeckStats", () => {
  beforeEach(() => {
    useDeckStore.setState({
      cards: [],
      name: "",
      description: "",
      format: "standard",
      isModified: false,
    });
  });

  it("should show 0/60 for empty deck", () => {
    render(<DeckStats />);

    expect(screen.getByText("0/60")).toBeInTheDocument();
  });

  it("should show correct total count", () => {
    useDeckStore.getState().addCard(createMockCard({ id: "p1" }));
    useDeckStore.getState().addCard(createMockCard({ id: "p1" }));
    useDeckStore.getState().addCard(createMockCard({ id: "p2" }));

    render(<DeckStats />);

    expect(screen.getByText("3/60")).toBeInTheDocument();
  });

  it("should show Pokemon count", () => {
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "p2", supertype: "Pokemon" }));

    render(<DeckStats />);

    // Find the parent container of "Pokemon" label and check for count
    const pokemonLabel = screen.getByText("Pokemon");
    const container = pokemonLabel.parentElement;
    expect(container).toHaveTextContent("2");
  });

  it("should show Trainer count", () => {
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "t1", supertype: "Trainer" }));

    render(<DeckStats />);

    const trainerLabel = screen.getByText("Trainer");
    const container = trainerLabel.parentElement;
    expect(container).toHaveTextContent("1");
  });

  it("should show Energy count", () => {
    useDeckStore.getState().addCard(createBasicEnergyCard());
    useDeckStore.getState().addCard(createBasicEnergyCard());
    useDeckStore.getState().addCard(createBasicEnergyCard());

    render(<DeckStats />);

    const energyLabel = screen.getByText("Energy");
    const container = energyLabel.parentElement;
    expect(container).toHaveTextContent("3");
  });

  it("should show 'Need X more cards' when under 60", () => {
    useDeckStore.getState().addCard(createMockCard({ id: "p1" }));

    render(<DeckStats />);

    expect(screen.getByText("Need 59 more cards")).toBeInTheDocument();
  });

  it("should show 'Deck is valid' when exactly 60 cards", () => {
    // Add 60 basic energy cards
    const energy = createBasicEnergyCard();
    for (let i = 0; i < 60; i++) {
      useDeckStore.getState().addCard(energy);
    }

    render(<DeckStats />);

    expect(screen.getByText("Deck is valid")).toBeInTheDocument();
  });

  it("should have progress bar with correct aria attributes", () => {
    useDeckStore.getState().addCard(createMockCard({ id: "p1" }));
    useDeckStore.getState().addCard(createMockCard({ id: "p2" }));

    render(<DeckStats />);

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-valuenow", "2");
    expect(progressBar).toHaveAttribute("aria-valuemin", "0");
    expect(progressBar).toHaveAttribute("aria-valuemax", "60");
  });

  it("should handle singular form for 'Need 1 more card'", () => {
    // Add 59 basic energy cards
    const energy = createBasicEnergyCard();
    for (let i = 0; i < 59; i++) {
      useDeckStore.getState().addCard(energy);
    }

    render(<DeckStats />);

    expect(screen.getByText("Need 1 more card")).toBeInTheDocument();
  });
});
