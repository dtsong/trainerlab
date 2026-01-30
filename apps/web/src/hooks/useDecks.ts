"use client";

import { useState, useEffect, useCallback } from "react";
import type { SavedDeck, DeckCard, DeckFormat } from "@/types/deck";

const STORAGE_KEY = "trainerlab-saved-decks";

/**
 * Hook for managing saved decks in localStorage.
 * Will be replaced with API calls when backend is ready.
 */
export function useDecks() {
  const [decks, setDecks] = useState<SavedDeck[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Load decks from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setDecks(JSON.parse(stored));
      }
      setLoadError(null);
    } catch (error) {
      console.error("Failed to load decks from localStorage:", error);
      setLoadError(
        "Could not load your saved decks. Your browser storage may be corrupted or unavailable.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save decks to localStorage - returns true on success, false on failure
  const saveDecks = useCallback((newDecks: SavedDeck[]): boolean => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newDecks));
      setDecks(newDecks);
      return true;
    } catch (error) {
      console.error("Failed to save decks to localStorage:", error);
      return false;
    }
  }, []);

  const createDeck = useCallback(
    (deck: {
      name: string;
      description: string;
      format: DeckFormat;
      cards: DeckCard[];
    }): { deck: SavedDeck; saved: boolean } => {
      const now = new Date().toISOString();
      const newDeck: SavedDeck = {
        id: generateId(),
        name: deck.name || "Untitled Deck",
        description: deck.description,
        format: deck.format,
        cards: deck.cards,
        createdAt: now,
        updatedAt: now,
      };

      const saved = saveDecks([...decks, newDeck]);
      return { deck: newDeck, saved };
    },
    [decks, saveDecks],
  );

  const updateDeck = useCallback(
    (
      id: string,
      updates: Partial<{
        name: string;
        description: string;
        format: DeckFormat;
        cards: DeckCard[];
      }>,
    ): { deck: SavedDeck | null; saved: boolean } => {
      const deckIndex = decks.findIndex((d) => d.id === id);
      if (deckIndex === -1) return { deck: null, saved: false };

      const updatedDeck: SavedDeck = {
        ...decks[deckIndex],
        ...updates,
        updatedAt: new Date().toISOString(),
      };

      const newDecks = [...decks];
      newDecks[deckIndex] = updatedDeck;
      const saved = saveDecks(newDecks);

      return { deck: updatedDeck, saved };
    },
    [decks, saveDecks],
  );

  const deleteDeck = useCallback(
    (id: string): { found: boolean; saved: boolean } => {
      const newDecks = decks.filter((d) => d.id !== id);
      if (newDecks.length === decks.length) {
        return { found: false, saved: false };
      }

      const saved = saveDecks(newDecks);
      return { found: true, saved };
    },
    [decks, saveDecks],
  );

  const getDeck = useCallback(
    (id: string): SavedDeck | undefined => {
      return decks.find((d) => d.id === id);
    },
    [decks],
  );

  return {
    decks,
    isLoading,
    loadError,
    createDeck,
    updateDeck,
    deleteDeck,
    getDeck,
  };
}

/**
 * Hook for a single deck by ID.
 */
export function useDeck(id: string) {
  const { getDeck, isLoading, loadError, updateDeck, deleteDeck } = useDecks();
  const [deck, setDeck] = useState<SavedDeck | undefined>(undefined);

  useEffect(() => {
    if (!isLoading) {
      setDeck(getDeck(id));
    }
  }, [id, isLoading, getDeck]);

  return {
    deck,
    isLoading,
    loadError,
    updateDeck: (
      updates: Partial<{
        name: string;
        description: string;
        format: DeckFormat;
        cards: DeckCard[];
      }>,
    ) => updateDeck(id, updates),
    deleteDeck: () => deleteDeck(id),
  };
}

function generateId(): string {
  return `deck_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}
