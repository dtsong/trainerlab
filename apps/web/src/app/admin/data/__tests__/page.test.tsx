import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/admin/data",
}));

// Mock auth
vi.mock("@/hooks", () => ({
  useAuth: vi.fn(() => ({
    user: { email: "admin@trainerlab.gg" },
    loading: false,
    signOut: vi.fn(),
  })),
}));

// Mock admin check
vi.mock("@/lib/admin", () => ({
  isAdminEmail: vi.fn(() => true),
}));

// Mock API
const mockGetOverview = vi.fn();
const mockListMetaSnapshots = vi.fn();
const mockGetMetaSnapshotDetail = vi.fn();
const mockGetPipelineHealth = vi.fn();

vi.mock("@/lib/api", () => ({
  adminDataApi: {
    getOverview: (...args: unknown[]) => mockGetOverview(...args),
    listMetaSnapshots: (...args: unknown[]) => mockListMetaSnapshots(...args),
    getMetaSnapshotDetail: (...args: unknown[]) =>
      mockGetMetaSnapshotDetail(...args),
    getPipelineHealth: (...args: unknown[]) => mockGetPipelineHealth(...args),
  },
}));

import AdminDataPage from "../page";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe("AdminDataPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders overview tab with table data", async () => {
    mockGetOverview.mockResolvedValue({
      tables: [
        {
          name: "tournaments",
          row_count: 100,
          latest_date: "2024-01-15",
          detail: null,
        },
        {
          name: "cards",
          row_count: 5000,
          latest_date: null,
          detail: null,
        },
      ],
      generated_at: "2024-01-15T12:00:00Z",
    });
    mockListMetaSnapshots.mockResolvedValue({ items: [], total: 0 });
    mockGetPipelineHealth.mockResolvedValue({
      pipelines: [],
      checked_at: "2024-01-15T12:00:00Z",
    });

    render(<AdminDataPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("tournaments")).toBeInTheDocument();
    });
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("5,000")).toBeInTheDocument();
  });

  it("renders loading state", () => {
    mockGetOverview.mockReturnValue(new Promise(() => {}));
    mockListMetaSnapshots.mockReturnValue(new Promise(() => {}));
    mockGetPipelineHealth.mockReturnValue(new Promise(() => {}));

    render(<AdminDataPage />, { wrapper: createWrapper() });

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders pipeline health tab", async () => {
    mockGetOverview.mockResolvedValue({
      tables: [],
      generated_at: "",
    });
    mockListMetaSnapshots.mockResolvedValue({ items: [], total: 0 });
    mockGetPipelineHealth.mockResolvedValue({
      pipelines: [
        {
          name: "Meta Compute",
          status: "healthy",
          last_run: "2024-01-15",
          days_since_run: 0,
        },
        {
          name: "JP Scrape",
          status: "stale",
          last_run: "2024-01-08",
          days_since_run: 7,
        },
        {
          name: "Card Sync",
          status: "critical",
          last_run: null,
          days_since_run: null,
        },
      ],
      checked_at: "2024-01-15T12:00:00Z",
    });

    const user = userEvent.setup();
    render(<AdminDataPage />, { wrapper: createWrapper() });

    const pipelineTab = screen.getByRole("tab", {
      name: /pipeline health/i,
    });
    await user.click(pipelineTab);

    await waitFor(() => {
      expect(screen.getByText("Meta Compute")).toBeInTheDocument();
    });
    expect(screen.getByText("healthy")).toBeInTheDocument();
    expect(screen.getByText("stale")).toBeInTheDocument();
    expect(screen.getByText("critical")).toBeInTheDocument();
  });

  it("renders meta inspector tab", async () => {
    mockGetOverview.mockResolvedValue({
      tables: [],
      generated_at: "",
    });
    mockListMetaSnapshots.mockResolvedValue({
      items: [
        {
          id: "test-id-1",
          snapshot_date: "2024-01-15",
          region: null,
          format: "standard",
          best_of: 3,
          sample_size: 100,
          archetype_count: 12,
          diversity_index: 0.77,
        },
      ],
      total: 1,
    });
    mockGetPipelineHealth.mockResolvedValue({
      pipelines: [],
      checked_at: "",
    });

    const user = userEvent.setup();
    render(<AdminDataPage />, { wrapper: createWrapper() });

    const metaTab = screen.getByRole("tab", {
      name: /meta inspector/i,
    });
    await user.click(metaTab);

    await waitFor(() => {
      expect(screen.getByText("2024-01-15")).toBeInTheDocument();
    });
  });

  it("shows page title", () => {
    mockGetOverview.mockReturnValue(new Promise(() => {}));
    mockListMetaSnapshots.mockReturnValue(new Promise(() => {}));
    mockGetPipelineHealth.mockReturnValue(new Promise(() => {}));

    render(<AdminDataPage />, { wrapper: createWrapper() });

    expect(screen.getByText("Data")).toBeInTheDocument();
  });
});
