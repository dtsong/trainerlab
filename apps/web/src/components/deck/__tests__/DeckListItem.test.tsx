import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeckListItem } from "../DeckListItem";
import type { DeckCard } from "@/types/deck";
import type { ApiCardSummary } from "@trainerlab/shared-types";

function createMockDeckCard(
  overrides: Partial<ApiCardSummary> = {},
  quantity = 1
): DeckCard {
  return {
    card: {
      id: "swsh1-1",
      name: "Pikachu",
      supertype: "Pokemon",
      types: ["Lightning"],
      set_id: "swsh1",
      rarity: "Common",
      image_small: "https://example.com/pikachu.png",
      ...overrides,
    },
    quantity,
    position: 0,
  };
}

describe("DeckListItem", () => {
  it("should render card name and supertype", () => {
    const deckCard = createMockDeckCard();
    render(
      <DeckListItem
        deckCard={deckCard}
        onQuantityChange={vi.fn()}
        onRemove={vi.fn()}
      />
    );

    expect(screen.getByText("Pikachu")).toBeInTheDocument();
    expect(screen.getByText("Pokemon - Lightning")).toBeInTheDocument();
  });

  it("should display quantity", () => {
    const deckCard = createMockDeckCard({}, 3);
    render(
      <DeckListItem
        deckCard={deckCard}
        onQuantityChange={vi.fn()}
        onRemove={vi.fn()}
      />
    );

    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("should call onQuantityChange when + is clicked", async () => {
    const user = userEvent.setup();
    const onQuantityChange = vi.fn();
    const deckCard = createMockDeckCard();

    render(
      <DeckListItem
        deckCard={deckCard}
        onQuantityChange={onQuantityChange}
        onRemove={vi.fn()}
      />
    );

    await user.click(screen.getByLabelText("Increase quantity"));
    expect(onQuantityChange).toHaveBeenCalledWith("swsh1-1", 1);
  });

  it("should call onQuantityChange when - is clicked", async () => {
    const user = userEvent.setup();
    const onQuantityChange = vi.fn();
    const deckCard = createMockDeckCard({}, 2);

    render(
      <DeckListItem
        deckCard={deckCard}
        onQuantityChange={onQuantityChange}
        onRemove={vi.fn()}
      />
    );

    await user.click(screen.getByLabelText("Decrease quantity"));
    expect(onQuantityChange).toHaveBeenCalledWith("swsh1-1", -1);
  });

  it("should disable - button when quantity is 1", () => {
    const deckCard = createMockDeckCard({}, 1);
    render(
      <DeckListItem
        deckCard={deckCard}
        onQuantityChange={vi.fn()}
        onRemove={vi.fn()}
      />
    );

    expect(screen.getByLabelText("Decrease quantity")).toBeDisabled();
  });

  it("should call onRemove when delete is clicked", async () => {
    const user = userEvent.setup();
    const onRemove = vi.fn();
    const deckCard = createMockDeckCard();

    render(
      <DeckListItem
        deckCard={deckCard}
        onQuantityChange={vi.fn()}
        onRemove={onRemove}
      />
    );

    await user.click(screen.getByLabelText("Remove card"));
    expect(onRemove).toHaveBeenCalledWith("swsh1-1");
  });

  it("should link to card detail page", () => {
    const deckCard = createMockDeckCard();
    render(
      <DeckListItem
        deckCard={deckCard}
        onQuantityChange={vi.fn()}
        onRemove={vi.fn()}
      />
    );

    const links = screen.getAllByRole("link");
    expect(links[0]).toHaveAttribute("href", "/investigate/card/swsh1-1");
  });

  it("should handle card without types", () => {
    const deckCard = createMockDeckCard({ types: null });
    render(
      <DeckListItem
        deckCard={deckCard}
        onQuantityChange={vi.fn()}
        onRemove={vi.fn()}
      />
    );

    expect(screen.getByText("Pokemon")).toBeInTheDocument();
  });
});
