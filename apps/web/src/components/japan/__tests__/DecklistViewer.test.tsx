import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DecklistViewer } from "../DecklistViewer";
import type { ApiDecklistResponse } from "@trainerlab/shared-types";

const mockDecklist: ApiDecklistResponse = {
  placement_id: "test-id",
  player_name: "Taro",
  archetype: "Charizard ex",
  tournament_name: "City League Tokyo",
  tournament_date: "2024-03-10",
  source_url: "https://limitlesstcg.com/decks/abc",
  cards: [
    {
      card_id: "sv4-6",
      card_name: "Charizard ex",
      quantity: 3,
      supertype: "Pokemon",
    },
    {
      card_id: "sv3-12",
      card_name: "Charmander",
      quantity: 4,
      supertype: "Pokemon",
    },
    {
      card_id: "sv1-198",
      card_name: "Rare Candy",
      quantity: 4,
      supertype: "Trainer",
    },
    {
      card_id: "sv1-199",
      card_name: "Nest Ball",
      quantity: 4,
      supertype: "Trainer",
    },
    {
      card_id: "energy-1",
      card_name: "Fire Energy",
      quantity: 10,
      supertype: "Energy",
    },
  ],
  total_cards: 25,
};

describe("DecklistViewer", () => {
  it("should render the decklist viewer", () => {
    render(<DecklistViewer decklist={mockDecklist} />);
    expect(screen.getByTestId("decklist-viewer")).toBeInTheDocument();
  });

  it("should display player name and archetype", () => {
    render(<DecklistViewer decklist={mockDecklist} />);
    expect(screen.getByText("Taro")).toBeInTheDocument();
    // "Charizard ex" appears as both archetype badge and card name
    expect(screen.getAllByText("Charizard ex").length).toBeGreaterThanOrEqual(
      1
    );
  });

  it("should display total card count", () => {
    render(<DecklistViewer decklist={mockDecklist} />);
    expect(screen.getByText("25 cards")).toBeInTheDocument();
  });

  it("should group cards by supertype", () => {
    render(<DecklistViewer decklist={mockDecklist} />);
    expect(screen.getByText("Pokemon (7)")).toBeInTheDocument();
    expect(screen.getByText("Trainer (8)")).toBeInTheDocument();
    expect(screen.getByText("Energy (10)")).toBeInTheDocument();
  });

  it("should show card names with quantities", () => {
    render(<DecklistViewer decklist={mockDecklist} />);
    expect(screen.getByText("Rare Candy")).toBeInTheDocument();
    expect(screen.getByText("Fire Energy")).toBeInTheDocument();
    expect(screen.getByText("Charmander")).toBeInTheDocument();
  });

  it("should render Limitless link when source_url is present", () => {
    render(<DecklistViewer decklist={mockDecklist} />);
    const link = screen.getByText("View on Limitless");
    expect(link.closest("a")).toHaveAttribute(
      "href",
      "https://limitlesstcg.com/decks/abc"
    );
  });

  it("should not render Limitless link when source_url is null", () => {
    const noSource = { ...mockDecklist, source_url: null };
    render(<DecklistViewer decklist={noSource} />);
    expect(screen.queryByText("View on Limitless")).not.toBeInTheDocument();
  });

  it("should handle decklist with no player name", () => {
    const noPlayer = { ...mockDecklist, player_name: null };
    render(<DecklistViewer decklist={noPlayer} />);
    expect(screen.queryByText("Taro")).not.toBeInTheDocument();
  });

  it("should handle cards with null supertype as Trainer", () => {
    const decklist: ApiDecklistResponse = {
      ...mockDecklist,
      cards: [
        {
          card_id: "x1",
          card_name: "Mystery Card",
          quantity: 2,
          supertype: null,
        },
      ],
      total_cards: 2,
    };
    render(<DecklistViewer decklist={decklist} />);
    expect(screen.getByText("Trainer (2)")).toBeInTheDocument();
  });

  describe("energy collapsing", () => {
    it("should collapse same-name energy cards from different sets", () => {
      const decklist: ApiDecklistResponse = {
        ...mockDecklist,
        cards: [
          {
            card_id: "sve-2",
            card_name: "Fire Energy",
            quantity: 6,
            supertype: "Energy",
            set_id: "sve",
          },
          {
            card_id: "svi-1",
            card_name: "Fire Energy",
            quantity: 4,
            supertype: "Energy",
            set_id: "svi",
          },
        ],
        total_cards: 10,
      };
      render(<DecklistViewer decklist={decklist} />);
      expect(screen.getByText("Energy (10)")).toBeInTheDocument();
      // Should show single collapsed entry
      const items = screen.getAllByText("Fire Energy");
      expect(items).toHaveLength(1);
      expect(screen.getByText("10x")).toBeInTheDocument();
    });

    it("should collapse Basic prefix energy into same name", () => {
      const decklist: ApiDecklistResponse = {
        ...mockDecklist,
        cards: [
          {
            card_id: "sve-2",
            card_name: "Basic Fire Energy",
            quantity: 5,
            supertype: "Energy",
          },
          {
            card_id: "svi-1",
            card_name: "Fire Energy",
            quantity: 3,
            supertype: "Energy",
          },
        ],
        total_cards: 8,
      };
      render(<DecklistViewer decklist={decklist} />);
      expect(screen.getByText("Energy (8)")).toBeInTheDocument();
      const items = screen.getAllByText("Fire Energy");
      expect(items).toHaveLength(1);
      expect(screen.getByText("8x")).toBeInTheDocument();
    });

    it("should keep different energy types separate", () => {
      const decklist: ApiDecklistResponse = {
        ...mockDecklist,
        cards: [
          {
            card_id: "sve-2",
            card_name: "Fire Energy",
            quantity: 6,
            supertype: "Energy",
          },
          {
            card_id: "sve-3",
            card_name: "Water Energy",
            quantity: 4,
            supertype: "Energy",
          },
        ],
        total_cards: 10,
      };
      render(<DecklistViewer decklist={decklist} />);
      expect(screen.getByText("Fire Energy")).toBeInTheDocument();
      expect(screen.getByText("Water Energy")).toBeInTheDocument();
    });
  });

  describe("unreleased card indicators", () => {
    it("should show JP set badge for POR-prefixed cards", () => {
      const decklist: ApiDecklistResponse = {
        ...mockDecklist,
        cards: [
          {
            card_id: "POR-042",
            card_name: "Meowth ex",
            quantity: 3,
            supertype: "Pokemon",
            set_id: "POR",
            set_name: null,
          },
        ],
        total_cards: 3,
      };
      render(<DecklistViewer decklist={decklist} />);
      expect(screen.getByText("POR")).toBeInTheDocument();
    });

    it("should show set code with set name for unreleased cards", () => {
      const decklist: ApiDecklistResponse = {
        ...mockDecklist,
        cards: [
          {
            card_id: "POR-042",
            card_name: "Meowth ex",
            quantity: 3,
            supertype: "Pokemon",
            set_id: "ME03",
            set_name: "Perfect Order",
          },
        ],
        total_cards: 3,
      };
      render(<DecklistViewer decklist={decklist} />);
      expect(screen.getByText("ME03 Perfect Order")).toBeInTheDocument();
    });

    it("should not show badge for released cards", () => {
      const decklist: ApiDecklistResponse = {
        ...mockDecklist,
        cards: [
          {
            card_id: "sv4-6",
            card_name: "Charizard ex",
            quantity: 3,
            supertype: "Pokemon",
            set_id: "sv4",
            set_name: "Paradox Rift",
          },
        ],
        total_cards: 3,
      };
      render(<DecklistViewer decklist={decklist} />);
      expect(screen.queryByText("sv4")).not.toBeInTheDocument();
      expect(screen.queryByText("Paradox Rift")).not.toBeInTheDocument();
    });
  });
});
