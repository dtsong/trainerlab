import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import JapanMetaPage from "../page";
import type {
  ApiMetaSnapshot,
  ApiArchetypeDetailResponse,
} from "@trainerlab/shared-types";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

// Mock all child components to isolate page-level tests
vi.mock("@/components/meta", () => ({
  MetaPieChart: () => <div data-testid="meta-pie-chart" />,
  MetaTrendChart: () => <div data-testid="meta-trend-chart" />,
  DateRangePicker: () => <div data-testid="date-range-picker" />,
  BO1ContextBanner: () => <div data-testid="bo1-context-banner" />,
  ChartErrorBoundary: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

vi.mock("@/components/japan", () => ({
  CardInnovationTracker: () => <div data-testid="card-innovation" />,
  NewArchetypeWatch: () => <div data-testid="new-archetype-watch" />,
  CityLeagueResultsFeed: () => <div data-testid="city-league-feed" />,
  MetaDivergenceComparison: () => <div data-testid="meta-divergence" />,
  CardCountEvolutionSection: () => <div data-testid="card-count-evo" />,
  CardAdoptionRates: () => <div data-testid="card-adoption" />,
  UpcomingCards: () => <div data-testid="upcoming-cards" />,
}));

vi.mock("@/lib/api", () => ({
  metaApi: {
    getCurrent: vi.fn(),
    getHistory: vi.fn(),
    getArchetypeDetail: vi.fn(),
  },
}));

vi.mock("@/lib/meta-utils", () => ({
  transformSnapshot: vi.fn((s: unknown) => s),
  parseDays: vi.fn(() => 30),
  getErrorMessage: vi.fn(() => "Error message"),
}));

import { metaApi } from "@/lib/api";

const mockSnapshot: ApiMetaSnapshot = {
  snapshot_date: "2026-02-05",
  region: "JP",
  format: "standard",
  best_of: 1,
  archetype_breakdown: [
    {
      name: "Charizard ex",
      share: 0.2,
      key_cards: [],
      sprite_urls: [],
    },
    {
      name: "Raging Bolt ex",
      share: 0.15,
      key_cards: [],
      sprite_urls: [],
    },
    {
      name: "Dragapult ex",
      share: 0.1,
      key_cards: [],
      sprite_urls: [],
    },
  ],
  card_usage: [],
  sample_size: 250,
};

const mockArchetypeDetail: ApiArchetypeDetailResponse = {
  name: "Charizard ex",
  current_share: 0.2,
  history: [],
  key_cards: [
    { card_id: "Charizard ex SV4-6", inclusion_rate: 0.95, avg_copies: 2.0 },
    { card_id: "Rare Candy SV1-191", inclusion_rate: 0.92, avg_copies: 4.0 },
    { card_id: "Rotom V CRZ-45", inclusion_rate: 0.55, avg_copies: 1.2 },
  ],
  sample_decks: [],
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe("JapanMetaPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(metaApi.getHistory).mockResolvedValue({ snapshots: [] });
    vi.mocked(metaApi.getArchetypeDetail).mockResolvedValue(
      mockArchetypeDetail
    );
  });

  it("should render persistent BO1 context strip", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("bo1-context-strip")).toBeInTheDocument();
    });
    expect(screen.getByText(/Best-of-1/)).toBeInTheDocument();
  });

  it("should render confidence badge when data loads", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("confidence-badge")).toBeInTheDocument();
    });
  });

  it("should render tech card insights with archetype buttons", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);
    vi.mocked(metaApi.getArchetypeDetail).mockResolvedValue(
      mockArchetypeDetail
    );

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Tech Card Insights")).toBeInTheDocument();
    });

    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    expect(screen.getByText("Raging Bolt ex")).toBeInTheDocument();
  });

  it("should show core and tech card groups", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);
    vi.mocked(metaApi.getArchetypeDetail).mockResolvedValue(
      mockArchetypeDetail
    );

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Core/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Tech \(flex slots\)/)).toBeInTheDocument();

    // Core cards
    expect(screen.getByText("Charizard ex SV4-6")).toBeInTheDocument();
    expect(screen.getByText("Rare Candy SV1-191")).toBeInTheDocument();

    // Tech cards
    expect(screen.getByText("Rotom V CRZ-45")).toBeInTheDocument();
  });

  it("should switch archetypes when clicking buttons", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);
    vi.mocked(metaApi.getArchetypeDetail).mockResolvedValue(
      mockArchetypeDetail
    );

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Raging Bolt ex")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Raging Bolt ex"));

    // Should have called getArchetypeDetail with the new name
    await waitFor(() => {
      expect(metaApi.getArchetypeDetail).toHaveBeenCalledWith(
        "Raging Bolt ex",
        expect.objectContaining({ region: "JP", best_of: 1 })
      );
    });
  });
});
