import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NewArchetypeWatch } from "../NewArchetypeWatch";
import * as api from "@/lib/api";
import type { ApiJPNewArchetype } from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  japanApi: {
    listNewArchetypes: vi.fn(),
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

const mockArchetype: ApiJPNewArchetype = {
  id: "arch-1",
  archetype_id: "raging-bolt",
  name: "Raging Bolt ex",
  name_jp: "Takeru Ikazuchi",
  key_cards: ["Raging Bolt ex", "Ogerpon ex"],
  enabled_by_set: "SV6",
  jp_meta_share: 0.085,
  jp_trend: "rising",
  city_league_results: [
    {
      tournament: "City League Tokyo",
      date: "2024-03-10",
      placements: [1, 4, 7],
    },
  ],
  estimated_en_legal_date: "2024-09-01T00:00:00Z",
  analysis: "Strong against current meta. Expected to be Tier A in EN.",
};

describe("NewArchetypeWatch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render loading state initially", () => {
    mockJapanApi.listNewArchetypes.mockReturnValue(new Promise(() => {}));

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    expect(screen.getByText("New Archetype Watch (BO1)")).toBeInTheDocument();
  });

  it("should render title and description when data loads", async () => {
    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [],
      total: 0,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    // Wait for the description which only appears after data loads
    expect(
      await screen.findByText(
        "JP-exclusive archetypes not yet in the English meta"
      )
    ).toBeInTheDocument();
    expect(screen.getByText("New Archetype Watch (BO1)")).toBeInTheDocument();
  });

  it("should display empty state when no archetypes", async () => {
    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [],
      total: 0,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("No new archetypes tracked yet")
    ).toBeInTheDocument();
  });

  it("should render archetype name and JP name", async () => {
    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [mockArchetype],
      total: 1,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    // "Raging Bolt ex" appears as both name and a key card badge
    const matches = await screen.findAllByText("Raging Bolt ex");
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Takeru Ikazuchi")).toBeInTheDocument();
  });

  it("should display meta share percentage", async () => {
    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [mockArchetype],
      total: 1,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    expect(await screen.findByText("8.5%")).toBeInTheDocument();
  });

  it("should render key cards as badges", async () => {
    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [mockArchetype],
      total: 1,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    // "Raging Bolt ex" appears as both name and key card badge
    await screen.findAllByText("Raging Bolt ex");
    expect(screen.getByText("Key Cards")).toBeInTheDocument();
    expect(screen.getByText("Ogerpon ex")).toBeInTheDocument();
  });

  it("should display enabled by set", async () => {
    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [mockArchetype],
      total: 1,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    expect(await screen.findByText("Enabled by:")).toBeInTheDocument();
    expect(screen.getByText("SV6")).toBeInTheDocument();
  });

  it("should display city league top 8 placements", async () => {
    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [mockArchetype],
      total: 1,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    expect(await screen.findByText("Top 8s: 1, 4, 7")).toBeInTheDocument();
  });

  it("should display estimated EN legal date", async () => {
    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [mockArchetype],
      total: 1,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    // date-fns format uses local timezone, so "2024-09-01T00:00:00Z" may
    // render as Aug or Sep depending on the runner's timezone
    expect(
      await screen.findByText(/Est\. EN Legal: (Aug|Sep) 2024/)
    ).toBeInTheDocument();
  });

  it("should display analysis text", async () => {
    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [mockArchetype],
      total: 1,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    expect(
      await screen.findByText(
        "Strong against current meta. Expected to be Tier A in EN."
      )
    ).toBeInTheDocument();
  });

  it("should not render key cards section when key_cards is null", async () => {
    const noKeyCards: ApiJPNewArchetype = {
      ...mockArchetype,
      key_cards: null,
    };

    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [noKeyCards],
      total: 1,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    await screen.findByText("Raging Bolt ex");
    expect(screen.queryByText("Key Cards")).not.toBeInTheDocument();
  });

  it("should not render estimated date when null", async () => {
    const noDate: ApiJPNewArchetype = {
      ...mockArchetype,
      estimated_en_legal_date: null,
    };

    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [noDate],
      total: 1,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    await screen.findAllByText("Raging Bolt ex");
    expect(screen.queryByText(/Est\. EN Legal/)).not.toBeInTheDocument();
  });

  it("should not render analysis when null", async () => {
    const noAnalysis: ApiJPNewArchetype = {
      ...mockArchetype,
      analysis: null,
    };

    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [noAnalysis],
      total: 1,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    await screen.findAllByText("Raging Bolt ex");
    expect(
      screen.queryByText("Strong against current meta.")
    ).not.toBeInTheDocument();
  });

  it("should show error state when data fails to load", async () => {
    mockJapanApi.listNewArchetypes.mockRejectedValue(
      new Error("Network error")
    );

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Failed to load new archetypes")
    ).toBeInTheDocument();
  });

  it("should pass custom limit to API", () => {
    mockJapanApi.listNewArchetypes.mockReturnValue(new Promise(() => {}));

    render(<NewArchetypeWatch limit={3} />, { wrapper: createWrapper() });

    expect(mockJapanApi.listNewArchetypes).toHaveBeenCalledWith(
      expect.objectContaining({ limit: 3 })
    );
  });

  it("should render multiple archetype cards in a grid", async () => {
    const secondArchetype: ApiJPNewArchetype = {
      ...mockArchetype,
      id: "arch-2",
      archetype_id: "gouging-fire",
      name: "Gouging Fire ex",
      name_jp: null,
      jp_meta_share: 0.042,
    };

    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [mockArchetype, secondArchetype],
      total: 2,
    });

    render(<NewArchetypeWatch />, { wrapper: createWrapper() });

    // "Raging Bolt ex" appears multiple times (name + key card badge, and
    // secondArchetype also inherits key_cards with "Raging Bolt ex")
    const matches = await screen.findAllByText("Raging Bolt ex");
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Gouging Fire ex")).toBeInTheDocument();
  });

  it("should apply custom className", async () => {
    mockJapanApi.listNewArchetypes.mockResolvedValue({
      items: [],
      total: 0,
    });

    const { container } = render(
      <NewArchetypeWatch className="custom-class" />,
      { wrapper: createWrapper() }
    );

    await screen.findByText("New Archetype Watch (BO1)");
    const wrapper = container.querySelector(".custom-class");
    expect(wrapper).toBeInTheDocument();
  });
});
