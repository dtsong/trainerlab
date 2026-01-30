/**
 * Deck builder types for frontend state management.
 */

import type { ApiCardSummary } from "@trainerlab/shared-types";

/**
 * A card entry in a deck with quantity and ordering.
 */
export interface DeckCard {
  /** Card data from API */
  card: ApiCardSummary;
  /** Number of this card in deck (1-4, unlimited for basic energy) */
  quantity: number;
  /** Position for ordering cards in the deck list */
  position: number;
}

/**
 * Deck format for legality checking.
 */
export type DeckFormat = "standard" | "expanded";

/**
 * Deck builder state shape.
 */
export interface DeckState {
  /** Cards in the deck */
  cards: DeckCard[];
  /** Deck name */
  name: string;
  /** Deck description */
  description: string;
  /** Deck format (standard or expanded) */
  format: DeckFormat;
  /** Whether the deck has unsaved changes */
  isModified: boolean;
}
