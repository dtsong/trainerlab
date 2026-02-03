import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MetaDivergenceComparison } from "../MetaDivergenceComparison";
import * as api from "@/lib/api";

vi.mock("@/lib/api", () => ({
  metaApi: {
    getCurrent: vi.fn(),
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

describe("MetaDivergenceComparison", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render loading state initially", () => {
    mockMetaApi.getCurrent.mockReturnValue(new Promise(() => {}));

    render(<MetaDivergenceComparison />, { wrapper: createWrapper() });
    expect(screen.getByText("JP vs International Meta")).toBeInTheDocument();
  });

  it("should render both columns when data loads", async () => {
    const jpMeta = {
      snapshot_date: "2024-03-10",
      region: "JP",
      format: "standard" as const,
      best_of: 1 as const,
      archetype_breakdown: [
        { name: "Charizard ex", share: 0.15 },
        { name: "Lugia VSTAR", share: 0.12 },
        { name: "JP Exclusive", share: 0.08 },
      ],
      card_usage: [],
      sample_size: 100,
    };

    const globalMeta = {
      snapshot_date: "2024-03-10",
      region: null,
      format: "standard" as const,
      best_of: 3 as const,
      archetype_breakdown: [
        { name: "Charizard ex", share: 0.18 },
        { name: "Lugia VSTAR", share: 0.1 },
        { name: "EN Exclusive", share: 0.09 },
      ],
      card_usage: [],
      sample_size: 200,
    };

    mockMetaApi.getCurrent
      .mockResolvedValueOnce(jpMeta)
      .mockResolvedValueOnce(globalMeta);

    render(<MetaDivergenceComparison />, { wrapper: createWrapper() });

    const jpCol = await screen.findByText("Japan (BO1)");
    expect(jpCol).toBeInTheDocument();
    expect(screen.getByText("International (BO3)")).toBeInTheDocument();
  });

  it("should show JP Only badge for JP-exclusive archetypes", async () => {
    mockMetaApi.getCurrent
      .mockResolvedValueOnce({
        snapshot_date: "2024-03-10",
        region: "JP",
        format: "standard" as const,
        best_of: 1 as const,
        archetype_breakdown: [{ name: "JP Exclusive", share: 0.1 }],
        card_usage: [],
        sample_size: 50,
      })
      .mockResolvedValueOnce({
        snapshot_date: "2024-03-10",
        region: null,
        format: "standard" as const,
        best_of: 3 as const,
        archetype_breakdown: [{ name: "EN Only Deck", share: 0.1 }],
        card_usage: [],
        sample_size: 100,
      });

    render(<MetaDivergenceComparison />, { wrapper: createWrapper() });

    const jpOnly = await screen.findByText("JP Only");
    expect(jpOnly).toBeInTheDocument();
    expect(screen.getByText("EN Only")).toBeInTheDocument();
  });

  it("should render with custom className", () => {
    mockMetaApi.getCurrent.mockReturnValue(new Promise(() => {}));

    render(<MetaDivergenceComparison className="custom-class" />, {
      wrapper: createWrapper(),
    });
    expect(screen.getByText("JP vs International Meta")).toBeInTheDocument();
  });
});
