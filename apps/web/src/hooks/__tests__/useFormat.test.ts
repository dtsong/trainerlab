import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type {
  ApiFormatConfig,
  ApiUpcomingFormat,
  ApiRotationImpactList,
  ApiRotationImpact,
} from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  formatApi: {
    getCurrent: vi.fn(),
    getUpcoming: vi.fn(),
  },
  rotationApi: {
    getImpacts: vi.fn(),
    getArchetypeImpact: vi.fn(),
  },
}));

import { formatApi, rotationApi } from "@/lib/api";
import {
  useCurrentFormat,
  useUpcomingFormat,
  useRotationImpacts,
  useArchetypeRotationImpact,
} from "../useFormat";

const mockCurrentFormat: ApiFormatConfig = {
  id: "format-1",
  name: "svi-tef",
  display_name: "Scarlet & Violet - Temporal Forces",
  legal_sets: ["sv1", "sv2", "sv3", "sv4", "sv5"],
  start_date: "2024-03-01",
  end_date: null,
  is_current: true,
  is_upcoming: false,
  rotation_details: null,
};

const mockUpcomingFormat: ApiUpcomingFormat = {
  format: {
    ...mockCurrentFormat,
    id: "format-2",
    name: "svi-por",
    display_name: "Scarlet & Violet - Paldean Fates",
    is_current: false,
    is_upcoming: true,
    start_date: "2024-09-01",
    rotation_details: {
      rotating_out_sets: ["sv1", "sv2"],
      new_set: "sv6",
    },
  },
  days_until_rotation: 60,
  rotation_date: "2024-09-01",
};

const mockRotationImpactList: ApiRotationImpactList = {
  format_transition: "svi-tef-to-svi-por",
  impacts: [
    {
      id: "impact-1",
      format_transition: "svi-tef-to-svi-por",
      archetype_id: "charizard-ex",
      archetype_name: "Charizard ex",
      survival_rating: "adapts",
      rotating_cards: [
        {
          card_name: "Arven",
          card_id: "sv1-166",
          count: 4,
          role: "supporter",
          replacement: "Iono",
        },
      ],
      analysis: "Charizard ex remains viable.",
      jp_evidence: "Strong JP results",
      jp_survival_share: 0.15,
    },
  ],
  total_archetypes: 1,
};

const mockArchetypeImpact: ApiRotationImpact = {
  id: "impact-1",
  format_transition: "svi-tef-to-svi-por",
  archetype_id: "charizard-ex",
  archetype_name: "Charizard ex",
  survival_rating: "adapts",
  rotating_cards: [],
  analysis: "Detailed analysis",
  jp_evidence: "JP evidence",
  jp_survival_share: 0.15,
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

describe("useCurrentFormat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch current format", async () => {
    vi.mocked(formatApi.getCurrent).mockResolvedValue(mockCurrentFormat);

    const { result } = renderHook(() => useCurrentFormat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockCurrentFormat);
    expect(formatApi.getCurrent).toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(formatApi.getCurrent).mockRejectedValue(
      new Error("Failed to fetch format")
    );

    const { result } = renderHook(() => useCurrentFormat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useUpcomingFormat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch upcoming format with countdown", async () => {
    vi.mocked(formatApi.getUpcoming).mockResolvedValue(mockUpcomingFormat);

    const { result } = renderHook(() => useUpcomingFormat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockUpcomingFormat);
    expect(result.current.data?.days_until_rotation).toBe(60);
  });

  it("should handle API errors", async () => {
    vi.mocked(formatApi.getUpcoming).mockRejectedValue(
      new Error("No upcoming format")
    );

    const { result } = renderHook(() => useUpcomingFormat(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useRotationImpacts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch rotation impacts for transition", async () => {
    vi.mocked(rotationApi.getImpacts).mockResolvedValue(mockRotationImpactList);

    const { result } = renderHook(
      () => useRotationImpacts("svi-tef-to-svi-por"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockRotationImpactList);
    expect(rotationApi.getImpacts).toHaveBeenCalledWith("svi-tef-to-svi-por");
  });

  it("should not fetch when transition is empty", async () => {
    const { result } = renderHook(() => useRotationImpacts(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(rotationApi.getImpacts).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(rotationApi.getImpacts).mockRejectedValue(
      new Error("Failed to fetch impacts")
    );

    const { result } = renderHook(
      () => useRotationImpacts("svi-tef-to-svi-por"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useArchetypeRotationImpact", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch archetype rotation impact", async () => {
    vi.mocked(rotationApi.getArchetypeImpact).mockResolvedValue(
      mockArchetypeImpact
    );

    const { result } = renderHook(
      () => useArchetypeRotationImpact("charizard-ex"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockArchetypeImpact);
    expect(rotationApi.getArchetypeImpact).toHaveBeenCalledWith(
      "charizard-ex",
      undefined
    );
  });

  it("should fetch with specific transition", async () => {
    vi.mocked(rotationApi.getArchetypeImpact).mockResolvedValue(
      mockArchetypeImpact
    );

    const { result } = renderHook(
      () => useArchetypeRotationImpact("charizard-ex", "svi-tef-to-svi-por"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(rotationApi.getArchetypeImpact).toHaveBeenCalledWith(
      "charizard-ex",
      "svi-tef-to-svi-por"
    );
  });

  it("should not fetch when archetype ID is empty", async () => {
    const { result } = renderHook(() => useArchetypeRotationImpact(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(rotationApi.getArchetypeImpact).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(rotationApi.getArchetypeImpact).mockRejectedValue(
      new Error("Archetype not found")
    );

    const { result } = renderHook(
      () => useArchetypeRotationImpact("nonexistent"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
