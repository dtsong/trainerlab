import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CityLeagueResultsFeed } from "../CityLeagueResultsFeed";
import * as api from "@/lib/api";

vi.mock("@/lib/api", () => ({
  tournamentsApi: {
    list: vi.fn(),
    getPlacementDecklist: vi.fn(),
  },
}));

const mockTournamentsApi = vi.mocked(api.tournamentsApi);

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

describe("CityLeagueResultsFeed", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render loading state initially", () => {
    mockTournamentsApi.list.mockReturnValue(new Promise(() => {}));

    render(<CityLeagueResultsFeed />, { wrapper: createWrapper() });
    expect(screen.getByText("City League Results")).toBeInTheDocument();
  });

  it("should render empty state when no tournaments", async () => {
    mockTournamentsApi.list.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      has_next: false,
      has_prev: false,
    });

    render(<CityLeagueResultsFeed />, { wrapper: createWrapper() });

    const empty = await screen.findByText(
      "No City League results in this date range"
    );
    expect(empty).toBeInTheDocument();
  });

  it("should render tournament items", async () => {
    mockTournamentsApi.list.mockResolvedValue({
      items: [
        {
          id: "t1",
          name: "City League Tokyo",
          date: "2024-03-10",
          region: "JP",
          format: "standard" as const,
          best_of: 1 as const,
          participant_count: 64,
          top_placements: [
            { placement: 1, player_name: "Taro", archetype: "Charizard ex" },
            { placement: 2, player_name: "Jiro", archetype: "Lugia VSTAR" },
          ],
        },
      ],
      total: 1,
      page: 1,
      limit: 10,
      has_next: false,
      has_prev: false,
    });

    render(<CityLeagueResultsFeed />, { wrapper: createWrapper() });

    const name = await screen.findByText("City League Tokyo");
    expect(name).toBeInTheDocument();
    expect(screen.getByText("64")).toBeInTheDocument();
  });

  it("should pass date params to API", () => {
    mockTournamentsApi.list.mockReturnValue(new Promise(() => {}));

    render(
      <CityLeagueResultsFeed startDate="2024-01-01" endDate="2024-03-31" />,
      { wrapper: createWrapper() }
    );

    expect(mockTournamentsApi.list).toHaveBeenCalledWith(
      expect.objectContaining({
        region: "JP",
        best_of: 1,
        start_date: "2024-01-01",
        end_date: "2024-03-31",
      })
    );
  });
});
