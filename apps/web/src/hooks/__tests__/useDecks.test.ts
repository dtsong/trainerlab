import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useDecks, useDeck } from "../useDecks";
import type { SavedDeck, DeckCard } from "@/types/deck";

const STORAGE_KEY = "trainerlab-saved-decks";

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  };
})();

Object.defineProperty(window, "localStorage", { value: localStorageMock });

// Helper to create a mock deck
function createMockDeck(overrides: Partial<SavedDeck> = {}): SavedDeck {
  return {
    id: "deck_123",
    name: "Test Deck",
    description: "A test deck",
    format: "standard",
    cards: [],
    createdAt: "2024-01-01T00:00:00.000Z",
    updatedAt: "2024-01-01T00:00:00.000Z",
    ...overrides,
  };
}

describe("useDecks", () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  describe("initial load", () => {
    it("should complete loading and have empty decks when localStorage is empty", async () => {
      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.decks).toHaveLength(0);
      expect(result.current.loadError).toBeNull();
    });

    it("should load decks from localStorage", async () => {
      const mockDecks = [createMockDeck({ id: "deck_1", name: "Deck 1" })];
      localStorageMock.setItem(STORAGE_KEY, JSON.stringify(mockDecks));

      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.decks).toHaveLength(1);
      expect(result.current.decks[0].name).toBe("Deck 1");
    });

    it("should handle empty localStorage", async () => {
      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.decks).toHaveLength(0);
      expect(result.current.loadError).toBeNull();
    });

    it("should set loadError when localStorage read fails", async () => {
      localStorageMock.getItem.mockImplementationOnce(() => {
        throw new Error("Storage unavailable");
      });

      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.loadError).toBeTruthy();
      expect(result.current.decks).toHaveLength(0);
    });

    it("should set loadError when JSON parsing fails", async () => {
      localStorageMock.setItem(STORAGE_KEY, "invalid json");

      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.loadError).toBeTruthy();
    });
  });

  describe("createDeck", () => {
    it("should create a deck with generated ID and timestamps", async () => {
      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let createResult: { deck: SavedDeck; saved: boolean };
      act(() => {
        createResult = result.current.createDeck({
          name: "New Deck",
          description: "Description",
          format: "standard",
          cards: [],
        });
      });

      expect(createResult!.deck.id).toMatch(/^deck_\d+_[a-z0-9]+$/);
      expect(createResult!.deck.name).toBe("New Deck");
      expect(createResult!.deck.createdAt).toBeTruthy();
      expect(createResult!.deck.updatedAt).toBeTruthy();
      expect(createResult!.saved).toBe(true);
    });

    it("should use 'Untitled Deck' when name is empty", async () => {
      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let createResult: { deck: SavedDeck; saved: boolean };
      act(() => {
        createResult = result.current.createDeck({
          name: "",
          description: "",
          format: "standard",
          cards: [],
        });
      });

      expect(createResult!.deck.name).toBe("Untitled Deck");
    });

    it("should persist to localStorage", async () => {
      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.createDeck({
          name: "New Deck",
          description: "",
          format: "standard",
          cards: [],
        });
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        STORAGE_KEY,
        expect.any(String)
      );

      const savedData = JSON.parse(
        localStorageMock.setItem.mock.calls[0][1] as string
      );
      expect(savedData).toHaveLength(1);
      expect(savedData[0].name).toBe("New Deck");
    });

    it("should return saved: false when localStorage fails", async () => {
      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      localStorageMock.setItem.mockImplementationOnce(() => {
        throw new Error("Quota exceeded");
      });

      let createResult: { deck: SavedDeck; saved: boolean };
      act(() => {
        createResult = result.current.createDeck({
          name: "New Deck",
          description: "",
          format: "standard",
          cards: [],
        });
      });

      expect(createResult!.saved).toBe(false);
      // Deck should still be created in memory even if save fails
      expect(createResult!.deck.name).toBe("New Deck");
    });
  });

  describe("updateDeck", () => {
    it("should return deck: null for non-existent deck ID", async () => {
      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let updateResult: { deck: SavedDeck | null; saved: boolean };
      act(() => {
        updateResult = result.current.updateDeck("nonexistent", {
          name: "Updated",
        });
      });

      expect(updateResult!.deck).toBeNull();
      expect(updateResult!.saved).toBe(false);
    });

    it("should update deck and preserve unchanged fields", async () => {
      const mockDecks = [
        createMockDeck({
          id: "deck_1",
          name: "Original",
          description: "Original Desc",
          format: "standard",
        }),
      ];
      localStorageMock.setItem(STORAGE_KEY, JSON.stringify(mockDecks));

      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let updateResult: { deck: SavedDeck | null; saved: boolean };
      act(() => {
        updateResult = result.current.updateDeck("deck_1", {
          name: "Updated Name",
        });
      });

      expect(updateResult!.deck?.name).toBe("Updated Name");
      expect(updateResult!.deck?.description).toBe("Original Desc");
      expect(updateResult!.deck?.format).toBe("standard");
      expect(updateResult!.saved).toBe(true);
    });

    it("should update the updatedAt timestamp", async () => {
      const originalDate = "2024-01-01T00:00:00.000Z";
      const mockDecks = [
        createMockDeck({
          id: "deck_1",
          updatedAt: originalDate,
        }),
      ];
      localStorageMock.setItem(STORAGE_KEY, JSON.stringify(mockDecks));

      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let updateResult: { deck: SavedDeck | null; saved: boolean };
      act(() => {
        updateResult = result.current.updateDeck("deck_1", { name: "Updated" });
      });

      expect(updateResult!.deck?.updatedAt).not.toBe(originalDate);
    });
  });

  describe("deleteDeck", () => {
    it("should return found: false for non-existent deck ID", async () => {
      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let deleteResult: { found: boolean; saved: boolean };
      act(() => {
        deleteResult = result.current.deleteDeck("nonexistent");
      });

      expect(deleteResult!.found).toBe(false);
      expect(deleteResult!.saved).toBe(false);
    });

    it("should delete deck and return success", async () => {
      const mockDecks = [
        createMockDeck({ id: "deck_1" }),
        createMockDeck({ id: "deck_2" }),
      ];
      localStorageMock.setItem(STORAGE_KEY, JSON.stringify(mockDecks));

      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.decks).toHaveLength(2);

      let deleteResult: { found: boolean; saved: boolean };
      act(() => {
        deleteResult = result.current.deleteDeck("deck_1");
      });

      expect(deleteResult!.found).toBe(true);
      expect(deleteResult!.saved).toBe(true);
      expect(result.current.decks).toHaveLength(1);
      expect(result.current.decks[0].id).toBe("deck_2");
    });
  });

  describe("getDeck", () => {
    it("should return undefined for non-existent deck ID", async () => {
      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const deck = result.current.getDeck("nonexistent");
      expect(deck).toBeUndefined();
    });

    it("should return deck when found", async () => {
      const mockDecks = [createMockDeck({ id: "deck_1", name: "Test" })];
      localStorageMock.setItem(STORAGE_KEY, JSON.stringify(mockDecks));

      const { result } = renderHook(() => useDecks());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const deck = result.current.getDeck("deck_1");
      expect(deck?.name).toBe("Test");
    });
  });
});

describe("useDeck", () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  it("should return undefined for non-existent deck", async () => {
    const { result } = renderHook(() => useDeck("nonexistent"));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.deck).toBeUndefined();
  });

  it("should return deck when found", async () => {
    const mockDecks = [createMockDeck({ id: "deck_1", name: "Test Deck" })];
    localStorageMock.setItem(STORAGE_KEY, JSON.stringify(mockDecks));

    const { result } = renderHook(() => useDeck("deck_1"));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.deck?.name).toBe("Test Deck");
  });

  it("should expose loadError from useDecks", async () => {
    localStorageMock.getItem.mockImplementationOnce(() => {
      throw new Error("Storage error");
    });

    const { result } = renderHook(() => useDeck("deck_1"));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.loadError).toBeTruthy();
  });
});
