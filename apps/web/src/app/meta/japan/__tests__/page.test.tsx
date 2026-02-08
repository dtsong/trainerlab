import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import JapanMetaPage from "../page";
import type {
  ApiMetaSnapshot,
  ApiArchetypeDetailResponse,
} from "@trainerlab/shared-types";

// Capture the push mock so we can assert on it
const mockPush = vi.fn();

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
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
  CardCountEvolutionSection: () => <div data-testid="card-count-evo" />,
  CardAdoptionRates: () => <div data-testid="card-adoption" />,
  UpcomingCards: () => <div data-testid="upcoming-cards" />,
  RotationBriefingHeader: ({ phase }: { phase: string }) => (
    <div data-testid="rotation-briefing-header" data-phase={phase} />
  ),
  JPAnalysisTab: ({ era }: { era?: string }) => (
    <div data-testid="jp-analysis-tab" data-era={era} />
  ),
}));

// Capture Tabs onValueChange so TabsTrigger can call it
let tabsOnValueChange: ((v: string) => void) | undefined;

// Mock shadcn/ui Tabs so we can test tab switching without Radix
vi.mock("@/components/ui/tabs", () => ({
  Tabs: ({
    children,
    value,
    onValueChange,
  }: {
    children: React.ReactNode;
    value: string;
    onValueChange: (v: string) => void;
  }) => {
    tabsOnValueChange = onValueChange;
    return (
      <div data-testid="tabs" data-value={value}>
        {children}
      </div>
    );
  },
  TabsList: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="tabs-list">{children}</div>
  ),
  TabsTrigger: ({
    children,
    value,
  }: {
    children: React.ReactNode;
    value: string;
  }) => (
    <button
      data-testid={`tab-${value}`}
      onClick={() => tabsOnValueChange?.(value)}
    >
      {children}
    </button>
  ),
  TabsContent: ({
    children,
    value,
  }: {
    children: React.ReactNode;
    value: string;
  }) => <div data-testid={`tab-content-${value}`}>{children}</div>,
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
    tabsOnValueChange = undefined;
    vi.mocked(metaApi.getHistory).mockResolvedValue({ snapshots: [] });
    vi.mocked(metaApi.getArchetypeDetail).mockResolvedValue(
      mockArchetypeDetail
    );
  });

  it("should render BO1 context banner", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("bo1-context-banner")).toBeInTheDocument();
    });
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

  it("should render rotation briefing header with post-rotation phase", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      const header = screen.getByTestId("rotation-briefing-header");
      expect(header).toBeInTheDocument();
      expect(header).toHaveAttribute("data-phase", "post-rotation");
    });
  });

  it("should have tabbed layout with Meta Overview and JP Analysis tabs", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("tabs")).toBeInTheDocument();
    });

    expect(screen.getByTestId("tab-overview")).toHaveTextContent(
      "Meta Overview"
    );
    expect(screen.getByTestId("tab-analysis")).toHaveTextContent("JP Analysis");
  });

  it("should render overview tab content by default", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("tab-content-overview")).toBeInTheDocument();
    });

    // Overview tab should contain meta charts and child components
    expect(screen.getByTestId("city-league-feed")).toBeInTheDocument();
    expect(screen.getByTestId("card-adoption")).toBeInTheDocument();
    expect(screen.getByTestId("upcoming-cards")).toBeInTheDocument();
    expect(screen.getByTestId("card-count-evo")).toBeInTheDocument();
  });

  it("should render JP Analysis tab content", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("tab-content-analysis")).toBeInTheDocument();
    });

    const analysisTab = screen.getByTestId("jp-analysis-tab");
    expect(analysisTab).toBeInTheDocument();
    expect(analysisTab).toHaveAttribute("data-era", "post-nihil-zero");
  });

  it("should call router.push on tab switch", async () => {
    vi.mocked(metaApi.getCurrent).mockResolvedValue(mockSnapshot);

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("tab-analysis")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("tab-analysis"));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining("tab=analysis")
      );
    });
  });

  it("should show data freshness warning when data is stale (>48h)", async () => {
    const staleSnapshot: ApiMetaSnapshot = {
      ...mockSnapshot,
      // Set snapshot_date to 4 days ago
      snapshot_date: "2026-02-01",
    };
    vi.mocked(metaApi.getCurrent).mockResolvedValue(staleSnapshot);

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("data-freshness-warning")).toBeInTheDocument();
    });

    expect(screen.getByText(/Data may be stale/)).toBeInTheDocument();
  });

  it("should not show data freshness warning when data is fresh", async () => {
    const freshSnapshot: ApiMetaSnapshot = {
      ...mockSnapshot,
      // Use today's date so it's definitely < 48h old
      snapshot_date: new Date().toISOString().split("T")[0],
    };
    vi.mocked(metaApi.getCurrent).mockResolvedValue(freshSnapshot);

    render(<JapanMetaPage />, { wrapper: createWrapper() });

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByTestId("confidence-badge")).toBeInTheDocument();
    });

    expect(
      screen.queryByTestId("data-freshness-warning")
    ).not.toBeInTheDocument();
  });
});
