import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type {
  ApiSet,
  ApiPaginatedResponse,
  ApiCardSummary,
} from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  setsApi: {
    list: vi.fn(),
    getById: vi.fn(),
    getCards: vi.fn(),
  },
}));

import { setsApi } from "@/lib/api";
import { useSets, useSet, useSetCards } from "../useSets";

const mockSet: ApiSet = {
  id: "sv3",
  name: "Obsidian Flames",
  series: "Scarlet & Violet",
  card_count: 230,
  release_date: "2023-08-11",
  symbol_url: "https://example.com/sv3-symbol.png",
  logo_url: "https://example.com/sv3-logo.png",
  created_at: "2023-08-01T00:00:00Z",
  updated_at: "2023-08-01T00:00:00Z",
};

const mockSets: ApiSet[] = [
  mockSet,
  {
    id: "sv4",
    name: "Paradox Rift",
    series: "Scarlet & Violet",
    card_count: 182,
    release_date: "2023-11-03",
    symbol_url: "https://example.com/sv4-symbol.png",
    logo_url: "https://example.com/sv4-logo.png",
    created_at: "2023-11-01T00:00:00Z",
    updated_at: "2023-11-01T00:00:00Z",
  },
];

const mockCardSummary: ApiCardSummary = {
  id: "sv3-125",
  name: "Charizard ex",
  image_small: "https://example.com/charizard-small.jpg",
  supertype: "Pokemon",
  types: ["Fire"],
  set_id: "sv3",
};

const mockPaginatedCards: ApiPaginatedResponse<ApiCardSummary> = {
  items: [mockCardSummary],
  total: 230,
  page: 1,
  limit: 20,
  has_next: true,
  has_prev: false,
  total_pages: 12,
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

describe("useSets", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch all sets", async () => {
    vi.mocked(setsApi.list).mockResolvedValue(mockSets);

    const { result } = renderHook(() => useSets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockSets);
    expect(setsApi.list).toHaveBeenCalledOnce();
  });

  it("should handle API errors", async () => {
    vi.mocked(setsApi.list).mockRejectedValue(
      new Error("Failed to fetch sets")
    );

    const { result } = renderHook(() => useSets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });

  it("should return empty array when no sets exist", async () => {
    vi.mocked(setsApi.list).mockResolvedValue([]);

    const { result } = renderHook(() => useSets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([]);
  });
});

describe("useSet", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch set by ID", async () => {
    vi.mocked(setsApi.getById).mockResolvedValue(mockSet);

    const { result } = renderHook(() => useSet("sv3"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockSet);
    expect(setsApi.getById).toHaveBeenCalledWith("sv3");
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useSet(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(setsApi.getById).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(setsApi.getById).mockRejectedValue(new Error("Set not found"));

    const { result } = renderHook(() => useSet("nonexistent"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useSetCards", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch cards for a set with default pagination", async () => {
    vi.mocked(setsApi.getCards).mockResolvedValue(mockPaginatedCards);

    const { result } = renderHook(() => useSetCards("sv3"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockPaginatedCards);
    expect(setsApi.getCards).toHaveBeenCalledWith("sv3", 1, 20);
  });

  it("should fetch cards with custom pagination", async () => {
    vi.mocked(setsApi.getCards).mockResolvedValue({
      ...mockPaginatedCards,
      page: 2,
      has_prev: true,
    });

    const { result } = renderHook(() => useSetCards("sv3", 2, 50), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(setsApi.getCards).toHaveBeenCalledWith("sv3", 2, 50);
    expect(result.current.data?.page).toBe(2);
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useSetCards(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(setsApi.getCards).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(setsApi.getCards).mockRejectedValue(
      new Error("Failed to fetch cards")
    );

    const { result } = renderHook(() => useSetCards("sv3"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
