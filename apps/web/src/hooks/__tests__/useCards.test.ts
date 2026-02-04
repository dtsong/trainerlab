import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type {
  ApiPaginatedResponse,
  ApiCardSummary,
  ApiCard,
} from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  cardsApi: {
    search: vi.fn(),
    getById: vi.fn(),
  },
}));

import { cardsApi } from "@/lib/api";
import { useCards, useCard, useCardSearch } from "../useCards";

const mockCardSummary: ApiCardSummary = {
  id: "sv3-125",
  name: "Charizard ex",
  image_small: "https://example.com/charizard-small.jpg",
  supertype: "Pokémon",
  types: ["Fire"],
  set_id: "sv3",
};

const mockPaginatedResponse: ApiPaginatedResponse<ApiCardSummary> = {
  items: [mockCardSummary],
  total: 100,
  page: 1,
  limit: 20,
  has_next: true,
  has_prev: false,
};

const mockCard: ApiCard = {
  ...mockCardSummary,
  image_large: "https://example.com/charizard-large.jpg",
  subtypes: ["Stage 2", "ex"],
  rules: [],
  attacks: [],
  weaknesses: [],
  resistances: [],
  retreat_cost: ["Colorless", "Colorless"],
  hp: "330",
  rarity: "Double Rare",
  artist: "Test Artist",
  set_name: "Obsidian Flames",
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
}

describe("useCards", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch cards with default params", async () => {
    vi.mocked(cardsApi.search).mockResolvedValue(mockPaginatedResponse);

    const { result } = renderHook(() => useCards(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockPaginatedResponse);
    expect(cardsApi.search).toHaveBeenCalledWith({});
  });

  it("should fetch cards with search query", async () => {
    vi.mocked(cardsApi.search).mockResolvedValue(mockPaginatedResponse);

    const { result } = renderHook(() => useCards({ q: "Charizard" }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(cardsApi.search).toHaveBeenCalledWith({ q: "Charizard" });
  });

  it("should fetch cards with filters", async () => {
    vi.mocked(cardsApi.search).mockResolvedValue(mockPaginatedResponse);

    const params = {
      supertype: "Pokémon",
      types: "Fire",
      set_id: "sv3",
      standard: true,
    };

    const { result } = renderHook(() => useCards(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(cardsApi.search).toHaveBeenCalledWith(params);
  });

  it("should handle pagination params", async () => {
    vi.mocked(cardsApi.search).mockResolvedValue({
      ...mockPaginatedResponse,
      page: 2,
      has_prev: true,
    });

    const { result } = renderHook(() => useCards({ page: 2, limit: 50 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(cardsApi.search).toHaveBeenCalledWith({ page: 2, limit: 50 });
    expect(result.current.data?.page).toBe(2);
  });

  it("should handle API errors", async () => {
    vi.mocked(cardsApi.search).mockRejectedValue(new Error("API Error"));

    const { result } = renderHook(() => useCards(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch card by ID", async () => {
    vi.mocked(cardsApi.getById).mockResolvedValue(mockCard);

    const { result } = renderHook(() => useCard("sv3-125"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockCard);
    expect(cardsApi.getById).toHaveBeenCalledWith("sv3-125");
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useCard(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(cardsApi.getById).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(cardsApi.getById).mockRejectedValue(new Error("Card not found"));

    const { result } = renderHook(() => useCard("nonexistent"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useCardSearch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should search cards with query", async () => {
    vi.mocked(cardsApi.search).mockResolvedValue(mockPaginatedResponse);

    const { result } = renderHook(() => useCardSearch("Charizard"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(cardsApi.search).toHaveBeenCalledWith({ q: "Charizard", limit: 20 });
  });

  it("should not search when query is empty", async () => {
    const { result } = renderHook(() => useCardSearch(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(cardsApi.search).not.toHaveBeenCalled();
  });

  it("should not search when query is whitespace only", async () => {
    const { result } = renderHook(() => useCardSearch("   "), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(cardsApi.search).not.toHaveBeenCalled();
  });

  it("should use custom limit", async () => {
    vi.mocked(cardsApi.search).mockResolvedValue(mockPaginatedResponse);

    const { result } = renderHook(() => useCardSearch("Charizard", 50), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(cardsApi.search).toHaveBeenCalledWith({ q: "Charizard", limit: 50 });
  });

  it("should handle API errors", async () => {
    vi.mocked(cardsApi.search).mockRejectedValue(new Error("Search failed"));

    const { result } = renderHook(() => useCardSearch("test"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
