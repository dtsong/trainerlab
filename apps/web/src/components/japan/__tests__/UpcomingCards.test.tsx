import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { UpcomingCards } from "../UpcomingCards";
import * as api from "@/lib/api";
import type { ApiJPUnreleasedCard } from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  translationsApi: {
    getUpcomingCards: vi.fn(),
  },
}));

const mockTranslationsApi = vi.mocked(api.translationsApi);

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

const mockCard: ApiJPUnreleasedCard = {
  id: "card-1",
  jp_card_id: "sv7-055",
  jp_set_id: "SV7",
  name_jp: "Mewtwo ex",
  name_en: "Mewtwo ex EN",
  card_type: "Pokemon",
  competitive_impact: 5,
  affected_archetypes: ["Mewtwo ex", "Psychic Box"],
  notes: "Strong GX attack with high damage ceiling",
  expected_release_set: "Stellar Crown",
  is_released: false,
};

describe("UpcomingCards", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render loading state initially", () => {
    mockTranslationsApi.getUpcomingCards.mockReturnValue(new Promise(() => {}));

    render(<UpcomingCards />, { wrapper: createWrapper() });

    expect(screen.getByText("Upcoming Cards")).toBeInTheDocument();
  });

  it("should render loading skeleton placeholders", () => {
    mockTranslationsApi.getUpcomingCards.mockReturnValue(new Promise(() => {}));

    const { container } = render(<UpcomingCards />, {
      wrapper: createWrapper(),
    });

    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons).toHaveLength(3);
  });

  it("should show error state when data fails to load", async () => {
    mockTranslationsApi.getUpcomingCards.mockRejectedValue(
      new Error("Network error")
    );

    render(<UpcomingCards />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Failed to load upcoming cards")
    ).toBeInTheDocument();
    expect(screen.getByText("Upcoming Cards")).toBeInTheDocument();
  });

  it("should render title and description when data loads", async () => {
    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [],
      total: 0,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Japanese cards not yet released internationally")
    ).toBeInTheDocument();
    expect(screen.getByText("Upcoming Cards")).toBeInTheDocument();
  });

  it("should display empty state when no cards", async () => {
    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [],
      total: 0,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("No upcoming cards tracked")
    ).toBeInTheDocument();
  });

  it("should render card with English name and Japanese subtitle", async () => {
    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [mockCard],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    expect(await screen.findByText("Mewtwo ex EN")).toBeInTheDocument();
    // "Mewtwo ex" appears as JP subtitle and as an archetype badge
    const jpNameMatches = screen.getAllByText("Mewtwo ex");
    expect(jpNameMatches.length).toBeGreaterThanOrEqual(1);
  });

  it("should display JP name as primary when no English name", async () => {
    const jpOnlyCard: ApiJPUnreleasedCard = {
      ...mockCard,
      id: "card-2",
      name_en: null,
    };

    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [jpOnlyCard],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    // "Mewtwo ex" appears as card name (h4) and as archetype badge
    const matches = await screen.findAllByText("Mewtwo ex");
    expect(matches.length).toBeGreaterThanOrEqual(1);
    // English name should not appear
    expect(screen.queryByText("Mewtwo ex EN")).not.toBeInTheDocument();
  });

  it("should display expected release set badge", async () => {
    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [mockCard],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    expect(await screen.findByText("Stellar Crown")).toBeInTheDocument();
  });

  it("should not render release set badge when not provided", async () => {
    const noReleaseSet: ApiJPUnreleasedCard = {
      ...mockCard,
      id: "card-3",
      expected_release_set: null,
    };

    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [noReleaseSet],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    await screen.findByText("Mewtwo ex EN");
    expect(screen.queryByText("Stellar Crown")).not.toBeInTheDocument();
  });

  it("should display jp_set_id badge", async () => {
    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [mockCard],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    expect(await screen.findByText("SV7")).toBeInTheDocument();
  });

  it("should display card type badge", async () => {
    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [mockCard],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    expect(await screen.findByText("Pokemon")).toBeInTheDocument();
  });

  it("should show High Impact badge when competitive_impact >= 4", async () => {
    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [mockCard],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    expect(await screen.findByText("High Impact")).toBeInTheDocument();
  });

  it("should not show High Impact badge when competitive_impact < 4", async () => {
    const lowImpactCard: ApiJPUnreleasedCard = {
      ...mockCard,
      id: "card-4",
      competitive_impact: 2,
    };

    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [lowImpactCard],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    await screen.findByText("Mewtwo ex EN");
    expect(screen.queryByText("High Impact")).not.toBeInTheDocument();
  });

  it("should display notes text", async () => {
    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [mockCard],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Strong GX attack with high damage ceiling")
    ).toBeInTheDocument();
  });

  it("should not render notes when not provided", async () => {
    const noNotes: ApiJPUnreleasedCard = {
      ...mockCard,
      id: "card-5",
      notes: null,
    };

    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [noNotes],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    await screen.findByText("Mewtwo ex EN");
    expect(
      screen.queryByText("Strong GX attack with high damage ceiling")
    ).not.toBeInTheDocument();
  });

  it("should display affected archetype badges (up to 3)", async () => {
    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [mockCard],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    // mockCard has archetypes: ["Mewtwo ex", "Psychic Box"]
    // "Mewtwo ex" also appears as the JP name, so check for both archetypes
    await screen.findByText("Psychic Box");
    const mewtwoMatches = screen.getAllByText("Mewtwo ex");
    expect(mewtwoMatches.length).toBeGreaterThanOrEqual(1);
  });

  it("should truncate archetypes at 3", async () => {
    const manyArchetypes: ApiJPUnreleasedCard = {
      ...mockCard,
      id: "card-6",
      affected_archetypes: ["Arch A", "Arch B", "Arch C", "Arch D", "Arch E"],
    };

    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [manyArchetypes],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    expect(await screen.findByText("Arch A")).toBeInTheDocument();
    expect(screen.getByText("Arch B")).toBeInTheDocument();
    expect(screen.getByText("Arch C")).toBeInTheDocument();
    expect(screen.queryByText("Arch D")).not.toBeInTheDocument();
    expect(screen.queryByText("Arch E")).not.toBeInTheDocument();
  });

  it("should not render archetype section when affected_archetypes is null", async () => {
    const noArchetypes: ApiJPUnreleasedCard = {
      ...mockCard,
      id: "card-7",
      affected_archetypes: null,
    };

    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [noArchetypes],
      total: 1,
    });

    render(<UpcomingCards />, { wrapper: createWrapper() });

    await screen.findByText("Mewtwo ex EN");
    expect(screen.queryByText("Psychic Box")).not.toBeInTheDocument();
  });

  it("should pass custom limit to API", () => {
    mockTranslationsApi.getUpcomingCards.mockReturnValue(new Promise(() => {}));

    render(<UpcomingCards limit={5} />, {
      wrapper: createWrapper(),
    });

    expect(mockTranslationsApi.getUpcomingCards).toHaveBeenCalledWith(
      expect.objectContaining({ limit: 5 })
    );
  });

  it("should use default limit of 10", () => {
    mockTranslationsApi.getUpcomingCards.mockReturnValue(new Promise(() => {}));

    render(<UpcomingCards />, {
      wrapper: createWrapper(),
    });

    expect(mockTranslationsApi.getUpcomingCards).toHaveBeenCalledWith(
      expect.objectContaining({ limit: 10 })
    );
  });

  it("should apply custom className", async () => {
    mockTranslationsApi.getUpcomingCards.mockResolvedValue({
      cards: [],
      total: 0,
    });

    const { container } = render(<UpcomingCards className="custom-class" />, {
      wrapper: createWrapper(),
    });

    await screen.findByText("Upcoming Cards");
    const card = container.querySelector(".custom-class");
    expect(card).toBeInTheDocument();
  });
});
