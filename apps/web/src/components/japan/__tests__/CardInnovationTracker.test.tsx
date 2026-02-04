import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CardInnovationTracker } from "../CardInnovationTracker";
import * as api from "@/lib/api";
import type { ApiJPCardInnovation } from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  japanApi: {
    listInnovations: vi.fn(),
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

const mockCard: ApiJPCardInnovation = {
  id: "card-1",
  card_id: "sv6-42",
  card_name: "Dragapult ex",
  card_name_jp: "Drapa ex JP",
  set_code: "SV6",
  is_legal_en: false,
  adoption_rate: 0.352,
  adoption_trend: "rising",
  archetypes_using: ["Dragapult ex", "Charizard ex"],
  competitive_impact_rating: 4,
  sample_size: 120,
};

describe("CardInnovationTracker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render loading state initially", () => {
    mockJapanApi.listInnovations.mockReturnValue(new Promise(() => {}));

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    expect(screen.getByText("Card Innovation Tracker")).toBeInTheDocument();
  });

  it("should render title and description when data loads", async () => {
    mockJapanApi.listInnovations.mockResolvedValue({
      items: [],
      total: 0,
    });

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    // Wait for the description which only appears after data loads
    expect(
      await screen.findByText(
        "New cards seeing competitive play in Japan City Leagues"
      )
    ).toBeInTheDocument();
    expect(screen.getByText("Card Innovation Tracker")).toBeInTheDocument();
  });

  it("should display empty state when no cards", async () => {
    mockJapanApi.listInnovations.mockResolvedValue({
      items: [],
      total: 0,
    });

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("No card innovations tracked yet")
    ).toBeInTheDocument();
  });

  it("should render table headers", async () => {
    mockJapanApi.listInnovations.mockResolvedValue({
      items: [mockCard],
      total: 1,
    });

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    expect(await screen.findByText("Card")).toBeInTheDocument();
    expect(screen.getByText("Set")).toBeInTheDocument();
    expect(screen.getByText("Adoption")).toBeInTheDocument();
    expect(screen.getByText("Impact")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Archetypes")).toBeInTheDocument();
  });

  it("should render card name and JP name", async () => {
    mockJapanApi.listInnovations.mockResolvedValue({
      items: [mockCard],
      total: 1,
    });

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    // "Dragapult ex" appears both as card name and as an archetype badge
    const matches = await screen.findAllByText("Dragapult ex");
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Drapa ex JP")).toBeInTheDocument();
  });

  it("should display adoption rate as percentage", async () => {
    mockJapanApi.listInnovations.mockResolvedValue({
      items: [mockCard],
      total: 1,
    });

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    expect(await screen.findByText("35.2%")).toBeInTheDocument();
  });

  it("should display set code badge", async () => {
    mockJapanApi.listInnovations.mockResolvedValue({
      items: [mockCard],
      total: 1,
    });

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    expect(await screen.findByText("SV6")).toBeInTheDocument();
  });

  it("should show 'JP Only' badge when card is not legal in EN", async () => {
    mockJapanApi.listInnovations.mockResolvedValue({
      items: [mockCard],
      total: 1,
    });

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    expect(await screen.findByText("JP Only")).toBeInTheDocument();
  });

  it("should show 'Legal' badge when card is legal in EN", async () => {
    const legalCard: ApiJPCardInnovation = {
      ...mockCard,
      id: "card-2",
      is_legal_en: true,
    };

    mockJapanApi.listInnovations.mockResolvedValue({
      items: [legalCard],
      total: 1,
    });

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    expect(await screen.findByText("Legal")).toBeInTheDocument();
  });

  it("should display archetype badges", async () => {
    mockJapanApi.listInnovations.mockResolvedValue({
      items: [mockCard],
      total: 1,
    });

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    // "Dragapult ex" appears as both card name and archetype badge
    const matches = await screen.findAllByText("Dragapult ex");
    expect(matches.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
  });

  it("should truncate archetypes at 3 and show overflow count", async () => {
    const manyArchetypes: ApiJPCardInnovation = {
      ...mockCard,
      archetypes_using: ["Arch A", "Arch B", "Arch C", "Arch D", "Arch E"],
    };

    mockJapanApi.listInnovations.mockResolvedValue({
      items: [manyArchetypes],
      total: 1,
    });

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    expect(await screen.findByText("Arch A")).toBeInTheDocument();
    expect(screen.getByText("Arch B")).toBeInTheDocument();
    expect(screen.getByText("Arch C")).toBeInTheDocument();
    expect(screen.queryByText("Arch D")).not.toBeInTheDocument();
    expect(screen.getByText("+2")).toBeInTheDocument();
  });

  it("should show error state when data fails to load", async () => {
    mockJapanApi.listInnovations.mockRejectedValue(new Error("Network error"));

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Failed to load card innovations")
    ).toBeInTheDocument();
  });

  it("should pass showJpOnly filter to API", () => {
    mockJapanApi.listInnovations.mockReturnValue(new Promise(() => {}));

    render(<CardInnovationTracker showJpOnly />, {
      wrapper: createWrapper(),
    });

    expect(mockJapanApi.listInnovations).toHaveBeenCalledWith(
      expect.objectContaining({ en_legal: false })
    );
  });

  it("should pass custom limit to API", () => {
    mockJapanApi.listInnovations.mockReturnValue(new Promise(() => {}));

    render(<CardInnovationTracker limit={5} />, {
      wrapper: createWrapper(),
    });

    expect(mockJapanApi.listInnovations).toHaveBeenCalledWith(
      expect.objectContaining({ limit: 5 })
    );
  });

  it("should apply custom className", async () => {
    mockJapanApi.listInnovations.mockResolvedValue({
      items: [],
      total: 0,
    });

    const { container } = render(
      <CardInnovationTracker className="custom-class" />,
      { wrapper: createWrapper() }
    );

    await screen.findByText("Card Innovation Tracker");
    const card = container.querySelector(".custom-class");
    expect(card).toBeInTheDocument();
  });

  it("should handle card without JP name", async () => {
    const noJpName: ApiJPCardInnovation = {
      ...mockCard,
      card_name_jp: null,
    };

    mockJapanApi.listInnovations.mockResolvedValue({
      items: [noJpName],
      total: 1,
    });

    render(<CardInnovationTracker />, { wrapper: createWrapper() });

    // "Dragapult ex" appears as both card name and archetype badge
    const matches = await screen.findAllByText("Dragapult ex");
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("Drapa ex JP")).not.toBeInTheDocument();
  });
});
