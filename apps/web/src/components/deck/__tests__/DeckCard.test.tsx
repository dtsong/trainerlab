import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DeckCard } from "../DeckCard";
import type { SavedDeck } from "@/types/deck";
import type { ApiCardSummary } from "@trainerlab/shared-types";

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

// Mock next/image
vi.mock("next/image", () => ({
  default: (props: Record<string, unknown>) => <img {...props} />,
}));

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

function createMockDeck(overrides: Partial<SavedDeck> = {}): SavedDeck {
  return {
    id: "deck-1",
    name: "Electric Surge",
    description: "A powerful electric deck",
    format: "standard",
    cards: [
      {
        card: createMockCard(),
        quantity: 4,
        position: 0,
      },
      {
        card: createMockCard({
          id: "swsh1-2",
          name: "Raichu",
          image_small: "https://example.com/raichu.png",
        }),
        quantity: 2,
        position: 1,
      },
      {
        card: createMockCard({
          id: "swsh1-3",
          name: "Professor's Research",
          supertype: "Trainer",
          image_small: "https://example.com/professor.png",
        }),
        quantity: 4,
        position: 2,
      },
    ],
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-02T00:00:00Z",
    ...overrides,
  };
}

describe("DeckCard", () => {
  it("should render the deck name", () => {
    const deck = createMockDeck();
    render(<DeckCard deck={deck} />);
    expect(screen.getByText("Electric Surge")).toBeInTheDocument();
  });

  it("should render the deck description", () => {
    const deck = createMockDeck();
    render(<DeckCard deck={deck} />);
    expect(screen.getByText("A powerful electric deck")).toBeInTheDocument();
  });

  it("should not render description when empty", () => {
    const deck = createMockDeck({ description: "" });
    render(<DeckCard deck={deck} />);
    expect(
      screen.queryByText("A powerful electric deck")
    ).not.toBeInTheDocument();
  });

  describe("format badge", () => {
    it("should show 'Standard' badge for standard format", () => {
      const deck = createMockDeck({ format: "standard" });
      render(<DeckCard deck={deck} />);
      expect(screen.getByText("Standard")).toBeInTheDocument();
    });

    it("should show 'Expanded' badge for expanded format", () => {
      const deck = createMockDeck({ format: "expanded" });
      render(<DeckCard deck={deck} />);
      expect(screen.getByText("Expanded")).toBeInTheDocument();
    });
  });

  describe("card count", () => {
    it("should display total card count", () => {
      const deck = createMockDeck();
      // 4 + 2 + 4 = 10 cards
      render(<DeckCard deck={deck} />);
      expect(screen.getByText("10 cards")).toBeInTheDocument();
    });

    it("should use singular 'card' for count of 1", () => {
      const deck = createMockDeck({
        cards: [
          {
            card: createMockCard(),
            quantity: 1,
            position: 0,
          },
        ],
      });
      render(<DeckCard deck={deck} />);
      expect(screen.getByText("1 card")).toBeInTheDocument();
    });

    it("should display 0 cards when deck is empty", () => {
      const deck = createMockDeck({ cards: [] });
      render(<DeckCard deck={deck} />);
      expect(screen.getByText("0 cards")).toBeInTheDocument();
    });
  });

  describe("featured card images", () => {
    it("should render featured card images for Pokemon cards", () => {
      const deck = createMockDeck();
      render(<DeckCard deck={deck} />);

      const images = document.querySelectorAll("img");
      expect(images.length).toBeGreaterThan(0);
    });

    it("should show up to 3 featured cards", () => {
      const deck = createMockDeck({
        cards: [
          {
            card: createMockCard({ id: "p1", name: "Pikachu" }),
            quantity: 4,
            position: 0,
          },
          {
            card: createMockCard({ id: "p2", name: "Raichu" }),
            quantity: 3,
            position: 1,
          },
          {
            card: createMockCard({ id: "p3", name: "Jolteon" }),
            quantity: 2,
            position: 2,
          },
          {
            card: createMockCard({ id: "p4", name: "Zapdos" }),
            quantity: 1,
            position: 3,
          },
        ],
      });
      render(<DeckCard deck={deck} />);

      const images = document.querySelectorAll("img");
      expect(images.length).toBe(3);
    });

    it("should show 'No cards' text when deck has no cards", () => {
      const deck = createMockDeck({ cards: [] });
      render(<DeckCard deck={deck} />);
      expect(screen.getByText("No cards")).toBeInTheDocument();
    });

    it("should fill featured slots with non-Pokemon if not enough Pokemon", () => {
      const deck = createMockDeck({
        cards: [
          {
            card: createMockCard({
              id: "p1",
              name: "Pikachu",
              supertype: "Pokemon",
            }),
            quantity: 2,
            position: 0,
          },
          {
            card: createMockCard({
              id: "t1",
              name: "Pokeball",
              supertype: "Trainer",
            }),
            quantity: 4,
            position: 1,
          },
          {
            card: createMockCard({
              id: "e1",
              name: "Lightning Energy",
              supertype: "Energy",
            }),
            quantity: 4,
            position: 2,
          },
        ],
      });
      render(<DeckCard deck={deck} />);

      const images = document.querySelectorAll("img");
      // 1 Pokemon + 2 non-Pokemon = 3 featured
      expect(images.length).toBe(3);
    });

    it("should handle cards with null image_small gracefully", () => {
      const deck = createMockDeck({
        cards: [
          {
            card: createMockCard({
              id: "p1",
              name: "Pikachu",
              image_small: null,
            }),
            quantity: 2,
            position: 0,
          },
        ],
      });
      render(<DeckCard deck={deck} />);

      // Should not crash; image placeholder shown instead
      const images = document.querySelectorAll("img");
      expect(images.length).toBe(0);
    });
  });

  describe("action buttons", () => {
    it("should render View button linking to deck detail", () => {
      const deck = createMockDeck({ id: "deck-42" });
      render(<DeckCard deck={deck} />);

      const viewLink = screen.getByText("View").closest("a");
      expect(viewLink).toHaveAttribute("href", "/decks/deck-42");
    });

    it("should render Edit button linking to deck edit", () => {
      const deck = createMockDeck({ id: "deck-42" });
      render(<DeckCard deck={deck} />);

      const editLink = screen.getByText("Edit").closest("a");
      expect(editLink).toHaveAttribute("href", "/decks/deck-42?edit=true");
    });
  });
});
