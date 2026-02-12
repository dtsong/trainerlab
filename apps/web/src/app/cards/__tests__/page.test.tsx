import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import CardsPage from "../page";

const mockPush = vi.fn();
const mockReplace = vi.fn();
let mockSearchParams = new URLSearchParams();

const mockUseCards = vi.fn();
const mockUseSets = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useSearchParams: () => mockSearchParams,
}));

vi.mock("@/hooks/useCards", () => ({
  useCards: (...args: unknown[]) => mockUseCards(...args),
}));

vi.mock("@/hooks/useSets", () => ({
  useSets: () => mockUseSets(),
}));

vi.mock("@/components/cards", () => ({
  DEFAULT_FILTERS: {
    supertype: "all",
    types: "all",
    set_id: "all",
    standard_legal: "all",
  },
  CardGrid: ({ cards }: { cards: Array<{ id: string }> }) => (
    <div data-testid="card-grid">{cards.length}</div>
  ),
  CardGridSkeleton: () => <div data-testid="card-grid-skeleton" />,
  CardFiltersSkeleton: () => <div data-testid="card-filters-skeleton" />,
  CardSearchInput: ({
    value,
    onChange,
  }: {
    value: string;
    onChange: (value: string) => void;
  }) => (
    <input
      aria-label="Search cards"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
  CardFilters: ({
    onChange,
  }: {
    onChange: (key: string, value: string) => void;
  }) => (
    <button onClick={() => onChange("supertype", "Trainer")}>
      Set supertype
    </button>
  ),
  MobileCardFilters: () => <div data-testid="mobile-filters" />,
}));

describe("CardsPage URL behavior", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams();

    mockUseSets.mockReturnValue({
      data: [{ id: "sv1", name: "Scarlet & Violet" }],
      isLoading: false,
    });

    mockUseCards.mockReturnValue({
      data: {
        items: [{ id: "1" }],
        total: 40,
        page: 1,
        total_pages: 2,
      },
      isLoading: false,
      isError: false,
      error: null,
    });
  });

  it("hydrates search and filters from URL params", () => {
    mockSearchParams = new URLSearchParams(
      "q=pikachu&page=3&supertype=Trainer&types=Fire&set_id=sv1&standard_legal=expanded"
    );

    render(<CardsPage />);

    expect(mockUseCards).toHaveBeenCalledWith(
      expect.objectContaining({
        q: "pikachu",
        page: 3,
        supertype: "Trainer",
        types: "Fire",
        set_id: "sv1",
        expanded: true,
        standard: undefined,
      })
    );
  });

  it("uses replace for search changes and resets page", () => {
    mockSearchParams = new URLSearchParams("page=2");

    render(<CardsPage />);

    fireEvent.change(screen.getByLabelText("Search cards"), {
      target: { value: "charizard" },
    });

    expect(mockReplace).toHaveBeenCalledWith("/cards?q=charizard", {
      scroll: false,
    });
  });

  it("uses push for pagination changes", () => {
    render(<CardsPage />);

    fireEvent.click(screen.getByText("Next"));

    expect(mockPush).toHaveBeenCalledWith("/cards?page=2", { scroll: false });
  });
});
