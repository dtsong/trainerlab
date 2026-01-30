/**
 * Zustand store for deck builder state management.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
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

interface SupertypeCounts {
  Pokemon: number;
  Trainer: number;
  Energy: number;
}

interface CardsByType {
  Pokemon: DeckCard[];
  Trainer: DeckCard[];
  Energy: DeckCard[];
}

interface DeckGetters {
  /** Total number of cards in deck (sum of quantities) */
  totalCards: () => number;
  /** Number of Pokemon cards */
  pokemonCount: () => number;
  /** Number of Trainer cards */
  trainerCount: () => number;
  /** Number of Energy cards */
  energyCount: () => number;
  /** Card counts by supertype */
  supertypeCounts: () => SupertypeCounts;
  /** Whether deck has exactly 60 cards */
  isValid: () => boolean;
  /** Cards grouped by supertype */
  cardsByType: () => CardsByType;
}

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
  /** Load an existing deck for editing */
  loadDeck: (deck: Omit<DeckState, "isModified">) => void;
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

const STORAGE_KEY = "deck-builder-storage";

export const useDeckStore = create<DeckState & DeckActions & DeckGetters>()(
  persist(
    (set, get) => ({
      ...initialState,

      addCard: (card: ApiCardSummary) => {
        set((state) => {
          const existingIndex = state.cards.findIndex(
            (c) => c.card.id === card.id,
          );

          if (existingIndex >= 0) {
            const existing = state.cards[existingIndex];
            const canAddMore =
              isBasicEnergy(card) || existing.quantity < MAX_CARD_QUANTITY;

            if (!canAddMore) {
              return state;
            }

            const newCards = [...state.cards];
            newCards[existingIndex] = {
              ...existing,
              quantity: existing.quantity + 1,
            };

            return { cards: newCards, isModified: true };
          }

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
          const existingIndex = state.cards.findIndex(
            (c) => c.card.id === cardId,
          );

          if (existingIndex < 0) {
            return state;
          }

          const existing = state.cards[existingIndex];

          if (existing.quantity > 1) {
            const newCards = [...state.cards];
            newCards[existingIndex] = {
              ...existing,
              quantity: existing.quantity - 1,
            };
            return { cards: newCards, isModified: true };
          }

          const newCards = state.cards
            .filter((_, i) => i !== existingIndex)
            .map((c, i) => ({ ...c, position: i }));

          return { cards: newCards, isModified: true };
        });
      },

      setQuantity: (cardId: string, quantity: number) => {
        set((state) => {
          const existingIndex = state.cards.findIndex(
            (c) => c.card.id === cardId,
          );

          if (existingIndex < 0) {
            return state;
          }

          if (quantity <= 0) {
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

      loadDeck: (deck: Omit<DeckState, "isModified">) => {
        set({ ...deck, isModified: false });
      },

      resetModified: () => {
        set({ isModified: false });
      },

      // Computed getters
      totalCards: () => {
        return get().cards.reduce((sum, c) => sum + c.quantity, 0);
      },

      pokemonCount: () => {
        return get()
          .cards.filter((c) => c.card.supertype === "Pokemon")
          .reduce((sum, c) => sum + c.quantity, 0);
      },

      trainerCount: () => {
        return get()
          .cards.filter((c) => c.card.supertype === "Trainer")
          .reduce((sum, c) => sum + c.quantity, 0);
      },

      energyCount: () => {
        return get()
          .cards.filter((c) => c.card.supertype === "Energy")
          .reduce((sum, c) => sum + c.quantity, 0);
      },

      supertypeCounts: () => {
        const state = get();
        return {
          Pokemon: state.cards
            .filter((c) => c.card.supertype === "Pokemon")
            .reduce((sum, c) => sum + c.quantity, 0),
          Trainer: state.cards
            .filter((c) => c.card.supertype === "Trainer")
            .reduce((sum, c) => sum + c.quantity, 0),
          Energy: state.cards
            .filter((c) => c.card.supertype === "Energy")
            .reduce((sum, c) => sum + c.quantity, 0),
        };
      },

      isValid: () => {
        return get().totalCards() === 60;
      },

      cardsByType: () => {
        const cards = get().cards;
        return {
          Pokemon: cards.filter((c) => c.card.supertype === "Pokemon"),
          Trainer: cards.filter((c) => c.card.supertype === "Trainer"),
          Energy: cards.filter((c) => c.card.supertype === "Energy"),
        };
      },
    }),
    {
      name: STORAGE_KEY,
      partialize: (state) => ({
        cards: state.cards,
        name: state.name,
        description: state.description,
        format: state.format,
      }),
      onRehydrateStorage: () => {
        return (state, error) => {
          if (error) {
            console.error("Failed to restore deck from localStorage:", error);
          }
        };
      },
      storage: {
        getItem: (name) => {
          try {
            const value = localStorage.getItem(name);
            return value ? JSON.parse(value) : null;
          } catch (error) {
            console.error("Failed to read deck from localStorage:", error);
            return null;
          }
        },
        setItem: (name, value) => {
          try {
            localStorage.setItem(name, JSON.stringify(value));
          } catch (error) {
            console.error("Failed to save deck to localStorage:", error);
          }
        },
        removeItem: (name) => {
          try {
            localStorage.removeItem(name);
          } catch (error) {
            console.error("Failed to remove deck from localStorage:", error);
          }
        },
      },
    },
  ),
);
