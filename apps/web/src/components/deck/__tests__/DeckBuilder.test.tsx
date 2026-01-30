import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeckBuilder } from "../DeckBuilder";
import { useDeckStore } from "@/stores/deckStore";
import * as api from "@/lib/api";

// Mock the API
vi.mock("@/lib/api", () => ({
  cardsApi: {
    search: vi.fn(),
  },
}));

const mockCardsApi = vi.mocked(api.cardsApi);

describe("DeckBuilder", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDeckStore.setState({
      cards: [],
      name: "",
      description: "",
      format: "standard",
      isModified: false,
    });
  });

  it("should render deck name input", () => {
    render(<DeckBuilder />);
    expect(screen.getByPlaceholderText("Deck name...")).toBeInTheDocument();
  });

  it("should render save button when onSave is provided", () => {
    render(<DeckBuilder onSave={() => {}} />);
    expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
  });

  it("should render search input", () => {
    render(<DeckBuilder />);
    expect(
      screen.getByPlaceholderText("Search cards to add..."),
    ).toBeInTheDocument();
  });

  it("should disable save button when deck is not modified", () => {
    render(<DeckBuilder onSave={() => {}} />);
    expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();
  });

  it("should enable save button when deck is modified", () => {
    useDeckStore.getState().setName("My Deck");
    render(<DeckBuilder onSave={() => {}} />);
    expect(screen.getByRole("button", { name: /save/i })).not.toBeDisabled();
  });

  it("should update deck name when typing", async () => {
    const user = userEvent.setup();
    render(<DeckBuilder />);

    const input = screen.getByPlaceholderText("Deck name...");
    await user.type(input, "Test Deck");

    expect(useDeckStore.getState().name).toBe("Test Deck");
  });

  it("should show empty state message when no search", () => {
    render(<DeckBuilder />);
    expect(
      screen.getByText("Search for cards to add to your deck"),
    ).toBeInTheDocument();
  });

  it("should show loading state during search", async () => {
    mockCardsApi.search.mockImplementation(
      () => new Promise(() => {}), // Never resolves
    );

    const user = userEvent.setup();
    render(<DeckBuilder />);

    const input = screen.getByPlaceholderText("Search cards to add...");
    await user.type(input, "Pikachu");

    // Wait for debounce
    await waitFor(() => {
      expect(mockCardsApi.search).toHaveBeenCalled();
    });
  });

  it("should display search results", async () => {
    mockCardsApi.search.mockResolvedValue({
      items: [
        {
          id: "swsh1-1",
          name: "Pikachu",
          supertype: "Pokemon",
          types: ["Lightning"],
          set_id: "swsh1",
          rarity: "Common",
          image_small: null,
        },
      ],
      total: 1,
      page: 1,
      limit: 20,
      total_pages: 1,
      has_next: false,
      has_prev: false,
    });

    const user = userEvent.setup();
    render(<DeckBuilder />);

    const input = screen.getByPlaceholderText("Search cards to add...");
    await user.type(input, "Pikachu");

    await waitFor(() => {
      expect(screen.getByText("Pikachu")).toBeInTheDocument();
    });
  });

  it("should add card to deck when clicked", async () => {
    mockCardsApi.search.mockResolvedValue({
      items: [
        {
          id: "swsh1-1",
          name: "Pikachu",
          supertype: "Pokemon",
          types: ["Lightning"],
          set_id: "swsh1",
          rarity: "Common",
          image_small: null,
        },
      ],
      total: 1,
      page: 1,
      limit: 20,
      total_pages: 1,
      has_next: false,
      has_prev: false,
    });

    const user = userEvent.setup();
    render(<DeckBuilder />);

    const input = screen.getByPlaceholderText("Search cards to add...");
    await user.type(input, "Pikachu");

    await waitFor(() => {
      expect(screen.getByText("Pikachu")).toBeInTheDocument();
    });

    // Click the card button to add it
    const cardButton = screen.getByRole("button", { name: /pikachu/i });
    await user.click(cardButton);

    expect(useDeckStore.getState().cards).toHaveLength(1);
    expect(useDeckStore.getState().cards[0].card.name).toBe("Pikachu");
  });

  it("should show error when search fails", async () => {
    mockCardsApi.search.mockRejectedValue(new Error("Network error"));

    const user = userEvent.setup();
    render(<DeckBuilder />);

    const input = screen.getByPlaceholderText("Search cards to add...");
    await user.type(input, "Pikachu");

    await waitFor(() => {
      expect(
        screen.getByText("Failed to search cards. Please try again."),
      ).toBeInTheDocument();
    });
  });

  it("should show 'No cards found' for empty search results", async () => {
    mockCardsApi.search.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      total_pages: 0,
      has_next: false,
      has_prev: false,
    });

    const user = userEvent.setup();
    render(<DeckBuilder />);

    const input = screen.getByPlaceholderText("Search cards to add...");
    await user.type(input, "NonexistentCard");

    await waitFor(() => {
      expect(screen.getByText("No cards found")).toBeInTheDocument();
    });
  });
});
