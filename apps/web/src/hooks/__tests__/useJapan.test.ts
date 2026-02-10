import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/api", () => ({
  japanApi: {
    listInnovations: vi.fn(),
    getInnovationDetail: vi.fn(),
    listNewArchetypes: vi.fn(),
    listSetImpacts: vi.fn(),
    listPredictions: vi.fn(),
    getCardCountEvolution: vi.fn(),
  },
}));

import { japanApi } from "@/lib/api";
import {
  useJPCardInnovations,
  useJPCardInnovationDetail,
  useJPNewArchetypes,
  useJPSetImpacts,
  usePredictions,
  useCardCountEvolution,
} from "../useJapan";

const mockInnovationList = {
  items: [
    {
      id: "inno-1",
      card_id: "sv5-101",
      card_name: "Dragapult ex",
      set_code: "sv5",
      is_legal_en: false,
      adoption_rate: 0.85,
      competitive_impact_rating: 8.5,
      sample_size: 50,
    },
  ],
  total: 1,
};

const mockInnovationDetail = {
  id: "inno-1",
  card_id: "sv5-101",
  card_name: "Dragapult ex",
  set_code: "sv5",
  is_legal_en: false,
  adoption_rate: 0.85,
  competitive_impact_rating: 8.5,
  sample_size: 50,
};

const mockArchetypeList = {
  items: [
    {
      id: "arch-1",
      archetype_id: "dragapult-ex",
      name: "Dragapult ex",
      jp_meta_share: 12.5,
    },
  ],
  total: 1,
};

const mockSetImpactList = {
  items: [
    {
      id: "si-1",
      set_code: "sv5",
      set_name: "Temporal Forces",
      jp_release_date: "2024-01-26",
    },
  ],
  total: 1,
};

const mockPredictionList = {
  items: [
    {
      id: "pred-1",
      prediction_text: "Dragapult will rise",
      target_event: "Regional",
      created_at: "2024-01-01T00:00:00Z",
    },
  ],
  total: 1,
  resolved: 0,
  correct: 0,
  partial: 0,
  incorrect: 0,
};

