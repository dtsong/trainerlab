import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { JPPreview } from "../JPPreview";

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
vi.mock("@/components/ui/section-label", () => ({
  SectionLabel: ({ label }: { label: string }) => <span>{label}</span>,
}));

vi.mock("@/components/ui/jp-signal-badge", () => ({
  JPSignalBadge: () => <span data-testid="jp-signal-badge" />,
}));

vi.mock("../skeletons", () => ({
  ComparisonRowSkeleton: () => <div data-testid="comparison-skeleton" />,
}));

// Mock hooks
const mockUseHomeMetaData = vi.fn();
const mockUsePredictions = vi.fn();

vi.mock("@/hooks/useMeta", () => ({
  useHomeMetaData: () => mockUseHomeMetaData(),
}));

vi.mock("@/hooks/useJapan", () => ({
  usePredictions: (...args: unknown[]) => mockUsePredictions(...args),
}));

// Mock home-utils
vi.mock("@/lib/home-utils", () => ({
  buildJPComparisons: vi.fn(
    (
      globalMeta:
        | { archetype_breakdown?: { name: string; share: number }[] }
        | undefined,
      jpMeta:
        | { archetype_breakdown?: { name: string; share: number }[] }
        | undefined,
      limit: number = 3
    ) => {
      if (
        !globalMeta?.archetype_breakdown?.length ||
        !jpMeta?.archetype_breakdown?.length
      ) {
        return [];
      }
      const jpTop = jpMeta.archetype_breakdown.slice(0, limit);
      const globalTop = globalMeta.archetype_breakdown.slice(0, limit);
      return jpTop.map((jp: { name: string; share: number }, i: number) => ({
        rank: i + 1,
        jpName: jp.name,
        jpShare: jp.share * 100,
        enName: globalTop[i]?.name ?? "---",
        enShare: (globalTop[i]?.share ?? 0) * 100,
        divergence: 10,
      }));
    }
  ),
}));

describe("JPPreview", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUsePredictions.mockReturnValue({
      data: undefined,
    });
  });

  it("should return null when no JP data and not loading", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      jpMeta: undefined,
      isLoading: false,
      isError: false,
    });

    const { container } = render(<JPPreview />);

    expect(container.firstChild).toBeNull();
  });

  it("should render the section label", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      jpMeta: {
        archetype_breakdown: [{ name: "Dragapult ex", share: 0.18 }],
      },
      isLoading: false,
      isError: false,
    });

    render(<JPPreview />);

    expect(screen.getByText("Japan vs Global")).toBeInTheDocument();
  });

  it("should render 'Full JP Analysis' link to /meta/japan", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      jpMeta: {
        archetype_breakdown: [{ name: "Dragapult ex", share: 0.18 }],
      },
      isLoading: false,
      isError: false,
    });

    render(<JPPreview />);

    const link = screen.getByRole("link", { name: /Full JP Analysis/i });
    expect(link).toHaveAttribute("href", "/meta/japan");
  });

  it("should render comparison table headers", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      jpMeta: {
        archetype_breakdown: [{ name: "Dragapult ex", share: 0.18 }],
      },
      isLoading: false,
      isError: false,
    });

    render(<JPPreview />);

    expect(screen.getByText("Japan Top 3")).toBeInTheDocument();
    expect(screen.getByText("Global Top 3")).toBeInTheDocument();
  });

  it("should show loading skeletons while loading", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      jpMeta: undefined,
      isLoading: true,
      isError: false,
    });

    render(<JPPreview />);

    const skeletons = screen.getAllByTestId("comparison-skeleton");
    expect(skeletons).toHaveLength(3);
  });

  it("should render JP and global archetype names", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [
          { name: "Charizard ex", share: 0.15 },
          { name: "Lugia VSTAR", share: 0.12 },
        ],
      },
      jpMeta: {
        archetype_breakdown: [
          { name: "Dragapult ex", share: 0.18 },
          { name: "Raging Bolt ex", share: 0.14 },
        ],
      },
      isLoading: false,
      isError: false,
    });

    render(<JPPreview />);

    expect(screen.getByText("Dragapult ex")).toBeInTheDocument();
    expect(screen.getByText("Raging Bolt ex")).toBeInTheDocument();
    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    expect(screen.getByText("Lugia VSTAR")).toBeInTheDocument();
  });

  it("should render meta share percentages", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      jpMeta: {
        archetype_breakdown: [{ name: "Dragapult ex", share: 0.18 }],
      },
      isLoading: false,
      isError: false,
    });

    render(<JPPreview />);

    expect(screen.getByText("18%")).toBeInTheDocument();
    expect(screen.getByText("15%")).toBeInTheDocument();
  });

  it("should render a prediction callout when prediction data is available", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      jpMeta: {
        archetype_breakdown: [{ name: "Dragapult ex", share: 0.18 }],
      },
      isLoading: false,
      isError: false,
    });

    mockUsePredictions.mockReturnValue({
      data: {
        items: [
          {
            prediction_text:
              "Dragapult ex will rise to Tier 1 in global meta within 2 months",
            confidence: "high",
          },
        ],
      },
    });

    render(<JPPreview />);

    expect(screen.getByText("Prediction:")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Dragapult ex will rise to Tier 1 in global meta within 2 months/
      )
    ).toBeInTheDocument();
    expect(screen.getByText("high confidence")).toBeInTheDocument();
  });

  it("should not render prediction callout when no predictions", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      jpMeta: {
        archetype_breakdown: [{ name: "Dragapult ex", share: 0.18 }],
      },
      isLoading: false,
      isError: false,
    });

    mockUsePredictions.mockReturnValue({ data: undefined });

    render(<JPPreview />);

    expect(screen.queryByText("Prediction:")).not.toBeInTheDocument();
  });
});
