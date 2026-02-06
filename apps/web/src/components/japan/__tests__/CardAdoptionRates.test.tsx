import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CardAdoptionRates } from "../CardAdoptionRates";
import * as api from "@/lib/api";
import type { ApiJPAdoptionRate } from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  translationsApi: {
    getAdoptionRates: vi.fn(),
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

const mockRate: ApiJPAdoptionRate = {
  id: "rate-1",
  card_id: "sv6-101",
  card_name_jp: "Pikachu ex JP",
  card_name_en: "Pikachu ex",
  inclusion_rate: 0.75,
  avg_copies: 2.3,
  archetype_context: "Lightning Box",
  period_start: "2024-01-01",
  period_end: "2024-01-31",
  source: "city-league",
};

describe("CardAdoptionRates", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render loading state initially", () => {
    mockTranslationsApi.getAdoptionRates.mockReturnValue(new Promise(() => {}));

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(screen.getByText("Card Adoption Rates (BO1)")).toBeInTheDocument();
  });

  it("should render skeleton placeholders while loading", () => {
    mockTranslationsApi.getAdoptionRates.mockReturnValue(new Promise(() => {}));

    const { container } = render(<CardAdoptionRates />, {
      wrapper: createWrapper(),
    });

    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons).toHaveLength(5);
  });

  it("should render title and description when data loads", async () => {
    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [],
      total: 0,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Most-used cards in JP meta (last 30 days)")
    ).toBeInTheDocument();
    expect(screen.getByText("Card Adoption Rates (BO1)")).toBeInTheDocument();
  });

  it("should display empty state when no rates", async () => {
    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [],
      total: 0,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("No adoption rate data available")
    ).toBeInTheDocument();
  });

  it("should render table headers when data exists", async () => {
    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [mockRate],
      total: 1,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(await screen.findByText("Card")).toBeInTheDocument();
    expect(screen.getByText("Inclusion Rate")).toBeInTheDocument();
    expect(screen.getByText("Avg Copies")).toBeInTheDocument();
    expect(screen.getByText("Archetype")).toBeInTheDocument();
    expect(screen.getByText("Period")).toBeInTheDocument();
  });

  it("should render card name with JP name subtitle", async () => {
    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [mockRate],
      total: 1,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(await screen.findByText("Pikachu ex")).toBeInTheDocument();
    expect(screen.getByText("Pikachu ex JP")).toBeInTheDocument();
  });

  it("should display inclusion rate as percentage bar", async () => {
    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [mockRate],
      total: 1,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(await screen.findByText("75%")).toBeInTheDocument();
  });

  it("should display average copies", async () => {
    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [mockRate],
      total: 1,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(await screen.findByText("2.3")).toBeInTheDocument();
  });

  it("should display dash when avg_copies is null", async () => {
    const noCopiesRate: ApiJPAdoptionRate = {
      ...mockRate,
      id: "rate-2",
      avg_copies: null,
    };

    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [noCopiesRate],
      total: 1,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(await screen.findByText("-")).toBeInTheDocument();
  });

  it("should display archetype badge when archetype_context exists", async () => {
    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [mockRate],
      total: 1,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(await screen.findByText("Lightning Box")).toBeInTheDocument();
  });

  it("should display 'All' when archetype_context is null", async () => {
    const noArchetypeRate: ApiJPAdoptionRate = {
      ...mockRate,
      id: "rate-3",
      archetype_context: null,
    };

    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [noArchetypeRate],
      total: 1,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(await screen.findByText("All")).toBeInTheDocument();
  });

  it("should display period dates", async () => {
    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [mockRate],
      total: 1,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("2024-01-01 - 2024-01-31")
    ).toBeInTheDocument();
  });

  it("should show error state when data fails to load", async () => {
    mockTranslationsApi.getAdoptionRates.mockRejectedValue(
      new Error("Network error")
    );

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Failed to load adoption rates")
    ).toBeInTheDocument();
  });

  it("should handle card with only JP name (no EN name)", async () => {
    const jpOnlyRate: ApiJPAdoptionRate = {
      ...mockRate,
      id: "rate-4",
      card_name_en: null,
      card_name_jp: "Pikachu ex JP",
    };

    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [jpOnlyRate],
      total: 1,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(await screen.findByText("Pikachu ex JP")).toBeInTheDocument();
  });

  it("should fall back to card_id when both names are null", async () => {
    const noNameRate: ApiJPAdoptionRate = {
      ...mockRate,
      id: "rate-5",
      card_name_en: null,
      card_name_jp: null,
    };

    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [noNameRate],
      total: 1,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(await screen.findByText("sv6-101")).toBeInTheDocument();
  });

  it("should not show JP subtitle when EN name is missing", async () => {
    const noEnRate: ApiJPAdoptionRate = {
      ...mockRate,
      id: "rate-6",
      card_name_en: null,
    };

    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [noEnRate],
      total: 1,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    // JP name is shown as the primary name, not as a subtitle
    const jpTexts = await screen.findAllByText("Pikachu ex JP");
    expect(jpTexts).toHaveLength(1);
  });

  it("should pass custom days to API and display in description", async () => {
    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [],
      total: 0,
    });

    render(<CardAdoptionRates days={14} />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Most-used cards in JP meta (last 14 days)")
    ).toBeInTheDocument();
  });

  it("should apply custom className", async () => {
    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [],
      total: 0,
    });

    const { container } = render(
      <CardAdoptionRates className="custom-class" />,
      { wrapper: createWrapper() }
    );

    await screen.findByText("Card Adoption Rates (BO1)");
    const card = container.querySelector(".custom-class");
    expect(card).toBeInTheDocument();
  });

  it("should render multiple rates", async () => {
    const secondRate: ApiJPAdoptionRate = {
      id: "rate-7",
      card_id: "sv6-102",
      card_name_jp: "Charizard ex JP",
      card_name_en: "Charizard ex",
      inclusion_rate: 0.42,
      avg_copies: 1.8,
      archetype_context: "Fire Box",
      period_start: "2024-01-01",
      period_end: "2024-01-31",
      source: "city-league",
    };

    mockTranslationsApi.getAdoptionRates.mockResolvedValue({
      rates: [mockRate, secondRate],
      total: 2,
    });

    render(<CardAdoptionRates />, { wrapper: createWrapper() });

    expect(await screen.findByText("Pikachu ex")).toBeInTheDocument();
    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("42%")).toBeInTheDocument();
  });
});
