import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CardCountEvolutionSection } from "../CardCountEvolutionSection";
import * as api from "@/lib/api";

// Mock ResizeObserver for Recharts
beforeEach(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

vi.mock("@/lib/api", () => ({
  japanApi: {
    getCardCountEvolution: vi.fn(),
  },
}));

const mockJapanApi = vi.mocked(api.japanApi);

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

const defaultProps = {
  archetypes: ["Charizard ex", "Lugia VSTAR", "Gardevoir ex"],
  selectedArchetype: "Charizard ex",
  onArchetypeChange: vi.fn(),
};

describe("CardCountEvolutionSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render section title and description", () => {
    mockJapanApi.getCardCountEvolution.mockReturnValue(new Promise(() => {}));

    render(<CardCountEvolutionSection {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText("Card Count Evolution")).toBeInTheDocument();
    expect(
      screen.getByText(
        "How average card copies change over time within an archetype"
      )
    ).toBeInTheDocument();
  });

  it("should render archetype selector", () => {
    mockJapanApi.getCardCountEvolution.mockReturnValue(new Promise(() => {}));

    render(<CardCountEvolutionSection {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByTestId("archetype-selector")).toBeInTheDocument();
  });

  it("should render test id", () => {
    mockJapanApi.getCardCountEvolution.mockReturnValue(new Promise(() => {}));

    render(<CardCountEvolutionSection {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByTestId("card-count-section")).toBeInTheDocument();
  });

  it("should show chart when data loads", async () => {
    mockJapanApi.getCardCountEvolution.mockResolvedValue({
      archetype: "Charizard ex",
      cards: [
        {
          card_id: "sv4-6",
          card_name: "Charizard ex",
          data_points: [
            {
              snapshot_date: "2024-01-08",
              avg_copies: 3.0,
              inclusion_rate: 0.9,
              sample_size: 10,
            },
          ],
          total_change: 0.5,
          current_avg: 3.0,
        },
      ],
      tournaments_analyzed: 5,
    });

    render(<CardCountEvolutionSection {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    const chartContainer = await screen.findByTestId("card-count-chart");
    expect(chartContainer).toBeInTheDocument();
    expect(screen.getByText("Based on 5 tournaments")).toBeInTheDocument();
  });

  it("should not render selector when no archetypes", () => {
    mockJapanApi.getCardCountEvolution.mockReturnValue(new Promise(() => {}));

    render(<CardCountEvolutionSection {...defaultProps} archetypes={[]} />, {
      wrapper: createWrapper(),
    });

    expect(screen.queryByTestId("archetype-selector")).not.toBeInTheDocument();
  });
});
