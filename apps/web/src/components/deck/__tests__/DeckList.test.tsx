import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeckList } from "../DeckList";
import { useDeckStore } from "@/stores/deckStore";
import type { ApiCardSummary } from "@trainerlab/shared-types";

function createMockCard(
  overrides: Partial<ApiCardSummary> = {}
): ApiCardSummary {
  return {
    id: "swsh1-1",
    name: "Pikachu",
    supertype: "Pokemon",
    types: ["Lightning"],
    set_id: "swsh1",
    rarity: "Common",
    image_small: "https://example.com/pikachu.png",
    ...overrides,
  };
}

describe("DeckList", () => {
  beforeEach(() => {
    useDeckStore.setState({
      cards: [],
      name: "",
      description: "",
      format: "standard",
      isModified: false,
    });
  });

  it("should show empty state when no cards", () => {
    render(<DeckList />);

    expect(screen.getByText("No cards in deck")).toBeInTheDocument();
    expect(screen.getByText("Click cards to add them")).toBeInTheDocument();
  });

  it("should display cards grouped by supertype", () => {
    // Add cards of different types
    useDeckStore
      .getState()
      .addCard(
        createMockCard({ id: "p1", name: "Pikachu", supertype: "Pokemon" })
      );
    useDeckStore
      .getState()
      .addCard(
        createMockCard({ id: "t1", name: "Pokeball", supertype: "Trainer" })
      );
    useDeckStore.getState().addCard(
      createMockCard({
        id: "e1",
        name: "Lightning Energy",
        supertype: "Energy",
      })
    );

    render(<DeckList />);

    // Should have section headers
    expect(screen.getByText("Pokemon")).toBeInTheDocument();
    expect(screen.getByText("Trainer")).toBeInTheDocument();
    expect(screen.getByText("Energy")).toBeInTheDocument();

    // Should show card names
    expect(screen.getByText("Pikachu")).toBeInTheDocument();
    expect(screen.getByText("Pokeball")).toBeInTheDocument();
    expect(screen.getByText("Lightning Energy")).toBeInTheDocument();
  });

  it("should show counts per supertype", () => {
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "p1", supertype: "Pokemon" })); // qty 2
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "t1", supertype: "Trainer" }));

    render(<DeckList />);

    // Pokemon section should show count of 2
    const pokemonSection = screen.getByText("Pokemon").closest("header");
    expect(pokemonSection).toHaveTextContent("2");

    // Trainer section should show count of 1
    const trainerSection = screen.getByText("Trainer").closest("header");
    expect(trainerSection).toHaveTextContent("1");
  });

  it("should not show empty sections", () => {
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));

    render(<DeckList />);

    expect(screen.getByText("Pokemon")).toBeInTheDocument();
    expect(screen.queryByText("Trainer")).not.toBeInTheDocument();
    expect(screen.queryByText("Energy")).not.toBeInTheDocument();
  });

  it("should increment quantity when + is clicked", async () => {
    const user = userEvent.setup();
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));

    render(<DeckList />);

    await user.click(screen.getByLabelText("Increase quantity"));

    const state = useDeckStore.getState();
    expect(state.cards[0].quantity).toBe(2);
  });

  it("should decrement quantity when - is clicked", async () => {
    const user = userEvent.setup();
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "p1", supertype: "Pokemon" })); // qty 2

    render(<DeckList />);

    await user.click(screen.getByLabelText("Decrease quantity"));

    const state = useDeckStore.getState();
    expect(state.cards[0].quantity).toBe(1);
  });

  it("should remove all copies when delete is clicked", async () => {
    const user = userEvent.setup();
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "p1", supertype: "Pokemon" }));
    useDeckStore
      .getState()
      .addCard(createMockCard({ id: "p1", supertype: "Pokemon" })); // qty 3

    render(<DeckList />);

    await user.click(screen.getByLabelText("Remove card"));

    const state = useDeckStore.getState();
    expect(state.cards).toHaveLength(0);
  });
});
