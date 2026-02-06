import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MetaDivergenceComparison } from "../MetaDivergenceComparison";
import * as api from "@/lib/api";
import type { ApiMetaComparisonResponse } from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  metaApi: {
    compare: vi.fn(),
  },
}));

const mockMetaApi = vi.mocked(api.metaApi);

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
    {
      archetype: "JP Exclusive",
      region_a_share: 0.08,
      region_b_share: 0,
      divergence: 0.08,
      region_a_tier: "B",
      region_b_tier: null,
      sprite_urls: [],
    },
    {
      archetype: "EN Only Deck",
      region_a_share: 0,
      region_b_share: 0.1,
      divergence: -0.1,
      region_a_tier: null,
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

describe("MetaDivergenceComparison", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render loading state initially", () => {
    mockMetaApi.compare.mockReturnValue(new Promise(() => {}));

    render(<MetaDivergenceComparison />, { wrapper: createWrapper() });
    expect(screen.getByText("JP vs International Meta")).toBeInTheDocument();
  });

  it("should render comparison data with confidence badges", async () => {
    mockMetaApi.compare.mockResolvedValue(mockComparisonResponse);

    render(<MetaDivergenceComparison />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    });

    // Check confidence badges are rendered
    const badges = screen.getAllByTestId("confidence-badge");
    expect(badges.length).toBeGreaterThanOrEqual(2);
  });

  it("should show JP Only badge for JP-exclusive archetypes", async () => {
    mockMetaApi.compare.mockResolvedValue(mockComparisonResponse);

    render(<MetaDivergenceComparison />, { wrapper: createWrapper() });

    const jpOnly = await screen.findByText("JP Only");
    expect(jpOnly).toBeInTheDocument();
    expect(screen.getByText("EN Only")).toBeInTheDocument();
  });

  it("should show divergence pp badge for significant divergence", async () => {
    mockMetaApi.compare.mockResolvedValue(mockComparisonResponse);

    render(<MetaDivergenceComparison />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    });

    // +5.0pp divergence for Charizard ex
    expect(screen.getByText("+5.0pp")).toBeInTheDocument();
  });

  it("should toggle lag analysis on button click", async () => {
    mockMetaApi.compare.mockResolvedValue(mockComparisonResponse);

    render(<MetaDivergenceComparison />, { wrapper: createWrapper() });

    const lagButton = await screen.findByText("14-Day Lag");
    expect(lagButton).toBeInTheDocument();

    fireEvent.click(lagButton);

    expect(screen.getByText("Hide Lag")).toBeInTheDocument();
  });

  it("should render with custom className", () => {
    mockMetaApi.compare.mockReturnValue(new Promise(() => {}));

    render(<MetaDivergenceComparison className="custom-class" />, {
      wrapper: createWrapper(),
    });
    expect(screen.getByText("JP vs International Meta")).toBeInTheDocument();
  });

  it("should show error state", async () => {
    mockMetaApi.compare.mockRejectedValue(new Error("Failed"));

    render(<MetaDivergenceComparison />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(
        screen.getByText("Failed to load meta comparison")
      ).toBeInTheDocument();
    });
  });

  it("should render empty state when no comparisons", async () => {
    mockMetaApi.compare.mockResolvedValue({
      ...mockComparisonResponse,
      comparisons: [],
    });

    render(<MetaDivergenceComparison />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("No data available")).toBeInTheDocument();
    });
  });
});
