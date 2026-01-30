/**
 * Zustand store for deck builder state management.
 */

import { create } from "zustand";
import type { ApiCardSummary } from "@trainerlab/shared-types";
import type { DeckCard, DeckFormat, DeckState } from "@/types/deck";

/**
 * Check if a card is a basic energy card.
 * Basic energy cards have no quantity limit in decks.
 */
function isBasicEnergy(card: ApiCardSummary): boolean {
  return card.supertype === "Energy" && !card.name.includes("Special");
}

/**
 * Maximum quantity allowed for non-basic-energy cards.
 */
const MAX_CARD_QUANTITY = 4;

interface DeckActions {
  /** Add a card to the deck (increments quantity if exists) */
  addCard: (card: ApiCardSummary) => void;
  /** Remove a card from the deck (decrements quantity, removes if 0) */
  removeCard: (cardId: string) => void;
  /** Set exact quantity for a card (removes if 0) */
  setQuantity: (cardId: string, quantity: number) => void;
  /** Set deck name */
  setName: (name: string) => void;
  /** Set deck description */
  setDescription: (description: string) => void;
  /** Set deck format */
  setFormat: (format: DeckFormat) => void;
  /** Clear all cards from deck */
  clearDeck: () => void;
  /** Reset modified flag (after save) */
  resetModified: () => void;
}

const initialState: DeckState = {
  cards: [],
  name: "",
  description: "",
  format: "standard",
  isModified: false,
};

export const useDeckStore = create<DeckState & DeckActions>((set) => ({
  ...initialState,

  addCard: (card: ApiCardSummary) => {
    set((state) => {
      const existingIndex = state.cards.findIndex((c) => c.card.id === card.id);

      if (existingIndex >= 0) {
        // Card exists, increment quantity
        const existing = state.cards[existingIndex];
        const canAddMore =
          isBasicEnergy(card) || existing.quantity < MAX_CARD_QUANTITY;

        if (!canAddMore) {
          return state; // At limit, no change
        }

        const newCards = [...state.cards];
        newCards[existingIndex] = {
          ...existing,
          quantity: existing.quantity + 1,
        };

        return { cards: newCards, isModified: true };
      }

      // New card, add with quantity 1
      const newCard: DeckCard = {
        card,
        quantity: 1,
        position: state.cards.length,
      };

      return { cards: [...state.cards, newCard], isModified: true };
    });
  },

  removeCard: (cardId: string) => {
    set((state) => {
      const existingIndex = state.cards.findIndex((c) => c.card.id === cardId);

      if (existingIndex < 0) {
        return state; // Card not found
      }

      const existing = state.cards[existingIndex];

      if (existing.quantity > 1) {
        // Decrement quantity
        const newCards = [...state.cards];
        newCards[existingIndex] = {
          ...existing,
          quantity: existing.quantity - 1,
        };
        return { cards: newCards, isModified: true };
      }

      // Remove card entirely and reindex positions
      const newCards = state.cards
        .filter((_, i) => i !== existingIndex)
        .map((c, i) => ({ ...c, position: i }));

      return { cards: newCards, isModified: true };
    });
  },

  setQuantity: (cardId: string, quantity: number) => {
    set((state) => {
      const existingIndex = state.cards.findIndex((c) => c.card.id === cardId);

      if (existingIndex < 0) {
        return state; // Card not found
      }

      if (quantity <= 0) {
        // Remove card entirely and reindex positions
        const newCards = state.cards
          .filter((_, i) => i !== existingIndex)
          .map((c, i) => ({ ...c, position: i }));
        return { cards: newCards, isModified: true };
      }

      const existing = state.cards[existingIndex];
      const maxQuantity = isBasicEnergy(existing.card)
        ? Infinity
        : MAX_CARD_QUANTITY;
      const clampedQuantity = Math.min(quantity, maxQuantity);

      const newCards = [...state.cards];
      newCards[existingIndex] = {
        ...existing,
        quantity: clampedQuantity,
      };

      return { cards: newCards, isModified: true };
    });
  },

  setName: (name: string) => {
    set({ name, isModified: true });
  },

  setDescription: (description: string) => {
    set({ description, isModified: true });
  },

  setFormat: (format: DeckFormat) => {
    set({ format, isModified: true });
  },

  clearDeck: () => {
    set({ cards: [], isModified: true });
  },

  resetModified: () => {
    set({ isModified: false });
  },
}));
