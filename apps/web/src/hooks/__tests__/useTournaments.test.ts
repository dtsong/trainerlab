import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type {
  ApiTournamentListResponse,
  ApiTournamentSummary,
  ApiTournamentDetail,
  ApiDecklistResponse,
} from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  tournamentsApi: {
    list: vi.fn(),
    getById: vi.fn(),
    getPlacementDecklist: vi.fn(),
  },
}));

import { tournamentsApi } from "@/lib/api";
import {
  useTournaments,
  useTournament,
  usePlacementDecklist,
} from "../useTournaments";

const mockTournamentSummary: ApiTournamentSummary = {
  id: "tournament-123",
  name: "Regional Championship",
  date: "2024-06-15",
  region: "NA",
  format: "standard",
  best_of: 3,
  participant_count: 256,
  tier: "major",
  top_placements: [],
};

const mockListResponse: ApiTournamentListResponse = {
  items: [mockTournamentSummary],
  total: 50,
  page: 1,
  limit: 20,
  has_next: true,
  has_prev: false,
};

const mockTournamentDetail: ApiTournamentDetail = {
  ...mockTournamentSummary,
  source_url: "https://example.com/tournament",
  placements: [
    {
      id: "placement-1",
      placement: 1,
      player_name: "Champion Player",
      archetype: "Charizard ex",
      has_decklist: true,
    },
  ],
  meta_breakdown: [],
};

const mockDecklist: ApiDecklistResponse = {
  placement_id: "placement-1",
  player_name: "Champion Player",
  archetype: "Charizard ex",
  tournament_name: "Regional Championship",
  tournament_date: "2024-06-15",
  cards: [
    { card_id: "sv3-125", card_name: "Charizard ex", quantity: 2 },
    { card_id: "sv3-46", card_name: "Charmander", quantity: 4 },
  ],
  total_cards: 6,
  source_url: "https://example.com/decklist",
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

describe("useTournaments", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch tournaments with default params", async () => {
    vi.mocked(tournamentsApi.list).mockResolvedValue(mockListResponse);

    const { result } = renderHook(() => useTournaments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockListResponse);
    expect(tournamentsApi.list).toHaveBeenCalledWith({});
  });

  it("should fetch tournaments with region filter", async () => {
    vi.mocked(tournamentsApi.list).mockResolvedValue(mockListResponse);

    const { result } = renderHook(() => useTournaments({ region: "JP" }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tournamentsApi.list).toHaveBeenCalledWith({ region: "JP" });
  });

  it("should fetch tournaments with format filter", async () => {
    vi.mocked(tournamentsApi.list).mockResolvedValue(mockListResponse);

    const { result } = renderHook(
      () => useTournaments({ format: "expanded" }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tournamentsApi.list).toHaveBeenCalledWith({ format: "expanded" });
  });

  it("should fetch tournaments with date range", async () => {
    vi.mocked(tournamentsApi.list).mockResolvedValue(mockListResponse);

    const params = {
      start_date: "2024-01-01",
      end_date: "2024-06-30",
    };

    const { result } = renderHook(() => useTournaments(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tournamentsApi.list).toHaveBeenCalledWith(params);
  });

  it("should fetch tournaments with tier filter", async () => {
    vi.mocked(tournamentsApi.list).mockResolvedValue(mockListResponse);

    const { result } = renderHook(() => useTournaments({ tier: "major" }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tournamentsApi.list).toHaveBeenCalledWith({ tier: "major" });
  });

  it("should handle pagination", async () => {
    vi.mocked(tournamentsApi.list).mockResolvedValue({
      ...mockListResponse,
      page: 2,
      has_prev: true,
    });

    const { result } = renderHook(
      () => useTournaments({ page: 2, limit: 50 }),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tournamentsApi.list).toHaveBeenCalledWith({ page: 2, limit: 50 });
  });

  it("should handle API errors", async () => {
    vi.mocked(tournamentsApi.list).mockRejectedValue(new Error("API Error"));

    const { result } = renderHook(() => useTournaments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useTournament", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch tournament by ID", async () => {
    vi.mocked(tournamentsApi.getById).mockResolvedValue(mockTournamentDetail);

    const { result } = renderHook(() => useTournament("tournament-123"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockTournamentDetail);
    expect(tournamentsApi.getById).toHaveBeenCalledWith("tournament-123");
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useTournament(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(tournamentsApi.getById).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(tournamentsApi.getById).mockRejectedValue(
      new Error("Tournament not found")
    );

    const { result } = renderHook(() => useTournament("nonexistent"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("usePlacementDecklist", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch placement decklist", async () => {
    vi.mocked(tournamentsApi.getPlacementDecklist).mockResolvedValue(
      mockDecklist
    );

    const { result } = renderHook(
      () => usePlacementDecklist("tournament-123", "placement-1"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockDecklist);
    expect(tournamentsApi.getPlacementDecklist).toHaveBeenCalledWith(
      "tournament-123",
      "placement-1"
    );
  });

  it("should not fetch when tournament ID is null", async () => {
    const { result } = renderHook(
      () => usePlacementDecklist(null, "placement-1"),
      { wrapper: createWrapper() }
    );

    expect(result.current.isFetching).toBe(false);
    expect(tournamentsApi.getPlacementDecklist).not.toHaveBeenCalled();
  });

  it("should not fetch when placement ID is null", async () => {
    const { result } = renderHook(
      () => usePlacementDecklist("tournament-123", null),
      { wrapper: createWrapper() }
    );

    expect(result.current.isFetching).toBe(false);
    expect(tournamentsApi.getPlacementDecklist).not.toHaveBeenCalled();
  });

  it("should not fetch when both IDs are null", async () => {
    const { result } = renderHook(() => usePlacementDecklist(null, null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(tournamentsApi.getPlacementDecklist).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(tournamentsApi.getPlacementDecklist).mockRejectedValue(
      new Error("Decklist not found")
    );

    const { result } = renderHook(
      () => usePlacementDecklist("tournament-123", "nonexistent"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
