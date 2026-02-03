import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeckImportModal } from "../DeckImportModal";
import { useDeckStore } from "@/stores/deckStore";
import * as api from "@/lib/api";
import type { ApiCardSummary } from "@trainerlab/shared-types";

// Mock the API
vi.mock("@/lib/api", () => ({
  cardsApi: {
    search: vi.fn(),
  },
}));

const mockCardsApi = vi.mocked(api.cardsApi);

const mockCard = (overrides: Partial<ApiCardSummary> = {}): ApiCardSummary => ({
  id: "swsh1-25",
  name: "Pikachu",
  supertype: "Pokemon",
  types: ["Lightning"],
  set_id: "swsh1",
  rarity: "Common",
  image_small: null,
  ...overrides,
});

describe("DeckImportModal", () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
  };

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

  describe("rendering", () => {
    it("should render dialog with title and description", () => {
      render(<DeckImportModal {...defaultProps} />);

      expect(screen.getByText("Import Deck")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Paste a deck list from Pokemon TCG Online or Pokemon TCG Live."
        )
      ).toBeInTheDocument();
    });

    it("should render textarea with placeholder", () => {
      render(<DeckImportModal {...defaultProps} />);

      expect(
        screen.getByPlaceholderText(/Paste your deck list here/)
      ).toBeInTheDocument();
    });

    it("should render Cancel button", () => {
      render(<DeckImportModal {...defaultProps} />);

      expect(
        screen.getByRole("button", { name: /cancel/i })
      ).toBeInTheDocument();
    });

    it("should render Import button", () => {
      render(<DeckImportModal {...defaultProps} />);

      expect(
        screen.getByRole("button", { name: /import/i })
      ).toBeInTheDocument();
    });

    it("should disable Import button when textarea is empty", () => {
      render(<DeckImportModal {...defaultProps} />);

      expect(screen.getByRole("button", { name: /import/i })).toBeDisabled();
    });
  });

  describe("parse preview", () => {
    it("should show preview when valid deck list is entered", async () => {
      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 Pikachu SVI 25");

      expect(screen.getByText("Preview")).toBeInTheDocument();
      expect(screen.getByText("1 unique cards, 4 total")).toBeInTheDocument();
      expect(screen.getByText("4x Pikachu (SVI)")).toBeInTheDocument();
    });

    it("should show correct counts for multiple cards", async () => {
      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 Pikachu SVI 25\n2 Raichu SVI 26");

      expect(screen.getByText("2 unique cards, 6 total")).toBeInTheDocument();
    });

    it("should show parse errors in preview", async () => {
      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      // Invalid line without quantity
      await user.type(textarea, "4 Pikachu SVI 25\nInvalid line here");

      await waitFor(() => {
        expect(screen.getByText(/Line 2: Could not parse/)).toBeInTheDocument();
      });
    });

    it("should enable Import button when valid cards are parsed", async () => {
      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 Pikachu SVI 25");

      expect(
        screen.getByRole("button", { name: /import/i })
      ).not.toBeDisabled();
    });

    it("should truncate preview when more than 10 cards", async () => {
      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      const cards = Array.from(
        { length: 12 },
        (_, i) => `1 Card${i + 1} SET ${i + 1}`
      ).join("\n");
      await user.type(textarea, cards);

      expect(screen.getByText("...and 2 more")).toBeInTheDocument();
    });
  });

  describe("import flow", () => {
    it("should search for cards when import is clicked", async () => {
      mockCardsApi.search.mockResolvedValue({
        items: [mockCard()],
        total: 1,
        page: 1,
        limit: 10,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      });

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      expect(mockCardsApi.search).toHaveBeenCalledWith({
        q: "Pikachu",
        limit: 10,
      });
    });

    it("should show importing state during import", async () => {
      mockCardsApi.search.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      expect(screen.getByText("Importing...")).toBeInTheDocument();
    });

    it("should disable textarea during import", async () => {
      mockCardsApi.search.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      expect(textarea).toBeDisabled();
    });

    it("should add found card to deck store", async () => {
      const pikachu = mockCard({
        id: "svi-25",
        name: "Pikachu",
        set_id: "svi",
      });
      mockCardsApi.search.mockResolvedValue({
        items: [pikachu],
        total: 1,
        page: 1,
        limit: 10,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      });

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "1 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      await waitFor(() => {
        expect(useDeckStore.getState().cards).toHaveLength(1);
        expect(useDeckStore.getState().cards[0].card.name).toBe("Pikachu");
      });
    });

    it("should set quantity when importing multiple copies", async () => {
      const pikachu = mockCard({
        id: "svi-25",
        name: "Pikachu",
        set_id: "svi",
      });
      mockCardsApi.search.mockResolvedValue({
        items: [pikachu],
        total: 1,
        page: 1,
        limit: 10,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      });

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      await waitFor(() => {
        expect(useDeckStore.getState().cards[0].quantity).toBe(4);
      });
    });

    it("should show found status for matched cards", async () => {
      mockCardsApi.search.mockResolvedValue({
        items: [mockCard()],
        total: 1,
        page: 1,
        limit: 10,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      });

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      await waitFor(() => {
        expect(screen.getByText("Import Status")).toBeInTheDocument();
        expect(screen.getByText("1 found, 0 not found")).toBeInTheDocument();
      });
    });

    it("should show not_found status when no cards match", async () => {
      mockCardsApi.search.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        limit: 10,
        total_pages: 0,
        has_next: false,
        has_prev: false,
      });

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 NonexistentCard SET 999");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      await waitFor(() => {
        expect(screen.getByText("0 found, 1 not found")).toBeInTheDocument();
      });
    });

    it("should show error status when API fails", async () => {
      mockCardsApi.search.mockRejectedValue(new Error("Network error"));

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      await waitFor(() => {
        expect(screen.getByText(/network error/)).toBeInTheDocument();
        expect(
          screen.getByText("0 found, 0 not found, 1 failed")
        ).toBeInTheDocument();
      });
    });

    it("should continue importing other cards when one fails", async () => {
      const pikachu = mockCard({
        id: "svi-25",
        name: "Pikachu",
        set_id: "svi",
      });

      // First call fails, second succeeds
      mockCardsApi.search
        .mockRejectedValueOnce(new Error("Network error"))
        .mockResolvedValueOnce({
          items: [pikachu],
          total: 1,
          page: 1,
          limit: 10,
          total_pages: 1,
          has_next: false,
          has_prev: false,
        });

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "2 FailingCard SET 1\n2 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      await waitFor(() => {
        expect(
          screen.getByText("1 found, 0 not found, 1 failed")
        ).toBeInTheDocument();
        expect(useDeckStore.getState().cards).toHaveLength(1);
      });
    });
  });

  describe("card matching", () => {
    it("should prefer exact name match over partial match", async () => {
      const exactMatch = mockCard({
        id: "exact-1",
        name: "Pikachu",
        set_id: "svi",
      });
      const partialMatch = mockCard({
        id: "partial-1",
        name: "Pikachu V",
        set_id: "svi",
      });

      mockCardsApi.search.mockResolvedValue({
        items: [partialMatch, exactMatch],
        total: 2,
        page: 1,
        limit: 10,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      });

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "1 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      await waitFor(() => {
        expect(useDeckStore.getState().cards[0].card.id).toBe("exact-1");
      });
    });

    it("should prefer set+name match over name-only match", async () => {
      const wrongSet = mockCard({
        id: "wrong-set",
        name: "Pikachu",
        set_id: "swsh1",
      });
      const correctSet = mockCard({
        id: "correct-set",
        name: "Pikachu",
        set_id: "svi",
      });

      mockCardsApi.search.mockResolvedValue({
        items: [wrongSet, correctSet],
        total: 2,
        page: 1,
        limit: 10,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      });

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "1 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      await waitFor(() => {
        expect(useDeckStore.getState().cards[0].card.id).toBe("correct-set");
      });
    });

    it("should fall back to first result when no exact match", async () => {
      const firstResult = mockCard({
        id: "first-result",
        name: "Pikachu V",
        set_id: "swsh1",
      });

      mockCardsApi.search.mockResolvedValue({
        items: [firstResult],
        total: 1,
        page: 1,
        limit: 10,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      });

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "1 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      await waitFor(() => {
        expect(useDeckStore.getState().cards[0].card.id).toBe("first-result");
      });
    });
  });

  describe("modal controls", () => {
    it("should call onOpenChange when Cancel is clicked", async () => {
      const onOpenChange = vi.fn();
      const user = userEvent.setup();
      render(<DeckImportModal open={true} onOpenChange={onOpenChange} />);

      const cancelBtn = screen.getByRole("button", { name: /cancel/i });
      await user.click(cancelBtn);

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });

    it("should reset state when closing", async () => {
      const onOpenChange = vi.fn();
      const user = userEvent.setup();
      render(<DeckImportModal open={true} onOpenChange={onOpenChange} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 Pikachu SVI 25");

      const cancelBtn = screen.getByRole("button", { name: /cancel/i });
      await user.click(cancelBtn);

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });

    it("should show Done button after import completes", async () => {
      mockCardsApi.search.mockResolvedValue({
        items: [mockCard()],
        total: 1,
        page: 1,
        limit: 10,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      });

      const user = userEvent.setup();
      render(<DeckImportModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/Paste your deck list here/);
      await user.type(textarea, "4 Pikachu SVI 25");

      const importBtn = screen.getByRole("button", { name: /import/i });
      await user.click(importBtn);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /done/i })
        ).toBeInTheDocument();
        expect(
          screen.queryByRole("button", { name: /import/i })
        ).not.toBeInTheDocument();
      });
    });
  });
});
