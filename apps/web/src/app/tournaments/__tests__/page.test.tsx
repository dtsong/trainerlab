import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import TournamentsPage from "../page";

const mockPush = vi.fn();
const mockReplace = vi.fn();
let mockSearchParams = new URLSearchParams();
const mockTournamentList = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useSearchParams: () => mockSearchParams,
}));

vi.mock("@/components/ui/tabs", () => ({
  Tabs: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TabsList: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  TabsTrigger: ({ children }: { children: React.ReactNode }) => (
    <button>{children}</button>
  ),
  TabsContent: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

vi.mock("@/components/meta", () => ({
  BO1ContextBanner: () => <div>BO1 Context</div>,
}));

vi.mock("@/components/tournaments", () => ({
  TournamentFilters: () => <div>Filters</div>,
  TournamentList: (props: Record<string, unknown>) => {
    mockTournamentList(props);
    return <div>Tournament List</div>;
  },
}));

describe("TournamentsPage filters", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams("major_format=svi-asc&season=2026");
  });

  it("hydrates TPCI query params into list API filters", () => {
    render(<TournamentsPage />);

    expect(mockTournamentList).toHaveBeenCalledWith(
      expect.objectContaining({
        apiParams: expect.objectContaining({
          tier: "major",
          major_format_key: "svi-asc",
          season: 2026,
          official_only: true,
        }),
        showMajorFormatBadge: true,
      })
    );
  });
});
