import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { FormatForecast } from "../FormatForecast";
import type { ApiFormatForecastResponse } from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  metaApi: {
    getForecast: vi.fn(),
  },
  japanApi: {
    listPredictions: vi.fn(),
  },
}));

import { metaApi, japanApi } from "@/lib/api";

const mockForecast: ApiFormatForecastResponse = {
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
    {
      archetype: "Charizard ex",
      jp_share: 0.2,
      en_share: 0.18,
      divergence: 0.02,
      tier: "S",
      trend_direction: "stable",
      sprite_urls: [],
      confidence: "high",
    },
  ],
  jp_snapshot_date: "2026-02-05",
  en_snapshot_date: "2026-02-05",
  jp_sample_size: 200,
  en_sample_size: 500,
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
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe("FormatForecast", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(japanApi.listPredictions).mockResolvedValue({
      items: [],
      total: 0,
      resolved: 0,
      correct: 0,
      partial: 0,
      incorrect: 0,
    });
  });

  it("should render forecast data with archetype names", async () => {
    vi.mocked(metaApi.getForecast).mockResolvedValue(mockForecast);

    render(<FormatForecast />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Raging Bolt ex")).toBeInTheDocument();
    });
    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
  });

  it("should show Format Forecast label", async () => {
    vi.mocked(metaApi.getForecast).mockResolvedValue(mockForecast);

    render(<FormatForecast />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("FORMAT FORECAST")).toBeInTheDocument();
    });
  });

  it("should show divergence badges", async () => {
    vi.mocked(metaApi.getForecast).mockResolvedValue(mockForecast);

    render(<FormatForecast />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("+7.0pp")).toBeInTheDocument();
    });
    expect(screen.getByText("+2.0pp")).toBeInTheDocument();
  });

  it("should show deep dive link to japan page", async () => {
    vi.mocked(metaApi.getForecast).mockResolvedValue(mockForecast);

    render(<FormatForecast />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(
        screen.getByText("Deep Dive: Full JP Analysis")
      ).toBeInTheDocument();
    });
  });

  it("should render loading skeleton", () => {
    vi.mocked(metaApi.getForecast).mockReturnValue(new Promise(() => {}));

    render(<FormatForecast />, { wrapper: createWrapper() });

    expect(screen.getByText("FORMAT FORECAST")).toBeInTheDocument();
  });

  it("should return null when no data and not loading", async () => {
    vi.mocked(metaApi.getForecast).mockResolvedValue({
      ...mockForecast,
      forecast_archetypes: [],
    });

    const { container } = render(<FormatForecast />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(container.querySelector("section")).toBeNull();
    });
  });

  it("should hide section gracefully when API returns error", async () => {
    vi.mocked(metaApi.getForecast).mockRejectedValue(
      new Error("Internal Server Error")
    );

    const { container } = render(<FormatForecast />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(container.querySelector("section")).toBeNull();
    });
  });

  it("should render single archetype correctly", async () => {
    vi.mocked(metaApi.getForecast).mockResolvedValue({
      ...mockForecast,
      forecast_archetypes: [mockForecast.forecast_archetypes[0]],
    });

    render(<FormatForecast />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Raging Bolt ex")).toBeInTheDocument();
    });
    expect(screen.queryByText("Charizard ex")).not.toBeInTheDocument();
  });
});
