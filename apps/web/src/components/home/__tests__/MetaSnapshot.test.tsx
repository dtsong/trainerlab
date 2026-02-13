import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MetaSnapshot } from "../MetaSnapshot";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

// Mock sub-components
vi.mock("@/components/ui/trend-arrow", () => ({
  TrendArrow: ({ direction, value }: { direction: string; value?: number }) => (
    <span data-testid="trend-arrow">
      {direction} {value}
    </span>
  ),
}));

vi.mock("@/components/ui/jp-signal-badge", () => ({
  JPSignalBadge: () => <span data-testid="jp-signal-badge" />,
}));

vi.mock("@/components/ui/section-label", () => ({
  SectionLabel: ({ label }: { label: string }) => <span>{label}</span>,
}));

vi.mock("../skeletons", () => ({
  SpecimenCardSkeleton: () => <div data-testid="specimen-skeleton" />,
}));

vi.mock("@/components/meta", () => ({
  ArchetypeSprites: ({
    spriteUrls,
    archetypeName,
  }: {
    spriteUrls: string[];
    archetypeName: string;
  }) => (
    <span data-testid="archetype-sprites" data-name={archetypeName}>
      {spriteUrls.length} sprites
    </span>
  ),
}));

// Mock hooks
const mockUseHomeMetaData = vi.fn();

vi.mock("@/hooks/useMeta", () => ({
  useHomeMetaData: () => mockUseHomeMetaData(),
}));

// Mock home-utils
vi.mock("@/lib/home-utils", () => ({
  computeTrends: vi.fn(
    (
      globalMeta:
        | {
            archetype_breakdown?: {
              name: string;
              share: number;
              sprite_urls?: string[] | null;
            }[];
          }
        | undefined,
      _history: unknown,
      _jpMeta: unknown,
      limit: number = 5
    ) => {
      if (!globalMeta?.archetype_breakdown?.length) return [];
      return globalMeta.archetype_breakdown.slice(0, limit).map(
        (
          arch: {
            name: string;
            share: number;
            sprite_urls?: string[] | null;
          },
          i: number
        ) => ({
          rank: i + 1,
          name: arch.name,
          metaShare: arch.share * 100,
          trend: "stable" as const,
          trendValue: undefined,
          jpSignal: undefined,
          spriteUrls: arch.sprite_urls ?? undefined,
        })
      );
    }
  ),
}));

describe("MetaSnapshot", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render the section label", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      jpMeta: undefined,
      history: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<MetaSnapshot />);

    expect(screen.getByText("Meta Snapshot")).toBeInTheDocument();
  });

  it("should render 'View Full Meta' link to /meta", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      jpMeta: undefined,
      history: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<MetaSnapshot />);

    const link = screen.getByRole("link", { name: /View Full Meta/i });
    expect(link).toHaveAttribute("href", "/meta");
  });

  it("should show skeleton cards while loading", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      jpMeta: undefined,
      history: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    });

    render(<MetaSnapshot />);

    const skeletons = screen.getAllByTestId("specimen-skeleton");
    expect(skeletons).toHaveLength(5);
  });

  it("should show error state with retry button when isError", () => {
    const mockRefetch = vi.fn();
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      jpMeta: undefined,
      history: undefined,
      isLoading: false,
      isError: true,
      refetch: mockRefetch,
    });

    render(<MetaSnapshot />);

    expect(
      screen.getByText(/could not load meta snapshot/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Retry/i })).toBeInTheDocument();
  });

  it("should call refetch when retry button is clicked", async () => {
    const user = userEvent.setup();
    const mockRefetch = vi.fn();
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      jpMeta: undefined,
      history: undefined,
      isLoading: false,
      isError: true,
      refetch: mockRefetch,
    });

    render(<MetaSnapshot />);

    await user.click(screen.getByRole("button", { name: /Retry/i }));
    expect(mockRefetch).toHaveBeenCalled();
  });

  it("should render archetype specimen cards when data is available", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [
          { name: "Charizard ex", share: 0.15 },
          { name: "Lugia VSTAR", share: 0.12 },
          { name: "Gardevoir ex", share: 0.1 },
        ],
        sample_size: 5000,
      },
      jpMeta: undefined,
      history: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<MetaSnapshot />);

    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    expect(screen.getByText("Lugia VSTAR")).toBeInTheDocument();
    expect(screen.getByText("Gardevoir ex")).toBeInTheDocument();
  });

  it("should render meta share percentages for archetypes", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.153 }],
        sample_size: 5000,
      },
      jpMeta: undefined,
      history: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<MetaSnapshot />);

    expect(screen.getByText("15.3%")).toBeInTheDocument();
  });

  it("should render 'Build It' links for each archetype", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
        sample_size: 5000,
      },
      jpMeta: undefined,
      history: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<MetaSnapshot />);

    const buildLink = screen.getByRole("link", { name: /Build It/i });
    expect(buildLink).toHaveAttribute(
      "href",
      "/decks/new?archetype=Charizard%20ex"
    );
  });

  it("should show sample size annotation when data is available", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
        sample_size: 5000,
      },
      jpMeta: undefined,
      history: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<MetaSnapshot />);

    expect(screen.getByText("5000")).toBeInTheDocument();
    expect(screen.getByText(/decklists analyzed/i)).toBeInTheDocument();
  });

  it("should render annotation about update frequency", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      jpMeta: undefined,
      history: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<MetaSnapshot />);

    expect(
      screen.getByText(/Current tournament meta analysis/)
    ).toBeInTheDocument();
  });

  it("should render sprites when spriteUrls are available", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [
          {
            name: "Charizard ex",
            share: 0.15,
            sprite_urls: ["https://sprites.example.com/charizard.png"],
          },
        ],
        sample_size: 5000,
      },
      jpMeta: undefined,
      history: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<MetaSnapshot />);

    expect(screen.getByTestId("archetype-sprites")).toBeInTheDocument();
  });

  it("should show gray placeholder when no sprites available", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Rogue Deck", share: 0.05 }],
        sample_size: 100,
      },
      jpMeta: undefined,
      history: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<MetaSnapshot />);

    expect(screen.queryByTestId("archetype-sprites")).not.toBeInTheDocument();
  });
});
