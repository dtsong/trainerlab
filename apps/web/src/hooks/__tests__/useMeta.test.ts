import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  useCurrentMeta,
  useMetaHistory,
  useHomeMetaData,
  useMetaComparison,
  useFormatForecast,
} from "../useMeta";
import type {
  ApiMetaSnapshot,
  ApiMetaHistoryResponse,
  ApiMetaComparisonResponse,
  ApiFormatForecastResponse,
} from "@trainerlab/shared-types";

// Mock the API module
vi.mock("@/lib/api", () => ({
  metaApi: {
    getCurrent: vi.fn(),
    getHistory: vi.fn(),
    compare: vi.fn(),
    getForecast: vi.fn(),
  },
}));

import { metaApi } from "@/lib/api";

const mockSnapshot: ApiMetaSnapshot = {
  snapshot_date: "2025-01-15",
  region: null,
  format: "standard",
  best_of: 3,
  archetype_breakdown: [
    { name: "Charizard ex", share: 18.5 },
    { name: "Lugia VSTAR", share: 14.2 },
  ],
  card_usage: [],
  sample_size: 100,
};

const mockJPSnapshot: ApiMetaSnapshot = {
  ...mockSnapshot,
  region: "JP",
  best_of: 1,
  archetype_breakdown: [
    { name: "Raging Bolt ex", share: 22.1 },
    { name: "Charizard ex", share: 15.8 },
  ],
  sample_size: 50,
};

const mockHistory: ApiMetaHistoryResponse = {
  snapshots: [
    {
      ...mockSnapshot,
      snapshot_date: "2024-12-15",
      archetype_breakdown: [
        { name: "Charizard ex", share: 15.0 },
        { name: "Lugia VSTAR", share: 16.0 },
      ],
    },
    mockSnapshot,
  ],
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

describe("useCurrentMeta", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch current meta data", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);

    const { result } = renderHook(() => useCurrentMeta({ best_of: 3 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockSnapshot);
    expect(metaApi.getCurrent).toHaveBeenCalledWith({ best_of: 3 });
  });

  it("should handle API errors", async () => {
    vi.mocked(metaApi.getCurrent).mockRejectedValue(new Error("API Error"));

    const { result } = renderHook(() => useCurrentMeta(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useMetaHistory", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch meta history", async () => {
    vi.mocked(metaApi.getHistory).mockResolvedValue(mockHistory);

    const { result } = renderHook(
      () => useMetaHistory({ best_of: 3, days: 30 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockHistory);
    expect(metaApi.getHistory).toHaveBeenCalledWith({ best_of: 3, days: 30 });
  });
});

describe("useHomeMetaData", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch global meta, JP meta, and history in parallel", async () => {
    vi.mocked(metaApi.getCurrent)
      .mockResolvedValueOnce(mockSnapshot)
      .mockResolvedValueOnce(mockJPSnapshot);
    vi.mocked(metaApi.getHistory).mockResolvedValue(mockHistory);

    const { result } = renderHook(() => useHomeMetaData(), {
      wrapper: createWrapper(),
    });

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.globalMeta).toEqual(mockSnapshot);
    expect(result.current.jpMeta).toEqual(mockJPSnapshot);
    expect(result.current.history).toEqual(mockHistory);
    expect(result.current.isError).toBe(false);

    // Should have called getCurrent twice (global + JP) and getHistory once
    expect(metaApi.getCurrent).toHaveBeenCalledTimes(2);
    expect(metaApi.getHistory).toHaveBeenCalledTimes(1);
  });

  it("should report errors when any query fails", async () => {
    vi.mocked(metaApi.getCurrent)
      .mockResolvedValueOnce(mockSnapshot)
      .mockRejectedValueOnce(new Error("JP unavailable"));
    vi.mocked(metaApi.getHistory).mockResolvedValue(mockHistory);

    const { result } = renderHook(() => useHomeMetaData(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.isError).toBe(true);
    expect(result.current.errors.length).toBeGreaterThan(0);
    // Global meta and history should still be available
    expect(result.current.globalMeta).toEqual(mockSnapshot);
    expect(result.current.history).toEqual(mockHistory);
  });
});

const mockComparisonResponse: ApiMetaComparisonResponse = {
  region_a: "JP",
  region_b: "Global",
  region_a_snapshot_date: "2026-02-05",
  region_b_snapshot_date: "2026-02-05",
  comparisons: [
    {
      archetype: "Charizard ex",
      region_a_share: 0.2,
      region_b_share: 0.15,
      divergence: 0.05,
      region_a_tier: "S",
      region_b_tier: "A",
      sprite_urls: [],
    },
  ],
  region_a_confidence: {
    sample_size: 200,
    data_freshness_days: 1,
    confidence: "high",
  },
  region_b_confidence: {
    sample_size: 500,
    data_freshness_days: 1,
    confidence: "high",
  },
  lag_analysis: null,
};

const mockForecastResponse: ApiFormatForecastResponse = {
  forecast_archetypes: [
    {
      archetype: "Raging Bolt ex",
      jp_share: 0.15,
      en_share: 0.08,
      divergence: 0.07,
      tier: "A",
      trend_direction: "up",
      sprite_urls: [],
      confidence: "high",
    },
  ],
  jp_snapshot_date: "2026-02-05",
  en_snapshot_date: "2026-02-05",
  jp_sample_size: 200,
  en_sample_size: 500,
};

describe("useMetaComparison", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch meta comparison data", async () => {
    vi.mocked(metaApi.compare).mockResolvedValue(mockComparisonResponse);

    const { result } = renderHook(() => useMetaComparison({ region_a: "JP" }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockComparisonResponse);
    expect(metaApi.compare).toHaveBeenCalledWith({ region_a: "JP" });
  });

  it("should handle API errors", async () => {
    vi.mocked(metaApi.compare).mockRejectedValue(new Error("Not found"));

    const { result } = renderHook(() => useMetaComparison(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeTruthy();
  });
});

describe("useFormatForecast", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch format forecast data", async () => {
    vi.mocked(metaApi.getForecast).mockResolvedValue(mockForecastResponse);

    const { result } = renderHook(() => useFormatForecast({ top_n: 5 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockForecastResponse);
    expect(metaApi.getForecast).toHaveBeenCalledWith({ top_n: 5 });
  });

  it("should handle API errors", async () => {
    vi.mocked(metaApi.getForecast).mockRejectedValue(new Error("Failed"));

    const { result } = renderHook(() => useFormatForecast(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeTruthy();
  });
});