const mockCardCountEvolution = {
  archetype: "Dragapult ex",
  cards: [
    {
      card_id: "sv5-101",
      card_name: "Dragapult ex",
      data_points: [
        {
          snapshot_date: "2024-01-01",
          avg_copies: 4,
          inclusion_rate: 0.95,
          sample_size: 20,
        },
      ],
      total_change: 0,
      current_avg: 4,
    },
  ],
  tournaments_analyzed: 5,
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

describe("useJPCardInnovations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch innovations with default params", async () => {
    vi.mocked(japanApi.listInnovations).mockResolvedValue(mockInnovationList);

    const { result } = renderHook(() => useJPCardInnovations(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockInnovationList);
    expect(japanApi.listInnovations).toHaveBeenCalledWith({});
  });

  it("should fetch innovations with params", async () => {
    vi.mocked(japanApi.listInnovations).mockResolvedValue(mockInnovationList);

    const params = {
      set_code: "sv5",
      en_legal: true,
      min_impact: 5,
      limit: 10,
    };
    const { result } = renderHook(() => useJPCardInnovations(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(japanApi.listInnovations).toHaveBeenCalledWith(params);
  });

  it("should handle API errors", async () => {
    vi.mocked(japanApi.listInnovations).mockRejectedValue(
      new Error("Failed to fetch innovations")
    );

    const { result } = renderHook(() => useJPCardInnovations(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useJPCardInnovationDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch innovation detail by card ID", async () => {
    vi.mocked(japanApi.getInnovationDetail).mockResolvedValue(
      mockInnovationDetail
    );

    const { result } = renderHook(() => useJPCardInnovationDetail("sv5-101"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockInnovationDetail);
    expect(japanApi.getInnovationDetail).toHaveBeenCalledWith("sv5-101");
  });

  it("should not fetch when cardId is null", async () => {
    const { result } = renderHook(() => useJPCardInnovationDetail(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(japanApi.getInnovationDetail).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(japanApi.getInnovationDetail).mockRejectedValue(
      new Error("Not found")
    );

    const { result } = renderHook(() => useJPCardInnovationDetail("bad-id"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useJPNewArchetypes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch new archetypes with default params", async () => {
    vi.mocked(japanApi.listNewArchetypes).mockResolvedValue(mockArchetypeList);

    const { result } = renderHook(() => useJPNewArchetypes(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockArchetypeList);
    expect(japanApi.listNewArchetypes).toHaveBeenCalledWith({});
  });

  it("should fetch new archetypes with params", async () => {
    vi.mocked(japanApi.listNewArchetypes).mockResolvedValue(mockArchetypeList);

    const params = { set_code: "sv5", limit: 5 };
    const { result } = renderHook(() => useJPNewArchetypes(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(japanApi.listNewArchetypes).toHaveBeenCalledWith(params);
  });

  it("should handle API errors", async () => {
    vi.mocked(japanApi.listNewArchetypes).mockRejectedValue(
      new Error("Server error")
    );

    const { result } = renderHook(() => useJPNewArchetypes(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useJPSetImpacts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch set impacts with default params", async () => {
    vi.mocked(japanApi.listSetImpacts).mockResolvedValue(mockSetImpactList);

    const { result } = renderHook(() => useJPSetImpacts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockSetImpactList);
    expect(japanApi.listSetImpacts).toHaveBeenCalledWith({});
  });

  it("should fetch set impacts with params", async () => {
    vi.mocked(japanApi.listSetImpacts).mockResolvedValue(mockSetImpactList);

    const params = { set_code: "sv5", limit: 3 };
    const { result } = renderHook(() => useJPSetImpacts(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(japanApi.listSetImpacts).toHaveBeenCalledWith(params);
  });

  it("should handle API errors", async () => {
    vi.mocked(japanApi.listSetImpacts).mockRejectedValue(
      new Error("Server error")
    );

    const { result } = renderHook(() => useJPSetImpacts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("usePredictions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch predictions with default params", async () => {
    vi.mocked(japanApi.listPredictions).mockResolvedValue(mockPredictionList);

    const { result } = renderHook(() => usePredictions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockPredictionList);
    expect(japanApi.listPredictions).toHaveBeenCalledWith({});
  });

  it("should fetch predictions with params", async () => {
    vi.mocked(japanApi.listPredictions).mockResolvedValue(mockPredictionList);

    const params = { category: "archetype", resolved_only: true, limit: 10 };
    const { result } = renderHook(() => usePredictions(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(japanApi.listPredictions).toHaveBeenCalledWith(params);
  });

  it("should handle API errors", async () => {
    vi.mocked(japanApi.listPredictions).mockRejectedValue(
      new Error("Server error")
    );

    const { result } = renderHook(() => usePredictions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useCardCountEvolution", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch card count evolution with params", async () => {
    vi.mocked(japanApi.getCardCountEvolution).mockResolvedValue(
      mockCardCountEvolution
    );

    const params = { archetype: "Dragapult ex", days: 30, top_cards: 5 };
    const { result } = renderHook(() => useCardCountEvolution(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockCardCountEvolution);
    expect(japanApi.getCardCountEvolution).toHaveBeenCalledWith(params);
  });

  it("should not fetch when params is null", async () => {
    const { result } = renderHook(() => useCardCountEvolution(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(japanApi.getCardCountEvolution).not.toHaveBeenCalled();
  });

  it("should not fetch when archetype is empty string", async () => {
    const { result } = renderHook(
      () => useCardCountEvolution({ archetype: "", days: 30 }),
      { wrapper: createWrapper() }
    );

    expect(result.current.isFetching).toBe(false);
    expect(japanApi.getCardCountEvolution).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(japanApi.getCardCountEvolution).mockRejectedValue(
      new Error("Server error")
    );

    const params = { archetype: "Dragapult ex" };
    const { result } = renderHook(() => useCardCountEvolution(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
