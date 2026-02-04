import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/api", () => ({
  translationsApi: {
    getAdoptionRates: vi.fn(),
    getUpcomingCards: vi.fn(),
  },
}));

import { translationsApi } from "@/lib/api";
import { useJPAdoptionRates, useJPUpcomingCards } from "../useTranslations";

const mockAdoptionRates = {
  items: [
    {
      card_id: "sv5-101",
      card_name: "Dragapult ex",
      adoption_rate: 0.85,
      archetype: "Dragapult ex",
    },
  ],
  total: 1,
};

const mockUpcomingCards = {
  items: [
    {
      card_id: "sv6-050",
      card_name: "Upcoming Card",
      set_code: "sv6",
      impact_score: 7.5,
      released_in_en: false,
    },
  ],
  total: 1,
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

describe("useJPAdoptionRates", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch adoption rates with default params", async () => {
    vi.mocked(translationsApi.getAdoptionRates).mockResolvedValue(
      mockAdoptionRates
    );

    const { result } = renderHook(() => useJPAdoptionRates(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockAdoptionRates);
    expect(translationsApi.getAdoptionRates).toHaveBeenCalledWith({});
  });

  it("should fetch adoption rates with params", async () => {
    vi.mocked(translationsApi.getAdoptionRates).mockResolvedValue(
      mockAdoptionRates
    );

    const params = { days: 30, archetype: "Dragapult ex", limit: 10 };
    const { result } = renderHook(() => useJPAdoptionRates(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(translationsApi.getAdoptionRates).toHaveBeenCalledWith(params);
  });

  it("should handle API errors", async () => {
    vi.mocked(translationsApi.getAdoptionRates).mockRejectedValue(
      new Error("Server error")
    );

    const { result } = renderHook(() => useJPAdoptionRates(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useJPUpcomingCards", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch upcoming cards with default params", async () => {
    vi.mocked(translationsApi.getUpcomingCards).mockResolvedValue(
      mockUpcomingCards
    );

    const { result } = renderHook(() => useJPUpcomingCards(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockUpcomingCards);
    expect(translationsApi.getUpcomingCards).toHaveBeenCalledWith({});
  });

  it("should fetch upcoming cards with params", async () => {
    vi.mocked(translationsApi.getUpcomingCards).mockResolvedValue(
      mockUpcomingCards
    );

    const params = { include_released: true, min_impact: 5, limit: 20 };
    const { result } = renderHook(() => useJPUpcomingCards(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(translationsApi.getUpcomingCards).toHaveBeenCalledWith(params);
  });

  it("should handle API errors", async () => {
    vi.mocked(translationsApi.getUpcomingCards).mockRejectedValue(
      new Error("Server error")
    );

    const { result } = renderHook(() => useJPUpcomingCards(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
