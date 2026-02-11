import React from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";

vi.mock("next/link", () => ({
  __esModule: true,
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("@/hooks", () => ({
  useWidgets: vi.fn(),
  useExports: vi.fn(),
  useApiKeys: vi.fn(),
  useCreateExport: vi.fn(),
  useCreateApiKey: vi.fn(),
  useFormatForecast: vi.fn(),
}));

import {
  useApiKeys,
  useCreateApiKey,
  useCreateExport,
  useExports,
  useFormatForecast,
  useWidgets,
} from "@/hooks";
import { CreatorDashboard } from "../CreatorDashboard";

function renderWithClient(node: React.ReactNode) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={client}>{node}</QueryClientProvider>
  );
}

describe("CreatorDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useWidgets).mockReturnValue({
      data: {
        items: [],
        total: 0,
        page: 1,
        limit: 24,
        has_next: false,
        has_prev: false,
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWidgets>);

    vi.mocked(useExports).mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
    } as unknown as ReturnType<typeof useExports>);

    vi.mocked(useApiKeys).mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
    } as unknown as ReturnType<typeof useApiKeys>);

    vi.mocked(useFormatForecast).mockReturnValue({
      data: { forecast_archetypes: [], generated_at: "", lookback_days: 7 },
      isLoading: false,
    } as unknown as ReturnType<typeof useFormatForecast>);

    vi.mocked(useCreateExport).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateExport>);

    vi.mocked(useCreateApiKey).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateApiKey>);
  });

  it("renders all required dashboard sections", () => {
    renderWithClient(<CreatorDashboard />);

    expect(screen.getByText("Your Widgets")).toBeInTheDocument();
    expect(screen.getByText("Quick Exports")).toBeInTheDocument();
    expect(screen.getByText("Trending Data")).toBeInTheDocument();
    expect(screen.getByText("API Access")).toBeInTheDocument();
  });
});
