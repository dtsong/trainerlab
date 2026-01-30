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

  // Load decks from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setDecks(JSON.parse(stored));
      }
    } catch (error) {
      console.error("Failed to load decks from localStorage:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save decks to localStorage whenever they change
  const saveDecks = useCallback((newDecks: SavedDeck[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newDecks));
      setDecks(newDecks);
    } catch (error) {
      console.error("Failed to save decks to localStorage:", error);
    }
  }, []);

  const createDeck = useCallback(
    (deck: {
      name: string;
      description: string;
      format: DeckFormat;
      cards: DeckCard[];
    }): SavedDeck => {
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

      saveDecks([...decks, newDeck]);
      return newDeck;
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
    ): SavedDeck | null => {
      const deckIndex = decks.findIndex((d) => d.id === id);
      if (deckIndex === -1) return null;

      const updatedDeck: SavedDeck = {
        ...decks[deckIndex],
        ...updates,
        updatedAt: new Date().toISOString(),
      };

      const newDecks = [...decks];
      newDecks[deckIndex] = updatedDeck;
      saveDecks(newDecks);

      return updatedDeck;
    },
    [decks, saveDecks],
  );

  const deleteDeck = useCallback(
    (id: string): boolean => {
      const newDecks = decks.filter((d) => d.id !== id);
      if (newDecks.length === decks.length) return false;

      saveDecks(newDecks);
      return true;
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
  const { getDeck, isLoading, updateDeck, deleteDeck } = useDecks();
  const [deck, setDeck] = useState<SavedDeck | undefined>(undefined);

  useEffect(() => {
    if (!isLoading) {
      setDeck(getDeck(id));
    }
  }, [id, isLoading, getDeck]);

  return {
    deck,
    isLoading,
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
