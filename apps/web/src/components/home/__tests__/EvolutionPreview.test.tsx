import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { EvolutionPreview } from "../EvolutionPreview";

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

vi.mock("@/components/ui/badge", () => ({
  Badge: ({
    children,
  }: {
    children: React.ReactNode;
    variant?: string;
    className?: string;
  }) => <span data-testid="badge">{children}</span>,
}));

// Mock hooks
const mockUseHomeMetaData = vi.fn();
const mockUseEvolutionArticles = vi.fn();
const mockUseArchetypeEvolution = vi.fn();

vi.mock("@/hooks/useMeta", () => ({
  useHomeMetaData: () => mockUseHomeMetaData(),
}));

vi.mock("@/hooks/useEvolution", () => ({
  useEvolutionArticles: (...args: unknown[]) =>
    mockUseEvolutionArticles(...args),
  useArchetypeEvolution: (...args: unknown[]) =>
    mockUseArchetypeEvolution(...args),
}));

// Mock home-utils
vi.mock("@/lib/home-utils", () => ({
  computeMetaMovers: vi.fn(() => []),
}));

describe("EvolutionPreview", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseEvolutionArticles.mockReturnValue({
      data: undefined,
      isError: false,
    });

    mockUseArchetypeEvolution.mockReturnValue({
      data: undefined,
      isError: false,
    });
  });

  it("should return null when no top archetype data and not loading", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: { archetype_breakdown: [] },
      history: undefined,
      isLoading: false,
      isError: false,
    });

    const { container } = render(<EvolutionPreview />);

    expect(container.firstChild).toBeNull();
  });

  it("should render the section label", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      history: { snapshots: [] },
      isLoading: false,
      isError: false,
    });

    render(<EvolutionPreview />);

    expect(screen.getByText("Deck Evolution")).toBeInTheDocument();
  });

  it("should render the top archetype name", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.153 }],
      },
      history: { snapshots: [] },
      isLoading: false,
      isError: false,
    });

    render(<EvolutionPreview />);

    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
  });

  it("should render the current meta share percentage", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.153 }],
      },
      history: { snapshots: [] },
      isLoading: false,
      isError: false,
    });

    render(<EvolutionPreview />);

    expect(screen.getByText("15.3%")).toBeInTheDocument();
  });

  it("should render 'Meta Movers (30 days)' heading", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      history: { snapshots: [] },
      isLoading: false,
      isError: false,
    });

    render(<EvolutionPreview />);

    expect(screen.getByText("Meta Movers (30 days)")).toBeInTheDocument();
  });

  it("should show loading skeleton when loading", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: undefined,
      history: undefined,
      isLoading: true,
      isError: false,
    });

    render(<EvolutionPreview />);

    // The loading state renders animate-pulse divs
    expect(screen.getByText("Deck Evolution")).toBeInTheDocument();
  });

  it("should show 'Not enough historical data yet' when no movers", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      history: { snapshots: [] },
      isLoading: false,
      isError: false,
    });

    render(<EvolutionPreview />);

    expect(
      screen.getByText("Not enough historical data yet")
    ).toBeInTheDocument();
  });

  it("should show 'Current meta share' when no previous data", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      history: { snapshots: [] },
      isLoading: false,
      isError: false,
    });

    render(<EvolutionPreview />);

    expect(screen.getByText("Current meta share")).toBeInTheDocument();
  });

  it("should render a featured evolution article when available", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      history: { snapshots: [] },
      isLoading: false,
      isError: false,
    });

    mockUseEvolutionArticles.mockReturnValue({
      data: [
        {
          title: "The Rise of Charizard ex",
          slug: "rise-of-charizard",
          excerpt: "How Charizard ex took over the meta",
        },
      ],
      isError: false,
    });

    render(<EvolutionPreview />);

    expect(screen.getByText("Featured Evolution")).toBeInTheDocument();
    expect(screen.getByText("The Rise of Charizard ex")).toBeInTheDocument();
    expect(
      screen.getByText("How Charizard ex took over the meta")
    ).toBeInTheDocument();

    const articleLink = screen.getByRole("link", {
      name: /Read Full Evolution Analysis/i,
    });
    expect(articleLink).toHaveAttribute("href", "/evolution/rise-of-charizard");
  });

  it("should render fallback link to /evolution when no featured article", () => {
    mockUseHomeMetaData.mockReturnValue({
      globalMeta: {
        archetype_breakdown: [{ name: "Charizard ex", share: 0.15 }],
      },
      history: { snapshots: [] },
      isLoading: false,
      isError: false,
    });

    mockUseEvolutionArticles.mockReturnValue({
      data: undefined,
      isError: false,
    });

    render(<EvolutionPreview />);

    const link = screen.getByRole("link", {
      name: /View all evolution articles/i,
    });
    expect(link).toHaveAttribute("href", "/evolution");
  });
});
