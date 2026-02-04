import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  useEvolutionArticles,
  useEvolutionArticle,
  useArchetypeEvolution,
  useArchetypePrediction,
  usePredictionAccuracy,
} from "../useEvolution";
import type {
  ApiEvolutionArticleListItem,
  ApiEvolutionArticle,
  ApiEvolutionTimeline,
  ApiArchetypePrediction,
  ApiPredictionAccuracy,
} from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  evolutionApi: {
    listArticles: vi.fn(),
    getArticleBySlug: vi.fn(),
    getAccuracy: vi.fn(),
    getArchetypeEvolution: vi.fn(),
    getArchetypePrediction: vi.fn(),
  },
}));

import { evolutionApi } from "@/lib/api";

const mockArticleListItem: ApiEvolutionArticleListItem = {
  id: "article-1",
  archetype_id: "charizard-ex",
  slug: "charizard-ex-evolution",
  title: "Charizard ex: A Journey Through the Meta",
  excerpt: "How Charizard ex has adapted over the season.",
  status: "published",
  is_premium: false,
  published_at: "2025-01-15T00:00:00Z",
};

const mockArticle: ApiEvolutionArticle = {
  ...mockArticleListItem,
  introduction: "Charizard ex has been a meta staple...",
  conclusion: "Looking forward, expect more tech choices...",
  view_count: 1500,
  share_count: 42,
  snapshots: [
    {
      id: "snapshot-1",
      archetype: "charizard-ex",
      tournament_id: "tournament-1",
      meta_share: 0.185,
      top_cut_conversion: 0.22,
      best_placement: 1,
      deck_count: 45,
      consensus_list: null,
      meta_context: "Charizard dominated after LAIC",
      adaptations: [],
      created_at: "2025-01-10T00:00:00Z",
    },
  ],
};

const mockTimeline: ApiEvolutionTimeline = {
  archetype: "charizard-ex",
  snapshots: [
    {
      id: "snapshot-2",
      archetype: "charizard-ex",
      tournament_id: "tournament-2",
      meta_share: 0.192,
      top_cut_conversion: 0.25,
      best_placement: 2,
      deck_count: 52,
      consensus_list: null,
      meta_context: null,
      adaptations: [
        {
          id: "adapt-1",
          type: "tech",
          description: "Added Unfair Stamp for Lugia matchup",
          cards_added: [{ name: "Unfair Stamp", count: 1 }],
          cards_removed: [{ name: "Boss's Orders", count: 1 }],
          target_archetype: "lugia-vstar",
          confidence: 0.85,
          source: "diff",
        },
      ],
      created_at: "2025-01-20T00:00:00Z",
    },
  ],
};

const mockPrediction: ApiArchetypePrediction = {
  id: "pred-1",
  archetype_id: "charizard-ex",
  target_tournament_id: "tournament-3",
  predicted_meta_share: { low: 0.15, mid: 0.18, high: 0.22 },
  predicted_day2_rate: { low: 0.18, mid: 0.22, high: 0.26 },
  predicted_tier: "S",
  likely_adaptations: [{ type: "tech", description: "Expect Iron Hands" }],
  confidence: 0.75,
  methodology: "Historical + JP signals",
  actual_meta_share: null,
  accuracy_score: null,
  created_at: "2025-01-18T00:00:00Z",
};

const mockAccuracy: ApiPredictionAccuracy = {
  total_predictions: 50,
  scored_predictions: 35,
  average_accuracy: 0.73,
  predictions: [mockPrediction],
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

describe("useEvolutionArticles", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch evolution articles", async () => {
    vi.mocked(evolutionApi.listArticles).mockResolvedValue([mockArticleListItem]);

    const { result } = renderHook(() => useEvolutionArticles({ limit: 20 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([mockArticleListItem]);
    expect(evolutionApi.listArticles).toHaveBeenCalledWith({ limit: 20 });
  });

  it("should handle API errors", async () => {
    vi.mocked(evolutionApi.listArticles).mockRejectedValue(new Error("API Error"));

    const { result } = renderHook(() => useEvolutionArticles(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });

  it("should pass pagination parameters including offset", async () => {
    vi.mocked(evolutionApi.listArticles).mockResolvedValue([mockArticleListItem]);

    const { result } = renderHook(
      () => useEvolutionArticles({ limit: 10, offset: 20 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([mockArticleListItem]);
    expect(evolutionApi.listArticles).toHaveBeenCalledWith({
      limit: 10,
      offset: 20,
    });
  });
});

describe("useEvolutionArticle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch a single article by slug", async () => {
    vi.mocked(evolutionApi.getArticleBySlug).mockResolvedValue(mockArticle);

    const { result } = renderHook(
      () => useEvolutionArticle("charizard-ex-evolution"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockArticle);
    expect(evolutionApi.getArticleBySlug).toHaveBeenCalledWith(
      "charizard-ex-evolution"
    );
  });

  it("should not fetch when slug is null", async () => {
    const { result } = renderHook(() => useEvolutionArticle(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(evolutionApi.getArticleBySlug).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(evolutionApi.getArticleBySlug).mockRejectedValue(
      new Error("Article not found")
    );

    const { result } = renderHook(
      () => useEvolutionArticle("nonexistent-slug"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useArchetypeEvolution", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch archetype evolution timeline", async () => {
    vi.mocked(evolutionApi.getArchetypeEvolution).mockResolvedValue(mockTimeline);

    const { result } = renderHook(
      () => useArchetypeEvolution("charizard-ex", 10),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockTimeline);
    expect(evolutionApi.getArchetypeEvolution).toHaveBeenCalledWith(
      "charizard-ex",
      10
    );
  });

  it("should not fetch when archetypeId is null", async () => {
    const { result } = renderHook(() => useArchetypeEvolution(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(evolutionApi.getArchetypeEvolution).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(evolutionApi.getArchetypeEvolution).mockRejectedValue(
      new Error("Evolution data not found")
    );

    const { result } = renderHook(
      () => useArchetypeEvolution("nonexistent-archetype"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useArchetypePrediction", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch archetype prediction", async () => {
    vi.mocked(evolutionApi.getArchetypePrediction).mockResolvedValue(
      mockPrediction
    );

    const { result } = renderHook(
      () => useArchetypePrediction("charizard-ex"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockPrediction);
    expect(evolutionApi.getArchetypePrediction).toHaveBeenCalledWith(
      "charizard-ex"
    );
  });

  it("should not fetch when archetypeId is null", async () => {
    const { result } = renderHook(() => useArchetypePrediction(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(evolutionApi.getArchetypePrediction).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(evolutionApi.getArchetypePrediction).mockRejectedValue(
      new Error("Prediction not found")
    );

    const { result } = renderHook(
      () => useArchetypePrediction("nonexistent-archetype"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("usePredictionAccuracy", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch prediction accuracy", async () => {
    vi.mocked(evolutionApi.getAccuracy).mockResolvedValue(mockAccuracy);

    const { result } = renderHook(() => usePredictionAccuracy(20), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockAccuracy);
    expect(evolutionApi.getAccuracy).toHaveBeenCalledWith(20);
  });

  it("should handle API errors", async () => {
    vi.mocked(evolutionApi.getAccuracy).mockRejectedValue(new Error("API Error"));

    const { result } = renderHook(() => usePredictionAccuracy(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
